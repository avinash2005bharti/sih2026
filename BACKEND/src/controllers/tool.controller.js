const Tool = require("../models/tool.model");


// CREATE TOOL
async function createTool(req, res) {
    try {
        const {
            name,
            description,
            type,
            endpoint,
            method,
            parameters,
            requiresApproval
        } = req.body;

        if (!name || !description || !type) {
            return res.status(400).json({
                success: false,
                message: "Name, description and type are required"
            });
        }

        const tool = await Tool.create({
            name,
            description,
            type,
            endpoint,
            method,
            parameters,
            requiresApproval
        });

        return res.status(201).json({
            success: true,
            message: "Tool created successfully",
            tool
        });

    } catch (error) {
        console.error("Create Tool Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to create tool"
        });
    }
}


// GET TOOLS
async function getTools(req, res) {
    try {
        const tools = await Tool.find({
            isActive: true
        }).sort({
            createdAt: -1
        });

        return res.status(200).json({
            success: true,
            tools
        });

    } catch (error) {
        console.error("Get Tools Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch tools"
        });
    }
}


// GET TOOL
async function getToolById(req, res) {
    try {
        const { toolId } = req.params;

        const tool = await Tool.findById(toolId);

        if (!tool) {
            return res.status(404).json({
                success: false,
                message: "Tool not found"
            });
        }

        return res.status(200).json({
            success: true,
            tool
        });

    } catch (error) {
        console.error("Get Tool Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch tool"
        });
    }
}


// UPDATE TOOL
async function updateTool(req, res) {
    try {
        const { toolId } = req.params;

        const tool = await Tool.findByIdAndUpdate(
            toolId,
            req.body,
            {
                new: true,
                runValidators: true
            }
        );

        if (!tool) {
            return res.status(404).json({
                success: false,
                message: "Tool not found"
            });
        }

        return res.status(200).json({
            success: true,
            message: "Tool updated successfully",
            tool
        });

    } catch (error) {
        console.error("Update Tool Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to update tool"
        });
    }
}


// DELETE TOOL
async function deleteTool(req, res) {
    try {
        const { toolId } = req.params;

        const tool = await Tool.findByIdAndUpdate(
            toolId,
            {
                isActive: false
            },
            {
                new: true
            }
        );

        if (!tool) {
            return res.status(404).json({
                success: false,
                message: "Tool not found"
            });
        }

        return res.status(200).json({
            success: true,
            message: "Tool deleted successfully"
        });

    } catch (error) {
        console.error("Delete Tool Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to delete tool"
        });
    }
}


module.exports = {
    createTool,
    getTools,
    getToolById,
    updateTool,
    deleteTool
};