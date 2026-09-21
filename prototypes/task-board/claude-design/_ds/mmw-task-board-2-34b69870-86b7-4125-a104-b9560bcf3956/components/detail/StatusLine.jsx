import React from "react";
import {part} from "../_shared/ui.js";

// The lamp, its word, the step (tickets only) and the elapsed time or landed count.
// Source: detail.mjs ticketCard `va-status`, card `dp-status`.
export function StatusLine({ticket, lamp, statusWord, phase, elapsed, "data-ui": ui}) {
  if (ticket) {
    return (
      <div className="va-status" data-ui={ui}>
        <span className={`lamp big ${lamp}`} data-ui={part(ui, "lamp")}></span>
        <span className={`va-word ${lamp}`} data-ui={part(ui, "status")}>{statusWord}</span>
        <span className={`pill big ${phase}`} data-ui={part(ui, "phase")}>{phase}</span>
        <span className="va-elapsed" data-ui={part(ui, "elapsed")}>{elapsed || ""}</span>
      </div>
    );
  }
  return (
    <div className="dp-status" data-ui={ui}>
      <span className={`lamp big ${lamp}`} data-ui={part(ui, "lamp")}></span>
      <span className={`status-word ${lamp}`} data-ui={part(ui, "status")}>{statusWord}</span>
      <span className="dp-elapsed" data-ui={part(ui, "elapsed")}>{elapsed || ""}</span>
    </div>
  );
}
