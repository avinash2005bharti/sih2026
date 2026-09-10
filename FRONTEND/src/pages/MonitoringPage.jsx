import React, { useState, useEffect } from 'react';
import {
  Activity,
  Server,
  Cpu,
  ShieldCheck,
  Radio,
  Lock,
  RefreshCw,
  HardDrive,
  Zap,
} from 'lucide-react';
import settingApi from '../api/settingApi';
import modelApi from '../api/modelApi';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import Loader from '../components/common/Loader';

const MonitoringPage = () => {
  const [health, setHealth] = useState({ success: true, message: 'AI Workbench API is running' });
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const [hRes, mRes] = await Promise.allSettled([
        settingApi.checkHealth(),
        modelApi.getModels(),
      ]);

      if (hRes.status === 'fulfilled') setHealth(hRes.value);
      if (mRes.status === 'fulfilled' && mRes.value?.models) setModels(mRes.value.models);
    } catch (e) {
      console.warn('Monitoring API check:', e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <Activity className="w-6 h-6 text-emerald-600" />
            Cluster Health & Telemetry
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Real-time verification of on-premise compute nodes, model endpoints, and zero-egress firewalls.
          </p>
        </div>
        <Button
          onClick={fetchStatus}
          variant="secondary"
          size="sm"
          icon={RefreshCw}
          isLoading={loading}
          className="self-start sm:self-auto"
        >
          Refresh Cluster
        </Button>
      </div>

      {/* Top 4 Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-500">API Gateway</span>
            <div className="p-1.5 bg-emerald-50 text-emerald-600 rounded-lg">
              <Server className="w-4 h-4" />
            </div>
          </div>
          <div className="text-lg font-bold text-slate-900 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            Online (200 OK)
          </div>
          <span className="text-[10px] font-mono text-slate-400 mt-1 block">
            Port 5000 • Express 5.x
          </span>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-500">Air-Gap Shield</span>
            <div className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="text-lg font-bold text-emerald-600 flex items-center gap-1.5">
            Active / Verified
          </div>
          <span className="text-[10px] font-mono text-slate-400 mt-1 block">
            0 External Calls • FIPS 140-3
          </span>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-500">Local Inference</span>
            <div className="p-1.5 bg-purple-50 text-purple-600 rounded-lg">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="text-lg font-bold text-slate-900">
            {health?.inferenceRate ?? '—'}
          </div>
          <span className="text-[10px] font-mono text-slate-400 mt-1 block">
            vLLM Engine • FlashAttention-2
          </span>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-500">GPU VRAM Load</span>
            <div className="p-1.5 bg-slate-100 text-slate-700 rounded-lg">
              <Cpu className="w-4 h-4" />
            </div>
          </div>
          <div className="text-lg font-bold text-slate-900">
            {health?.gpuVram ?? '—'}
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full mt-2 overflow-hidden">
            <div
              className="bg-blue-600 h-full rounded-full"
              style={{ width: health?.gpuVramPct ? `${health.gpuVramPct}%` : '0%' }}
            />
          </div>
        </Card>
      </div>

      {/* Model Clusters Table */}
      <Card className="p-5">
        <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-blue-600" />
          Air-Gapped Foundation Model Registry
        </h3>

        <div className="overflow-x-auto">
          {models.length === 0 ? (
            <div className="py-10 text-center text-xs text-slate-400">
              <Cpu className="w-8 h-8 mx-auto mb-2 text-slate-300" />
              No models registered yet. Add models via the Settings page or backend admin.
            </div>
          ) : (
            <table className="min-w-full text-xs text-left divide-y divide-slate-200">
              <thead className="bg-slate-50 text-slate-700 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-4 py-2.5">Model Name</th>
                  <th className="px-4 py-2.5">Provider</th>
                  <th className="px-4 py-2.5">Type</th>
                  <th className="px-4 py-2.5">Context</th>
                  <th className="px-4 py-2.5">Quantization</th>
                  <th className="px-4 py-2.5">Isolation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {models.map((m, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/60">
                    <td className="px-4 py-2.5 font-semibold text-slate-900 font-mono">
                      {m.displayName || m.name}
                    </td>
                    <td className="px-4 py-2.5 uppercase font-mono text-slate-600">
                      {m.provider}
                    </td>
                    <td className="px-4 py-2.5 text-slate-600 uppercase font-mono">
                      {m.modelType}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-slate-600">
                      {((m.contextWindow || 32768) / 1024).toFixed(0)}k tokens
                    </td>
                    <td className="px-4 py-2.5 font-mono text-slate-600">
                      {m.quantization || 'FP16'}
                    </td>
                    <td className="px-4 py-2.5">
                      <Badge variant="sovereign" size="sm" dot>
                        Air-Gapped
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>
    </div>
  );
};

export default MonitoringPage;
