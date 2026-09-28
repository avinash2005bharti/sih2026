import asyncio
import base64
import httpx
from pathlib import Path

async def test():
    img_path = Path("..") / "COMPARE TABLE.jpeg"
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    payload = {
        "model": "qwen2.5vl:3b",
        "messages": [
            {
                "role": "user",
                "content": "Describe what is in this image.",
                "images": [img_b64]
            }
        ],
        "stream": False,
    }
    
    print("Sending raw request to Ollama /api/chat...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post("http://127.0.0.1:11434/api/chat", json=payload)
        print("Status code:", resp.status_code)
        print("Response JSON keys:", resp.json().keys())
        print("Response JSON:", resp.json())

if __name__ == "__main__":
    asyncio.run(test())
