/* 画布的几何：卡片摆在哪、线怎么弯、光束跑多快。
   照 mmw-v2/board/page/board-logic.mjs 的 Board.graph / Board.layout 和
   canvas.mjs 的 edgesSVG / beamSVG 移过来，只吃 data/canvas-scenes.js 里
   已经算好的 lamp / phase / released / running 这些字段。 */
(function () {
  const G = {
    mapX: 12, trunkX: 30, specX: 52, containerRight: 220,
    firstIssueX: 272, ticketWidth: 328, ticketHeight: 100, decisionWidth: 298,
    decisionHeight: 74, columnGap: 84, rowGap: 14, containerHeight: 72,
  };
  const LAMP_WORD = {orange: "needs you", green: "running", ink: "done", hollow: "queued"};
  const BEAM_SPEED = 170;
  const COMET = [
    [64, 3.4, "#22a06b", 0.10], [40, 3.2, "#22a06b", 0.22], [24, 3.0, "#2fbf7e", 0.45],
    [12, 2.8, "#46d894", 0.85], [5, 2.6, "#effff6", 1],
  ];
  const px = n => Math.round(n * 10) / 10 + "px";
  const f = n => +n.toFixed(2);

  function graph(items) {
    const ids = new Set(items.map(item => item.n));
    const preds = new Map(items.map(item => [item.n, (item.blocked || []).filter(n => ids.has(n))]));
    const succs = new Map(items.map(item => [item.n, []]));
    for (const [n, blockers] of preds) for (const b of blockers) succs.get(b).push(n);

    const indegree = new Map(items.map(item => [item.n, preds.get(item.n).length]));
    const layer = new Map();
    const queue = items.filter(item => indegree.get(item.n) === 0).map(item => item.n);
    for (const n of queue) layer.set(n, 0);
    while (queue.length) {
      const n = queue.shift();
      for (const next of succs.get(n)) {
        layer.set(next, Math.max(layer.get(next) ?? 0, layer.get(n) + 1));
        indegree.set(next, indegree.get(next) - 1);
        if (indegree.get(next) === 0) queue.push(next);
      }
    }
    const unresolved = new Set(items.filter(item => !layer.has(item.n)).map(item => item.n));
    const last = Math.max(-1, ...layer.values()) + 1;
    for (const n of unresolved) layer.set(n, last);

    const reachable = (from, to, omitDirect) => {
      const seen = new Set([from]);
      const pending = succs.get(from).filter(next => !(omitDirect && next === to));
      while (pending.length) {
        const next = pending.pop();
        if (next === to) return true;
        if (seen.has(next)) continue;
        seen.add(next);
        pending.push(...succs.get(next));
      }
      return false;
    };
    const cyclic = new Set([...unresolved].filter(n =>
      succs.get(n).some(next => unresolved.has(next) && reachable(next, n, false))));
    const edges = [];
    for (const [to, blockers] of preds) for (const from of blockers) {
      const cyc = cyclic.has(from) && cyclic.has(to) && reachable(to, from, false);
      if (!cyc && reachable(from, to, true)) continue;
      edges.push({from, to, cyc});
    }
    return {layer, preds, cyclic, edges};
  }

  const edgeState = (from, to, type) => {
    if (type === "decision") return from.closed ? "done" : "blocked";
    if (!from.released) return "blocked";
    return to.running ? "flow" : "done";
  };

  function layout(task, expanded) {
    const nodes = [];
    const edges = [];
    const labels = [];

    const band = (items, top, width, height) => {
      const g = graph(items);
      const byLayer = new Map();
      for (const item of items) {
        const l = g.layer.get(item.n);
        if (!byLayer.has(l)) byLayer.set(l, []);
        byLayer.get(l).push(item);
      }
      const positions = new Map();
      let bottom = top;
      for (const l of [...byLayer.keys()].sort((a, b) => a - b)) {
        const column = byLayer.get(l).map(item => {
          const blockers = g.preds.get(item.n).filter(n => positions.has(n));
          const wanted = blockers.length
            ? blockers.reduce((sum, n) => sum + positions.get(n).y, 0) / blockers.length
            : top;
          return {item, wanted};
        }).sort((a, b) => a.wanted - b.wanted || a.item.n - b.item.n);
        let y = top;
        for (const entry of column) {
          y = Math.max(entry.wanted, y);
          positions.set(entry.item.n, {x: G.firstIssueX + l * (width + G.columnGap), y});
          y += height + G.rowGap;
        }
        bottom = Math.max(bottom, y - G.rowGap);
      }
      return {graph: g, positions, height: bottom - top};
    };

    const expansionCurve = (fromY, node) => {
      const x1 = G.containerRight;
      const x2 = node.x;
      const y2 = node.y + node.h / 2;
      return `M ${x1} ${fromY} C ${x1 + 26} ${fromY}, ${x2 - 26} ${y2}, ${x2} ${y2}`;
    };
    const blockingCurve = (from, to, cyc) => {
      const x1 = from.x + from.w;
      const y1 = from.y + from.h / 2;
      if (cyc) {
        const y2 = to.y + to.h / 2;
        const bulge = x1 + 34;
        return `M ${x1} ${y1} C ${bulge} ${y1}, ${bulge} ${y2}, ${x1} ${y2}`;
      }
      const x2 = to.x;
      const y2 = to.y + to.h / 2;
      const dx = Math.max(28, (x2 - x1) * 0.55);
      return `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
    };

    const place = (items, type, width, height, top, container, middle) => {
      const result = band(items, top, width, height);
      const placed = new Map();
      for (const item of items) {
        const p = result.positions.get(item.n);
        const node = {id: item.n, type, ref: item, x: p.x, y: p.y, w: width, h: height,
          parent: container, cyclic: result.graph.cyclic.has(item.n)};
        nodes.push(node);
        placed.set(item.n, node);
      }
      for (const node of placed.values()) {
        if (result.graph.layer.get(node.id) === 0) {
          const flowing = type === "ticket" && node.ref.running;
          edges.push({kind: "expand", from: container, to: node.id, d: expansionCurve(middle, node),
            state: flowing ? "flow" : "done",
            ends: [[G.containerRight, middle], [node.x, node.y + node.h / 2]]});
        }
      }
      for (const edge of result.graph.edges) {
        const from = placed.get(edge.from);
        const to = placed.get(edge.to);
        edges.push({kind: "block", from: edge.from, to: edge.to, cyc: edge.cyc,
          state: edge.cyc ? "blocked" : edgeState(from.ref, to.ref, type),
          d: blockingCurve(from, to, edge.cyc),
          ends: [[from.x + from.w, from.y + from.h / 2],
            edge.cyc ? [from.x + from.w, to.y + to.h / 2] : [to.x, to.y + to.h / 2]]});
      }
      if (result.graph.cyclic.size) {
        const first = placed.get([...result.graph.cyclic][0]);
        labels.push({x: first.x, y: top - 18, warn: true,
          text: `blocking cycle · ${[...result.graph.cyclic].map(n => "#" + n).join(" ⇄ ")}`});
      }
      return result.height;
    };

    let y = 40;
    if (task.kind === "spec") {
      const spec = task.specs[0];
      nodes.push({id: spec.n, type: "spec", ref: spec, x: G.mapX, y,
        w: G.containerRight - G.mapX, h: G.containerHeight});
      if (expanded.has(spec.n)) {
        place(spec.tickets, "ticket", G.ticketWidth, G.ticketHeight, y, spec.n, y + G.containerHeight / 2);
      }
    } else {
      const mapNode = {id: task.n, type: "map", ref: task, x: G.mapX, y,
        w: G.containerRight - G.mapX, h: G.containerHeight};
      nodes.push(mapNode);
      let mapBand = G.containerHeight;
      if (task.decisions.length && expanded.has(task.n)) {
        labels.push({x: G.firstIssueX, y: y - 18, text: `decision tickets · ${task.decisions.length}`});
        mapBand = Math.max(G.containerHeight, place(task.decisions, "decision",
          G.decisionWidth, G.decisionHeight, y, task.n, y + G.containerHeight / 2));
      }
      y += mapBand + 48;
      labels.push({x: G.specX, y: y - 18, text: `spec · ${task.specs.length}`});
      let lastMiddle = y;
      for (const spec of task.specs) {
        nodes.push({id: spec.n, type: "spec", ref: spec, x: G.specX, y,
          w: G.containerRight - G.specX, h: G.containerHeight});
        lastMiddle = y + G.containerHeight / 2;
        edges.push({kind: "trunk", d: `M ${G.trunkX} ${lastMiddle - 10} Q ${G.trunkX} ${lastMiddle} ${G.trunkX + 10} ${lastMiddle} H ${G.specX}`});
        let height = G.containerHeight;
        if (expanded.has(spec.n)) {
          height = Math.max(G.containerHeight, place(spec.tickets, "ticket",
            G.ticketWidth, G.ticketHeight, y, spec.n, lastMiddle));
        }
        y += height + 26;
      }
      edges.unshift({kind: "trunk", d: `M ${G.trunkX} ${mapNode.y + mapNode.h} V ${lastMiddle - 10}`});
    }
    return {nodes, edges, labels,
      W: Math.max(...nodes.map(n => n.x + n.w)) + 60,
      H: Math.max(...nodes.map(n => n.y + n.h)) + 60};
  }

  function curveLength([x1, y1], [x2, y2]) {
    const dx = Math.max(28, (x2 - x1) * 0.55);
    const points = [[x1, y1], [x1 + dx, y1], [x2 - dx, y2], [x2, y2]];
    let len = 0;
    let prev = points[0];
    for (let i = 1; i <= 32; i++) {
      const t = i / 32;
      const u = 1 - t;
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
    const layers = COMET.map(([length, width, color, opacity]) =>
      `<path d="${edge.d}" stroke="${color}" stroke-opacity="${opacity}" stroke-width="${width}" stroke-dasharray="${f(length)} ${f(len + tail * 3)}" stroke-dashoffset="${f(length)}"><animate attributeName="stroke-dashoffset" from="${f(length)}" to="${f(length - len - tail)}" dur="${f(dur)}s" begin="${f(begin)}s" repeatCount="indefinite"/></path>`).join("");
    const arrive = begin + dur * len / (len + tail);
    return `<g class="e-beam">${layers}</g><circle class="e-pulse" cx="${b[0]}" cy="${b[1]}" r="2.6" opacity="0"><animate attributeName="r" values="2.6;11" dur="${f(dur)}s" begin="${f(arrive)}s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.7;0" dur="${f(dur)}s" begin="${f(arrive)}s" repeatCount="indefinite"/></circle>`;
  }

  function edgesSVG(l, sel, selIsIssue, reduced) {
    const order = {done: 0, blocked: 1, flow: 2};
    const blocks = l.edges.filter(e => e.kind === "block").sort((a, b) => order[a.state] - order[b.state]);
    const lines = l.edges.filter(e => e.kind !== "block").map(e =>
      `<path class="${e.kind === "trunk" ? "e-trunk" : "e-expand"}" d="${e.d}"/>`
      + (e.kind === "expand" && e.state === "flow" ? beamSVG(e, reduced) : "")).join("");
    const curves = blocks.map(e => {
      const hot = selIsIssue && (e.from === sel || e.to === sel);
      const cls = `e-block ${e.state}${hot ? " hot" : ""}${e.cyc ? " cyc" : ""}`;
      const ports = e.ends.map(([x, y]) => `<circle class="e-port ${e.state}" cx="${x}" cy="${y}" r="2.6"/>`).join("");
      return `<path class="${cls}" d="${e.d}"/>${e.state === "flow" ? beamSVG(e, reduced) : ""}${ports}`;
    }).join("");
    return `<svg class="edges" width="${l.W}" height="${l.H}" viewBox="0 0 ${l.W} ${l.H}" aria-hidden="true">${lines}${curves}</svg>`;
  }

  const aggregate = tickets => {
    const lamps = tickets.map(t => t.lamp);
    if (lamps.includes("orange")) return "orange";
    if (lamps.includes("green")) return "green";
    if (lamps.length && lamps.every(l => l === "ink")) return "ink";
    return "hollow";
  };

  // The canvas as the page draws it: three lists of cards, the lane labels, the world
  // size and one SVG string for every line between them.
  function view(task, expandedList, sel, reduced) {
    if (!task) return {hasTask: false, containers: [], decisions: [], tickets: [], labels: [], svg: "", W: 0, H: 0};
    const expanded = new Set(expandedList);
    const l = layout(task, expanded);
    const selNode = l.nodes.find(node => node.id === sel);
    const selIsIssue = Boolean(selNode && (selNode.type === "ticket" || selNode.type === "decision"));
    const pos = node => ({left: px(node.x), top: px(node.y), width: px(node.w), height: px(node.h)});
    const containers = [];
    const decisions = [];
    const tickets = [];
    const allTickets = task.specs.flatMap(spec => spec.tickets);
    for (const node of l.nodes) {
      const on = node.id === sel;
      if (node.type === "ticket") {
        const t = node.ref;
        containers.length;
        tickets.push({n: t.n, ...pos(node), num: "#" + t.n, title: t.title, phase: t.phase,
          pillCls: "pill " + t.phase,
          cls: "card" + (on ? " on" : "") + (t.closeout ? " closeout" : "") + (node.cyclic ? " cycle" : ""),
          lampCls: "lamp " + t.lamp, lampWord: LAMP_WORD[t.lamp],
          run: t.run, runCls: t.runFlag ? "card-run flag" : "card-run"});
      } else if (node.type === "decision") {
        const d = node.ref;
        decisions.push({n: d.n, ...pos(node), num: "#" + d.n, title: d.title, kind: d.kind,
          cls: "card" + (on ? " on" : "") + (node.cyclic ? " cycle" : ""),
          lampCls: "lamp small " + (d.closed ? "ink" : "hollow")});
      } else {
        const c = node.ref;
        const isMap = node.type === "map";
        const list = isMap ? allTickets : c.tickets;
        const done = list.filter(t => t.done).length;
        const open = expanded.has(c.n);
        containers.push({n: c.n, ...pos(node), title: c.title,
          num: "#" + c.n + (isMap ? " · " + c.kind : ""),
          cls: "card" + (on ? " on" : ""),
          titleCls: isMap ? "card-title map one-line" : "card-title one-line",
          lampCls: "lamp " + aggregate(list), lampWord: LAMP_WORD[aggregate(list)],
          count: done + "/" + list.length,
          canExpand: isMap ? c.decisions.length > 0 : c.tickets.length > 0,
          chev: open ? "▾" : "▸", toggleLabel: (open ? "collapse #" : "expand #") + c.n,
          barWidth: (list.length ? 100 * done / list.length : 0) + "%"});
      }
    }
    return {
      hasTask: true, containers, decisions, tickets,
      labels: l.labels.map(label => ({cls: label.warn ? "eyebrow warn" : "eyebrow",
        left: px(label.x), top: px(label.y), text: label.text})),
      W: l.W, H: l.H, nodes: l.nodes.map(n => ({id: n.id, x: n.x, y: n.y, w: n.w, h: n.h})),
      svg: edgesSVG(l, sel, selIsIssue, reduced),
    };
  }

  window.BoardLayout = {layout, view, aggregate, LAMP_WORD};
})();
