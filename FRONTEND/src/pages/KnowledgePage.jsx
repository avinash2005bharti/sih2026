import React, { useState, useEffect } from 'react';
import {
  Database,
  Plus,
  Trash2,
  Layers,
  FileText,
  Cpu,
  CheckCircle2,
} from 'lucide-react';
import knowledgeApi from '../api/knowledgeApi';
import modelApi from '../api/modelApi';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Modal from '../components/common/Modal';
import Loader from '../components/common/Loader';
import EmptyState from '../components/common/EmptyState';

const KnowledgePage = () => {
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    collectionName: '',
    embeddingModel: '',
    vectorDimension: 1536,
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [kbRes, modelsRes] = await Promise.allSettled([
        knowledgeApi.getKnowledgeBases(),
        modelApi.getModels(),
      ]);

      if (kbRes.status === 'fulfilled' && kbRes.value?.knowledgeBases) {
        setKnowledgeBases(kbRes.value.knowledgeBases);
      }
      if (modelsRes.status === 'fulfilled' && modelsRes.value?.models) {
        const emb = modelsRes.value.models.filter((m) => m.modelType === 'embedding');
        setModels(emb.length > 0 ? emb : modelsRes.value.models);
        if (modelsRes.value.models.length > 0) {
          setFormData((prev) => ({ ...prev, embeddingModel: modelsRes.value.models[0]._id }));
        }
      }
    } catch (e) {
      console.warn('Backend knowledge bases unavailable:', e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.collectionName) {
      setError('Name and collectionName are required');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        ...formData,
        vectorDimension: parseInt(formData.vectorDimension) || 1536,
      };
      if (!payload.embeddingModel && models.length > 0) {
        payload.embeddingModel = models[0]._id;
      }

      const res = await knowledgeApi.createKnowledgeBase(payload);
      if (res && res.knowledgeBase) {
        setKnowledgeBases((prev) => [res.knowledgeBase, ...prev]);
        setIsCreateModalOpen(false);
        setFormData({
          name: '',
          description: '',
          collectionName: '',
          embeddingModel: models[0]?._id || '',
          vectorDimension: 1536,
        });
      }
    } catch (err) {
      setError(err.message || 'Failed to create knowledge base');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (kbId) => {
    if (!confirm('Are you sure you want to deactivate this vector collection?')) return;
    try {
      await knowledgeApi.deleteKnowledgeBase(kbId);
      setKnowledgeBases((prev) => prev.filter((k) => k._id !== kbId));
    } catch (err) {
      alert(err.message || 'Failed to delete knowledge base');
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <Database className="w-6 h-6 text-blue-600" />
            Air-Gapped Knowledge Bases & Vector Stores
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Maintain isolated Qdrant vector collections and Neo4j graph nodes for zero-egress RAG.
          </p>
        </div>
        <Button
          onClick={() => setIsCreateModalOpen(true)}
          icon={Plus}
          className="self-start sm:self-auto"
        >
          Create Collection
        </Button>
      </div>

      {loading ? (
        <Loader text="Loading on-prem Qdrant vector collections..." />
      ) : knowledgeBases.length === 0 ? (
        <EmptyState
          icon={Database}
          title="No Knowledge Base Collections"
          description="Create your first air-gapped vector store collection to index plant blueprints, manuals, and sensor catalogs."
          actionText="Create Collection"
          onAction={() => setIsCreateModalOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {knowledgeBases.map((kb) => (
            <Card key={kb._id} className="p-5 flex flex-col justify-between hover:border-slate-300 transition-all">
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="p-2.5 bg-blue-50 text-blue-600 rounded-xl">
                    <Database className="w-5 h-5" />
                  </div>
                  <Badge variant="sovereign" size="sm" dot>
                    Qdrant Active
                  </Badge>
                </div>

                <h3 className="text-sm font-semibold text-slate-900 mb-1">
                  {kb.name}
                </h3>
                <div className="text-[11px] font-mono text-blue-600 mb-2">
                  collection: {kb.collectionName}
                </div>
                <p className="text-xs text-slate-500 line-clamp-2 mb-3">
                  {kb.description || 'Isolated engineering knowledge collection.'}
                </p>

                <div className="flex flex-wrap gap-1.5 mb-4">
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-slate-100 text-slate-700 rounded border border-slate-200">
                    Dim: {kb.vectorDimension || 1536}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-slate-100 text-slate-700 rounded border border-slate-200">
                    Docs: {kb.documents?.length || 0}
                  </span>
                  {kb.embeddingModel && (
                    <span className="text-[10px] font-mono px-2 py-0.5 bg-purple-50 text-purple-700 rounded border border-purple-200/60">
                      {kb.embeddingModel.displayName || 'BGE-Large-Local'}
                    </span>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                <span className="text-[10px] font-mono text-slate-500">
                  Cosine Metric
                </span>
                <button
                  onClick={() => handleDelete(kb._id)}
                  className="p-1 text-slate-400 hover:text-rose-600 rounded transition-colors"
                  title="Delete Collection"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Initialize Vector Collection"
        subtitle="Provisions an isolated Qdrant vector index in the air-gapped cluster"
        icon={Database}
      >
        <form onSubmit={handleCreate} className="space-y-4 text-xs">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Knowledge Base Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g. Refinery P&ID Technical Index"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Qdrant Collection Name *
              </label>
              <input
                type="text"
                required
                value={formData.collectionName}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    collectionName: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '_'),
                  })
                }
                placeholder="refinery_pid_v1"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg font-mono text-xs"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Vector Dimension
              </label>
              <select
                value={formData.vectorDimension}
                onChange={(e) => setFormData({ ...formData, vectorDimension: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white font-mono text-xs"
              >
                <option value="1536">1536 (OpenAI / Local Dense)</option>
                <option value="1024">1024 (BGE-Large / E5)</option>
                <option value="768">768 (MiniLM / BERT-Base)</option>
                <option value="384">384 (All-MiniLM-L6-v2)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Description
            </label>
            <textarea
              rows={2}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Collection scope and document types..."
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
              Initialize Collection
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default KnowledgePage;
