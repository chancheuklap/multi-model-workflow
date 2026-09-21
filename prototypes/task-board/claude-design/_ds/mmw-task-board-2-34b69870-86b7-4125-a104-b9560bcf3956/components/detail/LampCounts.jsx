import React from "react";
import {part} from "../_shared/ui.js";

// How many of a spec's or map's tickets sit under each lamp. Source: detail.mjs
// containerBody `lamps-count`.
export function LampCounts({lamps = [], "data-ui": ui}) {
  return (
    <div className="lamps-count" data-ui={ui}>
      {lamps.map((item, i) => (
        <span key={i} className="lc-item" data-ui={part(ui, "item")}>
          <span className={`lamp ${item.lamp}`}></span>{item.word}<span className="lc-n">{item.n}</span>
        </span>
      ))}
    </div>
  );
}
