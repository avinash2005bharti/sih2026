const Task = require("../models/task.model");
const Execution = require("../models/execution.model");


// CREATE TASK
async function createTask(req, res) {
    try {
        const userId = req.user._id;

        const {
            title,
            objective,
            priority,
            orchestrator,
            selectedAgents,
            conversation
        } = req.body;

        if (!objective) {
            return res.status(400).json({
                success: false,
                message: "Task objective is required"
            });
        }

        const task = await Task.create({
            user: userId,
            conversation,
            title,
            objective,
            priority,
            orchestrator,
            selectedAgents,
            status: "queued"
        });

        return res.status(201).json({
            success: true,
            message: "Task created successfully",
            task
        });

    } catch (error) {
        console.error("Create Task Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to create task"
        });
    }
}


// GET USER TASKS
async function getTasks(req, res) {
    try {
        const userId = req.user._id;

        const tasks = await Task.find({
            user: userId
        })
            .populate("orchestrator", "name type")
            .populate("selectedAgents", "name type")
            .sort({ createdAt: -1 });

        return res.status(200).json({
            success: true,
            tasks
        });

    } catch (error) {
        console.error("Get Tasks Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch tasks"
        });
    }
}


// GET TASK
async function getTaskById(req, res) {
    try {
        const userId = req.user._id;
        const { taskId } = req.params;

        const task = await Task.findOne({
            _id: taskId,
            user: userId
        })
            .populate("orchestrator")
            .populate("selectedAgents");

        if (!task) {
            return res.status(404).json({
                success: false,
                message: "Task not found"
            });
        }

        const executions = await Execution.find({
            task: taskId
        })
            .populate("agent", "name type")
            .populate("model", "name displayName")
            .sort({ stepNumber: 1 });

        return res.status(200).json({
            success: true,
            task,
            executions
        });

    } catch (error) {
        console.error("Get Task Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch task"
        });
    }
}


// CANCEL TASK
async function cancelTask(req, res) {
    try {
        const userId = req.user._id;
        const { taskId } = req.params;

        const task = await Task.findOneAndUpdate(
            {
                _id: taskId,
                user: userId
            },
            {
                status: "cancelled"
            },
            {
                new: true
            }
        );

        if (!task) {
            return res.status(404).json({
                success: false,
                message: "Task not found"
            });
        }

        return res.status(200).json({
            success: true,
            message: "Task cancelled successfully",
            task
        });

    } catch (error) {
        console.error("Cancel Task Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to cancel task"
        });
    }
}


module.exports = {
    createTask,
    getTasks,
    getTaskById,
    cancelTask
};