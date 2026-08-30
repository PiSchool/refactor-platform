'use client';

import {
  Download,
  FileSpreadsheet,
  Loader2,
  Plus,
  RotateCcw,
  SkipForward,
  Square,
  Trash2,
} from 'lucide-react';
import { Btn } from '@/components/ui';

export function NewRunButton({ onClick }: { onClick: () => void }) {
  return (
    <Btn variant="primary" size="md" icon={<Plus className="h-4 w-4" />} onClick={onClick}>
      New run
    </Btn>
  );
}

/** `stopping` is true from the moment the request is accepted until the run
 *  actually leaves the running state. Without it the button looked identical
 *  before and after being pressed, so a stop that was in progress was
 *  indistinguishable from one that had been ignored. */
export function RunHeaderActions({ runId, live, stopping, onRestart, onStop, onDelete }: {
  runId: string;
  live: boolean;
  stopping?: boolean;
  onRestart: () => void;
  onStop: () => void;
  onDelete: () => void;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <a href={`/api/runs/${runId}/export.csv`}><Btn variant="outline" icon={<FileSpreadsheet className="h-3.5 w-3.5" />}>CSV</Btn></a>
      <a href={`/api/runs/${runId}/export`}><Btn variant="outline" icon={<Download className="h-3.5 w-3.5" />}>Export ZIP</Btn></a>
      {!live && <Btn variant="outline" icon={<RotateCcw className="h-3.5 w-3.5" />} onClick={onRestart}>Restart</Btn>}
      {live && (
        <Btn variant="danger" disabled={stopping}
          icon={stopping ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Square className="h-3.5 w-3.5" />}
          onClick={onStop}>
          {stopping ? 'Stopping' : 'Stop'}
        </Btn>
      )}
      {!live && <Btn variant="invisible" icon={<Trash2 className="h-3.5 w-3.5" />} onClick={onDelete}>Delete</Btn>}
    </div>
  );
}

export function SkipTaskAction({ onSkip }: { onSkip: () => void }) {
  return (
    <span onClick={(event) => { event.stopPropagation(); onSkip(); }} title="Skip">
      <SkipForward className="h-3.5 w-3.5 text-fg-muted hover:text-fg" />
    </span>
  );
}