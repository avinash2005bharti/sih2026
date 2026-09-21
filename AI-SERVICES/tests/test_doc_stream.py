import urllib.request
import json
import sys

payload = {
    "message": "can tell me how many document i have in my document sections",
    "agent": "general",
    "model": "auto",
    "conversation_id": "test_doc_count_verification",
    "user_id": "test_user"
}

req = urllib.request.Request(
    "http://localhost:8000/api/chat/stream",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

print("[INFO] Sending request to http://localhost:8000/api/chat/stream...")
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if not line_str.startswith("data: "):
                continue
            data_str = line_str[6:].strip()
            if not data_str or data_str == "[DONE]":
                break
            try:
                data = json.loads(data_str)
                if "token" in data:
                    print(data["token"], end="", flush=True)
                elif "content" in data:
                    print(data["content"], end="", flush=True)
                elif "final_response" in data:
                    print(f"\n[FINAL RESPONSE]:\n{data['final_response']}")
                elif "response" in data:
                    print(f"\n[RESPONSE]:\n{data['response']}")
                elif "event" in data:
                    print(f"\n[EVENT]: {data['event']} (details: {data.get('status', data.get('stage', ''))})")
            except Exception as pe:
                pass
    print("\n[DONE] Stream completed.")
except Exception as e:
    print(f"\n[ERROR]: {e}")
    sys.exit(1)
