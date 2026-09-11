export function render(host, data = {}, api = undefined) {
  const root = document.createElement("section");
  root.dataset.screen = "canvas";
  root.setAttribute("aria-label", "画布");
  host.replaceChildren(root);
  return root;
}
