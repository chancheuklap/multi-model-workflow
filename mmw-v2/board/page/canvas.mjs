import {Board, LAMP_WORD, defaultExpanded} from "./board-logic.mjs";

const BEAM_SPEED = 170; // px per second
const COMET = [ // length px, stroke width, colour, opacity — tail first, head last
  [64, 3.4, "#22a06b", 0.10], [40, 3.2, "#22a06b", 0.22], [24, 3.0, "#2fbf7e", 0.45],
  [12, 2.8, "#46d894", 0.85], [5, 2.6, "#effff6", 1],
];
const mounted = new WeakMap();

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
    .map(edge => `<path class="${edge.kind === "trunk" ? "e-trunk" : "e-expand"}" d="${edge.d}"/>`
      + (edge.kind === "expand" && edge.state === "flow" ? beamSVG(edge, reduced) : "")).join("");
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
      const ticket = node.ref, lamp = Board.lamp(ticket), phase = Board.phase(ticket), run = Board.runLine(ticket);
      tickets.push({
        n: ticket.n, pos: pos(node), title: ticket.title, num: "#" + ticket.n, phase,
        pillCls: "pill " + phase,
        cls: "card" + (on ? " on" : "") + (ticket.closeout ? " closeout" : "") + (node.cyclic ? " cycle" : ""),
        lampCls: "lamp " + lamp, lampWord: LAMP_WORD[lamp],
        run: run.text, runCls: run.flag ? "card-run flag" : "card-run",
      });
    } else if (node.type === "decision") {
      const decision = node.ref;
      decisions.push({
        n: decision.n, pos: pos(node), title: decision.title, num: "#" + decision.n, kind: decision.kind,
        cls: "card" + (on ? " on" : "") + (node.cyclic ? " cycle" : ""),
        lampCls: "lamp small " + Board.decisionLamp(decision),
      });
    } else {
      const container = node.ref, isMap = node.type === "map";
      const list = isMap ? Board.allTickets(container) : container.tickets;
      const lamp = Board.aggregate(list);
      const done = list.filter(ticket => Board.done(ticket)).length;
      const canExpand = isMap ? container.decisions.length > 0 : container.tickets.length > 0;
      const open = expanded.has(container.n);
      containers.push({
        n: container.n, pos: pos(node), title: container.title,
        num: "#" + container.n + (isMap ? " · " + container.kind : ""),
        cls: "card" + (on ? " on" : ""), titleCls: "card-title one-line",
        lampCls: "lamp " + lamp, lampWord: LAMP_WORD[lamp], count: `${done}/${list.length}`,
        canExpand, chev: open ? "▾" : "▸", toggleLabel: (open ? "collapse #" : "expand #") + container.n,
        barStyle: {width: (list.length ? 100 * done / list.length : 0) + "%"},
      });
    }
  }
  return {
    hasTask: true, noTask: false, containers, decisions, tickets,
    labels: layout.labels.map(label => ({
      cls: label.warn ? "eyebrow warn" : "eyebrow",
      pos: {left: px(label.x), top: px(label.y)},
      text: label.text,
    })),
    worldSize: {width: px(layout.W), height: px(layout.H)},
    svg: edgesSVG(layout, sel, selIsIssue, reduced),
    layout: {W: layout.W, H: layout.H, nodes: layout.nodes.map(node => ({id: node.id, x: node.x, y: node.y, w: node.w, h: node.h}))},
  };
}

