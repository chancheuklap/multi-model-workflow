import {render as renderProduct} from "/product/detail.mjs";

// Scene input is the design page's example data (`DETAIL_SCENES.<scene>`).
// An issue that has a scene is drawn as that view, and the recorded scene name
// is the one for its kind. An issue with no scene enters the screen-contract
// row's `next` and is drawn as that scene's own entry.
const DETAIL = "Component · 详情.";
const KIND_SCENE = {
  ticket: `${DETAIL}morning`,
  spec: `${DETAIL}spec`,
  map: `${DETAIL}map`,
  decision: `${DETAIL}decision`,
};

function contractNext(ui, kind) {
  if (ui === "详情.blocker" && kind === "decision") return `${DETAIL}decision`;
  if (ui === "详情.blocker" || ui === "详情.blocks" || ui === "详情.ticket-row") {
    return `${DETAIL}morning`;
  }
  if (ui === "详情.spec-row") return `${DETAIL}spec`;
  if (ui === "详情.decision-row") return `${DETAIL}decision`;
  if (ui === "详情.origin.link" && kind === "spec") return `${DETAIL}map`;
  if (ui === "详情.origin.link") return `${DETAIL}spec`;
  return null;
}

async function loadScenes() {
  const response = await fetch("/scenes.json");
  if (!response.ok) throw new Error(`scenes.json returned ${response.status}`);
  const scenes = await response.json();
  const names = scenes
    .map(scene => scene.name)
    .filter(name => String(name || "").startsWith(DETAIL));
  return Promise.all(names.map(async name => {
    const scene = await fetch(`/scene-input.json?scene=${encodeURIComponent(name)}`);
    if (!scene.ok) throw new Error(`scene input ${name} returned ${scene.status}`);
    return {name, view: await scene.json()};
  }));
}

export function render(host, data, api) {
  const transitions = [];
  window.storyTransitions = () => structuredClone(transitions);
  const byGh = new Map();
  const byScene = new Map();
  const index = sceneView => {
    if (sceneView && !sceneView.empty && sceneView.gh != null && !byGh.has(sceneView.gh)) {
      byGh.set(sceneView.gh, sceneView);
    }
  };
  index(data);
  const ready = loadScenes().then(loaded => {
    for (const {name, view: sceneView} of loaded) {
      byScene.set(name, sceneView);
      index(sceneView);
    }
    window.storyDetailLoaded = true;
  });
  window.storyDetailReady = ready;
  ready.catch(error => {
    window.storyDetailError = String(error && error.message || error);
  });

  let view = data;
  const move = scene => transitions.push({scene, data: null});
  const unloaded = n => {
    const fact = window.storyDetailError || "storyDetailLoaded is not set";
    const root = host.querySelector("[data-ui='详情.root']");
    if (!root) return;
    root.textContent = `Scene input did not load (${fact}). The story cannot draw #${n}. Reload the story page.`;
  };
  const paint = () => {
    const root = renderProduct(host, view, api, {
      onGoto(n, ui) {
        if (window.storyDetailError || !window.storyDetailLoaded) {
          unloaded(n);
          return;
        }
        const known = byGh.get(n);
        if (known) {
          const scene = KIND_SCENE[known.kind];
          if (!scene) return;
          view = known;
          move(scene);
          paint();
          return;
        }
        const scene = contractNext(ui, view && view.kind);
        const entry = scene && byScene.get(scene);
        if (!entry) return;
        view = entry;
        move(scene);
        paint();
      },
      onClose() {
        view = {empty: true};
        move(`${DETAIL}nothing-selected`);
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
