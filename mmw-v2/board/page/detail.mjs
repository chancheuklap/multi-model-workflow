import {Board, LAMP_WORD, PHASES, eventBlocks, blockSummary} from "./board-logic.mjs";
import {el, minutes} from "./shared.mjs";

const NEEDS_YOU = new Set(["decision", "fault", "contract"]);
const duration = value => value < 60
  ? `${value}m`
  : `${Math.floor(value / 60)}h${String(value % 60).padStart(2, "0")}m`;

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

function elapsedAt(ticket, now) {
  if (now == null) return Board.elapsed(ticket);
  const first = ticket.fold.sessions[0]?.started_at;
  if (!first) return "";
  const landed = ticket.events.find(event => event.event === "ticket.landed");
  if (ticket.fold.landed && landed) return duration(minutes(first, landed.at));
  if (Board.handedBack(ticket)) return duration(minutes(first, ticket.fold.outcome.at));
  const bounce = Board.bounce(ticket);
  if (bounce) return duration(minutes(first, bounce.at));
  return duration(minutes(first, now));
}

function ticketView(tasks, found, now) {
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
    title: ticket.title, lamp, statusWord: LAMP_WORD[lamp], elapsed: elapsedAt(ticket, now),
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

export function fromBoard(payload = {}, selected, now) {
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
  const view = found.type === "ticket" ? ticketView(tasks, found, now)
    : found.type === "decision" ? decisionView(tasks, found)
      : containerView(tasks, found);
  view.repo = payload.repo;
  return view;
}

function goto(hooks, n, ui) {
  if (n == null) return;
  // ui is the control's data-ui id. The board follows n; a story uses ui to
  // tell which screen-contract row fired.
  hooks.onGoto?.(n, ui);
}

function openGithub(view) {
  if (view.gh != null && view.repo) {
    window.open(`https://github.com/${view.repo}/issues/${view.gh}`, "_blank", "noopener,noreferrer");
  }
}

function tailOf(row) {
  if (row.hold) return {cls: "row-state hold", text: "held", ui: "hold"};
  if (row.phase) return {cls: `pill ${row.phase}`, text: row.phase, ui: "phase"};
  return {
    cls: row.state === "not landed" ? "row-state open" : "row-state",
    text: row.state ?? "",
    ui: "state",
  };
}

function relation(hooks, row, ui, {where, holdClass}) {
  const last = tailOf(row);
  const whereNode = where === false ? null : el("span", {
    class: "meta", ...(where === "ui" ? {"data-ui": `${ui}.where`} : {}),
  }, row.where || "");
  const body = [
    el("span", {class: `lamp ${row.lamp || "none"}`, "data-ui": `${ui}.lamp`}),
    el("span", {class: "row-num", "data-ui": `${ui}.number`}, row.num),
    el("span", {class: "row-title", "data-ui": `${ui}.title`}, row.title,
      whereNode ? " " : null, whereNode),
    el("span", {class: last.cls, "data-ui": `${ui}.${last.ui}`}, last.text),
  ];
  return el("button", {
    type: "button", class: holdClass && row.hold ? "row hold" : "row", "data-ui": ui,
    onClick: row.unknown ? null : () => goto(hooks, row.n, ui),
  }, ...body);
}

function section(ui, title, note, ...rows) {
  return el("section", {class: "section", "data-ui": ui},
    el("div", {class: "eyebrow spread"},
      el("span", {"data-ui": `${ui}.title`}, title),
      note == null ? null : el("span", {"data-ui": `${ui}.count`}, String(note))),
    ...rows);
}

function blockingSection(hooks, view) {
  const blockers = view.blockers || [];
  const blocks = view.blocks || [];
  const opts = {where: false, holdClass: false};
  return [
    section("详情.blocked-by", "Blocked by", blockers.length,
      ...blockers.map(row => relation(hooks, row, "详情.blocker", opts)),
      blockers.length ? null : el("p", {class: "row-none"}, "none")),
    section("详情.blocking", "Blocking", blocks.length,
      ...blocks.map(row => relation(hooks, row, "详情.blocks", opts)),
      blocks.length ? null : el("p", {class: "row-none"}, "none")),
  ];
}

function origin(hooks, view) {
  const parts = [el("span", {"data-ui": "详情.origin.number"}, view.num || "")];
  for (const link of view.links || []) {
    parts.push(el("span", {}, "·"), " ", el("button", {
      type: "button", class: "link", "data-ui": "详情.origin.link",
      onClick: () => goto(hooks, link.n, "详情.origin.link"),
    }, link.label));
  }
  return el("div", {class: "links", "data-ui": "详情.origin"}, ...parts);
}

function ticketRuntime(view) {
  if (view.runtime) {
    return el("div", {class: "kv", "data-ui": "详情.runtime"},
      el("div", {class: "kv-who"},
        el("span", {class: "kv-title", "data-ui": "详情.runtime.grade"}, view.runtime.grade || ""),
        el("span", {class: "kv-sub", "data-ui": "详情.runtime.model"}, view.runtime.model || "")),
      el("div", {class: "kv-grid ruled"},
        ...(view.runtime.rows || []).flatMap(row => [
          el("span", {class: "kv-k", "data-ui": "详情.runtime.key"}, row.k),
          el("span", {class: "kv-v", "data-ui": "详情.runtime.value"}, row.v),
        ])));
  }
  return el("p", {class: "row-none", "data-ui": "详情.runtime"},
    view.noRunText || "not dispatched yet");
}

function backendDetail(rows) {
  return el("span", {class: "log-x"},
    el("span", {class: "kv kv-grid", "data-ui": "详情.event.detail"},
      ...rows.flatMap(row => [
        el("span", {class: "kv-k"}, row.k),
        el("span", {class: "kv-v"}, row.v),
      ])));
}

function eventRow(item, key, ui, repaint) {
  const opened = ui.openEvents.has(key);
  return el("button", {type: "button", class: "log-ev", "data-detail-key": key,
    onClick: () => {
      if (opened) ui.openEvents.delete(key); else ui.openEvents.add(key);
      repaint();
      ui.hooks.onEventToggle?.(!opened);
    }, "data-ui": "详情.event"},
  el("span", {class: "log-t", "data-ui": "详情.event.time"}, item.time),
  el("span", {class: item.tone === "warn" || item.tone === "needs-you" ? "log-n warn" : "log-n",
    "data-ui": "详情.event.name"}, item.name),
  item.hasText ? el("span", {class: "log-x", "data-ui": "详情.event.text"}, item.text) : null,
  opened ? backendDetail(item.detail) : null);
}

function phaseBlock(block, index, view, ui, repaint) {
  const key = `${view.gh}:b${index}`;
  const defaultOpen = block.openByDefault;
  const opened = ui.toggledBlocks.has(key) ? !defaultOpen : defaultOpen;
  const header = el("button", {type: "button", class: "log-head", "data-detail-key": key,
    "data-ui": "详情.event-block.toggle",
    onClick: () => {
      if (ui.toggledBlocks.has(key)) ui.toggledBlocks.delete(key); else ui.toggledBlocks.add(key);
      repaint();
      ui.hooks.onEventBlockToggle?.(!opened);
    }},
  el("span", {class: "log-chev", "data-ui": "详情.event-block.chev"}, opened ? "▾" : "▸"),
  el("span", {class: `pill ${block.phase}`, "data-ui": "详情.event-block.phase"}, block.phase),
  el("span", {class: "log-sum", "data-ui": "详情.event-block.summary"}, opened ? "" : block.summary),
  el("span", {class: "log-time", "data-ui": "详情.event-block.time"}, opened ? block.span : block.from));
  const card = el("div", {class: block.tone === "plain" ? "log-block" : "log-block warn",
    "data-ui": "详情.event-block"}, header);
  if (opened) {
    card.append(el("div", {class: "log-body"},
      ...(block.items || []).map((item, itemIndex) =>
        eventRow(item, `${key}:${itemIndex}`, ui, repaint))));
  }
  return card;
}

function frame(hooks, view, {githubInHead, phase}) {
  const head = [
    el("span", {class: "eyebrow", "data-ui": "详情.head.eyebrow"}, view.eyebrow || ""),
  ];
  if (githubInHead) {
    head.push(el("button", {type: "button", class: "btn sm", "data-ui": "详情.head.github",
      onClick: () => openGithub(view)}, "GitHub ↗"));
  }
  head.push(el("button", {type: "button", class: "iconbtn close", "aria-label": "关闭详情",
    "data-ui": "详情.head.close", onClick: () => hooks.onClose?.()}, "×"));
  const status = [
    el("span", {class: `lamp big ${view.lamp || "hollow"}`, "data-ui": "详情.status.lamp"}),
    el("span", {class: `status-word ${view.lamp || ""}`, "data-ui": "详情.status.status"}, view.statusWord || ""),
  ];
  if (phase && view.phase) {
    status.push(el("span", {class: `pill big ${view.phase}`, "data-ui": "详情.status.phase"}, view.phase));
  }
  status.push(el("span", {class: "meta", "data-ui": "详情.status.elapsed"}, view.elapsed || ""));
  return [
    el("div", {class: "detail-head", "data-ui": "详情.head"}, ...head),
    el("div", {class: "detail-id"},
      el("h2", {class: "title", "data-ui": "详情.title"}, view.title || ""),
      origin(hooks, view)),
    el("div", {class: "detail-status", "data-ui": "详情.status"}, ...status),
  ];
}

function ticketCard(hooks, view, ui, repaint) {
  const blocks = view.phaseBlocks || [];
  const parts = [...frame(hooks, view, {githubInHead: true, phase: true}), ticketRuntime(view)];
  if (view.why?.length) {
    parts.push(el("div", {class: "callout", "data-ui": "详情.why"},
      el("span", {class: "eyebrow orange", "data-ui": "详情.why.title"}, "Needs you"),
      ...view.why.map(item => el("span", {class: "why-item", "data-ui": "详情.why.item"},
        el("b", {}, item.head), " ", item.body))));
  }
  if (view.blockers?.length) {
    parts.push(section("详情.blocked-by", "Blocked by", view.blockers.length,
      ...heldFirst(view.blockers).map(row => relation(hooks, row, "详情.blocker",
        {where: "ui", holdClass: true}))));
  }
  if (view.blocks?.length) {
    parts.push(section("详情.blocking", "Blocking", view.blocks.length,
      ...heldFirst(view.blocks).map(row => relation(hooks, row, "详情.blocks",
        {where: "plain", holdClass: false}))));
  }
  parts.push(section("详情.events", "Events", view.eventCount ?? (view.rawEvents || []).length,
    ...blocks.map((block, index) => phaseBlock(block, index, view, ui, repaint))));
  if (view.kids?.length) {
    parts.push(section("详情.sub-issues", "Sub-issues", view.kids.length,
      ...view.kids.map(kid => el("div", {class: "row sub-issue", "data-ui": "详情.sub-issue"},
        el("span", {class: `lamp ${kid.lamp}`, "data-ui": "详情.sub-issue.lamp"}),
        el("span", {class: "row-num", "data-ui": "详情.sub-issue.number"}, kid.num),
        el("span", {class: "row-title", "data-ui": "详情.sub-issue.title"}, kid.title),
        el("span", {class: kid.hot ? "pill tag hot" : "pill tag",
          "data-ui": "详情.sub-issue.kind"}, kid.kind)))));
  }
  return parts;
}

function containerBody(hooks, view) {
  const kids = [
    section("详情.summary", view.listTitle, view.listCount,
      el("div", {class: "counters loose", "data-ui": "详情.lamp-counts"},
        ...(view.lamps || []).map(item => el("span", {class: "counter plain",
          "data-ui": "详情.lamp-counts.item"},
          el("span", {class: `lamp ${item.lamp}`}), item.word,
          el("span", {class: "counter-n"}, String(item.n))))),
      el("div", {class: "counters", "data-ui": "详情.phase-counts"},
        ...(view.phases || []).map(item => el("span", {class: `pill ${item.phase}`,
          "data-ui": "详情.phase-counts.item"}, item.label)))),
  ];
  if (view.kind === "spec") {
    kids.push(section("详情.by-number", "By number", null,
      ...(view.ticketRows || []).map(row => relation(hooks, row, "详情.ticket-row",
        {where: "ui", holdClass: false}))));
  }
  if (view.kind === "map") {
    kids.push(section("详情.specs", "spec", view.specCount,
      ...(view.specRows || []).map(row => relation(hooks, row, "详情.spec-row",
        {where: "ui", holdClass: false}))));
    if (view.decisionRows?.length) {
      kids.push(section("详情.decisions", "Decision tickets", view.decisionCount,
        ...(view.decisionRows || []).map(row => relation(hooks, row, "详情.decision-row",
          {where: "ui", holdClass: false}))));
    }
  }
  return kids;
}

function card(hooks, view) {
  const parts = [...frame(hooks, view, {githubInHead: false, phase: false})];
  if (view.kind === "spec" || view.kind === "map") parts.push(...containerBody(hooks, view));
  if (view.kind === "decision") parts.push(...blockingSection(hooks, view));
  if (view.ghLabel) {
    parts.push(el("button", {
      type: "button", class: "btn sm github", "data-ui": "详情.github",
      onClick: () => openGithub(view),
    }, view.ghLabel));
  }
  return parts;
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
    root = el("aside", {class: "detail board", "aria-label": "详情", "data-ui": "详情.root"});
    root.dataset.screen = "detail";
    host._detailRoot = root;
    host.replaceChildren(root);
  }
  const ui = host._detailUi ||= {openEvents: new Set(), toggledBlocks: new Set(), hooks};
  ui.hooks = hooks;
  const repaint = () => render(host, view, api, hooks);
  if (!view.empty && view.kind === "ticket") root.replaceChildren(...ticketCard(hooks, view, ui, repaint));
  else if (!view.empty && view.kind) root.replaceChildren(...card(hooks, view));
  else {
    root.replaceChildren(el("div", {class: "empty", "data-ui": "详情.empty"},
      el("p", {class: "display", "data-ui": "详情.empty.title"}, view.emptyTitle || "点一张卡"),
      el("p", {class: "empty-text"}, view.emptyText || "画布上任意一张卡——map、spec、ticket 或 decision ticket——点一下，它的全部细节就在这一栏。")));
  }
  if (host._detailEsc) document.removeEventListener("keydown", host._detailEsc);
  host._detailEsc = event => {
    if (event.key === "Escape" && !view.empty && view.kind) hooks.onClose?.();
  };
  document.addEventListener("keydown", host._detailEsc);
  return root;
}
