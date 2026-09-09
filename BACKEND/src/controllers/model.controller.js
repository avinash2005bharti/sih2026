const AIModel = require("../models/aiModel.model");


// CREATE MODEL
async function createModel(req, res) {
    try {
        const {
            name,
            displayName,
            provider,
            modelType,
            modelPath,
            endpoint,
            capabilities,
            contextWindow,
            parameters,
            quantization,
            isLocal,
            priority
        } = req.body;

        if (!name || !displayName || !provider || !modelType) {
            return res.status(400).json({
                success: false,
                message: "Required model fields are missing"
            });
        }

        const existingModel = await AIModel.findOne({ name });

        if (existingModel) {
            return res.status(409).json({
                success: false,
                message: "Model already exists"
            });
        }

        const model = await AIModel.create({
            name,
            displayName,
            provider,
            modelType,
            modelPath,
            endpoint,
            capabilities,
            contextWindow,
            parameters,
            quantization,
            isLocal,
            priority
        });

        return res.status(201).json({
            success: true,
            message: "AI model created successfully",
            model
        });

    } catch (error) {
        console.error("Create Model Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to create model"
        });
    }
}


// GET MODELS
async function getModels(req, res) {
    try {
        const models = await AIModel.find({
            isActive: true
        }).sort({
            priority: 1,
            createdAt: -1
        });

        return res.status(200).json({
            success: true,
            models
        });

    } catch (error) {
        console.error("Get Models Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch models"
        });
    }
}


// GET MODEL
async function getModelById(req, res) {
    try {
        const { modelId } = req.params;

        const model = await AIModel.findById(modelId);

        if (!model) {
            return res.status(404).json({
                success: false,
                message: "Model not found"
            });
        }

        return res.status(200).json({
            success: true,
            model
        });

    } catch (error) {
        console.error("Get Model Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch model"
        });
    }
}


// UPDATE MODEL
async function updateModel(req, res) {
    try {
        const { modelId } = req.params;

        const model = await AIModel.findByIdAndUpdate(
            modelId,
            req.body,
            {
                new: true,
                runValidators: true
            }
        );

        if (!model) {
            return res.status(404).json({
                success: false,
                message: "Model not found"
            });
        }

        return res.status(200).json({
            success: true,
            message: "Model updated successfully",
            model
        });

    } catch (error) {
        console.error("Update Model Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to update model"
        });
    }
}


// DELETE MODEL
async function deleteModel(req, res) {
    try {
        const { modelId } = req.params;

        const model = await AIModel.findByIdAndUpdate(
            modelId,
            {
                isActive: false
            },
            {
                new: true
            }
        );

        if (!model) {
            return res.status(404).json({
                success: false,
                message: "Model not found"
            });
        }

        return res.status(200).json({
            success: true,
            message: "Model deleted successfully"
        });

    } catch (error) {
        console.error("Delete Model Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to delete model"
        });
    }
}


module.exports = {
    createModel,
    getModels,
    getModelById,
    updateModel,
    deleteModel
};