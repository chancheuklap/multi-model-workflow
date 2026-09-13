import assert from "node:assert/strict";
import test from "node:test";

import {fromBoard, fromScene, render} from "../../board/page/detail.mjs";
import {describeEvent, eventBlocks} from "../../board/page/board-logic.mjs";
import {accessibleName, installDom, namedButton, walk} from "./fake-dom.mjs";

const ticketScene = {
  vals: {
    repo: "chancheuklap/multi-model-workflow",
    d: {
      isTicket: true, hasCard: true, eyebrow: "Ticket", num: "#133",
      title: "折叠接入中继", lampCls: "lamp big orange", statusWord: "needs you",
      wordCls: "va-word orange", pillCls: "pill big working", phase: "working",
      elapsed: "1h02m", hasRun: true, noRun: false, noRunText: "not dispatched yet",
      runGrade: "senior-worker", runModel: "grok · grok 4.6 · xhigh",
      runRows: [
        {k: "ticket branch", v: "issue-133"},
        {k: "base branch", v: "wake-relay"},
        {k: "worktree", v: "…/.worktrees/133-fold-relay"},
        {k: "machine", v: "cheuk-mbp"},
      ],
      hasWhy: true,
      why: [{head: "#150 contract", body: "spec 本身不成立，要回到写 spec 的人"}],
      gh: 133,
    },
    emptyTitle: "点一张卡",
    emptyText: "画布上任意一张卡——map、spec、ticket 或 decision ticket——点一下，它的全部细节就在这一栏。",
    links: [{label: "spec #131", n: 131}, {label: "map #98", n: 98}],
    blockedBy: [{n: 132, known: true, num: "#132", lampCls: "lamp ink",
      title: "中继进程骨架", hold: false, phase: "landed", showHold: false, showPill: true}],
    blocking: [{n: 135, known: true, num: "#135", lampCls: "lamp hollow",
      title: "投递回执", hold: true, phase: "queued", showHold: true, showPill: false}],
    kids: [{num: "#150", kind: "contract", title: "spec 没写队列为空时中继读什么",
      lampCls: "lamp orange", kindCls: "pv-kind hot"}],
    rawEvents: [
      {event: "worker.started", at: "2026-09-10T22:38:00Z", line: "worker started",
        payload: {host: "grok", model: "grok 4.6", effort: "xhigh", session: "w94b8"}},
      {event: "ticket.claimed", at: "2026-09-10T22:38:00Z", line: "claimed", payload: {}},
    ],
    phaseBlocks: [{
      phase: "working", tone: "needs-you", openByDefault: true,
      summary: "Your decision needed — 唤醒要不要跨过已暂停的 spec",
      from: "22:38", span: "22:38–23:31",
      items: [
        {time: "22:38", name: "Worker started", text: "grok grok 4.6, xhigh effort",
          hasText: true, tone: "plain",
          detail: [{k: "session", v: "w94b8"}, {k: "comment", v: "worker started"}]},
        {time: "22:38", name: "Ticket claimed", text: "", hasText: false, tone: "plain",
          detail: [{k: "comment", v: "claimed"}]},
      ],
    }],
  },
};

const emptyScene = {
  vals: {
    d: {isEmpty: true, hasCard: false, hasTasks: false},
    emptyTitle: "这里是详情",
    emptyText: "The Night 开起来之后，点画布上的卡，它的细节显示在这一栏。",
    links: [], blockedBy: [], blocking: [], kids: [],
  },
};

function mount(view, api, hooks) {
  const {document, window} = installDom();
  const host = document.createElement("div");
  return {document, window, host, root: render(host, view, api, hooks)};
}

test("empty scene shows the empty copy and no GitHub button", () => {
  const {root} = mount(fromScene(emptyScene));
  assert.equal(root.dataset.screen, "detail");
  assert.equal(root.getAttribute("aria-label"), "详情");
  assert.match(root.textContent, /这里是详情/);
  assert.match(root.textContent, /The Night 开起来之后/);
  assert.equal(walk(root).filter(node => node.tagName === "BUTTON").length, 0);
});

test("a ticket scene shows GitHub, origin, status, held relations, and phase blocks", () => {
  const {root} = mount(fromScene(ticketScene));
  assert.ok(namedButton(root, "关闭详情"));
  assert.ok(namedButton(root, "GitHub ↗"));
  assert.ok(namedButton(root, "spec #131"));
  assert.ok(namedButton(root, "map #98"));
  assert.match(root.textContent, /折叠接入中继/);
  assert.match(root.textContent, /Needs you/);
  assert.match(root.textContent, /senior-worker/);
  assert.match(root.textContent, /Events/);
  assert.match(root.textContent, /Worker started/);
  assert.ok(namedButton(root, "#132 中继进程骨架 landed"));
  assert.ok(namedButton(root, "#135 投递回执 held"));
  const heading = walk(root).find(node => node.tagName === "H2");
  assert.equal(accessibleName(heading), "折叠接入中继");
});

test("close and Escape call onClose", () => {
  let closed = 0;
  const {root, document} = mount(fromScene(ticketScene), undefined, {onClose: () => { closed += 1; }});
  namedButton(root, "关闭详情").click();
  assert.equal(closed, 1);
  document.dispatchEvent({type: "keydown", key: "Escape", preventDefault() {}});
  assert.equal(closed, 2);
});

test("ticket numbers in the panel call onGoto, unknown rows do not", () => {
  const seen = [];
  const scene = structuredClone(ticketScene);
  scene.vals.blockedBy.push({
    n: 399, known: false, unknown: true, num: "#399", lampCls: "lamp none",
    title: "不在这棵树里，读不到它的状态", state: "unknown", hold: false, showHold: false, showPill: false,
  });
  const {root} = mount(fromScene(scene), undefined, {onGoto: n => seen.push(n)});
  namedButton(root, "spec #131").click();
  namedButton(root, "#132 中继进程骨架 landed").click();
  namedButton(root, "#135 投递回执 held").click();
  namedButton(root, "#399 不在这棵树里，读不到它的状态 unknown").click();
  assert.deepEqual(seen, [131, 132, 135]);
});

