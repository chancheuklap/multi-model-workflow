import React from "react";
import {part} from "../_shared/ui.js";

// Where a ticket runs: grade, host · model · effort, then branch, base, worktree,
// machine and slot; or the line that says it has not run. Source: detail.mjs ticketRuntime.
export function RunBox({runtime, noRunText, "data-ui": ui}) {
  if (!runtime) return <p className="pv-none" data-ui={ui}>{noRunText || "not dispatched yet"}</p>;
  return (
    <div className="pv-run" data-ui={ui}>
      <div className="pv-run-who">
        <span className="pv-run-grade" data-ui={part(ui, "grade")}>{runtime.grade || ""}</span>
        {runtime.model ? <span className="pv-run-model" data-ui={part(ui, "model")}>{runtime.model}</span> : null}
      </div>
      {runtime.rows && runtime.rows.length ? (
        <div className="pv-run-where">
          {runtime.rows.flatMap((row, i) => [
            <span key={`k${i}`} className="pv-run-k" data-ui={part(ui, "key")}>{row.k}</span>,
            <span key={`v${i}`} className="pv-run-v" data-ui={part(ui, "value")}>{row.v}</span>,
          ])}
        </div>
      ) : null}
    </div>
  );
}
