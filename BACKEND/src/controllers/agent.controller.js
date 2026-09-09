const Agent = require("../models/agent.model");

// CREATE AGENT
async function createAgent(req, res) {
    try {
        const {
            name,
            description,
            type,
            model,
            systemPrompt,
            capabilities,
            tools,
            knowledgeBases,
            temperature,
            maxTokens
        } = req.body;

        if (!name || !type || !systemPrompt) {
            return res.status(400).json({
                success: false,
                message: "Name, type and systemPrompt are required"
            });
        }

        const agent = await Agent.create({
            name,
            description,
            type,
            model,
            systemPrompt,
            capabilities,
            tools,
            knowledgeBases,
            temperature,
            maxTokens
        });

        return res.status(201).json({
            success: true,
            message: "Agent created successfully",
            agent
        });

    } catch (error) {
        console.error("Create Agent Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to create agent"
        });
    }
}


// GET ALL AGENTS
async function getAgents(req, res) {
    try {
        const agents = await Agent.find({
            isActive: true
        })
            .populate("model", "name displayName provider modelType")
            .populate("tools", "name type")
            .populate("knowledgeBases", "name collectionName")
            .sort({ createdAt: -1 });

        return res.status(200).json({
            success: true,
            agents
        });

    } catch (error) {
        console.error("Get Agents Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch agents"
        });
    }
}


// GET SINGLE AGENT
async function getAgentById(req, res) {
    try {
        const { agentId } = req.params;

        const agent = await Agent.findById(agentId)
            .populate("model")
            .populate("tools")
            .populate("knowledgeBases");

        if (!agent) {
            return res.status(404).json({
                success: false,
                message: "Agent not found"
            });
        }

        return res.status(200).json({
            success: true,
            agent
        });

    } catch (error) {
        console.error("Get Agent Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch agent"
        });
    }
}


// UPDATE AGENT
async function updateAgent(req, res) {
    try {
        const { agentId } = req.params;

        const agent = await Agent.findByIdAndUpdate(
            agentId,
            req.body,
            {
                new: true,
                runValidators: true
            }
        );

        if (!agent) {
            return res.status(404).json({
                success: false,
                message: "Agent not found"
            });
        }

        return res.status(200).json({
            success: true,
            message: "Agent updated successfully",
            agent
        });

    } catch (error) {
        console.error("Update Agent Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to update agent"
        });
    }
}


// DELETE AGENT
async function deleteAgent(req, res) {
    try {
        const { agentId } = req.params;

        const agent = await Agent.findByIdAndUpdate(
            agentId,
            {
                isActive: false
            },
            {
                new: true
            }
        );

        if (!agent) {
            return res.status(404).json({
                success: false,
                message: "Agent not found"
            });
        }

        return res.status(200).json({
            success: true,
            message: "Agent deleted successfully"
        });

    } catch (error) {
        console.error("Delete Agent Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to delete agent"
        });
    }
}


module.exports = {
    createAgent,
    getAgents,
    getAgentById,
    updateAgent,
    deleteAgent
};