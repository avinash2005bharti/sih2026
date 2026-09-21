const fs = require("fs");
const path = require("path");
const Document = require("../models/document.model");
const pythonService = require("../services/python.service");

// UPLOAD & PROCESS DOCUMENT
async function uploadDocument(req, res) {
    try {
        const userId = req.user._id;

        let name = req.body.name;
        let originalName = req.body.originalName;
        let mimeType = req.body.mimeType || "application/pdf";
        let fileSize = Number(req.body.fileSize) || 0;
        let filePath = req.body.filePath;
        let storageType = req.body.storageType || "local";
        let documentType = req.body.documentType || "manual";

        // If file uploaded through multer
        if (req.file) {
            originalName = req.file.originalname;
            name = name || req.file.originalname.replace(/\.[^/.]+$/, "");
            mimeType = req.file.mimetype;
            fileSize = req.file.size;
            filePath = req.file.path;

            const ext = path.extname(req.file.originalname).toLowerCase();
            if (ext === ".pdf") documentType = "pdf";
            else if ([".png", ".jpg", ".jpeg"].includes(ext)) documentType = "image";
            else if ([".doc", ".docx"].includes(ext)) documentType = "word";
            else if ([".xls", ".xlsx", ".csv"].includes(ext)) documentType = "excel";
            else if ([".txt", ".md", ".log"].includes(ext)) documentType = "text";
        }

        if (!name) {
            return res.status(400).json({
                success: false,
                message: "Document name is required"
            });
        }

        if (!filePath) {
            return res.status(400).json({
                success: false,
                message: "A document file or filePath is required"
            });
        }

        // 1. Create document entry in MongoDB with processing status
        const isAdmin = Boolean(req.user.isAdmin || req.user.role === "admin");
        const uploaderName = req.user.fullName
            ? `${req.user.fullName.firstName || ""} ${req.user.fullName.lastName || ""}`.trim()
            : req.user.email || "User";
        const uploaderEmail = req.user.email || "";
        const uploaderRole = req.user.role || (isAdmin ? "admin" : "client");
        const uploaderDepartment = req.user.department || "";

        // 1. Create document entry in MongoDB with processing status and RBAC flags
        const document = await Document.create({
            uploadedBy: userId,
            name,
            originalName: originalName || name,
            mimeType,
            fileSize,
            filePath,
            storageType,
            documentType,
            processingStatus: "processing",
            isUploadedByAdmin: isAdmin,
            uploaderRole,
            uploaderInfo: {
                name: uploaderName,
                email: uploaderEmail,
                role: uploaderRole,
                department: uploaderDepartment
            },
            metadata: {
                chunksCount: 0
            }
        });

        // 2. Trigger Python AI Service chunking, embeddings, and Qdrant ingestion
        try {
            console.log(`[DocumentController] Dispatching document '${name}' (${document._id}) to Python AI service...`);
            const aiResult = await pythonService.processDocument({
                filePath,
                documentId: document._id.toString(),
                userId: userId.toString(),
                name
            });

            console.log(`[DocumentController] Document indexed successfully:`, aiResult);

            const chunksIndexed = aiResult.details?.chunks_indexed || 0;
            const charCount = aiResult.details?.character_count || 0;
            const previewText = aiResult.details?.extracted_text_preview || "";

            // Update MongoDB record with processed status and indexing stats
            document.processingStatus = "processed";
            document.extractedText = previewText;
            document.metadata = {
                chunksCount: chunksIndexed,
                characterCount: charCount,
                processedAt: new Date()
            };
            await document.save();

        } catch (aiError) {
            console.error(`[DocumentController] AI vectorization warning for doc ${document._id}:`, aiError.message);
            document.processingStatus = "failed";
            document.metadata = {
                error: aiError.message,
                failedAt: new Date()
            };
            await document.save();
        }

        return res.status(201).json({
            success: true,
            message: document.processingStatus === "processed"
                ? `Document uploaded, chunked into ${document.metadata?.chunksCount || 0} vectors and indexed into Qdrant.`
                : "Document uploaded but vector processing encountered an error.",
            document
        });

    } catch (error) {
        console.error("Upload Document Error:", error);
        return res.status(500).json({
            success: false,
            message: error.message || "Failed to upload document"
        });
    }
}


