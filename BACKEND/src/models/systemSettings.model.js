const mongoose = require("mongoose");

const systemSettingSchema = new mongoose.Schema(
  {
    key: {
      type: String,
      required: true,
      unique: true
    },

    value: {
      type: mongoose.Schema.Types.Mixed
    },

    category: {
      type: String,
      enum: [
        "system",
        "security",
        "ai",
        "database",
        "network",
        "orchestrator"
      ]
    },

    description: String
  },
  {
    timestamps: true
  }
);

module.exports = mongoose.model(
  "SystemSetting",
  systemSettingSchema
);