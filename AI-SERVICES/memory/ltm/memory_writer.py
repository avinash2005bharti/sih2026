"""
LTM Memory Writer for Sovereign AI Workbench.
Handles async memory extraction, secret/credential sanitization, classification,
Qdrant vector upsert, and Neo4j graph entity persistence.
"""

import re
import uuid
import time
from typing import Any, Dict, List, Optional
from core.logging import logger
from memory.models import MemoryItem, MemoryType
from memory.embeddings.embedding_service import embedding_service
from memory.vector.qdrant_service import qdrant_service
from memory.graph.neo4j_service import neo4j_service
from memory.mem0.mem0_service import mem0_service


SECRET_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|bearer|token|secret|password|passwd|auth)\s*[:=]\s*["\']?[a-zA-Z0-9_\-\.]{8,}'),
    re.compile(r'(?i)mongodb(?:\+srv)?:\/\/[^\s]+'),
    re.compile(r'ghp_[a-zA-Z0-9]{36}'),
    re.compile(r'xkeysib-[a-zA-Z0-9]{64}'),
    re.compile(r'eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}'),  # JWT
    re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----')
]

# Words that should never be treated as a "name" or "org" entity — these were
# leaking into the graph because the wrapper text ("User profile: ...") itself
# gets re-scanned for capitalized phrases.
ENTITY_BLOCKLIST = {"user", "user profile", "profile", "key entities", "assistant"}


