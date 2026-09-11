export function render(host) {
  const root = document.createElement("nav");
  root.dataset.storyRoot = "";
  root.dataset.screen = "tasks";
  root.setAttribute("aria-label", "任务");
  root.style.cssText = "width:236px;height:848px";
  host.replaceChildren(root);
}
