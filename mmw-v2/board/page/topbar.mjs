export function render(host, data = {}, api = undefined) {
  const root = document.createElement("header");
  root.dataset.screen = "topbar";
  host.replaceChildren(root);
  return root;
}
