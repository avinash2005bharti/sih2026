const express = require("express");
const axios = require("axios");
const { authUser, adminMiddleware } = require("../middlewares/auth.middleware");

const router = express.Router();
const PYTHON_AI_SERVICE_URL = process.env.PYTHON_AI_SERVICE_URL || "http://127.0.0.1:8000";

/**
 * GET /api/memory/health
 * Unified memory architecture health check.
 */
router.get("/health", async (req, res) => {
    try {
        const response = await axios.get(`${PYTHON_AI_SERVICE_URL}/api/memory/health`, { timeout: 8000 });
        return res.status(200).json(response.data);
    } catch (error) {
        return res.status(200).json({
            memory: "degraded",
            stm: "degraded",
            ltm: "degraded",
            qdrant: "unknown",
            neo4j: "unknown",
            mem0: "unknown",
            ollama: "unknown",
            embedding_model: "unknown",
            error: error.message
        });
    }
});

/**
 * GET /api/memory/search
 * Semantic memory search isolated by user.
 */
router.get("/search", authUser, async (req, res) => {
    try {
        const { q, limit = 5, score_threshold = 0.60 } = req.query;
        if (!q) {
            return res.status(400).json({ message: "Search query 'q' is required" });
        }

        const response = await axios.get(`${PYTHON_AI_SERVICE_URL}/api/memory/search`, {
            params: {
                q,
                user_id: req.user._id.toString(),
                limit,
                score_threshold
            },
            timeout: 10000
        });

        return res.status(200).json(response.data);
    } catch (error) {
        console.error("❌ Memory Search Error:", error.response?.data || error.message);
        return res.status(error.response?.status || 500).json({
            message: error.response?.data?.detail || "Memory search failed"
        });
    }
});

/**
 * POST /api/memory
 * Record a user preference, fact, or instruction.
 */
router.post("/", authUser, async (req, res) => {
    try {
        const { content, memory_type = "fact", conversation_id, importance = 0.8 } = req.body;
        if (!content || !content.trim()) {
            return res.status(400).json({ message: "Memory content is required" });
        }

        const response = await axios.post(
            `${PYTHON_AI_SERVICE_URL}/api/memory`,
            {
                content: content.trim(),
                user_id: req.user._id.toString(),
                memory_type,
                conversation_id,
                importance
            },
            { timeout: 15000 }
        );

        return res.status(201).json(response.data);
    } catch (error) {
        console.error("❌ Record Memory Error:", error.response?.data || error.message);
        return res.status(error.response?.status || 500).json({
            message: error.response?.data?.detail || "Failed to record memory"
        });
    }
});

/**
 * DELETE /api/memory/:memory_id
 * Delete a memory. Normal users can delete their own; admins can delete any.
 */
router.delete("/:memory_id", authUser, async (req, res) => {
    try {
        const { memory_id } = req.params;
        const response = await axios.delete(
            `${PYTHON_AI_SERVICE_URL}/api/memory/${memory_id}`,
            {
                params: {
                    user_id: req.user._id.toString()
                },
                timeout: 10000
            }
        );

        return res.status(200).json(response.data);
    } catch (error) {
        console.error("❌ Delete Memory Error:", error.response?.data || error.message);
        return res.status(error.response?.status || 500).json({
            message: error.response?.data?.detail || "Failed to delete memory"
        });
    }
});

/**
 * GET /api/memory/graph
 * Query Neo4j entity relationships for query terms.
 */
router.get("/graph", authUser, async (req, res) => {
    try {
        const { query } = req.query;
        if (!query) {
            return res.status(400).json({ message: "Query string is required" });
        }

        const response = await axios.get(`${PYTHON_AI_SERVICE_URL}/api/memory/graph`, {
            params: {
                query,
                user_id: req.user._id.toString()
            },
            timeout: 10000
        });

        return res.status(200).json(response.data);
    } catch (error) {
        return res.status(500).json({
            message: error.response?.data?.detail || "Failed to query graph context"
        });
    }
});

module.exports = router;
