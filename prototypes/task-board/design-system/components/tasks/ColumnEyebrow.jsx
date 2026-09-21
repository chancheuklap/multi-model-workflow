import React from "react";
import {part} from "../_shared/ui.js";

// The small uppercase heading over the task list, with its count. Source: tasks.mjs
// render, `div.col-eyebrow`.
export function ColumnEyebrow({label, count, "data-ui": ui}) {
  return (
    <div className="col-eyebrow" data-ui={ui}>
      <span data-ui={part(ui, "label")}>{label}</span>
      <span data-ui={part(ui, "count")}>{String(count)}</span>
    </div>
  );
}
