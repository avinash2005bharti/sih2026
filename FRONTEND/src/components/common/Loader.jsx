import React from 'react';
import swarajLoading from '../../asset/swaraj_loading-removebg-preview.png';

export const Loader = ({ text = 'Loading SWaRaj AI...', size = 'md' }) => {
  const sizeMap = {
    sm: 'w-7 h-7',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  };

  return (
    <div className="flex flex-col items-center justify-center p-6 text-slate-500 gap-3 animate-in fade-in duration-200">
      <div className="relative flex items-center justify-center">
        <div className="absolute -inset-1 rounded-2xl bg-blue-500/10 animate-pulse" />
        <img
          src={swarajLoading}
          alt="SWaRaj Loading"
          className={`${sizeMap[size] || sizeMap.md} object-contain animate-pulse drop-shadow-sm select-none`}
        />
      </div>
      {text && (
        <span className="text-xs font-semibold text-slate-600 tracking-tight font-sans">
          {text}
        </span>
      )}
    </div>
  );
};

export const Skeleton = ({ className = '' }) => {
  return <div className={`animate-pulse bg-slate-200/80 rounded ${className}`} />;
};

export default Loader;
