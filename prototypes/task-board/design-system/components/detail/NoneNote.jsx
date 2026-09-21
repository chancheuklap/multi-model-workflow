import React from "react";

// The one line a list shows when it is empty: "none" under a blocking list, "no events
// yet" under Events. Source: detail.mjs `p.rel-none`, `p.pv-none`.
export function NoneNote({ticket, text, "data-ui": ui}) {
  return <p className={ticket ? "pv-none" : "rel-none"} data-ui={ui}>{text}</p>;
}
