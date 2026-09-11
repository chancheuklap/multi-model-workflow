import assert from "node:assert/strict";
import test from "node:test";

import {render} from "../../board/page/detail.mjs";

const ticket = {
  vals: {
    repo: "chancheuklap/multi-model-workflow",
    d: {
      isTicket: true, hasCard: true, eyebrow: "Ticket", num: "#133",
      title: "折叠接入中继", lightCls: "light big orange", statusWord: "需要你",
      statusCls: "status-word orange", elapsed: "已跑 1h02m", pillCls: "pill big working",
      step: "working", hint: "现在在这一步",
      path: [
        {name: "queued", cls: "path-step done", sep: true},
        {name: "working", cls: "path-step now-working", sep: true},
        {name: "waiting", cls: "path-step", sep: true},
        {name: "review", cls: "path-step", sep: true},
        {name: "verify", cls: "path-step", sep: true},
        {name: "landed", cls: "path-step", sep: false},
      ],
      hasWhy: true,
      why: [{head: "#150 contract", body: "spec 本身不成立，要回到写 spec 的人"}],
      hasWorker: true, facts: [{k: "host", v: "grok · grok 4.6 · xhigh"}],
      manySessions: false, sessions: [], closeout: false, ghLabel: "在 GitHub 打开 #133 ↗", gh: 133,
      noBlockers: false, noBlocks: false, noKids: false, noEvents: false,
      kidCount: 1, eventCount: "1 条评论",
      events: [{time: "06:38", name: "worker.started", nameCls: "ev-name",
        field: "herdr · w94b8 · cheuk-mbp", line: "worker started", dotCls: "light green ev-dot"}],
    },
    emptyTitle: "点一张卡",
    emptyText: "画布上任意一张卡——map、spec、ticket 或决策票——点一下，它的全部细节就在这一栏。",
    runtimeNote: "取自 worker.started",
    noWorker: false,
    links: [{label: "spec #131", n: 131}, {label: "map #98", n: 98}],
    blockers: [{n: 132, known: true, unknown: false, num: "#132", lightCls: "light ink",
      title: "中继进程骨架", where: "", state: "已合入", stateCls: "rel-state"}],
    blocks: [{n: 135, known: true, unknown: false, num: "#135", lightCls: "light hollow",
      title: "投递回执", where: "", state: "待派", stateCls: "rel-state"}],
    kids: [{num: "#150", kind: "contract", title: "spec 没写队列为空时中继读什么",
      to: "等你", toCls: "kid-to orange", hasGoto: false, noGoto: true, lightCls: "light orange"}],
    ticketRows: [], specRows: [], decisionRows: [],
  },
};

const empty = {
  vals: {
    d: {isEmpty: true, hasCard: false, hasTasks: false},
    emptyTitle: "这里是详情",
    emptyText: "有了任务之后，点画布上的卡，它的细节显示在这一栏。",
    links: [], blockers: [], blocks: [], kids: [], ticketRows: [], specRows: [], decisionRows: [],
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

function textOf(node) {
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
  return walk(root).find(node => node.tagName === "BUTTON" && textOf(node) === name);
}

function mount(data, api, hooks) {
  const {document, window} = installDom();
  const host = document.createElement("div");
  return {document, window, host, root: render(host, data, api, hooks)};
}

test("empty scene shows the empty copy and no GitHub button", () => {
  const {root} = mount(empty);
  assert.equal(root.dataset.screen, "detail");
  assert.equal(root.getAttribute("aria-label"), "详情");
  assert.match(root.textContent, /这里是详情/);
  assert.equal(namedButton(root, "在 GitHub 打开 #133 ↗"), undefined);
});

test("a ticket scene shows origin, status, why-orange, and GitHub", () => {
  const {root} = mount(ticket);
  assert.ok(namedButton(root, "关闭详情"));
  assert.ok(namedButton(root, "spec #131"));
  assert.ok(namedButton(root, "map #98"));
  assert.match(root.textContent, /折叠接入中继/);
  assert.match(root.textContent, /为什么是橙的/);
  assert.match(root.textContent, /取自 worker.started/);
  assert.ok(namedButton(root, "#132 中继进程骨架 已合入"));
  assert.ok(namedButton(root, "在 GitHub 打开 #133 ↗"));
  const heading = walk(root).find(node => node.tagName === "H2");
  assert.equal(textOf(heading), "折叠接入中继");
});

test("关闭详情 and Escape call onClose", () => {
  let closed = 0;
  const {root, document} = mount(ticket, undefined, {onClose: () => { closed += 1; }});
  namedButton(root, "关闭详情").click();
  assert.equal(closed, 1);
  document.dispatchEvent({type: "keydown", key: "Escape", preventDefault() {}});
  assert.equal(closed, 2);
});

test("ticket numbers in the panel call onGoto", () => {
  const seen = [];
  const {root} = mount(ticket, undefined, {onGoto: n => seen.push(n)});
  namedButton(root, "spec #131").click();
  namedButton(root, "#132 中继进程骨架 已合入").click();
  namedButton(root, "#135 投递回执 待派").click();
  assert.deepEqual(seen, [131, 132, 135]);
});

test("在 GitHub 打开 uses a new tab and does not call the API client", () => {
  const {root, window} = mount(ticket, {refresh() { throw new Error("board wrote"); }});
  namedButton(root, "在 GitHub 打开 #133 ↗").click();
  assert.deepEqual(window.opened, [
    ["https://github.com/chancheuklap/multi-model-workflow/issues/133", "_blank", "noopener,noreferrer"],
  ]);
});
