import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import { Mail, Lock, User, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react';

const SignupPage: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await api.register(email, password, fullName);
            setSuccess(true);
            setTimeout(() => navigate('/login'), 2000);
        } catch (err: any) {
            setError(err.message || 'Registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 mesh-gradient px-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Create Account</h1>
                    <p className="text-slate-500 mt-2">Join our premium document analysis platform</p>
                </div>

                <div className="bg-white/80 backdrop-blur-xl border border-white/20 rounded-3xl shadow-2xl p-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
                    {error && (
                        <div className="mb-6 p-4 rounded-2xl bg-red-50 border border-red-100 flex items-start gap-3 text-red-600 animate-shake">
                            <AlertCircle size={20} className="shrink-0 mt-0.5" />
                            <p className="text-sm font-medium">{error}</p>
                        </div>
                    )}

                    {success && (
                        <div className="mb-6 p-4 rounded-2xl bg-green-50 border border-green-100 flex items-start gap-3 text-green-600 border-l-4 border-l-green-500">
                            <CheckCircle2 size={20} className="shrink-0 mt-0.5" />
                            <div>
                                <p className="text-sm font-bold">Account created successfully!</p>
                                <p className="text-xs mt-1">Redirecting you to login...</p>
                            </div>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-sm font-semibold text-slate-700 mb-2 ml-1">Full Name</label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-brand-primary transition-colors">
                                    <User size={18} />
                                </div>
                                <input
                                    type="text"
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
                                    className="w-full pl-11 pr-4 py-3 bg-white border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-primary/10 focus:border-brand-primary outline-none transition-all placeholder:text-slate-400"
                                    placeholder="John Doe"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-slate-700 mb-2 ml-1">Email Address</label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-brand-primary transition-colors">
                                    <Mail size={18} />
                                </div>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-11 pr-4 py-3 bg-white border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-primary/10 focus:border-brand-primary outline-none transition-all placeholder:text-slate-400"
                                    placeholder="name@company.com"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-slate-700 mb-2 ml-1">Password</label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-brand-primary transition-colors">
                                    <Lock size={18} />
                                </div>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-11 pr-4 py-3 bg-white border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-primary/10 focus:border-brand-primary outline-none transition-all placeholder:text-slate-400"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading || success}
                            className="w-full py-4 bg-brand-primary hover:bg-brand-primary/95 text-white rounded-2xl font-bold shadow-lg shadow-brand-primary/25 active:scale-[0.98] transition-all flex items-center justify-center gap-2 group disabled:opacity-70 disabled:pointer-events-none"
                        >
                            {loading ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    Get Started
                                    <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-8 text-center pt-6 border-t border-slate-100">
                        <p className="text-sm text-slate-500 font-medium">
                            Already have an account?{' '}
                            <Link to="/login" className="text-brand-primary hover:text-brand-primary/80 font-bold transition-colors">
                                Sign In
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SignupPage;
