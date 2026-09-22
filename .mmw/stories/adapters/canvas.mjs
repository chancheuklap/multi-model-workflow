import {render as renderProduct} from "/product/canvas.mjs";

// The scene input is the design page's own example data (`CANVAS_SCENES.<scene>`):
// which node is selected, which containers are open, and the tree with the lamp,
// phase and run the page draws. The component lays that tree out. A field the
// scene does not carry is not filled in here.
export function render(host, data, api) {
  const transitions = [];
  window.storyTransitions = () => structuredClone(transitions);
  const move = (scene, value) => transitions.push({scene, data: value});
  const root = renderProduct(host, {
    task: data.task ?? null,
    sel: data.selected ?? null,
    expanded: data.expanded ?? [],
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
