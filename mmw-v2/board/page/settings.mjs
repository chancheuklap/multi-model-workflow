import {
  CATALOG, LocalConfig, catalogFromPayload, settingsView,
} from "./local-config.mjs";
import {el, hand} from "./shared.mjs";

function copy(value) {
  return JSON.parse(JSON.stringify(value));
}

function selectEl(cls, value, disabled, label, opts, onChange, dataUi) {
  const options = opts || [];
  const node = el("select", {
    class: cls, "aria-label": label, disabled: !!disabled,
    "data-ui": dataUi,
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

function chipClass(cls) {
  const state = String(cls || "").trim().split(/\s+/)[1] || "";
  return state === "" || state === "ok" ? "pill tag" : "pill tag dashed";
}

function roleFoot(items, dataUi = null) {
  if (!items?.length) return null;
  return el("div", {class: "role-foot", "data-ui": dataUi}, items.map(item =>
    el("div", {class: "hatch-bar", "data-ui": dataUi ? `${dataUi}.item` : null},
      el("span", {class: "hatch-swatch"}), item.text)));
}

function flagsFromErrors(errors) {
  return (errors || []).map(error => {
    const [key, cell] = String(error.cell || "").split(".");
    return {key, cell: cell || key, text: error.reason};
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
  const saved = {runner: payload.runner, rows: copy(payload.rows)};
  return {
    catalog, scan: payload.scan.hosts,
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

function viewOf(model) {
  if (model.view) return model.view;
  return settingsView(model.st, model.scan, model.catalog);
}

function saveBody(model) {
  return {
    version: model.st.version,
    runner: model.st.draft.runner,
    rows: model.st.draft.rows,
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
    model.scan = body.hosts;
    model.st.scanSource = body.source;
    model.st.scannedAt = body.scanned_at;
    model.st.scanning = Boolean(body.scanning);
    redraw();
  };

  const restoreShown = shown => {
    model.st.scanning = false;
    if (shown) {
      model.view = shown;
      paint(host, model, api, hooks);
      return;
    }
    redraw();
  };

  const rescan = async source => {
    const shown = model.view ? copy(model.view) : null;
    model.st.scanning = true;
    state("scanning");
    redraw();
    const response = await hand(() => api.scanSettings({source}));
    if (!response?.ok) {
      restoreShown(shown);
      return;
    }
    const body = await readJson(response);
    if (!body.hosts) {
      restoreShown(shown);
      return;
    }
    applyScan(body);
  };

  const setCell = (key, cell, value) => {
    const previous = {runner: model.st.draft.runner};
    LocalConfig.setCell(model.scan, model.st.draft, key, cell, value);
    model.st.savedAt = null;
    model.st.serverFlags = [];
    if (key === "runner" && LocalConfig.needsRescan(previous, model.st.draft)) {
      void rescan(LocalConfig.source(model.st.draft));
      return;
    }
    state(LocalConfig.problems(model.scan, model.st.draft, model.catalog).length
      ? "incomplete" : "edited");
    redraw();
  };

  const save = async () => {
    const response = await hand(() => api.saveSettings(saveBody(model)));
    if (!response) return;
    const body = await readJson(response);
    if (response.status === 409) {
      model.st.refused = LocalConfig.changes(model.st.draft, model.st.saved).length || 1;
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
    const next = fromPayload(body);
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
        el("h2", {class: "title", "data-ui": "本机配置.sheet.title"}, "这台机器上，每个 agent 跑在哪"),
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
    el("section", {class: "set-block", "data-ui": "本机配置.hosts"},
      el("div", {class: "set-block-head"},
        el("span", {class: "eyebrow", "data-ui": "本机配置.hosts.title"}, "本机的 host"),
        el("span", {class: "scan", "data-ui": "本机配置.scan"},
          v.scanning ? [el("span", {class: "spin"}), v.scanningText] : [
            v.scannedText,
            el("button", {type: "button", class: "link",
              "data-ui": "本机配置.scan.rescan",
              onClick: () => void rescan(LocalConfig.source(model.st.draft))},
              "重新扫描"),
          ],
        ),
      ),
      el("div", {class: "hostscan"}, (v.chips || []).map(chip =>
        el("span", {class: chipClass(chip.cls), "data-ui": "本机配置.host"},
          el("span", {class: "pill-name", "data-ui": "本机配置.host.name"}, chip.host), chip.what))),
    ),
    el("section", {class: "set-block ruled", "data-ui": "本机配置.runner-block"},
      el("div", {class: "runner-row", "data-ui": "本机配置.runner"},
        el("div", {class: "role-name"},
          el("span", {class: "role-agent", "data-ui": "本机配置.runner.label"}, "runner"),
          el("span", {class: "role-what", "data-ui": "本机配置.runner.what"}, "用什么起 session")),
        selectEl(v.runnerCls, v.runner, v.runnerOff, "runner", v.runnerOpts,
          value => setCell("runner", "runner", value), "本机配置.runner.select"),
        v.runnerHasBad ? roleFoot(v.runnerBads) : null,
      ),
      el("p", {class: "set-note", "data-ui": "本机配置.runner-note"},
        "环境变量 ", el("span", {class: "code"}, "MMW_RUNNER"),
        " 设了时，它优先于这一格。「按所在环境判断」让 ",
        el("span", {class: "code"}, "start"),
        " 看自己跑在哪个 runner 里，判断不出时用 orca。runner 是 paseo 时，",
        el("span", {class: "code"}, "start"),
        " 向 Paseo 要 model，所以换到 paseo 或从 paseo 换走，选项会重新扫描。"),
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
          selectEl(row.hostCls, row.host, row.hostOff, row.hostLabel, row.hostOpts,
            value => setCell(row.agent, "host", value), "本机配置.role.host"),
          selectEl(row.modelCls, row.model, row.modelOff, row.modelLabel, row.modelOpts,
            value => setCell(row.agent, "model", value), "本机配置.role.model"),
          selectEl(row.effortCls, row.effort, row.effortOff, row.effortLabel, row.effortOpts,
            value => setCell(row.agent, "effort", value), "本机配置.role.effort"),
          row.hasBad ? roleFoot(row.bads, "本机配置.role.problem") : null,
        )),
      ),
      el("p", {class: "set-note", "data-ui": "本机配置.initial-note"},
        "一台新机器第一次安装时，这里填的是 MMW 自带的初始值；之后只按这里选的跑，MMW 更新不会改它。"),
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
