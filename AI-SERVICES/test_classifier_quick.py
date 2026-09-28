from orchestrator.task_classifier import task_classifier

tests = [
    ("Explain what a P&ID is.", "GENERAL", "general"),
    ("Write Python code to calculate the average of a list.", "CODE_GENERATION", "code_agent"),
    ("Here is some data. Generate an Excel file.", "EXCEL_GENERATION", "spreadsheet_agent"),
    ("Create an Excel file from this dataset.", "EXCEL_GENERATION", "spreadsheet_agent"),
    ("Create a PDF inspection report from these findings.", "PDF_GENERATION", "reporting_agent"),
    ("What was the pressure recorded in Unit 4?", "DOCUMENT_QA", "document_agent"),
    ("Extract all visible text from this image.", "OCR", "ocr_agent"),
    ("Identify this industrial component.", "VISION", "vision_agent"),
    ("Extract this table into structured data.", "DOCUMENT_ANALYSIS", "document_agent"),
    ("Extract the inspection records and create an Excel sheet.", "DOCUMENT_ANALYSIS", "spreadsheet_agent")
]

passed = 0
for q, exp_type, exp_agent in tests:
    res = task_classifier.classify(q)
    matches = (res.task_type == exp_type and res.agent == exp_agent)
    if matches:
        passed += 1
    print(f"[{'PASS' if matches else 'FAIL'}] '{q[:35]}' -> type={res.task_type} (exp={exp_type}) | agent={res.agent} (exp={exp_agent}) | model={res.recommended_model}")

print(f"\nTotal: {passed}/{len(tests)} passed.")
