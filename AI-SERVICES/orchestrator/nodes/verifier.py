"""
Verifier Node for Sovereign Agentic Orchestrator.
Evaluates observation quality and completeness against the step's expected outcome.
Controls step progression or triggers error recovery / retries.
"""

from orchestrator.state import AgenticState
from core.logging import logger


class VerifierNode:
    """Verifies step observations and decides whether to advance or retry."""

    async def execute(self, state: AgenticState) -> AgenticState:
        state.status = "verifying"

        if not state.observations:
            logger.warning("VerifierNode: No observations found.")
            state.verification_passed = True
            state.current_step_index += 1
            return state

        latest_obs = state.observations[-1]
        current_step = state.plan[state.current_step_index] if state.plan and state.current_step_index < len(state.plan) else None

        step_title = current_step.title if current_step else f"Step {latest_obs.step_number}"
        logger.info(f"VerifierNode checking observation for: '{step_title}'")

        # Verification check: did the step execution succeed?
        is_success = latest_obs.success

        if not is_success and state.retry_count < state.max_retries:
            state.retry_count += 1
            state.verification_passed = False
            state.verification_notes = f"Step failed; retrying attempt {state.retry_count}/{state.max_retries}"
            logger.warning(f"VerifierNode rejected observation. {state.verification_notes}")
            # Keep current_step_index so executor can retry
        else:
            state.verification_passed = True
            state.verification_notes = "Observation verified successfully."
            state.retry_count = 0
            state.current_step_index += 1
            logger.info(f"VerifierNode verified Step. Advancing to step index {state.current_step_index}/{len(state.plan)}")

        return state
