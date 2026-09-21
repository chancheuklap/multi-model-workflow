import React from "react";

// The capsule that names the step a ticket is at. Source: board.css "the pill";
// canvas.mjs ticketCard, detail.mjs `pill big …`. `children` replaces the step name
// where the product writes a count beside it (detail.mjs phases-count).
export function StepPill({phase, big, children, "data-ui": ui}) {
  return <span className={big ? `pill big ${phase}` : `pill ${phase}`} data-ui={ui}>{children ?? phase}</span>;
}
