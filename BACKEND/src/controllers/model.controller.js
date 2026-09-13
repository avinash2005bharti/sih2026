const AIModel = require("../models/aiModel.model");
const axios = require("axios");
const { getAIModels, checkAIServiceHealth, pullAIModel, getOllamaModels: fetchOllamaModels } = require("../services/python.service");
const { OLLAMA_BASE_URL, checkOllamaHealth, listModels: fetchLocalOllamaModels, pullModel: pullLocalOllamaModel } = require("../services/ollama.service");
const { detectHardware } = require("../services/hardware.service");

const PYTHON_AI_SERVICE_URL = process.env.PYTHON_AI_SERVICE_URL || "http://127.0.0.1:8000";

// CREATE MODEL
async function createModel(req, res) {
  try {
    const {
      name,
      displayName,
      provider,
      modelType,
      modelPath,
      endpoint,
      capabilities,
      contextWindow,
      parameters,
      quantization,
      isLocal,
      priority,
    } = req.body;

    if (!name || !displayName || !provider || !modelType) {
      return res.status(400).json({
        success: false,
        message: "Required model fields are missing",
      });
    }

    const existingModel = await AIModel.findOne({ name });

    if (existingModel) {
      return res.status(409).json({
        success: false,
        message: "Model already exists",
      });
    }

    const model = await AIModel.create({
      name,
      displayName,
      provider,
      modelType,
      modelPath,
      endpoint: endpoint || OLLAMA_BASE_URL,
      capabilities,
      contextWindow,
      parameters,
      quantization,
      isLocal: isLocal !== undefined ? isLocal : true,
      priority,
    });

    return res.status(201).json({
      success: true,
      message: "AI model created successfully",
      model,
    });
  } catch (error) {
    console.error("Create Model Error:", error);
    return res.status(500).json({
      success: false,
      message: "Failed to create model",
    });
  }
}

// GET MODELS
async function getModels(req, res) {
  try {
    // 1. Dynamically discover and synchronize from local Ollama
    try {
      let discoveredModels = [];

      // Try via Python AI service first
      try {
        const aiServiceOllama = await fetchOllamaModels();
        if (aiServiceOllama && Array.isArray(aiServiceOllama.models)) {
          discoveredModels = aiServiceOllama.models;
        }
      } catch (err) {
        // Fallback: Query local Ollama directly
        discoveredModels = await fetchLocalOllamaModels();
      }

      for (const m of discoveredModels) {
        const modelName = m.model || m.name;
        if (!modelName) continue;

        const isVision =
          (m.type && m.type.toLowerCase() === "vision") ||
          (m.capabilities && m.capabilities.includes("image_understanding")) ||
          m.name?.includes("vl") ||
          m.name?.includes("vision");
        const isEmbed =
          (m.type && m.type.toLowerCase() === "embedding") ||
          (m.capabilities && m.capabilities.includes("embeddings")) ||
          m.name?.includes("embed");

        const resolvedType = isVision ? "vlm" : isEmbed ? "embedding" : "llm";

        await AIModel.updateOne(
          { name: modelName },
          {
            $set: {
              displayName: modelName,
              provider: "ollama",
              modelType: resolvedType,
              endpoint: OLLAMA_BASE_URL,
              isActive: true,
              isLocal: true,
            },
          },
          { upsert: true }
        );
      }
    } catch (ollamaErr) {
      console.warn("Notice: Failed to sync local Ollama models in getModels:", ollamaErr.message);
    }

    const models = await AIModel.find({
      isActive: true,
    }).sort({
      priority: 1,
      createdAt: -1,
    });

    return res.status(200).json({
      success: true,
      models,
    });
  } catch (error) {
    console.error("Get Models Error:", error);
    return res.status(500).json({
      success: false,
      message: "Failed to fetch models",
    });
  }
}

// GET MODEL BY ID
async function getModelById(req, res) {
  try {
    const { modelId } = req.params;
    const model = await AIModel.findById(modelId);

    if (!model) {
      return res.status(404).json({
        success: false,
        message: "Model not found",
      });
    }

    return res.status(200).json({
      success: true,
      model,
    });
  } catch (error) {
    console.error("Get Model Error:", error);
    return res.status(500).json({
      success: false,
      message: "Failed to fetch model",
    });
  }
}

// UPDATE MODEL
async function updateModel(req, res) {
  try {
    const { modelId } = req.params;
    const model = await AIModel.findByIdAndUpdate(modelId, req.body, {
      new: true,
      runValidators: true,
    });

    if (!model) {
      return res.status(404).json({
        success: false,
        message: "Model not found",
      });
    }

    return res.status(200).json({
      success: true,
      message: "Model updated successfully",
      model,
    });
  } catch (error) {
    console.error("Update Model Error:", error);
    return res.status(500).json({
      success: false,
      message: "Failed to update model",
    });
  }
}

