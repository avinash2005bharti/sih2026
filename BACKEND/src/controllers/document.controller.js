const Document = require("../models/document.model");


// UPLOAD DOCUMENT
async function uploadDocument(req, res) {
    try {
        const userId = req.user._id;

        const {
            name,
            originalName,
            mimeType,
            fileSize,
            filePath,
            storageType,
            documentType
        } = req.body;

        if (!name || !filePath) {
            return res.status(400).json({
                success: false,
                message: "Document name and filePath are required"
            });
        }

        const document = await Document.create({
            uploadedBy: userId,
            name,
            originalName,
            mimeType,
            fileSize,
            filePath,
            storageType,
            documentType,
            processingStatus: "uploaded"
        });

        return res.status(201).json({
            success: true,
            message: "Document uploaded successfully",
            document
        });

    } catch (error) {
        console.error("Upload Document Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to upload document"
        });
    }
}


// GET DOCUMENTS
async function getDocuments(req, res) {
    try {
        const userId = req.user._id;

        const documents = await Document.find({
            uploadedBy: userId
        })
            .sort({ createdAt: -1 });

        return res.status(200).json({
            success: true,
            documents
        });

    } catch (error) {
        console.error("Get Documents Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch documents"
        });
    }
}


// GET DOCUMENT
async function getDocumentById(req, res) {
    try {
        const userId = req.user._id;
        const { documentId } = req.params;

        const document = await Document.findOne({
            _id: documentId,
            uploadedBy: userId
        });

        if (!document) {
            return res.status(404).json({
                success: false,
                message: "Document not found"
            });
        }

        return res.status(200).json({
            success: true,
            document
        });

    } catch (error) {
        console.error("Get Document Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch document"
        });
    }
}


// DELETE DOCUMENT
async function deleteDocument(req, res) {
    try {
        const userId = req.user._id;
        const { documentId } = req.params;

        const document = await Document.findOneAndDelete({
            _id: documentId,
            uploadedBy: userId
        });

        if (!document) {
            return res.status(404).json({
                success: false,
                message: "Document not found"
            });
        }

        return res.status(200).json({
            success: true,
            message: "Document deleted successfully"
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
    deleteDocument
};