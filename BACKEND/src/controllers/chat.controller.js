const Conversation = require("../models/conversation.model");
const Message = require("../models/message.model");
const { sendChatToAI } = require("../services/python.service");

// ===============================
// CREATE NEW CHAT
// ===============================

async function createChat(req, res) {
    try {
        const userId = req.user._id;

        const { title } = req.body;

        const chat = await Conversation.create({
            user: userId,
            title: title || "New Conversation",
            status: "active"
        });

        return res.status(201).json({
            success: true,
            message: "Chat created successfully",
            chat
        });

    } catch (error) {
        console.error("Create Chat Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to create chat"
        });
    }
}


// ===============================
// GET USER CHATS
// ===============================

async function getUserChats(req, res) {
    try {
        const userId = req.user._id;

        const chats = await Conversation.find({
            user: userId
        })
            .sort({ updatedAt: -1 })
            .populate("activeAgent", "name type");

        return res.status(200).json({
            success: true,
            chats
        });

    } catch (error) {
        console.error("Get Chats Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch chats"
        });
    }
}


// ===============================
// GET SINGLE CHAT
// ===============================

async function getChatById(req, res) {
    try {
        const userId = req.user._id;
        const { chatId } = req.params;

        const chat = await Conversation.findOne({
            _id: chatId,
            user: userId
        }).populate("activeAgent", "name type");

        if (!chat) {
            return res.status(404).json({
                success: false,
                message: "Chat not found"
            });
        }

        const messages = await Message.find({
            conversation: chatId
        })
            .sort({ createdAt: 1 })
            .populate("agent", "name type")
            .populate("modelUsed", "name displayName");

        return res.status(200).json({
            success: true,
            chat,
            messages
        });

    } catch (error) {
        console.error("Get Chat Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch chat"
        });
    }
}


// ===============================
// SEND MESSAGE
// ===============================

async function sendMessage(req, res) {
    try {
        const userId = req.user._id;
        const { chatId } = req.params;
        const { content, model, images, fileIds } = req.body;

        // Validate message
        if (!content || !content.trim()) {
            return res.status(400).json({
                success: false,
                message: "Message content is required"
            });
        }

        // Check chat ownership
        const chat = await Conversation.findOne({
            _id: chatId,
            user: userId
        });

        if (!chat) {
            return res.status(404).json({
                success: false,
                message: "Chat not found"
            });
        }

        // ==========================
        // SAVE USER MESSAGE
        // ==========================

        const userMessage = await Message.create({
            conversation: chatId,
            sender: "user",
            content: content.trim()
        });

        // ==========================
        // CALL PYTHON AI SERVICE
        // ==========================

        let aiContent = "AI service did not return a response.";
        try {
            const aiResult = await sendChatToAI({
                message: content.trim(),
                conversationId: chatId,
                userId: userId.toString(),
                isAdmin: Boolean(req.user?.isAdmin || req.user?.role === "admin"),
                userRole: req.user?.role || (req.user?.isAdmin ? "admin" : "operator"),
                userName: req.user?.fullName ? `${req.user.fullName.firstName || ""} ${req.user.fullName.lastName || ""}`.trim() : req.user?.email || "User",
                userEmail: req.user?.email || "",
                model: model || "auto",
                images: Array.isArray(images) ? images : [],
                fileIds: Array.isArray(fileIds) ? fileIds : [],
            });
            if (aiResult && aiResult.response) {
                aiContent = aiResult.response;
            }
        } catch (aiErr) {
            console.error("❌ AI service error in REST sendMessage:", aiErr.message);
            aiContent = "Sovereign AI is currently offline or unreachable. Please verify the AI service is running.";
        }

        // ==========================
        // SAVE AI MESSAGE
        // ==========================

        const assistantMessage = await Message.create({
            conversation: chatId,
            sender: "assistant",
            content: aiContent
        });

        // Update chat timestamp safely avoiding DocumentNotFoundError
        await Conversation.findByIdAndUpdate(chatId, { updatedAt: new Date() });

        return res.status(200).json({
            success: true,
            userMessage,
            assistantMessage
        });

    } catch (error) {
        console.error("Send Message Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to send message"
        });
    }
}


// ===============================
// DELETE CHAT
// ===============================

async function deleteChat(req, res) {
    try {
        const userId = req.user._id;
        const { chatId } = req.params;

        const chat = await Conversation.findOneAndDelete({
            _id: chatId,
            user: userId
        });

        if (!chat) {
            return res.status(404).json({
                success: false,
                message: "Chat not found"
            });
        }

        // Delete associated messages
        await Message.deleteMany({
            conversation: chatId
        });

        return res.status(200).json({
            success: true,
            message: "Chat deleted successfully"
        });

    } catch (error) {
        console.error("Delete Chat Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to delete chat"
        });
    }
}


module.exports = {
    createChat,
    getUserChats,
    getChatById,
    sendMessage,
    deleteChat
};