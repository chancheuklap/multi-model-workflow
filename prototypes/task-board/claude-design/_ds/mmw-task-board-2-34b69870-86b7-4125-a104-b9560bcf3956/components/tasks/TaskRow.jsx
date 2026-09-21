import React from "react";
import {part} from "../_shared/ui.js";

// One task in the left column: its lamp, number and kind, title, and landed progress.
// Source: tasks.mjs rowButton. `row` is one row of tasks.mjs taskListView.
export function TaskRow({row, onPick, "data-ui": ui}) {
  return (
    <button type="button" className={row.cls} onClick={onPick} data-ui={ui}>
      <span className={row.lampCls} title={row.lampWord} data-ui={part(ui, "lamp")}></span>
      <span className="task-meta" data-ui={part(ui, "meta")}>{row.meta}</span>
      <span className={row.titleCls} data-ui={part(ui, "title")}>{row.title}</span>
      <span className="task-progress">
        <span className="bar"><span className="bar-fill" style={{width: row.barStyle.width}} data-ui={part(ui, "bar")}></span></span>
        <span className="task-count" data-ui={part(ui, "count")}>{row.count}</span>
      </span>
    </button>
  );
}
