import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import Button from '../components/common/Button';

const NotFoundPage = () => {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-[#f8fafc] px-4 text-center">
      <div className="w-14 h-14 rounded-2xl bg-slate-100 text-slate-500 flex items-center justify-center mb-4">
        <ShieldAlert className="w-8 h-8 text-slate-600" />
      </div>
      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">
        404 - Node Not Found
      </h1>
      <p className="text-xs sm:text-sm text-slate-500 max-w-md mb-6">
        The requested internal resource or air-gapped route does not exist on this sovereign workbench node.
      </p>
      <Link to="/chat">
        <Button icon={ArrowLeft}>Return to AI Assistant</Button>
      </Link>
    </div>
  );
};

export default NotFoundPage;
