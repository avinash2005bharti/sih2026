/**
 * Reusable Local Ollama Client Service for Node.js Backend.
 * Direct communication with local Ollama runtime on Windows host (http://localhost:11434).
 * Fully wrapped in try/catch to safely handle offline state, timeouts, and missing models.
 */

const axios = require("axios");

const OLLAMA_BASE_URL =
  process.env.OLLAMA_BASE_URL ||
  process.env.OLLAMA_HOST ||
  "http://localhost:11434";

/**
 * Helper to identify vision capability from model name
 */
function isVisionModel(modelName) {
  if (!modelName || typeof modelName !== "string") return false;
  const nameLower = modelName.toLowerCase();
  const visionIndicators = ["vision", "llava", "minicpm-v", "bakllava", "vl", "qwen2.5vl", "moondream"];
  return visionIndicators.some((ind) => nameLower.includes(ind));
}

/**
 * Normalize Ollama error responses into developer/user-friendly messages
 */
function normalizeOllamaError(error, modelName = "") {
  if (error.code === "ECONNREFUSED" || error.code === "ENOTFOUND") {
    return {
      message: `Ollama is not running at ${OLLAMA_BASE_URL}. Please run 'ollama serve' in your terminal.`,
      code: "OLLAMA_NOT_RUNNING",
      available: false,
    };
  }
  if (error.code === "ECONNABORTED" || error.message?.includes("timeout")) {
    return {
      message: `Ollama request timed out for model '${modelName}'.`,
      code: "OLLAMA_TIMEOUT",
    };
  }

  const responseText = (error.response?.data?.error || error.response?.data || error.message || "").toString();
  const lower = responseText.toLowerCase();

  if (lower.includes("does not support images") || lower.includes("vision")) {
    return {
      message: "Selected model does not support vision. Please select a vision-capable Ollama model.",
      code: "VISION_NOT_SUPPORTED",
    };
  }
  if (lower.includes("not found") || error.response?.status === 404) {
    return {
      message: `Model '${modelName}' not found in local Ollama. Please run: ollama pull ${modelName}`,
      code: "MODEL_NOT_FOUND",
    };
  }
  if (lower.includes("memory") || lower.includes("allocate") || lower.includes("cuda out of memory") || lower.includes("ram")) {
    return {
      message: "Model loading failed due to insufficient system RAM/memory. Consider selecting a smaller model.",
      code: "INSUFFICIENT_MEMORY",
    };
  }

  return {
    message: responseText || "Ollama service error",
    code: "OLLAMA_ERROR",
  };
}

/**
 * Check connectivity and list models from local Ollama
 */
async function checkOllamaHealth() {
  try {
    const response = await axios.get(`${OLLAMA_BASE_URL}/api/tags`, {
      timeout: 3000,
    });

    const models = response.data?.models || [];
    return {
      available: true,
      url: OLLAMA_BASE_URL,
      modelsAvailable: models.length > 0,
      models: models.map((m) => m.name),
      count: models.length,
    };
  } catch (error) {
    const norm = normalizeOllamaError(error);
    return {
      available: false,
      url: OLLAMA_BASE_URL,
      modelsAvailable: false,
      models: [],
      count: 0,
      error: norm.message,
    };
  }
}

/**
 * List all installed models with enriched capability detection
 */
async function listModels() {
  try {
    const response = await axios.get(`${OLLAMA_BASE_URL}/api/tags`, {
      timeout: 5000,
    });

    const rawModels = response.data?.models || [];
    return rawModels.map((m) => {
      const name = m.name || "";
      const sizeBytes = m.size || 0;
      const details = m.details || {};
      const nameLower = name.toLowerCase();

      let modelType = "llm";
      let capabilities = ["text"];

      if (isVisionModel(nameLower)) {
        modelType = "vlm";
        capabilities = ["text", "vision"];
      } else if (nameLower.includes("embed") || nameLower.includes("nomic") || nameLower.includes("bge")) {
        modelType = "embedding";
        capabilities = ["embedding"];
      } else {
        if (nameLower.includes("code") || nameLower.includes("coder")) {
          capabilities.push("coding");
        }
      }

      const sizeStr =
        sizeBytes >= 1024 ** 3
          ? `${(sizeBytes / 1024 ** 3).toFixed(1)} GB`
          : sizeBytes > 0
          ? `${Math.round(sizeBytes / 1024 ** 2)} MB`
          : "Unknown";

      return {
        name,
        displayName: name,
        provider: "ollama",
        modelType,
        endpoint: OLLAMA_BASE_URL,
        size: sizeStr,
        sizeBytes,
        capabilities,
        family: details.family || "",
        parameterSize: details.parameter_size || "",
        quantization: details.quantization_level || "",
        isLocal: true,
        isActive: true,
      };
    });
  } catch (error) {
    console.warn(`[OllamaService] Could not list models from ${OLLAMA_BASE_URL}:`, error.message);
    return [];
  }
}

/**
 * Generate text completion
 */
async function generate({ model, prompt, system = null, options = null }) {
  try {
    const payload = { model, prompt, stream: false };
    if (system) payload.system = system;
    if (options) payload.options = options;

    const response = await axios.post(`${OLLAMA_BASE_URL}/api/generate`, payload, {
      timeout: 300000,
    });
    return response.data?.response || "";
  } catch (error) {
    const norm = normalizeOllamaError(error, model);
    throw new Error(norm.message);
  }
}

/**
 * Chat completion
 */
async function chat({ model, messages, options = null }) {
  try {
    const payload = { model, messages, stream: false };
    if (options) payload.options = options;

    const response = await axios.post(`${OLLAMA_BASE_URL}/api/chat`, payload, {
      timeout: 300000,
    });
    return response.data?.message?.content || "";
  } catch (error) {
    const norm = normalizeOllamaError(error, model);
    throw new Error(norm.message);
  }
}

/**
 * Generate response with vision model
 */
async function generateWithVision({ model, prompt, images = [], options = null }) {
  if (!isVisionModel(model)) {
    throw new Error("Selected model does not support vision. Please select a vision-capable Ollama model.");
  }

  const cleanImages = images.map((img) => (img.startsWith("data:image") ? img.split(",")[1] : img));

  const messages = [
    {
      role: "user",
      content: prompt,
      images: cleanImages,
    },
  ];

  return await chat({ model, messages, options });
}

/**
 * Pull a model into local Ollama
 */
async function pullModel(modelName) {
  try {
    const response = await axios.post(
      `${OLLAMA_BASE_URL}/api/pull`,
      { name: modelName, stream: false },
      { timeout: 600000 }
    );
    return {
      success: true,
      message: `Model '${modelName}' pulled successfully`,
      data: response.data,
    };
  } catch (error) {
    const norm = normalizeOllamaError(error, modelName);
    throw new Error(norm.message);
  }
}

module.exports = {
  OLLAMA_BASE_URL,
  checkOllamaHealth,
  listModels,
  generate,
  chat,
  generateWithVision,
  pullModel,
  isVisionModel,
  normalizeOllamaError,
};
