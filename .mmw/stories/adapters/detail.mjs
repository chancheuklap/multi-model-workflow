import {find, fromBoard, render as renderProduct} from "/product/detail.mjs";

export function render(host, data, api) {
  const transitions = [];
  let selected = data.select?.node ?? null;
  window.storyTransitions = () => structuredClone(transitions);

  const move = scene => transitions.push({scene, data: null});
  const sceneFor = n => {
    const target = find(data.payload.tasks || [], n);
    if (!target) return null;
    if (target.type === "map") return "Component · 详情.map";
    if (target.type === "spec") return "Component · 详情.spec";
    if (target.type === "decision") return "Component · 详情.decision";
    return "Component · 详情.morning";
  };
  const paint = () => {
    const root = renderProduct(host, fromBoard(data.payload, selected, new Date(data.now)), api, {
      onGoto(n) {
        const scene = sceneFor(n);
        if (!scene) return;
        selected = n;
        move(scene);
        paint();
      },
      onClose() {
        selected = null;
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
