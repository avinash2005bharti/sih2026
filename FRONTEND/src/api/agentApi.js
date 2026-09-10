import client from './client';

export const agentApi = {
  // Get all active agents
  getAgents: async () => {
    const res = await client.get('/agents');
    return res.data;
  },

  // Get agent by ID with populated model, tools, and knowledge bases
  getAgentById: async (agentId) => {
    const res = await client.get(`/agents/${agentId}`);
    return res.data;
  },

  // Create new specialized agent
  createAgent: async (agentData) => {
    const res = await client.post('/agents', agentData);
    return res.data;
  },

  // Update agent configuration
  updateAgent: async (agentId, agentData) => {
    const res = await client.put(`/agents/${agentId}`, agentData);
    return res.data;
  },

  // Soft delete agent (sets isActive: false)
  deleteAgent: async (agentId) => {
    const res = await client.delete(`/agents/${agentId}`);
    return res.data;
  },
};

export default agentApi;
