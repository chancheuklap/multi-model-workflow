import React from "react";

// The title of what the detail column shows. Source: detail.mjs `h2.pv-title`, `h2.dp-title`.
export function DetailTitle({ticket, title, "data-ui": ui}) {
  return <h2 className={ticket ? "pv-title" : "dp-title"} data-ui={ui}>{title}</h2>;
}
