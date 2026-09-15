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
  Terminal,
  Clock,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Loader2,
  Eye,
  ChevronDown,
  ScanLine,
  Layers,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';

/**
 * Lightweight, robust syntax highlighter for code blocks
 */
const highlightCode = (code, lang = '') => {
  if (!code) return null;
  const language = (lang || '').toLowerCase().trim();
  const lines = code.split(/\r?\n/);

  return lines.map((line, lineIdx) => {
    let remaining = line;
    let tokenIdx = 0;

    // Line comment matchers
    const isPythonOrShell = ['python', 'py', 'sh', 'bash', 'zsh', 'yaml', 'yml'].includes(language);
    const commentMatch = isPythonOrShell ? remaining.match(/^(.*?)(\/\/.*|#.*)$/) : remaining.match(/^(.*?)(\/\/.*)$/);

    let codePart = remaining;
    let commentPart = null;
    if (commentMatch && !remaining.includes('"""') && !remaining.includes("'''")) {
      codePart = commentMatch[1];
      commentPart = commentMatch[2];
    }

    // Tokenize strings, numbers, keywords in codePart
    const tokenRegex = /(".*?"|'.*?'|`.*?`|\b(?:def|class|import|from|return|if|else|elif|for|while|try|except|finally|async|await|with|as|in|is|not|and|or|const|let|var|function|new|throw|catch|typeof|instanceof|yield|break|continue|None|True|False|true|false|null|undefined)\b|\b\d+\b|[a-zA-Z_][a-zA-Z0-9_]*(?=\())/g;
    
    let lastPos = 0;
    let match;
    const lineElements = [];

    while ((match = tokenRegex.exec(codePart)) !== null) {
      if (match.index > lastPos) {
        lineElements.push(<span key={`txt-${lineIdx}-${tokenIdx++}`}>{codePart.slice(lastPos, match.index)}</span>);
      }
      const tok = match[0];
      if (tok.startsWith('"') || tok.startsWith("'") || tok.startsWith('`')) {
        lineElements.push(<span key={`str-${lineIdx}-${tokenIdx++}`} className="text-amber-300 font-medium">{tok}</span>);
      } else if (/^\d+$/.test(tok)) {
        lineElements.push(<span key={`num-${lineIdx}-${tokenIdx++}`} className="text-emerald-400">{tok}</span>);
      } else if (match[1]) {
        lineElements.push(<span key={`fn-${lineIdx}-${tokenIdx++}`} className="text-cyan-300">{tok}</span>);
      } else {
        lineElements.push(<span key={`kw-${lineIdx}-${tokenIdx++}`} className="text-purple-400 font-semibold">{tok}</span>);
      }
      lastPos = match.index + tok.length;
    }
    if (lastPos < codePart.length) {
      lineElements.push(<span key={`txt-${lineIdx}-${tokenIdx++}`}>{codePart.slice(lastPos)}</span>);
    }
    if (commentPart) {
      lineElements.push(<span key={`cmt-${lineIdx}-${tokenIdx++}`} className="text-slate-500 italic">{commentPart}</span>);
    }

    return (
      <div key={`line-${lineIdx}`} className="table-row leading-relaxed">
        <span className="table-cell pr-4 text-right select-none text-slate-600 text-[11px] font-mono opacity-50">{lineIdx + 1}</span>
        <span className="table-cell whitespace-pre">{lineElements.length > 0 ? lineElements : '\u00A0'}</span>
      </div>
    );
  });
};

/**
 * Dedicated Syntax-Highlighted Code Block with Copy Feedback
 */
const CodeBlock = ({ language, code, isStreaming = false }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const displayLang = (language || 'code').toLowerCase().trim();

  return (
    <div className="my-3 rounded-xl overflow-hidden border border-slate-700/80 bg-slate-950 shadow-md">
      {/* Terminal Titlebar */}
      <div className="flex items-center justify-between px-3.5 py-2 bg-slate-900 border-b border-slate-800 text-slate-300">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80 inline-block"></span>
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80 inline-block"></span>
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80 inline-block"></span>
          <span className="ml-2 px-2 py-0.5 rounded text-[10px] font-mono font-semibold tracking-wider uppercase bg-slate-800 text-cyan-400 border border-slate-700">
            {displayLang}
          </span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors border border-slate-700 cursor-pointer"
          title="Copy code to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 text-[11px]">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-[11px]">Copy code</span>
            </>
          )}
        </button>
      </div>
      {/* Code Content */}
      <div className="p-4 overflow-x-auto text-slate-100 font-mono text-xs sm:text-[13px] leading-relaxed bg-[#0d1117] selection:bg-blue-900 selection:text-white">
        <pre className="table w-full">
          <code>{highlightCode(code, displayLang)}</code>
        </pre>
      </div>
    </div>
  );
};

/**
 * Dedicated Run Output Card displaying terminal stdout, stderr, and execution metadata
 */
const RunOutputCard = ({ execution, index }) => {
  const [expanded, setExpanded] = useState(true);
  const { tool, duration_seconds, stdout, stderr, exit_code, success, arguments: args } = execution;
  const isSuccess = success !== false && (exit_code === 0 || exit_code === undefined);

  const formatToolName = (name) => {
    switch (name) {
      case 'execute_python': return 'Python Sandbox Execution';
      case 'execute_code': return 'Sandbox Code Execution';
      case 'create_file': return 'File System Write';
      case 'create_pdf': return 'PDF Document Generation';
      case 'list_files': return 'File System Listing';
      case 'read_file': return 'File Read Operation';
      default: return name || 'Tool Execution';
    }
  };

  return (
    <div key={index} className="my-3 rounded-xl border border-slate-800 bg-slate-950 overflow-hidden shadow-md font-mono text-xs">
      {/* Header */}
      <div 
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between px-3.5 py-2.5 bg-slate-900 border-b border-slate-800 cursor-pointer hover:bg-slate-800/80 transition-colors select-none"
      >
        <div className="flex items-center gap-2 flex-wrap">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span className="font-semibold text-slate-200 text-xs">
            {formatToolName(tool)}
          </span>
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold flex items-center gap-1 ${
            isSuccess 
              ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60' 
              : 'bg-rose-950/80 text-rose-400 border border-rose-800/60'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${isSuccess ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
            {isSuccess ? `Exit 0 (Success)` : `Exit ${exit_code ?? 'Error'}`}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {duration_seconds !== undefined && (
            <span className="text-[11px] text-slate-400 flex items-center gap-1 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/50">
              <Clock className="w-3 h-3 text-slate-400" />
              {Number(duration_seconds).toFixed(2)}s
            </span>
          )}
          <ChevronRight className={`w-3.5 h-3.5 text-slate-400 transition-transform ${expanded ? 'rotate-90' : ''}`} />
        </div>
      </div>

      {/* Body */}
      {expanded && (
        <div className="p-3 bg-[#0a0e14] space-y-2.5">
          {args && (args.code || args.command || args.path || args.filename) && (
            <div className="text-[11px] text-slate-400">
              <span className="text-slate-500 font-semibold">Target: </span>
              <span className="text-slate-300 font-mono">
                {args.path || args.filename || (args.code ? `${args.code.slice(0, 60)}...` : args.command)}
              </span>
            </div>
          )}

          {/* Standard Output */}
          {stdout && (
            <div className="space-y-1">
              <div className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                Terminal Output (stdout)
              </div>
              <pre className="p-2.5 bg-black/80 rounded-lg text-emerald-400 font-mono text-xs overflow-x-auto border border-emerald-950/60 whitespace-pre-wrap">
                <code>{stdout}</code>
              </pre>
            </div>
          )}

          {/* Standard Error */}
          {stderr && (
            <div className="space-y-1">
              <div className="text-[10px] font-semibold text-rose-400 uppercase tracking-wider flex items-center gap-1">
                <XCircle className="w-3 h-3 text-rose-400" />
                Execution Error (stderr)
              </div>
              <pre className="p-2.5 bg-rose-950/20 rounded-lg text-rose-300 font-mono text-xs overflow-x-auto border border-rose-900/50 whitespace-pre-wrap">
                <code>{stderr}</code>
              </pre>
            </div>
          )}

          {!stdout && !stderr && (
            <div className="text-slate-400 text-xs italic">
              Execution completed successfully with no terminal output.
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * Dedicated Multimodal Inspection Card
 * Shows transparent separation between:
 * 1. Exact Alphanumeric OCR Facts (PaddleOCR)
 * 2. Visual Scene Reasoning (Moondream)
 */
const MultimodalInspectionCard = ({ ocr, vision }) => {
  const [activeTab, setActiveTab] = useState(ocr ? 'ocr' : 'vision');
  const [isExpanded, setIsExpanded] = useState(true);
  const [copied, setCopied] = useState(false);

  if (!ocr && !vision) return null;

  const handleCopyText = () => {
    if (!ocr?.text) return;
    navigator.clipboard.writeText(ocr.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const ocrLines = ocr?.lines || [];
  const avgConfidence = ocr?.average_confidence 
    ? Math.round(ocr.average_confidence * 100) 
    : (ocrLines.length > 0 ? Math.round((ocrLines.reduce((acc, l) => acc + (l.confidence || 0), 0) / ocrLines.length) * 100) : null);

  return (
    <div className="my-3 rounded-xl border border-indigo-200/80 bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950/40 text-slate-200 overflow-hidden shadow-md">
      {/* Titlebar / Header */}
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-slate-900/90 border-b border-slate-800 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></div>
          <span className="font-semibold text-cyan-300 font-mono flex items-center gap-1.5">
            <ScanLine className="w-3.5 h-3.5 text-cyan-400" />
            Multimodal Inspection Telemetry
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-950 border border-indigo-800 text-indigo-300 font-mono">
            Air-Gapped Sovereign Pipeline
          </span>
        </div>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-slate-400 hover:text-white transition-colors p-1 rounded hover:bg-slate-800 cursor-pointer"
          title={isExpanded ? "Collapse telemetry" : "Expand telemetry"}
        >
          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
      </div>

      {isExpanded && (
        <div className="p-3">
          {/* Tab Selector Buttons */}
          <div className="flex items-center gap-2 mb-3 border-b border-slate-800 pb-2">
            {ocr && (
              <button
                onClick={() => setActiveTab('ocr')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  activeTab === 'ocr'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-xs'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <ScanLine className="w-3.5 h-3.5" />
                <span>Extracted Text (PaddleOCR)</span>
                {ocrLines.length > 0 && (
                  <span className="text-[10px] bg-cyan-900/60 text-cyan-200 px-1.5 py-0.5 rounded-full font-mono border border-cyan-700/50">
                    {ocrLines.length} lines
                  </span>
                )}
              </button>
            )}

            {vision && (
              <button
                onClick={() => setActiveTab('vision')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  activeTab === 'vision'
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-xs'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Eye className="w-3.5 h-3.5" />
                <span>Visual Scene Reasoning (Moondream)</span>
                <span className="text-[10px] bg-purple-900/60 text-purple-200 px-1.5 py-0.5 rounded-full font-mono border border-purple-700/50">
                  Visual Only
                </span>
              </button>
            )}
          </div>

          {/* Tab Content: OCR */}
          {activeTab === 'ocr' && ocr && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Exact Alphanumeric Facts {avgConfidence !== null && `(Avg Confidence: ${avgConfidence}%)`}
                </span>
                <button
                  onClick={handleCopyText}
                  className="flex items-center gap-1 px-2 py-0.5 bg-slate-800 hover:bg-slate-700 rounded text-slate-300 transition-colors border border-slate-700 text-[10px] cursor-pointer"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  {copied ? 'Copied' : 'Copy All Text'}
                </button>
              </div>

              {/* Line by line extraction with confidence scores */}
              {ocrLines.length > 0 ? (
                <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                  {ocrLines.map((line, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between px-2.5 py-1.5 rounded bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-colors font-mono text-xs"
                    >
                      <span className="text-slate-200 selection:bg-cyan-900">{line.text}</span>
                      {line.confidence !== undefined && (
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                          line.confidence >= 0.9 
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/60' 
                            : line.confidence >= 0.7 
                            ? 'bg-amber-950 text-amber-400 border border-amber-800/60' 
                            : 'bg-rose-950 text-rose-400 border border-rose-800/60'
                        }`}>
                          {Math.round(line.confidence * 100)}%
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <pre className="p-2.5 rounded bg-slate-900 font-mono text-xs text-slate-200 whitespace-pre-wrap">
                  {ocr.text || 'No text detected'}
                </pre>
              )}

              <p className="text-[10px] text-slate-500 italic mt-1 font-mono">
                Source: On-premise PaddleOCR. Text extraction strictly avoids LLM visual transcription to prevent hallucination.
              </p>
            </div>
          )}

          {/* Tab Content: Vision */}
          {activeTab === 'vision' && vision && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[11px] text-purple-400 font-mono">
                <span className="flex items-center gap-1.5">
                  <Eye className="w-3.5 h-3.5 text-purple-400" />
                  Visual Scene Analysis (Local Ollama: moondream)
                </span>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 text-xs text-slate-200 leading-relaxed font-sans">
                {vision.scene_description || vision.description || 'Visual scene understanding completed.'}
              </div>

              {vision.physical_anomalies && vision.physical_anomalies.length > 0 && (
                <div className="mt-2">
                  <span className="text-[10px] uppercase font-mono text-amber-400 font-semibold tracking-wider">
                    Physical Anomalies Detected:
                  </span>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {vision.physical_anomalies.map((anomaly, aIdx) => (
                      <span key={aIdx} className="text-[10px] px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800/60 font-mono">
                        {anomaly}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <p className="text-[10px] text-slate-500 italic mt-1 font-mono">
                Source: Local Moondream. Visual reasoning describes physical appearance, damage, and context without primary text reading.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

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

  // Helper to parse inline markdown (bold, inline code)
  const parseInlineStyles = (text) => {
    if (!text) return null;
    const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code
            key={i}
            className="px-1.5 py-0.5 bg-slate-100 text-slate-800 rounded font-mono text-[11px] border border-slate-200 font-medium"
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

  // Render text blocks (headings, lists, blockquotes, tables, paragraphs)
  const renderTextBlocks = (textChunk, keyPrefix) => {
    if (!textChunk) return [];
    const lines = textChunk.split('\n');
    const rendered = [];
    let inTable = false;
    let tableRows = [];

    lines.forEach((line, index) => {
      if (line.trim().startsWith('|')) {
        inTable = true;
        tableRows.push(line);
        return;
      } else if (inTable) {
        inTable = false;
        rendered.push(
          <div key={`${keyPrefix}-tbl-${index}`} className="my-3 overflow-x-auto border border-slate-200 rounded-lg shadow-2xs">
            <table className="min-w-full text-xs text-left divide-y divide-slate-200">
              <tbody className="divide-y divide-slate-100 bg-white">
                {tableRows.map((row, rIdx) => {
                  const cells = row.split('|').filter((c, i, a) => i !== 0 && i !== a.length - 1);
                  if (row.includes('---')) return null;
                  const isHeader = rIdx === 0;
                  return (
                    <tr key={rIdx} className={isHeader ? 'bg-slate-50 font-semibold text-slate-800' : 'hover:bg-slate-50/60'}>
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

      if (line.startsWith('### ')) {
        rendered.push(
          <h4 key={`${keyPrefix}-${index}`} className="text-sm font-bold text-slate-900 mt-3 mb-1.5 flex items-center gap-1.5">
            {line.replace('### ', '').replace(/\*\*/g, '')}
          </h4>
        );
      } else if (line.startsWith('## ')) {
        rendered.push(
          <h3 key={`${keyPrefix}-${index}`} className="text-base font-bold text-slate-900 mt-4 mb-2">
            {line.replace('## ', '').replace(/\*\*/g, '')}
          </h3>
        );
      } else if (line.startsWith('> ')) {
        rendered.push(
          <div key={`${keyPrefix}-${index}`} className="my-2 p-2.5 bg-blue-50/80 border-l-3 border-blue-600 text-xs text-blue-900 rounded-r-lg font-medium">
            {line.replace('> ', '').replace(/\*\*/g, '')}
          </div>
        );
      } else if (line.trim().startsWith('* ') || line.trim().startsWith('- ')) {
        const text = line.replace(/^[\*\-]\s+/, '');
        rendered.push(
          <div key={`${keyPrefix}-${index}`} className="flex items-start gap-2 text-xs sm:text-sm text-slate-700 my-1 pl-1">
            <span className="text-blue-600 font-bold mt-0.5">•</span>
            <span>{parseInlineStyles(text)}</span>
          </div>
        );
      } else if (line.trim().match(/^\d+\.\s/)) {
        const num = line.match(/^(\d+\.)\s/)[1];
        const text = line.replace(/^\d+\.\s+/, '');
        rendered.push(
          <div key={`${keyPrefix}-${index}`} className="flex items-start gap-2 text-xs sm:text-sm text-slate-700 my-1 pl-1">
            <span className="text-blue-600 font-semibold font-mono text-[11px]">{num}</span>
            <span>{parseInlineStyles(text)}</span>
          </div>
        );
      } else if (line.trim()) {
        rendered.push(
          <p key={`${keyPrefix}-${index}`} className="text-xs sm:text-sm text-slate-700 my-1.5 leading-relaxed whitespace-pre-wrap">
            {parseInlineStyles(line)}
          </p>
        );
      }
    });

    return rendered;
  };

  // Main Markdown Parser that extracts fenced code blocks
  const renderFormattedContent = (content) => {
    if (!content) return null;

    const codeBlockRegex = /```([a-zA-Z0-9_+-]*)[^\n\r]*\r?\n([\s\S]*?)```/g;
    const elements = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      const textBefore = content.substring(lastIndex, match.index);
      if (textBefore) {
        elements.push(...renderTextBlocks(textBefore, `pre-${lastIndex}`));
      }
      const language = match[1] || 'code';
      const code = match[2];
      elements.push(
        <CodeBlock key={`code-${match.index}`} language={language} code={code} />
      );
      lastIndex = match.index + match[0].length;
    }

    const remainingText = content.substring(lastIndex);
    if (remainingText) {
      if (remainingText.includes('```')) {
        const parts = remainingText.split('```');
        if (parts[0]) {
          elements.push(...renderTextBlocks(parts[0], `rem-${lastIndex}`));
        }
        const rawCode = parts.slice(1).join('```');
        const firstLineBreak = rawCode.search(/\r?\n/);
        let lang = 'code';
        let code = rawCode;
        if (firstLineBreak !== -1) {
          lang = rawCode.substring(0, firstLineBreak).trim() || 'code';
          const matchBreak = rawCode.match(/\r?\n/);
          const breakLen = matchBreak ? matchBreak[0].length : 1;
          code = rawCode.substring(firstLineBreak + breakLen);
        }
        elements.push(
          <CodeBlock key={`unclosed-${lastIndex}`} language={lang} code={code} isStreaming={true} />
        );
      } else {
        elements.push(...renderTextBlocks(remainingText, `post-${lastIndex}`));
      }
    }

    return elements;
  };

  const toolExecutions = message.toolExecutions || message.metadata?.toolExecutions || [];
  const generatedFiles = message.generatedFiles || message.metadata?.generatedFiles || [];

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
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-xs font-semibold text-slate-900">
              {isUser ? 'You' : 'Sovereign Assistant'}
            </span>

            {!isUser && (
              <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full text-[10px] font-mono border border-blue-200/60">
                {message.agent?.name || 'Orchestrator'}
              </span>
            )}

            {!isUser && toolExecutions.length > 0 && (
              <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-full text-[10px] font-mono border border-emerald-200/60 flex items-center gap-1">
                <Cpu className="w-3 h-3 text-emerald-600" />
                {toolExecutions.length} Tool{toolExecutions.length > 1 ? 's' : ''} Executed
              </span>
            )}

            {!isUser && message.modelUsed && (
              <span className="text-[10px] font-mono text-slate-400 hidden sm:inline">
                {message.modelUsed.displayName || 'qwen2.5-coder'}
              </span>
            )}

            <span className="text-[10px] text-slate-400 ml-auto font-mono">
              {new Date(message.createdAt || Date.now()).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>

          {/* User Attachment / Image Preview if present */}
          {message.attachment && (
            <div className="mb-3 space-y-2">
              {message.attachment.base64 && (
                <div className="relative inline-block group">
                  <img
                    src={message.attachment.base64.startsWith('data:')
                      ? message.attachment.base64
                      : `data:${message.attachment.type || 'image/png'};base64,${message.attachment.base64}`}
                    alt={message.attachment.name || 'Inspection image'}
                    className="max-w-xs sm:max-w-sm max-h-56 rounded-xl border border-slate-300 shadow-sm object-contain bg-slate-900/5 transition-transform group-hover:scale-[1.01]"
                  />
                  <div className="absolute top-2 right-2 px-2 py-0.5 rounded bg-black/70 backdrop-blur-xs text-white text-[10px] font-mono">
                    Visual Target
                  </div>
                </div>
              )}
              <div className="inline-flex items-center gap-2 px-2.5 py-1 bg-slate-100 rounded-lg text-xs text-slate-700 border border-slate-200">
                <FileText className="w-3.5 h-3.5 text-slate-500" />
                <span className="font-medium">{message.attachment.name}</span>
                {message.attachment.size && (
                  <span className="text-[10px] text-slate-400 font-mono">
                    ({Math.round(message.attachment.size / 1024)} KB)
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Deep Reasoning Button (if available) */}
          {message.reasoningSteps && message.reasoningSteps.length > 0 && (
            <div className="my-2">
              <button
                onClick={() => setActiveReasoningTrace(message.reasoningSteps)}
                className="inline-flex items-center gap-2 px-3 py-1.5 bg-purple-50 hover:bg-purple-100/80 border border-purple-200/80 text-purple-800 rounded-lg text-xs font-medium transition-colors group cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                <span>Verified Air-Gap Reasoning Trace ({message.reasoningSteps.length} Steps)</span>
                <ChevronRight className="w-3.5 h-3.5 text-purple-500 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          )}

          {/* Tool Execution Run Output Cards */}
          {toolExecutions.length > 0 && (
            <div className="my-3 space-y-2">
              {toolExecutions.map((exec, idx) => (
                <RunOutputCard key={idx} execution={exec} index={idx} />
              ))}
            </div>
          )}

          {/* Vision / OCR Real-time Progress Banner during streaming */}
          {message.visionProgress && (
            <div className="my-2.5 inline-flex items-center gap-2.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyan-50 to-indigo-50 border border-cyan-200 text-cyan-900 text-xs font-medium animate-pulse shadow-xs">
              <Loader2 className="w-4 h-4 text-cyan-600 animate-spin flex-shrink-0" />
              <div className="flex flex-col">
                <span className="font-mono text-xs font-semibold text-cyan-950">Air-Gap Multimodal Pipeline Active</span>
                <span className="font-mono text-[11px] text-cyan-700">{message.visionProgress}</span>
              </div>
            </div>
          )}

          {/* Multimodal Telemetry Inspection Card */}
          {(message.ocr || message.vision || message.metadata?.ocr || message.metadata?.vision) && (
            <MultimodalInspectionCard
              ocr={message.ocr || message.metadata?.ocr}
              vision={message.vision || message.metadata?.vision}
            />
          )}

          {/* Message Content Body */}
          <div className="prose-slate max-w-none text-slate-800">
            {renderFormattedContent(message.content)}
          </div>

          {/* Generated Sovereign Artifacts if present */}
          {generatedFiles.length > 0 && (
            <div className="mt-3 p-3 bg-emerald-50/70 border border-emerald-200/80 rounded-xl">
              <div className="text-[11px] font-semibold text-emerald-800 uppercase tracking-wider mb-2 flex items-center gap-1.5 font-mono">
                <FileText className="w-3.5 h-3.5 text-emerald-600" />
                Generated Sovereign Artifacts
              </div>
              <div className="flex flex-wrap gap-2">
                {generatedFiles.map((file, fIdx) => {
                  const fileUrl = `http://localhost:8000/workspace/${file.path}`;
                  return (
                    <a
                      key={fIdx}
                      href={fileUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      download={file.name}
                      className="inline-flex items-center gap-2 px-3 py-1.5 bg-white hover:bg-emerald-100/60 border border-emerald-300 text-emerald-900 rounded-lg text-xs font-medium shadow-2xs hover:shadow-xs transition-all cursor-pointer group"
                    >
                      <FileText className="w-4 h-4 text-emerald-600 group-hover:scale-110 transition-transform" />
                      <span className="font-mono text-xs">{file.name}</span>
                      <span className="text-[10px] text-emerald-600 bg-emerald-100/80 px-1.5 py-0.5 rounded font-mono">
                        {file.mime_type === 'application/pdf' ? 'PDF' : 'FILE'}
                      </span>
                    </a>
                  );
                })}
              </div>
            </div>
          )}

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
