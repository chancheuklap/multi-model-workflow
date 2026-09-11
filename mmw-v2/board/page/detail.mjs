const REPO = "chancheuklap/multi-model-workflow";

function el(doc, tag, attrs = {}, ...kids) {
  const node = doc.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "disabled") node.disabled = true;
    else if (key === "html") node.innerHTML = value;
    else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid == null || kid === false) continue;
    node.append(typeof kid === "object" ? kid : String(kid));
  }
  return node;
}

function goto(hooks, n) {
  if (n == null) return;
  hooks.onGoto?.(n);
}

function relRow(doc, hooks, row, asButton) {
  const body = [
    el(doc, "span", {class: row.lightCls}),
    el(doc, "span", {class: "rel-num"}, row.num),
    el(doc, "span", {class: "rel-title"}, row.title, " ", el(doc, "span", {class: "rel-where"}, row.where || "")),
    el(doc, "span", {class: row.pillCls || row.stateCls}, row.step || row.state),
  ];
  if (asButton === false || row.unknown || row.known === false) {
    return el(doc, "div", {class: "rel-static"}, ...body);
  }
  return el(doc, "button", {type: "button", class: "rel", onClick: () => goto(hooks, row.n)}, ...body);
}

function origin(doc, hooks, d, links) {
  const parts = [el(doc, "span", {}, d.num)];
  for (const link of links || []) {
    parts.push(el(doc, "span", {}, "·"), el(doc, "button", {
      type: "button", class: "dp-link", onClick: () => goto(hooks, link.n),
    }, link.label));
  }
  return el(doc, "div", {class: "dp-origin"}, ...parts);
}

function path(doc, steps) {
  const parts = [];
  for (const step of steps || []) {
    parts.push(el(doc, "span", {class: step.cls}, step.name));
    if (step.sep) parts.push(el(doc, "span", {class: "path-sep"}, "›"));
  }
  return el(doc, "div", {class: "path"}, ...parts);
}

