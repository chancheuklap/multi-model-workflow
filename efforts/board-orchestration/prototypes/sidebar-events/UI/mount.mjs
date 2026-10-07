// The prototype's mount point inside the real board page: it takes the same view the real
// detail column is given, hands it to one of the three variants, and draws the switcher.
// A card that is not a ticket falls through to the real column — the question here is
// only about the ticket sidebar.
import {el} from "../shared.mjs";
import {Board} from "../board-logic.mjs";
import {find, fromBoard, render as realRender} from "../detail.mjs";
import * as A from "./variant-a.mjs";
import * as B from "./variant-b.mjs";
import * as C from "./variant-c.mjs";

const VARIANTS = {A, B, C};
const KEYS = Object.keys(VARIANTS);
const ui = {open: new Set(), toggled: new Set()};
let current = null;

function styles() {
  if (document.querySelector('link[data-proto-css]')) return;
  const link = el("link", {rel: "stylesheet", href: "./proto/proto.css"});
  link.dataset.protoCss = "1";
  document.head.append(link);
}

function switcher(key) {
  let bar = document.querySelector(".pxs");
  const go = phase => {
    const next = KEYS[(KEYS.indexOf(current.key) + phase + KEYS.length) % KEYS.length];
    const url = new URL(location.href);
    url.searchParams.set("variant", next);
    history.replaceState(null, "", url);
    current.key = next;
    paint();
  };
  if (!bar) {
    bar = el("div", {class: "pxs"},
      el("button", {type: "button", "aria-label": "上一个", onClick: () => go(-1)}, "‹"),
      el("span", {class: "pxs-label"}),
      el("button", {type: "button", "aria-label": "下一个", onClick: () => go(1)}, "›"));
    document.body.append(bar);
    document.addEventListener("keydown", event => {
      const tag = document.activeElement?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || document.activeElement?.isContentEditable) return;
      if (event.key === "ArrowLeft") go(-1);
      if (event.key === "ArrowRight") go(1);
    });
  }
  bar.querySelector(".pxs-label").replaceChildren(
    el("span", {class: "pxs-key"}, key), " · ", VARIANTS[key].NAME);
}

function paint() {
  const {host, payload, sel, api, hooks, key} = current;
  const view = fromBoard(payload, sel);
  if (view.empty) {
    host.replaceChildren();
    switcher(key);
    return;
  }
  if (view.kind !== "ticket") {
    if (host.querySelector("[data-proto-column]")) host.replaceChildren();
    realRender(host, view, api, hooks);
    switcher(key);
    return;
  }
  const found = find(payload.tasks || [], sel);
  view.raw = found?.ref?.events || [];
  // A related ticket is shown with the same phase pill its own card carries, plus whether
  // its hold on this one is still in force — the question a blocking list is read for.
  const mark = (rows, upstream) => (rows || []).map(row => {
    const other = find(payload.tasks || [], row.n);
    const ticket = other?.type === "ticket" ? other.ref : null;
    return {...row, phase: ticket ? Board.phase(ticket) : null,
      hold: Boolean(ticket) && (upstream ? !Board.released(ticket) : !Board.released(found.ref))};
  });
  view.blockers = mark(view.blockers, true);
  view.blocks = mark(view.blocks, false);
  // The scroll bar of this column belongs to the `aside` itself, so the `aside` is built
  // once and only its contents are swapped: a new element would come in at scrollTop 0 and
  // throw the reader back to the top on every repaint — every toggle, and every poll of
  // the board. The control that caused the repaint is rebuilt too, so it is found again by
  // its key and given the focus back.
  let root = host.querySelector('[data-proto-column]');
  if (!root) {
    root = el("aside", {class: "detail board", "aria-label": "详情"});
    root.dataset.screen = "detail";
    root.dataset.protoColumn = "1";
    root.addEventListener("proto:repaint", () => paint());
    host.replaceChildren(root);
  }
  const focused = document.activeElement?.dataset?.k;
  root.replaceChildren(VARIANTS[key].render(view, hooks, ui));
  if (focused) root.querySelector(`[data-k="${CSS.escape(focused)}"]`)?.focus({preventScroll: true});
  switcher(key);
}

export function mount(host, {payload, sel, variant}, api, hooks) {
  styles();
  const key = KEYS.includes(current?.key) ? current.key
    : KEYS.includes(String(variant).toUpperCase()) ? String(variant).toUpperCase() : "A";
  current = {host, payload, sel, api, hooks, key};
  paint();
}