// GET DOCUMENTS (WITH RBAC VISIBILITY RULES)
async function getDocuments(req, res) {
    try {
        const userId = req.user._id;
        const isAdmin = Boolean(req.user.isAdmin || req.user.role === "admin");
        const User = require("../models/user.model");

        let filter = {};
        if (!isAdmin) {
            // Find all admin user IDs so any document uploaded by an admin is included
            const adminUsers = await User.find({
                $or: [{ isAdmin: true }, { role: "admin" }]
            }).select("_id");
            const adminIds = adminUsers.map(u => u._id);

            // Clients see:
            // 1. All documents uploaded by ANY Admin (isUploadedByAdmin: true OR uploadedBy in adminIds)
            // 2. Documents uploaded by this specific client (uploadedBy: userId)
            // 3. System / global assets (uploadedBy: null / undefined)
            // Clients do NOT see documents uploaded by other clients.
            filter = {
                $or: [
                    { uploadedBy: userId },
                    { isUploadedByAdmin: true },
                    { uploadedBy: { $in: adminIds } },
                    { uploadedBy: { $exists: false } },
                    { uploadedBy: null }
                ]
            };
        } else {
            // Admin sees ALL documents uploaded across the system
            filter = {};
        }

        const documents = await Document.find(filter)
            .populate("uploadedBy", "fullName email role department isAdmin")
            .sort({ createdAt: -1 })
            .lean();

        // Format documents with permissions and uploader information
        const formattedDocs = documents.map(doc => {
            const docIsAdmin = Boolean(
                doc.isUploadedByAdmin ||
                (doc.uploadedBy && (doc.uploadedBy.isAdmin || doc.uploadedBy.role === "admin")) ||
                !doc.uploadedBy
            );
            const isOwner = doc.uploadedBy && (
                doc.uploadedBy._id ? doc.uploadedBy._id.toString() === userId.toString() : doc.uploadedBy.toString() === userId.toString()
            );

            // Can modify: Admin can modify/delete; Client can only modify/delete their own non-admin docs
            const canModify = isAdmin || (isOwner && !docIsAdmin);

            let uploaderDisplay = "Admin (Global Asset)";
            if (doc.uploaderInfo?.name) {
                uploaderDisplay = `${doc.uploaderInfo.name} (${doc.uploaderInfo.role || doc.uploaderRole || "User"})`;
            } else if (doc.uploadedBy && typeof doc.uploadedBy === "object") {
                const fName = doc.uploadedBy.fullName
                    ? `${doc.uploadedBy.fullName.firstName || ""} ${doc.uploadedBy.fullName.lastName || ""}`.trim()
                    : doc.uploadedBy.email;
                uploaderDisplay = `${fName} (${doc.uploadedBy.role || "User"})`;
            }

            return {
                ...doc,
                isUploadedByAdmin: docIsAdmin,
                canModify,
                isOwner,
                uploaderDisplay,
                uploadedByName: doc.uploaderInfo?.name || (doc.uploadedBy?.fullName ? `${doc.uploadedBy.fullName.firstName || ""} ${doc.uploadedBy.fullName.lastName || ""}`.trim() : "Unknown"),
                uploadedByEmail: doc.uploaderInfo?.email || doc.uploadedBy?.email || "",
                uploadTime: doc.createdAt
            };
        });

        return res.status(200).json({
            success: true,
            count: formattedDocs.length,
            documents: formattedDocs
        });

    } catch (error) {
        console.error("Get Documents Error:", error);
        return res.status(500).json({
            success: false,
            message: "Failed to fetch documents"
        });
    }
}


// GET DOCUMENT BY ID (ENFORCING CLIENT ISOLATION)
async function getDocumentById(req, res) {
    try {
        const userId = req.user._id;
        const isAdmin = Boolean(req.user.isAdmin || req.user.role === "admin");
        const { documentId } = req.params;
        const User = require("../models/user.model");

        const document = await Document.findById(documentId)
            .populate("uploadedBy", "fullName email role department isAdmin")
            .lean();

        if (!document) {
            return res.status(404).json({
                success: false,
                message: "Document not found"
            });
        }

        const adminUsers = await User.find({
            $or: [{ isAdmin: true }, { role: "admin" }]
        }).select("_id");
        const adminIdStrings = adminUsers.map(u => u._id.toString());

        const docUploaderId = document.uploadedBy?._id
            ? document.uploadedBy._id.toString()
            : (document.uploadedBy ? document.uploadedBy.toString() : null);

        const docIsAdmin = Boolean(
            document.isUploadedByAdmin ||
            (docUploaderId && adminIdStrings.includes(docUploaderId)) ||
            (document.uploadedBy && (document.uploadedBy.isAdmin || document.uploadedBy.role === "admin")) ||
            !docUploaderId
        );
        const isOwner = docUploaderId && (docUploaderId === userId.toString());

        // RBAC Enforcement:
        // Admin sees all.
        // Client sees if it's an admin-uploaded doc OR if the client owns it.
        if (!isAdmin && !docIsAdmin && !isOwner) {
            return res.status(403).json({
                success: false,
                message: "Access denied: You do not have permission to access another client's document."
            });
        }

        const canModify = isAdmin || (isOwner && !docIsAdmin);

        return res.status(200).json({
            success: true,
            document: {
                ...document,
                isUploadedByAdmin: docIsAdmin,
                canModify,
                isOwner,
                uploaderDisplay: document.uploaderInfo?.name || (document.uploadedBy?.fullName ? `${document.uploadedBy.fullName.firstName || ""} ${document.uploadedBy.fullName.lastName || ""}`.trim() : "Unknown"),
                uploadedByEmail: document.uploaderInfo?.email || document.uploadedBy?.email || ""
            }
        });

    } catch (error) {
        console.error("Get Document Error:", error);
        return res.status(500).json({
            success: false,
            message: "Failed to fetch document"
        });
    }
}


