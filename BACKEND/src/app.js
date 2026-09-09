const express = require("express");
const cookieParser = require("cookie-parser");
const cors = require("cors");
const path = require("path");

// Routes
const authRoutes = require("./routes/auth.routes");
const chatRoutes = require("./routes/chat.routes");
const agentRoutes = require("./routes/agent.routes");
const modelRoutes = require("./routes/model.routes");
const documentRoutes = require("./routes/document.routes");
const taskRoutes = require("./routes/task.routes");
const workflowRoutes = require("./routes/workflow.routes");
const knowledgeBaseRoutes = require("./routes/knowledgeBase.routes");
const toolRoutes = require("./routes/tool.routes");
const settingRoutes = require("./routes/setting.routes");

// Create Express app
const app = express();

// ===============================
// Middlewares
// ===============================

app.use(
    cors({
        origin: process.env.FRONTEND_URL,
        credentials: true
    })
);

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());

// Static files
app.use("/uploads", express.static(path.join(__dirname, "uploads")));

// ===============================
// API Routes
// ===============================

// Authentication
app.use("/api/auth", authRoutes);

// Chat & Conversations
app.use("/api/chat", chatRoutes);

// AI Agents
app.use("/api/agents", agentRoutes);

// AI Model Registry
app.use("/api/models", modelRoutes);

// Documents
app.use("/api/documents", documentRoutes);

// Agentic Tasks
app.use("/api/tasks", taskRoutes);

// Workflows
app.use("/api/workflows", workflowRoutes);

// RAG / Knowledge Bases
app.use("/api/knowledge-bases", knowledgeBaseRoutes);

// Agent Tools
app.use("/api/tools", toolRoutes);

// System Settings
app.use("/api/settings", settingRoutes);

// ===============================
// Health Check
// ===============================

app.get("/api/health", (req, res) => {
    res.status(200).json({
        success: true,
        message: "AI Workbench API is running"
    });
});

// ===============================
// 404 Handler
// ===============================

app.use((req, res) => {
    res.status(404).json({
        success: false,
        message: `Route ${req.method} ${req.originalUrl} not found`
    });
});

// ===============================
// Export
// ===============================

module.exports = app;