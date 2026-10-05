#!/usr/bin/env node
// Run the CHECK of every unmet criterion in the ledgers named on the command line
// and write each result back as that criterion's checkbox and EVIDENCE line.
// Zero dependencies. Node 16+.
//
// The ledgers are files verify-ticket writes into a directory of its own for one
// run, so one process reads and writes each of them and nothing else does.

import { statSync, writeFileSync } from "node:fs";
import { spawn } from "node:child_process";
import { Worker } from "node:worker_threads";
import { delimiter, dirname, basename, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  MAX_AUTOMATIC_EVIDENCE_CHARS, MAX_CHECK_OUTPUT_BYTES, automaticEvidencePrefix,
  formatDocument, gateDefinitionDigest, gateState, parseGates, qualify, readLedger, sha256,
} from "./lib/gates.mjs";
import { terminateProcessTree } from "./lib/process-tree.mjs";

const HELP = `usage: gate-check.mjs [--reverify] [--timeout S] [--cwd DIR] file ...

  (default)       run the CHECK of every unmet criterion and update its ledger
  --reverify      run every criterion with a CHECK, met ones included
  --timeout S     per-check timeout, integer seconds 1..86400 (default 120)
  --cwd DIR       directory a CHECK runs in (default: beside its ledger);
                  a criterion's CWD attribute is resolved against it

A CHECK runs as written, in /bin/sh, with the inherited environment.

exit codes: 0 all met; 1 unmet or abandoned; 2 usage, parse or infrastructure.`;

const FLAG_OPTIONS = new Set(["--reverify", "--help", "-h"]);
const VALUE_OPTIONS = new Set(["--timeout", "--cwd"]);
const SHELL = "/bin/sh";
const MAX_OUTPUT_BYTES = MAX_CHECK_OUTPUT_BYTES;
const REGEX_TIMEOUT_MS = 250;
const REGEX_STARTUP_TIMEOUT_MS = 5000;
const DEFAULT_TIMEOUT_SECONDS = 120;
const CHECK_SUPERVISOR = fileURLToPath(new URL("./lib/check-supervisor.mjs", import.meta.url));

// Titles, paths, commands and output come from the repository and must not be able
// to rewrite terminal history, set a window title, or visually reorder text. Strip
// every C0/C1 control plus Unicode bidi formatting markers at the final sink.
const UNSAFE_TERMINAL_RE = /[\u0000-\u001f\u007f-\u009f\u061c\u200e\u200f\u2028-\u202e\u2066-\u2069]/g;
const terminalSafe = (value) => String(value).replace(UNSAFE_TERMINAL_RE, " ");
for (const method of ["log", "error"]) {
  const write = console[method].bind(console);
  console[method] = (...values) => write(...values.map(terminalSafe));
}

function parseArgs(argv) {
  const options = {};
  const files = [];
  let positional = false;
  for (let index = 0; index < argv.length; index++) {
    const arg = argv[index];
    if (arg === "--") { positional = true; continue; }
    if (!positional && FLAG_OPTIONS.has(arg)) {
      const key = arg.replace(/^-+/, "");
      if (options[key] !== undefined) return { error: "duplicate option " + arg };
      options[key] = true;
      continue;
    }
    if (!positional && arg.startsWith("--")) {
      const equals = arg.indexOf("=");
      const name = equals === -1 ? arg : arg.slice(0, equals);
      if (!VALUE_OPTIONS.has(name)) return { error: "unknown option " + name };
      const key = name.slice(2);
      if (options[key] !== undefined) return { error: "duplicate option " + name };
      const value = equals === -1 ? argv[++index] : arg.slice(equals + 1);
      if (value === undefined || value === "") return { error: name + " needs a value" };
      options[key] = value;
      continue;
    }
    if (!positional && arg.startsWith("-")) return { error: "unknown option " + arg };
    files.push(arg);
  }
  return { options, files };
}

function failUsage(message) {
  console.error("gate-check: " + message);
  console.error("run gate-check.mjs --help for usage");
  process.exit(2);
}

