import client from './client';

export const adminApi = {
  // Fetch paginated / searched users
  getUsers: async (params = {}) => {
    const res = await client.get('/admin/users', { params });
    return res.data;
  },

  // Fetch single user by ID
  getUserById: async (userId) => {
    const res = await client.get(`/admin/users/${userId}`);
    return res.data;
  },

  // Create new user (Admin only)
  createUser: async (userData) => {
    const res = await client.post('/admin/users', userData);
    return res.data;
  },

  // Update existing user (role, department, status, password, isAdmin)
  updateUser: async (userId, data) => {
    const res = await client.put(`/admin/users/${userId}`, data);
    return res.data;
  },
};

export default adminApi;
