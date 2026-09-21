import React from "react";
import {part} from "../_shared/ui.js";

// One related issue: a blocker, a ticket it blocks, or a row of a spec's or map's list.
// On a ticket (`ticket`) a blocker still holding reads "held"; elsewhere the row ends
// in its step pill or its state. A row the tree cannot read does not link. Source:
// detail.mjs ticketRelation and relRow.
export function RelationRow({ticket, row, onGoto, "data-ui": ui}) {
  const go = () => onGoto && onGoto(row.n);
  if (ticket) {
    const last = row.hold ? <span className="pv-rel-hold" data-ui={part(ui, "hold")}>held</span>
      : row.phase ? <span className={`pill ${row.phase}`} data-ui={part(ui, "phase")}>{row.phase}</span>
        : <span className="pv-rel-s" data-ui={part(ui, "state")}>{row.state}</span>;
    const body = [
      <span key="l" className={`lamp ${row.lamp}`} data-ui={part(ui, "lamp")}></span>,
      <span key="n" className="pv-rel-n" data-ui={part(ui, "number")}>{row.num}</span>,
      <span key="t" className="pv-rel-t" data-ui={part(ui, "title")}>{row.title}{row.where ? " " : null}
        {row.where ? <span className="rel-where" data-ui={part(ui, "where")}>{row.where}</span> : null}</span>,
      <React.Fragment key="x">{last}</React.Fragment>,
    ];
    if (row.unknown) return <button type="button" className="pv-rel" data-ui={ui}>{body}</button>;
    return <button type="button" className={row.hold ? "pv-rel hold" : "pv-rel"} onClick={go} data-ui={ui}>{body}</button>;
  }
  const last = row.phase ? <span className={`pill ${row.phase}`} data-ui={part(ui, "phase")}>{row.phase}</span>
    : <span className={row.state === "not landed" ? "rel-state open" : "rel-state"} data-ui={part(ui, "state")}>{row.state}</span>;
  const body = [
    <span key="l" className={`lamp ${row.lamp}`} data-ui={part(ui, "lamp")}></span>,
    <span key="n" className="rel-num" data-ui={part(ui, "number")}>{row.num}</span>,
    <span key="t" className="rel-title" data-ui={part(ui, "title")}>{row.title} <span className="rel-where" data-ui={part(ui, "where")}>{row.where || ""}</span></span>,
    <React.Fragment key="x">{last}</React.Fragment>,
  ];
  if (row.unknown) return <div className="rel-static" data-ui={ui}>{body}</div>;
  return <button type="button" className="rel" onClick={go} data-ui={ui}>{body}</button>;
}
