import React from "react";

// Open the shown map, spec or decision ticket on GitHub. Source: detail.mjs card `dp-gh`.
export function GithubButton({label, onClick, "data-ui": ui}) {
  return <button type="button" className="dp-gh" onClick={onClick} data-ui={ui}>{label}</button>;
}
