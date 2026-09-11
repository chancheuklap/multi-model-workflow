import assert from "node:assert/strict";
import test from "node:test";

import {makeApi} from "../../board/page/api.mjs";
import {fromBoard, fromScene, render} from "../../board/page/topbar.mjs";

const morningScene = {
  vals: {
    v: {
      orangeN: 3, greenN: 3, hollowN: 9, inkN: 9, hot: true,
      needCls: "counter hot", needNCls: "counter-n hot", needLightCls: "light orange",
      waitingSub: "其中等槽位 1", readCls: "readstate", readText: "只读 · 07:39 读取",
      noNeed: false, hasWaiting: true,
    },
    gearCls: "gear",
  },
};

const emptyScene = {
  vals: {
    v: {
      orangeN: 0, greenN: 0, hollowN: 0, inkN: 0, hot: false,
      needCls: "counter", needNCls: "counter-n", needLightCls: "light hollow",
      waitingSub: "", readCls: "readstate", readText: "只读 · 07:39 读取",
      noNeed: true, hasWaiting: false,
    },
    gearCls: "gear",
  },
};

class TextNode {
  constructor(text) {
    this.nodeType = 3;
    this.textContent = String(text);
    this.children = [];
    this.tagName = "";
    this.attrs = {};
  }
}

class Elem {
  constructor(tag, doc) {
    this.tagName = String(tag).toUpperCase();
    this.nodeType = 1;
    this.children = [];
    this.attrs = Object.create(null);
    this.listeners = Object.create(null);
    this.ownerDocument = doc;
    this._disabled = false;
    this.style = {};
    const self = this;
    this.dataset = new Proxy({}, {
      get(_, key) {
        return self.getAttribute("data-" + String(key).replace(/[A-Z]/g, ch => `-${ch.toLowerCase()}`));
      },
      set(_, key, value) {
        self.setAttribute("data-" + String(key).replace(/[A-Z]/g, ch => `-${ch.toLowerCase()}`), value);
        return true;
      },
    });
  }
  set className(value) { this.setAttribute("class", value); }
  get className() { return this.getAttribute("class") || ""; }
  set disabled(value) {
    this._disabled = Boolean(value);
    if (value) this.setAttribute("disabled", "");
    else delete this.attrs.disabled;
  }
  get disabled() { return this._disabled; }
  set innerHTML(value) { this._innerHTML = String(value); this.children = []; }
  get innerHTML() { return this._innerHTML || ""; }
  set textContent(value) {
    const node = new TextNode(value);
    node.parentNode = this;
    this.children = [node];
  }
  get textContent() {
    if (this._innerHTML) return this._innerHTML.replace(/<[^>]+>/g, "");
    return this.children.map(child => child.textContent).join("");
  }
  setAttribute(key, value) { this.attrs[key] = String(value); }
  getAttribute(key) { return key in this.attrs ? this.attrs[key] : null; }
  appendChild(child) { child.parentNode = this; this.children.push(child); return child; }
  append(...nodes) {
    for (const node of nodes) this.appendChild(typeof node === "string" ? new TextNode(node) : node);
  }
  replaceChildren(...nodes) { this.children = []; this.append(...nodes); }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  removeEventListener(type, fn) {
    this.listeners[type] = (this.listeners[type] || []).filter(item => item !== fn);
  }
  dispatchEvent(event) { for (const fn of this.listeners[event.type] || []) fn(event); }
  click() {
    if (this._disabled) return;
    this.dispatchEvent({type: "click", preventDefault() {}, target: this});
  }
}

function installDom() {
  const listeners = Object.create(null);
  const document = {
    createElement: tag => new Elem(tag, document),
    addEventListener: (type, fn) => { (listeners[type] ||= []).push(fn); },
    removeEventListener: (type, fn) => {
      listeners[type] = (listeners[type] || []).filter(item => item !== fn);
    },
    dispatchEvent: event => { for (const fn of listeners[event.type] || []) fn(event); },
  };
  globalThis.document = document;
  globalThis.window = {opened: [], open(...args) { window.opened.push(args); }};
  return {document, window: globalThis.window};
}

