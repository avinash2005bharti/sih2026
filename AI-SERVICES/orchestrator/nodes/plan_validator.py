from typing import Any, Dict, List
from orchestrator.state import OrchestratorState, PlanStep
from tools.tool_manager import tool_manager
from llm.model_registry import model_registry
from core.logging import logger

def validate_plan_dag(state: OrchestratorState) -> OrchestratorState:
    """
    Programmatic Plan Validator:
    Verifies that the plan has valid DAG dependencies, references existing tools,
    and assigns legitimate local models. Never allows hallucinated tool names.
    """
    plan = state.plan
    issues: List[str] = []

    if not plan:
        issues.append("Plan contains no steps.")
        state.plan_valid = False
        state.plan_issues = issues
        return state

    step_ids = {s.id for s in plan}
    registered_tools = set(tool_manager._tools.keys())

    for step in plan:
        # 1. Dependency checks
        for dep in step.dependencies:
            if dep not in step_ids:
                issues.append(f"Step {step.id} references non-existent dependency Step {dep}.")
            if dep >= step.id:
                issues.append(f"Step {step.id} has invalid forward or self dependency on Step {dep}.")

        # 2. Tool verification
        if step.tool:
            has_tool = (step.tool in registered_tools or tool_manager.get_tool(step.tool) is not None or step.tool == "none")
            if not has_tool:
                issues.append(f"Step {step.id} references hallucinated tool '{step.tool}'.")

        # 3. Model fallback verification
        if step.model:
            known_model = model_registry.get_model(step.model)
            if not known_model:
                # Automatically map to appropriate fallback
                step.model = "qwen3:4b"

    state.plan_valid = (len(issues) == 0)
    state.plan_issues = issues

    logger.info(f"PLAN VALIDATION | Valid: {state.plan_valid} | Steps: {len(plan)} | Issues: {issues}")
    return state

validate_plan_node = validate_plan_dag
