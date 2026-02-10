import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import type { BatchStatusResponse, BatchSessionInfo } from '../services/types';
import { ArrowLeft, CheckCircle, XCircle, Clock, Loader, FileText } from 'lucide-react';

export function BatchResultsPage() {
    const { batchId } = useParams<{ batchId: string }>();
    const navigate = useNavigate();
    const [batchStatus, setBatchStatus] = useState<BatchStatusResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!batchId) return;

        const fetchBatchStatus = async (showLoading = false) => {
            if (showLoading) setIsLoading(true);
            try {
                const status = await api.getBatchStatus(batchId);
                setBatchStatus(prev => {
                    // Only update if status changed to prevent redundant renders 
                    // (although React does this for primitives, batchStatus is an object)
                    return JSON.stringify(prev) === JSON.stringify(status) ? prev : status;
                });
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load batch status');
            } finally {
                setIsLoading(false);
            }
        };

        fetchBatchStatus(true);

        // Poll for updates every 5 seconds
        const interval = setInterval(() => {
            // We use the functional update pattern or just call fetch
            // But we need to know if we should continue polling
            api.getBatchStatus(batchId).then(status => {
                setBatchStatus(prev => {
                    return JSON.stringify(prev) === JSON.stringify(status) ? prev : status;
                });
            }).catch(err => {
                console.error("Polling error:", err);
            });
        }, 5000);

        return () => clearInterval(interval);
    }, [batchId, navigate]);

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed':
                return <CheckCircle className="w-5 h-5 text-brand-secondary" />;
            case 'failed':
                return <XCircle className="w-5 h-5 text-red-500" />;
            case 'processing':
                return <Loader className="w-5 h-5 text-brand-primary animate-spin" />;
            default:
                return <Clock className="w-5 h-5 text-slate-400" />;
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed':
                return 'bg-emerald-50 text-emerald-700 border-emerald-100';
            case 'failed':
                return 'bg-red-50 text-red-700 border-red-100';
            case 'processing':
                return 'bg-brand-primary/5 text-brand-primary border-brand-primary/10';
            default:
                return 'bg-slate-50 text-slate-600 border-slate-100';
        }
    };

    const handleViewResult = (session: BatchSessionInfo) => {
        if (session.result_available) {
            navigate(`/report/${session.session_id}`);
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <div className="text-center">
                    <Loader className="w-12 h-12 text-brand-primary animate-spin mx-auto mb-6 opacity-30" />
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">Synching Batch Data...</p>
                </div>
            </div>
        );
    }

    if (error || !batchStatus) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
                <div className="bg-white border border-red-100 rounded-[2rem] p-12 text-center shadow-xl max-w-md w-full">
                    <XCircle className="w-16 h-16 text-red-400 mx-auto mb-6 opacity-50" />
                    <h3 className="text-xl font-black text-slate-900 uppercase tracking-tight mb-2">Matrix Failure</h3>
                    <p className="text-red-600 font-medium text-sm leading-relaxed mb-8">{error || 'Batch not found'}</p>
                    <button
                        onClick={() => navigate('/')}
                        className="px-8 py-3 bg-slate-900 text-white rounded-xl font-black uppercase text-[10px] tracking-widest hover:bg-slate-800 transition-all shadow-xl shadow-slate-900/10"
                    >
                        Return to Hub
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto py-12 px-4 space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
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
                    <h1 className="text-3xl font-bold tracking-tight text-slate-800 sm:text-4xl">
                        Batch <span className="text-brand-primary">Results</span>
                    </h1>
                    <p className="text-sm font-medium text-slate-500 uppercase tracking-wider px-1">Batch ID: {batchId}</p>
                </div>
            </div>

            {/* Status Summary */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-8">Summary</h2>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
                    <div className="space-y-1">
                        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total</p>
                        <p className="text-3xl font-bold text-slate-800 tracking-tight">{batchStatus.total_students}</p>
                    </div>
                    <div className="space-y-1">
                        <p className="text-xs font-semibold text-emerald-600/70 uppercase tracking-wider">Completed</p>
                        <p className="text-3xl font-bold text-brand-secondary tracking-tight">{batchStatus.completed}</p>
                    </div>
                    <div className="space-y-1">
                        <p className="text-xs font-semibold text-brand-primary/70 uppercase tracking-wider">Processing</p>
                        <p className="text-3xl font-bold text-brand-primary tracking-tight">{batchStatus.processing}</p>
                    </div>
                    <div className="space-y-1">
                        <p className="text-xs font-semibold text-red-600/70 uppercase tracking-wider">Failed</p>
                        <p className="text-3xl font-bold text-red-500 tracking-tight">{batchStatus.failed}</p>
                    </div>
                    <div className="space-y-1">
                        <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Created</p>
                        <p className="text-3xl font-bold text-slate-300 tracking-tight">{batchStatus.created}</p>
                    </div>
                </div>
            </div>

            {/* Student Matrix */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-8 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/30">
                    <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Documents</h2>
                    <div className="text-xs font-medium text-slate-400">
                        {batchStatus.sessions.length} Students
                    </div>
                </div>
                <div className="divide-y divide-slate-50">
                    {batchStatus.sessions.map((session) => (
                        <div
                            key={session.session_id}
                            className="px-10 py-8 hover:bg-slate-50 transition-all group"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-6 flex-1">
                                    <div className="w-12 h-12 rounded-xl bg-slate-50 flex items-center justify-center group-hover:bg-white group-hover:shadow-md transition-all">
                                        {getStatusIcon(session.status)}
                                    </div>
                                    <div>
                                        <h3 className="text-base font-semibold text-slate-800 tracking-tight">{session.student_name}</h3>
                                        <p className="text-xs text-slate-400 mt-0.5">
                                            {session.total_files} files
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-6">
                                    <span
                                        className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(
                                            session.status
                                        )}`}
                                    >
                                        {session.status}
                                    </span>

                                    {/* Actions */}
                                    <div className="flex items-center gap-2">
                                        {(session.status === 'processing' || session.status === 'uploading') && (
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={() => navigate(`/processing/${session.session_id}`)}
                                                    className="px-4 py-2 bg-brand-primary/5 text-brand-primary rounded-xl hover:bg-brand-primary/10 transition-all text-xs font-semibold uppercase tracking-wider"
                                                >
                                                    View Progress
                                                </button>
                                                <button
                                                    onClick={async () => {
                                                        if (window.confirm(`Are you sure you want to cancel processing for ${session.student_name}?`)) {
                                                            try {
                                                                await api.cancelProcessing(session.session_id);
                                                                // Refresh status
                                                                const status = await api.getBatchStatus(batchId!);
                                                                setBatchStatus(status);
                                                            } catch (err) {
                                                                alert('Failed to cancel: ' + (err instanceof Error ? err.message : String(err)));
                                                            }
                                                        }
                                                    }}
                                                    className="px-4 py-2 bg-red-50 text-red-600 rounded-xl hover:bg-red-100 transition-all text-xs font-semibold uppercase tracking-wider"
                                                >
                                                    Stop
                                                </button>
                                            </div>
                                        )}

                                        {session.status === 'failed' && (
                                            <button
                                                onClick={() => navigate(`/processing/${session.session_id}`)}
                                                className="px-4 py-2 bg-slate-100 text-slate-500 rounded-xl hover:bg-slate-200 transition-all text-xs font-semibold uppercase tracking-wider"
                                            >
                                                View Error
                                            </button>
                                        )}

                                        {session.result_available && (
                                            <button
                                                onClick={() => handleViewResult(session)}
                                                className="flex items-center gap-2 px-6 py-2 bg-brand-primary text-white rounded-xl hover:bg-brand-primary/90 transition-all text-xs font-bold uppercase tracking-wider shadow-md shadow-brand-primary/10"
                                            >
                                                <FileText className="w-4 h-4" />
                                                View Report
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Auto-refresh indicator */}
            {(batchStatus.status === 'processing' || batchStatus.status === 'created') && (
                <div className="mt-8 flex items-center justify-center gap-3">
                    <div className="w-8 h-1 bg-slate-100 rounded-full overflow-hidden">
                        <div className="h-full bg-brand-primary/40 animate-pulse" style={{ width: '100%' }}></div>
                    </div>
                    <p className="text-xs font-medium text-slate-400">Refreshing every 5s</p>
                </div>
            )}
        </div>
    );
}
