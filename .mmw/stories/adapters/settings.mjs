import {render as renderProduct} from "/product/settings.mjs";

export function render(host, data, api) {
  const root = renderProduct(host, data, api);
  root.dataset.storyRoot = "";
  root.style.cssText = "width:1440px;height:900px";
}
