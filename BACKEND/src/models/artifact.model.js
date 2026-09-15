const mongoose = require("mongoose");

const artifactSchema = new mongoose.Schema(
  {
    conversation: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Conversation",
      required: true,
      index: true,
    },
    execution: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Execution",
    },
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
    },
    filename: {
      type: String,
      required: true,
      index: true,
    },
    artifactType: {
      type: String,
      enum: ["spreadsheet", "document", "image", "code", "pdf", "excel", "report", "other"],
      default: "other",
    },
    path: {
      type: String,
      required: true,
    },
    mimeType: {
      type: String,
      default: "application/octet-stream",
    },
    sizeBytes: {
      type: Number,
      default: 0,
    },
    description: {
      type: String,
      default: "",
    },
    status: {
      type: String,
      enum: ["created", "verified", "failed", "archived"],
      default: "created",
    },
    metadata: {
      type: mongoose.Schema.Types.Mixed,
      default: {},
    },
  },
  {
    timestamps: true,
  }
);

// Compound index for fast retrieval of artifacts by conversation
artifactSchema.index({ conversation: 1, createdAt: -1 });

module.exports = mongoose.model("Artifact", artifactSchema);
