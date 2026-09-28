import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopHeader from './TopHeader';
import MobileNav from './MobileNav';
import SovereignStatusModal from '../chat/SovereignStatusModal';
import ReasoningDrawer from '../chat/ReasoningDrawer';

const AppLayout = () => {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-transparent">
      {/* Toggleable Sidebar — animates width via inline styles */}
      <Sidebar />

      {/* Main Content Area — flex-1 fills remaining space, transitions smoothly */}
      <div className="flex flex-col flex-1 min-w-0 h-full overflow-hidden transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]">
        <TopHeader />

        <main className="flex-1 overflow-y-auto relative pb-16 lg:pb-0">
          <div className="max-w-6xl mx-auto px-4 py-6">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Mobile Bottom Navigation */}
      <MobileNav />

      {/* Sovereign AI Status Verification Modal */}
      <SovereignStatusModal />

      {/* Deep Reasoning Trace Slide-Over Drawer */}
      <ReasoningDrawer />
    </div>
  );
};

export default AppLayout;
