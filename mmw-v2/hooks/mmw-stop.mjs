#!/usr/bin/env node
// Claude Code Stop hook for one unlazy pipeline. Zero dependencies. Node 16+.
//
// mmw：本层的完成拦截。原件：unlazy scripts/stop-hook.mjs @265fbd5。精确修改：
//   - 判定物换成 worktree 根的 .mmw-ticket-state.json（与 landing-closeout 的 implement 共享契约：
//     gates[] 里存在 checked:false 即未清），不再解析 GATES.md 账本与 dispatch；
//   - 文件缺失、解析失败一律放行（契约要求；unlazy 原件把坏账本算作待办）；
//   - stdin 改为带超时的异步读取（ponytail #443：宿主不关 stdin 时 readFileSync(0) 会挂死）；
//   - block 输出经 mmw-runtime.js 分流成各宿主的形状；
//   - 去掉 --scope 与 pipeline 相关分支。
// 循环保护（MAX_BLOCKS、进度哈希、按会话计数）逐字保留。

import { existsSync, readFileSync, unlinkSync } from "node:fs";
import { join, resolve } from "node:path";
import { createRequire } from "node:module";
import { hookStatePath, sha256, withFileLock, writeAtomic } from "./lib/state.mjs";

const require = createRequire(import.meta.url);
const { writeHookOutput } = require("./mmw-runtime.js");

const MAX_BLOCKS = 6;
const TICKET_STATE_FILE = ".mmw-ticket-state.json";
const STDIN_TIMEOUT_MS = 1000;
const safeHostText = (value, max = 500) => String(value)
  .replace(/[\u0000-\u001f\u007f]/g, " ")
  .replace(/\s+/g, " ")
  .trim()
  .slice(0, max);

function normalizeHookState(value) {
  if (!value || typeof value !== "object" || Array.isArray(value) || value.schema !== 1 ||
      !value.sessions || typeof value.sessions !== "object" || Array.isArray(value.sessions)) {
    return { schema: 1, sessions: {} };
  }
  const sessions = {};
  for (const [key, current] of Object.entries(value.sessions)) {
    if (!/^[a-f0-9]{24}$/.test(key) || !current || typeof current !== "object" || Array.isArray(current) ||
        !/^[a-f0-9]{24}$/.test(String(current.hash || "")) ||
        !Number.isInteger(current.blocks) || current.blocks < 0 ||
        typeof current.updatedAt !== "string" || Number.isNaN(Date.parse(current.updatedAt))) continue;
    sessions[key] = current;
  }
  return { schema: 1, sessions };
}

const allow = (message) => {
  if (message) console.log(JSON.stringify({ systemMessage: message }));
  process.exit(0);
};

// mmw: Never block the session (#443): recover on stdin error or a short fallback.
function readStdin(timeoutMs) {
  return new Promise((done) => {
    let input = "";
    let finished = false;
    const finish = () => { if (finished) return; finished = true; done(input); };
    process.stdin.on("data", (chunk) => { input += chunk; });
    process.stdin.on("end", finish);
    process.stdin.on("error", finish);
    setTimeout(finish, timeoutMs).unref();
  });
}

let payload = {};
try { payload = JSON.parse((await readStdin(STDIN_TIMEOUT_MS)).replace(/^\uFEFF/, "") || "{}"); }
catch { allow(null); }
if (!payload || typeof payload !== "object" || Array.isArray(payload)) payload = {};

// mmw: cwd 字段各家不同——Claude/Codex 给 cwd，Grok 给 workspaceRoot（另有环境变量），Cursor 给 workspace_roots[]。
const root = resolve(
  (typeof payload.cwd === "string" && payload.cwd) ||
  (typeof payload.workspaceRoot === "string" && payload.workspaceRoot) ||
  (Array.isArray(payload.workspace_roots) && typeof payload.workspace_roots[0] === "string" && payload.workspace_roots[0]) ||
  process.env.GROK_WORKSPACE_ROOT ||
  process.cwd());
const sessionId = payload.session_id || payload.sessionId || payload.conversation_id || process.env.GROK_SESSION_ID || "anonymous";
const sessionKey = sha256(String(sessionId)).slice(0, 24);

const statePath = hookStatePath(root);

