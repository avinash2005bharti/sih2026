import React, { useState, useRef, useEffect } from 'react';
import {
  Shield,
  ShieldCheck,
  ChevronDown,
  Download,
  HelpCircle,
  Menu,
  CheckCircle2,
  Lock,
  Cpu,
  Server,
  Radio,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useAuth } from '../../context/AuthContext';

const TopHeader = () => {
  const { user } = useAuth();
  const {
    agents,
    selectedAgent,
    setSelectedAgent,
    setIsStatusModalOpen,
    isSidebarOpen,
    setIsSidebarOpen,
  } = useChat();

  const [isAgentMenuOpen, setIsAgentMenuOpen] = useState(false);
  const agentMenuRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (agentMenuRef.current && !agentMenuRef.current.contains(e.target)) {
        setIsAgentMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-30 flex-shrink-0">
      {/* Primary Header Bar */}
      <div className="px-4 py-2.5 flex items-center justify-between gap-4">
        {/* Left Side: Mobile Hamburger & Assistant Info */}
        <div className="flex items-center gap-3">
          {/* Mobile Drawer Trigger */}
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-1.5 text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100 lg:hidden"
            aria-label="Toggle Navigation Menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* AI Assistant Title */}
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-slate-900">
                AI Assistant
              </span>
              <span className="w-2 h-2 rounded-full bg-emerald-500 pulse-dot" />
            </div>
            <div className="text-[11px] text-slate-500 hidden sm:block">
              Secure organizational industrial AI
            </div>
          </div>

          {/* Agent Selector Dropdown */}
          <div className="relative ml-2" ref={agentMenuRef}>
            <button
              onClick={() => setIsAgentMenuOpen(!isAgentMenuOpen)}
              className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-full text-xs font-medium text-slate-700 shadow-2xs transition-colors"
            >
              <div className="p-0.5 bg-blue-100 text-blue-700 rounded-full">
                <Cpu className="w-3.5 h-3.5" />
              </div>
              <span>{selectedAgent?.name || 'General Assistant'}</span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {/* Dropdown Menu */}
            {isAgentMenuOpen && (
              <div className="absolute left-0 mt-1.5 w-64 bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 z-50 animate-in fade-in zoom-in-95 duration-150">
                <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-100">
                  Select Specialized Agent
                </div>
                {agents.map((agent) => {
                  const isSelected = selectedAgent?._id === agent._id;
                  return (
                    <button
                      key={agent._id}
                      onClick={() => {
                        setSelectedAgent(agent);
                        setIsAgentMenuOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-50 transition-colors ${
                        isSelected ? 'bg-blue-50/70 text-blue-700 font-semibold' : 'text-slate-700'
                      }`}
                    >
                      <div>
                        <div className="font-medium">{agent.name}</div>
                        {agent.description && (
                          <div className="text-[10px] text-slate-400 truncate max-w-[190px]">
                            {agent.description}
                          </div>
                        )}
                      </div>
                      {isSelected && <CheckCircle2 className="w-4 h-4 text-blue-600 flex-shrink-0" />}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Sovereign Status Pill & Controls */}
        <div className="flex items-center gap-2">
          {/* Sovereign Mode Verified Pill Button */}
          <button
            onClick={() => setIsStatusModalOpen(true)}
            className="flex items-center gap-2 px-3 py-1 bg-emerald-50 hover:bg-emerald-100/80 border border-emerald-200 text-emerald-800 text-[11px] font-mono font-semibold rounded-full tracking-wider transition-colors shadow-2xs"
            title="View Sovereign AI Air-Gap & Cryptographic Verification"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500 pulse-dot" />
            <span className="hidden md:inline">SOVEREIGN MODE VERIFIED</span>
            <span className="md:hidden">SOVEREIGN</span>
          </button>

          {/* Quick Header Actions */}
          <div className="flex items-center border-l border-slate-200 pl-2 gap-1 text-slate-500">
            <button
              onClick={() => setIsStatusModalOpen(true)}
              className="p-1.5 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
              title="Security & Isolation Status"
            >
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
            </button>
            <button
              onClick={() => window.print()}
              className="p-1.5 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors hidden sm:block"
              title="Export Current Conversation"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsStatusModalOpen(true)}
              className="p-1.5 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
              title="Air-Gap Architecture Help"
            >
              <HelpCircle className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Air-Gap Telemetry Sub-Banner (Exact match from Desktop screenshot) */}
      <div className="px-4 py-1.5 bg-[#f1f5f9]/70 border-t border-slate-200/80 flex flex-wrap items-center justify-between text-[11px] font-mono text-slate-600 gap-2">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-slate-800 font-semibold tracking-wide">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>AIR-GAP SHIELD ACTIVE</span>
          </div>
          <span className="text-slate-300 hidden sm:inline">|</span>
          <span className="text-slate-500 hidden md:inline">
            100% On-Premise Execution • 0 External API Calls • Zero Data Egress Protocol
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 bg-white border border-slate-200 rounded text-[10px] text-slate-700 font-semibold shadow-2xs">
            NODE: MIL-NODE-04-TX
          </span>
          <span className="px-2 py-0.5 bg-blue-50 border border-blue-200 rounded text-[10px] text-blue-700 font-semibold flex items-center gap-1">
            <Lock className="w-2.5 h-2.5" />
            FIPS 140-3 L4
          </span>
        </div>
      </div>
    </header>
  );
};

export default TopHeader;
