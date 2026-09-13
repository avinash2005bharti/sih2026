const fs = require('fs');

const socketPath = 'FRONTEND/src/services/socket.js';
let content = fs.readFileSync(socketPath, 'utf8');

// Update sendChatMessage signature
content = content.replace(
  /export const sendChatMessage = \(message, \{ conversationId = null, model = "auto", agent = "general" \} = \{\}\) => \{/g,
  `export const sendChatMessage = (message, { conversationId = null, model = "auto", agent = "general", requestId = null } = {}) => {`
);

content = content.replace(
  /const messageId = `msg_\$\{Date\.now\(\)\}`;[\s\n]*socket\.emit\("chat:send", \{[\s\n]*conversationId,[\s\n]*message,[\s\n]*model,[\s\n]*agent,[\s\n]*\}\);/g,
  `const messageId = requestId || \`msg_\${Date.now()}\`;
  socket.emit("chat:send", {
    conversationId,
    message,
    model,
    agent,
    requestId: messageId
  });`
);

// Add stopChatMessage function
const stopFn = `
/**
 * Stop a chat generation via Socket.IO
 */
export const stopChatMessage = (requestId, conversationId) => {
  if (!socket) return;
  socket.emit("chat:stop", { requestId, conversationId });
};
`;
content = content.replace(
  /export const checkAIServiceHealth/g,
  stopFn + '\nexport const checkAIServiceHealth'
);

// Update subscribeToChatEvents to accept onStopped
content = content.replace(
  /export const subscribeToChatEvents = \(\{ onStart, onChunk, onComplete, onError \} = \{\}\) => \{/g,
  `export const subscribeToChatEvents = ({ onStart, onChunk, onComplete, onError, onStopped } = {}) => {`
);

content = content.replace(
  /const errorHandler = \(data\) => \{[^}]+\};/g,
  `const errorHandler = (data) => {
    console.error("❌ chat:error", data);
    onError?.(data);
  };
  const stoppedHandler = (data) => {
    console.log("🛑 chat:stopped", data);
    onStopped?.(data);
  };`
);

content = content.replace(
  /socket\.on\("chat:error", errorHandler\);/g,
  `socket.on("chat:error", errorHandler);
  socket.on("chat:stopped", stoppedHandler);`
);

content = content.replace(
  /socket\.off\("chat:error", errorHandler\);/g,
  `socket.off("chat:error", errorHandler);
    socket.off("chat:stopped", stoppedHandler);`
);

content = content.replace(
  /subscribeToChatEvents,[\s\n]*subscribeToHealthEvents/g,
  `stopChatMessage,
  subscribeToChatEvents,
  subscribeToHealthEvents`
);

fs.writeFileSync(socketPath, content, 'utf8');
console.log('socket.js patched successfully!');
