import {render as renderProduct} from "/product/settings.mjs";

export function render(host, data, api) {
  host.style.cssText = "width:1440px;height:900px;position:relative;background:#e6e3df";
  document.documentElement.style.background = "#e6e3df";
  document.body.style.background = "#e6e3df";
  const root = renderProduct(host, data, api);
  root.dataset.storyRoot = "";
  return root;
}