function markSelected(view, sel) {
  const mark = items => items.map(item => ({
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

function present(data, sel, expanded, reduced) {
  if (typeof data.project === "function") return data.project(sel, expanded, reduced);
  if (data.task && typeof data.task === "object") {
    return canvasView(data.task, sel, expanded, reduced);
  }
  if (!data.view) return canvasView(null);
  const view = reduced && data.view.svg ? {...data.view, svg: stillEdges(data.view.svg)} : data.view;
  return markSelected(view, sel);
}

function dataUi(node, id) {
  node.setAttribute("data-ui", id);
  return node;
}

function cardHit(n, title, onPick, ui) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "card-hit";
  button.setAttribute("aria-label", `#${n} ${title}`);
  dataUi(button, `${ui}.open`);
  button.addEventListener("click", () => onPick(n));
  return button;
}

function cardShell(item, onPick, {ui, lampTitle, titled, titleCls, right, after}) {
  const card = document.createElement("div");
  card.className = item.cls;
  dataUi(card, ui);
  Object.assign(card.style, item.pos);
  if (titled) card.title = item.title;
  const lamp = document.createElement("span");
  lamp.className = item.lampCls;
  dataUi(lamp, `${ui}.lamp`);
  if (lampTitle) lamp.title = item.lampWord;
  const num = document.createElement("span");
  num.className = "card-num";
  dataUi(num, `${ui}.num`);
  num.textContent = item.num;
  const rightEl = document.createElement("span");
  rightEl.className = "card-right";
  rightEl.append(...right);
  const top = document.createElement("div");
  top.className = "card-top";
  top.append(lamp, num, rightEl);
  const title = document.createElement("div");
  title.className = titleCls;
  dataUi(title, `${ui}.title`);
  title.textContent = item.title;
  card.append(cardHit(item.n, item.title, onPick, ui), top, title, ...after);
  return card;
}

function containerCard(item, onPick, onToggle) {
  const ui = "画布.container-card";
  const count = document.createElement("span");
  count.className = "card-count";
  dataUi(count, `${ui}.count`);
  count.textContent = item.count;
  const right = [count];
  if (item.canExpand) {
    const chev = document.createElement("button");
    chev.type = "button";
    chev.className = "iconbtn sm bare";
    chev.setAttribute("aria-label", item.toggleLabel);
    dataUi(chev, `${ui}.expand`);
    chev.textContent = item.chev;
    chev.addEventListener("click", event => {
      event.stopPropagation();
      onToggle(item.n);
    });
    right.push(chev);
  }
  const fill = document.createElement("div");
  fill.className = "bar-fill";
  dataUi(fill, `${ui}.bar`);
  fill.style.width = item.barStyle.width;
  const bar = document.createElement("div");
  bar.className = "bar thin";
  bar.append(fill);
  return cardShell(item, onPick, {
    ui, lampTitle: true, titled: true, titleCls: item.titleCls, right, after: [bar],
  });
}

function decisionCard(item, onPick) {
  const ui = "画布.decision-card";
  const kind = document.createElement("span");
  kind.className = "card-kind";
  dataUi(kind, `${ui}.kind`);
  kind.textContent = item.kind;
  return cardShell(item, onPick, {
    ui, lampTitle: false, titled: true, titleCls: "card-title decision", right: [kind], after: [],
  });
}

function ticketCard(item, onPick) {
  const ui = "画布.ticket-card";
  const pill = document.createElement("span");
  pill.className = item.pillCls;
  dataUi(pill, `${ui}.phase`);
  pill.textContent = item.phase;
  const run = document.createElement("div");
  run.className = item.runCls;
  dataUi(run, `${ui}.run`);
  run.textContent = item.run;
  return cardShell(item, onPick, {
    ui, lampTitle: true, titled: true, titleCls: "card-title", right: [pill], after: [run],
  });
}

function legend() {
  const root = document.createElement("div");
  root.className = "legend";
  dataUi(root, "画布.legend");
  const item = (lineClass, text, name) => {
    const span = document.createElement("span");
    span.className = "legend-item";
    dataUi(span, `画布.legend.${name}`);
    const line = document.createElement("span");
    line.className = lineClass;
    span.append(line, text);
    return span;
  };
  const bar = document.createElement("span");
  bar.className = "legend-item";
  dataUi(bar, "画布.legend.closeout");
  const mark = document.createElement("span");
  mark.className = "legend-bar";
  bar.append(mark, "closing pass");
  root.append(
    item("legend-line", "contains · released", "walked"),
    item("legend-line flow", "released · working", "flow"),
    item("legend-line blocked", "blocked", "blocked"),
    bar,
  );
  return root;
}

function zoomBar(onOut, onIn, onFit, level) {
  const root = document.createElement("div");
  root.className = "toolbar";
  dataUi(root, "画布.zoom");
  const out = document.createElement("button");
  out.type = "button";
  out.className = "iconbtn sm bare round";
  out.setAttribute("aria-label", "zoom out");
  dataUi(out, "画布.zoom.out");
  out.textContent = "−";
  out.addEventListener("click", onOut);
  const zoomLevel = document.createElement("span");
  zoomLevel.className = "toolbar-value";
  dataUi(zoomLevel, "画布.zoom.level");
  zoomLevel.textContent = level;
  const inn = document.createElement("button");
  inn.type = "button";
  inn.className = "iconbtn sm bare round";
  inn.setAttribute("aria-label", "zoom in");
  dataUi(inn, "画布.zoom.in");
  inn.textContent = "+";
  inn.addEventListener("click", onIn);
  const sep = document.createElement("span");
  sep.className = "toolbar-sep";
  const fit = document.createElement("button");
  fit.type = "button";
  fit.className = "iconbtn sm bare round fit";
  dataUi(fit, "画布.zoom.fit");
  fit.textContent = "fit";
  fit.addEventListener("click", onFit);
  root.append(out, zoomLevel, inn, sep, fit);
  return {root, zoomLevel};
}

function emptyState() {
  const root = document.createElement("div");
  root.className = "empty center";
  dataUi(root, "画布.empty");
  const title = document.createElement("p");
  title.className = "display";
  dataUi(title, "画布.empty.title");
  title.textContent = "The Night 还没开始";
  const text = document.createElement("p");
  text.className = "empty-text";
  dataUi(text, "画布.empty.text");
  text.append("The Night 是一次讨论开出的那张 ticket。给它打上 ");
  const code = document.createElement("span");
  code.className = "code";
  code.textContent = "mmw:map";
  text.append(code, " label，下一次读取时它和它下面的 spec、ticket 就会出现在这里。");
  root.append(title, text);
  return root;
}

function clampK(k) {
  return Math.min(1.6, Math.max(0.3, k));
}

function startingExpanded(data) {
  if (data.expanded != null) return [...data.expanded];
  if (data.task && typeof data.task === "object") return [...defaultExpanded(data.task)];
  return [];
}

export function render(host, data = {}, api = undefined) {
  const prior = mounted.get(host);
  if (prior) prior.cleanup();

  // Pan and zoom belong to the person looking at the canvas, not to the data behind it: a
  // redraw of the same task carries the viewport over, and only a different task is fitted
  // afresh.
  const taskKey = data.task && typeof data.task === "object" ? data.task.n : null;
  const kept = prior && prior.taskKey === taskKey ? prior.state : null;
  const reduced = prefersReduced();
  const state = {
    sel: data.sel ?? null,
    expanded: startingExpanded(data),
    view: kept ? kept.view : {x: 20, y: 12, k: 1},
    didInit: Boolean(kept && kept.didInit),
    drag: null,
    suppress: false,
  };
  // A card picked anywhere but here (the topbar's jump, a link in the detail column) can
  // land outside the viewport; one the user clicked on the canvas is already inside it.
  const toReveal = kept && state.sel != null && state.sel !== kept.sel;

  const root = document.createElement("main");
  root.dataset.screen = "canvas";
  root.className = "canvas canvas-surface board";
  dataUi(root, "画布.root");
  root.setAttribute("aria-label", "画布：拖动平移，按住 ⌘ 或双指捏合缩放");

  let worldEl, zoomEl, lastView;

  const size = () => ({width: root.offsetWidth, height: root.offsetHeight});

  const applyView = () => {
    const v = state.view;
    if (worldEl) worldEl.style.transform = `translate(${v.x}px, ${v.y}px) scale(${v.k})`;
    if (zoomEl) zoomEl.textContent = Math.round(v.k * 100) + "%";
  };

  const box = n => lastView?.layout?.nodes.find(node => node.id === n) || null;

  const fitted = (layout, r) => {
    const k = clampK(Math.min(1, (r.width - 40) / layout.W, (r.height - 70) / layout.H));
    return {k, x: Math.max(12, (r.width - layout.W * k) / 2), y: 12};
  };

  const initialView = () => {
    const layout = lastView?.layout;
    if (!layout) return;
    const r = size();
    if (!r.width || !r.height) return;
    state.view = fitted(layout, r);
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
    data.onViewport?.("canvas-zoomed", {...v});
  };

  const fitView = () => {
    const layout = lastView?.layout;
    if (!layout) return;
    const r = size();
    state.view = fitted(layout, r);
    applyView();
    data.onViewport?.("canvas-fitted", {...state.view});
  };

  // The smallest pan that puts the selected card inside the viewport; zoom is left alone.
  const revealSel = () => {
    const b = box(state.sel);
    if (!b) return;
    const r = size();
    if (!r.width || !r.height) return;
    const v = state.view, pad = 24, foot = 60; // foot: the zoom bar's own strip
    const left = b.x * v.k + v.x, right = (b.x + b.w) * v.k + v.x;
    const top = b.y * v.k + v.y, bottom = (b.y + b.h) * v.k + v.y;
    let dx = 0, dy = 0;
    if (right > r.width - pad) dx = r.width - pad - right;
    if (left + dx < pad) dx = pad - left;
    if (bottom > r.height - foot) dy = r.height - foot - bottom;
    if (top + dy < pad) dy = pad - top;
    if (!dx && !dy) return;
    v.x += dx;
    v.y += dy;
    applyView();
  };

  const center = () => {
    const r = size();
    return [r.width / 2, r.height / 2];
  };

  const paint = () => {
    lastView = present(data, state.sel, state.expanded, reduced);
    root.replaceChildren();
    worldEl = zoomEl = null;
    if (!lastView.hasTask) {
      root.append(emptyState());
      return;
    }
    const world = document.createElement("div");
    world.className = "world";
    Object.assign(world.style, lastView.worldSize);
    worldEl = world;
    const edges = document.createElement("div");
    edges.className = "edges-host";
    edges.innerHTML = lastView.svg || "";
    world.append(edges);
    for (const label of lastView.labels) {
      const node = document.createElement("div");
      node.className = label.cls;
      dataUi(node, "画布.lane-label");
      Object.assign(node.style, label.pos);
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
    if (!state.didInit) initialView();
    else applyView();
  };

  const choose = n => {
    if (state.suppress) return;
    state.sel = n;
    data.onSelectNode?.(n);
    paint();
  };

  const toggleOpen = n => {
    const expanded = new Set(state.expanded);
    if (expanded.has(n)) expanded.delete(n);
    else expanded.add(n);
    state.expanded = [...expanded];
    data.onToggle?.(n, state.expanded);
    paint();
  };

  const onPointerDown = event => {
    if (event.button !== 0 || event.target.closest?.(".toolbar, .legend, .iconbtn")) return;
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
    if ((event.key === "f" || event.key === "F") && !event.metaKey && !event.ctrlKey) fitView();
  };

  root.addEventListener("pointerdown", onPointerDown);
  root.addEventListener("wheel", onWheel, {passive: false});
  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", onUp);
  window.addEventListener("keydown", onKey);

  paint();
  host.replaceChildren(root);
  if (!state.didInit) queueMicrotask(initialView);
  else if (toReveal) queueMicrotask(revealSel);

  let observer;
  if (typeof ResizeObserver === "function") {
    observer = new ResizeObserver(() => {
      if (!state.didInit) initialView();
    });
    observer.observe(root);
  }

  mounted.set(host, {
    taskKey,
    state,
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
