import {Board, LAMP_WORD, PHASES} from "./board-logic.mjs";
import {groupEventBlocks} from "./event-history.mjs";
import {el} from "./shared.mjs";

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

function relFrom(row) {
  return {
    n: row.n,
    num: row.num,
    title: row.title,
    where: row.where || "",
    lamp: lampFrom(row.lampCls),
    state: row.state,
    phase: row.phase,
    hold: Boolean(row.hold),
    unknown: Boolean(row.unknown || row.known === false),
  };
}

function kidFrom(row) {
  return {
    num: row.num, kind: row.kind, title: row.title, to: row.to,
    lamp: lampFrom(row.lampCls), goto: row.goto, hasGoto: Boolean(row.hasGoto),
    orange: (row.toCls || "").includes("orange"),
  };
}

function pathFrom(phases) {
  return (phases || []).map(phase => ({
    name: phase.name,
    done: (phase.cls || "").includes("done"),
    now: /now-/.test(phase.cls || ""),
    sep: Boolean(phase.sep),
  }));
}

const firstRows = (...candidates) => candidates.find(rows => Array.isArray(rows) && rows.length) || [];

export function fromScene(data = {}) {
  const vals = data.vals || {};
  const d = vals.d || {};
  const hasCard = d.hasCard ?? Boolean(d.isTicket || d.isMap || d.isSpec || d.isDecision || d.isCardNotTicket);
  if (!hasCard) {
    return {
      empty: true,
      emptyTitle: vals.emptyTitle || "点一张卡",
      emptyText: vals.emptyText || "画布上任意一张卡——map、spec、ticket 或 decision ticket——点一下，它的全部细节就在这一栏。",
    };
  }
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
    hint: d.hint,
    path: pathFrom(d.path),
    why: d.why || [],
    facts: d.facts || [],
    sessions: (d.sessions || []).map(session => ({
      ...session, live: (session.stateCls || "").includes("live"),
    })),
    closeout: d.closeout
      ? {from: d.closeoutFrom, fromLabel: d.closeoutFromLabel, child: d.closeoutChild}
      : null,
    links: vals.links || d.links || [],
    blockers: firstRows(vals.blockedBy, vals.blockers, d.blockedBy, d.blockers).map(relFrom),
    blocks: firstRows(vals.blocking, vals.blocks, d.blocking, d.blocks).map(relFrom),
    kids: firstRows(vals.kids, d.kids).map(kidFrom),
    rawEvents: vals.rawEvents || d.rawEvents || (d.events || []).map(event => ({
      event: event.event || event.name, time: event.time, line: event.line,
      payload: event.payload || {},
    })),
    phaseBlocks: (vals.phaseBlocks || d.phaseBlocks || []).map(block => ({
      ...block,
      items: (block.items || []).map(item => ({
        ...item,
        tone: item.tone || ((item.nameCls || "").includes("warn") ? "warn" : "plain"),
      })),
    })),
    runtime: d.hasRun ? {grade: d.runGrade, model: d.runModel, rows: d.runRows || []} : null,
    runtimeNote: vals.runtimeNote || "",
    hasWorker: Boolean(d.hasWorker ?? d.hasRun),
    gh: d.gh,
    ghLabel: d.ghLabel,
    listTitle: d.listTitle,
    listCount: d.listCount,
    lamps: (d.lamps || []).map(item => ({lamp: lampFrom(item.cls), word: item.word, n: item.n})),
    phases: (d.phases || []).map(item => ({
      phase: (item.cls || "").replace(/^pill\s+/, ""), label: item.label,
    })),
    ticketRows: (vals.ticketRows || []).map(relFrom),
    specRows: (vals.specRows || []).map(relFrom),
    decisionRows: (vals.decisionRows || []).map(relFrom),
    specCount: d.specCount,
    decisionCount: d.decisionCount,
  };
}

