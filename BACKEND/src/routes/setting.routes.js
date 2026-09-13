const express = require("express");

const {
    getSettings,
    getSetting,
    createOrUpdateSetting,
    deleteSetting
} = require("../controllers/setting.controller");

const authMiddleware = require("../middlewares/auth.middleware");

const router = express.Router();

router.get("/", authMiddleware.authUser, getSettings);

router.get("/:key", authMiddleware.authUser, getSetting);

router.put("/:key", authMiddleware.authUser, createOrUpdateSetting);

router.delete("/:key", authMiddleware.authUser, deleteSetting);

module.exports = router;