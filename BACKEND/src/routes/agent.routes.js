const express = require("express");

const {
    createAgent,
    getAgents,
    getAgentById,
    updateAgent,
    deleteAgent
} = require("../controllers/agent.controller");

const authMiddleware = require("../middlewares/auth.middleware");

const router = express.Router();

router.post("/", authMiddleware.authUser, createAgent);

router.get("/", authMiddleware.authUser, getAgents);

router.get("/:agentId", authMiddleware.authUser, getAgentById);

router.put("/:agentId", authMiddleware.authUser, updateAgent);

router.delete("/:agentId", authMiddleware.authUser, deleteAgent);

module.exports = router;