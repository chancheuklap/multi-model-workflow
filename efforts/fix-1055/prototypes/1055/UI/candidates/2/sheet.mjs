// Variant 2 of the 本机配置 sheet (#1055): the page is organised by host. Each host is one block,
// headed by its model catalog's state; in it are the session roles that run on that host and the
// model and effort a subagent gets when a session on that host sends one.
import {LocalConfig, catalogFromPayload, settingsView} from "/local-config.mjs";
import {el, hand, hhmm} from "/shared.mjs";
// Prototype only: the real GET /api/settings does not answer the #1055 fields yet, so a reread adds them
// the way the mount does. The product copy drops this import and reads the answer as it comes.
import {withFake} from "../../fake.mjs";

export const name = "按 host 分块";

const STYLESHEET = new URL("./sheet.css", import.meta.url).href;
if (typeof document !== "undefined" && !document.querySelector(`link[href="${STYLESHEET}"]`)) {
  document.head.append(el("link", {rel: "stylesheet", href: STYLESHEET}));
}

const INHERIT = "inherit";
const INHERIT_TEXT = "跟叫它的会话一样";
const SUB_CELLS = ["model", "effort"];
const SUBAGENT_WHAT = {
  "review-axis": "代码审查时，审四个审查维度中的一个",
  reader: "读大量材料，交回浓缩的结论",
  default: "其余点名派出的子代理，包括没写派哪一行的",
};
const FAILURE_WORD = {
  missing: "本机找不到它的 CLI",
  exit: "CLI 出错退出",
  timeout: "超时",
  unparseable: "回答看不懂",
  empty: "回答了一个空列表",
};

function copy(value) {
  return JSON.parse(JSON.stringify(value));
}

function when(iso) {
  if (!iso) return "";
  const at = new Date(iso), now = new Date();
  return at.toDateString() === now.toDateString()
    ? hhmm(iso) : `${at.getMonth() + 1}月${at.getDate()}日 ${hhmm(iso)}`;
}

const subKey = (row, host) => `subagents.${row}.${host}`;
const shown = value => (value === INHERIT ? INHERIT_TEXT : value);

function selectEl(cls, value, disabled, label, opts, onChange, dataUi, focusKey) {
  const options = opts || [];
  const node = el("select", {
    class: cls, "aria-label": label, disabled: !!disabled,
    "data-ui": dataUi, "data-focus": focusKey,
    onChange: event => onChange(event.target.value),
  }, options.flatMap((option, index) => [
    index ? " " : null,
    el("option", {
      value: option.value, disabled: !!option.disabled, label: option.text,
      selected: option.selected || option.value === value,
    }, option.text),
  ]));
  if (value != null) node.value = value;
  return node;
}

function chipClass(state) {
  return state === "" || state === "ok" ? "pill tag" : "pill tag dashed";
}

function foot(items, dataUi) {
  if (!items?.length) return null;
  return el("div", {class: "role-foot", "data-ui": dataUi}, items.map(item =>
    el("div", {class: "hatch-bar", "data-ui": `${dataUi}.item`},
      el("span", {class: "hatch-swatch"}), item.text)));
}

// Server errors name a cell as `<role>.<cell>` or `subagents.<row>.<host>.<cell>`.
function flagsFromErrors(errors) {
  return (errors || []).map(error => {
    const parts = String(error.cell || "").split(".");
    if (parts[0] === "subagents") {
      const key = parts.length >= 3 ? subKey(parts[1], parts[2]) : parts.slice(0, 2).join(".");
      return {key, cell: parts[3] || "model", text: error.reason};
    }
    return {key: parts[0], cell: parts[1] || parts[0], text: error.reason};
  });
}

function detachEsc(host) {
  if (!host._settingsEsc) return;
  document.removeEventListener("keydown", host._settingsEsc, true);
  host._settingsEsc = null;
}

export function unmount(host) {
  detachEsc(host);
  host.replaceChildren();
}

export function fromPayload(payload) {
  const catalog = catalogFromPayload(payload);
  const saved = {runner: payload.runner, rows: copy(payload.rows), subagents: copy(payload.subagents || {})};
  return {
    catalog, scan: payload.scan.hosts,
    options: payload.subagent_options,
    stale: payload.stale || [],
    st: {
      saved, draft: copy(saved),
      scanSource: payload.scan.source,
      scannedAt: payload.scan.scanned_at,
      scanning: Boolean(payload.scan.scanning),
      savedAt: payload.saved_at || null,
      refused: 0, reread: false,
      version: payload.version,
      modifiedAt: payload.modified_at || null,
      serverFlags: [],
    },
  };
}

