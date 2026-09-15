import json
import uuid
import urllib.request

def run_tests():
    base_url = "http://127.0.0.1:8000/api/chat"
    
    print("Running tests against Sovereign AI Backend...")
    
    def make_req(payload):
        req = urllib.request.Request(base_url, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                status = resp.getcode()
                data = json.loads(resp.read().decode())
                return status, data
        except Exception as e:
            return 500, str(e)

    # TEST 1
    print("\n--- TEST 1: Create Excel only ---")
    conv_1 = uuid.uuid4().hex
    req_1 = uuid.uuid4().hex
    status, data1 = make_req({
        "message": "Create an Excel file containing a maintenance inspection report with 3 rows of dummy data.",
        "conversation_id": conv_1,
        "request_id": req_1,
        "user_id": "test_user_1",
        "model": "qwen2.5-coder:1.5b",
        "agent": "maintenance"
    })
    print(f"Status: {status}")
    if isinstance(data1, dict):
        print(f"Tools Executed: {[tc.get('tool') for tc in data1.get('tool_executions', [])]}")
        print(f"Files Generated: {[f.get('name') for f in data1.get('generated_files', [])]}")
    else:
        print(f"Error: {data1}")
        
    # TEST 2
    print("\n--- TEST 2: Create PDF only ---")
    conv_2 = uuid.uuid4().hex
    req_2 = uuid.uuid4().hex
    status, data2 = make_req({
        "message": "Create a PDF maintenance inspection report with 3 rows of dummy data.",
        "conversation_id": conv_2,
        "request_id": req_2,
        "user_id": "test_user_1",
        "model": "qwen2.5-coder:1.5b",
        "agent": "maintenance"
    })
    print(f"Status: {status}")
    if isinstance(data2, dict):
        print(f"Tools Executed: {[tc.get('tool') for tc in data2.get('tool_executions', [])]}")
        print(f"Files Generated: {[f.get('name') for f in data2.get('generated_files', [])]}")
    else:
        print(f"Error: {data2}")

    # TEST 3
    print("\n--- TEST 3: Create Excel and PDF ---")
    conv_3 = uuid.uuid4().hex
    req_3 = uuid.uuid4().hex
    status, data3 = make_req({
        "message": "Create both an Excel and PDF maintenance inspection report using the EXACT SAME data. It should have columns 'ID' and 'Status' and 2 rows.",
        "conversation_id": conv_3,
        "request_id": req_3,
        "user_id": "test_user_1",
        "model": "qwen2.5-coder:1.5b",
        "agent": "maintenance"
    })
    print(f"Status: {status}")
    if isinstance(data3, dict):
        tools_exec3 = data3.get('tool_executions', [])
        print(f"Tools Executed: {[tc.get('tool') for tc in tools_exec3]}")
        print(f"Files Generated: {[f.get('name') for f in data3.get('generated_files', [])]}")
        for tc in tools_exec3:
            print(f"Tool Args ({tc['tool']}): {tc.get('arguments', {})}")
    else:
        print(f"Error: {data3}")

    # TEST 5
    print("\n--- TEST 5: Normal chat (no tools) ---")
    conv_5 = uuid.uuid4().hex
    req_5 = uuid.uuid4().hex
    status, data5 = make_req({
        "message": "what is 2+2?",
        "conversation_id": conv_5,
        "request_id": req_5,
        "user_id": "test_user_1",
        "model": "qwen2.5-coder:1.5b",
        "agent": "auto"
    })
    print(f"Status: {status}")
    if isinstance(data5, dict):
        print(f"Tools Executed: {[tc.get('tool') for tc in data5.get('tool_executions', [])]}")
        print(f"Final Response: {data5.get('response')}")
    else:
        print(f"Error: {data5}")

    # TEST 6 & 8: Verify MongoDB Artifact Records
    print("\n--- TEST 6 & 8: Verify MongoDB Records ---")
    print("MongoDB verification skipped because pymongo is not in global env. Check backend console logs to see insertion confirmations.")

if __name__ == "__main__":
    run_tests()
