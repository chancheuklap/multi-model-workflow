/* @ds-bundle: {"format":4,"namespace":"MMWTaskBoard2_34b698","components":["CanvasEmpty","ContainerCard","DecisionCard","Edges","LaneLabel","Legend","TicketCard","ZoomBar","DetailEmpty","DetailHead","DetailTitle","EventBlock","EventRow","GithubButton","LampCounts","NeedsYou","NoneNote","Origin","PhaseCounts","RelationRow","RunBox","Section","StatusLine","SubIssueRow","Button","CodeText","HostChip","ProblemList","RefusedBanner","RoleRow","RolesTable","RunnerRow","ScanStatus","Select","SetBlock","SetNote","Sheet","Lamp","StepPill","ColumnEyebrow","TaskRow","TasksEmpty","Brand","Counter","IconButton","ReadState"],"sourceHashes":{"CanvasEmpty":"10f547c60646318e","ContainerCard":"2acfc66a6f494888","DecisionCard":"37e6d3f06835ca9b","Edges":"ef780cf86aa9bc60","LaneLabel":"35246166490c5474","Legend":"37807dfe46afa75f","TicketCard":"623c9139f7365836","ZoomBar":"d7e23ccf81eeacb2","DetailEmpty":"4e0d89dbbf3b931a","DetailHead":"e5835c3ccc7d538d","DetailTitle":"3e00e91dbe96bf10","EventBlock":"9fca5edd709efb63","EventRow":"438f48a7d4b48fb7","GithubButton":"60a84b3c45d757bd","LampCounts":"85d810685a29e11e","NeedsYou":"4aa630837df2548f","NoneNote":"61f0a2557d57bd20","Origin":"bb126bbfc661382f","PhaseCounts":"578be626c8865217","RelationRow":"2f294fd344d3a6d6","RunBox":"a76c7053ba41673c","Section":"7f1e043d7861b45f","StatusLine":"d747f2beff3c5b08","SubIssueRow":"f2fdefddc17d1183","Button":"1ccf667bbdba0980","CodeText":"b18f2df9cfb77d80","HostChip":"19586895f2a1d856","ProblemList":"a55530b7b848519f","RefusedBanner":"da4be775064fdcf3","RoleRow":"43cfb86cee7f89b0","RolesTable":"0ee7f1a1dc679f78","RunnerRow":"ecb3349aacc11b83","ScanStatus":"df6b5ca4abe9dfa9","Select":"1234309a4dada3a7","SetBlock":"b29291f8310c3b8e","SetNote":"56cde0882c3effb7","Sheet":"34532a43c90ffd29","Lamp":"d1d46459163cb993","StepPill":"6c797f640e3f726d","ColumnEyebrow":"2a68f95eed49fba8","TaskRow":"7c013edbb6544e20","TasksEmpty":"362398226eb13a5a","Brand":"6e4641a9cfb31584","Counter":"a09b2a6a84f814e4","IconButton":"a42e02508f3e45b9","ReadState":"d9d7a26253a51331"},"inlinedExternals":[],"unexposedExports":[]} */
var __ds = (() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // entry.js
  var entry_exports = {};
  __export(entry_exports, {
    Brand: () => Brand,
    Button: () => Button,
    CanvasEmpty: () => CanvasEmpty,
    CodeText: () => CodeText,
    ColumnEyebrow: () => ColumnEyebrow,
    ContainerCard: () => ContainerCard,
    Counter: () => Counter,
    DecisionCard: () => DecisionCard,
    DetailEmpty: () => DetailEmpty,
    DetailHead: () => DetailHead,
    DetailTitle: () => DetailTitle,
    Edges: () => Edges,
    EventBlock: () => EventBlock,
    EventRow: () => EventRow,
    GithubButton: () => GithubButton,
    HostChip: () => HostChip,
    IconButton: () => IconButton,
    Lamp: () => Lamp,
    LampCounts: () => LampCounts,
    LaneLabel: () => LaneLabel,
    Legend: () => Legend,
    NeedsYou: () => NeedsYou,
    NoneNote: () => NoneNote,
    Origin: () => Origin,
    PhaseCounts: () => PhaseCounts,
    ProblemList: () => ProblemList,
    ReadState: () => ReadState,
    RefusedBanner: () => RefusedBanner,
    RelationRow: () => RelationRow,
    RoleRow: () => RoleRow,
    RolesTable: () => RolesTable,
    RunBox: () => RunBox,
    RunnerRow: () => RunnerRow,
    ScanStatus: () => ScanStatus,
    Section: () => Section,
    Select: () => Select,
    SetBlock: () => SetBlock,
    SetNote: () => SetNote,
    Sheet: () => Sheet,
    StatusLine: () => StatusLine,
    StepPill: () => StepPill,
    SubIssueRow: () => SubIssueRow,
    TaskRow: () => TaskRow,
    TasksEmpty: () => TasksEmpty,
    TicketCard: () => TicketCard,
    ZoomBar: () => ZoomBar
  });

  // react-shim.js
  var react_shim_default = new Proxy({}, { get: (_, key) => window.React[key] });

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/_shared/ui.js
  var part = (ui, name) => ui ? `${ui}.${name}` : void 0;

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/canvas/CanvasEmpty.jsx
  function CanvasEmpty({ "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "canvas-empty", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("div", null, /* @__PURE__ */ react_shim_default.createElement("p", { className: "canvas-empty-title", "data-ui": part(ui, "title") }, "The Night \u8FD8\u6CA1\u5F00\u59CB"), /* @__PURE__ */ react_shim_default.createElement("p", { className: "canvas-empty-text", "data-ui": part(ui, "text") }, "The Night \u662F\u4E00\u6B21\u8BA8\u8BBA\u5F00\u51FA\u7684\u90A3\u5F20 ticket\u3002\u7ED9\u5B83\u6253\u4E0A ", /* @__PURE__ */ react_shim_default.createElement("span", { className: "code" }, "mmw:map"), " label\uFF0C\u4E0B\u4E00\u6B21\u8BFB\u53D6\u65F6\u5B83\u548C\u5B83\u4E0B\u9762\u7684 spec\u3001ticket \u5C31\u4F1A\u51FA\u73B0\u5728\u8FD9\u91CC\u3002")));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/canvas/card-shell.jsx
  function cardShell(item, { ui, onPick, lampTitle, titleCls, right, after }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: item.cls, style: item.pos, title: item.title, "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement(
      "button",
      {
        type: "button",
        className: "card-hit",
        "aria-label": `#${item.n} ${item.title}`,
        onClick: onPick,
        "data-ui": part(ui, "open")
      }
    ), /* @__PURE__ */ react_shim_default.createElement("div", { className: "card-top" }, /* @__PURE__ */ react_shim_default.createElement("span", { className: item.lampCls, title: lampTitle ? item.lampWord : void 0, "data-ui": part(ui, "lamp") }), /* @__PURE__ */ react_shim_default.createElement("span", { className: "card-num", "data-ui": part(ui, "num") }, item.num), /* @__PURE__ */ react_shim_default.createElement("span", { className: "card-right" }, right)), /* @__PURE__ */ react_shim_default.createElement("div", { className: titleCls, "data-ui": part(ui, "title") }, item.title), after);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/canvas/ContainerCard.jsx
  function ContainerCard({ item, onPick, onToggle, "data-ui": ui }) {
    const right = [/* @__PURE__ */ react_shim_default.createElement("span", { key: "c", className: "card-count", "data-ui": part(ui, "count") }, item.count)];
    if (item.canExpand) {
      right.push(
        /* @__PURE__ */ react_shim_default.createElement(
          "button",
          {
            key: "x",
            type: "button",
            className: "chev",
            "aria-label": item.toggleLabel,
            "data-ui": part(ui, "expand"),
            onClick: (event) => {
              event.stopPropagation();
              if (onToggle) onToggle(item.n);
            }
          },
          item.chev
        )
      );
    }
    const after = /* @__PURE__ */ react_shim_default.createElement("div", { className: "card-bar" }, /* @__PURE__ */ react_shim_default.createElement("div", { className: "card-bar-fill", style: { width: item.barStyle.width }, "data-ui": part(ui, "bar") }));
    return cardShell(item, { ui, onPick, lampTitle: true, titleCls: item.titleCls, right, after });
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/canvas/DecisionCard.jsx
  function DecisionCard({ item, onPick, "data-ui": ui }) {
    const right = /* @__PURE__ */ react_shim_default.createElement("span", { className: "card-kind", "data-ui": part(ui, "kind") }, item.kind);
    return cardShell(item, { ui, onPick, lampTitle: false, titleCls: "card-title decision", right, after: null });
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/canvas/Edges.jsx
  function Edges({ svg, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "edges-host", "data-ui": ui, dangerouslySetInnerHTML: { __html: svg || "" } });
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/canvas/LaneLabel.jsx
  function LaneLabel({ label, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: label.cls, style: label.pos, "data-ui": ui }, label.text);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/canvas/Legend.jsx
  function Legend({ "data-ui": ui }) {
    const item = (cls, text, name) => /* @__PURE__ */ react_shim_default.createElement("span", { className: "legend-item", "data-ui": part(ui, name) }, /* @__PURE__ */ react_shim_default.createElement("span", { className: cls }), text);
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "legend", "data-ui": ui }, item("legend-line", "contains \xB7 released", "walked"), item("legend-line flow", "released \xB7 working", "flow"), item("legend-line blocked", "blocked", "blocked"), item("legend-bar", "closing pass", "closeout"));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/canvas/TicketCard.jsx
  function TicketCard({ item, onPick, "data-ui": ui }) {
    const right = /* @__PURE__ */ react_shim_default.createElement("span", { className: item.pillCls, "data-ui": part(ui, "phase") }, item.phase);
    const after = /* @__PURE__ */ react_shim_default.createElement("div", { className: item.runCls, "data-ui": part(ui, "run") }, item.run);
    return cardShell(item, { ui, onPick, lampTitle: true, titleCls: "card-title", right, after });
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/canvas/ZoomBar.jsx
  function ZoomBar({ level, onOut, onIn, onFit, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "zoom", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "zoom-btn", "aria-label": "zoom out", onClick: onOut, "data-ui": part(ui, "out") }, "\u2212"), /* @__PURE__ */ react_shim_default.createElement("span", { className: "zoom-level", "data-ui": part(ui, "level") }, level), /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "zoom-btn", "aria-label": "zoom in", onClick: onIn, "data-ui": part(ui, "in") }, "+"), /* @__PURE__ */ react_shim_default.createElement("span", { className: "zoom-sep" }), /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "zoom-btn text", onClick: onFit, "data-ui": part(ui, "fit") }, "fit"));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/DetailEmpty.jsx
  function DetailEmpty({ title, text, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "dp-empty", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("p", { className: "dp-empty-title", "data-ui": part(ui, "title") }, title), text);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/DetailHead.jsx
  function DetailHead({ ticket, eyebrow, onGithub, onClose, "data-ui": ui }) {
    if (ticket) {
      return /* @__PURE__ */ react_shim_default.createElement("div", { className: "pv-head", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "pv-eyebrow", "data-ui": part(ui, "eyebrow") }, eyebrow || "Ticket"), /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "pv-gh", onClick: onGithub, "data-ui": part(ui, "github") }, "GitHub \u2197"), /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "pv-close", "aria-label": "\u5173\u95ED\u8BE6\u60C5", onClick: onClose, "data-ui": part(ui, "close") }, "\xD7"));
    }
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "dp-head", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "dp-eyebrow", "data-ui": part(ui, "eyebrow") }, eyebrow), /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "dp-close", "aria-label": "\u5173\u95ED\u8BE6\u60C5", onClick: onClose, "data-ui": part(ui, "close") }, "\xD7"));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/DetailTitle.jsx
  function DetailTitle({ ticket, title, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("h2", { className: ticket ? "pv-title" : "dp-title", "data-ui": ui }, title);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/EventBlock.jsx
  function EventBlock({ block, opened, onToggle, children, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: block.tone === "plain" ? "va-block" : "va-block warn", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "va-bhead", onClick: onToggle, "data-ui": part(ui, "toggle") }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "va-chev", "data-ui": part(ui, "chev") }, opened ? "\u25BE" : "\u25B8"), /* @__PURE__ */ react_shim_default.createElement("span", { className: `pill ${block.phase}`, "data-ui": part(ui, "phase") }, block.phase), /* @__PURE__ */ react_shim_default.createElement("span", { className: "va-bsum", "data-ui": part(ui, "summary") }, opened ? "" : block.summary), /* @__PURE__ */ react_shim_default.createElement("span", { className: "va-btime", "data-ui": part(ui, "time") }, opened ? block.span : block.from)), opened ? /* @__PURE__ */ react_shim_default.createElement("div", { className: "va-body" }, children) : null);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/EventRow.jsx
  function EventRow({ item, opened, onToggle, "data-ui": ui }) {
    const warn = item.tone === "warn" || item.tone === "needs-you";
    return /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "va-ev", onClick: onToggle, "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "va-t", "data-ui": part(ui, "time") }, item.time), /* @__PURE__ */ react_shim_default.createElement("span", { className: warn ? "va-n warn" : "va-n", "data-ui": part(ui, "name") }, item.name), item.hasText ? /* @__PURE__ */ react_shim_default.createElement("span", { className: "va-x", "data-ui": part(ui, "text") }, item.text) : null, opened ? /* @__PURE__ */ react_shim_default.createElement("span", { className: "va-x" }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "pv-detail", "data-ui": part(ui, "detail") }, (item.detail || []).flatMap((row, i) => [
      /* @__PURE__ */ react_shim_default.createElement("span", { key: `k${i}`, className: "pv-detail-k" }, row.k),
      /* @__PURE__ */ react_shim_default.createElement("span", { key: `v${i}`, className: "pv-detail-v" }, row.v)
    ]))) : null);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/GithubButton.jsx
  function GithubButton({ label, onClick, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "dp-gh", onClick, "data-ui": ui }, label);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/LampCounts.jsx
  function LampCounts({ lamps = [], "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "lamps-count", "data-ui": ui }, lamps.map((item, i) => /* @__PURE__ */ react_shim_default.createElement("span", { key: i, className: "lc-item", "data-ui": part(ui, "item") }, /* @__PURE__ */ react_shim_default.createElement("span", { className: `lamp ${item.lamp}` }), item.word, /* @__PURE__ */ react_shim_default.createElement("span", { className: "lc-n" }, item.n))));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/NeedsYou.jsx
  function NeedsYou({ why = [], "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "pv-why", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "pv-why-t", "data-ui": part(ui, "title") }, "Needs you"), why.map((item, i) => /* @__PURE__ */ react_shim_default.createElement("span", { key: i, "data-ui": part(ui, "item") }, /* @__PURE__ */ react_shim_default.createElement("b", null, item.head), " ", item.body)));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/NoneNote.jsx
  function NoneNote({ ticket, text, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("p", { className: ticket ? "pv-none" : "rel-none", "data-ui": ui }, text);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/Origin.jsx
  function Origin({ ticket, num, links = [], onGoto, "data-ui": ui }) {
    const cls = ticket ? "pv-links" : "dp-origin";
    const linkCls = ticket ? "pv-link" : "dp-link";
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: cls, "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("span", { "data-ui": part(ui, "number") }, num), links.flatMap((link, i) => [
      /* @__PURE__ */ react_shim_default.createElement("span", { key: `d${i}` }, "\xB7"),
      /* @__PURE__ */ react_shim_default.createElement(
        "button",
        {
          key: `l${i}`,
          type: "button",
          className: linkCls,
          onClick: () => onGoto && onGoto(link.n),
          "data-ui": part(ui, "link")
        },
        link.label
      )
    ]));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/PhaseCounts.jsx
  function PhaseCounts({ phases = [], "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "phases-count", "data-ui": ui }, phases.map((item, i) => /* @__PURE__ */ react_shim_default.createElement("span", { key: i, className: `pill ${item.phase}`, "data-ui": part(ui, "item") }, item.label)));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/RelationRow.jsx
  function RelationRow({ ticket, row, onGoto, "data-ui": ui }) {
    const go = () => onGoto && onGoto(row.n);
    if (ticket) {
      const last2 = row.hold ? /* @__PURE__ */ react_shim_default.createElement("span", { className: "pv-rel-hold", "data-ui": part(ui, "hold") }, "held") : row.phase ? /* @__PURE__ */ react_shim_default.createElement("span", { className: `pill ${row.phase}`, "data-ui": part(ui, "phase") }, row.phase) : /* @__PURE__ */ react_shim_default.createElement("span", { className: "pv-rel-s", "data-ui": part(ui, "state") }, row.state);
      const body2 = [
        /* @__PURE__ */ react_shim_default.createElement("span", { key: "l", className: `lamp ${row.lamp}`, "data-ui": part(ui, "lamp") }),
        /* @__PURE__ */ react_shim_default.createElement("span", { key: "n", className: "pv-rel-n", "data-ui": part(ui, "number") }, row.num),
        /* @__PURE__ */ react_shim_default.createElement("span", { key: "t", className: "pv-rel-t", "data-ui": part(ui, "title") }, row.title, row.where ? " " : null, row.where ? /* @__PURE__ */ react_shim_default.createElement("span", { className: "rel-where", "data-ui": part(ui, "where") }, row.where) : null),
        /* @__PURE__ */ react_shim_default.createElement(react_shim_default.Fragment, { key: "x" }, last2)
      ];
      if (row.unknown) return /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "pv-rel", "data-ui": ui }, body2);
      return /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: row.hold ? "pv-rel hold" : "pv-rel", onClick: go, "data-ui": ui }, body2);
    }
    const last = row.phase ? /* @__PURE__ */ react_shim_default.createElement("span", { className: `pill ${row.phase}`, "data-ui": part(ui, "phase") }, row.phase) : /* @__PURE__ */ react_shim_default.createElement("span", { className: row.state === "not landed" ? "rel-state open" : "rel-state", "data-ui": part(ui, "state") }, row.state);
    const body = [
      /* @__PURE__ */ react_shim_default.createElement("span", { key: "l", className: `lamp ${row.lamp}`, "data-ui": part(ui, "lamp") }),
      /* @__PURE__ */ react_shim_default.createElement("span", { key: "n", className: "rel-num", "data-ui": part(ui, "number") }, row.num),
      /* @__PURE__ */ react_shim_default.createElement("span", { key: "t", className: "rel-title", "data-ui": part(ui, "title") }, row.title, " ", /* @__PURE__ */ react_shim_default.createElement("span", { className: "rel-where", "data-ui": part(ui, "where") }, row.where || "")),
      /* @__PURE__ */ react_shim_default.createElement(react_shim_default.Fragment, { key: "x" }, last)
    ];
    if (row.unknown) return /* @__PURE__ */ react_shim_default.createElement("div", { className: "rel-static", "data-ui": ui }, body);
    return /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "rel", onClick: go, "data-ui": ui }, body);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/RunBox.jsx
  function RunBox({ runtime, noRunText, "data-ui": ui }) {
    if (!runtime) return /* @__PURE__ */ react_shim_default.createElement("p", { className: "pv-none", "data-ui": ui }, noRunText || "not dispatched yet");
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "pv-run", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("div", { className: "pv-run-who" }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "pv-run-grade", "data-ui": part(ui, "grade") }, runtime.grade || ""), runtime.model ? /* @__PURE__ */ react_shim_default.createElement("span", { className: "pv-run-model", "data-ui": part(ui, "model") }, runtime.model) : null), runtime.rows && runtime.rows.length ? /* @__PURE__ */ react_shim_default.createElement("div", { className: "pv-run-where" }, runtime.rows.flatMap((row, i) => [
      /* @__PURE__ */ react_shim_default.createElement("span", { key: `k${i}`, className: "pv-run-k", "data-ui": part(ui, "key") }, row.k),
      /* @__PURE__ */ react_shim_default.createElement("span", { key: `v${i}`, className: "pv-run-v", "data-ui": part(ui, "value") }, row.v)
    ])) : null);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/Section.jsx
  function Section({ ticket, title, note, children, "data-ui": ui }) {
    const cls = ticket ? "pv-sec" : "dp-section";
    const titleCls = ticket ? "pv-sec-title" : "dp-section-title";
    return /* @__PURE__ */ react_shim_default.createElement("section", { className: cls, "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("div", { className: titleCls }, /* @__PURE__ */ react_shim_default.createElement("span", { "data-ui": part(ui, "title") }, title), note == null ? null : /* @__PURE__ */ react_shim_default.createElement("span", { "data-ui": part(ui, "count") }, String(note))), children);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/StatusLine.jsx
  function StatusLine({ ticket, lamp, statusWord, phase, elapsed, "data-ui": ui }) {
    if (ticket) {
      return /* @__PURE__ */ react_shim_default.createElement("div", { className: "va-status", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("span", { className: `lamp big ${lamp}`, "data-ui": part(ui, "lamp") }), /* @__PURE__ */ react_shim_default.createElement("span", { className: `va-word ${lamp}`, "data-ui": part(ui, "status") }, statusWord), /* @__PURE__ */ react_shim_default.createElement("span", { className: `pill big ${phase}`, "data-ui": part(ui, "phase") }, phase), /* @__PURE__ */ react_shim_default.createElement("span", { className: "va-elapsed", "data-ui": part(ui, "elapsed") }, elapsed || ""));
    }
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "dp-status", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("span", { className: `lamp big ${lamp}`, "data-ui": part(ui, "lamp") }), /* @__PURE__ */ react_shim_default.createElement("span", { className: `status-word ${lamp}`, "data-ui": part(ui, "status") }, statusWord), /* @__PURE__ */ react_shim_default.createElement("span", { className: "dp-elapsed", "data-ui": part(ui, "elapsed") }, elapsed || ""));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/detail/SubIssueRow.jsx
  function SubIssueRow({ kid, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "pv-rel", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("span", { className: `lamp ${kid.lamp}`, "data-ui": part(ui, "lamp") }), /* @__PURE__ */ react_shim_default.createElement("span", { className: "pv-rel-n", "data-ui": part(ui, "number") }, kid.num), /* @__PURE__ */ react_shim_default.createElement("span", { className: "pv-rel-t", "data-ui": part(ui, "title") }, kid.title), /* @__PURE__ */ react_shim_default.createElement("span", { className: kid.hot ? "pv-kind hot" : "pv-kind", "data-ui": part(ui, "kind") }, kid.kind));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/settings/Button.jsx
  function Button({ kind, disabled, onClick, children, "data-ui": ui }) {
    const cls = kind === "primary" ? "btn primary" : kind === "link" ? "linkbtn" : "btn";
    return /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: cls, disabled: !!disabled, onClick, "data-ui": ui }, children);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/settings/CodeText.jsx
  function CodeText({ children, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("span", { className: "sheet-code", "data-ui": ui }, children);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/settings/HostChip.jsx
  function HostChip({ chip, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("span", { className: chip.cls, "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "hs-name", "data-ui": part(ui, "name") }, chip.host), chip.what);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/settings/ProblemList.jsx
  function ProblemList({ items = [], "data-ui": ui }) {
    if (!items.length) return null;
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "role-foot", "data-ui": ui }, items.map((item, i) => /* @__PURE__ */ react_shim_default.createElement("div", { key: i, className: "role-bad", "data-ui": part(ui, "item") }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "hatch" }), item.text)));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/settings/RefusedBanner.jsx
  function RefusedBanner({ text, onReread, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "refused", role: "alert", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("p", { className: "refused-text", "data-ui": part(ui, "text") }, /* @__PURE__ */ react_shim_default.createElement("b", null, "\u6CA1\u6709\u4FDD\u5B58\u3002"), text), /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "btn", onClick: onReread, "data-ui": part(ui, "reread") }, "\u91CD\u65B0\u8BFB\u53D6"));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/settings/Select.jsx
  function Select({ cls, value, disabled, label, opts = [], onChange, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement(
      "select",
      {
        className: cls,
        "aria-label": label,
        disabled: !!disabled,
        value: value ?? "",
        onChange: (event) => onChange && onChange(event.target.value),
        "data-ui": ui
      },
      opts.map((option) => /* @__PURE__ */ react_shim_default.createElement("option", { key: option.value, value: option.value, disabled: !!option.disabled, label: option.text }, option.text))
    );
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/settings/RoleRow.jsx
  function RoleRow({ row, onCell, "data-ui": ui }) {
    const set = (cell) => (value) => onCell && onCell(row.agent, cell, value);
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "role", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("div", { className: "role-name" }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "role-agent", "data-ui": part(ui, "agent") }, row.agent), /* @__PURE__ */ react_shim_default.createElement("span", { className: "role-what", "data-ui": part(ui, "what") }, row.what)), /* @__PURE__ */ react_shim_default.createElement(Select, { cls: row.hostCls, value: row.host, disabled: row.hostOff, label: row.hostLabel, opts: row.hostOpts, onChange: set("host"), "data-ui": part(ui, "host") }), /* @__PURE__ */ react_shim_default.createElement(Select, { cls: row.modelCls, value: row.model, disabled: row.modelOff, label: row.modelLabel, opts: row.modelOpts, onChange: set("model"), "data-ui": part(ui, "model") }), /* @__PURE__ */ react_shim_default.createElement(Select, { cls: row.effortCls, value: row.effort, disabled: row.effortOff, label: row.effortLabel, opts: row.effortOpts, onChange: set("effort"), "data-ui": part(ui, "effort") }), row.hasBad ? /* @__PURE__ */ react_shim_default.createElement(ProblemList, { items: row.bads, "data-ui": part(ui, "problem") }) : null);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/settings/RolesTable.jsx
  function RolesTable({ children, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "roles", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("div", { className: "roles-head", "data-ui": part(ui, "head") }, /* @__PURE__ */ react_shim_default.createElement("span", null, "agent"), /* @__PURE__ */ react_shim_default.createElement("span", null, "host"), /* @__PURE__ */ react_shim_default.createElement("span", null, "model"), /* @__PURE__ */ react_shim_default.createElement("span", null, "effort")), children);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/settings/RunnerRow.jsx
  function RunnerRow({ cls, value, disabled, opts, bads = [], onChange, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "runner-row", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("div", { className: "role-name" }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "role-agent", "data-ui": part(ui, "label") }, "runner"), /* @__PURE__ */ react_shim_default.createElement("span", { className: "role-what", "data-ui": part(ui, "what") }, "\u7528\u4EC0\u4E48\u8D77 session")), /* @__PURE__ */ react_shim_default.createElement(Select, { cls, value, disabled, label: "runner", opts, onChange, "data-ui": part(ui, "select") }), bads.length ? /* @__PURE__ */ react_shim_default.createElement(ProblemList, { items: bads, "data-ui": part(ui, "problem") }) : null);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/settings/ScanStatus.jsx
  function ScanStatus({ scanning, scanningText, scannedText, onRescan, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("span", { className: "scan", "data-ui": ui }, scanning ? [/* @__PURE__ */ react_shim_default.createElement("span", { key: "s", className: "spin" }), scanningText] : [
      scannedText,
      /* @__PURE__ */ react_shim_default.createElement("button", { key: "b", type: "button", className: "linkbtn", onClick: onRescan, "data-ui": part(ui, "rescan") }, "\u91CD\u65B0\u626B\u63CF")
    ]);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/settings/SetBlock.jsx
  function SetBlock({ ruled, title, aside, children, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("section", { className: ruled ? "set-block ruled" : "set-block", "data-ui": ui }, title ? /* @__PURE__ */ react_shim_default.createElement("div", { className: "set-block-head" }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "dp-section-title", "data-ui": part(ui, "title") }, title), aside) : null, children);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/settings/SetNote.jsx
  function SetNote({ children, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("p", { className: "set-note", "data-ui": ui }, children);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/settings/Sheet.jsx
  function Sheet({ store, strong, quiet, hatch, closeLabel, saveOff, changed, onClose, onSave, children, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement(
      "div",
      {
        className: "scrim board",
        "data-ui": ui,
        onClick: (event) => {
          if (event.target === event.currentTarget && !changed && onClose) onClose();
        }
      },
      /* @__PURE__ */ react_shim_default.createElement("div", { className: "sheet", role: "dialog", "aria-modal": "true", "aria-label": "\u672C\u673A\u914D\u7F6E" }, /* @__PURE__ */ react_shim_default.createElement("div", { className: "sheet-head" }, /* @__PURE__ */ react_shim_default.createElement("div", { className: "sheet-head-text" }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "dp-eyebrow", "data-ui": part(ui, "eyebrow") }, "\u672C\u673A\u914D\u7F6E"), /* @__PURE__ */ react_shim_default.createElement("h2", { className: "sheet-title", "data-ui": part(ui, "title") }, "\u8FD9\u53F0\u673A\u5668\u4E0A\uFF0C\u6BCF\u4E2A agent \u8DD1\u5728\u54EA"), /* @__PURE__ */ react_shim_default.createElement("p", { className: "sheet-sub", "data-ui": part(ui, "intro") }, "\u4E0B\u62C9\u83DC\u5355\u91CC\u7684\u9009\u9879\uFF0C\u662F MMW \u521A\u95EE\u8FC7\u8FD9\u53F0\u673A\u5668\u4E0A\u7684 host \u5F97\u5230\u7684\uFF0C\u95EE\u7684\u5730\u65B9\u548C ", /* @__PURE__ */ react_shim_default.createElement("span", { className: "sheet-code" }, "start"), " \u8D77 session \u65F6\u95EE\u7684\u662F\u540C\u4E00\u5904\u3002\u8FD9\u91CC\u5C31\u662F MMW \u7BA1\u8FD9\u4EF6\u4E8B\u7684\u552F\u4E00\u5730\u65B9\uFF0C\u4FDD\u5B58\u5728\u672C\u673A\u7684 ", /* @__PURE__ */ react_shim_default.createElement("span", { className: "sheet-code" }, store), "\uFF1B\u8FD9\u4E00\u9875\u4E0D\u5199 GitHub\u3002")), /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "dp-close", "aria-label": "\u5173\u95ED\u672C\u673A\u914D\u7F6E", onClick: onClose, "data-ui": part(ui, "close") }, "\xD7")), /* @__PURE__ */ react_shim_default.createElement("div", { className: "sheet-body" }, children), /* @__PURE__ */ react_shim_default.createElement("div", { className: "sheet-foot" }, /* @__PURE__ */ react_shim_default.createElement("div", { className: "foot-status", "aria-live": "polite" }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "foot-strong", "data-ui": part(ui, "status") }, hatch ? /* @__PURE__ */ react_shim_default.createElement("span", { className: "hatch" }) : null, strong), /* @__PURE__ */ react_shim_default.createElement("span", { className: "foot-quiet", "data-ui": part(ui, "status-note") }, quiet)), /* @__PURE__ */ react_shim_default.createElement("div", { className: "foot-actions" }, /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "btn", onClick: onClose, "data-ui": part(ui, "cancel") }, closeLabel), /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: "btn primary", disabled: !!saveOff, onClick: onSave, "data-ui": part(ui, "save") }, "\u4FDD\u5B58"))))
    );
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/status/Lamp.jsx
  function Lamp({ tone = "hollow", size, title, "data-ui": ui }) {
    const cls = ["lamp", size, tone].filter(Boolean).join(" ");
    return /* @__PURE__ */ react_shim_default.createElement("span", { className: cls, title, "data-ui": ui });
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/status/StepPill.jsx
  function StepPill({ phase, big, children, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("span", { className: big ? `pill big ${phase}` : `pill ${phase}`, "data-ui": ui }, children ?? phase);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/tasks/ColumnEyebrow.jsx
  function ColumnEyebrow({ label, count, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "col-eyebrow", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("span", { "data-ui": part(ui, "label") }, label), /* @__PURE__ */ react_shim_default.createElement("span", { "data-ui": part(ui, "count") }, String(count)));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/tasks/TaskRow.jsx
  function TaskRow({ row, onPick, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("button", { type: "button", className: row.cls, onClick: onPick, "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("span", { className: row.lampCls, title: row.lampWord, "data-ui": part(ui, "lamp") }), /* @__PURE__ */ react_shim_default.createElement("span", { className: "task-meta", "data-ui": part(ui, "meta") }, row.meta), /* @__PURE__ */ react_shim_default.createElement("span", { className: row.titleCls, "data-ui": part(ui, "title") }, row.title), /* @__PURE__ */ react_shim_default.createElement("span", { className: "task-progress" }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "bar" }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "bar-fill", style: { width: row.barStyle.width }, "data-ui": part(ui, "bar") })), /* @__PURE__ */ react_shim_default.createElement("span", { className: "task-count", "data-ui": part(ui, "count") }, row.count)));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/tasks/TasksEmpty.jsx
  function TasksEmpty({ "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("p", { className: "tasks-empty", "data-ui": ui }, "\u6CA1\u6709\u5E26 mmw:map label \u7684 ticket\u3002");
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/topbar/Brand.jsx
  function Brand({ repo, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: "brand", "data-ui": ui }, /* @__PURE__ */ react_shim_default.createElement("span", { className: "brand-mark", "data-ui": part(ui, "mark") }, "MMW"), /* @__PURE__ */ react_shim_default.createElement("span", { className: "brand-name", "data-ui": part(ui, "name") }, "task board"), /* @__PURE__ */ react_shim_default.createElement("span", { className: "brand-repo", "data-ui": part(ui, "repo") }, repo));
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/topbar/Counter.jsx
  function Counter({ lamp, label, count, sub, button, hot, title, onClick, "data-ui": ui }) {
    const kids = [
      /* @__PURE__ */ react_shim_default.createElement("span", { key: "l", className: `lamp ${lamp}`, "data-ui": part(ui, "lamp") }),
      label,
      /* @__PURE__ */ react_shim_default.createElement("span", { key: "n", className: hot ? "counter-n hot" : "counter-n", "data-ui": part(ui, "count") }, String(count)),
      sub ? /* @__PURE__ */ react_shim_default.createElement("span", { key: "s", className: "counter-sub", "data-ui": part(ui, "sub") }, sub) : null
    ];
    if (button) {
      return /* @__PURE__ */ react_shim_default.createElement(
        "button",
        {
          type: "button",
          className: hot ? "counter hot" : "counter",
          disabled: !hot,
          title,
          onClick,
          "data-ui": ui
        },
        kids
      );
    }
    return /* @__PURE__ */ react_shim_default.createElement("span", { className: "counter", "data-ui": ui }, kids);
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/topbar/IconButton.jsx
  var ICONS = {
    refresh: '<svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path></svg>',
    settings: '<svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg>'
  };
  function IconButton({ icon, on, label, title, onClick, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement(
      "button",
      {
        type: "button",
        className: on ? "gear on" : "gear",
        "aria-label": label,
        title,
        onClick,
        "data-ui": ui,
        dangerouslySetInnerHTML: { __html: ICONS[icon] }
      }
    );
  }

  // ../../../../../../../Users/cheuklapchan/multi-model-workflow/.worktrees/selkie/prototypes/task-board/design-system/components/topbar/ReadState.jsx
  function ReadState({ failed, text, "data-ui": ui }) {
    return /* @__PURE__ */ react_shim_default.createElement("div", { className: failed ? "readstate failed" : "readstate", "data-ui": ui }, text);
  }
  return __toCommonJS(entry_exports);
})();
window.MMWTaskBoard2_34b698 = Object.assign(window.MMWTaskBoard2_34b698 || {}, __ds);
