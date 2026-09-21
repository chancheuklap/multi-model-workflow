import React from "react";

// Every line on the canvas: the trunk, the expansions, and the blocking curves coloured
// by how the wait stands. Source: canvas.mjs edgesSVG, whose markup `svg` is.
export function Edges({svg, "data-ui": ui}) {
  return <div className="edges-host" data-ui={ui} dangerouslySetInnerHTML={{__html: svg || ""}}></div>;
}
