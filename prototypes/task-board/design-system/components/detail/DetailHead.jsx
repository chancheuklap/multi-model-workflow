import React from "react";
import {part} from "../_shared/ui.js";

// The first row of the detail column: what is shown, then GitHub and close. A ticket's
// head carries the GitHub link; a map, spec or decision ticket puts it at the bottom
// (GithubButton). Source: detail.mjs ticketCard `pv-head`, card `dp-head`.
export function DetailHead({ticket, eyebrow, onGithub, onClose, "data-ui": ui}) {
  if (ticket) {
    return (
      <div className="pv-head" data-ui={ui}>
        <span className="pv-eyebrow" data-ui={part(ui, "eyebrow")}>{eyebrow || "Ticket"}</span>
        <button type="button" className="pv-gh" onClick={onGithub} data-ui={part(ui, "github")}>GitHub ↗</button>
        <button type="button" className="pv-close" aria-label="关闭详情" onClick={onClose} data-ui={part(ui, "close")}>×</button>
      </div>
    );
  }
  return (
    <div className="dp-head" data-ui={ui}>
      <span className="dp-eyebrow" data-ui={part(ui, "eyebrow")}>{eyebrow}</span>
      <button type="button" className="dp-close" aria-label="关闭详情" onClick={onClose} data-ui={part(ui, "close")}>×</button>
    </div>
  );
}
