/**
 * @module diff
 * @description Minimal unified-diff parser: enough to render a GitHub-style
 * split of files → hunks → lines with original/new line numbers.
 */

export type DiffLineKind = 'add' | 'del' | 'ctx' | 'meta';

export interface DiffLine {
  kind: DiffLineKind;
  text: string;
  oldNo: number | null;
  newNo: number | null;
}

export interface DiffHunk {
  header: string;
  lines: DiffLine[];
}

export interface DiffFile {
  path: string;
  oldPath: string | null;
  status: 'added' | 'deleted' | 'renamed' | 'modified';
  additions: number;
  deletions: number;
  hunks: DiffHunk[];
  binary: boolean;
}

const HUNK = /^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$/;

/** Parse `git diff` output. Unknown/extra headers are ignored, never thrown on. */
export function parseDiff(text: string): DiffFile[] {
  const files: DiffFile[] = [];
  if (!text.trim()) return files;

  let file: DiffFile | null = null;
  let hunk: DiffHunk | null = null;
  let oldNo = 0;
  let newNo = 0;

  const push = () => {
    if (file) files.push(file);
  };

  for (const raw of text.split('\n')) {
    if (raw.startsWith('diff --git ')) {
      push();
      hunk = null;
      const m = raw.match(/^diff --git a\/(.+?) b\/(.+)$/);
      file = {
        path: m?.[2] ?? raw.slice('diff --git '.length),
        oldPath: m?.[1] ?? null,
        status: 'modified',
        additions: 0,
        deletions: 0,
        hunks: [],
        binary: false,
      };
      continue;
    }
    if (!file) continue;

    if (raw.startsWith('new file mode')) { file.status = 'added'; continue; }
    if (raw.startsWith('deleted file mode')) { file.status = 'deleted'; continue; }
    if (raw.startsWith('rename to ')) { file.status = 'renamed'; file.path = raw.slice('rename to '.length); continue; }
    if (raw.startsWith('rename from ')) { file.oldPath = raw.slice('rename from '.length); continue; }
    if (raw.startsWith('Binary files')) { file.binary = true; continue; }
    if (raw.startsWith('index ') || raw.startsWith('--- ') || raw.startsWith('+++ ') ||
        raw.startsWith('old mode') || raw.startsWith('new mode') || raw.startsWith('similarity index')) {
      continue;
    }

    const hm = raw.match(HUNK);
    if (hm) {
      oldNo = Number(hm[1]);
      newNo = Number(hm[3]);
      hunk = { header: raw, lines: [] };
      file.hunks.push(hunk);
      continue;
    }
    if (!hunk) continue;

    if (raw.startsWith('\\')) {   // "\ No newline at end of file"
      hunk.lines.push({ kind: 'meta', text: raw, oldNo: null, newNo: null });
    } else if (raw.startsWith('+')) {
      file.additions++;
      hunk.lines.push({ kind: 'add', text: raw.slice(1), oldNo: null, newNo: newNo++ });
    } else if (raw.startsWith('-')) {
      file.deletions++;
      hunk.lines.push({ kind: 'del', text: raw.slice(1), oldNo: oldNo++, newNo: null });
    } else if (raw.startsWith(' ') || raw === '') {
      hunk.lines.push({ kind: 'ctx', text: raw.slice(1), oldNo: oldNo++, newNo: newNo++ });
    }
  }
  push();
  return files;
}

export function diffTotals(files: DiffFile[]) {
  return files.reduce(
    (acc, f) => ({ additions: acc.additions + f.additions, deletions: acc.deletions + f.deletions }),
    { additions: 0, deletions: 0 },
  );
}
