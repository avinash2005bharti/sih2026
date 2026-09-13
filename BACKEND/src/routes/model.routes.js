const express = require("express");

const {
    createModel,
    getModels,
    getModelById,
    updateModel,
    deleteModel,
    getOllamaModels,
    pullModel,
    healthCheck,
    getModelRoles,
    updateModelRole
} = require("../controllers/model.controller");

const authMiddleware = require("../middlewares/auth.middleware");

const router = express.Router();

router.get("/ollama", authMiddleware.authUser, getOllamaModels);
router.post("/pull", authMiddleware.authUser, authMiddleware.adminMiddleware, pullModel);
router.get("/health", authMiddleware.authUser, healthCheck);
router.get("/roles", authMiddleware.authUser, getModelRoles);
router.put("/roles", authMiddleware.authUser, authMiddleware.adminMiddleware, updateModelRole);

router.post("/", authMiddleware.authUser, authMiddleware.adminMiddleware, createModel);

router.get("/", authMiddleware.authUser, getModels);

router.get("/:modelId", authMiddleware.authUser, getModelById);

router.put("/:modelId", authMiddleware.authUser, authMiddleware.adminMiddleware, updateModel);

router.delete("/:modelId", authMiddleware.authUser, authMiddleware.adminMiddleware, deleteModel);

module.exports = router;