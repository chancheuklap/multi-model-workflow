import React from "react";
import {part} from "../_shared/ui.js";
import {Select} from "./Select.jsx";
import {ProblemList} from "./ProblemList.jsx";

// Which runner starts sessions. Source: settings.mjs paint `div.runner-row`.
export function RunnerRow({cls, value, disabled, opts, bads = [], onChange, "data-ui": ui}) {
  return (
    <div className="runner-row" data-ui={ui}>
      <div className="role-name">
        <span className="role-agent" data-ui={part(ui, "label")}>runner</span>
        <span className="role-what" data-ui={part(ui, "what")}>用什么起 session</span>
      </div>
      <Select cls={cls} value={value} disabled={disabled} label="runner" opts={opts} onChange={onChange} data-ui={part(ui, "select")} />
      {bads.length ? <ProblemList items={bads} data-ui={part(ui, "problem")} /> : null}
    </div>
  );
}
