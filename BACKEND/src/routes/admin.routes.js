const express = require('express');
const router = express.Router();
const adminControllers = require('../controllers/admin.controller');
const authControllers = require('../controllers/auth.control');
const authMiddleware = require('../middlewares/auth.middleware');

// All admin routes require authentication + admin role
router.get('/users', authMiddleware.authUser, authMiddleware.adminMiddleware, adminControllers.getUsers);
router.post('/users', authMiddleware.authUser, authMiddleware.adminMiddleware, authControllers.registerUser);
router.get('/users/:userId', authMiddleware.authUser, authMiddleware.adminMiddleware, adminControllers.getUserById);
router.put('/users/:userId', authMiddleware.authUser, authMiddleware.adminMiddleware, adminControllers.updateUser);

module.exports = router;
