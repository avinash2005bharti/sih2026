import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import chatApi from '../api/chatApi';
import agentApi from '../api/agentApi';
import modelApi from '../api/modelApi';

const ChatContext = createContext(null);

export const ChatProvider = ({ children }) => {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [activeChat, setActiveChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingChats, setLoadingChats] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [sendError, setSendError] = useState(null);

  // Agents & Models — empty by default until fetched from backend
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);

  // Deep reasoning & UI toggles
  const [deepReasoning, setDeepReasoning] = useState(true);
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);
  const [activeReasoningTrace, setActiveReasoningTrace] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Fetch all chats from the backend
  const fetchChats = useCallback(async () => {
    setLoadingChats(true);
    try {
      const data = await chatApi.getUserChats();
      setChats(data?.chats || []);
    } catch (e) {
      console.error('Failed to fetch chats:', e.message);
      setChats([]);
    } finally {
      setLoadingChats(false);
    }
  }, []);

  // Fetch agents from backend
  const fetchAgents = useCallback(async () => {
    try {
      const data = await agentApi.getAgents();
      const list = data?.agents || [];
      setAgents(list);
      if (list.length > 0) setSelectedAgent(list[0]);
    } catch (e) {
      console.error('Failed to fetch agents:', e.message);
      setAgents([]);
    }
  }, []);

  // Fetch models from backend
  const fetchModels = useCallback(async () => {
    try {
      const data = await modelApi.getModels();
      const list = data?.models || [];
      setModels(list);
      if (list.length > 0) setSelectedModel(list[0]);
    } catch (e) {
      console.error('Failed to fetch models:', e.message);
      setModels([]);
    }
  }, []);

  useEffect(() => {
    fetchChats();
    fetchAgents();
    fetchModels();
  }, [fetchChats, fetchAgents, fetchModels]);

  // Select a conversation and load its messages
  const selectChat = async (chatId) => {
    setActiveChatId(chatId);
    setMessages([]);
    setSendError(null);
    setLoadingMessages(true);
    try {
      const data = await chatApi.getChatById(chatId);
      if (data && data.chat) {
        setActiveChat(data.chat);
        setMessages(data.messages || []);
      }
    } catch (e) {
      console.error('Failed to load chat messages:', e.message);
      // Show the chat shell but no messages — empty state is fine
      const foundChat = chats.find((c) => c._id === chatId);
      setActiveChat(foundChat || { _id: chatId, title: 'Conversation' });
      setMessages([]);
    } finally {
      setLoadingMessages(false);
    }
  };

  // Start a fresh chat session
  const createNewChat = () => {
    setActiveChatId(null);
    setActiveChat(null);
    setMessages([]);
    setSendError(null);
    setActiveReasoningTrace(null);
  };

  // Send a message — no synthetic fallback
  const sendMessage = async (content, attachment = null) => {
    if (!content.trim() && !attachment) return;

    setSendError(null);
    let targetChatId = activeChatId;

    // Create a new conversation if none is active
    if (!targetChatId) {
      const title = content.trim().slice(0, 60) + (content.length > 60 ? '...' : '');
      try {
        const createRes = await chatApi.createChat(title);
        if (createRes && createRes.chat) {
          targetChatId = createRes.chat._id;
          setActiveChatId(targetChatId);
          setActiveChat(createRes.chat);
          setChats((prev) => [createRes.chat, ...prev]);
        } else {
          throw new Error('Failed to create conversation');
        }
      } catch (e) {
        setSendError('Could not start a new conversation. Is the backend running?');
        return;
      }
    }

    // Optimistic user message bubble
    const userMsg = {
      _id: 'msg_' + Date.now(),
      conversation: targetChatId,
      sender: 'user',
      content: content.trim(),
      attachment: attachment || null,
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsGenerating(true);

    try {
      const res = await chatApi.sendMessage(targetChatId, content);
      if (res && res.assistantMessage) {
        setMessages((prev) => [...prev, res.assistantMessage]);
      } else {
        throw new Error('No assistant response received');
      }
    } catch (err) {
      console.error('Send message failed:', err.message);
      setSendError('Failed to get a response. Please try again.');
      // Remove the optimistic user message to keep UI consistent
      setMessages((prev) => prev.filter((m) => m._id !== userMsg._id));
    } finally {
      setIsGenerating(false);
    }
  };

  // Delete a chat
  const deleteChat = async (chatId) => {
    try {
      await chatApi.deleteChat(chatId);
    } catch (e) {
      console.error('Delete chat failed:', e.message);
    }
    setChats((prev) => prev.filter((c) => c._id !== chatId));
    if (activeChatId === chatId) {
      createNewChat();
    }
  };

  return (
    <ChatContext.Provider
      value={{
        chats,
        activeChatId,
        activeChat,
        messages,
        loadingChats,
        loadingMessages,
        isGenerating,
        sendError,
        agents,
        selectedAgent,
        setSelectedAgent,
        models,
        selectedModel,
        setSelectedModel,
        deepReasoning,
        setDeepReasoning,
        isStatusModalOpen,
        setIsStatusModalOpen,
        activeReasoningTrace,
        setActiveReasoningTrace,
        isSidebarOpen,
        setIsSidebarOpen,
        selectChat,
        createNewChat,
        sendMessage,
        deleteChat,
        refreshChats: fetchChats,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

export default ChatContext;