function ticketBody(doc, hooks, vals) {
  const d = vals.d;
  const kids = [];
  kids.push(
    el(doc, "div", {class: "dp-step"},
      el(doc, "span", {class: d.pillCls}, d.step),
      el(doc, "span", {class: "dp-hint"}, d.hint),
    ),
    path(doc, d.path),
  );
  if (d.hasWhy) {
    kids.push(el(doc, "div", {class: "why"},
      el(doc, "span", {class: "why-title"}, "为什么是橙的"),
      ...(d.why || []).map(item => el(doc, "span", {},
        el(doc, "b", {class: "why-child"}, item.head), " ", item.body)),
    ));
  }
  const runtime = [
    el(doc, "div", {class: "dp-section-title"},
      el(doc, "span", {}, "运行时"), el(doc, "span", {}, vals.runtimeNote || "")),
  ];
  if (d.hasWorker) {
    runtime.push(el(doc, "div", {class: "facts"},
      ...(d.facts || []).flatMap(fact => [
        el(doc, "span", {class: "fact-key"}, fact.k),
        el(doc, "span", {class: "fact-val"}, fact.v),
      ]),
    ));
    if (d.manySessions) {
      for (const session of d.sessions || []) {
        runtime.push(el(doc, "div", {class: "session"},
          el(doc, "span", {class: "session-kind"}, session.kind),
          el(doc, "span", {class: "session-what"}, session.what),
          el(doc, "span", {class: session.stateCls}, session.state),
        ));
      }
    }
  }
  if (vals.noWorker) {
    runtime.push(el(doc, "p", {class: "rel-none"},
      "尚未派发。frontier 选中它之后，这里会出现它跑在哪个 host、哪个 runner。"));
  }
  kids.push(el(doc, "section", {class: "dp-section"}, ...runtime));

  const blocking = [
    el(doc, "div", {class: "dp-section-title"}, el(doc, "span", {}, "阻塞")),
    el(doc, "div", {class: "rel-label"}, "阻塞它的"),
    ...(vals.blockers || []).map(row => relRow(doc, hooks, row)),
    d.noBlockers ? el(doc, "p", {class: "rel-none"}, "无，一开始就能动") : null,
    el(doc, "div", {class: "rel-label"}, "它阻塞的"),
    ...(vals.blocks || []).map(row => relRow(doc, hooks, row)),
    d.noBlocks ? el(doc, "p", {class: "rel-none"}, "无") : null,
  ];
  kids.push(el(doc, "section", {class: "dp-section"}, ...blocking));

  const childSection = [
    el(doc, "div", {class: "dp-section-title"},
      el(doc, "span", {}, "子 issue"), el(doc, "span", {}, d.kidCount)),
    ...(vals.kids || []).map(kid => el(doc, "div", {class: "kid"},
      el(doc, "span", {class: kid.lightCls}),
      el(doc, "span", {class: "kid-num"}, kid.num),
      el(doc, "span", {class: "kid-kind"}, kid.kind),
      kid.hasGoto
        ? el(doc, "button", {type: "button", class: "dp-link kid-to", onClick: () => goto(hooks, kid.goto)}, kid.to)
        : el(doc, "span", {class: kid.toCls}, kid.to),
      el(doc, "span", {class: "kid-title"}, kid.title),
    )),
    d.noKids ? el(doc, "p", {class: "rel-none"}, "没有开出子 issue") : null,
  ];
  kids.push(el(doc, "section", {class: "dp-section"}, ...childSection));

  const events = [
    el(doc, "div", {class: "dp-section-title"},
      el(doc, "span", {}, "事件"), el(doc, "span", {}, d.eventCount)),
    d.noEvents ? el(doc, "p", {class: "rel-none"}, "还没有事件。第一条会是 worker.started。") : null,
    el(doc, "div", {class: "events"},
      ...(d.events || []).map(event => el(doc, "div", {class: "ev"},
        el(doc, "span", {class: event.dotCls}),
        el(doc, "div", {class: "ev-head"},
          el(doc, "span", {class: "ev-time"}, event.time),
          el(doc, "span", {class: event.nameCls}, event.name),
          el(doc, "span", {class: "ev-field"}, event.field),
        ),
        el(doc, "div", {class: "ev-line"}, event.line),
      )),
    ),
  ];
  kids.push(el(doc, "section", {class: "dp-section"}, ...events));
  return kids;
}

function containerBody(doc, hooks, vals) {
  const d = vals.d;
  const kids = [
    el(doc, "section", {class: "dp-section"},
      el(doc, "div", {class: "dp-section-title"},
        el(doc, "span", {}, d.listTitle), el(doc, "span", {}, d.listCount)),
      el(doc, "div", {class: "lights-count"},
        ...(d.lights || []).map(item => el(doc, "span", {class: "lc-item"},
          el(doc, "span", {class: item.cls}), item.word, el(doc, "span", {class: "lc-n"}, item.n)))),
      el(doc, "div", {class: "steps-count"},
        ...(d.steps || []).map(item => el(doc, "span", {class: item.cls}, item.label))),
    ),
  ];
  if (d.isSpec) {
    kids.push(el(doc, "section", {class: "dp-section"},
      el(doc, "div", {class: "dp-section-title"}, el(doc, "span", {}, "按票号")),
      ...(vals.ticketRows || []).map(row => relRow(doc, hooks, row)),
    ));
  }
  if (d.isMap) {
    kids.push(el(doc, "section", {class: "dp-section"},
      el(doc, "div", {class: "dp-section-title"},
        el(doc, "span", {}, "spec"), el(doc, "span", {}, d.specCount)),
      ...(vals.specRows || []).map(row => relRow(doc, hooks, row)),
    ));
    if (d.hasDecisions) {
      kids.push(el(doc, "section", {class: "dp-section"},
        el(doc, "div", {class: "dp-section-title"},
          el(doc, "span", {}, "决策票"), el(doc, "span", {}, d.decisionCount)),
        ...(vals.decisionRows || []).map(row => relRow(doc, hooks, row)),
      ));
    }
  }
  return kids;
}

