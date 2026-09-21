import React from "react";

// What the task list says when no ticket carries the map label. Source: tasks.mjs
// render, `p.tasks-empty`.
export function TasksEmpty({"data-ui": ui}) {
  return <p className="tasks-empty" data-ui={ui}>没有带 mmw:map label 的 ticket。</p>;
}
