import React from 'react';
import { NavLink } from 'react-router-dom';
import { MessageSquare, Bot, FileText, Settings } from 'lucide-react';

const MOBILE_ITEMS = [
  { name: 'Chat', path: '/chat', icon: MessageSquare },
  { name: 'Agents', path: '/agents', icon: Bot },
  { name: 'Documents', path: '/documents', icon: FileText },
  { name: 'Settings', path: '/settings', icon: Settings },
];

const MobileNav = () => {
  return (
    <div className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-slate-200 px-4 py-2 flex items-center justify-around shadow-lg">
      {MOBILE_ITEMS.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 text-[10px] font-medium transition-colors ${
                isActive
                  ? 'text-blue-600 font-semibold'
                  : 'text-slate-500 hover:text-slate-900'
              }`
            }
          >
            <Icon className="w-5 h-5" />
            <span>{item.name}</span>
          </NavLink>
        );
      })}
    </div>
  );
};

export default MobileNav;
