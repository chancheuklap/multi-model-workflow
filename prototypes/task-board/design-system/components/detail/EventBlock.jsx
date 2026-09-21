import React from "react";
import {part} from "../_shared/ui.js";

// One step of a ticket's history: its pill and time span, and, open, one row per event.
// A closed block shows the event most worth opening it for. Source: detail.mjs
// phaseBlock; `block` is one of detail.mjs phaseBlocksFrom's blocks.
export function EventBlock({block, opened, onToggle, children, "data-ui": ui}) {
  return (
    <div className={block.tone === "plain" ? "va-block" : "va-block warn"} data-ui={ui}>
      <button type="button" className="va-bhead" onClick={onToggle} data-ui={part(ui, "toggle")}>
        <span className="va-chev" data-ui={part(ui, "chev")}>{opened ? "▾" : "▸"}</span>
        <span className={`pill ${block.phase}`} data-ui={part(ui, "phase")}>{block.phase}</span>
        <span className="va-bsum" data-ui={part(ui, "summary")}>{opened ? "" : block.summary}</span>
        <span className="va-btime" data-ui={part(ui, "time")}>{opened ? block.span : block.from}</span>
      </button>
      {opened ? <div className="va-body">{children}</div> : null}
    </div>
  );
}
