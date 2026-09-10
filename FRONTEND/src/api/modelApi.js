import client from './client';

export const modelApi = {
  // Get all active local/air-gapped AI models
  getModels: async () => {
    const res = await client.get('/models');
    return res.data;
  },

  // Get specific model details
  getModelById: async (modelId) => {
    const res = await client.get(`/models/${modelId}`);
    return res.data;
  },

  // Register new AI model
  createModel: async (modelData) => {
    const res = await client.post('/models', modelData);
    return res.data;
  },

  // Update AI model configuration
  updateModel: async (modelId, modelData) => {
    const res = await client.put(`/models/${modelId}`, modelData);
    return res.data;
  },

  // Soft delete model
  deleteModel: async (modelId) => {
    const res = await client.delete(`/models/${modelId}`);
    return res.data;
  },
};

export default modelApi;
