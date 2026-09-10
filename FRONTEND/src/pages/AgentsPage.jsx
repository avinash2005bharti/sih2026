import React, { useState, useEffect } from 'react';
import {
  Bot,
  Plus,
  Trash2,
  Cpu,
  Sparkles,
  Sliders,
  CheckCircle2,
  Layers,
} from 'lucide-react';
import agentApi from '../api/agentApi';
import modelApi from '../api/modelApi';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Modal from '../components/common/Modal';
import Loader from '../components/common/Loader';

const AGENT_TYPES = [
  'orchestrator',
  'document',
  'maintenance',
  'safety',
  'compliance',
  'risk',
  'reporting',
  'research',
  'custom',
];

const AgentsPage = () => {
  const [agents, setAgents] = useState([]);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // New agent form
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: 'document',
    model: '',
    systemPrompt: '',
    temperature: 0.2,
    maxTokens: 2048,
    capabilities: 'document parsing, schema extraction, OCR cross-reference',
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [agentsRes, modelsRes] = await Promise.allSettled([
        agentApi.getAgents(),
        modelApi.getModels(),
      ]);

      if (agentsRes.status === 'fulfilled' && agentsRes.value?.agents) {
        setAgents(agentsRes.value.agents);
      }
      if (modelsRes.status === 'fulfilled' && modelsRes.value?.models) {
        setModels(modelsRes.value.models);
        if (modelsRes.value.models.length > 0) {
          setFormData((prev) => ({ ...prev, model: modelsRes.value.models[0]._id }));
        }
      }
    } catch (e) {
      console.warn('Failed to load agents from backend:', e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.systemPrompt) {
      setError('Name and System Prompt are required');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        ...formData,
        capabilities: formData.capabilities
          ? formData.capabilities.split(',').map((c) => c.trim())
          : [],
        temperature: parseFloat(formData.temperature) || 0.2,
        maxTokens: parseInt(formData.maxTokens) || 2048,
      };
      if (!payload.model && models.length > 0) {
        payload.model = models[0]._id;
      }

      const res = await agentApi.createAgent(payload);
      if (res && res.agent) {
        setAgents((prev) => [res.agent, ...prev]);
        setIsCreateModalOpen(false);
        setFormData({
          name: '',
          description: '',
          type: 'document',
          model: models[0]?._id || '',
          systemPrompt: '',
          temperature: 0.2,
          maxTokens: 2048,
          capabilities: '',
        });
      }
    } catch (err) {
      setError(err.message || 'Failed to create agent');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (agentId) => {
    if (!confirm('Are you sure you want to deactivate this agent?')) return;
    try {
      await agentApi.deleteAgent(agentId);
      setAgents((prev) => prev.filter((a) => a._id !== agentId));
    } catch (err) {
      alert(err.message || 'Failed to delete agent');
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <Bot className="w-6 h-6 text-blue-600" />
            Specialized Autonomous Agents
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Configure domain-specific AI agents equipped with local tools, knowledge bases, and air-gapped models.
          </p>
        </div>
        <Button
          onClick={() => setIsCreateModalOpen(true)}
          icon={Plus}
          className="self-start sm:self-auto"
        >
          Create Agent
        </Button>
      </div>

      {loading ? (
        <Loader text="Loading on-prem agent registry..." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <Card key={agent._id} className="p-5 flex flex-col justify-between hover:border-slate-300 transition-all">
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="p-2.5 bg-blue-50 text-blue-700 rounded-xl">
                    <Bot className="w-5 h-5" />
                  </div>
                  <Badge variant="blue" size="sm">
                    {agent.type}
                  </Badge>
                </div>

                <h3 className="text-sm font-semibold text-slate-900 mb-1">
                  {agent.name}
                </h3>
                <p className="text-xs text-slate-500 line-clamp-2 mb-3">
                  {agent.description || 'No description provided.'}
                </p>

                {/* System Prompt snippet */}
                <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 mb-3 text-[11px] font-mono text-slate-600 line-clamp-3">
                  {agent.systemPrompt}
                </div>

                {/* Metadata tags */}
                <div className="flex flex-wrap gap-1.5 mb-4">
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-slate-100 text-slate-700 rounded border border-slate-200">
                    Temp: {agent.temperature ?? 0.2}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-slate-100 text-slate-700 rounded border border-slate-200">
                    Max: {agent.maxTokens ?? 2048}
                  </span>
                  {agent.model && (
                    <span className="text-[10px] font-mono px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded border border-emerald-200/60">
                      {agent.model.displayName || agent.model.name || 'Local LLM'}
                    </span>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1 font-mono text-[10px]">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Active
                </span>
                <button
                  onClick={() => handleDelete(agent._id)}
                  className="p-1 text-slate-400 hover:text-rose-600 rounded transition-colors"
                  title="Deactivate Agent"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Agent Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Register New Specialized Agent"
        subtitle="Deploys an autonomous worker within your air-gapped cluster"
        icon={Bot}
      >
        <form onSubmit={handleCreate} className="space-y-4 text-xs">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Agent Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g. Turbine Diagnostic Agent"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Agent Domain Type *
              </label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white"
              >
                {AGENT_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Assigned Local Model
              </label>
              <select
                value={formData.model}
                onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white"
              >
                {models.map((m) => (
                  <option key={m._id} value={m._id}>
                    {m.displayName || m.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Description
            </label>
            <input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Brief summary of agent scope and responsibilities"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              System Prompt Directive *
            </label>
            <textarea
              required
              rows={4}
              value={formData.systemPrompt}
              onChange={(e) => setFormData({ ...formData, systemPrompt: e.target.value })}
              placeholder="You are an industrial diagnostics specialist. Analyze vibration spectrum data strictly adhering to ISO-10816 standards..."
              className="w-full px-3 py-2 border border-slate-200 rounded-lg font-mono text-xs"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Temperature ({formData.temperature})
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={formData.temperature}
                onChange={(e) => setFormData({ ...formData, temperature: e.target.value })}
                className="w-full"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Max Output Tokens
              </label>
              <input
                type="number"
                value={formData.maxTokens}
                onChange={(e) => setFormData({ ...formData, maxTokens: e.target.value })}
                className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
              />
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Capabilities (Comma-separated)
            </label>
            <input
              type="text"
              value={formData.capabilities}
              onChange={(e) => setFormData({ ...formData, capabilities: e.target.value })}
              placeholder="vibration analysis, MTBF calculation, SOP verification"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg"
            />
          </div>

          <div className="pt-3 border-t border-slate-100 flex justify-end gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={submitting}>
              Deploy Agent
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default AgentsPage;
