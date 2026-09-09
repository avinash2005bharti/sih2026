const axios = require("axios");

/**
 * Python AI Service Configuration
 *
 * Local development:
 * PYTHON_AI_SERVICE_URL=http://127.0.0.1:8000
 *
 * Docker:
 * PYTHON_AI_SERVICE_URL=http://ai-service:8000
 */

const PYTHON_AI_SERVICE_URL =
    process.env.PYTHON_AI_SERVICE_URL || "http://127.0.0.1:8000";


/**
 * Send chat request to Python AI Service
 */
async function sendChatToAI({
    message,
    conversationId,
    userId,
    model,
    context = {},
}) {
    try {
        const response = await axios.post(
            `${PYTHON_AI_SERVICE_URL}/api/chat`,
            {
                message,
                conversationId,
                userId,
                model,
                context,
            },
            {
                timeout: 120000, // 2 minutes
                headers: {
                    "Content-Type": "application/json",
                },
            }
        );

        return response.data;

    } catch (error) {

        console.error(
            "❌ Python AI Service Error:",
            error.response?.data || error.message
        );

        throw new Error(
            error.response?.data?.message ||
            "Python AI Service is unavailable"
        );
    }
}


/**
 * Check Python AI Service health
 */
async function checkAIServiceHealth() {
    try {

        const response = await axios.get(
            `${PYTHON_AI_SERVICE_URL}/api/health`,
            {
                timeout: 5000,
            }
        );

        return response.data;

    } catch (error) {

        console.error(
            "❌ AI Service Health Check Failed:",
            error.message
        );

        return {
            success: false,
            status: "offline",
            message: "Python AI Service is unavailable",
        };
    }
}


/**
 * Get available AI models
 */
async function getAIModels() {
    try {

        const response = await axios.get(
            `${PYTHON_AI_SERVICE_URL}/api/models`,
            {
                timeout: 10000,
            }
        );

        return response.data;

    } catch (error) {

        console.error(
            "❌ Failed to fetch AI models:",
            error.response?.data || error.message
        );

        throw new Error("Unable to fetch AI models");
    }
}


/**
 * Send document to Python AI Service
 *
 * Later this will handle:
 * - PDF
 * - DOCX
 * - Images
 * - OCR
 * - Embeddings
 * - RAG ingestion
 */
async function processDocument({
    filePath,
    documentId,
    userId,
}) {
    try {

        const response = await axios.post(
            `${PYTHON_AI_SERVICE_URL}/api/documents/process`,
            {
                filePath,
                documentId,
                userId,
            },
            {
                timeout: 300000, // 5 minutes
                headers: {
                    "Content-Type": "application/json",
                },
            }
        );

        return response.data;

    } catch (error) {

        console.error(
            "❌ Document Processing Error:",
            error.response?.data || error.message
        );

        throw new Error(
            error.response?.data?.message ||
            "Document processing failed"
        );
    }
}


module.exports = {
    sendChatToAI,
    checkAIServiceHealth,
    getAIModels,
    processDocument,
};