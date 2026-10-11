import {LocalConfig} from "/product/local-config.mjs";
import {fromPayload, render as renderProduct} from "/product/settings.mjs";

// Scene input is SETTINGS_SCENES.<scene>: the settings answer (payload) plus
// this scene's page edits. The sheet's own logic turns that into the view.
// Element parity compares the result with the design page's SETTINGS_VIEWS.

function applyPage(model, page) {
  for (const [agent, cell, value] of page.edit || []) {
    LocalConfig.setCell(model.scan, model.st.draft, agent, cell, value);
  }
  if (page.scanning) model.st.scanning = true;
  if (page.refused) model.st.refused = page.refused;
  if (page.modifiedAt) model.st.modifiedAt = page.modifiedAt;
  if (page.saveAt) {
    model.st.saved = structuredClone(model.st.draft);
    model.st.savedAt = page.saveAt;
  }
  if (page.serverFlags) {
    model.st.serverFlags = page.serverFlags.map(error => {
      const [key, cell] = String(error.cell).split(".");
      return {key, cell: cell || key, text: error.reason};
    });
  }
  return model;
}

export function render(host, data, api) {
  const transitions = [];
  window.storyTransitions = () => structuredClone(transitions);
  const root = renderProduct(host, applyPage(fromPayload(data.payload), data.page || {}), api, {
    onState(state) {
      transitions.push({
        scene: state === "closed" ? "settings-closed" : `Component · 本机配置.${state}`,
      });
    },
  });
  root.dataset.storyRoot = "";
  return root;
}
