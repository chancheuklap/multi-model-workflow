import React from "react";
import {part} from "../_shared/ui.js";

// The four agents' rows under one column head, so the dropdowns line up. Source:
// settings.mjs paint `div.roles`.
export function RolesTable({children, "data-ui": ui}) {
  return (
    <div className="roles" data-ui={ui}>
      <div className="roles-head" data-ui={part(ui, "head")}><span>agent</span><span>host</span><span>model</span><span>effort</span></div>
      {children}
    </div>
  );
}
