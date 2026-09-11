export function render(host) {
  const root = document.createElement("aside");
  root.dataset.storyRoot = "";
  root.dataset.screen = "detail";
  root.setAttribute("aria-label", "详情");
  root.style.cssText = "width:340px;height:848px";
  host.replaceChildren(root);
}
