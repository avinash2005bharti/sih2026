import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
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
  PanelLeftClose,
  PanelLeft,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useAuth } from '../../context/AuthContext';
import swarajLogo from '../../asset/swaraj.logo-removebg-preview.png';

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
    toggleSidebar,
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
    // Close on mobile only
    if (window.innerWidth < 1024) toggleSidebar(false);
  };

  const handleSelectChat = (chatId) => {
    selectChat(chatId);
    navigate('/chat');
    if (window.innerWidth < 1024) toggleSidebar(false);
  };

  const handleNavClick = () => {
    if (window.innerWidth < 1024) toggleSidebar(false);
  };

  return (
    <>
      {/* Mobile Backdrop — only on small screens when sidebar is open */}
      <div
        className={`fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs lg:hidden transition-opacity duration-300 ${
          isSidebarOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={() => toggleSidebar(false)}
      />

      {/* Sidebar Container */}
      <aside
        style={{
          width: isSidebarOpen ? '260px' : '0px',
          minWidth: isSidebarOpen ? '260px' : '0px',
        }}
        className={`
          fixed lg:relative top-0 left-0 bottom-0 z-50
          bg-white border-r border-slate-200/90
          flex flex-col justify-between
          transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]
          overflow-hidden select-none
          ${!isSidebarOpen ? 'lg:border-r-0' : ''}
        `}
      >
        {/* Inner content wrapper — keeps content at 260px, prevents squish */}
        <div className="w-[260px] min-w-[260px] flex flex-col h-full">
          {/* Top Header & Brand */}
          <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
            <div className="px-3.5 py-3 flex items-center justify-between border-b border-slate-200">
              <div
                className="flex items-center gap-2.5 cursor-pointer"
                onClick={() => {
                  navigate('/chat');
                  handleNavClick();
                }}
                role="button"
                tabIndex={0}
              >
                <img
                  src={swarajLogo}
                  alt="SWaRaj Logo"
                  className="w-8 h-8 rounded-lg object-contain shadow-2xs border border-slate-100"
                />
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-extrabold text-slate-900 text-sm tracking-tight">
                      SWaRaj
                    </span>
                    <span className="text-[9px] px-1.5 py-0.2 bg-blue-50 text-blue-700 font-mono font-bold rounded border border-blue-100">
                      AI
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500 font-medium -mt-0.5 truncate max-w-[150px]">
                    Autonomous AI Workbench
                  </div>
                </div>
              </div>

              {/* Collapse button — always visible */}
              <button
                onClick={() => toggleSidebar(false)}
                className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                title="Close sidebar"
                aria-label="Close sidebar"
              >
                <PanelLeftClose className="w-4 h-4" />
              </button>
            </div>

            {/* New Chat Button */}
            <div className="p-2.5">
              <button
                onClick={handleNewChat}
                className="w-full flex items-center justify-between px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-xs transition-all group"
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
            <div className="px-2.5 py-1">
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
                      onClick={handleNavClick}
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
                    onClick={handleNavClick}
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
            <div className="px-2.5 py-2.5 border-t border-slate-200 mt-1 flex-1 min-h-0 flex flex-col">
              <div className="flex items-center justify-between px-2 mb-1.5 text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
                <span>Recent Conversations</span>
                <History className="w-3.5 h-3.5 text-slate-400" />
              </div>

              <div className="overflow-y-auto space-y-0.5 pr-1 flex-1">
                {chats.length === 0 ? (
                  <div className="px-2 py-1 text-slate-400 text-[11px] italic">
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

          {/* Bottom Navigation & User Profile */}
          <div className="p-2.5 border-t border-slate-200 bg-slate-50/50 space-y-1.5">
            {/* Settings link */}
            <NavLink
              to="/settings"
              onClick={handleNavClick}
              className="flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Settings className="w-4 h-4 text-slate-500" />
                <span>Settings & System</span>
              </div>
              <span className="text-[10px] font-mono text-slate-400">v3.4</span>
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
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
