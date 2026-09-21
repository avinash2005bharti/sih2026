import React, { useState, useRef, useEffect } from 'react';
import {
  Plus,
  ArrowUp,
  Mic,
  MicOff,
  X,
  FileText,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';

const ChatInputBar = ({ inputRef, onSend, initialValue = '' }) => {
  const { selectedAgent, isGenerating, stopGeneration } = useChat();

  const [input, setInput] = useState(initialValue);
  const [attachment, setAttachment] = useState(null);

  // Speech Recognition state
  const [isListening, setIsListening] = useState(false);
  const [speechError, setSpeechError] = useState(null);
  const recognitionRef = useRef(null);
  const baseInputRef = useRef('');

  const fileInputRef = useRef(null);
  const internalRef = useRef(null);
  const textareaRef = inputRef || internalRef;

  // Sync initial value if provided from parent (e.g., prompt suggestions)
  useEffect(() => {
    if (initialValue) {
      setInput(initialValue);
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }
  }, [initialValue]);

  // Auto-resize textarea according to scrollHeight
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        180
      )}px`;
    }
  }, [input]);

  // Handle keyboard submit on Enter (Shift+Enter for newline)
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if ((!input.trim() && !attachment) || isGenerating) return;

    // Stop speech recognition if still active
    if (isListening) {
      stopListening();
    }

    onSend(input.trim(), attachment);
    setInput('');
    setAttachment(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setAttachment({
          file,
          name: file.name,
          size: (file.size / 1024).toFixed(1) + ' KB',
          type: file.type || 'application/octet-stream',
          base64: reader.result,
        });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveAttachment = () => {
    setAttachment(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Browser Web Speech API implementation
  const isSpeechSupported =
    typeof window !== 'undefined' &&
    Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);

  const startListening = () => {
    setSpeechError(null);

    if (!isSpeechSupported) {
      setSpeechError(
        'Speech recognition is not supported in this browser. Please use Chrome or Edge.'
      );
      setTimeout(() => setSpeechError(null), 4500);
      return;
    }

    try {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;

      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      baseInputRef.current = input;

      recognition.onstart = () => {
        setIsListening(true);
        setSpeechError(null);
      };

      recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const trans = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += trans;
          } else {
            interimTranscript += trans;
          }
        }

        const speechText = (finalTranscript || interimTranscript).trim();
        if (speechText) {
          const prefix = baseInputRef.current
            ? baseInputRef.current.trim() + ' '
            : '';
          setInput(prefix + speechText);
        }
      };

      recognition.onerror = (event) => {
        console.warn('SpeechRecognition error:', event.error);
        if (event.error === 'not-allowed') {
          setSpeechError(
            'Microphone access denied. Please allow microphone permissions in your browser.'
          );
        } else if (event.error === 'no-speech') {
          // No speech detected, quietly ignore
        } else if (event.error !== 'aborted') {
          setSpeechError(`Microphone error: ${event.error}`);
        }
        setIsListening(false);
        setTimeout(() => setSpeechError(null), 4500);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.start();
    } catch (err) {
      console.error('Failed to initialize speech recognition:', err);
      setSpeechError('Could not initialize speech recognition.');
      setIsListening(false);
      setTimeout(() => setSpeechError(null), 4500);
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        // Ignore stop error
      }
      recognitionRef.current = null;
    }
    setIsListening(false);
  };

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  // Clean up recognition listener on component unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          // Ignore unmount error
        }
      }
    };
  }, []);

  const agentDisplayName = selectedAgent?.name || 'General Agent';

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-4">
      {/* 1. Agent Name Indicator */}
      <div className="flex items-center justify-center mb-2.5">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/95 border border-slate-200 text-slate-700 text-xs font-semibold shadow-2xs">
          <span className="w-2 h-2 rounded-full bg-blue-600 flex-shrink-0" />
          <span className="tracking-tight">{agentDisplayName}</span>
        </div>
      </div>

      {/* 2. Composer Card */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-card p-2 sm:p-2.5 transition-all focus-within:border-blue-500/80 focus-within:ring-2 focus-within:ring-blue-100">
        {/* Attachment Preview Pill */}
        {attachment && (
          <div className="mb-2 inline-flex items-center gap-2 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 animate-in fade-in">
            <FileText className="w-4 h-4 text-blue-600 flex-shrink-0" />
            <span className="font-medium truncate max-w-[200px] sm:max-w-md">
              {attachment.name}
            </span>
            <span className="text-[10px] text-slate-400 font-mono">
              ({attachment.size})
            </span>
            <button
              type="button"
              onClick={handleRemoveAttachment}
              className="p-0.5 text-slate-400 hover:text-rose-600 rounded transition-colors"
              title="Remove attachment"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Speech Error Banner */}
        {speechError && (
          <div className="mb-2 p-2 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center gap-2 animate-in fade-in">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600" />
            <span>{speechError}</span>
          </div>
        )}

        {/* Listening Active Banner */}
        {isListening && (
          <div className="mb-2 flex items-center justify-between px-3 py-1.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs animate-in fade-in">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
              <span className="font-medium">Listening to speech... Speak clearly</span>
            </div>
            <button
              type="button"
              onClick={stopListening}
              className="text-[11px] font-semibold text-rose-700 hover:underline"
            >
              Done
            </button>
          </div>
        )}

        {/* Main Composer Row: [+] [Textarea] [Mic] [Send] */}
        <div className="flex items-center gap-1 sm:gap-2">
          {/* File Attachment Button (+) */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
            accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.json,.py,.md,.png,.jpg,.jpeg"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isGenerating}
            className="w-9 h-9 rounded-full flex items-center justify-center text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors flex-shrink-0 disabled:opacity-40"
            title="Attach File (+)"
          >
            <Plus className="w-5 h-5 stroke-[2]" />
          </button>

          {/* Auto-resizing Text Input */}
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask Sovereign AI to do something..."
            disabled={isGenerating}
            className="flex-1 max-h-[180px] py-2 px-2 text-sm text-slate-900 placeholder-slate-400 bg-transparent resize-none focus:outline-none leading-relaxed"
          />

          {/* Microphone Button */}
          <button
            type="button"
            onClick={toggleListening}
            disabled={isGenerating}
            className={`w-9 h-9 rounded-full flex items-center justify-center transition-colors flex-shrink-0 ${
              isListening
                ? 'bg-rose-500 text-white shadow-xs animate-pulse'
                : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
            }`}
            title={isListening ? 'Stop listening' : 'Dictate with microphone'}
          >
            {isListening ? (
              <MicOff className="w-4 h-4" />
            ) : (
              <Mic className="w-4 h-4" />
            )}
          </button>

          {/* Send Button */}
          <button
            type="button"
            onClick={isGenerating ? stopGeneration : handleSubmit}
            disabled={!isGenerating && !input.trim() && !attachment}
            className={`w-9 h-9 rounded-full flex items-center justify-center shadow-xs transition-all flex-shrink-0 ${
              isGenerating
                ? 'bg-rose-500 hover:bg-rose-600 text-white'
                : !input.trim() && !attachment
                ? 'bg-slate-100 text-slate-300 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
            title={isGenerating ? 'Stop generating' : 'Send message (Enter)'}
            aria-label={isGenerating ? 'Stop generating' : 'Send message'}
          >
            {isGenerating ? (
              <span className="w-3.5 h-3.5 rounded-sm bg-white" />
            ) : (
              <ArrowUp className="w-4 h-4 stroke-[2.5]" />
            )}
          </button>
        </div>
      </div>

      {/* Sovereign Footnote */}
      <div className="text-center text-[10px] text-slate-400 font-mono mt-2 tracking-tight">
        Confidential PSU / Defense Grade • Sovereign On-Premise Execution
      </div>
    </div>
  );
};

export default ChatInputBar;
