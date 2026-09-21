import React from "react";
import {part} from "../_shared/ui.js";

// A save refused because the configuration changed elsewhere, with a way to read it
// again. Source: settings.mjs paint `div.refused`.
export function RefusedBanner({text, onReread, "data-ui": ui}) {
  return (
    <div className="refused" role="alert" data-ui={ui}>
      <p className="refused-text" data-ui={part(ui, "text")}><b>没有保存。</b>{text}</p>
      <button type="button" className="btn" onClick={onReread} data-ui={part(ui, "reread")}>重新读取</button>
    </div>
  );
}
