import React, { useState, useEffect } from 'react';
import {
  FileText,
  Upload,
  Trash2,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileSpreadsheet,
  FileCode,
  FileCheck,
  HardDrive,
  Download,
  Eye,
  Layers,
  Database,
  Lock,
  Shield
} from 'lucide-react';
import documentApi from '../api/documentApi';
import { useAuth } from '../context/AuthContext';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Modal from '../components/common/Modal';
import Loader from '../components/common/Loader';
import EmptyState from '../components/common/EmptyState';

const DOC_TYPES = [
  'pdf',
  'report',
  'manual',
  'sop',
  'image',
  'word',
  'excel',
  'text',
  'other',
];

const DocumentsPage = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin' || user?.isAdmin;
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Upload Form
  const [formData, setFormData] = useState({
    name: '',
    documentType: 'manual',
    storageType: 'local',
  });
  const [selectedFile, setSelectedFile] = useState(null);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const res = await documentApi.getDocuments();
      if (res && res.documents) {
        setDocuments(res.documents);
      }
    } catch (e) {
      console.warn('Backend documents unavailable, using local cache:', e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  // Poll while any documents are still in 'processing' status
  useEffect(() => {
    const hasProcessing = documents.some((d) => d.processingStatus === 'processing');
    if (!hasProcessing) return;

    const timer = setInterval(async () => {
      try {
        const res = await documentApi.getDocuments();
        if (res && res.documents) {
          setDocuments(res.documents);
        }
      } catch (err) {
        // Silent catch during background polling
      }
    }, 3000);

    return () => clearInterval(timer);
  }, [documents]);

  const handleFilePick = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setFormData((prev) => ({
        ...prev,
        name: prev.name || file.name.replace(/\.[^/.]+$/, ''),
      }));
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !selectedFile) {
      setError('Please provide document title and select a file');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const formPayload = new FormData();
      formPayload.append('file', selectedFile);
      formPayload.append('name', formData.name);
      formPayload.append('documentType', formData.documentType);
      formPayload.append('storageType', formData.storageType);

      const res = await documentApi.uploadDocument(formPayload);
      if (res && res.document) {
        setDocuments((prev) => [res.document, ...prev.filter((d) => d._id !== res.document._id)]);
        setIsUploadModalOpen(false);
        setSelectedFile(null);
        setFormData({
          name: '',
          documentType: 'manual',
          storageType: 'local',
        });
      }
    } catch (err) {
      setError(err.message || 'Failed to upload and vectorize document');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (docId) => {
    if (!confirm('Are you sure you want to delete this document from encrypted storage and Qdrant vector index?')) return;
    try {
      await documentApi.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d._id !== docId));
      if (selectedDoc?._id === docId) setSelectedDoc(null);
    } catch (err) {
      alert(err.message || 'Failed to delete document');
    }
  };

  const getStatusBadge = (doc) => {
    const status = doc.processingStatus || 'uploaded';
    const chunks = doc.metadata?.chunksCount;
    switch (status) {
      case 'processed':
        return (
          <Badge variant="sovereign" size="sm" dot>
            Processed {chunks !== undefined && chunks > 0 ? `(${chunks} chunks)` : ''}
          </Badge>
        );
      case 'processing':
        return (
          <Badge variant="warning" size="sm" dot>
            Chunking & Ingesting...
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="danger" size="sm">
            Failed
          </Badge>
        );
      default:
        return (
          <Badge variant="default" size="sm">
            Uploaded
          </Badge>
        );
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-blue-600" />
            Confidential Document Repository
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Store, chunk, and vectorize technical manuals, blueprints, SOP directives, and plant reports into Qdrant for Autonomous Agent retrieval.
          </p>
        </div>
        <div className="flex items-center gap-2.5 self-start sm:self-auto">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadDocuments}
            className="text-xs"
          >
            Refresh
          </Button>
          <Button
            onClick={() => setIsUploadModalOpen(true)}
            icon={Upload}
          >
            Upload Document
          </Button>
        </div>
      </div>

      {loading ? (
        <Loader text="Loading encrypted document index and vector status..." />
      ) : documents.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No documents uploaded yet"
          description="Upload technical specs, plant layouts, or operating procedures to enable offline Graph RAG analysis and Agent CRUD actions."
          actionText="Upload First Document"
          onAction={() => setIsUploadModalOpen(true)}
        />
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs text-left divide-y divide-slate-200">
              <thead className="bg-slate-50 text-slate-700 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-4 py-3">Document</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Access & Visibility</th>
                  <th className="px-4 py-3">Storage</th>
                  <th className="px-4 py-3">Qdrant Vectors</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Uploaded</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {documents.map((doc) => (
                  <tr key={doc._id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2.5">
                        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900 cursor-pointer hover:text-blue-600" onClick={() => setSelectedDoc(doc)}>
                            {doc.name}
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            {doc.originalName || doc.filePath}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 uppercase font-mono text-[10px] text-slate-600">
                      {doc.documentType || 'PDF'}
                    </td>
                    <td className="px-4 py-3">
                      {doc.isUploadedByAdmin ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200" title="Admin Policy: Available to all clients (read-only)">
                          <Shield className="w-3 h-3 text-emerald-600" />
                          Admin Policy (Global Read-Only)
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-200" title="Client Document: Visible only to Admin and Uploader">
                          <Lock className="w-3 h-3 text-indigo-500" />
                          {isAdmin ? `Client: ${doc.uploaderInfo?.name || doc.uploaderInfo?.email || 'Confidential'}` : 'Private Upload'}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-600">
                        <HardDrive className="w-3 h-3 text-slate-400" />
                        {doc.storageType || 'local'}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] text-slate-600">
                      <span className="inline-flex items-center gap-1">
                        <Database className="w-3 h-3 text-blue-500" />
                        {doc.metadata?.chunksCount !== undefined ? `${doc.metadata.chunksCount} chunks` : 'N/A'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {getStatusBadge(doc)}
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-[11px] font-mono">
                      {new Date(doc.createdAt || Date.now()).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => setSelectedDoc(doc)}
                          className="p-1.5 text-slate-400 hover:text-blue-600 rounded transition-colors"
                          title="View Document Details & Chunks"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {doc.canModify === false || (!isAdmin && doc.isUploadedByAdmin) ? (
                          <span
                            className="p-1.5 text-slate-300 cursor-not-allowed"
                            title="Admin policy: Global documents cannot be modified or deleted by clients"
                          >
                            <Lock className="w-4 h-4 text-amber-500" />
                          </span>
                        ) : (
                          <button
                            onClick={() => handleDelete(doc._id)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 rounded transition-colors"
                            title="Delete Document"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* View Document Details Modal */}
      {selectedDoc && (
        <Modal
          isOpen={Boolean(selectedDoc)}
          onClose={() => setSelectedDoc(null)}
          title={selectedDoc.name}
          subtitle={`Type: ${selectedDoc.documentType?.toUpperCase()} | Chunks in Qdrant: ${selectedDoc.metadata?.chunksCount || 0}`}
          icon={FileText}
        >
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-lg font-mono text-[11px]">
              <div>
                <span className="text-slate-400">Document ID:</span>
                <p className="font-semibold text-slate-800 break-all">{selectedDoc._id}</p>
              </div>
              <div>
                <span className="text-slate-400">Status:</span>
                <p className="mt-0.5">{getStatusBadge(selectedDoc)}</p>
              </div>
              <div>
                <span className="text-slate-400">Governance & Access:</span>
                <p className="font-semibold text-slate-800">
                  {selectedDoc.isUploadedByAdmin ? 'Admin Policy (All Clients Read-Only)' : 'Confidential (Admin & Uploader)'}
                </p>
              </div>
              <div>
                <span className="text-slate-400">Uploaded By:</span>
                <p className="font-semibold text-slate-800">
                  {selectedDoc.uploaderInfo?.name 
                    ? `${selectedDoc.uploaderInfo.name} (${selectedDoc.uploaderInfo.role || 'client'})` 
                    : (selectedDoc.isUploadedByAdmin ? 'Admin' : 'Client')}
                  {selectedDoc.uploaderInfo?.email && <span className="block text-[10px] text-slate-500 font-normal">{selectedDoc.uploaderInfo.email}</span>}
                </p>
              </div>
              <div>
                <span className="text-slate-400">Upload Timestamp:</span>
                <p className="font-semibold text-slate-700">
                  {new Date(selectedDoc.createdAt || Date.now()).toLocaleString()}
                </p>
              </div>
              <div>
                <span className="text-slate-400">File Size:</span>
                <p className="font-semibold text-slate-700">
                  {selectedDoc.fileSize ? `${(selectedDoc.fileSize / 1024).toFixed(1)} KB` : 'N/A'}
                </p>
              </div>
              <div className="col-span-2">
                <span className="text-slate-400">File Path:</span>
                <p className="font-semibold text-slate-700 truncate" title={selectedDoc.filePath}>{selectedDoc.filePath || 'Stored on disk'}</p>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="font-semibold text-slate-700">
                  Extracted Content / Vector Preview
                </label>
                <span className="text-[10px] text-slate-400 font-mono">
                  {selectedDoc.extractedText ? `${selectedDoc.extractedText.length} characters` : 'No text preview'}
                </span>
              </div>
              <div className="p-3 bg-slate-900 text-slate-200 rounded-lg max-h-60 overflow-y-auto font-mono text-[11px] whitespace-pre-wrap">
                {selectedDoc.extractedText || 'No text extracted. Document may be binary or pending OCR.'}
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex justify-end gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setSelectedDoc(null)}
              >
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Upload Modal */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        title="Ingest & Vectorize Document"
        subtitle="Uploads file, runs chunking, embeds text, and indexes into Qdrant for AI Agents"
        icon={Upload}
      >
        <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Document Display Title *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g. Flare Header Inspection SOP Rev 4"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Document Classification *
              </label>
              <select
                value={formData.documentType}
                onChange={(e) => setFormData({ ...formData, documentType: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white"
              >
                {DOC_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Storage Target
              </label>
              <select
                value={formData.storageType}
                onChange={(e) => setFormData({ ...formData, storageType: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white"
              >
                <option value="local">Air-Gapped Local Storage</option>
                <option value="docker_volume">Isolated Docker Volume</option>
                <option value="minio">On-Prem S3 / MinIO</option>
              </select>
            </div>
          </div>

          {/* File input box */}
          <div className="p-6 border-2 border-dashed border-slate-200 rounded-xl text-center hover:border-blue-400 transition-colors bg-slate-50/50">
            <input
              type="file"
              id="file-upload"
              onChange={handleFilePick}
              className="hidden"
            />
            <label htmlFor="file-upload" className="cursor-pointer block">
              <Upload className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <div className="font-semibold text-slate-800">
                {selectedFile ? selectedFile.name : 'Click to select technical file'}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Supports PDF, DOCX, XLSX, TXT, CSV, MD, PNG, JPG (Max 150MB per file)
              </p>
            </label>
          </div>

          <div className="pt-3 border-t border-slate-100 flex justify-end gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsUploadModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={submitting}>
              {submitting ? 'Chunking & Vectorizing...' : 'Ingest & Vectorize'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default DocumentsPage;