test("GitHub uses a new tab and does not call the API client", () => {
  const api = new Proxy({}, {get() { throw new Error("board wrote"); }});
  const {root, window} = mount(fromScene(ticketScene), api);
  namedButton(root, "GitHub ↗").click();
  assert.deepEqual(window.opened, [
    ["https://github.com/chancheuklap/multi-model-workflow/issues/133", "_blank", "noopener,noreferrer"],
  ]);
});

test("fromBoard maps a folded ticket onto the detail panel", () => {
  const ticket = {
    n: 133, title: "折叠接入中继", blocked: [132], children: [], events: [],
    fold: {
      children: {}, sessions: [], landed: false, returned: false, bounced: false,
      outcome: null, waiting: null, review: null, worker: null,
    },
  };
  const landed = {
    n: 132, title: "中继进程骨架", blocked: [], children: [], events: [],
    blocker_hold: "",
    fold: {
      children: {}, sessions: [], landed: true, returned: false, bounced: false,
      outcome: null, waiting: null, review: null,
    },
  };
  const view = fromBoard({
    repo: "example/board",
    tasks: [{
      n: 98, kind: "wayfinder", title: "落地流水线改造", decisions: [],
      specs: [{n: 131, title: "唤醒回路", tickets: [landed, ticket]}],
    }],
  }, 133);
  assert.equal(view.kind, "ticket");
  assert.equal(view.title, "折叠接入中继");
  assert.equal(view.lamp, "hollow");
  assert.equal(view.repo, "example/board");
  const {root} = mount(view);
  assert.ok(namedButton(root, "GitHub ↗"));
  namedButton(root, "GitHub ↗").click();
  assert.equal(globalThis.window.opened[0][0], "https://github.com/example/board/issues/133");
});

test("selecting a spec that has no map shows the spec card with no map link", () => {
  const fold = {children: {}, sessions: [], landed: false, returned: false, bounced: false,
    outcome: null, unreadable: [], passed: false, review: null, waiting: null};
  const ticket = {n: 31, title: "its ticket", state: "open", blocked: [], blockers: [], children: [], events: [], fold};
  const spec = {n: 30, title: "lone spec", tickets: [ticket]};
  const tasks = [{n: 30, kind: "spec", title: "lone spec", state: "open", decisions: [], specs: [spec]}];
  const view = fromBoard({tasks, repo: "x/y"}, 30);
  assert.equal(view.kind, "spec");
  assert.equal(view.eyebrow, "Spec");
  assert.deepEqual(view.links, []);
  assert.equal(view.listCount, 1);
  const {root} = mount(view);
  assert.ok(namedButton(root, "在 GitHub 打开 #30 ↗"));
});

test("pipeline events become human-readable phase blocks", () => {
  const events = [
    {event: "worker.started", at: "2026-09-12T10:00:00Z", line: "raw worker line",
      payload: {host: "codex", model: "gpt-5.6-sol", effort: "medium"}},
    {event: "ticket.claimed", at: "2026-09-12T10:01:00Z", line: "raw claim", payload: {}},
    {event: "ticket.checked", at: "2026-09-12T10:20:00Z", line: "raw check",
      payload: {run: "self", result: "met", counts: {met: 6, total: 6}}},
    {event: "reviewer.started", at: "2026-09-12T10:21:00Z", line: "raw reviewer",
      payload: {host: "claude", model: "opus", effort: "high"}},
    {event: "reviewer.reported", at: "2026-09-12T10:30:00Z", line: "raw report", payload: {}},
    {event: "ticket.checked", at: "2026-09-12T10:35:00Z", line: "final run",
      payload: {run: "reverify", actor: "worker", result: "met", counts: {met: 6, total: 6}}},
    {event: "ticket.landed", at: "2026-09-12T10:40:00Z", line: "raw landed",
      payload: {into: "task-board"}},
  ];

  const described = events.map(describeEvent);
  assert.deepEqual(described.map(event => event.name), [
    "Worker started", "Ticket claimed", "Criteria run", "Reviewer started", "Review posted",
    "Final criteria run", "Landed",
  ]);
  assert.deepEqual(eventBlocks(events).map(block => block.phase), ["working", "review", "verify", "landed"]);
  assert.equal(described.some(event => /^(worker|ticket|reviewer)\./.test(event.name)), false);
  assert.equal(describeEvent({
    event: "ticket.checked", payload: {run: "reverify", stage: "regress"},
  }).name, "Criteria re-run after landing");
});

test("ticket rendering shows phase blocks and keeps backend fields behind an event click", () => {
  const {root} = mount(fromScene(ticketScene));
  assert.match(root.textContent, /Worker started/);
  assert.doesNotMatch(root.textContent, /worker\.started|w94b8/);
  const eventButton = namedButton(root, "22:38 Worker started grok grok 4.6, xhigh effort");
  assert.ok(eventButton);
  eventButton.click();
  assert.match(root.textContent, /w94b8/);
  assert.match(root.textContent, /session/);
});

test("poll repaint keeps the detail root and an opened event", () => {
  const view = fromScene(ticketScene);
  const {host, root} = mount(view);
  namedButton(root, "22:38 Worker started grok grok 4.6, xhigh effort").click();
  assert.match(root.textContent, /w94b8/);

  const repainted = render(host, view);
  assert.equal(repainted, root);
  assert.match(repainted.textContent, /w94b8/);
});
