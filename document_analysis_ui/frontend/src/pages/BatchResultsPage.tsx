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
                return <CheckCircle className="w-5 h-5 text-green-600" />;
            case 'failed':
                return <XCircle className="w-5 h-5 text-red-600" />;
            case 'processing':
                return <Loader className="w-5 h-5 text-blue-600 animate-spin" />;
            default:
                return <Clock className="w-5 h-5 text-gray-400" />;
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed':
                return 'bg-green-100 text-green-800 border-green-200';
            case 'failed':
                return 'bg-red-100 text-red-800 border-red-200';
            case 'processing':
                return 'bg-blue-100 text-blue-800 border-blue-200';
            default:
                return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    const handleViewResult = (session: BatchSessionInfo) => {
        if (session.result_available) {
            navigate(`/report/${session.session_id}`);
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <Loader className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
                    <p className="text-gray-600">Loading batch status...</p>
                </div>
            </div>
        );
    }

    if (error || !batchStatus) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <XCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
                    <p className="text-red-800">{error || 'Batch not found'}</p>
                    <button
                        onClick={() => navigate('/')}
                        className="mt-4 text-blue-600 hover:text-blue-700"
                    >
                        Return to Home
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <div className="max-w-6xl mx-auto py-8 px-4">
                {/* Header */}
                <div className="mb-6">
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
                    >
                        <ArrowLeft className="w-5 h-5" />
                        Back to Home
                    </button>
                    <h1 className="text-3xl font-bold text-gray-900">Batch Results</h1>
                    <p className="text-gray-600 mt-2">Batch ID: {batchId}</p>
                </div>

                {/* Status Summary */}
                <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Summary</h2>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                        <div className="text-center">
                            <p className="text-3xl font-bold text-gray-900">{batchStatus.total_students}</p>
                            <p className="text-sm text-gray-600">Total Students</p>
                        </div>
                        <div className="text-center">
                            <p className="text-3xl font-bold text-green-600">{batchStatus.completed}</p>
                            <p className="text-sm text-gray-600">Completed</p>
                        </div>
                        <div className="text-center">
                            <p className="text-3xl font-bold text-blue-600">{batchStatus.processing}</p>
                            <p className="text-sm text-gray-600">Processing</p>
                        </div>
                        <div className="text-center">
                            <p className="text-3xl font-bold text-red-600">{batchStatus.failed}</p>
                            <p className="text-sm text-gray-600">Failed</p>
                        </div>
                        <div className="text-center">
                            <p className="text-3xl font-bold text-gray-600">{batchStatus.created}</p>
                            <p className="text-sm text-gray-600">Pending</p>
                        </div>
                    </div>
                </div>

                {/* Student List */}
                <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <h2 className="text-xl font-semibold text-gray-900">Students</h2>
                    </div>
                    <div className="divide-y divide-gray-200">
                        {batchStatus.sessions.map((session) => (
                            <div
                                key={session.session_id}
                                className="px-6 py-4 hover:bg-gray-50 transition-colors"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4 flex-1">
                                        {getStatusIcon(session.status)}
                                        <div>
                                            <h3 className="font-medium text-gray-900">{session.student_name}</h3>
                                            <p className="text-sm text-gray-500">
                                                {session.total_files} file{session.total_files !== 1 ? 's' : ''} uploaded
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <span
                                            className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(
                                                session.status
                                            )}`}
                                        >
                                            {session.status}
                                        </span>

                                        {/* Actions */}
                                        <div className="flex items-center gap-2">
                                            {(session.status === 'processing' || session.status === 'uploading') && (
                                                <>
                                                    <button
                                                        onClick={() => navigate(`/processing/${session.session_id}`)}
                                                        className="px-4 py-2 bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 transition-colors text-sm font-medium"
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
                                                        className="px-4 py-2 bg-red-50 text-red-600 rounded-md hover:bg-red-100 transition-colors text-sm font-medium"
                                                    >
                                                        Cancel
                                                    </button>
                                                </>
                                            )}

                                            {session.status === 'failed' && (
                                                <button
                                                    onClick={() => navigate(`/processing/${session.session_id}`)}
                                                    className="px-4 py-2 bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200 transition-colors text-sm font-medium"
                                                >
                                                    View Error
                                                </button>
                                            )}

                                            {session.result_available && (
                                                <button
                                                    onClick={() => handleViewResult(session)}
                                                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
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
                    <div className="mt-4 text-center text-sm text-gray-500">
                        <Loader className="w-4 h-4 inline-block animate-spin mr-2" />
                        Auto-refreshing every 5 seconds...
                    </div>
                )}
            </div>
        </div>
    );
}
