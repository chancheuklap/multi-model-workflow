import React from "react";
import {part} from "../_shared/ui.js";

// The settings sheet over a dimmed page: head, a scrolling body, and a foot that says
// what a save would change. A click on the dim closes it only when nothing is changed.
// Source: settings.mjs paint (`scrim`, `sheet`, `sheet-head`, `sheet-body`, `sheet-foot`).
export function Sheet({store, strong, quiet, hatch, closeLabel, saveOff, changed, onClose, onSave, children, "data-ui": ui}) {
  return (
    <div className="scrim board" data-ui={ui}
      onClick={event => { if (event.target === event.currentTarget && !changed && onClose) onClose(); }}>
      <div className="sheet" role="dialog" aria-modal="true" aria-label="本机配置">
        <div className="sheet-head">
          <div className="sheet-head-text">
            <span className="dp-eyebrow" data-ui={part(ui, "eyebrow")}>本机配置</span>
            <h2 className="sheet-title" data-ui={part(ui, "title")}>这台机器上，每个 agent 跑在哪</h2>
            <p className="sheet-sub" data-ui={part(ui, "intro")}>下拉菜单里的选项，是 MMW 刚问过这台机器上的 host 得到的，问的地方和 <span className="sheet-code">start</span> 起 session 时问的是同一处。这里就是 MMW 管这件事的唯一地方，保存在本机的 <span className="sheet-code">{store}</span>；这一页不写 GitHub。</p>
          </div>
          <button type="button" className="dp-close" aria-label="关闭本机配置" onClick={onClose} data-ui={part(ui, "close")}>×</button>
        </div>
        <div className="sheet-body">{children}</div>
        <div className="sheet-foot">
          <div className="foot-status" aria-live="polite">
            <span className="foot-strong" data-ui={part(ui, "status")}>{hatch ? <span className="hatch"></span> : null}{strong}</span>
            <span className="foot-quiet" data-ui={part(ui, "status-note")}>{quiet}</span>
          </div>
          <div className="foot-actions">
            <button type="button" className="btn" onClick={onClose} data-ui={part(ui, "cancel")}>{closeLabel}</button>
            <button type="button" className="btn primary" disabled={!!saveOff} onClick={onSave} data-ui={part(ui, "save")}>保存</button>
          </div>
        </div>
      </div>
    </div>
  );
}
