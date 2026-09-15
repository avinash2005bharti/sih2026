import httpx
import json
from typing import AsyncGenerator, Dict, Any, List, Optional
from core.config import settings
from core.logging import logger


class OllamaClient:
    """
    Robust local Ollama client targeting Windows host Ollama (http://localhost:11434).
    Safely handles connection errors, offline instances, timeouts, memory pressure, and vision models.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")

    @staticmethod
    def is_vision_model(model_name: str) -> bool:
        """Check if a model name indicates vision / multimodal capability."""
        name_lower = (model_name or "").lower()
        vision_indicators = ["vision", "llava", "minicpm-v", "bakllava", "vl", "qwen2.5vl", "moondream"]
        return any(ind in name_lower for ind in vision_indicators)

    async def health_check(self) -> dict:
        """Check Ollama connectivity and list available models."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                return {
                    "status": "ok",
                    "available": True,
                    "url": self.base_url,
                    "models_available": models,
                    "count": len(models)
                }
        except httpx.ConnectError:
            logger.warning(f"Ollama is unreachable at {self.base_url}. Service may not be running.")
            return {
                "status": "error",
                "available": False,
                "url": self.base_url,
                "detail": f"Ollama service is not running at {self.base_url}. Please run: ollama serve",
                "models_available": []
            }
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return {
                "status": "error",
                "available": False,
                "url": self.base_url,
                "detail": str(e),
                "models_available": []
            }

    async def get_available_models(self) -> list[str]:
        """Get list of available models installed in local Ollama."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                return [m.get("name") for m in data.get("models", []) if m.get("name")]
        except Exception as e:
            logger.warning(f"Could not fetch models from Ollama at {self.base_url}: {e}")
            return []

    async def unload_other_models(self, target_model: str):
        """CPU Guard: Unload all models except the target model to save RAM."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/ps")
                if resp.status_code == 200:
                    running_models = resp.json().get("models", [])
                    for m in running_models:
                        m_name = m.get("name")
                        if m_name and m_name != target_model:
                            logger.info(f"CPU Guard: Unloading model {m_name}")
                            # To unload, we call generate with keep_alive=0
                            await client.post(
                                f"{self.base_url}/api/generate",
                                json={"model": m_name, "keep_alive": 0}
                            )
        except Exception as e:
            logger.warning(f"CPU Guard failed: {e}")

    async def list_models_detailed(self) -> List[Dict[str, Any]]:
        """List models with metadata like size, family, and capabilities."""
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()

            models = []
            for m in data.get("models", []):
                name = m.get("name", "")
                size_bytes = m.get("size", 0)
                details = m.get("details", {})
                name_lower = name.lower()

                if self.is_vision_model(name_lower):
                    model_type = "Vision"
                    caps = ["text_generation", "image_understanding"]
                elif any(e in name_lower for e in ["embed", "nomic", "bge"]):
                    model_type = "Embedding"
                    caps = ["embeddings", "semantic_search"]
                else:
                    model_type = "LLM"
                    caps = ["text_generation"]
                    if any(c in name_lower for c in ["code", "coder", "starcoder", "deepseek-coder", "codellama"]):
                        caps.append("code_generation")

                size_str = (
                    f"{size_bytes / (1024**3):.1f} GB" if size_bytes >= 1024**3
                    else f"{size_bytes / (1024**2):.0f} MB" if size_bytes > 0
                    else "Unknown"
                )

                models.append({
                    "name": name,
                    "provider": "ollama",
                    "type": model_type,
                    "status": "Ready",
                    "size": size_str,
                    "sizeBytes": size_bytes,
                    "capabilities": caps,
                    "details": details,
                    "family": details.get("family", ""),
                    "parameterSize": details.get("parameter_size", ""),
                    "quantization": details.get("quantization_level", "")
                })
            return models
        except Exception as e:
            logger.warning(f"Error listing detailed models from Ollama: {e}")
            return []

    async def resolve_model(self, model: str, require_vision: bool = False) -> str:
        """Resolve a model name against installed models, with safe fallback."""
        available = await self.get_available_models()
        if not available:
            return model

        # If vision is required, match only vision models
        if require_vision:
            vision_models = [m for m in available if self.is_vision_model(m)]
            if vision_models:
                for m in vision_models:
                    if m == model or m.split(":")[0] == model.split(":")[0]:
                        return m
                return vision_models[0]
            return model

        # 1. Exact match or tag prefix match
        for m in available:
            if m == model or m.split(":")[0] == model.split(":")[0]:
                return m

        # 2. Fallback to first non-embedding model
        chat_models = [m for m in available if not any(emb in m.lower() for emb in ["embed", "bge", "bert"])]
        if chat_models:
            fallback = chat_models[0]
            logger.warning(f"Model '{model}' not found in Ollama. Falling back to '{fallback}'.")
            return fallback

        return model

    def _normalize_error_message(self, err_text: str, model_name: str) -> str:
        """Translate raw Ollama error strings into clear, developer-friendly messages."""
        lower = err_text.lower()
        if "does not support images" in lower or "vision" in lower:
            return "Selected model does not support vision. Please select a vision-capable Ollama model."
        if "not found" in lower or "try pulling" in lower:
            return f"Model '{model_name}' was not found in local Ollama. Please run: ollama pull {model_name}"
        if "memory" in lower or "allocate" in lower or "cuda out of memory" in lower or "ram" in lower:
            return "Model loading failed due to insufficient system resources/memory. Ensure only one model is loaded or select a smaller quantized model."
        return err_text

    async def chat(self, model: str, messages: list[dict], options: Optional[dict] = None) -> str:
        """Non-streaming chat request with automatic model resolution and vision error protection."""
        has_images = any(bool(m.get("images")) for m in messages if isinstance(m, dict))
        effective_model = await self.resolve_model(model, require_vision=has_images)

        # CPU Guard
        await self.unload_other_models(effective_model)

        # Pre-check vision capability if images are provided
        if has_images and not self.is_vision_model(effective_model):
            logger.warning(f"Attempted vision call with non-vision model: {effective_model}")
            raise ValueError("Selected model does not support vision. Please select a vision-capable Ollama model.")

        payload = {"model": effective_model, "messages": messages, "stream": False}
        if options:
            payload["options"] = options

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                if resp.status_code >= 400:
                    err_msg = resp.text
                    clean_msg = self._normalize_error_message(err_msg, effective_model)
                    raise RuntimeError(clean_msg)

                data = resp.json()
                return data.get("message", {}).get("content", "")

        except httpx.ConnectError:
            msg = f"Ollama is not running at {self.base_url}. Please run: ollama serve"
            logger.error(msg)
            raise ConnectionError(msg)
        except httpx.TimeoutException:
            msg = f"Ollama request timed out after 300 seconds for model '{effective_model}'."
            logger.error(msg)
            raise TimeoutError(msg)
        except Exception as e:
            clean_msg = self._normalize_error_message(str(e), effective_model)
            logger.error(f"Ollama chat call failed: {clean_msg}")
            raise RuntimeError(clean_msg)

    async def chat_json(self, model: str, messages: list[dict], options: Optional[dict] = None) -> dict:
        """Chat request expecting structured JSON output."""
        effective_model = await self.resolve_model(model)
        await self.unload_other_models(effective_model)
        payload = {"model": effective_model, "messages": messages, "format": "json", "stream": False}
        if options:
            payload["options"] = options
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data.get("message", {}).get("content", "{}")
                return json.loads(content)
        except json.JSONDecodeError as je:
            logger.warning(f"Ollama JSON decode failed: {je}")
            return {"error": "Invalid JSON response from model", "raw": content}
        except httpx.ConnectError:
            raise ConnectionError(f"Ollama is not running at {self.base_url}. Please run: ollama serve")
        except Exception as e:
            logger.error(f"Ollama chat_json failed: {e}")
            raise

    async def generate(self, model: str, prompt: str, system: Optional[str] = None, options: Optional[dict] = None) -> str:
        """Direct text generation from a prompt."""
        effective_model = await self.resolve_model(model)
        await self.unload_other_models(effective_model)
        payload = {"model": effective_model, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                if resp.status_code >= 400:
                    raise RuntimeError(self._normalize_error_message(resp.text, effective_model))
                data = resp.json()
                return data.get("response", "")
        except httpx.ConnectError:
            raise ConnectionError(f"Ollama is not running at {self.base_url}. Please run: ollama serve")
        except Exception as e:
            logger.error(f"Ollama generate call failed: {e}")
            raise

    async def generate_with_vision(self, model: str, prompt: str, images: list[str], options: Optional[dict] = None) -> str:
        """Dedicated helper to generate text response from an image prompt."""
        effective_model = await self.resolve_model(model, require_vision=True)
        await self.unload_other_models(effective_model)
        if not self.is_vision_model(effective_model):
            raise ValueError("Selected model does not support vision. Please select a vision-capable Ollama model.")

        messages = [
            {
                "role": "user",
                "content": prompt,
                "images": images
            }
        ]
        return await self.chat(model=effective_model, messages=messages, options=options)

    async def chat_stream(self, model: str, messages: list[dict], options: Optional[dict] = None) -> AsyncGenerator[str, None]:
        """Streaming chat request - yields individual tokens/chunks."""
        has_images = any(bool(m.get("images")) for m in messages if isinstance(m, dict))
        effective_model = await self.resolve_model(model, require_vision=has_images)
        await self.unload_other_models(effective_model)

        if has_images and not self.is_vision_model(effective_model):
            yield "Selected model does not support vision. Please select a vision-capable Ollama model."
            return

        payload = {"model": effective_model, "messages": messages, "stream": True}
        if options:
            payload["options"] = options

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                    if resp.status_code >= 400:
                        err_body = await resp.aread()
                        clean_err = self._normalize_error_message(err_body.decode(errors="ignore"), effective_model)
                        yield f"Error: {clean_err}"
                        return

                    async for line in resp.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if "error" in data:
                                    yield f"Error: {self._normalize_error_message(data['error'], effective_model)}"
                                    return
                                content = data.get("message", {}).get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse Ollama response line: {line}")
        except httpx.ConnectError:
            yield f"Error: Ollama is not running at {self.base_url}. Please run: ollama serve"
        except Exception as e:
            clean_err = self._normalize_error_message(str(e), effective_model)
            logger.error(f"Ollama streaming chat failed: {clean_err}")
            yield f"Error: {clean_err}"

    async def generate_embedding(self, model: str, text: str) -> list[float]:
        """Generate embedding for text using /api/embed or /api/embeddings."""
        await self.unload_other_models(model)
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{self.base_url}/api/embed", json={"model": model, "input": text})
                if resp.status_code == 200:
                    data = resp.json()
                    embeddings = data.get("embeddings", [])
                    if embeddings and len(embeddings) > 0:
                        return embeddings[0]

                resp = await client.post(f"{self.base_url}/api/embeddings", json={"model": model, "prompt": text})
                resp.raise_for_status()
                data = resp.json()
                return data.get("embedding", [])
        except httpx.ConnectError:
            raise ConnectionError(f"Ollama is not running at {self.base_url}. Please run: ollama serve")
        except Exception as e:
            logger.error(f"Ollama embedding call failed: {e}")
            raise

    async def pull_model(self, model_name: str) -> dict:
        """Pull a model via local Ollama API."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(600.0)) as client:
                resp = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model_name, "stream": False}
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.ConnectError:
            raise ConnectionError(f"Ollama is not running at {self.base_url}. Please run: ollama serve")
        except Exception as e:
            logger.error(f"Failed to pull model '{model_name}': {e}")
            raise


ollama_client = OllamaClient()