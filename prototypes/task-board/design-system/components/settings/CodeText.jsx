import React from "react";

// A command or file name inside the sheet's prose. Source: settings.mjs `span.sheet-code`.
export function CodeText({children, "data-ui": ui}) {
  return <span className="sheet-code" data-ui={ui}>{children}</span>;
}
