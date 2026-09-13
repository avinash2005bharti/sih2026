import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  ShieldCheck,
  ChevronDown,
  Download,
  HelpCircle,
  Menu,
  CheckCircle2,
  Cpu,
  User,
  Settings,
  Users,
  LogOut,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useAuth } from '../../context/AuthContext';

const TopHeader = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const {
    agents,
    selectedAgent,
    setSelectedAgent,
    setIsStatusModalOpen,
    isSidebarOpen,
    setIsSidebarOpen,
  } = useChat();

  const [isAgentMenuOpen, setIsAgentMenuOpen] = useState(false);
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const agentMenuRef = useRef(null);
  const profileMenuRef = useRef(null);

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
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="border-b border-slate-200/90 bg-white/95 backdrop-blur-md sticky top-0 z-30 flex-shrink-0 shadow-2xs">
      {/* Primary Header Bar */}
      <div className="px-4 py-2.5 flex items-center justify-between gap-4">
        {/* Left Side: Mobile Hamburger, Assistant Info & Agent Selector */}
        <div className="flex items-center gap-3">
          {/* Mobile Drawer Trigger */}
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-1.5 text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100 lg:hidden transition-colors"
            aria-label="Toggle Navigation Menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* AI Assistant Title */}
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-slate-900 tracking-tight">
                AI Assistant
              </span>
              <span className="w-2 h-2 rounded-full bg-emerald-500 pulse-dot" />
              {isAdmin && (
                <span className="px-1.5 py-0.2 text-[10px] font-mono font-bold uppercase rounded bg-purple-50 text-purple-700 border border-purple-200">
                  ADMIN
                </span>
              )}
            </div>
            <div className="text-[11px] text-slate-500 hidden sm:block font-medium">
              Secure organizational industrial AI
            </div>
          </div>

          {/* Agent Selector Dropdown */}
          <div className="relative ml-2" ref={agentMenuRef}>
            <button
              onClick={() => setIsAgentMenuOpen(!isAgentMenuOpen)}
              className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-full text-xs font-semibold text-slate-800 shadow-2xs transition-colors"
            >
              <div className="p-0.5 bg-blue-100 text-blue-700 rounded-full">
                <Cpu className="w-3.5 h-3.5" />
              </div>
              <span className="truncate max-w-[140px] sm:max-w-[180px]">
                {selectedAgent?.name || 'General Assistant'}
              </span>
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
                        isSelected ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-slate-700'
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

        {/* Right Side: Sovereign Status Pill, Controls & User Avatar Menu */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Sovereign Mode Verified Pill Button */}
          <button
            onClick={() => setIsStatusModalOpen(true)}
            className="flex items-center gap-2 px-3 py-1 bg-emerald-50 hover:bg-emerald-100/70 border border-emerald-200 text-emerald-800 text-[11px] font-mono font-semibold rounded-full tracking-wider transition-colors shadow-2xs"
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

          {/* Authenticated User Avatar Dropdown */}
          <div className="relative border-l border-slate-200 pl-2 sm:pl-3" ref={profileMenuRef}>
            <button
              onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
              className="flex items-center gap-2 p-1 hover:bg-slate-100 rounded-full sm:rounded-lg transition-colors"
              title={`Logged in as ${userFullName}`}
            >
              <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold shadow-2xs ring-1 ring-blue-500/20">
                {userInitials}
              </div>
              <span className="text-xs font-semibold text-slate-800 hidden md:inline truncate max-w-[130px]">
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
