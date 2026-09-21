import React from "react";
import {part} from "../_shared/ui.js";
import {cardShell} from "./card-shell.jsx";

// A decision ticket of a map: a lower card with its kind where a ticket has its pill.
// Source: canvas.mjs decisionCard; `item` is one of canvasView's `decisions`.
export function DecisionCard({item, onPick, "data-ui": ui}) {
  const right = <span className="card-kind" data-ui={part(ui, "kind")}>{item.kind}</span>;
  return cardShell(item, {ui, onPick, lampTitle: false, titleCls: "card-title decision", right, after: null});
}