async function clearSessionState() {
  if (!existsSync(statePath)) return;
  try {
    await withFileLock(root, statePath, () => {
      let state = { schema: 1, sessions: {} };
      try { state = JSON.parse(readFileSync(statePath, "utf8")); } catch { /* replace invalid local state */ }
      state = normalizeHookState(state);
      delete state.sessions[sessionKey];
      if (!Object.keys(state.sessions).length) {
        try { unlinkSync(statePath); } catch { /* already absent */ }
      } else writeAtomic(statePath, JSON.stringify(state, null, 2) + "\n", { root });
    }, { timeoutMs: 10000 });
  } catch {
    // State cleanup must never trap a session after the gates are complete.
  }
}

const ticketStatePath = join(root, TICKET_STATE_FILE);

if (!existsSync(ticketStatePath)) {
  await clearSessionState();
  allow(null);
}

// mmw: 状态文件读不到或不是契约形状 → 放行（fail-open）。
let ticketState;
try { ticketState = JSON.parse(readFileSync(ticketStatePath, "utf8").replace(/^\uFEFF/, "")); }
catch { allow(null); }
if (!ticketState || typeof ticketState !== "object" || Array.isArray(ticketState) || !Array.isArray(ticketState.gates)) {
  allow(null);
}

const unmet = [];
// The loop guard compares resolved gate state between stops, not raw bytes.
// Byte comparison counted any edit as progress: a comment, a reflowed line, or
// the checker rewriting an evidence line with a fresh PATH hash. That rearmed
// the guard indefinitely, so the six-block release could only ever fire for an
// agent doing literally nothing, which is the one case least in need of it.
// Dispatch issue strings encode only canonical state and counts, not raw JSON
// bytes or timestamps, so metadata-only edits do not reset the same guard.
const resolved = [];
for (const [index, gate] of ticketState.gates.entries()) {
  const id = "G" + (index + 1);
  const state = gate && typeof gate === "object" && gate.checked === true ? "met" : "unmet";
  resolved.push(id + "=" + state);
  if (state === "unmet") unmet.push(id + " " + safeHostText(gate && gate.text ? gate.text : "", 80));
}

if (!unmet.length) {
  await clearSessionState();
  allow(null);
}

const progressHash = sha256(resolved.sort().join("\0")).slice(0, 24);
let sessionState;
try {
  sessionState = await withFileLock(root, statePath, () => {
    let state = { schema: 1, sessions: {} };
    try { state = JSON.parse(readFileSync(statePath, "utf8")); } catch { /* new or corrupt local state */ }
    state = normalizeHookState(state);
    let current = state.sessions[sessionKey];
    if (!current || current.hash !== progressHash) current = { hash: progressHash, blocks: 0 };
    current.blocks += 1;
    current.updatedAt = new Date().toISOString();
    state.sessions[sessionKey] = current;
    // Bound abandoned session debris without mixing counters between sessions.
    const entries = Object.entries(state.sessions).sort((a, b) => String(b[1].updatedAt).localeCompare(String(a[1].updatedAt)));
    state.sessions = Object.fromEntries(entries.slice(0, 64));
    writeAtomic(statePath, JSON.stringify(state, null, 2) + "\n", { root });
    return current;
  }, { timeoutMs: 10000 });
} catch (error) {
  allow("mmw: could not update the serialized hook state (" + safeHostText(error.message) + "); not blocking to avoid a trap.");
}

const where = Number.isInteger(ticketState.ticket) ? " [ticket #" + ticketState.ticket + "]" : "";
const outstanding = unmet.map((item) => safeHostText(item));
if (sessionState.blocks > MAX_BLOCKS) {
  allow("mmw: releasing after " + MAX_BLOCKS + " blocks without gate progress" + where +
    "; " + outstanding.length + " item(s) remain (" + outstanding.slice(0, 4).join(", ") + ").");
}

const list = outstanding.slice(0, 5).join(", ") + (outstanding.length > 5 ? ", +" + (outstanding.length - 5) + " more" : "");
try {
  writeHookOutput("Stop", "worker",
    "mmw" + where + ": " + outstanding.length + " gate(s) still unchecked in " + TICKET_STATE_FILE + ": " + list +
    ". Run each gate's check, record its evidence, and set checked:true before finishing.");
} catch {
  // Silent fail — a stdout error at hook exit must not surface as a hook failure.
}
process.exit(0);
