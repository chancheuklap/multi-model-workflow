import React from "react";
import {part} from "../_shared/ui.js";

// The frame every canvas card shares. Source: canvas.mjs cardShell and cardHit: the
// whole card is one button (`card-hit`), then the top row, the title, and what follows.
export function cardShell(item, {ui, onPick, lampTitle, titleCls, right, after}) {
  return (
    <div className={item.cls} style={item.pos} title={item.title} data-ui={ui}>
      <button type="button" className="card-hit" aria-label={`#${item.n} ${item.title}`} onClick={onPick}
        data-ui={part(ui, "open")}></button>
      <div className="card-top">
        <span className={item.lampCls} title={lampTitle ? item.lampWord : undefined} data-ui={part(ui, "lamp")}></span>
        <span className="card-num" data-ui={part(ui, "num")}>{item.num}</span>
        <span className="card-right">{right}</span>
      </div>
      <div className={titleCls} data-ui={part(ui, "title")}>{item.title}</div>
      {after}
    </div>
  );
}
