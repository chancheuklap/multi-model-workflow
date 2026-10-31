import {LocalConfig, catalogFromPayload, settingsView} from "./local-config.mjs";
import {el, hand, hhmm} from "./shared.mjs";

const SUB_HOSTS = [{id: "claude", label: "Claude"}, {id: "codex", label: "Codex"}];
const SUB_FIELDS = [{id: "model", label: "model"}, {id: "effort", label: "effort"}];
const INHERIT = "inherit";
const INHERIT_TEXT = "跟叫它的会话一样";
const FAILURE_KIND = {
  missing: "找不到命令", timeout: "超时", exit: "非零退出", unparseable: "读不出结构", empty: "读出空列表",
};
const TABS = [
  {id: "roles", label: "会话角色"},
  {id: "subagents", label: "子代理"},
  {id: "catalog", label: "型号目录"},
];

function copy(value) {
  return JSON.parse(JSON.stringify(value));
}

const tabOf = path => (path.startsWith("subagents.") ? "subagents" : "roles");
const shown = value => (value === INHERIT ? INHERIT_TEXT : value);
// One name per model on the whole sheet: the one the agent rows show. A subagent cell stores the catalog
// id, which models.py requires; the page shows the name the interface gives for that id.
const modelName = (model, host, value) =>
  (value === INHERIT ? INHERIT_TEXT : model.options.labels?.[host]?.[value] || value);

function readWhen(iso) {
  if (!iso) return "";
  const at = new Date(iso);
  const sameDay = at.toDateString() === new Date().toDateString();
  const mins = Math.max(0, Math.round((Date.now() - at) / 60000));
  const ago = mins < 1 ? "刚才" : mins < 60 ? `${mins} 分钟前`
    : mins < 1440 ? `${Math.round(mins / 60)} 小时前` : `${Math.round(mins / 1440)} 天前`;
  return `${sameDay ? "" : `${at.getMonth() + 1}月${at.getDate()}日 `}${hhmm(iso)}（${ago}）`;
}

