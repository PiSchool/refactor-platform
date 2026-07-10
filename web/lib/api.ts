'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { Catalog, Overview, RunSummary, RunTask, SettingsDoc } from '@/lib/types';

async function j<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { ...init, headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) } });
  if (!res.ok) throw new Error(`${res.status} ${await res.text().catch(() => res.statusText)}`);
  return res.json();
}

export function useOverview() {
  return useQuery({ queryKey: ['overview'], queryFn: () => j<Overview>('/api/overview'), refetchInterval: 4000 });
}

export function useRuns(filters: { status?: string; benchmark?: string } = {}) {
  const qs = new URLSearchParams(Object.entries(filters).filter(([, v]) => v) as [string, string][]).toString();
  return useQuery({
    queryKey: ['runs', filters],
    queryFn: () => j<{ runs: RunSummary[] }>(`/api/runs${qs ? `?${qs}` : ''}`),
    refetchInterval: 4000,
  });
}

export function useRun(id: string) {
  return useQuery({
    queryKey: ['run', id],
    queryFn: () => j<RunSummary>(`/api/runs/${id}`),
    refetchInterval: (q) => (['running', 'queued'].includes((q.state.data as RunSummary | undefined)?.status || '') ? 2000 : false),
  });
}

export function useCatalog() {
  return useQuery({ queryKey: ['catalog'], queryFn: () => j<Catalog>('/api/catalog') });
}

export function useBenchmarkTasks(id: string | null) {
  return useQuery({
    enabled: !!id,
    queryKey: ['benchTasks', id],
    queryFn: () => j<{ tasks: { taskKey: string; title: string; params: Record<string, unknown> }[]; facets: any[] }>(`/api/benchmarks/${id}/tasks`),
  });
}

export interface ProviderModel {
  id: string;
  name: string;
  contextLength: number | null;
  free: boolean;
  /** USD per token, as published by the provider */
  pricing?: Record<string, string>;
}

/** Provider model catalog. Cached server-side; `source` reveals offline state. */
export function useModels() {
  return useQuery({
    queryKey: ['models'],
    staleTime: 10 * 60 * 1000,
    queryFn: () => j<{ models: ProviderModel[]; source: string; detail?: string }>('/api/models'),
  });
}

export function useSettings() {
  return useQuery({ queryKey: ['settings'], queryFn: () => j<SettingsDoc>('/api/settings') });
}

export function useCreateRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) => j<RunSummary>('/api/runs', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['runs'] }); qc.invalidateQueries({ queryKey: ['overview'] }); },
  });
}

export function useRunAction() {
  const qc = useQueryClient();
  const invalidate = () => { qc.invalidateQueries({ queryKey: ['runs'] }); qc.invalidateQueries({ queryKey: ['overview'] }); };
  return {
    stop: useMutation({ mutationFn: (id: string) => j(`/api/runs/${id}/stop`, { method: 'POST' }), onSuccess: invalidate }),
    restart: useMutation({ mutationFn: (id: string) => j<RunSummary>(`/api/runs/${id}/restart`, { method: 'POST' }), onSuccess: invalidate }),
    del: useMutation({ mutationFn: (id: string) => j(`/api/runs/${id}`, { method: 'DELETE' }), onSuccess: invalidate }),
    skip: useMutation({ mutationFn: ({ runId, taskId }: { runId: string; taskId: string }) => j(`/api/runs/${runId}/tasks/${taskId}/skip`, { method: 'POST' }), onSuccess: invalidate }),
  };
}
