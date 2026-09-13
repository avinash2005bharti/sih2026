import React, { useEffect, useRef } from 'react';
import ChatMessageItem from './ChatMessageItem';
import { Shield } from 'lucide-react';
import { useChat } from '../../context/ChatContext';

const ChatMessageList = ({ messages }) => {
  const bottomRef = useRef(null);
  const { isGenerating, selectedAgent, selectedModel } = useChat();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isGenerating]);

  return (
    <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
      {messages.map((msg, index) => (
        <ChatMessageItem key={msg._id || index} message={msg} />
      ))}

      {/* Generating / Thinking Indicator */}
      {isGenerating && (
        <div className="py-4 px-4 sm:px-6 bg-white/60 border-y border-slate-100">
          <div className="max-w-4xl mx-auto flex gap-3.5 items-start">
            <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center flex-shrink-0 animate-pulse">
              <Shield className="w-4 h-4 fill-white/20" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-xs font-semibold text-slate-900">
                  {selectedAgent?.name || 'Sovereign Assistant'}
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  {selectedModel?.displayName || 'Llama-3-70B'}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
                <div className="flex gap-1 items-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce" />
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce [animation-delay:0.2s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce [animation-delay:0.4s]" />
                </div>
                <span className="text-[11px] text-slate-400 ml-1">
                  Parsing local knowledge graph & telemetry...
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} className="h-4" />
    </div>
  );
};

export default ChatMessageList;
