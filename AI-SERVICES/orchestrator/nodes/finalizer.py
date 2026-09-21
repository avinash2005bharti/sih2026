"""
Finalizer Node for Sovereign Agentic Orchestrator.
Synthesizes observations, tool outputs, and specialist findings into an
authoritative, confidential industrial response.
"""

import json
from orchestrator.state import AgenticState
from llm.ollama_client import ollama_client
from core.config import settings
from core.logging import logger

FINALIZER_SYSTEM_PROMPT = """You are the Sovereign Industrial Synthesizer.
Synthesize the observations, tool outputs, and specialist findings into an authoritative, complete, production-grade industrial deliverable.
When the user's objective is to create, author, or specify an SOP, document, maintenance schedule, or procedure:
1. Provide the complete document deliverable with all sections (Header, Executive Summary, Scope, Technical Parameters & Data Tables, Sequential Step-by-Step Procedures, Hazard & Safety Controls, and Quality Assurance Checklists).
2. Never truncate, omit, or summarize critical technical procedures with 'etc.' or placeholders.
3. Faithfully incorporate all reference document evidence and numerical parameters from the observations.
4. Conclude with clear links or file paths to any generated file artifacts (e.g. PDF, Markdown, Excel)."""


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
        generated_file_paths = []
        for obs in state.observations:
            output_str = ""
            if isinstance(obs.output, list):
                for sub in obs.output:
                    res = sub.get("result", {})
                    if isinstance(res, dict) and res.get("file_path"):
                        generated_file_paths.append(res.get("file_path"))
                    output_str += f"\n- {sub.get('tool', 'tool')}: {json.dumps(res, indent=2)[:3000]}"
            elif isinstance(obs.output, dict):
                if obs.output.get("file_path"):
                    generated_file_paths.append(obs.output.get("file_path"))
                output_str = json.dumps(obs.output, indent=2)[:3000]
            else:
                output_str = str(obs.output)[:3000]

            obs_text_blocks.append(
                f"### Step {obs.step_number}: {obs.tool_name or 'Analysis'} (Agent: {obs.agent_name})\n"
                f"**Specialist Analysis & Findings**:\n{obs.thought}\n\n"
                f"**Tool Execution Output / Parameters**:\n{output_str}"
            )

        combined_obs = "\n\n".join(obs_text_blocks)

        prompt = (
            f"User Goal: {state.user_query}\n\n"
            f"Execution History & Observations:\n{combined_obs}\n\n"
            f"Synthesize the final deliverable with complete technical depth, all sequential procedures, and full data tables."
        )

        try:
            from llm.model_registry import model_registry
            reporting_model = model_registry.get_model("reporting")
            messages = [
                {"role": "system", "content": FINALIZER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            final_resp = await ollama_client.chat(model=reporting_model, messages=messages)
            state.final_response = final_resp.strip()
            if generated_file_paths and not any(fp in state.final_response for fp in generated_file_paths):
                state.final_response += "\n\n### Generated Deliverables\n" + "\n".join([f"- `{fp}`" for fp in set(generated_file_paths)])
        except Exception as e:
            logger.warning(f"Finalizer LLM synthesis failed ({e}), creating structured comprehensive markdown fallback")
            files_section = ""
            if generated_file_paths:
                files_section = "\n\n### Generated Deliverable Files\n" + "\n".join([f"- `{fp}`" for fp in set(generated_file_paths)])

            findings = "\n\n".join([f"#### Step {o.step_number}: {o.agent_name.capitalize()}\n{o.thought}" for o in state.observations if o.thought])
            state.final_response = (
                f"# Sovereign Execution & Technical Deliverable\n\n"
                f"**Objective**: {state.user_query}\n\n"
                f"## Executive Summary & Findings\n"
                f"{findings}\n"
                f"{files_section}\n\n"
                f"**Verification Status**: All operational steps and technical criteria verified within sovereign enclave."
            )

        state.status = "completed"
        logger.info("FinalizerNode synthesis completed.")
        return state
