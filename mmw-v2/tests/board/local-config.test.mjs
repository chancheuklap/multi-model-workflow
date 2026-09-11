import assert from "node:assert/strict";
import test from "node:test";
import {CATALOG, LocalConfig} from "../../board/page/local-config.mjs";

const copy = value => JSON.parse(JSON.stringify(value));

function offered(models) {
  return {state: "ok", offered: models};
}

const scan = {
  cursor: offered([
    {model: "auto", efforts: ["—"]},
    {model: "grok 4.6", efforts: ["low", "medium", "high"]},
    {model: "composer 2.5", efforts: ["high"]},
  ]),
  grok: offered([
    {model: "grok 4.6", efforts: ["low", "medium", "high", "xhigh"]},
    {model: "grok 4.5", efforts: ["high"]},
  ]),
  claude: offered([
    {model: "opus 5", efforts: ["medium", "high"]},
    {model: "sonnet 5", efforts: ["high"]},
    {model: "fable 5.1", efforts: ["medium"]},
  ]),
  codex: offered([
    {model: "gpt 5.6 sol", efforts: ["low", "medium", "high", "xhigh"]},
    {model: "gpt 6 astra", efforts: ["high"]},
  ]),
  pi: offered([{model: "pi-model", efforts: ["high"]}]),
};

const saved = {
  runner: "orca",
  rows: {
    "junior-worker": {host: "grok", model: "grok 4.6", effort: "high"},
    "senior-worker": {host: "codex", model: "gpt 5.6 sol", effort: "high"},
    reviewer: {host: "claude", model: "opus 5", effort: "high"},
    verifier: {host: "claude", model: "sonnet 5", effort: "high"},
    advisor: {host: "claude", model: "fable 5.1", effort: "medium"},
  },
};

test("changing the host keeps a model the new host offers and clears it otherwise", () => {
  const keepFrom = copy(saved);
  keepFrom.rows["junior-worker"] = {host: "cursor", model: "grok 4.6", effort: "high"};
  const keep = LocalConfig.setCell(scan, keepFrom, "junior-worker", "host", "grok");
  assert.equal(keep.rows["junior-worker"].model, "grok 4.6");
  assert.equal(keep.rows["junior-worker"].effort, "high");

  const dropEffort = copy(saved);
  dropEffort.rows["junior-worker"].effort = "xhigh";
  const keptModel = LocalConfig.setCell(scan, dropEffort, "junior-worker", "host", "cursor");
  assert.equal(keptModel.rows["junior-worker"].model, "grok 4.6");
  assert.equal(keptModel.rows["junior-worker"].effort, "");

  const clear = LocalConfig.setCell(scan, copy(saved), "junior-worker", "host", "claude");
  assert.equal(clear.rows["junior-worker"].model, "");
  assert.equal(clear.rows["junior-worker"].effort, "");
});

test("a model with one effort takes it", () => {
  const draft = copy(saved);
  draft.rows["junior-worker"].effort = "xhigh";
  LocalConfig.setCell(scan, draft, "junior-worker", "model", "grok 4.5");
  assert.equal(draft.rows["junior-worker"].effort, "high");
});

test("a saved value this machine no longer offers is flagged with its reason", () => {
  const retired = copy(scan);
  retired.grok = offered([{model: "grok 4.5", efforts: ["high"]}]);
  const modelFlags = LocalConfig.problems(retired, saved);
  const model = modelFlags.find(item => item.key === "junior-worker" && item.cell === "model");
  assert.ok(model);
  assert.match(model.text, /这台机器的 grok 已经不提供 grok 4.6/);
  const modelOpts = LocalConfig.rowOptions(retired, saved, "junior-worker").model;
  assert.equal(modelOpts[0].value, "grok 4.6");
  assert.match(modelOpts[0].text, /本机已经没有/);
  assert.equal(modelOpts[0].selected, true);

  const missing = copy(scan);
  missing.grok = {state: "missing", offered: []};
  const hostFlags = LocalConfig.problems(missing, saved);
  const host = hostFlags.find(item => item.key === "junior-worker" && item.cell === "host");
  assert.ok(host);
  assert.match(host.text, /没装 grok/);
  assert.match(host.text, /换一个这台机器有的/);
  const grokOpt = LocalConfig.rowOptions(missing, saved, "junior-worker").host.find(o => o.value === "grok");
  assert.equal(grokOpt.selected, true);
  assert.match(grokOpt.text, /本机没装/);
  assert.equal(grokOpt.disabled, false);

  const stale = copy(saved);
  stale.rows["junior-worker"].effort = "max";
  const effortFlags = LocalConfig.problems(scan, stale);
  const effort = effortFlags.find(item => item.key === "junior-worker" && item.cell === "effort");
  assert.ok(effort);
  assert.match(effort.text, /没有 max 这一档/);
  const effortOpts = LocalConfig.rowOptions(scan, stale, "junior-worker").effort;
  assert.equal(effortOpts[0].value, "max");
  assert.equal(effortOpts[0].selected, true);
  assert.match(effortOpts[0].text, /本机已经没有/);
});

