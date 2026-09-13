import {fromScene, render as renderProduct} from "/product/detail.mjs";

export function render(host, data, api) {
  const root = renderProduct(host, fromScene(data), api);
  root.dataset.storyRoot = "";
  root.style.cssText = "width:340px;height:848px";
}
