export function render(host) {
  const root = document.createElement("header");
  root.dataset.storyRoot = "";
  root.dataset.screen = "topbar";
  root.style.height = "52px";
  host.replaceChildren(root);
}
