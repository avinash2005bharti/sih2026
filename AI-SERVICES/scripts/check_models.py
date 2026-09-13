"""
Startup script to verify and pull required local Ollama models for Sovereign AI Workbench.
Checks availability of:
- qwen2.5-coder:3b (code generation & execution)
- nomic-embed-text:latest (vector embeddings for Qdrant & Mem0)
- qwen2.5:3b (general reasoning / orchestration)
- qwen2.5vl:3b (vision-language / multimodal)
"""

import sys
import json
import httpx
from typing import List, Dict, Any

OLLAMA_BASE_URL = "http://localhost:11434"

REQUIRED_MODELS = [
    {"name": "qwen2.5-coder:3b", "role": "Code Generation & Execution", "required": True},
    {"name": "nomic-embed-text:latest", "role": "Text Embeddings (Qdrant & Mem0)", "required": True},
    {"name": "qwen2.5:3b", "role": "General Reasoning & Orchestration", "required": False},
    {"name": "qwen2.5vl:3b", "role": "Vision & Multimodal Analysis", "required": False},
]


def check_ollama_reachable(base_url: str = OLLAMA_BASE_URL) -> bool:
    """Confirm Ollama HTTP service is reachable."""
    try:
        r = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        return r.status_code == 200
    except Exception as e:
        print(f"[FATAL] Cannot reach Ollama service at {base_url}: {e}", file=sys.stderr)
        return False


def get_available_models(base_url: str = OLLAMA_BASE_URL) -> Dict[str, Any]:
    """Fetch all locally installed models from Ollama."""
    try:
        r = httpx.get(f"{base_url}/api/tags", timeout=10.0)
        if r.status_code != 200:
            return {}
        data = r.json()
        models = data.get("models", [])
        return {m["name"]: m for m in models}
    except Exception as e:
        print(f"[ERROR] Failed to fetch models list from Ollama: {e}", file=sys.stderr)
        return {}


def pull_model(model_name: str, base_url: str = OLLAMA_BASE_URL) -> bool:
    """Pull model via Ollama HTTP API with progress logging."""
    print(f"\n[INFO] Pulling model '{model_name}' from Ollama registry...")
    try:
        with httpx.Client(timeout=600.0) as client:
            with client.stream("POST", f"{base_url}/api/pull", json={"name": model_name}) as response:
                if response.status_code != 200:
                    print(f"[ERROR] Pull failed for '{model_name}' with status {response.status_code}", file=sys.stderr)
                    return False

                last_status = ""
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        status = chunk.get("status", "")
                        completed = chunk.get("completed")
                        total = chunk.get("total")
                        if total and completed:
                            pct = (completed / total) * 100
                            print(f"\r[PULL: {model_name}] {status} - {pct:.1f}%", end="", flush=True)
                        elif status != last_status:
                            print(f"\n[PULL: {model_name}] {status}")
                            last_status = status
                    except Exception:
                        pass
        print(f"\n[SUCCESS] Model '{model_name}' pulled successfully.")
        return True
    except Exception as e:
        print(f"\n[ERROR] Exception pulling '{model_name}': {e}", file=sys.stderr)
        return False


def main():
    print("=" * 60)
    print("Sovereign AI Workbench — Local Model Availability Check")
    print("=" * 60)

    if not check_ollama_reachable():
        print("[FATAL] Ollama service unreachable. Exiting with error code 1.", file=sys.stderr)
        sys.exit(1)

    installed = get_available_models()
    print(f"[INFO] Currently installed models in Ollama: {list(installed.keys())}\n")

    failed_required = []

    for req in REQUIRED_MODELS:
        m_name = req["name"]
        is_installed = any(m_name in k or k.startswith(m_name.split(":")[0]) for k in installed.keys())

        if is_installed:
            print(f"[OK] {m_name:<25} ({req['role']}) is ready.")
        else:
            print(f"[MISSING] {m_name:<25} ({req['role']})")
            if req["required"]:
                print(f"[INFO] Attempting auto-pull for required model '{m_name}'...")
                success = pull_model(m_name)
                if not success:
                    failed_required.append(m_name)
            else:
                print(f"[INFO] Optional model '{m_name}' not installed. Continuing...")

    if failed_required:
        print(f"\n[FATAL] Failed to pull required models: {failed_required}", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] All required local models verified and ready for Sovereign Mode.")
    print("=" * 60)


if __name__ == "__main__":
    main()
