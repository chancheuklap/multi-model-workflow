// Leaf helpers the three variants share: a pill, a lamp, one relation row, the
// backend-detail table, the GitHub button. Layout and section order are each variant's
// own — that is what is being compared.
import {el} from "../shared.mjs";

export const pill = (phase, label = phase, extra = "") =>
  el("span", {class: `pill ${phase}${extra ? ` ${extra}` : ""}`}, label);

export const lamp = (lamp, big = false) => el("span", {class: `lamp ${lamp}${big ? " big" : ""}`});

export function links(view, hooks) {
  const parts = [el("span", {}, view.num)];
  for (const link of view.links || []) {
    parts.push(el("span", {}, "·"),
      el("button", {type: "button", class: "pv-link", onClick: () => hooks.onGoto?.(link.n)}, link.label));
  }
  return el("div", {class: "pv-links"}, ...parts);
}

// The head row: what this card is, the way out to GitHub, and the way to shut the column.
// The GitHub button sits here rather than under the last section, so it is reachable
// without scrolling whatever the ticket's history is.
export function head(view, hooks, eyebrow = "Ticket") {
  return el("div", {class: "pv-head"},
    el("span", {class: "pv-eyebrow"}, eyebrow),
    ghButton(view),
    el("button", {type: "button", class: "pv-close", "aria-label": "关闭详情",
      onClick: () => hooks.onClose?.()}, "×"));
}

export function why(view) {
  if (!view.why?.length) return null;
  return el("div", {class: "pv-why"},
    el("span", {class: "pv-why-t"}, "Needs you"),
    ...view.why.map(item => el("span", {}, el("b", {}, item.head), " ", item.body)));
}

// One related issue: its own lamp and phase pill, so it reads the way its card on the
// canvas reads, and — when its hold has not ended — `挡着`, which is the only thing this
// list is opened to find out.
// The board writes the elapsed time as a sentence — `用时 1h44m`, `跑了 1h02m 后交回`. The
// status word and the pill beside it already say how it ended, so the slot takes the
// duration alone.
export const elapsed = view => String(view.elapsed || "")
  .replace(/^\D+/, "").replace(/(\d+) 分钟/, "$1m").replace(/ 后.*$/, "");

// The two directions of a blocking edge, under the names GitHub gives them on the issue
// itself — its API calls the two connections `blockedBy` and `blocking`. Each row is
// sorted so whatever still holds is on top.
export function blockingSections(view, hooks, section) {
  const held = rows => [...rows].sort((one, two) => Number(two.hold) - Number(one.hold));
  const group = (title, rows) => rows.length
    ? section(title, rows.length, ...held(rows).map(row => relRow(row, hooks))) : null;
  return [group("Blocked by", view.blockers || []), group("Blocking", view.blocks || [])];
}

// A sub-issue is read by its kind: which of the five it is says who can answer it, and
// that is the only thing worth a chip. Whether it is answered yet is the lamp's job.
const NEEDS_YOU_KIND = new Set(["decision", "fault", "contract"]);

export function kidRow(kid) {
  return el("div", {class: "pv-rel"},
    lamp(kid.lamp), el("span", {class: "pv-rel-n"}, kid.num),
    el("span", {class: "pv-rel-t"}, kid.title),
    el("span", {class: `pv-kind${NEEDS_YOU_KIND.has(kid.kind) ? " hot" : ""}`}, kid.kind));
}

export function relRow(row, hooks) {
  return el("button", {type: "button", class: `pv-rel${row.hold ? " hold" : ""}`,
    onClick: () => hooks.onGoto?.(row.n)},
    lamp(row.lamp), el("span", {class: "pv-rel-n"}, row.num),
    el("span", {class: "pv-rel-t"}, row.title),
    row.hold ? el("span", {class: "pv-rel-hold"}, "held")
      : row.phase ? pill(row.phase) : el("span", {class: "pv-rel-s"}, row.state));
}

// Where the ticket ran, read off its newest `worker.started`: the grade it was given and
// the model that filled it, then the four addresses a person may want to go to. Nothing
// is folded away and nothing is a hash — `runner` and its session id are the pipeline's
// own handle on the session, and `base`, the commit the branch was cut from, is a machine's
// fact; all three stay in that event's own detail table, one click away in the list below.
export function runtime(view, ui, {models = true} = {}) {
  const started = [...(view.raw || [])].reverse().find(event => event.event === "worker.started");
  if (!view.hasWorker || !started) {
    return el("p", {class: "pv-none"}, view.phase === "landed"
      ? "closed without a run" : "not dispatched yet");
  }
  const payload = started.payload || {};
  const worktree = String(payload.worktree || "").split("/.worktrees/")[1];
  // The slot a run held is a number in its own `ticket.checked`; the board's fact line
  // wraps it in a sentence, which this column has no room for.
  const slot = [...(view.raw || [])].reverse()
    .find(event => event.event === "ticket.checked" && event.payload?.slot != null)?.payload.slot;
  const rows = [
    ["ticket branch", payload.branch],
    ["base branch", payload.into],
    ["worktree", worktree ? `…/.worktrees/${worktree}` : payload.worktree],
    ["machine", payload.machine],
    ...(slot != null ? [["slot", String(slot)]] : []),
  ].filter(([, value]) => value);
  return el("div", {class: "pv-run"},
    el("div", {class: "pv-run-who"},
      el("span", {class: "pv-run-grade"}, payload.grade),
      models ? el("span", {class: "pv-run-model"},
        `${payload.host} · ${payload.model} · ${payload.effort}`) : null),
    el("div", {class: "pv-run-where"},
      ...rows.flatMap(([key, value]) =>
        [el("span", {class: "pv-run-k"}, key), el("span", {class: "pv-run-v"}, value)])));
}

export function detailTable(rows) {
  return el("div", {class: "pv-detail"},
    ...rows.flatMap(([key, value]) => [el("b", {}, key), el("span", {}, value)]));
}

export function ghButton(view) {
  return el("button", {type: "button", class: "pv-gh", onClick: () => {
    if (view.gh != null && view.repo) {
      window.open(`https://github.com/${view.repo}/issues/${view.gh}`, "_blank", "noopener,noreferrer");
    }
  }}, "GitHub ↗");
}
