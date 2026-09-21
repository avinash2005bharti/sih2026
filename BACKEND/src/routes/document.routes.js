const express = require("express");
const path = require("path");
const fs = require("fs");
const multer = require("multer");

const {
    uploadDocument,
    getDocuments,
    getDocumentById,
    updateDocument,
    deleteDocument
} = require("../controllers/document.controller");

const authMiddleware = require("../middlewares/auth.middleware");

// Configure local storage for uploaded documents
const uploadDir = path.resolve(__dirname, "../../uploads/documents");
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, uploadDir);
    },
    filename: function (req, file, cb) {
        const uniquePrefix = Date.now() + "-" + Math.round(Math.random() * 1e6);
        const safeOriginal = file.originalname.replace(/[^a-zA-Z0-9_.-]/g, "_");
        cb(null, `${uniquePrefix}_${safeOriginal}`);
    }
});

const upload = multer({
    storage: storage,
    limits: { fileSize: 150 * 1024 * 1024 } // 150 MB
});

const router = express.Router();

router.post("/", authMiddleware.authUser, upload.single("file"), uploadDocument);

router.get("/", authMiddleware.authUser, getDocuments);

router.get("/:documentId", authMiddleware.authUser, getDocumentById);

router.put("/:documentId", authMiddleware.authUser, updateDocument);

router.delete("/:documentId", authMiddleware.authUser, deleteDocument);

module.exports = router;