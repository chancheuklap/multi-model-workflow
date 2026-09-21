import React from "react";
import {part} from "../_shared/ui.js";

// How many of a spec's or map's tickets sit at each step. Source: detail.mjs
// containerBody `phases-count`.
export function PhaseCounts({phases = [], "data-ui": ui}) {
  return (
    <div className="phases-count" data-ui={ui}>
      {phases.map((item, i) => <span key={i} className={`pill ${item.phase}`} data-ui={part(ui, "item")}>{item.label}</span>)}
    </div>
  );
}
