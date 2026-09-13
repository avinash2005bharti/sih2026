const KnowledgeBase = require("../models/knowledgeBase.model");


// CREATE KNOWLEDGE BASE
async function createKnowledgeBase(req, res) {
    try {
        const userId = req.user._id;

        const {
            name,
            description,
            collectionName,
            embeddingModel,
            vectorDimension
        } = req.body;

        if (!name || !collectionName || !vectorDimension) {
            return res.status(400).json({
                success: false,
                message: "Name, collectionName and vectorDimension are required"
            });
        }

        const knowledgeBase = await KnowledgeBase.create({
            name,
            description,
            owner: userId,
            collectionName,
            embeddingModel,
            vectorDimension,
            documents: []
        });

        return res.status(201).json({
            success: true,
            message: "Knowledge base created successfully",
            knowledgeBase
        });

    } catch (error) {
        console.error("Create Knowledge Base Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to create knowledge base"
        });
    }
}


// GET KNOWLEDGE BASES
async function getKnowledgeBases(req, res) {
    try {
        const userId = req.user._id;

        const knowledgeBases = await KnowledgeBase.find({
            owner: userId,
            isActive: true
        })
            .populate("embeddingModel", "name displayName modelType")
            .populate("documents", "name documentType processingStatus")
            .sort({ createdAt: -1 });

        return res.status(200).json({
            success: true,
            knowledgeBases
        });

    } catch (error) {
        console.error("Get Knowledge Bases Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch knowledge bases"
        });
    }
}


// GET SINGLE KNOWLEDGE BASE
async function getKnowledgeBaseById(req, res) {
    try {
        const userId = req.user._id;
        const { knowledgeBaseId } = req.params;

        const knowledgeBase = await KnowledgeBase.findOne({
            _id: knowledgeBaseId,
            owner: userId
        })
            .populate("embeddingModel")
            .populate("documents");

        if (!knowledgeBase) {
            return res.status(404).json({
                success: false,
                message: "Knowledge base not found"
            });
        }

        return res.status(200).json({
            success: true,
            knowledgeBase
        });

    } catch (error) {
        console.error("Get Knowledge Base Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch knowledge base"
        });
    }
}


// UPDATE
async function updateKnowledgeBase(req, res) {
    try {
        const userId = req.user._id;
        const { knowledgeBaseId } = req.params;

        const knowledgeBase = await KnowledgeBase.findOneAndUpdate(
            {
                _id: knowledgeBaseId,
                owner: userId
            },
            req.body,
            {
                new: true,
                runValidators: true
            }
        );

        if (!knowledgeBase) {
            return res.status(404).json({
                success: false,
                message: "Knowledge base not found"
            });
        }

        return res.status(200).json({
            success: true,
            message: "Knowledge base updated successfully",
            knowledgeBase
        });

    } catch (error) {
        console.error("Update Knowledge Base Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to update knowledge base"
        });
    }
}


// DELETE
async function deleteKnowledgeBase(req, res) {
    try {
        const userId = req.user._id;
        const { knowledgeBaseId } = req.params;

        const knowledgeBase = await KnowledgeBase.findOneAndUpdate(
            {
                _id: knowledgeBaseId,
                owner: userId
            },
            {
                isActive: false
            },
            {
                new: true
            }
        );

        if (!knowledgeBase) {
            return res.status(404).json({
                success: false,
                message: "Knowledge base not found"
            });
        }

        return res.status(200).json({
            success: true,
            message: "Knowledge base deleted successfully"
        });

    } catch (error) {
        console.error("Delete Knowledge Base Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to delete knowledge base"
        });
    }
}


module.exports = {
    createKnowledgeBase,
    getKnowledgeBases,
    getKnowledgeBaseById,
    updateKnowledgeBase,
    deleteKnowledgeBase
};