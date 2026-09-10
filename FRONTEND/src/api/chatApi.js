import client from './client';

export const chatApi = {
  // Get all chats of the current user
  getUserChats: async () => {
    const res = await client.get('/chat');
    return res.data;
  },

  // Create a new chat conversation
  createChat: async (title = 'New Conversation') => {
    const res = await client.post('/chat', { title });
    return res.data;
  },

  // Fetch a specific conversation with all historical messages
  getChatById: async (chatId) => {
    const res = await client.get(`/chat/${chatId}`);
    return res.data;
  },

  // Send a message within a conversation
  sendMessage: async (chatId, content) => {
    const res = await client.post(`/chat/${chatId}/message`, { content });
    return res.data;
  },

  // Delete a chat conversation and all related messages
  deleteChat: async (chatId) => {
    const res = await client.delete(`/chat/${chatId}`);
    return res.data;
  },
};

export default chatApi;
