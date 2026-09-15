"""
Context Builder for Short-Term Memory.
Transforms raw conversation history into bounded, clean prompt context.
"""

from typing import List, Dict, Optional, Any
from memory.models import STMContext, STMMessage


class STMContextBuilder:
    """Builds prompt-ready context strings and message lists from STMContext."""

    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens

    def _get_text(self, content: Any) -> str:
        """Safely extract string content from message body."""
        if content is None:
            return ""
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, (dict, list)):
            import json
            try:
                return json.dumps(content)
            except Exception:
                return str(content).strip()
        return str(content).strip()

    def format_history_for_prompt(
        self,
        stm_context: STMContext,
        current_query: Optional[str] = None
    ) -> str:
        """
        Format recent conversation history into a structured context string.
        Excludes the latest message if it's identical to the current_query.
        """
        if not stm_context or not stm_context.messages:
            return ""

        msgs = stm_context.messages
        # If the last message is identical to current query, omit it from history
        if current_query and msgs and self._get_text(msgs[-1].content) == current_query.strip():
            msgs = msgs[:-1]

        if not msgs:
            return ""

        lines = ["### Recent Conversation Context (STM):"]
        for m in msgs:
            text = self._get_text(m.content)
            if not text:
                continue
            speaker = "User" if m.role == "user" else "Assistant"
            lines.append(f"{speaker}: {text}")

        return "\n".join(lines) if len(lines) > 1 else ""

    def format_messages_for_llm(
        self,
        stm_context: STMContext,
        current_query: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Format recent conversation into OpenAI / Ollama compatible message list.
        [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}]
        """
        if not stm_context or not stm_context.messages:
            return []

        msgs = stm_context.messages
        if current_query and msgs and self._get_text(msgs[-1].content) == current_query.strip():
            msgs = msgs[:-1]

        result = []
        for m in msgs:
            role = "user" if m.role == "user" else "assistant"
            result.append({"role": role, "content": self._get_text(m.content)})
        return result


# Global singleton instance
context_builder = STMContextBuilder()
