/* Mini dc-import for the story-parity fixture. No React, no CDN. */
"use strict";
window.DCLogic = class DCLogic {};

const COPY = {
  alpha: "Alpha scene copy",
  beta: "Beta scene copy",
  gamma: "Gamma scene copy",
};

class DcImport extends HTMLElement {
  connectedCallback() {
    this._render();
  }

  async _render() {
    let root = document.getElementById("dc-root");
    if (!root) {
      root = document.createElement("div");
      root.id = "dc-root";
      document.body.appendChild(root);
    }
    const name = this.getAttribute("name") || "";
    const scenario = this.getAttribute("scenario") || "alpha";
    const url = "./" + encodeURIComponent(name) + ".dc.html";
    const html = await (await fetch(url)).text();
    const doc = new DOMParser().parseFromString(html, "text/html");
    const src = doc.querySelector("x-dc");
    const helmet = src && src.querySelector("helmet");
    if (helmet) {
      for (const node of [...helmet.querySelectorAll("style")]) {
        document.head.appendChild(document.importNode(node, true));
      }
      helmet.remove();
    }
    root.innerHTML = src ? src.innerHTML : "";
    const copy = COPY[scenario] || "";
    root.innerHTML = root.innerHTML.replace(/\{\{\s*copy\s*\}\}/g, copy);
  }
}

customElements.define("dc-import", DcImport);
