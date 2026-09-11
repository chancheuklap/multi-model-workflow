import {Board, LIGHT_WORD} from "./board-logic.mjs";

const BEAM_SPEED = 170;
const COMET = [
  [64, 3.4, "#22a06b", 0.10], [40, 3.2, "#22a06b", 0.22], [24, 3.0, "#2fbf7e", 0.45],
  [12, 2.8, "#46d894", 0.85], [5, 2.6, "#effff6", 1],
];
const sessions = new WeakMap();

function css(value) {
  if (value == null || value === "") return "";
  if (typeof value === "string") return value;
  return Object.entries(value)
    .map(([key, val]) => `${key.replace(/[A-Z]/g, ch => `-${ch.toLowerCase()}`)}: ${val}`)
    .join("; ");
}

function px(n) {
  return Math.round(n * 10) / 10 + "px";
}

function prefersReduced() {
  return Boolean(typeof matchMedia === "function"
    && matchMedia("(prefers-reduced-motion: reduce)").matches);
}

function curveLength([x1, y1], [x2, y2]) {
  const dx = Math.max(28, (x2 - x1) * 0.55);
  const points = [[x1, y1], [x1 + dx, y1], [x2 - dx, y2], [x2, y2]];
  let len = 0, prev = points[0];
  for (let i = 1; i <= 32; i++) {
    const t = i / 32, u = 1 - t;
    const pt = [0, 1].map(k =>
      u * u * u * points[0][k] + 3 * u * u * t * points[1][k]
      + 3 * u * t * t * points[2][k] + t * t * t * points[3][k]);
    len += Math.hypot(pt[0] - prev[0], pt[1] - prev[1]);
    prev = pt;
  }
  return len;
}

function beamSVG(edge, reduced) {
  if (reduced) return `<path class="e-beam still" d="${edge.d}"/>`;
  const [a, b] = edge.ends;
  const len = curveLength(a, b);
  const tail = COMET[0][0];
  const dur = Math.max(0.9, (len + tail) / BEAM_SPEED);
  const begin = -(((a[0] * 7 + a[1] * 3 + b[1]) / 53) % dur);
  const f = n => +n.toFixed(2);
  const layers = COMET.map(([length, width, color, opacity]) =>
    `<path d="${edge.d}" stroke="${color}" stroke-opacity="${opacity}" stroke-width="${width}" stroke-dasharray="${f(length)} ${f(len + tail * 3)}" stroke-dashoffset="${f(length)}"><animate attributeName="stroke-dashoffset" from="${f(length)}" to="${f(length - len - tail)}" dur="${f(dur)}s" begin="${f(begin)}s" repeatCount="indefinite"/></path>`).join("");
  const arrive = begin + dur * len / (len + tail);
  return `<g class="e-beam">${layers}</g><circle class="e-pulse" cx="${b[0]}" cy="${b[1]}" r="2.6" opacity="0"><animate attributeName="r" values="2.6;11" dur="${f(dur)}s" begin="${f(arrive)}s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.7;0" dur="${f(dur)}s" begin="${f(arrive)}s" repeatCount="indefinite"/></circle>`;
}

function edgesSVG(layout, sel, selIsIssue, reduced) {
  const order = {done: 0, blocked: 1, flow: 2};
  const blocks = layout.edges.filter(edge => edge.kind === "block")
    .sort((a, b) => order[a.state] - order[b.state]);
  const lines = layout.edges.filter(edge => edge.kind !== "block")
    .map(edge => `<path class="${edge.kind === "trunk" ? "e-trunk" : "e-expand"}" d="${edge.d}"/>`).join("");
  const curves = blocks.map(edge => {
    const hot = selIsIssue && (edge.from === sel || edge.to === sel);
    const cls = `e-block ${edge.state}${hot ? " hot" : ""}${edge.cyc ? " cyc" : ""}`;
    const ports = edge.ends.map(([x, y]) =>
      `<circle class="e-port ${edge.state}" cx="${x}" cy="${y}" r="2.6"/>`).join("");
    return `<path class="${cls}" d="${edge.d}"/>${edge.state === "flow" ? beamSVG(edge, reduced) : ""}${ports}`;
  }).join("");
  return `<svg class="edges" width="${layout.W}" height="${layout.H}" viewBox="0 0 ${layout.W} ${layout.H}" aria-hidden="true">${lines}${curves}</svg>`;
}

