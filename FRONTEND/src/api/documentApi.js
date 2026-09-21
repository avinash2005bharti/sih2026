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

  // Record or upload a document file
  uploadDocument: async (documentData) => {
    const isFormData = typeof FormData !== 'undefined' && documentData instanceof FormData;
    const config = {
      timeout: 300000, // 5 minutes for document parsing, chunking, and vector ingestion
      ...(isFormData ? { headers: { 'Content-Type': 'multipart/form-data' } } : {})
    };
    const res = await client.post('/documents', documentData, config);
    return res.data;
  },

  // Update document
  updateDocument: async (documentId, documentData) => {
    const res = await client.put(`/documents/${documentId}`, documentData);
    return res.data;
  },

  // Delete document
  deleteDocument: async (documentId) => {
    const res = await client.delete(`/documents/${documentId}`);
    return res.data;
  },
};

export default documentApi;
