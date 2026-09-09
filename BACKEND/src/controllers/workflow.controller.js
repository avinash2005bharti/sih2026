const Workflow = require("../models/workflow.model");


// CREATE WORKFLOW
async function createWorkflow(req, res) {
    try {
        const userId = req.user._id;

        const {
            name,
            description,
            steps
        } = req.body;

        if (!name || !steps || !steps.length) {
            return res.status(400).json({
                success: false,
                message: "Workflow name and steps are required"
            });
        }

        const workflow = await Workflow.create({
            name,
            description,
            createdBy: userId,
            steps
        });

        return res.status(201).json({
            success: true,
            message: "Workflow created successfully",
            workflow
        });

    } catch (error) {
        console.error("Create Workflow Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to create workflow"
        });
    }
}


// GET WORKFLOWS
async function getWorkflows(req, res) {
    try {
        const userId = req.user._id;

        const workflows = await Workflow.find({
            $or: [
                { createdBy: userId },
                { createdBy: null }
            ],
            isActive: true
        })
            .populate("steps.agent", "name type")
            .sort({ createdAt: -1 });

        return res.status(200).json({
            success: true,
            workflows
        });

    } catch (error) {
        console.error("Get Workflows Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch workflows"
        });
    }
}


// GET WORKFLOW
async function getWorkflowById(req, res) {
    try {
        const { workflowId } = req.params;

        const workflow = await Workflow.findById(workflowId)
            .populate("steps.agent");

        if (!workflow) {
            return res.status(404).json({
                success: false,
                message: "Workflow not found"
            });
        }

        return res.status(200).json({
            success: true,
            workflow
        });

    } catch (error) {
        console.error("Get Workflow Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch workflow"
        });
    }
}


// UPDATE WORKFLOW
async function updateWorkflow(req, res) {
    try {
        const { workflowId } = req.params;

        const workflow = await Workflow.findByIdAndUpdate(
            workflowId,
            req.body,
            {
                new: true,
                runValidators: true
            }
        );

        if (!workflow) {
            return res.status(404).json({
                success: false,
                message: "Workflow not found"
            });
        }

        return res.status(200).json({
            success: true,
            message: "Workflow updated successfully",
            workflow
        });

    } catch (error) {
        console.error("Update Workflow Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to update workflow"
        });
    }
}


// DELETE WORKFLOW
async function deleteWorkflow(req, res) {
    try {
        const { workflowId } = req.params;

        const workflow = await Workflow.findByIdAndUpdate(
            workflowId,
            {
                isActive: false
            },
            {
                new: true
            }
        );

        if (!workflow) {
            return res.status(404).json({
                success: false,
                message: "Workflow not found"
            });
        }

        return res.status(200).json({
            success: true,
            message: "Workflow deleted successfully"
        });

    } catch (error) {
        console.error("Delete Workflow Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to delete workflow"
        });
    }
}


module.exports = {
    createWorkflow,
    getWorkflows,
    getWorkflowById,
    updateWorkflow,
    deleteWorkflow
};