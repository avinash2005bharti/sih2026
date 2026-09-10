import client from './client';

export const authApi = {
  // Login user
  login: async (credentials) => {
    const res = await client.post('/auth/login', credentials);
    return res.data;
  },

  // Register user (Note: backend requires admin privileges)
  register: async (userData) => {
    const res = await client.post('/auth/register', userData);
    return res.data;
  },

  // Reset password / request temporary password via Brevo email
  forgotPassword: async (email) => {
    const res = await client.post('/auth/forgot-password', { email });
    return res.data;
  },

  // Change password for currently authenticated user
  changePassword: async ({ currentPassword, newPassword }) => {
    const res = await client.put('/auth/change-password', {
      currentPassword,
      newPassword,
    });
    return res.data;
  },

  // Logout user and clear cookies
  logout: async () => {
    const res = await client.post('/auth/logout');
    return res.data;
  },
};

export default authApi;
