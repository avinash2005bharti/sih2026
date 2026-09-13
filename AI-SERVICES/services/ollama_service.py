"""
Unified Ollama service for AI-SERVICES.
Provides high-level helpers with try/catch error wrapping.
"""

from typing import Any, Dict, List, Optional
from llm.ollama_client import ollama_client
from core.logging import logger


async def check_ollama_health() -> Dict[str, Any]:
    """Check whether local Ollama is reachable and return model status."""
    return await ollama_client.health_check()


async def list_models() -> List[Dict[str, Any]]:
    """List all models installed in local Ollama."""
    return await ollama_client.list_models_detailed()


async def generate(
    model: str,
    prompt: str,
    system: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> str:
    """Generate text from a prompt."""
    return await ollama_client.generate(model=model, prompt=prompt, system=system, options=options)


async def chat(
    model: str,
    messages: List[Dict[str, Any]],
    options: Optional[Dict[str, Any]] = None
) -> str:
    """Chat with an Ollama model."""
    return await ollama_client.chat(model=model, messages=messages, options=options)


async def generate_with_vision(
    model: str,
    prompt: str,
    images: List[str],
    options: Optional[Dict[str, Any]] = None
) -> str:
    """Send image(s) to a vision-capable Ollama model."""
    return await ollama_client.generate_with_vision(
        model=model,
        prompt=prompt,
        images=images,
        options=options
    )


async def pull_model(model_name: str) -> Dict[str, Any]:
    """Pull a model into local Ollama."""
    return await ollama_client.pull_model(model_name)
