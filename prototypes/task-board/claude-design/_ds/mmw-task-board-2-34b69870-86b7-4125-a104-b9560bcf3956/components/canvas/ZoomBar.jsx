import React from "react";
import {part} from "../_shared/ui.js";

// Zoom out, the zoom level, zoom in, and fit. Source: canvas.mjs zoomBar.
export function ZoomBar({level, onOut, onIn, onFit, "data-ui": ui}) {
  return (
    <div className="zoom" data-ui={ui}>
      <button type="button" className="zoom-btn" aria-label="zoom out" onClick={onOut} data-ui={part(ui, "out")}>−</button>
      <span className="zoom-level" data-ui={part(ui, "level")}>{level}</span>
      <button type="button" className="zoom-btn" aria-label="zoom in" onClick={onIn} data-ui={part(ui, "in")}>+</button>
      <span className="zoom-sep"></span>
      <button type="button" className="zoom-btn text" onClick={onFit} data-ui={part(ui, "fit")}>fit</button>
    </div>
  );
}