test("pi under orca or herdr is flagged as a host the runner cannot start", () => {
  for (const runner of ["orca", "herdr"]) {
    const draft = copy(saved);
    draft.runner = runner;
    draft.rows.reviewer.host = "pi";
    draft.rows.reviewer.model = "pi-model";
    draft.rows.reviewer.effort = "high";
    const flags = LocalConfig.problems(scan, draft);
    const host = flags.find(item => item.key === "reviewer" && item.cell === "host");
    assert.ok(host, runner);
    assert.match(host.text, /orca 和 herdr 起不了 pi/);
    assert.equal(LocalConfig.hostState(scan, draft, "pi"), "unlaunchable");
  }
});

test("with paseo down every row is flagged", () => {
  const down = Object.fromEntries(CATALOG.hosts.map(host => [host, {state: "down", offered: []}]));
  const draft = copy(saved);
  draft.runner = "paseo";
  const flags = LocalConfig.problems(down, draft);
  assert.equal(flags.length, CATALOG.agents.length);
  for (const agent of CATALOG.agents) {
    const host = flags.find(item => item.key === agent && item.cell === "host");
    assert.ok(host, agent);
    assert.match(host.text, /先开 Paseo，或者把 runner 换回 orca 或 herdr/);
  }
});

test("changes are listed per row", () => {
  const draft = copy(saved);
  draft.runner = "herdr";
  LocalConfig.setCell(scan, draft, "senior-worker", "host", "claude");
  LocalConfig.setCell(scan, draft, "senior-worker", "model", "opus 5");
  LocalConfig.setCell(scan, draft, "senior-worker", "effort", "high");
  LocalConfig.setCell(scan, draft, "reviewer", "model", "sonnet 5");
  const listed = LocalConfig.changes(draft, saved);
  assert.deepEqual(listed.map(item => item.text), [
    "runner", "senior-worker 的 host、model", "reviewer 的 model",
  ]);
});

test("save is enabled only with changes, no flag and no scan running", () => {
  const draft = copy(saved);
  assert.equal(LocalConfig.saveOff(scan, draft, saved, {}), true);
  LocalConfig.setCell(scan, draft, "senior-worker", "host", "claude");
  LocalConfig.setCell(scan, draft, "senior-worker", "model", "opus 5");
  LocalConfig.setCell(scan, draft, "senior-worker", "effort", "high");
  assert.equal(LocalConfig.saveOff(scan, draft, saved, {}), false);
  assert.equal(LocalConfig.saveOff(scan, draft, saved, {scanning: true}), true);
  const flagged = copy(draft);
  flagged.rows["junior-worker"].host = "pi";
  assert.equal(LocalConfig.saveOff(scan, flagged, saved, {}), true);
  assert.equal(LocalConfig.saveOff(scan, draft, saved, {refused: 1}), true);
});

test("crossing paseo asks for a rescan", () => {
  assert.equal(LocalConfig.needsRescan({runner: "orca"}, {runner: "paseo"}), true);
  assert.equal(LocalConfig.needsRescan({runner: "paseo"}, {runner: "herdr"}), true);
  assert.equal(LocalConfig.needsRescan({runner: "orca"}, {runner: "herdr"}), false);
  assert.equal(LocalConfig.needsRescan({runner: "orca"}, {runner: "auto"}), false);
  assert.equal(LocalConfig.needsRescan({runner: "herdr"}, {runner: "auto"}), false);
  assert.equal(LocalConfig.needsRescan({runner: "auto"}, {runner: "orca"}), false);
});
