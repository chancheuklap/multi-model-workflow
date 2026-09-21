import React from "react";
import {part} from "../_shared/ui.js";

// When and where the hosts were last asked, and a rescan; or a spinner while asking.
// Source: settings.mjs paint `span.scan`.
export function ScanStatus({scanning, scanningText, scannedText, onRescan, "data-ui": ui}) {
  return (
    <span className="scan" data-ui={ui}>
      {scanning ? [<span key="s" className="spin"></span>, scanningText] : [
        scannedText,
        <button key="b" type="button" className="linkbtn" onClick={onRescan} data-ui={part(ui, "rescan")}>重新扫描</button>,
      ]}
    </span>
  );
}
