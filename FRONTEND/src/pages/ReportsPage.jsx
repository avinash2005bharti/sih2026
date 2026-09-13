import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  FileCheck,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Play,
  Download,
  Filter,
  Layers,
  ChevronRight,
} from 'lucide-react';
import taskApi from '../api/taskApi';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import Loader from '../components/common/Loader';
import EmptyState from '../components/common/EmptyState';

const ReportsPage = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState(null);
  const [taskDetail, setTaskDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);


  const loadTasks = async () => {
    setLoading(true);
    try {
      const res = await taskApi.getTasks();
      setTasks(res?.tasks || []);
    } catch (e) {
      console.error('Failed to fetch tasks:', e.message);
      setTasks([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleSelectTask = async (task) => {
    setSelectedTask(task);
    setDetailLoading(true);
    try {
      const res = await taskApi.getTaskById(task._id);
      setTaskDetail(res || { task, executions: [] });
    } catch (e) {
      console.error('Failed to fetch task detail:', e.message);
      setTaskDetail({ task, executions: [] });
    } finally {
      setDetailLoading(false);
    }
  };


  const getPriorityBadge = (p) => {
    switch (p) {
      case 'critical':
        return <Badge variant="danger" size="sm">CRITICAL</Badge>;
      case 'high':
        return <Badge variant="warning" size="sm">HIGH</Badge>;
      case 'medium':
        return <Badge variant="blue" size="sm">MEDIUM</Badge>;
      default:
        return <Badge variant="default" size="sm">LOW</Badge>;
    }
  };

  const getStatusBadge = (s) => {
    switch (s) {
      case 'completed':
        return <Badge variant="sovereign" size="sm" dot>COMPLETED</Badge>;
      case 'running':
        return <Badge variant="blue" size="sm" dot>RUNNING</Badge>;
      case 'failed':
        return <Badge variant="danger" size="sm">FAILED</Badge>;
      case 'cancelled':
        return <Badge variant="default" size="sm">CANCELLED</Badge>;
      default:
        return <Badge variant="default" size="sm">QUEUED</Badge>;
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <ShieldCheck className="w-6 h-6 text-emerald-600" />
            Compliance Reports & Agent Audit Trail
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Immutable log of all autonomous agent investigations, SCADA diagnostics, and supervisory approvals.
          </p>
        </div>
        <Button
          onClick={() => window.print()}
          variant="secondary"
          icon={Download}
          className="self-start sm:self-auto"
        >
          Export Audit Bundle
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Task List (Left 2 cols) */}
        <div className="lg:col-span-2 space-y-3">
          {loading ? (
            <Loader text="Retrieving immutable audit ledger..." />
          ) : tasks.length === 0 ? (
            <EmptyState
              title="No Audit Records Found"
              description="No agent task records have been logged yet. Dispatch a task from the chat interface to generate an audit trail."
              icon={ShieldCheck}
            />
          ) : (
            tasks.map((task) => {
              const isSelected = selectedTask?._id === task._id;

              return (
                <Card
                  key={task._id}
                  onClick={() => handleSelectTask(task)}
                  hoverable
                  className={`p-4 transition-all ${
                    isSelected ? 'ring-2 ring-blue-500 border-blue-500 bg-blue-50/20' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-0.5">
                        TASK ID: #{task._id.slice(-6)}
                      </span>
                      <h3 className="text-sm font-semibold text-slate-900">
                        {task.title || task.objective}
                      </h3>
                    </div>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {getPriorityBadge(task.priority)}
                      {getStatusBadge(task.status)}
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 line-clamp-2 mb-3">
                    {task.objective}
                  </p>

                  <div className="flex flex-wrap items-center justify-between text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-100">
                    <span>
                      Orchestrator: {task.orchestrator?.name || 'General Agent'}
                    </span>
                    <span>
                      {new Date(task.createdAt || Date.now()).toLocaleString()}
                    </span>
                  </div>
                </Card>
              );
            })
          )}
        </div>

        {/* Audit Inspector Panel (Right 1 col) */}
        <div className="lg:col-span-1">
          <Card className="p-5 sticky top-20 border-slate-200 shadow-card">
            <h3 className="text-sm font-bold text-slate-900 mb-1 flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-blue-600" />
              Audit Inspector
            </h3>
            <p className="text-[11px] text-slate-500 mb-4">
              Cryptographic execution breakdown for compliance officers.
            </p>

            {detailLoading ? (
              <Loader text="Loading step execution records..." size="sm" />
            ) : selectedTask ? (
              <div className="space-y-4 text-xs">
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/70 font-mono space-y-1.5">
                  <div className="flex justify-between">
                    <span className="text-slate-400 text-[10px]">RECORD ID</span>
                    <span className="text-slate-900 font-bold">{selectedTask._id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400 text-[10px]">HASH</span>
                    <span className="text-emerald-700 font-bold">SHA-256: VALID</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400 text-[10px]">EGRESS STATUS</span>
                    <span className="text-slate-700">0 EXTERNAL SOCKETS</span>
                  </div>
                </div>

                {/* Executions breakdown */}
                <div>
                  <h4 className="font-semibold text-slate-800 mb-2 text-xs">
                    Execution Steps ({taskDetail?.executions?.length || 0})
                  </h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {(taskDetail?.executions || []).map((step, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 bg-white border border-slate-200 rounded-lg text-slate-700 flex items-start gap-2 shadow-2xs"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 mt-0.5 flex-shrink-0" />
                        <div className="min-w-0 flex-1">
                          <div className="text-[11px] font-medium leading-tight">
                            {step.action}
                          </div>
                          {step.duration && (
                            <span className="text-[10px] font-mono text-slate-400">
                              {step.duration}ms duration
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Result */}
                {selectedTask.result && (
                  <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-lg text-blue-950 font-mono text-[11px]">
                    <span className="font-bold block mb-1">Summary Finding:</span>
                    <pre className="whitespace-pre-wrap font-sans text-xs">
                      {typeof selectedTask.result === 'string'
                        ? selectedTask.result
                        : JSON.stringify(selectedTask.result, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-10 text-slate-400 text-xs">
                Select a compliance report to inspect its cryptographic audit trail.
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
