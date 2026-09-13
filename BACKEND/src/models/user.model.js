const mongoose = require("mongoose");

const userSchema = new mongoose.Schema(
  {
    fullName: {
      firstName: {
        type: String,
        required: true,
        trim: true
      },
      middleName: {
        type: String,
        trim: true
      },
      lastName: {
        type: String,
        required: true,
        trim: true
      }
    },

    email: {
      type: String,
      required: true,
      unique: true,
      lowercase: true,
      trim: true
    },

    password: {
      type: String,
      required: true,
      select: false
    },

    role: {
      type: String,
      enum: [
        "admin",
        "operator",
        "engineer",
        "analyst",
        "viewer"
      ],
      default: "operator"
    },

    department: {
      type: String,
      trim: true
    },

    isAdmin: {
      type: Boolean,
      default: false
    },

    isActive: {
      type: Boolean,
      default: true
    },

    lastLogin: {
      type: Date
    }
  },
  {
    timestamps: true
  }
);

module.exports = mongoose.model("User", userSchema);