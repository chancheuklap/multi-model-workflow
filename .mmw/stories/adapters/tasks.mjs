import {render as renderProduct} from "/product/tasks.mjs";

export function render(host, data, api) {
  const root = renderProduct(host, {
    view: data.vals.v,
    selectedTask: data.state.task,
  }, api);
  root.dataset.storyRoot = "";
  root.style.cssText = "width:236px;height:848px";
}
