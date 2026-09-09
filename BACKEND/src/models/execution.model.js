const mongoose = require("mongoose");

const executionSchema = new mongoose.Schema(
  {
    task: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Task",
      required: true,
      index: true
    },

    agent: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Agent"
    },

    model: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "AIModel"
    },

    stepNumber: {
      type: Number,
      required: true
    },

    action: {
      type: String,
      required: true
    },

    input: {
      type: mongoose.Schema.Types.Mixed
    },

    output: {
      type: mongoose.Schema.Types.Mixed
    },

    status: {
      type: String,
      enum: [
        "pending",
        "running",
        "completed",
        "failed"
      ],
      default: "pending"
    },

    duration: {
      type: Number
    },

    error: {
      type: String
    }
  },
  {
    timestamps: true
  }
);

module.exports = mongoose.model(
  "Execution",
  executionSchema
);