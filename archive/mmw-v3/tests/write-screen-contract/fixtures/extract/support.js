"use strict";
window.DCLogic = class DCLogic {};

class DcImport extends HTMLElement {
  connectedCallback() { this.renderPage(); }

  async renderPage() {
    let root = document.getElementById("dc-root");
    if (!root) {
      root = document.createElement("div");
      root.id = "dc-root";
      document.body.appendChild(root);
    }
    const name = this.getAttribute("name") || "";
    const scene = this.getAttribute("scene") || "ready";
    const response = await fetch("./" + encodeURIComponent(name) + ".dc.html");
    const source = new DOMParser().parseFromString(await response.text(), "text/html");
    const component = source.querySelector("x-dc");
    const helmet = component && component.querySelector("helmet");
    if (helmet) {
      for (const node of helmet.querySelectorAll("style")) {
        document.head.appendChild(document.importNode(node, true));
      }
      helmet.remove();
    }
    root.innerHTML = component ? component.innerHTML : "";
    for (const node of root.querySelectorAll("[data-only-scene]")) {
      if (node.getAttribute("data-only-scene") !== scene) node.remove();
    }
    const viewport = root.querySelector('[data-ui="inventory.viewport"]');
    if (viewport) {
      viewport.textContent = navigator.language + " " + innerWidth + "x" + innerHeight;
    }
  }
}

customElements.define("dc-import", DcImport);