// UPDATE DOCUMENT (ADMIN-UPLOADED DOCS ARE READ-ONLY TO CLIENTS)
async function updateDocument(req, res) {
    try {
        const userId = req.user._id;
        const isAdmin = Boolean(req.user.isAdmin || req.user.role === "admin");
        const { documentId } = req.params;
        const { name, documentType, storageType } = req.body;

        const document = await Document.findById(documentId)
            .populate("uploadedBy", "fullName email role department isAdmin");

        if (!document) {
            return res.status(404).json({
                success: false,
                message: "Document not found"
            });
        }

        const docIsAdmin = Boolean(
            document.isUploadedByAdmin ||
            (document.uploadedBy && (document.uploadedBy.isAdmin || document.uploadedBy.role === "admin"))
        );
        const isOwner = document.uploadedBy && (
            document.uploadedBy._id ? document.uploadedBy._id.toString() === userId.toString() : document.uploadedBy.toString() === userId.toString()
        );

        // If document was uploaded by admin and requester is not an admin, forbid modification!
        if (docIsAdmin && !isAdmin) {
            return res.status(403).json({
                success: false,
                message: "Permission denied: Documents uploaded by administrator are official repository assets and cannot be modified by clients."
            });
        }

        // If client document, only admin or the client owner can modify
        if (!isAdmin && !isOwner) {
            return res.status(403).json({
                success: false,
                message: "Permission denied: You cannot modify another client's document."
            });
        }

        if (name) document.name = name;
        if (documentType) document.documentType = documentType;
        if (storageType) document.storageType = storageType;

        await document.save();

        return res.status(200).json({
            success: true,
            message: "Document updated successfully",
            document
        });

    } catch (error) {
        console.error("Update Document Error:", error);
        return res.status(500).json({
            success: false,
            message: "Failed to update document"
        });
    }
}


// DELETE DOCUMENT (ADMIN-UPLOADED DOCS CANNOT BE DELETED BY CLIENTS)
async function deleteDocument(req, res) {
    try {
        const userId = req.user._id;
        const isAdmin = Boolean(req.user.isAdmin || req.user.role === "admin");
        const { documentId } = req.params;

        const document = await Document.findById(documentId)
            .populate("uploadedBy", "fullName email role department isAdmin");

        if (!document) {
            return res.status(404).json({
                success: false,
                message: "Document not found"
            });
        }

        const docIsAdmin = Boolean(
            document.isUploadedByAdmin ||
            (document.uploadedBy && (document.uploadedBy.isAdmin || document.uploadedBy.role === "admin"))
        );
        const isOwner = document.uploadedBy && (
            document.uploadedBy._id ? document.uploadedBy._id.toString() === userId.toString() : document.uploadedBy.toString() === userId.toString()
        );

        // If document was uploaded by admin and requester is not an admin, forbid deletion!
        if (docIsAdmin && !isAdmin) {
            return res.status(403).json({
                success: false,
                message: "Permission denied: Documents uploaded by administrator are official repository assets and cannot be deleted by clients."
            });
        }

        // If client document, only admin or the client owner can delete
        if (!isAdmin && !isOwner) {
            return res.status(403).json({
                success: false,
                message: "Permission denied: You cannot delete another client's document."
            });
        }

        // 1. Delete vector points from Qdrant via Python AI Service
        try {
            await pythonService.deleteDocumentFromAI(documentId);
            console.log(`[DocumentController] Requested deletion of vectors in Qdrant for doc ${documentId}`);
        } catch (aiDelErr) {
            console.warn(`[DocumentController] AI deletion notice:`, aiDelErr.message);
        }

        // 2. Remove physical file from disk if present
        if (document.filePath && fs.existsSync(document.filePath)) {
            try {
                fs.unlinkSync(document.filePath);
                console.log(`[DocumentController] Deleted disk file: ${document.filePath}`);
            } catch (fileErr) {
                console.warn(`[DocumentController] File unlink error:`, fileErr.message);
            }
        }

        // 3. Delete document from MongoDB
        await Document.findByIdAndDelete(documentId);

        return res.status(200).json({
            success: true,
            message: "Document successfully deleted from repository and vector store"
        });

    } catch (error) {
        console.error("Delete Document Error:", error);
        return res.status(500).json({
            success: false,
            message: "Failed to delete document"
        });
    }
}


module.exports = {
    uploadDocument,
    getDocuments,
    getDocumentById,
    updateDocument,
    deleteDocument
};