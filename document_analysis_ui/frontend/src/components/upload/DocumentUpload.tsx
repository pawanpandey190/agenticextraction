import { useState } from 'react';
import { Upload, X, Play, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { GlassCard, GlassButton, GlassInput } from '../common/GlassComponents';
import { motion, AnimatePresence } from 'framer-motion';

interface DocumentUploadProps {
  uploadedFiles: string[];
  onUpload: (files: File[]) => void;
  onDelete: (filename: string) => void;
  onStartAnalysis: () => void;
  isLoading: boolean;
  financialThreshold: number;
  onThresholdChange: (value: number) => void;
  bankStatementPeriod: number;
  onPeriodChange: (value: number) => void;
}

export function DocumentUpload({
  uploadedFiles,
  onUpload,
  onDelete,
  onStartAnalysis,
  isLoading,
  financialThreshold,
  onThresholdChange,
  bankStatementPeriod,
  onPeriodChange,
}: DocumentUploadProps) {
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    setPendingFiles((prev) => [...prev, ...files]);
  };

  const removePendingFile = (index: number) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (pendingFiles.length === 0) return;
    await onUpload(pendingFiles);
    setPendingFiles([]);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Configuration Panel */}
      <div className="lg:col-span-1 space-y-6">
        <GlassCard className="h-full border-slate-200 shadow-sm bg-white">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-brand-primary/10">
              <Upload className="w-5 h-5 text-brand-primary" />
            </div>
            <h3 className="text-xl font-black text-slate-900 tracking-tight uppercase">Control Hub</h3>
          </div>

          <div className="space-y-6">
            <GlassInput
              label="Financial Threshold (EUR)"
              type="number"
              value={financialThreshold}
              onChange={(e) => onThresholdChange(Number(e.target.value))}
              min={0}
              step={1000}
              disabled={isLoading}
              placeholder="e.g. 15000"
            />

            <GlassInput
              label="Bank Statement Period (Months)"
              type="number"
              value={bankStatementPeriod}
              onChange={(e) => onPeriodChange(Number(e.target.value))}
              min={1}
              max={12}
              step={1}
              disabled={isLoading}
              placeholder="e.g. 3"
            />

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
              <div className="flex items-center gap-2 text-brand-primary/60">
                <AlertCircle className="w-4 h-4" />
                <span className="text-[10px] font-black uppercase tracking-widest">Global Policy</span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed font-medium">
                Statements covering less than {bankStatementPeriod} months or totals below €{financialThreshold.toLocaleString()} will be flagged for review.
              </p>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Upload Area */}
      <div className="lg:col-span-2 space-y-8">
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={onDrop}
          className="relative group"
        >
          <div className="absolute -inset-1 bg-gradient-to-r from-brand-primary/20 to-brand-accent/20 rounded-[2rem] blur opacity-25 group-hover:opacity-100 transition duration-1000 group-hover:duration-200"></div>
          <div className="relative bg-white border-2 border-dashed border-slate-200 rounded-[2rem] p-16 text-center hover:border-brand-primary hover:shadow-2xl hover:shadow-brand-primary/5 transition-all cursor-pointer">
            <input
              type="file"
              multiple
              onChange={(e) => {
                const files = e.target.files ? Array.from(e.target.files) : [];
                setPendingFiles((prev) => [...prev, ...files]);
              }}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="flex flex-col items-center">
              <div className="w-24 h-24 mb-6 rounded-3xl bg-slate-50 flex items-center justify-center group-hover:scale-105 group-hover:bg-brand-primary/5 group-hover:rotate-3 transition-all">
                <Upload className="w-10 h-10 text-slate-400 group-hover:text-brand-primary" />
              </div>
              <p className="text-2xl font-black text-slate-900 mb-2 tracking-tight">Ingest Documents</p>
              <p className="text-slate-400 font-medium">Drop files or click to initiate upload (PDF, PNG, JPG)</p>
            </div>
          </div>
        </div>

        {/* Pending Files List */}
        <AnimatePresence>
          {pendingFiles.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="space-y-4"
            >
              <div className="flex items-center justify-between">
                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] px-2 italic">Awaiting Transmission ({pendingFiles.length})</h4>
                <GlassButton size="sm" onClick={handleUpload} isLoading={isLoading}>
                  Upload Files
                </GlassButton>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {pendingFiles.map((file, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center justify-between p-4 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center space-x-3 truncate">
                      <div className="p-2 rounded-lg bg-brand-primary/10 text-brand-primary">
                        <FileText className="w-4 h-4 shrink-0" />
                      </div>
                      <span className="text-sm text-slate-900 font-bold truncate">{file.name}</span>
                    </div>
                    <button
                      onClick={() => removePendingFile(index)}
                      className="p-1 hover:bg-red-50 rounded-lg text-slate-400 hover:text-red-500 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Uploaded Files */}
        {uploadedFiles.length > 0 && (
          <div className="space-y-4">
            <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] px-2 italic">Secured in Pipeline</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {uploadedFiles.map((filename) => (
                <div key={filename} className="flex items-center justify-between p-4 bg-white border border-brand-secondary/20 rounded-xl shadow-sm border-l-4 border-brand-secondary">
                  <div className="flex items-center space-x-3 truncate">
                    <CheckCircle2 className="w-4 h-4 text-brand-secondary shrink-0" />
                    <span className="text-sm text-slate-900 font-bold truncate">{filename}</span>
                  </div>
                  <button
                    onClick={() => onDelete(filename)}
                    className="p-1 hover:bg-red-50 rounded-lg text-slate-400 hover:text-red-500 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Bar */}
        <div className="flex justify-end pt-4">
          <GlassButton
            onClick={onStartAnalysis}
            disabled={uploadedFiles.length === 0 || isLoading}
            size="lg"
            variant="secondary"
            className="w-full md:w-auto min-w-[200px]"
            icon={<Play className="w-5 h-5" />}
          >
            Start Analysis Pipeline
          </GlassButton>
        </div>
      </div>
    </div>
  );
}
