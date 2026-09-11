import {render as topbar} from "./topbar.mjs";
import {render as tasks} from "./tasks.mjs";
import {render as canvas} from "./canvas.mjs";
import {render as detail} from "./detail.mjs";
import {render as settings} from "./settings.mjs";

export function mountPage(doc = document) {
  for (const [mount, render] of Object.entries({topbar, tasks, canvas, detail, settings})) {
    render(doc.querySelector(`[data-mount="${mount}"]`));
  }
}

if (typeof document !== "undefined") mountPage(document);
