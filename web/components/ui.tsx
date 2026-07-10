/**
 * @module ui
 * @description GitHub Primer-faithful UI component library.
 * Colors, spacing, interactions, and animations match GitHub.com exactly.
 */
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertCircle, AlertTriangle, Ban, CheckCircle2, CircleDot,
  Clock, Info, Loader2, SkipForward, X, XCircle,
} from 'lucide-react';
import {
  ButtonHTMLAttributes, createContext, ReactNode,
  SelectHTMLAttributes, useCallback, useContext, useEffect, useRef, useState,
} from 'react';
import { cn, statusTone } from '@/lib/utils';

// ─── Status Icon ────────────────────────────────────────────────────────────

export function StatusIcon({ status, className}: { status: string; className?: string; pulse?: boolean }) {
  const tone = statusTone(status);
  const map: Record<string, { icon: typeof Loader2; color: string; anim: string }> = {
    running:   { icon: Loader2,      color: 'text-attention-fg', anim: 'animate-spin' },
    completed: { icon: CheckCircle2, color: 'text-success-fg',   anim: '' },
    failed:    { icon: XCircle,      color: 'text-danger-fg',    anim: '' },
    stopped:   { icon: Ban,          color: 'text-fg-muted',     anim: '' },
    pending:   { icon: CircleDot,    color: 'text-fg-subtle',    anim: '' },
    skipped:   { icon: SkipForward,  color: 'text-fg-subtle',    anim: '' },
    queued:    { icon: Clock,        color: 'text-fg-subtle',    anim: '' },
  };
  const { icon: Icon, color, anim } = map[tone] ?? { icon: CircleDot, color: 'text-fg-subtle', anim: '' };
  return <Icon className={cn('h-4 w-4 shrink-0', color, anim, className)} aria-hidden="true" />;
}

// ─── Status Badge ────────────────────────────────────────────────────────────

export function StatusBadge({ status}: { status: string; pulse?: boolean }) {
  const tone = statusTone(status);
  const cls: Record<string, string> = {
    running:   'bg-attention-subtle text-attention-fg border-attention-muted/40',
    completed: 'bg-success-subtle  text-success-fg  border-success-muted/40',
    failed:    'bg-danger-subtle   text-danger-fg   border-danger-muted/40',
    stopped:   'bg-neutral-subtle  text-fg-muted    border-border-muted',
    pending:   'bg-neutral-subtle  text-fg-subtle   border-border-muted',
  };
  return (
    <span className={cn(
      'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium capitalize transition-colors',
      cls[tone] ?? 'bg-neutral-subtle text-fg-subtle border-border-muted',
    )}>
      <StatusIcon status={status} className="h-3 w-3" />
      {String(status || 'unknown').replace(/_/g, ' ')}
    </span>
  );
}

// ─── Button ──────────────────────────────────────────────────────────────────

export function Btn({
  children, icon, variant = 'default', size = 'sm', loading, className, ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  icon?: ReactNode;
  variant?: 'default' | 'primary' | 'danger' | 'invisible' | 'outline';
  size?: 'sm' | 'md';
  loading?: boolean;
}) {
  const base = [
    'inline-flex items-center justify-center gap-1.5 rounded-md font-medium',
    'transition-colors duration-150',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-fg focus-visible:ring-offset-2 focus-visible:ring-offset-canvas',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    'select-none',
  ].join(' ');
  const sz = size === 'md' ? 'h-8 px-3 text-sm' : 'h-7 px-2.5 text-xs';
  const v: Record<string, string> = {
    default:   'border border-btn-border bg-btn-bg text-fg hover:bg-btn-hover active:scale-[0.98]',
    primary:   'border border-transparent bg-btn-primaryBg text-fg-onEmphasis hover:bg-btn-primaryHover active:scale-[0.98]',
    danger:    'border border-transparent bg-btn-dangerBg text-fg-onEmphasis hover:opacity-90 active:scale-[0.98]',
    invisible: 'border border-transparent bg-transparent text-fg-muted hover:bg-neutral-subtle hover:text-fg',
    outline:   'border border-border bg-transparent text-fg-muted hover:bg-neutral-subtle hover:text-fg hover:border-fg-muted',
  };
  return (
    <button {...props} disabled={props.disabled || loading} className={cn(base, sz, v[variant], className)}>
      {loading ? <Loader2 className="h-3 w-3 animate-spin" /> : icon && <span className="shrink-0">{icon}</span>}
      {children}
    </button>
  );
}

