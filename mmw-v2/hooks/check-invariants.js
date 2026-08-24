#!/usr/bin/env node
// 承重句机械校验：invariants.json 里的每条短语逐字存在于它的每个权威位置。
// 原件：ponytail scripts/check-rule-copies.js @2ed6c52 的 INVARIANTS 段。精确修改：去掉副本
// 逐字节比对段（本层没有整份副本，只有承重句）；短语清单从 invariants.json 读而不是写死；
// 加 --root <dir> 供测试指向一份改坏了的副本。
const fs = require('fs');
const path = require('path');

const rootArg = process.argv.indexOf('--root');
const root = rootArg === -1 ? path.join(__dirname, '..', '..') : path.resolve(process.argv[rootArg + 1]);
const listPath = path.join(__dirname, 'invariants.json');

function read(relPath) {
  return fs.readFileSync(path.join(root, relPath), 'utf8').replace(/\r\n/g, '\n').trim();
}

// SKILL.md is the runtime source of truth and is longer than the compact body,
// so it cannot be byte-compared. ponytail: canary, not full equality. Assert the
// load-bearing rules survive verbatim in both the source and AGENTS.md. Changing
// a rule's wording trips this, which is the reminder to propagate it everywhere.
// Upgrade path: generate the copies from SKILL.md if this ever misses a real drift.
const INVARIANTS = JSON.parse(fs.readFileSync(listPath, 'utf8')).invariants;

let failed = false;
let checked = 0;
let pending = 0;

for (const entry of INVARIANTS) {
  if (entry.pending || !entry.phrase || !entry.files.length) {
    pending += 1;
    console.log(`pending invariant (not checked): ${entry.note} — ${entry.pending || 'no phrase or location yet'}`);
    continue;
  }
  checked += 1;
  for (const label of entry.files) {
    let text;
    try {
      text = read(label);
    } catch (e) {
      console.error(`${label} is unreadable for rule invariant: "${entry.phrase}"`);
      failed = true;
      continue;
    }
    if (!text.includes(entry.phrase)) {
      console.error(`${label} is missing rule invariant: "${entry.phrase}"`);
      failed = true;
    }
  }
}

if (failed) {
  console.error('Update the copied rule text so the shared rules match.');
  process.exit(1);
}

console.log(`${checked} rule invariants present in their authoritative files; ${pending} pending.`);
