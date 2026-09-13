import {Board, LAMP_WORD, PHASES, eventBlocks, blockSummary} from "./board-logic.mjs";
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
  const tone = item.tone
    || ((item.nameCls || "").includes("warn") ? "warn" : "plain");
  const detail = (item.detail || []).map(row => Array.isArray(row)
    ? {k: row[0], v: row[1]} : {k: row.k, v: row.v});
  return {
    event: item.event, time: item.time, name: item.name, text: item.text || "",
    hasText: item.hasText ?? Boolean(item.text), tone, detail,
  };
}

export function fromScene(data = {}) {
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

function relatedRow(tasks, n, upstream, thisTicket, hereSpec) {
  const row = relRowFromBoard(tasks, n, upstream ? "blocker" : "blocked", hereSpec);
  const other = find(tasks, n);
  const ticket = other?.type === "ticket" ? other.ref : null;
  const hold = Boolean(ticket) && (upstream ? !Board.released(ticket) : !Board.released(thisTicket));
  return {...row, hold};
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
  const blockers = heldFirst(ticket.blocked.map(n => relatedRow(tasks, n, true, ticket, found.spec.n)));
  const blocking = heldFirst(found.spec.tickets
    .filter(item => item.blocked.includes(ticket.n))
    .map(item => relatedRow(tasks, item.n, false, ticket, found.spec.n)));
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
    el("span", {class: "pv-rel-t"}, row.title),
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
  item.hasText || item.text ? el("span", {class: "va-x"}, item.text) : null,
  opened ? backendDetail(item.detail || []) : null);
}

function phaseBlock(block, index, view, ui, repaint) {
  const key = `${view.gh}:b${index}`;
  const defaultOpen = block.openByDefault ?? (index === (view.phaseBlocks || []).length - 1
    || block.tone !== "plain");
  const opened = ui.toggledBlocks.has(key) ? !defaultOpen : defaultOpen;
  const header = el("button", {type: "button", class: "va-bhead", "data-detail-key": key,
    onClick: () => {
      if (ui.toggledBlocks.has(key)) ui.toggledBlocks.delete(key); else ui.toggledBlocks.add(key);
      repaint();
    }},
  el("span", {class: "va-chev"}, opened ? "▾" : "▸"),
  el("span", {class: `pill ${block.phase}`}, block.phase),
  el("span", {class: "va-bsum"}, opened ? "" : (block.summary || blockSummary(block))),
  el("span", {class: "va-btime"}, opened ? (block.span || block.from) : block.from));
  const card = el("div", {class: block.tone === "plain" ? "va-block" : "va-block warn"}, header);
  if (opened) {
    card.append(el("div", {class: "va-body"},
      ...(block.items || []).map((item, itemIndex) =>
        eventRow(item, `${key}:${itemIndex}`, ui, repaint))));
  }
  return card;
}

function ticketCard(hooks, view, ui, repaint) {
  const blocks = view.phaseBlocks?.length ? view.phaseBlocks : phaseBlocksFrom(view.rawEvents || []);
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
