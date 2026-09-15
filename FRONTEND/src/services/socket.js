import { io } from "socket.io-client";

/**
 * Socket.IO Client Initialization
 * 
 * Connects to Node.js backend running on port 5000
 * Uses persistent connection for real-time communication
 * 
 * Architecture:
 * React Frontend ↔ Socket.IO ↔ Node.js Backend ↔ FastAPI ↔ Ollama
 */

let socket = null;

/**
 * Initialize Socket.IO connection
 * 
 * @returns {Object} Socket instance
 */
export const initializeSocket = () => {
  if (socket) {
    if (socket.disconnected) {
      socket.connect();
    }
    return socket;
  }

  let rawSocketUrl = import.meta.env.VITE_SOCKET_URL || import.meta.env.VITE_API_URL || "http://localhost:5000";
  if (rawSocketUrl === "/" || rawSocketUrl.startsWith("/api")) {
    rawSocketUrl = "http://localhost:5000";
  }
  const socketUrl = rawSocketUrl.replace(/\/api\/?$/, "");

  socket = io(socketUrl, {
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5,
    withCredentials: true, // Important: Include httpOnly JWT cookies
    transports: ["websocket", "polling"],
  });

  // Connection event
  socket.on("connect", () => {
    console.log("✅ Socket connected:", socket.id);
  });

  // Socket confirmation from server
  socket.on("socket:connected", (data) => {
    console.log("✅ Socket server confirmed:", data.message);
  });

  // Disconnection event
  socket.on("disconnect", () => {
    console.log("❌ Socket disconnected");
  });

  // Connection error
  socket.on("connect_error", (error) => {
    console.error("❌ Socket connection error:", error);
  });

  return socket;
};

/**
 * Get current socket instance
 * 
 * @returns {Object} Socket instance or null
 */
export const getSocket = () => {
  if (!socket) {
    return initializeSocket();
  }
  return socket;
};

/**
 * Disconnect socket
 */
export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};

/**
 * Check if socket is connected
 * 
 * @returns {Boolean}
 */
export const isSocketConnected = () => {
  return socket && socket.connected;
};

/**
 * Join a conversation room
 * 
 * @param {String} conversationId - ID of conversation to join
 */
export const joinConversation = (conversationId) => {
  if (!socket) return;
  
  socket.emit("conversation:join", {
    conversationId,
  });
};

/**
 * Leave a conversation room
 * 
 * @param {String} conversationId - ID of conversation to leave
 */
export const leaveConversation = (conversationId) => {
  if (!socket) return;
  
  socket.emit("conversation:leave", {
    conversationId,
  });
};

/**
 * Send a chat message via Socket.IO
 * 
 * @param {String} message - User message
 * @param {String} conversationId - Optional: conversation ID
 * @param {String} model - Optional: model to use (default: "auto")
 * @param {String} agent - Optional: agent to use (default: "general")
 * @returns {String} messageId
 */
export const sendChatMessage = (message, { conversationId = null, model = "auto", agent = "general", requestId = null, images = [], attachment = null } = {}) => {
  if (!socket) {
    console.error("❌ Socket not connected");
    return null;
  }

  const messageId = requestId || `msg_${Date.now()}`;
  socket.emit("chat:send", {
    conversationId,
    message,
    model,
    agent,
    images,
    attachment,
    requestId: messageId
  });

  return messageId;
};

/**
 * Check AI service health via Socket.IO
 */

/**
 * Stop a chat generation via Socket.IO
 */
export const stopChatMessage = (requestId, conversationId) => {
  if (!socket) return;
  socket.emit("chat:stop", { requestId, conversationId });
};

export const checkAIServiceHealth = () => {
  if (!socket) return;
  
  socket.emit("health:check");
};

/**
 * Subscribe to chat events
 * 
 * @param {Function} onStart - Called when AI starts processing
 * @param {Function} onChunk - Called for each token/chunk (receives chunk text)
 * @param {Function} onComplete - Called when response is complete
 * @param {Function} onError - Called on error (receives error object)
 * @returns {Function} Unsubscribe function
 */
export const subscribeToChatEvents = ({ onStart, onChunk, onComplete, onError, onStopped, onProgress, onVisionResult } = {}) => {
  if (!socket) return () => {};

  const startHandler = (data) => {
    console.log("📨 chat:start", data);
    onStart?.(data);
  };

  const chunkHandler = (data) => {
    // console.log("📨 chat:chunk", data.chunk);
    onChunk?.(data.chunk, data.conversationId, data.messageId, data.generatedFiles, data.toolExecutions);
  };

  const completeHandler = (data) => {
    console.log("✅ chat:complete", data);
    onComplete?.(data);
  };

  const errorHandler = (data) => {
    console.error("❌ chat:error", data);
    onError?.(data);
  };
  const stoppedHandler = (data) => {
    console.log("🛑 chat:stopped", data);
    onStopped?.(data);
  };

  const progressHandler = (data) => {
    console.log("🔍 vision:progress", data);
    onProgress?.(data);
  };

  const visionResultHandler = (data) => {
    console.log("👁️ vision:result", data);
    onVisionResult?.(data);
  };

  socket.on("chat:start", startHandler);
  socket.on("chat:chunk", chunkHandler);
  socket.on("chat:complete", completeHandler);
  socket.on("chat:error", errorHandler);
  socket.on("chat:stopped", stoppedHandler);
  socket.on("vision:progress", progressHandler);
  socket.on("vision:result", visionResultHandler);

  // Return unsubscribe function
  return () => {
    socket.off("chat:start", startHandler);
    socket.off("chat:chunk", chunkHandler);
    socket.off("chat:complete", completeHandler);
    socket.off("chat:error", errorHandler);
    socket.off("chat:stopped", stoppedHandler);
    socket.off("vision:progress", progressHandler);
    socket.off("vision:result", visionResultHandler);
  };
};

/**
 * Subscribe to health check events
 * 
 * @param {Function} onStatus - Called when health status received
 * @returns {Function} Unsubscribe function
 */
export const subscribeToHealthEvents = (onStatus) => {
  if (!socket) return () => {};

  const handler = (data) => {
    console.log("🏥 health:status", data);
    onStatus?.(data);
  };

  socket.on("health:status", handler);

  return () => {
    socket.off("health:status", handler);
  };
};

export default {
  initializeSocket,
  getSocket,
  disconnectSocket,
  isSocketConnected,
  joinConversation,
  leaveConversation,
  sendChatMessage,
  checkAIServiceHealth,
  stopChatMessage,
  subscribeToChatEvents,
  subscribeToHealthEvents,
};
