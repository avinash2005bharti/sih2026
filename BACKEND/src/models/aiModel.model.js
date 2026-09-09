const mongoose = require("mongoose");

const aiModelSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: true
    },

    displayName: {
      type: String,
      required: true
    },

    provider: {
      type: String,
      enum: [
        "ollama",
        "vllm",
        "llama.cpp",
        "huggingface",
        "custom"
      ],
      required: true
    },

    modelType: {
      type: String,
      enum: [
        "llm",
        "vlm",
        "embedding",
        "reranker",
        "speech",
        "vision"
      ],
      required: true
    },

    modelPath: {
      type: String
    },

    endpoint: {
      type: String
    },

    capabilities: [
      {
        type: String,
        enum: [
          "text",
          "vision",
          "document",
          "reasoning",
          "coding",
          "embedding",
          "multilingual"
        ]
      }
    ],

    contextWindow: {
      type: Number
    },

    parameters: {
      type: String
    },

    quantization: {
      type: String
    },

    isLocal: {
      type: Boolean,
      default: true
    },

    isActive: {
      type: Boolean,
      default: true
    },

    priority: {
      type: Number,
      default: 1
    },

    metadata: {
      type: mongoose.Schema.Types.Mixed
    }
  },
  {
    timestamps: true
  }
);

module.exports = mongoose.model("AIModel", aiModelSchema);