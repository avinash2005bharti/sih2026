import pytest
import asyncio
from tools.tool_manager import tool_manager
from core.security import validate_safe_path

def test_file_writer_and_reader():
    async def _run():
        test_filename = "test_audit_note.txt"
        test_content = "Sovereign Industrial Audit Passed: All valves nominal."

        res_write = await tool_manager.execute_tool(
            name="file_writer",
            arguments={"file_path": test_filename, "content": test_content},
            user_role="engineer"
        )
        assert res_write["status"] == "success"

        res_read = await tool_manager.execute_tool(
            name="file_reader",
            arguments={"file_path": res_write["file_path"]},
            user_role="operator"
        )
        assert res_read["status"] == "success"
        assert test_content in res_read["content"]
    asyncio.run(_run())

def test_path_traversal_prevention():
    with pytest.raises(PermissionError):
        validate_safe_path("../../windows/system32/cmd.exe")

def test_python_executor_sandboxed():
    async def _run():
        code = (
            "import numpy as np\n"
            "vals = [10.5, 20.3, 30.2]\n"
            "print(f'Calculated Mean: {np.mean(vals):.2f}')\n"
        )
        res = await tool_manager.execute_tool(
            name="python_executor",
            arguments={"code": code},
            user_role="engineer"
        )
        assert res["status"] == "success"
        assert "Calculated Mean: 20.33" in res["stdout"]
    asyncio.run(_run())

def test_tool_rejection_for_hallucinated_name():
    async def _run():
        res = await tool_manager.execute_tool(
            name="non_existent_magic_tool",
            arguments={"x": 1},
            user_role="admin"
        )
        assert res["status"] == "error"
        assert res["error"] == "TOOL_NOT_FOUND"
    asyncio.run(_run())
