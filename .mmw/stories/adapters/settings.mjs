import {CATALOG, LocalConfig} from "/product/local-config.mjs";
import {render as renderProduct} from "/product/settings.mjs";

// Scene input is SETTINGS_VIEWS.<scene>, already the component view. The first
// paint uses it unchanged. A click needs a draft, and the only draft fields the
// scene carries are each row's host, model and effort, plus runner. It does not
// carry version, a host's offered models, scanned_at, source or modified_at;
// those stay absent. source() is the product's own rule from runner.

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

function modelFromView(view) {
  const draft = draftFrom(view);
  return {
    view,
    catalog: CATALOG,
    scan: {},
    st: {
      saved: structuredClone(draft),
      draft,
      scanSource: LocalConfig.source(draft),
      scannedAt: null,
      scanning: Boolean(view.scanning),
      savedAt: null,
      refused: 0,
      reread: false,
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
