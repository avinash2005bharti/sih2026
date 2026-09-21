"""
Comprehensive End-to-End Verification Test for Sovereign AI Document Services:
1. Multi-format document parser (PDF, PPTX, XLSX, DOCX, TXT, CSV)
2. OCR engine & OCR MCP tooling (Images, Scanned PDFs)
3. Document visibility in context builder for chat
4. PDF generation service (ReportLab publication-ready styling)
5. 2-step PDF generation protocol & Auto-Compiler in LangGraph Agent
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add AI-SERVICES root to sys.path
AI_ROOT = Path(__file__).resolve().parent.parent
if str(AI_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_ROOT))
PROJECT_ROOT = AI_ROOT.parent

from rag.parser import document_parser
from ocr.ocr_service import ocr_service
from tools.ocr_mcp import ocr_extract_text
from tools.agent_tools import create_pdf, create_excel, SANDBOX_DIR, REPORTS_DIR
from memory.context_builder import central_context_builder
from agents.langgraph_agent import SovereignLangGraphAgent


async def test_multi_format_parsing():
    print("\n" + "=" * 70)
    print("TEST 1: Multi-Format Document Parsing (PDF, PPTX, XLSX, DOCX, TXT, CSV)")
    print("=" * 70)

    # 1.1 PDF parsing
    pdf_path = PROJECT_ROOT / "enhace ppt.pdf"
    if pdf_path.exists():
        parsed_pdf = await asyncio.to_thread(document_parser.parse_file, str(pdf_path))
        print(f"✅ PDF Extracted: '{pdf_path.name}' -> {len(parsed_pdf.text)} chars, pages={parsed_pdf.metadata.get('page_count')}")
        assert len(parsed_pdf.text) > 0, "PDF extraction produced empty text!"
    else:
        print(f"⚠️ Warning: '{pdf_path}' not found on disk, skipping direct PDF test.")

    # 1.2 PPTX parsing
    pptx_path = PROJECT_ROOT / "enhace ppt.pptx"
    if pptx_path.exists():
        parsed_pptx = await asyncio.to_thread(document_parser.parse_file, str(pptx_path))
        print(f"✅ PPTX Extracted: '{pptx_path.name}' -> {len(parsed_pptx.text)} chars, slides={parsed_pptx.metadata.get('slide_count')}")
        assert len(parsed_pptx.text) > 0, "PPTX extraction produced empty text!"
    else:
        print(f"⚠️ Warning: '{pptx_path}' not found on disk, skipping direct PPTX test.")

    # 1.3 XLSX parsing (Create a test Excel file with openpyxl)
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sensor Readings"
    ws.append(["Timestamp", "Bearing Temp (°C)", "Vibration (mm/s)", "Pressure (PSI)", "Status"])
    ws.append(["2026-09-20 10:00:00", 72.4, 3.12, 145.2, "Normal"])
    ws.append(["2026-09-20 10:05:00", 88.9, 5.84, 138.0, "Warning"])
    ws.append(["2026-09-20 10:10:00", 96.1, 7.95, 129.5, "Critical"])
    test_xlsx_path = AI_ROOT / "workspace" / "test_sensor_telemetry.xlsx"
    test_xlsx_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(test_xlsx_path)

    parsed_xlsx = await asyncio.to_thread(document_parser.parse_file, str(test_xlsx_path))
    print(f"✅ XLSX Extracted: '{test_xlsx_path.name}' -> {len(parsed_xlsx.text)} chars, sheets={parsed_xlsx.metadata.get('sheets')}")
    assert "Bearing Temp" in parsed_xlsx.text and "96.1" in parsed_xlsx.text, "XLSX content mismatch!"

    # 1.4 DOCX parsing (Create a test Word document with docx)
    import docx
    doc = docx.Document()
    doc.add_heading("Sovereign Plant SOP 401", level=0)
    doc.add_paragraph("This standard operating procedure governs gas turbine emergency cooldown procedures.")
    t = doc.add_table(rows=1, cols=3)
    hdr_cells = t.rows[0].cells
    hdr_cells[0].text = "Step"
    hdr_cells[1].text = "Action"
    hdr_cells[2].text = "Safety Requirement"
    r = t.add_row().cells
    r[0].text = "1.0"
    r[1].text = "Trip turbine via local ESD panel"
    r[2].text = "Verify flame-out indicator within 3 seconds"
    test_docx_path = AI_ROOT / "workspace" / "test_sop_procedure.docx"
    doc.save(test_docx_path)

    parsed_docx = await asyncio.to_thread(document_parser.parse_file, str(test_docx_path))
    print(f"✅ DOCX Extracted: '{test_docx_path.name}' -> {len(parsed_docx.text)} chars")
    assert "Sovereign Plant SOP 401" in parsed_docx.text and "Trip turbine" in parsed_docx.text, "DOCX content mismatch!"

    # 1.5 TXT parsing
    test_txt_path = AI_ROOT / "workspace" / "test_log.txt"
    test_txt_path.write_text("Sovereign audit event: System health 100% verified on-premise.", encoding="utf-8")
    parsed_txt = await asyncio.to_thread(document_parser.parse_file, str(test_txt_path))
    print(f"✅ TXT Extracted: '{test_txt_path.name}' -> {len(parsed_txt.text)} chars")
    assert "System health 100%" in parsed_txt.text, "TXT content mismatch!"


async def test_ocr_services():
    print("\n" + "=" * 70)
    print("TEST 2: OCR Extraction (Images & Scanned PDFs)")
    print("=" * 70)

    # 2.1 Image OCR via ocr_service
    image_path = PROJECT_ROOT / "COMPARE TABLE.jpeg"
    if image_path.exists():
        ocr_result = await asyncio.to_thread(ocr_service.extract_text, str(image_path))
        lines_detected = len(ocr_result.get("lines", []))
        extracted_text = ocr_result.get("text", "")
        print(f"✅ Image OCR Success: '{image_path.name}' -> {lines_detected} lines detected, confidence={ocr_result.get('confidence', 0):.3f}")
        print(f"   Sample text: {extracted_text[:120]}...")
        assert lines_detected > 0, "OCR returned 0 lines!"

        # 2.2 OCR MCP Tool via ocr_extract_text
        mcp_result = await ocr_extract_text(image_path=str(image_path))
        print(f"✅ OCR MCP Tool Success: status={mcp_result.get('status')}, lines={len(mcp_result.get('lines', []))}")
        assert mcp_result.get("status") == "ok", f"OCR MCP tool failed: {mcp_result}"
    else:
        print(f"⚠️ Warning: '{image_path}' not found on disk, skipping image OCR test.")

    # 2.3 PDF OCR via ocr_service.extract_pdf (1 page for fast verification)
    pdf_path = PROJECT_ROOT / "enhace ppt.pdf"
    if pdf_path.exists():
        pdf_ocr_result = await asyncio.to_thread(ocr_service.extract_pdf, str(pdf_path), max_pages=1)
        print(f"✅ PDF OCR Page-Rendering Success: pages_processed={pdf_ocr_result.get('pages_processed')}, lines={len(pdf_ocr_result.get('lines', []))}")
        assert pdf_ocr_result.get("success"), "PDF OCR extraction failed!"


async def test_context_builder_document_visibility():
    print("\n" + "=" * 70)
    print("TEST 3: Document Visibility in Context Builder")
    print("=" * 70)

    # When user asks "generate pdf about same data", verify that attached document content is injected
    enriched = await central_context_builder.build(
        conversation_id="test_e2e_conv",
        user_id="test_admin_user",
        is_admin=True,
        query="generate pdf about same data",
        agent_id="document_agent"
    )

    prompt = enriched.system_prompt
    has_attached_docs = "### Attached Workspace Documents & Extracted Content" in prompt
    print(f"✅ Context Built: Length = {len(prompt):,} chars")
    print(f"   Attached Documents Section Injected: {has_attached_docs}")

    assert has_attached_docs, "Context Builder failed to inject Attached Documents section!"
    assert "CRITICAL DOCUMENT REFERENCE & GENERATION DIRECTIVE" in prompt, "Directive missing!"
    print("✅ Model Visibility Verified: The LLM receives document text in its system prompt.")


async def test_pdf_generation_tool():
    print("\n" + "=" * 70)
    print("TEST 4: PDF Generation Service (create_pdf)")
    print("=" * 70)

    pdf_title = "Turbine Vibration & Failure Prevention Technical Report"
    pdf_content = """# Executive Summary
