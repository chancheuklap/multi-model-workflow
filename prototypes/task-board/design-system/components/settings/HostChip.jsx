import React from "react";
import {part} from "../_shared/ui.js";

// One host and what this machine said about it. Source: settings.mjs paint `span.hs`;
// `chip` is one of local-config.mjs settingsView `chips`.
export function HostChip({chip, "data-ui": ui}) {
  return (
    <span className={chip.cls} data-ui={ui}>
      <span className="hs-name" data-ui={part(ui, "name")}>{chip.host}</span>{chip.what}
    </span>
  );
}
