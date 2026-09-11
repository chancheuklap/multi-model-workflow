import {render as renderProduct} from "/product/tasks.mjs";

export function render(host, data, api) {
  host.style.cssText = "width:236px;height:848px";
  const root = renderProduct(host, data, api);
  root.dataset.storyRoot = "";
  root.style.cssText = "width:236px;height:848px";
}
