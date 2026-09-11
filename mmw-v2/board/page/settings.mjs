import {
  CATALOG, LocalConfig, catalogFromPayload, settingsView,
} from "./local-config.mjs";

function el(tag, attrs = {}, ...kids) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "disabled") node.disabled = true;
    else if (key === "selected") node.selected = true;
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

function copy(value) {
  return JSON.parse(JSON.stringify(value));
}

function code(...parts) {
  const node = el("p", {class: "set-note"});
  for (const part of parts) {
    if (Array.isArray(part)) node.append(el("span", {class: "sheet-code"}, part[0]));
    else node.append(part);
  }
  return node;
}

function selectEl(cls, value, disabled, label, opts, onChange) {
  const node = el("select", {
    class: cls, "aria-label": label, disabled: !!disabled,
    onChange: event => onChange(event.target.value),
  }, (opts || []).map(option => el("option", {
    value: option.value, disabled: !!option.disabled, label: option.text,
    selected: option.selected || option.value === value,
  }, option.text)));
  if (value != null) node.value = value;
  return node;
}

function roleFoot(items) {
  if (!items?.length) return null;
  return el("div", {class: "role-foot"}, items.map(item =>
    el("div", {class: "role-bad"}, el("span", {class: "hatch"}), item.text)));
}

export function fromScene(data = {}) {
  const st = copy(data.state?.st || {});
  if (st.saved && st.saved.version == null) st.version = st.version ?? 1;
  else st.version = st.saved?.version ?? st.version;
  return {view: data.vals?.v, st, catalog: CATALOG};
}

export function fromPayload(payload = {}) {
  const catalog = catalogFromPayload(payload);
  const scan = payload.scan?.hosts || {};
  const saved = {runner: payload.runner, rows: copy(payload.rows || {})};
  return {
    catalog, scan,
    st: {
      saved, draft: copy(saved),
      scanSource: payload.scan?.source || LocalConfig.source(saved),
      scannedAt: payload.scan?.scanned_at,
      scanning: Boolean(payload.scan?.scanning),
      savedAt: payload.saved_at || null,
      refused: 0, reread: false,
      version: payload.version,
      modifiedAt: payload.modified_at || null,
    },
  };
}

function viewOf(model) {
  if (model.view && !model.dirty) return model.view;
  return settingsView(model.st, model.scan || {}, model.catalog || CATALOG);
}

function saveBody(model) {
  const draft = model.st?.draft;
  const view = model.view;
  const rows = draft?.rows || Object.fromEntries((view?.rows || []).map(row => [
    row.agent, {host: row.host, model: row.model, effort: row.effort},
  ]));
  return {
    version: model.st?.version ?? model.st?.saved?.version ?? 1,
    runner: draft?.runner ?? view?.runner,
    rows,
  };
}

async function hand(method, apply) {
  try {
    const response = await method();
    if (response?.ok) apply?.(await response.json());
    return response;
  } catch {
    return null;
  }
}

