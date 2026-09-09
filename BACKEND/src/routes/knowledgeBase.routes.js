const express = require("express");

const {
    createKnowledgeBase,
    getKnowledgeBases,
    getKnowledgeBaseById,
    updateKnowledgeBase,
    deleteKnowledgeBase
} = require("../controllers/knowledgeBase.controller");

const authMiddleware = require("../middlewares/auth.middleware");

const router = express.Router();

router.post("/", authMiddleware.authUser, createKnowledgeBase);

router.get("/", authMiddleware.authUser, getKnowledgeBases);

router.get("/:knowledgeBaseId", authMiddleware.authUser, getKnowledgeBaseById);

router.put("/:knowledgeBaseId", authMiddleware.authUser, updateKnowledgeBase);

router.delete("/:knowledgeBaseId", authMiddleware.authUser, deleteKnowledgeBase);

module.exports = router;