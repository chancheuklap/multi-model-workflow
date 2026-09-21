import React from "react";
import {part} from "../_shared/ui.js";

// One lamp count in the top bar. Source: topbar.mjs render, `.counter`. The
// "needs you" counter is a button that jumps to the next orange ticket (`hot` while
// there is one); the other three are plain spans.
export function Counter({lamp, label, count, sub, button, hot, title, onClick, "data-ui": ui}) {
  const kids = [
    <span key="l" className={`lamp ${lamp}`} data-ui={part(ui, "lamp")}></span>,
    label,
    <span key="n" className={hot ? "counter-n hot" : "counter-n"} data-ui={part(ui, "count")}>{String(count)}</span>,
    sub ? <span key="s" className="counter-sub" data-ui={part(ui, "sub")}>{sub}</span> : null,
  ];
  if (button) {
    return (
      <button type="button" className={hot ? "counter hot" : "counter"} disabled={!hot} title={title}
        onClick={onClick} data-ui={ui}>{kids}</button>
    );
  }
  return <span className="counter" data-ui={ui}>{kids}</span>;
}