class MemoryWriter:
    """Extracts, scrubs, and persists long-term semantic and graph memories."""

    def contains_secrets(self, text: str) -> bool:
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                return True
        return False

    def sanitize_text(self, text: str) -> str:
        sanitized = text
        for pattern in SECRET_PATTERNS:
            sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
        return sanitized

    def classify_memory(self, text: str) -> str:
        lower = text.lower()
        if any(w in lower for w in ["prefer", "like", "favorite", "choose", "always use", "default to", "my preference"]):
            return MemoryType.PREFERENCE.value
        if any(w in lower for w in ["rule", "must", "should always", "never", "do not", "instruction"]):
            return MemoryType.INSTRUCTION.value
        if any(w in lower for w in ["our project", "the project", "sih", "workbench", "architecture", "system uses"]):
            return MemoryType.PROJECT_KNOWLEDGE.value
        if any(w in lower for w in ["algorithm", "database", "docker", "python", "fastapi", "neo4j", "qdrant", "vibration", "pump"]):
            return MemoryType.TECHNICAL_KNOWLEDGE.value
        return MemoryType.FACT.value

    def extract_entities(self, text: str) -> List[str]:
        """Rule-based heuristic and regex entity extractor for local graphs."""
        entities = set()

        name_match = re.search(
            r'(?:i am|i\'m|my name is|call me|myself)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)',
            text,
            re.IGNORECASE
        )
        if name_match:
            name = name_match.group(1).strip().title()
            if name.lower() not in ["a", "an", "the", "here", "just", "your", "an agent", "a bot", "a tool", "working"]:
                entities.add(name)

        org_match = re.search(
            r'(?:from|at|team|company|organization)\s+([a-zA-Z0-9]+(?:\s+[a-zA-Z0-9]+)?)',
            text,
            re.IGNORECASE
        )
        if org_match:
            org = org_match.group(1).strip().title()
            if org.lower() not in ["a", "an", "the", "here", "home", "scratch", "now", "today", "us"]:
                entities.add(org)

        roles = re.findall(
            r'\b(creator|founder|developer|engineer|admin|author|maintainer|architect|researcher)\b',
            text,
            re.IGNORECASE
        )
        for r in roles:
            entities.add(r.title())

        known = [
            "Python", "Node.js", "FastAPI", "React", "Docker", "Qdrant", "Neo4j",
            "MongoDB", "Valkey", "Redis", "Ollama", "Mem0", "PaddleOCR", "Moondream",
            "LangGraph", "LangChain", "Sovereign AI", "Workbench", "SIH 2026",
            "vibration analysis", "pump failure detection"
        ]
        for k in known:
            if re.search(r'\b' + re.escape(k) + r'\b', text, re.IGNORECASE):
                entities.add(k)

        matches = re.findall(r'\b[A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*\b', text)
        for m in matches:
            if len(m) > 3 and m.lower() not in ENTITY_BLOCKLIST and m.lower() not in ["this", "that", "hello"]:
                entities.add(m)

        return list(entities)[:8]

    async def write_memory(
        self,
        user_id: str,
        content: str,
        conversation_id: Optional[str] = None,
        source_message_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        importance: float = 0.8,
        confidence: float = 0.95,
        entities: Optional[List[str]] = None
    ) -> Optional[MemoryItem]:
        """
        Store a persistent memory into both Qdrant (vector) and Neo4j (graph).
        `entities` can be pre-computed by the caller (e.g. extract_and_store_from_dialog)
        to avoid re-running extraction on the already-formatted content string.
        """
        if not content or not content.strip():
            return None

        if self.contains_secrets(content):
            logger.warning("[LTM] Memory contained credentials/secrets — redacting before storage.")
            content = self.sanitize_text(content)
            if not content.replace("[REDACTED_SECRET]", "").strip():
                logger.warning("[LTM] Memory fully redacted, nothing left to store. Skipping.")
                return None

        clean_content = content.strip()
        mem_type = memory_type or self.classify_memory(clean_content)
        final_entities = entities if entities is not None else self.extract_entities(clean_content)
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"

        # Normalize user_id to string consistently everywhere it's used downstream
        norm_user_id = str(user_id)

        item = MemoryItem(
            memory_id=memory_id,
            user_id=norm_user_id,
            conversation_id=conversation_id,
            source_id=conversation_id,
            source_message_id=source_message_id,
            memory_type=mem_type,
            content=clean_content,
            source="conversation",
            importance=importance,
            confidence=confidence,
            entity_references=final_entities,
            created_at=time.time(),
            updated_at=time.time()
        )

        logger.info(f"[LTM] Writing memory_id={memory_id} user_id='{norm_user_id}' type={mem_type} content='{clean_content[:80]}'")

        try:
            await mem0_service.add_memory(
                text_or_messages=clean_content,
                user_id=norm_user_id,
                metadata={
                    "memory_id": memory_id,
                    "memory_type": mem_type,
                    "conversation_id": conversation_id,
                    "source": "conversation"
                }
            )
        except Exception as e:
            logger.debug(f"[LTM] Mem0 add note: {e}")

        try:
            embed_text = f"search_document: {clean_content}"
            vector = await embedding_service.embed_text(embed_text)
            if vector:
                ok = await qdrant_service.upsert_memory(item, vector)
                if ok:
                    logger.info(f"[LTM] Upserted memory vector to Qdrant ({memory_id}) for user '{norm_user_id}'")
                else:
                    logger.error(f"[LTM] Qdrant upsert returned False for memory ({memory_id})")
            else:
                logger.error(f"[LTM] Embedding returned empty vector for memory ({memory_id}) — check embedding_service/Ollama connectivity")
        except Exception as e:
            logger.warning(f"[LTM] Qdrant memory write warning: {e}")

        try:
            await neo4j_service.record_memory(
                memory_id=memory_id,
                user_id=norm_user_id,
                content=clean_content,
                memory_type=mem_type,
                conversation_id=conversation_id,
                entities=final_entities
            )
            logger.info(f"[LTM] Recorded memory in Neo4j graph ({memory_id}) with entities: {final_entities}")
        except Exception as e:
            logger.warning(f"[LTM] Neo4j memory write warning: {e}")

        logger.info(f"[LTM] Stored memory '{memory_id}' (Type: {mem_type}) for user '{norm_user_id}'")
        return item

    async def extract_and_store_from_dialog(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        conversation_id: Optional[str] = None,
        source_message_id: Optional[str] = None
    ):
        """
        Background task: analyze conversation exchange and extract memorable facts,
        preferences, or project knowledge. Never blocks the main chat response.
        """
        if not user_message or len(user_message.strip()) < 5:
            return

        text = user_message.strip()
        lower = text.lower()

        trivial_phrases = ["hi", "hello", "hey", "test", "how are you", "what is", "who are you", "tell me", "ok", "okay", "thanks", "thank you"]
        if lower in trivial_phrases or (len(text.split()) <= 2 and not any(k in lower for k in ["prefer", "use", "project", "my", "i am", "i'm"])):
            return

        is_question = text.endswith("?") or lower.startswith((
            "what is", "what are", "who is", "who are", "where is", "where are",
            "why is", "why are", "when is", "when did", "how is", "how do", "how can",
            "did i", "what did", "can you tell", "tell me what", "is there", "are there"
        ))
        if is_question:
            logger.debug(f"[LTM] Skipping storage — message detected as a question: '{text[:60]}'")
            return

        signals = [
            "i am", "i'm", "my name", "myself", "call me", "creator", "founder",
            "developer", "engineer", "author", "maintainer", "from ", "work at",
            "working on", "prefer", "like", "favorite", "choice", "we use", "our stack",
            "uses", "is built with", "project uses", "team uses", "configured with",
            "maintenance team", "vibration", "always", "never", "remember that", "remember",
            "keep in mind", "note that", "don't forget"
        ]

        if any(sig in lower for sig in signals):
            try:
                entities = self.extract_entities(text)

                if any(k in lower for k in ["i am", "i'm", "my name", "creator", "from"]):
                    ent_str = ", ".join(entities) if entities else ""
                    fact_content = f"User profile: {text}. Key Entities: {ent_str}" if ent_str else f"User profile: {text}"
                else:
                    fact_content = text

                await self.write_memory(
                    user_id=user_id,
                    content=fact_content,
                    conversation_id=conversation_id,
                    source_message_id=source_message_id,
                    entities=entities  # pass pre-computed entities, don't re-extract from wrapper text
                )
            except Exception as e:
                logger.error(f"[LTM] Dialog extraction error: {e}")
        else:
            logger.debug(f"[LTM] No memory signals matched for: '{text[:60]}'")


# Global singleton instance
memory_writer = MemoryWriter()