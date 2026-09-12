import {render as renderProduct} from "/product/detail.mjs";

function lampFrom(cls) {
  if (!cls) return "hollow";
  if (/\borange\b/.test(cls)) return "orange";
  if (/\bgreen\b/.test(cls)) return "green";
  if (/\bink\b/.test(cls)) return "ink";
  if (/\bnone\b/.test(cls)) return "none";
  return "hollow";
}

function relFrom(row) {
  return {
    n: row.n, num: row.num, title: row.title, where: row.where || "",
    lamp: lampFrom(row.lampCls), state: row.state, phase: row.phase,
    unknown: Boolean(row.unknown || row.known === false),
  };
}

function viewFrom(data) {
  const vals = data?.vals || {};
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
    kind: d.isTicket ? "ticket" : d.isMap ? "map" : d.isSpec ? "spec" : d.isDecision ? "decision" : "empty",
    eyebrow: d.eyebrow, num: d.num, title: d.title,
    lamp: lampFrom(d.lampCls), statusWord: d.statusWord, elapsed: d.elapsed || "",
    phase: d.phase, hint: d.hint,
    path: (d.path || []).map(phase => ({
      name: phase.name, done: (phase.cls || "").includes("done"),
      now: /now-/.test(phase.cls || ""), sep: Boolean(phase.sep),
    })),
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
    kids: (vals.kids || []).map(row => ({
      num: row.num, kind: row.kind, title: row.title, to: row.to,
      lamp: lampFrom(row.lampCls), goto: row.goto, hasGoto: Boolean(row.hasGoto),
      orange: (row.toCls || "").includes("orange"),
    })),
    events: (d.events || []).map(event => ({
      time: event.time, name: event.name, field: event.field, line: event.line,
      lamp: lampFrom(event.dotCls),
    })),
    runtimeNote: vals.runtimeNote || "",
    hasWorker: Boolean(d.hasWorker),
    gh: d.gh, ghLabel: d.ghLabel,
    listTitle: d.listTitle, listCount: d.listCount,
    lamps: (d.lamps || []).map(item => ({lamp: lampFrom(item.cls), word: item.word, n: item.n})),
    phases: (d.phases || []).map(item => ({phase: (item.cls || "").replace(/^pill\s+/, ""), label: item.label})),
    ticketRows: (vals.ticketRows || []).map(relFrom),
    specRows: (vals.specRows || []).map(relFrom),
    decisionRows: (vals.decisionRows || []).map(relFrom),
    specCount: d.specCount, decisionCount: d.decisionCount,
  };
}

export function render(host, data, api) {
  const root = renderProduct(host, viewFrom(data), api);
  root.dataset.storyRoot = "";
  root.style.cssText = "width:340px;height:848px";
}
