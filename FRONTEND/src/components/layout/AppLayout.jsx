import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopHeader from './TopHeader';
import MobileNav from './MobileNav';
import SovereignStatusModal from '../chat/SovereignStatusModal';
import ReasoningDrawer from '../chat/ReasoningDrawer';

const AppLayout = () => {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#f8fafc]">
      {/* Fixed/Collapsible Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 min-w-0 h-full overflow-hidden">
        <TopHeader />

        <main className="flex-1 overflow-y-auto relative pb-16 lg:pb-0">
          <Outlet />
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