export function stillEdges(svg) {
  if (!svg) return svg;
  return svg
    .replace(/<g class="e-beam">[\s\S]*?<\/g>/g, match => {
      const d = /d="([^"]+)"/.exec(match);
      return d ? `<path class="e-beam still" d="${d[1]}"/>` : "";
    })
    .replace(/<circle class="e-pulse"[^>]*>[\s\S]*?<\/circle>/g, "");
}

export function canvasView(task, sel, expandedList, reduced) {
  if (!task) {
    return {
      hasTask: false, noTask: true, containers: [], decisions: [], tickets: [],
      labels: [], worldSize: {}, svg: "", layout: null,
    };
  }
  const expanded = new Set(expandedList);
  const layout = Board.layout(task, expanded);
  const selNode = layout.nodes.find(node => node.id === sel);
  const selIsIssue = Boolean(selNode && (selNode.type === "ticket" || selNode.type === "decision"));
  const pos = node => ({left: px(node.x), top: px(node.y), width: px(node.w), height: px(node.h)});
  const containers = [], decisions = [], tickets = [];
  for (const node of layout.nodes) {
    const on = node.id === sel;
    if (node.type === "ticket") {
      const ticket = node.ref, light = Board.light(ticket), step = Board.step(ticket), run = Board.runLine(ticket);
      tickets.push({
        n: ticket.n, pos: pos(node), title: ticket.title, num: "#" + ticket.n, step,
        pillCls: "pill " + step,
        cls: "card" + (on ? " on" : "") + (ticket.closeout ? " closeout" : "") + (node.cyclic ? " cycle" : ""),
        lightCls: "light " + light, lightWord: LIGHT_WORD[light],
        run: run.text, runCls: run.flag ? "card-run flag" : "card-run",
      });
    } else if (node.type === "decision") {
      const decision = node.ref;
      decisions.push({
        n: decision.n, pos: pos(node), title: decision.title, num: "#" + decision.n, kind: decision.kind,
        cls: "card" + (on ? " on" : ""), lightCls: "light small " + Board.decisionLight(decision),
      });
    } else {
      const container = node.ref, isMap = node.type === "map";
      const list = isMap ? Board.allTickets(container) : container.tickets;
      const light = Board.aggregate(list);
      const done = list.filter(ticket => ticket.fold.landed).length;
      const canExpand = isMap ? container.decisions.length > 0 : container.tickets.length > 0;
      const open = expanded.has(container.n);
      containers.push({
        n: container.n, pos: pos(node), title: container.title,
        num: "#" + container.n + (isMap ? " · " + container.kind : ""),
        cls: "card" + (on ? " on" : ""), titleCls: isMap ? "card-title map" : "card-title",
        lightCls: "light " + light, lightWord: LIGHT_WORD[light], count: `${done}/${list.length}`,
        canExpand, chev: open ? "▾" : "▸", toggleLabel: (open ? "收起 #" : "展开 #") + container.n,
        barStyle: {width: (list.length ? 100 * done / list.length : 0) + "%"},
      });
    }
  }
  return {
    hasTask: true, noTask: false, containers, decisions, tickets,
    labels: layout.labels.map(label => ({
      cls: label.warn ? "lane-label warn" : "lane-label",
      pos: {left: px(label.x), top: px(label.y)},
      text: label.text,
    })),
    worldSize: {width: px(layout.W), height: px(layout.H)},
    svg: edgesSVG(layout, sel, selIsIssue, reduced),
    layout: {W: layout.W, H: layout.H, nodes: layout.nodes.map(node => ({id: node.id, x: node.x, y: node.y, w: node.w, h: node.h}))},
  };
}

function viewFrom(data, sel, expanded, reduced) {
  if (data?.task && typeof data.task === "object") {
    return canvasView(data.task, sel, expanded, reduced);
  }
  const view = data?.vals?.v || data?.view;
  if (!view) {
    return {
      hasTask: false, noTask: true, containers: [], decisions: [], tickets: [],
      labels: [], worldSize: {}, svg: "", layout: null,
    };
  }
  if (!reduced || !view.svg) return view;
  return {...view, svg: stillEdges(view.svg)};
}

