const fs = require('fs');

const contextPath = 'FRONTEND/src/context/ChatContext.jsx';
let content = fs.readFileSync(contextPath, 'utf8');

// Import stopChatMessage
content = content.replace(
  /sendChatMessage, subscribeToChatEvents, joinConversation \} from '\.\.\/services\/socket';/g,
  `sendChatMessage, subscribeToChatEvents, joinConversation, stopChatMessage } from '../services/socket';`
);

// Add currentRequestId to state
content = content.replace(
  /const \[isGenerating, setIsGenerating\] = useState\(false\);/g,
  `const [isGenerating, setIsGenerating] = useState(false);\n  const [currentRequestId, setCurrentRequestId] = useState(null);`
);

// Update sendChatMessage call
content = content.replace(
  /sendChatMessage\(content\.trim\(\), \{[\s\n]*conversationId: targetChatId,[\s\n]*model: modelToUse,[\s\n]*agent: agentToUse,[\s\n]*\}\);/g,
  `const reqId = 'req_' + Date.now();
        setCurrentRequestId(reqId);
        sendChatMessage(content.trim(), {
          conversationId: targetChatId,
          model: modelToUse,
          agent: agentToUse,
          requestId: reqId
        });`
);

// Add onStopped handler
content = content.replace(
  /onError: \(error\) => \{/g,
  `onStopped: (data) => {
            console.log("🛑 Chat stopped via Socket", data);
            setIsGenerating(false);
            setCurrentRequestId(null);
          },
          onError: (error) => {`
);

// Clear currentRequestId on completion/error
content = content.replace(
  /setIsGenerating\(false\);[\s\n]*\},[\s\n]*onStopped:/g,
  `setIsGenerating(false);\n            setCurrentRequestId(null);\n          },\n          onStopped:`
);

content = content.replace(
  /setSendError\(error\.error \|\| 'Failed to get a response'\);[\s\n]*setIsGenerating\(false\);/g,
  `setSendError(error.error || 'Failed to get a response');\n            setIsGenerating(false);\n            setCurrentRequestId(null);`
);

// Add stopGeneration function
const stopGenFn = `
  const stopGeneration = useCallback(() => {
    if (socketConnected && currentRequestId) {
      console.log('🛑 Requesting generation stop for', currentRequestId);
      stopChatMessage(currentRequestId, activeChatId);
      setIsGenerating(false); // Optimistic UI update
    }
  }, [socketConnected, currentRequestId, activeChatId]);
`;
content = content.replace(
  /const deleteChat = async \(chatId\) => \{/g,
  stopGenFn + '\n  const deleteChat = async (chatId) => {'
);

// Add stopGeneration to context value
content = content.replace(
  /deleteChat,[\s\n]*refreshChats: fetchChats,/g,
  `deleteChat,\n        refreshChats: fetchChats,\n        stopGeneration,`
);

fs.writeFileSync(contextPath, content, 'utf8');
console.log('ChatContext.jsx patched successfully!');
