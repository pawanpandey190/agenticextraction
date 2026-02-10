import type { AnalysisResult } from '../../services/types';
import { GlassCard } from '../common/GlassComponents';
import { ShieldCheck, GraduationCap, Calculator, AlertCircle, CheckCircle2, XCircle, Info } from 'lucide-react';
import { motion } from 'framer-motion';

interface SummaryTabProps {
    data: AnalysisResult;
}

export function SummaryTab({ data }: SummaryTabProps) {
    const { passport, education, financial } = data;

    const sections = [
        {
            id: 'passport',
            title: 'Identity Verification',
            subtitle: 'Biometric & Document Integrity',
            icon: <ShieldCheck className="w-5 h-5" />,
            remarks: passport?.remarks,
            status: (passport?.accuracy_score ?? 0) >= 70 ? 'VERIFIED' : 'REVIEW_REQUIRED',
            isValid: (passport?.accuracy_score ?? 0) >= 70,
            color: (passport?.accuracy_score ?? 0) >= 70 ? 'text-brand-secondary border-brand-secondary/30 bg-brand-secondary/5' : 'text-amber-600 border-amber-200 bg-amber-50',
        },
        {
            id: 'education',
            title: 'Academic Standing',
            subtitle: 'Credential Equivalence Audit',
            icon: <GraduationCap className="w-5 h-5" />,
            remarks: education?.remarks,
            status: education?.validation_status === 'PASS' ? 'ELIGIBLE' : education?.validation_status === 'FAIL' ? 'INELIGIBLE' : 'PENDING',
            isValid: education?.validation_status === 'PASS',
            color: education?.validation_status === 'PASS' ? 'text-brand-secondary border-brand-secondary/30 bg-brand-secondary/5' : education?.validation_status === 'FAIL' ? 'text-red-600 border-red-200 bg-red-50' : 'text-slate-400 border-slate-200 bg-slate-50',
        },
        {
            id: 'financial',
            title: 'Financial Solvency',
            subtitle: 'Asset & Liquidity Analysis',
            icon: <Calculator className="w-5 h-5" />,
            remarks: financial?.remarks,
            status: financial?.worthiness_status === 'PASS' ? 'SOLVENT' : financial?.worthiness_status === 'FAIL' ? 'INSUFFICIENT' : 'PENDING',
            isValid: financial?.worthiness_status === 'PASS',
            color: financial?.worthiness_status === 'PASS' ? 'text-brand-secondary border-brand-secondary/30 bg-brand-secondary/5' : financial?.worthiness_status === 'FAIL' ? 'text-red-600 border-red-200 bg-red-50' : 'text-slate-400 border-slate-200 bg-slate-50',
        },
    ];

    return (
        <div className="space-y-8">
            {/* Overview Notice */}
            <GlassCard className="p-6 border-brand-primary/10 bg-brand-primary/5 flex items-start gap-4 shadow-sm">
                <div className="p-3 rounded-2xl bg-brand-primary/10 text-brand-primary">
                    <Info className="w-6 h-6" />
                </div>
                <div>
                    <h4 className="text-lg font-black text-slate-900 mb-1">Executive Summary</h4>
                    <p className="text-sm text-slate-500 font-medium leading-relaxed">
                        Consolidated intelligence report synthesizing document authenticity, academic validation, and financial viability for the French Admission Workflow.
                    </p>
                </div>
            </GlassCard>

            {/* Assessment Grid */}
            <div className="grid gap-6">
                {sections.map((section, idx) => (
                    <motion.div
                        key={section.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                    >
                        <GlassCard className="overflow-hidden border-slate-200 hover:border-brand-primary/30 transition-all group shadow-sm hover:shadow-md p-0">
                            <div className="px-8 py-5 border-b border-slate-100 bg-slate-50/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
                                <div className="flex items-center gap-4">
                                    <div className="p-3 rounded-2xl bg-white text-brand-primary border border-slate-200 group-hover:scale-105 transition-transform shadow-sm">
                                        {section.icon}
                                    </div>
                                    <div>
                                        <h3 className="text-base font-black text-slate-900 group-hover:text-brand-primary transition-colors tracking-tight">{section.title}</h3>
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{section.subtitle}</p>
                                    </div>
                                </div>
                                <div className={`flex items-center gap-2 px-4 py-1.5 rounded-full border text-[10px] font-black uppercase tracking-[0.1em] ${section.color}`}>
                                    {section.isValid ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                                    {section.status}
                                </div>
                            </div>
                            <div className="p-8">
                                {section.remarks ? (
                                    <p className="text-slate-600 leading-relaxed text-sm whitespace-pre-wrap italic font-medium">
                                        "{section.remarks}"
                                    </p>
                                ) : (
                                    <div className="flex items-center gap-2 text-slate-500 text-sm italic">
                                        <AlertCircle className="w-4 h-4" />
                                        No auditor remarks available.
                                    </div>
                                )}
                            </div>
                        </GlassCard>
                    </motion.div>
                ))}
            </div>
        </div>
    );
}
