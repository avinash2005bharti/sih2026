const SystemSetting = require("../models/systemSettings.model");


// GET ALL SETTINGS
async function getSettings(req, res) {
    try {
        const settings = await SystemSetting.find()
            .sort({ category: 1, key: 1 });

        return res.status(200).json({
            success: true,
            settings
        });

    } catch (error) {
        console.error("Get Settings Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch settings"
        });
    }
}


// GET SINGLE SETTING
async function getSetting(req, res) {
    try {
        const { key } = req.params;

        const setting = await SystemSetting.findOne({
            key
        });

        if (!setting) {
            return res.status(404).json({
                success: false,
                message: "Setting not found"
            });
        }

        return res.status(200).json({
            success: true,
            setting
        });

    } catch (error) {
        console.error("Get Setting Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to fetch setting"
        });
    }
}


// CREATE / UPDATE
async function createOrUpdateSetting(req, res) {
    try {
        const { key } = req.params;

        const {
            value,
            category,
            description
        } = req.body;

        const setting = await SystemSetting.findOneAndUpdate(
            { key },
            {
                key,
                value,
                category,
                description
            },
            {
                new: true,
                upsert: true,
                runValidators: true
            }
        );

        return res.status(200).json({
            success: true,
            message: "Setting saved successfully",
            setting
        });

    } catch (error) {
        console.error("Save Setting Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to save setting"
        });
    }
}


// DELETE
async function deleteSetting(req, res) {
    try {
        const { key } = req.params;

        const setting = await SystemSetting.findOneAndDelete({
            key
        });

        if (!setting) {
            return res.status(404).json({
                success: false,
                message: "Setting not found"
            });
        }

        return res.status(200).json({
            success: true,
            message: "Setting deleted successfully"
        });

    } catch (error) {
        console.error("Delete Setting Error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to delete setting"
        });
    }
}


module.exports = {
    getSettings,
    getSetting,
    createOrUpdateSetting,
    deleteSetting
};