export function find(tasks, n) {
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

function relRowFromBoard(tasks, n, role, hereSpec) {
  const found = find(tasks, n);
  if (!found) {
    return {n, num: `#${n}`, lamp: "none", title: "不在这棵树里，读不到它的状态",
      where: "", state: "unknown", unknown: true};
  }
  let lamp, state, phase;
  if (found.type === "ticket") {
    lamp = Board.lamp(found.ref);
    phase = Board.phase(found.ref);
    state = found.ref.fold.landed ? "landed"
      : role !== "blocker" ? LAMP_WORD[lamp]
        : Board.released(found.ref) ? "closed unpassed · released" : "not landed";
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
    state, phase,
  };
}

function kidTo(child) {
  if (child.resolution === "fixed") return {to: "fixed"};
  if (child.resolution === "stale") return {to: "stale"};
  if (child.resolution === "became-ticket") {
    return {to: `became #${child.ticket}`, goto: child.ticket, hasGoto: true};
  }
  if (NEEDS_YOU.has(child.kind)) return {to: "needs you", orange: true};
  return {to: child.kind === "deferred" ? "deferred" : "for the closing pass"};
}

function ticketView(tasks, found) {
  const ticket = found.ref, fold = ticket.fold, lamp = Board.lamp(ticket), phase = Board.phase(ticket);
  const stopped = Board.handedBack(ticket) || Board.bounce(ticket)
    || (fold.sessions.some(session => session.live) && Board.stoppedByFault(ticket));
  const index = PHASES.indexOf(phase);
  const worker = fold.worker;
  const blocks = found.spec.tickets.filter(item => item.blocked.includes(ticket.n)).map(item => item.n);
  const why = Board.why(ticket).map(item => item.child
    ? {head: `#${item.child} ${item.kind}`, body: `${item.title}。${item.text}`}
    : {head: "", body: item.text});
  return {
    empty: false, kind: "ticket", eyebrow: "Ticket", num: `#${ticket.n}`,
    repo: undefined,
    links: [{label: `spec #${found.spec.n}`, n: found.spec.n}, {label: `map #${found.task.n}`, n: found.task.n}],
    closeout: ticket.closeout
      ? {from: ticket.closeout.from, fromLabel: `#${ticket.closeout.from}`, child: `的 finding #${ticket.closeout.child}`}
      : null,
    title: ticket.title, lamp, statusWord: LAMP_WORD[lamp], elapsed: Board.elapsed(ticket),
    phase, hint: phase === "landed" ? "done" : stopped ? "stopped here" : phase === "queued" ? "not started" : "here now",
    path: PHASES.map((name, i) => ({name, done: i < index, now: i === index, sep: i < PHASES.length - 1})),
    why, facts: Board.facts(ticket).map(([k, v]) => ({k, v})),
    hasWorker: Boolean(worker), runtimeNote: worker ? "from worker.started" : "",
    sessions: fold.sessions.map(session => ({
      kind: session.kind, what: `${session.host} · ${session.model} · ${session.effort}`,
      state: Board.sessionState(session, ticket),
      live: session.live && !Board.stoppedByFault(ticket),
    })),
    blockers: ticket.blocked.map(n => {
      const row = relRowFromBoard(tasks, n, "blocker", found.spec.n);
      const other = find(tasks, n);
      return {...row, hold: other?.type === "ticket" && !Board.released(other.ref)};
    }),
    blocks: blocks.map(n => ({
      ...relRowFromBoard(tasks, n, "blocked", found.spec.n),
      hold: !Board.released(ticket),
    })),
    kids: Object.values(fold.children).map(child => {
      const to = kidTo(child);
      return {
        num: `#${child.child}`, kind: child.kind, title: child.title, to: to.to,
        goto: to.goto, hasGoto: Boolean(to.hasGoto), orange: Boolean(to.orange),
        lamp: child.resolution ? "ink" : NEEDS_YOU.has(child.kind) ? "orange" : "hollow",
      };
    }),
    rawEvents: ticket.events,
    gh: ticket.n, ghLabel: `在 GitHub 打开 #${ticket.n} ↗`,
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
    why: [], facts: [], sessions: [], kids: [], blockers: [], blocks: [],
    closeout: null, hasWorker: false, runtimeNote: "",
  };
}

function decisionView(tasks, found) {
  const decision = found.ref, lamp = Board.decisionLamp(decision);
  const blocks = found.task.decisions.filter(item => item.blocked.includes(decision.n)).map(item => item.n);
  return {
    empty: false, kind: "decision", eyebrow: `Decision ticket · ${decision.kind}`, num: `#${decision.n}`,
    links: [{label: `map #${found.task.n}`, n: found.task.n}],
    title: decision.title, lamp,
    statusWord: decision.state === "closed" ? "settled" : "open",
    elapsed: "",
    blockers: decision.blocked.map(n => relRowFromBoard(tasks, n, "decision", null)),
    blocks: blocks.map(n => relRowFromBoard(tasks, n, "decision", null)),
    gh: decision.n, ghLabel: `在 GitHub 打开 #${decision.n} ↗`,
    why: [], facts: [], sessions: [], kids: [], closeout: null,
    hasWorker: false, runtimeNote: "", path: [],
  };
}

export function fromBoard(payload = {}, selected) {
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

// GitHub's own two names for the two directions of a blocking link: its API calls the
// connections `blockedBy` and `blocking`, and the issue page heads them the same way.
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

const EVENT_WEIGHT = {
  "ticket.refused": 3, "ticket.returned": 3, "ticket.bounced": 3, "ticket.regressed": 3,
  "child.opened": 3, "ticket.checked": 2, "verifier.passed": 2, "verifier.failed": 2,
  "reviewer.reported": 2, "ticket.landed": 2, "ticket.passed": 2, "worker.lost": 2,
  "ticket.released": 1, "worker.started": 1,
};

const duration = view => String(view.elapsed || "")
  .replace(/^\D+/, "").replace(/(\d+) 分钟/, "$1m").replace(/ 后.*$/, "");

function openGithub(view) {
  if (view.gh != null && view.repo) {
    window.open(`https://github.com/${view.repo}/issues/${view.gh}`, "_blank", "noopener,noreferrer");
  }
}

function ticketOrigin(hooks, view) {
  const parts = [el("span", {}, view.num)];
  for (const link of view.links || []) {
    parts.push(el("span", {}, "·"), el("button", {
      type: "button", class: "ticket-detail-link", onClick: () => goto(hooks, link.n),
    }, link.label));
  }
  return el("div", {class: "ticket-detail-origin"}, ...parts);
}

function ticketRuntime(view) {
  if (view.runtime) {
    return el("div", {class: "ticket-runtime"},
      el("div", {class: "ticket-runtime-who"},
        el("span", {class: "ticket-runtime-grade"}, view.runtime.grade || "worker"),
        view.runtime.model ? el("span", {class: "ticket-runtime-model"}, view.runtime.model) : null),
      view.runtime.rows?.length ? el("div", {class: "ticket-runtime-where"},
        ...view.runtime.rows.flatMap(row => [
          el("span", {class: "ticket-runtime-key"}, row.k),
          el("span", {class: "ticket-runtime-value"}, row.v),
        ])) : null);
  }
  const started = [...(view.rawEvents || [])].reverse().find(event => event.event === "worker.started");
  if (!view.hasWorker || !started) {
    return el("p", {class: "ticket-detail-none"}, view.phase === "landed"
      ? "closed without a run" : "not dispatched yet");
  }
  const payload = started.payload || {};
  const worktree = String(payload.worktree || "").split("/.worktrees/")[1];
  const slot = [...(view.rawEvents || [])].reverse()
    .find(event => event.event === "ticket.checked" && event.payload?.slot != null)?.payload.slot;
  const rows = [
    ["ticket branch", payload.branch], ["base branch", payload.into],
    ["worktree", worktree ? `…/.worktrees/${worktree}` : payload.worktree],
    ["machine", payload.machine], ...(slot != null ? [["slot", String(slot)]] : []),
  ].filter(([, value]) => value);
  return el("div", {class: "ticket-runtime"},
    el("div", {class: "ticket-runtime-who"},
      el("span", {class: "ticket-runtime-grade"}, payload.grade || "worker"),
      payload.model ? el("span", {class: "ticket-runtime-model"},
        `${payload.host} · ${payload.model} · ${payload.effort}`) : null),
    rows.length ? el("div", {class: "ticket-runtime-where"},
      ...rows.flatMap(([key, value]) => [
        el("span", {class: "ticket-runtime-key"}, key),
        el("span", {class: "ticket-runtime-value"}, value),
      ])) : null);
}

function ticketRelation(hooks, row) {
  const body = [
    el("span", {class: `lamp ${row.lamp}`}), el("span", {class: "ticket-rel-num"}, row.num),
    el("span", {class: "ticket-rel-title"}, row.title),
    row.hold ? el("span", {class: "ticket-rel-hold"}, "held")
      : row.phase ? el("span", {class: `pill ${row.phase}`}, row.phase)
        : el("span", {class: "ticket-rel-state"}, row.state),
  ];
  if (row.unknown) return el("div", {class: "ticket-rel"}, ...body);
  return el("button", {type: "button", class: `ticket-rel${row.hold ? " hold" : ""}`,
    onClick: () => goto(hooks, row.n)}, ...body);
}

function ticketSection(title, count, ...rows) {
  return el("section", {class: "ticket-section"},
    el("div", {class: "ticket-section-title"}, el("span", {}, title), el("span", {}, count)), ...rows);
}

function ticketBlocking(hooks, view) {
  const heldFirst = rows => [...rows].sort((one, two) => Number(two.hold) - Number(one.hold));
  return [["Blocked by", view.blockers || []], ["Blocking", view.blocks || []]]
    .filter(([, rows]) => rows.length)
    .map(([title, rows]) => ticketSection(title, rows.length,
      ...heldFirst(rows).map(row => ticketRelation(hooks, row))));
}

function backendDetail(rows) {
  return el("span", {class: "event-details"},
    ...rows.flatMap(([key, value]) => [el("b", {}, key), el("span", {}, value)]));
}

function eventRow(item, key, ui, repaint) {
  const opened = ui.openEvents.has(key);
  const row = el("button", {type: "button", class: "phase-event", "data-detail-key": key,
    onClick: () => {
      if (opened) ui.openEvents.delete(key); else ui.openEvents.add(key);
      repaint(key);
    }},
  el("span", {class: "phase-event-time"}, item.time),
  el("span", {class: `phase-event-name${item.tone === "warn" || item.tone === "needs-you" ? " warn" : ""}`}, item.name),
  item.text ? el("span", {class: "phase-event-text"}, item.text) : null,
  opened ? backendDetail(item.detail) : null);
  return row;
}

function blockSummary(block) {
  if (block.summary) return block.summary;
  const best = block.items.reduce((pick, item) =>
    (EVENT_WEIGHT[item.event] || 0) >= (EVENT_WEIGHT[pick.event] || 0) ? item : pick, block.items[0]);
  return best.text ? `${best.name} — ${best.text}` : best.name;
}

function phaseBlock(block, index, total, view, ui, repaint) {
  const key = `${view.gh}:block:${index}`;
  const defaultOpen = block.openByDefault ?? (index === total - 1 || block.tone !== "plain");
  const opened = ui.toggledBlocks.has(key) ? !defaultOpen : defaultOpen;
  const header = el("button", {type: "button", class: "phase-block-head", "data-detail-key": key,
    onClick: () => {
      if (ui.toggledBlocks.has(key)) ui.toggledBlocks.delete(key); else ui.toggledBlocks.add(key);
      repaint(key);
    }},
  el("span", {class: "phase-block-chevron"}, opened ? "▾" : "▸"),
  el("span", {class: `pill ${block.phase}`}, block.phase),
  el("span", {class: "phase-block-summary"}, opened ? "" : blockSummary(block)),
  el("span", {class: "phase-block-time"}, opened
    ? (block.span || (block.from !== block.to ? `${block.from}–${block.to}` : block.from))
    : block.from));
  const card = el("div", {class: `phase-block${block.tone === "plain" ? "" : " warn"}`}, header);
  if (opened) card.append(el("div", {class: "phase-block-body"},
    ...block.items.map((item, itemIndex) => eventRow(item, `${key}:event:${itemIndex}`, ui, repaint))));
  return card;
}

function ticketCard(hooks, view, ui, repaint) {
  const blocks = view.phaseBlocks?.length ? view.phaseBlocks : groupEventBlocks(view.rawEvents || []);
  const parts = [
    el("div", {class: "ticket-detail-head"},
      el("span", {class: "ticket-detail-eyebrow"}, "Ticket"),
      el("button", {type: "button", class: "ticket-detail-github", onClick: () => openGithub(view)}, "GitHub ↗"),
      el("button", {type: "button", class: "ticket-detail-close", "aria-label": "关闭详情",
        onClick: () => hooks.onClose?.()}, "×")),
    el("h2", {class: "ticket-detail-title"}, view.title),
    ticketOrigin(hooks, view),
    el("div", {class: "ticket-detail-status"},
      el("span", {class: `lamp big ${view.lamp}`}),
      el("span", {class: `ticket-detail-status-word ${view.lamp}`}, view.statusWord),
      el("span", {class: `pill big ${view.phase}`}, view.phase),
      el("span", {class: "ticket-detail-elapsed"}, duration(view))),
    ticketRuntime(view),
  ];
  if (view.why?.length) {
    parts.push(el("div", {class: "ticket-detail-why"},
      el("span", {class: "ticket-detail-why-title"}, "Needs you"),
      ...view.why.map(item => el("span", {}, el("b", {}, item.head), " ", item.body))));
  }
  parts.push(...ticketBlocking(hooks, view));
  parts.push(ticketSection("Events", (view.rawEvents || []).length,
    ...(blocks.length ? blocks.map((block, index) => phaseBlock(block, index, blocks.length, view, ui, repaint))
      : [el("p", {class: "ticket-detail-none"}, "no events yet")])));
  if (view.kids?.length) {
    parts.push(ticketSection("Sub-issues", view.kids.length,
      ...view.kids.map(kid => el("div", {class: "ticket-rel"},
        el("span", {class: `lamp ${kid.lamp}`}), el("span", {class: "ticket-rel-num"}, kid.num),
        el("span", {class: "ticket-rel-title"}, kid.title),
        el("span", {class: `ticket-kind${NEEDS_YOU.has(kid.kind) ? " hot" : ""}`}, kid.kind)))));
  }
  return el("div", {class: "ticket-detail"}, ...parts);
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
  ];
  if (view.closeout) {
    parts.push(el("div", {class: "dp-closeout"},
      el("span", {class: "dp-closeout-bar"}),
      "opened in the closing pass · from",
      el("button", {type: "button", class: "dp-link",
        onClick: () => goto(hooks, view.closeout.from)}, view.closeout.fromLabel),
      view.closeout.child));
  }
  parts.push(
    el("h2", {class: "dp-title"}, view.title),
    el("div", {class: "dp-status"},
      el("span", {class: `lamp big ${view.lamp}`}),
      el("span", {class: `status-word ${view.lamp}`}, view.statusWord),
      el("span", {class: "dp-elapsed"}, view.elapsed || "")),
  );
  if (view.kind === "spec" || view.kind === "map") parts.push(...containerBody(hooks, view));
  if (view.kind === "decision") parts.push(...blockingSection(hooks, view, "none"));
  parts.push(el("button", {
    type: "button", class: "dp-gh",
    onClick: () => {
      if (view.gh != null && view.repo) {
        window.open(`https://github.com/${view.repo}/issues/${view.gh}`, "_blank", "noopener,noreferrer");
      }
    },
  }, view.ghLabel));
  return el("div", {class: "dp"}, ...parts);
}

export function unmount(host) {
  if (!host) return;
  if (host._detailEsc) document.removeEventListener("keydown", host._detailEsc);
  host._detailEsc = null;
  host._detailRoot = null;
  host._detailUi = null;
  host.replaceChildren();
}

export function render(host, view = {}, api, hooks = {}) {
  let root = host._detailRoot;
  if (!root) {
    root = el("aside", {class: "detail board", "aria-label": "detail"});
    root.dataset.screen = "detail";
    host._detailRoot = root;
    host.replaceChildren(root);
  }
  const ui = host._detailUi ||= {openEvents: new Set(), toggledBlocks: new Set()};
  const repaint = focusKey => {
    render(host, view, api, hooks);
    if (focusKey && typeof root.querySelector === "function") {
      root.querySelector(`[data-detail-key="${CSS.escape(focusKey)}"]`)?.focus({preventScroll: true});
    }
  };
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
