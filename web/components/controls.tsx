'use client';

/**
 * The controls the configuration screens are built from.
 *
 * Native `<input type="checkbox">` and unstyled `<select>` were used directly in
 * several screens, so the same idea looked different in each of them, and state
 * that a symbol expresses in one glance — enabled, overridden, unset — was
 * spelled out as a sentence beside every row. These carry the theme, the focus
 * ring and the keyboard behaviour once, and each of them takes the label it
 * announces to a screen reader and shows on hover, so a row needs no caption.
 */

import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/utils';

export type Tone = 'neutral' | 'accent' | 'success' | 'attention' | 'danger';

const CHIP: Record<Tone, string> = {
  neutral: 'border-border bg-canvas-subtle text-fg-muted',
  accent: 'border-accent-muted/50 bg-accent-subtle text-accent-fg',
  success: 'border-success-muted/50 bg-success-subtle text-success-fg',
  attention: 'border-attention-muted/50 bg-attention-subtle text-attention-fg',
  danger: 'border-danger-muted/50 bg-danger-subtle text-danger-fg',
};

const DOT: Record<Tone, string> = {
  neutral: 'bg-fg-subtle',
  accent: 'bg-accent-fg',
  success: 'bg-success-fg',
  attention: 'bg-attention-fg',
  danger: 'bg-danger-fg',
};

/** One fact, stated in as little space as it takes. `title` carries the longer
 *  form so the pill itself stays a glyph and a word. */
export function Chip({ icon, children, tone = 'neutral', mono, title, className }: {
  icon?: ReactNode;
  children?: ReactNode;
  tone?: Tone;
  mono?: boolean;
  title?: string;
  className?: string;
}) {
  return (
    <span
      title={title}
      className={cn(
        'inline-flex max-w-full items-center gap-1 rounded-full border px-1.5 py-px text-[11px] leading-4',
        CHIP[tone], mono && 'font-mono', className,
      )}
    >
      {icon}
      {children != null && <span className="truncate">{children}</span>}
    </span>
  );
}

/** A state marker: overridden, unsaved, a value set here. It is announced when
 *  it carries the only statement of that state, and decorative when the control
 *  around it already says the same thing. */
export function Dot({ tone = 'attention', label, className }: { tone?: Tone; label?: string; className?: string }) {
  return (
    <span
      {...(label ? { role: 'img', 'aria-label': label, title: label } : { 'aria-hidden': true })}
      className={cn('inline-block h-1.5 w-1.5 shrink-0 rounded-full', DOT[tone], className)}
    />
  );
}

/** On or off, for a setting that takes effect without a further confirmation. */
export function Switch({ checked, onChange, disabled, label }: {
  checked: boolean;
  onChange: (next: boolean) => void;
  disabled?: boolean;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        'relative inline-flex h-4 w-7 shrink-0 items-center rounded-full border transition-colors duration-150',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-fg focus-visible:ring-offset-1 focus-visible:ring-offset-canvas',
        checked ? 'border-accent-emphasis bg-accent-emphasis' : 'border-border bg-neutral-muted',
        disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer',
      )}
    >
      <span
        className={cn(
          'inline-block h-3 w-3 rounded-full bg-fg-onEmphasis shadow transition-transform duration-150',
          checked ? 'translate-x-3.5' : 'translate-x-0.5',
        )}
      />
    </button>
  );
}

/** An action with no room for a caption. The label is its accessible name and
 *  its tooltip, so the same string cannot drift between the two. */
export function IconBtn({ icon, label, tone = 'neutral', className, ...props }:
ButtonHTMLAttributes<HTMLButtonElement> & { icon: ReactNode; label: string; tone?: Tone }) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      {...props}
      className={cn(
        'inline-flex h-6 w-6 shrink-0 items-center justify-center rounded border border-transparent transition-colors',
        'hover:bg-neutral-subtle disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-fg',
        tone === 'danger' ? 'text-danger-fg' : 'text-fg-subtle hover:text-fg',
        className,
      )}
    >
      {icon}
    </button>
  );
}

/** Multi-selection, where a switch would wrongly suggest one setting per row.
 *  Native, so shift-click ranges and keyboard behaviour are the browser's, with
 *  the theme's accent applied instead of the user agent's blue. */
export function Checkbox({ checked, onChange, disabled, label, className }: {
  checked: boolean;
  onChange: (next: boolean) => void;
  disabled?: boolean;
  label: string;
  className?: string;
}) {
  return (
    <input
      type="checkbox"
      checked={checked}
      disabled={disabled}
      aria-label={label}
      onChange={(event) => onChange(event.target.checked)}
      className={cn(
        'h-3.5 w-3.5 shrink-0 cursor-pointer rounded border-border accent-accent-fg',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-fg focus-visible:ring-offset-1 focus-visible:ring-offset-canvas',
        disabled && 'cursor-not-allowed opacity-50',
        className,
      )}
    />
  );
}

export interface SegmentOption<T extends string> {
  value: T;
  label: string;
  icon?: ReactNode;
  /** Shown on hover; the label stays short enough to fit the control. */
  title?: string;
  count?: number;
}

/** A choice between a few named alternatives, where a dropdown would hide how
 *  many there are and which one is active. */
export function Segmented<T extends string>({ value, options, onChange, disabled, label, className }: {
  value: T;
  options: SegmentOption<T>[];
  onChange: (next: T) => void;
  disabled?: boolean;
  label: string;
  className?: string;
}) {
  return (
    <div role="tablist" aria-label={label} className={cn('inline-flex items-center gap-0.5 rounded-md border border-border p-0.5', className)}>
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={active}
            title={option.title ?? option.label}
            disabled={disabled}
            onClick={() => onChange(option.value)}
            className={cn(
              'inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-fg',
              active ? 'bg-neutral-subtle text-fg' : 'text-fg-muted hover:text-fg',
              disabled && 'cursor-not-allowed opacity-50',
            )}
          >
            {option.icon}
            {option.label}
            {option.count !== undefined && <span className="tabular-nums text-fg-subtle">{option.count}</span>}
          </button>
        );
      })}
    </div>
  );
}

/** A labelled group inside a panel, with the count it holds. Replaces a second
 *  panel whose only distinguishing content was another paragraph. */
export function SubHeading({ icon, title, count, detail, actions }: {
  icon?: ReactNode;
  title: string;
  count?: number;
  detail?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="flex items-center gap-2 pb-1.5">
      {icon}
      <h3 className="text-xs font-semibold uppercase tracking-wide text-fg-muted">{title}</h3>
      {count !== undefined && <span className="tabular-nums text-xs text-fg-subtle">{count}</span>}
      {detail && <span className="truncate text-xs text-fg-subtle" title={detail}>{detail}</span>}
      {actions && <span className="ml-auto flex items-center gap-1">{actions}</span>}
    </div>
  );
}
