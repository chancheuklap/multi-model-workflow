import {mountPage} from "/product/app.mjs";

export function render(host, data, api) {
  host.style.cssText = "width:1440px;height:900px";
  const root = mountPage(host, {data, api, live: false});
  root.dataset.storyRoot = "";
  return root;
}
