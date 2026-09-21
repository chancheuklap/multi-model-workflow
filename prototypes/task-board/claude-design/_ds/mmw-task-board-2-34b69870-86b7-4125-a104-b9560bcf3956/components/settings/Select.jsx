import React from "react";

// A dropdown of the sheet: a changed cell in heavier ink, one start would refuse
// hatched. Source: settings.mjs selectEl; `opts` are local-config.mjs options.
export function Select({cls, value, disabled, label, opts = [], onChange, "data-ui": ui}) {
  return (
    <select className={cls} aria-label={label} disabled={!!disabled} value={value ?? ""}
      onChange={event => onChange && onChange(event.target.value)} data-ui={ui}>
      {opts.map(option => (
        <option key={option.value} value={option.value} disabled={!!option.disabled} label={option.text}>{option.text}</option>
      ))}
    </select>
  );
}
