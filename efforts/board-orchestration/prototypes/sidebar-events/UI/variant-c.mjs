// Variant C · Run cards.
// Throws the flat list away. A ticket's life is a small number of attempts, and each
// attempt is one card: who ran it, which phases it reached (the card's own pills, greyed
// where it never got), what came out of it. Only the lines that carry an outcome are on
// the card; everything else, including every backend field, is behind one count.
import {el} from "../shared.mjs";
import {runs} from "./vocab.mjs";
import {head, links, lamp, pill, why, runtime, detailTable, elapsed} from "./parts.mjs";

export const NAME = "Run cards";

const PHASES = ["queued", "working", "waiting", "review", "verify", "landed"];
const KEY = new Set(["ticket.checked", "reviewer.reported", "verifier.passed", "verifier.failed",
  "child.opened", "child.closed", "ticket.refused", "ticket.returned", "ticket.bounced",
  "ticket.landed", "ticket.regressed", "ticket.passed", "ticket.released", "worker.touched",
  "worker.queued", "worker.lost", "reviewer.lost", "verifier.lost"]);
const AGENT = {"reviewer.started": "reviewer", "verifier.started": "verifier"};

const outcomeOf = run => {
  const last = run.items[run.items.length - 1];
  if (run.items.some(item => item.event === "ticket.landed")) return {tone: "good", word: "合入了"};
  if (run.items.some(item => item.event === "ticket.bounced")) return {tone: "warn", word: "合不进去"};
  if (run.items.some(item => item.event === "ticket.returned")) return {tone: "warn", word: "交回给你"};
  if (run.items.some(item => item.event === "ticket.refused")) return {tone: "warn", word: "没接下"};
  if (run.items.some(item => item.event === "ticket.released")) return {tone: "warn", word: "认领退回"};
  if (run.items.some(item => item.event === "ticket.passed")) return {tone: "good", word: "过了"};
  if (run.items.some(item => item.event === "ticket.regressed")) return {tone: "warn", word: "落地后又不过了"};
  if (run.kind !== "run") return null;
  return last.phase === "landed" ? null : {tone: "plain", word: `停在 ${last.phase}`};
};

const TITLE = {before: "开工前", after: "落地之后"};

function card(run, view, ui, index) {
  const key = `${view.gh}:r${index}`;
  const outcome = outcomeOf(run);
  const who = [];
  if (run.head) who.push(["worker", run.head.text]);
  for (const item of run.items) {
    if (AGENT[item.event] && item.text) who.push([AGENT[item.event], item.text]);
  }
  const lines = run.items.filter(item => KEY.has(item.event));
  const hidden = run.items.length - lines.length;
  const open = ui.open.has(key);

  const box = el("div", {class: `vc-run${outcome?.tone === "warn" ? " warn" : outcome?.tone === "good" ? " done" : ""}`},
    el("div", {class: "vc-rhead"},
      el("span", {class: "vc-rn"}, TITLE[run.kind] || `第 ${run.n} 次`),
      el("span", {class: "vc-rt"}, run.from === run.to ? run.from : `${run.from} → ${run.to}`)),
    el("div", {class: "vc-strip"},
      ...PHASES.filter(phase => run.phases.includes(phase)).map(phase => pill(phase)),
      outcome ? el("span", {class: `vc-out ${outcome.tone}`}, outcome.word) : null),
  );
  if (who.length) {
    box.append(el("div", {class: "vc-grid"},
      ...who.flatMap(([role, what]) => [el("span", {class: "vc-gk"}, role), el("span", {class: "vc-gv"}, what)])));
  }
  for (const item of lines) {
    box.append(el("div", {class: "vc-line"},
      el("span", {class: "vc-key"}, item.name),
      el("span", {class: "vc-val"}, item.text || "")));
  }
  const more = el("button", {type: "button", class: "pv-more", "data-k": key},
    open ? "收起这一次的全部记录" : `这一次共 ${run.items.length} 件事${hidden ? `，另有 ${hidden} 件未列` : ""} — 全部展开`);
  more.addEventListener("click", () => {
    if (open) ui.open.delete(key); else ui.open.add(key);
    more.dispatchEvent(new CustomEvent("proto:repaint", {bubbles: true}));
  });
  box.append(more);
  if (open) {
    for (const item of run.items) {
      box.append(el("div", {class: "vc-line"},
        el("span", {class: "vc-key"}, `${item.time} ${item.name}`),
        el("span", {class: "vc-val"}, item.text || "")),
      detailTable(item.detail));
    }
  }
  return box;
}

export function render(view, hooks, ui) {
  const list = runs(view.raw);
  const reached = new Set(list.flatMap(run => run.phases));
  const parts = [
    head(view, hooks),
    el("h2", {class: "pv-title"}, view.title),
    links(view, hooks),
    el("div", {class: "va-status"}, lamp(view.lamp, true),
      el("span", {class: `va-word ${view.lamp}`}, view.statusWord),
      el("span", {class: "va-elapsed"}, elapsed(view))),
    runtime(view, ui, {models: false}),
    el("div", {class: "vc-strip"},
      ...PHASES.map(phase => pill(phase, phase, phase === view.phase ? "big" : reached.has(phase) ? "" : "off"))),
    why(view),
    el("section", {class: "pv-sec"},
      el("div", {class: "pv-sec-title"}, el("span", {}, "Runs"), el("span", {}, list.length)),
      ...(list.length ? list.map((run, index) => card(run, view, ui, index))
        : [el("p", {class: "pv-none"}, "not dispatched yet")])),
  ];

  const rows = [];
  for (const kid of view.kids || []) rows.push([`${kid.num} ${kid.kind}`, `${kid.title} · ${kid.to}`]);
  for (const blocker of view.blockers || []) rows.push([`${blocker.num} blocked by`, blocker.title]);
  for (const blocked of view.blocks || []) rows.push([`${blocked.num} blocking`, blocked.title]);
  if (rows.length) {
    parts.push(el("section", {class: "pv-sec"},
      el("div", {class: "pv-sec-title"}, el("span", {}, "Blocked by · Blocking · Sub-issues")),
      el("div", {class: "vc-grid"},
        ...rows.flatMap(([key, value]) => [el("span", {class: "vc-gk"}, key), el("span", {class: "vc-gv"}, value)]))));
  }
  return el("div", {class: "pv"}, ...parts);
}
