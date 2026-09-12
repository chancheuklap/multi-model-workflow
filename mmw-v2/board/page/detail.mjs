import {Board, LIGHT_WORD, STEPS} from "./board-logic.mjs";
import {el, hhmm} from "./shared.mjs";

const NOW_CLASS = {
  queued: "now-queued", working: "now-working", waiting: "now-waiting",
  review: "now-review", verify: "now-verify", landed: "now-landed",
};
const NEEDS_YOU = new Set(["decision", "fault", "contract"]);
function lightFrom(cls) {
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
    light: lightFrom(row.lightCls),
    state: row.state,
    step: row.step,
    unknown: Boolean(row.unknown || row.known === false),
  };
}

function kidFrom(row) {
  return {
    num: row.num, kind: row.kind, title: row.title, to: row.to,
    light: lightFrom(row.lightCls), goto: row.goto, hasGoto: Boolean(row.hasGoto),
    orange: (row.toCls || "").includes("orange"),
  };
}

function pathFrom(steps) {
  return (steps || []).map(step => ({
    name: step.name,
    done: (step.cls || "").includes("done"),
    now: /now-/.test(step.cls || ""),
    sep: Boolean(step.sep),
  }));
}

export function fromScene(data = {}) {
  const vals = data.vals || {};
  const d = vals.d || {};
  if (!d.hasCard) {
    return {
      empty: true,
      emptyTitle: vals.emptyTitle || "点一张卡",
      emptyText: vals.emptyText || "画布上任意一张卡——map、spec、ticket 或决策票——点一下，它的全部细节就在这一栏。",
    };
  }
  return {
    empty: false,
    repo: vals.repo,
    kind: kindOf(d),
    eyebrow: d.eyebrow,
    num: d.num,
    title: d.title,
    light: lightFrom(d.lightCls),
    statusWord: d.statusWord,
    elapsed: d.elapsed || "",
    step: d.step,
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
    blockers: (vals.blockers || []).map(relFrom),
    blocks: (vals.blocks || []).map(relFrom),
    kids: (vals.kids || []).map(kidFrom),
    events: (d.events || []).map(event => ({
      time: event.time, name: event.name, field: event.field, line: event.line,
      light: lightFrom(event.dotCls),
    })),
    runtimeNote: vals.runtimeNote || "",
    hasWorker: Boolean(d.hasWorker),
    gh: d.gh,
    ghLabel: d.ghLabel,
    listTitle: d.listTitle,
    listCount: d.listCount,
    lights: (d.lights || []).map(item => ({light: lightFrom(item.cls), word: item.word, n: item.n})),
    steps: (d.steps || []).map(item => ({
      step: (item.cls || "").replace(/^pill\s+/, ""), label: item.label,
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
    return {n, num: `#${n}`, light: "none", title: "不在这棵树里，读不到它的状态",
      where: "", state: "未知", unknown: true};
  }
  let light, state;
  if (found.type === "ticket") {
    light = Board.light(found.ref);
    state = found.ref.fold.landed ? "已合入"
      : role !== "blocker" ? LIGHT_WORD[light]
        : Board.released(found.ref) ? "没过就关了，已放行" : "未合入";
  } else if (found.type === "spec") {
    light = Board.aggregate(found.ref.tickets);
    state = `${found.ref.tickets.filter(ticket => Board.done(ticket)).length}/${found.ref.tickets.length}`;
  } else {
    light = Board.decisionLight(found.ref);
    state = found.ref.state === "closed" ? "已关闭" : "开着";
  }
  return {
    n, num: `#${n}`, light, title: found.ref.title, unknown: false,
    where: found.spec && found.spec.n !== hereSpec ? `spec #${found.spec.n}` : "",
    state,
  };
}

function kidTo(child) {
  if (child.resolution === "fixed") return {to: "已修"};
  if (child.resolution === "stale") return {to: "条件已不成立"};
  if (child.resolution === "became-ticket") {
    return {to: `变成了 #${child.ticket}`, goto: child.ticket, hasGoto: true};
  }
  if (NEEDS_YOU.has(child.kind)) return {to: "等你", orange: true};
  return {to: child.kind === "deferred" ? "留给以后的票" : "等收口那一轮"};
}

function ticketView(tasks, found) {
  const ticket = found.ref, fold = ticket.fold, light = Board.light(ticket), step = Board.step(ticket);
  const stopped = Board.handedBack(ticket) || Board.bounce(ticket)
    || (fold.sessions.some(session => session.live) && Board.stoppedByFault(ticket));
  const index = STEPS.indexOf(step);
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
    title: ticket.title, light, statusWord: LIGHT_WORD[light], elapsed: Board.elapsed(ticket),
    step, hint: step === "landed" ? "走完了" : stopped ? "停在这一步" : step === "queued" ? "还没开始" : "现在在这一步",
    path: STEPS.map((name, i) => ({name, done: i < index, now: i === index, sep: i < STEPS.length - 1})),
    why, facts: Board.facts(ticket).map(([k, v]) => ({k, v})),
    hasWorker: Boolean(worker), runtimeNote: worker ? "取自 worker.started" : "",
    sessions: fold.sessions.map(session => ({
      kind: session.kind, what: `${session.host} · ${session.model} · ${session.effort}`,
      state: Board.sessionState(session, ticket),
      live: session.live && !Board.stoppedByFault(ticket),
    })),
    blockers: ticket.blocked.map(n => relRowFromBoard(tasks, n, "blocker", found.spec.n)),
    blocks: blocks.map(n => relRowFromBoard(tasks, n, "blocked", found.spec.n)),
    kids: Object.values(fold.children).map(child => {
      const to = kidTo(child);
      return {
        num: `#${child.child}`, kind: child.kind, title: child.title, to: to.to,
        goto: to.goto, hasGoto: Boolean(to.hasGoto), orange: Boolean(to.orange),
        light: child.resolution ? "ink" : NEEDS_YOU.has(child.kind) ? "orange" : "hollow",
      };
    }),
    events: ticket.events.map(event => ({
      time: hhmm(event.at), name: event.event, field: Board.evFields(event),
      line: event.line, light: Board.eventLight(event),
    })),
    gh: ticket.n, ghLabel: `在 GitHub 打开 #${ticket.n} ↗`,
  };
}

function containerView(tasks, found) {
  const container = found.ref, isMap = found.type === "map";
  const list = isMap ? Board.allTickets(container) : container.tickets;
  const light = Board.aggregate(list);
  const countLight = key => list.filter(ticket => Board.light(ticket) === key).length;
  const countStep = key => list.filter(ticket => Board.step(ticket) === key).length;
  const done = list.filter(ticket => Board.done(ticket)).length;
  return {
    empty: false, kind: isMap ? "map" : "spec",
    eyebrow: isMap ? "Map · 任务" : "Spec",
    num: `#${container.n}` + (isMap ? ` · ${container.kind}` : ""),
    links: isMap || found.task.n === container.n ? [] : [{label: `map #${found.task.n}`, n: found.task.n}],
    title: container.title, light, statusWord: LIGHT_WORD[light],
    elapsed: `${done}/${list.length} 落地`,
    listTitle: isMap ? "全部 ticket" : "它的 ticket", listCount: list.length,
    lights: ["orange", "green", "hollow", "ink"].filter(key => countLight(key))
      .map(key => ({light: key, word: LIGHT_WORD[key], n: countLight(key)})),
    steps: STEPS.filter(step => countStep(step)).map(step => ({step, label: `${step} · ${countStep(step)}`})),
    specRows: isMap ? container.specs.map(spec => relRowFromBoard(tasks, spec.n, "spec", null)) : [],
    specCount: isMap ? container.specs.length : 0,
    decisionCount: isMap ? container.decisions.length : 0,
    decisionRows: isMap ? container.decisions.map(decision => relRowFromBoard(tasks, decision.n, "decision", null)) : [],
    ticketRows: isMap ? [] : container.tickets.map(ticket => {
      const step = Board.step(ticket);
      return {n: ticket.n, num: `#${ticket.n}`, light: Board.light(ticket), title: ticket.title, step};
    }),
    gh: container.n, ghLabel: `在 GitHub 打开 #${container.n} ↗`,
    why: [], facts: [], sessions: [], kids: [], events: [], blockers: [], blocks: [],
    closeout: null, hasWorker: false, runtimeNote: "",
  };
}

function decisionView(tasks, found) {
  const decision = found.ref, light = Board.decisionLight(decision);
  const blocks = found.task.decisions.filter(item => item.blocked.includes(decision.n)).map(item => item.n);
  return {
    empty: false, kind: "decision", eyebrow: `决策票 · ${decision.kind}`, num: `#${decision.n}`,
    links: [{label: `map #${found.task.n}`, n: found.task.n}],
    title: decision.title, light,
    statusWord: decision.state === "closed" ? "已定" : "还开着",
    elapsed: "",
    blockers: decision.blocked.map(n => relRowFromBoard(tasks, n, "decision", null)),
    blocks: blocks.map(n => relRowFromBoard(tasks, n, "decision", null)),
    gh: decision.n, ghLabel: `在 GitHub 打开 #${decision.n} ↗`,
    why: [], facts: [], sessions: [], kids: [], events: [], closeout: null,
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
      ? "画布上任意一张卡——map、spec、ticket 或决策票——点一下，它的全部细节就在这一栏。"
      : "有了任务之后，点画布上的卡，它的细节显示在这一栏。",
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
  const last = row.step
    ? el("span", {class: `pill ${row.step}`}, row.step)
    : el("span", {class: row.state === "未合入" ? "rel-state open" : "rel-state"}, row.state);
  const body = [
    el("span", {class: `light ${row.light}`}),
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
  return section("阻塞", null,
    el("div", {class: "rel-label"}, "阻塞它的"),
    ...(view.blockers || []).map(row => relRow(hooks, row)),
    !view.blockers?.length ? el("p", {class: "rel-none"}, noneText) : null,
    el("div", {class: "rel-label"}, "它阻塞的"),
    ...(view.blocks || []).map(row => relRow(hooks, row)),
    !view.blocks?.length ? el("p", {class: "rel-none"}, "无") : null);
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

function ticketBody(hooks, view) {
  const kids = [
    el("div", {class: "dp-step"},
      el("span", {class: `pill big ${view.step}`}, view.step),
      el("span", {class: "dp-hint"}, view.hint)),
    el("div", {class: "path"},
      ...(view.path || []).flatMap(step => [
        el("span", {class: "path-step" + (step.done ? " done" : step.now ? ` ${NOW_CLASS[step.name]}` : "")},
          step.name),
        step.sep ? el("span", {class: "path-sep"}, "›") : null,
      ])),
  ];
  if (view.why?.length) {
    kids.push(el("div", {class: "why"},
      el("span", {class: "why-title"}, "为什么是橙的"),
      ...view.why.map(item => el("span", {}, el("b", {class: "why-child"}, item.head), " ", item.body))));
  }
  const runtime = [];
  if (view.hasWorker) {
    runtime.push(el("div", {class: "facts"},
      ...(view.facts || []).flatMap(fact => [
        el("span", {class: "fact-key"}, fact.k), el("span", {class: "fact-val"}, fact.v),
      ])));
    if ((view.sessions || []).length > 1) {
      for (const session of view.sessions) {
        runtime.push(el("div", {class: "session"},
          el("span", {class: "session-kind"}, session.kind),
          el("span", {class: "session-what"}, session.what),
          el("span", {class: session.live ? "session-state live" : "session-state"}, session.state)));
      }
    }
  }
  if (view.kind === "ticket" && !view.hasWorker) {
    runtime.push(el("p", {class: "rel-none"}, view.step === "landed"
      ? "没派发过就关了：它不是这条管线跑完的，没有 host、runner 可看。"
      : "尚未派发。frontier 选中它之后，这里会出现它跑在哪个 host、哪个 runner。"));
  }
  kids.push(section("运行时", view.runtimeNote || "", ...runtime));
  kids.push(blockingSection(hooks, view, "无，一开始就能动"));
  kids.push(section("子 issue", view.kids?.length ?? 0,
    ...(view.kids || []).map(kid => el("div", {class: "kid"},
      el("span", {class: `light ${kid.light}`}),
      el("span", {class: "kid-num"}, kid.num),
      el("span", {class: "kid-kind"}, kid.kind),
      kid.hasGoto
        ? el("button", {type: "button", class: "dp-link kid-to", onClick: () => goto(hooks, kid.goto)}, kid.to)
        : el("span", {class: kid.orange ? "kid-to orange" : "kid-to"}, kid.to),
      el("span", {class: "kid-title"}, kid.title))),
    view.kids?.length ? null : el("p", {class: "rel-none"}, "没有开出子 issue")));
  kids.push(section("事件", `${view.events?.length ?? 0} 条评论`,
    view.events?.length ? null : el("p", {class: "rel-none"}, "还没有事件。第一条会是 worker.started。"),
    el("div", {class: "events"},
      ...(view.events || []).map(event => el("div", {class: "ev"},
        el("span", {class: `light ${event.light} ev-dot`}),
        el("div", {class: "ev-head"},
          el("span", {class: "ev-time"}, event.time),
          el("span", {class: event.light === "orange" ? "ev-name orange" : "ev-name"}, event.name),
          el("span", {class: "ev-field"}, event.field)),
        el("div", {class: "ev-line"}, event.line))))));
  return kids;
}

function containerBody(hooks, view) {
  const kids = [
    section(view.listTitle, view.listCount,
      el("div", {class: "lights-count"},
        ...(view.lights || []).map(item => el("span", {class: "lc-item"},
          el("span", {class: `light ${item.light}`}), item.word, el("span", {class: "lc-n"}, item.n)))),
      el("div", {class: "steps-count"},
        ...(view.steps || []).map(item => el("span", {class: `pill ${item.step}`}, item.label)))),
  ];
  if (view.kind === "spec") {
    kids.push(section("按票号", null, ...(view.ticketRows || []).map(row => relRow(hooks, row))));
  }
  if (view.kind === "map") {
    kids.push(section("spec", view.specCount, ...(view.specRows || []).map(row => relRow(hooks, row))));
    if (view.decisionRows?.length) {
      kids.push(section("决策票", view.decisionCount,
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
      "收口那一轮新开 · 出自",
      el("button", {type: "button", class: "dp-link",
        onClick: () => goto(hooks, view.closeout.from)}, view.closeout.fromLabel),
      view.closeout.child));
  }
  parts.push(
    el("h2", {class: "dp-title"}, view.title),
    el("div", {class: "dp-status"},
      el("span", {class: `light big ${view.light}`}),
      el("span", {class: `status-word ${view.light}`}, view.statusWord),
      el("span", {class: "dp-elapsed"}, view.elapsed || "")),
  );
  if (view.kind === "ticket") parts.push(...ticketBody(hooks, view));
  if (view.kind === "spec" || view.kind === "map") parts.push(...containerBody(hooks, view));
  if (view.kind === "decision") parts.push(blockingSection(hooks, view, "无"));
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
  host.replaceChildren();
}

export function render(host, view = {}, api, hooks = {}) {
  const root = el("aside", {class: "detail board", "aria-label": "详情"});
  root.dataset.screen = "detail";
  if (!view.empty && view.kind) root.append(card(hooks, view));
  else {
    root.append(el("div", {class: "dp-empty"},
      el("p", {class: "dp-empty-title"}, view.emptyTitle || "点一张卡"),
      view.emptyText || "画布上任意一张卡——map、spec、ticket 或决策票——点一下，它的全部细节就在这一栏。"));
  }
  if (host._detailEsc) document.removeEventListener("keydown", host._detailEsc);
  host._detailEsc = event => {
    if (event.key === "Escape" && !view.empty && view.kind) hooks.onClose?.();
  };
  document.addEventListener("keydown", host._detailEsc);
  host.replaceChildren(root);
  return root;
}