function paint(host, model, api, hooks) {
  const v = viewOf(model);
  const close = () => hooks.onClose?.();
  const applyScan = body => {
    if (!body?.hosts) return;
    model.scan = body.hosts;
    model.st.scanSource = body.source || model.st.scanSource;
    model.st.scannedAt = body.scanned_at || model.st.scannedAt;
    model.st.scanning = Boolean(body.scanning);
    model.view = null;
    model.dirty = true;
    paint(host, model, api, hooks);
  };
  const rescan = source => {
    model.st.scanning = true;
    model.view = null;
    model.dirty = true;
    paint(host, model, api, hooks);
    void hand(() => api?.scanSettings({source}), applyScan);
  };
  const setCell = (key, cell, value) => {
    if (model.st?.draft) {
      const scan = model.scan || {};
      const previous = {runner: model.st.draft.runner};
      LocalConfig.setCell(scan, model.st.draft, key, cell, value);
      model.st.savedAt = null;
      model.view = null;
      model.dirty = true;
      if (key === "runner" && LocalConfig.needsRescan(previous, model.st.draft)) {
        rescan(LocalConfig.source(model.st.draft));
        return;
      }
    } else if (key === "runner") {
      const prev = LocalConfig.source({runner: v.runner});
      const next = LocalConfig.source({runner: value});
      if (prev !== next) void api?.scanSettings({source: next});
    }
    paint(host, model, api, hooks);
  };
  const save = async () => {
    const response = await hand(() => api?.saveSettings(saveBody(model)));
    if (!response) return;
    if (response.status === 409) {
      const body = await response.json().catch(() => ({}));
      model.st.refused = LocalConfig.changes(model.st.draft, model.st.saved).length || 1;
      model.st.modifiedAt = body.modified_at;
      model.view = null;
      model.dirty = true;
      paint(host, model, api, hooks);
      return;
    }
    if (!response.ok) return;
    const body = await response.json().catch(() => ({}));
    model.st.saved = copy(model.st.draft);
    model.st.version = body.version ?? model.st.version;
    model.st.savedAt = body.saved_at || new Date().toISOString();
    model.st.refused = 0;
    model.view = null;
    model.dirty = true;
    paint(host, model, api, hooks);
  };
  const reread = () => {
    void hand(() => api?.settings(), body => {
      if (!body || body.runner == null) return;
      const next = fromPayload(body);
      Object.assign(model, next);
      model.st.reread = true;
      model.view = null;
      model.dirty = true;
      paint(host, model, api, hooks);
    });
  };

  const root = el("div", {
    class: "scrim board",
    onClick: event => {
      if (event.target === event.currentTarget && !v.changed) close();
    },
  });
  root.dataset.screen = "settings";

  const sheet = el("div", {class: "sheet", role: "dialog", "aria-modal": "true", "aria-label": "本机配置"});
  sheet.append(
    el("div", {class: "sheet-head"},
      el("div", {class: "sheet-head-text"},
        el("span", {class: "dp-eyebrow"}, "本机配置"),
        el("h2", {class: "sheet-title"}, "这台机器上，每个角色跑在哪"),
        el("p", {class: "sheet-sub"},
          "下拉菜单里的选项，是 MMW 刚问过这台机器上的 host 得到的，问的地方和 ",
          el("span", {class: "sheet-code"}, "start"),
          " 起会话时问的是同一处。这里就是 MMW 管这件事的唯一地方，保存在本机的 ",
          el("span", {class: "sheet-code"}, v.store),
          "；这一页不写 GitHub。"),
      ),
      el("button", {type: "button", class: "dp-close", "aria-label": "关闭本机配置", onClick: close}, "×"),
    ),
  );

  const body = el("div", {class: "sheet-body"});
  if (v.refused) {
    body.append(el("div", {class: "refused", role: "alert"},
      el("p", {class: "refused-text"}, el("b", {}, "没有保存。"), v.refusedText),
      el("button", {type: "button", class: "btn", onClick: reread}, "重新读取")));
  }
  body.append(
    el("section", {class: "set-block"},
      el("div", {class: "set-block-head"},
        el("span", {class: "dp-section-title"}, "本机的 host"),
        el("span", {class: "scan"},
          v.scanning ? [el("span", {class: "spin"}), v.scanningText] : [
            v.scannedText,
            el("button", {type: "button", class: "linkbtn",
              onClick: () => rescan(LocalConfig.source(model.st?.draft || {runner: v.runner}))},
              "重新扫描"),
          ],
        ),
      ),
      el("div", {class: "hostscan"}, (v.chips || []).map(chip =>
        el("span", {class: chip.cls}, el("span", {class: "hs-name"}, chip.host), chip.what))),
    ),
    el("section", {class: "set-block ruled"},
      el("div", {class: "runner-row"},
        el("div", {class: "role-name"},
          el("span", {class: "role-agent"}, "runner"),
          el("span", {class: "role-what"}, "用什么起会话")),
        selectEl(v.runnerCls, v.runner, v.runnerOff, "runner", v.runnerOpts,
          value => setCell("runner", "runner", value)),
        v.runnerHasBad ? roleFoot(v.runnerBads) : null,
      ),
      code("环境变量 ", ["MMW_RUNNER"], " 设了时，它优先于这一格。「按所在环境判断」让 ",
        ["start"], " 看自己跑在哪个 runner 里，判断不出时用 orca。runner 是 paseo 时，",
        ["start"], " 向 Paseo 要 model，所以换到 paseo 或从 paseo 换走，选项会重新扫描。"),
    ),
    el("section", {class: "set-block ruled"},
      el("div", {class: "set-block-head"},
        el("span", {class: "dp-section-title"}, "一个角色一行")),
      el("div", {class: "roles"},
        el("div", {class: "roles-head"},
          el("span", {}, "agent"), el("span", {}, "host"),
          el("span", {}, "model"), el("span", {}, "effort")),
        (v.rows || []).map(row => el("div", {class: "role"},
          el("div", {class: "role-name"},
            el("span", {class: "role-agent"}, row.agent),
            el("span", {class: "role-what"}, row.what)),
          selectEl(row.hostCls, row.host, row.hostOff, row.hostLabel, row.hostOpts,
            value => setCell(row.agent, "host", value)),
          selectEl(row.modelCls, row.model, row.modelOff, row.modelLabel, row.modelOpts,
            value => setCell(row.agent, "model", value)),
          selectEl(row.effortCls, row.effort, row.effortOff, row.effortLabel, row.effortOpts,
            value => setCell(row.agent, "effort", value)),
          row.hasBad ? roleFoot(row.bads) : null,
        )),
      ),
      el("p", {class: "set-note"},
        "一台新机器第一次安装时，这里填的是 MMW 自带的初始值；之后只按这里选的跑，MMW 更新不会改它。"),
    ),
  );
  sheet.append(body);
  sheet.append(el("div", {class: "sheet-foot"},
    el("div", {class: "foot-status", "aria-live": "polite"},
      el("span", {class: "foot-strong"}, v.hatch ? el("span", {class: "hatch"}) : null, v.strong),
      el("span", {class: "foot-quiet"}, v.quiet)),
    el("div", {class: "foot-actions"},
      el("button", {type: "button", class: "btn", onClick: close}, v.closeLabel),
      el("button", {
        type: "button", class: "btn primary", disabled: !!v.saveOff, onClick: save,
      }, "保存")),
  ));
  root.append(sheet);

  if (host._settingsEsc) document.removeEventListener("keydown", host._settingsEsc, true);
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

export function render(host, data = {}, api, hooks = {}) {
  const model = data?.vals ? fromScene(data)
    : data?.st ? data
      : fromScene({state: {}, vals: {v: data.view || data}});
  if (!model.st) model.st = {draft: {runner: model.view?.runner, rows: {}}, saved: {runner: model.view?.runner, rows: {}}, refused: 0};
  return paint(host, model, api, hooks);
}
