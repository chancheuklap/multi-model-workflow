// Variant A · Phase blocks.
// The event list stops being 22 equal rows and becomes six blocks, one per phase the
// ticket card passed through. A block is headed by that phase's pill — the same pill the
// card on the canvas carries — and by what the block ended in. Only the last block and
// any block that went wrong are open, so the column opens at about six lines instead of
// twenty-two, and the rest is one click away.
import {el} from "../shared.mjs";
import {blocks} from "./vocab.mjs";
import {head, links, lamp, pill, why, relRow, runtime, detailTable, elapsed, blockingSections, kidRow} from "./parts.mjs";

export const NAME = "Phase blocks";

// What a shut block says on its one line: the event of it a person would have opened it
// for — a refusal or a finding before a criteria run, a criteria run before a claim.
const WEIGHT = {"ticket.refused": 3, "ticket.returned": 3, "ticket.bounced": 3,
  "ticket.regressed": 3, "child.opened": 3, "ticket.checked": 2, "verifier.passed": 2,
  "verifier.failed": 2, "reviewer.reported": 2, "ticket.landed": 2, "ticket.passed": 2,
  "worker.lost": 2, "ticket.released": 1, "worker.started": 1};
const summary = block => {
  const best = block.items.reduce((pick, item) =>
    (WEIGHT[item.event] || 0) >= (WEIGHT[pick.event] || 0) ? item : pick, block.items[0]);
  return best.text ? `${best.name} — ${best.text}` : best.name;
};

function event(item, ui, key) {
  const open = ui.open.has(key);
  const box = el("button", {type: "button", class: "va-ev", "data-k": key},
    el("span", {class: "va-t"}, item.time),
    el("span", {class: `va-n${item.tone === "warn" || item.tone === "needs-you" ? " warn" : ""}`}, item.name));
  if (item.text) box.append(el("span", {class: "va-x"}, item.text));
  if (open) box.append(el("span", {class: "va-x"}, detailTable(item.detail)));
  box.addEventListener("click", () => {
    if (open) ui.open.delete(key); else ui.open.add(key);
    box.dispatchEvent(new CustomEvent("proto:repaint", {bubbles: true}));
  });
  return box;
}

export function render(view, hooks, ui) {
  const list = blocks(view.raw);
  const parts = [
    head(view, hooks),
    el("h2", {class: "pv-title"}, view.title),
    links(view, hooks),
    el("div", {class: "va-status"}, lamp(view.lamp, true),
      el("span", {class: `va-word ${view.lamp}`}, view.statusWord),
      pill(view.phase, view.phase, "big"),
      el("span", {class: "va-elapsed"}, elapsed(view))),
    runtime(view, ui),
    why(view),
  ];

  const bodies = list.map((block, index) => {
    const key = `${view.gh}:b${index}`;
    const wanted = index === list.length - 1 || block.tone !== "plain";
    const open = ui.toggled.has(key) ? !wanted : wanted;
    const header = el("button", {type: "button", class: "va-bhead", "data-k": key},
      el("span", {class: "va-chev"}, open ? "▾" : "▸"),
      pill(block.phase),
      el("span", {class: "va-bsum"}, open ? "" : summary(block)),
      el("span", {class: "va-btime"}, open && block.from !== block.to ? `${block.from}–${block.to}` : block.from));
    header.addEventListener("click", () => {
      if (ui.toggled.has(key)) ui.toggled.delete(key); else ui.toggled.add(key);
      header.dispatchEvent(new CustomEvent("proto:repaint", {bubbles: true}));
    });
    const box = el("div", {class: `va-block${block.tone === "plain" ? "" : " warn"}`}, header);
    if (open) {
      box.append(el("div", {class: "va-body"},
        ...block.items.map((item, i) => event(item, ui, `${key}:${i}`))));
    }
    return box;
  });

  const section = (title, count, ...rows) => el("section", {class: "pv-sec"},
    el("div", {class: "pv-sec-title"}, el("span", {}, title), el("span", {}, count)), ...rows);
  parts.push(...blockingSections(view, hooks, section));

  parts.push(el("section", {class: "pv-sec"},
    el("div", {class: "pv-sec-title"}, el("span", {}, "Events"),
      el("span", {}, (view.raw || []).length)),
    ...(bodies.length ? bodies : [el("p", {class: "pv-none"}, "no events yet")])));

  if (view.kids?.length) {
    parts.push(el("section", {class: "pv-sec"},
      el("div", {class: "pv-sec-title"}, el("span", {}, "Sub-issues"), el("span", {}, view.kids.length)),
      ...view.kids.map(kidRow)));
  }

  return el("div", {class: "pv"}, ...parts);
}
