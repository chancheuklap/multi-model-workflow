export function render(host) {
  const root = document.createElement("nav");
  root.dataset.screen = "tasks";
  root.setAttribute("aria-label", "任务");
  host.replaceChildren(root);
  return root;
}
