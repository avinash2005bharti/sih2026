import React from 'react';
import Modal from '../common/Modal';
import {
  ShieldCheck,
  CheckCircle2,
  Server,
  Lock,
  Cpu,
  Database,
  Radio,
  FileCheck,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';

const SovereignStatusModal = () => {
  const { isStatusModalOpen, setIsStatusModalOpen } = useChat();

  const STATUS_ITEMS = [
    {
      label: 'Data Processing',
      value: 'On-Premise',
      desc: 'All inference, embeddings, and prompt contexts are retained within local hardware.',
      icon: Server,
    },
    {
      label: 'Local Models',
      value: 'Enabled',
      desc: 'Air-gapped Llama-3-70B-Gov & Mistral running via vLLM / Ollama clusters.',
      icon: Cpu,
    },
    {
      label: 'Audit Logging',
      value: 'Enabled',
      desc: 'Tamper-proof cryptographic event logs recorded to local append-only storage.',
      icon: FileCheck,
    },
    {
      label: 'RBAC (Role-Based Access)',
      value: 'Enabled',
      desc: 'Strict multi-tier clearance verified across Operator, Engineer, and Analyst personas.',
      icon: Lock,
    },
    {
      label: 'External AI API Calls',
      value: '0',
      desc: 'Strict hardware firewall rules block 100% of external outbound telemetry.',
      icon: Radio,
    },
  ];

  return (
    <Modal
      isOpen={isStatusModalOpen}
      onClose={() => setIsStatusModalOpen(false)}
      title="Sovereign AI Status"
      subtitle="Hardware-enforced air-gapped cryptographic assurance"
      icon={ShieldCheck}
      maxWidth="max-w-lg"
    >
      <div className="space-y-4">
        {/* Verification Summary Banner */}
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 text-white flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-emerald-950 uppercase tracking-wider">
                Sovereign Mode Verified
              </div>
              <div className="text-[11px] text-emerald-800">
                100% Isolated Environment • Zero Data Egress
              </div>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded font-semibold">
            SEC-OK
          </span>
        </div>

        {/* Five Mandatory Checks */}
        <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl bg-slate-50/40">
          {STATUS_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.label} className="p-3 flex items-start gap-3">
                <div className="p-1.5 bg-white border border-slate-200 rounded-lg text-emerald-600 flex-shrink-0 mt-0.5 shadow-2xs">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-800">
                      {item.label}
                    </span>
                    <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.2 rounded border border-emerald-200/50">
                      ✓ {item.value}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5 leading-normal">
                    {item.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Telemetry Hardware Specs */}
        <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
          <div className="p-2.5 bg-slate-100 rounded-lg border border-slate-200/80">
            <span className="text-slate-400 block text-[10px]">CLUSTER NODE</span>
            <span className="font-semibold text-slate-800">MIL-NODE-04-TX</span>
          </div>
          <div className="p-2.5 bg-slate-100 rounded-lg border border-slate-200/80">
            <span className="text-slate-400 block text-[10px]">SECURITY LEVEL</span>
            <span className="font-semibold text-slate-800">FIPS 140-3 LEVEL 4</span>
          </div>
        </div>

        {/* Close action */}
        <div className="pt-2 flex justify-end">
          <button
            type="button"
            onClick={() => setIsStatusModalOpen(false)}
            className="px-4 py-2 bg-slate-900 text-white hover:bg-slate-800 text-xs font-medium rounded-lg transition-colors"
          >
            Acknowledge & Close
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default SovereignStatusModal;
