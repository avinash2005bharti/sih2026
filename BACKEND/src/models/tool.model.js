const mongoose = require("mongoose");

const toolSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: true
    },

    description: {
      type: String,
      required: true
    },

    type: {
      type: String,
      enum: [
        "function",
        "api",
        "database",
        "rag",
        "calculator",
        "file",
        "system"
      ],
      required: true
    },

    endpoint: {
      type: String
    },

    method: {
      type: String,
      enum: [
        "GET",
        "POST",
        "PUT",
        "DELETE"
      ]
    },

    parameters: {
      type: mongoose.Schema.Types.Mixed
    },

    requiresApproval: {
      type: Boolean,
      default: false
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

module.exports = mongoose.model("Tool", toolSchema);