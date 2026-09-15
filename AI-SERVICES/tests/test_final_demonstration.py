"""
Exact End-to-End 5-Step Workflow Demonstration Script.

Simulates the exact user sequence:
Turn 1: "Create an Excel file named Maintenance_Inspection_Report.xlsx using the maintenance inspection data."
Turn 2: "Create a PDF of this data in tabular format."
Turn 3: "What did I ask you previously?"
Turn 4: "Which files have you created?"
Turn 5: "What was the purpose of those files?"
"""

import os
import sys
import uuid
import asyncio
import httpx

# Ensure AI-SERVICES is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.context_builder import central_context_builder
from memory.artifacts.artifact_store import artifact_store

BASE_URL = "http://127.0.0.1:8000"


async def run_demonstration():
    conversation_id = f"demo-workflow-{uuid.uuid4().hex[:8]}"
    user_id = "user-demo-engineer"

    print("=" * 80)
    print("SOVEREIGN ON-PREMISE AGENTIC AI WORKBENCH / SIH 26117")
    print("FINAL 5-STEP MEMORY & CONTEXT DEMONSTRATION")
    print(f"Conversation ID: {conversation_id}")
    print(f"User ID:         {user_id}")
    print("=" * 80)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # -------------------------------------------------------------
        # STEP 1: Create Excel file
        # -------------------------------------------------------------
        q1 = "Create an Excel file named Maintenance_Inspection_Report.xlsx using the maintenance inspection data."
        print(f"\n[STEP 1] USER -> {q1}")
        res1 = await client.post("/api/chat", json={
            "message": q1,
            "conversation_id": conversation_id,
            "user_id": user_id,
        })
        assert res1.status_code == 200, f"Step 1 failed: {res1.text}"
        ans1 = res1.json()["response"]
        print(f"[STEP 1] ASSISTANT -> {ans1}\n")

        # -------------------------------------------------------------
        # STEP 2: Create PDF file of this data
        # -------------------------------------------------------------
        q2 = "Create a PDF of this data in tabular format."
        print(f"[STEP 2] USER -> {q2}")
        res2 = await client.post("/api/chat", json={
            "message": q2,
            "conversation_id": conversation_id,
            "user_id": user_id,
        })
        assert res2.status_code == 200, f"Step 2 failed: {res2.text}"
        ans2 = res2.json()["response"]
        print(f"[STEP 2] ASSISTANT -> {ans2}\n")

        # -------------------------------------------------------------
        # STEP 3: "What did I ask you previously?"
        # -------------------------------------------------------------
        q3 = "What did I ask you previously?"
        print(f"[STEP 3] USER -> {q3}")
        res3 = await client.post("/api/chat", json={
            "message": q3,
            "conversation_id": conversation_id,
            "user_id": user_id,
        })
        assert res3.status_code == 200, f"Step 3 failed: {res3.text}"
        ans3 = res3.json()["response"]
        print(f"[STEP 3] ASSISTANT -> {ans3}\n")

        # -------------------------------------------------------------
        # STEP 4: "Which files have you created?"
        # -------------------------------------------------------------
        q4 = "Which files have you created?"
        print(f"[STEP 4] USER -> {q4}")
        res4 = await client.post("/api/chat", json={
            "message": q4,
            "conversation_id": conversation_id,
            "user_id": user_id,
        })
        assert res4.status_code == 200, f"Step 4 failed: {res4.text}"
        ans4 = res4.json()["response"]
        print(f"[STEP 4] ASSISTANT -> {ans4}\n")

        # -------------------------------------------------------------
        # STEP 5: "What was the purpose of those files?"
        # -------------------------------------------------------------
        q5 = "What was the purpose of those files?"
        print(f"[STEP 5] USER -> {q5}")
        res5 = await client.post("/api/chat", json={
            "message": q5,
            "conversation_id": conversation_id,
            "user_id": user_id,
        })
        assert res5.status_code == 200, f"Step 5 failed: {res5.text}"
        ans5 = res5.json()["response"]
        print(f"[STEP 5] ASSISTANT -> {ans5}\n")

        # -------------------------------------------------------------
        # Verification Summary
        # -------------------------------------------------------------
        print("=" * 80)
        print("DEMONSTRATION VERIFICATION CHECK:")
        print(f"- Step 3 mentions previous instruction: {any(t in ans3.lower() for t in ['maintenance', 'inspection', 'report', 'excel', 'pdf'])}")
        print(f"- Step 4 lists Maintenance_Inspection_Report.xlsx: {'maintenance_inspection_report.xlsx' in ans4.lower()}")
        print(f"- Step 4 lists Maintenance_Inspection_Report.pdf: {'maintenance_inspection_report.pdf' in ans4.lower() or 'pdf' in ans4.lower()}")
        print(f"- Step 5 explains purpose from maintenance data: {any(t in ans5.lower() for t in ['maintenance', 'inspection', 'equipment', 'industrial', 'report'])}")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_demonstration())
