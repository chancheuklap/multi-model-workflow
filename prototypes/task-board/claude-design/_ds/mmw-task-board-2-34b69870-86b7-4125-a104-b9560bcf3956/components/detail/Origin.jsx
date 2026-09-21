import React from "react";
import {part} from "../_shared/ui.js";

// Where the shown issue sits: its number, then links to its spec and map. Source:
// detail.mjs origin (`dp-origin`) and ticketCard (`pv-links`).
export function Origin({ticket, num, links = [], onGoto, "data-ui": ui}) {
  const cls = ticket ? "pv-links" : "dp-origin";
  const linkCls = ticket ? "pv-link" : "dp-link";
  return (
    <div className={cls} data-ui={ui}>
      <span data-ui={part(ui, "number")}>{num}</span>
      {links.flatMap((link, i) => [
        <span key={`d${i}`}>·</span>,
        <button key={`l${i}`} type="button" className={linkCls} onClick={() => onGoto && onGoto(link.n)}
          data-ui={part(ui, "link")}>{link.label}</button>,
      ])}
    </div>
  );
}
