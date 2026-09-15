import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './AuthContext';
import chatApi from '../api/chatApi';
import agentApi from '../api/agentApi';
import modelApi from '../api/modelApi';
import { initializeSocket, disconnectSocket, sendChatMessage, subscribeToChatEvents, joinConversation, stopChatMessage } from '../services/socket';

const ChatContext = createContext(null);

export const ChatProvider = ({ children }) => {
  const { user } = useAuth();
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [activeChat, setActiveChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingChats, setLoadingChats] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentRequestId, setCurrentRequestId] = useState(null);
  const [sendError, setSendError] = useState(null);

  // Agents & Models — empty by default until fetched from backend
  const AUTO_MODEL = { _id: 'auto', displayName: 'auto', name: 'Auto Route (Intelligent)', slug: 'auto' };
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [models, setModels] = useState([AUTO_MODEL]);
  const [selectedModel, setSelectedModel] = useState(AUTO_MODEL);

  // Deep reasoning & UI toggles
  const [deepReasoning, setDeepReasoning] = useState(true);
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);
  const [activeReasoningTrace, setActiveReasoningTrace] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Socket.IO connection status
  const [socketConnected, setSocketConnected] = useState(false);
  const socketRef = useRef(null);
  const unsubscribeChatEventsRef = useRef(null);

  // Initialize Socket.IO only when authenticated
  useEffect(() => {
    if (!user) {
      disconnectSocket();
      setSocketConnected(false);
      return;
    }

    const socket = initializeSocket();
    socketRef.current = socket;

    const onConnect = () => {
      console.log("✅ ChatContext: Socket connected");
      setSocketConnected(true);
    };

    const onDisconnect = () => {
      console.log("❌ ChatContext: Socket disconnected");
      setSocketConnected(false);
    };

    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);

    // Set initial state
    setSocketConnected(socket.connected);

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
    };
  }, [user]);

  // Fetch all chats from the backend
  const fetchChats = useCallback(async () => {
    if (!user) return;
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
  }, [user]);

  // Fetch agents from backend
  const fetchAgents = useCallback(async () => {
    if (!user) return;
    try {
      const data = await agentApi.getAgents();
      const list = data?.agents || [];
      setAgents(list);
      if (list.length > 0) setSelectedAgent(list[0]);
    } catch (e) {
      console.error('Failed to fetch agents:', e.message);
      setAgents([]);
    }
  }, [user]);

  // Fetch models from backend
  const fetchModels = useCallback(async () => {
    if (!user) return;
    try {
      const data = await modelApi.getModels();
      const list = data?.models || [];
      const fullList = [AUTO_MODEL, ...list.filter(m => m.slug !== 'auto' && m.displayName !== 'auto')];
      setModels(fullList);
      // Default to AUTO_MODEL unless already changed to a specific model
      setSelectedModel((prev) => prev && prev._id !== 'auto' ? prev : AUTO_MODEL);
    } catch (e) {
      console.error('Failed to fetch models:', e.message);
      setModels([AUTO_MODEL]);
      setSelectedModel(AUTO_MODEL);
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      fetchChats();
      fetchAgents();
      fetchModels();
    } else {
      setChats([]);
      setAgents([]);
      setModels([]);
    }
  }, [user, fetchChats, fetchAgents, fetchModels]);

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

  // Send a message using Socket.IO (streaming) or REST (fallback)
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

    // Join conversation room via Socket.IO
    if (socketConnected && targetChatId) {
      joinConversation(targetChatId);
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
      // Try Socket.IO first (streaming), fall back to REST if not connected
      if (socketConnected && socketRef.current) {
        console.log("📨 Sending message via Socket.IO");
        
        // Setup chat event listeners
        let streamingMessage = {
          _id: 'msg_' + Date.now() + '_ai',
          conversation: targetChatId,
          sender: 'assistant',
          content: '',
          generatedFiles: [],
          toolExecutions: [],
          ocr: null,
          vision: null,
          visionProgress: null,
          createdAt: new Date().toISOString(),
        };

        // Subscribe to chat events
        if (unsubscribeChatEventsRef.current) {
          unsubscribeChatEventsRef.current();
        }

        unsubscribeChatEventsRef.current = subscribeToChatEvents({
          onStart: (data) => {
            console.log("📨 Response started");
            streamingMessage._id = 'msg_' + Date.now() + '_ai';
            streamingMessage.generatedFiles = [];
            streamingMessage.toolExecutions = [];
            streamingMessage.ocr = null;
            streamingMessage.vision = null;
            streamingMessage.visionProgress = null;
            setMessages((prev) => [...prev, streamingMessage]);
            setIsGenerating(true);
          },
          onProgress: (data) => {
            console.log("🔍 Vision progress:", data.message);
            streamingMessage.visionProgress = data.message;
            setMessages((prev) => {
              const updated = [...prev];
              const idx = updated.findIndex((m) => m._id === streamingMessage._id);
              if (idx >= 0) {
                updated[idx] = { ...streamingMessage };
              }
              return updated;
            });
          },
          onVisionResult: (data) => {
            console.log("👁️ Vision result:", data);
            if (data.ocr) streamingMessage.ocr = data.ocr;
            if (data.vision) streamingMessage.vision = data.vision;
            setMessages((prev) => {
              const updated = [...prev];
              const idx = updated.findIndex((m) => m._id === streamingMessage._id);
              if (idx >= 0) {
                updated[idx] = { ...streamingMessage };
              }
              return updated;
            });
          },
          onChunk: (chunk, convId, msgId, generatedFiles, toolExecutions) => {
            streamingMessage.content += chunk;
            if (generatedFiles && generatedFiles.length > 0) {
              streamingMessage.generatedFiles = generatedFiles;
            }
            if (toolExecutions && toolExecutions.length > 0) {
              streamingMessage.toolExecutions = toolExecutions;
            }
            // Clear temporary progress banner once streaming text begins
            if (chunk && chunk.trim()) {
              streamingMessage.visionProgress = null;
            }
            setMessages((prev) => {
              const updated = [...prev];
              const idx = updated.findIndex((m) => m._id === streamingMessage._id);
              if (idx >= 0) {
                updated[idx] = { ...streamingMessage };
              }
              return updated;
            });
          },
          onComplete: async (data) => {
            console.log("✅ Response complete", data);
            // A final response is authoritative.  It covers non-streaming
            // fallbacks and stream providers that send completion before any
            // token, preventing an empty assistant bubble.
            if (data?.response && !streamingMessage.content) {
              streamingMessage.content = data.response;
            }
            if (data?.generatedFiles && data.generatedFiles.length > 0) {
              streamingMessage.generatedFiles = data.generatedFiles;
            }
            if (data?.toolExecutions && data.toolExecutions.length > 0) {
              streamingMessage.toolExecutions = data.toolExecutions;
            }
            if (data?.ocr) streamingMessage.ocr = data.ocr;
            if (data?.vision) streamingMessage.vision = data.vision;
            streamingMessage.visionProgress = null;
            setMessages((prev) => {
              const updated = [...prev];
              const idx = updated.findIndex((m) => m._id === streamingMessage._id);
              if (idx >= 0) {
                updated[idx] = { ...streamingMessage };
              }
              return updated;
            });
            setIsGenerating(false);
            setCurrentRequestId(null);
          },
          onStopped: (data) => {
            console.log("🛑 Chat stopped via Socket", data);
            setIsGenerating(false);
            setCurrentRequestId(null);
          },
          onError: (error) => {
            console.error("❌ Chat error via Socket:", error);
            setSendError(error.error || 'Failed to get a response');
            setIsGenerating(false);
            setCurrentRequestId(null);
            // Remove optimistic message
            setMessages((prev) =>
              prev.filter((m) => m._id !== streamingMessage._id && m._id !== userMsg._id)
            );
          },
        });

        // Send message via Socket.IO
        const modelToUse = selectedModel?.displayName || 'auto';
        // Agent selection belongs to the Python orchestrator.  The UI may
        // still display available agents, but must not force a generic agent.
        const agentToUse = 'auto';
        const reqId = 'req_' + Date.now();
        setCurrentRequestId(reqId);
        const imagesToSend = attachment?.base64 ? [attachment.base64] : [];
        sendChatMessage(content.trim(), {
          conversationId: targetChatId,
          model: modelToUse,
          agent: agentToUse,
          images: imagesToSend,
          attachment,
          requestId: reqId
        });
      } else {
        // Fallback to REST API
        console.log("📨 Sending message via REST (Socket.IO not available)");
        const res = await chatApi.sendMessage(targetChatId, content);
        if (res && res.assistantMessage) {
          setMessages((prev) => [...prev, res.assistantMessage]);
        } else {
          throw new Error('No assistant response received');
        }
        setIsGenerating(false);
      }
    } catch (err) {
      console.error('Send message failed:', err.message);
      setSendError('Failed to get a response. Please try again.');
      setIsGenerating(false);
      // Remove the optimistic user message to keep UI consistent
      setMessages((prev) => prev.filter((m) => m._id !== userMsg._id));
    }
  };

  // Delete a chat
  
  const stopGeneration = useCallback(() => {
    if (socketConnected && currentRequestId) {
      console.log('🛑 Requesting generation stop for', currentRequestId);
      stopChatMessage(currentRequestId, activeChatId);
      setIsGenerating(false); // Optimistic UI update
    }
  }, [socketConnected, currentRequestId, activeChatId]);

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
        socketConnected,
        selectChat,
        createNewChat,
        sendMessage,
        deleteChat,
        refreshChats: fetchChats,
        stopGeneration,
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