function asDirectory(path, label) {
  try {
    if (!statSync(path).isDirectory()) failUsage(label + " is not a directory: " + path);
  } catch (error) {
    if (error.code === "ENOENT") failUsage(label + " does not exist: " + path);
    failUsage("cannot inspect " + label + " " + path + ": " + error.message);
  }
}

function timeoutValue(value) {
  if (value === undefined) return DEFAULT_TIMEOUT_SECONDS;
  const number = Number(value);
  if (!Number.isFinite(number) || !Number.isInteger(number) || number < 1 || number > 86400) {
    failUsage("--timeout needs an integer from 1 through 86400, got " + JSON.stringify(value));
  }
  return number;
}

const parsedArgs = parseArgs(process.argv.slice(2));
if (parsedArgs.error) failUsage(parsedArgs.error);
const { options: opt, files: fileArgs } = parsedArgs;
if (opt.help || opt.h) {
  // HELP is a fixed local constant, so it keeps its layout instead of going
  // through the sanitizer meant for repository text.
  process.stdout.write(HELP + "\n");
  process.exit(0);
}
if (!fileArgs.length) failUsage("name at least one ledger file");

const timeoutSeconds = timeoutValue(opt.timeout);
const defaultCwd = opt.cwd ? resolve(opt.cwd) : null;
if (defaultCwd) asDirectory(defaultCwd, "--cwd");
const files = fileArgs.map((file) => resolve(file));

function readLedgerFile(file) {
  try { return readLedger(file); }
  catch (error) {
    if (error.code === "ENOENT") failUsage("no such gate file: " + file);
    failUsage("cannot read " + file + ": " + error.message);
  }
}

function loadLedger(file) {
  const doc = parseGates(readLedgerFile(file));
  for (const warning of doc.warnings) console.error("gate-check: " + file + ": warning: " + warning);
  if (doc.errors.length) {
    for (const error of doc.errors) console.error("gate-check: " + file + ": " + error);
    process.exit(2);
  }
  return { file, doc };
}

let ledgers = files.map(loadLedger);

const pathValue = String(process.env.PATH || "");
const pathEvidence = sha256(pathValue).slice(0, 12) + "/" +
  (pathValue ? pathValue.split(delimiter).length : 0) + " entries";
const pathTranscript = pathValue.replace(/[\r\n]/g, " ").slice(0, 800) + (pathValue.length > 800 ? "..." : "");

function resolvedGateCwd(gate, file) {
  const base = defaultCwd || dirname(file);
  return gate.cwd ? resolve(base, gate.cwd) : base;
}

// An EXPECT regex runs in a disposable worker so catastrophic backtracking cannot
// hang the run; the match budget starts once the worker is online.
function safeRegexMatch(expectation, output) {
  if (expectation.kind === "text") return Promise.resolve({ matched: output.includes(expectation.value) });
  return new Promise((done) => {
    let worker;
    let settled = false;
    let startupTimer = null;
    let matchTimer = null;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      if (startupTimer) clearTimeout(startupTimer);
      if (matchTimer) clearTimeout(matchTimer);
      if (worker) worker.terminate().catch(() => {});
      done(value);
    };
    try { worker = new Worker(new URL("./lib/regex-worker.mjs", import.meta.url)); }
    catch (error) {
      finish({ matched: false, error: "EXPECT worker could not start: " + error.message });
      return;
    }
    startupTimer = setTimeout(() => finish({
      matched: false,
      error: "EXPECT worker startup exceeded " + REGEX_STARTUP_TIMEOUT_MS + "ms",
    }), REGEX_STARTUP_TIMEOUT_MS);
    worker.once("online", () => {
      if (settled) return;
      clearTimeout(startupTimer);
      startupTimer = null;
      matchTimer = setTimeout(() => finish({
        matched: false,
        error: "EXPECT regex exceeded " + REGEX_TIMEOUT_MS + "ms",
      }), REGEX_TIMEOUT_MS);
      try { worker.postMessage({ source: expectation.source, flags: expectation.flags, output }); }
      catch (error) { finish({ matched: false, error: error.message }); }
    });
    worker.once("message", (message) => finish(message));
    worker.once("error", (error) => finish({ matched: false, error: error.message }));
    worker.once("exit", (code) => {
      finish({ matched: false, error: "EXPECT worker exited " + code + " without a result" });
    });
  });
}

