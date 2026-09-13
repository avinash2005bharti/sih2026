const fs = require('fs');

const socketServerPath = 'BACKEND/src/sockets/socket.server.js';
let content = fs.readFileSync(socketServerPath, 'utf8');

// Add activeGenerations map
content = content.replace(
  'module.exports = (server) => {',
  'const activeGenerations = new Map();\n\nmodule.exports = (server) => {'
);

// Replace chat:send event parsing
content = content.replace(
  /const messageId = `msg_\$\{Date\.now\(\)\}`;[\s\n]*const \{ conversationId, message, model = "auto", agent = "general" \} = data;/g,
  `const { conversationId, message, model = "auto", agent = "general", requestId } = data;\n      const messageId = requestId || \`msg_\${Date.now()}\`;`
);

// Add abort controller logic right before sending to AI
content = content.replace(
  /await sendChatToAIStream\(\{[\s\n]*socket,/g,
  `const abortController = new AbortController();
        activeGenerations.set(messageId, {
          abortController,
          socketId: socket.id,
          conversationId: chatId
        });

        // Stream to AI service
        await sendChatToAIStream({
          socket,
          abortSignal: abortController.signal,`
);

// Fix empty chunk database insertion and cleanup activeGenerations
content = content.replace(
  /if \(isComplete\) \{[\s\n]*const metadata = \{\};[\s\n]*if \(generatedFiles && generatedFiles\.length > 0\) metadata\.generatedFiles = generatedFiles;[\s\n]*if \(toolExecutions && toolExecutions\.length > 0\) metadata\.toolExecutions = toolExecutions;[\s\n]*await messageModel\.create\(\{[\s\n]*conversation: chatId,[\s\n]*sender: "assistant",[\s\n]*agent: agentDoc\._id,[\s\n]*content: fullResponse,[\s\n]*metadata: Object\.keys\(metadata\)\.length > 0 \? metadata : undefined,[\s\n]*\}\);[\s\n]*socket\.emit\("chat:complete"/g,
  `if (isComplete) {
              activeGenerations.delete(messageId);
              const metadata = {};
              if (generatedFiles && generatedFiles.length > 0) metadata.generatedFiles = generatedFiles;
              if (toolExecutions && toolExecutions.length > 0) metadata.toolExecutions = toolExecutions;

              if (fullResponse && fullResponse.trim().length > 0) {
                await messageModel.create({
                  conversation: chatId,
                  sender: "assistant",
                  agent: agentDoc._id,
                  content: fullResponse,
                  metadata: Object.keys(metadata).length > 0 ? metadata : undefined,
                });
              } else {
                console.log(\`Skipping DB save for message \${messageId}: content is empty.\`);
              }
              socket.emit("chat:complete"`
);

// Clean up activeGenerations on error
content = content.replace(
  /onError: \(error\) => \{[\s\n]*socket\.emit\("chat:error", \{/g,
  `onError: (error) => {
            activeGenerations.delete(messageId);
            socket.emit("chat:error", {`
);

content = content.replace(
  /console\.error\(".* Chat Error:", error\);[\s\n]*socket\.emit\("chat:error", \{[\s\n]*messageId,[\s\n]*error: error\.message \|\| "Failed to process message",[\s\n]*code: "INTERNAL_ERROR",[\s\n]*\}\);/g,
  `console.error("❌ Chat Error:", error);
        activeGenerations.delete(messageId);
        socket.emit("chat:error", {
          messageId,
          error: error.message || "Failed to process message",
          code: "INTERNAL_ERROR",
        });`
);

// Add chat:stop
content = content.replace(
  /\/\*\*[\s\n]*\* Event: conversation:join/g,
  `/**
     * Event: chat:stop
     * Frontend sends: { requestId, conversationId }
     */
    socket.on("chat:stop", (data) => {
      const { requestId, conversationId } = data;
      console.log(\`🛑 chat:stop requested for requestId: \${requestId}\`);
      
      const generation = activeGenerations.get(requestId);
      if (generation && generation.socketId === socket.id) {
        generation.abortController.abort();
        activeGenerations.delete(requestId);
        socket.emit("chat:stopped", { requestId, conversationId, status: "stopped" });
        console.log(\`✅ Aborted generation for requestId: \${requestId}\`);
      } else {
        console.warn(\`⚠️ Could not find active generation to stop for requestId: \${requestId}\`);
      }
    });

    /**
     * Event: conversation:join`
);

// Add disconnect cleanup
content = content.replace(
  /socket\.on\("disconnect", \(\) => \{[\s\n]*console\.log\(`[^`]+`\);[\s\n]*\}\);/g,
  `socket.on("disconnect", () => {
      console.log(\`🔌 Client disconnected: \${socket.id} (User: \${socket.user.email})\`);
      // Cleanup active generations
      for (const [reqId, gen] of activeGenerations.entries()) {
        if (gen.socketId === socket.id) {
          gen.abortController.abort();
          activeGenerations.delete(reqId);
          console.log(\`🧹 Aborted orphaned generation \${reqId} on disconnect\`);
        }
      }
    });`
);

fs.writeFileSync(socketServerPath, content, 'utf8');
console.log('socket.server.js patched successfully!');
