"""
Sovereign Agentic Orchestrator Graph.
Coordinates the state machine lifecycle:
Router -> (Direct -> Finalizer) OR (Planner -> Loop[AgentSelector -> Executor -> Verifier] -> Finalizer)
Includes step callbacks for real-time streaming to backend & frontend.
"""

from typing import Callable, Optional, List
from orchestrator.state import AgenticState
from orchestrator.nodes.router import RouterNode
from orchestrator.nodes.planner import PlannerNode
from orchestrator.nodes.agent_selector import AgentSelectorNode
from orchestrator.nodes.executor import ExecutorNode
from orchestrator.nodes.verifier import VerifierNode
from orchestrator.nodes.finalizer import FinalizerNode
from core.logging import logger


class SovereignOrchestrator:
    """State graph orchestrating sovereign agentic workflows."""

    def __init__(self):
        self.router = RouterNode()
        self.planner = PlannerNode()
        self.agent_selector = AgentSelectorNode()
        self.executor = ExecutorNode()
        self.verifier = VerifierNode()
        self.finalizer = FinalizerNode()
        logger.info("SovereignOrchestrator initialized with complete node graph.")

    async def run(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        on_step_callback: Optional[Callable[[str, AgenticState], None]] = None
    ) -> AgenticState:
        """
        Run the complete agentic state loop on user query.

        Args:
            query: User task or prompt
            conversation_id: Optional conversation ID
            on_step_callback: Optional async or sync callable for real-time progress updates
        """
        state = AgenticState(user_query=query, conversation_id=conversation_id)
        logger.info(f"Starting orchestration for task '{state.task_id}': {query[:80]}")

        # 1. Router Node
        state = await self.router.execute(state)
        await self._notify(on_step_callback, "routing", state)

        # 2. If direct chat, jump directly to finalizer
        if state.is_direct_chat:
            logger.info("Direct chat path triggered. Skipping multi-step planning.")
            state = await self.finalizer.execute(state)
            await self._notify(on_step_callback, "completed", state)
            return state

        # 3. Planner Node
        state = await self.planner.execute(state)
        await self._notify(on_step_callback, "planned", state)

        # 4. Step Execution Loop: AgentSelector -> Executor -> Verifier
        while state.current_step_index < len(state.plan) and state.iteration < state.max_iterations:
            state.iteration += 1
            step = state.plan[state.current_step_index]

            logger.info(f"--- Iteration {state.iteration}: Executing Step {step.step_number} ('{step.title}') ---")

            # Agent Selector
            state = await self.agent_selector.execute(state)
            await self._notify(on_step_callback, f"agent_selected:{state.selected_agent}", state)

            # Executor
            state = await self.executor.execute(state)
            await self._notify(on_step_callback, f"executed_step:{step.step_number}", state)

            # Verifier
            state = await self.verifier.execute(state)
            await self._notify(on_step_callback, f"verified_step:{step.step_number}", state)

        # 5. Finalizer Node
        state = await self.finalizer.execute(state)
        await self._notify(on_step_callback, "completed", state)

        logger.info(f"Orchestration completed for task '{state.task_id}' in {state.iteration} iterations.")
        return state

    async def _notify(self, callback: Optional[Callable], event: str, state: AgenticState):
        """Invoke progress notification callback safely."""
        if not callback:
            return
        try:
            import inspect
            if inspect.iscoroutinefunction(callback):
                await callback(event, state)
            else:
                callback(event, state)
        except Exception as e:
            logger.warning(f"Error in step notification callback: {e}")


# Global orchestrator singleton
orchestrator = SovereignOrchestrator()
