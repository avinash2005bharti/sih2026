import React, { useState, useRef, useEffect } from 'react';
import {
  Paperclip,
  ArrowUp,
  SlidersHorizontal,
  Mic,
  MicOff,
  Cpu,
  ChevronDown,
  Sparkles,
  X,
  FileText,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';

const ChatInputBar = ({ inputRef, onSend, initialValue = '' }) => {
  const {
    agents,
    selectedAgent,
    setSelectedAgent,
    models,
    selectedModel,
    setSelectedModel,
    deepReasoning,
    setDeepReasoning,
    isGenerating,
  } = useChat();

  const [input, setInput] = useState(initialValue);
  const [isListening, setIsListening] = useState(false);
  const [attachment, setAttachment] = useState(null);
  const [showAgentMenu, setShowAgentMenu] = useState(false);
  const [showModelMenu, setShowModelMenu] = useState(false);

  const fileInputRef = useRef(null);
  const internalRef = useRef(null);
  const textareaRef = inputRef || internalRef;

  useEffect(() => {
    if (initialValue) {
      setInput(initialValue);
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }
  }, [initialValue]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [input]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if ((!input.trim() && !attachment) || isGenerating) return;
    onSend(input, attachment);
    setInput('');
    setAttachment(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setAttachment({
        name: file.name,
        size: (file.size / 1024).toFixed(1) + ' KB',
        type: file.type || 'document',
      });
    }
  };

  // Mock voice input simulation
  const toggleListening = () => {
    if (isListening) {
      setIsListening(false);
    } else {
      setIsListening(true);
      setInput((prev) =>
        prev
          ? `${prev} [Vibrational anomaly detected on bearing unit 4]`
          : 'Analyze hydraulic pressure variance in compressor line B.'
      );
      setTimeout(() => setIsListening(false), 2500);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-4">
      {/* File Attachment Pill if selected */}
      {attachment && (
        <div className="mb-2 inline-flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800 animate-in fade-in">
          <FileText className="w-4 h-4 text-blue-600" />
          <span className="font-medium">{attachment.name}</span>
          <span className="text-[10px] text-blue-500">({attachment.size})</span>
          <button
            onClick={() => setAttachment(null)}
            className="p-0.5 hover:text-rose-600 rounded"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Main Input Card */}
      <div className="bg-white border border-slate-200/90 rounded-2xl shadow-card transition-shadow focus-within:border-blue-500/80 focus-within:ring-2 focus-within:ring-blue-100 overflow-visible relative">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Message Sovereign AI or upload technical specs, P&IDs, telemetry logs..."
          className="w-full pt-3.5 pb-2 px-4 text-sm text-slate-800 placeholder-slate-400 bg-transparent resize-none focus:outline-none max-h-[200px]"
        />

        {/* Bottom Action Controls */}
        <div className="px-3 pb-3 pt-1 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100/80 mt-1">
          {/* Left Controls */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-600">
            {/* Attach Spec */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg hover:bg-slate-100 text-slate-600 font-medium transition-colors"
              title="Attach Technical Spec, Manual or P&ID"
            >
              <Paperclip className="w-3.5 h-3.5 text-slate-500" />
              <span className="hidden sm:inline">Attach Spec</span>
            </button>

            {/* @Agent Selector */}
            <div className="relative">
              <button
                type="button"
                onClick={() => {
                  setShowAgentMenu(!showAgentMenu);
                  setShowModelMenu(false);
                }}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg hover:bg-blue-50 text-blue-700 font-semibold transition-colors"
              >
                <span>@{selectedAgent?.name || 'Agent'}</span>
                <ChevronDown className="w-3 h-3" />
              </button>

              {showAgentMenu && (
                <div className="absolute bottom-full mb-2 left-0 w-52 bg-white border border-slate-200 rounded-xl shadow-lg py-1 z-50 animate-in fade-in">
                  <div className="px-3 py-1 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                    Target Specialized Agent
                  </div>
                  {agents.map((agent) => (
                    <button
                      key={agent._id}
                      type="button"
                      onClick={() => {
                        setSelectedAgent(agent);
                        setShowAgentMenu(false);
                      }}
                      className="w-full text-left px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-100 flex items-center justify-between"
                    >
                      <span>{agent.name}</span>
                      <span className="text-[10px] text-slate-400">{agent.type}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Model Selector */}
            <div className="relative">
              <button
                type="button"
                onClick={() => {
                  setShowModelMenu(!showModelMenu);
                  setShowAgentMenu(false);
                }}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100/90 hover:bg-slate-200/80 text-slate-800 text-[11px] font-mono transition-colors"
                title="Select Local Air-Gapped Model"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span>{selectedModel?.displayName || 'Llama-3-70B-Gov'}</span>
                <SlidersHorizontal className="w-3 h-3 text-slate-400 ml-0.5" />
              </button>

              {showModelMenu && (
                <div className="absolute bottom-full mb-2 left-0 w-64 bg-white border border-slate-200 rounded-xl shadow-lg py-1 z-50 animate-in fade-in">
                  <div className="px-3 py-1 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                    On-Prem Model Registry
                  </div>
                  {models.map((mod) => (
                    <button
                      key={mod._id}
                      type="button"
                      onClick={() => {
                        setSelectedModel(mod);
                        setShowModelMenu(false);
                      }}
                      className="w-full text-left px-3 py-2 text-xs text-slate-700 hover:bg-slate-100 flex items-center justify-between"
                    >
                      <div>
                        <div className="font-mono font-medium text-slate-900">
                          {mod.displayName}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          {mod.provider} • {(mod.contextWindow / 1024).toFixed(0)}k Context
                        </div>
                      </div>
                      <span className="text-[10px] px-1.5 py-0.5 bg-emerald-50 text-emerald-700 rounded font-mono">
                        Local
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Deep Reasoning Toggle */}
            <button
              type="button"
              onClick={() => setDeepReasoning(!deepReasoning)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all ${
                deepReasoning
                  ? 'bg-purple-50 text-purple-700 border border-purple-200/80 font-semibold'
                  : 'text-slate-500 hover:bg-slate-100'
              }`}
              title="Multi-hop Graph RAG and Verification Steps"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Deep Reasoning</span>
            </button>

            {/* Microphone Voice Button */}
            <button
              type="button"
              onClick={toggleListening}
              className={`p-1.5 rounded-lg transition-colors ${
                isListening
                  ? 'bg-rose-50 text-rose-600 animate-pulse'
                  : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'
              }`}
              title="Voice Telemetry Dictation"
            >
              {isListening ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
            </button>
          </div>

          {/* Right Controls */}
          <div className="flex items-center gap-2">
            {/* Context Window Badge */}
            <span className="hidden sm:inline-flex items-center px-2 py-0.5 bg-slate-100 text-slate-600 text-[10px] font-mono rounded border border-slate-200">
              128k On-Prem
            </span>

            {/* Send Button */}
            <button
              type="button"
              onClick={handleSubmit}
              disabled={(!input.trim() && !attachment) || isGenerating}
              className="w-8 h-8 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:hover:bg-blue-600 text-white flex items-center justify-center shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
              aria-label="Send message"
            >
              <ArrowUp className="w-4 h-4 stroke-[2.5]" />
            </button>
          </div>
        </div>
      </div>

      {/* Air-Gap Security Disclaimer Footer */}
      <div className="text-center text-[10px] text-slate-400 font-mono mt-2 tracking-tight">
        Confidential PSU / Defence Tier • All reasoning runs strictly on sovereign isolated
        hardware • Strict air-gap audit logging active
      </div>
    </div>
  );
};

export default ChatInputBar;
