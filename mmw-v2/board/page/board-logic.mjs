import {hhmm, minutes} from "./shared.mjs";

export const STEPS = ["queued", "working", "waiting", "review", "verify", "landed"];
export const LIGHT_WORD = {orange: "需要你", green: "在跑", ink: "好了", hollow: "待派"};
const NEEDS_YOU_KIND = {
  decision: "只有你能拍板；worker 先按默认值继续",
  fault: "MMW 自己坏了，开它的 agent 已停下",
  contract: "spec 本身不成立，要回到写 spec 的人",
};
const NEEDS_YOU = new Set(Object.keys(NEEDS_YOU_KIND));
const QUEUE_REASON = {"product-full": "本产品的实例都占着", "machine-full": "这台机器的槽位都占着"};
const ENDED_BY = {
  "reviewer.reported": "已交评审", "verifier.passed": "复验通过", "verifier.failed": "复验没过",
  "ticket.landed": "已结束", "ticket.returned": "已交回", "ticket.bounced": "合不进去",
  "ticket.released": "认领已退", "spec.suspended": "这一夜暂停了", "worker.retracted": "已撤回",
  "worker.replaced": "已换人", "ticket.refused": "拒绝认领", "worker.lost": "会话没了",
  "reviewer.lost": "会话没了", "verifier.lost": "会话没了",
};
const duration = value => value < 60 ? `${value} 分钟` : `${Math.floor(value / 60)}h${String(value % 60).padStart(2, "0")}m`;
const short = value => String(value || "").slice(0, 7);
const workerStartedAfter = (fold, at) => fold.sessions.some(session =>
  session.kind === "worker" && session.started_at > at);

function childIsOpen(ticket, child) {
  const issue = (ticket.children || []).find(item => item.number === child.child);
  return issue ? String(issue.state).toUpperCase() !== "CLOSED" : !child.resolution;
}

