// Variant B · Plain-language feed.
// Keeps the one thing a chronological list is good at — you read it top to bottom — and
// fixes the reading instead of the structure: one sentence at the top says how the whole
// ticket went, every event is a plain English name with a plain English line under it,
// and the phase pill appears only on the row where the card's phase actually changed. The
// backend fields are one click behind each row, not on the page.
import {el} from "../shared.mjs";
import {describe} from "./vocab.mjs";
import {head, links, lamp, pill, why, relRow, runtime, detailTable, elapsed, blockingSections, kidRow} from "./parts.mjs";

export const NAME = "Plain-language feed";

function lede(view, items) {
  const starts = items.filter(item => item.event === "worker.started").length;
  const kids = items.filter(item => item.event === "child.opened").length;
  const checks = items.filter(item => item.event === "ticket.checked" && item.event !== "repo-checks"
    && /criteria met$|criteria met —/.test(item.text));
  const last = checks[checks.length - 1];
  const landed = items.find(item => item.event === "ticket.landed");
  const bounced = items.find(item => item.event === "ticket.bounced");
  const returned = items.find(item => item.event === "ticket.returned");
  const bits = [];
  if (landed) bits.push(`${landed.time} 合进了 ${landed.text.replace("merged into ", "")}`);
  else if (bounced) bits.push(`${bounced.time} 合不进去`);
  else if (returned) bits.push(`${returned.time} 交回给你`);
  else bits.push(`还在跑，这一步是 ${view.phase}`);
  if (starts) bits.push(`前后派了 ${starts} 次 worker`);
  if (last) bits.push(`acceptance criteria ${last.text.replace(" criteria met", "").replace(" of ", "/")}`);
  if (kids) bits.push(`开出 ${kids} 个子 issue`);
  return el("p", {class: "vb-lede"}, `${bits.join("，")}。`);
}

function row(item, ui, key) {
  const open = ui.open.has(key);
  const button = el("button", {type: "button", class: "vb-row", "data-k": key},
    el("span", {class: "vb-when"}, item.time),
    el("span", {},
      el("span", {class: `vb-name${item.tone === "warn" || item.tone === "needs-you" ? " warn" : ""}`}, item.name),
      item.text ? el("span", {class: "vb-text"}, item.text) : null));
  button.addEventListener("click", () => {
    if (open) ui.open.delete(key); else ui.open.add(key);
    button.dispatchEvent(new CustomEvent("proto:repaint", {bubbles: true}));
  });
  if (!open) return [button];
  return [button, el("div", {class: "vb-open"}, detailTable(item.detail))];
}

export function render(view, hooks, ui) {
  const items = (view.raw || []).map(describe);
  const feed = [];
  let phase = null;
  items.forEach((item, index) => {
    if (item.phase !== phase && !item.sticky) {
      phase = item.phase;
      feed.push(el("div", {class: "vb-mark"}, pill(phase)));
    }
    feed.push(...row(item, ui, `${view.gh}:${index}`));
  });

  const parts = [
    head(view, hooks),
    el("h2", {class: "pv-title"}, view.title),
    links(view, hooks),
    el("div", {class: "va-status"}, lamp(view.lamp, true),
      el("span", {class: `va-word ${view.lamp}`}, view.statusWord),
      el("span", {class: "va-elapsed"}, elapsed(view))),
    runtime(view, ui),
    lede(view, items),
    why(view),
    el("section", {class: "pv-sec"},
      el("div", {class: "pv-sec-title"}, el("span", {}, "Events"), el("span", {}, items.length)),
      el("div", {class: "vb-feed"},
        ...(feed.length ? feed : [el("p", {class: "pv-none"}, "no events yet")]))),
  ];

  const section = (title, count, ...rows) => el("section", {class: "pv-sec"},
    el("div", {class: "pv-sec-title"}, el("span", {}, title), el("span", {}, count)), ...rows);
  if (view.kids?.length) {
    parts.push(section("Sub-issues", view.kids.length, ...view.kids.map(kidRow)));
  }
  parts.push(...blockingSections(view, hooks, section));

  return el("div", {class: "pv"}, ...parts);
}
