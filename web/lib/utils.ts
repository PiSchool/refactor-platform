/**
 * @module utils
 * @description General utility functions: formatting, time, string manipulation.
 */
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { differenceInSeconds, formatDistanceToNowStrict, parseISO } from 'date-fns';
import type { JsonObject, JobStep, StepMetrics } from '@/lib/types';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatRelative(value?: string) {
  if (!value) return '-';
  try {
    const v = value.endsWith('Z') || value.includes('+') ? value : `${value}Z`;
    const d = parseISO(v);
    // Clamp future timestamps (container/browser clock skew) to now
    const ref = d > new Date() ? new Date() : d;
    return formatDistanceToNowStrict(ref, { addSuffix: true });
  } catch {
    return value;
  }
}

export function formatDurationSeconds(seconds?: number | null) {
  if (!seconds || seconds <= 0) return '0s';
  const mins = Math.floor(seconds / 60);
  const hrs = Math.floor(mins / 60);
  const secs = Math.floor(seconds % 60);
  if (hrs > 0) return `${hrs}h ${mins % 60}m`;
  if (mins > 0) return `${mins}m ${secs}s`;
  return `${secs}s`;
}

export function diffDuration(start?: string, end?: string, active = true) {
  if (!start) return '-';
  try {
    const s = start.endsWith('Z') || start.includes('+') ? start : `${start}Z`;
    const e = end ? (end.endsWith('Z') || end.includes('+') ? end : `${end}Z`) : null;
    // When not active (session completed) and no end time is available, return '-'
    // rather than falling back to new Date() which causes durations to grow forever.
    if (!e && !active) return '-';
    const seconds = differenceInSeconds(e ? parseISO(e) : new Date(), parseISO(s));
    return formatDurationSeconds(seconds);
  } catch {
    return '-';
  }
}

export function statusTone(status?: string) {
  switch (String(status || '').toLowerCase()) {
    case 'running':
    case 'indexing':
    case 'setting up':
    case 'setting_up':
      return 'running';
    case 'completed':
    case 'passed':
    case 'ready':
      return 'completed';
    case 'failed':
    case 'timed_out':
      return 'failed';
    case 'stopped':
    case 'skipped':
    case 'paused':
      return 'stopped';
    default:
      return 'pending';
  }
}

/** A run's `status` says it reached the end, not that its tasks passed.
 *  Display must not show a green check on a run whose tasks failed. */
export function runOutcome(run: { status: string; counts: { passed: number; total: number } }) {
  // A run's status reflects whether the pipeline *ran*, not how many tasks the
  // agent passed. This is an evaluation harness: tasks passing or failing the
  // benchmark is the measurement, not a run failure. Only a crash/stop/timeout
  // is a non-completed run — and the backend already sets those.
  return run.status;
}

export function percent(numerator?: number, denominator?: number) {
  if (!denominator) return 0;
  return Math.max(0, Math.min(100, (Number(numerator || 0) / Number(denominator)) * 100));
}

export function formatCount(value?: number | string | null) {
  const numeric = Number(value ?? 0);
  if (!Number.isFinite(numeric)) return '0';
  return numeric.toLocaleString();
}

export function humanizeStepName(value?: string) {
  const name = String(value || '').trim().toLowerCase();
  if (!name) return 'Idle';
  if (name === 'refbench') return 'RefactorBench';
  if (name === 'swe') return 'SWE-Refactor';
  if (name === 'cleanup') return 'Cleanup';
  return value || 'Idle';
}

export function compactSetupId(value?: string) {
  const setup = String(value || '').trim();
  if (!setup) return '';
  if (setup === 's1_default') return 's1';
  if (setup === 's1_lsp') return 's1-lsp';
  if (setup === 's2_rag') return 's2';
  if (setup === 's3_rag_multiagent') return 's3';
  return setup;
}

