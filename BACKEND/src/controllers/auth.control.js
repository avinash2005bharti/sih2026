const userModel = require('../models/user.model');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const crypto = require("crypto");
const { sendTemporaryPassword } = require("../services/mail.service");

async function registerUser(req, res) {

    try {
        const {
            email,
            fullName: {
                firstName,
                middleName,
                lastName
            } = {},
            password
        } = req.body;

        // Validation
        if (!email || !firstName || !lastName || !password) {
            return res.status(400).json({
                message: "All required fields are necessary"
            });
        }

        // Check existing user
        const existingUser = await userModel.findOne({ email });

        if (existingUser) {
            return res.status(409).json({
                message: "User already exists"
            });
        }

        // Hash password
        const hashedPassword = await bcrypt.hash(password, 10);

        // Create user
        const user = await userModel.create({
            email,
            fullName: {
                firstName,
                middleName,
                lastName
            },
            password: hashedPassword,
            isAdmin: false
        });

        return res.status(201).json({
            message: "User registered successfully",
            user: {
                id: user._id,
                email: user.email,
                fullName: user.fullName,
                isAdmin: user.isAdmin
            }
        });

    } catch (error) {
        console.error("Register Error:", error);

        return res.status(500).json({
            message: "Internal server error",
            error: error.message
        });
    }
}

async function loginUser(req, res) {
    try {

        const { email, password } = req.body;

        if (!email || !password) {
            return res.status(400).json({
                message: "Email and password are required"
            });
        }

        // 🔑 FIX: explicitly select password in case schema has `select: false`
        const user = await userModel.findOne({ email }).select('+password');

        if (!user || !user.password) {
            return res.status(401).json({
                message: "Invalid email or password"
            });
        }

        const isPasswordCorrect = await bcrypt.compare(
            password,
            user.password
        );

        if (!isPasswordCorrect) {
            return res.status(401).json({
                message: "Invalid email or password"
            });
        }

        const token = jwt.sign(
            {
                id: user._id,
                isAdmin: user.isAdmin
            },
            process.env.JWT_SECRET,
            {
                expiresIn: "7d"
            }
        );

        res.cookie("token", token, {
            httpOnly: true,
            secure: false,
            sameSite: "lax",
            maxAge: 7 * 24 * 60 * 60 * 1000
        });

        return res.status(200).json({
            message: "Login Successful",
            user: {
                email: user.email,
                _id: user._id,
                fullName: user.fullName,
                isAdmin: user.isAdmin
            }
        });

    } catch (err) {
        console.error("Login Error:", err);

        return res.status(500).json({
            message: "Something went wrong"
        });
    }
}

async function resetPassword(req, res) {

    try {

        const { email } = req.body;

        if (!email) {
            return res.status(400).json({
                message: "Email is required"
            });
        }

        const user = await userModel.findOne({ email });

        if (!user) {
            return res.status(404).json({
                message: "No account found with this email"
            });
        }

        const tempPassword = crypto
            .randomBytes(6)
            .toString("base64url");

        const hashedPassword = await bcrypt.hash(
            tempPassword,
            10
        );

        user.password = hashedPassword;

        await user.save();

        await sendTemporaryPassword(
            user.email,
            tempPassword
        );

        return res.status(200).json({
            message:
                "Temporary password has been sent to your registered email"
        });

    } catch (error) {
        console.error("Reset Password Error:", error);

        return res.status(500).json({
            message: "Unable to reset password"
        });
    }
}

async function changePassword(req, res) {

    try {

        const userId = req.user.id;

        const {
            currentPassword,
            newPassword
        } = req.body;

        if (!currentPassword || !newPassword) {
            return res.status(400).json({
                message: "Current password and new password are required"
            });
        }

        if (newPassword.length < 8) {
            return res.status(400).json({
                message: "New password must be at least 8 characters long"
            });
        }

        // 🔑 FIX: explicitly select password here too
        const user = await userModel.findById(userId).select('+password');

        if (!user || !user.password) {
            return res.status(404).json({
                message: "User not found"
            });
        }

        const isPasswordCorrect = await bcrypt.compare(
            currentPassword,
            user.password
        );

        if (!isPasswordCorrect) {
            return res.status(401).json({
                message: "Current password is incorrect"
            });
        }

        const isSamePassword = await bcrypt.compare(
            newPassword,
            user.password
        );

        if (isSamePassword) {
            return res.status(400).json({
                message: "New password must be different from current password"
            });
        }

        const hashedPassword = await bcrypt.hash(
            newPassword,
            10
        );

        user.password = hashedPassword;

        await user.save();

        return res.status(200).json({
            message: "Password changed successfully"
        });

    } catch (error) {
        console.error("Change Password Error:", error);

        return res.status(500).json({
            message: "Internal server error"
        });
    }
}

async function logoutUser(req, res) {

    res.clearCookie("token", {
        httpOnly: true,
        secure: true,
        sameSite: "none"
    });

    return res.status(200).json({
        message: "Logout Successful"
    });

}

module.exports = {
    registerUser,
    loginUser,
    resetPassword,
    changePassword,
    logoutUser
};