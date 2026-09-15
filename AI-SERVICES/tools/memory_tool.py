import json
from tools.base_tool import BaseTool
from memory.memory_manager import memory_manager
from core.logging import logger
from langchain_core.tools import tool

class SaveMemoryTool(BaseTool):
    """Saves long-term user facts and preferences to the Sovereign memory system."""
    name = "save_memory"
    description = "Save important facts or preferences about the user to long-term memory."
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "The ID of the user (can use 'system' if global)"},
            "fact": {"type": "string", "description": "The fact or preference to remember"}
        },
        "required": ["user_id", "fact"]
    }

    async def arun(self, user_id: str, fact: str, **kwargs) -> str:
        try:
            success = await memory_manager.remember(user_id=user_id, fact_or_preference=fact)
            if success:
                logger.info(f"[TOOL:save_memory] Saved fact for {user_id}: {fact}")
                return json.dumps({"success": True, "message": "Memory saved successfully."})
            return json.dumps({"success": False, "error": "Failed to save memory."})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})


@tool
async def save_memory(user_id: str, fact: str) -> str:
    """
    Save important facts or preferences about the user to long-term memory.
    Example: save_memory(user_id="alice", fact="User prefers dark mode and uses python.")
    """
    tool = SaveMemoryTool()
    return await tool.arun(user_id=user_id, fact=fact)
