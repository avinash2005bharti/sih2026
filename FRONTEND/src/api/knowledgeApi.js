import client from './client';

export const knowledgeApi = {
  // Get all user knowledge bases
  getKnowledgeBases: async () => {
    const res = await client.get('/knowledge-bases');
    return res.data;
  },

  // Get knowledge base details
  getKnowledgeBaseById: async (id) => {
    const res = await client.get(`/knowledge-bases/${id}`);
    return res.data;
  },

  // Create new knowledge base collection
  createKnowledgeBase: async (data) => {
    const res = await client.post('/knowledge-bases', data);
    return res.data;
  },

  // Update knowledge base
  updateKnowledgeBase: async (id, data) => {
    const res = await client.put(`/knowledge-bases/${id}`, data);
    return res.data;
  },

  // Delete knowledge base
  deleteKnowledgeBase: async (id) => {
    const res = await client.delete(`/knowledge-bases/${id}`);
    return res.data;
  },
};

export default knowledgeApi;
