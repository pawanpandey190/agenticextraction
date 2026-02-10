import { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface GlassCardProps {
    children: ReactNode;
    className?: string;
    animate?: boolean;
}

export function GlassCard({ children, className, animate = true }: GlassCardProps) {
    if (animate) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className={cn("glass-card p-6", className)}
            >
                {children}
            </motion.div>
        );
    }

    return (
        <div className={cn("glass-card p-6", className)}>
            {children}
        </div>
    );
}

interface GlassButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'outline' | 'glass';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
    icon?: ReactNode;
}

export function GlassButton({
    children,
    className,
    variant = 'primary',
    size = 'md',
    isLoading,
    icon,
    ...props
}: GlassButtonProps) {
    const variants = {
        primary: "bg-brand-primary text-white hover:bg-brand-primary/90 shadow-sm border border-brand-primary",
        secondary: "bg-brand-secondary text-white hover:bg-brand-secondary/90 shadow-sm border border-brand-secondary",
        outline: "border border-slate-200 bg-white hover:bg-slate-50 text-slate-700",
        glass: "bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200",
    };

    const sizes = {
        sm: "px-3 py-1.5 text-xs font-bold",
        md: "px-4 py-2 text-sm font-semibold",
        lg: "px-6 py-3 text-base font-bold uppercase tracking-wider",
    };

    return (
        <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            className={cn(
                "inline-flex items-center justify-center rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed",
                variants[variant],
                sizes[size],
                className
            )}
            disabled={isLoading}
            {...(props as any)}
        >
            {isLoading ? (
                <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
            ) : icon ? <span className="mr-2">{icon}</span> : null}
            {children}
        </motion.button>
    );
}

interface GlassInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
}

export function GlassInput({ label, error, className, ...props }: GlassInputProps) {
    return (
        <div className="space-y-1.5">
            {label && <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">{label}</label>}
            <input
                className={cn("glass-input w-full text-slate-900 placeholder:text-slate-400", error && "border-red-500/50 focus:ring-red-500/20", className)}
                {...props}
            />
            {error && <p className="text-xs text-red-500 mt-1 ml-1 font-medium">{error}</p>}
        </div>
    );
}
