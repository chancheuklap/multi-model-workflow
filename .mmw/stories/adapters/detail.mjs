import {render as renderProduct} from "/product/detail.mjs";

// The scene input is the design page's own example data (`DETAIL_SCENES.<scene>`).
// A click draws another of those views when one of them is that issue, and records
// the scene name for that kind. An issue with no scene is not given a made-up view.
const DETAIL = "Component · 详情.";
const KIND_SCENE = {
  ticket: `${DETAIL}morning`,
  spec: `${DETAIL}spec`,
  map: `${DETAIL}map`,
  decision: `${DETAIL}decision`,
};

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
    return scene.json();
  }));
}

export function render(host, data, api) {
  const transitions = [];
  window.storyTransitions = () => structuredClone(transitions);
  const byGh = new Map();
  const index = sceneView => {
    if (sceneView && !sceneView.empty && sceneView.gh != null && !byGh.has(sceneView.gh)) {
      byGh.set(sceneView.gh, sceneView);
    }
  };
  index(data);
  const ready = loadScenes().then(sceneViews => {
    for (const sceneView of sceneViews) index(sceneView);
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
      onGoto(n) {
        if (window.storyDetailError || !window.storyDetailLoaded) {
          unloaded(n);
          return;
        }
        const known = byGh.get(n);
        const scene = known && KIND_SCENE[known.kind];
        if (!scene) return;
        view = known;
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
