import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import type { Session } from '../services/types';
import { Clock, CheckCircle, XCircle, Loader2, ChevronRight, Search, FileText, Download } from 'lucide-react';

export function HistoryPage() {
    const [sessions, setSessions] = useState<Session[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchSessions = async () => {
            try {
                const data = await api.listSessions();
                // Sort by created_at descending
                const sorted = [...data].sort((a, b) =>
                    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                );
                setSessions(sorted);
            } catch (e) {
                setError(e instanceof Error ? e.message : 'Failed to load session history');
            } finally {
                setIsLoading(false);
            }
        };

        fetchSessions();
    }, []);

    const filteredSessions = sessions.filter(s =>
        (s.student_name?.toLowerCase() || '').includes(searchQuery.toLowerCase()) ||
        s.id.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed': return <CheckCircle className="w-5 h-5 text-green-500" />;
            case 'failed': return <XCircle className="w-5 h-5 text-red-500" />;
            case 'processing': return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
            default: return <Clock className="w-5 h-5 text-gray-400" />;
        }
    };

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleString(undefined, {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                    <Loader2 className="animate-spin h-10 w-10 text-blue-500 mx-auto" />
                    <p className="mt-3 text-gray-500">Loading history...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Session History</h1>
                    <p className="text-gray-500 mt-1">Review and download previous analysis results</p>
                </div>
                <Link
                    to="/"
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors shadow-sm"
                >
                    New Analysis
                </Link>
            </div>

            {/* Search and Filters */}
            <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center gap-3">
                <Search className="w-5 h-5 text-gray-400" />
                <input
                    type="text"
                    placeholder="Search by student name or session ID..."
                    className="flex-1 border-none focus:ring-0 text-gray-700"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
                <div className="text-sm text-gray-400 border-l pl-3">
                    {filteredSessions.length} sessions found
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-3">
                    <XCircle className="w-5 h-5" />
                    <p>{error}</p>
                </div>
            )}

            {/* Sessions List */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                {filteredSessions.length > 0 ? (
                    <div className="divide-y divide-gray-100">
                        {filteredSessions.map((session) => (
                            <div
                                key={session.id}
                                className="hover:bg-gray-50 transition-colors group cursor-pointer"
                                onClick={() => navigate(session.status === 'completed' ? `/report/${session.id}` : `/processing/${session.id}`)}
                            >
                                <div className="p-4 sm:p-6 flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="p-3 bg-gray-100 rounded-lg group-hover:bg-blue-50 transition-colors">
                                            <FileText className={`w-6 h-6 ${session.status === 'completed' ? 'text-blue-600' : 'text-gray-400'}`} />
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <h3 className="font-semibold text-gray-900">
                                                    {session.student_name || 'Individual Analysis'}
                                                </h3>
                                                {getStatusIcon(session.status)}
                                            </div>
                                            <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
                                                <span className="flex items-center gap-1">
                                                    <Clock className="w-3 h-3" />
                                                    {formatDate(session.created_at)}
                                                </span>
                                                <span className="px-2 py-0.5 bg-gray-100 rounded-full text-xs font-mono">
                                                    {session.id.slice(0, 8)}...
                                                </span>
                                                {session.batch_id && (
                                                    <span className="px-2 py-0.5 bg-purple-50 text-purple-600 rounded-full text-xs font-medium">
                                                        Part of Batch
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-4">
                                        <div className="text-right hidden sm:block">
                                            <div className="text-sm font-medium text-gray-900">
                                                {session.total_files} Documents
                                            </div>
                                            <div className="text-xs text-gray-500">
                                                {session.letter_available ? 'Letter Generated' : 'No Letter'}
                                            </div>
                                        </div>
                                        {session.letter_available && (
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    window.open(api.getLetterDownloadUrl(session.id), '_blank');
                                                }}
                                                className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                                title="Download Admission Letter"
                                            >
                                                <Download className="w-5 h-5" />
                                            </button>
                                        )}
                                        <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-blue-500 transition-colors" />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-16">
                        <Clock className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900">No sessions found</h3>
                        <p className="text-gray-500 mt-1">Start your first document analysis to see history here.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
