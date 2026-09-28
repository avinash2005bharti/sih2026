import asyncio
import base64
from pathlib import Path
from llm.ollama_client import ollama_client

async def test():
    img_path = Path("..") / "COMPARE TABLE.jpeg"
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    print("Testing qwen2.5vl:3b on COMPARE TABLE.jpeg...")
    try:
        res = await asyncio.wait_for(
            ollama_client.chat(
                model="qwen2.5vl:3b",
                messages=[{"role": "user", "content": "Extract all text and tabular data from this image verbatim.", "images": [img_b64]}],
                options={"num_predict": 256}
            ),
            timeout=40.0
        )
        print("qwen2.5vl:3b Result len:", len(res))
        print("qwen2.5vl:3b Result:", res[:400])
    except Exception as e:
        print("Error with qwen2.5vl:3b:", e)

if __name__ == "__main__":
    asyncio.run(test())
