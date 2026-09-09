const express = require('express');
const router = express.Router();
const authControllers = require('../controllers/auth.control');

const authMiddlewares = require('../middlewares/auth.middleware')

// register 
router.post('/register',authMiddlewares.authUser,authMiddlewares.adminMiddleware,authControllers.registerUser);

// login

router.post('/login', authControllers.loginUser)
// reset password
router.post("/forgot-password",authControllers.resetPassword)

// Change password
router.put("/change-password",authMiddlewares.authUser,authControllers.changePassword
);

// logout 
router.post("/logout",authMiddlewares.authUser,authControllers.logoutUser)

module.exports = router