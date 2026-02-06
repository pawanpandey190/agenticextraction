import { useState } from 'react';
import { DropZone } from './DropZone';
import { FileList } from './FileList';

interface DocumentUploadProps {
  uploadedFiles: string[];
  onUpload: (files: File[]) => Promise<void>;
  onDelete: (filename: string) => Promise<void>;
  onStartAnalysis: () => void;
  isLoading: boolean;
  financialThreshold: number;
  onThresholdChange: (value: number) => void;
}

export function DocumentUpload({
  uploadedFiles,
  onUpload,
  onDelete,
  onStartAnalysis,
  isLoading,
  financialThreshold,
  onThresholdChange,
}: DocumentUploadProps) {
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);

  const handleDrop = (files: File[]) => {
    setPendingFiles((prev) => [...prev, ...files]);
  };

  const handleUpload = async () => {
    if (pendingFiles.length === 0) return;
    await onUpload(pendingFiles);
    setPendingFiles([]);
  };

  const handleRemovePending = (index: number) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const canStartAnalysis = uploadedFiles.length > 0 && !isLoading;

  return (
    <div className="space-y-6">
      {/* Drop zone */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">Upload Documents</h3>
        <DropZone onDrop={handleDrop} disabled={isLoading} />
      </div>

      {/* Pending files */}
      {pendingFiles.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-yellow-800 mb-2">
            Pending upload ({pendingFiles.length} files)
          </h4>
          <ul className="space-y-1 mb-3">
            {pendingFiles.map((file, index) => (
              <li key={index} className="flex items-center justify-between text-sm">
                <span className="text-yellow-700">{file.name}</span>
                <button
                  onClick={() => handleRemovePending(index)}
                  className="text-yellow-600 hover:text-yellow-800"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
          <button
            onClick={handleUpload}
            disabled={isLoading}
            className="w-full py-2 px-4 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50"
          >
            {isLoading ? 'Uploading...' : 'Upload Files'}
          </button>
        </div>
      )}

      {/* Uploaded files */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">
          Uploaded Files ({uploadedFiles.length})
        </h3>
        <div className="border rounded-lg">
          <FileList
            files={uploadedFiles}
            onDelete={onDelete}
            showDelete={!isLoading}
          />
        </div>
      </div>

      {/* Configuration */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-lg font-medium text-gray-900 mb-3">Configuration</h3>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Financial Worthiness Threshold (EUR)
          </label>
          <input
            type="number"
            value={financialThreshold}
            onChange={(e) => onThresholdChange(Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            min={0}
            step={1000}
          />
          <p className="mt-1 text-sm text-gray-500">
            Documents with amounts above this threshold will be marked as financially worthy
          </p>
        </div>
      </div>

      {/* Start Analysis button */}
      <button
        onClick={onStartAnalysis}
        disabled={!canStartAnalysis}
        className={`
          w-full py-3 px-6 text-lg font-medium rounded-lg transition-colors
          ${canStartAnalysis
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }
        `}
      >
        Start Analysis
      </button>
    </div>
  );
}
