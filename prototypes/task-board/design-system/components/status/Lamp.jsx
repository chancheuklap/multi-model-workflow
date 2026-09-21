import React from "react";

// One dot that answers "does this need me". Source: board.css "the lamp"; the product
// writes `lamp <size> <tone>` (detail.mjs `lamp big …`, canvas.mjs `lamp small …`).
export function Lamp({tone = "hollow", size, title, "data-ui": ui}) {
  const cls = ["lamp", size, tone].filter(Boolean).join(" ");
  return <span className={cls} title={title} data-ui={ui}></span>;
}
