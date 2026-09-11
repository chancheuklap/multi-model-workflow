export function render(host, data = {}, api = undefined) {
  const root = document.createElement("section");
  root.dataset.screen = "settings";
  host.replaceChildren(root);
  return root;
}
