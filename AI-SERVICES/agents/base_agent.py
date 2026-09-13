"""
Base agent - provides common functionality for specialized agents.
Includes prompt building, model routing, and tool execution binding.
"""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from llm.model_router import model_router
from llm.ollama_client import ollama_client
from tools.tool_manager import tool_manager
from core.logging import logger


class BaseAgent(ABC):
    """Base class for all specialized agents."""

    def __init__(self, name: str, description: str, model: Optional[str] = None, tools: Optional[List[str]] = None):
        """
        Initialize base agent.

        Args:
            name: Agent name
            description: Agent description
            model: LLM model to use (optional, uses default if not specified)
            tools: List of tool names this agent can use
        """
        self.name = name
        self.description = description
        self.model = model
        self.tools = tools or []
        self.state = {}
        self.conversation_history = []

        logger.info(f"Initialized agent: {self.name} (tools: {self.tools})")

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute the agent's main task.

        Args:
            task: Task description
            context: Optional context dict with additional info

        Returns:
            Agent response
        """
        try:
            logger.info(f"Agent {self.name} executing task: {task[:100]}")

            if context is None:
                context = {}

            prompt = self._build_prompt(task, context)
            model = self.model or self._select_model(task)
            response = await self._call_model(model, prompt)
            result = await self._process_response(response)

            self.conversation_history.append({
                "task": task,
                "response": result,
                "model": model
            })

            logger.info(f"Agent {self.name} completed task")
            return result

        except Exception as e:
            logger.error(f"Agent {self.name} execution failed: {e}", exc_info=True)
            raise

    async def execute_with_tools(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute task with tool assistance. Runs relevant tools and synthesizes output.
        """
        if context is None:
            context = {}

        tool_outputs = []
        for tool_name in self.tools:
            tool = tool_manager.get_tool(tool_name)
            if tool:
                # Provide standard workspace params
                args = context.get(f"{tool_name}_args", {})
                if not args and "file_path" in context:
                    args = {"file_path": context["file_path"]}
                try:
                    res = await tool_manager.execute_tool(tool_name, args)
                    tool_outputs.append({"tool": tool_name, "output": res})
                except Exception as te:
                    logger.warning(f"Tool {tool_name} error in {self.name}: {te}")

        # Inject tool findings into prompt context
        if tool_outputs:
            context["tool_findings"] = tool_outputs

        reasoning = await self.execute(task, context)
        return {
            "agent": self.name,
            "reasoning": reasoning,
            "tool_outputs": tool_outputs
        }

    def _build_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """Build the prompt for the model."""
        system_message = self._get_system_message()
        context_str = self._format_context(context)

        tools_desc = ""
        if self.tools:
            tools_desc = f"\n\n{tool_manager.get_tools_prompt_description(self.tools)}"

        prompt = f"""{system_message}{tools_desc}

Task: {task}

{context_str}

Please provide a detailed, factual, and actionable response."""
        return prompt

    @abstractmethod
    def _get_system_message(self) -> str:
        """Get system message for this agent type."""
        pass

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for prompt."""
        if not context:
            return ""

        lines = ["Context:"]
        for key, value in context.items():
            lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def _select_model(self, task: str) -> str:
        """Select appropriate model for task."""
        return model_router.route(task, task_type="auto")

    async def _call_model(self, model: str, prompt: str) -> str:
        """Call the LLM model."""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await ollama_client.chat(model=model, messages=messages)
            return response
        except Exception as e:
            logger.error(f"Model call failed for {model}: {e}")
            raise

    async def _process_response(self, response: str) -> str:
        """Process model response."""
        return response.strip()

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        self.state = {}
        logger.debug(f"Cleared history for agent: {self.name}")

    def get_info(self) -> Dict[str, str]:
        """Get agent information."""
        return {
            "name": self.name,
            "description": self.description,
            "model": self.model or "auto-selected",
            "tools": ", ".join(self.tools),
            "state": str(self.state)
        }

    async def stream_response(self, task: str, context: Optional[Dict[str, Any]] = None):
        """Stream response token-by-token."""
        try:
            logger.info(f"Agent {self.name} streaming response for: {task[:100]}")

            if context is None:
                context = {}

            prompt = self._build_prompt(task, context)
            model = self.model or self._select_model(task)

            async for token in ollama_client.chat_stream(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            ):
                yield token

            logger.info(f"Agent {self.name} streaming complete")

        except Exception as e:
            logger.error(f"Streaming error in {self.name}: {e}")
            raise

