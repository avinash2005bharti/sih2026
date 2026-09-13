import client from './client';

export const workflowApi = {
  getWorkflows: async () => {
    const res = await client.get('/workflows');
    return res.data;
  },

  getWorkflowById: async (id) => {
    const res = await client.get(`/workflows/${id}`);
    return res.data;
  },

  createWorkflow: async (data) => {
    const res = await client.post('/workflows', data);
    return res.data;
  },

  updateWorkflow: async (id, data) => {
    const res = await client.put(`/workflows/${id}`, data);
    return res.data;
  },

  deleteWorkflow: async (id) => {
    const res = await client.delete(`/workflows/${id}`);
    return res.data;
  },
};

export default workflowApi;
