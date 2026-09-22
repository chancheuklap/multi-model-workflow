import {render as renderProduct} from "/product/detail.mjs";

// The scene input is the design page's own example data (`DETAIL_SCENES.<scene>`).
// A click renders another of those views when one of them is that node; otherwise
// it renders the row the click was on, and records the scene name for that kind.
const KIND_SCENE = {
  ticket: "Component · 详情.morning",
  spec: "Component · 详情.spec",
  map: "Component · 详情.map",
  decision: "Component · 详情.decision",
};

const LISTS = ["links", "blockers", "blocks", "ticketRows", "specRows", "decisionRows"];

function rowKind(source, row, list) {
  if (list === "links") {
    if (String(row.label || "").startsWith("spec")) return "spec";
    if (String(row.label || "").startsWith("map")) return "map";
    return null;
  }
  if (list === "specRows") return "spec";
  if (list === "decisionRows") return "decision";
  if (list === "ticketRows") return "ticket";
  return source?.kind === "decision" ? "decision" : "ticket";
}

function findRow(source, n) {
  for (const list of LISTS) {
    const row = (source?.[list] || []).find(item => item.n === n);
    if (row) return {row, kind: rowKind(source, row, list)};
  }
  return null;
}

function rowView(row, kind, repo) {
  return {
    empty: false, kind, num: row.num || "", title: row.title || "", lamp: row.lamp || "",
    phase: kind === "ticket" ? (row.phase || "") : "",
    links: [], blockers: [], blocks: [], kids: [], why: [],
    gh: row.n, repo,
  };
}

export function render(host, data, api) {
  const transitions = [];
  window.storyTransitions = () => structuredClone(transitions);
  const byGh = new Map();
  const index = view => {
    if (view && !view.empty && view.gh != null && !byGh.has(view.gh)) byGh.set(view.gh, view);
  };
  index(data);
  fetch("/scenes.json").then(response => response.json()).then(async scenes => {
    const names = scenes
      .map(scene => scene.name)
      .filter(name => String(name || "").startsWith("Component · 详情."));
    const views = await Promise.all(names.map(async name => {
      const response = await fetch(`/scene-input.json?scene=${encodeURIComponent(name)}`);
      return response.ok ? response.json() : null;
    }));
    for (const view of views) index(view);
  });

  let view = data;
  const move = scene => transitions.push({scene, data: null});
  const paint = () => {
    const root = renderProduct(host, view, api, {
      onGoto(n) {
        const known = byGh.get(n);
        const found = findRow(view, n);
        const kind = known?.kind || found?.kind;
        const scene = KIND_SCENE[kind];
        if (!scene) return;
        view = known || rowView(found.row, kind, data.repo);
        move(scene);
        paint();
      },
      onClose() {
        view = {empty: true};
        move("Component · 详情.nothing-selected");
        paint();
      },
      onEventBlockToggle(opened) {
        move(opened ? "event-block-open" : "event-block-closed");
      },
      onEventToggle(opened) {
        move(opened ? "event-detail-open" : "event-detail-closed");
      },
    });
    root.dataset.storyRoot = "";
    root.style.cssText = "width:340px;height:848px";
  };
  paint();
}
