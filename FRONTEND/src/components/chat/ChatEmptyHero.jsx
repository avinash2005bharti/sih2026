import React from 'react';
import {
  Shield,
  FileText,
  Wrench,
  AlertTriangle,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';

const PROMPT_SUGGESTIONS = [
  {
    id: 'doc',
    title: 'Analyze a Document',
    description:
      'Extract insights, structured schemas, and cross-references from technical manuals, blueprints, and P&IDs.',
    icon: FileText,
    iconBg: 'bg-blue-50 text-blue-600',
    prompt:
      'Extract engineering tolerances, metallurgy specifications, and operating pressure thresholds from our technical manual.',
    agentType: 'document',
  },
  {
    id: 'maint',
    title: 'Maintenance Analysis',
    description:
      'Identify equipment vibration anomalies, wear risks, thermal thresholds, and predict MTBF.',
    icon: Wrench,
    iconBg: 'bg-teal-50 text-teal-600',
    prompt:
      'Run a vibration spectrum diagnostic on Boiler Feed Pump P-12 and calculate estimated MTBF.',
    agentType: 'maintenance',
  },
  {
    id: 'safety',
    title: 'Safety Assessment',
    description:
      'Audit refinery hazards, flare line heat maps, OSHA standards, and safety SOP compliance.',
    icon: AlertTriangle,
    iconBg: 'bg-indigo-50 text-indigo-600',
    prompt:
      'Perform a safety SOP audit for Hydrocracker Unit 3 flare line pressure relief valves against OISD-STD-117.',
    agentType: 'safety',
  },
  {
    id: 'comp',
    title: 'Compliance & Policy Check',
    description:
      'Verify procurement agreements, PSU directives, and defence protocols against regulatory benchmarks.',
    icon: ShieldCheck,
    iconBg: 'bg-slate-100 text-slate-700',
    prompt:
      'Verify vendor procurement contract clause 14 against PSU defense offset and sovereign confidentiality directives.',
    agentType: 'compliance',
  },
];

const ChatEmptyHero = ({ onSelectPrompt }) => {
  const { agents, setSelectedAgent } = useChat();

  const handleCardClick = (item) => {
    // Optionally match specialized agent
    const matchedAgent = agents.find((a) => a.type === item.agentType);
    if (matchedAgent) {
      setSelectedAgent(matchedAgent);
    }
    onSelectPrompt(item.prompt);
  };

  return (
    <div className="flex flex-col items-center justify-center max-w-4xl mx-auto px-4 py-8 text-center animate-in fade-in duration-300">
      {/* Central Shield Icon */}
      <div className="w-14 h-14 rounded-2xl bg-white border border-slate-200/90 shadow-subtle flex items-center justify-center mb-5 group hover:scale-105 transition-transform">
        <Shield className="w-7 h-7 text-blue-600 fill-blue-50/50" />
      </div>

      {/* Main Title */}
      <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 mb-3">
        Sovereign AI Workbench
      </h1>

      {/* Subheading */}
      <p className="text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed mb-4">
        Your secure AI workspace for confidential organizational intelligence across
        industrial facilities, national defense systems, and PSU critical operations.
      </p>

      {/* Air-Gap Capability Tag */}
      <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100/90 border border-slate-200/80 text-[11px] font-mono text-slate-700 mb-8 shadow-2xs">
        <Sparkles className="w-3.5 h-3.5 text-blue-600" />
        <span>Local Air-Gapped LLM Cluster • Neo4j Graph RAG Active • Immutable Audit Trail</span>
      </div>

      {/* 2x2 Suggestion Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full text-left">
        {PROMPT_SUGGESTIONS.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.id}
              onClick={() => handleCardClick(item)}
              className="p-4 bg-white hover:bg-slate-50/80 border border-slate-200/90 hover:border-slate-300 rounded-xl shadow-subtle hover:shadow-card cursor-pointer transition-all duration-200 flex items-start gap-3.5 group"
            >
              <div
                className={`p-2.5 rounded-xl ${item.iconBg} flex-shrink-0 group-hover:scale-105 transition-transform`}
              >
                <Icon className="w-5 h-5" />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                  {item.title}
                </h3>
                <p className="text-xs text-slate-500 mt-1 leading-normal line-clamp-2">
                  {item.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ChatEmptyHero;
