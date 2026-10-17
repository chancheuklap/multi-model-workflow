import {LocalConfig, settingsView} from "/local-config.mjs";
import {hhmm} from "/shared.mjs";

export const INHERIT = "inherit";
export const INHERIT_TEXT = "跟叫它的会话一样";

const label = value => (value === INHERIT ? INHERIT_TEXT : value);
const mark = (opts, value) => opts.map(o => ({...o, selected: o.value === value, disabled: !!o.disabled}));

// The subagent rows of dispatch's roles.json `subagents`, and the options models.py accepts for
// them, both as the settings API hands them over (`subagent_options`); nothing here lists a model.
export const Subagents = {
  HOSTS: ["claude", "codex"],
  HOST_TEXT: {claude: "Claude", codex: "Codex"},
  CELLS: ["model", "effort"],
  WHAT: {
    "review-axis": "code-review 的四个审查轴，一个轴派一个",
    reader: "读大量材料，交回压缩过的结论",
    default: "其余点了名的子代理步骤，也包括没点行名的",
  },
  key: row => `sub:${row}`,
  rows: options => options?.rows || [],
  models: (options, host) => (host === "claude"
    ? options.claude.models : options.codex.models.map(m => m.model)),
  efforts(options, host, model) {
    if (host === "claude") return options.claude.efforts;
    if (model === INHERIT) return options.codex.inheritEfforts;
    const found = options.codex.models.find(m => m.model === model);
    return found ? [INHERIT, ...found.efforts.filter(e => e !== INHERIT)] : [];
  },
  staleOf: (stale, cell, stored) => (stale || []).find(s => s.cell === cell && s.stored === stored),

  problems(options, d, stale) {
    const S = Subagents, out = [];
    for (const row of S.rows(options)) {
      for (const host of S.HOSTS) {
        const c = d.subagents[row][host], key = S.key(row), name = S.HOST_TEXT[host];
        if (!S.models(options, host).includes(c.model)) {
          const gone = S.staleOf(stale, `subagents.${row}.${host}.model`, c.model);
          out.push({key, cell: `${host}.model`, text: gone
            ? `存的是 ${gone.stored}，${name} 的型号目录里已经没有它；现在可选：${gone.offered.join("、")}`
            : `${name} 的型号目录里没有 ${c.model}`});
          continue;
        }
        if (!c.effort) {
          out.push({key, cell: `${host}.effort`, text: `换了 ${name} 的 model，还没选 effort`});
          continue;
        }
        if (!S.efforts(options, host, c.model).includes(c.effort)) {
          out.push({key, cell: `${host}.effort`, text: `${label(c.model)} 在 ${name} 上没有 ${c.effort} 这一档`});
        }
      }
    }
    return out;
  },
  changes(options, d, s) {
    const S = Subagents, out = [];
    for (const row of S.rows(options)) {
      const cells = S.HOSTS.flatMap(host => S.CELLS
        .filter(cell => d.subagents[row][host][cell] !== s.subagents[row][host][cell])
        .map(cell => `${host}.${cell}`));
      if (cells.length) {
        const words = cells.map(c => {
          const [host, cell] = c.split(".");
          return `${S.HOST_TEXT[host]} ${cell}`;
        });
        out.push({key: S.key(row), text: `${row} 的 ${words.join("、")}`, cells});
      }
    }
    return out;
  },
  setCell(options, d, row, host, cell, value) {
    const c = d.subagents[row][host];
    c[cell] = value;
    if (cell === "model" && !Subagents.efforts(options, host, value).includes(c.effort)) c.effort = "";
    return d;
  },
  cellOptions(options, d, row, host) {
    const S = Subagents, c = d.subagents[row][host];
    const models = S.models(options, host), efforts = S.efforts(options, host, c.model);
    const modelKnown = models.includes(c.model);
    const model = [
      ...(modelKnown ? [] : [{value: c.model, text: `${c.model} · 目录里已经没有`}]),
      ...models.map(m => ({value: m, text: label(m)})),
    ];
    const effort = !modelKnown ? [{value: c.effort, text: label(c.effort) || "—"}] : [
      ...(!c.effort ? [{value: "", text: "选一档", disabled: true}]
        : efforts.includes(c.effort) ? [] : [{value: c.effort, text: `${label(c.effort)} · 这个 model 没有`}]),
      ...efforts.map(e => ({value: e, text: label(e)})),
    ];
    return {model: mark(model, c.model), effort: mark(effort, c.effort), modelKnown};
  },
};

// A 422 names a cell as `runner`, `<role>.<cell>` or `subagents.<row>.<host>[.<cell>]`.
export function flagsFromErrors(errors) {
  return (errors || []).map(error => {
    const parts = String(error.cell || "").split(".");
    if (parts[0] === "subagents") {
      const [, row = "", host = "claude", cell = "model"] = parts;
      return {key: Subagents.key(row), cell: `${host}.${cell}`, text: error.reason};
    }
    const [key, cell] = parts[0] === "rows" ? parts.slice(1) : parts;
    return {key, cell: cell || key, text: error.reason};
  });
}

