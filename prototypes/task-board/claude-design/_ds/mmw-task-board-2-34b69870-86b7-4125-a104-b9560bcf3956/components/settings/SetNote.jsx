import React from "react";

// A quiet paragraph under a block of the sheet. Source: settings.mjs paint `p.set-note`.
export function SetNote({children, "data-ui": ui}) {
  return <p className="set-note" data-ui={ui}>{children}</p>;
}
