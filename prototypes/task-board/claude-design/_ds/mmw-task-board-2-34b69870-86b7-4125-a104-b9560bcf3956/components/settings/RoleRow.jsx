import React from "react";
import {part} from "../_shared/ui.js";
import {Select} from "./Select.jsx";
import {ProblemList} from "./ProblemList.jsx";

// One agent's host, model and effort, with what is wrong with them. Source: settings.mjs
// paint `div.role`; `row` is one of local-config.mjs settingsView `rows`.
export function RoleRow({row, onCell, "data-ui": ui}) {
  const set = cell => value => onCell && onCell(row.agent, cell, value);
  return (
    <div className="role" data-ui={ui}>
      <div className="role-name">
        <span className="role-agent" data-ui={part(ui, "agent")}>{row.agent}</span>
        <span className="role-what" data-ui={part(ui, "what")}>{row.what}</span>
      </div>
      <Select cls={row.hostCls} value={row.host} disabled={row.hostOff} label={row.hostLabel} opts={row.hostOpts} onChange={set("host")} data-ui={part(ui, "host")} />
      <Select cls={row.modelCls} value={row.model} disabled={row.modelOff} label={row.modelLabel} opts={row.modelOpts} onChange={set("model")} data-ui={part(ui, "model")} />
      <Select cls={row.effortCls} value={row.effort} disabled={row.effortOff} label={row.effortLabel} opts={row.effortOpts} onChange={set("effort")} data-ui={part(ui, "effort")} />
      {row.hasBad ? <ProblemList items={row.bads} data-ui={part(ui, "problem")} /> : null}
    </div>
  );
}