// The subagent cells: what each select offers, which cells changed, which a save would be refused on.
const Subagents = {
  hosts: options => ["claude", "codex"].filter(h => options?.[h]),
  modelsOf(options, host) {
    return host === "claude"
      ? options.claude.models.map(model => ({model, efforts: options.claude.efforts}))
      : options.codex.models;
  },
  effortsOf(options, host, model) {
    if (host === "claude") return options.claude.efforts;
    const found = options.codex.models.find(m => m.model === model);
    if (!found) return [];
    return found.efforts.includes(INHERIT) ? found.efforts : [INHERIT, ...found.efforts];
  },
  staleOf(stale, row, host, value) {
    return stale.find(s => s.cell === `${subKey(row, host)}.model` && s.stored === value) || null;
  },
  cell: (d, row, host) => d.subagents[row]?.[host] || {model: INHERIT, effort: INHERIT},
  set(options, d, row, host, cell, value) {
    const c = {...Subagents.cell(d, row, host), [cell]: value};
    if (cell === "model" && !Subagents.effortsOf(options, host, c.model).includes(c.effort)) c.effort = INHERIT;
    d.subagents[row] = {...d.subagents[row], [host]: c};
  },
  changes(options, d, s) {
    const out = [];
    for (const row of options.rows) {
      for (const host of Subagents.hosts(options)) {
        const a = Subagents.cell(d, row, host), b = Subagents.cell(s, row, host);
        const cells = SUB_CELLS.filter(c => a[c] !== b[c]);
        if (cells.length) out.push({key: subKey(row, host), text: `${row} 在 ${host} 上的 ${cells.join("、")}`, cells});
      }
    }
    return out;
  },
  problems(options, stale, d) {
    const out = [];
    for (const row of options.rows) {
      for (const host of Subagents.hosts(options)) {
        const c = Subagents.cell(d, row, host), s = Subagents.staleOf(stale, row, host, c.model);
        if (s) {
          out.push({key: subKey(row, host), cell: "model", text: staleText(s)});
          continue;
        }
        if (!Subagents.modelsOf(options, host).some(m => m.model === c.model)) {
          out.push({key: subKey(row, host), cell: "model", text: `${host} 的目录里没有 ${c.model}`});
          continue;
        }
        if (!Subagents.effortsOf(options, host, c.model).includes(c.effort)) {
          out.push({key: subKey(row, host), cell: "effort",
            text: `${c.model === INHERIT ? `「${INHERIT_TEXT}」时` : c.model} 没有 ${c.effort} 这一档`});
        }
      }
    }
    return out;
  },
  options(options, stale, d, row, host) {
    const c = Subagents.cell(d, row, host);
    const models = Subagents.modelsOf(options, host);
    const known = models.some(m => m.model === c.model);
    const model = [
      ...(known ? [] : [{value: c.model, text: `${c.model} · 目录里已经没有`}]),
      ...models.map(m => ({value: m.model, text: shown(m.model)})),
    ];
    const levels = known ? Subagents.effortsOf(options, host, c.model) : [];
    const effort = !known ? [{value: c.effort, text: shown(c.effort)}] : [
      ...(levels.includes(c.effort) ? [] : [{value: c.effort, text: `${shown(c.effort)} · 这个型号没有`}]),
      ...levels.map(e => ({value: e, text: shown(e)})),
    ];
    return {model, effort, known, stale: Subagents.staleOf(stale, row, host, c.model)};
  },
};

function staleText(s) {
  return `存的是 ${s.stored}，${s.host} 的目录里已经没有；现在可选：${s.offered.join("、")}`;
}

