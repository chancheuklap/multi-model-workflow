import {hhmm, minutes} from "./shared.mjs";

// The two axes a ticket is read on, both defined in `docs/contexts/task-board/CONTEXT.md`:
// the phase is where the ticket stands inside itself, the lamp is what it wants from the
// outside. A ticket can be `working` and still want nothing, or `landed` and still need a
// person, so neither word can be read off the other.
export const PHASES = ["queued", "working", "waiting", "review", "verify", "landed"];
export const LAMP_WORD = {orange: "needs you", green: "running", ink: "done", hollow: "queued"};
const NEEDS_YOU_KIND = {
  decision: "只有你能拍板；worker 先按默认值继续",
  fault: "MMW 自己坏了，开它的 agent 已停下",
  contract: "spec 本身不成立，要回到写 spec 的人",
};
const NEEDS_YOU = new Set(Object.keys(NEEDS_YOU_KIND));
const QUEUE_REASON = {"product-full": "every instance of the product is held",
  "machine-full": "every slot on this machine is held"};
const ENDED_BY = {
  "reviewer.reported": "review posted", "verifier.passed": "verifier passed",
  "verifier.failed": "verifier failed", "ticket.landed": "landed",
  "ticket.returned": "handed back", "ticket.bounced": "bounced",
  "ticket.released": "claim released", "spec.suspended": "night suspended",
  "worker.retracted": "retracted", "worker.replaced": "replaced",
  "ticket.refused": "preflight refused", "worker.lost": "session lost",
  "reviewer.lost": "session lost", "verifier.lost": "session lost",
};
const duration = value => value < 60 ? `${value}m` : `${Math.floor(value / 60)}h${String(value % 60).padStart(2, "0")}m`;
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

  // Whether this ticket is finished, which is the same question `blocker_hold` already
  // answers for the ticket behind it: nothing more is coming from it. The ledger landed
  // it, or it closed with nothing that will ever land — taken through by hand outside the
  // pipeline, which writes no `ticket.landed` and can leave the ledger empty. A ticket
  // that passed and has not landed yet is not finished, and neither is one whose events
  // could not be read: those still say why they hold.
  done(ticket) {
    return Boolean(ticket.fold.landed) || this.released(ticket);
  },

  phase(ticket) {
    const fold = ticket.fold;
    if (this.done(ticket)) return "landed";
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
        ? abandoned.map(item => `handed back: ${item.ac} 放弃（${item.kind}）。${item.reason}`).join("；")
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

  lamp(ticket) {
    if (this.why(ticket).length) return "orange";
    if (this.running(ticket)) return "green";
    if (this.done(ticket)) return "ink";
    return "hollow";
  },

  eventLamp(event) {
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
      // Finished with no session at all: it was taken through by hand, so there is no
      // runner to name and "not dispatched" would read as work still to come.
      if (this.done(ticket)) return {text: "closed, never dispatched"};
      return {text: ticket.fold.claim_hold || ticket.fold.held
        ? "claimed · no session yet" : "not dispatched"};
    }
    const since = this.waitingSince(ticket);
    if (since) return {text: `waiting for a slot · since ${hhmm(since)}`};
    const session = live.length ? live[live.length - 1] : ticket.fold.worker;
    if (live.length && this.stoppedByFault(ticket)) return {text: `stopped · ${session.host} · ${session.model}`, flag: true};
    return {text: `${session.host} · ${session.model} · ${session.effort}`};
  },

  facts(ticket) {
    const fold = ticket.fold;
    const workerSession = fold.worker;
    if (!workerSession) return [];
    const rows = [
      ["host", `${workerSession.host} · ${workerSession.model} · ${workerSession.effort}`],
      ["runner", `${workerSession.runner} · ${workerSession.session}`],
      ["machine", workerSession.machine],
      ["ticket branch", `${workerSession.branch} @ ${short(workerSession.base)}`],
      ...(workerSession.into ? [["base branch", workerSession.into]] : []),
      ["worktree", `…/.worktrees/${String(workerSession.worktree).split("/.worktrees/")[1]}`],
      ["worker grade", workerSession.grade],
    ];
    const since = this.waitingSince(ticket);
    if (since) {
      const queued = fold.waiting.payload;
      rows.push(["slot", `queueing since ${hhmm(since)}: ${QUEUE_REASON[queued.reason]} (max ${queued.limit}). Until the next ticket.checked, the relay's wake and the criteria run included`]);
    } else if (fold.slot != null) rows.push(["slot", `${fold.slot}, held until this ticket lands, is handed back or bounces`]);
    return rows;
  },

  sessionState(session, ticket) {
    return !session.live ? (ENDED_BY[session.ended_by] || "ended")
      : this.stoppedByFault(ticket) ? "stopped on a fault" : "live";
  },

  elapsed(ticket) {
    const first = ticket.fold.sessions[0]?.started_at;
    if (!first) return "";
    const landed = ticket.events.find(event => event.event === "ticket.landed");
    if (ticket.fold.landed && landed) return duration(minutes(first, landed.at));
    if (this.handedBack(ticket)) return duration(minutes(first, ticket.fold.outcome.at));
    const bounce = this.bounce(ticket);
    if (bounce) return duration(minutes(first, bounce.at));
    return duration(minutes(first));
  },

  aggregate(tickets) {
    const lamps = tickets.map(ticket => this.lamp(ticket));
    if (lamps.includes("orange")) return "orange";
    if (lamps.includes("green")) return "green";
    if (lamps.length && lamps.every(lamp => lamp === "ink")) return "ink";
    return "hollow";
  },

  decisionLamp(decision) {
    return String(decision.state).toLowerCase() === "closed" ? "ink" : "hollow";
  },

  allTickets(task) { return task.specs.flatMap(spec => spec.tickets); },

  progress(task) {
    const tickets = this.allTickets(task);
    return {done: tickets.filter(ticket => this.done(ticket)).length, total: tickets.length};
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
    // Card sizes are the width two title lines need plus the card's own padding, and the
    // height that title and the run line under it take: measured on a live board, not chosen.
    // An ellipsis is the fallback for a title past that width, not the everyday case.
    const geometry = {mapX: 12, trunkX: 30, specX: 52, containerRight: 220,
      firstIssueX: 272, ticketWidth: 328, ticketHeight: 100, decisionWidth: 298,
      decisionHeight: 74, columnGap: 84, rowGap: 14, containerHeight: 72};
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
          // The container feeds a first-layer ticket the way a landed blocker feeds the
          // ticket behind it: while that ticket is being worked, the line carries the flow.
          const flowing = type === "ticket" && this.running(node.ref);
          edges.push({kind: "expand", from: container, to: node.id, d: expansionCurve(middle, node),
            state: flowing ? "flow" : "done",
            ends: [[geometry.containerRight, middle], [node.x, node.y + node.h / 2]]});
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
          text: `blocking cycle · ${[...result.graph.cyclic].map(number => `#${number}`).join(" ⇄ ")}`, warn: true});
      }
      return result.height;
    };

    let y = 40;
    if (task.kind === "spec") {
      // A spec with no map above it is the task itself: one container at the top,
      // its tickets hanging straight off it, no trunk and no spec row.
      const spec = task.specs[0];
      const specNode = {id: spec.n, type: "spec", ref: spec, x: geometry.mapX, y,
        w: geometry.containerRight - geometry.mapX, h: geometry.containerHeight};
      nodes.push(specNode);
      if (expanded.has(spec.n)) {
        place(spec.tickets, "ticket", geometry.ticketWidth, geometry.ticketHeight,
          y, spec.n, y + geometry.containerHeight / 2);
      }
      return {nodes, edges, labels,
        W: Math.max(...nodes.map(node => node.x + node.w)) + 60,
        H: Math.max(...nodes.map(node => node.y + node.h)) + 60};
    }
    const mapNode = {id: task.n, type: "map", ref: task, x: geometry.mapX, y,
      w: geometry.containerRight - geometry.mapX, h: geometry.containerHeight};
    nodes.push(mapNode);
    let mapBand = geometry.containerHeight;
    if (task.decisions.length && expanded.has(task.n)) {
      labels.push({x: geometry.firstIssueX, y: y - 18,
        text: `decision tickets · ${task.decisions.length}`});
      mapBand = Math.max(geometry.containerHeight,
        place(task.decisions, "decision", geometry.decisionWidth, geometry.decisionHeight,
          y, task.n, y + geometry.containerHeight / 2));
    }
    y += mapBand + 48;
    labels.push({x: geometry.specX, y: y - 18, text: `spec · ${task.specs.length}`});
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
    const lamp = Board.aggregate(spec.tickets);
    if (lamp === "orange" || lamp === "green") expanded.add(spec.n);
  }
  return expanded;
}
