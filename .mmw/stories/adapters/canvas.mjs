import {render as renderProduct} from "/product/canvas.mjs";

export function render(host, data, api) {
  const root = renderProduct(host, {
    view: data.vals.v,
    sel: data.state.sel,
    expanded: data.state.expanded,
  }, api);
  root.dataset.storyRoot = "";
  root.style.cssText = "width:864px;height:848px";
}
