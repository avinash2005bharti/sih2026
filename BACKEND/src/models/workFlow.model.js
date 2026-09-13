const mongoose = require("mongoose");

const workflowSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: true
    },

    description: String,

    createdBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User"
    },

    steps: [
      {
        order: {
          type: Number,
          required: true
        },

        agent: {
          type: mongoose.Schema.Types.ObjectId,
          ref: "Agent",
          required: true
        },

        condition: {
          type: String
        },

        continueOnFailure: {
          type: Boolean,
          default: false
        }
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
  "Workflow",
  workflowSchema
);