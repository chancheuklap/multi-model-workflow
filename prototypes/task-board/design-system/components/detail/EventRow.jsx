import React from "react";
import {part} from "../_shared/ui.js";

// One event on the ticket: time, name, one line from its payload, and, opened, every
// payload field and the comment's first line. Source: detail.mjs eventRow and backendDetail.
export function EventRow({item, opened, onToggle, "data-ui": ui}) {
  const warn = item.tone === "warn" || item.tone === "needs-you";
  return (
    <button type="button" className="va-ev" onClick={onToggle} data-ui={ui}>
      <span className="va-t" data-ui={part(ui, "time")}>{item.time}</span>
      <span className={warn ? "va-n warn" : "va-n"} data-ui={part(ui, "name")}>{item.name}</span>
      {item.hasText ? <span className="va-x" data-ui={part(ui, "text")}>{item.text}</span> : null}
      {opened ? (
        <span className="va-x">
          <span className="pv-detail" data-ui={part(ui, "detail")}>
            {(item.detail || []).flatMap((row, i) => [
              <span key={`k${i}`} className="pv-detail-k">{row.k}</span>,
              <span key={`v${i}`} className="pv-detail-v">{row.v}</span>,
            ])}
          </span>
        </span>
      ) : null}
    </button>
  );
}
