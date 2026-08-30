'use client';

import { useRef, useState } from 'react';
import { Upload } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { Btn } from '@/components/ui';

/** Import a run exported from this platform (or from another instance of it).
 *  The ZIP carries summary.json plus the per-task artifacts; the server rebuilds
 *  the rows and the artifact tree. */
export function ImportRun() {
  const input = useRef<HTMLInputElement>(null);
  const qc = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function upload(file: File) {
    setBusy(true);
    setError('');
    try {
      const body = new FormData();
      body.append('file', file);
      const res = await fetch('/api/runs/import', { method: 'POST', body });
      if (!res.ok) throw new Error(await res.text().catch(() => `HTTP ${res.status}`));
      qc.invalidateQueries({ queryKey: ['runs'] });
      qc.invalidateQueries({ queryKey: ['overview'] });
    } catch (e) {
      // The usual cause is a benchmark the target instance has not installed.
      setError(String(e instanceof Error ? e.message : e).slice(0, 200));
    } finally {
      setBusy(false);
      if (input.current) input.current.value = '';
    }
  }

  return (
    <>
      <input ref={input} type="file" accept=".zip" className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) upload(f); }} />
      <Btn variant="default" onClick={() => input.current?.click()} disabled={busy}
        icon={<Upload className="h-3.5 w-3.5" />}>
        {busy ? 'Importing…' : 'Import run'}
      </Btn>
      {error && <span className="text-xs text-danger-fg" title={error}>Import failed: {error}</span>}
    </>
  );
}
