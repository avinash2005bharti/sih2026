import React, { useRef, useState } from 'react';
import { useChat } from '../context/ChatContext';
import ChatEmptyHero from '../components/chat/ChatEmptyHero';
import ChatMessageList from '../components/chat/ChatMessageList';
import ChatInputBar from '../components/chat/ChatInputBar';
import Loader from '../components/common/Loader';

const ChatPage = () => {
  const { messages, loadingMessages, sendMessage } = useChat();
  const [promptText, setPromptText] = useState('');
  const inputRef = useRef(null);

  const handleSelectPrompt = (prompt) => {
    setPromptText(prompt);
  };

  const handleSend = (content, attachment) => {
    sendMessage(content, attachment);
    setPromptText('');
  };

  return (
    <div className="flex flex-col h-full w-full relative">
      {/* Scrollable conversation or centered hero */}
      <div className="flex-1 overflow-y-auto flex flex-col">
        {loadingMessages ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader text="Decentralized sovereign message retrieval..." size="md" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex-1 flex items-center justify-center my-auto py-6">
            <ChatEmptyHero onSelectPrompt={handleSelectPrompt} />
          </div>
        ) : (
          <ChatMessageList messages={messages} />
        )}
      </div>

      {/* Fixed Chat Input Bar at Bottom */}
      <div className="sticky bottom-0 z-20 bg-gradient-to-t from-[#f8fafc] via-[#f8fafc] to-transparent pt-4">
        <ChatInputBar
          inputRef={inputRef}
          onSend={handleSend}
          initialValue={promptText}
        />
      </div>
    </div>
  );
};

export default ChatPage;
