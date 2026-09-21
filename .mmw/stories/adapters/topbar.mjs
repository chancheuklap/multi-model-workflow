import {fromBoard, render as renderProduct} from "/product/topbar.mjs";

export function render(host, data, api) {
  const root = renderProduct(host, fromBoard(data.payload, new Date(data.now)), api);
  root.dataset.storyRoot = "";
  root.style.height = "52px";
}
