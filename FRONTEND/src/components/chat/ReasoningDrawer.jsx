import React from 'react';
import {
  X,
  Sparkles,
  CheckCircle2,
  Clock,
  Database,
  Shield,
  Layers,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';

const ReasoningDrawer = () => {
  const { activeReasoningTrace, setActiveReasoningTrace } = useChat();

  if (!activeReasoningTrace) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/30 backdrop-blur-xs flex justify-end animate-in fade-in duration-200">
      <div
        className="fixed inset-0"
        onClick={() => setActiveReasoningTrace(null)}
      />

      <div className="relative w-full max-w-md bg-white h-full shadow-2xl border-l border-slate-200 flex flex-col z-10 animate-in slide-in-from-right duration-250">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/60">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-purple-50 text-purple-700 rounded-lg">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">
                Reasoning & Multi-Hop Trace
              </h3>
              <p className="text-[11px] text-slate-500 font-mono">
                Hardware-isolated LangGraph execution trace
              </p>
            </div>
          </div>
          <button
            onClick={() => setActiveReasoningTrace(null)}
            className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Trace Steps Timeline */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold mb-2">
            Sequential Step Execution (100% On-Prem)
          </div>

          <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
            {activeReasoningTrace.map((step, idx) => (
              <div key={idx} className="relative">
                {/* Timeline node */}
                <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-white border-2 border-emerald-500 flex items-center justify-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                </div>

                <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3 shadow-2xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-slate-900">
                      {step.title}
                    </span>
                    {step.time && (
                      <span className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
                        <Clock className="w-2.5 h-2.5" />
                        {step.time}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-600 leading-normal">
                    {step.details}
                  </p>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="inline-flex items-center gap-1 text-[9px] font-mono font-semibold px-2 py-0.2 bg-emerald-50 text-emerald-700 border border-emerald-200/60 rounded">
                      <CheckCircle2 className="w-2.5 h-2.5" />
                      {step.status?.toUpperCase() || 'VERIFIED'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <span className="text-[10px] font-mono text-slate-400">
            Audit Trail Hash: #TR-99418
          </span>
          <button
            onClick={() => setActiveReasoningTrace(null)}
            className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium rounded-lg"
          >
            Close Trace
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReasoningDrawer;