function decisionBody(doc, hooks, vals) {
  const d = vals.d;
  return [
    el(doc, "section", {class: "dp-section"},
      el(doc, "div", {class: "dp-section-title"}, el(doc, "span", {}, "阻塞")),
      el(doc, "div", {class: "rel-label"}, "阻塞它的"),
      ...(vals.blockers || []).map(row => relRow(doc, hooks, row)),
      d.noBlockers ? el(doc, "p", {class: "rel-none"}, "无") : null,
      el(doc, "div", {class: "rel-label"}, "它阻塞的"),
      ...(vals.blocks || []).map(row => relRow(doc, hooks, row)),
      d.noBlocks ? el(doc, "p", {class: "rel-none"}, "无") : null,
    ),
  ];
}

function card(doc, hooks, vals) {
  const d = vals.d;
  const head = el(doc, "div", {class: "dp-head"},
    el(doc, "span", {class: "dp-eyebrow"}, d.eyebrow),
    el(doc, "button", {type: "button", class: "dp-close", "aria-label": "关闭详情", onClick: () => hooks.onClose?.()}, "×"),
  );
  const parts = [head, origin(doc, hooks, d, vals.links)];
  if (d.closeout) {
    parts.push(el(doc, "div", {class: "dp-closeout"},
      el(doc, "span", {class: "dp-closeout-bar"}),
      "收口那一轮新开 · 出自",
      el(doc, "button", {type: "button", class: "dp-link", onClick: () => goto(hooks, d.closeoutFrom)}, d.closeoutFromLabel),
      d.closeoutChild,
    ));
  }
  parts.push(
    el(doc, "h2", {class: "dp-title"}, d.title),
    el(doc, "div", {class: "dp-status"},
      el(doc, "span", {class: d.lightCls}),
      el(doc, "span", {class: d.statusCls}, d.statusWord),
      el(doc, "span", {class: "dp-elapsed"}, d.elapsed || ""),
    ),
  );
  if (d.isTicket) parts.push(...ticketBody(doc, hooks, vals));
  if (d.isContainer) parts.push(...containerBody(doc, hooks, vals));
  if (d.isDecision) parts.push(...decisionBody(doc, hooks, vals));
  const repo = vals.repo || REPO;
  parts.push(el(doc, "button", {
    type: "button", class: "dp-gh",
    onClick: () => {
      const open = (globalThis.window || globalThis).open;
      if (typeof open === "function" && d.gh != null) {
        open(`https://github.com/${repo}/issues/${d.gh}`, "_blank", "noopener,noreferrer");
      }
    },
  }, d.ghLabel));
  return el(doc, "div", {class: "dp"}, ...parts);
}

export function render(host, data = {}, api = undefined, hooks = {}) {
  const doc = host.ownerDocument || document;
  const vals = data.vals || {
    d: {isEmpty: true, hasCard: false, hasTasks: true},
    emptyTitle: "点一张卡",
    emptyText: "画布上任意一张卡——map、spec、ticket 或决策票——点一下，它的全部细节就在这一栏。",
  };
  const d = vals.d || {isEmpty: true, hasCard: false};
  const root = el(doc, "aside", {class: "detail board", "aria-label": "详情"});
  root.dataset.screen = "detail";
  if (d.hasCard) root.append(card(doc, hooks, vals));
  else {
    root.append(el(doc, "div", {class: "dp-empty"},
      el(doc, "p", {class: "dp-empty-title"}, vals.emptyTitle),
      vals.emptyText,
    ));
  }
  if (host._detailEsc) doc.removeEventListener("keydown", host._detailEsc);
  host._detailEsc = event => { if (event.key === "Escape" && d.hasCard) hooks.onClose?.(); };
  doc.addEventListener("keydown", host._detailEsc);
  host.replaceChildren(root);
  return root;
}
