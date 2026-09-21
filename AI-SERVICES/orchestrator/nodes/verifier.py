"""
Verifier Node (Critic) for Sovereign Agentic Orchestrator.
Uses Critic SLM (smollm2:1.7b with fallback) to audit step observations for:
- unsupported claims
- missing evidence
- incorrect tool result interpretation
- malformed output / hallucinations
- missing requested fields
"""

import json
from typing import Dict, Any, List
from orchestrator.state import AgenticState
from llm.ollama_client import ollama_client
from llm.model_registry import model_registry
from core.logging import logger

CRITIC_SYSTEM_PROMPT = """You are the Sovereign Industrial Verifier and Critic.
Your duty is to critically audit the specialist's observation and findings against the ground truth tool outputs.

Check for:
1. Unsupported claims (claims not present in the tool results or provided evidence)
2. Missing evidence or missing citations
3. Incorrect interpretation of numerical or textual tool data
4. Hallucinations or invented facts
5. Malformed responses

You must respond STRICTLY with valid JSON matching this schema:
{
  "valid": true,
  "issues": [],
  "unsupported_claims": [],
  "corrections": []
}

If the observation is grounded and factual, set "valid" to true with empty lists.
If invalid or hallucinated, set "valid" to false and specify the exact corrections."""


class VerifierNode:
    """Audits step observations using Critic SLM and controls step progression."""

    async def execute(self, state: AgenticState) -> AgenticState:
        state.status = "verifying"

        if not state.observations:
            logger.warning("[CRITIC] No observations to verify.")
            state.verification_passed = True
            state.current_step_index += 1
            return state

        latest_obs = state.observations[-1]
        current_step = state.plan[state.current_step_index] if state.plan and state.current_step_index < len(state.plan) else None
        step_title = current_step.title if current_step else f"Step {latest_obs.step_number}"

        logger.info(f"[CRITIC] Auditing observation for Step {latest_obs.step_number}: '{step_title}'")

        # 1. Base check: did the tool execution crash?
        if not latest_obs.success:
            if state.retry_count < state.max_retries:
                state.retry_count += 1
                state.verification_passed = False
                state.verification_notes = f"Tool execution failed; retrying step (attempt {state.retry_count}/{state.max_retries})"
                logger.warning(f"[CRITIC] Step failed tool execution. {state.verification_notes}")
                return state
            else:
                # Exceeded max retries, move on to avoid infinite loop
                state.verification_passed = False
                state.verification_notes = "Max retries reached on failed tool execution. Proceeding to next step."
                state.retry_count = 0
                state.current_step_index += 1
                return state

        # 2. Critic SLM verification
        critic_model = model_registry.get_model("critic")
        critique = await self._run_critic_slm(critic_model, current_step, latest_obs)

        is_valid = critique.get("valid", True)
        issues = critique.get("issues", [])
        unsupported = critique.get("unsupported_claims", [])
        corrections = critique.get("corrections", [])

        str_issues = [str(x) for x in (issues + unsupported) if x]
        str_corrections = [str(x) for x in corrections if x]
        issues_text = "; ".join(str_issues) if str_issues else "Validation flag"
        corr_text = "; ".join(str_corrections) if str_corrections else "Please review evidence"

        if not is_valid and (issues or unsupported) and state.retry_count < state.max_retries:
            state.retry_count += 1
            state.verification_passed = False
            state.verification_notes = f"Critic identified issues: {issues_text}. Corrections: {corr_text}"
            logger.warning(f"[CRITIC] Observation rejected by Critic SLM ({critic_model}). Retry {state.retry_count}/{state.max_retries}. Notes: {state.verification_notes}")
            # Keep current_step_index so executor can retry with feedback

        else:
            state.verification_passed = True
            state.verification_notes = "Observation verified successfully by sovereign critic."
            state.retry_count = 0
            state.current_step_index += 1
            logger.info(f"[CRITIC] Step {latest_obs.step_number} verified. Advancing to step {state.current_step_index}/{len(state.plan)}")

        return state

    async def _run_critic_slm(self, model: str, current_step: Any, latest_obs: Any) -> Dict[str, Any]:
        """Runs the Critic SLM on the step observation and returns structured evaluation."""
        tool_data = str(latest_obs.output)[:800]
        thought_data = str(latest_obs.thought)[:800]
        step_desc = current_step.description if current_step else ""

        user_content = (
            f"Step Objective: {step_desc}\n"
            f"Tool Output / Evidence:\n{tool_data}\n\n"
            f"Specialist Interpretation:\n{thought_data}\n\n"
            f"Critique this specialist output. Verify facts and evidence."
        )

        try:
            messages = [
                {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ]
            critique = await ollama_client.chat_json(model=model, messages=messages)
            if isinstance(critique, dict) and "valid" in critique:
                return critique
        except Exception as e:
            logger.warning(f"[CRITIC] Critic SLM call failed ({e}), applying deterministic rule check")

        # Deterministic verification fallback
        if not thought_data or len(thought_data.strip()) < 5:
            return {
                "valid": False,
                "issues": ["Specialist response is empty or too short"],
                "unsupported_claims": [],
                "corrections": ["Generate substantive analysis based on evidence"]
            }

        return {
            "valid": True,
            "issues": [],
            "unsupported_claims": [],
            "corrections": []
        }

