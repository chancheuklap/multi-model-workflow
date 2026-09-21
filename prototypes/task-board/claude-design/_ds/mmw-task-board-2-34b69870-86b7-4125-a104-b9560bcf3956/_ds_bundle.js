/* @ds-bundle: {"format":4,"namespace":"MMWTaskBoard2_34b698","components":[{"name":"CanvasEmpty","sourcePath":"components/canvas/CanvasEmpty.jsx"},{"name":"ContainerCard","sourcePath":"components/canvas/ContainerCard.jsx"},{"name":"DecisionCard","sourcePath":"components/canvas/DecisionCard.jsx"},{"name":"Edges","sourcePath":"components/canvas/Edges.jsx"},{"name":"LaneLabel","sourcePath":"components/canvas/LaneLabel.jsx"},{"name":"Legend","sourcePath":"components/canvas/Legend.jsx"},{"name":"TicketCard","sourcePath":"components/canvas/TicketCard.jsx"},{"name":"ZoomBar","sourcePath":"components/canvas/ZoomBar.jsx"},{"name":"DetailEmpty","sourcePath":"components/detail/DetailEmpty.jsx"},{"name":"DetailHead","sourcePath":"components/detail/DetailHead.jsx"},{"name":"DetailTitle","sourcePath":"components/detail/DetailTitle.jsx"},{"name":"EventBlock","sourcePath":"components/detail/EventBlock.jsx"},{"name":"EventRow","sourcePath":"components/detail/EventRow.jsx"},{"name":"GithubButton","sourcePath":"components/detail/GithubButton.jsx"},{"name":"LampCounts","sourcePath":"components/detail/LampCounts.jsx"},{"name":"NeedsYou","sourcePath":"components/detail/NeedsYou.jsx"},{"name":"NoneNote","sourcePath":"components/detail/NoneNote.jsx"},{"name":"Origin","sourcePath":"components/detail/Origin.jsx"},{"name":"PhaseCounts","sourcePath":"components/detail/PhaseCounts.jsx"},{"name":"RelationRow","sourcePath":"components/detail/RelationRow.jsx"},{"name":"RunBox","sourcePath":"components/detail/RunBox.jsx"},{"name":"Section","sourcePath":"components/detail/Section.jsx"},{"name":"StatusLine","sourcePath":"components/detail/StatusLine.jsx"},{"name":"SubIssueRow","sourcePath":"components/detail/SubIssueRow.jsx"},{"name":"Button","sourcePath":"components/settings/Button.jsx"},{"name":"CodeText","sourcePath":"components/settings/CodeText.jsx"},{"name":"HostChip","sourcePath":"components/settings/HostChip.jsx"},{"name":"ProblemList","sourcePath":"components/settings/ProblemList.jsx"},{"name":"RefusedBanner","sourcePath":"components/settings/RefusedBanner.jsx"},{"name":"RoleRow","sourcePath":"components/settings/RoleRow.jsx"},{"name":"RolesTable","sourcePath":"components/settings/RolesTable.jsx"},{"name":"RunnerRow","sourcePath":"components/settings/RunnerRow.jsx"},{"name":"ScanStatus","sourcePath":"components/settings/ScanStatus.jsx"},{"name":"Select","sourcePath":"components/settings/Select.jsx"},{"name":"SetBlock","sourcePath":"components/settings/SetBlock.jsx"},{"name":"SetNote","sourcePath":"components/settings/SetNote.jsx"},{"name":"Sheet","sourcePath":"components/settings/Sheet.jsx"},{"name":"Lamp","sourcePath":"components/status/Lamp.jsx"},{"name":"StepPill","sourcePath":"components/status/StepPill.jsx"},{"name":"ColumnEyebrow","sourcePath":"components/tasks/ColumnEyebrow.jsx"},{"name":"TaskRow","sourcePath":"components/tasks/TaskRow.jsx"},{"name":"TasksEmpty","sourcePath":"components/tasks/TasksEmpty.jsx"},{"name":"Brand","sourcePath":"components/topbar/Brand.jsx"},{"name":"Counter","sourcePath":"components/topbar/Counter.jsx"},{"name":"IconButton","sourcePath":"components/topbar/IconButton.jsx"},{"name":"ReadState","sourcePath":"components/topbar/ReadState.jsx"}],"sourceHashes":{"components/_shared/ui.js":"0072d8b5e16d","components/canvas/CanvasEmpty.jsx":"10f547c60646","components/canvas/ContainerCard.jsx":"2acfc66a6f49","components/canvas/DecisionCard.jsx":"37e6d3f06835","components/canvas/Edges.jsx":"ef780cf86aa9","components/canvas/LaneLabel.jsx":"35246166490c","components/canvas/Legend.jsx":"37807dfe46af","components/canvas/TicketCard.jsx":"623c9139f736","components/canvas/ZoomBar.jsx":"d7e23ccf81ee","components/canvas/card-shell.jsx":"678f92102837","components/detail/DetailEmpty.jsx":"4e0d89dbbf3b","components/detail/DetailHead.jsx":"e5835c3ccc7d","components/detail/DetailTitle.jsx":"3e00e91dbe96","components/detail/EventBlock.jsx":"9fca5edd709e","components/detail/EventRow.jsx":"438f48a7d4b4","components/detail/GithubButton.jsx":"60a84b3c45d7","components/detail/LampCounts.jsx":"85d810685a29","components/detail/NeedsYou.jsx":"4aa630837df2","components/detail/NoneNote.jsx":"61f0a2557d57","components/detail/Origin.jsx":"bb126bbfc661","components/detail/PhaseCounts.jsx":"578be626c886","components/detail/RelationRow.jsx":"2f294fd344d3","components/detail/RunBox.jsx":"a76c7053ba41","components/detail/Section.jsx":"7f1e043d7861","components/detail/StatusLine.jsx":"d747f2beff3c","components/detail/SubIssueRow.jsx":"f2fdefddc17d","components/settings/Button.jsx":"1ccf667bbdba","components/settings/CodeText.jsx":"b18f2df9cfb7","components/settings/HostChip.jsx":"19586895f2a1","components/settings/ProblemList.jsx":"a55530b7b848","components/settings/RefusedBanner.jsx":"da4be775064f","components/settings/RoleRow.jsx":"43cfb86cee7f","components/settings/RolesTable.jsx":"0ee7f1a1dc67","components/settings/RunnerRow.jsx":"ecb3349aacc1","components/settings/ScanStatus.jsx":"df6b5ca4abe9","components/settings/Select.jsx":"1234309a4dad","components/settings/SetBlock.jsx":"b29291f8310c","components/settings/SetNote.jsx":"56cde0882c3e","components/settings/Sheet.jsx":"34532a43c90f","components/status/Lamp.jsx":"d1d46459163c","components/status/StepPill.jsx":"6c797f640e3f","components/tasks/ColumnEyebrow.jsx":"2a68f95eed49","components/tasks/TaskRow.jsx":"7c013edbb654","components/tasks/TasksEmpty.jsx":"362398226eb1","components/topbar/Brand.jsx":"6e4641a9cfb3","components/topbar/Counter.jsx":"a09b2a6a84f8","components/topbar/IconButton.jsx":"a42e02508f3e","components/topbar/ReadState.jsx":"d9d7a26253a5","ui_kits/task-board/data/board-morning.js":"789588b57df2","ui_kits/task-board/data/settings.js":"40e73e931718","ui_kits/task-board/lib/board.js":"296a96a45e7f","ui_kits/task-board/screens.jsx":"36cbad74f5e7"},"inlinedExternals":[],"unexposedExports":[{"name":"cardShell","sourcePath":"components/canvas/card-shell.jsx"},{"name":"part","sourcePath":"components/_shared/ui.js"}]} */

(() => {

const __ds_ns = (window.MMWTaskBoard2_34b698 = window.MMWTaskBoard2_34b698 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/_shared/ui.js
try { (() => {
// The id a part of a component carries: `<data-ui>.<part>` when the page gave the
// component an id, nothing when it did not.
const part = (ui, name) => ui ? `${ui}.${name}` : undefined;
Object.assign(__ds_scope, { part });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/_shared/ui.js", error: String((e && e.message) || e) }); }

// components/canvas/CanvasEmpty.jsx
try { (() => {
// What the canvas says before any task exists. Source: canvas.mjs emptyState.
function CanvasEmpty({
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "canvas-empty",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("p", {
    className: "canvas-empty-title",
    "data-ui": __ds_scope.part(ui, "title")
  }, "The Night \u8FD8\u6CA1\u5F00\u59CB"), /*#__PURE__*/React.createElement("p", {
    className: "canvas-empty-text",
    "data-ui": __ds_scope.part(ui, "text")
  }, "The Night \u662F\u4E00\u6B21\u8BA8\u8BBA\u5F00\u51FA\u7684\u90A3\u5F20 ticket\u3002\u7ED9\u5B83\u6253\u4E0A ", /*#__PURE__*/React.createElement("span", {
    className: "code"
  }, "mmw:map"), " label\uFF0C\u4E0B\u4E00\u6B21\u8BFB\u53D6\u65F6\u5B83\u548C\u5B83\u4E0B\u9762\u7684 spec\u3001ticket \u5C31\u4F1A\u51FA\u73B0\u5728\u8FD9\u91CC\u3002")));
}
Object.assign(__ds_scope, { CanvasEmpty });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/canvas/CanvasEmpty.jsx", error: String((e && e.message) || e) }); }

// components/canvas/Edges.jsx
try { (() => {
// Every line on the canvas: the trunk, the expansions, and the blocking curves coloured
// by how the wait stands. Source: canvas.mjs edgesSVG, whose markup `svg` is.
function Edges({
  svg,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "edges-host",
    "data-ui": ui,
    dangerouslySetInnerHTML: {
      __html: svg || ""
    }
  });
}
Object.assign(__ds_scope, { Edges });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/canvas/Edges.jsx", error: String((e && e.message) || e) }); }

// components/canvas/LaneLabel.jsx
try { (() => {
// A small caption over a band of cards, or the warning over a blocking cycle. Source:
// canvas.mjs canvasView `labels`.
function LaneLabel({
  label,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: label.cls,
    style: label.pos,
    "data-ui": ui
  }, label.text);
}
Object.assign(__ds_scope, { LaneLabel });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/canvas/LaneLabel.jsx", error: String((e && e.message) || e) }); }

// components/canvas/Legend.jsx
try { (() => {
// What each line and mark on the canvas means. Source: canvas.mjs legend.
function Legend({
  "data-ui": ui
}) {
  const item = (cls, text, name) => /*#__PURE__*/React.createElement("span", {
    className: "legend-item",
    "data-ui": __ds_scope.part(ui, name)
  }, /*#__PURE__*/React.createElement("span", {
    className: cls
  }), text);
  return /*#__PURE__*/React.createElement("div", {
    className: "legend",
    "data-ui": ui
  }, item("legend-line", "contains · released", "walked"), item("legend-line flow", "released · working", "flow"), item("legend-line blocked", "blocked", "blocked"), item("legend-bar", "closing pass", "closeout"));
}
Object.assign(__ds_scope, { Legend });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/canvas/Legend.jsx", error: String((e && e.message) || e) }); }

// components/canvas/ZoomBar.jsx
try { (() => {
// Zoom out, the zoom level, zoom in, and fit. Source: canvas.mjs zoomBar.
function ZoomBar({
  level,
  onOut,
  onIn,
  onFit,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "zoom",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "zoom-btn",
    "aria-label": "zoom out",
    onClick: onOut,
    "data-ui": __ds_scope.part(ui, "out")
  }, "\u2212"), /*#__PURE__*/React.createElement("span", {
    className: "zoom-level",
    "data-ui": __ds_scope.part(ui, "level")
  }, level), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "zoom-btn",
    "aria-label": "zoom in",
    onClick: onIn,
    "data-ui": __ds_scope.part(ui, "in")
  }, "+"), /*#__PURE__*/React.createElement("span", {
    className: "zoom-sep"
  }), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "zoom-btn text",
    onClick: onFit,
    "data-ui": __ds_scope.part(ui, "fit")
  }, "fit"));
}
Object.assign(__ds_scope, { ZoomBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/canvas/ZoomBar.jsx", error: String((e && e.message) || e) }); }

// components/canvas/card-shell.jsx
try { (() => {
// The frame every canvas card shares. Source: canvas.mjs cardShell and cardHit: the
// whole card is one button (`card-hit`), then the top row, the title, and what follows.
function cardShell(item, {
  ui,
  onPick,
  lampTitle,
  titleCls,
  right,
  after
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: item.cls,
    style: item.pos,
    title: item.title,
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "card-hit",
    "aria-label": `#${item.n} ${item.title}`,
    onClick: onPick,
    "data-ui": __ds_scope.part(ui, "open")
  }), /*#__PURE__*/React.createElement("div", {
    className: "card-top"
  }, /*#__PURE__*/React.createElement("span", {
    className: item.lampCls,
    title: lampTitle ? item.lampWord : undefined,
    "data-ui": __ds_scope.part(ui, "lamp")
  }), /*#__PURE__*/React.createElement("span", {
    className: "card-num",
    "data-ui": __ds_scope.part(ui, "num")
  }, item.num), /*#__PURE__*/React.createElement("span", {
    className: "card-right"
  }, right)), /*#__PURE__*/React.createElement("div", {
    className: titleCls,
    "data-ui": __ds_scope.part(ui, "title")
  }, item.title), after);
}
Object.assign(__ds_scope, { cardShell });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/canvas/card-shell.jsx", error: String((e && e.message) || e) }); }

// components/canvas/ContainerCard.jsx
try { (() => {
// A map or spec on the canvas trunk: lamp, number, landed count, expand chevron, title
// and progress bar. Source: canvas.mjs containerCard; `item` is one of canvasView's
// `containers`.
function ContainerCard({
  item,
  onPick,
  onToggle,
  "data-ui": ui
}) {
  const right = [/*#__PURE__*/React.createElement("span", {
    key: "c",
    className: "card-count",
    "data-ui": __ds_scope.part(ui, "count")
  }, item.count)];
  if (item.canExpand) {
    right.push(/*#__PURE__*/React.createElement("button", {
      key: "x",
      type: "button",
      className: "chev",
      "aria-label": item.toggleLabel,
      "data-ui": __ds_scope.part(ui, "expand"),
      onClick: event => {
        event.stopPropagation();
        if (onToggle) onToggle(item.n);
      }
    }, item.chev));
  }
  const after = /*#__PURE__*/React.createElement("div", {
    className: "card-bar"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card-bar-fill",
    style: {
      width: item.barStyle.width
    },
    "data-ui": __ds_scope.part(ui, "bar")
  }));
  return __ds_scope.cardShell(item, {
    ui,
    onPick,
    lampTitle: true,
    titleCls: item.titleCls,
    right,
    after
  });
}
Object.assign(__ds_scope, { ContainerCard });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/canvas/ContainerCard.jsx", error: String((e && e.message) || e) }); }

// components/canvas/DecisionCard.jsx
try { (() => {
// A decision ticket of a map: a lower card with its kind where a ticket has its pill.
// Source: canvas.mjs decisionCard; `item` is one of canvasView's `decisions`.
function DecisionCard({
  item,
  onPick,
  "data-ui": ui
}) {
  const right = /*#__PURE__*/React.createElement("span", {
    className: "card-kind",
    "data-ui": __ds_scope.part(ui, "kind")
  }, item.kind);
  return __ds_scope.cardShell(item, {
    ui,
    onPick,
    lampTitle: false,
    titleCls: "card-title decision",
    right,
    after: null
  });
}
Object.assign(__ds_scope, { DecisionCard });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/canvas/DecisionCard.jsx", error: String((e && e.message) || e) }); }

// components/canvas/TicketCard.jsx
try { (() => {
// A ticket: lamp and number, step pill, title, and where it runs. Source: canvas.mjs
// ticketCard; `item` is one of canvasView's `tickets`.
function TicketCard({
  item,
  onPick,
  "data-ui": ui
}) {
  const right = /*#__PURE__*/React.createElement("span", {
    className: item.pillCls,
    "data-ui": __ds_scope.part(ui, "phase")
  }, item.phase);
  const after = /*#__PURE__*/React.createElement("div", {
    className: item.runCls,
    "data-ui": __ds_scope.part(ui, "run")
  }, item.run);
  return __ds_scope.cardShell(item, {
    ui,
    onPick,
    lampTitle: true,
    titleCls: "card-title",
    right,
    after
  });
}
Object.assign(__ds_scope, { TicketCard });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/canvas/TicketCard.jsx", error: String((e && e.message) || e) }); }

// components/detail/DetailEmpty.jsx
try { (() => {
// What the detail column says when nothing is picked. Source: detail.mjs render `dp-empty`.
function DetailEmpty({
  title,
  text,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "dp-empty",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("p", {
    className: "dp-empty-title",
    "data-ui": __ds_scope.part(ui, "title")
  }, title), text);
}
Object.assign(__ds_scope, { DetailEmpty });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/DetailEmpty.jsx", error: String((e && e.message) || e) }); }

// components/detail/DetailHead.jsx
try { (() => {
// The first row of the detail column: what is shown, then GitHub and close. A ticket's
// head carries the GitHub link; a map, spec or decision ticket puts it at the bottom
// (GithubButton). Source: detail.mjs ticketCard `pv-head`, card `dp-head`.
function DetailHead({
  ticket,
  eyebrow,
  onGithub,
  onClose,
  "data-ui": ui
}) {
  if (ticket) {
    return /*#__PURE__*/React.createElement("div", {
      className: "pv-head",
      "data-ui": ui
    }, /*#__PURE__*/React.createElement("span", {
      className: "pv-eyebrow",
      "data-ui": __ds_scope.part(ui, "eyebrow")
    }, eyebrow || "Ticket"), /*#__PURE__*/React.createElement("button", {
      type: "button",
      className: "pv-gh",
      onClick: onGithub,
      "data-ui": __ds_scope.part(ui, "github")
    }, "GitHub \u2197"), /*#__PURE__*/React.createElement("button", {
      type: "button",
      className: "pv-close",
      "aria-label": "\u5173\u95ED\u8BE6\u60C5",
      onClick: onClose,
      "data-ui": __ds_scope.part(ui, "close")
    }, "\xD7"));
  }
  return /*#__PURE__*/React.createElement("div", {
    className: "dp-head",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("span", {
    className: "dp-eyebrow",
    "data-ui": __ds_scope.part(ui, "eyebrow")
  }, eyebrow), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "dp-close",
    "aria-label": "\u5173\u95ED\u8BE6\u60C5",
    onClick: onClose,
    "data-ui": __ds_scope.part(ui, "close")
  }, "\xD7"));
}
Object.assign(__ds_scope, { DetailHead });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/DetailHead.jsx", error: String((e && e.message) || e) }); }

// components/detail/DetailTitle.jsx
try { (() => {
// The title of what the detail column shows. Source: detail.mjs `h2.pv-title`, `h2.dp-title`.
function DetailTitle({
  ticket,
  title,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("h2", {
    className: ticket ? "pv-title" : "dp-title",
    "data-ui": ui
  }, title);
}
Object.assign(__ds_scope, { DetailTitle });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/DetailTitle.jsx", error: String((e && e.message) || e) }); }

// components/detail/EventBlock.jsx
try { (() => {
// One step of a ticket's history: its pill and time span, and, open, one row per event.
// A closed block shows the event most worth opening it for. Source: detail.mjs
// phaseBlock; `block` is one of detail.mjs phaseBlocksFrom's blocks.
function EventBlock({
  block,
  opened,
  onToggle,
  children,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: block.tone === "plain" ? "va-block" : "va-block warn",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "va-bhead",
    onClick: onToggle,
    "data-ui": __ds_scope.part(ui, "toggle")
  }, /*#__PURE__*/React.createElement("span", {
    className: "va-chev",
    "data-ui": __ds_scope.part(ui, "chev")
  }, opened ? "▾" : "▸"), /*#__PURE__*/React.createElement("span", {
    className: `pill ${block.phase}`,
    "data-ui": __ds_scope.part(ui, "phase")
  }, block.phase), /*#__PURE__*/React.createElement("span", {
    className: "va-bsum",
    "data-ui": __ds_scope.part(ui, "summary")
  }, opened ? "" : block.summary), /*#__PURE__*/React.createElement("span", {
    className: "va-btime",
    "data-ui": __ds_scope.part(ui, "time")
  }, opened ? block.span : block.from)), opened ? /*#__PURE__*/React.createElement("div", {
    className: "va-body"
  }, children) : null);
}
Object.assign(__ds_scope, { EventBlock });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/EventBlock.jsx", error: String((e && e.message) || e) }); }

// components/detail/EventRow.jsx
try { (() => {
// One event on the ticket: time, name, one line from its payload, and, opened, every
// payload field and the comment's first line. Source: detail.mjs eventRow and backendDetail.
function EventRow({
  item,
  opened,
  onToggle,
  "data-ui": ui
}) {
  const warn = item.tone === "warn" || item.tone === "needs-you";
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "va-ev",
    onClick: onToggle,
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("span", {
    className: "va-t",
    "data-ui": __ds_scope.part(ui, "time")
  }, item.time), /*#__PURE__*/React.createElement("span", {
    className: warn ? "va-n warn" : "va-n",
    "data-ui": __ds_scope.part(ui, "name")
  }, item.name), item.hasText ? /*#__PURE__*/React.createElement("span", {
    className: "va-x",
    "data-ui": __ds_scope.part(ui, "text")
  }, item.text) : null, opened ? /*#__PURE__*/React.createElement("span", {
    className: "va-x"
  }, /*#__PURE__*/React.createElement("span", {
    className: "pv-detail",
    "data-ui": __ds_scope.part(ui, "detail")
  }, (item.detail || []).flatMap((row, i) => [/*#__PURE__*/React.createElement("span", {
    key: `k${i}`,
    className: "pv-detail-k"
  }, row.k), /*#__PURE__*/React.createElement("span", {
    key: `v${i}`,
    className: "pv-detail-v"
  }, row.v)]))) : null);
}
Object.assign(__ds_scope, { EventRow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/EventRow.jsx", error: String((e && e.message) || e) }); }

// components/detail/GithubButton.jsx
try { (() => {
// Open the shown map, spec or decision ticket on GitHub. Source: detail.mjs card `dp-gh`.
function GithubButton({
  label,
  onClick,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "dp-gh",
    onClick: onClick,
    "data-ui": ui
  }, label);
}
Object.assign(__ds_scope, { GithubButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/GithubButton.jsx", error: String((e && e.message) || e) }); }

// components/detail/LampCounts.jsx
try { (() => {
// How many of a spec's or map's tickets sit under each lamp. Source: detail.mjs
// containerBody `lamps-count`.
function LampCounts({
  lamps = [],
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "lamps-count",
    "data-ui": ui
  }, lamps.map((item, i) => /*#__PURE__*/React.createElement("span", {
    key: i,
    className: "lc-item",
    "data-ui": __ds_scope.part(ui, "item")
  }, /*#__PURE__*/React.createElement("span", {
    className: `lamp ${item.lamp}`
  }), item.word, /*#__PURE__*/React.createElement("span", {
    className: "lc-n"
  }, item.n))));
}
Object.assign(__ds_scope, { LampCounts });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/LampCounts.jsx", error: String((e && e.message) || e) }); }

// components/detail/NeedsYou.jsx
try { (() => {
// Why the lamp is orange: each open decision, fault or contract sub-issue, a hand-back,
// or a merge that bounced. Source: detail.mjs ticketCard `pv-why`.
function NeedsYou({
  why = [],
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "pv-why",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("span", {
    className: "pv-why-t",
    "data-ui": __ds_scope.part(ui, "title")
  }, "Needs you"), why.map((item, i) => /*#__PURE__*/React.createElement("span", {
    key: i,
    "data-ui": __ds_scope.part(ui, "item")
  }, /*#__PURE__*/React.createElement("b", null, item.head), " ", item.body)));
}
Object.assign(__ds_scope, { NeedsYou });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/NeedsYou.jsx", error: String((e && e.message) || e) }); }

// components/detail/NoneNote.jsx
try { (() => {
// The one line a list shows when it is empty: "none" under a blocking list, "no events
// yet" under Events. Source: detail.mjs `p.rel-none`, `p.pv-none`.
function NoneNote({
  ticket,
  text,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("p", {
    className: ticket ? "pv-none" : "rel-none",
    "data-ui": ui
  }, text);
}
Object.assign(__ds_scope, { NoneNote });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/NoneNote.jsx", error: String((e && e.message) || e) }); }

// components/detail/Origin.jsx
try { (() => {
// Where the shown issue sits: its number, then links to its spec and map. Source:
// detail.mjs origin (`dp-origin`) and ticketCard (`pv-links`).
function Origin({
  ticket,
  num,
  links = [],
  onGoto,
  "data-ui": ui
}) {
  const cls = ticket ? "pv-links" : "dp-origin";
  const linkCls = ticket ? "pv-link" : "dp-link";
  return /*#__PURE__*/React.createElement("div", {
    className: cls,
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("span", {
    "data-ui": __ds_scope.part(ui, "number")
  }, num), links.flatMap((link, i) => [/*#__PURE__*/React.createElement("span", {
    key: `d${i}`
  }, "\xB7"), /*#__PURE__*/React.createElement("button", {
    key: `l${i}`,
    type: "button",
    className: linkCls,
    onClick: () => onGoto && onGoto(link.n),
    "data-ui": __ds_scope.part(ui, "link")
  }, link.label)]));
}
Object.assign(__ds_scope, { Origin });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/Origin.jsx", error: String((e && e.message) || e) }); }

// components/detail/PhaseCounts.jsx
try { (() => {
// How many of a spec's or map's tickets sit at each step. Source: detail.mjs
// containerBody `phases-count`.
function PhaseCounts({
  phases = [],
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "phases-count",
    "data-ui": ui
  }, phases.map((item, i) => /*#__PURE__*/React.createElement("span", {
    key: i,
    className: `pill ${item.phase}`,
    "data-ui": __ds_scope.part(ui, "item")
  }, item.label)));
}
Object.assign(__ds_scope, { PhaseCounts });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/PhaseCounts.jsx", error: String((e && e.message) || e) }); }

// components/detail/RelationRow.jsx
try { (() => {
// One related issue: a blocker, a ticket it blocks, or a row of a spec's or map's list.
// On a ticket (`ticket`) a blocker still holding reads "held"; elsewhere the row ends
// in its step pill or its state. A row the tree cannot read does not link. Source:
// detail.mjs ticketRelation and relRow.
function RelationRow({
  ticket,
  row,
  onGoto,
  "data-ui": ui
}) {
  const go = () => onGoto && onGoto(row.n);
  if (ticket) {
    const last = row.hold ? /*#__PURE__*/React.createElement("span", {
      className: "pv-rel-hold",
      "data-ui": __ds_scope.part(ui, "hold")
    }, "held") : row.phase ? /*#__PURE__*/React.createElement("span", {
      className: `pill ${row.phase}`,
      "data-ui": __ds_scope.part(ui, "phase")
    }, row.phase) : /*#__PURE__*/React.createElement("span", {
      className: "pv-rel-s",
      "data-ui": __ds_scope.part(ui, "state")
    }, row.state);
    const body = [/*#__PURE__*/React.createElement("span", {
      key: "l",
      className: `lamp ${row.lamp}`,
      "data-ui": __ds_scope.part(ui, "lamp")
    }), /*#__PURE__*/React.createElement("span", {
      key: "n",
      className: "pv-rel-n",
      "data-ui": __ds_scope.part(ui, "number")
    }, row.num), /*#__PURE__*/React.createElement("span", {
      key: "t",
      className: "pv-rel-t",
      "data-ui": __ds_scope.part(ui, "title")
    }, row.title, row.where ? " " : null, row.where ? /*#__PURE__*/React.createElement("span", {
      className: "rel-where",
      "data-ui": __ds_scope.part(ui, "where")
    }, row.where) : null), /*#__PURE__*/React.createElement(React.Fragment, {
      key: "x"
    }, last)];
    if (row.unknown) return /*#__PURE__*/React.createElement("button", {
      type: "button",
      className: "pv-rel",
      "data-ui": ui
    }, body);
    return /*#__PURE__*/React.createElement("button", {
      type: "button",
      className: row.hold ? "pv-rel hold" : "pv-rel",
      onClick: go,
      "data-ui": ui
    }, body);
  }
  const last = row.phase ? /*#__PURE__*/React.createElement("span", {
    className: `pill ${row.phase}`,
    "data-ui": __ds_scope.part(ui, "phase")
  }, row.phase) : /*#__PURE__*/React.createElement("span", {
    className: row.state === "not landed" ? "rel-state open" : "rel-state",
    "data-ui": __ds_scope.part(ui, "state")
  }, row.state);
  const body = [/*#__PURE__*/React.createElement("span", {
    key: "l",
    className: `lamp ${row.lamp}`,
    "data-ui": __ds_scope.part(ui, "lamp")
  }), /*#__PURE__*/React.createElement("span", {
    key: "n",
    className: "rel-num",
    "data-ui": __ds_scope.part(ui, "number")
  }, row.num), /*#__PURE__*/React.createElement("span", {
    key: "t",
    className: "rel-title",
    "data-ui": __ds_scope.part(ui, "title")
  }, row.title, " ", /*#__PURE__*/React.createElement("span", {
    className: "rel-where",
    "data-ui": __ds_scope.part(ui, "where")
  }, row.where || "")), /*#__PURE__*/React.createElement(React.Fragment, {
    key: "x"
  }, last)];
  if (row.unknown) return /*#__PURE__*/React.createElement("div", {
    className: "rel-static",
    "data-ui": ui
  }, body);
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "rel",
    onClick: go,
    "data-ui": ui
  }, body);
}
Object.assign(__ds_scope, { RelationRow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/RelationRow.jsx", error: String((e && e.message) || e) }); }

// components/detail/RunBox.jsx
try { (() => {
// Where a ticket runs: grade, host · model · effort, then branch, base, worktree,
// machine and slot; or the line that says it has not run. Source: detail.mjs ticketRuntime.
function RunBox({
  runtime,
  noRunText,
  "data-ui": ui
}) {
  if (!runtime) return /*#__PURE__*/React.createElement("p", {
    className: "pv-none",
    "data-ui": ui
  }, noRunText || "not dispatched yet");
  return /*#__PURE__*/React.createElement("div", {
    className: "pv-run",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("div", {
    className: "pv-run-who"
  }, /*#__PURE__*/React.createElement("span", {
    className: "pv-run-grade",
    "data-ui": __ds_scope.part(ui, "grade")
  }, runtime.grade || ""), runtime.model ? /*#__PURE__*/React.createElement("span", {
    className: "pv-run-model",
    "data-ui": __ds_scope.part(ui, "model")
  }, runtime.model) : null), runtime.rows && runtime.rows.length ? /*#__PURE__*/React.createElement("div", {
    className: "pv-run-where"
  }, runtime.rows.flatMap((row, i) => [/*#__PURE__*/React.createElement("span", {
    key: `k${i}`,
    className: "pv-run-k",
    "data-ui": __ds_scope.part(ui, "key")
  }, row.k), /*#__PURE__*/React.createElement("span", {
    key: `v${i}`,
    className: "pv-run-v",
    "data-ui": __ds_scope.part(ui, "value")
  }, row.v)])) : null);
}
Object.assign(__ds_scope, { RunBox });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/RunBox.jsx", error: String((e && e.message) || e) }); }

// components/detail/Section.jsx
try { (() => {
// A ruled block of the detail column with a small uppercase title and a count. Source:
// detail.mjs section (`dp-section`) and ticketSection (`pv-sec`).
function Section({
  ticket,
  title,
  note,
  children,
  "data-ui": ui
}) {
  const cls = ticket ? "pv-sec" : "dp-section";
  const titleCls = ticket ? "pv-sec-title" : "dp-section-title";
  return /*#__PURE__*/React.createElement("section", {
    className: cls,
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("div", {
    className: titleCls
  }, /*#__PURE__*/React.createElement("span", {
    "data-ui": __ds_scope.part(ui, "title")
  }, title), note == null ? null : /*#__PURE__*/React.createElement("span", {
    "data-ui": __ds_scope.part(ui, "count")
  }, String(note))), children);
}
Object.assign(__ds_scope, { Section });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/Section.jsx", error: String((e && e.message) || e) }); }

// components/detail/StatusLine.jsx
try { (() => {
// The lamp, its word, the step (tickets only) and the elapsed time or landed count.
// Source: detail.mjs ticketCard `va-status`, card `dp-status`.
function StatusLine({
  ticket,
  lamp,
  statusWord,
  phase,
  elapsed,
  "data-ui": ui
}) {
  if (ticket) {
    return /*#__PURE__*/React.createElement("div", {
      className: "va-status",
      "data-ui": ui
    }, /*#__PURE__*/React.createElement("span", {
      className: `lamp big ${lamp}`,
      "data-ui": __ds_scope.part(ui, "lamp")
    }), /*#__PURE__*/React.createElement("span", {
      className: `va-word ${lamp}`,
      "data-ui": __ds_scope.part(ui, "status")
    }, statusWord), /*#__PURE__*/React.createElement("span", {
      className: `pill big ${phase}`,
      "data-ui": __ds_scope.part(ui, "phase")
    }, phase), /*#__PURE__*/React.createElement("span", {
      className: "va-elapsed",
      "data-ui": __ds_scope.part(ui, "elapsed")
    }, elapsed || ""));
  }
  return /*#__PURE__*/React.createElement("div", {
    className: "dp-status",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("span", {
    className: `lamp big ${lamp}`,
    "data-ui": __ds_scope.part(ui, "lamp")
  }), /*#__PURE__*/React.createElement("span", {
    className: `status-word ${lamp}`,
    "data-ui": __ds_scope.part(ui, "status")
  }, statusWord), /*#__PURE__*/React.createElement("span", {
    className: "dp-elapsed",
    "data-ui": __ds_scope.part(ui, "elapsed")
  }, elapsed || ""));
}
Object.assign(__ds_scope, { StatusLine });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/StatusLine.jsx", error: String((e && e.message) || e) }); }

// components/detail/SubIssueRow.jsx
try { (() => {
// A sub-issue a ticket opened, with its kind; the three kinds that need the owner are
// orange. Source: detail.mjs ticketCard Sub-issues.
function SubIssueRow({
  kid,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "pv-rel",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("span", {
    className: `lamp ${kid.lamp}`,
    "data-ui": __ds_scope.part(ui, "lamp")
  }), /*#__PURE__*/React.createElement("span", {
    className: "pv-rel-n",
    "data-ui": __ds_scope.part(ui, "number")
  }, kid.num), /*#__PURE__*/React.createElement("span", {
    className: "pv-rel-t",
    "data-ui": __ds_scope.part(ui, "title")
  }, kid.title), /*#__PURE__*/React.createElement("span", {
    className: kid.hot ? "pv-kind hot" : "pv-kind",
    "data-ui": __ds_scope.part(ui, "kind")
  }, kid.kind));
}
Object.assign(__ds_scope, { SubIssueRow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/detail/SubIssueRow.jsx", error: String((e && e.message) || e) }); }

// components/settings/Button.jsx
try { (() => {
// A button of the sheet: plain, primary (ink fill), or a text link. Source: settings.mjs
// `.btn`, `.btn.primary`, `.linkbtn`.
function Button({
  kind,
  disabled,
  onClick,
  children,
  "data-ui": ui
}) {
  const cls = kind === "primary" ? "btn primary" : kind === "link" ? "linkbtn" : "btn";
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: cls,
    disabled: !!disabled,
    onClick: onClick,
    "data-ui": ui
  }, children);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/settings/Button.jsx", error: String((e && e.message) || e) }); }

// components/settings/CodeText.jsx
try { (() => {
// A command or file name inside the sheet's prose. Source: settings.mjs `span.sheet-code`.
function CodeText({
  children,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("span", {
    className: "sheet-code",
    "data-ui": ui
  }, children);
}
Object.assign(__ds_scope, { CodeText });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/settings/CodeText.jsx", error: String((e && e.message) || e) }); }

// components/settings/HostChip.jsx
try { (() => {
// One host and what this machine said about it. Source: settings.mjs paint `span.hs`;
// `chip` is one of local-config.mjs settingsView `chips`.
function HostChip({
  chip,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("span", {
    className: chip.cls,
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("span", {
    className: "hs-name",
    "data-ui": __ds_scope.part(ui, "name")
  }, chip.host), chip.what);
}
Object.assign(__ds_scope, { HostChip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/settings/HostChip.jsx", error: String((e && e.message) || e) }); }

// components/settings/ProblemList.jsx
try { (() => {
// What is wrong with a row, one hatched line each. Source: settings.mjs roleFoot.
function ProblemList({
  items = [],
  "data-ui": ui
}) {
  if (!items.length) return null;
  return /*#__PURE__*/React.createElement("div", {
    className: "role-foot",
    "data-ui": ui
  }, items.map((item, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "role-bad",
    "data-ui": __ds_scope.part(ui, "item")
  }, /*#__PURE__*/React.createElement("span", {
    className: "hatch"
  }), item.text)));
}
Object.assign(__ds_scope, { ProblemList });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/settings/ProblemList.jsx", error: String((e && e.message) || e) }); }

// components/settings/RefusedBanner.jsx
try { (() => {
// A save refused because the configuration changed elsewhere, with a way to read it
// again. Source: settings.mjs paint `div.refused`.
function RefusedBanner({
  text,
  onReread,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "refused",
    role: "alert",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("p", {
    className: "refused-text",
    "data-ui": __ds_scope.part(ui, "text")
  }, /*#__PURE__*/React.createElement("b", null, "\u6CA1\u6709\u4FDD\u5B58\u3002"), text), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "btn",
    onClick: onReread,
    "data-ui": __ds_scope.part(ui, "reread")
  }, "\u91CD\u65B0\u8BFB\u53D6"));
}
Object.assign(__ds_scope, { RefusedBanner });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/settings/RefusedBanner.jsx", error: String((e && e.message) || e) }); }

// components/settings/RolesTable.jsx
try { (() => {
// The four agents' rows under one column head, so the dropdowns line up. Source:
// settings.mjs paint `div.roles`.
function RolesTable({
  children,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "roles",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("div", {
    className: "roles-head",
    "data-ui": __ds_scope.part(ui, "head")
  }, /*#__PURE__*/React.createElement("span", null, "agent"), /*#__PURE__*/React.createElement("span", null, "host"), /*#__PURE__*/React.createElement("span", null, "model"), /*#__PURE__*/React.createElement("span", null, "effort")), children);
}
Object.assign(__ds_scope, { RolesTable });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/settings/RolesTable.jsx", error: String((e && e.message) || e) }); }

// components/settings/ScanStatus.jsx
try { (() => {
// When and where the hosts were last asked, and a rescan; or a spinner while asking.
// Source: settings.mjs paint `span.scan`.
function ScanStatus({
  scanning,
  scanningText,
  scannedText,
  onRescan,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("span", {
    className: "scan",
    "data-ui": ui
  }, scanning ? [/*#__PURE__*/React.createElement("span", {
    key: "s",
    className: "spin"
  }), scanningText] : [scannedText, /*#__PURE__*/React.createElement("button", {
    key: "b",
    type: "button",
    className: "linkbtn",
    onClick: onRescan,
    "data-ui": __ds_scope.part(ui, "rescan")
  }, "\u91CD\u65B0\u626B\u63CF")]);
}
Object.assign(__ds_scope, { ScanStatus });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/settings/ScanStatus.jsx", error: String((e && e.message) || e) }); }

// components/settings/Select.jsx
try { (() => {
// A dropdown of the sheet: a changed cell in heavier ink, one start would refuse
// hatched. Source: settings.mjs selectEl; `opts` are local-config.mjs options.
function Select({
  cls,
  value,
  disabled,
  label,
  opts = [],
  onChange,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("select", {
    className: cls,
    "aria-label": label,
    disabled: !!disabled,
    value: value ?? "",
    onChange: event => onChange && onChange(event.target.value),
    "data-ui": ui
  }, opts.map(option => /*#__PURE__*/React.createElement("option", {
    key: option.value,
    value: option.value,
    disabled: !!option.disabled,
    label: option.text
  }, option.text)));
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/settings/Select.jsx", error: String((e && e.message) || e) }); }

// components/settings/RoleRow.jsx
try { (() => {
// One agent's host, model and effort, with what is wrong with them. Source: settings.mjs
// paint `div.role`; `row` is one of local-config.mjs settingsView `rows`.
function RoleRow({
  row,
  onCell,
  "data-ui": ui
}) {
  const set = cell => value => onCell && onCell(row.agent, cell, value);
  return /*#__PURE__*/React.createElement("div", {
    className: "role",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("div", {
    className: "role-name"
  }, /*#__PURE__*/React.createElement("span", {
    className: "role-agent",
    "data-ui": __ds_scope.part(ui, "agent")
  }, row.agent), /*#__PURE__*/React.createElement("span", {
    className: "role-what",
    "data-ui": __ds_scope.part(ui, "what")
  }, row.what)), /*#__PURE__*/React.createElement(__ds_scope.Select, {
    cls: row.hostCls,
    value: row.host,
    disabled: row.hostOff,
    label: row.hostLabel,
    opts: row.hostOpts,
    onChange: set("host"),
    "data-ui": __ds_scope.part(ui, "host")
  }), /*#__PURE__*/React.createElement(__ds_scope.Select, {
    cls: row.modelCls,
    value: row.model,
    disabled: row.modelOff,
    label: row.modelLabel,
    opts: row.modelOpts,
    onChange: set("model"),
    "data-ui": __ds_scope.part(ui, "model")
  }), /*#__PURE__*/React.createElement(__ds_scope.Select, {
    cls: row.effortCls,
    value: row.effort,
    disabled: row.effortOff,
    label: row.effortLabel,
    opts: row.effortOpts,
    onChange: set("effort"),
    "data-ui": __ds_scope.part(ui, "effort")
  }), row.hasBad ? /*#__PURE__*/React.createElement(__ds_scope.ProblemList, {
    items: row.bads,
    "data-ui": __ds_scope.part(ui, "problem")
  }) : null);
}
Object.assign(__ds_scope, { RoleRow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/settings/RoleRow.jsx", error: String((e && e.message) || e) }); }

// components/settings/RunnerRow.jsx
try { (() => {
// Which runner starts sessions. Source: settings.mjs paint `div.runner-row`.
function RunnerRow({
  cls,
  value,
  disabled,
  opts,
  bads = [],
  onChange,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "runner-row",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("div", {
    className: "role-name"
  }, /*#__PURE__*/React.createElement("span", {
    className: "role-agent",
    "data-ui": __ds_scope.part(ui, "label")
  }, "runner"), /*#__PURE__*/React.createElement("span", {
    className: "role-what",
    "data-ui": __ds_scope.part(ui, "what")
  }, "\u7528\u4EC0\u4E48\u8D77 session")), /*#__PURE__*/React.createElement(__ds_scope.Select, {
    cls: cls,
    value: value,
    disabled: disabled,
    label: "runner",
    opts: opts,
    onChange: onChange,
    "data-ui": __ds_scope.part(ui, "select")
  }), bads.length ? /*#__PURE__*/React.createElement(__ds_scope.ProblemList, {
    items: bads,
    "data-ui": __ds_scope.part(ui, "problem")
  }) : null);
}
Object.assign(__ds_scope, { RunnerRow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/settings/RunnerRow.jsx", error: String((e && e.message) || e) }); }

// components/settings/SetBlock.jsx
try { (() => {
// One block of the sheet's body, ruled from the one above, with an optional heading row.
// Source: settings.mjs paint `section.set-block`.
function SetBlock({
  ruled,
  title,
  aside,
  children,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("section", {
    className: ruled ? "set-block ruled" : "set-block",
    "data-ui": ui
  }, title ? /*#__PURE__*/React.createElement("div", {
    className: "set-block-head"
  }, /*#__PURE__*/React.createElement("span", {
    className: "dp-section-title",
    "data-ui": __ds_scope.part(ui, "title")
  }, title), aside) : null, children);
}
Object.assign(__ds_scope, { SetBlock });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/settings/SetBlock.jsx", error: String((e && e.message) || e) }); }

// components/settings/SetNote.jsx
try { (() => {
// A quiet paragraph under a block of the sheet. Source: settings.mjs paint `p.set-note`.
function SetNote({
  children,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("p", {
    className: "set-note",
    "data-ui": ui
  }, children);
}
Object.assign(__ds_scope, { SetNote });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/settings/SetNote.jsx", error: String((e && e.message) || e) }); }

// components/settings/Sheet.jsx
try { (() => {
// The settings sheet over a dimmed page: head, a scrolling body, and a foot that says
// what a save would change. A click on the dim closes it only when nothing is changed.
// Source: settings.mjs paint (`scrim`, `sheet`, `sheet-head`, `sheet-body`, `sheet-foot`).
function Sheet({
  store,
  strong,
  quiet,
  hatch,
  closeLabel,
  saveOff,
  changed,
  onClose,
  onSave,
  children,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "scrim board",
    "data-ui": ui,
    onClick: event => {
      if (event.target === event.currentTarget && !changed && onClose) onClose();
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "sheet",
    role: "dialog",
    "aria-modal": "true",
    "aria-label": "\u672C\u673A\u914D\u7F6E"
  }, /*#__PURE__*/React.createElement("div", {
    className: "sheet-head"
  }, /*#__PURE__*/React.createElement("div", {
    className: "sheet-head-text"
  }, /*#__PURE__*/React.createElement("span", {
    className: "dp-eyebrow",
    "data-ui": __ds_scope.part(ui, "eyebrow")
  }, "\u672C\u673A\u914D\u7F6E"), /*#__PURE__*/React.createElement("h2", {
    className: "sheet-title",
    "data-ui": __ds_scope.part(ui, "title")
  }, "\u8FD9\u53F0\u673A\u5668\u4E0A\uFF0C\u6BCF\u4E2A agent \u8DD1\u5728\u54EA"), /*#__PURE__*/React.createElement("p", {
    className: "sheet-sub",
    "data-ui": __ds_scope.part(ui, "intro")
  }, "\u4E0B\u62C9\u83DC\u5355\u91CC\u7684\u9009\u9879\uFF0C\u662F MMW \u521A\u95EE\u8FC7\u8FD9\u53F0\u673A\u5668\u4E0A\u7684 host \u5F97\u5230\u7684\uFF0C\u95EE\u7684\u5730\u65B9\u548C ", /*#__PURE__*/React.createElement("span", {
    className: "sheet-code"
  }, "start"), " \u8D77 session \u65F6\u95EE\u7684\u662F\u540C\u4E00\u5904\u3002\u8FD9\u91CC\u5C31\u662F MMW \u7BA1\u8FD9\u4EF6\u4E8B\u7684\u552F\u4E00\u5730\u65B9\uFF0C\u4FDD\u5B58\u5728\u672C\u673A\u7684 ", /*#__PURE__*/React.createElement("span", {
    className: "sheet-code"
  }, store), "\uFF1B\u8FD9\u4E00\u9875\u4E0D\u5199 GitHub\u3002")), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "dp-close",
    "aria-label": "\u5173\u95ED\u672C\u673A\u914D\u7F6E",
    onClick: onClose,
    "data-ui": __ds_scope.part(ui, "close")
  }, "\xD7")), /*#__PURE__*/React.createElement("div", {
    className: "sheet-body"
  }, children), /*#__PURE__*/React.createElement("div", {
    className: "sheet-foot"
  }, /*#__PURE__*/React.createElement("div", {
    className: "foot-status",
    "aria-live": "polite"
  }, /*#__PURE__*/React.createElement("span", {
    className: "foot-strong",
    "data-ui": __ds_scope.part(ui, "status")
  }, hatch ? /*#__PURE__*/React.createElement("span", {
    className: "hatch"
  }) : null, strong), /*#__PURE__*/React.createElement("span", {
    className: "foot-quiet",
    "data-ui": __ds_scope.part(ui, "status-note")
  }, quiet)), /*#__PURE__*/React.createElement("div", {
    className: "foot-actions"
  }, /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "btn",
    onClick: onClose,
    "data-ui": __ds_scope.part(ui, "cancel")
  }, closeLabel), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "btn primary",
    disabled: !!saveOff,
    onClick: onSave,
    "data-ui": __ds_scope.part(ui, "save")
  }, "\u4FDD\u5B58")))));
}
Object.assign(__ds_scope, { Sheet });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/settings/Sheet.jsx", error: String((e && e.message) || e) }); }

// components/status/Lamp.jsx
try { (() => {
// One dot that answers "does this need me". Source: board.css "the lamp"; the product
// writes `lamp <size> <tone>` (detail.mjs `lamp big …`, canvas.mjs `lamp small …`).
function Lamp({
  tone = "hollow",
  size,
  title,
  "data-ui": ui
}) {
  const cls = ["lamp", size, tone].filter(Boolean).join(" ");
  return /*#__PURE__*/React.createElement("span", {
    className: cls,
    title: title,
    "data-ui": ui
  });
}
Object.assign(__ds_scope, { Lamp });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/status/Lamp.jsx", error: String((e && e.message) || e) }); }

// components/status/StepPill.jsx
try { (() => {
// The capsule that names the step a ticket is at. Source: board.css "the pill";
// canvas.mjs ticketCard, detail.mjs `pill big …`. `children` replaces the step name
// where the product writes a count beside it (detail.mjs phases-count).
function StepPill({
  phase,
  big,
  children,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("span", {
    className: big ? `pill big ${phase}` : `pill ${phase}`,
    "data-ui": ui
  }, children ?? phase);
}
Object.assign(__ds_scope, { StepPill });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/status/StepPill.jsx", error: String((e && e.message) || e) }); }

// components/tasks/ColumnEyebrow.jsx
try { (() => {
// The small uppercase heading over the task list, with its count. Source: tasks.mjs
// render, `div.col-eyebrow`.
function ColumnEyebrow({
  label,
  count,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "col-eyebrow",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("span", {
    "data-ui": __ds_scope.part(ui, "label")
  }, label), /*#__PURE__*/React.createElement("span", {
    "data-ui": __ds_scope.part(ui, "count")
  }, String(count)));
}
Object.assign(__ds_scope, { ColumnEyebrow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/tasks/ColumnEyebrow.jsx", error: String((e && e.message) || e) }); }

// components/tasks/TaskRow.jsx
try { (() => {
// One task in the left column: its lamp, number and kind, title, and landed progress.
// Source: tasks.mjs rowButton. `row` is one row of tasks.mjs taskListView.
function TaskRow({
  row,
  onPick,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: row.cls,
    onClick: onPick,
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("span", {
    className: row.lampCls,
    title: row.lampWord,
    "data-ui": __ds_scope.part(ui, "lamp")
  }), /*#__PURE__*/React.createElement("span", {
    className: "task-meta",
    "data-ui": __ds_scope.part(ui, "meta")
  }, row.meta), /*#__PURE__*/React.createElement("span", {
    className: row.titleCls,
    "data-ui": __ds_scope.part(ui, "title")
  }, row.title), /*#__PURE__*/React.createElement("span", {
    className: "task-progress"
  }, /*#__PURE__*/React.createElement("span", {
    className: "bar"
  }, /*#__PURE__*/React.createElement("span", {
    className: "bar-fill",
    style: {
      width: row.barStyle.width
    },
    "data-ui": __ds_scope.part(ui, "bar")
  })), /*#__PURE__*/React.createElement("span", {
    className: "task-count",
    "data-ui": __ds_scope.part(ui, "count")
  }, row.count)));
}
Object.assign(__ds_scope, { TaskRow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/tasks/TaskRow.jsx", error: String((e && e.message) || e) }); }

// components/tasks/TasksEmpty.jsx
try { (() => {
// What the task list says when no ticket carries the map label. Source: tasks.mjs
// render, `p.tasks-empty`.
function TasksEmpty({
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("p", {
    className: "tasks-empty",
    "data-ui": ui
  }, "\u6CA1\u6709\u5E26 mmw:map label \u7684 ticket\u3002");
}
Object.assign(__ds_scope, { TasksEmpty });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/tasks/TasksEmpty.jsx", error: String((e && e.message) || e) }); }

// components/topbar/Brand.jsx
try { (() => {
// The word mark at the left of the top bar. Source: topbar.mjs render, `div.brand`.
function Brand({
  repo,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "brand",
    "data-ui": ui
  }, /*#__PURE__*/React.createElement("span", {
    className: "brand-mark",
    "data-ui": __ds_scope.part(ui, "mark")
  }, "MMW"), /*#__PURE__*/React.createElement("span", {
    className: "brand-name",
    "data-ui": __ds_scope.part(ui, "name")
  }, "task board"), /*#__PURE__*/React.createElement("span", {
    className: "brand-repo",
    "data-ui": __ds_scope.part(ui, "repo")
  }, repo));
}
Object.assign(__ds_scope, { Brand });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/topbar/Brand.jsx", error: String((e && e.message) || e) }); }

// components/topbar/Counter.jsx
try { (() => {
// One lamp count in the top bar. Source: topbar.mjs render, `.counter`. The
// "needs you" counter is a button that jumps to the next orange ticket (`hot` while
// there is one); the other three are plain spans.
function Counter({
  lamp,
  label,
  count,
  sub,
  button,
  hot,
  title,
  onClick,
  "data-ui": ui
}) {
  const kids = [/*#__PURE__*/React.createElement("span", {
    key: "l",
    className: `lamp ${lamp}`,
    "data-ui": __ds_scope.part(ui, "lamp")
  }), label, /*#__PURE__*/React.createElement("span", {
    key: "n",
    className: hot ? "counter-n hot" : "counter-n",
    "data-ui": __ds_scope.part(ui, "count")
  }, String(count)), sub ? /*#__PURE__*/React.createElement("span", {
    key: "s",
    className: "counter-sub",
    "data-ui": __ds_scope.part(ui, "sub")
  }, sub) : null];
  if (button) {
    return /*#__PURE__*/React.createElement("button", {
      type: "button",
      className: hot ? "counter hot" : "counter",
      disabled: !hot,
      title: title,
      onClick: onClick,
      "data-ui": ui
    }, kids);
  }
  return /*#__PURE__*/React.createElement("span", {
    className: "counter",
    "data-ui": ui
  }, kids);
}
Object.assign(__ds_scope, { Counter });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/topbar/Counter.jsx", error: String((e && e.message) || e) }); }

// components/topbar/IconButton.jsx
try { (() => {
// A square icon button at the right end of the top bar. Source: topbar.mjs render,
// `button.gear`; the icons are Lucide's rotate-cw and settings, as the product inlines them.
const ICONS = {
  refresh: '<svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path></svg>',
  settings: '<svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg>'
};
function IconButton({
  icon,
  on,
  label,
  title,
  onClick,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: on ? "gear on" : "gear",
    "aria-label": label,
    title: title,
    onClick: onClick,
    "data-ui": ui,
    dangerouslySetInnerHTML: {
      __html: ICONS[icon]
    }
  });
}
Object.assign(__ds_scope, { IconButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/topbar/IconButton.jsx", error: String((e && e.message) || e) }); }

// components/topbar/ReadState.jsx
try { (() => {
// When the page last read GitHub, or that the last read failed. Source: topbar.mjs
// render, `div.readstate`.
function ReadState({
  failed,
  text,
  "data-ui": ui
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: failed ? "readstate failed" : "readstate",
    "data-ui": ui
  }, text);
}
Object.assign(__ds_scope, { ReadState });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/topbar/ReadState.jsx", error: String((e && e.message) || e) }); }

// ui_kits/task-board/data/board-morning.js
try { (() => {
(window.BOARD_SCENES = window.BOARD_SCENES || {})["morning"] = {
  "name": "一夜之后",
  "now": "2026-09-10T23:40:00Z",
  "select": {
    "task": 98,
    "node": 133
  },
  "payload": {
    "tasks": [{
      "n": 98,
      "kind": "map",
      "title": "落地流水线改造",
      "state": "open",
      "decisions": [{
        "n": 99,
        "kind": "grilling",
        "title": "事件格式怎么定",
        "state": "closed",
        "blocked": []
      }, {
        "n": 100,
        "kind": "research",
        "title": "读票用什么",
        "state": "closed",
        "blocked": [99]
      }, {
        "n": 104,
        "kind": "prototype",
        "title": "唤醒要不要队列",
        "state": "closed",
        "blocked": [99]
      }, {
        "n": 105,
        "kind": "grilling",
        "title": "槽位推到哪一步",
        "state": "closed",
        "blocked": [100, 104]
      }, {
        "n": 106,
        "kind": "task",
        "title": "判活放哪一层",
        "state": "closed",
        "blocked": [105]
      }, {
        "n": 107,
        "kind": "grilling",
        "title": "团队版什么时候做",
        "state": "open",
        "blocked": [105]
      }],
      "specs": [{
        "n": 123,
        "title": "事件评论格式",
        "tickets": [{
          "n": 124,
          "title": "事件表与校验",
          "state": "closed",
          "blocked": [],
          "blockers": [],
          "blocker_hold": "",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 124,
            "events": [{
              "comment": 3180012400,
              "event": "worker.started",
              "at": "2026-09-10T12:05:00Z",
              "actor": "main",
              "line": "worker started on herdr: session we60f, cursor grok 4.6 (high)"
            }, {
              "comment": 3180012401,
              "event": "ticket.claimed",
              "at": "2026-09-10T12:05:00Z",
              "actor": "worker",
              "line": "Claimed #124 on issue-124 as chancheuklap"
            }, {
              "comment": 3180012402,
              "event": "ticket.checked",
              "at": "2026-09-10T12:43:00Z",
              "actor": "worker",
              "line": "Own run on 3c9089867fcc: ALL MET"
            }, {
              "comment": 3180012403,
              "event": "reviewer.started",
              "at": "2026-09-10T12:48:00Z",
              "actor": "worker",
              "line": "reviewer started on herdr: session wf19c, codex gpt-5.5 (medium)"
            }, {
              "comment": 3180012404,
              "event": "reviewer.reported",
              "at": "2026-09-10T13:01:00Z",
              "actor": "reviewer",
              "line": "REVIEW 4d2fce8de7c07b570423636266f7ae40c04c08f3..3c9089867fcc85a5a04fdc3d01544410a75da9d6"
            }, {
              "comment": 3180012405,
              "event": "worker.decided",
              "at": "2026-09-10T13:05:00Z",
              "actor": "worker",
              "line": "DECISIONS"
            }, {
              "comment": 3180012406,
              "event": "ticket.checked",
              "at": "2026-09-10T13:18:00Z",
              "actor": "worker",
              "line": "Reverify on 3c9089867fcc: ALL MET"
            }, {
              "comment": 3180012407,
              "event": "ticket.checked",
              "at": "2026-09-10T13:28:00Z",
              "actor": "worker",
              "line": "Repository checks on 3c9089867fcc: 3/3 passed"
            }, {
              "comment": 3180012408,
              "event": "ticket.passed",
              "at": "2026-09-10T13:31:00Z",
              "actor": "worker",
              "line": "ALL MET"
            }, {
              "comment": 3180012409,
              "event": "ticket.landed",
              "at": "2026-09-10T13:41:00Z",
              "actor": "main",
              "line": "Landed issue-124 into main"
            }],
            "last": {
              "comment": 3180012409,
              "event": "ticket.landed",
              "at": "2026-09-10T13:41:00Z",
              "actor": "main",
              "line": "Landed issue-124 into main",
              "body": "Landed issue-124 into main\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.landed\",\"stage\":\"land\",\"actor\":\"main\",\"spec\":123,\"ticket\":124,\"at\":\"2026-09-10T13:41:00Z\",\"branch\":\"issue-124\",\"into\":\"main\",\"commit\":\"3c9089867fcc85a5a04fdc3d01544410a75da9d6\",\"merge\":\"8d53661ca8f95f64083595fd504ff644e3aaa722\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.landed",
                "stage": "land",
                "actor": "main",
                "spec": 123,
                "ticket": 124,
                "at": "2026-09-10T13:41:00Z",
                "branch": "issue-124",
                "into": "main",
                "commit": "3c9089867fcc85a5a04fdc3d01544410a75da9d6",
                "merge": "8d53661ca8f95f64083595fd504ff644e3aaa722"
              }
            },
            "unreadable": [],
            "claimed": false,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": true,
            "returned": false,
            "outcome": {
              "comment": 3180012408,
              "event": "ticket.passed",
              "at": "2026-09-10T13:31:00Z",
              "actor": "worker",
              "line": "ALL MET",
              "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":123,\"ticket\":124,\"at\":\"2026-09-10T13:31:00Z\",\"commit\":\"3c9089867fcc85a5a04fdc3d01544410a75da9d6\",\"branch\":\"issue-124\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"main\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.passed",
                "stage": "close",
                "actor": "worker",
                "spec": 123,
                "ticket": 124,
                "at": "2026-09-10T13:31:00Z",
                "commit": "3c9089867fcc85a5a04fdc3d01544410a75da9d6",
                "branch": "issue-124",
                "counts": {
                  "met": 4,
                  "unmet": 0,
                  "abandoned": 0,
                  "total": 4
                },
                "into": "main"
              }
            },
            "landed": true,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": {
              "comment": 3180012404,
              "event": "reviewer.reported",
              "at": "2026-09-10T13:01:00Z",
              "actor": "reviewer",
              "line": "REVIEW 4d2fce8de7c07b570423636266f7ae40c04c08f3..3c9089867fcc85a5a04fdc3d01544410a75da9d6",
              "body": "REVIEW 4d2fce8de7c07b570423636266f7ae40c04c08f3..3c9089867fcc85a5a04fdc3d01544410a75da9d6\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":123,\"ticket\":124,\"at\":\"2026-09-10T13:01:00Z\",\"base\":\"4d2fce8de7c07b570423636266f7ae40c04c08f3\",\"head\":\"3c9089867fcc85a5a04fdc3d01544410a75da9d6\"} -->\n",
              "payload": {
                "v": 1,
                "event": "reviewer.reported",
                "stage": "review",
                "actor": "reviewer",
                "spec": 123,
                "ticket": 124,
                "at": "2026-09-10T13:01:00Z",
                "base": "4d2fce8de7c07b570423636266f7ae40c04c08f3",
                "head": "3c9089867fcc85a5a04fdc3d01544410a75da9d6"
              }
            },
            "decided": 1,
            "results": {
              "worker": {
                "comment": 3180012408,
                "event": "ticket.passed",
                "at": "2026-09-10T13:31:00Z",
                "actor": "worker",
                "line": "ALL MET",
                "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":123,\"ticket\":124,\"at\":\"2026-09-10T13:31:00Z\",\"commit\":\"3c9089867fcc85a5a04fdc3d01544410a75da9d6\",\"branch\":\"issue-124\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"main\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.passed",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 124,
                  "at": "2026-09-10T13:31:00Z",
                  "commit": "3c9089867fcc85a5a04fdc3d01544410a75da9d6",
                  "branch": "issue-124",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "into": "main"
                }
              },
              "reviewer": {
                "comment": 3180012404,
                "event": "reviewer.reported",
                "at": "2026-09-10T13:01:00Z",
                "actor": "reviewer",
                "line": "REVIEW 4d2fce8de7c07b570423636266f7ae40c04c08f3..3c9089867fcc85a5a04fdc3d01544410a75da9d6",
                "body": "REVIEW 4d2fce8de7c07b570423636266f7ae40c04c08f3..3c9089867fcc85a5a04fdc3d01544410a75da9d6\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":123,\"ticket\":124,\"at\":\"2026-09-10T13:01:00Z\",\"base\":\"4d2fce8de7c07b570423636266f7ae40c04c08f3\",\"head\":\"3c9089867fcc85a5a04fdc3d01544410a75da9d6\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "reviewer.reported",
                  "stage": "review",
                  "actor": "reviewer",
                  "spec": 123,
                  "ticket": 124,
                  "at": "2026-09-10T13:01:00Z",
                  "base": "4d2fce8de7c07b570423636266f7ae40c04c08f3",
                  "head": "3c9089867fcc85a5a04fdc3d01544410a75da9d6"
                }
              }
            },
            "checks": {
              "self": {
                "comment": 3180012402,
                "event": "ticket.checked",
                "at": "2026-09-10T12:43:00Z",
                "actor": "worker",
                "line": "Own run on 3c9089867fcc: ALL MET",
                "body": "Own run on 3c9089867fcc: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":123,\"ticket\":124,\"at\":\"2026-09-10T12:43:00Z\",\"run\":\"self\",\"commit\":\"3c9089867fcc85a5a04fdc3d01544410a75da9d6\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"f62356028a736716cdbe1f9a0fea2835a77d599d38c9fa26a6774ae515ce96a6\",\"slot\":1,\"port_base\":21100,\"outside_owns\":[]} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "work",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 124,
                  "at": "2026-09-10T12:43:00Z",
                  "run": "self",
                  "commit": "3c9089867fcc85a5a04fdc3d01544410a75da9d6",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "f62356028a736716cdbe1f9a0fea2835a77d599d38c9fa26a6774ae515ce96a6",
                  "slot": 1,
                  "port_base": 21100,
                  "outside_owns": []
                }
              },
              "reverify": {
                "comment": 3180012406,
                "event": "ticket.checked",
                "at": "2026-09-10T13:18:00Z",
                "actor": "worker",
                "line": "Reverify on 3c9089867fcc: ALL MET",
                "body": "Reverify on 3c9089867fcc: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"verify\",\"actor\":\"worker\",\"spec\":123,\"ticket\":124,\"at\":\"2026-09-10T13:18:00Z\",\"run\":\"reverify\",\"commit\":\"3c9089867fcc85a5a04fdc3d01544410a75da9d6\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"f62356028a736716cdbe1f9a0fea2835a77d599d38c9fa26a6774ae515ce96a6\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "verify",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 124,
                  "at": "2026-09-10T13:18:00Z",
                  "run": "reverify",
                  "commit": "3c9089867fcc85a5a04fdc3d01544410a75da9d6",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "f62356028a736716cdbe1f9a0fea2835a77d599d38c9fa26a6774ae515ce96a6"
                }
              },
              "repo-checks": {
                "comment": 3180012407,
                "event": "ticket.checked",
                "at": "2026-09-10T13:28:00Z",
                "actor": "worker",
                "line": "Repository checks on 3c9089867fcc: 3/3 passed",
                "body": "Repository checks on 3c9089867fcc: 3/3 passed\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":123,\"ticket\":124,\"at\":\"2026-09-10T13:28:00Z\",\"run\":\"repo-checks\",\"commit\":\"3c9089867fcc85a5a04fdc3d01544410a75da9d6\",\"result\":\"met\",\"counts\":{\"passed\":3,\"total\":3}} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 124,
                  "at": "2026-09-10T13:28:00Z",
                  "run": "repo-checks",
                  "commit": "3c9089867fcc85a5a04fdc3d01544410a75da9d6",
                  "result": "met",
                  "counts": {
                    "passed": 3,
                    "total": 3
                  }
                }
              },
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [{
              "kind": "worker",
              "session": "we60f",
              "runner": "herdr",
              "host": "cursor",
              "model": "grok 4.6",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/124-work",
              "branch": "issue-124",
              "base": "4d2fce8de7c07b570423636266f7ae40c04c08f3",
              "into": "main",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T12:05:00Z",
              "comment": 3180012400,
              "live": false,
              "ended_by": "ticket.landed"
            }, {
              "kind": "reviewer",
              "session": "wf19c",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/124-work",
              "branch": "issue-124",
              "base": "4d2fce8de7c07b570423636266f7ae40c04c08f3",
              "into": null,
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T12:48:00Z",
              "comment": 3180012403,
              "live": false,
              "ended_by": "reviewer.reported"
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "we60f",
              "runner": "herdr",
              "host": "cursor",
              "model": "grok 4.6",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/124-work",
              "branch": "issue-124",
              "base": "4d2fce8de7c07b570423636266f7ae40c04c08f3",
              "into": "main",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T12:05:00Z",
              "comment": 3180012400,
              "live": false,
              "ended_by": "ticket.landed"
            },
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": true
          },
          "events": [{
            "comment": 3180012400,
            "event": "worker.started",
            "at": "2026-09-10T12:05:00Z",
            "actor": "main",
            "line": "worker started on herdr: session we60f, cursor grok 4.6 (high)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 123,
              "ticket": 124,
              "at": "2026-09-10T12:05:00Z",
              "session": "we60f",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "cursor",
              "model": "grok 4.6",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/124-work",
              "branch": "issue-124",
              "base": "4d2fce8de7c07b570423636266f7ae40c04c08f3",
              "into": "main"
            }
          }, {
            "comment": 3180012401,
            "event": "ticket.claimed",
            "at": "2026-09-10T12:05:00Z",
            "actor": "worker",
            "line": "Claimed #124 on issue-124 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 123,
              "ticket": 124,
              "at": "2026-09-10T12:05:00Z",
              "login": "chancheuklap",
              "branch": "issue-124",
              "commit": "4d2fce8de7c07b570423636266f7ae40c04c08f3"
            }
          }, {
            "comment": 3180012402,
            "event": "ticket.checked",
            "at": "2026-09-10T12:43:00Z",
            "actor": "worker",
            "line": "Own run on 3c9089867fcc: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "work",
              "actor": "worker",
              "spec": 123,
              "ticket": 124,
              "at": "2026-09-10T12:43:00Z",
              "run": "self",
              "commit": "3c9089867fcc85a5a04fdc3d01544410a75da9d6",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "f62356028a736716cdbe1f9a0fea2835a77d599d38c9fa26a6774ae515ce96a6",
              "slot": 1,
              "port_base": 21100,
              "outside_owns": []
            }
          }, {
            "comment": 3180012403,
            "event": "reviewer.started",
            "at": "2026-09-10T12:48:00Z",
            "actor": "worker",
            "line": "reviewer started on herdr: session wf19c, codex gpt-5.5 (medium)",
            "payload": {
              "v": 1,
              "event": "reviewer.started",
              "stage": "review",
              "actor": "worker",
              "spec": 123,
              "ticket": 124,
              "at": "2026-09-10T12:48:00Z",
              "session": "wf19c",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/124-work",
              "branch": "issue-124",
              "base": "4d2fce8de7c07b570423636266f7ae40c04c08f3"
            }
          }, {
            "comment": 3180012404,
            "event": "reviewer.reported",
            "at": "2026-09-10T13:01:00Z",
            "actor": "reviewer",
            "line": "REVIEW 4d2fce8de7c07b570423636266f7ae40c04c08f3..3c9089867fcc85a5a04fdc3d01544410a75da9d6",
            "payload": {
              "v": 1,
              "event": "reviewer.reported",
              "stage": "review",
              "actor": "reviewer",
              "spec": 123,
              "ticket": 124,
              "at": "2026-09-10T13:01:00Z",
              "base": "4d2fce8de7c07b570423636266f7ae40c04c08f3",
              "head": "3c9089867fcc85a5a04fdc3d01544410a75da9d6"
            }
          }, {
            "comment": 3180012405,
            "event": "worker.decided",
            "at": "2026-09-10T13:05:00Z",
            "actor": "worker",
            "line": "DECISIONS",
            "payload": {
              "v": 1,
              "event": "worker.decided",
              "stage": "work",
              "actor": "worker",
              "spec": 123,
              "ticket": 124,
              "at": "2026-09-10T13:05:00Z"
            }
          }, {
            "comment": 3180012406,
            "event": "ticket.checked",
            "at": "2026-09-10T13:18:00Z",
            "actor": "worker",
            "line": "Reverify on 3c9089867fcc: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "verify",
              "actor": "worker",
              "spec": 123,
              "ticket": 124,
              "at": "2026-09-10T13:18:00Z",
              "run": "reverify",
              "commit": "3c9089867fcc85a5a04fdc3d01544410a75da9d6",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "f62356028a736716cdbe1f9a0fea2835a77d599d38c9fa26a6774ae515ce96a6"
            }
          }, {
            "comment": 3180012407,
            "event": "ticket.checked",
            "at": "2026-09-10T13:28:00Z",
            "actor": "worker",
            "line": "Repository checks on 3c9089867fcc: 3/3 passed",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "close",
              "actor": "worker",
              "spec": 123,
              "ticket": 124,
              "at": "2026-09-10T13:28:00Z",
              "run": "repo-checks",
              "commit": "3c9089867fcc85a5a04fdc3d01544410a75da9d6",
              "result": "met",
              "counts": {
                "passed": 3,
                "total": 3
              }
            }
          }, {
            "comment": 3180012408,
            "event": "ticket.passed",
            "at": "2026-09-10T13:31:00Z",
            "actor": "worker",
            "line": "ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.passed",
              "stage": "close",
              "actor": "worker",
              "spec": 123,
              "ticket": 124,
              "at": "2026-09-10T13:31:00Z",
              "commit": "3c9089867fcc85a5a04fdc3d01544410a75da9d6",
              "branch": "issue-124",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "into": "main"
            }
          }, {
            "comment": 3180012409,
            "event": "ticket.landed",
            "at": "2026-09-10T13:41:00Z",
            "actor": "main",
            "line": "Landed issue-124 into main",
            "payload": {
              "v": 1,
              "event": "ticket.landed",
              "stage": "land",
              "actor": "main",
              "spec": 123,
              "ticket": 124,
              "at": "2026-09-10T13:41:00Z",
              "branch": "issue-124",
              "into": "main",
              "commit": "3c9089867fcc85a5a04fdc3d01544410a75da9d6",
              "merge": "8d53661ca8f95f64083595fd504ff644e3aaa722"
            }
          }]
        }, {
          "n": 125,
          "title": "折叠重放",
          "state": "closed",
          "blocked": [124],
          "blockers": [{
            "number": 124,
            "title": "事件表与校验",
            "state": "closed",
            "spec": 123,
            "readable": true,
            "blocker_hold": ""
          }],
          "blocker_hold": "",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 125,
            "events": [{
              "comment": 3180012500,
              "event": "worker.started",
              "at": "2026-09-10T13:42:00Z",
              "actor": "main",
              "line": "worker started on herdr: session w28c4, grok grok 4.6 (xhigh)"
            }, {
              "comment": 3180012501,
              "event": "ticket.claimed",
              "at": "2026-09-10T13:42:00Z",
              "actor": "worker",
              "line": "Claimed #125 on issue-125 as chancheuklap"
            }, {
              "comment": 3180012502,
              "event": "ticket.checked",
              "at": "2026-09-10T14:26:00Z",
              "actor": "worker",
              "line": "Own run on 5fdc40ea96d3: ALL MET"
            }, {
              "comment": 3180012503,
              "event": "reviewer.started",
              "at": "2026-09-10T14:32:00Z",
              "actor": "worker",
              "line": "reviewer started on herdr: session w477d, codex gpt-5.5 (medium)"
            }, {
              "comment": 3180012504,
              "event": "reviewer.reported",
              "at": "2026-09-10T14:46:00Z",
              "actor": "reviewer",
              "line": "REVIEW e98c49005b3d0fa9cad061c2030deabff931c0fe..5fdc40ea96d3e3cc4721956a08a3dda5da757806"
            }, {
              "comment": 3180012505,
              "event": "worker.decided",
              "at": "2026-09-10T14:51:00Z",
              "actor": "worker",
              "line": "DECISIONS"
            }, {
              "comment": 3180012506,
              "event": "ticket.checked",
              "at": "2026-09-10T15:06:00Z",
              "actor": "worker",
              "line": "Reverify on 5fdc40ea96d3: ALL MET"
            }, {
              "comment": 3180012507,
              "event": "ticket.checked",
              "at": "2026-09-10T15:17:00Z",
              "actor": "worker",
              "line": "Repository checks on 5fdc40ea96d3: 3/3 passed"
            }, {
              "comment": 3180012508,
              "event": "ticket.passed",
              "at": "2026-09-10T15:22:00Z",
              "actor": "worker",
              "line": "ALL MET"
            }, {
              "comment": 3180012509,
              "event": "ticket.landed",
              "at": "2026-09-10T15:33:00Z",
              "actor": "main",
              "line": "Landed issue-125 into main"
            }],
            "last": {
              "comment": 3180012509,
              "event": "ticket.landed",
              "at": "2026-09-10T15:33:00Z",
              "actor": "main",
              "line": "Landed issue-125 into main",
              "body": "Landed issue-125 into main\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.landed\",\"stage\":\"land\",\"actor\":\"main\",\"spec\":123,\"ticket\":125,\"at\":\"2026-09-10T15:33:00Z\",\"branch\":\"issue-125\",\"into\":\"main\",\"commit\":\"5fdc40ea96d3e3cc4721956a08a3dda5da757806\",\"merge\":\"3d05768364d37ef1bf037ef14364634f83931a0f\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.landed",
                "stage": "land",
                "actor": "main",
                "spec": 123,
                "ticket": 125,
                "at": "2026-09-10T15:33:00Z",
                "branch": "issue-125",
                "into": "main",
                "commit": "5fdc40ea96d3e3cc4721956a08a3dda5da757806",
                "merge": "3d05768364d37ef1bf037ef14364634f83931a0f"
              }
            },
            "unreadable": [],
            "claimed": false,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": true,
            "returned": false,
            "outcome": {
              "comment": 3180012508,
              "event": "ticket.passed",
              "at": "2026-09-10T15:22:00Z",
              "actor": "worker",
              "line": "ALL MET",
              "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":123,\"ticket\":125,\"at\":\"2026-09-10T15:22:00Z\",\"commit\":\"5fdc40ea96d3e3cc4721956a08a3dda5da757806\",\"branch\":\"issue-125\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"main\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.passed",
                "stage": "close",
                "actor": "worker",
                "spec": 123,
                "ticket": 125,
                "at": "2026-09-10T15:22:00Z",
                "commit": "5fdc40ea96d3e3cc4721956a08a3dda5da757806",
                "branch": "issue-125",
                "counts": {
                  "met": 4,
                  "unmet": 0,
                  "abandoned": 0,
                  "total": 4
                },
                "into": "main"
              }
            },
            "landed": true,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": {
              "comment": 3180012504,
              "event": "reviewer.reported",
              "at": "2026-09-10T14:46:00Z",
              "actor": "reviewer",
              "line": "REVIEW e98c49005b3d0fa9cad061c2030deabff931c0fe..5fdc40ea96d3e3cc4721956a08a3dda5da757806",
              "body": "REVIEW e98c49005b3d0fa9cad061c2030deabff931c0fe..5fdc40ea96d3e3cc4721956a08a3dda5da757806\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":123,\"ticket\":125,\"at\":\"2026-09-10T14:46:00Z\",\"base\":\"e98c49005b3d0fa9cad061c2030deabff931c0fe\",\"head\":\"5fdc40ea96d3e3cc4721956a08a3dda5da757806\"} -->\n",
              "payload": {
                "v": 1,
                "event": "reviewer.reported",
                "stage": "review",
                "actor": "reviewer",
                "spec": 123,
                "ticket": 125,
                "at": "2026-09-10T14:46:00Z",
                "base": "e98c49005b3d0fa9cad061c2030deabff931c0fe",
                "head": "5fdc40ea96d3e3cc4721956a08a3dda5da757806"
              }
            },
            "decided": 1,
            "results": {
              "worker": {
                "comment": 3180012508,
                "event": "ticket.passed",
                "at": "2026-09-10T15:22:00Z",
                "actor": "worker",
                "line": "ALL MET",
                "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":123,\"ticket\":125,\"at\":\"2026-09-10T15:22:00Z\",\"commit\":\"5fdc40ea96d3e3cc4721956a08a3dda5da757806\",\"branch\":\"issue-125\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"main\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.passed",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 125,
                  "at": "2026-09-10T15:22:00Z",
                  "commit": "5fdc40ea96d3e3cc4721956a08a3dda5da757806",
                  "branch": "issue-125",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "into": "main"
                }
              },
              "reviewer": {
                "comment": 3180012504,
                "event": "reviewer.reported",
                "at": "2026-09-10T14:46:00Z",
                "actor": "reviewer",
                "line": "REVIEW e98c49005b3d0fa9cad061c2030deabff931c0fe..5fdc40ea96d3e3cc4721956a08a3dda5da757806",
                "body": "REVIEW e98c49005b3d0fa9cad061c2030deabff931c0fe..5fdc40ea96d3e3cc4721956a08a3dda5da757806\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":123,\"ticket\":125,\"at\":\"2026-09-10T14:46:00Z\",\"base\":\"e98c49005b3d0fa9cad061c2030deabff931c0fe\",\"head\":\"5fdc40ea96d3e3cc4721956a08a3dda5da757806\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "reviewer.reported",
                  "stage": "review",
                  "actor": "reviewer",
                  "spec": 123,
                  "ticket": 125,
                  "at": "2026-09-10T14:46:00Z",
                  "base": "e98c49005b3d0fa9cad061c2030deabff931c0fe",
                  "head": "5fdc40ea96d3e3cc4721956a08a3dda5da757806"
                }
              }
            },
            "checks": {
              "self": {
                "comment": 3180012502,
                "event": "ticket.checked",
                "at": "2026-09-10T14:26:00Z",
                "actor": "worker",
                "line": "Own run on 5fdc40ea96d3: ALL MET",
                "body": "Own run on 5fdc40ea96d3: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":123,\"ticket\":125,\"at\":\"2026-09-10T14:26:00Z\",\"run\":\"self\",\"commit\":\"5fdc40ea96d3e3cc4721956a08a3dda5da757806\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"016ffe5658b56833803bc743fa0f643e3659ddda5cda0911f67da09dd25fd986\",\"slot\":1,\"port_base\":21100,\"outside_owns\":[]} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "work",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 125,
                  "at": "2026-09-10T14:26:00Z",
                  "run": "self",
                  "commit": "5fdc40ea96d3e3cc4721956a08a3dda5da757806",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "016ffe5658b56833803bc743fa0f643e3659ddda5cda0911f67da09dd25fd986",
                  "slot": 1,
                  "port_base": 21100,
                  "outside_owns": []
                }
              },
              "reverify": {
                "comment": 3180012506,
                "event": "ticket.checked",
                "at": "2026-09-10T15:06:00Z",
                "actor": "worker",
                "line": "Reverify on 5fdc40ea96d3: ALL MET",
                "body": "Reverify on 5fdc40ea96d3: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"verify\",\"actor\":\"worker\",\"spec\":123,\"ticket\":125,\"at\":\"2026-09-10T15:06:00Z\",\"run\":\"reverify\",\"commit\":\"5fdc40ea96d3e3cc4721956a08a3dda5da757806\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"016ffe5658b56833803bc743fa0f643e3659ddda5cda0911f67da09dd25fd986\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "verify",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 125,
                  "at": "2026-09-10T15:06:00Z",
                  "run": "reverify",
                  "commit": "5fdc40ea96d3e3cc4721956a08a3dda5da757806",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "016ffe5658b56833803bc743fa0f643e3659ddda5cda0911f67da09dd25fd986"
                }
              },
              "repo-checks": {
                "comment": 3180012507,
                "event": "ticket.checked",
                "at": "2026-09-10T15:17:00Z",
                "actor": "worker",
                "line": "Repository checks on 5fdc40ea96d3: 3/3 passed",
                "body": "Repository checks on 5fdc40ea96d3: 3/3 passed\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":123,\"ticket\":125,\"at\":\"2026-09-10T15:17:00Z\",\"run\":\"repo-checks\",\"commit\":\"5fdc40ea96d3e3cc4721956a08a3dda5da757806\",\"result\":\"met\",\"counts\":{\"passed\":3,\"total\":3}} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 125,
                  "at": "2026-09-10T15:17:00Z",
                  "run": "repo-checks",
                  "commit": "5fdc40ea96d3e3cc4721956a08a3dda5da757806",
                  "result": "met",
                  "counts": {
                    "passed": 3,
                    "total": 3
                  }
                }
              },
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [{
              "kind": "worker",
              "session": "w28c4",
              "runner": "herdr",
              "host": "grok",
              "model": "grok 4.6",
              "effort": "xhigh",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/125-work",
              "branch": "issue-125",
              "base": "e98c49005b3d0fa9cad061c2030deabff931c0fe",
              "into": "main",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T13:42:00Z",
              "comment": 3180012500,
              "live": false,
              "ended_by": "ticket.landed"
            }, {
              "kind": "reviewer",
              "session": "w477d",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/125-work",
              "branch": "issue-125",
              "base": "e98c49005b3d0fa9cad061c2030deabff931c0fe",
              "into": null,
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T14:32:00Z",
              "comment": 3180012503,
              "live": false,
              "ended_by": "reviewer.reported"
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "w28c4",
              "runner": "herdr",
              "host": "grok",
              "model": "grok 4.6",
              "effort": "xhigh",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/125-work",
              "branch": "issue-125",
              "base": "e98c49005b3d0fa9cad061c2030deabff931c0fe",
              "into": "main",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T13:42:00Z",
              "comment": 3180012500,
              "live": false,
              "ended_by": "ticket.landed"
            },
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": true
          },
          "events": [{
            "comment": 3180012500,
            "event": "worker.started",
            "at": "2026-09-10T13:42:00Z",
            "actor": "main",
            "line": "worker started on herdr: session w28c4, grok grok 4.6 (xhigh)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 123,
              "ticket": 125,
              "at": "2026-09-10T13:42:00Z",
              "session": "w28c4",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "grok",
              "model": "grok 4.6",
              "effort": "xhigh",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/125-work",
              "branch": "issue-125",
              "base": "e98c49005b3d0fa9cad061c2030deabff931c0fe",
              "into": "main"
            }
          }, {
            "comment": 3180012501,
            "event": "ticket.claimed",
            "at": "2026-09-10T13:42:00Z",
            "actor": "worker",
            "line": "Claimed #125 on issue-125 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 123,
              "ticket": 125,
              "at": "2026-09-10T13:42:00Z",
              "login": "chancheuklap",
              "branch": "issue-125",
              "commit": "e98c49005b3d0fa9cad061c2030deabff931c0fe"
            }
          }, {
            "comment": 3180012502,
            "event": "ticket.checked",
            "at": "2026-09-10T14:26:00Z",
            "actor": "worker",
            "line": "Own run on 5fdc40ea96d3: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "work",
              "actor": "worker",
              "spec": 123,
              "ticket": 125,
              "at": "2026-09-10T14:26:00Z",
              "run": "self",
              "commit": "5fdc40ea96d3e3cc4721956a08a3dda5da757806",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "016ffe5658b56833803bc743fa0f643e3659ddda5cda0911f67da09dd25fd986",
              "slot": 1,
              "port_base": 21100,
              "outside_owns": []
            }
          }, {
            "comment": 3180012503,
            "event": "reviewer.started",
            "at": "2026-09-10T14:32:00Z",
            "actor": "worker",
            "line": "reviewer started on herdr: session w477d, codex gpt-5.5 (medium)",
            "payload": {
              "v": 1,
              "event": "reviewer.started",
              "stage": "review",
              "actor": "worker",
              "spec": 123,
              "ticket": 125,
              "at": "2026-09-10T14:32:00Z",
              "session": "w477d",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/125-work",
              "branch": "issue-125",
              "base": "e98c49005b3d0fa9cad061c2030deabff931c0fe"
            }
          }, {
            "comment": 3180012504,
            "event": "reviewer.reported",
            "at": "2026-09-10T14:46:00Z",
            "actor": "reviewer",
            "line": "REVIEW e98c49005b3d0fa9cad061c2030deabff931c0fe..5fdc40ea96d3e3cc4721956a08a3dda5da757806",
            "payload": {
              "v": 1,
              "event": "reviewer.reported",
              "stage": "review",
              "actor": "reviewer",
              "spec": 123,
              "ticket": 125,
              "at": "2026-09-10T14:46:00Z",
              "base": "e98c49005b3d0fa9cad061c2030deabff931c0fe",
              "head": "5fdc40ea96d3e3cc4721956a08a3dda5da757806"
            }
          }, {
            "comment": 3180012505,
            "event": "worker.decided",
            "at": "2026-09-10T14:51:00Z",
            "actor": "worker",
            "line": "DECISIONS",
            "payload": {
              "v": 1,
              "event": "worker.decided",
              "stage": "work",
              "actor": "worker",
              "spec": 123,
              "ticket": 125,
              "at": "2026-09-10T14:51:00Z"
            }
          }, {
            "comment": 3180012506,
            "event": "ticket.checked",
            "at": "2026-09-10T15:06:00Z",
            "actor": "worker",
            "line": "Reverify on 5fdc40ea96d3: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "verify",
              "actor": "worker",
              "spec": 123,
              "ticket": 125,
              "at": "2026-09-10T15:06:00Z",
              "run": "reverify",
              "commit": "5fdc40ea96d3e3cc4721956a08a3dda5da757806",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "016ffe5658b56833803bc743fa0f643e3659ddda5cda0911f67da09dd25fd986"
            }
          }, {
            "comment": 3180012507,
            "event": "ticket.checked",
            "at": "2026-09-10T15:17:00Z",
            "actor": "worker",
            "line": "Repository checks on 5fdc40ea96d3: 3/3 passed",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "close",
              "actor": "worker",
              "spec": 123,
              "ticket": 125,
              "at": "2026-09-10T15:17:00Z",
              "run": "repo-checks",
              "commit": "5fdc40ea96d3e3cc4721956a08a3dda5da757806",
              "result": "met",
              "counts": {
                "passed": 3,
                "total": 3
              }
            }
          }, {
            "comment": 3180012508,
            "event": "ticket.passed",
            "at": "2026-09-10T15:22:00Z",
            "actor": "worker",
            "line": "ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.passed",
              "stage": "close",
              "actor": "worker",
              "spec": 123,
              "ticket": 125,
              "at": "2026-09-10T15:22:00Z",
              "commit": "5fdc40ea96d3e3cc4721956a08a3dda5da757806",
              "branch": "issue-125",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "into": "main"
            }
          }, {
            "comment": 3180012509,
            "event": "ticket.landed",
            "at": "2026-09-10T15:33:00Z",
            "actor": "main",
            "line": "Landed issue-125 into main",
            "payload": {
              "v": 1,
              "event": "ticket.landed",
              "stage": "land",
              "actor": "main",
              "spec": 123,
              "ticket": 125,
              "at": "2026-09-10T15:33:00Z",
              "branch": "issue-125",
              "into": "main",
              "commit": "5fdc40ea96d3e3cc4721956a08a3dda5da757806",
              "merge": "3d05768364d37ef1bf037ef14364634f83931a0f"
            }
          }]
        }, {
          "n": 127,
          "title": "一次 GraphQL 读四层",
          "state": "closed",
          "blocked": [124],
          "blockers": [{
            "number": 124,
            "title": "事件表与校验",
            "state": "closed",
            "spec": 123,
            "readable": true,
            "blocker_hold": ""
          }],
          "blocker_hold": "",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 127,
            "events": [{
              "comment": 3180012700,
              "event": "worker.started",
              "at": "2026-09-10T13:42:00Z",
              "actor": "main",
              "line": "worker started on herdr: session w1057, claude opus 5 (high)"
            }, {
              "comment": 3180012701,
              "event": "ticket.claimed",
              "at": "2026-09-10T13:42:00Z",
              "actor": "worker",
              "line": "Claimed #127 on issue-127 as chancheuklap"
            }, {
              "comment": 3180012702,
              "event": "ticket.checked",
              "at": "2026-09-10T14:15:00Z",
              "actor": "worker",
              "line": "Own run on 58d668608321: ALL MET"
            }, {
              "comment": 3180012703,
              "event": "reviewer.started",
              "at": "2026-09-10T14:19:00Z",
              "actor": "worker",
              "line": "reviewer started on herdr: session w5f2f, codex gpt-5.5 (medium)"
            }, {
              "comment": 3180012704,
              "event": "reviewer.reported",
              "at": "2026-09-10T14:30:00Z",
              "actor": "reviewer",
              "line": "REVIEW 7be308639045b53f97e0fca53fe6b05f6242f777..58d668608321f7b2d37e81ea0a776d5dd5db5074"
            }, {
              "comment": 3180012705,
              "event": "worker.decided",
              "at": "2026-09-10T14:33:00Z",
              "actor": "worker",
              "line": "DECISIONS"
            }, {
              "comment": 3180012706,
              "event": "ticket.checked",
              "at": "2026-09-10T14:44:00Z",
              "actor": "worker",
              "line": "Reverify on 58d668608321: ALL MET"
            }, {
              "comment": 3180012707,
              "event": "ticket.checked",
              "at": "2026-09-10T14:53:00Z",
              "actor": "worker",
              "line": "Repository checks on 58d668608321: 3/3 passed"
            }, {
              "comment": 3180012708,
              "event": "ticket.passed",
              "at": "2026-09-10T14:56:00Z",
              "actor": "worker",
              "line": "ALL MET"
            }, {
              "comment": 3180012709,
              "event": "ticket.landed",
              "at": "2026-09-10T15:04:00Z",
              "actor": "main",
              "line": "Landed issue-127 into main"
            }],
            "last": {
              "comment": 3180012709,
              "event": "ticket.landed",
              "at": "2026-09-10T15:04:00Z",
              "actor": "main",
              "line": "Landed issue-127 into main",
              "body": "Landed issue-127 into main\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.landed\",\"stage\":\"land\",\"actor\":\"main\",\"spec\":123,\"ticket\":127,\"at\":\"2026-09-10T15:04:00Z\",\"branch\":\"issue-127\",\"into\":\"main\",\"commit\":\"58d668608321f7b2d37e81ea0a776d5dd5db5074\",\"merge\":\"9675e6eceda17d772c39c80f17b08e3d57a4dfe3\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.landed",
                "stage": "land",
                "actor": "main",
                "spec": 123,
                "ticket": 127,
                "at": "2026-09-10T15:04:00Z",
                "branch": "issue-127",
                "into": "main",
                "commit": "58d668608321f7b2d37e81ea0a776d5dd5db5074",
                "merge": "9675e6eceda17d772c39c80f17b08e3d57a4dfe3"
              }
            },
            "unreadable": [],
            "claimed": false,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": true,
            "returned": false,
            "outcome": {
              "comment": 3180012708,
              "event": "ticket.passed",
              "at": "2026-09-10T14:56:00Z",
              "actor": "worker",
              "line": "ALL MET",
              "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":123,\"ticket\":127,\"at\":\"2026-09-10T14:56:00Z\",\"commit\":\"58d668608321f7b2d37e81ea0a776d5dd5db5074\",\"branch\":\"issue-127\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"main\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.passed",
                "stage": "close",
                "actor": "worker",
                "spec": 123,
                "ticket": 127,
                "at": "2026-09-10T14:56:00Z",
                "commit": "58d668608321f7b2d37e81ea0a776d5dd5db5074",
                "branch": "issue-127",
                "counts": {
                  "met": 4,
                  "unmet": 0,
                  "abandoned": 0,
                  "total": 4
                },
                "into": "main"
              }
            },
            "landed": true,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": {
              "comment": 3180012704,
              "event": "reviewer.reported",
              "at": "2026-09-10T14:30:00Z",
              "actor": "reviewer",
              "line": "REVIEW 7be308639045b53f97e0fca53fe6b05f6242f777..58d668608321f7b2d37e81ea0a776d5dd5db5074",
              "body": "REVIEW 7be308639045b53f97e0fca53fe6b05f6242f777..58d668608321f7b2d37e81ea0a776d5dd5db5074\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":123,\"ticket\":127,\"at\":\"2026-09-10T14:30:00Z\",\"base\":\"7be308639045b53f97e0fca53fe6b05f6242f777\",\"head\":\"58d668608321f7b2d37e81ea0a776d5dd5db5074\"} -->\n",
              "payload": {
                "v": 1,
                "event": "reviewer.reported",
                "stage": "review",
                "actor": "reviewer",
                "spec": 123,
                "ticket": 127,
                "at": "2026-09-10T14:30:00Z",
                "base": "7be308639045b53f97e0fca53fe6b05f6242f777",
                "head": "58d668608321f7b2d37e81ea0a776d5dd5db5074"
              }
            },
            "decided": 1,
            "results": {
              "worker": {
                "comment": 3180012708,
                "event": "ticket.passed",
                "at": "2026-09-10T14:56:00Z",
                "actor": "worker",
                "line": "ALL MET",
                "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":123,\"ticket\":127,\"at\":\"2026-09-10T14:56:00Z\",\"commit\":\"58d668608321f7b2d37e81ea0a776d5dd5db5074\",\"branch\":\"issue-127\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"main\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.passed",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 127,
                  "at": "2026-09-10T14:56:00Z",
                  "commit": "58d668608321f7b2d37e81ea0a776d5dd5db5074",
                  "branch": "issue-127",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "into": "main"
                }
              },
              "reviewer": {
                "comment": 3180012704,
                "event": "reviewer.reported",
                "at": "2026-09-10T14:30:00Z",
                "actor": "reviewer",
                "line": "REVIEW 7be308639045b53f97e0fca53fe6b05f6242f777..58d668608321f7b2d37e81ea0a776d5dd5db5074",
                "body": "REVIEW 7be308639045b53f97e0fca53fe6b05f6242f777..58d668608321f7b2d37e81ea0a776d5dd5db5074\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":123,\"ticket\":127,\"at\":\"2026-09-10T14:30:00Z\",\"base\":\"7be308639045b53f97e0fca53fe6b05f6242f777\",\"head\":\"58d668608321f7b2d37e81ea0a776d5dd5db5074\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "reviewer.reported",
                  "stage": "review",
                  "actor": "reviewer",
                  "spec": 123,
                  "ticket": 127,
                  "at": "2026-09-10T14:30:00Z",
                  "base": "7be308639045b53f97e0fca53fe6b05f6242f777",
                  "head": "58d668608321f7b2d37e81ea0a776d5dd5db5074"
                }
              }
            },
            "checks": {
              "self": {
                "comment": 3180012702,
                "event": "ticket.checked",
                "at": "2026-09-10T14:15:00Z",
                "actor": "worker",
                "line": "Own run on 58d668608321: ALL MET",
                "body": "Own run on 58d668608321: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":123,\"ticket\":127,\"at\":\"2026-09-10T14:15:00Z\",\"run\":\"self\",\"commit\":\"58d668608321f7b2d37e81ea0a776d5dd5db5074\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"71b0214acd34321c306c869dad3d78dd37f0a7ec107c74cee1f129c69efd6148\",\"slot\":1,\"port_base\":21100,\"outside_owns\":[]} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "work",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 127,
                  "at": "2026-09-10T14:15:00Z",
                  "run": "self",
                  "commit": "58d668608321f7b2d37e81ea0a776d5dd5db5074",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "71b0214acd34321c306c869dad3d78dd37f0a7ec107c74cee1f129c69efd6148",
                  "slot": 1,
                  "port_base": 21100,
                  "outside_owns": []
                }
              },
              "reverify": {
                "comment": 3180012706,
                "event": "ticket.checked",
                "at": "2026-09-10T14:44:00Z",
                "actor": "worker",
                "line": "Reverify on 58d668608321: ALL MET",
                "body": "Reverify on 58d668608321: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"verify\",\"actor\":\"worker\",\"spec\":123,\"ticket\":127,\"at\":\"2026-09-10T14:44:00Z\",\"run\":\"reverify\",\"commit\":\"58d668608321f7b2d37e81ea0a776d5dd5db5074\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"71b0214acd34321c306c869dad3d78dd37f0a7ec107c74cee1f129c69efd6148\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "verify",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 127,
                  "at": "2026-09-10T14:44:00Z",
                  "run": "reverify",
                  "commit": "58d668608321f7b2d37e81ea0a776d5dd5db5074",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "71b0214acd34321c306c869dad3d78dd37f0a7ec107c74cee1f129c69efd6148"
                }
              },
              "repo-checks": {
                "comment": 3180012707,
                "event": "ticket.checked",
                "at": "2026-09-10T14:53:00Z",
                "actor": "worker",
                "line": "Repository checks on 58d668608321: 3/3 passed",
                "body": "Repository checks on 58d668608321: 3/3 passed\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":123,\"ticket\":127,\"at\":\"2026-09-10T14:53:00Z\",\"run\":\"repo-checks\",\"commit\":\"58d668608321f7b2d37e81ea0a776d5dd5db5074\",\"result\":\"met\",\"counts\":{\"passed\":3,\"total\":3}} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 127,
                  "at": "2026-09-10T14:53:00Z",
                  "run": "repo-checks",
                  "commit": "58d668608321f7b2d37e81ea0a776d5dd5db5074",
                  "result": "met",
                  "counts": {
                    "passed": 3,
                    "total": 3
                  }
                }
              },
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [{
              "kind": "worker",
              "session": "w1057",
              "runner": "herdr",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/127-work",
              "branch": "issue-127",
              "base": "7be308639045b53f97e0fca53fe6b05f6242f777",
              "into": "main",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T13:42:00Z",
              "comment": 3180012700,
              "live": false,
              "ended_by": "ticket.landed"
            }, {
              "kind": "reviewer",
              "session": "w5f2f",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/127-work",
              "branch": "issue-127",
              "base": "7be308639045b53f97e0fca53fe6b05f6242f777",
              "into": null,
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T14:19:00Z",
              "comment": 3180012703,
              "live": false,
              "ended_by": "reviewer.reported"
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "w1057",
              "runner": "herdr",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/127-work",
              "branch": "issue-127",
              "base": "7be308639045b53f97e0fca53fe6b05f6242f777",
              "into": "main",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T13:42:00Z",
              "comment": 3180012700,
              "live": false,
              "ended_by": "ticket.landed"
            },
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": true
          },
          "events": [{
            "comment": 3180012700,
            "event": "worker.started",
            "at": "2026-09-10T13:42:00Z",
            "actor": "main",
            "line": "worker started on herdr: session w1057, claude opus 5 (high)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 123,
              "ticket": 127,
              "at": "2026-09-10T13:42:00Z",
              "session": "w1057",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/127-work",
              "branch": "issue-127",
              "base": "7be308639045b53f97e0fca53fe6b05f6242f777",
              "into": "main"
            }
          }, {
            "comment": 3180012701,
            "event": "ticket.claimed",
            "at": "2026-09-10T13:42:00Z",
            "actor": "worker",
            "line": "Claimed #127 on issue-127 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 123,
              "ticket": 127,
              "at": "2026-09-10T13:42:00Z",
              "login": "chancheuklap",
              "branch": "issue-127",
              "commit": "7be308639045b53f97e0fca53fe6b05f6242f777"
            }
          }, {
            "comment": 3180012702,
            "event": "ticket.checked",
            "at": "2026-09-10T14:15:00Z",
            "actor": "worker",
            "line": "Own run on 58d668608321: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "work",
              "actor": "worker",
              "spec": 123,
              "ticket": 127,
              "at": "2026-09-10T14:15:00Z",
              "run": "self",
              "commit": "58d668608321f7b2d37e81ea0a776d5dd5db5074",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "71b0214acd34321c306c869dad3d78dd37f0a7ec107c74cee1f129c69efd6148",
              "slot": 1,
              "port_base": 21100,
              "outside_owns": []
            }
          }, {
            "comment": 3180012703,
            "event": "reviewer.started",
            "at": "2026-09-10T14:19:00Z",
            "actor": "worker",
            "line": "reviewer started on herdr: session w5f2f, codex gpt-5.5 (medium)",
            "payload": {
              "v": 1,
              "event": "reviewer.started",
              "stage": "review",
              "actor": "worker",
              "spec": 123,
              "ticket": 127,
              "at": "2026-09-10T14:19:00Z",
              "session": "w5f2f",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/127-work",
              "branch": "issue-127",
              "base": "7be308639045b53f97e0fca53fe6b05f6242f777"
            }
          }, {
            "comment": 3180012704,
            "event": "reviewer.reported",
            "at": "2026-09-10T14:30:00Z",
            "actor": "reviewer",
            "line": "REVIEW 7be308639045b53f97e0fca53fe6b05f6242f777..58d668608321f7b2d37e81ea0a776d5dd5db5074",
            "payload": {
              "v": 1,
              "event": "reviewer.reported",
              "stage": "review",
              "actor": "reviewer",
              "spec": 123,
              "ticket": 127,
              "at": "2026-09-10T14:30:00Z",
              "base": "7be308639045b53f97e0fca53fe6b05f6242f777",
              "head": "58d668608321f7b2d37e81ea0a776d5dd5db5074"
            }
          }, {
            "comment": 3180012705,
            "event": "worker.decided",
            "at": "2026-09-10T14:33:00Z",
            "actor": "worker",
            "line": "DECISIONS",
            "payload": {
              "v": 1,
              "event": "worker.decided",
              "stage": "work",
              "actor": "worker",
              "spec": 123,
              "ticket": 127,
              "at": "2026-09-10T14:33:00Z"
            }
          }, {
            "comment": 3180012706,
            "event": "ticket.checked",
            "at": "2026-09-10T14:44:00Z",
            "actor": "worker",
            "line": "Reverify on 58d668608321: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "verify",
              "actor": "worker",
              "spec": 123,
              "ticket": 127,
              "at": "2026-09-10T14:44:00Z",
              "run": "reverify",
              "commit": "58d668608321f7b2d37e81ea0a776d5dd5db5074",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "71b0214acd34321c306c869dad3d78dd37f0a7ec107c74cee1f129c69efd6148"
            }
          }, {
            "comment": 3180012707,
            "event": "ticket.checked",
            "at": "2026-09-10T14:53:00Z",
            "actor": "worker",
            "line": "Repository checks on 58d668608321: 3/3 passed",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "close",
              "actor": "worker",
              "spec": 123,
              "ticket": 127,
              "at": "2026-09-10T14:53:00Z",
              "run": "repo-checks",
              "commit": "58d668608321f7b2d37e81ea0a776d5dd5db5074",
              "result": "met",
              "counts": {
                "passed": 3,
                "total": 3
              }
            }
          }, {
            "comment": 3180012708,
            "event": "ticket.passed",
            "at": "2026-09-10T14:56:00Z",
            "actor": "worker",
            "line": "ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.passed",
              "stage": "close",
              "actor": "worker",
              "spec": 123,
              "ticket": 127,
              "at": "2026-09-10T14:56:00Z",
              "commit": "58d668608321f7b2d37e81ea0a776d5dd5db5074",
              "branch": "issue-127",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "into": "main"
            }
          }, {
            "comment": 3180012709,
            "event": "ticket.landed",
            "at": "2026-09-10T15:04:00Z",
            "actor": "main",
            "line": "Landed issue-127 into main",
            "payload": {
              "v": 1,
              "event": "ticket.landed",
              "stage": "land",
              "actor": "main",
              "spec": 123,
              "ticket": 127,
              "at": "2026-09-10T15:04:00Z",
              "branch": "issue-127",
              "into": "main",
              "commit": "58d668608321f7b2d37e81ea0a776d5dd5db5074",
              "merge": "9675e6eceda17d772c39c80f17b08e3d57a4dfe3"
            }
          }]
        }, {
          "n": 126,
          "title": "status.py 改读折叠",
          "state": "closed",
          "blocked": [125],
          "blockers": [{
            "number": 125,
            "title": "折叠重放",
            "state": "closed",
            "spec": 123,
            "readable": true,
            "blocker_hold": ""
          }],
          "blocker_hold": "",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 126,
            "events": [{
              "comment": 3180012600,
              "event": "worker.started",
              "at": "2026-09-10T15:34:00Z",
              "actor": "main",
              "line": "worker started on herdr: session w6989, codex gpt-5.5 (high)"
            }, {
              "comment": 3180012601,
              "event": "ticket.claimed",
              "at": "2026-09-10T15:34:00Z",
              "actor": "worker",
              "line": "Claimed #126 on issue-126 as chancheuklap"
            }, {
              "comment": 3180012602,
              "event": "ticket.checked",
              "at": "2026-09-10T16:19:00Z",
              "actor": "worker",
              "line": "Own run on a856900d5448: ALL MET"
            }, {
              "comment": 3180012603,
              "event": "reviewer.started",
              "at": "2026-09-10T16:24:00Z",
              "actor": "worker",
              "line": "reviewer started on herdr: session w8195, codex gpt-5.5 (medium)"
            }, {
              "comment": 3180012604,
              "event": "reviewer.reported",
              "at": "2026-09-10T16:39:00Z",
              "actor": "reviewer",
              "line": "REVIEW 5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890..a856900d544832dd0b0e44abb809c24715d2fae7"
            }, {
              "comment": 3180012605,
              "event": "worker.decided",
              "at": "2026-09-10T16:43:00Z",
              "actor": "worker",
              "line": "DECISIONS"
            }, {
              "comment": 3180012606,
              "event": "ticket.checked",
              "at": "2026-09-10T16:59:00Z",
              "actor": "worker",
              "line": "Reverify on a856900d5448: ALL MET"
            }, {
              "comment": 3180012607,
              "event": "ticket.checked",
              "at": "2026-09-10T17:10:00Z",
              "actor": "worker",
              "line": "Repository checks on a856900d5448: 3/3 passed"
            }, {
              "comment": 3180012608,
              "event": "ticket.passed",
              "at": "2026-09-10T17:15:00Z",
              "actor": "worker",
              "line": "ALL MET"
            }, {
              "comment": 3180012609,
              "event": "ticket.landed",
              "at": "2026-09-10T17:26:00Z",
              "actor": "main",
              "line": "Landed issue-126 into main"
            }],
            "last": {
              "comment": 3180012609,
              "event": "ticket.landed",
              "at": "2026-09-10T17:26:00Z",
              "actor": "main",
              "line": "Landed issue-126 into main",
              "body": "Landed issue-126 into main\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.landed\",\"stage\":\"land\",\"actor\":\"main\",\"spec\":123,\"ticket\":126,\"at\":\"2026-09-10T17:26:00Z\",\"branch\":\"issue-126\",\"into\":\"main\",\"commit\":\"a856900d544832dd0b0e44abb809c24715d2fae7\",\"merge\":\"6fa808ea85d117531cd85ade6ba1cabce132f1f0\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.landed",
                "stage": "land",
                "actor": "main",
                "spec": 123,
                "ticket": 126,
                "at": "2026-09-10T17:26:00Z",
                "branch": "issue-126",
                "into": "main",
                "commit": "a856900d544832dd0b0e44abb809c24715d2fae7",
                "merge": "6fa808ea85d117531cd85ade6ba1cabce132f1f0"
              }
            },
            "unreadable": [],
            "claimed": false,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": true,
            "returned": false,
            "outcome": {
              "comment": 3180012608,
              "event": "ticket.passed",
              "at": "2026-09-10T17:15:00Z",
              "actor": "worker",
              "line": "ALL MET",
              "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":123,\"ticket\":126,\"at\":\"2026-09-10T17:15:00Z\",\"commit\":\"a856900d544832dd0b0e44abb809c24715d2fae7\",\"branch\":\"issue-126\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"main\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.passed",
                "stage": "close",
                "actor": "worker",
                "spec": 123,
                "ticket": 126,
                "at": "2026-09-10T17:15:00Z",
                "commit": "a856900d544832dd0b0e44abb809c24715d2fae7",
                "branch": "issue-126",
                "counts": {
                  "met": 4,
                  "unmet": 0,
                  "abandoned": 0,
                  "total": 4
                },
                "into": "main"
              }
            },
            "landed": true,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": {
              "comment": 3180012604,
              "event": "reviewer.reported",
              "at": "2026-09-10T16:39:00Z",
              "actor": "reviewer",
              "line": "REVIEW 5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890..a856900d544832dd0b0e44abb809c24715d2fae7",
              "body": "REVIEW 5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890..a856900d544832dd0b0e44abb809c24715d2fae7\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":123,\"ticket\":126,\"at\":\"2026-09-10T16:39:00Z\",\"base\":\"5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890\",\"head\":\"a856900d544832dd0b0e44abb809c24715d2fae7\"} -->\n",
              "payload": {
                "v": 1,
                "event": "reviewer.reported",
                "stage": "review",
                "actor": "reviewer",
                "spec": 123,
                "ticket": 126,
                "at": "2026-09-10T16:39:00Z",
                "base": "5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890",
                "head": "a856900d544832dd0b0e44abb809c24715d2fae7"
              }
            },
            "decided": 1,
            "results": {
              "worker": {
                "comment": 3180012608,
                "event": "ticket.passed",
                "at": "2026-09-10T17:15:00Z",
                "actor": "worker",
                "line": "ALL MET",
                "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":123,\"ticket\":126,\"at\":\"2026-09-10T17:15:00Z\",\"commit\":\"a856900d544832dd0b0e44abb809c24715d2fae7\",\"branch\":\"issue-126\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"main\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.passed",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 126,
                  "at": "2026-09-10T17:15:00Z",
                  "commit": "a856900d544832dd0b0e44abb809c24715d2fae7",
                  "branch": "issue-126",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "into": "main"
                }
              },
              "reviewer": {
                "comment": 3180012604,
                "event": "reviewer.reported",
                "at": "2026-09-10T16:39:00Z",
                "actor": "reviewer",
                "line": "REVIEW 5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890..a856900d544832dd0b0e44abb809c24715d2fae7",
                "body": "REVIEW 5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890..a856900d544832dd0b0e44abb809c24715d2fae7\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":123,\"ticket\":126,\"at\":\"2026-09-10T16:39:00Z\",\"base\":\"5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890\",\"head\":\"a856900d544832dd0b0e44abb809c24715d2fae7\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "reviewer.reported",
                  "stage": "review",
                  "actor": "reviewer",
                  "spec": 123,
                  "ticket": 126,
                  "at": "2026-09-10T16:39:00Z",
                  "base": "5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890",
                  "head": "a856900d544832dd0b0e44abb809c24715d2fae7"
                }
              }
            },
            "checks": {
              "self": {
                "comment": 3180012602,
                "event": "ticket.checked",
                "at": "2026-09-10T16:19:00Z",
                "actor": "worker",
                "line": "Own run on a856900d5448: ALL MET",
                "body": "Own run on a856900d5448: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":123,\"ticket\":126,\"at\":\"2026-09-10T16:19:00Z\",\"run\":\"self\",\"commit\":\"a856900d544832dd0b0e44abb809c24715d2fae7\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"5e2829ad5a245d2edcf8bb5646113b926136045ad80a69c621383f3e33617c17\",\"slot\":1,\"port_base\":21100,\"outside_owns\":[]} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "work",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 126,
                  "at": "2026-09-10T16:19:00Z",
                  "run": "self",
                  "commit": "a856900d544832dd0b0e44abb809c24715d2fae7",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "5e2829ad5a245d2edcf8bb5646113b926136045ad80a69c621383f3e33617c17",
                  "slot": 1,
                  "port_base": 21100,
                  "outside_owns": []
                }
              },
              "reverify": {
                "comment": 3180012606,
                "event": "ticket.checked",
                "at": "2026-09-10T16:59:00Z",
                "actor": "worker",
                "line": "Reverify on a856900d5448: ALL MET",
                "body": "Reverify on a856900d5448: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"verify\",\"actor\":\"worker\",\"spec\":123,\"ticket\":126,\"at\":\"2026-09-10T16:59:00Z\",\"run\":\"reverify\",\"commit\":\"a856900d544832dd0b0e44abb809c24715d2fae7\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"5e2829ad5a245d2edcf8bb5646113b926136045ad80a69c621383f3e33617c17\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "verify",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 126,
                  "at": "2026-09-10T16:59:00Z",
                  "run": "reverify",
                  "commit": "a856900d544832dd0b0e44abb809c24715d2fae7",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "5e2829ad5a245d2edcf8bb5646113b926136045ad80a69c621383f3e33617c17"
                }
              },
              "repo-checks": {
                "comment": 3180012607,
                "event": "ticket.checked",
                "at": "2026-09-10T17:10:00Z",
                "actor": "worker",
                "line": "Repository checks on a856900d5448: 3/3 passed",
                "body": "Repository checks on a856900d5448: 3/3 passed\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":123,\"ticket\":126,\"at\":\"2026-09-10T17:10:00Z\",\"run\":\"repo-checks\",\"commit\":\"a856900d544832dd0b0e44abb809c24715d2fae7\",\"result\":\"met\",\"counts\":{\"passed\":3,\"total\":3}} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 123,
                  "ticket": 126,
                  "at": "2026-09-10T17:10:00Z",
                  "run": "repo-checks",
                  "commit": "a856900d544832dd0b0e44abb809c24715d2fae7",
                  "result": "met",
                  "counts": {
                    "passed": 3,
                    "total": 3
                  }
                }
              },
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [{
              "kind": "worker",
              "session": "w6989",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/126-work",
              "branch": "issue-126",
              "base": "5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890",
              "into": "main",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T15:34:00Z",
              "comment": 3180012600,
              "live": false,
              "ended_by": "ticket.landed"
            }, {
              "kind": "reviewer",
              "session": "w8195",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/126-work",
              "branch": "issue-126",
              "base": "5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890",
              "into": null,
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T16:24:00Z",
              "comment": 3180012603,
              "live": false,
              "ended_by": "reviewer.reported"
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "w6989",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/126-work",
              "branch": "issue-126",
              "base": "5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890",
              "into": "main",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T15:34:00Z",
              "comment": 3180012600,
              "live": false,
              "ended_by": "ticket.landed"
            },
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": true
          },
          "events": [{
            "comment": 3180012600,
            "event": "worker.started",
            "at": "2026-09-10T15:34:00Z",
            "actor": "main",
            "line": "worker started on herdr: session w6989, codex gpt-5.5 (high)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 123,
              "ticket": 126,
              "at": "2026-09-10T15:34:00Z",
              "session": "w6989",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/126-work",
              "branch": "issue-126",
              "base": "5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890",
              "into": "main"
            }
          }, {
            "comment": 3180012601,
            "event": "ticket.claimed",
            "at": "2026-09-10T15:34:00Z",
            "actor": "worker",
            "line": "Claimed #126 on issue-126 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 123,
              "ticket": 126,
              "at": "2026-09-10T15:34:00Z",
              "login": "chancheuklap",
              "branch": "issue-126",
              "commit": "5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890"
            }
          }, {
            "comment": 3180012602,
            "event": "ticket.checked",
            "at": "2026-09-10T16:19:00Z",
            "actor": "worker",
            "line": "Own run on a856900d5448: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "work",
              "actor": "worker",
              "spec": 123,
              "ticket": 126,
              "at": "2026-09-10T16:19:00Z",
              "run": "self",
              "commit": "a856900d544832dd0b0e44abb809c24715d2fae7",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "5e2829ad5a245d2edcf8bb5646113b926136045ad80a69c621383f3e33617c17",
              "slot": 1,
              "port_base": 21100,
              "outside_owns": []
            }
          }, {
            "comment": 3180012603,
            "event": "reviewer.started",
            "at": "2026-09-10T16:24:00Z",
            "actor": "worker",
            "line": "reviewer started on herdr: session w8195, codex gpt-5.5 (medium)",
            "payload": {
              "v": 1,
              "event": "reviewer.started",
              "stage": "review",
              "actor": "worker",
              "spec": 123,
              "ticket": 126,
              "at": "2026-09-10T16:24:00Z",
              "session": "w8195",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/126-work",
              "branch": "issue-126",
              "base": "5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890"
            }
          }, {
            "comment": 3180012604,
            "event": "reviewer.reported",
            "at": "2026-09-10T16:39:00Z",
            "actor": "reviewer",
            "line": "REVIEW 5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890..a856900d544832dd0b0e44abb809c24715d2fae7",
            "payload": {
              "v": 1,
              "event": "reviewer.reported",
              "stage": "review",
              "actor": "reviewer",
              "spec": 123,
              "ticket": 126,
              "at": "2026-09-10T16:39:00Z",
              "base": "5b21ca4d0c9d6e4b62c55ed6a51be45664ab8890",
              "head": "a856900d544832dd0b0e44abb809c24715d2fae7"
            }
          }, {
            "comment": 3180012605,
            "event": "worker.decided",
            "at": "2026-09-10T16:43:00Z",
            "actor": "worker",
            "line": "DECISIONS",
            "payload": {
              "v": 1,
              "event": "worker.decided",
              "stage": "work",
              "actor": "worker",
              "spec": 123,
              "ticket": 126,
              "at": "2026-09-10T16:43:00Z"
            }
          }, {
            "comment": 3180012606,
            "event": "ticket.checked",
            "at": "2026-09-10T16:59:00Z",
            "actor": "worker",
            "line": "Reverify on a856900d5448: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "verify",
              "actor": "worker",
              "spec": 123,
              "ticket": 126,
              "at": "2026-09-10T16:59:00Z",
              "run": "reverify",
              "commit": "a856900d544832dd0b0e44abb809c24715d2fae7",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "5e2829ad5a245d2edcf8bb5646113b926136045ad80a69c621383f3e33617c17"
            }
          }, {
            "comment": 3180012607,
            "event": "ticket.checked",
            "at": "2026-09-10T17:10:00Z",
            "actor": "worker",
            "line": "Repository checks on a856900d5448: 3/3 passed",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "close",
              "actor": "worker",
              "spec": 123,
              "ticket": 126,
              "at": "2026-09-10T17:10:00Z",
              "run": "repo-checks",
              "commit": "a856900d544832dd0b0e44abb809c24715d2fae7",
              "result": "met",
              "counts": {
                "passed": 3,
                "total": 3
              }
            }
          }, {
            "comment": 3180012608,
            "event": "ticket.passed",
            "at": "2026-09-10T17:15:00Z",
            "actor": "worker",
            "line": "ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.passed",
              "stage": "close",
              "actor": "worker",
              "spec": 123,
              "ticket": 126,
              "at": "2026-09-10T17:15:00Z",
              "commit": "a856900d544832dd0b0e44abb809c24715d2fae7",
              "branch": "issue-126",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "into": "main"
            }
          }, {
            "comment": 3180012609,
            "event": "ticket.landed",
            "at": "2026-09-10T17:26:00Z",
            "actor": "main",
            "line": "Landed issue-126 into main",
            "payload": {
              "v": 1,
              "event": "ticket.landed",
              "stage": "land",
              "actor": "main",
              "spec": 123,
              "ticket": 126,
              "at": "2026-09-10T17:26:00Z",
              "branch": "issue-126",
              "into": "main",
              "commit": "a856900d544832dd0b0e44abb809c24715d2fae7",
              "merge": "6fa808ea85d117531cd85ade6ba1cabce132f1f0"
            }
          }]
        }]
      }, {
        "n": 131,
        "title": "唤醒回路",
        "tickets": [{
          "n": 132,
          "title": "中继进程骨架",
          "state": "closed",
          "blocked": [],
          "blockers": [],
          "blocker_hold": "",
          "closeout": null,
          "children": [{
            "number": 148,
            "title": "status 表头少一列 runner",
            "state": "CLOSED"
          }, {
            "number": 147,
            "title": "中继日志不轮转，一夜能写满磁盘",
            "state": "CLOSED"
          }],
          "fold": {
            "issue": 132,
            "events": [{
              "comment": 3180013200,
              "event": "worker.started",
              "at": "2026-09-10T20:30:00Z",
              "actor": "main",
              "line": "worker started on herdr: session wc257, claude opus 5 (high)"
            }, {
              "comment": 3180013201,
              "event": "ticket.claimed",
              "at": "2026-09-10T20:30:00Z",
              "actor": "worker",
              "line": "Claimed #132 on issue-132 as chancheuklap"
            }, {
              "comment": 3180013202,
              "event": "child.opened",
              "at": "2026-09-10T21:05:00Z",
              "actor": "worker",
              "line": "Opened #148 (deferred): status 表头少一列 runner"
            }, {
              "comment": 3180013203,
              "event": "ticket.checked",
              "at": "2026-09-10T21:18:00Z",
              "actor": "worker",
              "line": "Own run on d1aa5a2a1955: ALL MET"
            }, {
              "comment": 3180013204,
              "event": "reviewer.started",
              "at": "2026-09-10T21:20:00Z",
              "actor": "worker",
              "line": "reviewer started on herdr: session wada4, codex gpt-5.5 (medium)"
            }, {
              "comment": 3180013205,
              "event": "reviewer.reported",
              "at": "2026-09-10T21:48:00Z",
              "actor": "reviewer",
              "line": "REVIEW 44aaf05df78c69da95e8b522dbaef7b22b5260dd..d1aa5a2a1955154cb7b1e656f89738daff02fe3e"
            }, {
              "comment": 3180013206,
              "event": "child.opened",
              "at": "2026-09-10T21:50:00Z",
              "actor": "worker",
              "line": "Opened #147 (finding): 中继日志不轮转，一夜能写满磁盘"
            }, {
              "comment": 3180013207,
              "event": "worker.decided",
              "at": "2026-09-10T21:52:00Z",
              "actor": "worker",
              "line": "DECISIONS"
            }, {
              "comment": 3180013208,
              "event": "ticket.checked",
              "at": "2026-09-10T22:10:00Z",
              "actor": "worker",
              "line": "Reverify on d1aa5a2a1955: ALL MET"
            }, {
              "comment": 3180013209,
              "event": "ticket.checked",
              "at": "2026-09-10T22:18:00Z",
              "actor": "worker",
              "line": "Repository checks on d1aa5a2a1955: 3/3 passed"
            }, {
              "comment": 3180013210,
              "event": "ticket.passed",
              "at": "2026-09-10T22:20:00Z",
              "actor": "worker",
              "line": "ALL MET"
            }, {
              "comment": 3180013211,
              "event": "child.closed",
              "at": "2026-09-10T22:36:00Z",
              "actor": "main",
              "line": "Fixed #148 on the closing pass"
            }, {
              "comment": 3180013212,
              "event": "child.closed",
              "at": "2026-09-10T22:36:00Z",
              "actor": "main",
              "line": "#147 became ticket #141 under #131"
            }, {
              "comment": 3180013213,
              "event": "ticket.landed",
              "at": "2026-09-10T22:36:00Z",
              "actor": "main",
              "line": "Landed issue-132 into wake-relay"
            }],
            "last": {
              "comment": 3180013213,
              "event": "ticket.landed",
              "at": "2026-09-10T22:36:00Z",
              "actor": "main",
              "line": "Landed issue-132 into wake-relay",
              "body": "Landed issue-132 into wake-relay\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.landed\",\"stage\":\"land\",\"actor\":\"main\",\"spec\":131,\"ticket\":132,\"at\":\"2026-09-10T22:36:00Z\",\"branch\":\"issue-132\",\"into\":\"wake-relay\",\"commit\":\"d1aa5a2a1955154cb7b1e656f89738daff02fe3e\",\"merge\":\"9ac6e028f39b4362e802cce8a1b05c3ee2c8a658\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.landed",
                "stage": "land",
                "actor": "main",
                "spec": 131,
                "ticket": 132,
                "at": "2026-09-10T22:36:00Z",
                "branch": "issue-132",
                "into": "wake-relay",
                "commit": "d1aa5a2a1955154cb7b1e656f89738daff02fe3e",
                "merge": "9ac6e028f39b4362e802cce8a1b05c3ee2c8a658"
              }
            },
            "unreadable": [],
            "claimed": false,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": true,
            "returned": false,
            "outcome": {
              "comment": 3180013210,
              "event": "ticket.passed",
              "at": "2026-09-10T22:20:00Z",
              "actor": "worker",
              "line": "ALL MET",
              "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":131,\"ticket\":132,\"at\":\"2026-09-10T22:20:00Z\",\"commit\":\"d1aa5a2a1955154cb7b1e656f89738daff02fe3e\",\"branch\":\"issue-132\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"wake-relay\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.passed",
                "stage": "close",
                "actor": "worker",
                "spec": 131,
                "ticket": 132,
                "at": "2026-09-10T22:20:00Z",
                "commit": "d1aa5a2a1955154cb7b1e656f89738daff02fe3e",
                "branch": "issue-132",
                "counts": {
                  "met": 4,
                  "unmet": 0,
                  "abandoned": 0,
                  "total": 4
                },
                "into": "wake-relay"
              }
            },
            "landed": true,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": {
              "comment": 3180013205,
              "event": "reviewer.reported",
              "at": "2026-09-10T21:48:00Z",
              "actor": "reviewer",
              "line": "REVIEW 44aaf05df78c69da95e8b522dbaef7b22b5260dd..d1aa5a2a1955154cb7b1e656f89738daff02fe3e",
              "body": "REVIEW 44aaf05df78c69da95e8b522dbaef7b22b5260dd..d1aa5a2a1955154cb7b1e656f89738daff02fe3e\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":131,\"ticket\":132,\"at\":\"2026-09-10T21:48:00Z\",\"base\":\"44aaf05df78c69da95e8b522dbaef7b22b5260dd\",\"head\":\"d1aa5a2a1955154cb7b1e656f89738daff02fe3e\"} -->\n",
              "payload": {
                "v": 1,
                "event": "reviewer.reported",
                "stage": "review",
                "actor": "reviewer",
                "spec": 131,
                "ticket": 132,
                "at": "2026-09-10T21:48:00Z",
                "base": "44aaf05df78c69da95e8b522dbaef7b22b5260dd",
                "head": "d1aa5a2a1955154cb7b1e656f89738daff02fe3e"
              }
            },
            "decided": 1,
            "results": {
              "worker": {
                "comment": 3180013210,
                "event": "ticket.passed",
                "at": "2026-09-10T22:20:00Z",
                "actor": "worker",
                "line": "ALL MET",
                "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":131,\"ticket\":132,\"at\":\"2026-09-10T22:20:00Z\",\"commit\":\"d1aa5a2a1955154cb7b1e656f89738daff02fe3e\",\"branch\":\"issue-132\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"wake-relay\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.passed",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 132,
                  "at": "2026-09-10T22:20:00Z",
                  "commit": "d1aa5a2a1955154cb7b1e656f89738daff02fe3e",
                  "branch": "issue-132",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "into": "wake-relay"
                }
              },
              "reviewer": {
                "comment": 3180013205,
                "event": "reviewer.reported",
                "at": "2026-09-10T21:48:00Z",
                "actor": "reviewer",
                "line": "REVIEW 44aaf05df78c69da95e8b522dbaef7b22b5260dd..d1aa5a2a1955154cb7b1e656f89738daff02fe3e",
                "body": "REVIEW 44aaf05df78c69da95e8b522dbaef7b22b5260dd..d1aa5a2a1955154cb7b1e656f89738daff02fe3e\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":131,\"ticket\":132,\"at\":\"2026-09-10T21:48:00Z\",\"base\":\"44aaf05df78c69da95e8b522dbaef7b22b5260dd\",\"head\":\"d1aa5a2a1955154cb7b1e656f89738daff02fe3e\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "reviewer.reported",
                  "stage": "review",
                  "actor": "reviewer",
                  "spec": 131,
                  "ticket": 132,
                  "at": "2026-09-10T21:48:00Z",
                  "base": "44aaf05df78c69da95e8b522dbaef7b22b5260dd",
                  "head": "d1aa5a2a1955154cb7b1e656f89738daff02fe3e"
                }
              }
            },
            "checks": {
              "self": {
                "comment": 3180013203,
                "event": "ticket.checked",
                "at": "2026-09-10T21:18:00Z",
                "actor": "worker",
                "line": "Own run on d1aa5a2a1955: ALL MET",
                "body": "Own run on d1aa5a2a1955: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":131,\"ticket\":132,\"at\":\"2026-09-10T21:18:00Z\",\"run\":\"self\",\"commit\":\"d1aa5a2a1955154cb7b1e656f89738daff02fe3e\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"142fa7c0e71e3efddfad0a6c1644d97ada6faa8a9fb18fcc7c5e6f7fdf6e9879\",\"slot\":1,\"port_base\":21100,\"outside_owns\":[]} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "work",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 132,
                  "at": "2026-09-10T21:18:00Z",
                  "run": "self",
                  "commit": "d1aa5a2a1955154cb7b1e656f89738daff02fe3e",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "142fa7c0e71e3efddfad0a6c1644d97ada6faa8a9fb18fcc7c5e6f7fdf6e9879",
                  "slot": 1,
                  "port_base": 21100,
                  "outside_owns": []
                }
              },
              "reverify": {
                "comment": 3180013208,
                "event": "ticket.checked",
                "at": "2026-09-10T22:10:00Z",
                "actor": "worker",
                "line": "Reverify on d1aa5a2a1955: ALL MET",
                "body": "Reverify on d1aa5a2a1955: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"verify\",\"actor\":\"worker\",\"spec\":131,\"ticket\":132,\"at\":\"2026-09-10T22:10:00Z\",\"run\":\"reverify\",\"commit\":\"d1aa5a2a1955154cb7b1e656f89738daff02fe3e\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"142fa7c0e71e3efddfad0a6c1644d97ada6faa8a9fb18fcc7c5e6f7fdf6e9879\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "verify",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 132,
                  "at": "2026-09-10T22:10:00Z",
                  "run": "reverify",
                  "commit": "d1aa5a2a1955154cb7b1e656f89738daff02fe3e",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "142fa7c0e71e3efddfad0a6c1644d97ada6faa8a9fb18fcc7c5e6f7fdf6e9879"
                }
              },
              "repo-checks": {
                "comment": 3180013209,
                "event": "ticket.checked",
                "at": "2026-09-10T22:18:00Z",
                "actor": "worker",
                "line": "Repository checks on d1aa5a2a1955: 3/3 passed",
                "body": "Repository checks on d1aa5a2a1955: 3/3 passed\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":131,\"ticket\":132,\"at\":\"2026-09-10T22:18:00Z\",\"run\":\"repo-checks\",\"commit\":\"d1aa5a2a1955154cb7b1e656f89738daff02fe3e\",\"result\":\"met\",\"counts\":{\"passed\":3,\"total\":3}} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 132,
                  "at": "2026-09-10T22:18:00Z",
                  "run": "repo-checks",
                  "commit": "d1aa5a2a1955154cb7b1e656f89738daff02fe3e",
                  "result": "met",
                  "counts": {
                    "passed": 3,
                    "total": 3
                  }
                }
              },
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {
              "147": {
                "child": 147,
                "kind": "finding",
                "title": "中继日志不轮转，一夜能写满磁盘",
                "opened": true,
                "spec": 131,
                "resolution": "became-ticket",
                "reason": null,
                "ticket": 141
              },
              "148": {
                "child": 148,
                "kind": "deferred",
                "title": "status 表头少一列 runner",
                "opened": true,
                "spec": 131,
                "resolution": "fixed",
                "reason": null,
                "ticket": null
              }
            },
            "sessions": [{
              "kind": "worker",
              "session": "wc257",
              "runner": "herdr",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/132-relay-skeleton",
              "branch": "issue-132",
              "base": "44aaf05df78c69da95e8b522dbaef7b22b5260dd",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T20:30:00Z",
              "comment": 3180013200,
              "live": false,
              "ended_by": "ticket.landed"
            }, {
              "kind": "reviewer",
              "session": "wada4",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/132-relay-skeleton",
              "branch": "issue-132",
              "base": "44aaf05df78c69da95e8b522dbaef7b22b5260dd",
              "into": null,
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T21:20:00Z",
              "comment": 3180013204,
              "live": false,
              "ended_by": "reviewer.reported"
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "wc257",
              "runner": "herdr",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/132-relay-skeleton",
              "branch": "issue-132",
              "base": "44aaf05df78c69da95e8b522dbaef7b22b5260dd",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T20:30:00Z",
              "comment": 3180013200,
              "live": false,
              "ended_by": "ticket.landed"
            },
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": true
          },
          "events": [{
            "comment": 3180013200,
            "event": "worker.started",
            "at": "2026-09-10T20:30:00Z",
            "actor": "main",
            "line": "worker started on herdr: session wc257, claude opus 5 (high)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 131,
              "ticket": 132,
              "at": "2026-09-10T20:30:00Z",
              "session": "wc257",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/132-relay-skeleton",
              "branch": "issue-132",
              "base": "44aaf05df78c69da95e8b522dbaef7b22b5260dd",
              "into": "wake-relay"
            }
          }, {
            "comment": 3180013201,
            "event": "ticket.claimed",
            "at": "2026-09-10T20:30:00Z",
            "actor": "worker",
            "line": "Claimed #132 on issue-132 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 131,
              "ticket": 132,
              "at": "2026-09-10T20:30:00Z",
              "login": "chancheuklap",
              "branch": "issue-132",
              "commit": "44aaf05df78c69da95e8b522dbaef7b22b5260dd"
            }
          }, {
            "comment": 3180013202,
            "event": "child.opened",
            "at": "2026-09-10T21:05:00Z",
            "actor": "worker",
            "line": "Opened #148 (deferred): status 表头少一列 runner",
            "payload": {
              "v": 1,
              "event": "child.opened",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 132,
              "at": "2026-09-10T21:05:00Z",
              "child": 148,
              "kind": "deferred",
              "title": "status 表头少一列 runner"
            }
          }, {
            "comment": 3180013203,
            "event": "ticket.checked",
            "at": "2026-09-10T21:18:00Z",
            "actor": "worker",
            "line": "Own run on d1aa5a2a1955: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 132,
              "at": "2026-09-10T21:18:00Z",
              "run": "self",
              "commit": "d1aa5a2a1955154cb7b1e656f89738daff02fe3e",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "142fa7c0e71e3efddfad0a6c1644d97ada6faa8a9fb18fcc7c5e6f7fdf6e9879",
              "slot": 1,
              "port_base": 21100,
              "outside_owns": []
            }
          }, {
            "comment": 3180013204,
            "event": "reviewer.started",
            "at": "2026-09-10T21:20:00Z",
            "actor": "worker",
            "line": "reviewer started on herdr: session wada4, codex gpt-5.5 (medium)",
            "payload": {
              "v": 1,
              "event": "reviewer.started",
              "stage": "review",
              "actor": "worker",
              "spec": 131,
              "ticket": 132,
              "at": "2026-09-10T21:20:00Z",
              "session": "wada4",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/132-relay-skeleton",
              "branch": "issue-132",
              "base": "44aaf05df78c69da95e8b522dbaef7b22b5260dd"
            }
          }, {
            "comment": 3180013205,
            "event": "reviewer.reported",
            "at": "2026-09-10T21:48:00Z",
            "actor": "reviewer",
            "line": "REVIEW 44aaf05df78c69da95e8b522dbaef7b22b5260dd..d1aa5a2a1955154cb7b1e656f89738daff02fe3e",
            "payload": {
              "v": 1,
              "event": "reviewer.reported",
              "stage": "review",
              "actor": "reviewer",
              "spec": 131,
              "ticket": 132,
              "at": "2026-09-10T21:48:00Z",
              "base": "44aaf05df78c69da95e8b522dbaef7b22b5260dd",
              "head": "d1aa5a2a1955154cb7b1e656f89738daff02fe3e"
            }
          }, {
            "comment": 3180013206,
            "event": "child.opened",
            "at": "2026-09-10T21:50:00Z",
            "actor": "worker",
            "line": "Opened #147 (finding): 中继日志不轮转，一夜能写满磁盘",
            "payload": {
              "v": 1,
              "event": "child.opened",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 132,
              "at": "2026-09-10T21:50:00Z",
              "child": 147,
              "kind": "finding",
              "title": "中继日志不轮转，一夜能写满磁盘"
            }
          }, {
            "comment": 3180013207,
            "event": "worker.decided",
            "at": "2026-09-10T21:52:00Z",
            "actor": "worker",
            "line": "DECISIONS",
            "payload": {
              "v": 1,
              "event": "worker.decided",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 132,
              "at": "2026-09-10T21:52:00Z"
            }
          }, {
            "comment": 3180013208,
            "event": "ticket.checked",
            "at": "2026-09-10T22:10:00Z",
            "actor": "worker",
            "line": "Reverify on d1aa5a2a1955: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "verify",
              "actor": "worker",
              "spec": 131,
              "ticket": 132,
              "at": "2026-09-10T22:10:00Z",
              "run": "reverify",
              "commit": "d1aa5a2a1955154cb7b1e656f89738daff02fe3e",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "142fa7c0e71e3efddfad0a6c1644d97ada6faa8a9fb18fcc7c5e6f7fdf6e9879"
            }
          }, {
            "comment": 3180013209,
            "event": "ticket.checked",
            "at": "2026-09-10T22:18:00Z",
            "actor": "worker",
            "line": "Repository checks on d1aa5a2a1955: 3/3 passed",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "close",
              "actor": "worker",
              "spec": 131,
              "ticket": 132,
              "at": "2026-09-10T22:18:00Z",
              "run": "repo-checks",
              "commit": "d1aa5a2a1955154cb7b1e656f89738daff02fe3e",
              "result": "met",
              "counts": {
                "passed": 3,
                "total": 3
              }
            }
          }, {
            "comment": 3180013210,
            "event": "ticket.passed",
            "at": "2026-09-10T22:20:00Z",
            "actor": "worker",
            "line": "ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.passed",
              "stage": "close",
              "actor": "worker",
              "spec": 131,
              "ticket": 132,
              "at": "2026-09-10T22:20:00Z",
              "commit": "d1aa5a2a1955154cb7b1e656f89738daff02fe3e",
              "branch": "issue-132",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "into": "wake-relay"
            }
          }, {
            "comment": 3180013211,
            "event": "child.closed",
            "at": "2026-09-10T22:36:00Z",
            "actor": "main",
            "line": "Fixed #148 on the closing pass",
            "payload": {
              "v": 1,
              "event": "child.closed",
              "stage": "close",
              "actor": "main",
              "spec": 131,
              "ticket": 132,
              "at": "2026-09-10T22:36:00Z",
              "child": 148,
              "resolution": "fixed",
              "commit": "9ac6e028f39b4362e802cce8a1b05c3ee2c8a658"
            }
          }, {
            "comment": 3180013212,
            "event": "child.closed",
            "at": "2026-09-10T22:36:00Z",
            "actor": "main",
            "line": "#147 became ticket #141 under #131",
            "payload": {
              "v": 1,
              "event": "child.closed",
              "stage": "close",
              "actor": "main",
              "spec": 131,
              "ticket": 132,
              "at": "2026-09-10T22:36:00Z",
              "child": 147,
              "resolution": "became-ticket",
              "became": 141
            }
          }, {
            "comment": 3180013213,
            "event": "ticket.landed",
            "at": "2026-09-10T22:36:00Z",
            "actor": "main",
            "line": "Landed issue-132 into wake-relay",
            "payload": {
              "v": 1,
              "event": "ticket.landed",
              "stage": "land",
              "actor": "main",
              "spec": 131,
              "ticket": 132,
              "at": "2026-09-10T22:36:00Z",
              "branch": "issue-132",
              "into": "wake-relay",
              "commit": "d1aa5a2a1955154cb7b1e656f89738daff02fe3e",
              "merge": "9ac6e028f39b4362e802cce8a1b05c3ee2c8a658"
            }
          }]
        }, {
          "n": 133,
          "title": "折叠接入中继",
          "state": "open",
          "blocked": [132],
          "blockers": [{
            "number": 132,
            "title": "中继进程骨架",
            "state": "closed",
            "spec": 131,
            "readable": true,
            "blocker_hold": ""
          }],
          "blocker_hold": "open",
          "closeout": null,
          "children": [{
            "number": 150,
            "title": "spec 没写队列为空时中继读什么",
            "state": "OPEN"
          }, {
            "number": 152,
            "title": "status.py 的表头还是旧词",
            "state": "OPEN"
          }, {
            "number": 151,
            "title": "唤醒要不要跨过已暂停的 spec",
            "state": "OPEN"
          }],
          "fold": {
            "issue": 133,
            "events": [{
              "comment": 3180013300,
              "event": "worker.started",
              "at": "2026-09-10T22:38:00Z",
              "actor": "main",
              "line": "worker started on herdr: session w94b8, grok grok 4.6 (xhigh)"
            }, {
              "comment": 3180013301,
              "event": "ticket.claimed",
              "at": "2026-09-10T22:38:00Z",
              "actor": "worker",
              "line": "Claimed #133 on issue-133 as chancheuklap"
            }, {
              "comment": 3180013302,
              "event": "child.opened",
              "at": "2026-09-10T22:51:00Z",
              "actor": "worker",
              "line": "Opened #150 (contract): spec 没写队列为空时中继读什么"
            }, {
              "comment": 3180013303,
              "event": "child.opened",
              "at": "2026-09-10T23:10:00Z",
              "actor": "worker",
              "line": "Opened #152 (deferred): status.py 的表头还是旧词"
            }, {
              "comment": 3180013304,
              "event": "child.opened",
              "at": "2026-09-10T23:31:00Z",
              "actor": "worker",
              "line": "Opened #151 (decision): 唤醒要不要跨过已暂停的 spec"
            }],
            "last": {
              "comment": 3180013304,
              "event": "child.opened",
              "at": "2026-09-10T23:31:00Z",
              "actor": "worker",
              "line": "Opened #151 (decision): 唤醒要不要跨过已暂停的 spec",
              "body": "Opened #151 (decision): 唤醒要不要跨过已暂停的 spec\n\n<!-- mmw {\"v\":1,\"event\":\"child.opened\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":131,\"ticket\":133,\"at\":\"2026-09-10T23:31:00Z\",\"child\":151,\"kind\":\"decision\",\"title\":\"唤醒要不要跨过已暂停的 spec\"} -->\n",
              "payload": {
                "v": 1,
                "event": "child.opened",
                "stage": "work",
                "actor": "worker",
                "spec": 131,
                "ticket": 133,
                "at": "2026-09-10T23:31:00Z",
                "child": 151,
                "kind": "decision",
                "title": "唤醒要不要跨过已暂停的 spec"
              }
            },
            "unreadable": [],
            "claimed": true,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": false,
            "returned": false,
            "outcome": null,
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": null,
            "decided": 0,
            "results": {
              "worker": null,
              "reviewer": null
            },
            "checks": {
              "self": null,
              "reverify": null,
              "repo-checks": null,
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {
              "150": {
                "child": 150,
                "kind": "contract",
                "title": "spec 没写队列为空时中继读什么",
                "opened": true,
                "spec": 131
              },
              "151": {
                "child": 151,
                "kind": "decision",
                "title": "唤醒要不要跨过已暂停的 spec",
                "opened": true,
                "spec": 131
              },
              "152": {
                "child": 152,
                "kind": "deferred",
                "title": "status.py 的表头还是旧词",
                "opened": true,
                "spec": 131
              }
            },
            "sessions": [{
              "kind": "worker",
              "session": "w94b8",
              "runner": "herdr",
              "host": "grok",
              "model": "grok 4.6",
              "effort": "xhigh",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/133-fold-relay",
              "branch": "issue-133",
              "base": "38f8f2261f08cadadd0c5b89c43983992cb9f4f5",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013300,
              "live": true,
              "ended_by": null
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "w94b8",
              "runner": "herdr",
              "host": "grok",
              "model": "grok 4.6",
              "effort": "xhigh",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/133-fold-relay",
              "branch": "issue-133",
              "base": "38f8f2261f08cadadd0c5b89c43983992cb9f4f5",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013300,
              "live": true,
              "ended_by": null
            },
            "live_workers": [{
              "kind": "worker",
              "session": "w94b8",
              "runner": "herdr",
              "host": "grok",
              "model": "grok 4.6",
              "effort": "xhigh",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/133-fold-relay",
              "branch": "issue-133",
              "base": "38f8f2261f08cadadd0c5b89c43983992cb9f4f5",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013300,
              "live": true,
              "ended_by": null
            }],
            "holders": [{
              "kind": "worker",
              "session": "w94b8",
              "runner": "herdr",
              "host": "grok",
              "model": "grok 4.6",
              "effort": "xhigh",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/133-fold-relay",
              "branch": "issue-133",
              "base": "38f8f2261f08cadadd0c5b89c43983992cb9f4f5",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013300,
              "live": true,
              "ended_by": null
            }],
            "held": true,
            "hold_ended": false
          },
          "events": [{
            "comment": 3180013300,
            "event": "worker.started",
            "at": "2026-09-10T22:38:00Z",
            "actor": "main",
            "line": "worker started on herdr: session w94b8, grok grok 4.6 (xhigh)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 131,
              "ticket": 133,
              "at": "2026-09-10T22:38:00Z",
              "session": "w94b8",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "grok",
              "model": "grok 4.6",
              "effort": "xhigh",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/133-fold-relay",
              "branch": "issue-133",
              "base": "38f8f2261f08cadadd0c5b89c43983992cb9f4f5",
              "into": "wake-relay"
            }
          }, {
            "comment": 3180013301,
            "event": "ticket.claimed",
            "at": "2026-09-10T22:38:00Z",
            "actor": "worker",
            "line": "Claimed #133 on issue-133 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 131,
              "ticket": 133,
              "at": "2026-09-10T22:38:00Z",
              "login": "chancheuklap",
              "branch": "issue-133",
              "commit": "38f8f2261f08cadadd0c5b89c43983992cb9f4f5"
            }
          }, {
            "comment": 3180013302,
            "event": "child.opened",
            "at": "2026-09-10T22:51:00Z",
            "actor": "worker",
            "line": "Opened #150 (contract): spec 没写队列为空时中继读什么",
            "payload": {
              "v": 1,
              "event": "child.opened",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 133,
              "at": "2026-09-10T22:51:00Z",
              "child": 150,
              "kind": "contract",
              "title": "spec 没写队列为空时中继读什么"
            }
          }, {
            "comment": 3180013303,
            "event": "child.opened",
            "at": "2026-09-10T23:10:00Z",
            "actor": "worker",
            "line": "Opened #152 (deferred): status.py 的表头还是旧词",
            "payload": {
              "v": 1,
              "event": "child.opened",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 133,
              "at": "2026-09-10T23:10:00Z",
              "child": 152,
              "kind": "deferred",
              "title": "status.py 的表头还是旧词"
            }
          }, {
            "comment": 3180013304,
            "event": "child.opened",
            "at": "2026-09-10T23:31:00Z",
            "actor": "worker",
            "line": "Opened #151 (decision): 唤醒要不要跨过已暂停的 spec",
            "payload": {
              "v": 1,
              "event": "child.opened",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 133,
              "at": "2026-09-10T23:31:00Z",
              "child": 151,
              "kind": "decision",
              "title": "唤醒要不要跨过已暂停的 spec"
            }
          }]
        }, {
          "n": 134,
          "title": "唤醒队列持久化",
          "state": "open",
          "blocked": [132],
          "blockers": [{
            "number": 132,
            "title": "中继进程骨架",
            "state": "closed",
            "spec": 131,
            "readable": true,
            "blocker_hold": ""
          }],
          "blocker_hold": "open",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 134,
            "events": [{
              "comment": 3180013400,
              "event": "worker.started",
              "at": "2026-09-10T22:38:00Z",
              "actor": "main",
              "line": "worker started on herdr: session w5d14, codex gpt-5.5 (high)"
            }, {
              "comment": 3180013401,
              "event": "ticket.claimed",
              "at": "2026-09-10T22:38:00Z",
              "actor": "worker",
              "line": "Claimed #134 on issue-134 as chancheuklap"
            }, {
              "comment": 3180013402,
              "event": "ticket.checked",
              "at": "2026-09-10T23:18:00Z",
              "actor": "worker",
              "line": "Own run on b04d79f94420: ALL MET"
            }, {
              "comment": 3180013403,
              "event": "reviewer.started",
              "at": "2026-09-10T23:22:00Z",
              "actor": "worker",
              "line": "reviewer started on herdr: session we7e3, codex gpt-5.5 (medium)"
            }],
            "last": {
              "comment": 3180013403,
              "event": "reviewer.started",
              "at": "2026-09-10T23:22:00Z",
              "actor": "worker",
              "line": "reviewer started on herdr: session we7e3, codex gpt-5.5 (medium)",
              "body": "reviewer started on herdr: session we7e3, codex gpt-5.5 (medium)\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.started\",\"stage\":\"review\",\"actor\":\"worker\",\"spec\":131,\"ticket\":134,\"at\":\"2026-09-10T23:22:00Z\",\"session\":\"we7e3\",\"runner\":\"herdr\",\"machine\":\"cheuk-mbp\",\"host\":\"codex\",\"model\":\"gpt-5.5\",\"effort\":\"medium\",\"grade\":\"reviewer\",\"worktree\":\"/Users/cheuklapchan/multi-model-workflow/.worktrees/134-work\",\"branch\":\"issue-134\",\"base\":\"a581acf6bf521aaeb0a055f2605f9ea5353517cb\"} -->\n",
              "payload": {
                "v": 1,
                "event": "reviewer.started",
                "stage": "review",
                "actor": "worker",
                "spec": 131,
                "ticket": 134,
                "at": "2026-09-10T23:22:00Z",
                "session": "we7e3",
                "runner": "herdr",
                "machine": "cheuk-mbp",
                "host": "codex",
                "model": "gpt-5.5",
                "effort": "medium",
                "grade": "reviewer",
                "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/134-work",
                "branch": "issue-134",
                "base": "a581acf6bf521aaeb0a055f2605f9ea5353517cb"
              }
            },
            "unreadable": [],
            "claimed": true,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": false,
            "returned": false,
            "outcome": null,
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": null,
            "decided": 0,
            "results": {
              "worker": null,
              "reviewer": null
            },
            "checks": {
              "self": {
                "comment": 3180013402,
                "event": "ticket.checked",
                "at": "2026-09-10T23:18:00Z",
                "actor": "worker",
                "line": "Own run on b04d79f94420: ALL MET",
                "body": "Own run on b04d79f94420: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":131,\"ticket\":134,\"at\":\"2026-09-10T23:18:00Z\",\"run\":\"self\",\"commit\":\"b04d79f9442083acf8112b8e0072b1dcf8d9e910\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"3469bc474360be437930c20396f8c426b9ef7a55a44400641e9bc5d6f706a6f1\",\"slot\":2,\"port_base\":21200,\"outside_owns\":[]} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "work",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 134,
                  "at": "2026-09-10T23:18:00Z",
                  "run": "self",
                  "commit": "b04d79f9442083acf8112b8e0072b1dcf8d9e910",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "3469bc474360be437930c20396f8c426b9ef7a55a44400641e9bc5d6f706a6f1",
                  "slot": 2,
                  "port_base": 21200,
                  "outside_owns": []
                }
              },
              "reverify": null,
              "repo-checks": null,
              "baseline": null
            },
            "waiting": null,
            "slot": 2,
            "touched": [],
            "children": {},
            "sessions": [{
              "kind": "worker",
              "session": "w5d14",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/134-work",
              "branch": "issue-134",
              "base": "a581acf6bf521aaeb0a055f2605f9ea5353517cb",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013400,
              "live": true,
              "ended_by": null
            }, {
              "kind": "reviewer",
              "session": "we7e3",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/134-work",
              "branch": "issue-134",
              "base": "a581acf6bf521aaeb0a055f2605f9ea5353517cb",
              "into": null,
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T23:22:00Z",
              "comment": 3180013403,
              "live": true,
              "ended_by": null
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "w5d14",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/134-work",
              "branch": "issue-134",
              "base": "a581acf6bf521aaeb0a055f2605f9ea5353517cb",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013400,
              "live": true,
              "ended_by": null
            },
            "live_workers": [{
              "kind": "worker",
              "session": "w5d14",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/134-work",
              "branch": "issue-134",
              "base": "a581acf6bf521aaeb0a055f2605f9ea5353517cb",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013400,
              "live": true,
              "ended_by": null
            }],
            "holders": [{
              "kind": "worker",
              "session": "w5d14",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/134-work",
              "branch": "issue-134",
              "base": "a581acf6bf521aaeb0a055f2605f9ea5353517cb",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013400,
              "live": true,
              "ended_by": null
            }, {
              "kind": "reviewer",
              "session": "we7e3",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/134-work",
              "branch": "issue-134",
              "base": "a581acf6bf521aaeb0a055f2605f9ea5353517cb",
              "into": null,
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T23:22:00Z",
              "comment": 3180013403,
              "live": true,
              "ended_by": null
            }],
            "held": true,
            "hold_ended": false
          },
          "events": [{
            "comment": 3180013400,
            "event": "worker.started",
            "at": "2026-09-10T22:38:00Z",
            "actor": "main",
            "line": "worker started on herdr: session w5d14, codex gpt-5.5 (high)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 131,
              "ticket": 134,
              "at": "2026-09-10T22:38:00Z",
              "session": "w5d14",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/134-work",
              "branch": "issue-134",
              "base": "a581acf6bf521aaeb0a055f2605f9ea5353517cb",
              "into": "wake-relay"
            }
          }, {
            "comment": 3180013401,
            "event": "ticket.claimed",
            "at": "2026-09-10T22:38:00Z",
            "actor": "worker",
            "line": "Claimed #134 on issue-134 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 131,
              "ticket": 134,
              "at": "2026-09-10T22:38:00Z",
              "login": "chancheuklap",
              "branch": "issue-134",
              "commit": "a581acf6bf521aaeb0a055f2605f9ea5353517cb"
            }
          }, {
            "comment": 3180013402,
            "event": "ticket.checked",
            "at": "2026-09-10T23:18:00Z",
            "actor": "worker",
            "line": "Own run on b04d79f94420: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 134,
              "at": "2026-09-10T23:18:00Z",
              "run": "self",
              "commit": "b04d79f9442083acf8112b8e0072b1dcf8d9e910",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "3469bc474360be437930c20396f8c426b9ef7a55a44400641e9bc5d6f706a6f1",
              "slot": 2,
              "port_base": 21200,
              "outside_owns": []
            }
          }, {
            "comment": 3180013403,
            "event": "reviewer.started",
            "at": "2026-09-10T23:22:00Z",
            "actor": "worker",
            "line": "reviewer started on herdr: session we7e3, codex gpt-5.5 (medium)",
            "payload": {
              "v": 1,
              "event": "reviewer.started",
              "stage": "review",
              "actor": "worker",
              "spec": 131,
              "ticket": 134,
              "at": "2026-09-10T23:22:00Z",
              "session": "we7e3",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/134-work",
              "branch": "issue-134",
              "base": "a581acf6bf521aaeb0a055f2605f9ea5353517cb"
            }
          }]
        }, {
          "n": 142,
          "title": "唤醒日志落盘",
          "state": "closed",
          "blocked": [132],
          "blockers": [{
            "number": 132,
            "title": "中继进程骨架",
            "state": "closed",
            "spec": 131,
            "readable": true,
            "blocker_hold": ""
          }],
          "blocker_hold": "",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 142,
            "events": [{
              "comment": 3180014200,
              "event": "worker.started",
              "at": "2026-09-10T22:38:00Z",
              "actor": "main",
              "line": "worker started on herdr: session wcd93, codex gpt 5.6 sol (medium)"
            }, {
              "comment": 3180014201,
              "event": "ticket.claimed",
              "at": "2026-09-10T22:38:00Z",
              "actor": "worker",
              "line": "Claimed #142 on issue-142 as chancheuklap"
            }, {
              "comment": 3180014202,
              "event": "ticket.checked",
              "at": "2026-09-10T22:52:00Z",
              "actor": "worker",
              "line": "Own run on d79a277ac48c: ALL MET"
            }, {
              "comment": 3180014203,
              "event": "reviewer.started",
              "at": "2026-09-10T22:53:00Z",
              "actor": "worker",
              "line": "reviewer started on herdr: session w8663, codex gpt-5.5 (medium)"
            }, {
              "comment": 3180014204,
              "event": "reviewer.reported",
              "at": "2026-09-10T22:58:00Z",
              "actor": "reviewer",
              "line": "REVIEW 483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05..d79a277ac48c9bf512b66d77bce242f58393fa5f"
            }, {
              "comment": 3180014205,
              "event": "worker.decided",
              "at": "2026-09-10T22:59:00Z",
              "actor": "worker",
              "line": "DECISIONS"
            }, {
              "comment": 3180014206,
              "event": "ticket.checked",
              "at": "2026-09-10T23:04:00Z",
              "actor": "worker",
              "line": "Reverify on d79a277ac48c: ALL MET"
            }, {
              "comment": 3180014207,
              "event": "ticket.checked",
              "at": "2026-09-10T23:07:00Z",
              "actor": "worker",
              "line": "Repository checks on d79a277ac48c: 3/3 passed"
            }, {
              "comment": 3180014208,
              "event": "ticket.passed",
              "at": "2026-09-10T23:09:00Z",
              "actor": "worker",
              "line": "ALL MET"
            }, {
              "comment": 3180014209,
              "event": "ticket.landed",
              "at": "2026-09-10T23:12:00Z",
              "actor": "main",
              "line": "Landed issue-142 into wake-relay"
            }],
            "last": {
              "comment": 3180014209,
              "event": "ticket.landed",
              "at": "2026-09-10T23:12:00Z",
              "actor": "main",
              "line": "Landed issue-142 into wake-relay",
              "body": "Landed issue-142 into wake-relay\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.landed\",\"stage\":\"land\",\"actor\":\"main\",\"spec\":131,\"ticket\":142,\"at\":\"2026-09-10T23:12:00Z\",\"branch\":\"issue-142\",\"into\":\"wake-relay\",\"commit\":\"d79a277ac48c9bf512b66d77bce242f58393fa5f\",\"merge\":\"4024d04358e510dd8dfbba5af37ed341f240ce54\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.landed",
                "stage": "land",
                "actor": "main",
                "spec": 131,
                "ticket": 142,
                "at": "2026-09-10T23:12:00Z",
                "branch": "issue-142",
                "into": "wake-relay",
                "commit": "d79a277ac48c9bf512b66d77bce242f58393fa5f",
                "merge": "4024d04358e510dd8dfbba5af37ed341f240ce54"
              }
            },
            "unreadable": [],
            "claimed": false,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": true,
            "returned": false,
            "outcome": {
              "comment": 3180014208,
              "event": "ticket.passed",
              "at": "2026-09-10T23:09:00Z",
              "actor": "worker",
              "line": "ALL MET",
              "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":131,\"ticket\":142,\"at\":\"2026-09-10T23:09:00Z\",\"commit\":\"d79a277ac48c9bf512b66d77bce242f58393fa5f\",\"branch\":\"issue-142\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"wake-relay\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.passed",
                "stage": "close",
                "actor": "worker",
                "spec": 131,
                "ticket": 142,
                "at": "2026-09-10T23:09:00Z",
                "commit": "d79a277ac48c9bf512b66d77bce242f58393fa5f",
                "branch": "issue-142",
                "counts": {
                  "met": 4,
                  "unmet": 0,
                  "abandoned": 0,
                  "total": 4
                },
                "into": "wake-relay"
              }
            },
            "landed": true,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": {
              "comment": 3180014204,
              "event": "reviewer.reported",
              "at": "2026-09-10T22:58:00Z",
              "actor": "reviewer",
              "line": "REVIEW 483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05..d79a277ac48c9bf512b66d77bce242f58393fa5f",
              "body": "REVIEW 483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05..d79a277ac48c9bf512b66d77bce242f58393fa5f\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":131,\"ticket\":142,\"at\":\"2026-09-10T22:58:00Z\",\"base\":\"483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05\",\"head\":\"d79a277ac48c9bf512b66d77bce242f58393fa5f\"} -->\n",
              "payload": {
                "v": 1,
                "event": "reviewer.reported",
                "stage": "review",
                "actor": "reviewer",
                "spec": 131,
                "ticket": 142,
                "at": "2026-09-10T22:58:00Z",
                "base": "483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05",
                "head": "d79a277ac48c9bf512b66d77bce242f58393fa5f"
              }
            },
            "decided": 1,
            "results": {
              "worker": {
                "comment": 3180014208,
                "event": "ticket.passed",
                "at": "2026-09-10T23:09:00Z",
                "actor": "worker",
                "line": "ALL MET",
                "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":131,\"ticket\":142,\"at\":\"2026-09-10T23:09:00Z\",\"commit\":\"d79a277ac48c9bf512b66d77bce242f58393fa5f\",\"branch\":\"issue-142\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"wake-relay\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.passed",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 142,
                  "at": "2026-09-10T23:09:00Z",
                  "commit": "d79a277ac48c9bf512b66d77bce242f58393fa5f",
                  "branch": "issue-142",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "into": "wake-relay"
                }
              },
              "reviewer": {
                "comment": 3180014204,
                "event": "reviewer.reported",
                "at": "2026-09-10T22:58:00Z",
                "actor": "reviewer",
                "line": "REVIEW 483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05..d79a277ac48c9bf512b66d77bce242f58393fa5f",
                "body": "REVIEW 483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05..d79a277ac48c9bf512b66d77bce242f58393fa5f\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":131,\"ticket\":142,\"at\":\"2026-09-10T22:58:00Z\",\"base\":\"483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05\",\"head\":\"d79a277ac48c9bf512b66d77bce242f58393fa5f\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "reviewer.reported",
                  "stage": "review",
                  "actor": "reviewer",
                  "spec": 131,
                  "ticket": 142,
                  "at": "2026-09-10T22:58:00Z",
                  "base": "483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05",
                  "head": "d79a277ac48c9bf512b66d77bce242f58393fa5f"
                }
              }
            },
            "checks": {
              "self": {
                "comment": 3180014202,
                "event": "ticket.checked",
                "at": "2026-09-10T22:52:00Z",
                "actor": "worker",
                "line": "Own run on d79a277ac48c: ALL MET",
                "body": "Own run on d79a277ac48c: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":131,\"ticket\":142,\"at\":\"2026-09-10T22:52:00Z\",\"run\":\"self\",\"commit\":\"d79a277ac48c9bf512b66d77bce242f58393fa5f\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"f704aa69d128634324f491953fc65e1251b8fc953fe78312ef032f28f141af94\",\"slot\":1,\"port_base\":21100,\"outside_owns\":[]} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "work",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 142,
                  "at": "2026-09-10T22:52:00Z",
                  "run": "self",
                  "commit": "d79a277ac48c9bf512b66d77bce242f58393fa5f",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "f704aa69d128634324f491953fc65e1251b8fc953fe78312ef032f28f141af94",
                  "slot": 1,
                  "port_base": 21100,
                  "outside_owns": []
                }
              },
              "reverify": {
                "comment": 3180014206,
                "event": "ticket.checked",
                "at": "2026-09-10T23:04:00Z",
                "actor": "worker",
                "line": "Reverify on d79a277ac48c: ALL MET",
                "body": "Reverify on d79a277ac48c: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"verify\",\"actor\":\"worker\",\"spec\":131,\"ticket\":142,\"at\":\"2026-09-10T23:04:00Z\",\"run\":\"reverify\",\"commit\":\"d79a277ac48c9bf512b66d77bce242f58393fa5f\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"f704aa69d128634324f491953fc65e1251b8fc953fe78312ef032f28f141af94\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "verify",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 142,
                  "at": "2026-09-10T23:04:00Z",
                  "run": "reverify",
                  "commit": "d79a277ac48c9bf512b66d77bce242f58393fa5f",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "f704aa69d128634324f491953fc65e1251b8fc953fe78312ef032f28f141af94"
                }
              },
              "repo-checks": {
                "comment": 3180014207,
                "event": "ticket.checked",
                "at": "2026-09-10T23:07:00Z",
                "actor": "worker",
                "line": "Repository checks on d79a277ac48c: 3/3 passed",
                "body": "Repository checks on d79a277ac48c: 3/3 passed\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":131,\"ticket\":142,\"at\":\"2026-09-10T23:07:00Z\",\"run\":\"repo-checks\",\"commit\":\"d79a277ac48c9bf512b66d77bce242f58393fa5f\",\"result\":\"met\",\"counts\":{\"passed\":3,\"total\":3}} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 142,
                  "at": "2026-09-10T23:07:00Z",
                  "run": "repo-checks",
                  "commit": "d79a277ac48c9bf512b66d77bce242f58393fa5f",
                  "result": "met",
                  "counts": {
                    "passed": 3,
                    "total": 3
                  }
                }
              },
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [{
              "kind": "worker",
              "session": "wcd93",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt 5.6 sol",
              "effort": "medium",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/142-work",
              "branch": "issue-142",
              "base": "483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180014200,
              "live": false,
              "ended_by": "ticket.landed"
            }, {
              "kind": "reviewer",
              "session": "w8663",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/142-work",
              "branch": "issue-142",
              "base": "483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05",
              "into": null,
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:53:00Z",
              "comment": 3180014203,
              "live": false,
              "ended_by": "reviewer.reported"
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "wcd93",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt 5.6 sol",
              "effort": "medium",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/142-work",
              "branch": "issue-142",
              "base": "483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180014200,
              "live": false,
              "ended_by": "ticket.landed"
            },
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": true
          },
          "events": [{
            "comment": 3180014200,
            "event": "worker.started",
            "at": "2026-09-10T22:38:00Z",
            "actor": "main",
            "line": "worker started on herdr: session wcd93, codex gpt 5.6 sol (medium)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 131,
              "ticket": 142,
              "at": "2026-09-10T22:38:00Z",
              "session": "wcd93",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt 5.6 sol",
              "effort": "medium",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/142-work",
              "branch": "issue-142",
              "base": "483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05",
              "into": "wake-relay"
            }
          }, {
            "comment": 3180014201,
            "event": "ticket.claimed",
            "at": "2026-09-10T22:38:00Z",
            "actor": "worker",
            "line": "Claimed #142 on issue-142 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 131,
              "ticket": 142,
              "at": "2026-09-10T22:38:00Z",
              "login": "chancheuklap",
              "branch": "issue-142",
              "commit": "483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05"
            }
          }, {
            "comment": 3180014202,
            "event": "ticket.checked",
            "at": "2026-09-10T22:52:00Z",
            "actor": "worker",
            "line": "Own run on d79a277ac48c: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 142,
              "at": "2026-09-10T22:52:00Z",
              "run": "self",
              "commit": "d79a277ac48c9bf512b66d77bce242f58393fa5f",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "f704aa69d128634324f491953fc65e1251b8fc953fe78312ef032f28f141af94",
              "slot": 1,
              "port_base": 21100,
              "outside_owns": []
            }
          }, {
            "comment": 3180014203,
            "event": "reviewer.started",
            "at": "2026-09-10T22:53:00Z",
            "actor": "worker",
            "line": "reviewer started on herdr: session w8663, codex gpt-5.5 (medium)",
            "payload": {
              "v": 1,
              "event": "reviewer.started",
              "stage": "review",
              "actor": "worker",
              "spec": 131,
              "ticket": 142,
              "at": "2026-09-10T22:53:00Z",
              "session": "w8663",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/142-work",
              "branch": "issue-142",
              "base": "483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05"
            }
          }, {
            "comment": 3180014204,
            "event": "reviewer.reported",
            "at": "2026-09-10T22:58:00Z",
            "actor": "reviewer",
            "line": "REVIEW 483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05..d79a277ac48c9bf512b66d77bce242f58393fa5f",
            "payload": {
              "v": 1,
              "event": "reviewer.reported",
              "stage": "review",
              "actor": "reviewer",
              "spec": 131,
              "ticket": 142,
              "at": "2026-09-10T22:58:00Z",
              "base": "483a2a5a9858b539dcd2a95d36c9f86e4a6e3d05",
              "head": "d79a277ac48c9bf512b66d77bce242f58393fa5f"
            }
          }, {
            "comment": 3180014205,
            "event": "worker.decided",
            "at": "2026-09-10T22:59:00Z",
            "actor": "worker",
            "line": "DECISIONS",
            "payload": {
              "v": 1,
              "event": "worker.decided",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 142,
              "at": "2026-09-10T22:59:00Z"
            }
          }, {
            "comment": 3180014206,
            "event": "ticket.checked",
            "at": "2026-09-10T23:04:00Z",
            "actor": "worker",
            "line": "Reverify on d79a277ac48c: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "verify",
              "actor": "worker",
              "spec": 131,
              "ticket": 142,
              "at": "2026-09-10T23:04:00Z",
              "run": "reverify",
              "commit": "d79a277ac48c9bf512b66d77bce242f58393fa5f",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "f704aa69d128634324f491953fc65e1251b8fc953fe78312ef032f28f141af94"
            }
          }, {
            "comment": 3180014207,
            "event": "ticket.checked",
            "at": "2026-09-10T23:07:00Z",
            "actor": "worker",
            "line": "Repository checks on d79a277ac48c: 3/3 passed",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "close",
              "actor": "worker",
              "spec": 131,
              "ticket": 142,
              "at": "2026-09-10T23:07:00Z",
              "run": "repo-checks",
              "commit": "d79a277ac48c9bf512b66d77bce242f58393fa5f",
              "result": "met",
              "counts": {
                "passed": 3,
                "total": 3
              }
            }
          }, {
            "comment": 3180014208,
            "event": "ticket.passed",
            "at": "2026-09-10T23:09:00Z",
            "actor": "worker",
            "line": "ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.passed",
              "stage": "close",
              "actor": "worker",
              "spec": 131,
              "ticket": 142,
              "at": "2026-09-10T23:09:00Z",
              "commit": "d79a277ac48c9bf512b66d77bce242f58393fa5f",
              "branch": "issue-142",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "into": "wake-relay"
            }
          }, {
            "comment": 3180014209,
            "event": "ticket.landed",
            "at": "2026-09-10T23:12:00Z",
            "actor": "main",
            "line": "Landed issue-142 into wake-relay",
            "payload": {
              "v": 1,
              "event": "ticket.landed",
              "stage": "land",
              "actor": "main",
              "spec": 131,
              "ticket": 142,
              "at": "2026-09-10T23:12:00Z",
              "branch": "issue-142",
              "into": "wake-relay",
              "commit": "d79a277ac48c9bf512b66d77bce242f58393fa5f",
              "merge": "4024d04358e510dd8dfbba5af37ed341f240ce54"
            }
          }]
        }, {
          "n": 139,
          "title": "槽位交还后叫醒",
          "state": "open",
          "blocked": [132],
          "blockers": [{
            "number": 132,
            "title": "中继进程骨架",
            "state": "closed",
            "spec": 131,
            "readable": true,
            "blocker_hold": ""
          }],
          "blocker_hold": "open",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 139,
            "events": [{
              "comment": 3180013900,
              "event": "worker.started",
              "at": "2026-09-10T22:38:00Z",
              "actor": "main",
              "line": "worker started on herdr: session w0871, claude opus 5 (high)"
            }, {
              "comment": 3180013901,
              "event": "ticket.claimed",
              "at": "2026-09-10T22:38:00Z",
              "actor": "worker",
              "line": "Claimed #139 on issue-139 as chancheuklap"
            }, {
              "comment": 3180013902,
              "event": "ticket.checked",
              "at": "2026-09-10T23:00:00Z",
              "actor": "worker",
              "line": "Own run on 51159e38b9e6: ALL MET"
            }, {
              "comment": 3180013903,
              "event": "reviewer.started",
              "at": "2026-09-10T23:02:00Z",
              "actor": "worker",
              "line": "reviewer started on herdr: session wb28e, codex gpt-5.5 (medium)"
            }, {
              "comment": 3180013904,
              "event": "reviewer.reported",
              "at": "2026-09-10T23:15:00Z",
              "actor": "reviewer",
              "line": "REVIEW 524c928981e6cb134fe1dfd637f1e19ed8543de5..51159e38b9e618fbd0ba0a5150f98362d4db163a"
            }, {
              "comment": 3180013905,
              "event": "worker.decided",
              "at": "2026-09-10T23:17:00Z",
              "actor": "worker",
              "line": "DECISIONS"
            }, {
              "comment": 3180013906,
              "event": "ticket.checked",
              "at": "2026-09-10T23:24:00Z",
              "actor": "worker",
              "line": "Reverify on 51159e38b9e6: ALL MET"
            }, {
              "comment": 3180013907,
              "event": "ticket.checked",
              "at": "2026-09-10T23:27:00Z",
              "actor": "worker",
              "line": "Repository checks on 51159e38b9e6: 3/3 passed"
            }, {
              "comment": 3180013908,
              "event": "ticket.passed",
              "at": "2026-09-10T23:28:00Z",
              "actor": "worker",
              "line": "ALL MET"
            }, {
              "comment": 3180013909,
              "event": "ticket.bounced",
              "at": "2026-09-10T23:29:00Z",
              "actor": "main",
              "line": "Did not land issue-139 into wake-relay: 2 files conflict"
            }],
            "last": {
              "comment": 3180013909,
              "event": "ticket.bounced",
              "at": "2026-09-10T23:29:00Z",
              "actor": "main",
              "line": "Did not land issue-139 into wake-relay: 2 files conflict",
              "body": "Did not land issue-139 into wake-relay: 2 files conflict\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.bounced\",\"stage\":\"land\",\"actor\":\"main\",\"spec\":131,\"ticket\":139,\"at\":\"2026-09-10T23:29:00Z\",\"reason\":\"conflict\",\"commit\":\"f3bebc0c9c6fae11fe69994b8e12fb381fdff156\",\"into\":\"wake-relay\",\"files\":[\"mmw-v2/skills/dispatch/scripts/relay.py\",\"mmw-v2/tests/relay/test_relay.py\"]} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.bounced",
                "stage": "land",
                "actor": "main",
                "spec": 131,
                "ticket": 139,
                "at": "2026-09-10T23:29:00Z",
                "reason": "conflict",
                "commit": "f3bebc0c9c6fae11fe69994b8e12fb381fdff156",
                "into": "wake-relay",
                "files": ["mmw-v2/skills/dispatch/scripts/relay.py", "mmw-v2/tests/relay/test_relay.py"]
              }
            },
            "unreadable": [],
            "claimed": false,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": false,
            "returned": false,
            "outcome": null,
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": true,
            "suspended": false,
            "review": {
              "comment": 3180013904,
              "event": "reviewer.reported",
              "at": "2026-09-10T23:15:00Z",
              "actor": "reviewer",
              "line": "REVIEW 524c928981e6cb134fe1dfd637f1e19ed8543de5..51159e38b9e618fbd0ba0a5150f98362d4db163a",
              "body": "REVIEW 524c928981e6cb134fe1dfd637f1e19ed8543de5..51159e38b9e618fbd0ba0a5150f98362d4db163a\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":131,\"ticket\":139,\"at\":\"2026-09-10T23:15:00Z\",\"base\":\"524c928981e6cb134fe1dfd637f1e19ed8543de5\",\"head\":\"51159e38b9e618fbd0ba0a5150f98362d4db163a\"} -->\n",
              "payload": {
                "v": 1,
                "event": "reviewer.reported",
                "stage": "review",
                "actor": "reviewer",
                "spec": 131,
                "ticket": 139,
                "at": "2026-09-10T23:15:00Z",
                "base": "524c928981e6cb134fe1dfd637f1e19ed8543de5",
                "head": "51159e38b9e618fbd0ba0a5150f98362d4db163a"
              }
            },
            "decided": 1,
            "results": {
              "worker": {
                "comment": 3180013908,
                "event": "ticket.passed",
                "at": "2026-09-10T23:28:00Z",
                "actor": "worker",
                "line": "ALL MET",
                "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":131,\"ticket\":139,\"at\":\"2026-09-10T23:28:00Z\",\"commit\":\"51159e38b9e618fbd0ba0a5150f98362d4db163a\",\"branch\":\"issue-139\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"wake-relay\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.passed",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 139,
                  "at": "2026-09-10T23:28:00Z",
                  "commit": "51159e38b9e618fbd0ba0a5150f98362d4db163a",
                  "branch": "issue-139",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "into": "wake-relay"
                }
              },
              "reviewer": {
                "comment": 3180013904,
                "event": "reviewer.reported",
                "at": "2026-09-10T23:15:00Z",
                "actor": "reviewer",
                "line": "REVIEW 524c928981e6cb134fe1dfd637f1e19ed8543de5..51159e38b9e618fbd0ba0a5150f98362d4db163a",
                "body": "REVIEW 524c928981e6cb134fe1dfd637f1e19ed8543de5..51159e38b9e618fbd0ba0a5150f98362d4db163a\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":131,\"ticket\":139,\"at\":\"2026-09-10T23:15:00Z\",\"base\":\"524c928981e6cb134fe1dfd637f1e19ed8543de5\",\"head\":\"51159e38b9e618fbd0ba0a5150f98362d4db163a\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "reviewer.reported",
                  "stage": "review",
                  "actor": "reviewer",
                  "spec": 131,
                  "ticket": 139,
                  "at": "2026-09-10T23:15:00Z",
                  "base": "524c928981e6cb134fe1dfd637f1e19ed8543de5",
                  "head": "51159e38b9e618fbd0ba0a5150f98362d4db163a"
                }
              }
            },
            "checks": {
              "self": {
                "comment": 3180013902,
                "event": "ticket.checked",
                "at": "2026-09-10T23:00:00Z",
                "actor": "worker",
                "line": "Own run on 51159e38b9e6: ALL MET",
                "body": "Own run on 51159e38b9e6: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":131,\"ticket\":139,\"at\":\"2026-09-10T23:00:00Z\",\"run\":\"self\",\"commit\":\"51159e38b9e618fbd0ba0a5150f98362d4db163a\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"e3b180c041d31d8446b51dc815978453ef93005876a2b4c7e101c83279ebc7a4\",\"slot\":2,\"port_base\":21200,\"outside_owns\":[]} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "work",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 139,
                  "at": "2026-09-10T23:00:00Z",
                  "run": "self",
                  "commit": "51159e38b9e618fbd0ba0a5150f98362d4db163a",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "e3b180c041d31d8446b51dc815978453ef93005876a2b4c7e101c83279ebc7a4",
                  "slot": 2,
                  "port_base": 21200,
                  "outside_owns": []
                }
              },
              "reverify": {
                "comment": 3180013906,
                "event": "ticket.checked",
                "at": "2026-09-10T23:24:00Z",
                "actor": "worker",
                "line": "Reverify on 51159e38b9e6: ALL MET",
                "body": "Reverify on 51159e38b9e6: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"verify\",\"actor\":\"worker\",\"spec\":131,\"ticket\":139,\"at\":\"2026-09-10T23:24:00Z\",\"run\":\"reverify\",\"commit\":\"51159e38b9e618fbd0ba0a5150f98362d4db163a\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"e3b180c041d31d8446b51dc815978453ef93005876a2b4c7e101c83279ebc7a4\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "verify",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 139,
                  "at": "2026-09-10T23:24:00Z",
                  "run": "reverify",
                  "commit": "51159e38b9e618fbd0ba0a5150f98362d4db163a",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "e3b180c041d31d8446b51dc815978453ef93005876a2b4c7e101c83279ebc7a4"
                }
              },
              "repo-checks": {
                "comment": 3180013907,
                "event": "ticket.checked",
                "at": "2026-09-10T23:27:00Z",
                "actor": "worker",
                "line": "Repository checks on 51159e38b9e6: 3/3 passed",
                "body": "Repository checks on 51159e38b9e6: 3/3 passed\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":131,\"ticket\":139,\"at\":\"2026-09-10T23:27:00Z\",\"run\":\"repo-checks\",\"commit\":\"51159e38b9e618fbd0ba0a5150f98362d4db163a\",\"result\":\"met\",\"counts\":{\"passed\":3,\"total\":3}} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 139,
                  "at": "2026-09-10T23:27:00Z",
                  "run": "repo-checks",
                  "commit": "51159e38b9e618fbd0ba0a5150f98362d4db163a",
                  "result": "met",
                  "counts": {
                    "passed": 3,
                    "total": 3
                  }
                }
              },
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [{
              "kind": "worker",
              "session": "w0871",
              "runner": "herdr",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/139-work",
              "branch": "issue-139",
              "base": "524c928981e6cb134fe1dfd637f1e19ed8543de5",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013900,
              "live": false,
              "ended_by": "ticket.bounced"
            }, {
              "kind": "reviewer",
              "session": "wb28e",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/139-work",
              "branch": "issue-139",
              "base": "524c928981e6cb134fe1dfd637f1e19ed8543de5",
              "into": null,
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T23:02:00Z",
              "comment": 3180013903,
              "live": false,
              "ended_by": "reviewer.reported"
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "w0871",
              "runner": "herdr",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/139-work",
              "branch": "issue-139",
              "base": "524c928981e6cb134fe1dfd637f1e19ed8543de5",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013900,
              "live": false,
              "ended_by": "ticket.bounced"
            },
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": true
          },
          "events": [{
            "comment": 3180013900,
            "event": "worker.started",
            "at": "2026-09-10T22:38:00Z",
            "actor": "main",
            "line": "worker started on herdr: session w0871, claude opus 5 (high)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 131,
              "ticket": 139,
              "at": "2026-09-10T22:38:00Z",
              "session": "w0871",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/139-work",
              "branch": "issue-139",
              "base": "524c928981e6cb134fe1dfd637f1e19ed8543de5",
              "into": "wake-relay"
            }
          }, {
            "comment": 3180013901,
            "event": "ticket.claimed",
            "at": "2026-09-10T22:38:00Z",
            "actor": "worker",
            "line": "Claimed #139 on issue-139 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 131,
              "ticket": 139,
              "at": "2026-09-10T22:38:00Z",
              "login": "chancheuklap",
              "branch": "issue-139",
              "commit": "524c928981e6cb134fe1dfd637f1e19ed8543de5"
            }
          }, {
            "comment": 3180013902,
            "event": "ticket.checked",
            "at": "2026-09-10T23:00:00Z",
            "actor": "worker",
            "line": "Own run on 51159e38b9e6: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 139,
              "at": "2026-09-10T23:00:00Z",
              "run": "self",
              "commit": "51159e38b9e618fbd0ba0a5150f98362d4db163a",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "e3b180c041d31d8446b51dc815978453ef93005876a2b4c7e101c83279ebc7a4",
              "slot": 2,
              "port_base": 21200,
              "outside_owns": []
            }
          }, {
            "comment": 3180013903,
            "event": "reviewer.started",
            "at": "2026-09-10T23:02:00Z",
            "actor": "worker",
            "line": "reviewer started on herdr: session wb28e, codex gpt-5.5 (medium)",
            "payload": {
              "v": 1,
              "event": "reviewer.started",
              "stage": "review",
              "actor": "worker",
              "spec": 131,
              "ticket": 139,
              "at": "2026-09-10T23:02:00Z",
              "session": "wb28e",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/139-work",
              "branch": "issue-139",
              "base": "524c928981e6cb134fe1dfd637f1e19ed8543de5"
            }
          }, {
            "comment": 3180013904,
            "event": "reviewer.reported",
            "at": "2026-09-10T23:15:00Z",
            "actor": "reviewer",
            "line": "REVIEW 524c928981e6cb134fe1dfd637f1e19ed8543de5..51159e38b9e618fbd0ba0a5150f98362d4db163a",
            "payload": {
              "v": 1,
              "event": "reviewer.reported",
              "stage": "review",
              "actor": "reviewer",
              "spec": 131,
              "ticket": 139,
              "at": "2026-09-10T23:15:00Z",
              "base": "524c928981e6cb134fe1dfd637f1e19ed8543de5",
              "head": "51159e38b9e618fbd0ba0a5150f98362d4db163a"
            }
          }, {
            "comment": 3180013905,
            "event": "worker.decided",
            "at": "2026-09-10T23:17:00Z",
            "actor": "worker",
            "line": "DECISIONS",
            "payload": {
              "v": 1,
              "event": "worker.decided",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 139,
              "at": "2026-09-10T23:17:00Z"
            }
          }, {
            "comment": 3180013906,
            "event": "ticket.checked",
            "at": "2026-09-10T23:24:00Z",
            "actor": "worker",
            "line": "Reverify on 51159e38b9e6: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "verify",
              "actor": "worker",
              "spec": 131,
              "ticket": 139,
              "at": "2026-09-10T23:24:00Z",
              "run": "reverify",
              "commit": "51159e38b9e618fbd0ba0a5150f98362d4db163a",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "e3b180c041d31d8446b51dc815978453ef93005876a2b4c7e101c83279ebc7a4"
            }
          }, {
            "comment": 3180013907,
            "event": "ticket.checked",
            "at": "2026-09-10T23:27:00Z",
            "actor": "worker",
            "line": "Repository checks on 51159e38b9e6: 3/3 passed",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "close",
              "actor": "worker",
              "spec": 131,
              "ticket": 139,
              "at": "2026-09-10T23:27:00Z",
              "run": "repo-checks",
              "commit": "51159e38b9e618fbd0ba0a5150f98362d4db163a",
              "result": "met",
              "counts": {
                "passed": 3,
                "total": 3
              }
            }
          }, {
            "comment": 3180013908,
            "event": "ticket.passed",
            "at": "2026-09-10T23:28:00Z",
            "actor": "worker",
            "line": "ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.passed",
              "stage": "close",
              "actor": "worker",
              "spec": 131,
              "ticket": 139,
              "at": "2026-09-10T23:28:00Z",
              "commit": "51159e38b9e618fbd0ba0a5150f98362d4db163a",
              "branch": "issue-139",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "into": "wake-relay"
            }
          }, {
            "comment": 3180013909,
            "event": "ticket.bounced",
            "at": "2026-09-10T23:29:00Z",
            "actor": "main",
            "line": "Did not land issue-139 into wake-relay: 2 files conflict",
            "payload": {
              "v": 1,
              "event": "ticket.bounced",
              "stage": "land",
              "actor": "main",
              "spec": 131,
              "ticket": 139,
              "at": "2026-09-10T23:29:00Z",
              "reason": "conflict",
              "commit": "f3bebc0c9c6fae11fe69994b8e12fb381fdff156",
              "into": "wake-relay",
              "files": ["mmw-v2/skills/dispatch/scripts/relay.py", "mmw-v2/tests/relay/test_relay.py"]
            }
          }]
        }, {
          "n": 138,
          "title": "离线时唤醒去向",
          "state": "open",
          "blocked": [132],
          "blockers": [{
            "number": 132,
            "title": "中继进程骨架",
            "state": "closed",
            "spec": 131,
            "readable": true,
            "blocker_hold": ""
          }],
          "blocker_hold": "open",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 138,
            "events": [{
              "comment": 3180013800,
              "event": "worker.started",
              "at": "2026-09-10T22:38:00Z",
              "actor": "main",
              "line": "worker started on herdr: session we7c5, grok grok 4.6 (high)"
            }, {
              "comment": 3180013801,
              "event": "ticket.claimed",
              "at": "2026-09-10T22:38:00Z",
              "actor": "worker",
              "line": "Claimed #138 on issue-138 as chancheuklap"
            }, {
              "comment": 3180013802,
              "event": "ticket.checked",
              "at": "2026-09-10T22:58:00Z",
              "actor": "worker",
              "line": "Own run on 47e282b29080: HANDOFF REQUIRED: AC3 stuck"
            }, {
              "comment": 3180013803,
              "event": "reviewer.started",
              "at": "2026-09-10T23:00:00Z",
              "actor": "worker",
              "line": "reviewer started on herdr: session w709a, codex gpt-5.5 (medium)"
            }, {
              "comment": 3180013804,
              "event": "reviewer.reported",
              "at": "2026-09-10T23:14:00Z",
              "actor": "reviewer",
              "line": "REVIEW 3d82cd10637f3d66d0a93d3d072bb2d245fd4089..47e282b2908040aafb0c4f5601876073ea90929a"
            }, {
              "comment": 3180013805,
              "event": "worker.decided",
              "at": "2026-09-10T23:16:00Z",
              "actor": "worker",
              "line": "DECISIONS"
            }, {
              "comment": 3180013806,
              "event": "ticket.checked",
              "at": "2026-09-10T23:22:00Z",
              "actor": "worker",
              "line": "Reverify on 47e282b29080: HANDOFF REQUIRED: AC3 stuck"
            }, {
              "comment": 3180013807,
              "event": "ticket.returned",
              "at": "2026-09-10T23:26:00Z",
              "actor": "worker",
              "line": "HANDOFF REQUIRED: AC3 stuck"
            }],
            "last": {
              "comment": 3180013807,
              "event": "ticket.returned",
              "at": "2026-09-10T23:26:00Z",
              "actor": "worker",
              "line": "HANDOFF REQUIRED: AC3 stuck",
              "body": "HANDOFF REQUIRED: AC3 stuck\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.returned\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":131,\"ticket\":138,\"at\":\"2026-09-10T23:26:00Z\",\"commit\":\"47e282b2908040aafb0c4f5601876073ea90929a\",\"branch\":\"issue-138\",\"counts\":{\"met\":3,\"unmet\":0,\"abandoned\":1,\"total\":4},\"abandoned\":[{\"ac\":\"AC3\",\"kind\":\"stuck\",\"reason\":\"离线投递要一个真的 main 会话来收，夜里起不来\"}]} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.returned",
                "stage": "close",
                "actor": "worker",
                "spec": 131,
                "ticket": 138,
                "at": "2026-09-10T23:26:00Z",
                "commit": "47e282b2908040aafb0c4f5601876073ea90929a",
                "branch": "issue-138",
                "counts": {
                  "met": 3,
                  "unmet": 0,
                  "abandoned": 1,
                  "total": 4
                },
                "abandoned": [{
                  "ac": "AC3",
                  "kind": "stuck",
                  "reason": "离线投递要一个真的 main 会话来收，夜里起不来"
                }]
              }
            },
            "unreadable": [],
            "claimed": false,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": false,
            "returned": true,
            "outcome": {
              "comment": 3180013807,
              "event": "ticket.returned",
              "at": "2026-09-10T23:26:00Z",
              "actor": "worker",
              "line": "HANDOFF REQUIRED: AC3 stuck",
              "body": "HANDOFF REQUIRED: AC3 stuck\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.returned\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":131,\"ticket\":138,\"at\":\"2026-09-10T23:26:00Z\",\"commit\":\"47e282b2908040aafb0c4f5601876073ea90929a\",\"branch\":\"issue-138\",\"counts\":{\"met\":3,\"unmet\":0,\"abandoned\":1,\"total\":4},\"abandoned\":[{\"ac\":\"AC3\",\"kind\":\"stuck\",\"reason\":\"离线投递要一个真的 main 会话来收，夜里起不来\"}]} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.returned",
                "stage": "close",
                "actor": "worker",
                "spec": 131,
                "ticket": 138,
                "at": "2026-09-10T23:26:00Z",
                "commit": "47e282b2908040aafb0c4f5601876073ea90929a",
                "branch": "issue-138",
                "counts": {
                  "met": 3,
                  "unmet": 0,
                  "abandoned": 1,
                  "total": 4
                },
                "abandoned": [{
                  "ac": "AC3",
                  "kind": "stuck",
                  "reason": "离线投递要一个真的 main 会话来收，夜里起不来"
                }]
              }
            },
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": {
              "comment": 3180013804,
              "event": "reviewer.reported",
              "at": "2026-09-10T23:14:00Z",
              "actor": "reviewer",
              "line": "REVIEW 3d82cd10637f3d66d0a93d3d072bb2d245fd4089..47e282b2908040aafb0c4f5601876073ea90929a",
              "body": "REVIEW 3d82cd10637f3d66d0a93d3d072bb2d245fd4089..47e282b2908040aafb0c4f5601876073ea90929a\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":131,\"ticket\":138,\"at\":\"2026-09-10T23:14:00Z\",\"base\":\"3d82cd10637f3d66d0a93d3d072bb2d245fd4089\",\"head\":\"47e282b2908040aafb0c4f5601876073ea90929a\"} -->\n",
              "payload": {
                "v": 1,
                "event": "reviewer.reported",
                "stage": "review",
                "actor": "reviewer",
                "spec": 131,
                "ticket": 138,
                "at": "2026-09-10T23:14:00Z",
                "base": "3d82cd10637f3d66d0a93d3d072bb2d245fd4089",
                "head": "47e282b2908040aafb0c4f5601876073ea90929a"
              }
            },
            "decided": 1,
            "results": {
              "worker": {
                "comment": 3180013807,
                "event": "ticket.returned",
                "at": "2026-09-10T23:26:00Z",
                "actor": "worker",
                "line": "HANDOFF REQUIRED: AC3 stuck",
                "body": "HANDOFF REQUIRED: AC3 stuck\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.returned\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":131,\"ticket\":138,\"at\":\"2026-09-10T23:26:00Z\",\"commit\":\"47e282b2908040aafb0c4f5601876073ea90929a\",\"branch\":\"issue-138\",\"counts\":{\"met\":3,\"unmet\":0,\"abandoned\":1,\"total\":4},\"abandoned\":[{\"ac\":\"AC3\",\"kind\":\"stuck\",\"reason\":\"离线投递要一个真的 main 会话来收，夜里起不来\"}]} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.returned",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 138,
                  "at": "2026-09-10T23:26:00Z",
                  "commit": "47e282b2908040aafb0c4f5601876073ea90929a",
                  "branch": "issue-138",
                  "counts": {
                    "met": 3,
                    "unmet": 0,
                    "abandoned": 1,
                    "total": 4
                  },
                  "abandoned": [{
                    "ac": "AC3",
                    "kind": "stuck",
                    "reason": "离线投递要一个真的 main 会话来收，夜里起不来"
                  }]
                }
              },
              "reviewer": {
                "comment": 3180013804,
                "event": "reviewer.reported",
                "at": "2026-09-10T23:14:00Z",
                "actor": "reviewer",
                "line": "REVIEW 3d82cd10637f3d66d0a93d3d072bb2d245fd4089..47e282b2908040aafb0c4f5601876073ea90929a",
                "body": "REVIEW 3d82cd10637f3d66d0a93d3d072bb2d245fd4089..47e282b2908040aafb0c4f5601876073ea90929a\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":131,\"ticket\":138,\"at\":\"2026-09-10T23:14:00Z\",\"base\":\"3d82cd10637f3d66d0a93d3d072bb2d245fd4089\",\"head\":\"47e282b2908040aafb0c4f5601876073ea90929a\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "reviewer.reported",
                  "stage": "review",
                  "actor": "reviewer",
                  "spec": 131,
                  "ticket": 138,
                  "at": "2026-09-10T23:14:00Z",
                  "base": "3d82cd10637f3d66d0a93d3d072bb2d245fd4089",
                  "head": "47e282b2908040aafb0c4f5601876073ea90929a"
                }
              }
            },
            "checks": {
              "self": {
                "comment": 3180013802,
                "event": "ticket.checked",
                "at": "2026-09-10T22:58:00Z",
                "actor": "worker",
                "line": "Own run on 47e282b29080: HANDOFF REQUIRED: AC3 stuck",
                "body": "Own run on 47e282b29080: HANDOFF REQUIRED: AC3 stuck\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":131,\"ticket\":138,\"at\":\"2026-09-10T22:58:00Z\",\"run\":\"self\",\"commit\":\"47e282b2908040aafb0c4f5601876073ea90929a\",\"result\":\"handoff\",\"counts\":{\"met\":3,\"unmet\":0,\"abandoned\":1,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":false,\"evidence\":\"pending\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[\"AC3\"],\"abandons\":[{\"ac\":\"AC3\",\"kind\":\"stuck\",\"reason\":\"离线投递要一个真的 main 会话来收，夜里起不来\"}],\"shape\":\"e25e12b6407de49b856f1a1a81348cc6b241654e16e044f346f70baa35eb7ca4\",\"slot\":1,\"port_base\":21100,\"outside_owns\":[]} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "work",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 138,
                  "at": "2026-09-10T22:58:00Z",
                  "run": "self",
                  "commit": "47e282b2908040aafb0c4f5601876073ea90929a",
                  "result": "handoff",
                  "counts": {
                    "met": 3,
                    "unmet": 0,
                    "abandoned": 1,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": false,
                    "evidence": "pending"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": ["AC3"],
                  "abandons": [{
                    "ac": "AC3",
                    "kind": "stuck",
                    "reason": "离线投递要一个真的 main 会话来收，夜里起不来"
                  }],
                  "shape": "e25e12b6407de49b856f1a1a81348cc6b241654e16e044f346f70baa35eb7ca4",
                  "slot": 1,
                  "port_base": 21100,
                  "outside_owns": []
                }
              },
              "reverify": {
                "comment": 3180013806,
                "event": "ticket.checked",
                "at": "2026-09-10T23:22:00Z",
                "actor": "worker",
                "line": "Reverify on 47e282b29080: HANDOFF REQUIRED: AC3 stuck",
                "body": "Reverify on 47e282b29080: HANDOFF REQUIRED: AC3 stuck\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"verify\",\"actor\":\"worker\",\"spec\":131,\"ticket\":138,\"at\":\"2026-09-10T23:22:00Z\",\"run\":\"reverify\",\"commit\":\"47e282b2908040aafb0c4f5601876073ea90929a\",\"result\":\"handoff\",\"counts\":{\"met\":3,\"unmet\":0,\"abandoned\":1,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":false,\"evidence\":\"pending\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[\"AC3\"],\"abandons\":[{\"ac\":\"AC3\",\"kind\":\"stuck\",\"reason\":\"离线投递要一个真的 main 会话来收，夜里起不来\"}],\"shape\":\"e25e12b6407de49b856f1a1a81348cc6b241654e16e044f346f70baa35eb7ca4\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "verify",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 138,
                  "at": "2026-09-10T23:22:00Z",
                  "run": "reverify",
                  "commit": "47e282b2908040aafb0c4f5601876073ea90929a",
                  "result": "handoff",
                  "counts": {
                    "met": 3,
                    "unmet": 0,
                    "abandoned": 1,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": false,
                    "evidence": "pending"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": ["AC3"],
                  "abandons": [{
                    "ac": "AC3",
                    "kind": "stuck",
                    "reason": "离线投递要一个真的 main 会话来收，夜里起不来"
                  }],
                  "shape": "e25e12b6407de49b856f1a1a81348cc6b241654e16e044f346f70baa35eb7ca4"
                }
              },
              "repo-checks": null,
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [{
              "kind": "worker",
              "session": "we7c5",
              "runner": "herdr",
              "host": "grok",
              "model": "grok 4.6",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/138-work",
              "branch": "issue-138",
              "base": "3d82cd10637f3d66d0a93d3d072bb2d245fd4089",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013800,
              "live": false,
              "ended_by": "ticket.returned"
            }, {
              "kind": "reviewer",
              "session": "w709a",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/138-work",
              "branch": "issue-138",
              "base": "3d82cd10637f3d66d0a93d3d072bb2d245fd4089",
              "into": null,
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T23:00:00Z",
              "comment": 3180013803,
              "live": false,
              "ended_by": "reviewer.reported"
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "we7c5",
              "runner": "herdr",
              "host": "grok",
              "model": "grok 4.6",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/138-work",
              "branch": "issue-138",
              "base": "3d82cd10637f3d66d0a93d3d072bb2d245fd4089",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013800,
              "live": false,
              "ended_by": "ticket.returned"
            },
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": true
          },
          "events": [{
            "comment": 3180013800,
            "event": "worker.started",
            "at": "2026-09-10T22:38:00Z",
            "actor": "main",
            "line": "worker started on herdr: session we7c5, grok grok 4.6 (high)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 131,
              "ticket": 138,
              "at": "2026-09-10T22:38:00Z",
              "session": "we7c5",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "grok",
              "model": "grok 4.6",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/138-work",
              "branch": "issue-138",
              "base": "3d82cd10637f3d66d0a93d3d072bb2d245fd4089",
              "into": "wake-relay"
            }
          }, {
            "comment": 3180013801,
            "event": "ticket.claimed",
            "at": "2026-09-10T22:38:00Z",
            "actor": "worker",
            "line": "Claimed #138 on issue-138 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 131,
              "ticket": 138,
              "at": "2026-09-10T22:38:00Z",
              "login": "chancheuklap",
              "branch": "issue-138",
              "commit": "3d82cd10637f3d66d0a93d3d072bb2d245fd4089"
            }
          }, {
            "comment": 3180013802,
            "event": "ticket.checked",
            "at": "2026-09-10T22:58:00Z",
            "actor": "worker",
            "line": "Own run on 47e282b29080: HANDOFF REQUIRED: AC3 stuck",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 138,
              "at": "2026-09-10T22:58:00Z",
              "run": "self",
              "commit": "47e282b2908040aafb0c4f5601876073ea90929a",
              "result": "handoff",
              "counts": {
                "met": 3,
                "unmet": 0,
                "abandoned": 1,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": false,
                "evidence": "pending"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": ["AC3"],
              "abandons": [{
                "ac": "AC3",
                "kind": "stuck",
                "reason": "离线投递要一个真的 main 会话来收，夜里起不来"
              }],
              "shape": "e25e12b6407de49b856f1a1a81348cc6b241654e16e044f346f70baa35eb7ca4",
              "slot": 1,
              "port_base": 21100,
              "outside_owns": []
            }
          }, {
            "comment": 3180013803,
            "event": "reviewer.started",
            "at": "2026-09-10T23:00:00Z",
            "actor": "worker",
            "line": "reviewer started on herdr: session w709a, codex gpt-5.5 (medium)",
            "payload": {
              "v": 1,
              "event": "reviewer.started",
              "stage": "review",
              "actor": "worker",
              "spec": 131,
              "ticket": 138,
              "at": "2026-09-10T23:00:00Z",
              "session": "w709a",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/138-work",
              "branch": "issue-138",
              "base": "3d82cd10637f3d66d0a93d3d072bb2d245fd4089"
            }
          }, {
            "comment": 3180013804,
            "event": "reviewer.reported",
            "at": "2026-09-10T23:14:00Z",
            "actor": "reviewer",
            "line": "REVIEW 3d82cd10637f3d66d0a93d3d072bb2d245fd4089..47e282b2908040aafb0c4f5601876073ea90929a",
            "payload": {
              "v": 1,
              "event": "reviewer.reported",
              "stage": "review",
              "actor": "reviewer",
              "spec": 131,
              "ticket": 138,
              "at": "2026-09-10T23:14:00Z",
              "base": "3d82cd10637f3d66d0a93d3d072bb2d245fd4089",
              "head": "47e282b2908040aafb0c4f5601876073ea90929a"
            }
          }, {
            "comment": 3180013805,
            "event": "worker.decided",
            "at": "2026-09-10T23:16:00Z",
            "actor": "worker",
            "line": "DECISIONS",
            "payload": {
              "v": 1,
              "event": "worker.decided",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 138,
              "at": "2026-09-10T23:16:00Z"
            }
          }, {
            "comment": 3180013806,
            "event": "ticket.checked",
            "at": "2026-09-10T23:22:00Z",
            "actor": "worker",
            "line": "Reverify on 47e282b29080: HANDOFF REQUIRED: AC3 stuck",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "verify",
              "actor": "worker",
              "spec": 131,
              "ticket": 138,
              "at": "2026-09-10T23:22:00Z",
              "run": "reverify",
              "commit": "47e282b2908040aafb0c4f5601876073ea90929a",
              "result": "handoff",
              "counts": {
                "met": 3,
                "unmet": 0,
                "abandoned": 1,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": false,
                "evidence": "pending"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": ["AC3"],
              "abandons": [{
                "ac": "AC3",
                "kind": "stuck",
                "reason": "离线投递要一个真的 main 会话来收，夜里起不来"
              }],
              "shape": "e25e12b6407de49b856f1a1a81348cc6b241654e16e044f346f70baa35eb7ca4"
            }
          }, {
            "comment": 3180013807,
            "event": "ticket.returned",
            "at": "2026-09-10T23:26:00Z",
            "actor": "worker",
            "line": "HANDOFF REQUIRED: AC3 stuck",
            "payload": {
              "v": 1,
              "event": "ticket.returned",
              "stage": "close",
              "actor": "worker",
              "spec": 131,
              "ticket": 138,
              "at": "2026-09-10T23:26:00Z",
              "commit": "47e282b2908040aafb0c4f5601876073ea90929a",
              "branch": "issue-138",
              "counts": {
                "met": 3,
                "unmet": 0,
                "abandoned": 1,
                "total": 4
              },
              "abandoned": [{
                "ac": "AC3",
                "kind": "stuck",
                "reason": "离线投递要一个真的 main 会话来收，夜里起不来"
              }]
            }
          }]
        }, {
          "n": 141,
          "title": "中继日志轮转",
          "state": "open",
          "blocked": [132],
          "blockers": [{
            "number": 132,
            "title": "中继进程骨架",
            "state": "closed",
            "spec": 131,
            "readable": true,
            "blocker_hold": ""
          }],
          "blocker_hold": "open",
          "closeout": {
            "from": 132,
            "child": 147
          },
          "children": [],
          "fold": {
            "issue": 141,
            "events": [{
              "comment": 3180014100,
              "event": "worker.started",
              "at": "2026-09-10T22:38:00Z",
              "actor": "main",
              "line": "worker started on orca: session term_5666, cursor composer 2.5 (—)"
            }, {
              "comment": 3180014101,
              "event": "ticket.claimed",
              "at": "2026-09-10T22:38:00Z",
              "actor": "worker",
              "line": "Claimed #141 on issue-141 as chancheuklap"
            }, {
              "comment": 3180014102,
              "event": "ticket.checked",
              "at": "2026-09-10T23:02:00Z",
              "actor": "worker",
              "line": "Own run on d1fc16755a5e: ALL MET"
            }, {
              "comment": 3180014103,
              "event": "reviewer.started",
              "at": "2026-09-10T23:04:00Z",
              "actor": "worker",
              "line": "reviewer started on herdr: session w4a5a, codex gpt-5.5 (medium)"
            }, {
              "comment": 3180014104,
              "event": "reviewer.reported",
              "at": "2026-09-10T23:24:00Z",
              "actor": "reviewer",
              "line": "REVIEW ae0a1c6e5d86efc074539319b3f5dd21c2b71880..d1fc16755a5e6b6a258774dbcb2b75aa9bd77183"
            }, {
              "comment": 3180014105,
              "event": "worker.decided",
              "at": "2026-09-10T23:28:00Z",
              "actor": "worker",
              "line": "DECISIONS"
            }],
            "last": {
              "comment": 3180014105,
              "event": "worker.decided",
              "at": "2026-09-10T23:28:00Z",
              "actor": "worker",
              "line": "DECISIONS",
              "body": "DECISIONS\n\n<!-- mmw {\"v\":1,\"event\":\"worker.decided\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":131,\"ticket\":141,\"at\":\"2026-09-10T23:28:00Z\"} -->\n",
              "payload": {
                "v": 1,
                "event": "worker.decided",
                "stage": "work",
                "actor": "worker",
                "spec": 131,
                "ticket": 141,
                "at": "2026-09-10T23:28:00Z"
              }
            },
            "unreadable": [],
            "claimed": true,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": false,
            "returned": false,
            "outcome": null,
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": {
              "comment": 3180014104,
              "event": "reviewer.reported",
              "at": "2026-09-10T23:24:00Z",
              "actor": "reviewer",
              "line": "REVIEW ae0a1c6e5d86efc074539319b3f5dd21c2b71880..d1fc16755a5e6b6a258774dbcb2b75aa9bd77183",
              "body": "REVIEW ae0a1c6e5d86efc074539319b3f5dd21c2b71880..d1fc16755a5e6b6a258774dbcb2b75aa9bd77183\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":131,\"ticket\":141,\"at\":\"2026-09-10T23:24:00Z\",\"base\":\"ae0a1c6e5d86efc074539319b3f5dd21c2b71880\",\"head\":\"d1fc16755a5e6b6a258774dbcb2b75aa9bd77183\"} -->\n",
              "payload": {
                "v": 1,
                "event": "reviewer.reported",
                "stage": "review",
                "actor": "reviewer",
                "spec": 131,
                "ticket": 141,
                "at": "2026-09-10T23:24:00Z",
                "base": "ae0a1c6e5d86efc074539319b3f5dd21c2b71880",
                "head": "d1fc16755a5e6b6a258774dbcb2b75aa9bd77183"
              }
            },
            "decided": 1,
            "results": {
              "worker": null,
              "reviewer": {
                "comment": 3180014104,
                "event": "reviewer.reported",
                "at": "2026-09-10T23:24:00Z",
                "actor": "reviewer",
                "line": "REVIEW ae0a1c6e5d86efc074539319b3f5dd21c2b71880..d1fc16755a5e6b6a258774dbcb2b75aa9bd77183",
                "body": "REVIEW ae0a1c6e5d86efc074539319b3f5dd21c2b71880..d1fc16755a5e6b6a258774dbcb2b75aa9bd77183\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":131,\"ticket\":141,\"at\":\"2026-09-10T23:24:00Z\",\"base\":\"ae0a1c6e5d86efc074539319b3f5dd21c2b71880\",\"head\":\"d1fc16755a5e6b6a258774dbcb2b75aa9bd77183\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "reviewer.reported",
                  "stage": "review",
                  "actor": "reviewer",
                  "spec": 131,
                  "ticket": 141,
                  "at": "2026-09-10T23:24:00Z",
                  "base": "ae0a1c6e5d86efc074539319b3f5dd21c2b71880",
                  "head": "d1fc16755a5e6b6a258774dbcb2b75aa9bd77183"
                }
              }
            },
            "checks": {
              "self": {
                "comment": 3180014102,
                "event": "ticket.checked",
                "at": "2026-09-10T23:02:00Z",
                "actor": "worker",
                "line": "Own run on d1fc16755a5e: ALL MET",
                "body": "Own run on d1fc16755a5e: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":131,\"ticket\":141,\"at\":\"2026-09-10T23:02:00Z\",\"run\":\"self\",\"commit\":\"d1fc16755a5e6b6a258774dbcb2b75aa9bd77183\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"449fd224bd8aa28f9e3b4bb0ec363d91f3e07a47dc2e2a13663b09494a801487\",\"slot\":1,\"port_base\":21100,\"outside_owns\":[]} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "work",
                  "actor": "worker",
                  "spec": 131,
                  "ticket": 141,
                  "at": "2026-09-10T23:02:00Z",
                  "run": "self",
                  "commit": "d1fc16755a5e6b6a258774dbcb2b75aa9bd77183",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "449fd224bd8aa28f9e3b4bb0ec363d91f3e07a47dc2e2a13663b09494a801487",
                  "slot": 1,
                  "port_base": 21100,
                  "outside_owns": []
                }
              },
              "reverify": null,
              "repo-checks": null,
              "baseline": null
            },
            "waiting": null,
            "slot": 1,
            "touched": [],
            "children": {},
            "sessions": [{
              "kind": "worker",
              "session": "term_5666",
              "runner": "orca",
              "host": "cursor",
              "model": "composer 2.5",
              "effort": "—",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/141-work",
              "branch": "issue-141",
              "base": "ae0a1c6e5d86efc074539319b3f5dd21c2b71880",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180014100,
              "live": true,
              "ended_by": null
            }, {
              "kind": "reviewer",
              "session": "w4a5a",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/141-work",
              "branch": "issue-141",
              "base": "ae0a1c6e5d86efc074539319b3f5dd21c2b71880",
              "into": null,
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T23:04:00Z",
              "comment": 3180014103,
              "live": false,
              "ended_by": "reviewer.reported"
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "term_5666",
              "runner": "orca",
              "host": "cursor",
              "model": "composer 2.5",
              "effort": "—",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/141-work",
              "branch": "issue-141",
              "base": "ae0a1c6e5d86efc074539319b3f5dd21c2b71880",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180014100,
              "live": true,
              "ended_by": null
            },
            "live_workers": [{
              "kind": "worker",
              "session": "term_5666",
              "runner": "orca",
              "host": "cursor",
              "model": "composer 2.5",
              "effort": "—",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/141-work",
              "branch": "issue-141",
              "base": "ae0a1c6e5d86efc074539319b3f5dd21c2b71880",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180014100,
              "live": true,
              "ended_by": null
            }],
            "holders": [{
              "kind": "worker",
              "session": "term_5666",
              "runner": "orca",
              "host": "cursor",
              "model": "composer 2.5",
              "effort": "—",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/141-work",
              "branch": "issue-141",
              "base": "ae0a1c6e5d86efc074539319b3f5dd21c2b71880",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180014100,
              "live": true,
              "ended_by": null
            }],
            "held": true,
            "hold_ended": false
          },
          "events": [{
            "comment": 3180014100,
            "event": "worker.started",
            "at": "2026-09-10T22:38:00Z",
            "actor": "main",
            "line": "worker started on orca: session term_5666, cursor composer 2.5 (—)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 131,
              "ticket": 141,
              "at": "2026-09-10T22:38:00Z",
              "session": "term_5666",
              "runner": "orca",
              "machine": "cheuk-mbp",
              "host": "cursor",
              "model": "composer 2.5",
              "effort": "—",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/141-work",
              "branch": "issue-141",
              "base": "ae0a1c6e5d86efc074539319b3f5dd21c2b71880",
              "into": "wake-relay"
            }
          }, {
            "comment": 3180014101,
            "event": "ticket.claimed",
            "at": "2026-09-10T22:38:00Z",
            "actor": "worker",
            "line": "Claimed #141 on issue-141 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 131,
              "ticket": 141,
              "at": "2026-09-10T22:38:00Z",
              "login": "chancheuklap",
              "branch": "issue-141",
              "commit": "ae0a1c6e5d86efc074539319b3f5dd21c2b71880"
            }
          }, {
            "comment": 3180014102,
            "event": "ticket.checked",
            "at": "2026-09-10T23:02:00Z",
            "actor": "worker",
            "line": "Own run on d1fc16755a5e: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 141,
              "at": "2026-09-10T23:02:00Z",
              "run": "self",
              "commit": "d1fc16755a5e6b6a258774dbcb2b75aa9bd77183",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "449fd224bd8aa28f9e3b4bb0ec363d91f3e07a47dc2e2a13663b09494a801487",
              "slot": 1,
              "port_base": 21100,
              "outside_owns": []
            }
          }, {
            "comment": 3180014103,
            "event": "reviewer.started",
            "at": "2026-09-10T23:04:00Z",
            "actor": "worker",
            "line": "reviewer started on herdr: session w4a5a, codex gpt-5.5 (medium)",
            "payload": {
              "v": 1,
              "event": "reviewer.started",
              "stage": "review",
              "actor": "worker",
              "spec": 131,
              "ticket": 141,
              "at": "2026-09-10T23:04:00Z",
              "session": "w4a5a",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/141-work",
              "branch": "issue-141",
              "base": "ae0a1c6e5d86efc074539319b3f5dd21c2b71880"
            }
          }, {
            "comment": 3180014104,
            "event": "reviewer.reported",
            "at": "2026-09-10T23:24:00Z",
            "actor": "reviewer",
            "line": "REVIEW ae0a1c6e5d86efc074539319b3f5dd21c2b71880..d1fc16755a5e6b6a258774dbcb2b75aa9bd77183",
            "payload": {
              "v": 1,
              "event": "reviewer.reported",
              "stage": "review",
              "actor": "reviewer",
              "spec": 131,
              "ticket": 141,
              "at": "2026-09-10T23:24:00Z",
              "base": "ae0a1c6e5d86efc074539319b3f5dd21c2b71880",
              "head": "d1fc16755a5e6b6a258774dbcb2b75aa9bd77183"
            }
          }, {
            "comment": 3180014105,
            "event": "worker.decided",
            "at": "2026-09-10T23:28:00Z",
            "actor": "worker",
            "line": "DECISIONS",
            "payload": {
              "v": 1,
              "event": "worker.decided",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 141,
              "at": "2026-09-10T23:28:00Z"
            }
          }]
        }, {
          "n": 136,
          "title": "重试与退避",
          "state": "open",
          "blocked": [132],
          "blockers": [{
            "number": 132,
            "title": "中继进程骨架",
            "state": "closed",
            "spec": 131,
            "readable": true,
            "blocker_hold": ""
          }],
          "blocker_hold": "open",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 136,
            "events": [{
              "comment": 3180013600,
              "event": "worker.started",
              "at": "2026-09-10T22:38:00Z",
              "actor": "main",
              "line": "worker started on herdr: session wa0be, claude opus 5 (high)"
            }, {
              "comment": 3180013601,
              "event": "ticket.claimed",
              "at": "2026-09-10T22:38:00Z",
              "actor": "worker",
              "line": "Claimed #136 on issue-136 as chancheuklap"
            }, {
              "comment": 3180013602,
              "event": "worker.queued",
              "at": "2026-09-10T23:32:00Z",
              "actor": "worker",
              "line": "Waiting for a product slot: this product's instance.max (2) is held"
            }],
            "last": {
              "comment": 3180013602,
              "event": "worker.queued",
              "at": "2026-09-10T23:32:00Z",
              "actor": "worker",
              "line": "Waiting for a product slot: this product's instance.max (2) is held",
              "body": "Waiting for a product slot: this product's instance.max (2) is held\n\n<!-- mmw {\"v\":1,\"event\":\"worker.queued\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":131,\"ticket\":136,\"at\":\"2026-09-10T23:32:00Z\",\"run\":\"self\",\"reason\":\"product-full\",\"limit\":2,\"holders\":[\"/Users/cheuklapchan/multi-model-workflow/.worktrees/126-work\",\"/Users/cheuklapchan/multi-model-workflow/.worktrees/127-work\"],\"worktree\":\"/Users/cheuklapchan/multi-model-workflow/.worktrees/136-work\"} -->\n",
              "payload": {
                "v": 1,
                "event": "worker.queued",
                "stage": "work",
                "actor": "worker",
                "spec": 131,
                "ticket": 136,
                "at": "2026-09-10T23:32:00Z",
                "run": "self",
                "reason": "product-full",
                "limit": 2,
                "holders": ["/Users/cheuklapchan/multi-model-workflow/.worktrees/126-work", "/Users/cheuklapchan/multi-model-workflow/.worktrees/127-work"],
                "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/136-work"
              }
            },
            "unreadable": [],
            "claimed": true,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": false,
            "returned": false,
            "outcome": null,
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": null,
            "decided": 0,
            "results": {
              "worker": null,
              "reviewer": null
            },
            "checks": {
              "self": null,
              "reverify": null,
              "repo-checks": null,
              "baseline": null
            },
            "waiting": {
              "comment": 3180013602,
              "event": "worker.queued",
              "at": "2026-09-10T23:32:00Z",
              "actor": "worker",
              "line": "Waiting for a product slot: this product's instance.max (2) is held",
              "body": "Waiting for a product slot: this product's instance.max (2) is held\n\n<!-- mmw {\"v\":1,\"event\":\"worker.queued\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":131,\"ticket\":136,\"at\":\"2026-09-10T23:32:00Z\",\"run\":\"self\",\"reason\":\"product-full\",\"limit\":2,\"holders\":[\"/Users/cheuklapchan/multi-model-workflow/.worktrees/126-work\",\"/Users/cheuklapchan/multi-model-workflow/.worktrees/127-work\"],\"worktree\":\"/Users/cheuklapchan/multi-model-workflow/.worktrees/136-work\"} -->\n",
              "payload": {
                "v": 1,
                "event": "worker.queued",
                "stage": "work",
                "actor": "worker",
                "spec": 131,
                "ticket": 136,
                "at": "2026-09-10T23:32:00Z",
                "run": "self",
                "reason": "product-full",
                "limit": 2,
                "holders": ["/Users/cheuklapchan/multi-model-workflow/.worktrees/126-work", "/Users/cheuklapchan/multi-model-workflow/.worktrees/127-work"],
                "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/136-work"
              }
            },
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [{
              "kind": "worker",
              "session": "wa0be",
              "runner": "herdr",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/136-work",
              "branch": "issue-136",
              "base": "3893a1954df97bd4e2aed22a0a1f2d27834185da",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013600,
              "live": true,
              "ended_by": null
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "wa0be",
              "runner": "herdr",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/136-work",
              "branch": "issue-136",
              "base": "3893a1954df97bd4e2aed22a0a1f2d27834185da",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013600,
              "live": true,
              "ended_by": null
            },
            "live_workers": [{
              "kind": "worker",
              "session": "wa0be",
              "runner": "herdr",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/136-work",
              "branch": "issue-136",
              "base": "3893a1954df97bd4e2aed22a0a1f2d27834185da",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013600,
              "live": true,
              "ended_by": null
            }],
            "holders": [{
              "kind": "worker",
              "session": "wa0be",
              "runner": "herdr",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/136-work",
              "branch": "issue-136",
              "base": "3893a1954df97bd4e2aed22a0a1f2d27834185da",
              "into": "wake-relay",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T22:38:00Z",
              "comment": 3180013600,
              "live": true,
              "ended_by": null
            }],
            "held": true,
            "hold_ended": false
          },
          "events": [{
            "comment": 3180013600,
            "event": "worker.started",
            "at": "2026-09-10T22:38:00Z",
            "actor": "main",
            "line": "worker started on herdr: session wa0be, claude opus 5 (high)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 131,
              "ticket": 136,
              "at": "2026-09-10T22:38:00Z",
              "session": "wa0be",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/136-work",
              "branch": "issue-136",
              "base": "3893a1954df97bd4e2aed22a0a1f2d27834185da",
              "into": "wake-relay"
            }
          }, {
            "comment": 3180013601,
            "event": "ticket.claimed",
            "at": "2026-09-10T22:38:00Z",
            "actor": "worker",
            "line": "Claimed #136 on issue-136 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 131,
              "ticket": 136,
              "at": "2026-09-10T22:38:00Z",
              "login": "chancheuklap",
              "branch": "issue-136",
              "commit": "3893a1954df97bd4e2aed22a0a1f2d27834185da"
            }
          }, {
            "comment": 3180013602,
            "event": "worker.queued",
            "at": "2026-09-10T23:32:00Z",
            "actor": "worker",
            "line": "Waiting for a product slot: this product's instance.max (2) is held",
            "payload": {
              "v": 1,
              "event": "worker.queued",
              "stage": "work",
              "actor": "worker",
              "spec": 131,
              "ticket": 136,
              "at": "2026-09-10T23:32:00Z",
              "run": "self",
              "reason": "product-full",
              "limit": 2,
              "holders": ["/Users/cheuklapchan/multi-model-workflow/.worktrees/126-work", "/Users/cheuklapchan/multi-model-workflow/.worktrees/127-work"],
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/136-work"
            }
          }]
        }, {
          "n": 135,
          "title": "投递回执",
          "state": "open",
          "blocked": [133, 134],
          "blockers": [{
            "number": 133,
            "title": "折叠接入中继",
            "state": "open",
            "spec": 131,
            "readable": true,
            "blocker_hold": "open"
          }, {
            "number": 134,
            "title": "唤醒队列持久化",
            "state": "open",
            "spec": 131,
            "readable": true,
            "blocker_hold": "open"
          }],
          "blocker_hold": "open",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 135,
            "events": [],
            "last": null,
            "unreadable": [],
            "claimed": false,
            "claimant": null,
            "refused": null,
            "passed": false,
            "returned": false,
            "outcome": null,
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": null,
            "decided": 0,
            "results": {
              "worker": null,
              "reviewer": null
            },
            "checks": {
              "self": null,
              "reverify": null,
              "repo-checks": null,
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [],
            "claim_hold": false,
            "ever_held": false,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": null,
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": false
          },
          "events": []
        }, {
          "n": 137,
          "title": "中继自检命令",
          "state": "open",
          "blocked": [135],
          "blockers": [{
            "number": 135,
            "title": "投递回执",
            "state": "open",
            "spec": 131,
            "readable": true,
            "blocker_hold": "open"
          }],
          "blocker_hold": "open",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 137,
            "events": [],
            "last": null,
            "unreadable": [],
            "claimed": false,
            "claimant": null,
            "refused": null,
            "passed": false,
            "returned": false,
            "outcome": null,
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": null,
            "decided": 0,
            "results": {
              "worker": null,
              "reviewer": null
            },
            "checks": {
              "self": null,
              "reverify": null,
              "repo-checks": null,
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [],
            "claim_hold": false,
            "ever_held": false,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": null,
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": false
          },
          "events": []
        }]
      }, {
        "n": 140,
        "title": "判活三层",
        "tickets": [{
          "n": 143,
          "title": "心跳读取",
          "state": "open",
          "blocked": [],
          "blockers": [],
          "blocker_hold": "open",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 143,
            "events": [],
            "last": null,
            "unreadable": [],
            "claimed": false,
            "claimant": null,
            "refused": null,
            "passed": false,
            "returned": false,
            "outcome": null,
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": null,
            "decided": 0,
            "results": {
              "worker": null,
              "reviewer": null
            },
            "checks": {
              "self": null,
              "reverify": null,
              "repo-checks": null,
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [],
            "claim_hold": false,
            "ever_held": false,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": null,
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": false
          },
          "events": []
        }, {
          "n": 144,
          "title": "回合守卫",
          "state": "open",
          "blocked": [143],
          "blockers": [{
            "number": 143,
            "title": "心跳读取",
            "state": "open",
            "spec": 140,
            "readable": true,
            "blocker_hold": "open"
          }],
          "blocker_hold": "open",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 144,
            "events": [],
            "last": null,
            "unreadable": [],
            "claimed": false,
            "claimant": null,
            "refused": null,
            "passed": false,
            "returned": false,
            "outcome": null,
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": null,
            "decided": 0,
            "results": {
              "worker": null,
              "reviewer": null
            },
            "checks": {
              "self": null,
              "reverify": null,
              "repo-checks": null,
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [],
            "claim_hold": false,
            "ever_held": false,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": null,
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": false
          },
          "events": []
        }, {
          "n": 145,
          "title": "worker.lost 写入",
          "state": "open",
          "blocked": [144],
          "blockers": [{
            "number": 144,
            "title": "回合守卫",
            "state": "open",
            "spec": 140,
            "readable": true,
            "blocker_hold": "open"
          }],
          "blocker_hold": "open",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 145,
            "events": [],
            "last": null,
            "unreadable": [],
            "claimed": false,
            "claimant": null,
            "refused": null,
            "passed": false,
            "returned": false,
            "outcome": null,
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": null,
            "decided": 0,
            "results": {
              "worker": null,
              "reviewer": null
            },
            "checks": {
              "self": null,
              "reverify": null,
              "repo-checks": null,
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [],
            "claim_hold": false,
            "ever_held": false,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": null,
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": false
          },
          "events": []
        }, {
          "n": 146,
          "title": "判活扫描",
          "state": "open",
          "blocked": [143],
          "blockers": [{
            "number": 143,
            "title": "心跳读取",
            "state": "open",
            "spec": 140,
            "readable": true,
            "blocker_hold": "open"
          }],
          "blocker_hold": "open",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 146,
            "events": [],
            "last": null,
            "unreadable": [],
            "claimed": false,
            "claimant": null,
            "refused": null,
            "passed": false,
            "returned": false,
            "outcome": null,
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": null,
            "decided": 0,
            "results": {
              "worker": null,
              "reviewer": null
            },
            "checks": {
              "self": null,
              "reverify": null,
              "repo-checks": null,
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [],
            "claim_hold": false,
            "ever_held": false,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": null,
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": false
          },
          "events": []
        }]
      }]
    }, {
      "n": 77,
      "kind": "map",
      "title": "交接包比对",
      "state": "open",
      "decisions": [],
      "specs": [{
        "n": 80,
        "title": "交接包落盘",
        "tickets": [{
          "n": 81,
          "title": "scenes.json 导出",
          "state": "closed",
          "blocked": [],
          "blockers": [],
          "blocker_hold": "",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 81,
            "events": [{
              "comment": 3180008100,
              "event": "worker.started",
              "at": "2026-09-10T11:10:00Z",
              "actor": "main",
              "line": "worker started on herdr: session wd6cf, claude opus 5 (high)"
            }, {
              "comment": 3180008101,
              "event": "ticket.claimed",
              "at": "2026-09-10T11:10:00Z",
              "actor": "worker",
              "line": "Claimed #81 on issue-81 as chancheuklap"
            }, {
              "comment": 3180008102,
              "event": "ticket.checked",
              "at": "2026-09-10T11:42:00Z",
              "actor": "worker",
              "line": "Own run on a93a6d92de87: ALL MET"
            }, {
              "comment": 3180008103,
              "event": "reviewer.started",
              "at": "2026-09-10T11:46:00Z",
              "actor": "worker",
              "line": "reviewer started on herdr: session wf296, codex gpt-5.5 (medium)"
            }, {
              "comment": 3180008104,
              "event": "reviewer.reported",
              "at": "2026-09-10T11:57:00Z",
              "actor": "reviewer",
              "line": "REVIEW 2c15fe9208a48edf57f90f3ccab5ad0833c23ea5..a93a6d92de870018237b60cbd8c6e4f931f595d1"
            }, {
              "comment": 3180008105,
              "event": "worker.decided",
              "at": "2026-09-10T12:00:00Z",
              "actor": "worker",
              "line": "DECISIONS"
            }, {
              "comment": 3180008106,
              "event": "ticket.checked",
              "at": "2026-09-10T12:12:00Z",
              "actor": "worker",
              "line": "Reverify on a93a6d92de87: ALL MET"
            }, {
              "comment": 3180008107,
              "event": "ticket.checked",
              "at": "2026-09-10T12:20:00Z",
              "actor": "worker",
              "line": "Repository checks on a93a6d92de87: 3/3 passed"
            }, {
              "comment": 3180008108,
              "event": "ticket.passed",
              "at": "2026-09-10T12:23:00Z",
              "actor": "worker",
              "line": "ALL MET"
            }, {
              "comment": 3180008109,
              "event": "ticket.landed",
              "at": "2026-09-10T12:31:00Z",
              "actor": "main",
              "line": "Landed issue-81 into main"
            }],
            "last": {
              "comment": 3180008109,
              "event": "ticket.landed",
              "at": "2026-09-10T12:31:00Z",
              "actor": "main",
              "line": "Landed issue-81 into main",
              "body": "Landed issue-81 into main\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.landed\",\"stage\":\"land\",\"actor\":\"main\",\"spec\":80,\"ticket\":81,\"at\":\"2026-09-10T12:31:00Z\",\"branch\":\"issue-81\",\"into\":\"main\",\"commit\":\"a93a6d92de870018237b60cbd8c6e4f931f595d1\",\"merge\":\"81e6f42ceba30cb31bf6c8dab59eb450c29fd3d1\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.landed",
                "stage": "land",
                "actor": "main",
                "spec": 80,
                "ticket": 81,
                "at": "2026-09-10T12:31:00Z",
                "branch": "issue-81",
                "into": "main",
                "commit": "a93a6d92de870018237b60cbd8c6e4f931f595d1",
                "merge": "81e6f42ceba30cb31bf6c8dab59eb450c29fd3d1"
              }
            },
            "unreadable": [],
            "claimed": false,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": true,
            "returned": false,
            "outcome": {
              "comment": 3180008108,
              "event": "ticket.passed",
              "at": "2026-09-10T12:23:00Z",
              "actor": "worker",
              "line": "ALL MET",
              "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":80,\"ticket\":81,\"at\":\"2026-09-10T12:23:00Z\",\"commit\":\"a93a6d92de870018237b60cbd8c6e4f931f595d1\",\"branch\":\"issue-81\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"main\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.passed",
                "stage": "close",
                "actor": "worker",
                "spec": 80,
                "ticket": 81,
                "at": "2026-09-10T12:23:00Z",
                "commit": "a93a6d92de870018237b60cbd8c6e4f931f595d1",
                "branch": "issue-81",
                "counts": {
                  "met": 4,
                  "unmet": 0,
                  "abandoned": 0,
                  "total": 4
                },
                "into": "main"
              }
            },
            "landed": true,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": {
              "comment": 3180008104,
              "event": "reviewer.reported",
              "at": "2026-09-10T11:57:00Z",
              "actor": "reviewer",
              "line": "REVIEW 2c15fe9208a48edf57f90f3ccab5ad0833c23ea5..a93a6d92de870018237b60cbd8c6e4f931f595d1",
              "body": "REVIEW 2c15fe9208a48edf57f90f3ccab5ad0833c23ea5..a93a6d92de870018237b60cbd8c6e4f931f595d1\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":80,\"ticket\":81,\"at\":\"2026-09-10T11:57:00Z\",\"base\":\"2c15fe9208a48edf57f90f3ccab5ad0833c23ea5\",\"head\":\"a93a6d92de870018237b60cbd8c6e4f931f595d1\"} -->\n",
              "payload": {
                "v": 1,
                "event": "reviewer.reported",
                "stage": "review",
                "actor": "reviewer",
                "spec": 80,
                "ticket": 81,
                "at": "2026-09-10T11:57:00Z",
                "base": "2c15fe9208a48edf57f90f3ccab5ad0833c23ea5",
                "head": "a93a6d92de870018237b60cbd8c6e4f931f595d1"
              }
            },
            "decided": 1,
            "results": {
              "worker": {
                "comment": 3180008108,
                "event": "ticket.passed",
                "at": "2026-09-10T12:23:00Z",
                "actor": "worker",
                "line": "ALL MET",
                "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":80,\"ticket\":81,\"at\":\"2026-09-10T12:23:00Z\",\"commit\":\"a93a6d92de870018237b60cbd8c6e4f931f595d1\",\"branch\":\"issue-81\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"main\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.passed",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 80,
                  "ticket": 81,
                  "at": "2026-09-10T12:23:00Z",
                  "commit": "a93a6d92de870018237b60cbd8c6e4f931f595d1",
                  "branch": "issue-81",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "into": "main"
                }
              },
              "reviewer": {
                "comment": 3180008104,
                "event": "reviewer.reported",
                "at": "2026-09-10T11:57:00Z",
                "actor": "reviewer",
                "line": "REVIEW 2c15fe9208a48edf57f90f3ccab5ad0833c23ea5..a93a6d92de870018237b60cbd8c6e4f931f595d1",
                "body": "REVIEW 2c15fe9208a48edf57f90f3ccab5ad0833c23ea5..a93a6d92de870018237b60cbd8c6e4f931f595d1\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":80,\"ticket\":81,\"at\":\"2026-09-10T11:57:00Z\",\"base\":\"2c15fe9208a48edf57f90f3ccab5ad0833c23ea5\",\"head\":\"a93a6d92de870018237b60cbd8c6e4f931f595d1\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "reviewer.reported",
                  "stage": "review",
                  "actor": "reviewer",
                  "spec": 80,
                  "ticket": 81,
                  "at": "2026-09-10T11:57:00Z",
                  "base": "2c15fe9208a48edf57f90f3ccab5ad0833c23ea5",
                  "head": "a93a6d92de870018237b60cbd8c6e4f931f595d1"
                }
              }
            },
            "checks": {
              "self": {
                "comment": 3180008102,
                "event": "ticket.checked",
                "at": "2026-09-10T11:42:00Z",
                "actor": "worker",
                "line": "Own run on a93a6d92de87: ALL MET",
                "body": "Own run on a93a6d92de87: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":80,\"ticket\":81,\"at\":\"2026-09-10T11:42:00Z\",\"run\":\"self\",\"commit\":\"a93a6d92de870018237b60cbd8c6e4f931f595d1\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"d0105bc6ef8bc6a7c09cb3621f3a3d9ce3bbef86cc2553bd14c7d49da47c89be\",\"slot\":1,\"port_base\":21100,\"outside_owns\":[]} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "work",
                  "actor": "worker",
                  "spec": 80,
                  "ticket": 81,
                  "at": "2026-09-10T11:42:00Z",
                  "run": "self",
                  "commit": "a93a6d92de870018237b60cbd8c6e4f931f595d1",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "d0105bc6ef8bc6a7c09cb3621f3a3d9ce3bbef86cc2553bd14c7d49da47c89be",
                  "slot": 1,
                  "port_base": 21100,
                  "outside_owns": []
                }
              },
              "reverify": {
                "comment": 3180008106,
                "event": "ticket.checked",
                "at": "2026-09-10T12:12:00Z",
                "actor": "worker",
                "line": "Reverify on a93a6d92de87: ALL MET",
                "body": "Reverify on a93a6d92de87: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"verify\",\"actor\":\"worker\",\"spec\":80,\"ticket\":81,\"at\":\"2026-09-10T12:12:00Z\",\"run\":\"reverify\",\"commit\":\"a93a6d92de870018237b60cbd8c6e4f931f595d1\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"d0105bc6ef8bc6a7c09cb3621f3a3d9ce3bbef86cc2553bd14c7d49da47c89be\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "verify",
                  "actor": "worker",
                  "spec": 80,
                  "ticket": 81,
                  "at": "2026-09-10T12:12:00Z",
                  "run": "reverify",
                  "commit": "a93a6d92de870018237b60cbd8c6e4f931f595d1",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "d0105bc6ef8bc6a7c09cb3621f3a3d9ce3bbef86cc2553bd14c7d49da47c89be"
                }
              },
              "repo-checks": {
                "comment": 3180008107,
                "event": "ticket.checked",
                "at": "2026-09-10T12:20:00Z",
                "actor": "worker",
                "line": "Repository checks on a93a6d92de87: 3/3 passed",
                "body": "Repository checks on a93a6d92de87: 3/3 passed\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":80,\"ticket\":81,\"at\":\"2026-09-10T12:20:00Z\",\"run\":\"repo-checks\",\"commit\":\"a93a6d92de870018237b60cbd8c6e4f931f595d1\",\"result\":\"met\",\"counts\":{\"passed\":3,\"total\":3}} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 80,
                  "ticket": 81,
                  "at": "2026-09-10T12:20:00Z",
                  "run": "repo-checks",
                  "commit": "a93a6d92de870018237b60cbd8c6e4f931f595d1",
                  "result": "met",
                  "counts": {
                    "passed": 3,
                    "total": 3
                  }
                }
              },
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [{
              "kind": "worker",
              "session": "wd6cf",
              "runner": "herdr",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/81-work",
              "branch": "issue-81",
              "base": "2c15fe9208a48edf57f90f3ccab5ad0833c23ea5",
              "into": "main",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T11:10:00Z",
              "comment": 3180008100,
              "live": false,
              "ended_by": "ticket.landed"
            }, {
              "kind": "reviewer",
              "session": "wf296",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/81-work",
              "branch": "issue-81",
              "base": "2c15fe9208a48edf57f90f3ccab5ad0833c23ea5",
              "into": null,
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T11:46:00Z",
              "comment": 3180008103,
              "live": false,
              "ended_by": "reviewer.reported"
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "wd6cf",
              "runner": "herdr",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/81-work",
              "branch": "issue-81",
              "base": "2c15fe9208a48edf57f90f3ccab5ad0833c23ea5",
              "into": "main",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T11:10:00Z",
              "comment": 3180008100,
              "live": false,
              "ended_by": "ticket.landed"
            },
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": true
          },
          "events": [{
            "comment": 3180008100,
            "event": "worker.started",
            "at": "2026-09-10T11:10:00Z",
            "actor": "main",
            "line": "worker started on herdr: session wd6cf, claude opus 5 (high)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 80,
              "ticket": 81,
              "at": "2026-09-10T11:10:00Z",
              "session": "wd6cf",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "claude",
              "model": "opus 5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/81-work",
              "branch": "issue-81",
              "base": "2c15fe9208a48edf57f90f3ccab5ad0833c23ea5",
              "into": "main"
            }
          }, {
            "comment": 3180008101,
            "event": "ticket.claimed",
            "at": "2026-09-10T11:10:00Z",
            "actor": "worker",
            "line": "Claimed #81 on issue-81 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 80,
              "ticket": 81,
              "at": "2026-09-10T11:10:00Z",
              "login": "chancheuklap",
              "branch": "issue-81",
              "commit": "2c15fe9208a48edf57f90f3ccab5ad0833c23ea5"
            }
          }, {
            "comment": 3180008102,
            "event": "ticket.checked",
            "at": "2026-09-10T11:42:00Z",
            "actor": "worker",
            "line": "Own run on a93a6d92de87: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "work",
              "actor": "worker",
              "spec": 80,
              "ticket": 81,
              "at": "2026-09-10T11:42:00Z",
              "run": "self",
              "commit": "a93a6d92de870018237b60cbd8c6e4f931f595d1",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "d0105bc6ef8bc6a7c09cb3621f3a3d9ce3bbef86cc2553bd14c7d49da47c89be",
              "slot": 1,
              "port_base": 21100,
              "outside_owns": []
            }
          }, {
            "comment": 3180008103,
            "event": "reviewer.started",
            "at": "2026-09-10T11:46:00Z",
            "actor": "worker",
            "line": "reviewer started on herdr: session wf296, codex gpt-5.5 (medium)",
            "payload": {
              "v": 1,
              "event": "reviewer.started",
              "stage": "review",
              "actor": "worker",
              "spec": 80,
              "ticket": 81,
              "at": "2026-09-10T11:46:00Z",
              "session": "wf296",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/81-work",
              "branch": "issue-81",
              "base": "2c15fe9208a48edf57f90f3ccab5ad0833c23ea5"
            }
          }, {
            "comment": 3180008104,
            "event": "reviewer.reported",
            "at": "2026-09-10T11:57:00Z",
            "actor": "reviewer",
            "line": "REVIEW 2c15fe9208a48edf57f90f3ccab5ad0833c23ea5..a93a6d92de870018237b60cbd8c6e4f931f595d1",
            "payload": {
              "v": 1,
              "event": "reviewer.reported",
              "stage": "review",
              "actor": "reviewer",
              "spec": 80,
              "ticket": 81,
              "at": "2026-09-10T11:57:00Z",
              "base": "2c15fe9208a48edf57f90f3ccab5ad0833c23ea5",
              "head": "a93a6d92de870018237b60cbd8c6e4f931f595d1"
            }
          }, {
            "comment": 3180008105,
            "event": "worker.decided",
            "at": "2026-09-10T12:00:00Z",
            "actor": "worker",
            "line": "DECISIONS",
            "payload": {
              "v": 1,
              "event": "worker.decided",
              "stage": "work",
              "actor": "worker",
              "spec": 80,
              "ticket": 81,
              "at": "2026-09-10T12:00:00Z"
            }
          }, {
            "comment": 3180008106,
            "event": "ticket.checked",
            "at": "2026-09-10T12:12:00Z",
            "actor": "worker",
            "line": "Reverify on a93a6d92de87: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "verify",
              "actor": "worker",
              "spec": 80,
              "ticket": 81,
              "at": "2026-09-10T12:12:00Z",
              "run": "reverify",
              "commit": "a93a6d92de870018237b60cbd8c6e4f931f595d1",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "d0105bc6ef8bc6a7c09cb3621f3a3d9ce3bbef86cc2553bd14c7d49da47c89be"
            }
          }, {
            "comment": 3180008107,
            "event": "ticket.checked",
            "at": "2026-09-10T12:20:00Z",
            "actor": "worker",
            "line": "Repository checks on a93a6d92de87: 3/3 passed",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "close",
              "actor": "worker",
              "spec": 80,
              "ticket": 81,
              "at": "2026-09-10T12:20:00Z",
              "run": "repo-checks",
              "commit": "a93a6d92de870018237b60cbd8c6e4f931f595d1",
              "result": "met",
              "counts": {
                "passed": 3,
                "total": 3
              }
            }
          }, {
            "comment": 3180008108,
            "event": "ticket.passed",
            "at": "2026-09-10T12:23:00Z",
            "actor": "worker",
            "line": "ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.passed",
              "stage": "close",
              "actor": "worker",
              "spec": 80,
              "ticket": 81,
              "at": "2026-09-10T12:23:00Z",
              "commit": "a93a6d92de870018237b60cbd8c6e4f931f595d1",
              "branch": "issue-81",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "into": "main"
            }
          }, {
            "comment": 3180008109,
            "event": "ticket.landed",
            "at": "2026-09-10T12:31:00Z",
            "actor": "main",
            "line": "Landed issue-81 into main",
            "payload": {
              "v": 1,
              "event": "ticket.landed",
              "stage": "land",
              "actor": "main",
              "spec": 80,
              "ticket": 81,
              "at": "2026-09-10T12:31:00Z",
              "branch": "issue-81",
              "into": "main",
              "commit": "a93a6d92de870018237b60cbd8c6e4f931f595d1",
              "merge": "81e6f42ceba30cb31bf6c8dab59eb450c29fd3d1"
            }
          }]
        }, {
          "n": 82,
          "title": "vendor 三个脚本",
          "state": "closed",
          "blocked": [81],
          "blockers": [{
            "number": 81,
            "title": "scenes.json 导出",
            "state": "closed",
            "spec": 80,
            "readable": true,
            "blocker_hold": ""
          }],
          "blocker_hold": "",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 82,
            "events": [{
              "comment": 3180008200,
              "event": "worker.started",
              "at": "2026-09-10T12:32:00Z",
              "actor": "main",
              "line": "worker started on herdr: session w6e16, cursor grok 4.6 (high)"
            }, {
              "comment": 3180008201,
              "event": "ticket.claimed",
              "at": "2026-09-10T12:32:00Z",
              "actor": "worker",
              "line": "Claimed #82 on issue-82 as chancheuklap"
            }, {
              "comment": 3180008202,
              "event": "ticket.checked",
              "at": "2026-09-10T12:51:00Z",
              "actor": "worker",
              "line": "Own run on 317cb6a9515d: ALL MET"
            }, {
              "comment": 3180008203,
              "event": "reviewer.started",
              "at": "2026-09-10T12:54:00Z",
              "actor": "worker",
              "line": "reviewer started on herdr: session w32fd, codex gpt-5.5 (medium)"
            }, {
              "comment": 3180008204,
              "event": "reviewer.reported",
              "at": "2026-09-10T13:00:00Z",
              "actor": "reviewer",
              "line": "REVIEW b81e35dfeae640a69757ab58da0a7591af3ab89a..317cb6a9515df8c63fb4e94491aef90e91f8b265"
            }, {
              "comment": 3180008205,
              "event": "worker.decided",
              "at": "2026-09-10T13:02:00Z",
              "actor": "worker",
              "line": "DECISIONS"
            }, {
              "comment": 3180008206,
              "event": "ticket.checked",
              "at": "2026-09-10T13:08:00Z",
              "actor": "worker",
              "line": "Reverify on 317cb6a9515d: ALL MET"
            }, {
              "comment": 3180008207,
              "event": "ticket.checked",
              "at": "2026-09-10T13:13:00Z",
              "actor": "worker",
              "line": "Repository checks on 317cb6a9515d: 3/3 passed"
            }, {
              "comment": 3180008208,
              "event": "ticket.passed",
              "at": "2026-09-10T13:15:00Z",
              "actor": "worker",
              "line": "ALL MET"
            }, {
              "comment": 3180008209,
              "event": "ticket.landed",
              "at": "2026-09-10T13:20:00Z",
              "actor": "main",
              "line": "Landed issue-82 into main"
            }],
            "last": {
              "comment": 3180008209,
              "event": "ticket.landed",
              "at": "2026-09-10T13:20:00Z",
              "actor": "main",
              "line": "Landed issue-82 into main",
              "body": "Landed issue-82 into main\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.landed\",\"stage\":\"land\",\"actor\":\"main\",\"spec\":80,\"ticket\":82,\"at\":\"2026-09-10T13:20:00Z\",\"branch\":\"issue-82\",\"into\":\"main\",\"commit\":\"317cb6a9515df8c63fb4e94491aef90e91f8b265\",\"merge\":\"4a94090c080e3df504e2be5c2d85dc3158f3167b\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.landed",
                "stage": "land",
                "actor": "main",
                "spec": 80,
                "ticket": 82,
                "at": "2026-09-10T13:20:00Z",
                "branch": "issue-82",
                "into": "main",
                "commit": "317cb6a9515df8c63fb4e94491aef90e91f8b265",
                "merge": "4a94090c080e3df504e2be5c2d85dc3158f3167b"
              }
            },
            "unreadable": [],
            "claimed": false,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": true,
            "returned": false,
            "outcome": {
              "comment": 3180008208,
              "event": "ticket.passed",
              "at": "2026-09-10T13:15:00Z",
              "actor": "worker",
              "line": "ALL MET",
              "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":80,\"ticket\":82,\"at\":\"2026-09-10T13:15:00Z\",\"commit\":\"317cb6a9515df8c63fb4e94491aef90e91f8b265\",\"branch\":\"issue-82\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"main\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.passed",
                "stage": "close",
                "actor": "worker",
                "spec": 80,
                "ticket": 82,
                "at": "2026-09-10T13:15:00Z",
                "commit": "317cb6a9515df8c63fb4e94491aef90e91f8b265",
                "branch": "issue-82",
                "counts": {
                  "met": 4,
                  "unmet": 0,
                  "abandoned": 0,
                  "total": 4
                },
                "into": "main"
              }
            },
            "landed": true,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": {
              "comment": 3180008204,
              "event": "reviewer.reported",
              "at": "2026-09-10T13:00:00Z",
              "actor": "reviewer",
              "line": "REVIEW b81e35dfeae640a69757ab58da0a7591af3ab89a..317cb6a9515df8c63fb4e94491aef90e91f8b265",
              "body": "REVIEW b81e35dfeae640a69757ab58da0a7591af3ab89a..317cb6a9515df8c63fb4e94491aef90e91f8b265\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":80,\"ticket\":82,\"at\":\"2026-09-10T13:00:00Z\",\"base\":\"b81e35dfeae640a69757ab58da0a7591af3ab89a\",\"head\":\"317cb6a9515df8c63fb4e94491aef90e91f8b265\"} -->\n",
              "payload": {
                "v": 1,
                "event": "reviewer.reported",
                "stage": "review",
                "actor": "reviewer",
                "spec": 80,
                "ticket": 82,
                "at": "2026-09-10T13:00:00Z",
                "base": "b81e35dfeae640a69757ab58da0a7591af3ab89a",
                "head": "317cb6a9515df8c63fb4e94491aef90e91f8b265"
              }
            },
            "decided": 1,
            "results": {
              "worker": {
                "comment": 3180008208,
                "event": "ticket.passed",
                "at": "2026-09-10T13:15:00Z",
                "actor": "worker",
                "line": "ALL MET",
                "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":80,\"ticket\":82,\"at\":\"2026-09-10T13:15:00Z\",\"commit\":\"317cb6a9515df8c63fb4e94491aef90e91f8b265\",\"branch\":\"issue-82\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"main\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.passed",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 80,
                  "ticket": 82,
                  "at": "2026-09-10T13:15:00Z",
                  "commit": "317cb6a9515df8c63fb4e94491aef90e91f8b265",
                  "branch": "issue-82",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "into": "main"
                }
              },
              "reviewer": {
                "comment": 3180008204,
                "event": "reviewer.reported",
                "at": "2026-09-10T13:00:00Z",
                "actor": "reviewer",
                "line": "REVIEW b81e35dfeae640a69757ab58da0a7591af3ab89a..317cb6a9515df8c63fb4e94491aef90e91f8b265",
                "body": "REVIEW b81e35dfeae640a69757ab58da0a7591af3ab89a..317cb6a9515df8c63fb4e94491aef90e91f8b265\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":80,\"ticket\":82,\"at\":\"2026-09-10T13:00:00Z\",\"base\":\"b81e35dfeae640a69757ab58da0a7591af3ab89a\",\"head\":\"317cb6a9515df8c63fb4e94491aef90e91f8b265\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "reviewer.reported",
                  "stage": "review",
                  "actor": "reviewer",
                  "spec": 80,
                  "ticket": 82,
                  "at": "2026-09-10T13:00:00Z",
                  "base": "b81e35dfeae640a69757ab58da0a7591af3ab89a",
                  "head": "317cb6a9515df8c63fb4e94491aef90e91f8b265"
                }
              }
            },
            "checks": {
              "self": {
                "comment": 3180008202,
                "event": "ticket.checked",
                "at": "2026-09-10T12:51:00Z",
                "actor": "worker",
                "line": "Own run on 317cb6a9515d: ALL MET",
                "body": "Own run on 317cb6a9515d: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":80,\"ticket\":82,\"at\":\"2026-09-10T12:51:00Z\",\"run\":\"self\",\"commit\":\"317cb6a9515df8c63fb4e94491aef90e91f8b265\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"a9553a56d3d0cc9aa5cd8ff54126b0f013fcfd9e8eed409b3d746c992954399e\",\"slot\":1,\"port_base\":21100,\"outside_owns\":[]} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "work",
                  "actor": "worker",
                  "spec": 80,
                  "ticket": 82,
                  "at": "2026-09-10T12:51:00Z",
                  "run": "self",
                  "commit": "317cb6a9515df8c63fb4e94491aef90e91f8b265",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "a9553a56d3d0cc9aa5cd8ff54126b0f013fcfd9e8eed409b3d746c992954399e",
                  "slot": 1,
                  "port_base": 21100,
                  "outside_owns": []
                }
              },
              "reverify": {
                "comment": 3180008206,
                "event": "ticket.checked",
                "at": "2026-09-10T13:08:00Z",
                "actor": "worker",
                "line": "Reverify on 317cb6a9515d: ALL MET",
                "body": "Reverify on 317cb6a9515d: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"verify\",\"actor\":\"worker\",\"spec\":80,\"ticket\":82,\"at\":\"2026-09-10T13:08:00Z\",\"run\":\"reverify\",\"commit\":\"317cb6a9515df8c63fb4e94491aef90e91f8b265\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"a9553a56d3d0cc9aa5cd8ff54126b0f013fcfd9e8eed409b3d746c992954399e\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "verify",
                  "actor": "worker",
                  "spec": 80,
                  "ticket": 82,
                  "at": "2026-09-10T13:08:00Z",
                  "run": "reverify",
                  "commit": "317cb6a9515df8c63fb4e94491aef90e91f8b265",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "a9553a56d3d0cc9aa5cd8ff54126b0f013fcfd9e8eed409b3d746c992954399e"
                }
              },
              "repo-checks": {
                "comment": 3180008207,
                "event": "ticket.checked",
                "at": "2026-09-10T13:13:00Z",
                "actor": "worker",
                "line": "Repository checks on 317cb6a9515d: 3/3 passed",
                "body": "Repository checks on 317cb6a9515d: 3/3 passed\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":80,\"ticket\":82,\"at\":\"2026-09-10T13:13:00Z\",\"run\":\"repo-checks\",\"commit\":\"317cb6a9515df8c63fb4e94491aef90e91f8b265\",\"result\":\"met\",\"counts\":{\"passed\":3,\"total\":3}} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 80,
                  "ticket": 82,
                  "at": "2026-09-10T13:13:00Z",
                  "run": "repo-checks",
                  "commit": "317cb6a9515df8c63fb4e94491aef90e91f8b265",
                  "result": "met",
                  "counts": {
                    "passed": 3,
                    "total": 3
                  }
                }
              },
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [{
              "kind": "worker",
              "session": "w6e16",
              "runner": "herdr",
              "host": "cursor",
              "model": "grok 4.6",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/82-work",
              "branch": "issue-82",
              "base": "b81e35dfeae640a69757ab58da0a7591af3ab89a",
              "into": "main",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T12:32:00Z",
              "comment": 3180008200,
              "live": false,
              "ended_by": "ticket.landed"
            }, {
              "kind": "reviewer",
              "session": "w32fd",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/82-work",
              "branch": "issue-82",
              "base": "b81e35dfeae640a69757ab58da0a7591af3ab89a",
              "into": null,
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T12:54:00Z",
              "comment": 3180008203,
              "live": false,
              "ended_by": "reviewer.reported"
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "w6e16",
              "runner": "herdr",
              "host": "cursor",
              "model": "grok 4.6",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/82-work",
              "branch": "issue-82",
              "base": "b81e35dfeae640a69757ab58da0a7591af3ab89a",
              "into": "main",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T12:32:00Z",
              "comment": 3180008200,
              "live": false,
              "ended_by": "ticket.landed"
            },
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": true
          },
          "events": [{
            "comment": 3180008200,
            "event": "worker.started",
            "at": "2026-09-10T12:32:00Z",
            "actor": "main",
            "line": "worker started on herdr: session w6e16, cursor grok 4.6 (high)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 80,
              "ticket": 82,
              "at": "2026-09-10T12:32:00Z",
              "session": "w6e16",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "cursor",
              "model": "grok 4.6",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/82-work",
              "branch": "issue-82",
              "base": "b81e35dfeae640a69757ab58da0a7591af3ab89a",
              "into": "main"
            }
          }, {
            "comment": 3180008201,
            "event": "ticket.claimed",
            "at": "2026-09-10T12:32:00Z",
            "actor": "worker",
            "line": "Claimed #82 on issue-82 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 80,
              "ticket": 82,
              "at": "2026-09-10T12:32:00Z",
              "login": "chancheuklap",
              "branch": "issue-82",
              "commit": "b81e35dfeae640a69757ab58da0a7591af3ab89a"
            }
          }, {
            "comment": 3180008202,
            "event": "ticket.checked",
            "at": "2026-09-10T12:51:00Z",
            "actor": "worker",
            "line": "Own run on 317cb6a9515d: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "work",
              "actor": "worker",
              "spec": 80,
              "ticket": 82,
              "at": "2026-09-10T12:51:00Z",
              "run": "self",
              "commit": "317cb6a9515df8c63fb4e94491aef90e91f8b265",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "a9553a56d3d0cc9aa5cd8ff54126b0f013fcfd9e8eed409b3d746c992954399e",
              "slot": 1,
              "port_base": 21100,
              "outside_owns": []
            }
          }, {
            "comment": 3180008203,
            "event": "reviewer.started",
            "at": "2026-09-10T12:54:00Z",
            "actor": "worker",
            "line": "reviewer started on herdr: session w32fd, codex gpt-5.5 (medium)",
            "payload": {
              "v": 1,
              "event": "reviewer.started",
              "stage": "review",
              "actor": "worker",
              "spec": 80,
              "ticket": 82,
              "at": "2026-09-10T12:54:00Z",
              "session": "w32fd",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/82-work",
              "branch": "issue-82",
              "base": "b81e35dfeae640a69757ab58da0a7591af3ab89a"
            }
          }, {
            "comment": 3180008204,
            "event": "reviewer.reported",
            "at": "2026-09-10T13:00:00Z",
            "actor": "reviewer",
            "line": "REVIEW b81e35dfeae640a69757ab58da0a7591af3ab89a..317cb6a9515df8c63fb4e94491aef90e91f8b265",
            "payload": {
              "v": 1,
              "event": "reviewer.reported",
              "stage": "review",
              "actor": "reviewer",
              "spec": 80,
              "ticket": 82,
              "at": "2026-09-10T13:00:00Z",
              "base": "b81e35dfeae640a69757ab58da0a7591af3ab89a",
              "head": "317cb6a9515df8c63fb4e94491aef90e91f8b265"
            }
          }, {
            "comment": 3180008205,
            "event": "worker.decided",
            "at": "2026-09-10T13:02:00Z",
            "actor": "worker",
            "line": "DECISIONS",
            "payload": {
              "v": 1,
              "event": "worker.decided",
              "stage": "work",
              "actor": "worker",
              "spec": 80,
              "ticket": 82,
              "at": "2026-09-10T13:02:00Z"
            }
          }, {
            "comment": 3180008206,
            "event": "ticket.checked",
            "at": "2026-09-10T13:08:00Z",
            "actor": "worker",
            "line": "Reverify on 317cb6a9515d: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "verify",
              "actor": "worker",
              "spec": 80,
              "ticket": 82,
              "at": "2026-09-10T13:08:00Z",
              "run": "reverify",
              "commit": "317cb6a9515df8c63fb4e94491aef90e91f8b265",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "a9553a56d3d0cc9aa5cd8ff54126b0f013fcfd9e8eed409b3d746c992954399e"
            }
          }, {
            "comment": 3180008207,
            "event": "ticket.checked",
            "at": "2026-09-10T13:13:00Z",
            "actor": "worker",
            "line": "Repository checks on 317cb6a9515d: 3/3 passed",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "close",
              "actor": "worker",
              "spec": 80,
              "ticket": 82,
              "at": "2026-09-10T13:13:00Z",
              "run": "repo-checks",
              "commit": "317cb6a9515df8c63fb4e94491aef90e91f8b265",
              "result": "met",
              "counts": {
                "passed": 3,
                "total": 3
              }
            }
          }, {
            "comment": 3180008208,
            "event": "ticket.passed",
            "at": "2026-09-10T13:15:00Z",
            "actor": "worker",
            "line": "ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.passed",
              "stage": "close",
              "actor": "worker",
              "spec": 80,
              "ticket": 82,
              "at": "2026-09-10T13:15:00Z",
              "commit": "317cb6a9515df8c63fb4e94491aef90e91f8b265",
              "branch": "issue-82",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "into": "main"
            }
          }, {
            "comment": 3180008209,
            "event": "ticket.landed",
            "at": "2026-09-10T13:20:00Z",
            "actor": "main",
            "line": "Landed issue-82 into main",
            "payload": {
              "v": 1,
              "event": "ticket.landed",
              "stage": "land",
              "actor": "main",
              "spec": 80,
              "ticket": 82,
              "at": "2026-09-10T13:20:00Z",
              "branch": "issue-82",
              "into": "main",
              "commit": "317cb6a9515df8c63fb4e94491aef90e91f8b265",
              "merge": "4a94090c080e3df504e2be5c2d85dc3158f3167b"
            }
          }]
        }, {
          "n": 83,
          "title": "断网渲染一遍",
          "state": "closed",
          "blocked": [82],
          "blockers": [{
            "number": 82,
            "title": "vendor 三个脚本",
            "state": "closed",
            "spec": 80,
            "readable": true,
            "blocker_hold": ""
          }],
          "blocker_hold": "",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 83,
            "events": [{
              "comment": 3180008300,
              "event": "worker.started",
              "at": "2026-09-10T13:21:00Z",
              "actor": "main",
              "line": "worker started on herdr: session w3c82, codex gpt-5.5 (high)"
            }, {
              "comment": 3180008301,
              "event": "ticket.claimed",
              "at": "2026-09-10T13:21:00Z",
              "actor": "worker",
              "line": "Claimed #83 on issue-83 as chancheuklap"
            }, {
              "comment": 3180008302,
              "event": "ticket.checked",
              "at": "2026-09-10T13:51:00Z",
              "actor": "worker",
              "line": "Own run on c5a3a7d338c7: ALL MET"
            }, {
              "comment": 3180008303,
              "event": "reviewer.started",
              "at": "2026-09-10T13:55:00Z",
              "actor": "worker",
              "line": "reviewer started on herdr: session w16e2, codex gpt-5.5 (medium)"
            }, {
              "comment": 3180008304,
              "event": "reviewer.reported",
              "at": "2026-09-10T14:04:00Z",
              "actor": "reviewer",
              "line": "REVIEW b3977aeaf8d429e7b937179e6db985a722712c64..c5a3a7d338c7853c337199105360198c015f5d49"
            }, {
              "comment": 3180008305,
              "event": "worker.decided",
              "at": "2026-09-10T14:08:00Z",
              "actor": "worker",
              "line": "DECISIONS"
            }, {
              "comment": 3180008306,
              "event": "ticket.checked",
              "at": "2026-09-10T14:18:00Z",
              "actor": "worker",
              "line": "Reverify on c5a3a7d338c7: ALL MET"
            }, {
              "comment": 3180008307,
              "event": "ticket.checked",
              "at": "2026-09-10T14:26:00Z",
              "actor": "worker",
              "line": "Repository checks on c5a3a7d338c7: 3/3 passed"
            }, {
              "comment": 3180008308,
              "event": "ticket.passed",
              "at": "2026-09-10T14:28:00Z",
              "actor": "worker",
              "line": "ALL MET"
            }, {
              "comment": 3180008309,
              "event": "ticket.landed",
              "at": "2026-09-10T14:36:00Z",
              "actor": "main",
              "line": "Landed issue-83 into main"
            }],
            "last": {
              "comment": 3180008309,
              "event": "ticket.landed",
              "at": "2026-09-10T14:36:00Z",
              "actor": "main",
              "line": "Landed issue-83 into main",
              "body": "Landed issue-83 into main\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.landed\",\"stage\":\"land\",\"actor\":\"main\",\"spec\":80,\"ticket\":83,\"at\":\"2026-09-10T14:36:00Z\",\"branch\":\"issue-83\",\"into\":\"main\",\"commit\":\"c5a3a7d338c7853c337199105360198c015f5d49\",\"merge\":\"28ba539d9256249ce85a4b6d5fa58bb80f15ff53\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.landed",
                "stage": "land",
                "actor": "main",
                "spec": 80,
                "ticket": 83,
                "at": "2026-09-10T14:36:00Z",
                "branch": "issue-83",
                "into": "main",
                "commit": "c5a3a7d338c7853c337199105360198c015f5d49",
                "merge": "28ba539d9256249ce85a4b6d5fa58bb80f15ff53"
              }
            },
            "unreadable": [],
            "claimed": false,
            "claimant": "chancheuklap",
            "refused": null,
            "passed": true,
            "returned": false,
            "outcome": {
              "comment": 3180008308,
              "event": "ticket.passed",
              "at": "2026-09-10T14:28:00Z",
              "actor": "worker",
              "line": "ALL MET",
              "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":80,\"ticket\":83,\"at\":\"2026-09-10T14:28:00Z\",\"commit\":\"c5a3a7d338c7853c337199105360198c015f5d49\",\"branch\":\"issue-83\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"main\"} -->\n",
              "payload": {
                "v": 1,
                "event": "ticket.passed",
                "stage": "close",
                "actor": "worker",
                "spec": 80,
                "ticket": 83,
                "at": "2026-09-10T14:28:00Z",
                "commit": "c5a3a7d338c7853c337199105360198c015f5d49",
                "branch": "issue-83",
                "counts": {
                  "met": 4,
                  "unmet": 0,
                  "abandoned": 0,
                  "total": 4
                },
                "into": "main"
              }
            },
            "landed": true,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": {
              "comment": 3180008304,
              "event": "reviewer.reported",
              "at": "2026-09-10T14:04:00Z",
              "actor": "reviewer",
              "line": "REVIEW b3977aeaf8d429e7b937179e6db985a722712c64..c5a3a7d338c7853c337199105360198c015f5d49",
              "body": "REVIEW b3977aeaf8d429e7b937179e6db985a722712c64..c5a3a7d338c7853c337199105360198c015f5d49\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":80,\"ticket\":83,\"at\":\"2026-09-10T14:04:00Z\",\"base\":\"b3977aeaf8d429e7b937179e6db985a722712c64\",\"head\":\"c5a3a7d338c7853c337199105360198c015f5d49\"} -->\n",
              "payload": {
                "v": 1,
                "event": "reviewer.reported",
                "stage": "review",
                "actor": "reviewer",
                "spec": 80,
                "ticket": 83,
                "at": "2026-09-10T14:04:00Z",
                "base": "b3977aeaf8d429e7b937179e6db985a722712c64",
                "head": "c5a3a7d338c7853c337199105360198c015f5d49"
              }
            },
            "decided": 1,
            "results": {
              "worker": {
                "comment": 3180008308,
                "event": "ticket.passed",
                "at": "2026-09-10T14:28:00Z",
                "actor": "worker",
                "line": "ALL MET",
                "body": "ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":80,\"ticket\":83,\"at\":\"2026-09-10T14:28:00Z\",\"commit\":\"c5a3a7d338c7853c337199105360198c015f5d49\",\"branch\":\"issue-83\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"into\":\"main\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.passed",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 80,
                  "ticket": 83,
                  "at": "2026-09-10T14:28:00Z",
                  "commit": "c5a3a7d338c7853c337199105360198c015f5d49",
                  "branch": "issue-83",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "into": "main"
                }
              },
              "reviewer": {
                "comment": 3180008304,
                "event": "reviewer.reported",
                "at": "2026-09-10T14:04:00Z",
                "actor": "reviewer",
                "line": "REVIEW b3977aeaf8d429e7b937179e6db985a722712c64..c5a3a7d338c7853c337199105360198c015f5d49",
                "body": "REVIEW b3977aeaf8d429e7b937179e6db985a722712c64..c5a3a7d338c7853c337199105360198c015f5d49\n\n<!-- mmw {\"v\":1,\"event\":\"reviewer.reported\",\"stage\":\"review\",\"actor\":\"reviewer\",\"spec\":80,\"ticket\":83,\"at\":\"2026-09-10T14:04:00Z\",\"base\":\"b3977aeaf8d429e7b937179e6db985a722712c64\",\"head\":\"c5a3a7d338c7853c337199105360198c015f5d49\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "reviewer.reported",
                  "stage": "review",
                  "actor": "reviewer",
                  "spec": 80,
                  "ticket": 83,
                  "at": "2026-09-10T14:04:00Z",
                  "base": "b3977aeaf8d429e7b937179e6db985a722712c64",
                  "head": "c5a3a7d338c7853c337199105360198c015f5d49"
                }
              }
            },
            "checks": {
              "self": {
                "comment": 3180008302,
                "event": "ticket.checked",
                "at": "2026-09-10T13:51:00Z",
                "actor": "worker",
                "line": "Own run on c5a3a7d338c7: ALL MET",
                "body": "Own run on c5a3a7d338c7: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"work\",\"actor\":\"worker\",\"spec\":80,\"ticket\":83,\"at\":\"2026-09-10T13:51:00Z\",\"run\":\"self\",\"commit\":\"c5a3a7d338c7853c337199105360198c015f5d49\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"8b830f2d2af55bba1bd2a3918a52f531d7e540cdccd7181aa76b7c164d007536\",\"slot\":1,\"port_base\":21100,\"outside_owns\":[]} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "work",
                  "actor": "worker",
                  "spec": 80,
                  "ticket": 83,
                  "at": "2026-09-10T13:51:00Z",
                  "run": "self",
                  "commit": "c5a3a7d338c7853c337199105360198c015f5d49",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "8b830f2d2af55bba1bd2a3918a52f531d7e540cdccd7181aa76b7c164d007536",
                  "slot": 1,
                  "port_base": 21100,
                  "outside_owns": []
                }
              },
              "reverify": {
                "comment": 3180008306,
                "event": "ticket.checked",
                "at": "2026-09-10T14:18:00Z",
                "actor": "worker",
                "line": "Reverify on c5a3a7d338c7: ALL MET",
                "body": "Reverify on c5a3a7d338c7: ALL MET\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"verify\",\"actor\":\"worker\",\"spec\":80,\"ticket\":83,\"at\":\"2026-09-10T14:18:00Z\",\"run\":\"reverify\",\"commit\":\"c5a3a7d338c7853c337199105360198c015f5d49\",\"result\":\"met\",\"counts\":{\"met\":4,\"unmet\":0,\"abandoned\":0,\"total\":4},\"criteria\":[{\"id\":\"AC1\",\"met\":true,\"evidence\":\"ac1.log\"},{\"id\":\"AC2\",\"met\":true,\"evidence\":\"ac2.log\"},{\"id\":\"AC3\",\"met\":true,\"evidence\":\"ac3.log\"},{\"id\":\"AC4\",\"met\":true,\"evidence\":\"ac4.log\"}],\"failed\":[],\"shape\":\"8b830f2d2af55bba1bd2a3918a52f531d7e540cdccd7181aa76b7c164d007536\"} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "verify",
                  "actor": "worker",
                  "spec": 80,
                  "ticket": 83,
                  "at": "2026-09-10T14:18:00Z",
                  "run": "reverify",
                  "commit": "c5a3a7d338c7853c337199105360198c015f5d49",
                  "result": "met",
                  "counts": {
                    "met": 4,
                    "unmet": 0,
                    "abandoned": 0,
                    "total": 4
                  },
                  "criteria": [{
                    "id": "AC1",
                    "met": true,
                    "evidence": "ac1.log"
                  }, {
                    "id": "AC2",
                    "met": true,
                    "evidence": "ac2.log"
                  }, {
                    "id": "AC3",
                    "met": true,
                    "evidence": "ac3.log"
                  }, {
                    "id": "AC4",
                    "met": true,
                    "evidence": "ac4.log"
                  }],
                  "failed": [],
                  "shape": "8b830f2d2af55bba1bd2a3918a52f531d7e540cdccd7181aa76b7c164d007536"
                }
              },
              "repo-checks": {
                "comment": 3180008307,
                "event": "ticket.checked",
                "at": "2026-09-10T14:26:00Z",
                "actor": "worker",
                "line": "Repository checks on c5a3a7d338c7: 3/3 passed",
                "body": "Repository checks on c5a3a7d338c7: 3/3 passed\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.checked\",\"stage\":\"close\",\"actor\":\"worker\",\"spec\":80,\"ticket\":83,\"at\":\"2026-09-10T14:26:00Z\",\"run\":\"repo-checks\",\"commit\":\"c5a3a7d338c7853c337199105360198c015f5d49\",\"result\":\"met\",\"counts\":{\"passed\":3,\"total\":3}} -->\n",
                "payload": {
                  "v": 1,
                  "event": "ticket.checked",
                  "stage": "close",
                  "actor": "worker",
                  "spec": 80,
                  "ticket": 83,
                  "at": "2026-09-10T14:26:00Z",
                  "run": "repo-checks",
                  "commit": "c5a3a7d338c7853c337199105360198c015f5d49",
                  "result": "met",
                  "counts": {
                    "passed": 3,
                    "total": 3
                  }
                }
              },
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [{
              "kind": "worker",
              "session": "w3c82",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/83-work",
              "branch": "issue-83",
              "base": "b3977aeaf8d429e7b937179e6db985a722712c64",
              "into": "main",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T13:21:00Z",
              "comment": 3180008300,
              "live": false,
              "ended_by": "ticket.landed"
            }, {
              "kind": "reviewer",
              "session": "w16e2",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/83-work",
              "branch": "issue-83",
              "base": "b3977aeaf8d429e7b937179e6db985a722712c64",
              "into": null,
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T13:55:00Z",
              "comment": 3180008303,
              "live": false,
              "ended_by": "reviewer.reported"
            }],
            "claim_hold": false,
            "ever_held": true,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": {
              "kind": "worker",
              "session": "w3c82",
              "runner": "herdr",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/83-work",
              "branch": "issue-83",
              "base": "b3977aeaf8d429e7b937179e6db985a722712c64",
              "into": "main",
              "machine": "cheuk-mbp",
              "started_at": "2026-09-10T13:21:00Z",
              "comment": 3180008300,
              "live": false,
              "ended_by": "ticket.landed"
            },
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": true
          },
          "events": [{
            "comment": 3180008300,
            "event": "worker.started",
            "at": "2026-09-10T13:21:00Z",
            "actor": "main",
            "line": "worker started on herdr: session w3c82, codex gpt-5.5 (high)",
            "payload": {
              "v": 1,
              "event": "worker.started",
              "stage": "dispatch",
              "actor": "main",
              "spec": 80,
              "ticket": 83,
              "at": "2026-09-10T13:21:00Z",
              "session": "w3c82",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "high",
              "grade": "senior-worker",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/83-work",
              "branch": "issue-83",
              "base": "b3977aeaf8d429e7b937179e6db985a722712c64",
              "into": "main"
            }
          }, {
            "comment": 3180008301,
            "event": "ticket.claimed",
            "at": "2026-09-10T13:21:00Z",
            "actor": "worker",
            "line": "Claimed #83 on issue-83 as chancheuklap",
            "payload": {
              "v": 1,
              "event": "ticket.claimed",
              "stage": "intake",
              "actor": "worker",
              "spec": 80,
              "ticket": 83,
              "at": "2026-09-10T13:21:00Z",
              "login": "chancheuklap",
              "branch": "issue-83",
              "commit": "b3977aeaf8d429e7b937179e6db985a722712c64"
            }
          }, {
            "comment": 3180008302,
            "event": "ticket.checked",
            "at": "2026-09-10T13:51:00Z",
            "actor": "worker",
            "line": "Own run on c5a3a7d338c7: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "work",
              "actor": "worker",
              "spec": 80,
              "ticket": 83,
              "at": "2026-09-10T13:51:00Z",
              "run": "self",
              "commit": "c5a3a7d338c7853c337199105360198c015f5d49",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "8b830f2d2af55bba1bd2a3918a52f531d7e540cdccd7181aa76b7c164d007536",
              "slot": 1,
              "port_base": 21100,
              "outside_owns": []
            }
          }, {
            "comment": 3180008303,
            "event": "reviewer.started",
            "at": "2026-09-10T13:55:00Z",
            "actor": "worker",
            "line": "reviewer started on herdr: session w16e2, codex gpt-5.5 (medium)",
            "payload": {
              "v": 1,
              "event": "reviewer.started",
              "stage": "review",
              "actor": "worker",
              "spec": 80,
              "ticket": 83,
              "at": "2026-09-10T13:55:00Z",
              "session": "w16e2",
              "runner": "herdr",
              "machine": "cheuk-mbp",
              "host": "codex",
              "model": "gpt-5.5",
              "effort": "medium",
              "grade": "reviewer",
              "worktree": "/Users/cheuklapchan/multi-model-workflow/.worktrees/83-work",
              "branch": "issue-83",
              "base": "b3977aeaf8d429e7b937179e6db985a722712c64"
            }
          }, {
            "comment": 3180008304,
            "event": "reviewer.reported",
            "at": "2026-09-10T14:04:00Z",
            "actor": "reviewer",
            "line": "REVIEW b3977aeaf8d429e7b937179e6db985a722712c64..c5a3a7d338c7853c337199105360198c015f5d49",
            "payload": {
              "v": 1,
              "event": "reviewer.reported",
              "stage": "review",
              "actor": "reviewer",
              "spec": 80,
              "ticket": 83,
              "at": "2026-09-10T14:04:00Z",
              "base": "b3977aeaf8d429e7b937179e6db985a722712c64",
              "head": "c5a3a7d338c7853c337199105360198c015f5d49"
            }
          }, {
            "comment": 3180008305,
            "event": "worker.decided",
            "at": "2026-09-10T14:08:00Z",
            "actor": "worker",
            "line": "DECISIONS",
            "payload": {
              "v": 1,
              "event": "worker.decided",
              "stage": "work",
              "actor": "worker",
              "spec": 80,
              "ticket": 83,
              "at": "2026-09-10T14:08:00Z"
            }
          }, {
            "comment": 3180008306,
            "event": "ticket.checked",
            "at": "2026-09-10T14:18:00Z",
            "actor": "worker",
            "line": "Reverify on c5a3a7d338c7: ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "verify",
              "actor": "worker",
              "spec": 80,
              "ticket": 83,
              "at": "2026-09-10T14:18:00Z",
              "run": "reverify",
              "commit": "c5a3a7d338c7853c337199105360198c015f5d49",
              "result": "met",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "criteria": [{
                "id": "AC1",
                "met": true,
                "evidence": "ac1.log"
              }, {
                "id": "AC2",
                "met": true,
                "evidence": "ac2.log"
              }, {
                "id": "AC3",
                "met": true,
                "evidence": "ac3.log"
              }, {
                "id": "AC4",
                "met": true,
                "evidence": "ac4.log"
              }],
              "failed": [],
              "shape": "8b830f2d2af55bba1bd2a3918a52f531d7e540cdccd7181aa76b7c164d007536"
            }
          }, {
            "comment": 3180008307,
            "event": "ticket.checked",
            "at": "2026-09-10T14:26:00Z",
            "actor": "worker",
            "line": "Repository checks on c5a3a7d338c7: 3/3 passed",
            "payload": {
              "v": 1,
              "event": "ticket.checked",
              "stage": "close",
              "actor": "worker",
              "spec": 80,
              "ticket": 83,
              "at": "2026-09-10T14:26:00Z",
              "run": "repo-checks",
              "commit": "c5a3a7d338c7853c337199105360198c015f5d49",
              "result": "met",
              "counts": {
                "passed": 3,
                "total": 3
              }
            }
          }, {
            "comment": 3180008308,
            "event": "ticket.passed",
            "at": "2026-09-10T14:28:00Z",
            "actor": "worker",
            "line": "ALL MET",
            "payload": {
              "v": 1,
              "event": "ticket.passed",
              "stage": "close",
              "actor": "worker",
              "spec": 80,
              "ticket": 83,
              "at": "2026-09-10T14:28:00Z",
              "commit": "c5a3a7d338c7853c337199105360198c015f5d49",
              "branch": "issue-83",
              "counts": {
                "met": 4,
                "unmet": 0,
                "abandoned": 0,
                "total": 4
              },
              "into": "main"
            }
          }, {
            "comment": 3180008309,
            "event": "ticket.landed",
            "at": "2026-09-10T14:36:00Z",
            "actor": "main",
            "line": "Landed issue-83 into main",
            "payload": {
              "v": 1,
              "event": "ticket.landed",
              "stage": "land",
              "actor": "main",
              "spec": 80,
              "ticket": 83,
              "at": "2026-09-10T14:36:00Z",
              "branch": "issue-83",
              "into": "main",
              "commit": "c5a3a7d338c7853c337199105360198c015f5d49",
              "merge": "28ba539d9256249ce85a4b6d5fa58bb80f15ff53"
            }
          }]
        }]
      }]
    }, {
      "n": 101,
      "kind": "map",
      "title": "子 issue 五种改名",
      "state": "open",
      "decisions": [],
      "specs": [{
        "n": 108,
        "title": "child 用新名字",
        "tickets": [{
          "n": 109,
          "title": "events.py 换成新名",
          "state": "open",
          "blocked": [],
          "blockers": [],
          "blocker_hold": "open",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 109,
            "events": [],
            "last": null,
            "unreadable": [],
            "claimed": false,
            "claimant": null,
            "refused": null,
            "passed": false,
            "returned": false,
            "outcome": null,
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": null,
            "decided": 0,
            "results": {
              "worker": null,
              "reviewer": null
            },
            "checks": {
              "self": null,
              "reverify": null,
              "repo-checks": null,
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [],
            "claim_hold": false,
            "ever_held": false,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": null,
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": false
          },
          "events": []
        }, {
          "n": 110,
          "title": "verify-ticket 读新名",
          "state": "open",
          "blocked": [109],
          "blockers": [{
            "number": 109,
            "title": "events.py 换成新名",
            "state": "open",
            "spec": 108,
            "readable": true,
            "blocker_hold": "open"
          }],
          "blocker_hold": "open",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 110,
            "events": [],
            "last": null,
            "unreadable": [],
            "claimed": false,
            "claimant": null,
            "refused": null,
            "passed": false,
            "returned": false,
            "outcome": null,
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": null,
            "decided": 0,
            "results": {
              "worker": null,
              "reviewer": null
            },
            "checks": {
              "self": null,
              "reverify": null,
              "repo-checks": null,
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [],
            "claim_hold": false,
            "ever_held": false,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": null,
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": false
          },
          "events": []
        }, {
          "n": 111,
          "title": "文档跟着改",
          "state": "open",
          "blocked": [109],
          "blockers": [{
            "number": 109,
            "title": "events.py 换成新名",
            "state": "open",
            "spec": 108,
            "readable": true,
            "blocker_hold": "open"
          }],
          "blocker_hold": "open",
          "closeout": null,
          "children": [],
          "fold": {
            "issue": 111,
            "events": [],
            "last": null,
            "unreadable": [],
            "claimed": false,
            "claimant": null,
            "refused": null,
            "passed": false,
            "returned": false,
            "outcome": null,
            "landed": false,
            "released": null,
            "regressed": false,
            "bounced": false,
            "suspended": false,
            "review": null,
            "decided": 0,
            "results": {
              "worker": null,
              "reviewer": null
            },
            "checks": {
              "self": null,
              "reverify": null,
              "repo-checks": null,
              "baseline": null
            },
            "waiting": null,
            "slot": null,
            "touched": [],
            "children": {},
            "sessions": [],
            "claim_hold": false,
            "ever_held": false,
            "spec_opened": false,
            "spec_closed": false,
            "spec_retroed": null,
            "spec_merged": false,
            "worker": null,
            "live_workers": [],
            "holders": [],
            "held": false,
            "hold_ended": false
          },
          "events": []
        }]
      }]
    }],
    "repo": "chancheuklap/multi-model-workflow",
    "read_at": "2026-09-10T23:39:00Z"
  }
};
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/task-board/data/board-morning.js", error: String((e && e.message) || e) }); }

// ui_kits/task-board/data/settings.js
try { (() => {
window.SETTINGS_SCENES = {
  "mine": {
    "name": "本机配置合法",
    "payload": {
      "version": 12,
      "runner": "orca",
      "rows": {
        "junior-worker": {
          "host": "grok",
          "model": "grok 4.6",
          "effort": "high"
        },
        "senior-worker": {
          "host": "codex",
          "model": "gpt 5.6 sol",
          "effort": "high"
        },
        "reviewer": {
          "host": "claude",
          "model": "opus 5",
          "effort": "high"
        },
        "advisor": {
          "host": "claude",
          "model": "fable 5.1",
          "effort": "medium"
        }
      },
      "hosts": [{
        "name": "cursor",
        "binary": "cursor-agent",
        "cli": true,
        "paseo": true
      }, {
        "name": "grok",
        "binary": "grok",
        "cli": true,
        "paseo": true
      }, {
        "name": "claude",
        "binary": "claude",
        "cli": true,
        "paseo": true
      }, {
        "name": "codex",
        "binary": "codex",
        "cli": true,
        "paseo": true
      }, {
        "name": "pi",
        "binary": "pi",
        "cli": false,
        "paseo": true
      }],
      "runners": ["herdr", "orca", "paseo", "auto"],
      "scan": {
        "source": "cli",
        "scanned_at": "2026-09-10T23:02:00Z",
        "scanning": false,
        "hosts": {
          "cursor": {
            "state": "ok",
            "offered": [{
              "model": "auto",
              "efforts": ["—"]
            }, {
              "model": "composer 2.5",
              "efforts": ["—"]
            }, {
              "model": "gemini 3.8 flash",
              "efforts": ["medium"]
            }, {
              "model": "gpt-5.6 sol",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6 fast",
              "efforts": ["high"]
            }, {
              "model": "kimi k3",
              "efforts": ["high"]
            }, {
              "model": "opus 5",
              "efforts": ["medium", "high"]
            }, {
              "model": "sonnet 5",
              "efforts": ["high"]
            }]
          },
          "grok": {
            "state": "ok",
            "offered": [{
              "model": "grok 4.6",
              "efforts": ["low", "medium", "high", "xhigh"]
            }, {
              "model": "grok 4.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "claude": {
            "state": "ok",
            "offered": [{
              "model": "opus 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "sonnet 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5.1",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }]
          },
          "codex": {
            "state": "ok",
            "offered": [{
              "model": "gpt 6 astra",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 sol",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 luna",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt 5.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "pi": {
            "state": "ok",
            "offered": [{
              "model": "deepseek-v4-pro",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "k3",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "grok-4.6",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt-5.6-sol",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }]
          }
        }
      }
    },
    "page": {}
  },
  "fresh": {
    "name": "新机器 · 初始值里的 grok 没装",
    "payload": {
      "version": 12,
      "runner": "orca",
      "rows": {
        "junior-worker": {
          "host": "grok",
          "model": "grok 4.6",
          "effort": "high"
        },
        "senior-worker": {
          "host": "codex",
          "model": "gpt 5.6 sol",
          "effort": "high"
        },
        "reviewer": {
          "host": "claude",
          "model": "opus 5",
          "effort": "high"
        },
        "advisor": {
          "host": "claude",
          "model": "fable 5.1",
          "effort": "medium"
        }
      },
      "hosts": [{
        "name": "cursor",
        "binary": "cursor-agent",
        "cli": true,
        "paseo": true
      }, {
        "name": "grok",
        "binary": "grok",
        "cli": true,
        "paseo": true
      }, {
        "name": "claude",
        "binary": "claude",
        "cli": true,
        "paseo": true
      }, {
        "name": "codex",
        "binary": "codex",
        "cli": true,
        "paseo": true
      }, {
        "name": "pi",
        "binary": "pi",
        "cli": false,
        "paseo": true
      }],
      "runners": ["herdr", "orca", "paseo", "auto"],
      "scan": {
        "source": "cli",
        "scanned_at": "2026-09-10T23:02:00Z",
        "scanning": false,
        "hosts": {
          "cursor": {
            "state": "ok",
            "offered": [{
              "model": "auto",
              "efforts": ["—"]
            }, {
              "model": "composer 2.5",
              "efforts": ["—"]
            }, {
              "model": "gemini 3.8 flash",
              "efforts": ["medium"]
            }, {
              "model": "gpt-5.6 sol",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6 fast",
              "efforts": ["high"]
            }, {
              "model": "kimi k3",
              "efforts": ["high"]
            }, {
              "model": "opus 5",
              "efforts": ["medium", "high"]
            }, {
              "model": "sonnet 5",
              "efforts": ["high"]
            }]
          },
          "grok": {
            "state": "missing",
            "offered": []
          },
          "claude": {
            "state": "ok",
            "offered": [{
              "model": "opus 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "sonnet 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5.1",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }]
          },
          "codex": {
            "state": "ok",
            "offered": [{
              "model": "gpt 6 astra",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 sol",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 luna",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt 5.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "pi": {
            "state": "ok",
            "offered": [{
              "model": "deepseek-v4-pro",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "k3",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "grok-4.6",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt-5.6-sol",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }]
          }
        }
      }
    },
    "page": {}
  },
  "retired": {
    "name": "选中的 model 本机已经没有",
    "payload": {
      "version": 12,
      "runner": "orca",
      "rows": {
        "junior-worker": {
          "host": "grok",
          "model": "grok 4.6",
          "effort": "high"
        },
        "senior-worker": {
          "host": "codex",
          "model": "gpt 5.6 sol",
          "effort": "high"
        },
        "reviewer": {
          "host": "claude",
          "model": "opus 5",
          "effort": "high"
        },
        "advisor": {
          "host": "claude",
          "model": "fable 5",
          "effort": "medium"
        }
      },
      "hosts": [{
        "name": "cursor",
        "binary": "cursor-agent",
        "cli": true,
        "paseo": true
      }, {
        "name": "grok",
        "binary": "grok",
        "cli": true,
        "paseo": true
      }, {
        "name": "claude",
        "binary": "claude",
        "cli": true,
        "paseo": true
      }, {
        "name": "codex",
        "binary": "codex",
        "cli": true,
        "paseo": true
      }, {
        "name": "pi",
        "binary": "pi",
        "cli": false,
        "paseo": true
      }],
      "runners": ["herdr", "orca", "paseo", "auto"],
      "scan": {
        "source": "cli",
        "scanned_at": "2026-09-10T23:30:00Z",
        "scanning": false,
        "hosts": {
          "cursor": {
            "state": "ok",
            "offered": [{
              "model": "auto",
              "efforts": ["—"]
            }, {
              "model": "composer 2.5",
              "efforts": ["—"]
            }, {
              "model": "gemini 3.8 flash",
              "efforts": ["medium"]
            }, {
              "model": "gpt-5.6 sol",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6 fast",
              "efforts": ["high"]
            }, {
              "model": "kimi k3",
              "efforts": ["high"]
            }, {
              "model": "opus 5",
              "efforts": ["medium", "high"]
            }, {
              "model": "sonnet 5",
              "efforts": ["high"]
            }]
          },
          "grok": {
            "state": "ok",
            "offered": [{
              "model": "grok 4.6",
              "efforts": ["low", "medium", "high", "xhigh"]
            }, {
              "model": "grok 4.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "claude": {
            "state": "ok",
            "offered": [{
              "model": "opus 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "sonnet 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5.1",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }]
          },
          "codex": {
            "state": "ok",
            "offered": [{
              "model": "gpt 6 astra",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 sol",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 luna",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt 5.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "pi": {
            "state": "ok",
            "offered": [{
              "model": "deepseek-v4-pro",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "k3",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "grok-4.6",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt-5.6-sol",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }]
          }
        }
      }
    },
    "page": {}
  },
  "paseo-off": {
    "name": "runner 是 paseo · Paseo 没开",
    "payload": {
      "version": 12,
      "runner": "paseo",
      "rows": {
        "junior-worker": {
          "host": "grok",
          "model": "grok 4.6",
          "effort": "high"
        },
        "senior-worker": {
          "host": "codex",
          "model": "gpt 5.6 sol",
          "effort": "high"
        },
        "reviewer": {
          "host": "claude",
          "model": "opus 5",
          "effort": "high"
        },
        "advisor": {
          "host": "claude",
          "model": "fable 5.1",
          "effort": "medium"
        }
      },
      "hosts": [{
        "name": "cursor",
        "binary": "cursor-agent",
        "cli": true,
        "paseo": true
      }, {
        "name": "grok",
        "binary": "grok",
        "cli": true,
        "paseo": true
      }, {
        "name": "claude",
        "binary": "claude",
        "cli": true,
        "paseo": true
      }, {
        "name": "codex",
        "binary": "codex",
        "cli": true,
        "paseo": true
      }, {
        "name": "pi",
        "binary": "pi",
        "cli": false,
        "paseo": true
      }],
      "runners": ["herdr", "orca", "paseo", "auto"],
      "scan": {
        "source": "paseo",
        "scanned_at": "2026-09-10T23:02:00Z",
        "scanning": false,
        "hosts": {
          "cursor": {
            "state": "down",
            "offered": []
          },
          "grok": {
            "state": "down",
            "offered": []
          },
          "claude": {
            "state": "down",
            "offered": []
          },
          "codex": {
            "state": "down",
            "offered": []
          },
          "pi": {
            "state": "down",
            "offered": []
          }
        }
      }
    },
    "page": {}
  },
  "changed": {
    "name": "打开后被别处改过",
    "payload": {
      "version": 12,
      "runner": "orca",
      "rows": {
        "junior-worker": {
          "host": "grok",
          "model": "grok 4.6",
          "effort": "high"
        },
        "senior-worker": {
          "host": "codex",
          "model": "gpt 5.6 sol",
          "effort": "high"
        },
        "reviewer": {
          "host": "claude",
          "model": "opus 5",
          "effort": "high"
        },
        "advisor": {
          "host": "claude",
          "model": "fable 5.1",
          "effort": "medium"
        }
      },
      "hosts": [{
        "name": "cursor",
        "binary": "cursor-agent",
        "cli": true,
        "paseo": true
      }, {
        "name": "grok",
        "binary": "grok",
        "cli": true,
        "paseo": true
      }, {
        "name": "claude",
        "binary": "claude",
        "cli": true,
        "paseo": true
      }, {
        "name": "codex",
        "binary": "codex",
        "cli": true,
        "paseo": true
      }, {
        "name": "pi",
        "binary": "pi",
        "cli": false,
        "paseo": true
      }],
      "runners": ["herdr", "orca", "paseo", "auto"],
      "scan": {
        "source": "cli",
        "scanned_at": "2026-09-10T23:02:00Z",
        "scanning": false,
        "hosts": {
          "cursor": {
            "state": "ok",
            "offered": [{
              "model": "auto",
              "efforts": ["—"]
            }, {
              "model": "composer 2.5",
              "efforts": ["—"]
            }, {
              "model": "gemini 3.8 flash",
              "efforts": ["medium"]
            }, {
              "model": "gpt-5.6 sol",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6 fast",
              "efforts": ["high"]
            }, {
              "model": "kimi k3",
              "efforts": ["high"]
            }, {
              "model": "opus 5",
              "efforts": ["medium", "high"]
            }, {
              "model": "sonnet 5",
              "efforts": ["high"]
            }]
          },
          "grok": {
            "state": "ok",
            "offered": [{
              "model": "grok 4.6",
              "efforts": ["low", "medium", "high", "xhigh"]
            }, {
              "model": "grok 4.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "claude": {
            "state": "ok",
            "offered": [{
              "model": "opus 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "sonnet 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5.1",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }]
          },
          "codex": {
            "state": "ok",
            "offered": [{
              "model": "gpt 6 astra",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 sol",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 luna",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt 5.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "pi": {
            "state": "ok",
            "offered": [{
              "model": "deepseek-v4-pro",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "k3",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "grok-4.6",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt-5.6-sol",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }]
          }
        }
      }
    },
    "page": {
      "edit": [["reviewer", "effort", "xhigh"]],
      "refused": 1,
      "modifiedAt": "2026-09-10T23:44:00Z"
    }
  },
  "edited": {
    "name": "改了几处，还没保存",
    "payload": {
      "version": 12,
      "runner": "orca",
      "rows": {
        "junior-worker": {
          "host": "grok",
          "model": "grok 4.6",
          "effort": "high"
        },
        "senior-worker": {
          "host": "codex",
          "model": "gpt 5.6 sol",
          "effort": "high"
        },
        "reviewer": {
          "host": "claude",
          "model": "opus 5",
          "effort": "high"
        },
        "advisor": {
          "host": "claude",
          "model": "fable 5.1",
          "effort": "medium"
        }
      },
      "hosts": [{
        "name": "cursor",
        "binary": "cursor-agent",
        "cli": true,
        "paseo": true
      }, {
        "name": "grok",
        "binary": "grok",
        "cli": true,
        "paseo": true
      }, {
        "name": "claude",
        "binary": "claude",
        "cli": true,
        "paseo": true
      }, {
        "name": "codex",
        "binary": "codex",
        "cli": true,
        "paseo": true
      }, {
        "name": "pi",
        "binary": "pi",
        "cli": false,
        "paseo": true
      }],
      "runners": ["herdr", "orca", "paseo", "auto"],
      "scan": {
        "source": "cli",
        "scanned_at": "2026-09-10T23:02:00Z",
        "scanning": false,
        "hosts": {
          "cursor": {
            "state": "ok",
            "offered": [{
              "model": "auto",
              "efforts": ["—"]
            }, {
              "model": "composer 2.5",
              "efforts": ["—"]
            }, {
              "model": "gemini 3.8 flash",
              "efforts": ["medium"]
            }, {
              "model": "gpt-5.6 sol",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6 fast",
              "efforts": ["high"]
            }, {
              "model": "kimi k3",
              "efforts": ["high"]
            }, {
              "model": "opus 5",
              "efforts": ["medium", "high"]
            }, {
              "model": "sonnet 5",
              "efforts": ["high"]
            }]
          },
          "grok": {
            "state": "ok",
            "offered": [{
              "model": "grok 4.6",
              "efforts": ["low", "medium", "high", "xhigh"]
            }, {
              "model": "grok 4.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "claude": {
            "state": "ok",
            "offered": [{
              "model": "opus 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "sonnet 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5.1",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }]
          },
          "codex": {
            "state": "ok",
            "offered": [{
              "model": "gpt 6 astra",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 sol",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 luna",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt 5.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "pi": {
            "state": "ok",
            "offered": [{
              "model": "deepseek-v4-pro",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "k3",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "grok-4.6",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt-5.6-sol",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }]
          }
        }
      }
    },
    "page": {
      "edit": [["senior-worker", "host", "claude"], ["senior-worker", "model", "opus 5"], ["senior-worker", "effort", "high"]]
    }
  },
  "incomplete": {
    "name": "换了 host，model 空着等选",
    "payload": {
      "version": 12,
      "runner": "orca",
      "rows": {
        "junior-worker": {
          "host": "grok",
          "model": "grok 4.6",
          "effort": "high"
        },
        "senior-worker": {
          "host": "codex",
          "model": "gpt 5.6 sol",
          "effort": "high"
        },
        "reviewer": {
          "host": "claude",
          "model": "opus 5",
          "effort": "high"
        },
        "advisor": {
          "host": "claude",
          "model": "fable 5.1",
          "effort": "medium"
        }
      },
      "hosts": [{
        "name": "cursor",
        "binary": "cursor-agent",
        "cli": true,
        "paseo": true
      }, {
        "name": "grok",
        "binary": "grok",
        "cli": true,
        "paseo": true
      }, {
        "name": "claude",
        "binary": "claude",
        "cli": true,
        "paseo": true
      }, {
        "name": "codex",
        "binary": "codex",
        "cli": true,
        "paseo": true
      }, {
        "name": "pi",
        "binary": "pi",
        "cli": false,
        "paseo": true
      }],
      "runners": ["herdr", "orca", "paseo", "auto"],
      "scan": {
        "source": "cli",
        "scanned_at": "2026-09-10T23:02:00Z",
        "scanning": false,
        "hosts": {
          "cursor": {
            "state": "ok",
            "offered": [{
              "model": "auto",
              "efforts": ["—"]
            }, {
              "model": "composer 2.5",
              "efforts": ["—"]
            }, {
              "model": "gemini 3.8 flash",
              "efforts": ["medium"]
            }, {
              "model": "gpt-5.6 sol",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6 fast",
              "efforts": ["high"]
            }, {
              "model": "kimi k3",
              "efforts": ["high"]
            }, {
              "model": "opus 5",
              "efforts": ["medium", "high"]
            }, {
              "model": "sonnet 5",
              "efforts": ["high"]
            }]
          },
          "grok": {
            "state": "ok",
            "offered": [{
              "model": "grok 4.6",
              "efforts": ["low", "medium", "high", "xhigh"]
            }, {
              "model": "grok 4.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "claude": {
            "state": "ok",
            "offered": [{
              "model": "opus 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "sonnet 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5.1",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }]
          },
          "codex": {
            "state": "ok",
            "offered": [{
              "model": "gpt 6 astra",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 sol",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 luna",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt 5.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "pi": {
            "state": "ok",
            "offered": [{
              "model": "deepseek-v4-pro",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "k3",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "grok-4.6",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt-5.6-sol",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }]
          }
        }
      }
    },
    "page": {
      "edit": [["reviewer", "host", "codex"]]
    }
  },
  "scanning": {
    "name": "正在重新扫描",
    "payload": {
      "version": 12,
      "runner": "orca",
      "rows": {
        "junior-worker": {
          "host": "grok",
          "model": "grok 4.6",
          "effort": "high"
        },
        "senior-worker": {
          "host": "codex",
          "model": "gpt 5.6 sol",
          "effort": "high"
        },
        "reviewer": {
          "host": "claude",
          "model": "opus 5",
          "effort": "high"
        },
        "advisor": {
          "host": "claude",
          "model": "fable 5.1",
          "effort": "medium"
        }
      },
      "hosts": [{
        "name": "cursor",
        "binary": "cursor-agent",
        "cli": true,
        "paseo": true
      }, {
        "name": "grok",
        "binary": "grok",
        "cli": true,
        "paseo": true
      }, {
        "name": "claude",
        "binary": "claude",
        "cli": true,
        "paseo": true
      }, {
        "name": "codex",
        "binary": "codex",
        "cli": true,
        "paseo": true
      }, {
        "name": "pi",
        "binary": "pi",
        "cli": false,
        "paseo": true
      }],
      "runners": ["herdr", "orca", "paseo", "auto"],
      "scan": {
        "source": "cli",
        "scanned_at": "2026-09-10T23:02:00Z",
        "scanning": false,
        "hosts": {
          "cursor": {
            "state": "ok",
            "offered": [{
              "model": "auto",
              "efforts": ["—"]
            }, {
              "model": "composer 2.5",
              "efforts": ["—"]
            }, {
              "model": "gemini 3.8 flash",
              "efforts": ["medium"]
            }, {
              "model": "gpt-5.6 sol",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6 fast",
              "efforts": ["high"]
            }, {
              "model": "kimi k3",
              "efforts": ["high"]
            }, {
              "model": "opus 5",
              "efforts": ["medium", "high"]
            }, {
              "model": "sonnet 5",
              "efforts": ["high"]
            }]
          },
          "grok": {
            "state": "ok",
            "offered": [{
              "model": "grok 4.6",
              "efforts": ["low", "medium", "high", "xhigh"]
            }, {
              "model": "grok 4.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "claude": {
            "state": "ok",
            "offered": [{
              "model": "opus 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "sonnet 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5.1",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }]
          },
          "codex": {
            "state": "ok",
            "offered": [{
              "model": "gpt 6 astra",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 sol",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 luna",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt 5.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "pi": {
            "state": "ok",
            "offered": [{
              "model": "deepseek-v4-pro",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "k3",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "grok-4.6",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt-5.6-sol",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }]
          }
        }
      }
    },
    "page": {
      "scanning": true
    }
  },
  "saved": {
    "name": "保存成功",
    "payload": {
      "version": 12,
      "runner": "orca",
      "rows": {
        "junior-worker": {
          "host": "grok",
          "model": "grok 4.6",
          "effort": "high"
        },
        "senior-worker": {
          "host": "codex",
          "model": "gpt 5.6 sol",
          "effort": "high"
        },
        "reviewer": {
          "host": "claude",
          "model": "opus 5",
          "effort": "high"
        },
        "advisor": {
          "host": "claude",
          "model": "fable 5.1",
          "effort": "medium"
        }
      },
      "hosts": [{
        "name": "cursor",
        "binary": "cursor-agent",
        "cli": true,
        "paseo": true
      }, {
        "name": "grok",
        "binary": "grok",
        "cli": true,
        "paseo": true
      }, {
        "name": "claude",
        "binary": "claude",
        "cli": true,
        "paseo": true
      }, {
        "name": "codex",
        "binary": "codex",
        "cli": true,
        "paseo": true
      }, {
        "name": "pi",
        "binary": "pi",
        "cli": false,
        "paseo": true
      }],
      "runners": ["herdr", "orca", "paseo", "auto"],
      "scan": {
        "source": "cli",
        "scanned_at": "2026-09-10T23:02:00Z",
        "scanning": false,
        "hosts": {
          "cursor": {
            "state": "ok",
            "offered": [{
              "model": "auto",
              "efforts": ["—"]
            }, {
              "model": "composer 2.5",
              "efforts": ["—"]
            }, {
              "model": "gemini 3.8 flash",
              "efforts": ["medium"]
            }, {
              "model": "gpt-5.6 sol",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6 fast",
              "efforts": ["high"]
            }, {
              "model": "kimi k3",
              "efforts": ["high"]
            }, {
              "model": "opus 5",
              "efforts": ["medium", "high"]
            }, {
              "model": "sonnet 5",
              "efforts": ["high"]
            }]
          },
          "grok": {
            "state": "ok",
            "offered": [{
              "model": "grok 4.6",
              "efforts": ["low", "medium", "high", "xhigh"]
            }, {
              "model": "grok 4.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "claude": {
            "state": "ok",
            "offered": [{
              "model": "opus 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "sonnet 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5.1",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }]
          },
          "codex": {
            "state": "ok",
            "offered": [{
              "model": "gpt 6 astra",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 sol",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 luna",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt 5.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "pi": {
            "state": "ok",
            "offered": [{
              "model": "deepseek-v4-pro",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "k3",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "grok-4.6",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt-5.6-sol",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }]
          }
        }
      }
    },
    "page": {
      "edit": [["advisor", "effort", "high"]],
      "saveAt": "2026-09-10T23:41:00Z"
    }
  },
  "refused": {
    "name": "保存被拒：start 会拒绝的格子",
    "payload": {
      "version": 12,
      "runner": "orca",
      "rows": {
        "junior-worker": {
          "host": "grok",
          "model": "grok 4.6",
          "effort": "high"
        },
        "senior-worker": {
          "host": "codex",
          "model": "gpt 5.6 sol",
          "effort": "high"
        },
        "reviewer": {
          "host": "claude",
          "model": "opus 5",
          "effort": "high"
        },
        "advisor": {
          "host": "claude",
          "model": "fable 5.1",
          "effort": "medium"
        }
      },
      "hosts": [{
        "name": "cursor",
        "binary": "cursor-agent",
        "cli": true,
        "paseo": true
      }, {
        "name": "grok",
        "binary": "grok",
        "cli": true,
        "paseo": true
      }, {
        "name": "claude",
        "binary": "claude",
        "cli": true,
        "paseo": true
      }, {
        "name": "codex",
        "binary": "codex",
        "cli": true,
        "paseo": true
      }, {
        "name": "pi",
        "binary": "pi",
        "cli": false,
        "paseo": true
      }],
      "runners": ["herdr", "orca", "paseo", "auto"],
      "scan": {
        "source": "cli",
        "scanned_at": "2026-09-10T23:02:00Z",
        "scanning": false,
        "hosts": {
          "cursor": {
            "state": "ok",
            "offered": [{
              "model": "auto",
              "efforts": ["—"]
            }, {
              "model": "composer 2.5",
              "efforts": ["—"]
            }, {
              "model": "gemini 3.8 flash",
              "efforts": ["medium"]
            }, {
              "model": "gpt-5.6 sol",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6",
              "efforts": ["high", "xhigh"]
            }, {
              "model": "grok 4.6 fast",
              "efforts": ["high"]
            }, {
              "model": "kimi k3",
              "efforts": ["high"]
            }, {
              "model": "opus 5",
              "efforts": ["medium", "high"]
            }, {
              "model": "sonnet 5",
              "efforts": ["high"]
            }]
          },
          "grok": {
            "state": "ok",
            "offered": [{
              "model": "grok 4.6",
              "efforts": ["low", "medium", "high", "xhigh"]
            }, {
              "model": "grok 4.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "claude": {
            "state": "ok",
            "offered": [{
              "model": "opus 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "sonnet 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5.1",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "fable 5",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }]
          },
          "codex": {
            "state": "ok",
            "offered": [{
              "model": "gpt 6 astra",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 sol",
              "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]
            }, {
              "model": "gpt 5.6 luna",
              "efforts": ["low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt 5.5",
              "efforts": ["low", "medium", "high", "xhigh"]
            }]
          },
          "pi": {
            "state": "ok",
            "offered": [{
              "model": "deepseek-v4-pro",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "k3",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "grok-4.6",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }, {
              "model": "gpt-5.6-sol",
              "efforts": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
            }]
          }
        }
      }
    },
    "page": {
      "edit": [["advisor", "effort", "high"]],
      "serverFlags": [{
        "cell": "advisor.effort",
        "reason": "fable 5.1 在 claude 上没有 high 这一档"
      }]
    }
  }
};
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/task-board/data/settings.js", error: String((e && e.message) || e) }); }

// ui_kits/task-board/lib/board.js
try { (() => {
(function () {
  window.MMW = window.MMW || {};
  const MMW = window.MMW;
  // ── shared.mjs ──
  (function () {
    function el(tag, attrs = {}, ...kids) {
      const node = document.createElement(tag);
      for (const [key, value] of Object.entries(attrs)) {
        if (value == null || value === false) continue;
        if (key === "class") node.className = value;else if (key === "disabled") node.disabled = true;else if (key === "selected") node.selected = true;else if (key === "html") node.innerHTML = value;else if (key.startsWith("on") && typeof value === "function") {
          node.addEventListener(key.slice(2).toLowerCase(), value);
        } else node.setAttribute(key, value === true ? "" : String(value));
      }
      for (const kid of kids.flat(Infinity)) {
        if (kid == null || kid === false) continue;
        node.append(typeof kid === "object" ? kid : String(kid));
      }
      return node;
    }
    const hhmm = value => new Date(value).toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false
    });
    const minutes = (from, to = window.MMW_NOW ? new Date(window.MMW_NOW) : new Date()) => Math.max(0, Math.round((new Date(to) - new Date(from)) / 60000));
    async function hand(method) {
      try {
        return await method();
      } catch {
        return null;
      }
    }
    MMW['shared'] = {
      el,
      hhmm,
      minutes,
      hand
    };
    Object.assign(MMW, MMW['shared']);
  })();
  // ── board-logic.mjs ──
  (function () {
    const {
      hhmm,
      minutes
    } = MMW;

    // The two axes a ticket is read on, both defined in `docs/contexts/task-board/CONTEXT.md`:
    // the phase is where the ticket stands inside itself, the lamp is what it wants from the
    // outside. A ticket can be `working` and still want nothing, or `landed` and still need a
    // person, so neither word can be read off the other.
    const PHASES = ["queued", "working", "waiting", "review", "verify", "landed"];
    const LAMP_WORD = {
      orange: "needs you",
      green: "running",
      ink: "done",
      hollow: "queued"
    };
    const NEEDS_YOU_KIND = {
      decision: "只有你能拍板；worker 先按默认值继续",
      fault: "MMW 自己坏了，开它的 agent 已停下",
      contract: "spec 本身不成立，要回到写 spec 的人"
    };
    const NEEDS_YOU = new Set(Object.keys(NEEDS_YOU_KIND));
    const duration = value => value < 60 ? `${value}m` : `${Math.floor(value / 60)}h${String(value % 60).padStart(2, "0")}m`;
    const short = value => String(value || "").slice(0, 7);
    const workerStartedAfter = (fold, at) => fold.sessions.some(session => session.kind === "worker" && session.started_at > at);
    function childIsOpen(ticket, child) {
      const issue = (ticket.children || []).find(item => item.number === child.child);
      return issue ? String(issue.state).toUpperCase() !== "CLOSED" : !child.resolution;
    }
    const Board = {
      stoppedByFault(ticket) {
        let started = -1;
        ticket.events.forEach((event, index) => {
          if (event.event === "worker.started" || event.event === "worker.resumed") started = index;
        });
        return ticket.events.some((event, index) => {
          if (index <= started || event.event !== "child.opened" || event.payload?.kind !== "fault") return false;
          const child = ticket.fold.children[String(event.payload.child)] || {
            child: event.payload.child
          };
          return childIsOpen(ticket, child);
        });
      },
      handedBack(ticket) {
        const fold = ticket.fold;
        return Boolean(fold.returned && fold.outcome && !workerStartedAfter(fold, fold.outcome.at));
      },
      bounce(ticket) {
        if (!ticket.fold.bounced) return null;
        const event = [...ticket.events].reverse().find(item => item.event === "ticket.bounced");
        return event && !workerStartedAfter(ticket.fold, event.at) ? event : null;
      },
      running(ticket) {
        const held = ticket.fold.held ?? (ticket.fold.claim_hold || ticket.fold.sessions.some(session => session.live));
        return held && !this.stoppedByFault(ticket);
      },
      stoppedAt(ticket) {
        if (this.bounce(ticket)) return "verify";
        return this.workflowPhase(ticket);
      },
      workflowPhase(ticket) {
        const reviewerLive = ticket.fold.sessions.some(session => session.kind === "reviewer" && session.live);
        let phase = reviewerLive ? "review" : "working";
        for (const event of ticket.events) {
          if (event.event === "ticket.checked" && event.payload?.run === "reverify" && event.payload?.actor === "worker") {
            phase = "verify";
          } else if (event.event === "reviewer.started") {
            phase = "review";
          } else if (event.event === "reviewer.reported" || !reviewerLive && (["worker.started", "worker.resumed", "ticket.claimed", "worker.decided"].includes(event.event) || event.event === "ticket.checked" && event.payload?.run === "self")) {
            phase = "working";
          }
        }
        return phase;
      },
      // Whether this ticket is finished, which is the same question `blocker_hold` already
      // answers for the ticket behind it: nothing more is coming from it. The ledger landed
      // it, or it closed with nothing that will ever land — taken through by hand outside the
      // pipeline, which writes no `ticket.landed` and can leave the ledger empty. A ticket
      // that passed and has not landed yet is not finished, and neither is one whose events
      // could not be read: those still say why they hold.
      done(ticket) {
        return Boolean(ticket.fold.landed) || this.released(ticket);
      },
      phase(ticket) {
        const fold = ticket.fold;
        if (this.done(ticket)) return "landed";
        const live = fold.sessions.filter(session => session.live);
        if (this.handedBack(ticket) || this.bounce(ticket) || live.length && this.stoppedByFault(ticket)) {
          return this.stoppedAt(ticket);
        }
        if (!live.length) return "queued";
        if (fold.waiting) return "waiting";
        return this.workflowPhase(ticket);
      },
      why(ticket) {
        const reasons = [];
        for (const child of Object.values(ticket.fold.children)) {
          if (NEEDS_YOU.has(child.kind) && childIsOpen(ticket, child)) {
            reasons.push({
              kind: child.kind,
              child: child.child,
              title: child.title,
              text: NEEDS_YOU_KIND[child.kind]
            });
          }
        }
        if (this.handedBack(ticket)) {
          const abandoned = ticket.fold.outcome.payload?.abandoned || [];
          reasons.push({
            kind: "returned",
            text: abandoned.length ? abandoned.map(item => `handed back: ${item.ac} 放弃（${item.kind}）。${item.reason}`).join("；") : ticket.fold.outcome.line
          });
        }
        const bounce = this.bounce(ticket);
        if (bounce) {
          const payload = bounce.payload || {};
          const failures = (payload.commands || []).map(item => {
            const output = item.output || item.last || item.stderr;
            return output ? `${item.command}：${Array.isArray(output) ? output.join(" / ") : output}` : item.command;
          });
          reasons.push({
            kind: "bounced",
            text: payload.reason === "conflict" ? `合不进 ${payload.into}（${short(payload.commit)}）：冲突在 ${(payload.files || []).join("、")}。等早上 triage` : `合不进 ${payload.into}（${short(payload.commit)}）：合并后检查没过 ${failures.join("、")}。等早上 triage`
          });
        }
        return reasons;
      },
      lamp(ticket) {
        if (this.why(ticket).length) return "orange";
        if (this.running(ticket)) return "green";
        if (this.done(ticket)) return "ink";
        return "hollow";
      },
      waitingSince(ticket) {
        return ticket.fold.waiting && ticket.fold.sessions.some(session => session.live) ? ticket.fold.waiting.at : null;
      },
      runLine(ticket) {
        const live = ticket.fold.sessions.filter(session => session.live);
        if (!ticket.fold.sessions.length) {
          // Finished with no session at all: it was taken through by hand, so there is no
          // runner to name and "not dispatched" would read as work still to come.
          if (this.done(ticket)) return {
            text: "closed, never dispatched"
          };
          return {
            text: ticket.fold.claim_hold || ticket.fold.held ? "claimed · no session yet" : "not dispatched"
          };
        }
        const since = this.waitingSince(ticket);
        if (since) return {
          text: `waiting for a slot · since ${hhmm(since)}`
        };
        const session = live.length ? live[live.length - 1] : ticket.fold.worker;
        if (live.length && this.stoppedByFault(ticket)) return {
          text: `stopped · ${session.host} · ${session.model}`,
          flag: true
        };
        return {
          text: `${session.host} · ${session.model} · ${session.effort}`
        };
      },
      elapsed(ticket) {
        const first = ticket.fold.sessions[0]?.started_at;
        if (!first) return "";
        const landed = ticket.events.find(event => event.event === "ticket.landed");
        if (ticket.fold.landed && landed) return duration(minutes(first, landed.at));
        if (this.handedBack(ticket)) return duration(minutes(first, ticket.fold.outcome.at));
        const bounce = this.bounce(ticket);
        if (bounce) return duration(minutes(first, bounce.at));
        return duration(minutes(first));
      },
      aggregate(tickets) {
        const lamps = tickets.map(ticket => this.lamp(ticket));
        if (lamps.includes("orange")) return "orange";
        if (lamps.includes("green")) return "green";
        if (lamps.length && lamps.every(lamp => lamp === "ink")) return "ink";
        return "hollow";
      },
      decisionLamp(decision) {
        return String(decision.state).toLowerCase() === "closed" ? "ink" : "hollow";
      },
      allTickets(task) {
        return task.specs.flatMap(spec => spec.tickets);
      },
      progress(task) {
        const tickets = this.allTickets(task);
        return {
          done: tickets.filter(ticket => this.done(ticket)).length,
          total: tickets.length
        };
      },
      released(blocker) {
        return blocker.blocker_hold === "";
      },
      edgeState(blocker, blocked, type = "ticket") {
        if (type === "decision") return String(blocker.state).toLowerCase() === "closed" ? "done" : "blocked";
        if (!this.released(blocker)) return "blocked";
        return this.running(blocked) ? "flow" : "done";
      },
      graph(items) {
        const ids = new Set(items.map(item => item.n));
        const predecessors = new Map(items.map(item => [item.n, item.blocked.filter(number => ids.has(number))]));
        const successors = new Map(items.map(item => [item.n, []]));
        for (const [number, blockers] of predecessors) for (const blocker of blockers) successors.get(blocker).push(number);
        const indegree = new Map(items.map(item => [item.n, predecessors.get(item.n).length]));
        const layers = new Map();
        const queue = items.filter(item => indegree.get(item.n) === 0).map(item => item.n);
        for (const number of queue) layers.set(number, 0);
        while (queue.length) {
          const number = queue.shift();
          for (const next of successors.get(number)) {
            layers.set(next, Math.max(layers.get(next) ?? 0, layers.get(number) + 1));
            indegree.set(next, indegree.get(next) - 1);
            if (indegree.get(next) === 0) queue.push(next);
          }
        }
        const unresolved = new Set(items.filter(item => !layers.has(item.n)).map(item => item.n));
        const last = Math.max(-1, ...layers.values()) + 1;
        for (const number of unresolved) layers.set(number, last);
        const reachable = (from, to, omitDirect) => {
          const seen = new Set([from]);
          const pending = successors.get(from).filter(next => !(omitDirect && next === to));
          while (pending.length) {
            const next = pending.pop();
            if (next === to) return true;
            if (seen.has(next)) continue;
            seen.add(next);
            pending.push(...successors.get(next));
          }
          return false;
        };
        const cyclic = new Set([...unresolved].filter(number => successors.get(number).some(next => unresolved.has(next) && reachable(next, number, false))));
        const edges = [];
        for (const [to, blockers] of predecessors) for (const from of blockers) {
          const cycle = cyclic.has(from) && cyclic.has(to) && reachable(to, from, false);
          if (!cycle && reachable(from, to, true)) continue;
          edges.push({
            from,
            to,
            cyc: cycle
          });
        }
        return {
          layer: layers,
          preds: predecessors,
          cyclic,
          edges
        };
      },
      layout(task, expanded) {
        // Card sizes are the width two title lines need plus the card's own padding, and the
        // height that title and the run line under it take: measured on a live board, not chosen.
        // An ellipsis is the fallback for a title past that width, not the everyday case.
        const geometry = {
          mapX: 12,
          trunkX: 30,
          specX: 52,
          containerRight: 220,
          firstIssueX: 272,
          ticketWidth: 328,
          ticketHeight: 100,
          decisionWidth: 298,
          decisionHeight: 74,
          columnGap: 84,
          rowGap: 14,
          containerHeight: 72
        };
        const nodes = [];
        const edges = [];
        const labels = [];
        const band = (items, top, width, height) => {
          const graph = this.graph(items);
          const byLayer = new Map();
          for (const item of items) {
            const layer = graph.layer.get(item.n);
            if (!byLayer.has(layer)) byLayer.set(layer, []);
            byLayer.get(layer).push(item);
          }
          const positions = new Map();
          let bottom = top;
          for (const layer of [...byLayer.keys()].sort((a, b) => a - b)) {
            const column = byLayer.get(layer).map(item => {
              const blockers = graph.preds.get(item.n).filter(number => positions.has(number));
              const wanted = blockers.length ? blockers.reduce((sum, number) => sum + positions.get(number).y, 0) / blockers.length : top;
              return {
                item,
                wanted
              };
            }).sort((a, b) => a.wanted - b.wanted || a.item.n - b.item.n);
            let y = top;
            for (const entry of column) {
              y = Math.max(entry.wanted, y);
              positions.set(entry.item.n, {
                x: geometry.firstIssueX + layer * (width + geometry.columnGap),
                y
              });
              y += height + geometry.rowGap;
            }
            bottom = Math.max(bottom, y - geometry.rowGap);
          }
          return {
            graph,
            positions,
            height: bottom - top
          };
        };
        const expansionCurve = (fromY, node) => {
          const x1 = geometry.containerRight;
          const x2 = node.x;
          const y2 = node.y + node.h / 2;
          return `M ${x1} ${fromY} C ${x1 + 26} ${fromY}, ${x2 - 26} ${y2}, ${x2} ${y2}`;
        };
        const blockingCurve = (from, to, cycle) => {
          const x1 = from.x + from.w;
          const y1 = from.y + from.h / 2;
          if (cycle) {
            const y2 = to.y + to.h / 2;
            const bulge = x1 + 34;
            return `M ${x1} ${y1} C ${bulge} ${y1}, ${bulge} ${y2}, ${x1} ${y2}`;
          }
          const x2 = to.x;
          const y2 = to.y + to.h / 2;
          const dx = Math.max(28, (x2 - x1) * 0.55);
          return `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
        };
        const place = (items, type, width, height, top, container, middle) => {
          const result = band(items, top, width, height);
          const placed = new Map();
          for (const item of items) {
            const position = result.positions.get(item.n);
            const node = {
              id: item.n,
              type,
              ref: item,
              x: position.x,
              y: position.y,
              w: width,
              h: height,
              parent: container,
              cyclic: result.graph.cyclic.has(item.n)
            };
            nodes.push(node);
            placed.set(item.n, node);
          }
          for (const node of placed.values()) {
            if (result.graph.layer.get(node.id) === 0) {
              // The container feeds a first-layer ticket the way a landed blocker feeds the
              // ticket behind it: while that ticket is being worked, the line carries the flow.
              const flowing = type === "ticket" && this.running(node.ref);
              edges.push({
                kind: "expand",
                from: container,
                to: node.id,
                d: expansionCurve(middle, node),
                state: flowing ? "flow" : "done",
                ends: [[geometry.containerRight, middle], [node.x, node.y + node.h / 2]]
              });
            }
          }
          for (const edge of result.graph.edges) {
            const from = placed.get(edge.from);
            const to = placed.get(edge.to);
            edges.push({
              kind: "block",
              from: edge.from,
              to: edge.to,
              cyc: edge.cyc,
              state: edge.cyc ? "blocked" : this.edgeState(from.ref, to.ref, type),
              d: blockingCurve(from, to, edge.cyc),
              ends: [[from.x + from.w, from.y + from.h / 2], edge.cyc ? [from.x + from.w, to.y + to.h / 2] : [to.x, to.y + to.h / 2]]
            });
          }
          if (result.graph.cyclic.size) {
            const first = placed.get([...result.graph.cyclic][0]);
            labels.push({
              x: first.x,
              y: top - 18,
              text: `blocking cycle · ${[...result.graph.cyclic].map(number => `#${number}`).join(" ⇄ ")}`,
              warn: true
            });
          }
          return result.height;
        };
        let y = 40;
        if (task.kind === "spec") {
          // A spec with no map above it is the task itself: one container at the top,
          // its tickets hanging straight off it, no trunk and no spec row.
          const spec = task.specs[0];
          const specNode = {
            id: spec.n,
            type: "spec",
            ref: spec,
            x: geometry.mapX,
            y,
            w: geometry.containerRight - geometry.mapX,
            h: geometry.containerHeight
          };
          nodes.push(specNode);
          if (expanded.has(spec.n)) {
            place(spec.tickets, "ticket", geometry.ticketWidth, geometry.ticketHeight, y, spec.n, y + geometry.containerHeight / 2);
          }
          return {
            nodes,
            edges,
            labels,
            W: Math.max(...nodes.map(node => node.x + node.w)) + 60,
            H: Math.max(...nodes.map(node => node.y + node.h)) + 60
          };
        }
        const mapNode = {
          id: task.n,
          type: "map",
          ref: task,
          x: geometry.mapX,
          y,
          w: geometry.containerRight - geometry.mapX,
          h: geometry.containerHeight
        };
        nodes.push(mapNode);
        let mapBand = geometry.containerHeight;
        if (task.decisions.length && expanded.has(task.n)) {
          labels.push({
            x: geometry.firstIssueX,
            y: y - 18,
            text: `decision tickets · ${task.decisions.length}`
          });
          mapBand = Math.max(geometry.containerHeight, place(task.decisions, "decision", geometry.decisionWidth, geometry.decisionHeight, y, task.n, y + geometry.containerHeight / 2));
        }
        y += mapBand + 48;
        labels.push({
          x: geometry.specX,
          y: y - 18,
          text: `spec · ${task.specs.length}`
        });
        let lastMiddle = y;
        for (const spec of task.specs) {
          const specNode = {
            id: spec.n,
            type: "spec",
            ref: spec,
            x: geometry.specX,
            y,
            w: geometry.containerRight - geometry.specX,
            h: geometry.containerHeight
          };
          nodes.push(specNode);
          lastMiddle = y + geometry.containerHeight / 2;
          edges.push({
            kind: "trunk",
            d: `M ${geometry.trunkX} ${lastMiddle - 10} Q ${geometry.trunkX} ${lastMiddle} ${geometry.trunkX + 10} ${lastMiddle} H ${geometry.specX}`
          });
          let height = geometry.containerHeight;
          if (expanded.has(spec.n)) {
            height = Math.max(geometry.containerHeight, place(spec.tickets, "ticket", geometry.ticketWidth, geometry.ticketHeight, y, spec.n, lastMiddle));
          }
          y += height + 26;
        }
        edges.unshift({
          kind: "trunk",
          d: `M ${geometry.trunkX} ${mapNode.y + mapNode.h} V ${lastMiddle - 10}`
        });
        return {
          nodes,
          edges,
          labels,
          W: Math.max(...nodes.map(node => node.x + node.w)) + 60,
          H: Math.max(...nodes.map(node => node.y + node.h)) + 60
        };
      }
    };
    function defaultExpanded(task) {
      const expanded = new Set([task.n]);
      for (const spec of task.specs) {
        const lamp = Board.aggregate(spec.tickets);
        if (lamp === "orange" || lamp === "green") expanded.add(spec.n);
      }
      return expanded;
    }

    // Every pipeline event as a person reads it: an English name, the phase pill the ticket
    // card carried while that event was the newest one, and one sentence from the payload.
    // A claim never opens a block of its own: start and claim are one act.
    const PHASE_OF_EVENT = {
      "worker.started": "working",
      "worker.resumed": "working",
      "ticket.claimed": "working",
      "worker.touched": "working",
      "worker.decided": "working",
      "child.opened": "working",
      "worker.queued": "waiting",
      "reviewer.started": "review",
      "reviewer.reported": "review",
      "ticket.passed": "verify",
      "ticket.returned": "verify",
      "ticket.bounced": "verify",
      "ticket.refused": "queued",
      "ticket.released": "queued",
      "worker.retracted": "queued",
      "worker.replaced": "queued",
      "worker.lost": "queued",
      "reviewer.lost": "queued",
      "ticket.landed": "landed",
      "ticket.regressed": "landed",
      "child.closed": "landed",
      "spec.merged": "landed",
      "spec.opened": "queued",
      "spec.suspended": "queued",
      "spec.closed": "queued"
    };
    const STICKY_EVENTS = new Set(["ticket.claimed"]);
    const EVENT_NAME = {
      "spec.opened": "Night opened",
      "spec.suspended": "Night suspended",
      "spec.closed": "Night closed",
      "spec.merged": "Night's branch merged",
      "ticket.claimed": "Ticket claimed",
      "ticket.refused": "Pick-up refused",
      "ticket.passed": "Ticket passed",
      "ticket.returned": "Ticket handed back",
      "ticket.released": "Claim released",
      "ticket.landed": "Landed",
      "ticket.regressed": "Regressed after landing",
      "ticket.bounced": "Merge bounced",
      "worker.started": "Worker started",
      "worker.resumed": "Worker resumed",
      "worker.retracted": "Worker retracted",
      "worker.replaced": "Worker replaced",
      "worker.decided": "Decisions recorded",
      "worker.queued": "Waiting for a slot",
      "worker.touched": "Another ticket touched its files",
      "worker.lost": "Worker session lost",
      "reviewer.started": "Reviewer started",
      "reviewer.reported": "Review posted",
      "reviewer.lost": "Reviewer session lost"
    };
    const CHILD_NAME = {
      finding: "Finding raised",
      contract: "Spec does not hold",
      deferred: "Left for a later ticket",
      decision: "Your decision needed",
      fault: "MMW itself broke"
    };
    const RUN_NAME = {
      self: "Criteria run",
      reverify: "Final criteria run",
      "repo-checks": "Repository checks"
    };
    const REFUSAL = {
      "wrong-branch": "the worktree was on the wrong branch",
      "dirty-tree": "the tree already carried uncommitted changes",
      "not-open": "the ticket was no longer open",
      "not-ready": "the ticket was not in the agent queue",
      blocked: "a ticket in front of it had not landed",
      "claimed-by-other": "someone else already held it"
    };
    const RELEASE = {
      landed: "it had landed",
      suspended: "the night was suspended",
      "worker-lost": "its worker's session was gone"
    };
    const QUEUE = {
      "product-full": "every instance of the product was in use",
      "machine-full": "every slot on this machine was in use"
    };
    const RESOLUTION = {
      fixed: "fixed",
      stale: "no longer applies",
      "became-ticket": "became a ticket"
    };
    const COMMON_FIELDS = new Set(["v", "event", "stage", "actor", "spec", "ticket", "at"]);
    const SUMMARY_WEIGHT = {
      "ticket.refused": 3,
      "ticket.returned": 3,
      "ticket.bounced": 3,
      "ticket.regressed": 3,
      "child.opened": 3,
      "ticket.checked": 2,
      "reviewer.reported": 2,
      "ticket.landed": 2,
      "ticket.passed": 2,
      "worker.lost": 2,
      "ticket.released": 1,
      "worker.started": 1
    };
    const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;
    const listOf = (items, max = 2) => {
      const all = items || [];
      if (all.length <= max) return all.join(", ");
      return `${all.slice(0, max).join(", ")} and ${all.length - max} more`;
    };
    const countsText = counts => {
      if (!counts || counts.total == null) return "";
      return `${counts.met ?? counts.passed ?? 0} of ${counts.total}`;
    };
    function eventText(event, payload) {
      switch (event) {
        case "worker.started":
        case "worker.resumed":
        case "reviewer.started":
          return payload.model ? `${payload.host} ${payload.model}, ${payload.effort} effort` : "";
        case "worker.touched":
          return `#${payload.by} changed ${plural((payload.files || []).length, "file")} this ticket owns`;
        case "worker.queued":
          return QUEUE[payload.reason] || "";
        case "worker.decided":
          return "the calls the worker made on its own, written down for the review";
        case "ticket.refused":
          return `it would not start: ${REFUSAL[payload.reason] || payload.reason}`;
        case "ticket.released":
          return `back in the queue: ${RELEASE[payload.reason] || payload.reason}`;
        case "ticket.checked":
          {
            const counts = countsText(payload.counts);
            if (payload.run === "repo-checks") {
              return `${counts || "the"} repository check${payload.counts?.total === 1 ? "" : "s"} passed`;
            }
            const failed = (payload.failed || []).length ? ` — ${listOf(payload.failed, 3)} unmet` : "";
            return `${counts} criteria met${failed}`;
          }
        case "ticket.passed":
          return `${countsText(payload.counts)} criteria met, ticket closed`;
        case "ticket.returned":
          return "handed back with criteria it could not meet";
        case "ticket.landed":
          return `merged into ${payload.into}`;
        case "ticket.bounced":
          return payload.reason === "conflict" ? `conflict with ${payload.into} in ${plural((payload.files || []).length, "file")}` : `checks failed after merging into ${payload.into}`;
        case "ticket.regressed":
          return `${listOf(payload.failed, 3)} stopped passing on the base branch`;
        case "reviewer.reported":
          return "the three-axis review is on the ticket";
        case "worker.lost":
        case "reviewer.lost":
          return "its session stopped without finishing";
        case "child.opened":
          return payload.title || "";
        case "child.closed":
          return payload.resolution === "became-ticket" ? `#${payload.child} became ticket #${payload.became}` : `#${payload.child}: ${RESOLUTION[payload.resolution] || payload.resolution}`;
        case "spec.merged":
          return `into the project branch ${payload.project}`;
        default:
          return "";
      }
    }
    function eventName(event, payload) {
      if (event === "ticket.checked") {
        if (payload.run === "reverify" && payload.stage === "regress") return "Criteria re-run after landing";
        return RUN_NAME[payload.run] || "Criteria run";
      }
      if (event === "child.opened") return CHILD_NAME[payload.kind] || "Sub-issue opened";
      if (event === "child.closed") {
        return payload.resolution === "became-ticket" ? "Finding became a ticket" : "Sub-issue closed";
      }
      return EVENT_NAME[event] || event;
    }
    function eventTone(event, payload) {
      if (event === "child.opened" && NEEDS_YOU.has(payload.kind)) return "needs-you";
      if (event === "ticket.returned" || event === "ticket.bounced" || event === "ticket.regressed") return "needs-you";
      if (event === "ticket.refused" || /\.lost$|^worker\.(retracted|replaced)$/.test(event)) return "warn";
      if (event === "ticket.checked" && payload.result !== "met") return "warn";
      if (/^ticket\.(landed|passed)$/.test(event)) return "good";
      return "plain";
    }
    function eventPhase(event, payload) {
      if (event === "ticket.checked") {
        if (payload.run === "repo-checks") return "verify";
        if (payload.run === "reverify") return payload.stage === "regress" ? "landed" : "verify";
        return "working";
      }
      return PHASE_OF_EVENT[event] || "working";
    }
    function eventDetail(payload, line) {
      const rows = [];
      for (const [key, value] of Object.entries(payload)) {
        if (COMMON_FIELDS.has(key) || key === "details") continue;
        if (key === "criteria") {
          rows.push({
            k: key,
            v: value.map(item => `${item.id} ${item.met ? "met" : "unmet"}`).join(", ")
          });
          continue;
        }
        rows.push({
          k: key,
          v: Array.isArray(value) ? value.join(", ") : typeof value === "object" && value !== null ? JSON.stringify(value) : String(value)
        });
      }
      rows.push({
        k: "comment",
        v: line
      });
      return rows;
    }
    function describeEvent(raw = {}) {
      const payload = raw.payload || {};
      const event = raw.event || "";
      return {
        event,
        time: raw.at ? hhmm(raw.at) : raw.time || "",
        name: eventName(event, payload),
        text: eventText(event, payload),
        phase: eventPhase(event, payload),
        tone: eventTone(event, payload),
        sticky: STICKY_EVENTS.has(event),
        detail: eventDetail(payload, raw.line || "")
      };
    }
    function eventBlocks(events = []) {
      const out = [];
      for (const raw of events) {
        const item = describeEvent(raw);
        const last = out[out.length - 1];
        if (last && (last.phase === item.phase || item.sticky)) last.items.push(item);else out.push({
          phase: item.phase,
          items: [item]
        });
      }
      for (const block of out) {
        block.from = block.items[0].time;
        block.to = block.items[block.items.length - 1].time;
        block.tone = block.items.some(item => item.tone === "needs-you") ? "needs-you" : block.items.some(item => item.tone === "warn") ? "warn" : "plain";
      }
      return out;
    }
    function blockSummary(block) {
      const best = block.items.reduce((pick, item) => (SUMMARY_WEIGHT[item.event] || 0) >= (SUMMARY_WEIGHT[pick.event] || 0) ? item : pick, block.items[0]);
      return best.text ? `${best.name} — ${best.text}` : best.name;
    }
    MMW['board-logic'] = {
      PHASES,
      LAMP_WORD,
      Board,
      defaultExpanded,
      describeEvent,
      eventBlocks,
      blockSummary
    };
    Object.assign(MMW, MMW['board-logic']);
  })();
  // ── local-config.mjs ──
  (function () {
    const {
      hhmm
    } = MMW;
    const CATALOG = {
      store: "~/.mmw/models.json",
      agents: ["junior-worker", "senior-worker", "reviewer", "advisor"],
      hosts: ["cursor", "grok", "claude", "codex", "pi"],
      binaries: {
        cursor: "cursor-agent",
        grok: "grok",
        claude: "claude",
        codex: "codex",
        pi: "pi"
      },
      launch: {
        cursor: {
          cli: true,
          paseo: true
        },
        grok: {
          cli: true,
          paseo: true
        },
        claude: {
          cli: true,
          paseo: true
        },
        codex: {
          cli: true,
          paseo: true
        },
        pi: {
          cli: false,
          paseo: true
        }
      },
      runners: ["herdr", "orca", "paseo"]
    };
    const LocalConfig = {
      CELLS: ["host", "model", "effort"],
      ROLE_WHAT: {
        "junior-worker": "贴 junior-worker label 的 ticket",
        "senior-worker": "贴 senior-worker label 的 ticket",
        reviewer: "review 每张 ticket 的改动",
        advisor: "被问到时给第二意见"
      },
      source: d => d.runner === "paseo" ? "paseo" : "cli",
      needsRescan: (from, to) => LocalConfig.source(from) !== LocalConfig.source(to),
      hostScan: (scan, host) => scan[host] || {
        state: "missing",
        offered: []
      },
      hostState(scan, d, host, catalog = CATALOG) {
        const launch = catalog.launch[host] || {};
        return launch[LocalConfig.source(d)] ? LocalConfig.hostScan(scan, host).state : "unlaunchable";
      },
      offeredBy: (scan, host) => LocalConfig.hostScan(scan, host).offered,
      effortsOf: (scan, host, model) => (LocalConfig.offeredBy(scan, host).find(o => o.model === model) || {
        efforts: []
      }).efforts,
      stateWord: (state, d) => ({
        missing: "本机没装",
        silent: "没有回答",
        down: "Paseo 没开",
        unlaunchable: d && LocalConfig.source(d) === "paseo" ? "Paseo 起不了" : "orca、herdr 起不了"
      })[state] || state,
      hostWhy: (state, host, d, catalog = CATALOG) => ({
        missing: `这台机器上没装 ${host} 的 CLI（${catalog.binaries[host]}），换一个这台机器有的`,
        silent: `${host} 的 CLI 在扫描时没有回答，换一个这台机器有的`,
        down: `Paseo 服务没开，问不到 ${host} 的 model；先开 Paseo，或者把 runner 换回 orca 或 herdr`,
        unlaunchable: LocalConfig.source(d) === "paseo" ? `Paseo 起不了 ${host}：hosts.json 没给它 paseo 块；换一个 host` : `orca 和 herdr 起不了 ${host}：hosts.json 没给它命令行启动块（cli）；换一个 host，或者把 runner 换成 paseo`
      })[state],
      problems(scan, d, catalog = CATALOG) {
        const L = LocalConfig,
          out = [];
        if (d.runner !== "auto" && !catalog.runners.includes(d.runner)) {
          out.push({
            key: "runner",
            cell: "runner",
            text: `${d.runner} 没有适配器，start 起不了 session`
          });
        }
        for (const a of catalog.agents) {
          const r = d.rows[a];
          if (!catalog.hosts.includes(r.host)) {
            out.push({
              key: a,
              cell: "host",
              text: `${r.host} 不是 MMW 认识的 host`
            });
            continue;
          }
          const hs = L.hostScan(scan, r.host),
            hostState = L.hostState(scan, d, r.host, catalog);
          if (hostState !== "ok") {
            out.push({
              key: a,
              cell: "host",
              text: L.hostWhy(hostState, r.host, d, catalog)
            });
            continue;
          }
          if (!r.model) {
            out.push({
              key: a,
              cell: "model",
              text: "还没选 model"
            });
            continue;
          }
          if (!hs.offered.some(o => o.model === r.model)) {
            out.push({
              key: a,
              cell: "model",
              text: `这台机器的 ${r.host} 已经不提供 ${r.model}`
            });
            continue;
          }
          if (!r.effort) {
            out.push({
              key: a,
              cell: "effort",
              text: "还没选 effort"
            });
            continue;
          }
          if (!L.effortsOf(scan, r.host, r.model).includes(r.effort)) {
            out.push({
              key: a,
              cell: "effort",
              text: `${r.model} 在 ${r.host} 上没有 ${r.effort} 这一档`
            });
          }
        }
        return out;
      },
      changes(d, s, catalog = CATALOG) {
        const out = d.runner !== s.runner ? [{
          key: "runner",
          text: "runner",
          cells: ["runner"]
        }] : [];
        for (const a of catalog.agents) {
          const cells = LocalConfig.CELLS.filter(c => d.rows[a][c] !== s.rows[a][c]);
          if (cells.length) out.push({
            key: a,
            text: `${a} 的 ${cells.join("、")}`,
            cells
          });
        }
        return out;
      },
      setCell(scan, d, key, cell, value) {
        const L = LocalConfig;
        if (key === "runner") {
          d.runner = value;
          return d;
        }
        const r = d.rows[key];
        r[cell] = value;
        if (cell === "host" && !L.offeredBy(scan, value).some(o => o.model === r.model)) r.model = "";
        if (cell !== "effort") {
          const es = L.effortsOf(scan, r.host, r.model);
          if (!es.includes(r.effort)) r.effort = es.length === 1 ? es[0] : "";
        }
        return d;
      },
      saveOff(scan, d, saved, flags = {}, catalog = CATALOG) {
        const ch = LocalConfig.changes(d, saved, catalog);
        const probs = LocalConfig.problems(scan, d, catalog);
        return !ch.length || probs.length > 0 || !!flags.scanning || !!flags.refused;
      },
      runnerOptions(d, catalog = CATALOG) {
        const opts = [...(d.runner !== "auto" && !catalog.runners.includes(d.runner) ? [{
          value: d.runner,
          text: `${d.runner} · 没有适配器`
        }] : []), ...catalog.runners.map(r => ({
          value: r,
          text: r
        })), {
          value: "auto",
          text: "按所在环境判断"
        }];
        return opts.map(o => ({
          ...o,
          selected: o.value === d.runner,
          disabled: !!o.disabled
        }));
      },
      rowOptions(scan, d, a, catalog = CATALOG) {
        const L = LocalConfig,
          r = d.rows[a],
          hs = L.hostScan(scan, r.host);
        const hostOk = L.hostState(scan, d, r.host, catalog) === "ok";
        const modelKnown = hostOk && hs.offered.some(o => o.model === r.model);
        const mark = (opts, value) => opts.map(o => ({
          ...o,
          selected: o.value === value,
          disabled: !!o.disabled
        }));
        const host = [...(catalog.hosts.includes(r.host) ? [] : [{
          value: r.host,
          text: `${r.host} · MMW 不认识`
        }]), ...catalog.hosts.map(h => {
          const hostState = L.hostState(scan, d, h, catalog);
          return {
            value: h,
            text: hostState === "ok" ? h : `${h} · ${L.stateWord(hostState, d)}`,
            disabled: hostState !== "ok" && h !== r.host
          };
        })];
        const offeredEfforts = L.effortsOf(scan, r.host, r.model);
        const effortKnown = modelKnown && offeredEfforts.includes(r.effort);
        const model = !hostOk ? [{
          value: r.model,
          text: r.model || "—"
        }] : [...(!r.model ? [{
          value: "",
          text: "选一个 model",
          disabled: true
        }] : modelKnown ? [] : [{
          value: r.model,
          text: `${r.model} · 本机已经没有`
        }]), ...hs.offered.map(o => ({
          value: o.model,
          text: o.model
        }))];
        const effort = !modelKnown ? [{
          value: r.effort,
          text: r.effort || "—"
        }] : [...(!r.effort ? [{
          value: "",
          text: "选一档",
          disabled: true
        }] : effortKnown ? [] : [{
          value: r.effort,
          text: `${r.effort} · 本机已经没有`
        }]), ...offeredEfforts.map(e => ({
          value: e,
          text: e === "—" ? "—（不设）" : e
        }))];
        return {
          host: mark(host, r.host),
          model: mark(model, r.model),
          effort: mark(effort, r.effort),
          hostOk,
          modelKnown
        };
      },
      hostChips(scan, d, catalog = CATALOG) {
        return catalog.hosts.map(h => {
          const offered = LocalConfig.hostScan(scan, h);
          const hostState = LocalConfig.hostState(scan, d, h, catalog);
          return {
            host: h,
            state: hostState,
            what: hostState === "ok" ? `${offered.offered.length} 个 model` : LocalConfig.stateWord(hostState, d)
          };
        });
      }
    };
    function catalogFromPayload(payload) {
      const hosts = [];
      const launch = {};
      const binaries = {};
      for (const item of payload.hosts) {
        hosts.push(item.name);
        launch[item.name] = {
          cli: !!item.cli,
          paseo: !!item.paseo
        };
        if (item.binary) binaries[item.name] = item.binary;
      }
      return {
        store: CATALOG.store,
        agents: CATALOG.agents,
        hosts,
        binaries,
        launch,
        runners: payload.runners.filter(name => name !== "auto")
      };
    }
    function settingsView(sheet, scan, catalog) {
      const L = LocalConfig,
        draft = sheet.draft;
      const probs = [...(sheet.scanning ? [] : L.problems(scan, draft, catalog)), ...(sheet.serverFlags || [])];
      const ch = L.changes(draft, sheet.saved, catalog);
      const cls = (key, cell) => probs.some(p => p.key === key && p.cell === cell) ? "sel bad" : ch.some(c => c.key === key && c.cells.includes(cell)) ? "sel changed" : "sel";
      const bads = key => probs.filter(p => p.key === key).map(p => ({
        text: p.text
      }));
      const rows = catalog.agents.map(a => {
        const o = L.rowOptions(scan, draft, a, catalog),
          r = draft.rows[a],
          b = bads(a);
        return {
          agent: a,
          what: L.ROLE_WHAT[a],
          host: r.host,
          model: r.model,
          effort: r.effort,
          hostCls: cls(a, "host"),
          modelCls: cls(a, "model"),
          effortCls: cls(a, "effort"),
          hostOpts: o.host,
          modelOpts: o.model,
          effortOpts: o.effort,
          hostOff: sheet.scanning,
          modelOff: sheet.scanning || !o.hostOk,
          effortOff: sheet.scanning || !o.modelKnown,
          hostLabel: `${a} 的 host`,
          modelLabel: `${a} 的 model`,
          effortLabel: `${a} 的 effort`,
          bads: b,
          hasBad: b.length > 0
        };
      });
      const when = "保存后，下一个新起的 agent 就用新值；已经在跑的不受影响。";
      let strong,
        quiet,
        hatch = false;
      if (sheet.refused) {
        strong = "没有保存";
        quiet = "这一页打开之后，本机配置被别处改过，先重新读取。";
      } else if (sheet.scanning) {
        strong = "正在扫描本机的 host";
        quiet = "扫描完之前不能保存。";
      } else if (probs.length) {
        strong = `有 ${probs.length} 处 start 会拒绝，改好之前不能保存`;
        quiet = "带斜线的格子，下面一行写着哪里不对。";
        hatch = true;
      } else if (ch.length) {
        strong = `改了 ${ch.length} 处：${ch.map(c => c.text).join("；")}`;
        quiet = when;
      } else if (sheet.savedAt) {
        strong = `已保存 · ${hhmm(sheet.savedAt)}`;
        quiet = "从下一个新起的 agent 开始用；已经在跑的不受影响。";
      } else {
        strong = "没有改动";
        quiet = "上面就是下一个新起的 agent 会用的配置。";
      }
      const rb = bads("runner");
      const at = sheet.modifiedAt;
      return {
        store: catalog.store,
        rows,
        runner: draft.runner,
        runnerCls: cls("runner", "runner"),
        runnerOpts: L.runnerOptions(draft, catalog),
        runnerOff: sheet.scanning,
        runnerBads: rb,
        runnerHasBad: rb.length > 0,
        chips: L.hostChips(scan, draft, catalog).map(c => ({
          cls: "hs " + (sheet.scanning ? "" : c.state),
          host: c.host,
          what: sheet.scanning ? "…" : c.what
        })),
        scanning: sheet.scanning,
        scanningText: L.source(draft) === "paseo" ? "正在向 Paseo 要每个 host 的 model…" : "正在问每个 host 的 CLI 有哪些 model…",
        scannedText: `${sheet.scannedAt ? hhmm(sheet.scannedAt) : ""} 问${sheet.scanSource === "paseo" ? " Paseo" : "各 host 的 CLI"} ·`,
        refused: !!sheet.refused,
        refusedText: `这一页打开之后，本机配置在 ${at ? hhmm(at) : ""} 被别处改过（一个 agent 从命令行改的）。重新读取会换成现在保存着的内容，你刚才改的 ${sheet.refused} 处要再改一次。`,
        strong,
        quiet,
        hatch,
        closeLabel: ch.length ? "取消" : "关闭",
        saveOff: !ch.length || probs.length > 0 || !!sheet.scanning || !!sheet.refused,
        changed: ch.length > 0
      };
    }
    MMW['local-config'] = {
      CATALOG,
      LocalConfig,
      catalogFromPayload,
      settingsView
    };
    Object.assign(MMW, MMW['local-config']);
  })();
  // ── topbar.mjs ──
  (function () {
    const {
      Board,
      LAMP_WORD
    } = MMW;
    const {
      el,
      hand,
      hhmm,
      minutes
    } = MMW;
    const REFRESH_ICON = '<svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path></svg>';
    const GEAR_ICON = '<svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg>';
    function clockFrom(text) {
      return (text || "").match(/(\d{2}:\d{2})/)?.[1] || "";
    }
    function agoFrom(text) {
      return Number((text || "").match(/（(\d+) 分钟前）/)?.[1] || 0);
    }
    function fromScene(data = {}) {
      const v = data.vals?.v || {};
      return {
        orangeN: v.orangeN ?? 0,
        greenN: v.greenN ?? 0,
        hollowN: v.hollowN ?? 0,
        inkN: v.inkN ?? 0,
        waiting: v.hasWaiting ? Number((v.waitingSub || "").match(/(\d+)/)?.[1] || 0) : 0,
        readFailed: (v.readCls || "").includes("failed"),
        readClock: clockFrom(v.readText),
        readAgo: agoFrom(v.readText),
        settingsOpen: (data.vals?.gearCls || "gear") === "gear on"
      };
    }
    function fromBoard(payload = {}, now = new Date()) {
      const tasks = payload.tasks || [];
      const all = tasks.flatMap(task => Board.allTickets(task));
      const count = lamp => all.filter(ticket => Board.lamp(ticket) === lamp).length;
      const waiting = all.filter(ticket => Board.phase(ticket) === "waiting").length;
      const readAt = payload.read_failed?.at || payload.read_at;
      return {
        orangeN: count("orange"),
        greenN: count("green"),
        hollowN: count("hollow"),
        inkN: count("ink"),
        waiting,
        readFailed: Boolean(payload.read_failed),
        readClock: readAt ? hhmm(readAt) : "",
        readAgo: readAt ? minutes(readAt, now) : 0,
        settingsOpen: Boolean(payload.settingsOpen)
      };
    }
    async function notify(method, hook) {
      await hand(async () => {
        const response = await method();
        if (response.ok) hook?.(await response.json());
      });
    }
    function render(host, view = {}, api, hooks = {}) {
      const orangeN = view.orangeN ?? 0;
      const hot = orangeN > 0;
      const waiting = view.waiting || 0;
      const read = view.readFailed ? {
        cls: "readstate failed",
        text: `读 GitHub 失败 · 下面是 ${view.readClock} 的数据（${view.readAgo} 分钟前）`
      } : {
        cls: "readstate",
        text: view.readClock ? `只读 · ${view.readClock} 读取` : ""
      };
      const root = el("header", {
        class: "topbar board"
      });
      root.dataset.screen = "topbar";
      root.append(el("div", {
        class: "brand"
      }, el("span", {
        class: "brand-mark"
      }, "MMW"), el("span", {
        class: "brand-name"
      }, "task board"), el("span", {
        class: "brand-repo"
      }, "chancheuklap/multi-model-workflow")), el("div", {
        class: "counters"
      }, el("button", {
        type: "button",
        class: hot ? "counter hot" : "counter",
        disabled: !hot,
        title: "跳到下一张 needs you 的 ticket",
        onClick: () => hooks.onJumpNeedYou?.()
      }, el("span", {
        class: hot ? "lamp orange" : "lamp hollow"
      }), LAMP_WORD.orange, el("span", {
        class: hot ? "counter-n hot" : "counter-n"
      }, String(orangeN))), el("span", {
        class: "counter"
      }, el("span", {
        class: "lamp green"
      }), LAMP_WORD.green, el("span", {
        class: "counter-n"
      }, String(view.greenN ?? 0)), waiting ? el("span", {
        class: "counter-sub"
      }, `waiting for a slot ${waiting}`) : null), el("span", {
        class: "counter"
      }, el("span", {
        class: "lamp hollow"
      }), LAMP_WORD.hollow, el("span", {
        class: "counter-n"
      }, String(view.hollowN ?? 0))), el("span", {
        class: "counter"
      }, el("span", {
        class: "lamp ink"
      }), LAMP_WORD.ink, el("span", {
        class: "counter-n"
      }, String(view.inkN ?? 0)))), el("div", {
        class: read.cls
      }, read.text), el("button", {
        type: "button",
        class: "gear",
        "aria-label": "立刻重读 GitHub",
        title: "立刻重读 GitHub（页面开着时每分钟自动读一次）",
        html: REFRESH_ICON,
        onClick: () => {
          void notify(() => api.refresh(), hooks.onRefresh);
        }
      }), el("button", {
        type: "button",
        class: view.settingsOpen ? "gear on" : "gear",
        "aria-label": "本机配置",
        title: "本机配置：每个 agent 跑在哪个 host、model、effort",
        html: GEAR_ICON,
        onClick: () => {
          void notify(() => api.settings(), hooks.onOpenSettings);
        }
      }));
      host.replaceChildren(root);
      return root;
    }
    MMW['topbar'] = {
      fromScene,
      fromBoard,
      render
    };
  })();
  // ── tasks.mjs ──
  (function () {
    const {
      Board,
      LAMP_WORD
    } = MMW;
    function markOn(row, selectedTask) {
      const on = row.n === selectedTask;
      return {
        ...row,
        cls: on ? "task on" : "task",
        titleCls: on ? "task-title on" : "task-title"
      };
    }
    function taskListView(tasks, selectedTask) {
      return {
        count: tasks.length,
        empty: !tasks.length,
        rows: tasks.map(task => {
          const progress = Board.progress(task);
          const lamp = Board.aggregate(Board.allTickets(task));
          return markOn({
            n: task.n,
            lampCls: "lamp " + lamp,
            lampWord: LAMP_WORD[lamp],
            meta: `#${task.n} · ${task.kind}`,
            title: task.title,
            barStyle: {
              width: (progress.total ? 100 * progress.done / progress.total : 0) + "%"
            },
            count: `${progress.done}/${progress.total} landed`
          }, selectedTask);
        })
      };
    }
    function rowsFor(data, selectedTask) {
      if (Array.isArray(data.tasks)) return taskListView(data.tasks, selectedTask);
      if (data.view) {
        return {
          count: data.view.count,
          empty: data.view.empty,
          rows: data.view.rows.map(row => markOn(row, selectedTask))
        };
      }
      return {
        count: 0,
        empty: true,
        rows: []
      };
    }
    function rowButton(row, onPick) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = row.cls;
      button.addEventListener("click", () => onPick(row.n));
      const lamp = document.createElement("span");
      lamp.className = row.lampCls;
      lamp.title = row.lampWord;
      const meta = document.createElement("span");
      meta.className = "task-meta";
      meta.textContent = row.meta;
      const title = document.createElement("span");
      title.className = row.titleCls;
      title.textContent = row.title;
      const fill = document.createElement("span");
      fill.className = "bar-fill";
      fill.style.width = row.barStyle.width;
      const bar = document.createElement("span");
      bar.className = "bar";
      bar.append(fill);
      const count = document.createElement("span");
      count.className = "task-count";
      count.textContent = row.count;
      const progress = document.createElement("span");
      progress.className = "task-progress";
      progress.append(bar, count);
      button.append(lamp, meta, title, progress);
      return button;
    }
    function render(host, data = {}, api = undefined) {
      const root = document.createElement("nav");
      root.dataset.screen = "tasks";
      root.className = "tasks board";
      root.setAttribute("aria-label", "The Night");
      const paint = selectedTask => {
        const next = rowsFor(data, selectedTask);
        const eyebrow = document.createElement("div");
        eyebrow.className = "col-eyebrow";
        const label = document.createElement("span");
        label.textContent = "The Night";
        const count = document.createElement("span");
        count.textContent = String(next.count);
        eyebrow.append(label, count);
        const kids = [eyebrow];
        if (next.empty) {
          const empty = document.createElement("p");
          empty.className = "tasks-empty";
          empty.textContent = "没有带 mmw:map label 的 ticket。";
          kids.push(empty);
        }
        for (const row of next.rows) {
          kids.push(rowButton(row, n => {
            paint(n);
            data.onSelectTask?.(n);
          }));
        }
        root.replaceChildren(...kids);
      };
      paint(data.selectedTask ?? null);
      host.replaceChildren(root);
      return root;
    }
    MMW['tasks'] = {
      taskListView,
      render
    };
  })();
  // ── canvas.mjs ──
  (function () {
    const {
      Board,
      LAMP_WORD,
      defaultExpanded
    } = MMW;
    const BEAM_SPEED = 170; // px per second
    const COMET = [
    // length px, stroke width, colour, opacity — tail first, head last
    [64, 3.4, "#22a06b", 0.10], [40, 3.2, "#22a06b", 0.22], [24, 3.0, "#2fbf7e", 0.45], [12, 2.8, "#46d894", 0.85], [5, 2.6, "#effff6", 1]];
    const mounted = new WeakMap();
    function px(n) {
      return Math.round(n * 10) / 10 + "px";
    }
    function prefersReduced() {
      return Boolean(typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches);
    }
    function curveLength([x1, y1], [x2, y2]) {
      const dx = Math.max(28, (x2 - x1) * 0.55);
      const points = [[x1, y1], [x1 + dx, y1], [x2 - dx, y2], [x2, y2]];
      let len = 0,
        prev = points[0];
      for (let i = 1; i <= 32; i++) {
        const t = i / 32,
          u = 1 - t;
        const pt = [0, 1].map(k => u * u * u * points[0][k] + 3 * u * u * t * points[1][k] + 3 * u * t * t * points[2][k] + t * t * t * points[3][k]);
        len += Math.hypot(pt[0] - prev[0], pt[1] - prev[1]);
        prev = pt;
      }
      return len;
    }
    function beamSVG(edge, reduced) {
      if (reduced) return `<path class="e-beam still" d="${edge.d}"/>`;
      const [a, b] = edge.ends;
      const len = curveLength(a, b);
      const tail = COMET[0][0];
      const dur = Math.max(0.9, (len + tail) / BEAM_SPEED);
      const begin = -((a[0] * 7 + a[1] * 3 + b[1]) / 53 % dur);
      const f = n => +n.toFixed(2);
      const layers = COMET.map(([length, width, color, opacity]) => `<path d="${edge.d}" stroke="${color}" stroke-opacity="${opacity}" stroke-width="${width}" stroke-dasharray="${f(length)} ${f(len + tail * 3)}" stroke-dashoffset="${f(length)}"><animate attributeName="stroke-dashoffset" from="${f(length)}" to="${f(length - len - tail)}" dur="${f(dur)}s" begin="${f(begin)}s" repeatCount="indefinite"/></path>`).join("");
      const arrive = begin + dur * len / (len + tail);
      return `<g class="e-beam">${layers}</g><circle class="e-pulse" cx="${b[0]}" cy="${b[1]}" r="2.6" opacity="0"><animate attributeName="r" values="2.6;11" dur="${f(dur)}s" begin="${f(arrive)}s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.7;0" dur="${f(dur)}s" begin="${f(arrive)}s" repeatCount="indefinite"/></circle>`;
    }
    function edgesSVG(layout, sel, selIsIssue, reduced) {
      const order = {
        done: 0,
        blocked: 1,
        flow: 2
      };
      const blocks = layout.edges.filter(edge => edge.kind === "block").sort((a, b) => order[a.state] - order[b.state]);
      const lines = layout.edges.filter(edge => edge.kind !== "block").map(edge => `<path class="${edge.kind === "trunk" ? "e-trunk" : "e-expand"}" d="${edge.d}"/>` + (edge.kind === "expand" && edge.state === "flow" ? beamSVG(edge, reduced) : "")).join("");
      const curves = blocks.map(edge => {
        const hot = selIsIssue && (edge.from === sel || edge.to === sel);
        const cls = `e-block ${edge.state}${hot ? " hot" : ""}${edge.cyc ? " cyc" : ""}`;
        const ports = edge.ends.map(([x, y]) => `<circle class="e-port ${edge.state}" cx="${x}" cy="${y}" r="2.6"/>`).join("");
        return `<path class="${cls}" d="${edge.d}"/>${edge.state === "flow" ? beamSVG(edge, reduced) : ""}${ports}`;
      }).join("");
      return `<svg class="edges" width="${layout.W}" height="${layout.H}" viewBox="0 0 ${layout.W} ${layout.H}" aria-hidden="true">${lines}${curves}</svg>`;
    }
    function stillEdges(svg) {
      if (!svg) return svg;
      return svg.replace(/<g class="e-beam">[\s\S]*?<\/g>/g, match => {
        const d = /d="([^"]+)"/.exec(match);
        return d ? `<path class="e-beam still" d="${d[1]}"/>` : "";
      }).replace(/<circle class="e-pulse"[^>]*>[\s\S]*?<\/circle>/g, "");
    }
    function canvasView(task, sel, expandedList, reduced) {
      if (!task) {
        return {
          hasTask: false,
          noTask: true,
          containers: [],
          decisions: [],
          tickets: [],
          labels: [],
          worldSize: {},
          svg: "",
          layout: null
        };
      }
      const expanded = new Set(expandedList);
      const layout = Board.layout(task, expanded);
      const selNode = layout.nodes.find(node => node.id === sel);
      const selIsIssue = Boolean(selNode && (selNode.type === "ticket" || selNode.type === "decision"));
      const pos = node => ({
        left: px(node.x),
        top: px(node.y),
        width: px(node.w),
        height: px(node.h)
      });
      const containers = [],
        decisions = [],
        tickets = [];
      for (const node of layout.nodes) {
        const on = node.id === sel;
        if (node.type === "ticket") {
          const ticket = node.ref,
            lamp = Board.lamp(ticket),
            phase = Board.phase(ticket),
            run = Board.runLine(ticket);
          tickets.push({
            n: ticket.n,
            pos: pos(node),
            title: ticket.title,
            num: "#" + ticket.n,
            phase,
            pillCls: "pill " + phase,
            cls: "card" + (on ? " on" : "") + (ticket.closeout ? " closeout" : "") + (node.cyclic ? " cycle" : ""),
            lampCls: "lamp " + lamp,
            lampWord: LAMP_WORD[lamp],
            run: run.text,
            runCls: run.flag ? "card-run flag" : "card-run"
          });
        } else if (node.type === "decision") {
          const decision = node.ref;
          decisions.push({
            n: decision.n,
            pos: pos(node),
            title: decision.title,
            num: "#" + decision.n,
            kind: decision.kind,
            cls: "card" + (on ? " on" : "") + (node.cyclic ? " cycle" : ""),
            lampCls: "lamp small " + Board.decisionLamp(decision)
          });
        } else {
          const container = node.ref,
            isMap = node.type === "map";
          const list = isMap ? Board.allTickets(container) : container.tickets;
          const lamp = Board.aggregate(list);
          const done = list.filter(ticket => Board.done(ticket)).length;
          const canExpand = isMap ? container.decisions.length > 0 : container.tickets.length > 0;
          const open = expanded.has(container.n);
          containers.push({
            n: container.n,
            pos: pos(node),
            title: container.title,
            num: "#" + container.n + (isMap ? " · " + container.kind : ""),
            cls: "card" + (on ? " on" : ""),
            titleCls: isMap ? "card-title map container" : "card-title container",
            lampCls: "lamp " + lamp,
            lampWord: LAMP_WORD[lamp],
            count: `${done}/${list.length}`,
            canExpand,
            chev: open ? "▾" : "▸",
            toggleLabel: (open ? "collapse #" : "expand #") + container.n,
            barStyle: {
              width: (list.length ? 100 * done / list.length : 0) + "%"
            }
          });
        }
      }
      return {
        hasTask: true,
        noTask: false,
        containers,
        decisions,
        tickets,
        labels: layout.labels.map(label => ({
          cls: label.warn ? "lane-label warn" : "lane-label",
          pos: {
            left: px(label.x),
            top: px(label.y)
          },
          text: label.text
        })),
        worldSize: {
          width: px(layout.W),
          height: px(layout.H)
        },
        svg: edgesSVG(layout, sel, selIsIssue, reduced),
        layout: {
          W: layout.W,
          H: layout.H,
          nodes: layout.nodes.map(node => ({
            id: node.id,
            x: node.x,
            y: node.y,
            w: node.w,
            h: node.h
          }))
        }
      };
    }
    function markSelected(view, sel) {
      const mark = items => items.map(item => ({
        ...item,
        cls: item.cls.split(" ").filter(name => name !== "on").join(" ") + (item.n === sel ? " on" : "")
      }));
      return {
        ...view,
        containers: mark(view.containers),
        decisions: mark(view.decisions),
        tickets: mark(view.tickets)
      };
    }
    function present(data, sel, expanded, reduced) {
      if (data.task && typeof data.task === "object") {
        return canvasView(data.task, sel, expanded, reduced);
      }
      if (!data.view) return canvasView(null);
      const view = reduced && data.view.svg ? {
        ...data.view,
        svg: stillEdges(data.view.svg)
      } : data.view;
      return markSelected(view, sel);
    }
    function cardHit(n, title, onPick) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "card-hit";
      button.setAttribute("aria-label", `#${n} ${title}`);
      button.addEventListener("click", () => onPick(n));
      return button;
    }
    function cardShell(item, onPick, {
      lampTitle,
      titled,
      titleCls,
      right,
      after
    }) {
      const card = document.createElement("div");
      card.className = item.cls;
      Object.assign(card.style, item.pos);
      if (titled) card.title = item.title;
      const lamp = document.createElement("span");
      lamp.className = item.lampCls;
      if (lampTitle) lamp.title = item.lampWord;
      const num = document.createElement("span");
      num.className = "card-num";
      num.textContent = item.num;
      const rightEl = document.createElement("span");
      rightEl.className = "card-right";
      rightEl.append(...right);
      const top = document.createElement("div");
      top.className = "card-top";
      top.append(lamp, num, rightEl);
      const title = document.createElement("div");
      title.className = titleCls;
      title.textContent = item.title;
      card.append(cardHit(item.n, item.title, onPick), top, title, ...after);
      return card;
    }
    function containerCard(item, onPick, onToggle) {
      const count = document.createElement("span");
      count.className = "card-count";
      count.textContent = item.count;
      const right = [count];
      if (item.canExpand) {
        const chev = document.createElement("button");
        chev.type = "button";
        chev.className = "chev";
        chev.setAttribute("aria-label", item.toggleLabel);
        chev.textContent = item.chev;
        chev.addEventListener("click", event => {
          event.stopPropagation();
          onToggle(item.n);
        });
        right.push(chev);
      }
      const fill = document.createElement("div");
      fill.className = "card-bar-fill";
      fill.style.width = item.barStyle.width;
      const bar = document.createElement("div");
      bar.className = "card-bar";
      bar.append(fill);
      return cardShell(item, onPick, {
        lampTitle: true,
        titled: true,
        titleCls: item.titleCls,
        right,
        after: [bar]
      });
    }
    function decisionCard(item, onPick) {
      const kind = document.createElement("span");
      kind.className = "card-kind";
      kind.textContent = item.kind;
      return cardShell(item, onPick, {
        lampTitle: false,
        titled: true,
        titleCls: "card-title decision",
        right: [kind],
        after: []
      });
    }
    function ticketCard(item, onPick) {
      const pill = document.createElement("span");
      pill.className = item.pillCls;
      pill.textContent = item.phase;
      const run = document.createElement("div");
      run.className = item.runCls;
      run.textContent = item.run;
      return cardShell(item, onPick, {
        lampTitle: true,
        titled: true,
        titleCls: "card-title",
        right: [pill],
        after: [run]
      });
    }
    function legend() {
      const root = document.createElement("div");
      root.className = "legend";
      const item = (lineClass, text) => {
        const span = document.createElement("span");
        span.className = "legend-item";
        const line = document.createElement("span");
        line.className = lineClass;
        span.append(line, text);
        return span;
      };
      const bar = document.createElement("span");
      bar.className = "legend-item";
      const mark = document.createElement("span");
      mark.className = "legend-bar";
      bar.append(mark, "closing pass");
      root.append(item("legend-line", "contains · released"), item("legend-line flow", "released · working"), item("legend-line blocked", "blocked"), bar);
      return root;
    }
    function zoomBar(onOut, onIn, onFit, level) {
      const root = document.createElement("div");
      root.className = "zoom";
      const out = document.createElement("button");
      out.type = "button";
      out.className = "zoom-btn";
      out.setAttribute("aria-label", "zoom out");
      out.textContent = "−";
      out.addEventListener("click", onOut);
      const zoomLevel = document.createElement("span");
      zoomLevel.className = "zoom-level";
      zoomLevel.textContent = level;
      const inn = document.createElement("button");
      inn.type = "button";
      inn.className = "zoom-btn";
      inn.setAttribute("aria-label", "zoom in");
      inn.textContent = "+";
      inn.addEventListener("click", onIn);
      const sep = document.createElement("span");
      sep.className = "zoom-sep";
      const fit = document.createElement("button");
      fit.type = "button";
      fit.className = "zoom-btn text";
      fit.textContent = "fit";
      fit.addEventListener("click", onFit);
      root.append(out, zoomLevel, inn, sep, fit);
      return {
        root,
        zoomLevel
      };
    }
    function emptyState() {
      const root = document.createElement("div");
      root.className = "canvas-empty";
      const wrap = document.createElement("div");
      const title = document.createElement("p");
      title.className = "canvas-empty-title";
      title.textContent = "The Night 还没开始";
      const text = document.createElement("p");
      text.className = "canvas-empty-text";
      text.append("The Night 是一次讨论开出的那张 ticket。给它打上 ");
      const code = document.createElement("span");
      code.className = "code";
      code.textContent = "mmw:map";
      text.append(code, " label，下一次读取时它和它下面的 spec、ticket 就会出现在这里。");
      wrap.append(title, text);
      root.append(wrap);
      return root;
    }
    function clampK(k) {
      return Math.min(1.6, Math.max(0.3, k));
    }
    function startingExpanded(data) {
      if (data.expanded != null) return [...data.expanded];
      if (data.task && typeof data.task === "object") return [...defaultExpanded(data.task)];
      return [];
    }
    function render(host, data = {}, api = undefined) {
      const prior = mounted.get(host);
      if (prior) prior.cleanup();

      // Pan and zoom belong to the person looking at the canvas, not to the data behind it: a
      // redraw of the same task carries the viewport over, and only a different task is fitted
      // afresh.
      const taskKey = data.task && typeof data.task === "object" ? data.task.n : null;
      const kept = prior && prior.taskKey === taskKey ? prior.state : null;
      const reduced = prefersReduced();
      const state = {
        sel: data.sel ?? null,
        expanded: startingExpanded(data),
        view: kept ? kept.view : {
          x: 20,
          y: 12,
          k: 1
        },
        didInit: Boolean(kept && kept.didInit),
        drag: null,
        suppress: false
      };
      // A card picked anywhere but here (the topbar's jump, a link in the detail column) can
      // land outside the viewport; one the user clicked on the canvas is already inside it.
      const toReveal = kept && state.sel != null && state.sel !== kept.sel;
      const root = document.createElement("main");
      root.dataset.screen = "canvas";
      root.className = "canvas board";
      root.setAttribute("aria-label", "画布：拖动平移，按住 ⌘ 或双指捏合缩放");
      let worldEl, zoomEl, lastView;
      const size = () => ({
        width: root.offsetWidth,
        height: root.offsetHeight
      });
      const applyView = () => {
        const v = state.view;
        if (worldEl) worldEl.style.transform = `translate(${v.x}px, ${v.y}px) scale(${v.k})`;
        if (zoomEl) zoomEl.textContent = Math.round(v.k * 100) + "%";
      };
      const box = n => lastView?.layout?.nodes.find(node => node.id === n) || null;
      const initialView = () => {
        const layout = lastView?.layout;
        if (!layout) return;
        const r = size();
        if (!r.width || !r.height) return;
        const kFit = Math.min((r.width - 40) / layout.W, (r.height - 70) / layout.H);
        const v = state.view = {
          k: clampK(Math.max(0.9, Math.min(1, kFit))),
          x: 20,
          y: 12
        };
        const b = state.sel != null ? box(state.sel) : null;
        if (b) {
          if ((b.y + b.h) * v.k + v.y > r.height - 70) v.y = Math.min(12, r.height * 0.45 - (b.y + b.h / 2) * v.k);
          if ((b.x + b.w) * v.k + v.x > r.width - 24) v.x = Math.min(20, r.width - 24 - (b.x + b.w) * v.k);
        }
        applyView();
        state.didInit = true;
      };
      const zoomAt = (k2, cx, cy) => {
        const v = state.view;
        k2 = clampK(k2);
        v.x = cx - (cx - v.x) * (k2 / v.k);
        v.y = cy - (cy - v.y) * (k2 / v.k);
        v.k = k2;
        applyView();
      };
      const fitView = () => {
        const layout = lastView?.layout;
        if (!layout) return;
        const r = size();
        const k = clampK(Math.min(1, (r.width - 40) / layout.W, (r.height - 70) / layout.H));
        state.view = {
          k,
          x: Math.max(12, (r.width - layout.W * k) / 2),
          y: 12
        };
        applyView();
      };

      // The smallest pan that puts the selected card inside the viewport; zoom is left alone.
      const revealSel = () => {
        const b = box(state.sel);
        if (!b) return;
        const r = size();
        if (!r.width || !r.height) return;
        const v = state.view,
          pad = 24,
          foot = 60; // foot: the zoom bar's own strip
        const left = b.x * v.k + v.x,
          right = (b.x + b.w) * v.k + v.x;
        const top = b.y * v.k + v.y,
          bottom = (b.y + b.h) * v.k + v.y;
        let dx = 0,
          dy = 0;
        if (right > r.width - pad) dx = r.width - pad - right;
        if (left + dx < pad) dx = pad - left;
        if (bottom > r.height - foot) dy = r.height - foot - bottom;
        if (top + dy < pad) dy = pad - top;
        if (!dx && !dy) return;
        v.x += dx;
        v.y += dy;
        applyView();
      };
      const center = () => {
        const r = size();
        return [r.width / 2, r.height / 2];
      };
      const paint = () => {
        lastView = present(data, state.sel, state.expanded, reduced);
        root.replaceChildren();
        worldEl = zoomEl = null;
        if (!lastView.hasTask) {
          root.append(emptyState());
          return;
        }
        const world = document.createElement("div");
        world.className = "world";
        Object.assign(world.style, lastView.worldSize);
        worldEl = world;
        const edges = document.createElement("div");
        edges.className = "edges-host";
        edges.innerHTML = lastView.svg || "";
        world.append(edges);
        for (const label of lastView.labels) {
          const node = document.createElement("div");
          node.className = label.cls;
          Object.assign(node.style, label.pos);
          node.textContent = label.text;
          world.append(node);
        }
        for (const item of lastView.containers) world.append(containerCard(item, choose, toggleOpen));
        for (const item of lastView.decisions) world.append(decisionCard(item, choose));
        for (const item of lastView.tickets) world.append(ticketCard(item, choose));
        const zoom = zoomBar(() => {
          const [cx, cy] = center();
          zoomAt(state.view.k / 1.2, cx, cy);
        }, () => {
          const [cx, cy] = center();
          zoomAt(state.view.k * 1.2, cx, cy);
        }, fitView, Math.round(state.view.k * 100) + "%");
        zoomEl = zoom.zoomLevel;
        root.append(world, legend(), zoom.root);
        if (!state.didInit) initialView();else applyView();
      };
      const choose = n => {
        if (state.suppress) return;
        state.sel = n;
        data.onSelectNode?.(n);
        paint();
      };
      const toggleOpen = n => {
        const expanded = new Set(state.expanded);
        if (expanded.has(n)) expanded.delete(n);else expanded.add(n);
        state.expanded = [...expanded];
        data.onToggle?.(n, state.expanded);
        paint();
      };
      const onPointerDown = event => {
        if (event.button !== 0 || event.target.closest?.(".zoom, .legend, .chev")) return;
        state.drag = {
          x: event.clientX,
          y: event.clientY,
          vx: state.view.x,
          vy: state.view.y,
          moved: false,
          id: event.pointerId
        };
      };
      const onWheel = event => {
        if (!lastView?.layout) return;
        event.preventDefault();
        const r = root.getBoundingClientRect();
        if (event.ctrlKey || event.metaKey) zoomAt(state.view.k * Math.exp(-event.deltaY * 0.01), event.clientX - r.left, event.clientY - r.top);else {
          state.view.x -= event.deltaX;
          state.view.y -= event.deltaY;
          applyView();
        }
      };
      const onMove = event => {
        const drag = state.drag;
        if (!drag || event.pointerId !== drag.id) return;
        const dx = event.clientX - drag.x,
          dy = event.clientY - drag.y;
        if (!drag.moved && Math.hypot(dx, dy) > 4) {
          drag.moved = true;
          root.classList.add("dragging");
        }
        if (drag.moved) {
          state.view.x = drag.vx + dx;
          state.view.y = drag.vy + dy;
          applyView();
        }
      };
      const onUp = event => {
        const drag = state.drag;
        if (!drag || event.pointerId !== drag.id) return;
        state.drag = null;
        root.classList.remove("dragging");
        if (drag.moved) {
          state.suppress = true;
          setTimeout(() => {
            state.suppress = false;
          }, 0);
        }
      };
      const onKey = event => {
        if (event.target.closest?.("input, textarea, [contenteditable]")) return;
        if ((event.key === "f" || event.key === "F") && !event.metaKey && !event.ctrlKey) fitView();
      };
      root.addEventListener("pointerdown", onPointerDown);
      root.addEventListener("wheel", onWheel, {
        passive: false
      });
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
      window.addEventListener("keydown", onKey);
      paint();
      host.replaceChildren(root);
      if (!state.didInit) queueMicrotask(initialView);else if (toReveal) queueMicrotask(revealSel);
      let observer;
      if (typeof ResizeObserver === "function") {
        observer = new ResizeObserver(() => {
          if (!state.didInit) initialView();
        });
        observer.observe(root);
      }
      mounted.set(host, {
        taskKey,
        state,
        cleanup() {
          root.removeEventListener("pointerdown", onPointerDown);
          root.removeEventListener("wheel", onWheel);
          window.removeEventListener("pointermove", onMove);
          window.removeEventListener("pointerup", onUp);
          window.removeEventListener("keydown", onKey);
          observer?.disconnect();
        }
      });
      return root;
    }
    MMW['canvas'] = {
      stillEdges,
      canvasView,
      render
    };
  })();
  // ── detail.mjs ──
  (function () {
    const {
      Board,
      LAMP_WORD,
      PHASES,
      eventBlocks,
      blockSummary
    } = MMW;
    const {
      el
    } = MMW;
    const NEEDS_YOU = new Set(["decision", "fault", "contract"]);
    function lampFrom(cls) {
      if (!cls) return "hollow";
      if (/\borange\b/.test(cls)) return "orange";
      if (/\bgreen\b/.test(cls)) return "green";
      if (/\bink\b/.test(cls)) return "ink";
      if (/\bnone\b/.test(cls)) return "none";
      return "hollow";
    }
    function kindOf(d) {
      if (d.isTicket) return "ticket";
      if (d.isMap) return "map";
      if (d.isSpec) return "spec";
      if (d.isDecision) return "decision";
      return "empty";
    }
    function firstRows(...candidates) {
      return candidates.find(rows => Array.isArray(rows) && rows.length) || [];
    }
    function relFrom(row) {
      return {
        n: row.n,
        num: row.num,
        title: row.title,
        where: row.where || "",
        lamp: lampFrom(row.lampCls),
        state: row.state,
        phase: row.phase,
        hold: Boolean(row.hold || row.showHold),
        unknown: Boolean(row.unknown || row.known === false)
      };
    }
    function phaseItemFrom(item) {
      return {
        event: item.event,
        time: item.time,
        name: item.name,
        text: item.text || "",
        hasText: item.hasText ?? Boolean(item.text),
        tone: item.tone || "plain",
        detail: item.detail || []
      };
    }
    function fromScene(data = {}) {
      const vals = data.vals || {};
      const d = vals.d || {};
      const hasCard = d.hasCard ?? Boolean(d.isTicket || d.isMap || d.isSpec || d.isDecision || d.isContainer);
      if (!hasCard) {
        return {
          empty: true,
          emptyTitle: vals.emptyTitle || "点一张卡",
          emptyText: vals.emptyText || "画布上任意一张卡——map、spec、ticket 或 decision ticket——点一下，它的全部细节就在这一栏。"
        };
      }
      const rawEvents = vals.rawEvents || d.rawEvents || [];
      const phaseBlocks = (vals.phaseBlocks || d.phaseBlocks || []).map(block => ({
        phase: block.phase,
        tone: block.tone || "plain",
        openByDefault: Boolean(block.openByDefault),
        summary: block.summary || "",
        from: block.from,
        span: block.span || (block.from !== block.to ? `${block.from}–${block.to}` : block.from),
        items: (block.items || []).map(phaseItemFrom)
      }));
      return {
        empty: false,
        repo: vals.repo,
        kind: kindOf(d),
        eyebrow: d.eyebrow,
        num: d.num,
        title: d.title,
        lamp: lampFrom(d.lampCls),
        statusWord: d.statusWord,
        elapsed: d.elapsed || "",
        phase: d.phase,
        why: d.why || [],
        links: vals.links || d.links || [],
        blockers: firstRows(vals.blockedBy, d.blockedBy, vals.blockers, d.blockers).map(relFrom),
        blocks: firstRows(vals.blocking, d.blocking, vals.blocks, d.blocks).map(relFrom),
        kids: firstRows(vals.kids, d.kids).map(row => ({
          num: row.num,
          kind: row.kind,
          title: row.title,
          lamp: lampFrom(row.lampCls),
          hot: Boolean(row.kindCls && row.kindCls.includes("hot")) || NEEDS_YOU.has(row.kind)
        })),
        rawEvents,
        eventCount: d.eventCount ?? rawEvents.length,
        phaseBlocks,
        runtime: d.hasRun ? {
          grade: d.runGrade,
          model: d.runModel,
          rows: d.runRows || []
        } : null,
        noRunText: d.noRunText || "not dispatched yet",
        gh: d.gh,
        ghLabel: d.ghLabel,
        listTitle: d.listTitle,
        listCount: d.listCount,
        lamps: (d.lamps || []).map(item => ({
          lamp: lampFrom(item.cls),
          word: item.word,
          n: item.n
        })),
        phases: (d.phases || []).map(item => ({
          phase: (item.cls || "").replace(/^pill\s+/, ""),
          label: item.label
        })),
        ticketRows: (vals.ticketRows || d.ticketRows || []).map(relFrom),
        specRows: (vals.specRows || d.specRows || []).map(relFrom),
        decisionRows: (vals.decisionRows || d.decisionRows || []).map(relFrom),
        specCount: d.specCount,
        decisionCount: d.decisionCount
      };
    }
    function find(tasks, n) {
      if (n == null) return null;
      for (const task of tasks) {
        if (task.n === n) {
          return task.kind === "spec" ? {
            type: "spec",
            ref: task.specs[0],
            task
          } : {
            type: "map",
            ref: task,
            task
          };
        }
        for (const decision of task.decisions || []) {
          if (decision.n === n) return {
            type: "decision",
            ref: decision,
            task
          };
        }
        for (const spec of task.specs || []) {
          if (spec.n === n) return {
            type: "spec",
            ref: spec,
            task
          };
          for (const ticket of spec.tickets || []) {
            if (ticket.n === n) return {
              type: "ticket",
              ref: ticket,
              task,
              spec
            };
          }
        }
      }
      return null;
    }
    function relRowFromBoard(tasks, n, role, hereSpec, thisTicket) {
      const found = find(tasks, n);
      if (!found) {
        return {
          n,
          num: `#${n}`,
          lamp: "none",
          title: "不在这棵树里，读不到它的状态",
          where: "",
          state: "unknown",
          unknown: true,
          hold: false
        };
      }
      let lamp,
        state,
        phase,
        hold = false;
      if (found.type === "ticket") {
        lamp = Board.lamp(found.ref);
        phase = Board.phase(found.ref);
        state = found.ref.fold.landed ? "landed" : role !== "blocker" ? LAMP_WORD[lamp] : Board.released(found.ref) ? "closed unpassed · released" : "not landed";
        hold = role === "blocker" ? !Board.released(found.ref) : Boolean(thisTicket) && !Board.released(thisTicket);
      } else if (found.type === "spec") {
        lamp = Board.aggregate(found.ref.tickets);
        state = `${found.ref.tickets.filter(ticket => Board.done(ticket)).length}/${found.ref.tickets.length}`;
      } else {
        lamp = Board.decisionLamp(found.ref);
        state = found.ref.state === "closed" ? "closed" : "open";
      }
      return {
        n,
        num: `#${n}`,
        lamp,
        title: found.ref.title,
        unknown: false,
        where: found.spec && found.spec.n !== hereSpec ? `spec #${found.spec.n}` : "",
        state,
        phase,
        hold
      };
    }
    function heldFirst(rows) {
      return [...rows].sort((a, b) => Number(b.hold) - Number(a.hold));
    }
    function phaseBlocksFrom(events) {
      const blocks = eventBlocks(events);
      return blocks.map((block, index) => ({
        phase: block.phase,
        tone: block.tone,
        openByDefault: index === blocks.length - 1 || block.tone !== "plain",
        summary: blockSummary(block),
        from: block.from,
        span: block.from !== block.to ? `${block.from}–${block.to}` : block.from,
        items: block.items.map(item => ({
          event: item.event,
          time: item.time,
          name: item.name,
          text: item.text,
          hasText: Boolean(item.text),
          tone: item.tone,
          detail: item.detail
        }))
      }));
    }
    function ticketView(tasks, found) {
      const ticket = found.ref,
        fold = ticket.fold,
        lamp = Board.lamp(ticket),
        phase = Board.phase(ticket);
      const started = [...ticket.events].reverse().find(event => event.event === "worker.started");
      const hasRun = Boolean(fold.worker && started);
      const payload = started && started.payload || {};
      const worktree = String(payload.worktree || "").split("/.worktrees/")[1];
      const slot = [...ticket.events].reverse().find(event => event.event === "ticket.checked" && event.payload?.slot != null);
      const runRows = [["ticket branch", payload.branch], ["base branch", payload.into], ["worktree", worktree ? `…/.worktrees/${worktree}` : payload.worktree], ["machine", payload.machine], ...(slot ? [["slot", String(slot.payload.slot)]] : [])].filter(([, value]) => value).map(([k, v]) => ({
        k,
        v
      }));
      const blockers = ticket.blocked.map(n => relRowFromBoard(tasks, n, "blocker", found.spec.n, ticket));
      const blocking = found.spec.tickets.filter(item => item.blocked.includes(ticket.n)).map(item => relRowFromBoard(tasks, item.n, "blocked", found.spec.n, ticket));
      const kids = Object.values(fold.children);
      return {
        empty: false,
        kind: "ticket",
        eyebrow: "Ticket",
        num: `#${ticket.n}`,
        links: [{
          label: `spec #${found.spec.n}`,
          n: found.spec.n
        }, {
          label: `map #${found.task.n}`,
          n: found.task.n
        }],
        title: ticket.title,
        lamp,
        statusWord: LAMP_WORD[lamp],
        elapsed: Board.elapsed(ticket),
        phase,
        why: Board.why(ticket).map(item => item.child ? {
          head: `#${item.child} ${item.kind}`,
          body: `${item.title}。${item.text}`
        } : {
          head: "",
          body: item.text
        }),
        runtime: hasRun ? {
          grade: payload.grade || "",
          model: `${payload.host} · ${payload.model} · ${payload.effort}`,
          rows: runRows
        } : null,
        noRunText: phase === "landed" ? "closed without a run" : "not dispatched yet",
        blockers,
        blocks: blocking,
        kids: kids.map(child => ({
          num: `#${child.child}`,
          title: child.title,
          kind: child.kind,
          lamp: child.resolution ? "ink" : NEEDS_YOU.has(child.kind) ? "orange" : "hollow",
          hot: NEEDS_YOU.has(child.kind)
        })),
        rawEvents: ticket.events,
        eventCount: ticket.events.length,
        phaseBlocks: phaseBlocksFrom(ticket.events),
        gh: ticket.n
      };
    }
    function containerView(tasks, found) {
      const container = found.ref,
        isMap = found.type === "map";
      const list = isMap ? Board.allTickets(container) : container.tickets;
      const lamp = Board.aggregate(list);
      const countLight = key => list.filter(ticket => Board.lamp(ticket) === key).length;
      const countPhase = key => list.filter(ticket => Board.phase(ticket) === key).length;
      const done = list.filter(ticket => Board.done(ticket)).length;
      return {
        empty: false,
        kind: isMap ? "map" : "spec",
        eyebrow: isMap ? "The Night" : "Spec",
        num: `#${container.n}` + (isMap ? ` · ${container.kind}` : ""),
        links: isMap || found.task.n === container.n ? [] : [{
          label: `map #${found.task.n}`,
          n: found.task.n
        }],
        title: container.title,
        lamp,
        statusWord: LAMP_WORD[lamp],
        elapsed: `${done}/${list.length} landed`,
        listTitle: isMap ? "All tickets" : "Its tickets",
        listCount: list.length,
        lamps: ["orange", "green", "hollow", "ink"].filter(key => countLight(key)).map(key => ({
          lamp: key,
          word: LAMP_WORD[key],
          n: countLight(key)
        })),
        phases: PHASES.filter(phase => countPhase(phase)).map(phase => ({
          phase,
          label: `${phase} · ${countPhase(phase)}`
        })),
        specRows: isMap ? container.specs.map(spec => relRowFromBoard(tasks, spec.n, "spec", null)) : [],
        specCount: isMap ? container.specs.length : 0,
        decisionCount: isMap ? container.decisions.length : 0,
        decisionRows: isMap ? container.decisions.map(decision => relRowFromBoard(tasks, decision.n, "decision", null)) : [],
        ticketRows: isMap ? [] : container.tickets.map(ticket => {
          const phase = Board.phase(ticket);
          return {
            n: ticket.n,
            num: `#${ticket.n}`,
            lamp: Board.lamp(ticket),
            title: ticket.title,
            phase
          };
        }),
        gh: container.n,
        ghLabel: `在 GitHub 打开 #${container.n} ↗`,
        why: [],
        kids: [],
        blockers: [],
        blocks: []
      };
    }
    function decisionView(tasks, found) {
      const decision = found.ref,
        lamp = Board.decisionLamp(decision);
      const blocks = found.task.decisions.filter(item => item.blocked.includes(decision.n)).map(item => item.n);
      return {
        empty: false,
        kind: "decision",
        eyebrow: `Decision ticket · ${decision.kind}`,
        num: `#${decision.n}`,
        links: [{
          label: `map #${found.task.n}`,
          n: found.task.n
        }],
        title: decision.title,
        lamp,
        statusWord: decision.state === "closed" ? "settled" : "还开着",
        elapsed: "",
        blockers: decision.blocked.map(n => relRowFromBoard(tasks, n, "decision", null)),
        blocks: blocks.map(n => relRowFromBoard(tasks, n, "decision", null)),
        gh: decision.n,
        ghLabel: `在 GitHub 打开 #${decision.n} ↗`,
        why: [],
        kids: []
      };
    }
    function fromBoard(payload = {}, selected) {
      const tasks = payload.tasks || [];
      const found = find(tasks, selected);
      const empty = {
        empty: true,
        emptyTitle: tasks.length ? "点一张卡" : "这里是详情",
        emptyText: tasks.length ? "画布上任意一张卡——map、spec、ticket 或 decision ticket——点一下，它的全部细节就在这一栏。" : "The Night 开起来之后，点画布上的卡，它的细节显示在这一栏。",
        repo: payload.repo
      };
      if (!found) return empty;
      const view = found.type === "ticket" ? ticketView(tasks, found) : found.type === "decision" ? decisionView(tasks, found) : containerView(tasks, found);
      view.repo = payload.repo;
      return view;
    }
    function goto(hooks, n) {
      if (n == null) return;
      hooks.onGoto?.(n);
    }
    function openGithub(view) {
      if (view.gh != null && view.repo) {
        window.open(`https://github.com/${view.repo}/issues/${view.gh}`, "_blank", "noopener,noreferrer");
      }
    }
    function relRow(hooks, row) {
      const last = row.phase ? el("span", {
        class: `pill ${row.phase}`
      }, row.phase) : el("span", {
        class: row.state === "not landed" ? "rel-state open" : "rel-state"
      }, row.state);
      const body = [el("span", {
        class: `lamp ${row.lamp}`
      }), el("span", {
        class: "rel-num"
      }, row.num), el("span", {
        class: "rel-title"
      }, row.title, " ", el("span", {
        class: "rel-where"
      }, row.where || "")), last];
      if (row.unknown) return el("div", {
        class: "rel-static"
      }, ...body);
      return el("button", {
        type: "button",
        class: "rel",
        onClick: () => goto(hooks, row.n)
      }, ...body);
    }
    function section(title, note, ...rows) {
      return el("section", {
        class: "dp-section"
      }, el("div", {
        class: "dp-section-title"
      }, el("span", {}, title), note == null ? null : el("span", {}, note)), ...rows);
    }
    function blockingSection(hooks, view, noneText) {
      return [section("Blocked by", view.blockers?.length || null, ...(view.blockers || []).map(row => relRow(hooks, row)), !view.blockers?.length ? el("p", {
        class: "rel-none"
      }, noneText) : null), section("Blocking", view.blocks?.length || null, ...(view.blocks || []).map(row => relRow(hooks, row)), !view.blocks?.length ? el("p", {
        class: "rel-none"
      }, "none") : null)];
    }
    function origin(hooks, view) {
      const parts = [el("span", {}, view.num)];
      for (const link of view.links || []) {
        parts.push(el("span", {}, "·"), el("button", {
          type: "button",
          class: "dp-link",
          onClick: () => goto(hooks, link.n)
        }, link.label));
      }
      return el("div", {
        class: "dp-origin"
      }, ...parts);
    }
    function ticketRelation(hooks, row) {
      const last = row.hold ? el("span", {
        class: "pv-rel-hold"
      }, "held") : row.phase ? el("span", {
        class: `pill ${row.phase}`
      }, row.phase) : el("span", {
        class: "pv-rel-s"
      }, row.state);
      const body = [el("span", {
        class: `lamp ${row.lamp}`
      }), el("span", {
        class: "pv-rel-n"
      }, row.num), el("span", {
        class: "pv-rel-t"
      }, row.title, row.where ? " " : null, row.where ? el("span", {
        class: "rel-where"
      }, row.where) : null), last];
      if (row.unknown) {
        return el("button", {
          type: "button",
          class: "pv-rel"
        }, ...body);
      }
      return el("button", {
        type: "button",
        class: row.hold ? "pv-rel hold" : "pv-rel",
        onClick: () => goto(hooks, row.n)
      }, ...body);
    }
    function ticketSection(title, count, ...rows) {
      return el("section", {
        class: "pv-sec"
      }, el("div", {
        class: "pv-sec-title"
      }, el("span", {}, title), el("span", {}, count)), ...rows);
    }
    function ticketRuntime(view) {
      if (view.runtime) {
        return el("div", {
          class: "pv-run"
        }, el("div", {
          class: "pv-run-who"
        }, el("span", {
          class: "pv-run-grade"
        }, view.runtime.grade || ""), view.runtime.model ? el("span", {
          class: "pv-run-model"
        }, view.runtime.model) : null), view.runtime.rows?.length ? el("div", {
          class: "pv-run-where"
        }, ...view.runtime.rows.flatMap(row => [el("span", {
          class: "pv-run-k"
        }, row.k), el("span", {
          class: "pv-run-v"
        }, row.v)])) : null);
      }
      return el("p", {
        class: "pv-none"
      }, view.noRunText || "not dispatched yet");
    }
    function backendDetail(rows) {
      return el("span", {
        class: "va-x"
      }, el("span", {
        class: "pv-detail"
      }, ...rows.flatMap(row => [el("span", {
        class: "pv-detail-k"
      }, row.k), el("span", {
        class: "pv-detail-v"
      }, row.v)])));
    }
    function eventRow(item, key, ui, repaint) {
      const opened = ui.openEvents.has(key);
      return el("button", {
        type: "button",
        class: "va-ev",
        "data-detail-key": key,
        onClick: () => {
          if (opened) ui.openEvents.delete(key);else ui.openEvents.add(key);
          repaint();
        }
      }, el("span", {
        class: "va-t"
      }, item.time), el("span", {
        class: item.tone === "warn" || item.tone === "needs-you" ? "va-n warn" : "va-n"
      }, item.name), item.hasText ? el("span", {
        class: "va-x"
      }, item.text) : null, opened ? backendDetail(item.detail) : null);
    }
    function phaseBlock(block, index, view, ui, repaint) {
      const key = `${view.gh}:b${index}`;
      const defaultOpen = block.openByDefault;
      const opened = ui.toggledBlocks.has(key) ? !defaultOpen : defaultOpen;
      const header = el("button", {
        type: "button",
        class: "va-bhead",
        "data-detail-key": key,
        onClick: () => {
          if (ui.toggledBlocks.has(key)) ui.toggledBlocks.delete(key);else ui.toggledBlocks.add(key);
          repaint();
        }
      }, el("span", {
        class: "va-chev"
      }, opened ? "▾" : "▸"), el("span", {
        class: `pill ${block.phase}`
      }, block.phase), el("span", {
        class: "va-bsum"
      }, opened ? "" : block.summary), el("span", {
        class: "va-btime"
      }, opened ? block.span : block.from));
      const card = el("div", {
        class: block.tone === "plain" ? "va-block" : "va-block warn"
      }, header);
      if (opened) {
        card.append(el("div", {
          class: "va-body"
        }, ...(block.items || []).map((item, itemIndex) => eventRow(item, `${key}:${itemIndex}`, ui, repaint))));
      }
      return card;
    }
    function ticketCard(hooks, view, ui, repaint) {
      const blocks = view.phaseBlocks || [];
      const parts = [el("div", {
        class: "pv-head"
      }, el("span", {
        class: "pv-eyebrow"
      }, view.eyebrow || "Ticket"), el("button", {
        type: "button",
        class: "pv-gh",
        onClick: () => openGithub(view)
      }, "GitHub ↗"), el("button", {
        type: "button",
        class: "pv-close",
        "aria-label": "关闭详情",
        onClick: () => hooks.onClose?.()
      }, "×")), el("h2", {
        class: "pv-title"
      }, view.title), el("div", {
        class: "pv-links"
      }, el("span", {}, view.num), ...(view.links || []).flatMap(link => [el("span", {}, "·"), el("button", {
        type: "button",
        class: "pv-link",
        onClick: () => goto(hooks, link.n)
      }, link.label)])), el("div", {
        class: "va-status"
      }, el("span", {
        class: `lamp big ${view.lamp}`
      }), el("span", {
        class: `va-word ${view.lamp}`
      }, view.statusWord), el("span", {
        class: `pill big ${view.phase}`
      }, view.phase), el("span", {
        class: "va-elapsed"
      }, view.elapsed || "")), ticketRuntime(view)];
      if (view.why?.length) {
        parts.push(el("div", {
          class: "pv-why"
        }, el("span", {
          class: "pv-why-t"
        }, "Needs you"), ...view.why.map(item => el("span", {}, el("b", {}, item.head), " ", item.body))));
      }
      if (view.blockers?.length) {
        parts.push(ticketSection("Blocked by", view.blockers.length, ...heldFirst(view.blockers).map(row => ticketRelation(hooks, row))));
      }
      if (view.blocks?.length) {
        parts.push(ticketSection("Blocking", view.blocks.length, ...heldFirst(view.blocks).map(row => ticketRelation(hooks, row))));
      }
      parts.push(ticketSection("Events", view.eventCount ?? (view.rawEvents || []).length, view.rawEvents?.length || blocks.length ? null : el("p", {
        class: "pv-none"
      }, "no events yet"), ...(blocks.length ? blocks.map((block, index) => phaseBlock(block, index, view, ui, repaint)) : [])));
      if (view.kids?.length) {
        parts.push(ticketSection("Sub-issues", view.kids.length, ...view.kids.map(kid => el("div", {
          class: "pv-rel"
        }, el("span", {
          class: `lamp ${kid.lamp}`
        }), el("span", {
          class: "pv-rel-n"
        }, kid.num), el("span", {
          class: "pv-rel-t"
        }, kid.title), el("span", {
          class: kid.hot ? "pv-kind hot" : "pv-kind"
        }, kid.kind)))));
      }
      return el("div", {
        class: "pv"
      }, ...parts);
    }
    function containerBody(hooks, view) {
      const kids = [section(view.listTitle, view.listCount, el("div", {
        class: "lamps-count"
      }, ...(view.lamps || []).map(item => el("span", {
        class: "lc-item"
      }, el("span", {
        class: `lamp ${item.lamp}`
      }), item.word, el("span", {
        class: "lc-n"
      }, item.n)))), el("div", {
        class: "phases-count"
      }, ...(view.phases || []).map(item => el("span", {
        class: `pill ${item.phase}`
      }, item.label))))];
      if (view.kind === "spec") {
        kids.push(section("By number", null, ...(view.ticketRows || []).map(row => relRow(hooks, row))));
      }
      if (view.kind === "map") {
        kids.push(section("spec", view.specCount, ...(view.specRows || []).map(row => relRow(hooks, row))));
        if (view.decisionRows?.length) {
          kids.push(section("Decision tickets", view.decisionCount, ...(view.decisionRows || []).map(row => relRow(hooks, row))));
        }
      }
      return kids;
    }
    function card(hooks, view) {
      const parts = [el("div", {
        class: "dp-head"
      }, el("span", {
        class: "dp-eyebrow"
      }, view.eyebrow), el("button", {
        type: "button",
        class: "dp-close",
        "aria-label": "关闭详情",
        onClick: () => hooks.onClose?.()
      }, "×")), origin(hooks, view), el("h2", {
        class: "dp-title"
      }, view.title), el("div", {
        class: "dp-status"
      }, el("span", {
        class: `lamp big ${view.lamp}`
      }), el("span", {
        class: `status-word ${view.lamp}`
      }, view.statusWord), el("span", {
        class: "dp-elapsed"
      }, view.elapsed || ""))];
      if (view.kind === "spec" || view.kind === "map") parts.push(...containerBody(hooks, view));
      if (view.kind === "decision") parts.push(...blockingSection(hooks, view, "none"));
      parts.push(el("button", {
        type: "button",
        class: "dp-gh",
        onClick: () => openGithub(view)
      }, view.ghLabel));
      return el("div", {
        class: "dp"
      }, ...parts);
    }
    function unmount(host) {
      if (!host) return;
      if (host._detailEsc) document.removeEventListener("keydown", host._detailEsc);
      host._detailEsc = null;
      host._detailRoot = null;
      host._detailUi = null;
      host.replaceChildren();
    }
    function render(host, view = {}, api, hooks = {}) {
      let root = host._detailRoot;
      if (!root) {
        root = el("aside", {
          class: "detail board",
          "aria-label": "详情"
        });
        root.dataset.screen = "detail";
        host._detailRoot = root;
        host.replaceChildren(root);
      }
      const ui = host._detailUi ||= {
        openEvents: new Set(),
        toggledBlocks: new Set()
      };
      const repaint = () => render(host, view, api, hooks);
      if (!view.empty && view.kind === "ticket") root.replaceChildren(ticketCard(hooks, view, ui, repaint));else if (!view.empty && view.kind) root.replaceChildren(card(hooks, view));else {
        root.replaceChildren(el("div", {
          class: "dp-empty"
        }, el("p", {
          class: "dp-empty-title"
        }, view.emptyTitle || "点一张卡"), view.emptyText || "画布上任意一张卡——map、spec、ticket 或 decision ticket——点一下，它的全部细节就在这一栏。"));
      }
      if (host._detailEsc) document.removeEventListener("keydown", host._detailEsc);
      host._detailEsc = event => {
        if (event.key === "Escape" && !view.empty && view.kind) hooks.onClose?.();
      };
      document.addEventListener("keydown", host._detailEsc);
      return root;
    }
    MMW['detail'] = {
      fromScene,
      find,
      fromBoard,
      unmount,
      render
    };
  })();
  // ── settings.mjs ──
  (function () {
    const {
      CATALOG,
      LocalConfig,
      catalogFromPayload,
      settingsView
    } = MMW;
    const {
      el,
      hand
    } = MMW;
    function copy(value) {
      return JSON.parse(JSON.stringify(value));
    }
    function selectEl(cls, value, disabled, label, opts, onChange) {
      const node = el("select", {
        class: cls,
        "aria-label": label,
        disabled: !!disabled,
        onChange: event => onChange(event.target.value)
      }, (opts || []).map(option => el("option", {
        value: option.value,
        disabled: !!option.disabled,
        label: option.text,
        selected: option.selected || option.value === value
      }, option.text)));
      if (value != null) node.value = value;
      return node;
    }
    function roleFoot(items) {
      if (!items?.length) return null;
      return el("div", {
        class: "role-foot"
      }, items.map(item => el("div", {
        class: "role-bad"
      }, el("span", {
        class: "hatch"
      }), item.text)));
    }
    function flagsFromErrors(errors) {
      return (errors || []).map(error => {
        const [key, cell] = String(error.cell || "").split(".");
        return {
          key,
          cell: cell || key,
          text: error.reason
        };
      });
    }
    function detachEsc(host) {
      if (!host._settingsEsc) return;
      document.removeEventListener("keydown", host._settingsEsc, true);
      host._settingsEsc = null;
    }
    function unmount(host) {
      detachEsc(host);
      host.replaceChildren();
    }
    function fromScene(data = {}) {
      const st = copy(data.state.st);
      st.version = st.saved?.version ?? 1;
      st.serverFlags = [];
      return {
        view: data.vals.v,
        st,
        catalog: CATALOG,
        scan: {}
      };
    }
    function fromPayload(payload) {
      const catalog = catalogFromPayload(payload);
      const saved = {
        runner: payload.runner,
        rows: copy(payload.rows)
      };
      return {
        catalog,
        scan: payload.scan.hosts,
        st: {
          saved,
          draft: copy(saved),
          scanSource: payload.scan.source,
          scannedAt: payload.scan.scanned_at,
          scanning: Boolean(payload.scan.scanning),
          savedAt: payload.saved_at || null,
          refused: 0,
          reread: false,
          version: payload.version,
          modifiedAt: payload.modified_at || null,
          serverFlags: []
        }
      };
    }
    function viewOf(model) {
      if (model.view) return model.view;
      return settingsView(model.st, model.scan, model.catalog);
    }
    function saveBody(model) {
      return {
        version: model.st.version,
        runner: model.st.draft.runner,
        rows: model.st.draft.rows
      };
    }
    async function readJson(response) {
      try {
        return await response.json();
      } catch {
        return {};
      }
    }
    function paint(host, model, api, hooks) {
      const v = viewOf(model);
      const close = () => {
        unmount(host);
        hooks.onClose?.();
      };
      const redraw = () => {
        model.view = null;
        paint(host, model, api, hooks);
      };
      const applyScan = body => {
        model.scan = body.hosts;
        model.st.scanSource = body.source;
        model.st.scannedAt = body.scanned_at;
        model.st.scanning = Boolean(body.scanning);
        redraw();
      };
      const rescan = async source => {
        model.st.scanning = true;
        redraw();
        const response = await hand(() => api.scanSettings({
          source
        }));
        if (!response?.ok) {
          model.st.scanning = false;
          redraw();
          return;
        }
        const body = await readJson(response);
        if (!body.hosts) {
          model.st.scanning = false;
          redraw();
          return;
        }
        applyScan(body);
      };
      const setCell = (key, cell, value) => {
        const previous = {
          runner: model.st.draft.runner
        };
        LocalConfig.setCell(model.scan, model.st.draft, key, cell, value);
        model.st.savedAt = null;
        model.st.serverFlags = [];
        if (key === "runner" && LocalConfig.needsRescan(previous, model.st.draft)) {
          void rescan(LocalConfig.source(model.st.draft));
          return;
        }
        redraw();
      };
      const save = async () => {
        const response = await hand(() => api.saveSettings(saveBody(model)));
        if (!response) return;
        const body = await readJson(response);
        if (response.status === 409) {
          model.st.refused = LocalConfig.changes(model.st.draft, model.st.saved).length || 1;
          model.st.modifiedAt = body.modified_at;
          redraw();
          return;
        }
        if (response.status === 422) {
          model.st.serverFlags = flagsFromErrors(body.errors);
          redraw();
          return;
        }
        if (!response.ok) return;
        model.st.saved = copy(model.st.draft);
        model.st.version = body.version ?? model.st.version;
        model.st.savedAt = body.saved_at;
        model.st.refused = 0;
        model.st.serverFlags = [];
        redraw();
      };
      const reread = async () => {
        const response = await hand(() => api.settings());
        if (!response?.ok) return;
        const body = await readJson(response);
        if (body.runner == null) return;
        const next = fromPayload(body);
        Object.assign(model, next);
        model.st.reread = true;
        redraw();
      };
      const root = el("div", {
        class: "scrim board",
        onClick: event => {
          if (event.target === event.currentTarget && !v.changed) close();
        }
      });
      root.dataset.screen = "settings";
      const sheet = el("div", {
        class: "sheet",
        role: "dialog",
        "aria-modal": "true",
        "aria-label": "本机配置"
      });
      sheet.append(el("div", {
        class: "sheet-head"
      }, el("div", {
        class: "sheet-head-text"
      }, el("span", {
        class: "dp-eyebrow"
      }, "本机配置"), el("h2", {
        class: "sheet-title"
      }, "这台机器上，每个 agent 跑在哪"), el("p", {
        class: "sheet-sub"
      }, "下拉菜单里的选项，是 MMW 刚问过这台机器上的 host 得到的，问的地方和 ", el("span", {
        class: "sheet-code"
      }, "start"), " 起 session 时问的是同一处。这里就是 MMW 管这件事的唯一地方，保存在本机的 ", el("span", {
        class: "sheet-code"
      }, v.store), "；这一页不写 GitHub。")), el("button", {
        type: "button",
        class: "dp-close",
        "aria-label": "关闭本机配置",
        onClick: close
      }, "×")));
      const body = el("div", {
        class: "sheet-body"
      });
      if (v.refused) {
        body.append(el("div", {
          class: "refused",
          role: "alert"
        }, el("p", {
          class: "refused-text"
        }, el("b", {}, "没有保存。"), v.refusedText), el("button", {
          type: "button",
          class: "btn",
          onClick: reread
        }, "重新读取")));
      }
      body.append(el("section", {
        class: "set-block"
      }, el("div", {
        class: "set-block-head"
      }, el("span", {
        class: "dp-section-title"
      }, "本机的 host"), el("span", {
        class: "scan"
      }, v.scanning ? [el("span", {
        class: "spin"
      }), v.scanningText] : [v.scannedText, el("button", {
        type: "button",
        class: "linkbtn",
        onClick: () => void rescan(LocalConfig.source(model.st.draft))
      }, "重新扫描")])), el("div", {
        class: "hostscan"
      }, (v.chips || []).map(chip => el("span", {
        class: chip.cls
      }, el("span", {
        class: "hs-name"
      }, chip.host), chip.what)))), el("section", {
        class: "set-block ruled"
      }, el("div", {
        class: "runner-row"
      }, el("div", {
        class: "role-name"
      }, el("span", {
        class: "role-agent"
      }, "runner"), el("span", {
        class: "role-what"
      }, "用什么起 session")), selectEl(v.runnerCls, v.runner, v.runnerOff, "runner", v.runnerOpts, value => setCell("runner", "runner", value)), v.runnerHasBad ? roleFoot(v.runnerBads) : null), el("p", {
        class: "set-note"
      }, "环境变量 ", el("span", {
        class: "sheet-code"
      }, "MMW_RUNNER"), " 设了时，它优先于这一格。「按所在环境判断」让 ", el("span", {
        class: "sheet-code"
      }, "start"), " 看自己跑在哪个 runner 里，判断不出时用 orca。runner 是 paseo 时，", el("span", {
        class: "sheet-code"
      }, "start"), " 向 Paseo 要 model，所以换到 paseo 或从 paseo 换走，选项会重新扫描。")), el("section", {
        class: "set-block ruled"
      }, el("div", {
        class: "set-block-head"
      }, el("span", {
        class: "dp-section-title"
      }, "一个 agent 一行")), el("div", {
        class: "roles"
      }, el("div", {
        class: "roles-head"
      }, el("span", {}, "agent"), el("span", {}, "host"), el("span", {}, "model"), el("span", {}, "effort")), (v.rows || []).map(row => el("div", {
        class: "role"
      }, el("div", {
        class: "role-name"
      }, el("span", {
        class: "role-agent"
      }, row.agent), el("span", {
        class: "role-what"
      }, row.what)), selectEl(row.hostCls, row.host, row.hostOff, row.hostLabel, row.hostOpts, value => setCell(row.agent, "host", value)), selectEl(row.modelCls, row.model, row.modelOff, row.modelLabel, row.modelOpts, value => setCell(row.agent, "model", value)), selectEl(row.effortCls, row.effort, row.effortOff, row.effortLabel, row.effortOpts, value => setCell(row.agent, "effort", value)), row.hasBad ? roleFoot(row.bads) : null))), el("p", {
        class: "set-note"
      }, "一台新机器第一次安装时，这里填的是 MMW 自带的初始值；之后只按这里选的跑，MMW 更新不会改它。")));
      sheet.append(body);
      sheet.append(el("div", {
        class: "sheet-foot"
      }, el("div", {
        class: "foot-status",
        "aria-live": "polite"
      }, el("span", {
        class: "foot-strong"
      }, v.hatch ? el("span", {
        class: "hatch"
      }) : null, v.strong), el("span", {
        class: "foot-quiet"
      }, v.quiet)), el("div", {
        class: "foot-actions"
      }, el("button", {
        type: "button",
        class: "btn",
        onClick: close
      }, v.closeLabel), el("button", {
        type: "button",
        class: "btn primary",
        disabled: !!v.saveOff,
        onClick: save
      }, "保存"))));
      root.append(sheet);
      detachEsc(host);
      host._settingsEsc = event => {
        if (event.key !== "Escape") return;
        event.preventDefault();
        event.stopImmediatePropagation();
        close();
      };
      document.addEventListener("keydown", host._settingsEsc, true);
      host.replaceChildren(root);
      return root;
    }
    function render(host, model, api, hooks = {}) {
      return paint(host, model, api, hooks);
    }
    MMW['settings'] = {
      unmount,
      fromScene,
      fromPayload,
      render
    };
  })();
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/task-board/lib/board.js", error: String((e && e.message) || e) }); }

// ui_kits/task-board/screens.jsx
try { (() => {
// The task board's five regions, composed from the design system's components and fed
// by the product's own logic (lib/board.js, the page modules of mmw-v2/board/page) and
// example data (data/, built by prototypes/task-board/553/UI/build_scenes.py).
const C = window.MMWTaskBoard2_34b698;
const M = window.MMW;
function TopBar({
  payload,
  now,
  settingsOpen,
  ui = "顶栏"
}) {
  const v = M.topbar.fromBoard({
    ...payload,
    settingsOpen
  }, new Date(now));
  const hot = v.orangeN > 0;
  const read = v.readFailed ? {
    failed: true,
    text: `读 GitHub 失败 · 下面是 ${v.readClock} 的数据（${v.readAgo} 分钟前）`
  } : {
    failed: false,
    text: v.readClock ? `只读 · ${v.readClock} 读取` : ""
  };
  return /*#__PURE__*/React.createElement("header", {
    className: "topbar board",
    "data-screen": "topbar"
  }, /*#__PURE__*/React.createElement(C.Brand, {
    repo: payload.repo,
    "data-ui": `${ui}.brand`
  }), /*#__PURE__*/React.createElement("div", {
    className: "counters"
  }, /*#__PURE__*/React.createElement(C.Counter, {
    button: true,
    hot: hot,
    lamp: hot ? "orange" : "hollow",
    label: "needs you",
    count: v.orangeN,
    title: "\u8DF3\u5230\u4E0B\u4E00\u5F20 needs you \u7684 ticket",
    "data-ui": `${ui}.needs-you`
  }), /*#__PURE__*/React.createElement(C.Counter, {
    lamp: "green",
    label: "running",
    count: v.greenN,
    sub: v.waiting ? `waiting for a slot ${v.waiting}` : null,
    "data-ui": `${ui}.running`
  }), /*#__PURE__*/React.createElement(C.Counter, {
    lamp: "hollow",
    label: "queued",
    count: v.hollowN,
    "data-ui": `${ui}.queued`
  }), /*#__PURE__*/React.createElement(C.Counter, {
    lamp: "ink",
    label: "done",
    count: v.inkN,
    "data-ui": `${ui}.done`
  })), /*#__PURE__*/React.createElement(C.ReadState, {
    failed: read.failed,
    text: read.text,
    "data-ui": `${ui}.read-state`
  }), /*#__PURE__*/React.createElement(C.IconButton, {
    icon: "refresh",
    label: "\u7ACB\u523B\u91CD\u8BFB GitHub",
    title: "\u7ACB\u523B\u91CD\u8BFB GitHub\uFF08\u9875\u9762\u5F00\u7740\u65F6\u6BCF\u5206\u949F\u81EA\u52A8\u8BFB\u4E00\u6B21\uFF09",
    "data-ui": `${ui}.refresh`
  }), /*#__PURE__*/React.createElement(C.IconButton, {
    icon: "settings",
    on: settingsOpen,
    label: "\u672C\u673A\u914D\u7F6E",
    title: "\u672C\u673A\u914D\u7F6E\uFF1A\u6BCF\u4E2A agent \u8DD1\u5728\u54EA\u4E2A host\u3001model\u3001effort",
    "data-ui": `${ui}.settings`
  }));
}
function TaskList({
  tasks,
  selected,
  ui = "任务列表"
}) {
  const v = M.tasks.taskListView(tasks, selected);
  return /*#__PURE__*/React.createElement("nav", {
    className: "tasks board",
    "aria-label": "The Night",
    "data-screen": "tasks"
  }, /*#__PURE__*/React.createElement(C.ColumnEyebrow, {
    label: "The Night",
    count: v.count,
    "data-ui": `${ui}.eyebrow`
  }), v.empty ? /*#__PURE__*/React.createElement(C.TasksEmpty, {
    "data-ui": `${ui}.empty`
  }) : null, v.rows.map(row => /*#__PURE__*/React.createElement(C.TaskRow, {
    key: row.n,
    row: row,
    "data-ui": `${ui}.task`
  })));
}
function Canvas({
  task,
  sel,
  width = 864,
  height = 848,
  ui = "画布"
}) {
  if (!task) return /*#__PURE__*/React.createElement("main", {
    className: "canvas board",
    "data-screen": "canvas"
  }, /*#__PURE__*/React.createElement(C.CanvasEmpty, {
    "data-ui": `${ui}.empty`
  }));
  const v = M.canvas.canvasView(task, sel, [...M.defaultExpanded(task)], true);
  const kFit = Math.min((width - 40) / v.layout.W, (height - 70) / v.layout.H);
  const view = {
    k: Math.min(1.6, Math.max(0.3, Math.max(0.9, Math.min(1, kFit)))),
    x: 20,
    y: 12
  };
  const b = sel != null ? v.layout.nodes.find(node => node.id === sel) : null;
  if (b) {
    if ((b.y + b.h) * view.k + view.y > height - 70) view.y = Math.min(12, height * 0.45 - (b.y + b.h / 2) * view.k);
    if ((b.x + b.w) * view.k + view.x > width - 24) view.x = Math.min(20, width - 24 - (b.x + b.w) * view.k);
  }
  return /*#__PURE__*/React.createElement("main", {
    className: "canvas board",
    "data-screen": "canvas",
    style: {
      width,
      height
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "world",
    style: {
      ...v.worldSize,
      transform: `translate(${view.x}px, ${view.y}px) scale(${view.k})`
    }
  }, /*#__PURE__*/React.createElement(C.Edges, {
    svg: v.svg
  }), v.labels.map((label, i) => /*#__PURE__*/React.createElement(C.LaneLabel, {
    key: `l${i}`,
    label: label,
    "data-ui": `${ui}.lane-label`
  })), v.containers.map(item => /*#__PURE__*/React.createElement(C.ContainerCard, {
    key: item.n,
    item: item,
    "data-ui": `${ui}.container-card`
  })), v.decisions.map(item => /*#__PURE__*/React.createElement(C.DecisionCard, {
    key: item.n,
    item: item,
    "data-ui": `${ui}.decision-card`
  })), v.tickets.map(item => /*#__PURE__*/React.createElement(C.TicketCard, {
    key: item.n,
    item: item,
    "data-ui": `${ui}.ticket-card`
  }))), /*#__PURE__*/React.createElement(C.Legend, {
    "data-ui": `${ui}.legend`
  }), /*#__PURE__*/React.createElement(C.ZoomBar, {
    level: `${Math.round(view.k * 100)}%`,
    "data-ui": `${ui}.zoom`
  }));
}
function Detail({
  payload,
  sel,
  ui = "详情"
}) {
  const v = M.detail.fromBoard(payload, sel);
  if (v.empty) return /*#__PURE__*/React.createElement("aside", {
    className: "detail board",
    "aria-label": "\u8BE6\u60C5"
  }, /*#__PURE__*/React.createElement(C.DetailEmpty, {
    title: v.emptyTitle,
    text: v.emptyText,
    "data-ui": `${ui}.empty`
  }));
  if (v.kind === "ticket") {
    const held = rows => [...rows].sort((a, b) => Number(b.hold) - Number(a.hold));
    const blocks = v.phaseBlocks || [];
    return /*#__PURE__*/React.createElement("aside", {
      className: "detail board",
      "aria-label": "\u8BE6\u60C5"
    }, /*#__PURE__*/React.createElement("div", {
      className: "pv"
    }, /*#__PURE__*/React.createElement(C.DetailHead, {
      ticket: true,
      eyebrow: v.eyebrow,
      "data-ui": `${ui}.head`
    }), /*#__PURE__*/React.createElement(C.DetailTitle, {
      ticket: true,
      title: v.title,
      "data-ui": `${ui}.title`
    }), /*#__PURE__*/React.createElement(C.Origin, {
      ticket: true,
      num: v.num,
      links: v.links,
      "data-ui": `${ui}.origin`
    }), /*#__PURE__*/React.createElement(C.StatusLine, {
      ticket: true,
      lamp: v.lamp,
      statusWord: v.statusWord,
      phase: v.phase,
      elapsed: v.elapsed,
      "data-ui": `${ui}.status`
    }), /*#__PURE__*/React.createElement(C.RunBox, {
      runtime: v.runtime,
      noRunText: v.noRunText,
      "data-ui": `${ui}.runtime`
    }), v.why.length ? /*#__PURE__*/React.createElement(C.NeedsYou, {
      why: v.why,
      "data-ui": `${ui}.why`
    }) : null, v.blockers.length ? /*#__PURE__*/React.createElement(C.Section, {
      ticket: true,
      title: "Blocked by",
      note: v.blockers.length,
      "data-ui": `${ui}.blocked-by`
    }, held(v.blockers).map(row => /*#__PURE__*/React.createElement(C.RelationRow, {
      ticket: true,
      key: row.n,
      row: row,
      "data-ui": `${ui}.blocker`
    }))) : null, v.blocks.length ? /*#__PURE__*/React.createElement(C.Section, {
      ticket: true,
      title: "Blocking",
      note: v.blocks.length,
      "data-ui": `${ui}.blocking`
    }, held(v.blocks).map(row => /*#__PURE__*/React.createElement(C.RelationRow, {
      ticket: true,
      key: row.n,
      row: row,
      "data-ui": `${ui}.blocks`
    }))) : null, /*#__PURE__*/React.createElement(C.Section, {
      ticket: true,
      title: "Events",
      note: v.eventCount,
      "data-ui": `${ui}.events`
    }, !(v.rawEvents.length || blocks.length) ? /*#__PURE__*/React.createElement(C.NoneNote, {
      ticket: true,
      text: "no events yet"
    }) : null, blocks.map((block, i) => /*#__PURE__*/React.createElement(C.EventBlock, {
      key: i,
      block: block,
      opened: block.openByDefault,
      "data-ui": `${ui}.event-block`
    }, block.items.map((item, j) => /*#__PURE__*/React.createElement(C.EventRow, {
      key: j,
      item: item,
      "data-ui": `${ui}.event`
    }))))), v.kids.length ? /*#__PURE__*/React.createElement(C.Section, {
      ticket: true,
      title: "Sub-issues",
      note: v.kids.length,
      "data-ui": `${ui}.sub-issues`
    }, v.kids.map((kid, i) => /*#__PURE__*/React.createElement(C.SubIssueRow, {
      key: i,
      kid: kid,
      "data-ui": `${ui}.sub-issue`
    }))) : null));
  }
  const rows = (list, id) => list.map(row => /*#__PURE__*/React.createElement(C.RelationRow, {
    key: row.n,
    row: row,
    "data-ui": `${ui}.${id}`
  }));
  return /*#__PURE__*/React.createElement("aside", {
    className: "detail board",
    "aria-label": "\u8BE6\u60C5"
  }, /*#__PURE__*/React.createElement("div", {
    className: "dp"
  }, /*#__PURE__*/React.createElement(C.DetailHead, {
    eyebrow: v.eyebrow,
    "data-ui": `${ui}.head`
  }), /*#__PURE__*/React.createElement(C.Origin, {
    num: v.num,
    links: v.links,
    "data-ui": `${ui}.origin`
  }), /*#__PURE__*/React.createElement(C.DetailTitle, {
    title: v.title,
    "data-ui": `${ui}.title`
  }), /*#__PURE__*/React.createElement(C.StatusLine, {
    lamp: v.lamp,
    statusWord: v.statusWord,
    elapsed: v.elapsed,
    "data-ui": `${ui}.status`
  }), v.kind === "spec" || v.kind === "map" ? /*#__PURE__*/React.createElement(C.Section, {
    title: v.listTitle,
    note: v.listCount,
    "data-ui": `${ui}.summary`
  }, /*#__PURE__*/React.createElement(C.LampCounts, {
    lamps: v.lamps,
    "data-ui": `${ui}.lamp-counts`
  }), /*#__PURE__*/React.createElement(C.PhaseCounts, {
    phases: v.phases.map(p => ({
      phase: p.phase,
      label: p.label
    })),
    "data-ui": `${ui}.phase-counts`
  })) : null, v.kind === "spec" ? /*#__PURE__*/React.createElement(C.Section, {
    title: "By number",
    "data-ui": `${ui}.by-number`
  }, rows(v.ticketRows, "ticket-row")) : null, v.kind === "map" ? /*#__PURE__*/React.createElement(C.Section, {
    title: "spec",
    note: v.specCount,
    "data-ui": `${ui}.specs`
  }, rows(v.specRows, "spec-row")) : null, v.kind === "map" && v.decisionRows.length ? /*#__PURE__*/React.createElement(C.Section, {
    title: "Decision tickets",
    note: v.decisionCount,
    "data-ui": `${ui}.decisions`
  }, rows(v.decisionRows, "decision-row")) : null, v.kind === "decision" ? [/*#__PURE__*/React.createElement(C.Section, {
    key: "a",
    title: "Blocked by",
    note: v.blockers.length || null,
    "data-ui": `${ui}.blocked-by`
  }, rows(v.blockers, "blocker"), !v.blockers.length ? /*#__PURE__*/React.createElement(C.NoneNote, {
    text: "none"
  }) : null), /*#__PURE__*/React.createElement(C.Section, {
    key: "b",
    title: "Blocking",
    note: v.blocks.length || null,
    "data-ui": `${ui}.blocking`
  }, rows(v.blocks, "blocks"), !v.blocks.length ? /*#__PURE__*/React.createElement(C.NoneNote, {
    text: "none"
  }) : null)] : null, /*#__PURE__*/React.createElement(C.GithubButton, {
    label: v.ghLabel,
    "data-ui": `${ui}.github`
  })));
}
function Settings({
  scene = "mine",
  ui = "本机配置"
}) {
  const model = M.settings.fromPayload(window.SETTINGS_SCENES[scene].payload);
  const v = M.settingsView(model.st, model.scan, model.catalog);
  return /*#__PURE__*/React.createElement(C.Sheet, {
    store: v.store,
    strong: v.strong,
    quiet: v.quiet,
    hatch: v.hatch,
    closeLabel: v.closeLabel,
    saveOff: v.saveOff,
    changed: v.changed,
    "data-ui": ui
  }, v.refused ? /*#__PURE__*/React.createElement(C.RefusedBanner, {
    text: v.refusedText,
    "data-ui": `${ui}.refused`
  }) : null, /*#__PURE__*/React.createElement(C.SetBlock, {
    title: "\u672C\u673A\u7684 host",
    "data-ui": `${ui}.hosts`,
    aside: /*#__PURE__*/React.createElement(C.ScanStatus, {
      scanning: v.scanning,
      scanningText: v.scanningText,
      scannedText: v.scannedText,
      "data-ui": `${ui}.scan`
    })
  }, /*#__PURE__*/React.createElement("div", {
    className: "hostscan"
  }, v.chips.map(chip => /*#__PURE__*/React.createElement(C.HostChip, {
    key: chip.host,
    chip: chip,
    "data-ui": `${ui}.host`
  })))), /*#__PURE__*/React.createElement(C.SetBlock, {
    ruled: true,
    "data-ui": `${ui}.runner-block`
  }, /*#__PURE__*/React.createElement(C.RunnerRow, {
    cls: v.runnerCls,
    value: v.runner,
    disabled: v.runnerOff,
    opts: v.runnerOpts,
    bads: v.runnerBads,
    "data-ui": `${ui}.runner`
  }), /*#__PURE__*/React.createElement(C.SetNote, {
    "data-ui": `${ui}.runner-note`
  }, "\u73AF\u5883\u53D8\u91CF ", /*#__PURE__*/React.createElement(C.CodeText, null, "MMW_RUNNER"), " \u8BBE\u4E86\u65F6\uFF0C\u5B83\u4F18\u5148\u4E8E\u8FD9\u4E00\u683C\u3002\u300C\u6309\u6240\u5728\u73AF\u5883\u5224\u65AD\u300D\u8BA9 ", /*#__PURE__*/React.createElement(C.CodeText, null, "start"), " \u770B\u81EA\u5DF1\u8DD1\u5728\u54EA\u4E2A runner \u91CC\uFF0C\u5224\u65AD\u4E0D\u51FA\u65F6\u7528 orca\u3002runner \u662F paseo \u65F6\uFF0C", /*#__PURE__*/React.createElement(C.CodeText, null, "start"), " \u5411 Paseo \u8981 model\uFF0C\u6240\u4EE5\u6362\u5230 paseo \u6216\u4ECE paseo \u6362\u8D70\uFF0C\u9009\u9879\u4F1A\u91CD\u65B0\u626B\u63CF\u3002")), /*#__PURE__*/React.createElement(C.SetBlock, {
    ruled: true,
    title: "\u4E00\u4E2A agent \u4E00\u884C",
    "data-ui": `${ui}.roles-block`
  }, /*#__PURE__*/React.createElement(C.RolesTable, {
    "data-ui": `${ui}.roles`
  }, v.rows.map(row => /*#__PURE__*/React.createElement(C.RoleRow, {
    key: row.agent,
    row: row,
    "data-ui": `${ui}.role`
  }))), /*#__PURE__*/React.createElement(C.SetNote, {
    "data-ui": `${ui}.initial-note`
  }, "\u4E00\u53F0\u65B0\u673A\u5668\u7B2C\u4E00\u6B21\u5B89\u88C5\u65F6\uFF0C\u8FD9\u91CC\u586B\u7684\u662F MMW \u81EA\u5E26\u7684\u521D\u59CB\u503C\uFF1B\u4E4B\u540E\u53EA\u6309\u8FD9\u91CC\u9009\u7684\u8DD1\uFF0CMMW \u66F4\u65B0\u4E0D\u4F1A\u6539\u5B83\u3002")));
}
function Board({
  settingsOpen
}) {
  const scene = window.BOARD_SCENES.morning;
  window.MMW_NOW = scene.now;
  const tasks = scene.payload.tasks;
  const task = tasks.find(t => t.n === scene.select.task);
  return /*#__PURE__*/React.createElement("main", {
    className: "app-shell board",
    style: {
      height: 900
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "app-top"
  }, /*#__PURE__*/React.createElement(TopBar, {
    payload: scene.payload,
    now: scene.now,
    settingsOpen: settingsOpen
  })), /*#__PURE__*/React.createElement("div", {
    className: "app-slot"
  }, /*#__PURE__*/React.createElement(TaskList, {
    tasks: tasks,
    selected: task.n
  })), /*#__PURE__*/React.createElement("div", {
    className: "app-slot"
  }, /*#__PURE__*/React.createElement(Canvas, {
    task: task,
    sel: scene.select.node
  })), /*#__PURE__*/React.createElement("div", {
    className: "app-slot"
  }, /*#__PURE__*/React.createElement(Detail, {
    payload: scene.payload,
    sel: scene.select.node
  })), settingsOpen ? /*#__PURE__*/React.createElement("div", {
    className: "app-sheet",
    style: {
      pointerEvents: "auto"
    }
  }, /*#__PURE__*/React.createElement(Settings, null)) : null);
}
function mount(element) {
  window.MMW_NOW = window.BOARD_SCENES.morning.now;
  ReactDOM.createRoot(document.getElementById("root")).render(element);
}
Object.assign(window, {
  TaskBoardScreens: {
    TopBar,
    TaskList,
    Canvas,
    Detail,
    Settings,
    Board,
    mount
  }
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/task-board/screens.jsx", error: String((e && e.message) || e) }); }

__ds_ns.CanvasEmpty = __ds_scope.CanvasEmpty;

__ds_ns.ContainerCard = __ds_scope.ContainerCard;

__ds_ns.DecisionCard = __ds_scope.DecisionCard;

__ds_ns.Edges = __ds_scope.Edges;

__ds_ns.LaneLabel = __ds_scope.LaneLabel;

__ds_ns.Legend = __ds_scope.Legend;

__ds_ns.TicketCard = __ds_scope.TicketCard;

__ds_ns.ZoomBar = __ds_scope.ZoomBar;

__ds_ns.DetailEmpty = __ds_scope.DetailEmpty;

__ds_ns.DetailHead = __ds_scope.DetailHead;

__ds_ns.DetailTitle = __ds_scope.DetailTitle;

__ds_ns.EventBlock = __ds_scope.EventBlock;

__ds_ns.EventRow = __ds_scope.EventRow;

__ds_ns.GithubButton = __ds_scope.GithubButton;

__ds_ns.LampCounts = __ds_scope.LampCounts;

__ds_ns.NeedsYou = __ds_scope.NeedsYou;

__ds_ns.NoneNote = __ds_scope.NoneNote;

__ds_ns.Origin = __ds_scope.Origin;

__ds_ns.PhaseCounts = __ds_scope.PhaseCounts;

__ds_ns.RelationRow = __ds_scope.RelationRow;

__ds_ns.RunBox = __ds_scope.RunBox;

__ds_ns.Section = __ds_scope.Section;

__ds_ns.StatusLine = __ds_scope.StatusLine;

__ds_ns.SubIssueRow = __ds_scope.SubIssueRow;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.CodeText = __ds_scope.CodeText;

__ds_ns.HostChip = __ds_scope.HostChip;

__ds_ns.ProblemList = __ds_scope.ProblemList;

__ds_ns.RefusedBanner = __ds_scope.RefusedBanner;

__ds_ns.RoleRow = __ds_scope.RoleRow;

__ds_ns.RolesTable = __ds_scope.RolesTable;

__ds_ns.RunnerRow = __ds_scope.RunnerRow;

__ds_ns.ScanStatus = __ds_scope.ScanStatus;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.SetBlock = __ds_scope.SetBlock;

__ds_ns.SetNote = __ds_scope.SetNote;

__ds_ns.Sheet = __ds_scope.Sheet;

__ds_ns.Lamp = __ds_scope.Lamp;

__ds_ns.StepPill = __ds_scope.StepPill;

__ds_ns.ColumnEyebrow = __ds_scope.ColumnEyebrow;

__ds_ns.TaskRow = __ds_scope.TaskRow;

__ds_ns.TasksEmpty = __ds_scope.TasksEmpty;

__ds_ns.Brand = __ds_scope.Brand;

__ds_ns.Counter = __ds_scope.Counter;

__ds_ns.IconButton = __ds_scope.IconButton;

__ds_ns.ReadState = __ds_scope.ReadState;

})();
