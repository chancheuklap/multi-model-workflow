import assert from "node:assert/strict";
import test from "node:test";

import {fromPayload, render} from "../../board/page/settings.mjs";
import {installDom, walk} from "./fake-dom.mjs";

const payload = {
  version: 12,
  runner: "orca",
  rows: {
    "junior-worker": {host: "claude", model: "opus 5", effort: "high"},
    "senior-worker": {host: "codex", model: "gpt 5.6 sol", effort: "high"},
    reviewer: {host: "claude", model: "opus 5", effort: "high"},
    advisor: {host: "claude", model: "fable 5.1", effort: "medium"},
  },
  hosts: [
    {name: "codex", binary: "codex", cli: true, paseo: true},
    {name: "claude", binary: "claude", cli: true, paseo: true},
  ],
  runners: ["herdr", "orca", "paseo", "auto"],
  scan: {
    source: "cli", scanned_at: "2026-09-10T23:02:00Z", scanning: false,
    hosts: {
      codex: {state: "ok", offered: [{model: "gpt 5.6 sol", efforts: ["high"]}]},
      claude: {state: "ok", offered: [
        {model: "opus 5", efforts: ["high"]},
        {model: "fable 5.1", efforts: ["medium"]},
      ]},
    },
  },
};

function byUi(root, id) {
  return walk(root).find(node => node.getAttribute?.("data-ui") === id);
}

test("Escape closes the sheet and keeps no edit", () => {
  const {document} = installDom();
  const host = document.createElement("div");
  let closed = 0;
  let root = render(host, fromPayload(structuredClone(payload)), {}, {
    onClose() { closed += 1; },
  });

  const runner = byUi(root, "本机配置.runner.select");
  runner.dispatchEvent({type: "change", target: {value: "herdr"}});
  assert.equal(byUi(host, "本机配置.runner.select").value, "herdr");

  document.dispatchEvent({
    type: "keydown", key: "Escape", preventDefault() {}, stopImmediatePropagation() {},
  });
  assert.equal(closed, 1);
  assert.equal(host.children.length, 0);

  root = render(host, fromPayload(structuredClone(payload)), {}, {
    onClose() { closed += 1; },
  });
  assert.equal(byUi(root, "本机配置.runner.select").value, "orca");
});

test("selecting a single-host runner changes every role to its models after its catalog arrives", async () => {
  const {document} = installDom();
  const host = document.createElement("div");
  const input = structuredClone(payload);
  for (const role of ["researcher", "candidate", "retro-analyst"])
    input.rows[role] = {host: "claude", model: "opus 5", effort: "high"};
  input.runners.push("codex-app");
  input.runner_options = {orca: {catalog: "cli", launch: "cli"},
    "codex-app": {catalog: "codex-app", launch: "codex-app"}};
  input.hosts[0].launch = ["cli", "paseo", "codex-app"];
  input.hosts[1].launch = ["cli", "paseo"];
  input.subagents = {reader: {claude: {model: "opus", effort: "high"},
    codex: {model: "inherit", effort: "inherit"}}};
  input.subagent_options = {rows: ["reader"],
    claude: {models: ["opus"], efforts: ["high"]},
    codex: {models: [{model: "gpt-6.1-sol", efforts: ["medium", "high"]}], inherit_efforts: ["high"]}};
  const model = fromPayload(input);
  let resolveScan, written;
  const api = {
    scanSettings: () => new Promise(resolve => { resolveScan = resolve; }),
    saveSettings: async value => {
      written = value;
      return {ok: true, json: async () => ({version: 13, saved_at: "2026-10-31T12:00:00Z"})};
    },
  };
  render(host, model, api);
  byUi(host, "本机配置.runner.select").dispatchEvent({type: "change", target: {value: "codex-app"}});
  const hosts = () => walk(host).filter(n => n.getAttribute?.("data-ui") === "本机配置.role.host");
  assert.equal(hosts().length, 7);
  for (const select of hosts()) {
    assert.equal(select.value, "codex");
    assert.deepEqual(walk(select).filter(n => n.tagName === "OPTION").map(n => n.getAttribute("value")), ["codex"]);
  }
  resolveScan({ok: true, json: async () => ({source: "codex-app", scanned_at: "2026-10-31T12:00:00Z",
    hosts: {codex: {state: "ok", offered: [
      {model: "gpt 6.1 sol", efforts: ["medium", "high"]},
      {model: "gpt 6 luna", efforts: ["high"]},
      {model: "gpt 5.6 sol", efforts: ["high"]},
    ]}, claude: {state: "unlaunchable", offered: []}}})});
  await new Promise(resolve => setTimeout(resolve, 0));
  for (const row of Object.values(model.st.draft.rows)) {
    assert.equal(row.host, "codex");
    assert.ok(["gpt 6.1 sol", "gpt 5.6 sol"].includes(row.model));
    assert.ok(["medium", "high"].includes(row.effort));
  }
  assert.equal(model.st.draft.rows["senior-worker"].model, "gpt 5.6 sol");
  assert.equal(model.st.draft.rows.advisor.effort, "medium");
  assert.deepEqual(walk(host).filter(n => n.getAttribute?.("data-ui") === "本机配置.subagent.host")
    .map(n => n.textContent), ["codex"]);
  const save = byUi(host, "本机配置.sheet.save");
  assert.equal(save.disabled, false);
  save.dispatchEvent({type: "click"});
  await new Promise(resolve => setTimeout(resolve, 0));
  assert.equal(written.runner, "codex-app");
  assert.equal(Object.values(written.rows).filter(r => r.host === "codex").length, 7);
  assert.equal(written.subagents.reader.claude.model, "opus");
  byUi(host, "本机配置.runner.select").dispatchEvent({type: "change", target: {value: "orca"}});
  resolveScan({ok: true, json: async () => input.scan});
  await new Promise(resolve => setTimeout(resolve, 0));
  assert.deepEqual(walk(hosts()[0]).filter(n => n.tagName === "OPTION").map(n => n.getAttribute("value")), ["codex", "claude"]);
  assert.deepEqual(walk(host).filter(n => n.getAttribute?.("data-ui") === "本机配置.subagent.host")
    .map(n => n.textContent), ["claude", "codex"]);
});
