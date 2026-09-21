import React from "react";
import {part} from "../_shared/ui.js";

// What the canvas says before any task exists. Source: canvas.mjs emptyState.
export function CanvasEmpty({"data-ui": ui}) {
  return (
    <div className="canvas-empty" data-ui={ui}>
      <div>
        <p className="canvas-empty-title" data-ui={part(ui, "title")}>The Night 还没开始</p>
        <p className="canvas-empty-text" data-ui={part(ui, "text")}>The Night 是一次讨论开出的那张 ticket。给它打上 <span className="code">mmw:map</span> label，下一次读取时它和它下面的 spec、ticket 就会出现在这里。</p>
      </div>
    </div>
  );
}
