const User = require('../models/user.model');
const bcrypt = require('bcrypt');

// GET /api/admin/users?page=1&limit=25&search=term
async function getUsers(req, res) {
  try {
    const page = parseInt(req.query.page, 10) || 1;
    const limit = parseInt(req.query.limit, 10) || 25;
    const search = req.query.search || '';

    const filter = {};
    if (search) {
      filter.$or = [
        { email: { $regex: search, $options: 'i' } },
        { 'fullName.firstName': { $regex: search, $options: 'i' } },
        { 'fullName.lastName': { $regex: search, $options: 'i' } },
      ];
    }

    const total = await User.countDocuments(filter);
    const users = await User.find(filter)
      .sort({ createdAt: -1 })
      .skip((page - 1) * limit)
      .limit(limit)
      .select('email fullName role isAdmin isActive department createdAt');

    return res.status(200).json({ success: true, users, total, page, limit });
  } catch (error) {
    console.error('Get Admin Users Error:', error);
    return res.status(500).json({ success: false, message: 'Failed to fetch users' });
  }
}

// GET /api/admin/users/:userId
async function getUserById(req, res) {
  try {
    const { userId } = req.params;
    const user = await User.findById(userId).select('email fullName role isAdmin isActive department createdAt');
    if (!user) {
      return res.status(404).json({ success: false, message: 'User not found' });
    }
    return res.status(200).json({ success: true, user });
  } catch (error) {
    console.error('Get Admin User Error:', error);
    return res.status(500).json({ success: false, message: 'Failed to fetch user' });
  }
}

// PUT /api/admin/users/:userId
async function updateUser(req, res) {
  try {
    const { userId } = req.params;
    const { role, isActive, department, password, isAdmin } = req.body;

    const update = {};
    if (typeof role !== 'undefined') update.role = role;
    if (typeof isActive !== 'undefined') update.isActive = isActive;
    if (typeof department !== 'undefined') update.department = department;
    if (typeof isAdmin !== 'undefined') update.isAdmin = isAdmin;

    // If password provided, hash it
    if (password) {
      if (password.length < 8) {
        return res.status(400).json({ success: false, message: 'Password must be at least 8 characters' });
      }
      const hashed = await bcrypt.hash(password, 10);
      update.password = hashed;
    }

    const user = await User.findByIdAndUpdate(userId, update, { new: true }).select('email fullName role isAdmin isActive department createdAt');
    if (!user) {
      return res.status(404).json({ success: false, message: 'User not found' });
    }

    return res.status(200).json({ success: true, message: 'User updated', user });
  } catch (error) {
    console.error('Update Admin User Error:', error);
    return res.status(500).json({ success: false, message: 'Failed to update user' });
  }
}

module.exports = {
  getUsers,
  getUserById,
  updateUser,
};
