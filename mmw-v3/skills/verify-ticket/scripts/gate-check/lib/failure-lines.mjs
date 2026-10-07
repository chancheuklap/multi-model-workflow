// The lines a failure report keeps. Shared by a criterion summary and a repository
// check's bounce, so the two reports pick lines with one rule.
// Zero dependencies. Node 16+.

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const ERROR_LINE_RE = /error|fail|assert|exception|traceback/i;
export const PATH_LINE_RE = /(?:^|[\s"'`(])(?:[\w.+@-]+\/)*[\w.+@-]+\.[A-Za-z][\w]*:\d+\b/;

// Error lines and path:line lines, in the order they appeared, then the last two
// lines. When that does not fit, path:line lines and the last two lines keep their
// place and error lines fill what remains. The cut names how many lines were left
// out and where the whole output was written.
export function failureOutput(output, max = 480, logPath = null) {
  const hide = (text) => text.replace(/STORY OK|JOURNEY OK|HARNESS OK|LINT OK/g, "[redacted]");
  const lines = String(output).split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (!lines.length) return hide("(no output)".slice(0, max));
  const indexed = lines.map((line, index) => ({
    line, index,
    error: ERROR_LINE_RE.test(line),
    path: PATH_LINE_RE.test(line),
  }));
  const reserved = [];
  const reservedAt = new Set();
  const reserve = (item) => {
    if (reservedAt.has(item.index)) return;
    reservedAt.add(item.index);
    reserved.push(item);
  };
  for (const item of indexed) if (item.path) reserve(item);
  for (const item of indexed.slice(-2)) reserve(item);
  let errors = indexed.filter((item) => item.error && !reservedAt.has(item.index));
  let tails = reserved.filter((item) => !item.path);
  const render = (errorItems, tailItems, withSuffix) => {
    const body = [...errorItems, ...reserved.filter((item) => item.path || tailItems.includes(item))];
    body.sort((a, b) => a.index - b.index);
    const omitted = lines.length - body.length;
    const suffix = withSuffix && omitted > 0
      ? " | +" + omitted + " more" + (logPath ? " | " + logPath : "")
      : "";
    return body.map((item) => item.line).join(" | ") + suffix;
  };
  const plain = render(errors, tails, false);
  if (plain.length <= max) return hide(plain);
  let summary = render(errors, tails, true);
  while (summary.length > max && errors.length) {
    errors = errors.slice(0, -1);
    summary = render(errors, tails, true);
  }
  while (summary.length > max && tails.length) {
    tails = tails.slice(0, -1);
    summary = render(errors, tails, true);
  }
  if (summary.length > max) summary = summary.slice(0, max);
  return hide(summary);
}

// The first `maxErrorLines` lines that match an error or a path:line — a path line
// spends one of those places — plus the last `tailLines`, once each, in appearance
// order. Blank lines are dropped the same way `failureOutput` drops them.
export function checksExcerpt(output, maxErrorLines = 10, tailLines = 30) {
  const hide = (text) => text.replace(/STORY OK|JOURNEY OK|HARNESS OK|LINT OK/g, "[redacted]");
  const lines = String(output).split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const indexed = lines.map((line, index) => ({
    line, index,
    hit: ERROR_LINE_RE.test(line) || PATH_LINE_RE.test(line),
  }));
  const kept = new Set();
  let errors = 0;
  for (const item of indexed) {
    if (!item.hit || errors >= maxErrorLines) continue;
    kept.add(item.index);
    errors += 1;
  }
  for (const item of indexed.slice(-tailLines)) kept.add(item.index);
  return indexed.filter((item) => kept.has(item.index)).map((item) => hide(item.line));
}

function isDirectRun() {
  const entry = process.argv[1];
  if (!entry) return false;
  return fileURLToPath(import.meta.url) === resolve(entry);
}

// `node failure-lines.mjs [maxErrorLines] [tailLines]` reads the check's output on
// stdin and writes the excerpt lines, with no extra trailing newline.
if (isDirectRun()) {
  const maxErrorLines = Number(process.argv[2] ?? 10);
  const tailLines = Number(process.argv[3] ?? 30);
  const lines = checksExcerpt(readFileSync(0, "utf8"), maxErrorLines, tailLines);
  if (lines.length) process.stdout.write(lines.join("\n"));
}