export const Board = {
  stoppedByFault(ticket) {
    let started = -1;
    ticket.events.forEach((event, index) => {
      if (event.event === "worker.started" || event.event === "worker.resumed") started = index;
    });
    return ticket.events.some((event, index) => {
      if (index <= started || event.event !== "child.opened" || event.payload?.kind !== "fault") return false;
      const child = ticket.fold.children[String(event.payload.child)] || {child: event.payload.child};
      return childIsOpen(ticket, child);
    });
  },

  handedBack(ticket) {
    const fold = ticket.fold;
    return Boolean(fold.returned && fold.outcome && !workerStartedAfter(fold, fold.outcome.at));
  },

  bounce(ticket) {
    if (!ticket.fold.bounced) return null;
    const event = [...ticket.events].reverse().find(item => item.event === "ticket.bounced");
    return event && !workerStartedAfter(ticket.fold, event.at) ? event : null;
  },

  running(ticket) {
    const held = ticket.fold.held ?? (ticket.fold.claim_hold
      || ticket.fold.sessions.some(session => session.live));
    return held && !this.stoppedByFault(ticket);
  },

  stoppedAt(ticket) {
    const kinds = ticket.fold.sessions.map(session => session.kind);
    if (kinds.includes("verifier") || this.bounce(ticket)) return "verify";
    if (kinds.includes("reviewer") && !ticket.fold.review) return "review";
    return "working";
  },

  step(ticket) {
    const fold = ticket.fold;
    if (fold.landed) return "landed";
    const live = fold.sessions.filter(session => session.live);
    if (this.handedBack(ticket) || this.bounce(ticket) || (live.length && this.stoppedByFault(ticket))) {
      return this.stoppedAt(ticket);
    }
    if (!live.length) return "queued";
    if (live.some(session => session.kind === "verifier")) return "verify";
    if (fold.verdict?.event === "verifier.passed") return "verify";
    if (live.some(session => session.kind === "reviewer")) return "review";
    if (fold.waiting) return "waiting";
    return "working";
  },

  why(ticket) {
    const reasons = [];
    for (const child of Object.values(ticket.fold.children)) {
      if (NEEDS_YOU.has(child.kind) && childIsOpen(ticket, child)) {
        reasons.push({kind: child.kind, child: child.child, title: child.title, text: NEEDS_YOU_KIND[child.kind]});
      }
    }
    if (this.handedBack(ticket)) {
      const abandoned = ticket.fold.outcome.payload?.abandoned || [];
      reasons.push({kind: "returned", text: abandoned.length
        ? abandoned.map(item => `交回：${item.ac} 放弃（${item.kind}）。${item.reason}`).join("；")
        : ticket.fold.outcome.line});
    }
    const bounce = this.bounce(ticket);
    if (bounce) {
      const payload = bounce.payload || {};
      const failures = (payload.commands || []).map(item => {
        const output = item.output || item.last || item.stderr;
        return output ? `${item.command}：${Array.isArray(output) ? output.join(" / ") : output}` : item.command;
      });
      reasons.push({kind: "bounced", text: payload.reason === "conflict"
        ? `合不进 ${payload.into}（${short(payload.commit)}）：冲突在 ${(payload.files || []).join("、")}。等早上 triage`
        : `合不进 ${payload.into}（${short(payload.commit)}）：合并后检查没过 ${failures.join("、")}。等早上 triage`});
    }
    return reasons;
  },

  light(ticket) {
    if (this.why(ticket).length) return "orange";
    if (this.running(ticket)) return "green";
    if (ticket.fold.landed) return "ink";
    return "hollow";
  },

  eventLight(event) {
    if (event.event === "child.opened" && NEEDS_YOU.has(event.payload?.kind)) return "orange";
    if (event.event === "ticket.returned" || event.event === "ticket.bounced") return "orange";
    if (/\.started$|^worker\.resumed$|^ticket\.claimed$/.test(event.event)) return "green";
    if (/^ticket\.(landed|passed)$|^verifier\.passed$|^reviewer\.reported$|^child\.closed$/.test(event.event)) return "ink";
    return "hollow";
  },

  evFields(event) {
    const payload = event.payload || {};
    if (/\.started$/.test(event.event)) return `${payload.runner} · ${payload.session} · ${payload.machine}`;
    if (/\.lost$|^worker\.(retracted|replaced|resumed)$/.test(event.event)) return `${payload.runner} · ${payload.session}`;
    if (event.event === "ticket.claimed") return `login=${payload.login}`;
    if (event.event === "ticket.checked") return `run=${payload.run} result=${payload.result}${payload.slot != null ? ` slot=${payload.slot}` : ""}`;
    if (event.event === "worker.queued") return `reason=${payload.reason} run=${payload.run}`;
    if (event.event === "child.opened") return `kind=${payload.kind} #${payload.child}`;
    if (event.event === "child.closed") return `#${payload.child} → ${payload.resolution}${payload.became ? ` #${payload.became}` : ""}`;
    if (event.event === "ticket.returned") return (payload.abandoned || []).map(item => `${item.ac}=${item.kind}`).join(" ");
    if (event.event === "ticket.bounced") return `reason=${payload.reason} onto=${short(payload.commit)}`;
    if (event.event === "reviewer.reported") return `${short(payload.base)}..${short(payload.head)}`;
    if (payload.commit) return `commit=${short(payload.commit)}`;
    return "";
  },

  waitingSince(ticket) {
    return ticket.fold.waiting && ticket.fold.sessions.some(session => session.live) ? ticket.fold.waiting.at : null;
  },

  runLine(ticket) {
    const live = ticket.fold.sessions.filter(session => session.live);
    if (!ticket.fold.sessions.length) {
      return {text: ticket.fold.claim_hold || ticket.fold.held ? "已认领 · 待派发" : "尚未派发"};
    }
    const since = this.waitingSince(ticket);
    if (since) return {text: `等槽位 · ${hhmm(since)} 起`};
    const session = live.length ? live[live.length - 1] : ticket.fold.worker;
    if (live.length && this.stoppedByFault(ticket)) return {text: `已停下 · ${session.host} · ${session.model}`, flag: true};
    return {text: `${session.host} · ${session.model} · ${session.effort}`};
  },

  facts(ticket) {
    const fold = ticket.fold;
    const workerSession = fold.worker;
    if (!workerSession) return [];
    const rows = [
      ["host", `${workerSession.host} · ${workerSession.model} · ${workerSession.effort}`],
      ["runner", `${workerSession.runner} · ${workerSession.session}`], ["机器", workerSession.machine],
      ["分支", `${workerSession.branch} @ ${short(workerSession.base)}`],
      ...(workerSession.into ? [["合进", workerSession.into]] : []),
      ["工作树", `…/.worktrees/${String(workerSession.worktree).split("/.worktrees/")[1]}`], ["档位", workerSession.grade],
    ];
    const since = this.waitingSince(ticket);
    if (since) {
      const queued = fold.waiting.payload;
      rows.push(["槽位", `${hhmm(since)} 起排队：${QUEUE_REASON[queued.reason]}（上限 ${queued.limit}）。到下一条 ticket.checked 为止，其中含等中继叫醒与跑判据的时间`]);
    } else if (fold.slot != null) rows.push(["槽位", `${fold.slot} 号，持有到这张票落地、交回或合不进去`]);
    return rows;
  },

  sessionState(session, ticket) {
    return !session.live ? (ENDED_BY[session.ended_by] || "已结束") : this.stoppedByFault(ticket) ? "开了 fault 后停下" : "在跑";
  },

  elapsed(ticket) {
    const first = ticket.fold.sessions[0]?.started_at;
    if (!first) return "";
    const landed = ticket.events.find(event => event.event === "ticket.landed");
    if (ticket.fold.landed && landed) return `用时 ${duration(minutes(first, landed.at))}`;
    if (this.handedBack(ticket)) return `跑了 ${duration(minutes(first, ticket.fold.outcome.at))} 后交回`;
    const bounce = this.bounce(ticket);
    if (bounce) return `跑了 ${duration(minutes(first, bounce.at))} 后合不进去`;
    return `已跑 ${duration(minutes(first))}`;
  },

  aggregate(tickets) {
    const lights = tickets.map(ticket => this.light(ticket));
    if (lights.includes("orange")) return "orange";
    if (lights.includes("green")) return "green";
    if (lights.length && lights.every(light => light === "ink")) return "ink";
    return "hollow";
  },

  decisionLight(decision) {
    return String(decision.state).toLowerCase() === "closed" ? "ink" : "hollow";
  },

  allTickets(task) { return task.specs.flatMap(spec => spec.tickets); },

  progress(task) {
    const tickets = this.allTickets(task);
    return {done: tickets.filter(ticket => ticket.fold.landed).length, total: tickets.length};
  },

  released(blocker) {
    return blocker.blocker_hold === "";
  },

  edgeState(blocker, blocked, type = "ticket") {
    if (type === "decision") return String(blocker.state).toLowerCase() === "closed" ? "done" : "blocked";
    if (!this.released(blocker)) return "blocked";
    return this.running(blocked) ? "flow" : "done";
  },

  graph(items) {
    const ids = new Set(items.map(item => item.n));
    const predecessors = new Map(items.map(item => [item.n, item.blocked.filter(number => ids.has(number))]));
    const successors = new Map(items.map(item => [item.n, []]));
    for (const [number, blockers] of predecessors) for (const blocker of blockers) successors.get(blocker).push(number);

    const indegree = new Map(items.map(item => [item.n, predecessors.get(item.n).length]));
    const layers = new Map();
    const queue = items.filter(item => indegree.get(item.n) === 0).map(item => item.n);
    for (const number of queue) layers.set(number, 0);
    while (queue.length) {
      const number = queue.shift();
      for (const next of successors.get(number)) {
        layers.set(next, Math.max(layers.get(next) ?? 0, layers.get(number) + 1));
        indegree.set(next, indegree.get(next) - 1);
        if (indegree.get(next) === 0) queue.push(next);
      }
    }

    const unresolved = new Set(items.filter(item => !layers.has(item.n)).map(item => item.n));
    const last = Math.max(-1, ...layers.values()) + 1;
    for (const number of unresolved) layers.set(number, last);

    const reachable = (from, to, omitDirect) => {
      const seen = new Set([from]);
      const pending = successors.get(from).filter(next => !(omitDirect && next === to));
      while (pending.length) {
        const next = pending.pop();
        if (next === to) return true;
        if (seen.has(next)) continue;
        seen.add(next);
        pending.push(...successors.get(next));
      }
      return false;
    };
    const cyclic = new Set([...unresolved].filter(number =>
      successors.get(number).some(next => unresolved.has(next) && reachable(next, number, false))));
    const edges = [];
    for (const [to, blockers] of predecessors) for (const from of blockers) {
      const cycle = cyclic.has(from) && cyclic.has(to) && reachable(to, from, false);
      if (!cycle && reachable(from, to, true)) continue;
      edges.push({from, to, cyc: cycle});
    }
    return {layer: layers, preds: predecessors, cyclic, edges};
  },

  layout(task, expanded) {
    const geometry = {mapX: 12, trunkX: 30, specX: 52, containerRight: 220,
      firstIssueX: 272, ticketWidth: 184, ticketHeight: 94, decisionWidth: 164,
      decisionHeight: 62, columnGap: 84, rowGap: 14, containerHeight: 72};
    const nodes = [];
    const edges = [];
    const labels = [];

    const band = (items, top, width, height) => {
      const graph = this.graph(items);
      const byLayer = new Map();
      for (const item of items) {
        const layer = graph.layer.get(item.n);
        if (!byLayer.has(layer)) byLayer.set(layer, []);
        byLayer.get(layer).push(item);
      }
      const positions = new Map();
      let bottom = top;
      for (const layer of [...byLayer.keys()].sort((a, b) => a - b)) {
        const column = byLayer.get(layer).map(item => {
          const blockers = graph.preds.get(item.n).filter(number => positions.has(number));
          const wanted = blockers.length
            ? blockers.reduce((sum, number) => sum + positions.get(number).y, 0) / blockers.length
            : top;
          return {item, wanted};
        }).sort((a, b) => a.wanted - b.wanted || a.item.n - b.item.n);
        let y = top;
        for (const entry of column) {
          y = Math.max(entry.wanted, y);
          positions.set(entry.item.n, {x: geometry.firstIssueX + layer * (width + geometry.columnGap), y});
          y += height + geometry.rowGap;
        }
        bottom = Math.max(bottom, y - geometry.rowGap);
      }
      return {graph, positions, height: bottom - top};
    };

    const expansionCurve = (fromY, node) => {
      const x1 = geometry.containerRight;
      const x2 = node.x;
      const y2 = node.y + node.h / 2;
      return `M ${x1} ${fromY} C ${x1 + 26} ${fromY}, ${x2 - 26} ${y2}, ${x2} ${y2}`;
    };
    const blockingCurve = (from, to, cycle) => {
      const x1 = from.x + from.w;
      const y1 = from.y + from.h / 2;
      if (cycle) {
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
        const position = result.positions.get(item.n);
        const node = {id: item.n, type, ref: item, x: position.x, y: position.y,
          w: width, h: height, parent: container, cyclic: result.graph.cyclic.has(item.n)};
        nodes.push(node);
        placed.set(item.n, node);
      }
      for (const node of placed.values()) {
        if (result.graph.layer.get(node.id) === 0) {
          edges.push({kind: "expand", from: container, to: node.id, d: expansionCurve(middle, node)});
        }
      }
      for (const edge of result.graph.edges) {
        const from = placed.get(edge.from);
        const to = placed.get(edge.to);
        edges.push({kind: "block", from: edge.from, to: edge.to, cyc: edge.cyc,
          state: edge.cyc ? "blocked" : this.edgeState(from.ref, to.ref, type),
          d: blockingCurve(from, to, edge.cyc),
          ends: [[from.x + from.w, from.y + from.h / 2],
            edge.cyc ? [from.x + from.w, to.y + to.h / 2] : [to.x, to.y + to.h / 2]]});
      }
      if (result.graph.cyclic.size) {
        const first = placed.get([...result.graph.cyclic][0]);
        labels.push({x: first.x, y: top - 18,
          text: `阻塞成环 · ${[...result.graph.cyclic].map(number => `#${number}`).join(" ⇄ ")} · 排不出先后`, warn: true});
      }
      return result.height;
    };

    let y = 40;
    const mapNode = {id: task.n, type: "map", ref: task, x: geometry.mapX, y,
      w: geometry.containerRight - geometry.mapX, h: geometry.containerHeight};
    nodes.push(mapNode);
    let mapBand = geometry.containerHeight;
    if (task.decisions.length && expanded.has(task.n)) {
      labels.push({x: geometry.firstIssueX, y: y - 18,
        text: `这次讨论自己的票 · ${task.decisions.length} 张`});
      mapBand = Math.max(geometry.containerHeight,
        place(task.decisions, "decision", geometry.decisionWidth, geometry.decisionHeight,
          y, task.n, y + geometry.containerHeight / 2));
    }
    y += mapBand + 48;
    labels.push({x: geometry.specX, y: y - 18, text: `讨论产出的 spec · ${task.specs.length} 个`});
    let lastMiddle = y;
    for (const spec of task.specs) {
      const specNode = {id: spec.n, type: "spec", ref: spec, x: geometry.specX, y,
        w: geometry.containerRight - geometry.specX, h: geometry.containerHeight};
      nodes.push(specNode);
      lastMiddle = y + geometry.containerHeight / 2;
      edges.push({kind: "trunk", d: `M ${geometry.trunkX} ${lastMiddle - 10} Q ${geometry.trunkX} ${lastMiddle} ${geometry.trunkX + 10} ${lastMiddle} H ${geometry.specX}`});
      let height = geometry.containerHeight;
      if (expanded.has(spec.n)) {
        height = Math.max(geometry.containerHeight,
          place(spec.tickets, "ticket", geometry.ticketWidth, geometry.ticketHeight,
            y, spec.n, lastMiddle));
      }
      y += height + 26;
    }
    edges.unshift({kind: "trunk", d: `M ${geometry.trunkX} ${mapNode.y + mapNode.h} V ${lastMiddle - 10}`});
    return {nodes, edges, labels,
      W: Math.max(...nodes.map(node => node.x + node.w)) + 60,
      H: Math.max(...nodes.map(node => node.y + node.h)) + 60};
  },
};

export function defaultExpanded(task) {
  const expanded = new Set([task.n]);
  for (const spec of task.specs) {
    const light = Board.aggregate(spec.tickets);
    if (light === "orange" || light === "green") expanded.add(spec.n);
  }
  return expanded;
}