function markSelected(view, sel) {
  const mark = (items, extra = "") => items.map(item => ({
    ...item,
    cls: item.cls.split(" ").filter(name => name !== "on").join(" ") + (item.n === sel ? " on" : ""),
  }));
  return {
    ...view,
    containers: mark(view.containers),
    decisions: mark(view.decisions),
    tickets: mark(view.tickets),
  };
}

function cardHit(n, title, onPick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "card-hit";
  button.setAttribute("aria-label", `#${n} ${title}`);
  button.addEventListener("click", () => onPick(n));
  return button;
}

function containerCard(item, onPick, onToggle) {
  const card = document.createElement("div");
  card.className = item.cls;
  card.style.cssText = css(item.pos);
  const light = document.createElement("span");
  light.className = item.lightCls;
  light.title = item.lightWord;
  const num = document.createElement("span");
  num.className = "card-num";
  num.textContent = item.num;
  const count = document.createElement("span");
  count.className = "card-count";
  count.textContent = item.count;
  const right = document.createElement("span");
  right.className = "card-right";
  right.append(count);
  if (item.canExpand) {
    const chev = document.createElement("button");
    chev.type = "button";
    chev.className = "chev";
    chev.setAttribute("aria-label", item.toggleLabel);
    chev.textContent = item.chev;
    chev.addEventListener("click", event => {
      event.stopPropagation();
      onToggle(item.n);
    });
    right.append(chev);
  }
  const top = document.createElement("div");
  top.className = "card-top";
  top.append(light, num, right);
  const title = document.createElement("div");
  title.className = item.titleCls;
  title.textContent = item.title;
  const fill = document.createElement("div");
  fill.className = "card-bar-fill";
  fill.style.cssText = css(item.barStyle);
  const bar = document.createElement("div");
  bar.className = "card-bar";
  bar.append(fill);
  card.append(cardHit(item.n, item.title, onPick), top, title, bar);
  return card;
}

function decisionCard(item, onPick) {
  const card = document.createElement("div");
  card.className = item.cls;
  card.style.cssText = css(item.pos);
  card.title = item.title;
  const light = document.createElement("span");
  light.className = item.lightCls;
  const num = document.createElement("span");
  num.className = "card-num";
  num.textContent = item.num;
  const kind = document.createElement("span");
  kind.className = "card-kind";
  kind.textContent = item.kind;
  const right = document.createElement("span");
  right.className = "card-right";
  right.append(kind);
  const top = document.createElement("div");
  top.className = "card-top";
  top.append(light, num, right);
  const title = document.createElement("div");
  title.className = "card-title decision";
  title.textContent = item.title;
  card.append(cardHit(item.n, item.title, onPick), top, title);
  return card;
}

function ticketCard(item, onPick) {
  const card = document.createElement("div");
  card.className = item.cls;
  card.style.cssText = css(item.pos);
  card.title = item.title;
  const light = document.createElement("span");
  light.className = item.lightCls;
  light.title = item.lightWord;
  const num = document.createElement("span");
  num.className = "card-num";
  num.textContent = item.num;
  const pill = document.createElement("span");
  pill.className = item.pillCls;
  pill.textContent = item.step;
  const right = document.createElement("span");
  right.className = "card-right";
  right.append(pill);
  const top = document.createElement("div");
  top.className = "card-top";
  top.append(light, num, right);
  const title = document.createElement("div");
  title.className = "card-title";
  title.textContent = item.title;
  const run = document.createElement("div");
  run.className = item.runCls;
  run.textContent = item.run;
  card.append(cardHit(item.n, item.title, onPick), top, title, run);
  return card;
}

function legend() {
  const root = document.createElement("div");
  root.className = "legend";
  const item = (lineClass, text) => {
    const span = document.createElement("span");
    span.className = "legend-item";
    const line = document.createElement("span");
    line.className = lineClass;
    span.append(line, text);
    return span;
  };
  const bar = document.createElement("span");
  bar.className = "legend-item";
  const mark = document.createElement("span");
  mark.className = "legend-bar";
  bar.append(mark, "收口新开");
  root.append(
    item("legend-line", "展开 · 走过"),
    item("legend-line flow", "在走"),
    item("legend-line blocked", "被挡"),
    bar,
  );
  return root;
}

