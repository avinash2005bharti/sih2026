import React from 'react';
import { FileText, Sparkles, ChevronRight } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import swarajLogo from '../../asset/swaraj.logo-removebg-preview.png';

const SUGGESTED_PROMPTS = [
  'Summarize key compliance points from the latest inspection report.',
  'Analyze hydraulic pressure variance in compressor line B.',
  'Identify potential safety hazards in our boiler maintenance SOP.',
  'Draft an executive briefing based on uploaded technical manuals.',
  'Generate Python validation script for telemetry logs.',
];

const ChatEmptyHero = ({ onSelectPrompt }) => {
  const { agents, switchAgent, activeAgentState } = useChat();

  const handleAgentSelect = (agent) => {
    switchAgent(agent);
    if (agent.defaultPrompt) {
      onSelectPrompt(agent.defaultPrompt);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center max-w-3xl mx-auto px-4 py-4 text-center animate-in fade-in duration-300 w-full">
      {/* Compact Welcome Strip */}
      <div className="flex flex-col items-center mb-4">
        <div className="relative mb-2">
          <img
            src={swarajLogo}
            alt="SWaRaj Logo"
            className="w-12 h-12 object-contain rounded-xl shadow-xs border border-slate-200/90 bg-white p-1"
          />
        </div>

        <h1 className="text-lg sm:text-xl font-extrabold tracking-tight text-slate-900 flex items-center gap-1.5">
          <span>SWaRaj</span>
        </h1>

        <p className="text-xs text-slate-500 font-medium max-w-md mt-0.5">
          Sovereign Workbench for Real-time Autonomous Judgment
        </p>
      </div>

      {/* Quick Analysis Prompts - Horizontal Scrollable Chip List */}
      <div className="w-full max-w-2xl mb-4">
        <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-center gap-1.5">
          <Sparkles className="w-3 h-3 text-blue-500" />
          <span>Quick Analysis Prompts</span>
        </div>
        <div className="flex items-center gap-2 overflow-x-auto pb-1.5 px-1 no-scrollbar scroll-smooth">
          {SUGGESTED_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => onSelectPrompt(prompt)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-blue-50/70 border border-slate-200 hover:border-blue-300 text-xs text-slate-700 hover:text-blue-800 rounded-full whitespace-nowrap shadow-2xs hover:shadow-xs transition-all flex-shrink-0 group"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 group-hover:scale-125 transition-transform" />
              <span>{prompt}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Specialized Agent Chips (Horizontal) */}
      {agents && agents.length > 0 && (
        <div className="w-full max-w-2xl">
          <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Active Specialized Agents
          </div>
          <div className="flex items-center justify-center gap-2 flex-wrap">
            {agents.slice(0, 4).map((agent) => {
              const isSelected = activeAgentState?.slug === agent.slug || activeAgentState?.name === agent.name;
              return (
                <button
                  key={agent._id}
                  onClick={() => handleAgentSelect(agent)}
                  className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs transition-all shadow-2xs border ${
                    isSelected
                      ? 'bg-blue-50 border-blue-300 text-blue-700 font-semibold'
                      : 'bg-white hover:bg-slate-50 border-slate-200 text-slate-700'
                  }`}
                >
                  <FileText className={`w-3.5 h-3.5 ${isSelected ? 'text-blue-600' : 'text-slate-400'}`} />
                  <span>{agent.name}</span>
                  {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatEmptyHero;
