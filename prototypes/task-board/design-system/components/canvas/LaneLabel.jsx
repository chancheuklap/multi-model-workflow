import React from "react";

// A small caption over a band of cards, or the warning over a blocking cycle. Source:
// canvas.mjs canvasView `labels`.
export function LaneLabel({label, "data-ui": ui}) {
  return <div className={label.cls} style={label.pos} data-ui={ui}>{label.text}</div>;
}