function outputFingerprint(output) {
  const value = String(output);
  return { sha256: sha256(value), bytes: Buffer.byteLength(value, "utf8") };
}

function runCheck(task) {
  return new Promise((done) => {
    const chunks = { stdout: [], stderr: [] };
    let bytes = 0;
    let rawOverflow = false;
    let timedOut = false;
    let spawnError = null;
    let closed = false;
    let closeStreamsTimer = null;
    let forceSettleTimer = null;
    let timeoutTimer = null;
    let cleanupDiagnostic = null;
    let child;

    const settle = async (exitCode, signal) => {
      if (closed) return;
      closed = true;
      if (timeoutTimer) clearTimeout(timeoutTimer);
      if (closeStreamsTimer) clearTimeout(closeStreamsTimer);
      if (forceSettleTimer) clearTimeout(forceSettleTimer);
      const stdout = Buffer.concat(chunks.stdout).toString("utf8");
      const stderr = Buffer.concat(chunks.stderr).toString("utf8");
      const output = stdout + (stdout && stderr ? "\n" : "") + stderr;
      // EXPECT and the recorded fingerprint both use this combined string, so it
      // is held to the same 1 MiB ceiling as the raw capture: invalid-byte
      // replacement and the separator can push it over even when the child
      // emitted exactly MAX_OUTPUT_BYTES.
      const fingerprint = outputFingerprint(output);
      const normalizedOverflow = fingerprint.bytes > MAX_OUTPUT_BYTES;
      const overflow = rawOverflow || normalizedOverflow;
      const match = timedOut || overflow || spawnError
        ? { matched: false }
        : await safeRegexMatch(task.gate.expectation, output);
      const cleanupSuffix = cleanupDiagnostic ? "; cleanup: " + cleanupDiagnostic : "";
      const error = timedOut ? "timed out after " + timeoutSeconds + "s" + cleanupSuffix
        : overflow ? "output exceeded " + MAX_OUTPUT_BYTES + " bytes" +
          (rawOverflow ? "" : " after stdout/stderr UTF-8 combination") + cleanupSuffix
          : spawnError ? spawnError.message
            : match.error || null;
      done({
        ...task, output, outputFingerprint: fingerprint,
        exitCode, signal, matched: Boolean(match.matched), error,
        ok: !error && exitCode === 0 && Boolean(match.matched),
      });
    };

    const stopChild = () => {
      if (closeStreamsTimer) return;
      const cleanup = terminateProcessTree(child);
      cleanupDiagnostic = cleanup.diagnostic;
      // A descendant that escaped the shell can keep inherited pipes open
      // forever. Give stdio a short grace period to drain, then close it, and
      // settle regardless once the bounded cleanup attempt is over.
      closeStreamsTimer = setTimeout(() => {
        try { child.stdout.destroy(); } catch { /* closed */ }
        try { child.stderr.destroy(); } catch { /* closed */ }
      }, 1000);
      forceSettleTimer = setTimeout(() => {
        try { child.stdout.destroy(); } catch { /* closed */ }
        try { child.stderr.destroy(); } catch { /* closed */ }
        try { child.unref(); } catch { /* unavailable */ }
        settle(null, null);
      }, 1500);
    };

    const capture = (stream, chunk) => {
      const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
      const remaining = MAX_OUTPUT_BYTES - bytes;
      if (remaining > 0) chunks[stream].push(buffer.subarray(0, remaining));
      bytes += buffer.length;
      if (bytes > MAX_OUTPUT_BYTES && !rawOverflow) {
        rawOverflow = true;
        stopChild();
      }
    };

    try {
      child = spawn(process.execPath, [CHECK_SUPERVISOR, SHELL, task.gate.check], {
        cwd: task.cwd,
        shell: false,
        detached: true,
        env: process.env,
        stdio: ["ignore", "pipe", "pipe"],
      });
    } catch (error) {
      done({
        ...task, ok: false, output: "", outputFingerprint: outputFingerprint(""),
        exitCode: null, signal: null, matched: false, error: error.message,
      });
      return;
    }
    child.stdout.on("data", (chunk) => capture("stdout", chunk));
    child.stderr.on("data", (chunk) => capture("stderr", chunk));
    child.once("error", (error) => { spawnError = error; });
    timeoutTimer = setTimeout(() => {
      timedOut = true;
      stopChild();
    }, timeoutSeconds * 1000);
    child.once("close", settle);
  });
}

