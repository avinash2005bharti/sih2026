const fs = require("fs");
const path = require("path");
const { Server } = require("socket.io");
const { sendChatToAI, checkAIServiceHealth, sendChatToAIStream } = require("../services/python.service");
const userModel = require("../models/user.model");
const conversationModel = require("../models/conversation.model");
const messageModel = require("../models/message.model");

/**
 * Socket.IO Server Initialization
 * 
 * Architecture:
 * React Frontend ↔ Socket.IO ↔ Node.js Backend ↔ FastAPI AI Service ↔ Ollama
 */


/**
 * Active generation registry.
 * Key: requestId (string)
 * Value: { abortController, socketId, conversationId, completed }
 */
const activeGenerations = new Map();
const completedGenerations = new Set();

module.exports = function initializeSocketServer(httpServer) {
  const io = new Server(httpServer, {
    cors: {
      origin: [
        process.env.FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
      ].filter(Boolean),
      credentials: true,
      methods: ["GET", "POST"],
    },
    transports: ["websocket", "polling"],
  });

  io.use(async (socket, next) => {
    try {
      let token = socket.handshake.auth?.token;
      if (!token && socket.request.headers.cookie) {
        token = socket.request.headers.cookie
          .split("; ")
          .find((c) => c.startsWith("token="))
          ?.split("=")[1];
      }

      if (!token) {
        return next(new Error("Authentication required"));
      }

      const jwt = require("jsonwebtoken");
      const secret = process.env.JWT_SECRET || "default_secret";
      const decoded = jwt.verify(token, secret);
      
      if (!decoded || !decoded.id) {
        return next(new Error("Invalid token payload"));
      }

      const mongoose = require("mongoose");
      if (mongoose.connection.readyState !== 1) {
        return next(new Error("Database unavailable"));
      }
      
      socket.userId = decoded.id;
      socket.user = await userModel.findById(decoded.id);

      if (!socket.user) {
        return next(new Error("User not found"));
      }

      next();
    } catch (error) {
      console.error("Socket authentication error:", error.message);
      next(new Error("Authentication failed"));
    }
  });

  io.on("connection", async (socket) => {
    console.log(`✅ Client connected: ${socket.id} (User: ${socket.user.email})`);
    socket.join(`user:${socket.userId}`);
    socket.emit("socket:connected", {
      success: true,
      socketId: socket.id,
      message: "Socket connected to Sovereign AI Service",
    });

    /**
     * Event: chat:send
     * Frontend sends: { conversationId?, message, model?, agent? }
     */
    socket.on("chat:send", async (data) => {
      const {
        conversationId,
        message,
        model = "auto",
        agent = "auto",
        requestId,
        images,
        attachment,
        file_ids,
        fileIds,
        files
      } = data;
      const messageId = requestId || `msg_${Date.now()}`;
      let chatId = conversationId;

      // Extract images vs document files
      let effectiveImages = [];
      let effectiveFileIds = [];

      if (Array.isArray(file_ids)) effectiveFileIds.push(...file_ids);
      if (Array.isArray(fileIds)) effectiveFileIds.push(...fileIds);
      if (Array.isArray(files)) {
        for (const f of files) {
          if (typeof f === "string") effectiveFileIds.push(f);
          else if (f?.path) effectiveFileIds.push(f.path);
          else if (f?.file_id || f?._id) effectiveFileIds.push(f.file_id || f._id);
        }
      }

      const isImagePayload = (mime, filename, dataUrl) => {
        if (mime && typeof mime === "string" && mime.toLowerCase().startsWith("image/")) return true;
        if (filename && typeof filename === "string") {
          const ext = path.extname(filename).toLowerCase();
          if ([".jpg", ".jpeg", ".png", ".webp", ".bmp", ".jfif", ".tiff", ".gif"].includes(ext)) return true;
        }
        if (dataUrl && typeof dataUrl === "string" && dataUrl.startsWith("data:image/")) return true;
        return false;
      };

      if (Array.isArray(images) && images.length > 0) {
        effectiveImages = images;
      }

      if (attachment && typeof attachment === "object") {
        const rawData = attachment.data || attachment.base64;
        const mime = attachment.type || "";
        const name = attachment.name || `attachment_${Date.now()}`;

        if (isImagePayload(mime, name, rawData)) {
          if (rawData) effectiveImages.push(rawData);
        } else if (rawData) {
          try {
            const uploadDir = path.resolve(__dirname, "../../uploads/documents");
            if (!fs.existsSync(uploadDir)) {
              fs.mkdirSync(uploadDir, { recursive: true });
            }
            const cleanName = name.replace(/[^a-zA-Z0-9._-]/g, "_");
            const targetFilename = `${Date.now()}-${cleanName}`;
            const targetPath = path.join(uploadDir, targetFilename);
            const base64Content = rawData.includes(";base64,") ? rawData.split(";base64,")[1] : rawData;
            fs.writeFileSync(targetPath, Buffer.from(base64Content, "base64"));
            effectiveFileIds.push(targetPath);
            console.log(`📎 Saved document attachment to ${targetPath} (${base64Content.length} chars)`);
          } catch (attErr) {
            console.error("Failed to save attachment file:", attErr);
          }
        } else if (attachment.path) {
          effectiveFileIds.push(attachment.path);
        } else if (attachment.file_id || attachment._id) {
          effectiveFileIds.push(attachment.file_id || attachment._id);
        }
      } else if (data.image) {
        effectiveImages.push(data.image);
      }

      console.log(`📨 chat:send from ${socket.user.email}: "${(message || '').substring(0, 50)}..." (images: ${effectiveImages.length}, files: ${effectiveFileIds.length})`);

      try {
        // Validate message, image, or document attachment
        if ((!message || message.trim().length === 0) && effectiveImages.length === 0 && effectiveFileIds.length === 0) {
          socket.emit("chat:error", {
            messageId,
            error: "Message, image, or document attachment cannot be empty",
            code: "INVALID_MESSAGE",
          });
          return;
        }

        const effectivePrompt = message && message.trim().length > 0 
          ? message.trim() 
          : (effectiveImages.length > 0 ? "Analyze this image" : "Analyze and summarize this document");

        // Resolve agent slug to DB Agent
        const Agent = require("../models/agent.model");
        const agentDoc = agent && agent !== "auto" ? await Agent.findOne({ slug: agent }) : null;
        if (agent && agent !== "auto" && !agentDoc) {
          const availableAgents = await Agent.find({ isActive: true }).select('slug name');
          console.error(`Agent '${agent}' not found. Available agents:`, availableAgents.map(a => a.slug));
          socket.emit("chat:error", {
            messageId,
            error: `Agent '${agent}' not found`,
            code: "AGENT_NOT_FOUND",
          });
          return;
        }

        // Extract agent config for forwarding to Python AI service
        const agentSystemPrompt = agentDoc?.systemPrompt;
        const agentTemperature = agentDoc?.temperature;
        const agentMaxTokens = agentDoc?.maxTokens;
        const effectiveModel = (model && model.toLowerCase() === "auto") ? "auto" : (agentDoc?.modelName || model);

        // Resolve or create conversation
        if (!chatId) {
          const newChat = await conversationModel.create({
            user: socket.userId,
            title: effectivePrompt.substring(0, 50),
            type: "chat",
            activeAgent: agentDoc?._id,
          });
          chatId = newChat._id.toString();
        }

        // Save user message with correct schema
        await messageModel.create({
          conversation: chatId,
          sender: "user",
          agent: agentDoc?._id,
          content: effectivePrompt,
        });

        // Emit start event
        const startedPayload = {
          conversationId: chatId,
          messageId,
          requestId: messageId,
          status: "processing",
        };
        socket.emit("chat:start", startedPayload); // legacy UI contract
        socket.emit("chat:started", startedPayload);
        socket.emit("chat:status", { ...startedPayload, stage: "accepted" });

        // Stream to AI service
        const abortController = new AbortController();
        activeGenerations.set(messageId, {
          abortController,
          socketId: socket.id,
          conversationId: chatId
        });

        // Stream to AI service
        await sendChatToAIStream({
          socket,
          abortSignal: abortController.signal,
          messageId,
          requestId: messageId,
          conversationId: chatId,
          message: effectivePrompt,
          model: effectiveModel,
          agent: agentDoc ? agentDoc.slug : agent,
          images: effectiveImages,
          fileIds: effectiveFileIds,
          systemPrompt: agentSystemPrompt,
          temperature: agentTemperature,
          maxTokens: agentMaxTokens,
          userId: socket.userId,
          isAdmin: Boolean(socket.user?.isAdmin || socket.user?.role === "admin"),
          userRole: socket.user?.role || (socket.user?.isAdmin ? "admin" : "operator"),
          userName: socket.user?.fullName ? `${socket.user.fullName.firstName || ""} ${socket.user.fullName.lastName || ""}`.trim() : socket.user?.email || "User",
          userEmail: socket.user?.email || "",
          onChunk: async (chunk, isComplete, fullResponse, generatedFiles = [], toolExecutions = [], multimodalData = null) => {
            // Skip empty chunks
            if (!isComplete && (chunk == null || (typeof chunk === 'string' && !chunk))) {
              return;
            }

            socket.emit("chat:chunk", {
              conversationId: chatId,
              messageId,
              chunk: chunk || "",
              isComplete,
              generatedFiles,
              toolExecutions,
            });
            if (!isComplete) socket.emit("chat:token", { conversationId: chatId, messageId, token: chunk || "" });

            if (isComplete) {
              // Prevent duplicate completion (race between stream 'end' and status:'completed')
              if (completedGenerations.has(messageId)) {
                return;
              }
              completedGenerations.add(messageId);
              setTimeout(() => completedGenerations.delete(messageId), 60000);

              const gen = activeGenerations.get(messageId);
              if (gen) gen.completed = true;
              activeGenerations.delete(messageId);

              const metadata = {};
              if (generatedFiles && generatedFiles.length > 0) metadata.generatedFiles = generatedFiles;
              if (toolExecutions && toolExecutions.length > 0) metadata.toolExecutions = toolExecutions;
              if (multimodalData) {
                if (multimodalData.ocr) metadata.ocr = multimodalData.ocr;
                if (multimodalData.vision) metadata.vision = multimodalData.vision;
              }

              // Only persist non-empty assistant responses
              if (fullResponse && fullResponse.trim().length > 0) {
                try {
                  await messageModel.create({
                    conversation: chatId,
                    sender: "assistant",
                    agent: agentDoc?._id,
                    content: fullResponse,
                    metadata: Object.keys(metadata).length > 0 ? metadata : undefined,
                  });
                } catch (dbErr) {
                  console.error(`❌ Failed to save assistant message for ${messageId}:`, dbErr.message);
                }
              } else {
                console.log(`⏭️ Skipping DB save for message ${messageId}: content is empty.`);
              }

              socket.emit("chat:complete", {
                conversationId: chatId,
                messageId,
                status: "completed",
                response: fullResponse || "",
                generatedFiles,
                toolExecutions,
                ocr: multimodalData?.ocr,
                vision: multimodalData?.vision,
              });
              socket.emit("chat:response", { conversationId: chatId, messageId, response: fullResponse || "", generatedFiles, toolExecutions });
              socket.emit("chat:completed", { conversationId: chatId, messageId, status: "completed" });
            }
          },
          onError: (error) => {
            activeGenerations.delete(messageId);
            const errorPayload = {
              messageId,
              error: error.message || "AI service error",
              code: error.code || "AI_SERVICE_ERROR",
            };
            socket.emit("chat:error", errorPayload);
            socket.emit("chat:completed", { conversationId: chatId, messageId, status: "failed" });
          },
        });
      } catch (error) {
        console.error("❌ Chat Error:", error);
        activeGenerations.delete(messageId);
        socket.emit("chat:error", {
          messageId,
          error: error.message || "Failed to process message",
          code: "INTERNAL_ERROR",
        });
        socket.emit("chat:completed", { conversationId: chatId, messageId, status: "failed" });
      }
    });

    /**
     * Event: chat:stop
     * Frontend sends: { requestId, conversationId }
     */
    socket.on("chat:stop", (data) => {
      const { requestId, conversationId } = data;
      console.log(`🛑 chat:stop requested for requestId: ${requestId}`);
      
      const generation = activeGenerations.get(requestId);
      if (generation && generation.socketId === socket.id) {
        generation.abortController.abort();
        activeGenerations.delete(requestId);
        socket.emit("chat:stopped", { requestId, conversationId, status: "stopped" });
        console.log(`✅ Aborted generation for requestId: ${requestId}`);
      } else {
        console.warn(`⚠️ Could not find active generation to stop for requestId: ${requestId}`);
      }
    });

    /**
     * Event: conversation:join
     * User joins a specific conversation room
     */
    socket.on("conversation:join", async (data) => {
      const { conversationId } = data;

      try {
        // Verify user has access to this conversation
        const chat = await conversationModel.findById(conversationId);
        
        if (!chat) {
          socket.emit("chat:error", {
            error: "Conversation not found",
            code: "CONVERSATION_NOT_FOUND",
          });
          return;
        }

        if (chat.user && !chat.user.equals(socket.userId)) {
          socket.emit("chat:error", {
            error: "Unauthorized access",
            code: "UNAUTHORIZED",
          });
          return;
        }

        // Join room
        socket.join(`conversation:${conversationId}`);
        console.log(`📍 User ${socket.user.email} joined conversation ${conversationId}`);

        socket.emit("conversation:joined", {
          conversationId,
          status: "joined",
        });
      } catch (error) {
        console.error("❌ Join Conversation Error:", error);
        socket.emit("chat:error", {
          error: "Failed to join conversation",
          code: "JOIN_ERROR",
        });
      }
    });

    /**
     * Event: conversation:leave
     * User leaves a conversation room
     */
    socket.on("conversation:leave", (data) => {
      const { conversationId } = data;
      socket.leave(`conversation:${conversationId}`);
      console.log(`📍 User ${socket.user.email} left conversation ${conversationId}`);
    });

    /**
     * Event: health:check
     * Frontend can request AI service health
     */
    socket.on("health:check", async () => {
      try {
        const health = await checkAIServiceHealth();
        socket.emit("health:status", health);
      } catch (error) {
        socket.emit("health:status", {
          success: false,
          status: "offline",
          message: "AI Service unreachable",
        });
      }
    });

    /**
     * Disconnection Handler
     */
    socket.on("disconnect", () => {
      console.log(`🔌 Client disconnected: ${socket.id} (User: ${socket.user.email})`);
      // Cleanup active generations
      for (const [reqId, gen] of activeGenerations.entries()) {
        if (gen.socketId === socket.id) {
          gen.abortController.abort();
          activeGenerations.delete(reqId);
          console.log(`🧹 Aborted orphaned generation ${reqId} on disconnect`);
        }
      }
    });

    /**
     * Error Handler
     */
    socket.on("error", (error) => {
      console.error(`❌ Socket Error [${socket.id}]:`, error);
    });
  });

  console.log("🔌 Socket.IO server initialized");
  return io;
};
