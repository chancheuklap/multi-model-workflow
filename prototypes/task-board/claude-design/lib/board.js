(function () {
window.MMW = window.MMW || {};
const MMW = window.MMW;
// ── shared.mjs ──
(function () {

function el(tag, attrs = {}, ...kids) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "disabled") node.disabled = true;
    else if (key === "selected") node.selected = true;
    else if (key === "html") node.innerHTML = value;
    else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid == null || kid === false) continue;
    node.append(typeof kid === "object" ? kid : String(kid));
  }
  return node;
}

const hhmm = value => new Date(value).toLocaleTimeString("en-GB", {
  hour: "2-digit", minute: "2-digit", hour12: false,
});

const minutes = (from, to = (window.MMW_NOW ? new Date(window.MMW_NOW) : new Date())) =>
  Math.max(0, Math.round((new Date(to) - new Date(from)) / 60000));

async function hand(method) {
  try {
    return await method();
  } catch {
    return null;
  }
}

MMW['shared'] = {el, hhmm, minutes, hand};
Object.assign(MMW, MMW['shared']);
})();
// ── board-logic.mjs ──
(function () {
const {hhmm, minutes} = MMW;

// The two axes a ticket is read on, both defined in `docs/contexts/task-board/CONTEXT.md`:
// the phase is where the ticket stands inside itself, the lamp is what it wants from the
// outside. A ticket can be `working` and still want nothing, or `landed` and still need a
// person, so neither word can be read off the other.
const PHASES = ["queued", "working", "waiting", "review", "verify", "landed"];
const LAMP_WORD = {orange: "needs you", green: "running", ink: "done", hollow: "queued"};
const NEEDS_YOU_KIND = {
  decision: "只有你能拍板；worker 先按默认值继续",
  fault: "MMW 自己坏了，开它的 agent 已停下",
  contract: "spec 本身不成立，要回到写 spec 的人",
};
const NEEDS_YOU = new Set(Object.keys(NEEDS_YOU_KIND));
const duration = value => value < 60 ? `${value}m` : `${Math.floor(value / 60)}h${String(value % 60).padStart(2, "0")}m`;
const short = value => String(value || "").slice(0, 7);
const workerStartedAfter = (fold, at) => fold.sessions.some(session =>
  session.kind === "worker" && session.started_at > at);

function childIsOpen(ticket, child) {
  const issue = (ticket.children || []).find(item => item.number === child.child);
  return issue ? String(issue.state).toUpperCase() !== "CLOSED" : !child.resolution;
}

const Board = {
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
    if (this.bounce(ticket)) return "verify";
    return this.workflowPhase(ticket);
  },

  workflowPhase(ticket) {
    const reviewerLive = ticket.fold.sessions.some(session => session.kind === "reviewer" && session.live);
    let phase = reviewerLive ? "review" : "working";
    for (const event of ticket.events) {
      if (event.event === "ticket.checked" && event.payload?.run === "reverify"
          && event.payload?.actor === "worker") {
        phase = "verify";
      } else if (event.event === "reviewer.started") {
        phase = "review";
      } else if (event.event === "reviewer.reported"
          || (!reviewerLive && (["worker.started", "worker.resumed", "ticket.claimed",
            "worker.decided"].includes(event.event)
            || (event.event === "ticket.checked" && event.payload?.run === "self")))) {
        phase = "working";
      }
    }
    return phase;
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
    if (fold.waiting) return "waiting";
    return this.workflowPhase(ticket);
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

function defaultExpanded(task) {
  const expanded = new Set([task.n]);
  for (const spec of task.specs) {
    const lamp = Board.aggregate(spec.tickets);
    if (lamp === "orange" || lamp === "green") expanded.add(spec.n);
  }
  return expanded;
}

// Every pipeline event as a person reads it: an English name, the phase pill the ticket
// card carried while that event was the newest one, and one sentence from the payload.
// A claim never opens a block of its own: start and claim are one act.
const PHASE_OF_EVENT = {
  "worker.started": "working", "worker.resumed": "working", "ticket.claimed": "working",
  "worker.touched": "working", "worker.decided": "working", "child.opened": "working",
  "worker.queued": "waiting",
  "reviewer.started": "review", "reviewer.reported": "review",
  "ticket.passed": "verify", "ticket.returned": "verify", "ticket.bounced": "verify",
  "ticket.refused": "queued", "ticket.released": "queued", "worker.retracted": "queued",
  "worker.replaced": "queued", "worker.lost": "queued", "reviewer.lost": "queued",
  "ticket.landed": "landed", "ticket.regressed": "landed", "child.closed": "landed",
  "spec.merged": "landed", "spec.opened": "queued", "spec.suspended": "queued",
  "spec.closed": "queued",
};
const STICKY_EVENTS = new Set(["ticket.claimed"]);
const EVENT_NAME = {
  "spec.opened": "Night opened", "spec.suspended": "Night suspended",
  "spec.closed": "Night closed", "spec.merged": "Night's branch merged",
  "ticket.claimed": "Ticket claimed", "ticket.refused": "Pick-up refused",
  "ticket.passed": "Ticket passed", "ticket.returned": "Ticket handed back",
  "ticket.released": "Claim released", "ticket.landed": "Landed",
  "ticket.regressed": "Regressed after landing", "ticket.bounced": "Merge bounced",
  "worker.started": "Worker started", "worker.resumed": "Worker resumed",
  "worker.retracted": "Worker retracted", "worker.replaced": "Worker replaced",
  "worker.decided": "Decisions recorded", "worker.queued": "Waiting for a slot",
  "worker.touched": "Another ticket touched its files", "worker.lost": "Worker session lost",
  "reviewer.started": "Reviewer started", "reviewer.reported": "Review posted",
  "reviewer.lost": "Reviewer session lost",
};
const CHILD_NAME = {
  finding: "Finding raised", contract: "Spec does not hold", deferred: "Left for a later ticket",
  decision: "Your decision needed", fault: "MMW itself broke",
};
const RUN_NAME = {self: "Criteria run", reverify: "Final criteria run", "repo-checks": "Repository checks"};
const REFUSAL = {
  "wrong-branch": "the worktree was on the wrong branch",
  "dirty-tree": "the tree already carried uncommitted changes",
  "not-open": "the ticket was no longer open",
  "not-ready": "the ticket was not in the agent queue",
  blocked: "a ticket in front of it had not landed",
  "claimed-by-other": "someone else already held it",
};
const RELEASE = {
  landed: "it had landed", suspended: "the night was suspended",
  "worker-lost": "its worker's session was gone",
};
const QUEUE = {
  "product-full": "every instance of the product was in use",
  "machine-full": "every slot on this machine was in use",
};
const RESOLUTION = {fixed: "fixed", stale: "no longer applies", "became-ticket": "became a ticket"};
const COMMON_FIELDS = new Set(["v", "event", "stage", "actor", "spec", "ticket", "at"]);
const SUMMARY_WEIGHT = {
  "ticket.refused": 3, "ticket.returned": 3, "ticket.bounced": 3, "ticket.regressed": 3,
  "child.opened": 3, "ticket.checked": 2, "reviewer.reported": 2, "ticket.landed": 2,
  "ticket.passed": 2, "worker.lost": 2, "ticket.released": 1, "worker.started": 1,
};

const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;
const listOf = (items, max = 2) => {
  const all = items || [];
  if (all.length <= max) return all.join(", ");
  return `${all.slice(0, max).join(", ")} and ${all.length - max} more`;
};
const countsText = counts => {
  if (!counts || counts.total == null) return "";
  return `${counts.met ?? counts.passed ?? 0} of ${counts.total}`;
};

function eventText(event, payload) {
  switch (event) {
    case "worker.started":
    case "worker.resumed":
    case "reviewer.started":
      return payload.model ? `${payload.host} ${payload.model}, ${payload.effort} effort` : "";
    case "worker.touched":
      return `#${payload.by} changed ${plural((payload.files || []).length, "file")} this ticket owns`;
    case "worker.queued":
      return QUEUE[payload.reason] || "";
    case "worker.decided":
      return "the calls the worker made on its own, written down for the review";
    case "ticket.refused":
      return `it would not start: ${REFUSAL[payload.reason] || payload.reason}`;
    case "ticket.released":
      return `back in the queue: ${RELEASE[payload.reason] || payload.reason}`;
    case "ticket.checked": {
      const counts = countsText(payload.counts);
      if (payload.run === "repo-checks") {
        return `${counts || "the"} repository check${payload.counts?.total === 1 ? "" : "s"} passed`;
      }
      const failed = (payload.failed || []).length ? ` — ${listOf(payload.failed, 3)} unmet` : "";
      return `${counts} criteria met${failed}`;
    }
    case "ticket.passed":
      return `${countsText(payload.counts)} criteria met, ticket closed`;
    case "ticket.returned":
      return "handed back with criteria it could not meet";
    case "ticket.landed":
      return `merged into ${payload.into}`;
    case "ticket.bounced":
      return payload.reason === "conflict"
        ? `conflict with ${payload.into} in ${plural((payload.files || []).length, "file")}`
        : `checks failed after merging into ${payload.into}`;
    case "ticket.regressed":
      return `${listOf(payload.failed, 3)} stopped passing on the base branch`;
    case "reviewer.reported":
      return "the three-axis review is on the ticket";
    case "worker.lost":
    case "reviewer.lost":
      return "its session stopped without finishing";
    case "child.opened":
      return payload.title || "";
    case "child.closed":
      return payload.resolution === "became-ticket"
        ? `#${payload.child} became ticket #${payload.became}`
        : `#${payload.child}: ${RESOLUTION[payload.resolution] || payload.resolution}`;
    case "spec.merged":
      return `into the project branch ${payload.project}`;
    default:
      return "";
  }
}

function eventName(event, payload) {
  if (event === "ticket.checked") {
    if (payload.run === "reverify" && payload.stage === "regress") return "Criteria re-run after landing";
    return RUN_NAME[payload.run] || "Criteria run";
  }
  if (event === "child.opened") return CHILD_NAME[payload.kind] || "Sub-issue opened";
  if (event === "child.closed") {
    return payload.resolution === "became-ticket" ? "Finding became a ticket" : "Sub-issue closed";
  }
  return EVENT_NAME[event] || event;
}

function eventTone(event, payload) {
  if (event === "child.opened" && NEEDS_YOU.has(payload.kind)) return "needs-you";
  if (event === "ticket.returned" || event === "ticket.bounced" || event === "ticket.regressed") return "needs-you";
  if (event === "ticket.refused" || /\.lost$|^worker\.(retracted|replaced)$/.test(event)) return "warn";
  if (event === "ticket.checked" && payload.result !== "met") return "warn";
  if (/^ticket\.(landed|passed)$/.test(event)) return "good";
  return "plain";
}

function eventPhase(event, payload) {
  if (event === "ticket.checked") {
    if (payload.run === "repo-checks") return "verify";
    if (payload.run === "reverify") return payload.stage === "regress" ? "landed" : "verify";
    return "working";
  }
  return PHASE_OF_EVENT[event] || "working";
}

function eventDetail(payload, line) {
  const rows = [];
  for (const [key, value] of Object.entries(payload)) {
    if (COMMON_FIELDS.has(key) || key === "details") continue;
    if (key === "criteria") {
      rows.push({k: key, v: value.map(item => `${item.id} ${item.met ? "met" : "unmet"}`).join(", ")});
      continue;
    }
    rows.push({
      k: key,
      v: Array.isArray(value) ? value.join(", ")
        : typeof value === "object" && value !== null ? JSON.stringify(value) : String(value),
    });
  }
  rows.push({k: "comment", v: line});
  return rows;
}

function describeEvent(raw = {}) {
  const payload = raw.payload || {};
  const event = raw.event || "";
  return {
    event,
    time: raw.at ? hhmm(raw.at) : raw.time || "",
    name: eventName(event, payload),
    text: eventText(event, payload),
    phase: eventPhase(event, payload),
    tone: eventTone(event, payload),
    sticky: STICKY_EVENTS.has(event),
    detail: eventDetail(payload, raw.line || ""),
  };
}

function eventBlocks(events = []) {
  const out = [];
  for (const raw of events) {
    const item = describeEvent(raw);
    const last = out[out.length - 1];
    if (last && (last.phase === item.phase || item.sticky)) last.items.push(item);
    else out.push({phase: item.phase, items: [item]});
  }
  for (const block of out) {
    block.from = block.items[0].time;
    block.to = block.items[block.items.length - 1].time;
    block.tone = block.items.some(item => item.tone === "needs-you") ? "needs-you"
      : block.items.some(item => item.tone === "warn") ? "warn" : "plain";
  }
  return out;
}

function blockSummary(block) {
  const best = block.items.reduce((pick, item) =>
    (SUMMARY_WEIGHT[item.event] || 0) >= (SUMMARY_WEIGHT[pick.event] || 0) ? item : pick,
  block.items[0]);
  return best.text ? `${best.name} — ${best.text}` : best.name;
}

MMW['board-logic'] = {PHASES, LAMP_WORD, Board, defaultExpanded, describeEvent, eventBlocks, blockSummary};
Object.assign(MMW, MMW['board-logic']);
})();
// ── local-config.mjs ──
(function () {
const {hhmm} = MMW;

const CATALOG = {
  store: "~/.mmw/models.json",
  agents: ["junior-worker", "senior-worker", "reviewer", "advisor"],
  hosts: ["cursor", "grok", "claude", "codex", "pi"],
  binaries: {cursor: "cursor-agent", grok: "grok", claude: "claude", codex: "codex", pi: "pi"},
  launch: {
    cursor: {cli: true, paseo: true},
    grok: {cli: true, paseo: true},
    claude: {cli: true, paseo: true},
    codex: {cli: true, paseo: true},
    pi: {cli: false, paseo: true},
  },
  runners: ["herdr", "orca", "paseo"],
};

const LocalConfig = {
  CELLS: ["host", "model", "effort"],
  ROLE_WHAT: {
    "junior-worker": "贴 junior-worker label 的 ticket",
    "senior-worker": "贴 senior-worker label 的 ticket",
    reviewer: "review 每张 ticket 的改动",
    advisor: "被问到时给第二意见",
  },
  source: d => (d.runner === "paseo" ? "paseo" : "cli"),
  needsRescan: (from, to) => LocalConfig.source(from) !== LocalConfig.source(to),
  hostScan: (scan, host) => scan[host] || {state: "missing", offered: []},
  hostState(scan, d, host, catalog = CATALOG) {
    const launch = catalog.launch[host] || {};
    return launch[LocalConfig.source(d)] ? LocalConfig.hostScan(scan, host).state : "unlaunchable";
  },
  offeredBy: (scan, host) => LocalConfig.hostScan(scan, host).offered,
  effortsOf: (scan, host, model) =>
    (LocalConfig.offeredBy(scan, host).find(o => o.model === model) || {efforts: []}).efforts,
  stateWord: (state, d) => ({
    missing: "本机没装", silent: "没有回答", down: "Paseo 没开",
    unlaunchable: d && LocalConfig.source(d) === "paseo" ? "Paseo 起不了" : "orca、herdr 起不了",
  }[state] || state),
  hostWhy: (state, host, d, catalog = CATALOG) => ({
    missing: `这台机器上没装 ${host} 的 CLI（${catalog.binaries[host]}），换一个这台机器有的`,
    silent: `${host} 的 CLI 在扫描时没有回答，换一个这台机器有的`,
    down: `Paseo 服务没开，问不到 ${host} 的 model；先开 Paseo，或者把 runner 换回 orca 或 herdr`,
    unlaunchable: LocalConfig.source(d) === "paseo"
      ? `Paseo 起不了 ${host}：hosts.json 没给它 paseo 块；换一个 host`
      : `orca 和 herdr 起不了 ${host}：hosts.json 没给它命令行启动块（cli）；换一个 host，或者把 runner 换成 paseo`,
  }[state]),

  problems(scan, d, catalog = CATALOG) {
    const L = LocalConfig, out = [];
    if (d.runner !== "auto" && !catalog.runners.includes(d.runner)) {
      out.push({key: "runner", cell: "runner", text: `${d.runner} 没有适配器，start 起不了 session`});
    }
    for (const a of catalog.agents) {
      const r = d.rows[a];
      if (!catalog.hosts.includes(r.host)) {
        out.push({key: a, cell: "host", text: `${r.host} 不是 MMW 认识的 host`});
        continue;
      }
      const hs = L.hostScan(scan, r.host), hostState = L.hostState(scan, d, r.host, catalog);
      if (hostState !== "ok") {
        out.push({key: a, cell: "host", text: L.hostWhy(hostState, r.host, d, catalog)});
        continue;
      }
      if (!r.model) {
        out.push({key: a, cell: "model", text: "还没选 model"});
        continue;
      }
      if (!hs.offered.some(o => o.model === r.model)) {
        out.push({key: a, cell: "model", text: `这台机器的 ${r.host} 已经不提供 ${r.model}`});
        continue;
      }
      if (!r.effort) {
        out.push({key: a, cell: "effort", text: "还没选 effort"});
        continue;
      }
      if (!L.effortsOf(scan, r.host, r.model).includes(r.effort)) {
        out.push({key: a, cell: "effort", text: `${r.model} 在 ${r.host} 上没有 ${r.effort} 这一档`});
      }
    }
    return out;
  },
  changes(d, s, catalog = CATALOG) {
    const out = d.runner !== s.runner ? [{key: "runner", text: "runner", cells: ["runner"]}] : [];
    for (const a of catalog.agents) {
      const cells = LocalConfig.CELLS.filter(c => d.rows[a][c] !== s.rows[a][c]);
      if (cells.length) out.push({key: a, text: `${a} 的 ${cells.join("、")}`, cells});
    }
    return out;
  },
  setCell(scan, d, key, cell, value) {
    const L = LocalConfig;
    if (key === "runner") {
      d.runner = value;
      return d;
    }
    const r = d.rows[key];
    r[cell] = value;
    if (cell === "host" && !L.offeredBy(scan, value).some(o => o.model === r.model)) r.model = "";
    if (cell !== "effort") {
      const es = L.effortsOf(scan, r.host, r.model);
      if (!es.includes(r.effort)) r.effort = es.length === 1 ? es[0] : "";
    }
    return d;
  },
  saveOff(scan, d, saved, flags = {}, catalog = CATALOG) {
    const ch = LocalConfig.changes(d, saved, catalog);
    const probs = LocalConfig.problems(scan, d, catalog);
    return !ch.length || probs.length > 0 || !!flags.scanning || !!flags.refused;
  },

  runnerOptions(d, catalog = CATALOG) {
    const opts = [
      ...(d.runner !== "auto" && !catalog.runners.includes(d.runner)
        ? [{value: d.runner, text: `${d.runner} · 没有适配器`}] : []),
      ...catalog.runners.map(r => ({value: r, text: r})),
      {value: "auto", text: "按所在环境判断"},
    ];
    return opts.map(o => ({...o, selected: o.value === d.runner, disabled: !!o.disabled}));
  },
  rowOptions(scan, d, a, catalog = CATALOG) {
    const L = LocalConfig, r = d.rows[a], hs = L.hostScan(scan, r.host);
    const hostOk = L.hostState(scan, d, r.host, catalog) === "ok";
    const modelKnown = hostOk && hs.offered.some(o => o.model === r.model);
    const mark = (opts, value) => opts.map(o => ({...o, selected: o.value === value, disabled: !!o.disabled}));
    const host = [
      ...(catalog.hosts.includes(r.host) ? [] : [{value: r.host, text: `${r.host} · MMW 不认识`}]),
      ...catalog.hosts.map(h => {
        const hostState = L.hostState(scan, d, h, catalog);
        return {
          value: h,
          text: hostState === "ok" ? h : `${h} · ${L.stateWord(hostState, d)}`,
          disabled: hostState !== "ok" && h !== r.host,
        };
      }),
    ];
    const offeredEfforts = L.effortsOf(scan, r.host, r.model);
    const effortKnown = modelKnown && offeredEfforts.includes(r.effort);
    const model = !hostOk ? [{value: r.model, text: r.model || "—"}] : [
      ...(!r.model ? [{value: "", text: "选一个 model", disabled: true}]
        : modelKnown ? [] : [{value: r.model, text: `${r.model} · 本机已经没有`}]),
      ...hs.offered.map(o => ({value: o.model, text: o.model})),
    ];
    const effort = !modelKnown ? [{value: r.effort, text: r.effort || "—"}] : [
      ...(!r.effort ? [{value: "", text: "选一档", disabled: true}]
        : effortKnown ? [] : [{value: r.effort, text: `${r.effort} · 本机已经没有`}]),
      ...offeredEfforts.map(e => ({value: e, text: e === "—" ? "—（不设）" : e})),
    ];
    return {host: mark(host, r.host), model: mark(model, r.model), effort: mark(effort, r.effort), hostOk, modelKnown};
  },
  hostChips(scan, d, catalog = CATALOG) {
    return catalog.hosts.map(h => {
      const offered = LocalConfig.hostScan(scan, h);
      const hostState = LocalConfig.hostState(scan, d, h, catalog);
      return {
        host: h, state: hostState,
        what: hostState === "ok" ? `${offered.offered.length} 个 model` : LocalConfig.stateWord(hostState, d),
      };
    });
  },
};

function catalogFromPayload(payload) {
  const hosts = [];
  const launch = {};
  const binaries = {};
  for (const item of payload.hosts) {
    hosts.push(item.name);
    launch[item.name] = {cli: !!item.cli, paseo: !!item.paseo};
    if (item.binary) binaries[item.name] = item.binary;
  }
  return {
    store: CATALOG.store,
    agents: CATALOG.agents,
    hosts,
    binaries,
    launch,
    runners: payload.runners.filter(name => name !== "auto"),
  };
}

function settingsView(sheet, scan, catalog) {
  const L = LocalConfig, draft = sheet.draft;
  const probs = [
    ...(sheet.scanning ? [] : L.problems(scan, draft, catalog)),
    ...(sheet.serverFlags || []),
  ];
  const ch = L.changes(draft, sheet.saved, catalog);
  const cls = (key, cell) => (probs.some(p => p.key === key && p.cell === cell) ? "sel bad"
    : ch.some(c => c.key === key && c.cells.includes(cell)) ? "sel changed" : "sel");
  const bads = key => probs.filter(p => p.key === key).map(p => ({text: p.text}));
  const rows = catalog.agents.map(a => {
    const o = L.rowOptions(scan, draft, a, catalog), r = draft.rows[a], b = bads(a);
    return {
      agent: a, what: L.ROLE_WHAT[a], host: r.host, model: r.model, effort: r.effort,
      hostCls: cls(a, "host"), modelCls: cls(a, "model"), effortCls: cls(a, "effort"),
      hostOpts: o.host, modelOpts: o.model, effortOpts: o.effort,
      hostOff: sheet.scanning, modelOff: sheet.scanning || !o.hostOk, effortOff: sheet.scanning || !o.modelKnown,
      hostLabel: `${a} 的 host`, modelLabel: `${a} 的 model`, effortLabel: `${a} 的 effort`,
      bads: b, hasBad: b.length > 0,
    };
  });
  const when = "保存后，下一个新起的 agent 就用新值；已经在跑的不受影响。";
  let strong, quiet, hatch = false;
  if (sheet.refused) {
    strong = "没有保存";
    quiet = "这一页打开之后，本机配置被别处改过，先重新读取。";
  } else if (sheet.scanning) {
    strong = "正在扫描本机的 host";
    quiet = "扫描完之前不能保存。";
  } else if (probs.length) {
    strong = `有 ${probs.length} 处 start 会拒绝，改好之前不能保存`;
    quiet = "带斜线的格子，下面一行写着哪里不对。";
    hatch = true;
  } else if (ch.length) {
    strong = `改了 ${ch.length} 处：${ch.map(c => c.text).join("；")}`;
    quiet = when;
  } else if (sheet.savedAt) {
    strong = `已保存 · ${hhmm(sheet.savedAt)}`;
    quiet = "从下一个新起的 agent 开始用；已经在跑的不受影响。";
  } else {
    strong = "没有改动";
    quiet = "上面就是下一个新起的 agent 会用的配置。";
  }
  const rb = bads("runner");
  const at = sheet.modifiedAt;
  return {
    store: catalog.store, rows,
    runner: draft.runner, runnerCls: cls("runner", "runner"), runnerOpts: L.runnerOptions(draft, catalog),
    runnerOff: sheet.scanning, runnerBads: rb, runnerHasBad: rb.length > 0,
    chips: L.hostChips(scan, draft, catalog).map(c => ({
      cls: "hs " + (sheet.scanning ? "" : c.state), host: c.host, what: sheet.scanning ? "…" : c.what,
    })),
    scanning: sheet.scanning,
    scanningText: L.source(draft) === "paseo" ? "正在向 Paseo 要每个 host 的 model…" : "正在问每个 host 的 CLI 有哪些 model…",
    scannedText: `${sheet.scannedAt ? hhmm(sheet.scannedAt) : ""} 问${sheet.scanSource === "paseo" ? " Paseo" : "各 host 的 CLI"} ·`,
    refused: !!sheet.refused,
    refusedText: `这一页打开之后，本机配置在 ${at ? hhmm(at) : ""} 被别处改过（一个 agent 从命令行改的）。重新读取会换成现在保存着的内容，你刚才改的 ${sheet.refused} 处要再改一次。`,
    strong, quiet, hatch,
    closeLabel: ch.length ? "取消" : "关闭",
    saveOff: !ch.length || probs.length > 0 || !!sheet.scanning || !!sheet.refused,
    changed: ch.length > 0,
  };
}

MMW['local-config'] = {CATALOG, LocalConfig, catalogFromPayload, settingsView};
Object.assign(MMW, MMW['local-config']);
})();
// ── topbar.mjs ──
(function () {
const {Board, LAMP_WORD} = MMW;
const {el, hand, hhmm, minutes} = MMW;

const REFRESH_ICON = '<svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path></svg>';
const GEAR_ICON = '<svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg>';

function clockFrom(text) {
  return (text || "").match(/(\d{2}:\d{2})/)?.[1] || "";
}

function agoFrom(text) {
  return Number((text || "").match(/（(\d+) 分钟前）/)?.[1] || 0);
}

function fromScene(data = {}) {
  const v = data.vals?.v || {};
  return {
    orangeN: v.orangeN ?? 0,
    greenN: v.greenN ?? 0,
    hollowN: v.hollowN ?? 0,
    inkN: v.inkN ?? 0,
    waiting: v.hasWaiting ? Number((v.waitingSub || "").match(/(\d+)/)?.[1] || 0) : 0,
    readFailed: (v.readCls || "").includes("failed"),
    readClock: clockFrom(v.readText),
    readAgo: agoFrom(v.readText),
    settingsOpen: (data.vals?.gearCls || "gear") === "gear on",
  };
}

function fromBoard(payload = {}, now = new Date()) {
  const tasks = payload.tasks || [];
  const all = tasks.flatMap(task => Board.allTickets(task));
  const count = lamp => all.filter(ticket => Board.lamp(ticket) === lamp).length;
  const waiting = all.filter(ticket => Board.phase(ticket) === "waiting").length;
  const readAt = payload.read_failed?.at || payload.read_at;
  return {
    orangeN: count("orange"),
    greenN: count("green"),
    hollowN: count("hollow"),
    inkN: count("ink"),
    waiting,
    readFailed: Boolean(payload.read_failed),
    readClock: readAt ? hhmm(readAt) : "",
    readAgo: readAt ? minutes(readAt, now) : 0,
    settingsOpen: Boolean(payload.settingsOpen),
  };
}

async function notify(method, hook) {
  await hand(async () => {
    const response = await method();
    if (response.ok) hook?.(await response.json());
  });
}

function render(host, view = {}, api, hooks = {}) {
  const orangeN = view.orangeN ?? 0;
  const hot = orangeN > 0;
  const waiting = view.waiting || 0;
  const read = view.readFailed
    ? {cls: "readstate failed", text: `读 GitHub 失败 · 下面是 ${view.readClock} 的数据（${view.readAgo} 分钟前）`}
    : {cls: "readstate", text: view.readClock ? `只读 · ${view.readClock} 读取` : ""};
  const root = el("header", {class: "topbar board"});
  root.dataset.screen = "topbar";
  root.append(
    el("div", {class: "brand"},
      el("span", {class: "brand-mark"}, "MMW"),
      el("span", {class: "brand-name"}, "task board"),
      el("span", {class: "brand-repo"}, "chancheuklap/multi-model-workflow"),
    ),
    el("div", {class: "counters"},
      el("button", {
        type: "button",
        class: hot ? "counter hot" : "counter",
        disabled: !hot,
        title: "跳到下一张 needs you 的 ticket",
        onClick: () => hooks.onJumpNeedYou?.(),
      }, el("span", {class: hot ? "lamp orange" : "lamp hollow"}),
        LAMP_WORD.orange, el("span", {class: hot ? "counter-n hot" : "counter-n"}, String(orangeN))),
      el("span", {class: "counter"},
        el("span", {class: "lamp green"}), LAMP_WORD.green,
        el("span", {class: "counter-n"}, String(view.greenN ?? 0)),
        waiting ? el("span", {class: "counter-sub"}, `waiting for a slot ${waiting}`) : null),
      el("span", {class: "counter"},
        el("span", {class: "lamp hollow"}), LAMP_WORD.hollow,
        el("span", {class: "counter-n"}, String(view.hollowN ?? 0))),
      el("span", {class: "counter"},
        el("span", {class: "lamp ink"}), LAMP_WORD.ink,
        el("span", {class: "counter-n"}, String(view.inkN ?? 0))),
    ),
    el("div", {class: read.cls}, read.text),
    el("button", {
      type: "button", class: "gear",
      "aria-label": "立刻重读 GitHub",
      title: "立刻重读 GitHub（页面开着时每分钟自动读一次）",
      html: REFRESH_ICON,
      onClick: () => { void notify(() => api.refresh(), hooks.onRefresh); },
    }),
    el("button", {
      type: "button", class: view.settingsOpen ? "gear on" : "gear",
      "aria-label": "本机配置",
      title: "本机配置：每个 agent 跑在哪个 host、model、effort",
      html: GEAR_ICON,
      onClick: () => { void notify(() => api.settings(), hooks.onOpenSettings); },
    }),
  );
  host.replaceChildren(root);
  return root;
}

MMW['topbar'] = {fromScene, fromBoard, render};
})();
// ── tasks.mjs ──
(function () {
const {Board, LAMP_WORD} = MMW;

function markOn(row, selectedTask) {
  const on = row.n === selectedTask;
  return {...row, cls: on ? "task on" : "task", titleCls: on ? "task-title on" : "task-title"};
}

function taskListView(tasks, selectedTask) {
  return {
    count: tasks.length,
    empty: !tasks.length,
    rows: tasks.map(task => {
      const progress = Board.progress(task);
      const lamp = Board.aggregate(Board.allTickets(task));
      return markOn({
        n: task.n,
        lampCls: "lamp " + lamp,
        lampWord: LAMP_WORD[lamp],
        meta: `#${task.n} · ${task.kind}`,
        title: task.title,
        barStyle: {width: (progress.total ? 100 * progress.done / progress.total : 0) + "%"},
        count: `${progress.done}/${progress.total} landed`,
      }, selectedTask);
    }),
  };
}

function rowsFor(data, selectedTask) {
  if (Array.isArray(data.tasks)) return taskListView(data.tasks, selectedTask);
  if (data.view) {
    return {
      count: data.view.count,
      empty: data.view.empty,
      rows: data.view.rows.map(row => markOn(row, selectedTask)),
    };
  }
  return {count: 0, empty: true, rows: []};
}

function rowButton(row, onPick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = row.cls;
  button.addEventListener("click", () => onPick(row.n));

  const lamp = document.createElement("span");
  lamp.className = row.lampCls;
  lamp.title = row.lampWord;

  const meta = document.createElement("span");
  meta.className = "task-meta";
  meta.textContent = row.meta;

  const title = document.createElement("span");
  title.className = row.titleCls;
  title.textContent = row.title;

  const fill = document.createElement("span");
  fill.className = "bar-fill";
  fill.style.width = row.barStyle.width;
  const bar = document.createElement("span");
  bar.className = "bar";
  bar.append(fill);
  const count = document.createElement("span");
  count.className = "task-count";
  count.textContent = row.count;
  const progress = document.createElement("span");
  progress.className = "task-progress";
  progress.append(bar, count);

  button.append(lamp, meta, title, progress);
  return button;
}

function render(host, data = {}, api = undefined) {
  const root = document.createElement("nav");
  root.dataset.screen = "tasks";
  root.className = "tasks board";
  root.setAttribute("aria-label", "The Night");

  const paint = (selectedTask) => {
    const next = rowsFor(data, selectedTask);
    const eyebrow = document.createElement("div");
    eyebrow.className = "col-eyebrow";
    const label = document.createElement("span");
    label.textContent = "The Night";
    const count = document.createElement("span");
    count.textContent = String(next.count);
    eyebrow.append(label, count);
    const kids = [eyebrow];
    if (next.empty) {
      const empty = document.createElement("p");
      empty.className = "tasks-empty";
      empty.textContent = "没有带 mmw:map label 的 ticket。";
      kids.push(empty);
    }
    for (const row of next.rows) {
      kids.push(rowButton(row, n => {
        paint(n);
        data.onSelectTask?.(n);
      }));
    }
    root.replaceChildren(...kids);
  };

  paint(data.selectedTask ?? null);
  host.replaceChildren(root);
  return root;
}

MMW['tasks'] = {taskListView, render};
})();
// ── canvas.mjs ──
(function () {
const {Board, LAMP_WORD, defaultExpanded} = MMW;

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

function stillEdges(svg) {
  if (!svg) return svg;
  return svg
    .replace(/<g class="e-beam">[\s\S]*?<\/g>/g, match => {
      const d = /d="([^"]+)"/.exec(match);
      return d ? `<path class="e-beam still" d="${d[1]}"/>` : "";
    })
    .replace(/<circle class="e-pulse"[^>]*>[\s\S]*?<\/circle>/g, "");
}

function canvasView(task, sel, expandedList, reduced) {
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
        cls: "card" + (on ? " on" : ""), titleCls: isMap ? "card-title map container" : "card-title container",
        lampCls: "lamp " + lamp, lampWord: LAMP_WORD[lamp], count: `${done}/${list.length}`,
        canExpand, chev: open ? "▾" : "▸", toggleLabel: (open ? "collapse #" : "expand #") + container.n,
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
  if (data.task && typeof data.task === "object") {
    return canvasView(data.task, sel, expanded, reduced);
  }
  if (!data.view) return canvasView(null);
  const view = reduced && data.view.svg ? {...data.view, svg: stillEdges(data.view.svg)} : data.view;
  return markSelected(view, sel);
}

function cardHit(n, title, onPick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "card-hit";
  button.setAttribute("aria-label", `#${n} ${title}`);
  button.addEventListener("click", () => onPick(n));
  return button;
}

function cardShell(item, onPick, {lampTitle, titled, titleCls, right, after}) {
  const card = document.createElement("div");
  card.className = item.cls;
  Object.assign(card.style, item.pos);
  if (titled) card.title = item.title;
  const lamp = document.createElement("span");
  lamp.className = item.lampCls;
  if (lampTitle) lamp.title = item.lampWord;
  const num = document.createElement("span");
  num.className = "card-num";
  num.textContent = item.num;
  const rightEl = document.createElement("span");
  rightEl.className = "card-right";
  rightEl.append(...right);
  const top = document.createElement("div");
  top.className = "card-top";
  top.append(lamp, num, rightEl);
  const title = document.createElement("div");
  title.className = titleCls;
  title.textContent = item.title;
  card.append(cardHit(item.n, item.title, onPick), top, title, ...after);
  return card;
}

function containerCard(item, onPick, onToggle) {
  const count = document.createElement("span");
  count.className = "card-count";
  count.textContent = item.count;
  const right = [count];
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
    right.push(chev);
  }
  const fill = document.createElement("div");
  fill.className = "card-bar-fill";
  fill.style.width = item.barStyle.width;
  const bar = document.createElement("div");
  bar.className = "card-bar";
  bar.append(fill);
  return cardShell(item, onPick, {lampTitle: true, titled: true, titleCls: item.titleCls, right, after: [bar]});
}

