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
  Users,
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

  const isAdmin = user?.isAdmin || user?.role === 'admin';

  const userFirstName = user?.fullName?.firstName || '';
  const userLastName = user?.fullName?.lastName || '';
  const userFullName = userFirstName
    ? `${userFirstName} ${userLastName}`.trim()
    : user?.email || 'Operator';
  const userInitials = userFirstName
    ? `${userFirstName[0]}${userLastName ? userLastName[0] : ''}`.toUpperCase()
    : 'OP';
  const userRole = user?.role ? user.role.toUpperCase() : 'OPERATOR';

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
        className={`fixed lg:static top-0 left-0 bottom-0 z-50 w-[265px] bg-white border-r border-slate-200/90 flex flex-col justify-between transition-transform duration-200 ease-in-out select-none ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Top Header & Brand */}
        <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
          <div className="p-4 pb-3 flex items-center justify-between border-b border-slate-200">
            <div
              className="flex items-center gap-2.5 cursor-pointer"
              onClick={() => {
                navigate('/chat');
                setIsSidebarOpen(false);
              }}
              role="button"
              tabIndex={0}
            >
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-xs">
                <Shield className="w-5 h-5 fill-white/20" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-slate-900 text-sm tracking-tight">
                    Sovereign
                  </span>
                  <span className="text-[10px] px-1.5 py-0.2 bg-slate-100 text-slate-700 font-mono font-bold rounded">
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
              className="w-full flex items-center justify-between px-3.5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-xs transition-all group"
            >
              <div className="flex items-center gap-2">
                <Plus className="w-4 h-4 stroke-[2.5] group-hover:scale-110 transition-transform" />
                <span>New Chat</span>
              </div>
              <span className="text-[10px] font-mono text-blue-100 bg-blue-700/60 px-1.5 py-0.5 rounded">
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
                        ? 'bg-blue-50 text-blue-700 shadow-2xs font-semibold'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-slate-500'}`} />
                    <span>{item.name}</span>
                  </NavLink>
                );
              })}

              {/* Admin-only User Management navigation link */}
              {isAdmin && (
                <NavLink
                  to="/settings?tab=users"
                  onClick={() => setIsSidebarOpen(false)}
                  className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                    location.pathname === '/settings' && location.search.includes('tab=users')
                      ? 'bg-purple-50 text-purple-700 shadow-2xs font-semibold'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Users className="w-4 h-4 text-purple-600" />
                    <span>User Management</span>
                  </div>
                  <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-purple-100 text-purple-700">
                    ADMIN
                  </span>
                </NavLink>
              )}
            </nav>
          </div>

          {/* Recent Conversations */}
          <div className="px-3 py-3 border-t border-slate-200 mt-2 flex-1 min-h-0 flex flex-col">
            <div className="flex items-center justify-between px-2 mb-1.5 text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
              <span>Recent Conversations</span>
              <History className="w-3.5 h-3.5 text-slate-400" />
            </div>

            <div className="overflow-y-auto space-y-0.5 pr-1 flex-1">
              {chats.length === 0 ? (
                <div className="px-2 py-3 text-center text-slate-400 text-xs italic">
                  No active conversations
                </div>
              ) : (
                chats.map((chat) => {
                  const isSelected = activeChatId === chat._id && location.pathname === '/chat';

                  return (
                    <div
                      key={chat._id}
                      onClick={() => handleSelectChat(chat._id)}
                      className={`group flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs cursor-pointer transition-colors ${
                        isSelected
                          ? 'bg-slate-100 text-slate-900 font-semibold'
                          : 'text-slate-600 hover:bg-slate-100/80 hover:text-slate-900'
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
                })
              )}
            </div>
          </div>
        </div>

        {/* Bottom Cluster Status & User Profile */}
        <div className="p-3 border-t border-slate-200 bg-slate-50/50 space-y-2">
          {/* Air-Gapped Cluster Badge */}
          <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200/80">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 pulse-dot flex-shrink-0" />
              <span className="text-[10px] font-mono font-bold tracking-wider text-emerald-900 uppercase">
                Air-Gapped Cluster
              </span>
            </div>
            <div className="text-[10px] text-emerald-700 font-mono mt-0.5">
              On-Premise • Zero Egress • Audited
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
          <div className="pt-2 border-t border-slate-200 flex items-center gap-2.5 px-1">
            <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center font-bold text-xs ring-1 ring-slate-300 flex-shrink-0">
              {userInitials}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-bold text-slate-900 truncate">
                {userFullName}
              </div>
              <div className="text-[10px] text-slate-500 truncate font-mono">
                {userRole}
                {user?.department ? ` • ${user.department}` : ''}
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
