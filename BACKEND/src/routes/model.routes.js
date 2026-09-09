const express = require("express");

const {
    createModel,
    getModels,
    getModelById,
    updateModel,
    deleteModel
} = require("../controllers/model.controller");

const authMiddleware = require("../middlewares/auth.middleware");

const router = express.Router();

router.post("/", authMiddleware.authUser, createModel);

router.get("/", authMiddleware.authUser, getModels);

router.get("/:modelId", authMiddleware.authUser, getModelById);

router.put("/:modelId", authMiddleware.authUser, updateModel);

router.delete("/:modelId", authMiddleware.authUser, deleteModel);

module.exports = router;