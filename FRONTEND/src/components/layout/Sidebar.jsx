import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  Shield,
  Plus,
  MessageSquare,
  Bot,
  FileText,
  Database,
  ShieldCheck,
  Settings,
  History,
  Activity,
  Trash2,
  Lock,
  Cpu,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useAuth } from '../../context/AuthContext';

const PRIMARY_NAV = [
  { name: 'Chat', path: '/chat', icon: MessageSquare },
  { name: 'Agents', path: '/agents', icon: Bot },
  { name: 'Documents', path: '/documents', icon: FileText },
  { name: 'Knowledge Base', path: '/knowledge', icon: Database },
  { name: 'Reports & Audits', path: '/reports', icon: ShieldCheck },
];

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const {
    chats,
    activeChatId,
    selectChat,
    createNewChat,
    deleteChat,
    isSidebarOpen,
    setIsSidebarOpen,
  } = useChat();

  const handleNewChat = () => {
    createNewChat();
    navigate('/chat');
    setIsSidebarOpen(false);
  };

  const handleSelectChat = (chatId) => {
    selectChat(chatId);
    navigate('/chat');
    setIsSidebarOpen(false);
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Main Sidebar */}
      <aside
        className={`fixed lg:static top-0 left-0 bottom-0 z-50 w-[265px] bg-[#f8fafc] border-r border-slate-200 flex flex-col justify-between transition-transform duration-200 ease-in-out select-none ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Top Header & Brand */}
        <div>
          <div className="p-4 pb-3 flex items-center justify-between border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#0a1128] flex items-center justify-center text-blue-400 shadow-sm">
                <Shield className="w-5 h-5 text-blue-400 fill-blue-500/20" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-slate-900 text-sm tracking-tight">
                    Sovereign
                  </span>
                  <span className="text-[10px] px-1 py-0.2 bg-slate-200 text-slate-600 font-mono font-bold rounded">
                    ENT
                  </span>
                </div>
                <div className="text-[11px] text-slate-500 font-medium -mt-0.5">
                  Workbench AI
                </div>
              </div>
            </div>
          </div>

          {/* New Chat Button */}
          <div className="p-3">
            <button
              onClick={handleNewChat}
              className="w-full flex items-center justify-between px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200/90 rounded-lg text-xs font-semibold text-slate-800 shadow-xs hover:border-slate-300 transition-all group"
            >
              <div className="flex items-center gap-2">
                <Plus className="w-4 h-4 text-blue-600 group-hover:scale-110 transition-transform" />
                <span>New Chat</span>
              </div>
              <span className="text-[10px] font-mono text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200/60">
                ⌘K
              </span>
            </button>
          </div>

          {/* Primary Modules */}
          <div className="px-3 py-1">
            <div className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase px-2 mb-1.5">
              Primary Modules
            </div>
            <nav className="space-y-0.5">
              {PRIMARY_NAV.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname.startsWith(item.path);

                return (
                  <NavLink
                    key={item.name}
                    to={item.path}
                    onClick={() => setIsSidebarOpen(false)}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-xs font-semibold'
                        : 'text-slate-600 hover:bg-slate-200/60 hover:text-slate-900'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-500'}`} />
                    <span>{item.name}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>

          {/* Recent Conversations */}
          <div className="px-3 py-3 border-t border-slate-200/60 mt-2">
            <div className="flex items-center justify-between px-2 mb-1.5 text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
              <span>Recent Conversations</span>
              <History className="w-3 h-3 text-slate-400" />
            </div>

            <div className="max-h-[220px] overflow-y-auto space-y-0.5 pr-1">
              {chats.map((chat) => {
                const isSelected = activeChatId === chat._id && location.pathname === '/chat';

                return (
                  <div
                    key={chat._id}
                    onClick={() => handleSelectChat(chat._id)}
                    className={`group flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-slate-200/80 text-slate-900 font-medium'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <Activity className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 flex-shrink-0" />
                      <span className="truncate text-xs">{chat.title || 'Inspection Report'}</span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteChat(chat._id);
                      }}
                      title="Delete chat"
                      className="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-600 transition-opacity"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Bottom Cluster Status & User Profile */}
        <div className="p-3 border-t border-slate-200/80 bg-white/50 space-y-2">
          {/* Air-Gapped Cluster Badge */}
          <div className="p-2.5 rounded-lg bg-slate-100/80 border border-slate-200/70">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 pulse-dot flex-shrink-0" />
              <span className="text-[10px] font-mono font-bold tracking-wider text-slate-800 uppercase">
                Air-Gapped Cluster
              </span>
            </div>
            <div className="text-[10px] text-slate-500 font-mono mt-0.5">
              On-Premise • Air-Gapped • Auditable
            </div>
          </div>

          {/* Settings link */}
          <NavLink
            to="/settings"
            onClick={() => setIsSidebarOpen(false)}
            className="flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Settings className="w-4 h-4 text-slate-500" />
              <span>Settings</span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">v3.4.1</span>
          </NavLink>

          {/* User Profile */}
          <div className="pt-2 border-t border-slate-100 flex items-center gap-2.5 px-1">
            <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center font-semibold text-xs ring-1 ring-slate-300">
              {user?.fullName?.firstName ? user.fullName.firstName[0] : 'E'}
              {user?.fullName?.lastName ? user.fullName.lastName[0] : 'R'}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-semibold text-slate-900 truncate">
                {user?.fullName?.firstName
                  ? `${user.fullName.firstName} ${user.fullName.lastName || ''}`
                  : 'Elena Rostova'}
              </div>
              <div className="text-[10px] text-slate-500 truncate">
                {user?.department || 'Systems Compliance Officer'}
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
