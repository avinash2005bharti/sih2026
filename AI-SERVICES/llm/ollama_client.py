"""
Ollama Client - CPU ONLY
Sovereign On-Premise Agentic AI Workbench

Purpose:
- Communicate with local Ollama running on Windows
- CPU-only inference
- No cloud APIs
- No GPU-specific logic
- Supports:
    * Text generation
    * Chat
    * Streaming
    * Vision
    * JSON generation
    * Embeddings
    * Model health/status
    * Model pulling

Current recommended local models:

General:
    qwen2.5:1.5b

Coding / Tool Planning:
    qwen2.5-coder:1.5b

Vision:
    moondream:latest

Embeddings:
    nomic-embed-text:latest
"""

import json
from typing import AsyncGenerator, Dict, Any, List, Optional

import httpx

from core.config import settings
from core.logging import logger


class OllamaClient:
    """
    CPU-only Ollama client.

    Important:
    This class ONLY communicates with Ollama.

    It does NOT:
        - decide which agent to use
        - execute filesystem tools
        - create files
        - create folders
        - perform RAG
        - manage Mem0
        - manage Qdrant
        - manage Neo4j
        - perform agent planning

    Those responsibilities belong to the Agent Orchestrator.
    """

    GENERAL_MODEL = "qwen2.5:1.5b"
    CODING_MODEL = "qwen2.5-coder:1.5b"
    VISION_MODEL = "moondream:latest"
    EMBEDDING_MODEL = "nomic-embed-text:latest"

    EMBEDDING_MODEL_NAMES = {
        "nomic-embed-text",
        "nomic-embed-text:latest",
    }

    VISION_MODEL_NAMES = {
        "moondream",
        "moondream:latest",
        "qwen2.5vl",
        "qwen2.5vl:latest",
    }

    def __init__(self, base_url: Optional[str] = None):
        configured_url = base_url or settings.OLLAMA_BASE_URL

        self.base_url = configured_url.rstrip("/")

        # CPU-only configuration.
        #
        # Ollama uses the OLLAMA_NUM_GPU environment variable.
        # Setting it to 0 prevents GPU layers from being used.
        #
        # This is mainly useful when the Ollama process itself is
        # started with this environment variable available.
        self.cpu_only = True

        logger.info(
            f"[OLLAMA] CPU-only client initialized: {self.base_url}"
        )

    # ============================================================
    # MODEL CLASSIFICATION
    # ============================================================

    @staticmethod
    def is_vision_model(model_name: str) -> bool:
        """
        Determine whether a model supports image input.

        Keep this explicit rather than checking generic strings
        such as 'vl', which can produce false positives.
        """

        if not model_name:
            return False

        normalized = model_name.lower().strip()

        return (
            normalized in OllamaClient.VISION_MODEL_NAMES
            or normalized.startswith("moondream:")
            or normalized.startswith("qwen2.5vl:")
        )

    @staticmethod
    def is_embedding_model(model_name: str) -> bool:
        """
        Determine whether a model is an embedding model.
        """

        if not model_name:
            return False

        normalized = model_name.lower().strip()

        return (
            normalized in OllamaClient.EMBEDDING_MODEL_NAMES
            or "embed" in normalized
        )

    @staticmethod
    def is_coding_model(model_name: str) -> bool:
        """
        Determine whether a model is intended for coding.
        """

        if not model_name:
            return False

        normalized = model_name.lower()

        return any(
            keyword in normalized
            for keyword in [
                "coder",
                "code",
                "starcoder",
                "codellama",
                "deepseek-coder",
            ]
        )

    # ============================================================
    # HTTP CLIENT
    # ============================================================

    def _client(
        self,
        timeout: float = 300.0,
    ) -> httpx.AsyncClient:
        """
        Create a configured async HTTP client.

        CPU inference can be slower, therefore generous timeouts
        are used.
        """

        return httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=timeout,
                write=timeout,
                pool=10.0,
            )
        )

    # ============================================================
    # HEALTH CHECK
    # ============================================================

    async def health_check(self) -> dict:
        """
        Check whether local Ollama is running.
        """

        try:
            async with self._client(timeout=10.0) as client:

                response = await client.get(
                    f"{self.base_url}/api/tags"
                )

                response.raise_for_status()

                data = response.json()

                models = [
                    model.get("name")
                    for model in data.get("models", [])
                    if model.get("name")
                ]

                try:
                    from llm.model_registry import model_registry
                    model_registry.update_installed_models(models)
                except Exception:
                    pass

                return {
                    "status": "ok",
                    "available": True,
                    "url": self.base_url,
                    "execution": "cpu",
                    "models_available": models,
                    "count": len(models),
                }

        except httpx.ConnectError:

            logger.warning(
                f"[OLLAMA] Ollama is unreachable at {self.base_url}"
            )

            return {
                "status": "error",
                "available": False,
                "url": self.base_url,
                "execution": "cpu",
                "models_available": [],
                "count": 0,
                "detail": (
                    f"Ollama is not running at {self.base_url}. "
                    "Start Ollama with: ollama serve"
                ),
            }

        except Exception as exc:

            logger.error(
                f"[OLLAMA] Health check failed: {exc}"
            )

            return {
                "status": "error",
                "available": False,
                "url": self.base_url,
                "execution": "cpu",
                "models_available": [],
                "count": 0,
                "detail": str(exc),
            }

    # ============================================================
    # AVAILABLE MODELS
    # ============================================================

    async def get_available_models(self) -> List[str]:
        """
        Return installed local Ollama model names.
        """

        try:

            async with self._client(timeout=10.0) as client:

                response = await client.get(
                    f"{self.base_url}/api/tags"
                )

                response.raise_for_status()

                data = response.json()

                return [
                    model.get("name")
                    for model in data.get("models", [])
                    if model.get("name")
                ]

        except Exception as exc:

            logger.warning(
                f"[OLLAMA] Could not retrieve models: {exc}"
            )

            return []

    # ============================================================
    # MODEL EXISTENCE
    # ============================================================

    async def model_exists(self, model_name: str) -> bool:
        """
        Check whether an exact model or base model exists.
        """

        available = await self.get_available_models()

        if model_name in available:
            return True

        requested_base = model_name.split(":")[0].lower()

        for installed in available:

            installed_base = installed.split(":")[0].lower()

            if installed_base == requested_base:
                return True

        return False

    # ============================================================
    # MODEL RESOLUTION
    # ============================================================

    async def resolve_model(
        self,
        model: str,
        require_vision: bool = False,
        require_embedding: bool = False,
    ) -> str:
        """
        Resolve an explicitly requested model.

        IMPORTANT:
        We do NOT silently replace an explicitly requested model
        with an unrelated model.

        This prevents:

            coding agent -> general model

        or:

            embedding -> chat model

        without the orchestrator knowing.
        """

        if not model:
            raise ValueError("Ollama model name cannot be empty.")

        normalized = model.strip()

        # --------------------------------------------------------
        # Embedding protection
        # --------------------------------------------------------

        if require_embedding:

            if not self.is_embedding_model(normalized):

                raise ValueError(
                    f"Model '{normalized}' is not an embedding model. "
                    f"Use '{self.EMBEDDING_MODEL}'."
                )

        # --------------------------------------------------------
        # Vision protection
        # --------------------------------------------------------

        if require_vision:

            if not self.is_vision_model(normalized):

                raise ValueError(
                    f"Model '{normalized}' is not vision-capable. "
                    f"Use '{self.VISION_MODEL}'."
                )

        # --------------------------------------------------------
        # Installed model check
        # --------------------------------------------------------

        available = await self.get_available_models()

        if not available:

            raise ConnectionError(
                f"No models were returned by Ollama at "
                f"{self.base_url}."
            )

        # Exact match
        if normalized in available:
            return normalized

        # Match model without tag
        requested_base = normalized.split(":")[0].lower()

        for installed in available:

            installed_base = installed.split(":")[0].lower()

            if installed_base == requested_base:

                logger.info(
                    f"[OLLAMA] Resolved '{normalized}' -> '{installed}'"
                )

                return installed

        # Fallback check via model_registry
        try:
            from llm.model_registry import model_registry
            fallback = model_registry.resolve_model(normalized)
            if fallback:
                fallback_base = fallback.split(":")[0].lower()
                for installed in available:
                    if installed == fallback or installed.split(":")[0].lower() == fallback_base:
                        logger.warning(
                            f"[OLLAMA] Model '{normalized}' not directly installed. Using fallback '{installed}'"
                        )
                        return installed
        except Exception as reg_err:
            logger.debug(f"[OLLAMA] Fallback lookup notice: {reg_err}")

        # Non-crashing default fallback to any installed general model
        if available:
            preferred = [m for m in available if not self.is_embedding_model(m) and not self.is_vision_model(m)]
            chosen = preferred[0] if preferred else available[0]
            logger.warning(
                f"[OLLAMA] Requested '{normalized}' unavailable. Falling back to installed '{chosen}'."
            )
            return chosen

        raise RuntimeError(
            f"Model '{normalized}' is not installed in local Ollama. "
            f"Available models: {', '.join(available)}"
        )

    # ============================================================
    # ERROR NORMALIZATION
    # ============================================================

    @staticmethod
    def normalize_error(
        error_text: str,
        model_name: str,
    ) -> str:

        text = str(error_text)
        lower = text.lower()

        if "does not support images" in lower:
            return (
                f"Model '{model_name}' does not support images. "
                "Use a vision model such as moondream:latest."
            )

        if "not found" in lower:
            return (
                f"Model '{model_name}' was not found in Ollama. "
                f"Run: ollama pull {model_name}"
            )

        if "memory" in lower or "allocate" in lower:
            return (
                f"Model '{model_name}' could not be loaded because "
                "the system does not have enough memory. "
                "Use a smaller quantized model or close other applications."
            )

        if "context" in lower:
            return (
                "The requested context is too large for the current "
                "CPU/RAM configuration. Reduce the context size."
            )

        return text

    # ============================================================
    # CHAT
    # ============================================================

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Non-streaming chat.

        Supports text and vision messages.
        """

        has_images = any(
            bool(message.get("images"))
            for message in messages
            if isinstance(message, dict)
        )

        effective_model = await self.resolve_model(
            model,
            require_vision=has_images,
        )

        payload = {
            "model": effective_model,
            "messages": messages,
            "stream": False,
            "keep_alive": getattr(settings, "OLLAMA_KEEP_ALIVE", "0"),
        }

        if options:
            payload["options"] = options

        try:

            logger.info(
                f"[OLLAMA] Chat request | "
                f"model={effective_model} | "
                f"vision={has_images} | "
                f"execution=CPU"
            )

            async with self._client(timeout=600.0) as client:

                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )

                if response.status_code >= 400:

                    raise RuntimeError(
                        self.normalize_error(
                            response.text,
                            effective_model,
                        )
                    )

                data = response.json()

                content = (
                    data.get("message", {})
                    .get("content", "")
                )

                if not content:

                    logger.warning(
                        f"[OLLAMA] Empty response from "
                        f"{effective_model}"
                    )

                return content

        except httpx.ConnectError:

            raise ConnectionError(
                f"Ollama is not running at {self.base_url}. "
                "Start it with: ollama serve"
            )

        except httpx.TimeoutException:

            raise TimeoutError(
                f"Ollama CPU request timed out for "
                f"model '{effective_model}'."
            )

        except Exception as exc:

            message = self.normalize_error(
                str(exc),
                effective_model,
            )

            logger.error(
                f"[OLLAMA] Chat failed: {message}"
            )

            raise RuntimeError(message) from exc

    # ============================================================
    # STREAMING CHAT
    # ============================================================

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Streaming chat.

        Yields only generated text chunks.

        Errors are raised instead of being mixed into the AI
        response stream.
        """

        has_images = any(
            bool(message.get("images"))
            for message in messages
            if isinstance(message, dict)
        )

        effective_model = await self.resolve_model(
            model,
            require_vision=has_images,
        )

        payload = {
            "model": effective_model,
            "messages": messages,
            "stream": True,
            "keep_alive": getattr(settings, "OLLAMA_KEEP_ALIVE", "0"),
        }

        if options:
            payload["options"] = options

        try:

            logger.info(
                f"[OLLAMA] Streaming request | "
                f"model={effective_model} | "
                f"CPU"
            )

            async with self._client(timeout=900.0) as client:

                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:

                    if response.status_code >= 400:

                        body = await response.aread()

                        raise RuntimeError(
                            self.normalize_error(
                                body.decode(
                                    errors="ignore"
                                ),
                                effective_model,
                            )
                        )

                    async for line in response.aiter_lines():

                        if not line.strip():
                            continue

                        try:

                            data = json.loads(line)

                        except json.JSONDecodeError:

                            logger.warning(
                                "[OLLAMA] Invalid streaming JSON"
                            )

                            continue

                        if data.get("error"):

                            raise RuntimeError(
                                self.normalize_error(
                                    data["error"],
                                    effective_model,
                                )
                            )

                        content = (
                            data.get("message", {})
                            .get("content", "")
                        )

                        if content:
                            yield content

                        if data.get("done"):
                            break

        except httpx.ConnectError:

            raise ConnectionError(
                f"Ollama is not running at {self.base_url}. "
                "Start it with: ollama serve"
            )

        except httpx.TimeoutException:

            raise TimeoutError(
                f"Ollama streaming request timed out for "
                f"model '{effective_model}'."
            )

        except Exception as exc:

            message = self.normalize_error(
                str(exc),
                effective_model,
            )

            logger.error(
                f"[OLLAMA] Streaming failed: {message}"
            )

            raise RuntimeError(message) from exc

    # ============================================================
    # JSON CHAT
    # ============================================================

    async def chat_json(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Ask Ollama for structured JSON.

        Useful for:
            - Agent plans
            - Risk analysis
            - Task classification
            - Tool selection
            - Validation results
        """

        effective_model = await self.resolve_model(model)

        # Never allow embedding model to produce agent JSON.
        if self.is_embedding_model(effective_model):

            raise ValueError(
                f"Embedding model '{effective_model}' cannot be "
                "used for JSON chat/planning."
            )

        payload = {
            "model": effective_model,
            "messages": messages,
            "format": "json",
            "stream": False,
            "keep_alive": getattr(settings, "OLLAMA_KEEP_ALIVE", "0"),
        }

        if options:
            payload["options"] = options

        content = ""

        try:

            async with self._client(timeout=600.0) as client:

                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )

                if response.status_code >= 400:

                    raise RuntimeError(
                        self.normalize_error(
                            response.text,
                            effective_model,
                        )
                    )

                data = response.json()

                content = (
                    data.get("message", {})
                    .get("content", "{}")
                )

                try:

                    parsed = json.loads(content)

                except json.JSONDecodeError as exc:

                    logger.error(
                        f"[OLLAMA] Invalid JSON response: {exc}"
                    )

                    raise RuntimeError(
                        "Ollama returned invalid JSON."
                    ) from exc

                if not isinstance(parsed, dict):

                    raise RuntimeError(
                        "Ollama JSON response is not an object."
                    )

                return parsed

        except httpx.ConnectError:

            raise ConnectionError(
                f"Ollama is not running at {self.base_url}."
            )

        except Exception as exc:

            logger.error(
                f"[OLLAMA] chat_json failed: {exc}"
            )

            raise

    # ============================================================
    # DIRECT GENERATION
    # ============================================================

    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Direct text generation.
        """

        effective_model = await self.resolve_model(model)

        if self.is_embedding_model(effective_model):

            raise ValueError(
                f"Embedding model '{effective_model}' cannot "
                "perform text generation."
            )

        payload = {
            "model": effective_model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": getattr(settings, "OLLAMA_KEEP_ALIVE", "0"),
        }

        if system:
            payload["system"] = system

        if options:
            payload["options"] = options

        try:

            async with self._client(timeout=600.0) as client:

                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )

                if response.status_code >= 400:

                    raise RuntimeError(
                        self.normalize_error(
                            response.text,
                            effective_model,
                        )
                    )

                data = response.json()

                return data.get("response", "")

        except httpx.ConnectError:

            raise ConnectionError(
                f"Ollama is not running at {self.base_url}."
            )

        except Exception as exc:

            logger.error(
                f"[OLLAMA] Generate failed: {exc}"
            )

            raise

    # ============================================================
    # VISION
    # ============================================================

    async def generate_with_vision(
        self,
        model: str,
        prompt: str,
        images: List[str],
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a response from one or more images.

        Images must be base64 encoded strings.
        """

        if not images:

            raise ValueError(
                "At least one image is required."
            )

        effective_model = await self.resolve_model(
            model,
            require_vision=True,
        )

        messages = [
            {
                "role": "user",
                "content": prompt,
                "images": images,
            }
        ]

        return await self.chat(
            model=effective_model,
            messages=messages,
            options=options,
        )

    # ============================================================
    # EMBEDDINGS
    # ============================================================

    async def generate_embedding(
        self,
        model: str,
        text: str,
    ) -> List[float]:
        """
        Generate a local embedding.

        Intended model:
            nomic-embed-text:latest

        Used by:
            Qdrant
            RAG
            Mem0
            semantic search
        """

        if not text or not text.strip():

            raise ValueError(
                "Cannot generate embedding for empty text."
            )

        effective_model = await self.resolve_model(
            model,
            require_embedding=True,
        )

        try:

            async with self._client(timeout=120.0) as client:

                # Modern Ollama API
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json={
                        "model": effective_model,
                        "input": text,
                    },
                )

                if response.status_code == 200:

                    data = response.json()

                    embeddings = data.get(
                        "embeddings",
                        [],
                    )

                    if embeddings:

                        return embeddings[0]

                # Legacy compatibility
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": effective_model,
                        "prompt": text,
                    },
                )

                if response.status_code >= 400:

                    raise RuntimeError(
                        self.normalize_error(
                            response.text,
                            effective_model,
                        )
                    )

                data = response.json()

                embedding = data.get(
                    "embedding",
                    [],
                )

                if not embedding:

                    raise RuntimeError(
                        "Ollama returned an empty embedding."
                    )

                return embedding

        except httpx.ConnectError:

            raise ConnectionError(
                f"Ollama is not running at {self.base_url}."
            )

        except Exception as exc:

            logger.error(
                f"[OLLAMA] Embedding generation failed: {exc}"
            )

            raise

    # ============================================================
    # RUNNING MODELS
    # ============================================================

    async def get_running_models(self) -> List[Dict[str, Any]]:
        """
        Get currently loaded/running models.

        Informational only.

        We intentionally do NOT automatically unload them.
        """

        try:

            async with self._client(timeout=10.0) as client:

                response = await client.get(
                    f"{self.base_url}/api/ps"
                )

                response.raise_for_status()

                data = response.json()

                return data.get("models", [])

        except Exception as exc:

            logger.warning(
                f"[OLLAMA] Could not get running models: {exc}"
            )

            return []

    # ============================================================
    # DETAILED MODEL INFORMATION
    # ============================================================

    async def list_models_detailed(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Return detailed information about installed models.
        """

        try:

            async with self._client(timeout=15.0) as client:

                response = await client.get(
                    f"{self.base_url}/api/tags"
                )

                response.raise_for_status()

                data = response.json()

            models = []

            for model in data.get("models", []):

                name = model.get("name", "")
                size_bytes = model.get("size", 0)
                details = model.get("details", {})

                if self.is_embedding_model(name):

                    model_type = "Embedding"

                    capabilities = [
                        "embeddings",
                        "semantic_search",
                        "rag",
                    ]

                elif self.is_vision_model(name):

                    model_type = "Vision"

                    capabilities = [
                        "text_generation",
                        "image_understanding",
                    ]

                elif self.is_coding_model(name):

                    model_type = "LLM"

                    capabilities = [
                        "text_generation",
                        "code_generation",
                        "tool_planning",
                    ]

                else:

                    model_type = "LLM"

                    capabilities = [
                        "text_generation",
                        "reasoning",
                    ]

                if size_bytes >= 1024 ** 3:

                    size = (
                        f"{size_bytes / (1024 ** 3):.2f} GB"
                    )

                elif size_bytes > 0:

                    size = (
                        f"{size_bytes / (1024 ** 2):.0f} MB"
                    )

                else:

                    size = "Unknown"

                models.append(
                    {
                        "name": name,
                        "provider": "ollama",
                        "type": model_type,
                        "execution": "cpu",
                        "status": "Ready",
                        "size": size,
                        "sizeBytes": size_bytes,
                        "capabilities": capabilities,
                        "details": details,
                        "family": details.get(
                            "family",
                            "",
                        ),
                        "parameterSize": details.get(
                            "parameter_size",
                            "",
                        ),
                        "quantization": details.get(
                            "quantization_level",
                            "",
                        ),
                    }
                )

            return models

        except Exception as exc:

            logger.warning(
                f"[OLLAMA] Detailed model listing failed: {exc}"
            )

            return []

    # ============================================================
    # PULL MODEL
    # ============================================================

    async def pull_model(
        self,
        model_name: str,
    ) -> Dict[str, Any]:
        """
        Pull a model into local Ollama.
        """

        if not model_name:

            raise ValueError(
                "Model name is required."
            )

        try:

            async with self._client(
                timeout=1800.0
            ) as client:

                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={
                        "name": model_name,
                        "stream": False,
                    },
                )

                if response.status_code >= 400:

                    raise RuntimeError(
                        self.normalize_error(
                            response.text,
                            model_name,
                        )
                    )

                return response.json()

        except httpx.ConnectError:

            raise ConnectionError(
                f"Ollama is not running at {self.base_url}."
            )

        except Exception as exc:

            logger.error(
                f"[OLLAMA] Failed to pull "
                f"'{model_name}': {exc}"
            )

            raise


# ================================================================
# SINGLETON
# ================================================================

ollama_client = OllamaClient()