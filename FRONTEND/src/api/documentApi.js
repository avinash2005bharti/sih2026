import client from './client';

export const documentApi = {
  // Get all documents uploaded by the user
  getDocuments: async () => {
    const res = await client.get('/documents');
    return res.data;
  },

  // Get specific document by ID
  getDocumentById: async (documentId) => {
    const res = await client.get(`/documents/${documentId}`);
    return res.data;
  },

  // Record an uploaded document
  uploadDocument: async (documentData) => {
    const res = await client.post('/documents', documentData);
    return res.data;
  },

  // Delete document
  deleteDocument: async (documentId) => {
    const res = await client.delete(`/documents/${documentId}`);
    return res.data;
  },
};

export default documentApi;
