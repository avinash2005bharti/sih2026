require('dotenv').config();
const app = require('./src/app');
const connectDB = require('./src/db/db');
const socket = require('./src/sockets/socket.server');
const { checkOllamaHealth, OLLAMA_BASE_URL } = require('./src/services/ollama.service');
const { detectHardware } = require('./src/services/hardware.service');
const httpserver = require("http").createServer(app);

const PORT = process.env.PORT || 5000;

const { seedDefaultAgents } = require('./src/seed/autoSeed');

async function performStartupDiagnostics() {
    console.log(`\n============================================================`);
    console.log(`🛡️  Sovereign On-Premise AI Workbench Backend Starting`);
    console.log(`============================================================`);

    // 1. Safe Hardware Detection (Non-crashing)
    try {
        const hw = await detectHardware();
        if (hw.nvidiaAvailable) {
            console.log(`🚀 Hardware: NVIDIA GPU detected -> ${hw.gpuName} (Driver: ${hw.driverVersion})`);
            console.log(`ℹ️  Local Ollama will automatically utilize GPU acceleration.`);
        } else {
            console.log(`💻 Hardware: NVIDIA GPU not detected.`);
            console.log(`ℹ️  Running in CPU / integrated graphics mode (seamless fallback).`);
        }
    } catch (err) {
        console.log(`💻 Hardware: CPU mode fallback.`);
    }

    // 2. Safe Ollama Reachability Check (Non-crashing)
    try {
        const ollamaStatus = await checkOllamaHealth();
        if (ollamaStatus.available) {
            console.log(`✅ Ollama: Connected at ${OLLAMA_BASE_URL} (${ollamaStatus.count} models available)`);
        } else {
            console.log(`\n------------------------------------------------------------`);
            console.log(`⚠️  Ollama is not installed or is not running at ${OLLAMA_BASE_URL}.`);
            console.log(`\nTo use local AI models, please install Ollama and run:`);
            console.log(`    ollama serve\n`);
            console.log(`The backend will continue running normally without crashing.`);
            console.log(`------------------------------------------------------------\n`);
        }
    } catch (err) {
        console.log(`⚠️  Ollama check skipped: ${err.message}. Continuing backend startup.`);
    }
}

connectDB()
    .then(async () => {
        await seedDefaultAgents();
    })
    .catch((err) => {
        console.warn(`⚠️ MongoDB connection issue (continuing): ${err.message}`);
    });

socket(httpserver);  // ✅ Socket.IO enabled

httpserver.on('error', (error) => {
    if (error.code === 'EADDRINUSE') {
        console.error(`\n❌ Error: Port ${PORT} is already in use.`);
        console.error(`Please check for another running backend instance or Docker container on port ${PORT}.\n`);
        process.exit(1);
    } else {
        console.error('❌ Server startup error:', error);
        process.exit(1);
    }
});

httpserver.listen(PORT, async () => {
    console.log(`Server is running on port ${PORT}`);
    await performStartupDiagnostics();
});