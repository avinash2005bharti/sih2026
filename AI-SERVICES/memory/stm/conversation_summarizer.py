"""
Conversation Summarizer for Sovereign AI Workbench.
Maintains a rolling, concise summary of large conversations to keep prompts bounded.
Saves summary to MongoDB conversations collection.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId

from core.logging import logger
from core.config import settings
from memory.stm.stm_manager import stm_manager
from llm.ollama_client import OllamaClient


class ConversationSummarizer:
    """Summarizes long dialogs and persists rolling summaries into MongoDB."""

    def __init__(self):
        self.summary_threshold = 8 # Run summary if conversation has >= 8 messages
        self._summarizing_convs = set() # Avoid concurrent duplicate summarizations

    async def summarize_if_needed(self, conversation_id: str, user_id: Optional[str] = None):
        """Check message count and trigger asynchronous summarization if threshold met."""
        if not conversation_id or conversation_id in self._summarizing_convs:
            return

        db = stm_manager._get_db()
        if db is None:
            return

        try:
            q_id = ObjectId(conversation_id) if ObjectId.is_valid(conversation_id) else conversation_id
            msg_count = db.messages.count_documents({"$or": [{"conversation_id": conversation_id}, {"conversation": q_id}]})
            if msg_count < self.summary_threshold:
                return

            self._summarizing_convs.add(conversation_id)
            asyncio.create_task(self._do_summarize(conversation_id, db))
        except Exception as e:
            logger.debug(f"[SUMMARIZER] Check error: {e}")

    async def _do_summarize(self, conversation_id: str, db: Any):
        """Execute summarization using local Ollama model."""
        try:
            q_id = ObjectId(conversation_id) if ObjectId.is_valid(conversation_id) else conversation_id
            cursor = (
                db.messages.find({"$or": [{"conversation_id": conversation_id}, {"conversation": q_id}]})
                .sort("createdAt", 1)
                .limit(25)
            )
            dialog_lines = []
            for m in cursor:
                sender = "User" if m.get("sender") == "user" else "Assistant"
                content = str(m.get("content", ""))[:200]
                if content:
                    dialog_lines.append(f"{sender}: {content}")

            if not dialog_lines:
                return

            prompt = (
                "Provide a concise, 3-4 bullet point operational summary of this ongoing conversation.\n"
                "Focus strictly on:\n"
                "- User's primary goals and instructions\n"
                "- Files, spreadsheets, or PDFs requested or created\n"
                "- Current status and decisions\n\n"
                f"Conversation:\n" + "\n".join(dialog_lines) + "\n\n"
                "Summary:"
            )

            client = OllamaClient()
            model = getattr(settings, "OLLAMA_CHAT_MODEL", "qwen2.5:1.5b")
            summary = await client.generate(model=model, prompt=prompt)
            summary = summary.strip()

            if summary:
                db.conversations.update_one(
                    {"_id": q_id},
                    {
                        "$set": {
                            "summary": summary,
                            "summaryUpdatedAt": datetime.now(timezone.utc)
                        }
                    }
                )
                logger.info(f"[SUMMARIZER] Updated rolling summary for conversation {conversation_id} ({len(summary)} chars)")

        except Exception as e:
            logger.warning(f"[SUMMARIZER] Summarization error for {conversation_id}: {e}")
        finally:
            self._summarizing_convs.discard(conversation_id)


# Global singleton instance
conversation_summarizer = ConversationSummarizer()
