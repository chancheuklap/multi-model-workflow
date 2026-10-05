import assert from "node:assert/strict";
import test from "node:test";

import {fromPayload, render} from "../../board/page/settings.mjs";
import {installDom, walk} from "./fake-dom.mjs";

const payload = {
  version: 12,
  runner: "orca",
  rows: {
    "junior-worker": {host: "grok", model: "grok 4.6", effort: "high"},
    "senior-worker": {host: "codex", model: "gpt 5.6 sol", effort: "high"},
    reviewer: {host: "claude", model: "opus 5", effort: "high"},
    advisor: {host: "claude", model: "fable 5.1", effort: "medium"},
  },
  hosts: [
    {name: "grok", binary: "grok", cli: true, paseo: true},
    {name: "codex", binary: "codex", cli: true, paseo: true},
    {name: "claude", binary: "claude", cli: true, paseo: true},
  ],
  runners: ["herdr", "orca", "paseo", "auto"],
  scan: {
    source: "cli", scanned_at: "2026-09-10T23:02:00Z", scanning: false,
    hosts: {
      grok: {state: "ok", offered: [{model: "grok 4.6", efforts: ["high"]}]},
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
