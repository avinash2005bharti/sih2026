"""
Sovereign Coding Workflow.
Dedicated pipeline for code generation, bug fixing, test writing, and sandbox execution.
Routes directly to qwen2.5-coder:3b, executes code via execution_runner, and formats output.
"""

import time
import re
from typing import Any, Dict, Optional, List
from llm.ollama_client import ollama_client
from workflows.execution import execution_runner
from core.logging import logger

CODE_MODEL = "qwen2.5-coder:3b"

SYSTEM_PROMPT = """You are a Sovereign Coding Specialist.
You generate robust, fully functional, production-ready code with complete syntax and explanations.
Always enclose code in properly tagged markdown code fences (e.g. ```python, ```cpp, ```javascript, ```bash).
Never truncate code or output unfinished snippets.
"""


class CodingWorkflow:
    """Handles code generation, explanation, and optional sandbox execution."""

    def __init__(self, model_name: str = CODE_MODEL):
        self.model_name = model_name

    def extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Extract code snippets and languages from markdown blocks."""
        matches = re.findall(r"```([a-zA-Z0-9_-]*)\n([\s\S]*?)```", text)
        blocks = []
        for lang, code in matches:
            blocks.append({
                "language": (lang or "python").lower().strip(),
                "code": code.strip()
            })
        return blocks

    async def run(
        self,
        prompt: str,
        execute_code: bool = True,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate code using the specialized coding model and optionally verify in sandbox."""
        start_time = time.time()
        logger.info(f"[CODING_WORKFLOW] Processing request with model {self.model_name}...")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        options = {
            "temperature": temperature,
            "num_predict": max(max_tokens, 2048)
        }

        # 1. Generate code via local LLM
        generated_text = await ollama_client.chat(
            model=self.model_name,
            messages=messages,
            options=options
        )

        code_blocks = self.extract_code_blocks(generated_text)
        tool_executions = []

        # 2. If execution is requested and python code is present, execute first python block in sandbox
        if execute_code and code_blocks:
            python_blocks = [b for b in code_blocks if b["language"] in ["python", "py"]]
            if python_blocks:
                first_code = python_blocks[0]["code"]
                exec_res = await execution_runner.execute_python_code(first_code)
                tool_executions.append({
                    "tool": "execute_python",
                    "arguments": {"code": first_code[:120] + "..."},
                    "stdout": exec_res.stdout,
                    "stderr": exec_res.stderr,
                    "exit_code": exec_res.exit_code,
                    "duration_seconds": exec_res.duration_seconds,
                    "success": exec_res.success
                })

        duration = round(time.time() - start_time, 3)
        return {
            "success": True,
            "model_used": self.model_name,
            "final_response": generated_text,
            "code_blocks": code_blocks,
            "tool_executions": tool_executions,
            "duration_seconds": duration
        }


# Global singleton workflow
coding_workflow = CodingWorkflow()
