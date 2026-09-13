const mongoose = require("mongoose");

const conversationSchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true
    },

    title: {
      type: String,
      default: "New Conversation"
    },

    type: {
      type: String,
      enum: [
        "chat",
        "document_analysis",
        "workflow",
        "research"
      ],
      default: "chat"
    },

    activeAgent: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Agent"
    },

    status: {
      type: String,
      enum: [
        "active",
        "completed",
        "archived"
      ],
      default: "active"
    }
  },
  {
    timestamps: true
  }
);

module.exports = mongoose.model(
  "Conversation",
  conversationSchema
);