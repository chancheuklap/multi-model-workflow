export function render(host) {
  const root = document.createElement("header");
  root.dataset.screen = "topbar";
  host.replaceChildren(root);
  return root;
}
