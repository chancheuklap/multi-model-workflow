import assert from "node:assert/strict";
import test from "node:test";

import {render} from "../../board/page/topbar.mjs";

const morning = {
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

const empty = {
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
    this._style = {};
    const self = this;
    this.style = new Proxy(this._style, {
      get(obj, key) { return obj[key]; },
      set(obj, key, value) { obj[key] = value; return true; },
    });
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
  const window = {opened: [], open(...args) { window.opened.push(args); }};
  globalThis.document = document;
  globalThis.window = window;
  return {document, window};
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

function mount(data, api, hooks) {
  const {document} = installDom();
  const host = document.createElement("div");
  return {document, host, root: render(host, data, api, hooks)};
}

test("morning vals show the four counts and the waiting sub-line", () => {
  const {root} = mount(morning);
  assert.equal(root.dataset.screen, "topbar");
  assert.equal(root.getAttribute("class"), "topbar board");
  assert.match(root.textContent, /需要你/);
  assert.match(root.textContent, /在跑/);
  assert.match(root.textContent, /其中等槽位 1/);
  assert.match(root.textContent, /待派/);
  assert.match(root.textContent, /好了/);
  assert.match(root.textContent, /只读 · 07:39 读取/);
  assert.equal(namedButton(root, "需要你 3").disabled, false);
  assert.ok(namedButton(root, "立刻重读 GitHub"));
  assert.ok(namedButton(root, "本机配置"));
});

test("empty vals disable 需要你 and hide the waiting sub-line", () => {
  const {root} = mount(empty);
  const need = namedButton(root, "需要你 0");
  assert.equal(need.disabled, true);
  assert.equal(walk(root).some(node => (node.className || "").includes("counter-sub")), false);
});

test("立刻重读 GitHub calls POST /api/board/refresh", () => {
  const calls = [];
  const {root} = mount(morning, {
    refresh: () => calls.push(["POST", "/api/board/refresh"]),
  });
  namedButton(root, "立刻重读 GitHub").click();
  assert.deepEqual(calls, [["POST", "/api/board/refresh"]]);
});

test("本机配置 calls GET /api/settings and hands the body to onOpenSettings", async () => {
  const sheet = {version: 1, runner: "orca"};
  let opened;
  const {root} = mount(morning, {
    settings: async () => ({ok: true, json: async () => sheet}),
  }, {onOpenSettings: value => { opened = value; }});
  namedButton(root, "本机配置").click();
  await Promise.resolve();
  await Promise.resolve();
  assert.equal(opened, sheet);
});

test("需要你 fires onJumpNeedYou only when some ticket is orange", () => {
  let jumps = 0;
  const hooks = {onJumpNeedYou: () => { jumps += 1; }};
  const {root: hot} = mount(morning, undefined, hooks);
  namedButton(hot, "需要你 3").click();
  assert.equal(jumps, 1);
  const {root: cold} = mount(empty, undefined, hooks);
  namedButton(cold, "需要你 0").click();
  assert.equal(jumps, 1);
});
