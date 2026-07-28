'use client';

import { useEffect, useState } from 'react';
import { Boxes, Gauge, GitBranch, ListTodo, MessageSquareText, Plug, Server, Sliders } from 'lucide-react';
import { useSettings } from '@/lib/api';
import { Select, SkeletonCard } from '@/components/ui';
import { RunDefaults } from '@/components/settings/run-defaults';
import { BenchmarksSection } from '@/components/settings/benchmarks';
import { EvaluationSection } from '@/components/settings/evaluation';
import { ReposSection } from '@/components/settings/repos';
import { TasksSection } from '@/components/settings/tasks';
import { PromptsSection } from '@/components/settings/prompts';
import { ServicesSection } from '@/components/settings/services';
import { PluginsSection } from '@/components/settings/plugins';

/** One icon per section: two sections sharing one made the nav unreadable at a
 *  glance, which is the only thing a 12-pixel glyph is for. */
const SECTIONS = [
  { id: 'general', label: 'General', icon: Sliders },
  { id: 'benchmarks', label: 'Benchmarks', icon: Boxes },
  { id: 'evaluation', label: 'Evaluation & metrics', icon: Gauge },
  { id: 'repos', label: 'Repositories', icon: GitBranch },
  { id: 'tasks', label: 'Tasks', icon: ListTodo },
  { id: 'prompts', label: 'Prompts', icon: MessageSquareText },
  { id: 'services', label: 'Services', icon: Server },
  { id: 'plugins', label: 'Plugins', icon: Plug },
] as const;

type SectionId = (typeof SECTIONS)[number]['id'];

export default function SettingsPage() {
  const { data, isLoading, refetch } = useSettings();
  const [section, setSection] = useState<SectionId>('general');
  const [bench, setBench] = useState('');

  useEffect(() => {
    if (data && !bench) setBench(data.plugins.benchmarks[0]?.key ?? '');
  }, [data, bench]);

  if (isLoading || !data) return <SkeletonCard rows={8} />;
  const benchmarks = data.plugins.benchmarks;

  return (
    <div className="flex h-[calc(100vh-3rem)] min-h-0 flex-col gap-3">
      <h1 className="shrink-0 text-lg font-semibold text-fg">Settings</h1>

      <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[200px_1fr]">
        {/* side nav — GitHub's settings layout */}
        <nav className="shrink-0 space-y-0.5 overflow-auto">
          {SECTIONS.map((s) => {
            const Icon = s.icon;
            const active = section === s.id;
            return (
              <button key={s.id} onClick={() => setSection(s.id)}
                className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors ${
                  active ? 'bg-sidenav-selected font-medium text-fg' : 'text-fg-muted hover:bg-neutral-subtle hover:text-fg'}`}>
                <Icon className="h-4 w-4 shrink-0" />
                <span className="truncate">{s.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="min-h-0 overflow-auto pr-1">
          {/* Which benchmark these settings belong to. Named, with its task
              count, because a bare key says nothing about what is selected. */}
          {['evaluation', 'repos', 'tasks', 'prompts'].includes(section) && (
            <div className="mb-3 flex items-center gap-2">
              <label className="text-xs text-fg-muted" htmlFor="benchmark-scope">Benchmark</label>
              <Select id="benchmark-scope" value={bench} onChange={(e) => setBench(e.target.value)}>
                {benchmarks.map((b) => (
                  <option key={b.key} value={b.key}>{b.name} · {b.taskCount.toLocaleString()} tasks</option>
                ))}
              </Select>
            </div>
          )}

          {section === 'general' && <RunDefaults editable={data.editable} onSaved={refetch} />}
          {section === 'benchmarks' && <BenchmarksSection benchmarks={data.plugins.benchmarks} onChanged={refetch} />}
          {section === 'evaluation' && bench && <EvaluationSection benchmark={bench} />}
          {section === 'repos' && bench && <ReposSection benchmark={bench} />}
          {section === 'tasks' && bench && <TasksSection benchmark={bench} />}
          {section === 'prompts' && bench && <PromptsSection benchmark={bench} />}
          {section === 'services' && <ServicesSection secrets={data.secrets} providers={data.providers ?? []} />}
          {section === 'plugins' && <PluginsSection plugins={data.plugins} errors={data.errors} />}
        </div>
      </div>
    </div>
  );
}
