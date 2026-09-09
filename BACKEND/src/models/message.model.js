const mongoose = require("mongoose");

const messageSchema = new mongoose.Schema(
  {
    conversation: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Conversation",
      required: true,
      index: true
    },

    sender: {
      type: String,
      enum: [
        "user",
        "assistant",
        "agent",
        "system",
        "tool"
      ],
      required: true
    },

    agent: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Agent"
    },

    content: {
      type: String,
      required: true
    },

    attachments: [
      {
        type: mongoose.Schema.Types.ObjectId,
        ref: "Document"
      }
    ],

    modelUsed: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "AIModel"
    },

    tokens: {
      input: Number,
      output: Number
    },

    metadata: {
      type: mongoose.Schema.Types.Mixed
    }
  },
  {
    timestamps: true
  }
);

module.exports = mongoose.model("Message", messageSchema);