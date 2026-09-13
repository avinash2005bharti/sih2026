import React from 'react';
import { Shield, FileText, PlusSquare, FolderOpen, Sparkles } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { Link } from 'react-router-dom';

const SUGGESTED_PROMPTS = [
  'Summarize the key compliance points from the latest inspection report.',
  'Analyze hydraulic pressure variance in compressor line B.',
  'Identify potential safety hazards in our boiler maintenance SOP.',
  'Draft an executive briefing based on uploaded technical manuals.',
];

const ChatEmptyHero = ({ onSelectPrompt }) => {
  const { agents, setSelectedAgent } = useChat();

  const handleAgentSelect = (agent) => {
    setSelectedAgent(agent);
    if (agent.defaultPrompt) {
      onSelectPrompt(agent.defaultPrompt);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center max-w-3xl mx-auto px-4 py-8 text-center animate-in fade-in duration-300">
      {/* Brand Icon */}
      <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4 shadow-sm">
        <Shield className="w-7 h-7 fill-blue-100" />
      </div>

      {/* Heading */}
      <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 mb-1.5">
        Sovereign AI Workbench
      </h1>

      {/* Subtitle */}
      <p className="text-xs sm:text-sm text-slate-500 max-w-lg leading-relaxed mb-6">
        Air-gapped organizational intelligence. Attach technical specs, manuals, or telemetry logs below to begin analysis.
      </p>

      {/* Starter Prompts */}
      <div className="w-full max-w-2xl mb-6">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center justify-center gap-1.5">
          <Sparkles className="w-3 h-3 text-blue-500" />
          <span>Quick Analysis Prompts</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
          {SUGGESTED_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => onSelectPrompt(prompt)}
              className="p-3 bg-white hover:bg-slate-50 border border-slate-200/90 rounded-xl text-xs text-slate-700 hover:text-slate-900 shadow-2xs hover:border-slate-300 transition-all leading-snug group flex items-start gap-2"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0 group-hover:scale-125 transition-transform" />
              <span>{prompt}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Specialized Agents Grid (from backend) */}
      {agents && agents.length > 0 && (
        <div className="w-full max-w-2xl">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5">
            Active Specialized Agents
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-left">
            {agents.slice(0, 3).map((agent) => (
              <button
                key={agent._id}
                onClick={() => handleAgentSelect(agent)}
                className="p-3 bg-white hover:bg-slate-50 border border-slate-200/90 rounded-xl shadow-2xs text-left hover:border-slate-300 transition-all group"
              >
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-6 h-6 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
                    <FileText className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-xs font-semibold text-slate-900 truncate">
                    {agent.name}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 truncate">
                  {agent.description || 'Specialized agent'}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatEmptyHero;