function decisionCard(item, onPick) {
  const kind = document.createElement("span");
  kind.className = "card-kind";
  kind.textContent = item.kind;
  return cardShell(item, onPick, {
    lampTitle: false, titled: true, titleCls: "card-title decision", right: [kind], after: [],
  });
}

function ticketCard(item, onPick) {
  const pill = document.createElement("span");
  pill.className = item.pillCls;
  pill.textContent = item.phase;
  const run = document.createElement("div");
  run.className = item.runCls;
  run.textContent = item.run;
  return cardShell(item, onPick, {
    lampTitle: true, titled: true, titleCls: "card-title", right: [pill], after: [run],
  });
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
  bar.append(mark, "closing pass");
  root.append(
    item("legend-line", "contains · released"),
    item("legend-line flow", "released · working"),
    item("legend-line blocked", "blocked"),
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
  out.setAttribute("aria-label", "zoom out");
  out.textContent = "−";
  out.addEventListener("click", onOut);
  const zoomLevel = document.createElement("span");
  zoomLevel.className = "zoom-level";
  zoomLevel.textContent = level;
  const inn = document.createElement("button");
  inn.type = "button";
  inn.className = "zoom-btn";
  inn.setAttribute("aria-label", "zoom in");
  inn.textContent = "+";
  inn.addEventListener("click", onIn);
  const sep = document.createElement("span");
  sep.className = "zoom-sep";
  const fit = document.createElement("button");
  fit.type = "button";
  fit.className = "zoom-btn text";
  fit.textContent = "fit";
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
  title.textContent = "The Night 还没开始";
  const text = document.createElement("p");
  text.className = "canvas-empty-text";
  text.append("The Night 是一次讨论开出的那张 ticket。给它打上 ");
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

function startingExpanded(data) {
  if (data.expanded != null) return [...data.expanded];
  if (data.task && typeof data.task === "object") return [...defaultExpanded(data.task)];
  return [];
}

function render(host, data = {}, api = undefined) {
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
  root.className = "canvas board";
  root.setAttribute("aria-label", "画布：拖动平移，按住 ⌘ 或双指捏合缩放");

  let worldEl, zoomEl, lastView;

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

MMW['canvas'] = {stillEdges, canvasView, render};
})();
// ── detail.mjs ──
(function () {
const {Board, LAMP_WORD, PHASES, eventBlocks, blockSummary} = MMW;
const {el} = MMW;

const NEEDS_YOU = new Set(["decision", "fault", "contract"]);

function lampFrom(cls) {
  if (!cls) return "hollow";
  if (/\borange\b/.test(cls)) return "orange";
  if (/\bgreen\b/.test(cls)) return "green";
  if (/\bink\b/.test(cls)) return "ink";
  if (/\bnone\b/.test(cls)) return "none";
  return "hollow";
}

function kindOf(d) {
  if (d.isTicket) return "ticket";
  if (d.isMap) return "map";
  if (d.isSpec) return "spec";
  if (d.isDecision) return "decision";
  return "empty";
}

function firstRows(...candidates) {
  return candidates.find(rows => Array.isArray(rows) && rows.length) || [];
}

function relFrom(row) {
  return {
    n: row.n,
    num: row.num,
    title: row.title,
    where: row.where || "",
    lamp: lampFrom(row.lampCls),
    state: row.state,
    phase: row.phase,
    hold: Boolean(row.hold || row.showHold),
    unknown: Boolean(row.unknown || row.known === false),
  };
}

function phaseItemFrom(item) {
  return {
    event: item.event, time: item.time, name: item.name, text: item.text || "",
    hasText: item.hasText ?? Boolean(item.text),
    tone: item.tone || "plain",
    detail: item.detail || [],
  };
}

function fromScene(data = {}) {
  const vals = data.vals || {};
  const d = vals.d || {};
  const hasCard = d.hasCard ?? Boolean(d.isTicket || d.isMap || d.isSpec || d.isDecision || d.isContainer);
  if (!hasCard) {
    return {
      empty: true,
      emptyTitle: vals.emptyTitle || "点一张卡",
      emptyText: vals.emptyText
        || "画布上任意一张卡——map、spec、ticket 或 decision ticket——点一下，它的全部细节就在这一栏。",
    };
  }
  const rawEvents = vals.rawEvents || d.rawEvents || [];
  const phaseBlocks = (vals.phaseBlocks || d.phaseBlocks || []).map(block => ({
    phase: block.phase,
    tone: block.tone || "plain",
    openByDefault: Boolean(block.openByDefault),
    summary: block.summary || "",
    from: block.from,
    span: block.span || (block.from !== block.to ? `${block.from}–${block.to}` : block.from),
    items: (block.items || []).map(phaseItemFrom),
  }));
  return {
    empty: false,
    repo: vals.repo,
    kind: kindOf(d),
    eyebrow: d.eyebrow,
    num: d.num,
    title: d.title,
    lamp: lampFrom(d.lampCls),
    statusWord: d.statusWord,
    elapsed: d.elapsed || "",
    phase: d.phase,
    why: d.why || [],
    links: vals.links || d.links || [],
    blockers: firstRows(vals.blockedBy, d.blockedBy, vals.blockers, d.blockers).map(relFrom),
    blocks: firstRows(vals.blocking, d.blocking, vals.blocks, d.blocks).map(relFrom),
    kids: firstRows(vals.kids, d.kids).map(row => ({
      num: row.num, kind: row.kind, title: row.title,
      lamp: lampFrom(row.lampCls),
      hot: Boolean(row.kindCls && row.kindCls.includes("hot")) || NEEDS_YOU.has(row.kind),
    })),
    rawEvents,
    eventCount: d.eventCount ?? rawEvents.length,
    phaseBlocks,
    runtime: d.hasRun ? {grade: d.runGrade, model: d.runModel, rows: d.runRows || []} : null,
    noRunText: d.noRunText || "not dispatched yet",
    gh: d.gh,
    ghLabel: d.ghLabel,
    listTitle: d.listTitle,
    listCount: d.listCount,
    lamps: (d.lamps || []).map(item => ({lamp: lampFrom(item.cls), word: item.word, n: item.n})),
    phases: (d.phases || []).map(item => ({
      phase: (item.cls || "").replace(/^pill\s+/, ""), label: item.label,
    })),
    ticketRows: (vals.ticketRows || d.ticketRows || []).map(relFrom),
    specRows: (vals.specRows || d.specRows || []).map(relFrom),
    decisionRows: (vals.decisionRows || d.decisionRows || []).map(relFrom),
    specCount: d.specCount,
    decisionCount: d.decisionCount,
  };
}

function find(tasks, n) {
  if (n == null) return null;
  for (const task of tasks) {
    if (task.n === n) {
      return task.kind === "spec" ? {type: "spec", ref: task.specs[0], task} : {type: "map", ref: task, task};
    }
    for (const decision of task.decisions || []) {
      if (decision.n === n) return {type: "decision", ref: decision, task};
    }
    for (const spec of task.specs || []) {
      if (spec.n === n) return {type: "spec", ref: spec, task};
      for (const ticket of spec.tickets || []) {
        if (ticket.n === n) return {type: "ticket", ref: ticket, task, spec};
      }
    }
  }
  return null;
}

function relRowFromBoard(tasks, n, role, hereSpec, thisTicket) {
  const found = find(tasks, n);
  if (!found) {
    return {n, num: `#${n}`, lamp: "none", title: "不在这棵树里，读不到它的状态",
      where: "", state: "unknown", unknown: true, hold: false};
  }
  let lamp, state, phase, hold = false;
  if (found.type === "ticket") {
    lamp = Board.lamp(found.ref);
    phase = Board.phase(found.ref);
    state = found.ref.fold.landed ? "landed"
      : role !== "blocker" ? LAMP_WORD[lamp]
        : Board.released(found.ref) ? "closed unpassed · released" : "not landed";
    hold = role === "blocker" ? !Board.released(found.ref)
      : Boolean(thisTicket) && !Board.released(thisTicket);
  } else if (found.type === "spec") {
    lamp = Board.aggregate(found.ref.tickets);
    state = `${found.ref.tickets.filter(ticket => Board.done(ticket)).length}/${found.ref.tickets.length}`;
  } else {
    lamp = Board.decisionLamp(found.ref);
    state = found.ref.state === "closed" ? "closed" : "open";
  }
  return {
    n, num: `#${n}`, lamp, title: found.ref.title, unknown: false,
    where: found.spec && found.spec.n !== hereSpec ? `spec #${found.spec.n}` : "",
    state, phase, hold,
  };
}

function heldFirst(rows) {
  return [...rows].sort((a, b) => Number(b.hold) - Number(a.hold));
}

function phaseBlocksFrom(events) {
  const blocks = eventBlocks(events);
  return blocks.map((block, index) => ({
    phase: block.phase,
    tone: block.tone,
    openByDefault: index === blocks.length - 1 || block.tone !== "plain",
    summary: blockSummary(block),
    from: block.from,
    span: block.from !== block.to ? `${block.from}–${block.to}` : block.from,
    items: block.items.map(item => ({
      event: item.event, time: item.time, name: item.name, text: item.text,
      hasText: Boolean(item.text), tone: item.tone, detail: item.detail,
    })),
  }));
}

function ticketView(tasks, found) {
  const ticket = found.ref, fold = ticket.fold, lamp = Board.lamp(ticket), phase = Board.phase(ticket);
  const started = [...ticket.events].reverse().find(event => event.event === "worker.started");
  const hasRun = Boolean(fold.worker && started);
  const payload = (started && started.payload) || {};
  const worktree = String(payload.worktree || "").split("/.worktrees/")[1];
  const slot = [...ticket.events].reverse()
    .find(event => event.event === "ticket.checked" && event.payload?.slot != null);
  const runRows = [
    ["ticket branch", payload.branch], ["base branch", payload.into],
    ["worktree", worktree ? `…/.worktrees/${worktree}` : payload.worktree],
    ["machine", payload.machine],
    ...(slot ? [["slot", String(slot.payload.slot)]] : []),
  ].filter(([, value]) => value).map(([k, v]) => ({k, v}));
  const blockers = ticket.blocked.map(n => relRowFromBoard(tasks, n, "blocker", found.spec.n, ticket));
  const blocking = found.spec.tickets
    .filter(item => item.blocked.includes(ticket.n))
    .map(item => relRowFromBoard(tasks, item.n, "blocked", found.spec.n, ticket));
  const kids = Object.values(fold.children);
  return {
    empty: false, kind: "ticket", eyebrow: "Ticket", num: `#${ticket.n}`,
    links: [{label: `spec #${found.spec.n}`, n: found.spec.n}, {label: `map #${found.task.n}`, n: found.task.n}],
    title: ticket.title, lamp, statusWord: LAMP_WORD[lamp], elapsed: Board.elapsed(ticket),
    phase,
    why: Board.why(ticket).map(item => item.child
      ? {head: `#${item.child} ${item.kind}`, body: `${item.title}。${item.text}`}
      : {head: "", body: item.text}),
    runtime: hasRun ? {
      grade: payload.grade || "",
      model: `${payload.host} · ${payload.model} · ${payload.effort}`,
      rows: runRows,
    } : null,
    noRunText: phase === "landed" ? "closed without a run" : "not dispatched yet",
    blockers, blocks: blocking,
    kids: kids.map(child => ({
      num: `#${child.child}`, title: child.title, kind: child.kind,
      lamp: child.resolution ? "ink" : NEEDS_YOU.has(child.kind) ? "orange" : "hollow",
      hot: NEEDS_YOU.has(child.kind),
    })),
    rawEvents: ticket.events,
    eventCount: ticket.events.length,
    phaseBlocks: phaseBlocksFrom(ticket.events),
    gh: ticket.n,
  };
}

function containerView(tasks, found) {
  const container = found.ref, isMap = found.type === "map";
  const list = isMap ? Board.allTickets(container) : container.tickets;
  const lamp = Board.aggregate(list);
  const countLight = key => list.filter(ticket => Board.lamp(ticket) === key).length;
  const countPhase = key => list.filter(ticket => Board.phase(ticket) === key).length;
  const done = list.filter(ticket => Board.done(ticket)).length;
  return {
    empty: false, kind: isMap ? "map" : "spec",
    eyebrow: isMap ? "The Night" : "Spec",
    num: `#${container.n}` + (isMap ? ` · ${container.kind}` : ""),
    links: isMap || found.task.n === container.n ? [] : [{label: `map #${found.task.n}`, n: found.task.n}],
    title: container.title, lamp, statusWord: LAMP_WORD[lamp],
    elapsed: `${done}/${list.length} landed`,
    listTitle: isMap ? "All tickets" : "Its tickets", listCount: list.length,
    lamps: ["orange", "green", "hollow", "ink"].filter(key => countLight(key))
      .map(key => ({lamp: key, word: LAMP_WORD[key], n: countLight(key)})),
    phases: PHASES.filter(phase => countPhase(phase)).map(phase => ({phase, label: `${phase} · ${countPhase(phase)}`})),
    specRows: isMap ? container.specs.map(spec => relRowFromBoard(tasks, spec.n, "spec", null)) : [],
    specCount: isMap ? container.specs.length : 0,
    decisionCount: isMap ? container.decisions.length : 0,
    decisionRows: isMap ? container.decisions.map(decision => relRowFromBoard(tasks, decision.n, "decision", null)) : [],
    ticketRows: isMap ? [] : container.tickets.map(ticket => {
      const phase = Board.phase(ticket);
      return {n: ticket.n, num: `#${ticket.n}`, lamp: Board.lamp(ticket), title: ticket.title, phase};
    }),
    gh: container.n, ghLabel: `在 GitHub 打开 #${container.n} ↗`,
    why: [], kids: [], blockers: [], blocks: [],
  };
}

function decisionView(tasks, found) {
  const decision = found.ref, lamp = Board.decisionLamp(decision);
  const blocks = found.task.decisions.filter(item => item.blocked.includes(decision.n)).map(item => item.n);
  return {
    empty: false, kind: "decision", eyebrow: `Decision ticket · ${decision.kind}`, num: `#${decision.n}`,
    links: [{label: `map #${found.task.n}`, n: found.task.n}],
    title: decision.title, lamp,
    statusWord: decision.state === "closed" ? "settled" : "还开着",
    elapsed: "",
    blockers: decision.blocked.map(n => relRowFromBoard(tasks, n, "decision", null)),
    blocks: blocks.map(n => relRowFromBoard(tasks, n, "decision", null)),
    gh: decision.n, ghLabel: `在 GitHub 打开 #${decision.n} ↗`,
    why: [], kids: [],
  };
}

function fromBoard(payload = {}, selected) {
  const tasks = payload.tasks || [];
  const found = find(tasks, selected);
  const empty = {
    empty: true,
    emptyTitle: tasks.length ? "点一张卡" : "这里是详情",
    emptyText: tasks.length
      ? "画布上任意一张卡——map、spec、ticket 或 decision ticket——点一下，它的全部细节就在这一栏。"
      : "The Night 开起来之后，点画布上的卡，它的细节显示在这一栏。",
    repo: payload.repo,
  };
  if (!found) return empty;
  const view = found.type === "ticket" ? ticketView(tasks, found)
    : found.type === "decision" ? decisionView(tasks, found)
      : containerView(tasks, found);
  view.repo = payload.repo;
  return view;
}

function goto(hooks, n) {
  if (n == null) return;
  hooks.onGoto?.(n);
}

function openGithub(view) {
  if (view.gh != null && view.repo) {
    window.open(`https://github.com/${view.repo}/issues/${view.gh}`, "_blank", "noopener,noreferrer");
  }
}

function relRow(hooks, row) {
  const last = row.phase
    ? el("span", {class: `pill ${row.phase}`}, row.phase)
    : el("span", {class: row.state === "not landed" ? "rel-state open" : "rel-state"}, row.state);
  const body = [
    el("span", {class: `lamp ${row.lamp}`}),
    el("span", {class: "rel-num"}, row.num),
    el("span", {class: "rel-title"}, row.title, " ", el("span", {class: "rel-where"}, row.where || "")),
    last,
  ];
  if (row.unknown) return el("div", {class: "rel-static"}, ...body);
  return el("button", {type: "button", class: "rel", onClick: () => goto(hooks, row.n)}, ...body);
}

function section(title, note, ...rows) {
  return el("section", {class: "dp-section"},
    el("div", {class: "dp-section-title"},
      el("span", {}, title), note == null ? null : el("span", {}, note)),
    ...rows);
}

function blockingSection(hooks, view, noneText) {
  return [
    section("Blocked by", view.blockers?.length || null,
      ...(view.blockers || []).map(row => relRow(hooks, row)),
      !view.blockers?.length ? el("p", {class: "rel-none"}, noneText) : null),
    section("Blocking", view.blocks?.length || null,
      ...(view.blocks || []).map(row => relRow(hooks, row)),
      !view.blocks?.length ? el("p", {class: "rel-none"}, "none") : null),
  ];
}

function origin(hooks, view) {
  const parts = [el("span", {}, view.num)];
  for (const link of view.links || []) {
    parts.push(el("span", {}, "·"), el("button", {
      type: "button", class: "dp-link", onClick: () => goto(hooks, link.n),
    }, link.label));
  }
  return el("div", {class: "dp-origin"}, ...parts);
}

function ticketRelation(hooks, row) {
  const last = row.hold ? el("span", {class: "pv-rel-hold"}, "held")
    : row.phase ? el("span", {class: `pill ${row.phase}`}, row.phase)
      : el("span", {class: "pv-rel-s"}, row.state);
  const body = [
    el("span", {class: `lamp ${row.lamp}`}),
    el("span", {class: "pv-rel-n"}, row.num),
    el("span", {class: "pv-rel-t"}, row.title,
      row.where ? " " : null,
      row.where ? el("span", {class: "rel-where"}, row.where) : null),
    last,
  ];
  if (row.unknown) {
    return el("button", {type: "button", class: "pv-rel"}, ...body);
  }
  return el("button", {
    type: "button", class: row.hold ? "pv-rel hold" : "pv-rel",
    onClick: () => goto(hooks, row.n),
  }, ...body);
}

function ticketSection(title, count, ...rows) {
  return el("section", {class: "pv-sec"},
    el("div", {class: "pv-sec-title"}, el("span", {}, title), el("span", {}, count)),
    ...rows);
}

function ticketRuntime(view) {
  if (view.runtime) {
    return el("div", {class: "pv-run"},
      el("div", {class: "pv-run-who"},
        el("span", {class: "pv-run-grade"}, view.runtime.grade || ""),
        view.runtime.model ? el("span", {class: "pv-run-model"}, view.runtime.model) : null),
      view.runtime.rows?.length ? el("div", {class: "pv-run-where"},
        ...view.runtime.rows.flatMap(row => [
          el("span", {class: "pv-run-k"}, row.k),
          el("span", {class: "pv-run-v"}, row.v),
        ])) : null);
  }
  return el("p", {class: "pv-none"}, view.noRunText || "not dispatched yet");
}

function backendDetail(rows) {
  return el("span", {class: "va-x"},
    el("span", {class: "pv-detail"},
      ...rows.flatMap(row => [
        el("span", {class: "pv-detail-k"}, row.k),
        el("span", {class: "pv-detail-v"}, row.v),
      ])));
}

function eventRow(item, key, ui, repaint) {
  const opened = ui.openEvents.has(key);
  return el("button", {type: "button", class: "va-ev", "data-detail-key": key,
    onClick: () => {
      if (opened) ui.openEvents.delete(key); else ui.openEvents.add(key);
      repaint();
    }},
  el("span", {class: "va-t"}, item.time),
  el("span", {class: item.tone === "warn" || item.tone === "needs-you" ? "va-n warn" : "va-n"}, item.name),
  item.hasText ? el("span", {class: "va-x"}, item.text) : null,
  opened ? backendDetail(item.detail) : null);
}

function phaseBlock(block, index, view, ui, repaint) {
  const key = `${view.gh}:b${index}`;
  const defaultOpen = block.openByDefault;
  const opened = ui.toggledBlocks.has(key) ? !defaultOpen : defaultOpen;
  const header = el("button", {type: "button", class: "va-bhead", "data-detail-key": key,
    onClick: () => {
      if (ui.toggledBlocks.has(key)) ui.toggledBlocks.delete(key); else ui.toggledBlocks.add(key);
      repaint();
    }},
  el("span", {class: "va-chev"}, opened ? "▾" : "▸"),
  el("span", {class: `pill ${block.phase}`}, block.phase),
  el("span", {class: "va-bsum"}, opened ? "" : block.summary),
  el("span", {class: "va-btime"}, opened ? block.span : block.from));
  const card = el("div", {class: block.tone === "plain" ? "va-block" : "va-block warn"}, header);
  if (opened) {
    card.append(el("div", {class: "va-body"},
      ...(block.items || []).map((item, itemIndex) =>
        eventRow(item, `${key}:${itemIndex}`, ui, repaint))));
  }
  return card;
}

function ticketCard(hooks, view, ui, repaint) {
  const blocks = view.phaseBlocks || [];
  const parts = [
    el("div", {class: "pv-head"},
      el("span", {class: "pv-eyebrow"}, view.eyebrow || "Ticket"),
      el("button", {type: "button", class: "pv-gh", onClick: () => openGithub(view)}, "GitHub ↗"),
      el("button", {type: "button", class: "pv-close", "aria-label": "关闭详情",
        onClick: () => hooks.onClose?.()}, "×")),
    el("h2", {class: "pv-title"}, view.title),
    el("div", {class: "pv-links"},
      el("span", {}, view.num),
      ...(view.links || []).flatMap(link => [
        el("span", {}, "·"),
        el("button", {type: "button", class: "pv-link", onClick: () => goto(hooks, link.n)}, link.label),
      ])),
    el("div", {class: "va-status"},
      el("span", {class: `lamp big ${view.lamp}`}),
      el("span", {class: `va-word ${view.lamp}`}, view.statusWord),
      el("span", {class: `pill big ${view.phase}`}, view.phase),
      el("span", {class: "va-elapsed"}, view.elapsed || "")),
    ticketRuntime(view),
  ];
  if (view.why?.length) {
    parts.push(el("div", {class: "pv-why"},
      el("span", {class: "pv-why-t"}, "Needs you"),
      ...view.why.map(item => el("span", {}, el("b", {}, item.head), " ", item.body))));
  }
  if (view.blockers?.length) {
    parts.push(ticketSection("Blocked by", view.blockers.length,
      ...heldFirst(view.blockers).map(row => ticketRelation(hooks, row))));
  }
  if (view.blocks?.length) {
    parts.push(ticketSection("Blocking", view.blocks.length,
      ...heldFirst(view.blocks).map(row => ticketRelation(hooks, row))));
  }
  parts.push(ticketSection("Events", view.eventCount ?? (view.rawEvents || []).length,
    view.rawEvents?.length || blocks.length
      ? null : el("p", {class: "pv-none"}, "no events yet"),
    ...(blocks.length ? blocks.map((block, index) => phaseBlock(block, index, view, ui, repaint)) : [])));
  if (view.kids?.length) {
    parts.push(ticketSection("Sub-issues", view.kids.length,
      ...view.kids.map(kid => el("div", {class: "pv-rel"},
        el("span", {class: `lamp ${kid.lamp}`}),
        el("span", {class: "pv-rel-n"}, kid.num),
        el("span", {class: "pv-rel-t"}, kid.title),
        el("span", {class: kid.hot ? "pv-kind hot" : "pv-kind"}, kid.kind)))));
  }
  return el("div", {class: "pv"}, ...parts);
}

function containerBody(hooks, view) {
  const kids = [
    section(view.listTitle, view.listCount,
      el("div", {class: "lamps-count"},
        ...(view.lamps || []).map(item => el("span", {class: "lc-item"},
          el("span", {class: `lamp ${item.lamp}`}), item.word, el("span", {class: "lc-n"}, item.n)))),
      el("div", {class: "phases-count"},
        ...(view.phases || []).map(item => el("span", {class: `pill ${item.phase}`}, item.label)))),
  ];
  if (view.kind === "spec") {
    kids.push(section("By number", null, ...(view.ticketRows || []).map(row => relRow(hooks, row))));
  }
  if (view.kind === "map") {
    kids.push(section("spec", view.specCount, ...(view.specRows || []).map(row => relRow(hooks, row))));
    if (view.decisionRows?.length) {
      kids.push(section("Decision tickets", view.decisionCount,
        ...(view.decisionRows || []).map(row => relRow(hooks, row))));
    }
  }
  return kids;
}

function card(hooks, view) {
  const parts = [
    el("div", {class: "dp-head"},
      el("span", {class: "dp-eyebrow"}, view.eyebrow),
      el("button", {type: "button", class: "dp-close", "aria-label": "关闭详情",
        onClick: () => hooks.onClose?.()}, "×")),
    origin(hooks, view),
    el("h2", {class: "dp-title"}, view.title),
    el("div", {class: "dp-status"},
      el("span", {class: `lamp big ${view.lamp}`}),
      el("span", {class: `status-word ${view.lamp}`}, view.statusWord),
      el("span", {class: "dp-elapsed"}, view.elapsed || "")),
  ];
  if (view.kind === "spec" || view.kind === "map") parts.push(...containerBody(hooks, view));
  if (view.kind === "decision") parts.push(...blockingSection(hooks, view, "none"));
  parts.push(el("button", {
    type: "button", class: "dp-gh",
    onClick: () => openGithub(view),
  }, view.ghLabel));
  return el("div", {class: "dp"}, ...parts);
}

function unmount(host) {
  if (!host) return;
  if (host._detailEsc) document.removeEventListener("keydown", host._detailEsc);
  host._detailEsc = null;
  host._detailRoot = null;
  host._detailUi = null;
  host.replaceChildren();
}

function render(host, view = {}, api, hooks = {}) {
  let root = host._detailRoot;
  if (!root) {
    root = el("aside", {class: "detail board", "aria-label": "详情"});
    root.dataset.screen = "detail";
    host._detailRoot = root;
    host.replaceChildren(root);
  }
  const ui = host._detailUi ||= {openEvents: new Set(), toggledBlocks: new Set()};
  const repaint = () => render(host, view, api, hooks);
  if (!view.empty && view.kind === "ticket") root.replaceChildren(ticketCard(hooks, view, ui, repaint));
  else if (!view.empty && view.kind) root.replaceChildren(card(hooks, view));
  else {
    root.replaceChildren(el("div", {class: "dp-empty"},
      el("p", {class: "dp-empty-title"}, view.emptyTitle || "点一张卡"),
      view.emptyText || "画布上任意一张卡——map、spec、ticket 或 decision ticket——点一下，它的全部细节就在这一栏。"));
  }
  if (host._detailEsc) document.removeEventListener("keydown", host._detailEsc);
  host._detailEsc = event => {
    if (event.key === "Escape" && !view.empty && view.kind) hooks.onClose?.();
  };
  document.addEventListener("keydown", host._detailEsc);
  return root;
}

MMW['detail'] = {fromScene, find, fromBoard, unmount, render};
})();
// ── settings.mjs ──
(function () {
const {CATALOG, LocalConfig, catalogFromPayload, settingsView} = MMW;
const {el, hand} = MMW;

function copy(value) {
  return JSON.parse(JSON.stringify(value));
}

function selectEl(cls, value, disabled, label, opts, onChange) {
  const node = el("select", {
    class: cls, "aria-label": label, disabled: !!disabled,
    onChange: event => onChange(event.target.value),
  }, (opts || []).map(option => el("option", {
    value: option.value, disabled: !!option.disabled, label: option.text,
    selected: option.selected || option.value === value,
  }, option.text)));
  if (value != null) node.value = value;
  return node;
}

function roleFoot(items) {
  if (!items?.length) return null;
  return el("div", {class: "role-foot"}, items.map(item =>
    el("div", {class: "role-bad"}, el("span", {class: "hatch"}), item.text)));
}

function flagsFromErrors(errors) {
  return (errors || []).map(error => {
    const [key, cell] = String(error.cell || "").split(".");
    return {key, cell: cell || key, text: error.reason};
  });
}

function detachEsc(host) {
  if (!host._settingsEsc) return;
  document.removeEventListener("keydown", host._settingsEsc, true);
  host._settingsEsc = null;
}

function unmount(host) {
  detachEsc(host);
  host.replaceChildren();
}

function fromScene(data = {}) {
  const st = copy(data.state.st);
  st.version = st.saved?.version ?? 1;
  st.serverFlags = [];
  return {view: data.vals.v, st, catalog: CATALOG, scan: {}};
}

function fromPayload(payload) {
  const catalog = catalogFromPayload(payload);
  const saved = {runner: payload.runner, rows: copy(payload.rows)};
  return {
    catalog, scan: payload.scan.hosts,
    st: {
      saved, draft: copy(saved),
      scanSource: payload.scan.source,
      scannedAt: payload.scan.scanned_at,
      scanning: Boolean(payload.scan.scanning),
      savedAt: payload.saved_at || null,
      refused: 0, reread: false,
      version: payload.version,
      modifiedAt: payload.modified_at || null,
      serverFlags: [],
    },
  };
}

function viewOf(model) {
  if (model.view) return model.view;
  return settingsView(model.st, model.scan, model.catalog);
}

function saveBody(model) {
  return {
    version: model.st.version,
    runner: model.st.draft.runner,
    rows: model.st.draft.rows,
  };
}

async function readJson(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

function paint(host, model, api, hooks) {
  const v = viewOf(model);
  const close = () => {
    unmount(host);
    hooks.onClose?.();
  };
  const redraw = () => {
    model.view = null;
    paint(host, model, api, hooks);
  };

  const applyScan = body => {
    model.scan = body.hosts;
    model.st.scanSource = body.source;
    model.st.scannedAt = body.scanned_at;
    model.st.scanning = Boolean(body.scanning);
    redraw();
  };

  const rescan = async source => {
    model.st.scanning = true;
    redraw();
    const response = await hand(() => api.scanSettings({source}));
    if (!response?.ok) {
      model.st.scanning = false;
      redraw();
      return;
    }
    const body = await readJson(response);
    if (!body.hosts) {
      model.st.scanning = false;
      redraw();
      return;
    }
    applyScan(body);
  };

  const setCell = (key, cell, value) => {
    const previous = {runner: model.st.draft.runner};
    LocalConfig.setCell(model.scan, model.st.draft, key, cell, value);
    model.st.savedAt = null;
    model.st.serverFlags = [];
    if (key === "runner" && LocalConfig.needsRescan(previous, model.st.draft)) {
      void rescan(LocalConfig.source(model.st.draft));
      return;
    }
    redraw();
  };

  const save = async () => {
    const response = await hand(() => api.saveSettings(saveBody(model)));
    if (!response) return;
    const body = await readJson(response);
    if (response.status === 409) {
      model.st.refused = LocalConfig.changes(model.st.draft, model.st.saved).length || 1;
      model.st.modifiedAt = body.modified_at;
      redraw();
      return;
    }
    if (response.status === 422) {
      model.st.serverFlags = flagsFromErrors(body.errors);
      redraw();
      return;
    }
    if (!response.ok) return;
    model.st.saved = copy(model.st.draft);
    model.st.version = body.version ?? model.st.version;
    model.st.savedAt = body.saved_at;
    model.st.refused = 0;
    model.st.serverFlags = [];
    redraw();
  };

  const reread = async () => {
    const response = await hand(() => api.settings());
    if (!response?.ok) return;
    const body = await readJson(response);
    if (body.runner == null) return;
    const next = fromPayload(body);
    Object.assign(model, next);
    model.st.reread = true;
    redraw();
  };

  const root = el("div", {
    class: "scrim board",
    onClick: event => {
      if (event.target === event.currentTarget && !v.changed) close();
    },
  });
  root.dataset.screen = "settings";

  const sheet = el("div", {class: "sheet", role: "dialog", "aria-modal": "true", "aria-label": "本机配置"});
  sheet.append(
    el("div", {class: "sheet-head"},
      el("div", {class: "sheet-head-text"},
        el("span", {class: "dp-eyebrow"}, "本机配置"),
        el("h2", {class: "sheet-title"}, "这台机器上，每个 agent 跑在哪"),
        el("p", {class: "sheet-sub"},
          "下拉菜单里的选项，是 MMW 刚问过这台机器上的 host 得到的，问的地方和 ",
          el("span", {class: "sheet-code"}, "start"),
          " 起 session 时问的是同一处。这里就是 MMW 管这件事的唯一地方，保存在本机的 ",
          el("span", {class: "sheet-code"}, v.store),
          "；这一页不写 GitHub。"),
      ),
      el("button", {type: "button", class: "dp-close", "aria-label": "关闭本机配置", onClick: close}, "×"),
    ),
  );

  const body = el("div", {class: "sheet-body"});
  if (v.refused) {
    body.append(el("div", {class: "refused", role: "alert"},
      el("p", {class: "refused-text"}, el("b", {}, "没有保存。"), v.refusedText),
      el("button", {type: "button", class: "btn", onClick: reread}, "重新读取")));
  }
  body.append(
    el("section", {class: "set-block"},
      el("div", {class: "set-block-head"},
        el("span", {class: "dp-section-title"}, "本机的 host"),
        el("span", {class: "scan"},
          v.scanning ? [el("span", {class: "spin"}), v.scanningText] : [
            v.scannedText,
            el("button", {type: "button", class: "linkbtn",
              onClick: () => void rescan(LocalConfig.source(model.st.draft))},
              "重新扫描"),
          ],
        ),
      ),
      el("div", {class: "hostscan"}, (v.chips || []).map(chip =>
        el("span", {class: chip.cls}, el("span", {class: "hs-name"}, chip.host), chip.what))),
    ),
    el("section", {class: "set-block ruled"},
      el("div", {class: "runner-row"},
        el("div", {class: "role-name"},
          el("span", {class: "role-agent"}, "runner"),
          el("span", {class: "role-what"}, "用什么起 session")),
        selectEl(v.runnerCls, v.runner, v.runnerOff, "runner", v.runnerOpts,
          value => setCell("runner", "runner", value)),
        v.runnerHasBad ? roleFoot(v.runnerBads) : null,
      ),
      el("p", {class: "set-note"},
        "环境变量 ", el("span", {class: "sheet-code"}, "MMW_RUNNER"),
        " 设了时，它优先于这一格。「按所在环境判断」让 ",
        el("span", {class: "sheet-code"}, "start"),
        " 看自己跑在哪个 runner 里，判断不出时用 orca。runner 是 paseo 时，",
        el("span", {class: "sheet-code"}, "start"),
        " 向 Paseo 要 model，所以换到 paseo 或从 paseo 换走，选项会重新扫描。"),
    ),
    el("section", {class: "set-block ruled"},
      el("div", {class: "set-block-head"},
        el("span", {class: "dp-section-title"}, "一个 agent 一行")),
      el("div", {class: "roles"},
        el("div", {class: "roles-head"},
          el("span", {}, "agent"), el("span", {}, "host"),
          el("span", {}, "model"), el("span", {}, "effort")),
        (v.rows || []).map(row => el("div", {class: "role"},
          el("div", {class: "role-name"},
            el("span", {class: "role-agent"}, row.agent),
            el("span", {class: "role-what"}, row.what)),
          selectEl(row.hostCls, row.host, row.hostOff, row.hostLabel, row.hostOpts,
            value => setCell(row.agent, "host", value)),
          selectEl(row.modelCls, row.model, row.modelOff, row.modelLabel, row.modelOpts,
            value => setCell(row.agent, "model", value)),
          selectEl(row.effortCls, row.effort, row.effortOff, row.effortLabel, row.effortOpts,
            value => setCell(row.agent, "effort", value)),
          row.hasBad ? roleFoot(row.bads) : null,
        )),
      ),
      el("p", {class: "set-note"},
        "一台新机器第一次安装时，这里填的是 MMW 自带的初始值；之后只按这里选的跑，MMW 更新不会改它。"),
    ),
  );
  sheet.append(body);
  sheet.append(el("div", {class: "sheet-foot"},
    el("div", {class: "foot-status", "aria-live": "polite"},
      el("span", {class: "foot-strong"}, v.hatch ? el("span", {class: "hatch"}) : null, v.strong),
      el("span", {class: "foot-quiet"}, v.quiet)),
    el("div", {class: "foot-actions"},
      el("button", {type: "button", class: "btn", onClick: close}, v.closeLabel),
      el("button", {
        type: "button", class: "btn primary", disabled: !!v.saveOff, onClick: save,
      }, "保存")),
  ));
  root.append(sheet);

  detachEsc(host);
  host._settingsEsc = event => {
    if (event.key !== "Escape") return;
    event.preventDefault();
    event.stopImmediatePropagation();
    close();
  };
  document.addEventListener("keydown", host._settingsEsc, true);
  host.replaceChildren(root);
  return root;
}

function render(host, model, api, hooks = {}) {
  return paint(host, model, api, hooks);
}

MMW['settings'] = {unmount, fromScene, fromPayload, render};
})();
})();
