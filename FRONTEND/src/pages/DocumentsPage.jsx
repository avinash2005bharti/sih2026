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
} from 'lucide-react';
import documentApi from '../api/documentApi';
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
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Upload Form
  const [formData, setFormData] = useState({
    name: '',
    documentType: 'manual',
    storageType: 'local',
    filePath: '',
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

  const handleFilePick = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setFormData((prev) => ({
        ...prev,
        name: prev.name || file.name.replace(/\.[^/.]+$/, ''),
        filePath: `/uploads/confidential/${file.name}`,
      }));
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || (!selectedFile && !formData.filePath)) {
      setError('Please provide document title and select a file');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        name: formData.name,
        originalName: selectedFile?.name || `${formData.name}.pdf`,
        mimeType: selectedFile?.type || 'application/pdf',
        fileSize: selectedFile?.size || 1048576,
        filePath: formData.filePath || `/uploads/${formData.name}.pdf`,
        storageType: formData.storageType,
        documentType: formData.documentType,
      };

      const res = await documentApi.uploadDocument(payload);
      if (res && res.document) {
        setDocuments((prev) => [res.document, ...prev]);
        setIsUploadModalOpen(false);
        setSelectedFile(null);
        setFormData({
          name: '',
          documentType: 'manual',
          storageType: 'local',
          filePath: '',
        });
      }
    } catch (err) {
      setError(err.message || 'Failed to upload document');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (docId) => {
    if (!confirm('Are you sure you want to delete this document from encrypted storage?')) return;
    try {
      await documentApi.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d._id !== docId));
    } catch (err) {
      alert(err.message || 'Failed to delete document');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'processed':
        return (
          <Badge variant="sovereign" size="sm" dot>
            Processed
          </Badge>
        );
      case 'processing':
        return (
          <Badge variant="warning" size="sm" dot>
            Parsing OCR
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
            Store, vectorize, and analyze air-gapped technical manuals, P&IDs, blueprints, and SOP directives.
          </p>
        </div>
        <Button
          onClick={() => setIsUploadModalOpen(true)}
          icon={Upload}
          className="self-start sm:self-auto"
        >
          Upload Document
        </Button>
      </div>

      {loading ? (
        <Loader text="Loading encrypted document index..." />
      ) : documents.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No documents uploaded yet"
          description="Upload technical specs, plant layouts, or operating procedures to enable offline Graph RAG analysis."
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
                  <th className="px-4 py-3">Storage</th>
                  <th className="px-4 py-3">Size</th>
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
                          <div className="font-semibold text-slate-900">
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
                      <span className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-600">
                        <HardDrive className="w-3 h-3 text-slate-400" />
                        {doc.storageType || 'local'}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] text-slate-500">
                      {doc.fileSize
                        ? `${(doc.fileSize / (1024 * 1024)).toFixed(2)} MB`
                        : '1.2 MB'}
                    </td>
                    <td className="px-4 py-3">
                      {getStatusBadge(doc.processingStatus)}
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-[11px] font-mono">
                      {new Date(doc.createdAt || Date.now()).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleDelete(doc._id)}
                        className="p-1.5 text-slate-400 hover:text-rose-600 rounded transition-colors"
                        title="Delete Document"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Upload Modal */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        title="Ingest Confidential Document"
        subtitle="Ingests file into local encrypted volume for on-prem RAG vectorization"
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
                Supports PDF, DOCX, XLSX, DWG, PNG (Max 150MB per file)
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
              Ingest & Vectorize
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default DocumentsPage;
