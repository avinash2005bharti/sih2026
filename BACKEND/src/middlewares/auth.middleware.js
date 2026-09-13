const userModel = require('../models/user.model');
const jwt = require('jsonwebtoken')

async function authUser(req, res, next) {
    const { token } = req.cookies;
    if (!token) {
        return res.status(401).json({ message: "Unauthorized" });
    }
    try {
        const decode = jwt.verify(token, process.env.JWT_SECRET);

        const user = await userModel.findById(decode.id);
        if (!user) {
            res.clearCookie("token", { httpOnly: true, secure: false, sameSite: "lax" });
            return res.status(401).json({ message: "User not found" });
        }
        req.user = user;
        next();
    } catch (err) {
        res.clearCookie("token", { httpOnly: true, secure: false, sameSite: "lax" });
        return res.status(401).json({ message: "Unauthorized", error: err.message });
    }
}

// admin middle ware

function adminMiddleware(req, res, next) {

  if (!req.user) {
    return res.status(401).json({
      message: 'Authentication required'
    });
  }

  if (!req.user.isAdmin && req.user.role !== 'admin') {
    return res.status(403).json({
      message: 'Only administrator can perform this action'
    });
  }

  next();
}



module.exports = {
    authUser,
    adminMiddleware
}