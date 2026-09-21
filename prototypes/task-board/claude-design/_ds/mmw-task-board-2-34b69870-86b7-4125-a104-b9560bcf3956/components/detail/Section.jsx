import React from "react";
import {part} from "../_shared/ui.js";

// A ruled block of the detail column with a small uppercase title and a count. Source:
// detail.mjs section (`dp-section`) and ticketSection (`pv-sec`).
export function Section({ticket, title, note, children, "data-ui": ui}) {
  const cls = ticket ? "pv-sec" : "dp-section";
  const titleCls = ticket ? "pv-sec-title" : "dp-section-title";
  return (
    <section className={cls} data-ui={ui}>
      <div className={titleCls}>
        <span data-ui={part(ui, "title")}>{title}</span>
        {note == null ? null : <span data-ui={part(ui, "count")}>{String(note)}</span>}
      </div>
      {children}
    </section>
  );
}
