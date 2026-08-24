#!/usr/bin/env node
// MMW — SubagentStart 纪律注入 hook。
// 原件：ponytail hooks/ponytail-subagent.js @2ed6c52。精确修改：去掉模式标志（本层无模式，
// 总是注入）；环境变量改名 MMW_SUBAGENT_MATCHER；新增 MMW_VERIFIER_MATCHER——agent_type
// 命中时注入复验者块（discipline/verifier.md），否则注入工人块。
//
// SessionStart context is parent-thread only and never reaches subagents, so
// without this every Task-spawned agent runs ponytail-unaware (issue #252).
// When ponytail mode is active, inject the same ruleset into each subagent.
//
// Scoping (opt-in, issue #506): set MMW_SUBAGENT_MATCHER to a regex and
// the ruleset is injected only into subagents whose agent_type matches. The
// regex is unanchored and case-insensitive — "explore|general" matches either,
// "^general$" is exact. Unset means inject into every subagent, as before.

const { getDisciplineInstructions } = require('./mmw-instructions');
const { writeHookOutput } = require('./mmw-runtime');

function inject(role) {
  try {
    writeHookOutput('SubagentStart', role, getDisciplineInstructions(role));
  } catch (e) {
    // Silent fail — a stdout error at hook exit must not surface as a hook failure.
  }
}

// A bad regex must never crash the hook; treat it as "no matcher" and inject.
let matcherRe = null;
try {
  if (process.env.MMW_SUBAGENT_MATCHER) {
    matcherRe = new RegExp(process.env.MMW_SUBAGENT_MATCHER, 'i');
  }
} catch (e) {
  matcherRe = null;
}

// mmw: 复验者的 agent_type 命中这个正则就注入复验者块。默认 "verifier"；坏正则当没设。
let verifierRe = null;
try {
  verifierRe = new RegExp(process.env.MMW_VERIFIER_MATCHER || 'verifier', 'i');
} catch (e) {
  verifierRe = null;
}

// No matcher → keep the original synchronous, stdin-independent path. On Windows
// the PowerShell `if {}` wrapper can swallow the piped JSON so stdin 'end' never
// fires (#443); the default path must not wait on stdin or it would stall every
// subagent spawn.
// mmw: 角色分流要读 agent_type，所以只有两个正则都没有时才走这条不读 stdin 的路。
if (!matcherRe && !verifierRe) {
  inject('worker');
  process.exit(0);
}

// Matcher set → read agent_type from stdin and skip only on a definite
// mismatch. Missing/unparseable agent_type, a stdin error, or the timeout all
// fail open (inject), so scoping never silently drops the persona.
let input = '';
let done = false;

function finish() {
  if (done) return;
  done = true;

  let agentType = '';
  try {
    // Strip UTF-8 BOM some shells prepend when piping (breaks JSON.parse)
    const payload = JSON.parse(input.replace(/^﻿/, ''));
    // mmw: Cursor 的字段名是 subagent_type；Grok 是 agentType / subagentType。
    agentType = String(payload.agent_type || payload.subagent_type || payload.subagentType || payload.agentType || '').trim();
  } catch (e) {
    // Unparseable payload — fall through and inject to be safe.
  }
  if (agentType && matcherRe && !matcherRe.test(agentType)) {
    process.exit(0);
  }
  inject(agentType && verifierRe && verifierRe.test(agentType) ? 'verifier' : 'worker');
}

process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', finish);
// Never block the session (#443): recover on stdin error or a short fallback.
process.stdin.on('error', () => { finish(); process.exit(0); });
setTimeout(() => { finish(); process.exit(0); }, 1000).unref();
