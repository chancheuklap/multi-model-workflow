export const CATALOG = {
  store: "~/.mmw/models.json",
  agents: ["junior-worker", "senior-worker", "reviewer", "verifier", "advisor"],
  hosts: ["cursor", "grok", "claude", "codex", "pi"],
  binaries: {cursor: "cursor-agent", grok: "grok", claude: "claude", codex: "codex", pi: "pi"},
  launch: {
    cursor: {cli: true, paseo: true},
    grok: {cli: true, paseo: true},
    claude: {cli: true, paseo: true},
    codex: {cli: true, paseo: true},
    pi: {cli: false, paseo: true},
  },
  runners: ["herdr", "orca", "paseo"],
};

export const LocalConfig = {
  CELLS: ["host", "model", "effort"],
  ROLE_WHAT: {
    "junior-worker": "贴 junior-worker label 的票",
    "senior-worker": "贴 senior-worker label 的票",
    reviewer: "评审每张票的改动",
    verifier: "复验每张票的判据",
    advisor: "被问到时给第二意见",
  },
  source: d => (d.runner === "paseo" ? "paseo" : "cli"),
  needsRescan: (from, to) => LocalConfig.source(from) !== LocalConfig.source(to),
  hostScan: (scan, host) => scan[host] || {state: "missing", offered: []},
  hostState(scan, d, host, catalog = CATALOG) {
    const launch = catalog.launch[host] || {};
    return launch[LocalConfig.source(d)] ? LocalConfig.hostScan(scan, host).state : "unlaunchable";
  },
  offeredBy: (scan, host) => LocalConfig.hostScan(scan, host).offered,
  effortsOf: (scan, host, model) =>
    (LocalConfig.offeredBy(scan, host).find(o => o.model === model) || {efforts: []}).efforts,
  stateWord: (state, d) => ({
    missing: "本机没装", silent: "没有回答", down: "Paseo 没开",
    unlaunchable: d && LocalConfig.source(d) === "paseo" ? "Paseo 起不了" : "orca、herdr 起不了",
  }[state] || state),
  hostWhy: (state, host, d, catalog = CATALOG) => ({
    missing: `这台机器上没装 ${host} 的 CLI（${catalog.binaries[host]}），换一个这台机器有的`,
    silent: `${host} 的 CLI 在扫描时没有回答，换一个这台机器有的`,
    down: `Paseo 服务没开，问不到 ${host} 的 model；先开 Paseo，或者把 runner 换回 orca 或 herdr`,
    unlaunchable: LocalConfig.source(d) === "paseo"
      ? `Paseo 起不了 ${host}：hosts.json 没给它 paseo 块；换一个 host`
      : `orca 和 herdr 起不了 ${host}：hosts.json 没给它命令行启动块（cli）；换一个 host，或者把 runner 换成 paseo`,
  }[state]),

  problems(scan, d, catalog = CATALOG) {
    const L = LocalConfig, out = [];
    if (d.runner !== "auto" && !catalog.runners.includes(d.runner)) {
      out.push({key: "runner", cell: "runner", text: `${d.runner} 没有适配器，start 起不了会话`});
    }
    for (const a of catalog.agents) {
      const r = d.rows[a];
      if (!catalog.hosts.includes(r.host)) {
        out.push({key: a, cell: "host", text: `${r.host} 不是 MMW 认识的 host`});
        continue;
      }
      const hs = L.hostScan(scan, r.host), hostState = L.hostState(scan, d, r.host, catalog);
      if (hostState !== "ok") {
        out.push({key: a, cell: "host", text: L.hostWhy(hostState, r.host, d, catalog)});
        continue;
      }
      if (!r.model) {
        out.push({key: a, cell: "model", text: "还没选 model"});
        continue;
      }
      if (!hs.offered.some(o => o.model === r.model)) {
        out.push({key: a, cell: "model", text: `这台机器的 ${r.host} 已经不提供 ${r.model}`});
        continue;
      }
      if (!r.effort) {
        out.push({key: a, cell: "effort", text: "还没选 effort"});
        continue;
      }
      if (!L.effortsOf(scan, r.host, r.model).includes(r.effort)) {
        out.push({key: a, cell: "effort", text: `${r.model} 在 ${r.host} 上没有 ${r.effort} 这一档`});
      }
    }
    return out;
  },
  changes(d, s, catalog = CATALOG) {
    const out = d.runner !== s.runner ? [{key: "runner", text: "runner", cells: ["runner"]}] : [];
    for (const a of catalog.agents) {
      const cells = LocalConfig.CELLS.filter(c => d.rows[a][c] !== s.rows[a][c]);
      if (cells.length) out.push({key: a, text: `${a} 的 ${cells.join("、")}`, cells});
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
    const opts = [
      ...(d.runner !== "auto" && !catalog.runners.includes(d.runner)
        ? [{value: d.runner, text: `${d.runner} · 没有适配器`}] : []),
      ...catalog.runners.map(r => ({value: r, text: r})),
      {value: "auto", text: "按所在环境判断"},
    ];
    return opts.map(o => ({...o, selected: o.value === d.runner, disabled: !!o.disabled}));
  },
  rowOptions(scan, d, a, catalog = CATALOG) {
    const L = LocalConfig, r = d.rows[a], hs = L.hostScan(scan, r.host);
    const hostOk = L.hostState(scan, d, r.host, catalog) === "ok";
    const modelKnown = hostOk && hs.offered.some(o => o.model === r.model);
    const mark = (opts, value) => opts.map(o => ({...o, selected: o.value === value, disabled: !!o.disabled}));
    const host = [
      ...(catalog.hosts.includes(r.host) ? [] : [{value: r.host, text: `${r.host} · MMW 不认识`}]),
      ...catalog.hosts.map(h => {
        const hostState = L.hostState(scan, d, h, catalog);
        return {
          value: h,
          text: hostState === "ok" ? h : `${h} · ${L.stateWord(hostState, d)}`,
          disabled: hostState !== "ok" && h !== r.host,
        };
      }),
    ];
    const offeredEfforts = L.effortsOf(scan, r.host, r.model);
    const effortKnown = modelKnown && offeredEfforts.includes(r.effort);
    const model = !hostOk ? [{value: r.model, text: r.model || "—"}] : [
      ...(!r.model ? [{value: "", text: "选一个 model", disabled: true}]
        : modelKnown ? [] : [{value: r.model, text: `${r.model} · 本机已经没有`}]),
      ...hs.offered.map(o => ({value: o.model, text: o.model})),
    ];
    const effort = !modelKnown ? [{value: r.effort, text: r.effort || "—"}] : [
      ...(!r.effort ? [{value: "", text: "选一档", disabled: true}]
        : effortKnown ? [] : [{value: r.effort, text: `${r.effort} · 本机已经没有`}]),
      ...offeredEfforts.map(e => ({value: e, text: e === "—" ? "—（不设）" : e})),
    ];
    return {host: mark(host, r.host), model: mark(model, r.model), effort: mark(effort, r.effort), hostOk, modelKnown};
  },
  hostChips(scan, d, catalog = CATALOG) {
    return catalog.hosts.map(h => {
      const offered = LocalConfig.hostScan(scan, h);
      const hostState = LocalConfig.hostState(scan, d, h, catalog);
      return {
        host: h, state: hostState,
        what: hostState === "ok" ? `${offered.offered.length} 个 model` : LocalConfig.stateWord(hostState, d),
      };
    });
  },
};

const hhmm = value => new Date(value).toLocaleTimeString("en-GB", {
  hour: "2-digit", minute: "2-digit", hour12: false,
});

export function catalogFromPayload(payload) {
  const hosts = [];
  const launch = {};
  const binaries = {};
  for (const item of payload.hosts) {
    hosts.push(item.name);
    launch[item.name] = {cli: !!item.cli, paseo: !!item.paseo};
    if (item.binary) binaries[item.name] = item.binary;
  }
  return {
    store: CATALOG.store,
    agents: CATALOG.agents,
    hosts,
    binaries,
    launch,
    runners: payload.runners.filter(name => name !== "auto"),
  };
}

export function settingsView(sheet, scan, catalog) {
  const L = LocalConfig, draft = sheet.draft;
  const probs = [
    ...(sheet.scanning ? [] : L.problems(scan, draft, catalog)),
    ...(sheet.serverFlags || []),
  ];
  const ch = L.changes(draft, sheet.saved, catalog);
  const cls = (key, cell) => (probs.some(p => p.key === key && p.cell === cell) ? "sel bad"
    : ch.some(c => c.key === key && c.cells.includes(cell)) ? "sel changed" : "sel");
  const bads = key => probs.filter(p => p.key === key).map(p => ({text: p.text}));
  const rows = catalog.agents.map(a => {
    const o = L.rowOptions(scan, draft, a, catalog), r = draft.rows[a], b = bads(a);
    return {
      agent: a, what: L.ROLE_WHAT[a], host: r.host, model: r.model, effort: r.effort,
      hostCls: cls(a, "host"), modelCls: cls(a, "model"), effortCls: cls(a, "effort"),
      hostOpts: o.host, modelOpts: o.model, effortOpts: o.effort,
      hostOff: sheet.scanning, modelOff: sheet.scanning || !o.hostOk, effortOff: sheet.scanning || !o.modelKnown,
      hostLabel: `${a} 的 host`, modelLabel: `${a} 的 model`, effortLabel: `${a} 的 effort`,
      bads: b, hasBad: b.length > 0,
    };
  });
  const when = "保存后，下一个新起的 agent 就用新值；已经在跑的不受影响。";
  let strong, quiet, hatch = false;
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
    store: catalog.store, rows,
    runner: draft.runner, runnerCls: cls("runner", "runner"), runnerOpts: L.runnerOptions(draft, catalog),
    runnerOff: sheet.scanning, runnerBads: rb, runnerHasBad: rb.length > 0,
    chips: L.hostChips(scan, draft, catalog).map(c => ({
      cls: "hs " + (sheet.scanning ? "" : c.state), host: c.host, what: sheet.scanning ? "…" : c.what,
    })),
    scanning: sheet.scanning,
    scanningText: L.source(draft) === "paseo" ? "正在向 Paseo 要每个 host 的 model…" : "正在问每个 host 的 CLI 有哪些 model…",
    scannedText: `${sheet.scannedAt ? hhmm(sheet.scannedAt) : ""} 问${sheet.scanSource === "paseo" ? " Paseo" : "各 host 的 CLI"} ·`,
    refused: !!sheet.refused,
    refusedText: `这一页打开之后，本机配置在 ${at ? hhmm(at) : ""} 被别处改过（一个 agent 从命令行改的）。重新读取会换成现在保存着的内容，你刚才改的 ${sheet.refused} 处要再改一次。`,
    strong, quiet, hatch,
    closeLabel: ch.length ? "取消" : "关闭",
    saveOff: !ch.length || probs.length > 0 || !!sheet.scanning || !!sheet.refused,
    changed: ch.length > 0,
  };
}
