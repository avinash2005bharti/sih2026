import client from './client';

export const settingApi = {
  // Get all system settings
  getSettings: async () => {
    const res = await client.get('/settings');
    return res.data;
  },

  // Get specific setting by key
  getSetting: async (key) => {
    const res = await client.get(`/settings/${key}`);
    return res.data;
  },

  // Update or upsert setting
  saveSetting: async (key, data) => {
    const res = await client.put(`/settings/${key}`, data);
    return res.data;
  },

  // Delete setting
  deleteSetting: async (key) => {
    const res = await client.delete(`/settings/${key}`);
    return res.data;
  },

  // Check backend server health
  checkHealth: async () => {
    const res = await client.get('/health');
    return res.data;
  },
};

export default settingApi;