function viewOf(model) {
  if (model.view) return model.view;
  const {st, scan, catalog, options, stale} = model;
  const base = settingsView(st, scan, catalog);
  const draft = st.draft;
  const subFlags = (st.serverFlags || []).filter(f => f.key.startsWith("subagents"));
  const subProbs = [...(st.scanning ? [] : Subagents.problems(options, stale, draft)), ...subFlags];
  const subCh = Subagents.changes(options, draft, st.saved);
  const rowProbs = [
    ...(st.scanning ? [] : LocalConfig.problems(scan, draft, catalog)),
    ...(st.serverFlags || []).filter(f => !f.key.startsWith("subagents")),
  ];
  const rowCh = LocalConfig.changes(draft, st.saved, catalog);
  const probs = [...rowProbs, ...subProbs], ch = [...rowCh, ...subCh];

  for (const row of base.rows) {
    const s = stale.find(x => x.cell === `rows.${row.agent}.model` && x.stored === row.model);
    if (!s) continue;
    row.bads = row.bads.map(b => (b.text === `这台机器的 ${row.host} 已经不提供 ${row.model}` ? {text: staleText(s)} : b));
  }

  const cls = (key, cell) => (subProbs.some(p => p.key === key && p.cell === cell) ? "sel bad"
    : subCh.some(c => c.key === key && c.cells.includes(cell)) ? "sel changed" : "sel");
  const subagents = host => options.rows.map(row => {
    const key = subKey(row, host), c = Subagents.cell(draft, row, host);
    const o = Subagents.options(options, stale, draft, row, host);
    const bads = subProbs.filter(p => p.key === key).map(p => ({text: p.text}));
    return {
      row, host, key, what: SUBAGENT_WHAT[row] || "", model: c.model, effort: c.effort,
      modelOpts: o.model, effortOpts: o.effort, modelCls: cls(key, "model"), effortCls: cls(key, "effort"),
      off: st.scanning, effortOff: st.scanning || !o.known,
      modelLabel: `${row} 在 ${host} 上的 model`, effortLabel: `${row} 在 ${host} 上的 effort`, bads,
    };
  });

  const chipOf = Object.fromEntries((base.chips || []).map(c => [c.host, c]));
  const hostNames = [...catalog.hosts];
  const blocks = hostNames.map(host => {
    const entry = scan[host] || {};
    const failure = entry.failure || null;
    const chip = chipOf[host] || {cls: "hs", what: ""};
    return {
      host,
      chipCls: chipClass(String(chip.cls).trim().split(/\s+/)[1] || ""),
      chipWhat: chip.what,
      readAt: entry.read_at || "",
      readText: st.scanning ? "正在读型号目录…"
        : entry.read_at ? `型号目录 ${when(entry.read_at)} 读到` : "型号目录还没读成功过",
      failureText: failure && !st.scanning ? [
        `上次读取在 ${when(failure.at)} 失败：${FAILURE_WORD[failure.kind] || failure.kind}`,
        failure.detail ? `（${failure.detail}）` : "",
        "。",
        entry.read_at ? `下拉里仍是 ${when(entry.read_at)} 读到的目录。` : "下拉里没有可选的 model。",
      ].join("") : "",
      rows: base.rows.filter(r => r.host === host),
      subagents: Subagents.hosts(options).includes(host) ? subagents(host) : [],
    };
  });
  const stray = base.rows.filter(r => !hostNames.includes(r.host));

  const afterSave = "保存后，下一个新起的 agent 和它派的子代理就用新值；已经在跑的不受影响。";
  let strong, quiet, hatch = false;
  if (st.refused) {
    strong = "没有保存";
    quiet = "这一页打开之后，本机配置被别处改过，先重新读取。";
  } else if (st.scanning) {
    strong = "正在扫描本机的 host";
    quiet = "扫描完之前不能保存。";
  } else if (probs.length) {
    strong = `有 ${probs.length} 处 start 会拒绝，改好之前不能保存`;
    quiet = "带斜线的格子，下面一行写着哪里不对。";
    hatch = true;
  } else if (ch.length) {
    strong = `改了 ${ch.length} 处：${ch.map(c => c.text).join("；")}`;
    quiet = afterSave;
  } else if (st.savedAt) {
    strong = `已保存 · ${hhmm(st.savedAt)}`;
    quiet = "从下一个新起的 agent 开始用；已经在跑的不受影响。";
  } else {
    strong = "没有改动";
    quiet = "上面就是下一个新起的 agent 会用的配置。";
  }
  return {
    ...base, blocks, stray, strong, quiet, hatch,
    closeLabel: ch.length ? "取消" : "关闭",
    saveOff: !ch.length || probs.length > 0 || !!st.scanning || !!st.refused,
    changed: ch.length > 0,
  };
}

function saveBody(model) {
  return {
    version: model.st.version,
    runner: model.st.draft.runner,
    rows: model.st.draft.rows,
    subagents: model.st.draft.subagents,
  };
}

