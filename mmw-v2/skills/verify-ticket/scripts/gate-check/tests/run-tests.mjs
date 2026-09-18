#!/usr/bin/env node
// run-tests.mjs : behavioural tests for the unlazy enforcement scripts.
// Zero dependencies, cross-platform (every CHECK command is a `node -e`).
//
//   node tests/run-tests.mjs            run all
//   node tests/run-tests.mjs scope      run tests whose name contains "scope"
//
// Prints "N/N passed" on success, which is the string CI and the repo's own
// gates match on.

import { existsSync, mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { execFile } from "node:child_process";
import { delimiter, join, dirname } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { automaticEvidencePrefix, gateDefinitionDigest, gateState, parseGates } from "../lib/gates.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const GATE_CHECK = join(HERE, "..", "gate-check.mjs");
const filter = process.argv[2] || "";

const tests = [];
const test = (name, fn) => tests.push({ name, fn });

// ------------------------------------------------------------- helpers

function sandbox() {
  const dir = mkdtempSync(join(tmpdir(), "unlazy-test-"));
  return {
    dir,
    write(rel, text) {
      const p = join(dir, rel);
      mkdirSync(dirname(p), { recursive: true });
      writeFileSync(p, text);
      return p;
    },
    read(rel) { return readFileSync(join(dir, rel), "utf8"); },
    cleanup() { try { rmSync(dir, { recursive: true, force: true }); } catch { /* windows lag */ } },
  };
}

function run(script, args, opts = {}) {
  return new Promise((res) => {
    const child = execFile(process.execPath, [script, ...args], {
      cwd: opts.cwd, encoding: "utf8", maxBuffer: 8 * 1024 * 1024,
      env: { ...process.env, ...(opts.env || {}) },
    }, (err, stdout, stderr) => {
      res({ code: err ? (err.code ?? 1) : 0, out: (stdout || "") + (stderr || "") });
    });
    if (opts.stdin !== undefined) { child.stdin.end(opts.stdin); }
  });
}

const gate = (id, title, check, expect) =>
  "- [ ] " + id + ": " + title + "\n" +
  (check ? "  CHECK: " + check + "\n" : "") +
  (expect ? "  EXPECT: " + expect + "\n" : "") +
  "  EVIDENCE: pending\n";

const nodeEval = (js) => 'node -e "' + js.replace(/"/g, '\\"') + '"';
const echoOk = (word) => nodeEval("console.log('" + word + "')");

function assert(cond, msg) { if (!cond) throw new Error(msg); }
function assertHas(hay, needle, label) {
  assert(hay.includes(needle), (label || "output") + " missing " + JSON.stringify(needle) + "\n--- got ---\n" + hay);
}
function assertLacks(hay, needle, label) {
  assert(!hay.includes(needle), (label || "output") + " unexpectedly contains " + JSON.stringify(needle) + "\n--- got ---\n" + hay);
}

// --------------------------------------------------------------- tests

test("args: two explicit files are both processed without --timeout", async () => {
  const s = sandbox();
  try {
    s.write("gates/leaf-a.md", "# Gates: A\n\n" + gate("G1", "A", echoOk("A-OK"), "A-OK"));
    s.write("gates/leaf-b.md", "# Gates: B\n\n" + gate("G1", "B", echoOk("B-OK"), "B-OK"));
    const r = await run(GATE_CHECK, ["gates/leaf-a.md", "gates/leaf-b.md"], { cwd: s.dir });
    assertHas(r.out, "PASS leaf-a:G1");
    assertHas(r.out, "PASS leaf-b:G1");
    assertHas(r.out, "ALL MET (2 met)");
    assertHas(s.read("gates/leaf-a.md"), "- [x] G1", "leaf-a");
    assert(r.code === 0, "expected exit 0, got " + r.code);
  } finally { s.cleanup(); }
});

test("args: one explicit file never widens to the rest of the tree", async () => {
  const s = sandbox();
  try {
    s.write("gates/leaf-a.md", "# Gates: A\n\n" + gate("G1", "A", echoOk("A-OK"), "A-OK"));
    s.write("gates/leaf-b.md", "# Gates: B\n\n" + gate("G1", "B", echoOk("B-OK"), "B-OK"));
    const r = await run(GATE_CHECK, ["gates/leaf-a.md"], { cwd: s.dir });
    assertHas(r.out, "PASS leaf-a:G1");
    assertLacks(r.out, "leaf-b", "run output");
    assertHas(s.read("gates/leaf-b.md"), "- [ ] G1", "leaf-b must be untouched");
    assertHas(s.read("gates/leaf-b.md"), "EVIDENCE: pending", "leaf-b evidence must be untouched");
  } finally { s.cleanup(); }
});

test("args: unknown option is rejected instead of treated as a file", async () => {
  const s = sandbox();
  try {
    s.write("GATES.md", "# Gates\n\n" + gate("G1", "x", echoOk("OK"), "OK"));
    const r = await run(GATE_CHECK, ["--nope"], { cwd: s.dir });
    assert(r.code === 2, "expected exit 2, got " + r.code);
    assertHas(r.out, "unknown option --nope");
  } finally { s.cleanup(); }
});

test("scope: running one pipeline leaves the other pipeline alone", async () => {
  const s = sandbox();
  try {
    s.write(".unlazy/api/gates/leaf-1.md", "# Gates: api1\n\n" + gate("G1", "api", echoOk("API-OK"), "API-OK"));
    s.write(".unlazy/web/gates/leaf-1.md", "# Gates: web1\n\n" + gate("G1", "web", echoOk("WEB-OK"), "WEB-OK"));
    const r = await run(GATE_CHECK, ["--scope", "api"], { cwd: s.dir });
    assertHas(r.out, "PASS leaf-1:G1");
    assertHas(r.out, "[scope api]");
    assertHas(s.read(".unlazy/api/gates/leaf-1.md"), "- [x] G1", "api gates");
    assertHas(s.read(".unlazy/web/gates/leaf-1.md"), "- [ ] G1", "web gates must be untouched");
  } finally { s.cleanup(); }
});

test("scope: two pipelines and no scope is refused, not guessed", async () => {
  const s = sandbox();
  try {
    s.write(".unlazy/api/gates/leaf-1.md", "# Gates: api\n\n" + gate("G1", "api", echoOk("API-OK"), "API-OK"));
    s.write(".unlazy/web/gates/leaf-1.md", "# Gates: web\n\n" + gate("G1", "web", echoOk("WEB-OK"), "WEB-OK"));
    const r = await run(GATE_CHECK, [], { cwd: s.dir });
    assert(r.code === 2, "expected exit 2, got " + r.code);
    assertHas(r.out, "2 pipelines present");
    assertHas(r.out, "api");
    assertHas(r.out, "web");
    assertHas(s.read(".unlazy/api/gates/leaf-1.md"), "- [ ] G1", "api must be untouched");
    assertHas(s.read(".unlazy/web/gates/leaf-1.md"), "- [ ] G1", "web must be untouched");
  } finally { s.cleanup(); }
});

test("scope: UNLAZY_SCOPE selects the pipeline", async () => {
  const s = sandbox();
  try {
    s.write(".unlazy/api/gates/leaf-1.md", "# Gates: api\n\n" + gate("G1", "api", echoOk("API-OK"), "API-OK"));
    s.write(".unlazy/web/gates/leaf-1.md", "# Gates: web\n\n" + gate("G1", "web", echoOk("WEB-OK"), "WEB-OK"));
    const r = await run(GATE_CHECK, [], { cwd: s.dir, env: { UNLAZY_SCOPE: "web" } });
    assertHas(r.out, "[scope web]");
    assertHas(s.read(".unlazy/web/gates/leaf-1.md"), "- [x] G1", "web gates");
    assertHas(s.read(".unlazy/api/gates/leaf-1.md"), "- [ ] G1", "api must be untouched");
  } finally { s.cleanup(); }
});

test("scope: a single pipeline needs no flag", async () => {
  const s = sandbox();
  try {
    s.write(".unlazy/solo/GATES.md", "# Gates: solo\n\n" + gate("G1", "solo", echoOk("S-OK"), "S-OK"));
    const r = await run(GATE_CHECK, [], { cwd: s.dir });
    assertHas(r.out, "ALL MET (1 met) [scope solo]");
  } finally { s.cleanup(); }
});

test("scope: legacy GATES.md layout still works", async () => {
  const s = sandbox();
  try {
    s.write("GATES.md", "# Gates\n\n" + gate("G1", "legacy", echoOk("L-OK"), "L-OK"));
    const r = await run(GATE_CHECK, [], { cwd: s.dir });
    assertHas(r.out, "PASS GATES:G1");
    assertHas(r.out, "ALL MET (1 met)");
  } finally { s.cleanup(); }
});

test("state: checked box with pending evidence counts as unmet", async () => {
  const s = sandbox();
  try {
    s.write("GATES.md", "# Gates\n\n- [x] G1: claimed\n  EVIDENCE: pending\n");
    const r = await run(GATE_CHECK, ["--status"], { cwd: s.dir });
    assert(r.code === 1, "expected exit 1, got " + r.code);
    assertHas(r.out, "UNMET GATES:G1 (checked but EVIDENCE pending)");
  } finally { s.cleanup(); }
});

test("state: ABANDON is a non-success handoff, not completion", async () => {
  const s = sandbox();
  try {
    s.write("GATES.md", "# Gates\n\n- [ ] G1: impossible\n  EVIDENCE: pending\n\nABANDON: G1 upstream API removed\n");
    const r = await run(GATE_CHECK, ["--status"], { cwd: s.dir });
    assert(r.code === 1, "expected exit 1, got " + r.code);
    assertHas(r.out, "HANDOFF REQUIRED: 1 abandoned");
    assertLacks(r.out, "ALL MET");
  } finally { s.cleanup(); }
});

test("state: abandoned and mixed ledgers stay handoffs in every run mode", async () => {
  for (const args of [["--status"], [], ["--reverify"]]) {
    const s = sandbox();
    try {
      s.write("GATES.md", [
        "# Gates",
        "",
        "- [x] G1: measured outcome",
        "  EVIDENCE: checked by test",
        "",
        "- [ ] G2: impossible outcome",
        "  EVIDENCE: pending",
        "",
        "ABANDON: G2 upstream API removed",
        "",
      ].join("\n"));
      const r = await run(GATE_CHECK, args, { cwd: s.dir });
      assert(r.code === 1, "expected exit 1 for " + JSON.stringify(args) + ", got " + r.code + "\n" + r.out);
      assertHas(r.out, "HANDOFF REQUIRED: 1 abandoned");
      assertLacks(r.out, "ALL MET");
    } finally { s.cleanup(); }
  }
});

test("state: multi-file verification cannot hide one abandoned child", async () => {
  const s = sandbox();
  try {
    s.write("met.md", "# Gates\n\n- [x] G1: complete\n  EVIDENCE: checked by test\n");
    s.write("abandoned.md", "# Gates\n\n- [ ] G1: impossible\n  EVIDENCE: pending\n\nABANDON: G1 upstream removed\n");
    const r = await run(GATE_CHECK, ["--status", "met.md", "abandoned.md"], { cwd: s.dir });
    assert(r.code === 1, "expected exit 1, got " + r.code + "\n" + r.out);
    assertHas(r.out, "HANDOFF REQUIRED: 1 abandoned");
    assertHas(r.out, "abandoned:G1");
    assertLacks(r.out, "ALL MET");
  } finally { s.cleanup(); }
});

test("hierarchy: an abandoned child cannot promote its N1 parent", async () => {
  const s = sandbox();
  try {
    const child = s.write("child.md", "# Gates\n\n- [ ] G1: impossible\n  EVIDENCE: pending\n\nABANDON: G1 upstream removed\n");
    s.write("parent-oracle.mjs", [
      "import { spawnSync } from 'node:child_process';",
      "const result = spawnSync(process.execPath, [" + JSON.stringify(GATE_CHECK) + ", '--reverify', " + JSON.stringify(child) + "], { encoding: 'utf8', env: process.env });",
      "process.stdout.write((result.stdout || '') + (result.stderr || ''));",
      "process.exit(result.status === 0 ? 0 : 1);",
      "",
    ].join("\n"));
    s.write("parent.md", "# Gates: parent\n\n" + gate("N1", "child is complete", "node parent-oracle.mjs", "ALL MET"));
    const r = await run(GATE_CHECK, ["parent.md"], { cwd: s.dir });
    assert(r.code === 1, "parent unexpectedly passed\n" + r.out);
    assertHas(r.out, "FAIL parent:N1");
    assertHas(r.out, "HANDOFF REQUIRED");
    assertLacks(r.out, "PASS parent:N1");
    assertHas(s.read("parent.md"), "- [ ] N1");
  } finally { s.cleanup(); }
});

test("state: unmet gates are reported with file-qualified ids", async () => {
  const s = sandbox();
  try {
    s.write(".unlazy/api/gates/leaf-1.md", "# Gates: 1\n\n" + gate("G1", "a", null, null));
    s.write(".unlazy/api/gates/leaf-2.md", "# Gates: 2\n\n" + gate("G1", "b", null, null));
    const r = await run(GATE_CHECK, ["--scope", "api", "--status"], { cwd: s.dir });
    assertHas(r.out, "leaf-1:G1");
    assertHas(r.out, "leaf-2:G1");
  } finally { s.cleanup(); }
});

test("run: a concurrent edit to another gate in the same file survives", async () => {
  const s = sandbox();
  try {
    // G1 is slow and will be flipped by gate-check; G2 is manual and gets its
    // evidence filled in by hand while that check is still running.
    s.write("GATES.md",
      "# Gates\n\n" +
      "- [ ] G1: slow\n  CHECK: " + nodeEval("setTimeout(()=>console.log('SLOW-OK'),2500)") +
      "\n  EXPECT: SLOW-OK\n  EVIDENCE: pending\n\n" +
      "- [ ] G2: manual\n  EVIDENCE: pending\n");
    const running = run(GATE_CHECK, [], { cwd: s.dir });
    await new Promise(r => setTimeout(r, 800));
    const text = s.read("GATES.md")
      .replace("- [ ] G2: manual\n  EVIDENCE: pending", "- [x] G2: manual\n  EVIDENCE: measured 47 rows, threadAnalysis.ts:88");
    s.write("GATES.md", text);
    await running;
    const after = s.read("GATES.md");
    assertHas(after, "- [x] G1", "G1 should be flipped by the checker");
    assertHas(after, "measured 47 rows", "the hand edit to G2 must not be clobbered");
    assertLacks(after, "G2: manual\n  EVIDENCE: pending", "G2 must not be reverted");
  } finally { s.cleanup(); }
});

test("checks: CWD runs a check in the directory it names", async () => {
  const s = sandbox();
  try {
    s.write("sub/marker.txt", "here\n");
    s.write("GATES.md", "# Gates\n\n" +
      "- [ ] G1: in sub\n  CHECK: " + nodeEval("console.log(require('fs').readFileSync('marker.txt','utf8'))") +
      "\n  EXPECT: here\n  CWD: sub\n  EVIDENCE: pending\n");
    const r = await run(GATE_CHECK, [], { cwd: s.dir });
    assertHas(r.out, "ALL MET (1 met)");
  } finally { s.cleanup(); }
});

test("leases: overlapping OWNS across pipelines is refused", async () => {
  const s = sandbox();
  try {
    s.write(".unlazy/api/gates/leaf-1.md", "OWNS: src/shared/**\n\n# Gates\n\n" + gate("G1", "a", null, null));
    s.write(".unlazy/web/gates/leaf-1.md", "OWNS: src/shared/util.ts\n\n# Gates\n\n" + gate("G1", "b", null, null));
    const a = await run(GATE_CHECK, ["--scope", "api", "--leaf", "leaf-1", "--claim"], { cwd: s.dir });
    assertHas(a.out, "CLAIMED 1 path(s) for api/leaf-1");
    const b = await run(GATE_CHECK, ["--scope", "web", "--leaf", "leaf-1", "--claim"], { cwd: s.dir });
    assert(b.code === 3, "expected exit 3 on conflict, got " + b.code);
    assertHas(b.out, "CONFLICT src/shared/util.ts overlaps src/shared/** held by api/leaf-1");
    assertHas(b.out, "CLAIM REFUSED");
  } finally { s.cleanup(); }
});

test("leases: disjoint OWNS both succeed, and release frees them", async () => {
  const s = sandbox();
  try {
    s.write(".unlazy/api/gates/leaf-1.md", "OWNS: src/api/**\n\n# Gates\n\n" + gate("G1", "a", null, null));
    s.write(".unlazy/api/gates/leaf-2.md", "OWNS: src/web/**\n\n# Gates\n\n" + gate("G1", "b", null, null));
    const a = await run(GATE_CHECK, ["--scope", "api", "--leaf", "leaf-1", "--claim"], { cwd: s.dir });
    const b = await run(GATE_CHECK, ["--scope", "api", "--leaf", "leaf-2", "--claim"], { cwd: s.dir });
    assert(a.code === 0 && b.code === 0, "disjoint claims should both succeed");
    assertHas(b.out, "CLAIMED 1 path(s) for api/leaf-2");
    const rel = await run(GATE_CHECK, ["--scope", "api", "--release"], { cwd: s.dir });
    assertHas(rel.out, "released 2 lease(s)");
  } finally { s.cleanup(); }
});

test("status log: appends, and appends survive concurrency", async () => {
  const s = sandbox();
  try {
    s.write(".unlazy/api/gates/leaf-1.md", "# Gates\n\n" + gate("G1", "a", null, null));
    await Promise.all([
      run(GATE_CHECK, ["--scope", "api", "--log", "leaf-1 started"], { cwd: s.dir }),
      run(GATE_CHECK, ["--scope", "api", "--log", "leaf-2 started"], { cwd: s.dir }),
      run(GATE_CHECK, ["--scope", "api", "--log", "leaf-3 started"], { cwd: s.dir }),
    ]);
    const log = s.read(".unlazy/api/status.log");
    for (const n of [1, 2, 3]) assertHas(log, "leaf-" + n + " started", "status log");
  } finally { s.cleanup(); }
});

test("evidence: a failing criterion records why it failed, not pending", async () => {
  const s = sandbox();
  try {
    const failing = nodeEval("console.log('line-one'); console.log('the-real-reason'); process.exit(3)");
    s.write("GATES.md", "# Gates\n\n" + gate("G1", "fails on purpose", failing, "never-printed"));
    const r = await run(GATE_CHECK, ["GATES.md"], { cwd: s.dir });
    const led = s.read("GATES.md");
    assert(r.code !== 0, "a failing criterion must still fail the run, got exit " + r.code);
    assertHas(led, "- [ ] G1", "a failed criterion stays unchecked");
    assertLacks(led, "EVIDENCE: pending", "ledger");
    assertHas(led, "exit=3", "ledger");
    assertHas(led, "EXPECT=not matched", "ledger");
    assertHas(led, "the-real-reason", "ledger");
  } finally { s.cleanup(); }
});

test("evidence: a reverify that turns a met criterion red records the failure, not pending", async () => {
  const s = sandbox();
  try {
    const failing = nodeEval("console.log('regressed-here'); process.exit(1)");
    s.write("GATES.md", "# Gates\n\n- [x] G1: was green\n  CHECK: " + failing +
      "\n  EXPECT: never-printed\n  EVIDENCE: exit=0; shell=/bin/sh; EXPECT=matched\n");
    const r = await run(GATE_CHECK, ["--reverify", "GATES.md"], { cwd: s.dir });
    const led = s.read("GATES.md");
    assert(r.code !== 0, "a regressed criterion must still fail the run, got exit " + r.code);
    assertHas(led, "- [ ] G1", "a regressed criterion is unchecked");
    assertLacks(led, "EVIDENCE: pending", "ledger");
    assertLacks(led, "EXPECT=matched", "the old pass evidence must not survive a failed reverify");
    assertHas(led, "exit=1", "ledger");
    assertHas(led, "regressed-here", "ledger");
  } finally { s.cleanup(); }
});

// The four below are upstream's evidence-binding and output-cap cases (hardening-tests.mjs
// at 1667149), with the approval steps taken out and a failed run expected to record its
// failure rather than `pending`.

test("evidence: the definition digest is fixed and only exact current evidence is met", async () => {
  const parsed = parseGates([
    "- [x] G1: digest fixture",
    "  CHECK: printf \"token-b\\n\"",
    "  EXPECT: token-c",
    "  EVIDENCE: pending",
    "",
  ].join("\n"));
  assert(!parsed.errors.length, parsed.errors.join("; "));
  const runnable = parsed.gates[0];
  const digest = gateDefinitionDigest(runnable);
  assert(digest === "544a096dd6735f1168b04cb00c40b2d7d8889c656e383d95ee6977ea90813ab5",
    "definition digest golden vector changed: " + digest);
  const prefix = automaticEvidencePrefix(digest);
  const state = (evidence) => gateState({ ...runnable, checked: true, evidence }, new Map());
  const success = prefix + " exit=0; EXPECT=matched; output-sha256=" + "a".repeat(64) +
    "; output-bytes=0; shell=/bin/sh";
  assert(state(success) === "met", "exact current evidence was not met");
  for (const evidence of [
    "pending",
    "exit=0; shell=/bin/sh; cwd=/tmp; EXPECT=matched",
    "automatic-evidence=v1; definition-sha256=" + "b".repeat(64) + "; exit=0",
    prefix + " exit=1; EXPECT=not matched; output-sha256=" + "a".repeat(64) + "; output-bytes=0;",
    success + "x".repeat(901),
    "reviewed by owner",
  ]) {
    assert(state(evidence) !== "met", "stale or unbound evidence was met: " + JSON.stringify(evidence));
  }
  assert(gateDefinitionDigest({ ...runnable, cwd: "." }) !== digest, "omitted CWD and CWD: . collided");
  assert(gateDefinitionDigest({ ...runnable, id: "RENAMED", title: "copy edited" }) === digest,
    "id or title changed the definition digest");
  assert(gateState({ ...runnable, checked: false, evidence: success }, new Map()) === "unmet",
    "unchecked current evidence became met");
});

test("evidence: a changed CHECK makes old evidence stale and a rerun replaces it", async () => {
  const s = sandbox();
  try {
    s.write("GATES.md", gate("G1", "bound evidence", echoOk("TOKEN-A"), "TOKEN-A"));
    let r = await run(GATE_CHECK, ["GATES.md"], { cwd: s.dir });
    assert(r.code === 0, r.out);
    let led = s.read("GATES.md");
    const first = (led.match(/definition-sha256=([a-f0-9]{64});/) || [])[1];
    assert(first, "a pass carries no definition digest\n" + led);
    assertHas(led, "EVIDENCE: automatic-evidence=v1; definition-sha256=" + first + "; exit=0;");

    r = await run(GATE_CHECK, ["--status", "GATES.md"], { cwd: s.dir, env: { PATH: "" } });
    assert(r.code === 0, "status needed a shell or PATH\n" + r.out);
    assertHas(r.out, "ALL MET (1 met)");

    s.write("GATES.md", led.replace(echoOk("TOKEN-A"), echoOk("TOKEN-B")));
    r = await run(GATE_CHECK, ["--status", "GATES.md"], { cwd: s.dir });
    assert(r.code === 1, r.out);
    assertHas(r.out, "checked but automatic evidence is stale or unbound");
    r = await run(GATE_CHECK, ["GATES.md"], { cwd: s.dir });
    assert(r.code === 1, r.out);
    led = s.read("GATES.md");
    assertHas(led, "- [ ] G1: bound evidence");
    assertLacks(led, "automatic-evidence=", "a failed rerun of stale evidence");
    assertHas(led, "EXPECT=not matched", "ledger");

    s.write("GATES.md", led.replace("EXPECT: TOKEN-A", "EXPECT: TOKEN-B"));
    r = await run(GATE_CHECK, ["GATES.md"], { cwd: s.dir });
    assert(r.code === 0, r.out);
    led = s.read("GATES.md");
    const second = (led.match(/definition-sha256=([a-f0-9]{64});/) || [])[1];
    assert(second && second !== first, "an edited pass kept the old digest\n" + led);

    s.write("GATES.md", led.replace(/EVIDENCE: .*$/m, "EVIDENCE: exit=0; shell=old-writer; EXPECT=matched"));
    r = await run(GATE_CHECK, ["GATES.md"], { cwd: s.dir });
    assert(r.code === 0, "legacy evidence was not rerun and migrated\n" + r.out);
    assertHas(s.read("GATES.md"), "EVIDENCE: automatic-evidence=v1; definition-sha256=" + second + ";");
  } finally { s.cleanup(); }
});

test("evidence: a long transcript cannot truncate the definition or output digest", async () => {
  if (process.platform === "win32") return;
  const s = sandbox();
  try {
    const deep = Array.from({ length: 22 }, (_, index) =>
      "segment-" + String(index).padStart(2, "0") + "-" + "x".repeat(18)).join("/");
    s.write(deep + "/check.mjs", "console.log('LONG-OK');\n");
    s.write("GATES.md", gate("G1", "long evidence transcript",
      JSON.stringify(process.execPath) + " check.mjs", "LONG-OK").replace("  EVIDENCE:", "  CWD: " + deep + "\n  EVIDENCE:"));
    const longPath = Array(120).fill(dirname(process.execPath)).join(delimiter);
    const r = await run(GATE_CHECK, ["GATES.md"], { cwd: s.dir, env: { PATH: longPath } });
    assert(r.code === 0, r.out);
    const line = s.read("GATES.md").split(/\r?\n/).find((l) => l.includes("EVIDENCE:"));
    assert(line.length <= "  EVIDENCE: ".length + 900, "evidence cap exceeded: " + line.length);
    assert(/^  EVIDENCE: automatic-evidence=v1; definition-sha256=[a-f0-9]{64};/.test(line),
      "the definition digest was truncated\n" + line);
    assert(/output-sha256=[a-f0-9]{64}; output-bytes=\d+;/.test(line),
      "the output fingerprint was truncated\n" + line);
  } finally { s.cleanup(); }
});

test("checks: the output cap applies to stdout and stderr combined", async () => {
  const s = sandbox();
  try {
    s.write("split-boundary.mjs",
      "process.stdout.write('a'.repeat(524287)); process.stderr.write('b'.repeat(524288));\n");
    s.write("GATES.md", gate("G1", "exactly at the cap once joined", "node split-boundary.mjs", "a"));
    let r = await run(GATE_CHECK, ["GATES.md"], { cwd: s.dir });
    assert(r.code === 0, "the exact joined boundary failed\n" + r.out.slice(-2000));
    assertHas(s.read("GATES.md"), "output-bytes=1048576;");

    s.write("split-cap.mjs",
      "process.stdout.write('a'.repeat(524288)); process.stderr.write('b'.repeat(524288));\n");
    s.write("GATES.md", gate("G1", "one byte over once joined", "node split-cap.mjs", "a"));
    r = await run(GATE_CHECK, ["GATES.md"], { cwd: s.dir });
    assert(r.code === 1, "over the joined cap returned " + r.code + "\n" + r.out.slice(-2000));
    assertHas(r.out, "output exceeded 1048576 bytes after stdout/stderr UTF-8 combination");
    const led = s.read("GATES.md");
    assertHas(led, "- [ ] G1:");
    assertLacks(led, "automatic-evidence=", "an over-cap run");
  } finally { s.cleanup(); }
});

// ---------------------------------------------------------------- driver

const selected = tests.filter(t => t.name.includes(filter));
let passed = 0;
const failures = [];

for (const t of selected) {
  try {
    await t.fn();
    passed++;
    console.log("ok   " + t.name);
  } catch (e) {
    failures.push({ name: t.name, err: e });
    console.log("FAIL " + t.name + "\n     " + String(e.message).split("\n").join("\n     "));
  }
}

console.log("");
console.log(passed + "/" + selected.length + " passed");
process.exit(failures.length ? 1 : 0);
