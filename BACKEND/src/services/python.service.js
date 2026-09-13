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
    images = [],
    context = {},
}) {
    try {
        const payload = {
            message,
            conversationId,
            userId,
            model,
            context,
        };
        if (images && images.length > 0) payload.images = images;

        const response = await axios.post(
            `${PYTHON_AI_SERVICE_URL}/api/chat`,
            payload,
            {
                timeout: 300000, // 5 minutes for local LLM inference
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
            error.response?.data?.detail ||
            error.response?.data?.message ||
            "Python AI Service is unavailable"
        );
    }
}

/**
 * Send chat request to Python AI Service with streaming response
 * 
 * Connects to FastAPI /api/chat/stream endpoint for token-by-token streaming
 * Used by Socket.IO to progressively send chunks to frontend
 */
async function sendChatToAIStream({
    socket,
    messageId,
    conversationId,
    message,
    model = "auto",
    agent = "general",
    images = [],
    systemPrompt,
    temperature,
    maxTokens,
    userId,
    abortSignal,
    onChunk = () => {},
    onError = () => {},
}) {
    try {
        const streamPayload = {
            message,
            model,
            conversationId,
            userId,
            agent,
            systemPrompt,
            temperature,
            maxTokens
        };
        if (images && images.length > 0) streamPayload.images = images;

        const response = await axios.post(
            `${PYTHON_AI_SERVICE_URL}/api/chat/stream`,
            streamPayload,
            {
                timeout: 300000, // 5 minutes for local LLM inference
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
                responseType: "stream", // Get streaming response
                signal: abortSignal,
            }
        );

        let fullResponse = "";
        let collectedFiles = [];
        let collectedToolExecutions = [];
        let collectedMultimodal = { ocr: null, vision: null };

        // Process SSE (Server-Sent Events) stream
        response.data.on("data", (chunk) => {
            const lines = chunk.toString().split("\n");

            for (const line of lines) {
                const trimmed = line.trim();
                if (!trimmed) continue;

                // Parse SSE format: "data: {...}"
                const payload = trimmed.startsWith("data:") ? trimmed.slice(5).trim() : trimmed;
                if (!payload || payload === "[DONE]") continue;

                try {
                    const data = JSON.parse(payload);

                    // Forward real-time agent lifecycle and tool events
                    if (socket && data.event) {
                        socket.emit(data.event, {
                            conversationId,
                            messageId,
                            ...data
                        });
                    }

                    if (data.file) {
                        collectedFiles.push(data.file);
                    }
                    if (data.generatedFiles && Array.isArray(data.generatedFiles)) {
                        collectedFiles = data.generatedFiles;
                    }
                    if (data.tool_executions && Array.isArray(data.tool_executions)) {
                        collectedToolExecutions = data.tool_executions;
                    }
                    if (data.event === "agent:tool:result") {
                        collectedToolExecutions.push({
                            tool: data.tool,
                            arguments: data.arguments,
                            result: data.result,
                            stdout: data.stdout,
                            stderr: data.stderr,
                            exit_code: data.exit_code,
                            duration_seconds: data.duration_seconds,
                            success: data.success,
                        });
                    }

                    if (data.event === "vision:result") {
                        if (data.ocr) collectedMultimodal.ocr = data.ocr;
                        if (data.vision) collectedMultimodal.vision = data.vision;
                    }

                    if (data.status === "completed" && !data.event) {
                        if (data.generatedFiles && Array.isArray(data.generatedFiles)) {
                            collectedFiles = data.generatedFiles;
                        }
                        if (data.tool_executions && Array.isArray(data.tool_executions)) {
                            collectedToolExecutions = data.tool_executions;
                        }
                        if (data.ocr) collectedMultimodal.ocr = data.ocr;
                        if (data.vision) collectedMultimodal.vision = data.vision;
                        onChunk("", true, fullResponse, collectedFiles, collectedToolExecutions, collectedMultimodal);
                        return;
                    }

                    const token = data.token || data.chunk || data.content || "";
                    console.log("RAW TOKEN:", JSON.stringify(token));
                    if (typeof token === "string" && token) {
                        fullResponse += token;
                        onChunk(token, false, fullResponse, collectedFiles, collectedToolExecutions);
                    }
                } catch (e) {
                    const normalized = payload.replace(/'/g, '"');
                    try {
                        const data = JSON.parse(normalized);
                        if (socket && data.event) {
                            socket.emit(data.event, {
                                conversationId,
                                messageId,
                                ...data
                            });
                        }
                        if (data.file) {
                            collectedFiles.push(data.file);
                        }
                        if (data.generatedFiles && Array.isArray(data.generatedFiles)) {
                            collectedFiles = data.generatedFiles;
                        }
                        if (data.tool_executions && Array.isArray(data.tool_executions)) {
                            collectedToolExecutions = data.tool_executions;
                        }
                        if (data.event === "agent:tool:result") {
                            collectedToolExecutions.push({
                                tool: data.tool,
                                arguments: data.arguments,
                                result: data.result,
                                stdout: data.stdout,
                                stderr: data.stderr,
                                exit_code: data.exit_code,
                                duration_seconds: data.duration_seconds,
                                success: data.success,
                            });
                        }
                        const token = data.token || data.chunk || data.content || "";
                        if (typeof token === "string" && token) {
                            fullResponse += token;
                            onChunk(token, false, fullResponse, collectedFiles, collectedToolExecutions);
                        }
                    } catch (fallbackErr) {
                        console.error("Failed to parse SSE line:", line, fallbackErr);
                    }
                }
            }
        });

        // Handle stream completion
        response.data.on("end", () => {
            console.log(`✅ Stream completed for message ${messageId}`);
            onChunk("", true, fullResponse, collectedFiles, collectedToolExecutions, collectedMultimodal); // Signal completion with files, tool executions, and multimodal data
        });

        // Handle stream errors
        response.data.on("error", (error) => {
            console.error("❌ Stream Error:", error);
            onError({
                message: "Stream interrupted",
                code: "STREAM_ERROR",
            });
        });

    } catch (error) {
        if (axios.isCancel(error) || error.name === 'AbortError' || error.name === 'CanceledError' || error.code === 'ERR_CANCELED') {
            console.log(`✅ Stream cancelled by client: ${messageId}`);
            return;
        }

        const errMsg = error.response?.data?.detail || error.response?.data?.message || error.message || "Streaming failed";
        console.error(
            "❌ Streaming Error:",
            errMsg
        );

        onError({
            message: errMsg,
            code: "STREAM_FAILED",
        });
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


/**
 * Get Ollama models
 */
async function getOllamaModels() {
    try {
        const response = await axios.get(
            `${PYTHON_AI_SERVICE_URL}/api/models/ollama`,
            {
                timeout: 10000,
            }
        );
        return response.data;
    } catch (error) {
        console.error(
            "❌ Failed to fetch Ollama models:",
            error.response?.data || error.message
        );
        throw new Error("Unable to fetch Ollama models");
    }
}

/**
 * Pull AI model
 */
async function pullAIModel(modelName) {
    try {
        const response = await axios.post(
            `${PYTHON_AI_SERVICE_URL}/api/models/pull`,
            { model: modelName },
            {
                timeout: 600000, // 10 minutes
                headers: {
                    "Content-Type": "application/json",
                },
            }
        );
        return response.data;
    } catch (error) {
        console.error(
            "❌ Failed to pull AI model:",
            error.response?.data || error.message
        );
        throw new Error("Unable to pull AI model");
    }
}

/**
 * Perform Multimodal Image Analysis (OCR + Moondream)
 */
async function analyzeImage({ image, prompt, filename }) {
    try {
        const response = await axios.post(
            `${PYTHON_AI_SERVICE_URL}/api/v1/vision/analyze`,
            { image, prompt, filename },
            {
                timeout: 300000,
                headers: {
                    "Content-Type": "application/json",
                },
            }
        );
        return response.data;
    } catch (error) {
        console.error(
            "❌ Multimodal Analysis Error:",
            error.response?.data || error.message
        );
        throw new Error(
            error.response?.data?.detail || "Multimodal vision analysis failed"
        );
    }
}

module.exports = {
    sendChatToAI,
    sendChatToAIStream,
    checkAIServiceHealth,
    getAIModels,
    processDocument,
    getOllamaModels,
    pullAIModel,
    analyzeImage
};