async function readJson(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

function roleRow(row, setCell) {
  return el("div", {class: "role", "data-ui": "本机配置.role"},
    el("div", {class: "role-name"},
      el("span", {class: "role-agent", "data-ui": "本机配置.role.agent"}, row.agent),
      el("span", {class: "role-what", "data-ui": "本机配置.role.what"}, row.what)),
    selectEl(row.hostCls, row.host, row.hostOff, row.hostLabel, row.hostOpts,
      value => setCell(row.agent, "host", value), "本机配置.role.host", `${row.agent}.host`),
    selectEl(row.modelCls, row.model, row.modelOff, row.modelLabel, row.modelOpts,
      value => setCell(row.agent, "model", value), "本机配置.role.model", `${row.agent}.model`),
    selectEl(row.effortCls, row.effort, row.effortOff, row.effortLabel, row.effortOpts,
      value => setCell(row.agent, "effort", value), "本机配置.role.effort", `${row.agent}.effort`),
    row.hasBad ? foot(row.bads, "本机配置.role.problem") : null,
  );
}

function subagentRow(s, setSub) {
  return el("div", {class: "role", "data-ui": "本机配置.subagent"},
    el("div", {class: "role-name"},
      el("span", {class: "role-agent", "data-ui": "本机配置.subagent.name"}, s.row),
      el("span", {class: "role-what", "data-ui": "本机配置.subagent.what"}, s.what)),
    el("span", {class: "host-cell", "aria-hidden": "true"}, s.host),
    selectEl(s.modelCls, s.model, s.off, s.modelLabel, s.modelOpts,
      value => setSub(s.row, s.host, "model", value), "本机配置.subagent.model", `${s.key}.model`),
    selectEl(s.effortCls, s.effort, s.effortOff, s.effortLabel, s.effortOpts,
      value => setSub(s.row, s.host, "effort", value), "本机配置.subagent.effort", `${s.key}.effort`),
    s.bads.length ? foot(s.bads, "本机配置.subagent.problem") : null,
  );
}

function hostBlock(b, setCell, setSub) {
  const titleId = `host-block-${b.host}`;
  return el("section", {class: "set-block ruled host-block", "aria-labelledby": titleId,
    "data-ui": "本机配置.host-block", "data-host": b.host},
  el("div", {class: "host-block-head"},
    el("h3", {class: "host-block-name", id: titleId, "data-ui": "本机配置.host.name"}, b.host),
    el("span", {class: b.chipCls, "data-ui": "本机配置.host"}, b.chipWhat),
    el("span", {class: "host-read", "data-ui": "本机配置.host.read-at"}, b.readText)),
  b.failureText ? el("div", {class: "hatch-bar host-failure", role: "status",
    "data-ui": "本机配置.host.failure"}, el("span", {class: "hatch-swatch"}), b.failureText) : null,
  el("div", {class: "roles", role: "group", "aria-label": `跑在 ${b.host} 上的会话角色`,
    "data-ui": "本机配置.roles"},
  el("div", {class: "eyebrow plain roles-head"},
    el("span", {}, "会话角色"), el("span", {}, "host"), el("span", {}, "model"), el("span", {}, "effort")),
  b.rows.length ? b.rows.map(row => roleRow(row, setCell))
    : el("p", {class: "set-note empty-note"}, `现在没有会话角色跑在 ${b.host} 上；把某一行的 host 换成 ${b.host}，它就到这一块来。`)),
  b.subagents.length ? el("div", {class: "roles subagents", role: "group",
    "aria-label": `${b.host} 上的子代理`, "data-ui": "本机配置.subagents"},
  el("div", {class: "eyebrow plain roles-head"},
    el("span", {}, "子代理"), el("span", {}), el("span", {}, "model"), el("span", {}, "effort")),
  el("p", {class: "set-note sub-note"},
    `会话内部临时派出的帮手，只在步骤点名时派。跑在 ${b.host} 上的会话派子代理时，用这几格；`,
    `选「${INHERIT_TEXT}」就用派它的那个会话自己的 model 或 effort。`),
  b.subagents.map(s => subagentRow(s, setSub))) : null,
  );
}

function paint(host, model, api, hooks) {
  const focused = document.activeElement?.dataset?.focus || null;
  const v = viewOf(model);
  const state = name => hooks.onState?.(name);
  const close = () => {
    unmount(host);
    state("closed");
    hooks.onClose?.();
  };
  const redraw = () => {
    model.view = null;
    paint(host, model, api, hooks);
  };

  const applyScan = body => {
    // A host the scan just answered was read at the scan's time, when the answer leaves read_at empty.
    for (const entry of Object.values(body.hosts)) {
      if (!entry.read_at && entry.state === "ok") entry.read_at = body.scanned_at;
    }
    model.scan = body.hosts;
    model.st.scanSource = body.source;
    model.st.scannedAt = body.scanned_at;
    model.st.scanning = Boolean(body.scanning);
    redraw();
  };

  const rescan = async source => {
    model.st.scanning = true;
    state("scanning");
    redraw();
    const response = await hand(() => api.scanSettings({source}));
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

  const edited = () => {
    model.st.savedAt = null;
    model.st.serverFlags = [];
    model.view = null;
    state(viewOf(model).hatch ? "incomplete" : "edited");
    redraw();
  };

  const setCell = (key, cell, value) => {
    const previous = {runner: model.st.draft.runner};
    LocalConfig.setCell(model.scan, model.st.draft, key, cell, value);
    if (key === "runner" && LocalConfig.needsRescan(previous, model.st.draft)) {
      model.st.savedAt = null;
      model.st.serverFlags = [];
      void rescan(LocalConfig.source(model.st.draft));
      return;
    }
    edited();
  };

  const setSub = (row, h, cell, value) => {
    Subagents.set(model.options, model.st.draft, row, h, cell, value);
    edited();
  };

  const save = async () => {
    const response = await hand(() => api.saveSettings(saveBody(model)));
    if (!response) return;
    const body = await readJson(response);
    if (response.status === 409) {
      model.st.refused = (LocalConfig.changes(model.st.draft, model.st.saved).length
        + Subagents.changes(model.options, model.st.draft, model.st.saved).length) || 1;
      model.st.modifiedAt = body.modified_at;
      state("changed");
      redraw();
      return;
    }
    if (response.status === 422) {
      model.st.serverFlags = flagsFromErrors(body.errors);
      state("refused");
      redraw();
      return;
    }
    if (!response.ok) return;
    model.st.saved = copy(model.st.draft);
    model.st.version = body.version ?? model.st.version;
    model.st.savedAt = body.saved_at;
    model.st.refused = 0;
    model.st.serverFlags = [];
    state("saved");
    redraw();
  };

  const reread = async () => {
    const response = await hand(() => api.settings());
    if (!response?.ok) return;
    const body = await readJson(response);
    if (body.runner == null) return;
    const next = fromPayload(withFake(body));
    Object.assign(model, next);
    model.st.reread = true;
    state("mine");
    redraw();
  };

  const root = el("div", {
    class: `settings-root board${hooks.onClose ? " transparent" : ""}`,
    "data-ui": "本机配置.root",
  });
  root.dataset.screen = "settings";
  const scrim = el("div", {
    class: "scrim board", "data-ui": "本机配置.sheet",
    onClick: event => {
      if (event.target === event.currentTarget && !v.changed) close();
    },
  });

  const sheet = el("div", {class: "sheet", role: "dialog", "aria-modal": "true", "aria-label": "本机配置"});
  sheet.append(
    el("div", {class: "sheet-head"},
      el("div", {class: "sheet-head-text"},
        el("span", {class: "eyebrow", "data-ui": "本机配置.sheet.eyebrow"}, "本机配置"),
        el("h2", {class: "title", "data-ui": "本机配置.sheet.title"}, "这台机器上，每个 host 跑哪些 agent"),
        el("p", {class: "sheet-intro", "data-ui": "本机配置.sheet.intro"},
          "下拉菜单里的选项，是 MMW 刚问过这台机器上的 host 得到的，问的地方和 ",
          el("span", {class: "code"}, "start"),
          " 起 session 时问的是同一处。这里就是 MMW 管这件事的唯一地方，保存在本机的 ",
          el("span", {class: "code"}, v.store),
          "；这一页不写 GitHub。"),
      ),
      el("button", {type: "button", class: "iconbtn close", "aria-label": "关闭本机配置",
        "data-ui": "本机配置.sheet.close", onClick: close}, "×"),
    ),
  );

  const body = el("div", {class: "sheet-body"});
  if (v.refused) {
    body.append(el("div", {class: "hatch-bar block refused-banner", role: "alert", "data-ui": "本机配置.refused"},
      el("p", {"data-ui": "本机配置.refused.text"},
        el("b", {}, "没有保存。"), v.refusedText),
      el("button", {type: "button", class: "btn sm", "data-ui": "本机配置.refused.reread",
        onClick: reread}, "重新读取")));
  }
  body.append(
    el("section", {class: "set-block", "data-ui": "本机配置.runner-block"},
      el("div", {class: "runner-row", "data-ui": "本机配置.runner"},
        el("div", {class: "role-name"},
          el("span", {class: "role-agent", "data-ui": "本机配置.runner.label"}, "runner"),
          el("span", {class: "role-what", "data-ui": "本机配置.runner.what"}, "用什么起 session")),
        selectEl(v.runnerCls, v.runner, v.runnerOff, "runner", v.runnerOpts,
          value => setCell("runner", "runner", value), "本机配置.runner.select", "runner"),
        el("span", {class: "scan", "data-ui": "本机配置.scan"},
          v.scanning ? [el("span", {class: "spin"}), v.scanningText] : [
            v.scannedText,
            el("button", {type: "button", class: "link",
              "data-ui": "本机配置.scan.rescan",
              onClick: () => void rescan(LocalConfig.source(model.st.draft))},
            "重新扫描"),
          ],
        ),
        v.runnerHasBad ? foot(v.runnerBads, "本机配置.runner.problem") : null,
      ),
      el("p", {class: "set-note", "data-ui": "本机配置.runner-note"},
        "环境变量 ", el("span", {class: "code"}, "MMW_RUNNER"),
        " 设了时，它优先于这一格。「按所在环境判断」让 ",
        el("span", {class: "code"}, "start"),
        " 看自己跑在哪个 runner 里，判断不出时用 orca。runner 是 paseo 时，",
        el("span", {class: "code"}, "start"),
        " 向 Paseo 要 model，所以换到 paseo 或从 paseo 换走，选项会重新扫描。"),
    ),
    ...v.blocks.map(b => hostBlock(b, setCell, setSub)),
    v.stray.length ? el("section", {class: "set-block ruled host-block", "aria-label": "MMW 不认识的 host",
      "data-ui": "本机配置.host-block"},
    el("div", {class: "host-block-head"},
      el("h3", {class: "host-block-name"}, "MMW 不认识的 host")),
    el("div", {class: "roles", role: "group", "aria-label": "跑在 MMW 不认识的 host 上的会话角色"},
      v.stray.map(row => roleRow(row, setCell)))) : "",
    el("p", {class: "set-note initial-note", "data-ui": "本机配置.initial-note"},
      "一台新机器第一次安装时，这里填的是 MMW 自带的初始值；之后只按这里选的跑，MMW 更新不会改它。"),
  );
  sheet.append(body);
  sheet.append(el("div", {class: "sheet-foot"},
    el("div", {class: "foot-status", "aria-live": "polite"},
      el("span", {class: "foot-strong", "data-ui": "本机配置.sheet.status"},
        v.hatch ? el("span", {class: "hatch-swatch"}) : null, v.strong),
      el("span", {class: "foot-quiet", "data-ui": "本机配置.sheet.status-note"}, v.quiet)),
    el("div", {class: "foot-actions"},
      el("button", {type: "button", class: "btn", "data-ui": "本机配置.sheet.cancel",
        onClick: close}, v.closeLabel),
      el("button", {
        type: "button", class: "btn primary", "data-ui": "本机配置.sheet.save",
        disabled: !!v.saveOff, onClick: save,
      }, "保存")),
  ));
  scrim.append(sheet);
  root.append(scrim);

  detachEsc(host);
  host._settingsEsc = event => {
    if (event.key !== "Escape") return;
    event.preventDefault();
    event.stopImmediatePropagation();
    close();
  };
  document.addEventListener("keydown", host._settingsEsc, true);
  const scrollTop = host.querySelector(".sheet-body")?.scrollTop || 0;
  host.replaceChildren(root);
  body.scrollTop = scrollTop;
  // A row whose host changed moves to its new host's block; keep the keyboard on the select it was on.
  if (focused) {
    const target = root.querySelector(`[data-focus="${focused}"]`);
    target?.focus();
    target?.closest(".role")?.scrollIntoView({block: "nearest"});
  }
  return root;
}

export function render(host, model, api, hooks = {}) {
  return paint(host, model, api, hooks);
}
