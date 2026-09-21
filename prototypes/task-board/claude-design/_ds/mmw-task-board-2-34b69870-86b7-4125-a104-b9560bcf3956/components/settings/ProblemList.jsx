import React from "react";
import {part} from "../_shared/ui.js";

// What is wrong with a row, one hatched line each. Source: settings.mjs roleFoot.
export function ProblemList({items = [], "data-ui": ui}) {
  if (!items.length) return null;
  return (
    <div className="role-foot" data-ui={ui}>
      {items.map((item, i) => <div key={i} className="role-bad" data-ui={part(ui, "item")}><span className="hatch"></span>{item.text}</div>)}
    </div>
  );
}
