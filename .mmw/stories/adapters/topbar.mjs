import {render as renderProduct} from "/product/topbar.mjs";

export function render(host, data, api) {
  const root = renderProduct(host, data, api);
  root.dataset.storyRoot = "";
  root.style.height = "52px";
}
