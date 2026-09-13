import React from 'react';

const Badge = ({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  className = '',
  icon: Icon,
}) => {
  const sizeClasses = {
    sm: 'text-[10px] px-1.5 py-0.5 font-medium',
    md: 'text-xs px-2.5 py-0.5 font-medium',
    lg: 'text-sm px-3 py-1 font-medium',
  };

  const variantClasses = {
    default: 'bg-slate-100 text-slate-700 border border-slate-200',
    sovereign:
      'bg-emerald-50 text-emerald-800 border border-emerald-200/60 font-semibold tracking-wide',
    blue: 'bg-blue-50 text-blue-700 border border-blue-200',
    warning: 'bg-amber-50 text-amber-800 border border-amber-200',
    danger: 'bg-rose-50 text-rose-700 border border-rose-200',
    purple: 'bg-indigo-50 text-indigo-700 border border-indigo-200',
    dark: 'bg-slate-900 text-slate-100 border border-slate-700',
    telemetry: 'bg-slate-100 text-slate-600 font-mono text-[11px] border border-slate-200',
  };

  const dotClasses = {
    default: 'bg-slate-400',
    sovereign: 'bg-emerald-500 pulse-dot',
    blue: 'bg-blue-500',
    warning: 'bg-amber-500',
    danger: 'bg-rose-500',
    purple: 'bg-indigo-500',
    dark: 'bg-emerald-400 pulse-dot',
    telemetry: 'bg-emerald-500',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full ${sizeClasses[size] || sizeClasses.md} ${
        variantClasses[variant] || variantClasses.default
      } ${className}`}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
            dotClasses[variant] || 'bg-slate-400'
          }`}
        />
      )}
      {Icon && <Icon className="w-3.5 h-3.5 flex-shrink-0" />}
      <span>{children}</span>
    </span>
  );
};

export default Badge;
