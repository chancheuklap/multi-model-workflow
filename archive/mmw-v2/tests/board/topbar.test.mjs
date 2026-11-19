import assert from "node:assert/strict";
import test from "node:test";

import {makeApi} from "../../board/page/api.mjs";
import {fromBoard, render} from "../../board/page/topbar.mjs";
import {installDom, namedButton, walk} from "./fake-dom.mjs";

const morningView = {
  orangeN: 3, greenN: 3, hollowN: 9, inkN: 9, waiting: 1,
  readFailed: false, readText: "只读 · 07:39 读取", settingsOpen: false,
};

const emptyView = {
  orangeN: 0, greenN: 0, hollowN: 0, inkN: 0, waiting: 0,
  readFailed: false, readText: "只读 · 07:39 读取", settingsOpen: false,
};

function counterNs(root) {
  return walk(root)
    .filter(node => (node.className || "").split(/\s+/).includes("counter-n"))
    .map(node => node.textContent);
}

function mount(view, api, hooks) {
  const {document} = installDom();
  const host = document.createElement("div");
  return {document, host, root: render(host, view, api, hooks)};
}

test("a populated view shows the four counts and the waiting sub-line", () => {
  const {root} = mount(morningView);
  assert.equal(root.dataset.screen, "topbar");
  assert.deepEqual(counterNs(root), ["3", "3", "9", "9"]);
  assert.match(root.textContent, /waiting for a slot 1/);
  assert.match(root.textContent, /只读 · 07:39 读取/);
  assert.equal(namedButton(root, "needs you 3").disabled, false);
});

test("an empty view disables needs you and hides the waiting sub-line", () => {
  const {root} = mount(emptyView);
  assert.equal(namedButton(root, "needs you 0").disabled, true);
  assert.deepEqual(counterNs(root), ["0", "0", "0", "0"]);
  assert.equal(walk(root).some(node => (node.className || "").includes("counter-sub")), false);
});

test("立刻重读 GitHub calls POST /api/board/refresh", async () => {
  const calls = [];
  const body = {tasks: [], read_at: "2026-09-11T07:39:00Z"};
  const received = new Promise(resolve => {
    const api = makeApi(async (method, path, fields) => {
      calls.push({method, path, fields});
      return {ok: true, json: async () => body};
    });
    const {root} = mount(morningView, api, {onRefresh: resolve});
    namedButton(root, "立刻重读 GitHub").click();
  });
  assert.equal(await received, body);
  assert.deepEqual(calls, [{method: "POST", path: "/api/board/refresh", fields: undefined}]);
});

test("本机配置 calls GET /api/settings and hands the body to onOpenSettings", async () => {
  const sheet = {version: 1, runner: "orca"};
  const opened = new Promise(resolve => {
    const api = makeApi(async (method, path, fields) => {
      assert.deepEqual({method, path, fields}, {method: "GET", path: "/api/settings", fields: undefined});
      return {ok: true, json: async () => sheet};
    });
    const {root} = mount(morningView, api, {onOpenSettings: resolve});
    namedButton(root, "本机配置").click();
  });
  assert.equal(await opened, sheet);
});

test("本机配置 does not open the sheet when the read fails", async () => {
  let opened = false;
  const {root} = mount(morningView, {
    settings: async () => ({ok: false, json: async () => ({})}),
  }, {onOpenSettings: () => { opened = true; }});
  namedButton(root, "本机配置").click();
  await new Promise(resolve => setTimeout(resolve, 0));
  assert.equal(opened, false);
});

test("topbar actions keep parse and hook failures silent", async () => {
  const malformed = mount(morningView, {
    settings: async () => ({ok: true, json: async () => { throw new Error("bad json"); }}),
  }, {onOpenSettings: () => { throw new Error("must not run"); }});
  namedButton(malformed.root, "本机配置").click();

  const hookFailure = mount(morningView, {
    settings: async () => ({ok: true, json: async () => ({version: 1})}),
  }, {onOpenSettings: () => { throw new Error("hook failed"); }});
  namedButton(hookFailure.root, "本机配置").click();
  await new Promise(resolve => setTimeout(resolve, 0));
});

test("needs you fires onJumpNeedYou only when some ticket is orange", () => {
  let jumps = 0;
  const hooks = {onJumpNeedYou: () => { jumps += 1; }};
  const {root: hot} = mount(morningView, undefined, hooks);
  namedButton(hot, "needs you 3").click();
  assert.equal(jumps, 1);
  const {root: cold} = mount(emptyView, undefined, hooks);
  namedButton(cold, "needs you 0").click();
  assert.equal(jumps, 1);
});

test("a failed read shows the time and age of the data below", () => {
  const orange = {
    n: 3, title: "work", blocked: [], children: [{number: 9, state: "OPEN"}], events: [],
    fold: {
      children: {9: {child: 9, kind: "decision", title: "choose"}},
      sessions: [], landed: false, returned: false, bounced: false,
      outcome: null, waiting: null, review: null,
    },
  };
  const readAt = new Date(2026, 8, 11, 7, 12);
  const now = new Date(2026, 8, 11, 8, 8);
  const view = fromBoard({
    tasks: [{n: 1, specs: [{n: 2, tickets: [orange]}], decisions: []}],
    read_at: readAt.toISOString(),
    read_failed: {at: new Date(2026, 8, 11, 7, 40).toISOString()},
  }, now);
  assert.equal(view.orangeN, 1);
  assert.equal(view.readFailed, true);
  const {root} = mount(view);
  assert.match(root.textContent, /读 GitHub 失败 · 下面是 07:12 的数据（56 分钟前）/);
  assert.equal(namedButton(root, "needs you 1").disabled, false);
});

test("an old read names its day and counts in hours", () => {
  const readAt = new Date(2026, 8, 20, 22, 10);
  const now = new Date(2026, 8, 21, 9, 30);
  const view = fromBoard({
    tasks: [],
    read_at: readAt.toISOString(),
    read_failed: {at: now.toISOString(), message: "offline"},
  }, now);
  const {root} = mount(view);
  assert.match(root.textContent,
    /读 GitHub 失败 · 下面是 9 月 20 日 22:10 的数据（11 小时前）/);
});

test("a board never read names no time", () => {
  const view = fromBoard({
    tasks: [],
    read_failed: {at: "2026-09-11T07:40:00Z", message: "offline"},
  }, new Date("2026-09-11T08:08:00Z"));
  const {root} = mount(view);
  const readState = walk(root).find(node => node.getAttribute("data-ui") === "顶栏.read-state");
  assert.equal(readState.textContent, "读 GitHub 失败");
});