// ─── Progress Bar ────────────────────────────────────────────────────────────

export function ProgressBar({ value = 0, total = 0, state = 'running' }: { value?: number; total?: number; state?: string }) {
  const pct = total > 0 ? Math.min(100, Math.max(0, (value / total) * 100)) : 0;
  const tone = statusTone(state);
  const barColor = tone === 'failed' ? 'bg-danger-fg' : tone === 'completed' ? 'bg-success-fg' : 'bg-accent-fg';
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-neutral-muted">
      <motion.div
        className={cn('h-full rounded-full', barColor)}
        initial={false}
        animate={{ width: `${pct}%` }}
        transition={{ type: 'spring', stiffness: 120, damping: 22 }}
      />
    </div>
  );
}

// ─── Skeleton ────────────────────────────────────────────────────────────────

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('animate-shimmer rounded', className)} />;
}

export function SkeletonRow({ cols = 3 }: { cols?: number }) {
  return (
    <div className="flex items-center gap-3 border-b border-border px-4 py-3 last:border-0">
      <Skeleton className="h-4 w-4 rounded-full shrink-0" />
      <div className="flex-1 space-y-1.5 min-w-0">
        <Skeleton className="h-3 w-32" />
        <Skeleton className="h-2.5 w-48" />
      </div>
      {cols > 2 && <Skeleton className="h-3 w-16 shrink-0" />}
    </div>
  );
}

export function SkeletonCard({ rows = 5 }: { rows?: number }) {
  return (
    <Card>
      <div className="border-b border-border px-4 py-3">
        <Skeleton className="h-4 w-28" />
      </div>
      {Array.from({ length: rows }).map((_, i) => <SkeletonRow key={i} />)}
    </Card>
  );
}

// ─── Empty State ─────────────────────────────────────────────────────────────

export function EmptyState({
  icon, title, description, action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 py-12 text-center">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-neutral-subtle">
        {icon ?? <AlertCircle className="h-5 w-5 text-fg-subtle" />}
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium text-fg">{title}</p>
        {description && <p className="text-xs text-fg-muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}

// ─── Card ────────────────────────────────────────────────────────────────────

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn('rounded-md border border-border bg-canvas overflow-hidden', className)}>
      {children}
    </div>
  );
}
// ─── Select ──────────────────────────────────────────────────────────────────

export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={cn(
        'h-8 appearance-none rounded-md border border-border bg-canvas-inset pl-2.5 pr-7 text-xs text-fg outline-none',
        'bg-[length:16px_16px] bg-[position:right_4px_center] bg-no-repeat',
        'hover:border-fg-muted focus:border-accent-fg focus:ring-1 focus:ring-accent-fg transition-colors',
        "bg-[url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236e7681' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E\")]",
        className,
      )}
    />
  );
}

// ─── Elapsed timer ──────────────────────────────────────────────────────────

/** Wall-clock elapsed time. Ticks once a second while the run is live, and
 *  freezes at the final duration once it finishes. */
