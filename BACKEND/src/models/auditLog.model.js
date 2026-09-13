const mongoose = require("mongoose");

const auditLogSchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User"
    },

    action: {
      type: String,
      required: true
    },

    resourceType: {
      type: String
    },

    resourceId: {
      type: mongoose.Schema.Types.ObjectId
    },

    status: {
      type: String,
      enum: [
        "success",
        "failure"
      ]
    },

    ipAddress: {
      type: String
    },

    details: {
      type: mongoose.Schema.Types.Mixed
    }
  },
  {
    timestamps: true
  }
);

module.exports = mongoose.model(
  "AuditLog",
  auditLogSchema
);