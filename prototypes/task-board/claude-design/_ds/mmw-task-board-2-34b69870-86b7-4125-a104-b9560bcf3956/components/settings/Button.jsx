import React from "react";

// A button of the sheet: plain, primary (ink fill), or a text link. Source: settings.mjs
// `.btn`, `.btn.primary`, `.linkbtn`.
export function Button({kind, disabled, onClick, children, "data-ui": ui}) {
  const cls = kind === "primary" ? "btn primary" : kind === "link" ? "linkbtn" : "btn";
  return <button type="button" className={cls} disabled={!!disabled} onClick={onClick} data-ui={ui}>{children}</button>;
}
