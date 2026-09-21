import React from "react";
import {part} from "../_shared/ui.js";
import {cardShell} from "./card-shell.jsx";

// A ticket: lamp and number, step pill, title, and where it runs. Source: canvas.mjs
// ticketCard; `item` is one of canvasView's `tickets`.
export function TicketCard({item, onPick, "data-ui": ui}) {
  const right = <span className={item.pillCls} data-ui={part(ui, "phase")}>{item.phase}</span>;
  const after = <div className={item.runCls} data-ui={part(ui, "run")}>{item.run}</div>;
  return cardShell(item, {ui, onPick, lampTitle: true, titleCls: "card-title", right, after});
}
