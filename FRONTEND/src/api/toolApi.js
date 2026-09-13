import client from './client';

export const toolApi = {
  getTools: async () => {
    const res = await client.get('/tools');
    return res.data;
  },

  getToolById: async (id) => {
    const res = await client.get(`/tools/${id}`);
    return res.data;
  },

  createTool: async (data) => {
    const res = await client.post('/tools', data);
    return res.data;
  },

  updateTool: async (id, data) => {
    const res = await client.put(`/tools/${id}`, data);
    return res.data;
  },

  deleteTool: async (id) => {
    const res = await client.delete(`/tools/${id}`);
    return res.data;
  },
};

export default toolApi;
