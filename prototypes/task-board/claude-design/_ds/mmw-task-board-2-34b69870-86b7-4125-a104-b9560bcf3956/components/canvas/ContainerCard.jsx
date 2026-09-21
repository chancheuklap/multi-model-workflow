import React from "react";
import {part} from "../_shared/ui.js";
import {cardShell} from "./card-shell.jsx";

// A map or spec on the canvas trunk: lamp, number, landed count, expand chevron, title
// and progress bar. Source: canvas.mjs containerCard; `item` is one of canvasView's
// `containers`.
export function ContainerCard({item, onPick, onToggle, "data-ui": ui}) {
  const right = [<span key="c" className="card-count" data-ui={part(ui, "count")}>{item.count}</span>];
  if (item.canExpand) {
    right.push(
      <button key="x" type="button" className="chev" aria-label={item.toggleLabel} data-ui={part(ui, "expand")}
        onClick={event => { event.stopPropagation(); if (onToggle) onToggle(item.n); }}>{item.chev}</button>);
  }
  const after = (
    <div className="card-bar"><div className="card-bar-fill" style={{width: item.barStyle.width}} data-ui={part(ui, "bar")}></div></div>
  );
  return cardShell(item, {ui, onPick, lampTitle: true, titleCls: item.titleCls, right, after});
}
