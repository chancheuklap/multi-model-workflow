export function render(host) {
  const root = document.createElement("aside");
  root.dataset.screen = "detail";
  root.setAttribute("aria-label", "详情");
  host.replaceChildren(root);
  return root;
}
