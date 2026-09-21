"""
Centralized Context Builder & Context-Aware Routing for Sovereign AI Workbench.
Implements the multi-layer memory architecture:
MongoDB Conversation History (STM) + Rolling Summary + Artifacts + Executions + Mem0/Qdrant LTM + Neo4j Graph.
Constructs clean, bounded prompt context and message history for LLM / LangGraph Agents.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from core.config import settings
from core.logging import logger

from memory.stm.stm_manager import stm_manager
from memory.artifacts.artifact_store import artifact_store
from memory.executions.execution_store import execution_store
from memory.ltm.ltm_manager import ltm_manager
from memory.graph.neo4j_service import neo4j_service


class QueryIntent(str, Enum):
    GREETING = "greeting"
    CONVERSATION_HISTORY = "conversation_history"
    ARTIFACT_QUERY = "artifact_query"
    EXECUTION_QUERY = "execution_query"
    LONG_TERM_MEMORY = "long_term_memory"
    DOCUMENT_METADATA_QUERY = "document_metadata_query"
    DOCUMENT_RAG = "document_rag"
    GRAPH_QUERY = "graph_query"
    CONTINUATION_OR_REFERENCE = "continuation_or_reference"
    GENERAL_TASK = "general_task"


@dataclass
class EnrichedContext:
    """Structured context object assembled for agent/LLM inference."""
    conversation_id: str
    user_id: Optional[str]
    intent: QueryIntent
    system_prompt: str
    history_messages: List[Dict[str, str]] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    executions: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    ltm_context: str = ""
    graph_context: str = ""
    document_context: str = ""
    repo_documents: List[Dict[str, Any]] = field(default_factory=list)
    observability: Dict[str, Any] = field(default_factory=dict)

    @property
    def recent_messages(self) -> List[Dict[str, str]]:
        """Alias for history_messages (STM)."""
        return self.history_messages

    @property
    def memories(self) -> List[str]:
        """List representation of LTM memories."""
        if not self.ltm_context:
            return []
        items = [line.strip("- *• ") for line in self.ltm_context.splitlines() if line.strip()]
        return items if items else [self.ltm_context]


class ContextBuilder:
    """
    Centralized Context Builder responsible for intelligent retrieval routing,
    gathering multi-layer state, and constructing prompt-ready context.
    """

    def classify_intent(self, query: str) -> QueryIntent:
        """
        Classify user query into target retrieval intent to avoid unnecessary overhead.
        Phase 12 & Phase 20 compliant.
        """
        q = (query or "").strip().lower()

        # 1. Greetings / Trivial conversational remarks
        greetings = ["hello", "hi", "hey", "good morning", "good evening", "good afternoon", "how are you", "who are you", "thanks", "thank you"]
        if q in greetings or any(q.startswith(g + " ") or q == g for g in ["hello", "hi", "hey"]):
            return QueryIntent.GREETING

        # 2. Artifact queries (generated files, reports, spreadsheets, PDFs)
        artifact_keywords = [
            "which file", "what file", "created file", "files have you created", "files did you create",
            "which files", "what files", "list files", "show files", "generated file", "created previously",
            "where is the file", "where is the report", "inspection report file",
            "purpose of those files", "purpose of these files"
        ]
        if any(kw in q for kw in artifact_keywords):
            return QueryIntent.ARTIFACT_QUERY

        # 3. Contextual Continuation / Anaphoric reference ("this data", "that file")
        reference_keywords = [
            "this data", "of this data", "that data", "this report", "that file",
            "same data", "the above data", "from this data"
        ]
        if any(kw in q for kw in reference_keywords):
            return QueryIntent.CONTINUATION_OR_REFERENCE

        # 4. Tool execution queries
        execution_keywords = [
            "what did you execute", "which tool did you run", "did the execution succeed",
            "did it run", "tool execution", "execution status", "command output", "execution logs",
            "did the pdf generation succeed", "did excel generation succeed"
        ]
        if any(kw in q for kw in execution_keywords):
            return QueryIntent.EXECUTION_QUERY

        # 5. Conversation history / previous instruction recall
        history_keywords = [
            "what did i ask", "what did i request", "what was my last", "last instruction",
            "previous instruction", "what did you say", "what was our last", "repeat what",
            "what was my earlier", "did i ask you", "what did i tell you earlier",
            "what is my name", "who am i", "my name is"
        ]
        if any(kw in q for kw in history_keywords):
            return QueryIntent.CONVERSATION_HISTORY

        # 6. Long-term memory / persistent project facts & preferences
        ltm_keywords = [
            "what do you remember", "my preference", "what format do i prefer", "my project",
            "what do you know about me", "remember that", "personal information", "audit format"
        ]
        if any(kw in q for kw in ltm_keywords):
            return QueryIntent.LONG_TERM_MEMORY

        # 7. Graph / relationship queries
        graph_keywords = [
            "connected to", "relationship between", "who inspected", "which department",
            "equipment failure", "risk associated with", "inspection graph", "condition of"
        ]
        if any(kw in q for kw in graph_keywords):
            return QueryIntent.GRAPH_QUERY

        # 8. Document repository queries (document count, list documents, document section)
        doc_repo_keywords = [
            "how many document", "how many documents", "count document", "count documents",
            "number of documents", "what documents", "which documents", "my documents",
            "document section", "document sections", "in document section", "in my document",
            "in my documents", "list documents", "show documents", "all documents",
            "uploaded documents", "find documents", "documents in my workspace",
            "documents in workspace", "documents do i have", "documents uploaded",
            "give me document", "give me the document", "give me any document", "give document",
            "get document", "read document", "view document", "display document", "show document",
            "show me document", "fetch document", "any document", "provide document", "open document",
            "access document", "see document", "see the document", "what is in the document",
            "what is in my document", "check documents", "check my documents", "check the document"
        ]
        if any(kw in q for kw in doc_repo_keywords):
            return QueryIntent.DOCUMENT_METADATA_QUERY

        # 9. Document RAG queries (content search within documents)
        doc_keywords = ["sop", "manual", "handbook", "policy", "uploaded document", "section in"]
        if any(kw in q for kw in doc_keywords):
            return QueryIntent.DOCUMENT_RAG

        return QueryIntent.GENERAL_TASK

    async def build(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        is_admin: bool = False,
        user_role: Optional[str] = None,
        query: str = "",
        agent_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        current_query: Optional[str] = None,
        **extra_kwargs
    ) -> EnrichedContext:
        """
        Assemble multi-layer context across STM, Summaries, Artifacts, Executions,
        LTM, Documents, and Knowledge Graph into an EnrichedContext bundle.
        """
        eff_query = (query or current_query or "").strip()
        intent = self.classify_intent(eff_query)
        logger.info(f"[CONTEXT] Building context | conv={conversation_id} | user={user_id} | is_admin={is_admin} | intent={intent.value} | query='{eff_query}'")

        history_messages: List[Dict[str, str]] = []
        artifacts: List[Dict[str, Any]] = []
        executions: List[Dict[str, Any]] = []
        summary = ""
        ltm_ctx = ""
        graph_ctx = ""
        doc_ctx = ""

        # ---------------------------------------------------------------------
        # 1. STM Conversation History (Always retrieved unless query is pure greeting)
        # ---------------------------------------------------------------------
        if conversation_id:
            try:
                # Limit turns for simple greeting, full recent history otherwise
                msg_limit = 4 if intent == QueryIntent.GREETING else getattr(settings, "STM_MAX_MESSAGES", 20)
                stm_ctx = await stm_manager.get_conversation_context(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    agent_id=agent_id,
                    limit=msg_limit
                )
                raw_msgs = stm_ctx.messages or []

                # Omit latest message if identical to current query (prevents self-referencing echo)
                clean_query = eff_query
                if raw_msgs and raw_msgs[-1].content.strip() == clean_query:
                    raw_msgs = raw_msgs[:-1]

                for m in raw_msgs:
                    history_messages.append({
                        "role": m.role,
                        "content": m.content.strip()
                    })
            except Exception as stm_err:
                logger.warning(f"[CONTEXT] STM retrieval warning: {stm_err}")

        # ---------------------------------------------------------------------
        # 2. Rolling Conversation Summary (if conversation is long)
        # ---------------------------------------------------------------------
        if conversation_id and len(history_messages) >= 6:
            try:
                db = stm_manager._get_db()
                if db is not None:
                    from bson import ObjectId
                    q_id = ObjectId(conversation_id) if ObjectId.is_valid(conversation_id) else conversation_id
                    conv_doc = db.conversations.find_one({"_id": q_id})
                    if conv_doc and conv_doc.get("summary"):
                        summary = conv_doc.get("summary", "")
            except Exception as sum_err:
                logger.debug(f"[CONTEXT] Summary retrieval note: {sum_err}")

        # ---------------------------------------------------------------------
        # 3. Artifact Memory (Retrieved for artifact queries, continuations, history)
        # ---------------------------------------------------------------------
        if conversation_id and intent in [
            QueryIntent.ARTIFACT_QUERY,
            QueryIntent.CONTINUATION_OR_REFERENCE,
            QueryIntent.GENERAL_TASK,
            QueryIntent.CONVERSATION_HISTORY,
            QueryIntent.EXECUTION_QUERY
        ]:
            try:
                artifacts = artifact_store.get_artifacts_for_conversation(conversation_id, limit=15)
            except Exception as art_err:
                logger.warning(f"[CONTEXT] Artifact retrieval warning: {art_err}")

        # ---------------------------------------------------------------------
        # 4. Tool Execution Memory (Retrieved for execution queries, tasks, and history)
        # ---------------------------------------------------------------------
        if conversation_id and intent in [QueryIntent.EXECUTION_QUERY, QueryIntent.GENERAL_TASK, QueryIntent.CONVERSATION_HISTORY]:
            try:
                executions = execution_store.get_recent_executions(conversation_id, limit=8)
            except Exception as exec_err:
                logger.warning(f"[CONTEXT] Execution retrieval warning: {exec_err}")

        # ---------------------------------------------------------------------
        # 5. Long-Term Memory (Mem0 / Qdrant).  Retrieval is deliberately
        # bounded, but must happen for ordinary task turns as well: durable
        # project facts are often relevant without the user saying "remember".
        # ---------------------------------------------------------------------
        if user_id and intent not in [QueryIntent.GREETING]:
            try:
                ltm_ctx = await ltm_manager.get_context(query=eff_query, user_id=user_id)
            except Exception as ltm_err:
                logger.debug(f"[CONTEXT] LTM retrieval note: {ltm_err}")

        # ---------------------------------------------------------------------
        # 6. Document Repository & Document Section Metadata
        # ---------------------------------------------------------------------
        repo_docs: List[Dict[str, Any]] = []
        doc_interest_keywords = [
            "document", "documents", "sop", "manual", "policy", "handbook", "procedure",
            "report", "reference", "uploaded", "database", "inspect", "audit", "guideline",
            "instruction", "file", "files", "spec", "specification", "turbine", "safety", "fmea",
            "how many document", "count document", "document section", "my documents", "list documents",
            "pdf", "generate pdf", "create pdf", "make pdf", "same data", "this data", "that data",
            "data", "excel", "summary", "summarize", "export"
        ]
        # Always fetch repo docs if user_id or conversation_id is present to give models complete document awareness
        is_doc_relevant = (
            bool(user_id or conversation_id)
            or intent in [
                QueryIntent.DOCUMENT_METADATA_QUERY,
                QueryIntent.DOCUMENT_RAG,
                QueryIntent.CONTINUATION_OR_REFERENCE,
                QueryIntent.GENERAL_TASK,
                QueryIntent.ARTIFACT_QUERY
            ]
            or any(kw in eff_query.lower() for kw in doc_interest_keywords)
        )
        if is_doc_relevant:
            try:
                from rag.document_store import document_store
                # Agents require unrestricted visibility into the Document Section repository
                repo_docs = document_store.list_documents(limit=100, user_id=user_id, is_admin=True)
                logger.info(f"[CONTEXT] Fetched {len(repo_docs)} repository documents for query context (user={user_id}, is_admin=True)")
            except Exception as repo_err:
                logger.warning(f"[CONTEXT] Document store list warning: {repo_err}")

        # ---------------------------------------------------------------------
        # 7. Document RAG Evidence Retrieval
        # ---------------------------------------------------------------------
        if intent not in [QueryIntent.DOCUMENT_METADATA_QUERY, QueryIntent.ARTIFACT_QUERY, QueryIntent.EXECUTION_QUERY] and (
            intent in [QueryIntent.DOCUMENT_RAG, QueryIntent.CONTINUATION_OR_REFERENCE, QueryIntent.GENERAL_TASK] or any(
                word in eff_query.lower() for word in doc_interest_keywords
            )
        ):
            try:
                from rag.retriever import rag_retriever
                allowed_doc_ids = None

                search_q = eff_query
                ref_keywords = ["same data", "this data", "that data", "this document", "the document", "pdf about", "generate pdf"]
                if any(rw in eff_query.lower() for rw in ref_keywords) and repo_docs:
                    top_doc = repo_docs[0]
                    search_q = top_doc.get("name") or top_doc.get("originalName") or eff_query

                results = await rag_retriever.retrieve(
                    search_q,
                    top_k=6,
                    score_threshold=0.15,
                    allowed_doc_ids=allowed_doc_ids,
                    user_id=user_id,
                    is_admin=True
                )
                if results:
                    evidence = []
                    for index, result in enumerate(results, start=1):
                        metadata = result.get("metadata") or {}
                        source = metadata.get("source") or metadata.get("filename") or result.get("filename") or "uploaded document"
                        page = metadata.get("page") or result.get("page")
                        label = f"{source}" + (f" — page {page}" if page is not None else "")
                        evidence.append(f"[Source {index}: {label}; score={result.get('score', 0):.3f}]\n{result.get('text', '')}")
                    doc_ctx = "\n\n".join(evidence)
            except Exception as rag_err:
                logger.warning(f"[CONTEXT] RAG retrieval warning: {rag_err}")

        # ---------------------------------------------------------------------
        # 8. Knowledge Graph (Neo4j) - Targeted retrieval only
        # ---------------------------------------------------------------------
        if intent == QueryIntent.GRAPH_QUERY:
            try:
                if neo4j_service._get_driver() is not None:
                    graph_results = await neo4j_service.query_related_context(eff_query, user_id=user_id, limit=5)
                    if graph_results:
                        graph_parts = []
                        for item in graph_results:
                            if isinstance(item, dict):
                                graph_parts.append(f"Entity: {item.get('name', '')} | Relations: {item.get('relations', '')} | Type: {item.get('type', '')}")
                            else:
                                graph_parts.append(str(item))
                        if graph_parts:
                            graph_ctx = "\n".join(graph_parts)
            except Exception as graph_err:
                logger.debug(f"[CONTEXT] Neo4j retrieval note: {graph_err}")

        # ---------------------------------------------------------------------
        # Assemble Final Context-Aware System Prompt
        # ---------------------------------------------------------------------
        base_sys = system_prompt or (
            "You are the Sovereign On-Premise AI Agent Workbench assistant. "
            "You operate strictly within a local, air-gapped, privacy-preserving infrastructure."
        )

        prompt_sections = [base_sys]

        # Prioritize Document Repository state directly after base system prompt
        if repo_docs:
            doc_lines = []
            doc_content_sections = []
            for i, d in enumerate(repo_docs, start=1):
                name = d.get("name") or d.get("originalName") or "Untitled"
                dtype = d.get("documentType") or "unknown"
                status = d.get("processingStatus") or "processed"
                chunks = d.get("metadata", {}).get("chunksCount", 0) if isinstance(d.get("metadata"), dict) else 0
                doc_id = str(d.get("document_id") or d.get("_id") or d.get("id") or "")
                doc_lines.append(f"{i}. \"{name}\" (ID: {doc_id}, Type: {dtype}, Status: {status}, Chunks: {chunks})")

                # Extract content preview for top 10 documents so model has complete visibility
                if i <= 10:
                    raw_content = d.get("extractedText") or ""
                    if not raw_content or len(raw_content.strip()) < 50:
                        fpath = d.get("filePath") or d.get("file_path") or name
                        try:
                            from rag.document_store import document_store
                            raw_content = document_store._read_full_document_content(fpath)
                        except Exception:
                            pass
                    clean_content = (raw_content or "").strip()
                    if clean_content:
                        if len(clean_content) > 3500:
                            clean_content = clean_content[:3500] + "\n... [Content truncated for prompt; complete text accessible via get_document_content or read_file]"
                        doc_content_sections.append(f"=== Document [{i}]: \"{name}\" (ID: {doc_id}, Type: {dtype}) ===\nEXTRACTED DOCUMENT CONTENT:\n{clean_content}")

            content_blocks_text = "\n\n".join(doc_content_sections)

            if intent == QueryIntent.DOCUMENT_METADATA_QUERY:
                docs_summary = (
                    f"### Workspace Document Repository (Document Section):\n"
                    f"- Total Documents in Workspace: {len(repo_docs)}\n"
                    f"- Document Details:\n" + "\n".join(doc_lines) + "\n\n"
                    f"CRITICAL RESPONSE DIRECTIVE:\n"
                    f"- The user is asking about the documents in their document section or workspace.\n"
                    f"- You and all autonomous agents have complete, real-time access to the Document Section and all its data.\n"
                    f"- Answer directly that there are {len(repo_docs)} document(s) in their document section, and list their names, IDs, types, and statuses clearly.\n"
                    f"- You have available tools: `list_documents`, `get_document`, `get_document_content`, `search_database_documents`.\n"
                    f"- Do NOT call `list_files` or ask the user for directory paths.\n"
                    f"- Never state that you cannot see, track, or access documents in the workspace."
                )
            else:
                docs_summary = (
                    f"### Available Database & Workspace Documents for Reference:\n"
                    f"- Total Documents Available: {len(repo_docs)}\n"
                    f"- Document Catalog:\n" + "\n".join(doc_lines) + "\n\n"
                    f"### Attached Workspace Documents & Extracted Content:\n"
                    f"{content_blocks_text if content_blocks_text else 'No text extracted yet.'}\n\n"
                    f"CRITICAL DOCUMENT REFERENCE & GENERATION DIRECTIVE:\n"
                    f"- You and all agents have full, direct visibility and read access to all uploaded documents and reference materials shown above.\n"
                    f"- Use `get_document_content` or `get_document` to fetch full unabridged text or metadata for any document by its name or ID.\n"
                    f"- When instructed to generate a PDF, report, or document based on 'same data', 'this data', or the uploaded document:\n"
                    f"  1. FIRST generate the complete, comprehensive report content (Executive Summary, Specifications, Operating Limits, Tables, Findings) directly from the extracted document content above.\n"
                    f"  2. Then fit and compile that generated content into an official PDF deliverable using `create_pdf(file_name=..., title=..., content=...)`.\n"
                    f"- Under NO circumstances should you state that you are unable to generate or ask the user to specify details when source documents are present above. Synthesize the deliverable directly from the data!"
                )
            prompt_sections.append(docs_summary)
        elif intent == QueryIntent.DOCUMENT_METADATA_QUERY or is_doc_relevant:
            prompt_sections.append(
                "### Workspace Document Repository (Document Section):\n"
                "- Total Documents in Workspace: 0 (No documents uploaded yet).\n\n"
                "CRITICAL RESPONSE DIRECTIVE:\n"
                "- The user has requested or asked about documents, but there are currently 0 documents in their workspace repository.\n"
                "- State clearly, politely, and directly that there are 0 documents uploaded or available in the workspace.\n"
                "- Inform the user that they can upload documents via the Documents section or chat attachment.\n"
                "- Under NO circumstances should you fabricate, hallucinate, or synthesize a Standard Operating Procedure (SOP), industrial manual, or fake document content."
            )

        if summary:
            prompt_sections.append(f"### Rolling Conversation Summary:\n{summary}")

        if artifacts:
            formatted_arts = artifact_store.format_artifacts_for_prompt(artifacts)
            if formatted_arts:
                prompt_sections.append(formatted_arts)
        elif intent == QueryIntent.ARTIFACT_QUERY:
            prompt_sections.append("### Generated Artifacts:\nNo files have been created yet in this conversation.")

        if executions:
            formatted_execs = execution_store.format_executions_for_prompt(executions)
            if formatted_execs:
                prompt_sections.append(formatted_execs)

        if ltm_ctx:
            prompt_sections.append(f"### Recalled Long-Term Facts & Preferences (LTM):\n{ltm_ctx}")

        if graph_ctx:
            prompt_sections.append(f"### Knowledge Graph Insights (Neo4j):\n{graph_ctx}")

        if doc_ctx:
            prompt_sections.append(
                "### Retrieved Document Evidence (RAG):\n" + doc_ctx +
                "\n\nUse this evidence when answering. Cite the source labels. Do not claim the documents say anything not present above."
            )
        elif intent == QueryIntent.DOCUMENT_RAG:
            prompt_sections.append("### Retrieved Document Evidence (RAG):\nNo sufficiently relevant document context was retrieved. State that clearly; do not invent document evidence.")

        # Add explicit instruction for conversational and memory accuracy
        prompt_sections.append(
            "IMPORTANT ACCURACY & GROUNDING INSTRUCTIONS:\n"
            "- Answer questions about previous instructions, messages, and created files truthfully using the conversation history and verified artifact records provided.\n"
            "- If the user asks what was previously asked, inspect the conversation history turns and state their previous request accurately.\n"
            "- If the user asks which files you created, refer directly to the verified artifacts above.\n"
            "- If the user refers to 'this data' or 'the report', ground your response in the immediate previous conversation turn and generated data."
        )

        final_system_prompt = "\n\n".join(prompt_sections).strip()

        # Observability metrics
        observability = {
            "conversation_id": conversation_id,
            "intent": intent.value,
            "stm_messages_count": len(history_messages),
            "artifacts_count": len(artifacts),
            "executions_count": len(executions),
            "has_summary": bool(summary),
            "has_ltm": bool(ltm_ctx),
            "has_graph": bool(graph_ctx),
            "repo_documents_count": len(repo_docs),
            "rag_chunks_count": doc_ctx.count("[Source "),
            "total_context_chars": len(final_system_prompt)
        }

        logger.info(
            f"[MEMORY] conversation_id={conversation_id} | "
            f"[STM] messages={len(history_messages)} | "
            f"[ARTIFACTS] results={len(artifacts)} | "
            f"[EXECUTIONS] results={len(executions)} | "
            f"[DOCS] repo_docs={len(repo_docs)} | "
            f"[MEM0/LTM] has_ltm={bool(ltm_ctx)} | "
            f"[NEO4J] has_graph={bool(graph_ctx)} | "
            f"[CONTEXT] assembled successfully | chars={len(final_system_prompt)}"
        )

        return EnrichedContext(
            conversation_id=conversation_id,
            user_id=user_id,
            intent=intent,
            system_prompt=final_system_prompt,
            history_messages=history_messages,
            artifacts=artifacts,
            executions=executions,
            summary=summary,
            ltm_context=ltm_ctx,
            graph_context=graph_ctx,
            document_context=doc_ctx,
            repo_documents=repo_docs,
            observability=observability
        )


# Global singleton instance
central_context_builder = ContextBuilder()