const pending = [];
for (const ledger of ledgers) {
  for (const gate of ledger.doc.gates) {
    if (ledger.doc.abandoned.has(gate.id) || !gate.check) continue;
    const state = gateState(gate, ledger.doc.abandoned);
    if (!opt.reverify && state === "met") continue;
    const cwd = resolvedGateCwd(gate, ledger.file);
    try {
      if (!statSync(cwd).isDirectory()) failUsage("gate " + qualify(ledger.file, gate.id) + " CWD is not a directory: " + cwd);
    } catch (error) {
      if (error.code === "ENOENT") failUsage("gate " + qualify(ledger.file, gate.id) + " CWD does not exist: " + cwd);
      failUsage("cannot inspect gate CWD " + cwd + ": " + error.message);
    }
    pending.push({
      file: ledger.file,
      gate,
      cwd,
      wasMet: state === "met",
      definitionDigest: gateDefinitionDigest(gate),
    });
  }
}

for (const task of pending) {
  console.log("  RUN  " + qualify(task.file, task.gate.id) + " shell=" + SHELL + " cwd=" + task.cwd + " PATH=" + pathTranscript);
}
const results = [];
for (const task of pending) results.push(await runCheck(task));
for (const result of results) {
  const fingerprint = result.outputFingerprint;
  const outputSummary = result.ok
    ? "sha256=" + fingerprint.sha256 + "; bytes=" + fingerprint.bytes
    : failureOutput(result.output);
  const outcome = "exit=" + (result.exitCode === null ? "none" : result.exitCode) +
    (result.signal ? " signal=" + result.signal : "") +
    "; EXPECT=" + (result.matched ? "matched" : "not matched") +
    "; output=" + outputSummary;
  if (result.ok) {
    console.log("  PASS " + qualify(result.file, result.gate.id) + ": " + result.gate.title);
    console.log("       " + outcome);
  } else {
    console.log("  FAIL " + qualify(result.file, result.gate.id) + ": " + result.gate.title);
    console.log("       " + (result.error ? result.error + "; " : "") + outcome);
  }
}

function failureOutput(output, max = 480) {
  const lines = String(output).split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length <= 8) return (lines.join(" | ") || "(no output)").slice(0, max);
  const summary = [...lines.slice(0, 6), "...", ...lines.slice(-2)].join(" | ");
  return summary.slice(0, max);
}

function evidenceFor(result) {
  const clean = (value) => terminalSafe(value).replace(/[\r\n\t]+/g, " ");
  const fingerprint = result.outputFingerprint;
  // The definition binding and the output fingerprint come first, so the cap
  // truncates only transcript detail, never what decides currentness.
  return (automaticEvidencePrefix(result.definitionDigest) +
    " exit=0; EXPECT=matched; output-sha256=" + fingerprint.sha256 +
    "; output-bytes=" + fingerprint.bytes + "; shell=" + SHELL +
    "; cwd=" + clean(result.cwd) + "; path=" + pathEvidence).slice(0, MAX_AUTOMATIC_EVIDENCE_CHARS);
}

