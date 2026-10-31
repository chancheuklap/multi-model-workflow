import assert from "node:assert/strict";
import test from "node:test";
import {readFileSync} from "node:fs";
import {CATALOG, LocalConfig, catalogFromPayload, settingsView} from "../../board/page/local-config.mjs";

const copy = value => JSON.parse(JSON.stringify(value));

function offered(models) {
  return {state: "ok", offered: models};
}

// "both 1" is a model name both hosts list, so a host change can keep the model.
const scan = {
  claude: offered([
    {model: "opus 5", efforts: ["medium", "high"]},
    {model: "sonnet 5", efforts: ["high"]},
    {model: "fable 5.1", efforts: ["medium"]},
    {model: "both 1", efforts: ["low", "medium", "high"]},
  ]),
  codex: offered([
    {model: "gpt 5.6 sol", efforts: ["low", "medium", "high", "xhigh"]},
    {model: "gpt 6 astra", efforts: ["high"]},
    {model: "both 1", efforts: ["low", "medium", "high", "xhigh"]},
  ]),
};

const saved = {
  runner: "orca",
  rows: {
    "junior-worker": {host: "codex", model: "gpt 5.6 sol", effort: "high"},
    "senior-worker": {host: "codex", model: "gpt 5.6 sol", effort: "high"},
    reviewer: {host: "claude", model: "opus 5", effort: "high"},
    advisor: {host: "claude", model: "fable 5.1", effort: "medium"},
    researcher: {host: "claude", model: "sonnet 5", effort: "high"},
    candidate: {host: "claude", model: "opus 5", effort: "high"},
  },
};

test("changing the host keeps a model the new host offers and clears it otherwise", () => {
  const keepFrom = copy(saved);
  keepFrom.rows["junior-worker"] = {host: "claude", model: "both 1", effort: "high"};
  const keep = LocalConfig.setCell(scan, keepFrom, "junior-worker", "host", "codex");
  assert.equal(keep.rows["junior-worker"].model, "both 1");
  assert.equal(keep.rows["junior-worker"].effort, "high");

  const dropEffort = copy(saved);
  dropEffort.rows["junior-worker"] = {host: "codex", model: "both 1", effort: "xhigh"};
  const keptModel = LocalConfig.setCell(scan, dropEffort, "junior-worker", "host", "claude");
  assert.equal(keptModel.rows["junior-worker"].model, "both 1");
  assert.equal(keptModel.rows["junior-worker"].effort, "");

  const clear = LocalConfig.setCell(scan, copy(saved), "junior-worker", "host", "claude");
  assert.equal(clear.rows["junior-worker"].model, "");
  assert.equal(clear.rows["junior-worker"].effort, "");
});

test("a model with one effort takes it", () => {
  const draft = copy(saved);
  draft.rows["junior-worker"].effort = "xhigh";
  LocalConfig.setCell(scan, draft, "junior-worker", "model", "gpt 6 astra");
  assert.equal(draft.rows["junior-worker"].effort, "high");
});

test("an alias option shows the model it resolves to today, and saves the alias", () => {
  const aliased = copy(scan);
  aliased.claude = offered([
    {model: "opus[1m]", efforts: ["high"], note: "Opus 5.5 with 1M context"},
    {model: "sonnet 5", efforts: ["high"]},
  ]);
  const draft = copy(saved);
  draft.rows.reviewer.model = "opus[1m]";
  const modelOpts = LocalConfig.rowOptions(aliased, draft, "reviewer").model;
  const opus = modelOpts.find(o => o.value === "opus[1m]");
  assert.equal(opus.text, "opus[1m] · Opus 5.5 with 1M context");
  assert.equal(opus.selected, true);
  assert.equal(modelOpts.find(o => o.value === "sonnet 5").text, "sonnet 5");
});

