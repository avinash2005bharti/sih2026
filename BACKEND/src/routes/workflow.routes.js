const express = require("express");

const {
    createWorkflow,
    getWorkflows,
    getWorkflowById,
    updateWorkflow,
    deleteWorkflow
} = require("../controllers/workflow.controller");

const authMiddleware = require("../middlewares/auth.middleware");

const router = express.Router();

router.post("/", authMiddleware.authUser, createWorkflow);

router.get("/", authMiddleware.authUser, getWorkflows);

router.get("/:workflowId", authMiddleware.authUser, getWorkflowById);

router.put("/:workflowId", authMiddleware.authUser, updateWorkflow);

router.delete("/:workflowId", authMiddleware.authUser, deleteWorkflow);

module.exports = router;