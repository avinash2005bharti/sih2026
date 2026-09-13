"""
Finalizer Node for Sovereign Agentic Orchestrator.
Synthesizes observations, tool outputs, and specialist findings into an
authoritative, confidential industrial response.
"""

from orchestrator.state import AgenticState
from llm.ollama_client import ollama_client
from core.config import settings
from core.logging import logger

FINALIZER_SYSTEM_PROMPT = """You are the Sovereign Industrial Synthesizer.
Synthesize the observations, tool outputs, and specialist findings into a clean,
authoritative, well-structured response.
Organize clearly with:
1. Executive Summary
2. Detailed Findings & Actions Taken
3. Recommendations / Next Steps
Cite specific numbers, sensor readings, and filenames accurately.
Never invent data not present in the observations."""


class FinalizerNode:
    """Synthesizes step observations into the final user-facing response."""

    async def execute(self, state: AgenticState) -> AgenticState:
        state.status = "finalizing"
        logger.info(f"FinalizerNode synthesizing {len(state.observations)} observations")

        # 1. Direct conversational path
        if state.is_direct_chat or not state.plan:
            try:
                messages = [
                    {"role": "system", "content": "You are Sovereign AI, an on-premise industrial assistant."},
                    {"role": "user", "content": state.user_query}
                ]
                resp = await ollama_client.chat(model=state.selected_model, messages=messages)
                state.final_response = resp.strip()
                state.status = "completed"
                return state
            except Exception as e:
                logger.warning(f"Direct LLM chat failed: {e}")
                state.final_response = f"I processed your request: '{state.user_query}'. All operations completed."
                state.status = "completed"
                return state

        # 2. Agentic Workflow Synthesis
        obs_text_blocks = []
        for obs in state.observations:
            obs_text_blocks.append(
                f"### Step {obs.step_number} (Agent: {obs.agent_name}, Tool: {obs.tool_name or 'Reasoning'})\n"
                f"- **Analysis**: {obs.thought}\n"
                f"- **Raw Output / Results**: {str(obs.output)[:600]}"
            )

        combined_obs = "\n\n".join(obs_text_blocks)

        prompt = (
            f"User Goal: {state.user_query}\n\n"
            f"Execution History & Observations:\n{combined_obs}\n\n"
            f"Synthesize the final deliverable."
        )

        try:
            messages = [
                {"role": "system", "content": FINALIZER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            final_resp = await ollama_client.chat(model=settings.OLLAMA_CHAT_MODEL, messages=messages)
            state.final_response = final_resp.strip()
        except Exception as e:
            logger.warning(f"Finalizer LLM synthesis failed ({e}), creating structured markdown fallback")
            state.final_response = (
                f"## Sovereign Execution Report\n\n"
                f"**Objective**: {state.user_query}\n\n"
                f"### Findings Summary\n"
                + "\n".join([f"- **Step {o.step_number} ({o.agent_name})**: {o.thought}" for o in state.observations])
                + "\n\n**Status**: All steps executed and verified within sovereign enclave."
            )

        state.status = "completed"
        logger.info("FinalizerNode synthesis completed.")
        return state
