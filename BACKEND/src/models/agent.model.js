const mongoose = require("mongoose");

const agentSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: true
    },
    slug: {
      type: String,
      required: true,
      unique: true,
    },

    description: {
      type: String
    },

    type: {
      type: String,
      enum: [
        "orchestrator",
        "document",
        "maintenance",
        "safety",
        "compliance",
        "risk",
        "reporting",
        "research",
        "custom",
        "general",
        "coding",
        "vision"
      ],
      required: true
    },

    model: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "AIModel"
    },

    modelName: {
      type: String
    },

    createdBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User"
    },

    systemPrompt: {
      type: String,
      required: true
    },

    capabilities: [
      String
    ],

    tools: [
      {
        type: mongoose.Schema.Types.ObjectId,
        ref: "Tool"
      }
    ],

    knowledgeBases: [
      {
        type: mongoose.Schema.Types.ObjectId,
        ref: "KnowledgeBase"
      }
    ],

    temperature: {
      type: Number,
      default: 0.2
    },

    maxTokens: {
      type: Number,
      default: 2048
    },

    isActive: {
      type: Boolean,
      default: true
    }
  },
  {
    timestamps: true
  }
);

module.exports = mongoose.model("Agent", agentSchema);