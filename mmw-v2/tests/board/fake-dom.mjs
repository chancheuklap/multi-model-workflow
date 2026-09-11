export class TextNode {
  constructor(text) {
    this.nodeType = 3;
    this.textContent = String(text);
    this.children = [];
    this.tagName = "";
    this.attrs = {};
  }
}

export class Elem {
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

export function installDom() {
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

export function walk(node) {
  const out = [];
  const visit = current => {
    if (current.nodeType === 1) out.push(current);
    for (const child of current.children || []) visit(child);
  };
  visit(node);
  return out;
}

export function accessibleName(node) {
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
