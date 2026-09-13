const express = require("express");

const {
    createChat,
    getUserChats,
    getChatById,
    sendMessage,
    deleteChat
} = require("../controllers/chat.controller");

const { authUser } = require("../middlewares/auth.middleware");

const router = express.Router();


// Create a new chat
router.post("/", authUser, createChat);


// Get all chats of logged-in user
router.get("/", authUser, getUserChats);


// Get a specific chat with messages
router.get("/:chatId", authUser, getChatById);


// Send message in a chat
router.post("/:chatId/message", authUser, sendMessage);


// Delete a chat
router.delete("/:chatId", authUser, deleteChat);


module.exports = router;