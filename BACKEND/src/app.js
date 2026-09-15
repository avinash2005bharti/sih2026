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
const adminRoutes = require("./routes/admin.routes");
const memoryRoutes = require("./routes/memory.routes");

// Create Express app
const app = express();

// ===============================
// Middlewares
// ===============================

const allowedOrigins = [
    process.env.FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000"
].filter(Boolean);

app.use(
    cors({
        origin: function (origin, callback) {
            if (!origin || allowedOrigins.includes(origin)) {
                callback(null, true);
            } else {
                callback(null, true); // Allow all in local sovereign development
            }
        },
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
// Admin routes
app.use('/api/admin', adminRoutes);

// Memory Architecture Routes
app.use('/api/memory', memoryRoutes);

// ===============================
// Health Check
// ===============================

const { checkOllamaHealth, OLLAMA_BASE_URL } = require("./services/ollama.service");
const { detectHardware } = require("./services/hardware.service");
const { checkAIServiceHealth } = require("./services/python.service");

app.get("/api/health", async (req, res) => {
    try {
        const [ollamaRes, hwRes, aiRes] = await Promise.allSettled([
            checkOllamaHealth(),
            detectHardware(),
            checkAIServiceHealth()
        ]);

        const ollama = ollamaRes.status === "fulfilled" ? ollamaRes.value : { available: false, url: OLLAMA_BASE_URL, modelsAvailable: false };
        const hw = hwRes.status === "fulfilled" ? hwRes.value : { nvidiaAvailable: false, mode: "cpu" };
        const ai = aiRes.status === "fulfilled" ? aiRes.value : { status: "offline" };

        const aiReachable = ai.status && ai.status !== "offline" && ai.status !== "error";
        const healthy = Boolean(ollama.available && aiReachable);
        return res.status(healthy ? 200 : 503).json({
            success: healthy,
            status: healthy ? "healthy" : "degraded",
            message: healthy ? "Sovereign AI Workbench API is healthy" : "Sovereign AI Workbench API is degraded",
            ollama: {
                available: ollama.available || false,
                url: OLLAMA_BASE_URL,
                modelsAvailable: ollama.modelsAvailable || false,
                count: ollama.count || 0
            },
            hardware: {
                nvidiaAvailable: hw.nvidiaAvailable || false,
                mode: hw.mode || "cpu"
            },
            services: {
                node: "healthy",
                python: ai.status || "offline",
                ollama: ollama.available ? "healthy" : "unavailable",
                ...(ai.services || {})
            }
        });
    } catch (error) {
        return res.status(503).json({
            success: false,
            status: "degraded",
            message: "Sovereign AI Workbench dependencies could not be checked",
            ollama: {
                available: false,
                url: process.env.OLLAMA_BASE_URL || "http://localhost:11434",
                modelsAvailable: false
            },
            hardware: {
                nvidiaAvailable: false,
                mode: "cpu"
            }
        });
    }
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
