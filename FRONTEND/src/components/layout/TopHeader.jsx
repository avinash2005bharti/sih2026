import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  ChevronDown,
  CheckCircle2,
  Settings,
  Users,
  LogOut,
  MoreVertical,
  ShieldCheck,
  FileDown,
  HelpCircle,
  PanelLeft,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useAuth } from '../../context/AuthContext';

const TopHeader = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const {
    agents,
    selectedAgent,
    switchAgent,
    activeAgentState,
    setIsStatusModalOpen,
    isSidebarOpen,
    toggleSidebar,
  } = useChat();

  const [isAgentMenuOpen, setIsAgentMenuOpen] = useState(false);
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isActionsMenuOpen, setIsActionsMenuOpen] = useState(false);
  const agentMenuRef = useRef(null);
  const profileMenuRef = useRef(null);
  const actionsMenuRef = useRef(null);

  const isAdmin = user?.isAdmin || user?.role === 'admin';

  const userFirstName = user?.fullName?.firstName || '';
  const userLastName = user?.fullName?.lastName || '';
  const userFullName = userFirstName
    ? `${userFirstName} ${userLastName}`.trim()
    : user?.email || 'Operator';
  const userInitials = userFirstName
    ? `${userFirstName[0]}${userLastName ? userLastName[0] : ''}`.toUpperCase()
    : 'OP';

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (agentMenuRef.current && !agentMenuRef.current.contains(e.target)) {
        setIsAgentMenuOpen(false);
      }
      if (profileMenuRef.current && !profileMenuRef.current.contains(e.target)) {
        setIsProfileMenuOpen(false);
      }
      if (actionsMenuRef.current && !actionsMenuRef.current.contains(e.target)) {
        setIsActionsMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Compute status colors and labels for the ONE live status indicator
  const agentStatus = activeAgentState?.status || 'idle';
  const agentName = activeAgentState?.name || selectedAgent?.name || 'General Assistant';

  const statusConfig = {
    running: {
      color: 'bg-blue-500',
      ping: 'bg-blue-400',
      label: 'Processing',
      textColor: 'text-blue-700',
      bgColor: 'bg-blue-50',
    },
    error: {
      color: 'bg-rose-500',
      ping: 'bg-rose-400',
      label: 'Error',
      textColor: 'text-rose-700',
      bgColor: 'bg-rose-50',
    },
    idle: {
      color: 'bg-emerald-500',
      ping: 'bg-emerald-400',
      label: 'Ready',
      textColor: 'text-emerald-700',
      bgColor: 'bg-emerald-50',
    },
  }[agentStatus] || {
    color: 'bg-emerald-500',
    ping: 'bg-emerald-400',
    label: 'Ready',
    textColor: 'text-emerald-700',
    bgColor: 'bg-emerald-50',
  };

  return (
    <header className="border-b border-slate-200/90 bg-white/95 backdrop-blur-md sticky top-0 z-30 flex-shrink-0 shadow-2xs">
      {/* Primary Header Bar */}
      <div className="px-3.5 py-2 flex items-center justify-between gap-3">
        {/* Left Side: Mobile Hamburger, Title & Agent Selector */}
        <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
          {/* Sidebar Toggle — visible on all screens when sidebar is closed */}
          {!isSidebarOpen && (
            <button
              onClick={() => toggleSidebar(true)}
              className="p-1.5 text-slate-500 hover:text-slate-800 rounded-lg hover:bg-slate-100 transition-colors"
              aria-label="Open sidebar"
              title="Open sidebar"
            >
              <PanelLeft className="w-5 h-5" />
            </button>
          )}

          {/* Rebranded Header Title: SWaRaj */}
          <div className="flex flex-col justify-center">
            <div className="flex items-center gap-2">
              <span className="text-sm font-black text-slate-900 tracking-tight">
                SWaRaj
              </span>
            </div>
            <div className="text-[10px] text-slate-500 hidden md:block font-medium truncate max-w-xs">
              Sovereign Workbench for Real-time Autonomous Judgment
            </div>
          </div>

          {/* Real-time Agent Selector Dropdown with LIVE status indicator */}
          <div className="relative ml-1 sm:ml-2" ref={agentMenuRef}>
            <button
              onClick={() => setIsAgentMenuOpen(!isAgentMenuOpen)}
              className="flex items-center gap-2 px-2.5 py-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-full text-xs font-semibold text-slate-800 shadow-2xs transition-colors"
              title={`Active Agent: ${agentName} (${statusConfig.label})`}
            >
              {/* Subtle Live Indicator Pulsing Dot */}
              <span className="relative flex h-2 w-2">
                <span
                  className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${statusConfig.ping}`}
                />
                <span
                  className={`relative inline-flex rounded-full h-2 w-2 ${statusConfig.color}`}
                />
              </span>

              <span className="truncate max-w-[130px] sm:max-w-[180px]">
                {agentName}
              </span>
              <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded font-bold uppercase ${statusConfig.bgColor} ${statusConfig.textColor} hidden sm:inline`}>
                {statusConfig.label}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {/* Dropdown Menu */}
            {isAgentMenuOpen && (
              <div className="absolute left-0 mt-1.5 w-64 bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 z-50 animate-in fade-in zoom-in-95 duration-150">
                <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-100 flex items-center justify-between">
                  <span>Specialized Agents</span>
                  <span className="text-[9px] text-emerald-600 font-mono">Real-Time Sync</span>
                </div>
                {agents.map((agent) => {
                  const isSelected =
                    activeAgentState?.slug === agent.slug ||
                    selectedAgent?._id === agent._id ||
                    activeAgentState?.name === agent.name;
                  return (
                    <button
                      key={agent._id}
                      onClick={() => {
                        switchAgent(agent);
                        setIsAgentMenuOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-50 transition-colors ${
                        isSelected ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-slate-700'
                      }`}
                    >
                      <div>
                        <div className="font-medium flex items-center gap-1.5">
                          <span>{agent.name}</span>
                          {isSelected && (
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
                          )}
                        </div>
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

        {/* Right Side: Consolidated Options Overflow Menu & User Profile */}
        <div className="flex items-center gap-1.5 sm:gap-2">
          {/* Consolidated Actions & Security Menu */}
          <div className="relative" ref={actionsMenuRef}>
            <button
              onClick={() => setIsActionsMenuOpen(!isActionsMenuOpen)}
              className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
              title="System Controls & Security"
              aria-label="More options"
            >
              <MoreVertical className="w-4 h-4" />
            </button>

            {isActionsMenuOpen && (
              <div className="absolute right-0 mt-1.5 w-56 bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 z-50 animate-in fade-in zoom-in-95 duration-150 text-xs">
                <div className="px-3 py-1 text-[10px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                  System & Verification
                </div>
                <button
                  onClick={() => {
                    setIsActionsMenuOpen(false);
                    setIsStatusModalOpen(true);
                  }}
                  className="w-full text-left px-3 py-2 text-slate-700 hover:bg-slate-50 flex items-center gap-2.5 transition-colors"
                >
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <div>
                    <div className="font-medium">Air-Gap Verification</div>
                    <div className="text-[10px] text-slate-400">Cryptographic audit & status</div>
                  </div>
                </button>
                <button
                  onClick={() => {
                    setIsActionsMenuOpen(false);
                    window.print();
                  }}
                  className="w-full text-left px-3 py-2 text-slate-700 hover:bg-slate-50 flex items-center gap-2.5 transition-colors"
                >
                  <FileDown className="w-4 h-4 text-slate-500" />
                  <div>
                    <div className="font-medium">Export Conversation</div>
                    <div className="text-[10px] text-slate-400">PDF report / print audit</div>
                  </div>
                </button>
                <button
                  onClick={() => {
                    setIsActionsMenuOpen(false);
                    setIsStatusModalOpen(true);
                  }}
                  className="w-full text-left px-3 py-2 text-slate-700 hover:bg-slate-50 flex items-center gap-2.5 transition-colors"
                >
                  <HelpCircle className="w-4 h-4 text-slate-500" />
                  <div>
                    <div className="font-medium">Architecture Help</div>
                    <div className="text-[10px] text-slate-400">On-premise deployment guide</div>
                  </div>
                </button>
              </div>
            )}
          </div>

          {/* Authenticated User Avatar Dropdown */}
          <div className="relative border-l border-slate-200 pl-2 sm:pl-2.5" ref={profileMenuRef}>
            <button
              onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
              className="flex items-center gap-2 p-0.5 hover:bg-slate-100 rounded-full sm:rounded-lg transition-colors"
              title={`Logged in as ${userFullName}`}
            >
              <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold shadow-2xs ring-1 ring-blue-500/20">
                {userInitials}
              </div>
              <span className="text-xs font-semibold text-slate-800 hidden md:inline truncate max-w-[120px]">
                {userFullName}
              </span>
              <ChevronDown className="w-3 h-3 text-slate-400 hidden sm:block" />
            </button>

            {/* Profile Dropdown Menu */}
            {isProfileMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 z-50 animate-in fade-in zoom-in-95 duration-150">
                <div className="px-3.5 py-2 border-b border-slate-100">
                  <div className="font-semibold text-xs text-slate-900 truncate">
                    {userFullName}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono truncate">
                    {user?.email}
                  </div>
                  <div className="mt-1.5 flex items-center gap-1.5">
                    <span className="px-1.5 py-0.5 text-[9px] font-mono font-semibold uppercase rounded bg-slate-100 text-slate-700">
                      {user?.role || 'operator'}
                    </span>
                    {isAdmin && (
                      <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold uppercase rounded bg-purple-100 text-purple-700">
                        Admin Clearance
                      </span>
                    )}
                  </div>
                </div>

                <div className="py-1 text-xs">
                  {isAdmin && (
                    <button
                      onClick={() => {
                        setIsProfileMenuOpen(false);
                        navigate('/settings?tab=users');
                      }}
                      className="w-full text-left px-3.5 py-2 text-slate-700 hover:bg-slate-50 flex items-center gap-2.5 transition-colors"
                    >
                      <Users className="w-4 h-4 text-purple-600" />
                      <span>User Management</span>
                    </button>
                  )}

                  <Link
                    to="/settings"
                    onClick={() => setIsProfileMenuOpen(false)}
                    className="w-full text-left px-3.5 py-2 text-slate-700 hover:bg-slate-50 flex items-center gap-2.5 transition-colors"
                  >
                    <Settings className="w-4 h-4 text-slate-500" />
                    <span>Settings & Profile</span>
                  </Link>

                  <button
                    onClick={() => {
                      setIsProfileMenuOpen(false);
                      logout();
                    }}
                    className="w-full text-left px-3.5 py-2 text-rose-600 hover:bg-rose-50 flex items-center gap-2.5 transition-colors border-t border-slate-100 mt-1"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default TopHeader;