export function Elapsed({ startedAt, finishedAt, className }: { startedAt?: string | null; finishedAt?: string | null; className?: string }) {
  const [now, setNow] = useState(() => Date.now());
  const live = Boolean(startedAt) && !finishedAt;

  useEffect(() => {
    if (!live) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [live]);

  if (!startedAt) return null;
  const start = new Date(startedAt).getTime();
  const end = finishedAt ? new Date(finishedAt).getTime() : now;
  const secs = Math.max(0, Math.round((end - start) / 1000));
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  const text = h ? `${h}h ${m}m ${s}s` : m ? `${m}m ${s}s` : `${s}s`;
  return <span className={cn('tabular-nums', className)}>{text}</span>;
}

export function LiveDot({ className }: { className?: string }) {
  return (
    <span className={cn('relative flex h-2 w-2 shrink-0', className)}>
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success-fg opacity-50" />
      <span className="relative inline-flex h-2 w-2 rounded-full bg-success-fg" />
    </span>
  );
}

// ─── Toast System ────────────────────────────────────────────────────────────

type ToastKind = 'success' | 'error' | 'warning' | 'info';
interface ToastItem { id: string; kind: ToastKind; message: string; duration?: number }

interface ToastCtx {
  toast: (message: string, kind?: ToastKind, duration?: number) => void;
}

const ToastContext = createContext<ToastCtx>({ toast: () => {} });

export function useToast() {
  return useContext(ToastContext).toast;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts(t => t.filter(x => x.id !== id));
  }, []);

  const toast = useCallback((message: string, kind: ToastKind = 'info', duration = 4000) => {
    const id = `${Date.now()}-${Math.random()}`;
    setToasts(t => [...t.slice(-4), { id, kind, message, duration }]);
    if (duration > 0) setTimeout(() => dismiss(id), duration);
  }, [dismiss]);

  const kindCls: Record<ToastKind, string> = {
    success: 'border-success-muted/60 bg-success-subtle text-success-fg',
    error:   'border-danger-muted/60  bg-danger-subtle  text-danger-fg',
    warning: 'border-attention-muted/60 bg-attention-subtle text-attention-fg',
    info:    'border-border bg-canvas-overlay text-fg',
  };
  const kindIcon: Record<ToastKind, typeof CheckCircle2> = {
    success: CheckCircle2,
    error:   XCircle,
    warning: AlertTriangle,
    info:    Info,
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {/* Toast portal */}
      <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex flex-col gap-2" aria-live="polite">
        <AnimatePresence>
          {toasts.map(t => {
            const Icon = kindIcon[t.kind];
            return (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, x: 16, scale: 0.95 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: 16, scale: 0.95 }}
                transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
                className={cn(
                  'pointer-events-auto flex items-start gap-2.5 rounded-md border px-3.5 py-2.5 text-xs font-medium shadow-lg backdrop-blur',
                  'max-w-[340px] min-w-[220px]',
                  kindCls[t.kind],
                )}
              >
                <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span className="flex-1 leading-5">{t.message}</span>
                <button
                  type="button"
                  onClick={() => dismiss(t.id)}
                  className="ml-1 shrink-0 opacity-60 hover:opacity-100 focus-ring"
                  aria-label="Dismiss"
                >
                  <X className="h-3 w-3" />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

// ─── Tooltip ─────────────────────────────────────────────────────────────────

export function Tooltip({ content, children, side = 'top' }: { content: string; children: ReactNode; side?: 'top' | 'bottom' | 'left' | 'right' }) {
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  const positionCls = {
    top:    '-translate-x-1/2 -translate-y-full -top-1.5 left-1/2',
    bottom: '-translate-x-1/2 translate-y-0.5 top-full left-1/2',
    left:   '-translate-x-full -translate-y-1/2 top-1/2 -left-1.5',
    right:  'translate-x-0.5 -translate-y-1/2 top-1/2 left-full',
  }[side];

  return (
    <span
      ref={ref}
      className="relative inline-flex"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      <AnimatePresence>
        {visible && (
          <motion.span
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.1 }}
            className={cn(
              'pointer-events-none absolute z-50 whitespace-nowrap rounded bg-fg px-2 py-1 text-[11px] font-medium text-canvas shadow-lg',
              positionCls,
            )}
          >
            {content}
          </motion.span>
        )}
      </AnimatePresence>
    </span>
  );
}

// ─── Badge ───────────────────────────────────────────────────────────────────

export function Badge({ children, variant = 'default', className }: { children: ReactNode; variant?: 'default' | 'accent' | 'success' | 'danger' | 'attention' | 'done'; className?: string }) {
  const v: Record<string, string> = {
    default:   'bg-neutral-subtle text-fg-muted border-border-muted',
    accent:    'bg-accent-subtle text-accent-fg border-accent-muted/40',
    success:   'bg-success-subtle text-success-fg border-success-muted/40',
    danger:    'bg-danger-subtle text-danger-fg border-danger-muted/40',
    attention: 'bg-attention-subtle text-attention-fg border-attention-muted/40',
    done:      'bg-done-emphasis/10 text-done-fg border-done-emphasis/20',
  };
  return (
    <span className={cn('inline-flex items-center rounded-full border px-1.5 py-0.5 text-[10px] font-medium', v[variant], className)}>
      {children}
    </span>
  );
}