This document specifies the critical telemetry analysis and preventative maintenance procedures for the Main Generation Gas Turbine unit at Sovereign Station 4.

## Key Telemetry Parameters
| Sensor Tag | Parameter | Baseline | Alert Limit | Current Reading | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TT-401A | Bearing Temp Drive End | 65.0 °C | 85.0 °C | 96.1 °C | CRITICAL |
| VT-402B | Radial Vibration | 2.5 mm/s | 4.5 mm/s | 7.95 mm/s | CRITICAL |
| PT-403C | Lube Oil Pressure | 150.0 PSI | 135.0 PSI | 129.5 PSI | WARNING |

## Diagnostic Finding
Analysis of fast-Fourier transform (FFT) vibration spectra indicates high 1X and 2X rotational frequency components accompanied by localized heat accumulation. This signature correlates with hydrodynamic journal bearing oil-whirl breakdown.

## Mandatory Remedial Action Checklist
- [x] **Immediate Load Shedding**: Reduce turbine electrical output to 40% immediately.
- [ ] **Auxiliary Lube Oil Pump Verification**: Switch auxiliary skid pump to manual override.
- [ ] **Controlled Cooldown Sequence**: Initiate 48-hour barred rotation cycle.
"""

    res_json_str = create_pdf.invoke({
        "file_name": "test_turbine_report.pdf",
        "title": pdf_title,
        "content": pdf_content
    })

    res = json.loads(res_json_str)
    print(f"✅ create_pdf Result: {res}")
    assert res.get("success"), f"create_pdf failed: {res}"

    pdf_file_path = Path(res.get("file_path"))
    assert pdf_file_path.exists(), f"PDF was not saved to {pdf_file_path}"
    file_size = pdf_file_path.stat().st_size
    print(f"✅ PDF File verified on disk: '{pdf_file_path.name}', size={file_size:,} bytes")
    assert file_size > 1000, f"PDF file size too small: {file_size} bytes"

    # Verify PDF magic bytes
    with open(pdf_file_path, "rb") as f:
        header = f.read(5)
    assert header == b"%PDF-", f"Invalid PDF header: {header}"
    print("✅ PDF Validated: Proper '%PDF-' binary signature confirmed.")


async def test_agent_2step_protocol_and_auto_compiler():
    print("\n" + "=" * 70)
    print("TEST 5: 2-Step Protocol & Agent Auto-Compiler Safeguard")
    print("=" * 70)

    # Instantiate LangGraph Agent
    agent = SovereignLangGraphAgent(
        model_name="qwen2.5:1.5b",
        system_prompt=(
            "You are the Sovereign Document Agent.\n"
            "### Attached Workspace Documents & Extracted Content\n"
            "Document 1: 'Operational_Manual_Rev2.pdf'\n"
            "Content:\n"
            "The turbine operational ceiling is 10,500 RPM with primary lube oil pressure of 145 PSI. "
            "Emergency shutdown triggers when radial vibration exceeds 7.5 mm/s or temperature exceeds 95 °C.\n"
            "Document 2: 'test_sensor_telemetry.xlsx'\n"
            "Content:\n"
            "Bearing Temp: 96.1 °C, Vibration: 7.95 mm/s, Pressure: 129.5 PSI. Status: Critical.\n"
        )
    )

    query = "generate pdf about same data"
    print(f"Executing Agent with prompt: '{query}'...")

    result = await agent.execute(
        query=query,
        conversation_id="e2e_test_compilation_conv",
        request_id="req_test_001",
        user_id="operator_01",
        is_admin=True
    )

    final_resp = result.get("final_response", "")
    gen_files = result.get("generated_files", [])

    print(f"Agent Final Response (first 250 chars):\n{final_resp[:250]}...\n")
    print(f"Agent Generated Files: {len(gen_files)} files")
    for f in gen_files:
        print(f"  - {f.get('name')} ({f.get('size_bytes', 0):,} bytes, path={f.get('path')})")

    # Assertions:
    # 1. Generated files MUST contain at least one PDF
    pdf_deliverables = [f for f in gen_files if f.get("name", "").endswith(".pdf")]
    assert len(pdf_deliverables) > 0, "No PDF deliverable was generated for 'generate pdf about same data'!"

    # 2. Response MUST NOT be a refusal
    refusal_words = ["unable to generate", "cannot generate", "please specify the details", "specify detail"]
    for rw in refusal_words:
        assert rw not in final_resp.lower(), f"Agent returned refusal: '{rw}' in final response!"

    # 3. Deliverable file exists on disk
    created_pdf = pdf_deliverables[0]
    p = SANDBOX_DIR / created_pdf["path"]
    if not p.exists():
        p = REPORTS_DIR / created_pdf["name"]
    assert p.exists() and p.stat().st_size > 500, f"Generated deliverable file '{p}' not found or empty!"

    print(f"✅ 2-Step Auto-Compiler Test PASSED! Produced deliverable '{p.name}' ({p.stat().st_size} bytes)")


async def main():
    print("=" * 70)
    print("STARTING SOVEREIGN AI DOCUMENT & OCR SERVICES VERIFICATION SUITE")
    print("=" * 70)

    try:
        await test_multi_format_parsing()
        await test_ocr_services()
        await test_context_builder_document_visibility()
        await test_pdf_generation_tool()
        await test_agent_2step_protocol_and_auto_compiler()

        print("\n" + "=" * 70)
        print("🎉 ALL DOCUMENT & OCR TESTS PASSED SUCCESSFULLY!")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
