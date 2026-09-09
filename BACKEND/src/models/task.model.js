const mongoose = require("mongoose");

const taskSchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true
    },

    conversation: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Conversation"
    },

    title: {
      type: String
    },

    objective: {
      type: String,
      required: true
    },

    status: {
      type: String,
      enum: [
        "queued",
        "planning",
        "running",
        "waiting_approval",
        "completed",
        "failed",
        "cancelled"
      ],
      default: "queued"
    },

    priority: {
      type: String,
      enum: [
        "low",
        "medium",
        "high",
        "critical"
      ],
      default: "medium"
    },

    orchestrator: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Agent"
    },

    selectedAgents: [
      {
        type: mongoose.Schema.Types.ObjectId,
        ref: "Agent"
      }
    ],

    result: {
      type: mongoose.Schema.Types.Mixed
    },

    error: {
      type: String
    },

    startedAt: Date,

    completedAt: Date
  },
  {
    timestamps: true
  }
);

module.exports = mongoose.model("Task", taskSchema);