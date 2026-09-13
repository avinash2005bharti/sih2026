const mongoose = require("mongoose");

const knowledgeBaseSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: true
    },

    description: {
      type: String
    },

    owner: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User"
    },

    collectionName: {
      type: String,
      required: true
    },

    embeddingModel: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "AIModel"
    },

    vectorDimension: {
      type: Number,
      required: true
    },

    documents: [
      {
        type: mongoose.Schema.Types.ObjectId,
        ref: "Document"
      }
    ],

    isActive: {
      type: Boolean,
      default: true
    }
  },
  {
    timestamps: true
  }
);

module.exports = mongoose.model(
  "KnowledgeBase",
  knowledgeBaseSchema
);