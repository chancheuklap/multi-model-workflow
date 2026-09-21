import React from "react";
import {part} from "../_shared/ui.js";

// A sub-issue a ticket opened, with its kind; the three kinds that need the owner are
// orange. Source: detail.mjs ticketCard Sub-issues.
export function SubIssueRow({kid, "data-ui": ui}) {
  return (
    <div className="pv-rel" data-ui={ui}>
      <span className={`lamp ${kid.lamp}`} data-ui={part(ui, "lamp")}></span>
      <span className="pv-rel-n" data-ui={part(ui, "number")}>{kid.num}</span>
      <span className="pv-rel-t" data-ui={part(ui, "title")}>{kid.title}</span>
      <span className={kid.hot ? "pv-kind hot" : "pv-kind"} data-ui={part(ui, "kind")}>{kid.kind}</span>
    </div>
  );
}
