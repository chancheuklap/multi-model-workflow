import React from "react";
import {part} from "../_shared/ui.js";

// The word mark at the left of the top bar. Source: topbar.mjs render, `div.brand`.
export function Brand({repo, "data-ui": ui}) {
  return (
    <div className="brand" data-ui={ui}>
      <span className="brand-mark" data-ui={part(ui, "mark")}>MMW</span>
      <span className="brand-name" data-ui={part(ui, "name")}>task board</span>
      <span className="brand-repo" data-ui={part(ui, "repo")}>{repo}</span>
    </div>
  );
}
