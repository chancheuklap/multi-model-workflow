export function render(host) {
  const root = document.createElement("main");
  root.dataset.storyRoot = "";
  root.dataset.screen = "canvas";
  root.setAttribute("aria-label", "画布：拖动平移，按住 ⌘ 或双指捏合缩放");
  root.style.cssText = "width:864px;height:848px";
  host.replaceChildren(root);
}