function walk(node) {
  const out = [];
  const visit = current => {
    if (current.nodeType === 1) out.push(current);
    for (const child of current.children || []) visit(child);
  };
  visit(node);
  return out;
}

function accName(node) {
  const label = node.getAttribute?.("aria-label");
  if (label) return label.replace(/\s+/g, " ").trim();
  const parts = [];
  const visit = current => {
    if (current.nodeType === 3) {
      const text = String(current.textContent || "").replace(/\s+/g, " ").trim();
      if (text) parts.push(text);
      return;
    }
    for (const child of current.children || []) visit(child);
  };
  visit(node);
  return parts.join(" ");
}

function namedButton(root, name) {
  return walk(root).find(node => node.tagName === "BUTTON" && accName(node) === name);
}

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

test("morning vals show the four counts and the waiting sub-line", () => {
  const {root} = mount(fromScene(morningScene));
  assert.equal(root.dataset.screen, "topbar");
  assert.deepEqual(counterNs(root), ["3", "3", "9", "9"]);
  assert.match(root.textContent, /其中等槽位 1/);
  assert.match(root.textContent, /只读 · 07:39 读取/);
  assert.equal(namedButton(root, "需要你 3").disabled, false);
});

test("empty vals disable 需要你 and hide the waiting sub-line", () => {
  const {root} = mount(fromScene(emptyScene));
  assert.equal(namedButton(root, "需要你 0").disabled, true);
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
    const {root} = mount(fromScene(morningScene), api, {onRefresh: resolve});
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
    const {root} = mount(fromScene(morningScene), api, {onOpenSettings: resolve});
    namedButton(root, "本机配置").click();
  });
  assert.equal(await opened, sheet);
});

test("本机配置 does not open the sheet when the read fails", async () => {
  let opened = false;
  const {root} = mount(fromScene(morningScene), {
    settings: async () => ({ok: false, json: async () => ({})}),
  }, {onOpenSettings: () => { opened = true; }});
  namedButton(root, "本机配置").click();
  await new Promise(resolve => setTimeout(resolve, 0));
  assert.equal(opened, false);
});

test("需要你 fires onJumpNeedYou only when some ticket is orange", () => {
  let jumps = 0;
  const hooks = {onJumpNeedYou: () => { jumps += 1; }};
  const {root: hot} = mount(fromScene(morningScene), undefined, hooks);
  namedButton(hot, "需要你 3").click();
  assert.equal(jumps, 1);
  const {root: cold} = mount(fromScene(emptyScene), undefined, hooks);
  namedButton(cold, "需要你 0").click();
  assert.equal(jumps, 1);
});

test("fromBoard maps GET /api/board lamps and a failed read onto the top bar", () => {
  const orange = {
    n: 3, title: "work", blocked: [], children: [{number: 9, state: "OPEN"}], events: [],
    fold: {
      children: {9: {child: 9, kind: "decision", title: "choose"}},
      sessions: [], landed: false, returned: false, bounced: false,
      outcome: null, waiting: null, review: null, verdict: null,
    },
  };
  const view = fromBoard({
    tasks: [{n: 1, specs: [{n: 2, tickets: [orange]}], decisions: []}],
    read_at: "2026-09-11T07:12:00Z",
    read_failed: {at: "2026-09-11T07:40:00Z"},
  }, new Date("2026-09-11T08:08:00Z"));
  assert.equal(view.orangeN, 1);
  assert.equal(view.readFailed, true);
  assert.equal(view.readAgo, 28);
  const {root} = mount(view);
  assert.match(root.textContent, /读 GitHub 失败 · 下面是 \d{2}:\d{2} 的数据（28 分钟前）/);
  assert.equal(namedButton(root, "需要你 1").disabled, false);
});
