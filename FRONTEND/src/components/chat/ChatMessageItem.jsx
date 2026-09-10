import React, { useState } from 'react';
import {
  Shield,
  User,
  Sparkles,
  Copy,
  Check,
  ThumbsUp,
  ThumbsDown,
  ChevronRight,
  FileText,
  Lock,
  Cpu,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';

const ChatMessageItem = ({ message }) => {
  const isUser = message.sender === 'user';
  const { setActiveReasoningTrace } = useChat();
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Helper to format basic markdown (headers, bold, tables, lists, quotes)
  const renderFormattedContent = (content) => {
    if (!content) return null;

    const lines = content.split('\n');
    const rendered = [];
    let inTable = false;
    let tableRows = [];

    lines.forEach((line, index) => {
      // Table detection
      if (line.trim().startsWith('|')) {
        inTable = true;
        tableRows.push(line);
        return;
      } else if (inTable) {
        inTable = false;
        rendered.push(
          <div key={`table-${index}`} className="my-3 overflow-x-auto border border-slate-200 rounded-lg shadow-2xs">
            <table className="min-w-full text-xs text-left divide-y divide-slate-200">
              <tbody className="divide-y divide-slate-100 bg-white">
                {tableRows.map((row, rIdx) => {
                  const cells = row
                    .split('|')
                    .filter((c, i, a) => i !== 0 && i !== a.length - 1);
                  if (row.includes('---')) return null; // delimiter row
                  const isHeader = rIdx === 0;
                  return (
                    <tr
                      key={rIdx}
                      className={isHeader ? 'bg-slate-50 font-semibold text-slate-800' : 'hover:bg-slate-50/60'}
                    >
                      {cells.map((cell, cIdx) => (
                        <td key={cIdx} className="px-3 py-2 text-slate-700 whitespace-nowrap">
                          {cell.trim()}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        );
        tableRows = [];
      }

      // Headers
      if (line.startsWith('### ')) {
        rendered.push(
          <h4 key={index} className="text-sm font-bold text-slate-900 mt-3 mb-1.5 flex items-center gap-1.5">
            {line.replace('### ', '').replace(/\*\*/g, '')}
          </h4>
        );
      } else if (line.startsWith('## ')) {
        rendered.push(
          <h3 key={index} className="text-base font-bold text-slate-900 mt-4 mb-2">
            {line.replace('## ', '').replace(/\*\*/g, '')}
          </h3>
        );
      } else if (line.startsWith('> ')) {
        // Blockquote
        rendered.push(
          <div
            key={index}
            className="my-2 p-2.5 bg-blue-50/80 border-l-3 border-blue-600 text-xs text-blue-900 rounded-r-lg font-medium"
          >
            {line.replace('> ', '').replace(/\*\*/g, '')}
          </div>
        );
      } else if (line.trim().startsWith('* ') || line.trim().startsWith('- ')) {
        // Bullet item
        const text = line.replace(/^[\*\-]\s+/, '');
        rendered.push(
          <div key={index} className="flex items-start gap-2 text-xs text-slate-700 my-1 pl-1">
            <span className="text-blue-600 font-bold mt-0.5">•</span>
            <span>{parseInlineStyles(text)}</span>
          </div>
        );
      } else if (line.trim().match(/^\d+\.\s/)) {
        // Numbered item
        const num = line.match(/^(\d+\.)\s/)[1];
        const text = line.replace(/^\d+\.\s+/, '');
        rendered.push(
          <div key={index} className="flex items-start gap-2 text-xs text-slate-700 my-1 pl-1">
            <span className="text-blue-600 font-semibold font-mono text-[11px]">{num}</span>
            <span>{parseInlineStyles(text)}</span>
          </div>
        );
      } else if (line.trim()) {
        rendered.push(
          <p key={index} className="text-xs sm:text-sm text-slate-700 my-1.5 leading-relaxed">
            {parseInlineStyles(line)}
          </p>
        );
      }
    });

    return rendered;
  };

  const parseInlineStyles = (text) => {
    // Basic bold and code span formatting
    const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code
            key={i}
            className="px-1.5 py-0.5 bg-slate-100 text-slate-800 rounded font-mono text-[11px] border border-slate-200"
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={i} className="font-semibold text-slate-900">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return part;
    });
  };

  return (
    <div className={`py-4 px-4 sm:px-6 w-full ${isUser ? 'bg-transparent' : 'bg-white/60 border-y border-slate-100'}`}>
      <div className="max-w-4xl mx-auto flex gap-3.5 items-start">
        {/* Avatar */}
        <div className="flex-shrink-0 mt-0.5">
          {isUser ? (
            <div className="w-7 h-7 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs font-semibold ring-1 ring-slate-200">
              <User className="w-3.5 h-3.5" />
            </div>
          ) : (
            <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center shadow-xs">
              <Shield className="w-4 h-4 fill-white/20" />
            </div>
          )}
        </div>

        {/* Message Container */}
        <div className="flex-1 min-w-0">
          {/* Metadata Header */}
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-slate-900">
              {isUser ? 'You' : 'Sovereign Assistant'}
            </span>

            {!isUser && message.agent && (
              <span className="px-2 py-0.2 bg-blue-50 text-blue-700 rounded-full text-[10px] font-mono border border-blue-200/60">
                {message.agent.name || 'Orchestrator'}
              </span>
            )}

            {!isUser && message.modelUsed && (
              <span className="text-[10px] font-mono text-slate-400 hidden sm:inline">
                {message.modelUsed.displayName || 'Llama-3-70B'}
              </span>
            )}

            <span className="text-[10px] text-slate-400 ml-auto font-mono">
              {new Date(message.createdAt || Date.now()).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>

          {/* User Attachment pill if present */}
          {message.attachment && (
            <div className="mb-2 inline-flex items-center gap-2 px-2.5 py-1 bg-slate-100 rounded-lg text-xs text-slate-700 border border-slate-200">
              <FileText className="w-3.5 h-3.5 text-slate-500" />
              <span className="font-medium">{message.attachment.name}</span>
            </div>
          )}

          {/* Deep Reasoning Button (if available) */}
          {message.reasoningSteps && message.reasoningSteps.length > 0 && (
            <div className="my-2">
              <button
                onClick={() => setActiveReasoningTrace(message.reasoningSteps)}
                className="inline-flex items-center gap-2 px-3 py-1.5 bg-purple-50 hover:bg-purple-100/80 border border-purple-200/80 text-purple-800 rounded-lg text-xs font-medium transition-colors group"
              >
                <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                <span>Verified Air-Gap Reasoning Trace ({message.reasoningSteps.length} Steps)</span>
                <ChevronRight className="w-3.5 h-3.5 text-purple-500 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          )}

          {/* Message Content Body */}
          <div className="prose-slate max-w-none text-slate-800">
            {renderFormattedContent(message.content)}
          </div>

          {/* Assistant Action Bar & Auditing Signature */}
          {!isUser && (
            <div className="mt-3 pt-2 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 text-slate-400 text-xs">
              <div className="flex items-center gap-1">
                <button
                  onClick={handleCopy}
                  className="p-1 hover:text-slate-700 rounded transition-colors"
                  title="Copy response"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={() => setFeedback('up')}
                  className={`p-1 rounded transition-colors ${
                    feedback === 'up' ? 'text-blue-600' : 'hover:text-slate-700'
                  }`}
                  title="Accurate telemetry"
                >
                  <ThumbsUp className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setFeedback('down')}
                  className={`p-1 rounded transition-colors ${
                    feedback === 'down' ? 'text-rose-600' : 'hover:text-slate-700'
                  }`}
                  title="Flag for audit"
                >
                  <ThumbsDown className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
                <span className="flex items-center gap-1">
                  <Lock className="w-3 h-3 text-emerald-600" />
                  SHA256: 0x9b4f..e7
                </span>
                {message.tokens && (
                  <span>
                    Tokens: {message.tokens.input + message.tokens.output}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessageItem;
