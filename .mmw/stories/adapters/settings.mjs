export function render(host) {
  const root = document.createElement("div");
  root.dataset.storyRoot = "";
  root.dataset.screen = "settings";
  root.style.cssText = "width:1440px;height:900px";
  host.replaceChildren(root);
}
