import React from "react";

// When the page last read GitHub, or that the last read failed. Source: topbar.mjs
// render, `div.readstate`.
export function ReadState({failed, text, "data-ui": ui}) {
  return <div className={failed ? "readstate failed" : "readstate"} data-ui={ui}>{text}</div>;
}
