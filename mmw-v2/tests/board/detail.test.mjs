import assert from "node:assert/strict";
import test from "node:test";

import {fromBoard, fromScene, render} from "../../board/page/detail.mjs";
import {accessibleName, installDom, namedButton, walk} from "./fake-dom.mjs";

const ticketScene = {
  vals: {
    repo: "chancheuklap/multi-model-workflow",
    d: {
      isTicket: true, hasCard: true, eyebrow: "Ticket", num: "#133",
      title: "折叠接入中继", lampCls: "lamp big orange", statusWord: "needs you",
      statusCls: "status-word orange", elapsed: "已跑 1h02m", pillCls: "pill big working",
      phase: "working", hint: "here now",
      path: [
        {name: "queued", cls: "path-phase done", sep: true},
        {name: "working", cls: "path-phase now-working", sep: true},
        {name: "waiting", cls: "path-phase", sep: true},
        {name: "review", cls: "path-phase", sep: true},
        {name: "verify", cls: "path-phase", sep: true},
        {name: "landed", cls: "path-phase", sep: false},
      ],
      hasWhy: true,
      why: [{head: "#150 contract", body: "spec 本身不成立，要回到写 spec 的人"}],
      hasWorker: true, facts: [{k: "host", v: "grok · grok 4.6 · xhigh"}],
      manySessions: false, sessions: [], closeout: false, ghLabel: "在 GitHub 打开 #133 ↗", gh: 133,
      noBlockers: false, noBlocks: false, noKids: false, noEvents: false,
      kidCount: 1, eventCount: "1 条评论",
      events: [{time: "06:38", name: "worker.started", nameCls: "ev-name",
        field: "herdr · w94b8 · cheuk-mbp", line: "worker started", dotCls: "lamp green ev-dot"}],
    },
    emptyTitle: "点一张卡",
    emptyText: "画布上任意一张卡——map、spec、ticket 或Decision ticket——点一下，它的全部细节就在这一栏。",
    runtimeNote: "from worker.started",
    noWorker: false,
    links: [{label: "spec #131", n: 131}, {label: "map #98", n: 98}],
    blockers: [{n: 132, known: true, unknown: false, num: "#132", lampCls: "lamp ink",
      title: "中继进程骨架", where: "", state: "landed", stateCls: "rel-state"}],
    blocks: [{n: 135, known: true, unknown: false, num: "#135", lampCls: "lamp hollow",
      title: "投递回执", where: "", state: "queued", stateCls: "rel-state"}],
    kids: [{num: "#150", kind: "contract", title: "spec 没写队列为空时中继读什么",
      to: "needs you", toCls: "kid-to orange", hasGoto: false, noGoto: true, lampCls: "lamp orange"}],
    ticketRows: [], specRows: [], decisionRows: [],
  },
};

const emptyScene = {
  vals: {
    d: {isEmpty: true, hasCard: false, hasTasks: false},
    emptyTitle: "这里是详情",
    emptyText: "有了任务之后，点画布上的卡，它的细节显示在这一栏。",
    links: [], blockers: [], blocks: [], kids: [], ticketRows: [], specRows: [], decisionRows: [],
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
  assert.equal(root.getAttribute("aria-label"), "detail");
  assert.match(root.textContent, /这里是详情/);
  assert.equal(
    walk(root).some(node => node.tagName === "BUTTON" && (node.className || "").split(/\s+/).includes("dp-gh")),
    false,
  );
  assert.equal(walk(root).filter(node => node.tagName === "BUTTON").length, 0);
});

test("a ticket scene shows origin, status, why-orange, and GitHub", () => {
  const {root} = mount(fromScene(ticketScene));
  assert.ok(namedButton(root, "close"));
  assert.ok(namedButton(root, "spec #131"));
  assert.ok(namedButton(root, "map #98"));
  assert.match(root.textContent, /折叠接入中继/);
  assert.match(root.textContent, /Needs you/);
  assert.match(root.textContent, /from worker.started/);
  assert.ok(namedButton(root, "#132 中继进程骨架 landed"));
  assert.ok(namedButton(root, "在 GitHub 打开 #133 ↗"));
  const heading = walk(root).find(node => node.tagName === "H2");
  assert.equal(accessibleName(heading), "折叠接入中继");
});

test("close and Escape call onClose", () => {
  let closed = 0;
  const {root, document} = mount(fromScene(ticketScene), undefined, {onClose: () => { closed += 1; }});
  namedButton(root, "close").click();
  assert.equal(closed, 1);
  document.dispatchEvent({type: "keydown", key: "Escape", preventDefault() {}});
  assert.equal(closed, 2);
});

test("ticket numbers in the panel call onGoto", () => {
  const seen = [];
  const {root} = mount(fromScene(ticketScene), undefined, {onGoto: n => seen.push(n)});
  namedButton(root, "spec #131").click();
  namedButton(root, "#132 中继进程骨架 landed").click();
  namedButton(root, "#135 投递回执 queued").click();
  assert.deepEqual(seen, [131, 132, 135]);
});

test("在 GitHub 打开 uses a new tab and does not call the API client", () => {
  const api = new Proxy({}, {get() { throw new Error("board wrote"); }});
  const {root, window} = mount(fromScene(ticketScene), api);
  namedButton(root, "在 GitHub 打开 #133 ↗").click();
  assert.deepEqual(window.opened, [
    ["https://github.com/chancheuklap/multi-model-workflow/issues/133", "_blank", "noopener,noreferrer"],
  ]);
});

test("fromBoard maps a folded ticket onto the detail panel", () => {
  const ticket = {
    n: 133, title: "折叠接入中继", blocked: [132], children: [], events: [],
    fold: {
      children: {}, sessions: [], landed: false, returned: false, bounced: false,
      outcome: null, waiting: null, review: null, verdict: null, worker: null,
    },
  };
  const landed = {
    n: 132, title: "中继进程骨架", blocked: [], children: [], events: [],
    fold: {
      children: {}, sessions: [], landed: true, returned: false, bounced: false,
      outcome: null, waiting: null, review: null, verdict: null,
    },
  };
  const view = fromBoard({
    repo: "example/board",
    tasks: [{
      n: 98, kind: "wayfinder", title: "landed流水线改造", decisions: [],
      specs: [{n: 131, title: "唤醒回路", tickets: [landed, ticket]}],
    }],
  }, 133);
  assert.equal(view.kind, "ticket");
  assert.equal(view.title, "折叠接入中继");
  assert.equal(view.lamp, "hollow");
  assert.equal(view.repo, "example/board");
  const {root} = mount(view);
  assert.ok(namedButton(root, "在 GitHub 打开 #133 ↗"));
  namedButton(root, "在 GitHub 打开 #133 ↗").click();
  assert.equal(globalThis.window.opened[0][0], "https://github.com/example/board/issues/133");
});

test("selecting a spec that has no map shows the spec card with no map link", () => {
  const fold = {children: {}, sessions: [], landed: false, returned: false, bounced: false,
    outcome: null, unreadable: [], passed: false, review: null, verdict: null, waiting: null};
  const ticket = {n: 31, title: "its ticket", state: "open", blocked: [], blockers: [], children: [], events: [], fold};
  const spec = {n: 30, title: "lone spec", tickets: [ticket]};
  const tasks = [{n: 30, kind: "spec", title: "lone spec", state: "open", decisions: [], specs: [spec]}];
  const view = fromBoard({tasks, repo: "x/y"}, 30);
  assert.equal(view.kind, "spec");
  assert.equal(view.eyebrow, "Spec");
  assert.deepEqual(view.links, []);
  assert.equal(view.listCount, 1);
});
