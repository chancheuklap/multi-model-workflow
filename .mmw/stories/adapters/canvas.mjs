import {render as renderProduct} from "/product/canvas.mjs";

export function render(host, data, api) {
  host.style.cssText = "width:864px;height:848px";
  const root = renderProduct(host, data, api);
  root.dataset.storyRoot = "";
  root.style.cssText = "width:864px;height:848px";
}
