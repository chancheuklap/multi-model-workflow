import React from "react";
import {part} from "../_shared/ui.js";

// Why the lamp is orange: each open decision, fault or contract sub-issue, a hand-back,
// or a merge that bounced. Source: detail.mjs ticketCard `pv-why`.
export function NeedsYou({why = [], "data-ui": ui}) {
  return (
    <div className="pv-why" data-ui={ui}>
      <span className="pv-why-t" data-ui={part(ui, "title")}>Needs you</span>
      {why.map((item, i) => <span key={i} data-ui={part(ui, "item")}><b>{item.head}</b> {item.body}</span>)}
    </div>
  );
}