// A failed criterion records why it failed, in the fields and order a pass records plus
// the output summary the console line already prints. It carries no `automatic-evidence`
// prefix: that prefix binds a pass to the definition that produced it, and a failure
// passes nothing. Without this line a red that did not repeat could never be explained.
// The checkbox stays the authority on met: every reader (`gateState`, and
// `verify-ticket.py`'s tally) counts a criterion met only when it is ticked, so evidence
// on an unticked line cannot pass it.
function failureEvidenceFor(result) {
  const clean = (value) => terminalSafe(value).replace(/[\r\n\t]+/g, " ");
  const fingerprint = result.outputFingerprint;
  return ("exit=" + (result.exitCode === null ? "none" : result.exitCode) +
    (result.signal ? "; signal=" + clean(result.signal) : "") +
    (result.error ? "; error=" + clean(result.error) : "") +
    "; EXPECT=" + (result.matched ? "matched" : "not matched") +
    "; output-sha256=" + fingerprint.sha256 + "; output-bytes=" + fingerprint.bytes +
    "; shell=" + SHELL + "; cwd=" + clean(result.cwd) + "; path=" + pathEvidence +
    "; output=" + clean(failureOutput(result.output))).slice(0, MAX_AUTOMATIC_EVIDENCE_CHARS);
}

function insertOrUpdateEvidence(doc, gate, value) {
  if (gate.evidenceLine !== -1) {
    const indent = (doc.lines[gate.evidenceLine].match(/^\s*/) || ["  "])[0];
    doc.lines[gate.evidenceLine] = indent + "EVIDENCE: " + value;
    return;
  }
  // attrEnd is past the gate's last attribute line, and past a fenced CHECK's closer.
  doc.lines.splice(gate.attrEnd, 0, "  EVIDENCE: " + value);
}

// Each result is applied to a fresh parse, because an inserted EVIDENCE line moves
// the line numbers of every criterion below it.
for (const result of results) {
  const doc = parseGates(readLedgerFile(result.file));
  const gate = doc.gates.find((each) => each.id === result.gate.id);
  if (result.ok) {
    doc.lines[gate.line] = doc.lines[gate.line].replace(/^- \[( |x|X)\]/, "- [x]");
    insertOrUpdateEvidence(doc, gate, evidenceFor(result));
  } else {
    doc.lines[gate.line] = doc.lines[gate.line].replace(/^- \[(x|X)\]/, "- [ ]");
    insertOrUpdateEvidence(doc, gate, failureEvidenceFor(result));
  }
  try { writeFileSync(result.file, formatDocument(doc)); }
  catch (error) {
    console.error("gate-check: cannot update " + result.file + ": " + error.message);
    process.exit(2);
  }
}

ledgers = files.map(loadLedger);
let totalMet = 0;
const unmetIds = [];
const abandonedIds = [];
const reverified = results.filter((result) => result.wasMet).length;

for (const ledger of ledgers) {
  for (const gate of ledger.doc.gates) {
    const state = gateState(gate, ledger.doc.abandoned);
    if (state === "abandoned") abandonedIds.push(qualify(ledger.file, gate.id));
    else if (state === "met") totalMet++;
    else unmetIds.push(qualify(ledger.file, gate.id));
  }
  console.log(basename(ledger.file) + ": " + ledger.doc.gates.length + " gates");
}

const verifyNote = opt.reverify
  ? ", reran: " + results.length + ", previously met reverified: " + reverified
  : "";
const list = (ids) => "  " + ids.slice(0, 12).join(", ") + (ids.length > 12 ? ", +" + (ids.length - 12) + " more" : "");
if (!unmetIds.length && !abandonedIds.length) {
  console.log("ALL MET (" + totalMet + " met" + verifyNote + ")");
  process.exit(0);
}
if (abandonedIds.length) {
  console.log("HANDOFF REQUIRED: " + abandonedIds.length + " abandoned (met: " + totalMet +
    (unmetIds.length ? ", unmet: " + unmetIds.length : "") + verifyNote + ")");
  console.log(list(abandonedIds));
}
if (unmetIds.length) {
  console.log("UNMET: " + unmetIds.length + " (met: " + totalMet +
    (abandonedIds.length ? ", abandoned: " + abandonedIds.length : "") + verifyNote + ")");
  console.log(list(unmetIds));
}
process.exit(1);
