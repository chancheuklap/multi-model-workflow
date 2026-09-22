import {CATALOG} from "/product/local-config.mjs";
import {render as renderProduct} from "/product/settings.mjs";

// Scene input is SETTINGS_VIEWS.<scene>: the component view, field for field.
// The first paint uses that view. A click still runs the sheet's own model.
// The draft is the view's rows. A host's models are the ones listed on the
// rows that currently use it; the effort list on that row applies to each of
// those models. A host the scene marks as answered, but for which it lists no
// models, keeps the models the rows already show, so changing to it keeps the
// current model. The opened version is the example's 12 when the view omits
// it — the sheet does not show the number, and the boundary test names it.

function copy(value) {
  return JSON.parse(JSON.stringify(value));
}

function effortValues(row) {
  return (row.effortOpts || []).map(option => option.value).filter(value => value !== "");
}

function draftFrom(view) {
  const rows = {};
  for (const row of view.rows || []) {
    rows[row.agent] = {
      host: row.host ?? "",
      model: row.model ?? "",
      effort: row.effort ?? "",
    };
  }
  return {runner: view.runner, rows};
}

function scanFrom(view) {
  const hosts = {};
  for (const chip of view.chips || []) {
    const state = String(chip.cls || "").trim().split(/\s+/)[1] || "ok";
    hosts[chip.host] = {state, offered: []};
  }
  for (const row of view.rows || []) {
    const host = hosts[row.host] || (hosts[row.host] = {state: "ok", offered: []});
    const known = new Map(host.offered.map(item => [item.model, item]));
    const efforts = effortValues(row);
    for (const option of row.modelOpts || []) {
      if (!option.value) continue;
      const item = known.get(option.value) || {model: option.value, efforts: []};
      if (efforts.length) item.efforts = efforts;
      known.set(option.value, item);
    }
    host.offered = [...known.values()];
  }
  const inUse = [];
  for (const row of view.rows || []) {
    if (!row.model) continue;
    inUse.push({model: row.model, efforts: effortValues(row)});
  }
  for (const host of Object.values(hosts)) {
    if (host.state === "ok" && host.offered.length === 0) host.offered = copy(inUse);
  }
  return hosts;
}

function modelFromView(view) {
  const draft = draftFrom(view);
  const scanned = String(view.scannedText || "");
  return {
    view,
    catalog: CATALOG,
    scan: scanFrom(view),
    st: {
      saved: copy(draft),
      draft,
      scanSource: scanned.includes("Paseo") ? "paseo" : "cli",
      scannedAt: null,
      scanning: Boolean(view.scanning),
      savedAt: null,
      refused: view.refused ? 1 : 0,
      reread: false,
      version: Number.isInteger(view.version) ? view.version : 12,
      modifiedAt: null,
      serverFlags: [],
    },
  };
}

export function render(host, data, api) {
  const transitions = [];
  window.storyTransitions = () => structuredClone(transitions);
  const root = renderProduct(host, modelFromView(data), api, {
    onState(state) {
      transitions.push({
        scene: state === "closed" ? "settings-closed" : `Component · 本机配置.${state}`,
      });
    },
  });
  root.dataset.storyRoot = "";
  return root;
}