test("a saved value this machine no longer offers is flagged with its reason", () => {
  const retired = copy(scan);
  retired.codex = offered([{model: "gpt 6 astra", efforts: ["high"]}]);
  const modelFlags = LocalConfig.problems(retired, saved);
  const model = modelFlags.find(item => item.key === "junior-worker" && item.cell === "model");
  assert.ok(model);
  assert.match(model.text, /这台机器的 codex 已经不提供 gpt 5.6 sol/);
  const modelOpts = LocalConfig.rowOptions(retired, saved, "junior-worker").model;
  assert.equal(modelOpts[0].value, "gpt 5.6 sol");
  assert.match(modelOpts[0].text, /本机已经没有/);
  assert.equal(modelOpts[0].selected, true);

  const missing = copy(scan);
  missing.codex = {state: "missing", offered: []};
  const hostFlags = LocalConfig.problems(missing, saved);
  const host = hostFlags.find(item => item.key === "junior-worker" && item.cell === "host");
  assert.ok(host);
  assert.match(host.text, /没装 codex/);
  assert.match(host.text, /换一个这台机器有的/);
  const codexOpt = LocalConfig.rowOptions(missing, saved, "junior-worker").host.find(o => o.value === "codex");
  assert.equal(codexOpt.selected, true);
  assert.match(codexOpt.text, /本机没装/);
  assert.equal(codexOpt.disabled, false);

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

test("a host with no cli block under orca or herdr is flagged as one the runner cannot start", () => {
  const catalog = copy(CATALOG);
  catalog.launch.claude = {cli: false, paseo: true};
  for (const runner of ["orca", "herdr"]) {
    const draft = copy(saved);
    draft.runner = runner;
    const flags = LocalConfig.problems(scan, draft, catalog);
    const host = flags.find(item => item.key === "reviewer" && item.cell === "host");
    assert.ok(host, runner);
    assert.equal(host.text, `${runner} 起不了 claude，换一个 host 或 runner`);
    assert.equal(LocalConfig.hostState(scan, draft, "claude", catalog), "unlaunchable");
  }
});

test("launch capability is independent of a shared catalog source", () => {
  const catalog = catalogFromPayload({
    hosts: [
      {name: "claude", launch: ["cli"]},
      {name: "codex", launch: ["cli", "native"]},
    ],
    runners: ["orca", "native-runner", "auto"],
    runner_options: {
      orca: {catalog: "cli", launch: "cli"},
      "native-runner": {catalog: "cli", launch: "native"},
    },
  });
  const draft = {...copy(saved), runner: "native-runner"};
  assert.equal(LocalConfig.source(draft, catalog), "cli");
  assert.equal(LocalConfig.needsRescan(saved, draft, catalog), false);
  assert.equal(LocalConfig.hostState(scan, draft, "claude", catalog), "unlaunchable");
  assert.equal(LocalConfig.hostState(scan, draft, "codex", catalog), "ok");
  const options = LocalConfig.rowOptions(scan, draft, "junior-worker", catalog);
  assert.equal(options.host.some(o => o.value === "claude"), false);
  assert.equal(options.host.find(o => o.value === "codex").disabled, false);
  assert.ok(LocalConfig.runnerOptions(draft, catalog).find(o => o.value === "native-runner").selected);
});

test("with paseo down every row is flagged", () => {
  const down = Object.fromEntries(CATALOG.hosts.map(host => [host, {state: "down", offered: []}]));
  const draft = copy(saved);
  draft.runner = "paseo";
  const flags = LocalConfig.problems(down, draft);
  assert.equal(flags.length, LocalConfig.roles(draft).length);
  for (const agent of LocalConfig.roles(draft)) {
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
  flagged.rows["junior-worker"].host = "nohost";
  assert.equal(LocalConfig.saveOff(scan, flagged, saved, {}), true);
  assert.equal(LocalConfig.saveOff(scan, draft, saved, {refused: 1}), true);
});

test("a cell the server flagged keeps Save off, on the rule and on the sheet's button", () => {
  const draft = copy(saved);
  LocalConfig.setCell(scan, draft, "senior-worker", "host", "claude");
  LocalConfig.setCell(scan, draft, "senior-worker", "model", "opus 5");
  LocalConfig.setCell(scan, draft, "senior-worker", "effort", "high");
  const serverFlags = [{key: "senior-worker", cell: "model", text: "start refused it"}];
  assert.equal(LocalConfig.saveOff(scan, draft, saved, {serverFlags}), true);
  const sheet = {draft, saved: copy(saved)};
  assert.equal(settingsView(sheet, scan, CATALOG).saveOff, false);
  assert.equal(settingsView({...sheet, serverFlags}, scan, CATALOG).saveOff, true);
  assert.equal(settingsView({...sheet, scanning: true}, scan, CATALOG).saveOff, true);
  assert.equal(settingsView({...sheet, refused: 1}, scan, CATALOG).saveOff, true);
  assert.equal(settingsView({draft: copy(saved), saved: copy(saved)}, scan, CATALOG).saveOff, true);
});

test("crossing paseo asks for a rescan", () => {
  assert.equal(LocalConfig.needsRescan({runner: "orca"}, {runner: "paseo"}), true);
  assert.equal(LocalConfig.needsRescan({runner: "paseo"}, {runner: "herdr"}), true);
  assert.equal(LocalConfig.needsRescan({runner: "orca"}, {runner: "herdr"}), false);
  assert.equal(LocalConfig.needsRescan({runner: "orca"}, {runner: "auto"}), false);
  assert.equal(LocalConfig.needsRescan({runner: "herdr"}, {runner: "auto"}), false);
  assert.equal(LocalConfig.needsRescan({runner: "auto"}, {runner: "orca"}), false);
});

test("the sheet has one row per role of roles.json, in its order, each with what it does", () => {
  const roles = JSON.parse(readFileSync(new URL("../../skills/dispatch/roles.json", import.meta.url)))
    .roles.map(role => role.name);
  assert.deepEqual(roles, ["junior-worker", "senior-worker", "reviewer", "researcher", "candidate", "retro-analyst", "advisor"]);
  const rows = Object.fromEntries(roles.map(role => [role, copy(saved.rows.reviewer)]));
  const config = {runner: "orca", rows};
  const view = settingsView({draft: copy(config), saved: copy(config)}, scan, CATALOG);
  assert.deepEqual(view.rows.map(row => row.agent), roles);
  for (const row of view.rows) assert.ok(row.what, row.agent);
  assert.equal(view.rows.find(row => row.agent === "retro-analyst").what,
    "从一个角度分拣一次运行的问题登记，核实、合并、给出方案");
});

test("every subagent row of roles.json says what it is for", () => {
  const rows = JSON.parse(readFileSync(new URL("../../skills/dispatch/roles.json", import.meta.url)))
    .subagents.map(row => row.name);
  assert.deepEqual(rows, ["review-axis", "reader", "default"]);
  assert.deepEqual(Object.keys(LocalConfig.SUBAGENT_WHAT), rows);
  assert.equal(LocalConfig.SUBAGENT_WHAT.reader, "读大量材料，交回压缩过的结论");
});
