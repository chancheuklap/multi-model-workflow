import {render as renderProduct} from "/product/canvas.mjs";

export function render(host, data, api) {
  const transitions = [];
  window.storyTransitions = () => structuredClone(transitions);
  const move = (scene, value) => transitions.push({scene, data: value});
  const tasks = data.payload?.tasks || [];
  const taskN = data.select?.task ?? tasks[0]?.n ?? null;
  const task = tasks.find(candidate => candidate.n === taskN) || null;
  const root = renderProduct(host, {
    task,
    sel: data.select?.node ?? null,
    onSelectNode(node) {
      move("Component · 画布.morning", {node});
    },
    onToggle(node, expanded) {
      move(expanded.includes(node) ? "container-expanded" : "container-collapsed",
        {node, expanded});
    },
    onViewport(scene, view) {
      move(scene, view);
    },
  }, api);
  root.dataset.storyRoot = "";
  root.style.cssText = "width:864px;height:848px";
}
