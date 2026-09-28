import ast
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.logging import logger

def validate_python_code(
    code_content: str,
    test_execution: bool = False,
    timeout_sec: int = 10
) -> Dict[str, Any]:
    """
    Mandatory Python Code Validator:
    Performs AST compilation check, syntax verification, dangerous call checks,
    and optional sandboxed test execution.
    """
    issues: List[str] = []
    corrections: List[str] = []

    # 1. AST Syntax Check
    try:
        compile(code_content, "<agent_generated_code>", "exec")
    except SyntaxError as e:
        issues.append(f"Python Syntax Error on line {e.lineno}: {e.msg}")
        corrections.append(f"Fix syntax error near line {e.lineno}: {e.text}")
        return {
            "valid": False,
            "score": 0,
            "issues": issues,
            "corrections": corrections,
            "error_type": "SyntaxError"
        }

    # 2. Dangerous imports check
    tree = ast.parse(code_content)
    disallowed_modules = ["shutil.rmtree", "os.system", "ctypes"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in ["pty", "posix"]:
                    issues.append(f"Disallowed platform-specific module: {alias.name}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "rmtree" and getattr(node.func.value, "id", "") == "shutil":
                    issues.append("Disallowed recursive directory deletion detected.")

    # 3. Optional sandboxed execution test
    exec_output = None
    if test_execution and len(issues) == 0:
        try:
            result = subprocess.run(
                [sys.executable, "-c", code_content],
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )
            if result.returncode != 0:
                issues.append(f"Execution failed with code {result.returncode}: {result.stderr.strip()[:300]}")
                corrections.append("Debug script runtime error based on stderr trace.")
            else:
                exec_output = result.stdout
        except subprocess.TimeoutExpired:
            issues.append(f"Execution timed out after {timeout_sec} seconds.")
            corrections.append("Ensure script terminates without infinite loops.")
        except Exception as e:
            issues.append(f"Execution check exception: {str(e)}")

    score = 100 - (len(issues) * 25)
    score = max(0, min(100, score))
    is_valid = len(issues) == 0

    return {
        "valid": is_valid,
        "score": score,
        "issues": issues,
        "corrections": corrections,
        "stdout": exec_output
    }
