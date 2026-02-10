import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderUpload } from '../components/upload/FolderUpload';
import { api } from '../services/api';
import { ArrowLeft, Upload, AlertCircle } from 'lucide-react';

export function BatchUploadPage() {
    const navigate = useNavigate();
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [financialThreshold, setFinancialThreshold] = useState(15000);
    const [bankStatementPeriod, setBankStatementPeriod] = useState(3);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleFilesSelected = (files: File[]) => {
        setSelectedFiles(files);
        setError(null);
    };

    const handleUpload = async () => {
        if (selectedFiles.length === 0) {
            setError('Please select student folders first');
            return;
        }

        setIsUploading(true);
        setError(null);

        try {
            // Step 1: Upload batch folders
            const response = await api.uploadBatchFolders(selectedFiles, financialThreshold, bankStatementPeriod);

            // Step 2: Automatically start processing for each student
            const processingPromises = response.sessions.map(async (session) => {
                try {
                    await api.startProcessing(session.session_id);
                } catch (err) {
                    console.error(`Failed to start processing for ${session.student_name}:`, err);
                }
            });

            // Wait for all processing to start
            await Promise.all(processingPromises);

            // Navigate to batch results page
            navigate(`/batch/${response.batch_id}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Upload failed');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="max-w-5xl mx-auto py-12 px-4 space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div className="space-y-4">
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-2 text-[10px] font-black text-brand-primary uppercase tracking-[0.3em] hover:text-brand-primary/80 transition-all mb-4 group"
                    >
                        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                        Back to Portal
                    </button>
                    <h1 className="text-4xl font-black tracking-tight text-slate-900 sm:text-6xl flex flex-col">
                        <span className="text-brand-primary opacity-50 uppercase text-xs tracking-[0.4em] font-black mb-2 px-1">Mass Ingestion</span>
                        Batch <span className="text-brand-primary">Upload</span>
                    </h1>
                    <p className="text-lg text-slate-500 font-medium max-w-2xl leading-relaxed">
                        Securely pipeline multiple student directories for parallel automated analysis.
                    </p>
                </div>
            </div>

            {/* Protocol Instructions */}
            <div className="bg-white border border-slate-200 rounded-[2rem] p-8 shadow-xl shadow-slate-200/50">
                <div className="flex items-start gap-4">
                    <div className="p-3 bg-brand-primary/10 rounded-2xl">
                        <AlertCircle className="w-6 h-6 text-brand-primary flex-shrink-0" />
                    </div>
                    <div className="flex-1">
                        <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest mb-4">Ingestion Protocol</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <ol className="text-sm text-slate-600 space-y-4 list-decimal list-inside font-medium leading-relaxed">
                                <li>
                                    <strong className="text-slate-900">Structure Matrix:</strong> Create a primary directory (e.g., "Batch_Queue") with sub-directories per student.
                                </li>
                                <li>
                                    <strong className="text-slate-900">Define Scope:</strong> Target the <strong>primary directory</strong> when prompted in the ingestion area below.
                                </li>
                                <li>
                                    <strong className="text-slate-900">Verify Mapping:</strong> Ensure all student nodes are correctly mapped by the system.
                                </li>
                                <li>
                                    <strong className="text-slate-900">Execute:</strong> Click "Initiate Batch Pipeline" to begin automated processing.
                                </li>
                            </ol>
                            <div className="p-4 bg-slate-900 rounded-3xl border border-slate-800 shadow-2xl">
                                <p className="text-[10px] text-brand-primary font-mono leading-loose">
                                    <span className="opacity-50 text-slate-500">ROOT/</span> Batch_Upload/ <span className="text-slate-400">← INGEST THIS</span><br />
                                    <span className="opacity-30 text-slate-600">├──</span> John_Doe/<br />
                                    <span className="opacity-30 text-slate-600">│&nbsp;&nbsp;&nbsp;├──</span> passport.pdf<br />
                                    <span className="opacity-30 text-slate-600">│&nbsp;&nbsp;&nbsp;└──</span> degree.pdf<br />
                                    <span className="opacity-30 text-slate-600">└──</span> Jane_Smith/<br />
                                    &nbsp;&nbsp;&nbsp;&nbsp;<span className="opacity-30 text-slate-600">├──</span> passport.pdf<br />
                                    &nbsp;&nbsp;&nbsp;&nbsp;<span className="opacity-30 text-slate-600">└──</span> degree.pdf
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="bg-red-50 border border-red-100 rounded-2xl p-5 flex items-center gap-3 shadow-sm">
                    <div className="p-1 rounded-lg bg-red-100/50">
                        <AlertCircle className="w-5 h-5 text-red-600" />
                    </div>
                    <p className="text-red-700 font-medium text-sm">{error}</p>
                </div>
            )}

            {/* Ingestion Matrix */}
            <div className="bg-white rounded-[2rem] border border-slate-200 shadow-sm p-2 overflow-hidden">
                <FolderUpload
                    onFilesSelected={handleFilesSelected}
                    disabled={isUploading}
                />
            </div>

            {/* Configuration Interface */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="bg-white rounded-[2rem] border border-slate-200 shadow-sm p-8 space-y-6">
                    <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest italic mb-2">Threshold Config</h3>
                    <div>
                        <label className="block text-xs font-black text-slate-500 uppercase tracking-widest mb-3 px-1">
                            Financial Magnitude (EUR)
                        </label>
                        <input
                            type="number"
                            value={financialThreshold}
                            onChange={(e) => setFinancialThreshold(Number(e.target.value))}
                            className="w-full px-5 py-4 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-2 focus:ring-brand-primary/20 text-slate-900 font-bold font-mono transition-all"
                            min={0}
                            step={1000}
                            disabled={isUploading}
                        />
                        <p className="mt-4 text-xs text-slate-400 font-medium leading-relaxed italic">
                            Students exceeding this liquidity ceiling will satisfy financial requirements.
                        </p>
                    </div>
                </div>

                <div className="bg-white rounded-[2rem] border border-slate-200 shadow-sm p-8 space-y-6">
                    <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest italic mb-2">Temporal Logic</h3>
                    <div>
                        <label className="block text-xs font-black text-slate-500 uppercase tracking-widest mb-3 px-1">
                            Minimal Period (Months)
                        </label>
                        <input
                            type="number"
                            value={bankStatementPeriod}
                            onChange={(e) => setBankStatementPeriod(Number(e.target.value))}
                            className="w-full px-5 py-4 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-2 focus:ring-brand-primary/20 text-slate-900 font-bold font-mono transition-all"
                            min={1}
                            max={12}
                            step={1}
                            disabled={isUploading}
                        />
                        <p className="mt-4 text-xs text-slate-400 font-medium leading-relaxed italic">
                            Required temporal breadth for bank records to achieve verification integrity.
                        </p>
                    </div>
                </div>
            </div>

            {/* Action Bar */}
            <div className="space-y-4">
                <button
                    onClick={handleUpload}
                    disabled={selectedFiles.length === 0 || isUploading}
                    className={`
                        w-full py-6 px-8 text-xs font-black uppercase tracking-[0.3em] rounded-2xl transition-all flex items-center justify-center gap-3 shadow-2xl
                        ${selectedFiles.length > 0 && !isUploading
                            ? 'bg-brand-primary text-white hover:bg-brand-primary/90 shadow-brand-primary/20 hover:scale-[1.02] active:scale-95'
                            : 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
                        }
                    `}
                >
                    <Upload className="w-5 h-5" />
                    {isUploading ? 'Executing Mass Pipeline...' : 'Initiate Batch Pipeline'}
                </button>

                <div className="flex items-center justify-center gap-2 p-4 bg-emerald-50 border border-emerald-100 rounded-2xl">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <p className="text-[10px] font-black text-emerald-800 uppercase tracking-widest">
                        Autonomous Processing Engaged: All nodes will auto-initiate post-ingestion
                    </p>
                </div>
            </div>
        </div>
    );
}
