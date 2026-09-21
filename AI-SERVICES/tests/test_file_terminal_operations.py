import os
import sys
import json
from pathlib import Path

# Set up paths
CURRENT_DIR = Path(__file__).resolve().parent
AI_SERVICES_DIR = CURRENT_DIR.parent
PROJECT_ROOT = AI_SERVICES_DIR.parent
sys.path.insert(0, str(AI_SERVICES_DIR))

from tools.agent_tools import (
    resolve_any_file_path,
    read_any_file,
    analyze_any_document,
    execute_terminal_command,
    execute_command,
    file_terminal_operations,
    read_file,
    create_file,
    patch_file,
    list_files,
    resolve_tool,
    AGENT_TOOLS,
    TOOLS_MAP
)


def run_tests():
    print("=== STARTING FILE & TERMINAL OPERATIONS TEST SUITE ===")
    failures = []

    # 1. Test Terminal Command Execution via execute_command
    print("\n--- Test 1: Direct execute_command ---")
    try:
        raw_res = execute_command.invoke({"command": "python --version"})
        res = json.loads(raw_res)
        print(f"Result: success={res.get('success')}, exit_code={res.get('exit_code')}, stdout={res.get('stdout')}")
        assert res.get("success") is True, f"Failed: {res}"
        assert "Python" in res.get("stdout") or "Python" in res.get("stderr"), f"Unexpected output: {res}"
        print("PASS: execute_command executed successfully.")
    except Exception as e:
        print(f"FAIL: execute_command: {e}")
        failures.append(f"Test 1: {e}")

    # 2. Test Terminal Action via file_terminal_operations
    print("\n--- Test 2: file_terminal_operations (action='terminal') ---")
    try:
        raw_res = file_terminal_operations.invoke({
            "action": "terminal",
            "command": "dir /b BACKEND\\uploads\\documents"
        })
        res = json.loads(raw_res)
        print(f"Result: success={res.get('success')}, stdout={res.get('stdout')[:150]}")
        assert res.get("success") is True, f"Failed: {res}"
        assert len(res.get("stdout", "")) > 0, "No output from dir command"
        print("PASS: file_terminal_operations terminal action succeeded.")
    except Exception as e:
        print(f"FAIL: file_terminal_operations terminal: {e}")
        failures.append(f"Test 2: {e}")

    # 3. Test Resolving and Reading Uploaded Document (PDF)
    print("\n--- Test 3: Reading Uploaded PDF via read_file ---")
    pdf_name = "1789822346748-589300_20250423-EB-Event-Driven_Design_for_Agents.PDF"
    try:
        raw_res = read_file.invoke({"file_path": pdf_name})
        res = json.loads(raw_res)
        print(f"Result: success={res.get('success')}, format={res.get('format')}, characters={len(res.get('content', ''))}")
        assert res.get("success") is True, f"Failed to read PDF: {res}"
        assert len(res.get("content", "")) > 100, "Extracted content is too short"
        print(f"PASS: Uploaded PDF read successfully ({len(res.get('content', ''))} characters extracted).")
    except Exception as e:
        print(f"FAIL: Reading Uploaded PDF: {e}")
        failures.append(f"Test 3: {e}")

    # 4. Test Deep Document Analysis via file_terminal_operations(action="analyze")
    print("\n--- Test 4: Document Analysis via file_terminal_operations (action='analyze') ---")
    try:
        raw_res = file_terminal_operations.invoke({
            "action": "analyze",
            "target": pdf_name,
            "query": "event-driven design agents"
        })
        res = json.loads(raw_res)
        print(f"Result: success={res.get('success')}, format={res.get('format')}, sections={len(res.get('detected_sections', []))}")
        assert res.get("success") is True, f"Failed to analyze document: {res}"
        assert len(res.get("summary_preview", "")) > 50, "Summary preview missing"
        print(f"PASS: Document analyzed successfully. Sections: {res.get('detected_sections')[:3]}")
    except Exception as e:
        print(f"FAIL: Analyzing document: {e}")
        failures.append(f"Test 4: {e}")

    # 5. Test Creating a New Deliverable File Based on Uploaded Document
    print("\n--- Test 5: Creating Markdown Deliverable via file_terminal_operations (action='write') ---")
    target_md = "reports/test_deliverable_from_doc.md"
    try:
        # First read excerpt from PDF
        read_res = json.loads(read_file.invoke({"file_path": pdf_name}))
        excerpt = read_res.get("content", "")[:300]

        content_to_write = (
            f"# Operational Implementation Guide\n\n"
            f"## Derived from: {pdf_name}\n\n"
            f"### Extracted Operational Specifications:\n"
            f"{excerpt}\n\n"
            f"### Verified Parameters:\n"
            f"- Architecture: Event-Driven Multi-Agent Framework\n"
            f"- Status: Verified and Active\n"
        )

        raw_res = file_terminal_operations.invoke({
            "action": "write",
            "target": target_md,
            "content": content_to_write
        })
        res = json.loads(raw_res)
        print(f"Result: success={res.get('success')}, file_path={res.get('file_path')}")
        assert res.get("success") is True, f"Failed to write file: {res}"
        assert Path(res.get("file_path")).exists(), "Created file does not exist on disk"
        print("PASS: New deliverable file created successfully based on uploaded document.")
    except Exception as e:
        print(f"FAIL: Creating deliverable file: {e}")
        failures.append(f"Test 5: {e}")

    # 6. Test Patching an Existing File
    print("\n--- Test 6: Patching File via file_terminal_operations (action='patch') ---")
    try:
        raw_res = file_terminal_operations.invoke({
            "action": "patch",
            "target": target_md,
            "content": "Status: Fully Approved by Sovereign Agent",
            "options": {"old_str": "Status: Verified and Active"}
        })
        res = json.loads(raw_res)
        print(f"Result: success={res.get('success')}, message={res.get('message')}")
        assert res.get("success") is True, f"Failed to patch file: {res}"

        # Verify content changed
        read_check = json.loads(read_file.invoke({"file_path": target_md}))
        assert "Fully Approved by Sovereign Agent" in read_check.get("content", ""), "Patch did not update content"
        print("PASS: File patched successfully.")
    except Exception as e:
        print(f"FAIL: Patching file: {e}")
        failures.append(f"Test 6: {e}")

    # 7. Test Creating a PDF via file_terminal_operations(action="create_pdf")
    print("\n--- Test 7: Creating PDF via file_terminal_operations (action='create_pdf') ---")
    pdf_out = "test_event_driven_sop.pdf"
    try:
        raw_res = file_terminal_operations.invoke({
            "action": "create_pdf",
            "target": pdf_out,
            "title": "Event-Driven Autonomous Agent Operating Procedure",
            "content": (
                "# 1. Purpose & Scope\n"
                "This document establishes the operational criteria for event-driven agent architectures.\n\n"
                "# 2. System Architecture & Tolerances\n"
                "Event-driven decoupling ensures deterministic telemetry processing and asynchronous tool execution.\n\n"
                "# 3. Verification Protocol\n"
                "All file and terminal operations execute within sovereign verified parameters.\n"
            ),
            "columns": ["Component", "Requirement", "Status"],
            "rows": [
                ["Message Bus", "Sub-millisecond latency", "Nominal"],
                ["Tool Execution", "Direct host sandbox execution", "Active"],
                ["Artifact Store", "Automatic persistence", "Verified"]
            ]
        })
        res = json.loads(raw_res)
        print(f"Result: success={res.get('success')}, file_path={res.get('file_path')}")
        assert res.get("success") is True, f"Failed to create PDF: {res}"
        assert Path(res.get("file_path")).exists(), "Created PDF does not exist on disk"
        print("PASS: PDF report created successfully.")
    except Exception as e:
        print(f"FAIL: Creating PDF: {e}")
        failures.append(f"Test 7: {e}")

    # 8. Test Search via file_terminal_operations (action='search')
    print("\n--- Test 8: Searching Files via file_terminal_operations (action='search') ---")
    try:
        raw_res = file_terminal_operations.invoke({
            "action": "search",
            "query": "Event-Driven"
        })
        res = json.loads(raw_res)
        print(f"Result: success={res.get('success')}, matches={res.get('matches_count')}")
        assert res.get("success") is True, f"Failed to search: {res}"
        assert res.get("matches_count", 0) > 0, "No matches found for 'Event-Driven'"
        print(f"PASS: File search succeeded with {res.get('matches_count')} matches.")
    except Exception as e:
        print(f"FAIL: Searching files: {e}")
        failures.append(f"Test 8: {e}")

    # 9. Test Tool Resolution with Aliases
    print("\n--- Test 9: Tool Resolution & Aliases ---")
    test_names = [
        "file_terminal_operations",
        "file_terminal",
        "terminal_ops",
        "file_ops",
        "terminal",
        "shell",
        "execute_command",
        "read_file",
        "create_pdf",
        "create_excel"
    ]
    for name in test_names:
        resolved = resolve_tool(name)
        assert resolved is not None, f"Failed to resolve tool '{name}'"
        print(f"Resolved '{name}' -> {resolved.name}")
    print("PASS: All tools and aliases resolved successfully.")

    print("\n" + "="*50)
    if failures:
        print(f"TEST SUITE COMPLETED WITH {len(failures)} FAILURES:")
        for f in failures:
            print(f" - {f}")
        return False
    else:
        print("ALL TESTS PASSED SUCCESSFULLY! (9/9)")
        return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
