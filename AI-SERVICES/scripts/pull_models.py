#!/usr/bin/env python3
"""
Pull Models Script for Sovereign AI Workbench.
SIH 26117

Checks which models from models.yaml are installed in local Ollama
and pulls any that are missing.

Usage:
  python scripts/pull_models.py              # Check only, print missing
  python scripts/pull_models.py --auto-pull  # Pull missing models automatically
"""

import sys
import json
import asyncio
import urllib.request
from pathlib import Path

# Add parent to sys.path so we can import project modules
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))

REQUIRED_MODELS = [
    "qwen3:0.6b",           # Router/classifier (522MB)
    "qwen3:1.7b",           # Planner (1.4GB)
    "qwen2.5:1.5b",         # General chat (986MB)
    "qwen2.5:0.5b",         # Ultra-fast fallback (397MB)
    "qwen2.5-coder:1.5b",   # Coding (986MB)
    "nomic-embed-text",     # Embeddings (274MB)
]

OPTIONAL_MODELS = [
    "qwen3-vl:4b",          # Vision GPU (3.3GB)
    "qwen2.5vl:3b",         # Vision fallback (3.2GB)
    "qwen2.5-coder:3b",     # Heavy coder GPU (1.9GB)
    "qwen3:4b",             # Complex reasoning (2.5GB)
]

OLLAMA_BASE_URL = "http://localhost:11434"


def get_installed_models() -> list[str]:
    """Query Ollama for installed models."""
    try:
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/tags",
            headers={"User-Agent": "SovereignAI/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            data = json.loads(resp.read().decode())
            return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception as e:
        print(f"❌ Cannot connect to Ollama at {OLLAMA_BASE_URL}: {e}")
        print("   Make sure Ollama is running: ollama serve")
        sys.exit(1)


def is_model_installed(model: str, installed: list[str]) -> bool:
    """Check if model is installed (with base name matching)."""
    norm = model.lower().strip()
    for inst in installed:
        inst_norm = inst.lower().strip()
        if inst_norm == norm or inst_norm.startswith(norm.split(":")[0] + ":"):
            return True
    return False


def pull_model(model: str) -> bool:
    """Pull a model using ollama CLI. Returns True if successful."""
    import subprocess
    print(f"⏳ Pulling {model}...")
    try:
        result = subprocess.run(
            ["ollama", "pull", model],
            capture_output=False,
            check=True
        )
        print(f"✅ {model} pulled successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to pull {model}: {e}")
        return False
    except FileNotFoundError:
        print("❌ 'ollama' command not found. Make sure Ollama is installed.")
        return False


def main():
    auto_pull = "--auto-pull" in sys.argv or "-y" in sys.argv

    print("\n" + "=" * 60)
    print("  Sovereign AI Workbench — Model Verification")
    print("  SIH 26117")
    print("=" * 60)
    print(f"\n  Checking Ollama at: {OLLAMA_BASE_URL}")

    installed = get_installed_models()
    print(f"\n  📦 Installed models ({len(installed)}):")
    for m in installed:
        print(f"     • {m}")

    # Check required models
    missing_required = []
    print(f"\n  🔍 Required models ({len(REQUIRED_MODELS)}):")
    for model in REQUIRED_MODELS:
        ok = is_model_installed(model, installed)
        status = "✅" if ok else "❌ MISSING"
        print(f"     {status} {model}")
        if not ok:
            missing_required.append(model)

    # Check optional models
    missing_optional = []
    print(f"\n  📋 Optional models ({len(OPTIONAL_MODELS)}):")
    for model in OPTIONAL_MODELS:
        ok = is_model_installed(model, installed)
        status = "✅" if ok else "⚠️  not installed"
        print(f"     {status} {model}")
        if not ok:
            missing_optional.append(model)

    print("\n" + "-" * 60)

    if not missing_required:
        print("\n  ✅ All required models are installed!")
    else:
        print(f"\n  ❌ Missing {len(missing_required)} required model(s):")
        for m in missing_required:
            print(f"     ollama pull {m}")

        if auto_pull:
            print("\n  ⏳ Auto-pulling missing models...")
            failed = []
            for m in missing_required:
                success = pull_model(m)
                if not success:
                    failed.append(m)
            if failed:
                print(f"\n  ❌ Failed to pull: {', '.join(failed)}")
                print("     Please run these manually:")
                for m in failed:
                    print(f"     ollama pull {m}")
            else:
                print("\n  ✅ All required models pulled successfully!")
        else:
            print("\n  Run with --auto-pull to pull missing models automatically:")
            print("     python scripts/pull_models.py --auto-pull")
            print("\n  Or pull manually:")
            for m in missing_required:
                print(f"     ollama pull {m}")

    print("\n" + "=" * 60 + "\n")
    return 0 if not missing_required else 1


if __name__ == "__main__":
    sys.exit(main())
