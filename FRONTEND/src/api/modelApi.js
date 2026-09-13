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

  // Delete model
  deleteModel: async (modelId) => {
    const res = await client.delete(`/models/${modelId}`);
    return res.data;
  },

  // Get Ollama models
  getOllamaModels: async () => {
    const res = await client.get('/models/ollama');
    return res.data;
  },

  // Pull Ollama model
  pullModel: async (modelName) => {
    const res = await client.post('/models/pull', { model: modelName });
    return res.data;
  },

  // Get models health
  getModelHealth: async () => {
    const res = await client.get('/models/health');
    return res.data;
  },
};

export default modelApi;