function zoomBar(onOut, onIn, onFit, level) {
  const root = document.createElement("div");
  root.className = "zoom";
  const out = document.createElement("button");
  out.type = "button";
  out.className = "zoom-btn";
  out.setAttribute("aria-label", "缩小");
  out.textContent = "−";
  out.addEventListener("click", onOut);
  const zoomLevel = document.createElement("span");
  zoomLevel.className = "zoom-level";
  zoomLevel.textContent = level;
  const inn = document.createElement("button");
  inn.type = "button";
  inn.className = "zoom-btn";
  inn.setAttribute("aria-label", "放大");
  inn.textContent = "+";
  inn.addEventListener("click", onIn);
  const sep = document.createElement("span");
  sep.className = "zoom-sep";
  const fit = document.createElement("button");
  fit.type = "button";
  fit.className = "zoom-btn text";
  fit.textContent = "适配";
  fit.addEventListener("click", onFit);
  root.append(out, zoomLevel, inn, sep, fit);
  return {root, zoomLevel};
}

function emptyState() {
  const root = document.createElement("div");
  root.className = "canvas-empty";
  const wrap = document.createElement("div");
  const title = document.createElement("p");
  title.className = "canvas-empty-title";
  title.textContent = "还没有任务";
  const text = document.createElement("p");
  text.className = "canvas-empty-text";
  text.append("一个任务就是一次讨论开出的那张票。给它打上 ");
  const code = document.createElement("span");
  code.className = "code";
  code.textContent = "mmw:map";
  text.append(code, " label，下一次读取时它和它下面的 spec、ticket 就会出现在这里。");
  wrap.append(title, text);
  root.append(wrap);
  return root;
}

function clampK(k) {
  return Math.min(1.6, Math.max(0.3, k));
}