export function joinSummary(parts: Array<string | null | undefined>) {
  return parts.map((part) => String(part || '').trim()).filter(Boolean).join(' · ');
}

export function formatRunScope(value?: string) {
  const scope = String(value || '').trim().toLowerCase();
  if (scope === 'smoke') return 'Smoke';
  if (scope === 'full') return 'Full';
  return value || '';
}

export function summarizeActiveWork(stepName?: string, metrics?: StepMetrics) {
  const data = metrics || {};
  const progress = ((data.taskProgress as any) || (data.refactoringProgress as any) || {}) as { index?: number; total?: number };
  const progressIndex = Number(progress.index || 0);
  const progressTotalRaw = Number(progress.total || 0);
  const selectedRefactoringsTotal = Number(
    (data.selectedRefactoringsTotal as number | undefined)
    || (data.projectSelectedRefactorings as number | undefined)
    || 0
  );
  const progressTotal = Math.max(progressTotalRaw, selectedRefactoringsTotal);
  const ragRowsProcessed = Number(data.ragRowsProcessed || 0);
  const ragRowsTotal = Number(data.ragRowsTotal || 0);
  const scope = [data.currentRepo, data.currentTaskId].filter(Boolean).join(' / ');
  const headline = [
    humanizeStepName(stepName),
    data.setup ? compactSetupId(String(data.setup)) : null,
    scope || null,
    progressTotal > 0 ? `${progressIndex}/${progressTotal}` : null,
  ]
    .filter(Boolean)
    .join(' · ');

  const detail = [
    data.mcpStatus ? `mcp ${String(data.mcpStatus)}` : null,
    data.ragStage ? `rag ${String(data.ragStage)}` : null,
    ragRowsTotal > 0 ? `index ${ragRowsProcessed}/${ragRowsTotal}` : null,
    data.liveResultsTotal ? `${Number(data.liveResultsTotal)} results` : null,
  ]
    .filter(Boolean)
    .join(' · ');

  return {
    headline: headline || humanizeStepName(stepName),
    detail,
    progressIndex,
    progressTotal,
  };
}

export function getStepMetrics(state: JsonObject | undefined, stepName?: string) {
  if (!state || !stepName) return undefined;
  const rawSteps = state.steps;
  if (!rawSteps || typeof rawSteps !== 'object' || Array.isArray(rawSteps)) return undefined;
  const step = (rawSteps as Record<string, unknown>)[stepName];
  if (!step || typeof step !== 'object' || Array.isArray(step)) return undefined;
  const metrics = (step as { metrics?: unknown }).metrics;
  if (!metrics || typeof metrics !== 'object' || Array.isArray(metrics)) return undefined;
  return metrics as StepMetrics;
}

export interface SubStep {
  label: string;
  status: string;
  detail?: string;
}

export function compactTaskId(value?: string) {
  let s = String(value || '').trim();
  s = s.replace(/\s*mcp\s+(not_required|required|not required)\s*/gi, '');
  s = s.replace(/mcp_(not_required|required)/gi, '');
  s = s.trim();
  // Truncate SHA-like hashes (40+ hex chars, possibly with _digits suffix)
  s = s.replace(/\b([0-9a-f]{8})[0-9a-f]{32,}(?:_[\d_]+)?\b/gi, '$1…');
  return s;
}

export function compactRunId(value?: string) {
  const s = String(value || '').trim();
  if (s.length <= 32) return s;
  return s.slice(0, 28) + '…';
}


/** Runs imported from the study archive are evidence, not something this instance
 *  produced. Badge them, or a reviewer cannot tell them apart from a live run. */
export function isArchived(r: { config?: Record<string, unknown> }): boolean {
  const config = r.config ?? {};
  const provenance = config.import;
  return Boolean(
    provenance
    && typeof provenance === 'object'
    && !Array.isArray(provenance)
    && typeof (provenance as Record<string, unknown>).sourceRunId === 'string'
  );
}
