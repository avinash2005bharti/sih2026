const express = require("express");

const {
    createTask,
    getTasks,
    getTaskById,
    cancelTask
} = require("../controllers/task.controller");

const authMiddleware = require("../middlewares/auth.middleware");

const router = express.Router();

router.post("/", authMiddleware.authUser, createTask);

router.get("/", authMiddleware.authUser, getTasks);

router.get("/:taskId", authMiddleware.authUser, getTaskById);

router.patch("/:taskId/cancel", authMiddleware.authUser, cancelTask);

module.exports = router;