const KIND = {
  missing: "找不到命令", timeout: "超时", exit: "非零退出", unparseable: "读不出结构", empty: "读出空列表",
};

function when(iso) {
  if (!iso) return "";
  const at = new Date(iso), now = new Date();
  if (at.toDateString() === now.toDateString()) return hhmm(iso);
  return `${String(at.getMonth() + 1).padStart(2, "0")}-${String(at.getDate()).padStart(2, "0")} ${hhmm(iso)}`;
}

function catalogLine(host, entry) {
  const readText = entry?.read_at ? `型号目录 ${when(entry.read_at)} 读到` : "还没读到过型号目录";
  const f = entry?.failure;
  const failure = f ? `${host} 的型号目录上次读取失败 · ${when(f.at)} · ${KIND[f.kind] || f.kind}：${f.detail}。${
    entry.read_at ? `下拉框里仍是 ${when(entry.read_at)} 读到的那一份。` : "还没有可用的目录。"}` : "";
  return {readText, failure};
}

// The whole sheet's view: what settingsView gives the runner and the agent rows, plus the
// subagent rows, each host's catalog status, and a footer and Save rule that count both kinds of row.
export function sheetView(st, scan, catalog, options, stale) {
  const L = LocalConfig, S = Subagents, d = st.draft;
  const flags = st.serverFlags || [];
  const base = settingsView({...st, serverFlags: flags.filter(f => !f.key.startsWith("sub:"))}, scan, catalog);

  const rowProbs = (st.scanning ? [] : L.problems(scan, d, catalog)).map(p => {
    const r = d.rows[p.key];
    const gone = p.cell === "model" && r && S.staleOf(stale, `rows.${p.key}.model`, r.model);
    return gone ? {...p, text: `存的是 ${gone.stored}，这台机器的 ${r.host} 已经不提供；现在可选：${gone.offered.join("、")}`} : p;
  });
  const subProbs = S.problems(options, d, stale);
  const probs = [...rowProbs, ...subProbs, ...flags];
  const ch = [...L.changes(d, st.saved, catalog), ...S.changes(options, d, st.saved)];
  const bads = key => probs.filter(p => p.key === key).map(p => ({text: p.text}));
  const cls = (key, cell) => (probs.some(p => p.key === key && p.cell === cell) ? "sel bad"
    : ch.some(c => c.key === key && c.cells.includes(cell)) ? "sel changed" : "sel");

  const rows = base.rows.map(row => {
    const b = bads(row.agent);
    return {...row, bads: b, hasBad: b.length > 0};
  });
  const subagents = S.rows(options).map(name => {
    const key = S.key(name), b = bads(key);
    return {
      name, what: S.WHAT[name] || "",
      lines: S.HOSTS.map(host => {
        const o = S.cellOptions(options, d, name, host), c = d.subagents[name][host];
        return {
          host, hostText: S.HOST_TEXT[host], model: c.model, effort: c.effort,
          modelOpts: o.model, effortOpts: o.effort,
          modelCls: cls(key, `${host}.model`), effortCls: cls(key, `${host}.effort`),
          modelOff: st.scanning, effortOff: st.scanning || !o.modelKnown,
          modelLabel: `${name} 的 ${S.HOST_TEXT[host]} model`, effortLabel: `${name} 的 ${S.HOST_TEXT[host]} effort`,
        };
      }),
      bads: b, hasBad: b.length > 0,
    };
  });
  const hosts = base.chips.map(chip => ({...chip, ...catalogLine(chip.host, scan[chip.host])}));

  let strong = base.strong, quiet = base.quiet, hatch = false;
  if (!st.refused && !st.scanning) {
    if (probs.length) {
      const by = subProbs.length || flags.some(f => f.key.startsWith("sub:")) ? "MMW" : "start";
      strong = `有 ${probs.length} 处 ${by} 会拒绝，改好之前不能保存`;
      quiet = "带斜线的格子，下面一行写着哪里不对。";
      hatch = true;
    } else if (ch.length) {
      strong = `改了 ${ch.length} 处：${ch.map(c => c.text).join("；")}`;
      quiet = "保存后，下一个新起的 agent、下一次派出的子代理就用新值；已经在跑的不受影响。";
    } else if (!st.savedAt) {
      strong = "没有改动";
      quiet = "上面就是下一个新起的 agent、下一次派出的子代理会用的配置。";
    }
  }
  return {
    ...base, rows, subagents, hosts, strong, quiet, hatch,
    closeLabel: ch.length ? "取消" : "关闭",
    saveOff: !ch.length || probs.length > 0 || flags.length > 0 || !!st.scanning || !!st.refused,
    changed: ch.length > 0,
  };
}