// DELETE MODEL
async function deleteModel(req, res) {
  try {
    const { modelId } = req.params;
    const model = await AIModel.findByIdAndUpdate(
      modelId,
      { isActive: false },
      { new: true }
    );

    if (!model) {
      return res.status(404).json({
        success: false,
        message: "Model not found",
      });
    }

    return res.status(200).json({
      success: true,
      message: "Model deleted successfully",
    });
  } catch (error) {
    console.error("Delete Model Error:", error);
    return res.status(500).json({
      success: false,
      message: "Failed to delete model",
    });
  }
}

// GET OLLAMA MODELS
async function getOllamaModels(req, res) {
  try {
    // Try AI service first
    try {
      const models = await fetchOllamaModels();
      return res.status(200).json(models);
    } catch (aiErr) {
      // Fallback directly to local Ollama runtime
      const localModels = await fetchLocalOllamaModels();
      return res.status(200).json({
        success: true,
        models: localModels,
        count: localModels.length,
      });
    }
  } catch (error) {
    console.error("Get Ollama Models Error:", error);
    return res.status(500).json({
      success: false,
      message: "Failed to fetch Ollama models",
    });
  }
}

// GET MODEL ROLES
async function getModelRoles(req, res) {
  try {
    const response = await axios.get(`${PYTHON_AI_SERVICE_URL}/api/models/roles`, {
      timeout: 5000,
    });
    return res.status(200).json(response.data);
  } catch (error) {
    return res.status(200).json({
      success: true,
      roles: {
        chat: process.env.OLLAMA_CHAT_MODEL || "qwen3:4b",
        coding: process.env.OLLAMA_CODE_MODEL || "qwen2.5-coder:3b",
        vision: process.env.OLLAMA_VISION_MODEL || "qwen2.5vl:3b",
        embedding: process.env.OLLAMA_EMBED_MODEL || "nomic-embed-text:latest",
      },
    });
  }
}

// UPDATE MODEL ROLE
async function updateModelRole(req, res) {
  try {
    const { role, model } = req.body;
    if (!role || !model) {
      return res.status(400).json({ success: false, message: "Role and model are required" });
    }

    const response = await axios.put(
      `${PYTHON_AI_SERVICE_URL}/api/models/roles`,
      { role, model },
      { timeout: 5000 }
    );
    return res.status(200).json(response.data);
  } catch (error) {
    return res.status(500).json({
      success: false,
      message: error.response?.data?.detail || error.message || "Failed to update model role",
    });
  }
}

// PULL MODEL
async function pullModel(req, res) {
  try {
    const { model } = req.body;
    if (!model || typeof model !== "string") {
      return res.status(400).json({ success: false, message: "Model name is required" });
    }

    if (/[;&|`$]/.test(model)) {
      return res.status(400).json({ success: false, message: "Invalid model name" });
    }

    try {
      const result = await pullAIModel(model);
      return res.status(200).json(result);
    } catch (aiErr) {
      const result = await pullLocalOllamaModel(model);
      return res.status(200).json(result);
    }
  } catch (error) {
    console.error("Pull Model Error:", error);
    return res.status(500).json({
      success: false,
      message: error.message || "Failed to pull model",
    });
  }
}

// HEALTH CHECK (Aggregated)
async function healthCheck(req, res) {
  try {
    const [aiServiceHealth, ollamaHealth, hardware] = await Promise.allSettled([
      checkAIServiceHealth(),
      checkOllamaHealth(),
      detectHardware(),
    ]);

    const aiStatus = aiServiceHealth.status === "fulfilled" ? aiServiceHealth.value : { status: "offline" };
    const ollamaStatus = ollamaHealth.status === "fulfilled" ? ollamaHealth.value : { available: false, url: OLLAMA_BASE_URL, modelsAvailable: false };
    const hwStatus = hardware.status === "fulfilled" ? hardware.value : { nvidiaAvailable: false, mode: "cpu" };

    return res.status(200).json({
      success: true,
      node: "ok",
      aiService: aiStatus.status || "offline",
      ollama: {
        available: ollamaStatus.available || false,
        url: OLLAMA_BASE_URL,
        modelsAvailable: ollamaStatus.modelsAvailable || false,
        count: ollamaStatus.count || 0,
      },
      hardware: {
        nvidiaAvailable: hwStatus.nvidiaAvailable || false,
        mode: hwStatus.mode || "cpu",
        gpuName: hwStatus.gpuName,
        driverVersion: hwStatus.driverVersion,
      },
    });
  } catch (error) {
    console.error("Health Check Error:", error);
    return res.status(500).json({
      success: false,
      message: "Failed to perform health check",
    });
  }
}

module.exports = {
  createModel,
  getModels,
  getModelById,
  updateModel,
  deleteModel,
  getOllamaModels,
  pullModel,
  healthCheck,
  getModelRoles,
  updateModelRole,
};