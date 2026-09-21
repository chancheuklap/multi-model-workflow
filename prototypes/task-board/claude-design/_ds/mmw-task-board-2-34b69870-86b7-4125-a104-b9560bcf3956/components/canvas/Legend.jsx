import React from "react";
import {part} from "../_shared/ui.js";

// What each line and mark on the canvas means. Source: canvas.mjs legend.
export function Legend({"data-ui": ui}) {
  const item = (cls, text, name) => (
    <span className="legend-item" data-ui={part(ui, name)}><span className={cls}></span>{text}</span>
  );
  return (
    <div className="legend" data-ui={ui}>
      {item("legend-line", "contains · released", "walked")}
      {item("legend-line flow", "released · working", "flow")}
      {item("legend-line blocked", "blocked", "blocked")}
      {item("legend-bar", "closing pass", "closeout")}
    </div>
  );
}
