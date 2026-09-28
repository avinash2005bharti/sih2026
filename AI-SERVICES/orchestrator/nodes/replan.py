from typing import Any, Dict, List
from orchestrator.state import OrchestratorState, PlanStep
from core.logging import logger

def replan_failed_steps(state: OrchestratorState) -> OrchestratorState:
    """
    Self-Correction & Re-Planning Node:
    Triggered when artifact or execution verification fails and retry limit is not exceeded.
    Diagnoses issues, resets failed steps, and injects corrective parameters.
    """
    verdict = state.validation_verdict
    state.retry_count += 1

    logger.warning(
        f"SELF-CORRECTION TRIGGERED (Attempt {state.retry_count}/{state.max_retries}) | "
        f"Issues to fix: {verdict.issues}"
    )

    # Reset any failed steps to RETRYING and clear blocking errors
    for step in state.plan:
        if step.status in ["FAILED", "BLOCKED", "VALIDATION_FAILED"]:
            step.status = "PENDING"
            step.error = None
            step.description += f" (Corrective Attempt {state.retry_count})"

    # If artifact was missing, ensure generator step is reset to PENDING
    for step in state.plan:
        if step.tool in ["pdf_creator", "xlsx_creator", "docx_creator"]:
            step.status = "PENDING"

    return state
