'use client';

import { ReactNode } from 'react';
import { Card } from '@/components/ui';

/** GitHub's settings "box": titled panel with a subdued description. */
export function Panel({ title, description, actions, children }: {
  title: string; description?: string; actions?: ReactNode; children: ReactNode;
}) {
  return (
    <Card className="mb-4">
      <div className="flex items-start justify-between gap-3 border-b border-border px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold text-fg">{title}</h2>
          {description && <p className="mt-0.5 text-xs text-fg-subtle">{description}</p>}
        </div>
        {actions && <div className="flex shrink-0 items-center gap-1.5">{actions}</div>}
      </div>
      <div className="p-4">{children}</div>
    </Card>
  );
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="flex items-start justify-between gap-4 py-1.5">
      <span className="pt-1">
        <span className="block text-xs text-fg">{label}</span>
        {hint && <span className="block text-[11px] text-fg-subtle">{hint}</span>}
      </span>
      <span className="shrink-0">{children}</span>
    </label>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input {...props}
      className={`h-8 rounded-md border border-border bg-canvas-inset px-3 text-sm text-fg ${props.className ?? 'w-64'}`} />
  );
}

export function Note({ children, tone = 'muted' }: { children: ReactNode; tone?: 'muted' | 'error' | 'ok' }) {
  const cls = tone === 'error' ? 'text-danger-fg' : tone === 'ok' ? 'text-success-fg' : 'text-fg-muted';
  return <span className={`text-xs ${cls}`}>{children}</span>;
}

/** Fetch JSON, but never poison state with an error body — the Settings page
 *  once crashed on `text.trim()` after a 404 returned `{detail: …}`. */
export async function getJson<T>(url: string): Promise<T | null> {
  const res = await fetch(url);
  if (!res.ok) return null;
  try {
    return (await res.json()) as T;
  } catch {
    return null;
  }
}
