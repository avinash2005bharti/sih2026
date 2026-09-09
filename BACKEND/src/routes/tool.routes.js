const express = require("express");

const {
    createTool,
    getTools,
    getToolById,
    updateTool,
    deleteTool
} = require("../controllers/tool.controller");

const authMiddleware = require("../middlewares/auth.middleware");

const router = express.Router();

router.post("/", authMiddleware.authUser, createTool);

router.get("/", authMiddleware.authUser, getTools);

router.get("/:toolId", authMiddleware.authUser, getToolById);

router.put("/:toolId", authMiddleware.authUser, updateTool);

router.delete("/:toolId", authMiddleware.authUser, deleteTool);

module.exports = router;