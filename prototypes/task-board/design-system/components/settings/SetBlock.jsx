import React from "react";
import {part} from "../_shared/ui.js";

// One block of the sheet's body, ruled from the one above, with an optional heading row.
// Source: settings.mjs paint `section.set-block`.
export function SetBlock({ruled, title, aside, children, "data-ui": ui}) {
  return (
    <section className={ruled ? "set-block ruled" : "set-block"} data-ui={ui}>
      {title ? (
        <div className="set-block-head">
          <span className="dp-section-title" data-ui={part(ui, "title")}>{title}</span>{aside}
        </div>
      ) : null}
      {children}
    </section>
  );
}
