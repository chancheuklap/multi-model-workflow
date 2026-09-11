export function render(host) {
  const root = document.createElement("section");
  root.dataset.screen = "settings";
  host.replaceChildren(root);
  return root;
}