function selectEl(cls, value, disabled, label, opts, onChange, dataUi, path) {
  const options = opts || [];
  const node = el("select", {
    class: cls, "aria-label": label, disabled: !!disabled,
    "data-ui": dataUi, "data-cell": path, "data-focus": path,
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

function roleFoot(items, dataUi = null) {
  if (!items?.length) return null;
  return el("div", {class: "role-foot", "data-ui": dataUi}, items.map(item =>
    el("div", {class: "hatch-bar", "data-ui": dataUi ? `${dataUi}.item` : null},
      el("span", {class: "hatch-swatch"}), item.text)));
}

// models.py names a session-role cell `<role>.<cell>`, a subagent cell `subagents.<row>.<host>.<field>`.
function flagsFromErrors(errors) {
  return (errors || []).map(error => {
    const cell = String(error.cell || "");
    if (cell === "runner") return {path: "runner", key: "runner", cell: "runner", text: error.reason};
    if (cell.startsWith("subagents")) return {path: cell, text: error.reason};
    const [key, part] = cell.split(".");
    if (key in LocalConfig.ROLE_WHAT || part) {
      return {path: `rows.${cell}`, key, cell: part || "host", text: error.reason};
    }
    return {path: cell, text: error.reason};
  });
}

const covers = (flagPath, path) => path === flagPath || path.startsWith(`${flagPath}.`);

function detachEsc(host) {
  if (!host._settingsEsc) return;
  document.removeEventListener("keydown", host._settingsEsc, true);
  host._settingsEsc = null;
}

export function unmount(host) {
  detachEsc(host);
  host.replaceChildren();
}

// The interface lists what a cell may hold besides `inherit`; every list on the page starts with it.
function withInherit(options) {
  const o = options || {rows: [], claude: {models: [], efforts: []}, codex: {models: [], inherit_efforts: []}, labels: {}};
  return {
    rows: o.rows, labels: o.labels,
    claude: {models: [INHERIT, ...o.claude.models], efforts: [INHERIT, ...o.claude.efforts]},
    codex: {
      models: [{model: INHERIT, efforts: o.codex.inherit_efforts}, ...o.codex.models],
      inheritEfforts: [INHERIT, ...o.codex.inherit_efforts],
    },
  };
}

export function fromPayload(payload) {
  const catalog = catalogFromPayload(payload);
  const saved = {runner: payload.runner, rows: copy(payload.rows), subagents: copy(payload.subagents || {})};
  return {
    catalog, scan: payload.scan.hosts,
    options: withInherit(payload.subagent_options),
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
      tab: "roles",
    },
  };
}

const Subagents = {
  rows: model => model.options.rows,
  get: (d, row, host) => d.subagents[row]?.[host] || {model: INHERIT, effort: INHERIT},
  codexEfforts(model, value) {
    const entry = model.options.codex.models.find(m => m.model === value);
    return entry ? [...new Set([INHERIT, ...entry.efforts])] : null;
  },
  effortsOf(model, host, value) {
    return host === "claude" ? model.options.claude.efforts : Subagents.codexEfforts(model, value);
  },
  modelsOf: (model, host) => (host === "claude"
    ? model.options.claude.models : model.options.codex.models.map(m => m.model)),
  set(model, d, row, host, field, value) {
    const cell = {...Subagents.get(d, row, host), [field]: value};
    if (field === "model") {
      const efforts = Subagents.effortsOf(model, host, value) || [];
      if (!efforts.includes(cell.effort)) cell.effort = INHERIT;
    }
    d.subagents[row] = {...d.subagents[row], [host]: cell};
  },
  changes(model, d, s) {
    const out = [];
    for (const row of Subagents.rows(model)) {
      for (const host of SUB_HOSTS) {
        const now = Subagents.get(d, row, host.id), was = Subagents.get(s, row, host.id);
        for (const field of SUB_FIELDS) {
          if (now[field.id] !== was[field.id]) {
            out.push({path: `subagents.${row}.${host.id}.${field.id}`, text: `${row} 的 ${host.label} ${field.label}`});
          }
        }
      }
    }
    return out;
  },
};

// A stale entry holds while the draft still carries the name it reports.
function draftValue(d, path) {
  const parts = path.split(".");
  if (parts[0] === "rows") return d.rows[parts[1]]?.[parts[2]];
  if (parts[0] === "subagents") return Subagents.get(d, parts[1], parts[2])[parts[3]];
  return d[path];
}

function staleText(entry, model) {
  const name = v => modelName(model, entry.host, v);
  return `存的是 ${name(entry.stored)}，${entry.host} 的目录里已经没有；现在可选：${entry.offered.map(name).join("、")}`;
}

function cellLabel(path) {
  const parts = path.split(".");
  if (parts[0] === "rows") return `会话角色 ${parts[1]} 的 ${parts[2]}`;
  if (parts[0] === "subagents") {
    const host = SUB_HOSTS.find(h => h.id === parts[2])?.label || parts[2];
    return `子代理 ${parts[1]} 的 ${host} ${parts[3]}`;
  }
  return path;
}

function view(model) {
  const st = model.st, d = st.draft;
  const launchable = LocalConfig.launchableHosts(d, model.catalog);
  const stale = model.stale.filter(entry => launchable.includes(entry.host)
    && draftValue(d, entry.cell) === entry.stored);
  const staleAt = path => stale.find(entry => entry.cell === path);
  const roleFlags = st.serverFlags.filter(f => f.key);
  const base = settingsView({...st, serverFlags: roleFlags}, model.scan, model.catalog);

  const roleProbs = [
    ...(st.scanning ? [] : LocalConfig.problems(model.scan, d, model.catalog)).map(p => {
      const entry = staleAt(p.key === "runner" ? "runner" : `rows.${p.key}.${p.cell}`);
      return entry ? {...p, text: staleText(entry, model)} : p;
    }),
    ...roleFlags,
  ];
  for (const row of base.rows) row.bads = roleProbs.filter(p => p.key === row.agent).map(p => ({text: p.text}));

  const subFlags = st.serverFlags.filter(f => !f.key && f.path.startsWith("subagents"));
  const otherFlags = st.serverFlags.filter(f => !f.key && !f.path.startsWith("subagents"));
  const subChanges = Subagents.changes(model, d, st.saved);
  const subProbs = [];
  const subRows = Subagents.rows(model).map(row => {
    const hosts = SUB_HOSTS.filter(host => launchable.includes(host.id)).map(host => {
      const cell = Subagents.get(d, row, host.id);
      const fields = SUB_FIELDS.map(field => {
        const path = `subagents.${row}.${host.id}.${field.id}`;
        const entry = staleAt(path);
        const flags = subFlags.filter(f => covers(f.path, path));
        if (entry) subProbs.push({path, row, text: `${host.label} ${field.label}：${staleText(entry, model)}`});
        for (const f of flags) subProbs.push({path, row, text: `${host.label} ${field.label}：${f.text}`});
        const changed = subChanges.some(c => c.path === path);
        return {path, field, bad: !!entry || flags.length > 0, changed};
      });
      const modelKnown = Subagents.modelsOf(model, host.id).includes(cell.model);
      const efforts = modelKnown ? Subagents.effortsOf(model, host.id, cell.model) : null;
      const mark = (list, value, missing, text = shown) => [
        ...(list.includes(value) ? [] : [{value, text: `${text(value)} · ${missing}`}]),
        ...list.map(v => ({value: v, text: text(v)})),
      ].map(o => ({...o, selected: o.value === value}));
      return {
        host, cell, fields,
        modelOpts: mark(Subagents.modelsOf(model, host.id), cell.model, "目录里已经没有",
          v => modelName(model, host.id, v)),
        effortOpts: efforts ? mark(efforts, cell.effort, `${cell.model} 没有这一档`)
          : [{value: cell.effort, text: shown(cell.effort), selected: true}],
        effortOff: !efforts,
      };
    });
    return {row, what: LocalConfig.SUBAGENT_WHAT[row] || "", hosts, bads: subProbs.filter(p => p.row === row)};
  });
  const roleChanges = LocalConfig.changes(d, st.saved, model.catalog);

  const hostCards = launchable.map(host => {
    const scan = LocalConfig.hostScan(model.scan, host);
    const state = LocalConfig.hostState(model.scan, d, host, model.catalog);
    return {
      host, state, failure: scan.failure || null,
      readAt: scan.read_at || (scan.offered?.length ? st.scannedAt : ""),
      word: state === "ok" ? `${scan.offered.length} 个 model` : LocalConfig.stateWord(state, d),
      offered: (scan.offered || []).map(o => o.model),
    };
  });
  const failures = hostCards.filter(c => c.failure).length;

  const probCount = roleProbs.length + subProbs.length + otherFlags.length;
  const changeTexts = [...roleChanges.map(c => c.text), ...subChanges.map(c => c.text)];
  const tabsWithProbs = [
    roleProbs.length ? "「会话角色」" : "", subProbs.length ? "「子代理」" : "",
  ].filter(Boolean).join("、");
  let strong, quiet, hatch = false;
  if (st.refused) {
    strong = "没有保存";
    quiet = "这一页打开之后，本机配置被别处改过，先重新读取。";
  } else if (st.scanning) {
    strong = "正在扫描本机的 host";
    quiet = "扫描完之前不能保存。";
  } else if (probCount) {
    strong = `有 ${probCount} 处不对，改好之前不能保存`;
    quiet = tabsWithProbs ? `带斜线的格子在${tabsWithProbs}页签里，下面一行写着哪里不对。` : "上面的斜线条写着哪里不对。";
    hatch = true;
  } else if (changeTexts.length) {
    strong = `改了 ${changeTexts.length} 处：${changeTexts.join("；")}`;
    quiet = "保存后，下一个新起的 agent 和下一次派出的子代理就用新值；已经在跑的不受影响。";
  } else if (st.savedAt) {
    strong = `已保存 · ${hhmm(st.savedAt)}`;
    quiet = "从下一个新起的 agent、下一次派出的子代理开始用；已经在跑的不受影响。";
  } else {
    strong = "没有改动";
    quiet = "三个页签里就是下一个新起的 agent 和子代理会用的配置。";
  }
  const saveOff = !changeTexts.length || probCount > 0 || st.serverFlags.length > 0
    || st.scanning || !!st.refused;

  const badge = (probs, changes) => (probs ? {text: `${probs} 处不对`, bad: true}
    : changes ? {text: `改了 ${changes} 处`, bad: false} : null);
  const tabBadges = {
    roles: [badge(roleProbs.length, roleChanges.length)].filter(Boolean),
    subagents: [badge(subProbs.length, subChanges.length)].filter(Boolean),
    catalog: [
      failures ? {text: "读取失败", bad: true} : null,
      stale.length ? {text: `${stale.length} 格旧型号`, bad: true} : null,
    ].filter(Boolean),
  };
  const codexInherit = model.options.codex.inheritEfforts.filter(e => e !== INHERIT);
  return {
    ...base, subRows, hostCards, stale, otherFlags, tabBadges, codexInherit,
    codexReadAt: hostCards.find(c => c.host === "codex")?.readAt || "",
    strong, quiet, hatch, saveOff,
    changed: changeTexts.length > 0,
    closeLabel: changeTexts.length ? "取消" : "关闭",
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
  const v = view(model);
  const st = model.st;
  const state = name => hooks.onState?.(name);
  const close = () => {
    unmount(host);
    state("closed");
    hooks.onClose?.();
  };
  const redraw = (focusKey = document.activeElement?.dataset?.focus) => {
    paint(host, model, api, hooks);
    if (focusKey) host.querySelector(`[data-focus="${CSS.escape(focusKey)}"]`)?.focus();
  };

  const rescan = async source => {
    st.scanning = true;
    state("scanning");
    redraw();
    const response = await hand(() => api.scanSettings({source}));
    const body = response?.ok ? await readJson(response) : {};
    st.scanning = false;
    if (body.hosts) {
      model.scan = body.hosts;
      st.scanSource = body.source;
      st.scannedAt = body.scanned_at;
      st.scanning = Boolean(body.scanning);
      LocalConfig.reconcileRunner(model.scan, st.draft, model.catalog);
    }
    redraw();
  };

  const edited = () => {
    st.savedAt = null;
    st.serverFlags = [];
    const after = view(model);
    state(after.hatch ? "incomplete" : "edited");
    redraw();
  };

  const setCell = (key, cell, value) => {
    const previous = {runner: st.draft.runner};
    LocalConfig.setCell(model.scan, st.draft, key, cell, value, model.catalog);
    if (key === "runner" && LocalConfig.needsRescan(previous, st.draft, model.catalog)) {
      st.savedAt = null;
      st.serverFlags = [];
      void rescan(st.draft.runner);
      return;
    }
    edited();
  };

  const setSub = (row, hostId, field, value) => {
    Subagents.set(model, st.draft, row, hostId, field, value);
    edited();
  };

  const showTab = (id, focus = true) => {
    st.tab = id;
    redraw(focus ? `tab:${id}` : null);
  };

  const jump = path => {
    st.tab = tabOf(path);
    redraw(null);
    const target = host.querySelector(`[data-cell="${CSS.escape(path)}"]`);
    if (!target) return;
    target.scrollIntoView({block: "center"});
    target.focus();
    target.classList.add("jumped");
    setTimeout(() => target.classList.remove("jumped"), 1600);
  };

  const save = async () => {
    const response = await hand(() => api.saveSettings({
      version: st.version, runner: st.draft.runner, rows: st.draft.rows, subagents: st.draft.subagents,
    }));
    if (!response) return;
    const body = await readJson(response);
    if (response.status === 409) {
      st.refused = (LocalConfig.changes(st.draft, st.saved).length
        + Subagents.changes(model, st.draft, st.saved).length) || 1;
      st.modifiedAt = body.modified_at;
      state("changed");
      redraw();
      return;
    }
    if (response.status === 422) {
      st.serverFlags = flagsFromErrors(body.errors);
      const first = st.serverFlags.find(f => f.path.startsWith("rows.") || f.path.startsWith("subagents."));
      if (first) st.tab = tabOf(first.path);
      state("refused");
      redraw();
      return;
    }
    if (!response.ok) return;
    st.saved = copy(st.draft);
    st.version = body.version ?? st.version;
    st.savedAt = body.saved_at;
    st.refused = 0;
    st.serverFlags = [];
    state("saved");
    redraw();
  };

  const reread = async () => {
    const response = await hand(() => api.settings());
    if (!response?.ok) return;
    const body = await readJson(response);
    if (body.runner == null) return;
    const tab = st.tab;
    Object.assign(model, fromPayload(body));
    model.st.reread = true;
    model.st.tab = tab;
    state("mine");
    paint(host, model, api, hooks);
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

  const sheet = el("div", {class: "sheet tabbed", role: "dialog", "aria-modal": "true", "aria-label": "本机配置"});
  sheet.append(
    el("div", {class: "sheet-head"},
      el("div", {class: "sheet-head-text"},
        el("span", {class: "eyebrow", "data-ui": "本机配置.sheet.eyebrow"}, "本机配置"),
        el("h2", {class: "title", "data-ui": "本机配置.sheet.title"}, "这台机器上，每个 agent 跑在哪"),
        el("p", {class: "sheet-intro", "data-ui": "本机配置.sheet.intro"},
          "这里就是 MMW 管这件事的唯一地方，保存在本机的 ",
          el("span", {class: "code"}, v.store),
          "；这一页不写 GitHub。三个页签共用底部的一个保存按钮。"),
      ),
      el("button", {type: "button", class: "iconbtn close", "aria-label": "关闭本机配置",
        "data-ui": "本机配置.sheet.close", onClick: close}, "×"),
    ),
  );

  const onTabKey = event => {
    const step = {ArrowRight: 1, ArrowLeft: -1}[event.key];
    if (!step) return;
    event.preventDefault();
    const at = TABS.findIndex(t => t.id === st.tab);
    showTab(TABS[(at + step + TABS.length) % TABS.length].id);
  };
  sheet.append(el("div", {class: "set-tabs", role: "tablist", "aria-label": "本机配置的三段", "data-ui": "本机配置.tabs"},
    TABS.map(tab => el("button", {
      type: "button", role: "tab", id: `set-tab-${tab.id}`, class: "set-tab",
      "aria-selected": String(st.tab === tab.id), "aria-controls": `set-panel-${tab.id}`,
      tabindex: st.tab === tab.id ? "0" : "-1", "data-focus": `tab:${tab.id}`,
      "data-ui": `本机配置.tab.${tab.id}`,
      onClick: () => showTab(tab.id), onKeydown: onTabKey,
    },
    el("span", {class: "set-tab-label"}, tab.label),
    v.tabBadges[tab.id].map(b => el("span", {class: `set-badge${b.bad ? " bad" : ""}`}, b.text)))),
  ));

  const body = el("div", {class: "sheet-body"});
  if (v.refused) {
    body.append(el("div", {class: "hatch-bar block refused-banner", role: "alert", "data-ui": "本机配置.refused"},
      el("p", {"data-ui": "本机配置.refused.text"},
        el("b", {}, "没有保存。"), v.refusedText),
      el("button", {type: "button", class: "btn sm", "data-ui": "本机配置.refused.reread",
        onClick: reread}, "重新读取")));
  }
  if (v.otherFlags.length) {
    body.append(el("div", {class: "set-flags", role: "alert", "data-ui": "本机配置.refused-cells"},
      roleFoot(v.otherFlags.map(f => ({text: `${f.path}：${f.text}`})))));
  }
  const panel = (id, ...kids) => el("div", {
    role: "tabpanel", id: `set-panel-${id}`, "aria-labelledby": `set-tab-${id}`,
    class: "set-panel", hidden: st.tab !== id, "data-ui": `本机配置.panel.${id}`,
  }, kids);

  body.append(
    panel("roles",
      el("section", {class: "set-block", "data-ui": "本机配置.runner-block"},
        el("div", {class: "runner-row", "data-ui": "本机配置.runner"},
          el("div", {class: "role-name"},
            el("span", {class: "role-agent", "data-ui": "本机配置.runner.label"}, "runner"),
            el("span", {class: "role-what", "data-ui": "本机配置.runner.what"}, "用什么起 session")),
          selectEl(v.runnerCls, v.runner, v.runnerOff, "runner", v.runnerOpts,
            value => setCell("runner", "runner", value), "本机配置.runner.select", "runner"),
          v.runnerHasBad ? roleFoot(v.runnerBads) : null,
        ),
        el("p", {class: "set-note", "data-ui": "本机配置.runner-note"},
          "环境变量 ", el("span", {class: "code"}, "MMW_RUNNER"),
          " 设了时，它优先于这一格。「按所在环境判断」让 ",
          el("span", {class: "code"}, "start"),
          " 看自己跑在哪个 runner 里，判断不出时用 orca。换 runner 后，型号目录不同就会重新扫描。"),
      ),
      el("section", {class: "set-block ruled", "data-ui": "本机配置.roles-block"},
        el("span", {class: "eyebrow", "data-ui": "本机配置.roles-block.title"}, "一个 agent 一行"),
        el("div", {class: "roles", "data-ui": "本机配置.roles"},
          el("div", {class: "eyebrow plain roles-head", "data-ui": "本机配置.roles.head"},
            el("span", {}, "agent"), el("span", {}, "host"),
            el("span", {}, "model"), el("span", {}, "effort")),
          (v.rows || []).map(row => el("div", {class: "role", "data-ui": "本机配置.role"},
            el("div", {class: "role-name"},
              el("span", {class: "role-agent", "data-ui": "本机配置.role.agent"}, row.agent),
              el("span", {class: "role-what", "data-ui": "本机配置.role.what"}, row.what)),
            ["host", "model", "effort"].map(cell => selectEl(
              row[`${cell}Cls`], row[cell], row[`${cell}Off`], row[`${cell}Label`], row[`${cell}Opts`],
              value => setCell(row.agent, cell, value), `本机配置.role.${cell}`, `rows.${row.agent}.${cell}`)),
            row.bads.length ? roleFoot(row.bads, "本机配置.role.problem") : null,
          )),
        ),
        el("p", {class: "set-note", "data-ui": "本机配置.initial-note"},
          "一台新机器第一次安装时，这里填的是 MMW 自带的初始值；之后只按这里选的跑，MMW 更新不会改它。",
          "下拉菜单里的 model 来自「型号目录」页签。"),
      ),
    ),
    panel("subagents",
      el("section", {class: "set-block", "data-ui": "本机配置.subagents-block"},
        el("span", {class: "eyebrow", "data-ui": "本机配置.subagents.title"}, "子代理"),
        el("p", {class: "set-note", "data-ui": "本机配置.subagents.intro"},
          "会话内部临时派出的帮手，只在步骤点名时派。只显示所选 runner 支持的 host；其他 host 的配置保留，切回支持它的 runner 后仍可使用。「",
          INHERIT_TEXT, "」就是用派它的那个会话自己的 model 或 effort。"),
        el("div", {class: "roles sub-roles", "data-ui": "本机配置.subagents"},
          el("div", {class: "eyebrow plain roles-head", "data-ui": "本机配置.subagents.head"},
            el("span", {}, "子代理"), el("span", {}, "host"), el("span", {}, "model"), el("span", {}, "effort")),
          v.subRows.map(r => el("div", {class: "role sub-role", role: "group", "aria-label": `子代理 ${r.row}`,
            "data-ui": "本机配置.subagent", style: `--host-count: ${r.hosts.length}`},
            el("div", {class: "role-name"},
              el("span", {class: "role-agent", "data-ui": "本机配置.subagent.name"}, r.row),
              el("span", {class: "role-what", "data-ui": "本机配置.subagent.what"}, r.what)),
            r.hosts.flatMap(h => [
              el("span", {class: "sub-host", "data-ui": "本机配置.subagent.host"}, h.host.id),
              ...h.fields.map(f => {
                const isModel = f.field.id === "model";
                const cls = `sel${f.bad ? " bad" : f.changed ? " changed" : ""}`;
                return selectEl(cls, h.cell[f.field.id], st.scanning || (!isModel && h.effortOff),
                  `${r.row} 的 ${h.host.label} ${f.field.label}`, isModel ? h.modelOpts : h.effortOpts,
                  value => setSub(r.row, h.host.id, f.field.id, value),
                  `本机配置.subagent.${h.host.id}.${f.field.id}`, f.path);
              }),
            ]),
            r.bads.length ? roleFoot(r.bads, "本机配置.subagent.problem") : null,
          )),
        ),
      ),
    ),
    panel("catalog",
      el("section", {class: "set-block", "data-ui": "本机配置.hosts"},
        el("div", {class: "set-block-head"},
          el("span", {class: "eyebrow", "data-ui": "本机配置.hosts.title"}, "本机的 host"),
          el("span", {class: "scan", "data-ui": "本机配置.scan"},
            v.scanning ? [el("span", {class: "spin"}), v.scanningText] : [
              v.scannedText,
              el("button", {type: "button", class: "link", "data-focus": "rescan",
                "data-ui": "本机配置.scan.rescan",
                onClick: () => void rescan(st.draft.runner)},
                "重新扫描"),
            ],
          ),
        ),
        el("p", {class: "set-note", "data-ui": "本机配置.catalog.intro"},
          "两个页签下拉菜单里的 model，都来自 MMW 问这台机器上每个 host 得到的目录，问的地方和 ",
          el("span", {class: "code"}, "start"),
          " 起 session 时问的是同一处。只显示所选 runner 支持的 host。读失败时，继续用上一次读成功的那份。"),
        el("div", {class: "set-hosts"}, v.hostCards.map(card => el("div", {
          class: "kv set-host", "data-ui": "本机配置.catalog.host",
        },
        el("div", {class: "set-host-head"},
          el("span", {class: v.scanning ? "pill tag dashed" : chipClass(card.state), "data-ui": "本机配置.host"},
            el("span", {class: "pill-name", "data-ui": "本机配置.host.name"}, card.host),
            v.scanning ? "…" : card.word),
          el("span", {class: "meta", "data-ui": "本机配置.catalog.read-at"},
            card.readAt ? `目录读于 ${readWhen(card.readAt)}` : "还没有读成功过")),
        card.failure ? el("div", {class: "hatch-bar set-failure", "data-ui": "本机配置.catalog.failure"},
          el("span", {class: "hatch-swatch"}),
          el("span", {},
            `最近一次读取失败（${card.failure.at ? hhmm(card.failure.at) : ""}）：`,
            `${FAILURE_KIND[card.failure.kind] || card.failure.kind} · ${card.failure.detail}`,
            card.readAt ? `。仍在用 ${hhmm(card.readAt)} 读到的那份。` : "。")) : null,
        card.offered.length ? el("div", {class: "kv-sub set-offered", "data-ui": "本机配置.catalog.offered"},
          "现在可选：", card.offered.join("、")) : null,
        ))),
      ),
      el("section", {class: "set-block ruled", "data-ui": "本机配置.catalog.stale"},
        el("span", {class: "eyebrow", "data-ui": "本机配置.catalog.stale.title"}, "存的型号已不在目录里"),
        v.stale.length ? el("ul", {class: "set-stale", "aria-label": "存的型号已不在目录里的格子"},
          v.stale.map(entry => el("li", {class: "set-stale-item", "data-ui": "本机配置.catalog.stale.item"},
            el("div", {class: "set-stale-text"},
              el("span", {class: "set-stale-cell"}, cellLabel(entry.cell)),
              el("span", {class: "role-what"}, staleText(entry, model))),
            el("button", {type: "button", class: "btn sm", "data-focus": `jump:${entry.cell}`,
              "aria-label": `跳到${cellLabel(entry.cell)}`, "data-ui": "本机配置.catalog.stale.jump",
              onClick: () => jump(entry.cell)}, "跳到这一格")))) :
          el("p", {class: "set-note", "data-ui": "本机配置.catalog.stale.none"}, "配置里存的 model 都还在目录里。"),
      ),
    ),
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
  host.replaceChildren(root);
  return root;
}

export function render(host, model, api, hooks = {}) {
  return paint(host, model, api, hooks);
}
