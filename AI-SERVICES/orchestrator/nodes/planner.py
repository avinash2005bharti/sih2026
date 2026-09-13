"""
Planner Node for Sovereign Agentic Orchestrator.
Decomposes complex industrial goals into actionable, ordered execution steps.
Uses local LLM structured JSON output with deterministic heuristic fallback.
"""

import json
from typing import List
from orchestrator.state import AgenticState, StepPlan
from llm.ollama_client import ollama_client
from core.config import settings
from core.logging import logger

PLANNER_SYSTEM_PROMPT = """You are the Sovereign Industrial Task Planner.
Break the user's objective into 1 to 4 logical sequential execution steps.
Available specialist agents:
- 'document_agent': document analysis, text search, manual inspection.
- 'maintenance_agent': equipment telemetry, failure codes, sensor diagnosis.
- 'safety_agent': OSHA hazard analysis, safety protocols, worker protection.
- 'compliance_agent': ISO standards, regulatory verification, audit checklists.
- 'risk_agent': probability/severity matrix, risk quantification, mitigations.
- 'code_agent': python script calculations, automation, data transformation.
- 'reporting_agent': synthesizing findings, creating markdown executive reports.

Available tools:
- 'read_file', 'write_file', 'list_directory', 'file_diff'
- 'execute_python'
- 'inspect_document', 'extract_document_sections'
- 'inspect_spreadsheet', 'filter_spreadsheet'
- 'search_knowledge_base'

Output strictly valid JSON with this exact schema:
{
  "plan": [
    {
      "step_number": 1,
      "title": "Short title",
      "description": "Specific action to perform",
      "target_agent": "name of specialist agent",
      "required_tools": ["tool1"],
      "expected_outcome": "what this step should produce"
    }
  ]
}"""


class PlannerNode:
    """Plans execution steps for the agentic workflow."""

    async def execute(self, state: AgenticState) -> AgenticState:
        logger.info(f"PlannerNode planning for task: {state.user_query[:80]}")
        state.status = "planning"

        model = settings.OLLAMA_CHAT_MODEL

        try:
            messages = [
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Create an execution plan for: {state.user_query}"}
            ]

            result = await ollama_client.chat_json(model=model, messages=messages)
            raw_plan = result.get("plan", [])

            if isinstance(raw_plan, list) and len(raw_plan) > 0:
                steps = []
                for idx, p in enumerate(raw_plan):
                    step = StepPlan(
                        step_number=p.get("step_number", idx + 1),
                        title=p.get("title", f"Step {idx + 1}"),
                        description=p.get("description", ""),
                        target_agent=p.get("target_agent", "general"),
                        required_tools=p.get("required_tools", []),
                        expected_outcome=p.get("expected_outcome", ""),
                        status="pending"
                    )
                    steps.append(step)
                state.plan = steps
                logger.info(f"PlannerNode generated {len(state.plan)} steps via LLM")
                return state

        except Exception as e:
            logger.warning(f"PlannerNode LLM generation failed ({e}), using deterministic heuristic fallback planner")

        # Deterministic heuristic fallback planner
        state.plan = self._fallback_plan(state.user_query)
        logger.info(f"PlannerNode generated {len(state.plan)} fallback steps")
        return state

    def _fallback_plan(self, query: str) -> List[StepPlan]:
        """Creates a reliable fallback plan when LLM is offline or busy."""
        q = query.lower()

        if any(w in q for w in ["csv", "spreadsheet", "data", "sensor", "telemetry", "vibration", "metric"]):
            return [
                StepPlan(
                    step_number=1,
                    title="Inspect Tabular Data",
                    description="Analyze spreadsheet columns, row count, and statistical distributions.",
                    target_agent="maintenance_agent",
                    required_tools=["inspect_spreadsheet", "filter_spreadsheet"],
                    expected_outcome="Summary statistics and filtered anomalies"
                ),
                StepPlan(
                    step_number=2,
                    title="Synthesize Technical Report",
                    description="Compile findings into a structured industrial diagnostic report.",
                    target_agent="reporting_agent",
                    required_tools=["write_file"],
                    expected_outcome="Final markdown report"
                )
            ]
        elif any(w in q for w in ["code", "python", "script", "calculate", "automation"]):
            return [
                StepPlan(
                    step_number=1,
                    title="Execute Computational Task",
                    description="Run Python code in the sandbox to process the requested logic.",
                    target_agent="code_agent",
                    required_tools=["execute_python"],
                    expected_outcome="Execution output and calculations"
                ),
                StepPlan(
                    step_number=2,
                    title="Verify and Format Results",
                    description="Verify execution correctness and provide formatted outcome.",
                    target_agent="reporting_agent",
                    required_tools=[],
                    expected_outcome="Verified solution"
                )
            ]
        elif any(w in q for w in ["hazard", "safety", "incident", "osha", "injury", "ppe"]):
            return [
                StepPlan(
                    step_number=1,
                    title="Assess Safety Hazards",
                    description="Identify hazards, evaluate OSHA / safety protocols, and categorize risk levels.",
                    target_agent="safety_agent",
                    required_tools=["search_knowledge_base"],
                    expected_outcome="Hazard identification and protocol mapping"
                ),
                StepPlan(
                    step_number=2,
                    title="Generate Safety Mitigation Plan",
                    description="Draft corrective actions, preventative measures, and compliance guidance.",
                    target_agent="compliance_agent",
                    required_tools=["write_file"],
                    expected_outcome="Safety action plan"
                )
            ]
        else:
            return [
                StepPlan(
                    step_number=1,
                    title="Analyze Request & Knowledge Base",
                    description="Examine the request and retrieve relevant industrial procedures or documentation.",
                    target_agent="document_agent",
                    required_tools=["search_knowledge_base", "inspect_document"],
                    expected_outcome="Relevant technical context and observations"
                ),
                StepPlan(
                    step_number=2,
                    title="Synthesize Findings",
                    description="Synthesize findings and deliver actionable recommendations.",
                    target_agent="reporting_agent",
                    required_tools=[],
                    expected_outcome="Comprehensive final answer"
                )
            ]
