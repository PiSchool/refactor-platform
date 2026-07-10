/**
 * @module cost
 * @description Model pricing and cost, mirroring `server/app/api/pricing.py`.
 * Prices are USD per token, straight from the provider catalog.
 *
 *   cacheRead ⊆ input   (billed at the cheaper cache-read rate)
 *   reasoning ⊆ output  (already inside outputTokens)
 */
import type { ProviderModel } from '@/lib/api';

export interface Usage {
  inputTokens: number;
  outputTokens: number;
  cacheReadTokens?: number;
}

/** A rate in USD/token, or null when the provider publishes no real price.
 *
 *  OpenRouter prices its routing models (`openrouter/auto` and friends) as `-1`,
 *  meaning "depends on whichever model the router picks". Multiplying that by a
 *  token count yields a large negative cost, so a negative rate is not a price. */
const rate = (pricing: Record<string, string> | undefined, key: string, fallback: number | null = 0) => {
  const v = pricing?.[key];
  if (v == null || v === '') return fallback;
  const n = Number(v);
  if (!Number.isFinite(n)) return fallback;
  return n >= 0 ? n : null;
};

/** null when the model has no published price — never guess a number. */
export function costUsd(usage: Usage, model: ProviderModel | undefined): number | null {
  const pricing = model?.pricing;
  if (!pricing || Object.keys(pricing).length === 0) return null;

  const prompt = rate(pricing, 'prompt');
  const completion = rate(pricing, 'completion');
  if (prompt == null || completion == null) return null;
  const cacheRead = rate(pricing, 'input_cache_read', prompt) ?? prompt;

  const cached = Math.max(0, Math.min(usage.cacheReadTokens ?? 0, usage.inputTokens));
  const fresh = usage.inputTokens - cached;
  return fresh * prompt + cached * cacheRead + usage.outputTokens * completion;
}

/** Money that can be fractions of a cent; never render "$0.00" for real spend. */
export function formatUsd(value: number | null | undefined): string {
  if (value == null) return '—';
  if (value === 0) return 'free';
  if (value < 0.01) return `$${value.toFixed(4)}`;
  if (value < 1) return `$${value.toFixed(3)}`;
  return `$${value.toFixed(2)}`;
}

export function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}