export function render(host, data = {}, api = undefined) {
  const prior = sessions.get(host);
  if (prior) prior.cleanup();

  const reduced = prefersReduced();
  const state = {
    sel: data.state?.sel ?? data.sel ?? null,
    expanded: [...(data.state?.expanded ?? data.expanded ?? [])],
    view: {x: 20, y: 12, k: 1},
    didInit: false,
    drag: null,
    suppress: false,
  };

  const root = document.createElement("main");
  root.dataset.screen = "canvas";
  root.className = "canvas board";
  root.setAttribute("aria-label", "画布：拖动平移，按住 ⌘ 或双指捏合缩放");

  let worldEl, edgesEl, zoomEl, lastView;

  const size = () => ({width: root.offsetWidth, height: root.offsetHeight});

  const applyView = () => {
    const v = state.view;
    if (worldEl) worldEl.style.transform = `translate(${v.x}px, ${v.y}px) scale(${v.k})`;
    if (zoomEl) zoomEl.textContent = Math.round(v.k * 100) + "%";
  };

  const box = n => lastView?.layout?.nodes.find(node => node.id === n) || null;

  const initialView = () => {
    const layout = lastView?.layout;
    if (!layout) return;
    const r = size();
    if (!r.width || !r.height) return;
    const kFit = Math.min((r.width - 40) / layout.W, (r.height - 70) / layout.H);
    const v = state.view = {k: clampK(Math.max(0.9, Math.min(1, kFit))), x: 20, y: 12};
    const b = state.sel != null ? box(state.sel) : null;
    if (b) {
      if ((b.y + b.h) * v.k + v.y > r.height - 70) v.y = Math.min(12, r.height * 0.45 - (b.y + b.h / 2) * v.k);
      if ((b.x + b.w) * v.k + v.x > r.width - 24) v.x = Math.min(20, r.width - 24 - (b.x + b.w) * v.k);
    }
    applyView();
    state.didInit = true;
  };

  const zoomAt = (k2, cx, cy) => {
    const v = state.view;
    k2 = clampK(k2);
    v.x = cx - (cx - v.x) * (k2 / v.k);
    v.y = cy - (cy - v.y) * (k2 / v.k);
    v.k = k2;
    applyView();
  };

  const fitView = () => {
    const layout = lastView?.layout;
    if (!layout) return;
    const r = size();
    const k = clampK(Math.min(1, (r.width - 40) / layout.W, (r.height - 70) / layout.H));
    state.view = {k, x: Math.max(12, (r.width - layout.W * k) / 2), y: 12};
    applyView();
  };

  const center = () => {
    const r = size();
    return [r.width / 2, r.height / 2];
  };

  const choose = n => {
    if (state.suppress) return;
    state.sel = n;
    data.onSelectNode?.(n);
    paint(false);
  };

  const toggleOpen = n => {
    const expanded = new Set(state.expanded);
    if (expanded.has(n)) expanded.delete(n);
    else expanded.add(n);
    state.expanded = [...expanded];
    data.onToggle?.(n, state.expanded);
    paint(false);
  };

  const paint = (resetView) => {
    lastView = viewFrom(data, state.sel, state.expanded, reduced);
    if (data.vals?.v || data.view) lastView = markSelected(lastView, state.sel);
    root.replaceChildren();
    worldEl = edgesEl = zoomEl = null;
    if (lastView.noTask || !lastView.hasTask) {
      root.append(emptyState());
      return;
    }
    const world = document.createElement("div");
    world.className = "world";
    world.style.cssText = css(lastView.worldSize);
    worldEl = world;
    const edges = document.createElement("div");
    edges.className = "edges-host";
    edges.innerHTML = lastView.svg || "";
    edgesEl = edges;
    world.append(edges);
    for (const label of lastView.labels) {
      const node = document.createElement("div");
      node.className = label.cls;
      node.style.cssText = css(label.pos);
      node.textContent = label.text;
      world.append(node);
    }
    for (const item of lastView.containers) world.append(containerCard(item, choose, toggleOpen));
    for (const item of lastView.decisions) world.append(decisionCard(item, choose));
    for (const item of lastView.tickets) world.append(ticketCard(item, choose));
    const zoom = zoomBar(
      () => { const [cx, cy] = center(); zoomAt(state.view.k / 1.2, cx, cy); },
      () => { const [cx, cy] = center(); zoomAt(state.view.k * 1.2, cx, cy); },
      fitView,
      Math.round(state.view.k * 100) + "%",
    );
    zoomEl = zoom.zoomLevel;
    root.append(world, legend(), zoom.root);
    if (resetView) state.didInit = false;
    if (!state.didInit) initialView();
    else applyView();
  };

  const onPointerDown = event => {
    if (event.button !== 0 || event.target.closest?.(".zoom, .legend, .chev")) return;
    state.drag = {
      x: event.clientX, y: event.clientY,
      vx: state.view.x, vy: state.view.y,
      moved: false, id: event.pointerId,
    };
  };
  const onWheel = event => {
    if (!lastView?.layout) return;
    event.preventDefault();
    const r = root.getBoundingClientRect();
    if (event.ctrlKey || event.metaKey) zoomAt(state.view.k * Math.exp(-event.deltaY * 0.01), event.clientX - r.left, event.clientY - r.top);
    else {
      state.view.x -= event.deltaX;
      state.view.y -= event.deltaY;
      applyView();
    }
  };
  const onMove = event => {
    const drag = state.drag;
    if (!drag || event.pointerId !== drag.id) return;
    const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
    if (!drag.moved && Math.hypot(dx, dy) > 4) {
      drag.moved = true;
      root.classList.add("dragging");
    }
    if (drag.moved) {
      state.view.x = drag.vx + dx;
      state.view.y = drag.vy + dy;
      applyView();
    }
  };
  const onUp = event => {
    const drag = state.drag;
    if (!drag || event.pointerId !== drag.id) return;
    state.drag = null;
    root.classList.remove("dragging");
    if (drag.moved) {
      state.suppress = true;
      setTimeout(() => { state.suppress = false; }, 0);
    }
  };
  const onKey = event => {
    if (event.target.closest?.("input, textarea, [contenteditable]")) return;
    if (event.key === "f" && !event.metaKey && !event.ctrlKey) fitView();
  };

  root.addEventListener("pointerdown", onPointerDown);
  root.addEventListener("wheel", onWheel, {passive: false});
  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", onUp);
  window.addEventListener("keydown", onKey);

  paint(true);
  host.replaceChildren(root);
  if (!state.didInit) queueMicrotask(initialView);

  let observer;
  if (typeof ResizeObserver === "function") {
    observer = new ResizeObserver(() => {
      if (!state.didInit) initialView();
    });
    observer.observe(root);
  }

  sessions.set(host, {
    cleanup() {
      root.removeEventListener("pointerdown", onPointerDown);
      root.removeEventListener("wheel", onWheel);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("keydown", onKey);
      observer?.disconnect();
    },
  });
  return root;
}
