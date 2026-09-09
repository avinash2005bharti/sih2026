const express = require("express");

const {
    uploadDocument,
    getDocuments,
    getDocumentById,
    deleteDocument
} = require("../controllers/document.controller");

const authMiddleware = require("../middlewares/auth.middleware");

const router = express.Router();

router.post("/", authMiddleware.authUser, uploadDocument);

router.get("/", authMiddleware.authUser, getDocuments);

router.get("/:documentId", authMiddleware.authUser, getDocumentById);

router.delete("/:documentId", authMiddleware.authUser, deleteDocument);

module.exports = router;