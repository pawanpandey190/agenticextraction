import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import type { Session } from '../services/types';
import { Clock, CheckCircle, XCircle, Loader2, ChevronRight, Search, FileText, Download, Trash2, ArrowLeft } from 'lucide-react';

export function HistoryPage() {
    const [sessions, setSessions] = useState<Session[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [dateQuery, setDateQuery] = useState('');
    const [isDeleting, setIsDeleting] = useState<string | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchSessions = async () => {
            try {
                const data = await api.listSessions();
                // api already returns sorted sessions, but let's be sure
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

    const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation();
        if (!window.confirm('Are you sure you want to delete this session and all its documents? This action cannot be undone.')) {
            return;
        }

        setIsDeleting(sessionId);
        try {
            await api.deleteSession(sessionId);
            setSessions(prev => prev.filter(s => s.id !== sessionId));
        } catch (e) {
            alert(e instanceof Error ? e.message : 'Failed to delete session');
        } finally {
            setIsDeleting(null);
        }
    };

    const filteredSessions = sessions.filter(s => {
        const matchesSearch = (s.student_name?.toLowerCase() || '').includes(searchQuery.toLowerCase()) ||
            s.id.toLowerCase().includes(searchQuery.toLowerCase());

        const matchesDate = !dateQuery || s.created_at.startsWith(dateQuery);

        return matchesSearch && matchesDate;
    });

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed': return <CheckCircle className="w-5 h-5 text-brand-secondary" />;
            case 'failed': return <XCircle className="w-5 h-5 text-red-500" />;
            case 'processing': return <Loader2 className="w-5 h-5 text-brand-primary animate-spin" />;
            default: return <Clock className="w-5 h-5 text-slate-400" />;
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
                    <Loader2 className="animate-spin h-10 w-10 text-brand-primary mx-auto mb-4 opacity-50" />
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest">Loading History...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div className="space-y-4">
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-2 text-[10px] font-black text-brand-primary uppercase tracking-[0.3em] hover:text-brand-primary/80 transition-all mb-4 group"
                    >
                        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                        Back to Portal
                    </button>
                    <div className="space-y-1">
                        <h1 className="text-2xl font-bold tracking-tight text-slate-800 sm:text-3xl">
                            Analysis History
                        </h1>
                        <p className="text-sm text-slate-500 font-medium max-w-2xl leading-relaxed">
                            Review and download previous analysis results.
                        </p>
                    </div>
                </div>
                <Link
                    to="/"
                    className="inline-flex items-center px-5 py-2.5 bg-brand-primary text-white rounded-xl font-bold uppercase text-[10px] tracking-wider hover:bg-brand-primary/90 transition-all shadow-md shadow-brand-primary/10"
                >
                    New Analysis
                </Link>
            </div>

            {/* Search and Filters */}
            <div className="bg-white p-2 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                <div className="flex-1 flex items-center gap-3 px-4 py-3">
                    <Search className="w-5 h-5 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Search by student name or session ID..."
                        className="flex-1 border-none focus:ring-0 text-sm text-slate-700 bg-transparent outline-none font-medium placeholder:text-slate-300"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>

                <div className="flex items-center gap-3 px-4 py-3 border-t sm:border-t-0 sm:border-l border-slate-100">
                    <Clock className="w-4 h-4 text-slate-400" />
                    <input
                        type="date"
                        className="border-none focus:ring-0 text-sm text-slate-600 bg-transparent outline-none cursor-pointer font-bold"
                        value={dateQuery}
                        onChange={(e) => setDateQuery(e.target.value)}
                    />
                    {dateQuery && (
                        <button
                            onClick={() => setDateQuery('')}
                            className="text-[10px] text-brand-primary font-black hover:text-brand-primary/80 uppercase tracking-widest px-2"
                        >
                            CLEAR
                        </button>
                    )}
                </div>

                <div className="hidden md:flex text-[10px] font-semibold text-slate-400 border-l border-slate-100 pl-4 pr-3 whitespace-nowrap uppercase tracking-wider">
                    {filteredSessions.length} Matches
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-100 text-red-700 px-6 py-4 rounded-2xl flex items-center gap-3 shadow-sm">
                    <XCircle className="w-5 h-5 text-red-500" />
                    <p className="font-medium">{error}</p>
                </div>
            )}

            {/* Sessions List */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                {filteredSessions.length > 0 ? (
                    <div className="divide-y divide-slate-50">
                        {filteredSessions.map((session) => (
                            <div
                                key={session.id}
                                className="group cursor-pointer hover:bg-slate-50 transition-all duration-300"
                                onClick={() => navigate(session.status === 'completed' ? `/report/${session.id}` : `/processing/${session.id}`)}
                            >
                                <div className="p-6 sm:p-8 flex items-center justify-between">
                                    <div className="flex items-center gap-6">
                                        <div className="p-4 bg-slate-50 rounded-2xl group-hover:bg-brand-primary/10 group-hover:scale-110 group-hover:-rotate-2 transition-all duration-500">
                                            <FileText className={`w-8 h-8 ${session.status === 'completed' ? 'text-brand-primary' : 'text-slate-300'}`} />
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-3">
                                                <h3 className="text-base font-bold text-slate-800 tracking-tight">
                                                    {session.student_name || 'Individual Analysis'}
                                                </h3>
                                                <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                                                    {getStatusIcon(session.status)}
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-4 mt-1.5">
                                                <span className="flex items-center gap-1.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                                                    <Clock className="w-3 h-3" />
                                                    {formatDate(session.created_at)}
                                                </span>
                                                <span className="px-2 py-0.5 bg-slate-50 text-slate-400 rounded-lg text-[10px] font-medium tracking-wider">
                                                    ID: {session.id.slice(0, 8)}
                                                </span>
                                                {session.batch_id && (
                                                    <span className="px-2 py-0.5 bg-brand-primary/5 text-brand-primary rounded-lg text-[10px] font-medium tracking-wider">
                                                        Batch Data
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-8">
                                        <div className="text-right hidden sm:block space-y-0.5">
                                            <div className="text-xs font-bold text-slate-800 uppercase tracking-tight">
                                                {session.total_files} Documents
                                            </div>
                                            <div className={`text-[10px] font-medium uppercase tracking-wider ${session.letter_available ? 'text-brand-secondary' : 'text-slate-300'}`}>
                                                {session.letter_available ? 'Report Ready' : 'Processing'}
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-3">
                                            {session.letter_available && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        window.open(api.getLetterDownloadUrl(session.id), '_blank');
                                                    }}
                                                    className="p-3 text-brand-primary bg-brand-primary/5 hover:bg-brand-primary/10 rounded-xl transition-all hover:scale-110 active:scale-90"
                                                    title="Download Admission Letter"
                                                >
                                                    <Download className="w-5 h-5" />
                                                </button>
                                            )}

                                            <button
                                                onClick={(e) => handleDelete(e, session.id)}
                                                disabled={isDeleting === session.id}
                                                className="p-3 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all disabled:opacity-50 hover:scale-110 active:scale-90"
                                                title="Delete Analysis"
                                            >
                                                {isDeleting === session.id ? (
                                                    <Loader2 className="w-5 h-5 animate-spin" />
                                                ) : (
                                                    <Trash2 className="w-5 h-5" />
                                                )}
                                            </button>

                                            <div className="ml-2 w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center group-hover:bg-brand-primary group-hover:text-white transition-all duration-500">
                                                <ChevronRight className="w-5 h-5" />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-32">
                        <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-8 border border-slate-100">
                            <Clock className="w-8 h-8 text-slate-200" />
                        </div>
                        <h3 className="text-xl font-bold text-slate-800 tracking-tight">No history found</h3>
                        <p className="text-slate-400 font-medium mt-2">Analyzed documents will appear here.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
