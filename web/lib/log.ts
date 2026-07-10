/**
 * @module log
 * @description Classifying build/test log lines, for colouring and for the
 * "errors & warnings only" filter.
 */

/** Maven and Gradle colour their output; the raw bytes are kept on disk. */
const ANSI = /\x1b\[[0-9;]*[A-Za-z]/g;
export const stripAnsi = (s: string) => s.replace(ANSI, '');

/** A clean summary line — "Failures: 0, Errors: 0" names errors but reports none,
 *  so it must not be mistaken for one by the generic matcher below. */
const CLEAN_SUMMARY = /(Failures|Errors):\s*0(,|\s|$)/i;
const REAL_FAILURES = /Failures: [1-9]|Errors: [1-9]/i;

/** Lines a reviewer scans for first.
 *
 *  The generic `error`/`fatal`/`exception` match matters: failures reach this log
 *  from the shell, the JVM and the harness — not only through Maven's `[ERROR]`
 *  vocabulary — and a filter that knows only Maven hides them completely. */
export function tone(line: string): string {
  if (REAL_FAILURES.test(line)) return 'text-danger-fg';
  if (CLEAN_SUMMARY.test(line)) {
    return /BUILD SUCCESS|Tests run:/.test(line) ? 'text-success-fg' : 'text-fg-muted';
  }
  if (/^\s*\[ERROR\]|BUILD FAILURE|FAILURES?!|<<< (FAILURE|ERROR)|^E\s|Traceback|AssertionError/.test(line)
      || /\b(errors?|fatal|exceptions?|not found|no such file|permission denied)\b/i.test(line)) {
    return 'text-danger-fg';
  }
  if (/^\s*\[WARNING\]|\bwarn(ing)?s?\b/i.test(line)) return 'text-attention-fg';
  if (/BUILD SUCCESS|^OK$|^\.+$/.test(line)) return 'text-success-fg';
  return 'text-fg-muted';
}

export const isProblem = (line: string) => tone(line) === 'text-danger-fg' || tone(line) === 'text-attention-fg';
