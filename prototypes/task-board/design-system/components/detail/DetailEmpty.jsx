import React from "react";
import {part} from "../_shared/ui.js";

// What the detail column says when nothing is picked. Source: detail.mjs render `dp-empty`.
export function DetailEmpty({title, text, "data-ui": ui}) {
  return (
    <div className="dp-empty" data-ui={ui}>
      <p className="dp-empty-title" data-ui={part(ui, "title")}>{title}</p>{text}
    </div>
  );
}
