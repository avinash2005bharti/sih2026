const mongoose = require("mongoose");

const documentSchema = new mongoose.Schema(
  {
    uploadedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true
    },

    name: {
      type: String,
      required: true
    },

    originalName: {
      type: String
    },

    mimeType: {
      type: String
    },

    fileSize: {
      type: Number
    },

    filePath: {
      type: String
    },

    storageType: {
      type: String,
      enum: [
        "local",
        "docker_volume",
        "minio"
      ],
      default: "local"
    },

    documentType: {
      type: String,
      enum: [
        "pdf",
        "image",
        "word",
        "excel",
        "text",
        "report",
        "manual",
        "sop",
        "other"
      ]
    },

    processingStatus: {
      type: String,
      enum: [
        "uploaded",
        "processing",
        "processed",
        "failed"
      ],
      default: "uploaded"
    },

    extractedText: {
      type: String
    },

    metadata: {
      type: mongoose.Schema.Types.Mixed
    }
  },
  {
    timestamps: true
  }
);

module.exports = mongoose.model("Document", documentSchema);