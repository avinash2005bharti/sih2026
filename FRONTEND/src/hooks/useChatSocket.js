import { useEffect, useRef, useCallback, useState } from "react";
import {
  initializeSocket,
  getSocket,
  isSocketConnected,
  sendChatMessage as socketSendMessage,
  subscribeToChatEvents,
  joinConversation as socketJoinConversation,
  leaveConversation as socketLeaveConversation,
  checkAIServiceHealth,
} from "../services/socket";

/**
 * React Hook for Socket.IO Chat Integration
 * 
 * Handles:
 * - Socket initialization and cleanup
 * - Message sending and streaming
 * - Chat state management
 * - Error handling and reconnection
 * 
 * Usage:
 * const { connected, sendMessage, streaming, response, error } = useChatSocket();
 */

export const useChatSocket = () => {
  const [connected, setConnected] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [response, setResponse] = useState("");
  const [error, setError] = useState(null);
  const [messageId, setMessageId] = useState(null);
  const [conversationId, setConversationId] = useState(null);

  const unsubscribeRef = useRef(null);
  const currentResponseRef = useRef("");

  // Initialize socket on mount
  useEffect(() => {
    const socket = initializeSocket();
    setConnected(socket.connected);

    const onConnect = () => {
      console.log("✅ Socket hook: connected");
      setConnected(true);
      setError(null);
    };

    const onDisconnect = () => {
      console.log("❌ Socket hook: disconnected");
      setConnected(false);
    };

    const onConnectError = (error) => {
      console.error("❌ Socket hook: connection error", error);
      setError("Connection error");
    };

    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);
    socket.on("connect_error", onConnectError);

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
      socket.off("connect_error", onConnectError);
    };
  }, []);

  // Subscribe to chat events
  useEffect(() => {
    const handleStart = (data) => {
      console.log("📨 Starting response...");
      setStreaming(true);
      setError(null);
      currentResponseRef.current = "";
      setResponse("");
      setMessageId(data.messageId);
      setConversationId(data.conversationId);
    };

    const handleChunk = (chunk) => {
      currentResponseRef.current += chunk;
      setResponse(currentResponseRef.current);
    };

    const handleComplete = (data) => {
      console.log("✅ Response complete");
      setStreaming(false);
      setResponse(currentResponseRef.current);
    };

    const handleError = (data) => {
      console.error("❌ Chat error:", data);
      setStreaming(false);
      setError(data.error || "Unknown error occurred");
    };

    unsubscribeRef.current = subscribeToChatEvents({
      onStart: handleStart,
      onChunk: handleChunk,
      onComplete: handleComplete,
      onError: handleError,
    });

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, []);

  // Send message via Socket.IO
  const sendMessage = useCallback(
    (message, options = {}) => {
      if (!connected) {
        setError("Socket not connected");
        return null;
      }

      if (!message || message.trim().length === 0) {
        setError("Message cannot be empty");
        return null;
      }

      try {
        const id = socketSendMessage(message, {
          conversationId: options.conversationId || conversationId,
          model: options.model || "auto",
          agent: options.agent || "general",
        });

        return id;
      } catch (err) {
        setError(err.message);
        return null;
      }
    },
    [connected, conversationId]
  );

  // Join conversation room
  const joinConversation = useCallback((convId) => {
    socketJoinConversation(convId);
    setConversationId(convId);
  }, []);

  // Leave conversation room
  const leaveConversation = useCallback((convId) => {
    socketLeaveConversation(convId);
    if (conversationId === convId) {
      setConversationId(null);
    }
  }, [conversationId]);

  // Reset response state
  const resetResponse = useCallback(() => {
    setResponse("");
    setError(null);
    setMessageId(null);
    currentResponseRef.current = "";
  }, []);

  return {
    // Connection status
    connected,
    
    // Chat state
    streaming,
    response,
    error,
    messageId,
    conversationId,
    
    // Methods
    sendMessage,
    joinConversation,
    leaveConversation,
    resetResponse,
    checkHealth: checkAIServiceHealth,
  };
};

export default useChatSocket;
