// Build pstack-atlas.html: merge the six survey JSONs (../reports/A*.json) and the principle nodes, assign each component its carrier, fill atlas.tpl.html.
const fs = require("fs"), path = require("path");
const DATA = path.join(__dirname, "..", "reports");
const files = fs.readdirSync(DATA).filter(f => /^A\d.*\.json$/.test(f)).sort();
const groups = Object.fromEntries(files.map(f => [f.slice(0, 2), JSON.parse(fs.readFileSync(path.join(DATA, f), "utf8"))]));

// ---------- merge components ----------
const comps = {};
for (const [g, d] of Object.entries(groups)) for (const c of d.components) {
  const size = JSON.stringify(c).length;
  if (!comps[c.id] || comps[c.id]._size < size) comps[c.id] = { ...c, _size: size, _group: g };
}
const PR = JSON.parse(fs.readFileSync(path.join(__dirname, "principles.json"), "utf8"));
for (const p of PR) if (!comps[p.id]) comps[p.id] = p;
for (const c of Object.values(comps)) delete c._size;

// ---------- merge edges ----------
const edges = [], seen = new Set(), missing = {};
function add(e, derived) {
  if (!comps[e.from] || !comps[e.to]) { const k = !comps[e.from] ? e.from : e.to; missing[k] = (missing[k] || 0) + 1; return; }
  if (e.from === e.to) return;
  const key = `${e.from}|${e.to}|${e.type}`;
  if (seen.has(key)) return;
  // a derived edge is skipped when any typed edge already joins the pair
  if (derived && edges.some(x => x.from === e.from && x.to === e.to)) return;
  seen.add(key);
  edges.push({ from: e.from, to: e.to, type: e.type, label: e.label || "", source: e.source || "", derived: !!derived });
}
for (const d of Object.values(groups)) for (const e of d.edges) add(e, false);
for (const c of Object.values(comps)) {
  for (const s of c.steps || []) for (const u of s.uses || []) {
    const t = u.startsWith("hu-") ? "human" : (u.startsWith("ar-") || u.startsWith("pf-")) ? "reads" : "invoke";
    add({ from: c.id, to: u, type: t, label: "", source: c.source }, true);
  }
  for (const p of c.principles || []) add({ from: c.id, to: p, type: "invoke", label: "", source: c.source }, true);
}

// ---------- carriers: what physical form each component takes (same 13 carriers as the MMW map) ----------
const P = "docs/research/code-landing-refs/pstack/";
const NEW = [
  // orch subcommands: the agent types these; orch.ts/store.ts is the code behind them
  ["cm-orch-init", "script", "command", "orch init", "建纸面账本", "在当前 agent 的 store 里建 orchestrate/<project-slug>/ 目录和初始文件。", P + "skills/poteto-mode/scripts/orch/orch.ts#init; playbooks/orchestrate.md#2. Install the runtime"],
  ["cm-orch-unit", "script", "command", "orch unit add / set / get / list / counts", "记工作单元", "登记每个工作单元（unit）的 track、brief 路径与状态；drain 时写入。", P + "skills/poteto-mode/scripts/orch/orch.ts#unit; playbooks/orchestrate.md#Queue and drain"],
  ["cm-orch-ledger", "script", "command", "orch ledger record / check / summary", "记验证结论", "按 PR 号加 head SHA 写一行验证结论；check 看当前 head 是否已验证。", P + "skills/poteto-mode/scripts/orch/orch.ts#ledger; playbooks/orchestrate.md#Verification"],
  ["cm-orch-inbox", "script", "command", "orch inbox push / drain / count", "收完成指针", "子 agent 完成时 push 一条指针；到批处理点 drain 一批再分类。", P + "skills/poteto-mode/scripts/orch/orch.ts#inbox; playbooks/orchestrate.md#Queue and drain"],
  ["cm-orch-gate", "script", "command", "orch gate park / list / resolve", "停放人工决定", "把需要人决定的问题连同选项和默认值停进 gates.md。", P + "skills/poteto-mode/scripts/orch/orch.ts#gate; playbooks/orchestrate.md#Store layout"],
  ["cm-orch-frontier", "script", "command", "orch frontier set / show", "读 Graphite 栈前沿", "从 gt 栈发现当前可合并前沿，写 frontier.json。", P + "skills/poteto-mode/scripts/orch/orch.ts#frontier; store.ts#graphiteFrontier"],
  ["cm-orch-status", "script", "command", "orch status", "出状态三行", "渲染 status.md，回复里只给三行：各状态计数、变化、待决 gate。", P + "skills/poteto-mode/scripts/orch/orch.ts#status; playbooks/orchestrate.md#Queue and drain"],
  ["cm-orch-standing", "script", "command", "orch standing show / add", "常设指令", "维护 standing orders（preferences.md）；每次派出与恢复都原样带上。", P + "skills/poteto-mode/scripts/orch/orch.ts#standing; playbooks/orchestrate.md#Store layout"],
  ["sc-log-sh", "script", "command", "log.sh", "追加决策记录", "给 decisions.tsv 追加一行格式正确的记录（时间、阶段、决定、理由、证据、结果）。", P + "skills/show-me-your-work/scripts/log.sh; SKILL.md#Use the helper"],
  // benny: Cursor Automations run a prompt that points at the pack's skills
  ["pm-benny-triage", "automation", "prompt", "triage automation prompt", "分诊自动化提示词", "setup-benny 让 Cursor 内置 /automate 据此写出线上自动化的提示词：读 triage-issue-reports 技能并处理这条 Slack 消息。", P + "automations/benny/templates/triage-automation-prompt.md"],
  ["pm-benny-reproduce", "automation", "prompt", "reproduce automation prompt", "复现自动化提示词", "同上，线上自动化读 reproduce-and-fix-issues 技能。", P + "automations/benny/templates/reproduce-automation-prompt.md"],
  ["cf-benny-config", "automation", "config", "configuration.yaml", "benny 配置", "Slack 频道、仓库、tracker、动作名；用户在目标仓库外或仓库内自建副本，不含密钥。", P + "automations/benny/templates/configuration.example.yaml; skills/setup-benny/SKILL.md#2. Adapt the configuration"],
  ["cf-plugin-json", "entry", "config", "plugin.json", "插件清单", "Cursor 插件清单：声明 skills/ 与 agents/ 两个目录，安装后这两处内容被宿主加载。", P + ".cursor-plugin/plugin.json"],
  // outside pstack
  ["ex-deslop", "platform", "external", "/deslop", "清代码冗余（cursor-team-kit）", "cursor-team-kit 插件里的命令与技能，不在 pstack 里；开 PR 前清掉代码里的叙述式注释、无依据的防御和死代码。", P + "README.md#233; playbooks/opening-a-pr.md#PRs"],
  ["ex-automate", "platform", "external", "/automate", "Cursor 内置自动化技能", "Cursor 内置技能；setup-benny 用它把提示词模板写成两条线上自动化。", P + "automations/benny/skills/setup-benny/SKILL.md#19"],
  ["ex-origin", "platform", "external", "origin CLI", "Origin 代码托管", "Cursor 的代码托管；babysit 与 shipping 先看 origin 是否可用，不可用才走 gh。", P + "skills/poteto-mode/playbooks/shipping.md#1; babysit.md#6"],
  // events that wake the coordinator
  ["ev-completion", "platform", "event", "子 agent 完成通知", "完成通知", "Task tool 或云端 agent 完成时宿主发来的通知；协调者收到后只做 orch inbox push，不当场审。", P + "skills/poteto-mode/playbooks/orchestrate.md#Queue and drain"],
  ["ev-watch-wake", "platform", "event", "watcher 唤醒", "PR 状态唤醒", "watch-pr 的输出在 /loop 动态模式下唤醒 agent；不另写 sleep 循环。", P + "skills/poteto-mode/playbooks/babysit.md#6"],
];
for (const [id, kind, carrier, name, label, purpose, source] of NEW) comps[id] = { id, kind, carrier, name, label, purpose, source, _new: true };
comps["sc-orch"].name = "orch.ts / store.ts"; comps["sc-orch"].label = "orch 子命令背后的实现";
const CAR = {
  "pb-": "reference", "pr-": "skill", "sk-": "skill", "hu-": "human", "au-": "skill",
};
const CAR_ID = {
  "sk-control-cli": "external", "sk-control-ui": "external",
  "ag-poteto-agent": "prompt", "ag-comment-sicko": "prompt", "ag-general-purpose": "external",
  "ar-todo": "external", "ar-models-rule": "config", "ar-pr": "tracker", "ar-stack": "tracker", "ar-brief": "prompt", "ar-goal": "command",
  "ar-resume-note": "artifact", "ar-orch-store": "artifact", "ar-ledger": "artifact", "ar-gates": "artifact", "ar-inbox": "artifact",
  "ar-plan-doc": "artifact", "ar-children-tsv": "artifact", "ar-decisions-tsv": "artifact",
  "pf-loop": "command", "pf-task-tool": "external", "pf-cursor-cloud": "external", "pf-github": "external", "pf-bugbot": "external",
  "pf-transcripts": "artifact", "pf-automations": "external", "pf-slack": "external", "pf-graphite": "external",
  "sc-watch-pr": "command", "sc-worktree-audit": "command", "sc-check-plan": "command", "sc-orch": "script", "sc-bootstrap": "script",
};
const CAR_NOTE = {
  "sk-control-cli": "在 cursor-team-kit 插件里，不属于 pstack；pstack 只点名调用。", "sk-control-ui": "在 cursor-team-kit 插件里，不属于 pstack；pstack 只点名调用。",
  "ag-poteto-agent": "agents/poteto-agent.md：子 agent 的定义文件，内容是给它的提示词。", "ag-comment-sicko": "agents/comment-sicko.md：子 agent 的定义文件，内容是给它的提示词。",
  "ag-general-purpose": "Cursor 内置的子 agent 类型，不是 pstack 的文件。", "ar-todo": "Cursor agent 内置的待办清单工具。",
  "ar-models-rule": "setup-pstack 写到用户的 .cursor/rules/ 下的规则文件。", "ar-brief": "协调者写给 worker 的开工提示，按九段模板填。",
  "ar-goal": "Cursor 内置命令。", "pf-loop": "Cursor 内置命令。", "pf-transcripts": "Cursor 写在本机的会话记录文件。",
  "sc-orch": "由 orch 各子命令调用。", "sc-bootstrap": "orch 与 watch-pr 启动时先调用它装依赖。",
  "sk-typescript-best-practices": "指南说它碰到 .ts 文件自己加载，但 frontmatter 设了 disable-model-invocation: true，两处矛盾。",
  "au-benny-triage": "automations/benny/skills/triage-issue-reports/SKILL.md。", "au-benny-reproduce": "automations/benny/skills/reproduce-and-fix-issues/SKILL.md。",
};
for (const c of Object.values(comps)) {
  if (!c.carrier) c.carrier = CAR_ID[c.id] || CAR[c.id.slice(0, 3)] || "external";
  if (CAR_NOTE[c.id]) c.carrier_note = CAR_NOTE[c.id];
}
// retarget orch edges to the subcommand that actually does it
const RET = { "ar-orch-store": "cm-orch-init", "ar-ledger": "cm-orch-ledger", "ar-inbox": "cm-orch-inbox", "ar-gates": "cm-orch-gate", "pf-graphite": "cm-orch-frontier" };
for (let i = edges.length - 1; i >= 0; i--) {
  const e = edges[i];
  if (e.from === "sc-orch" && RET[e.to]) { e.from = RET[e.to]; }
  if (e.to === "sc-orch" && RET[e.from] && e.derived) edges.splice(i, 1);
  if (e.from === "pb-orchestrate" && e.to === "sc-orch") edges.splice(i, 1);
}
const O = P + "skills/poteto-mode/playbooks/orchestrate.md";
const NE = [
  ...["init", "unit", "ledger", "inbox", "gate", "frontier", "status", "standing"].map(k => ["pb-orchestrate", "cm-orch-" + k, "invoke", "orch " + k, O]),
  ...["init", "unit", "ledger", "inbox", "gate", "frontier", "status", "standing"].map(k => ["cm-orch-" + k, "sc-orch", "invoke", "", P + "skills/poteto-mode/scripts/orch/orch.ts#createProgram"]),
  ["cm-orch-unit", "ar-orch-store", "writes", "units", P + "skills/poteto-mode/scripts/orch/store.ts#units"],
  ["cm-orch-status", "ar-orch-store", "writes", "status.md", P + "skills/poteto-mode/scripts/orch/orch.ts#status"],
  ["cm-orch-standing", "ar-orch-store", "writes", "preferences.md", O + "#Store layout"],
  ["cm-orch-gate", "hu-preference", "human", "等人决定", O + "#Store layout"],
  ["pf-task-tool", "ev-completion", "writes", "完成", O + "#Queue and drain"],
  ["pf-cursor-cloud", "ev-completion", "writes", "完成", O + "#Queue and drain"],
  ["ev-completion", "cm-orch-inbox", "wakes", "push 指针", O + "#Queue and drain"],
  ["sc-watch-pr", "ev-watch-wake", "writes", "输出", P + "skills/poteto-mode/playbooks/babysit.md#6"],
  ["ev-watch-wake", "pf-loop", "wakes", "唤醒", P + "skills/poteto-mode/playbooks/babysit.md#6"],
  ["sc-watch-pr", "sc-bootstrap", "invoke", "装依赖", P + "skills/poteto-mode/scripts/watch-pr/watch-pr#ensureDependenciesInstalled"],
  ["sk-show-me-your-work", "sc-log-sh", "invoke", "追加一行", P + "skills/show-me-your-work/SKILL.md#Use the helper"],
  ["sc-log-sh", "ar-decisions-tsv", "writes", "", P + "skills/show-me-your-work/scripts/log.sh"],
  ["pb-opening-a-pr", "ex-deslop", "invoke", "提交前清冗余", P + "skills/poteto-mode/playbooks/opening-a-pr.md#PRs"],
  ["pb-multi-phase-plan", "ex-deslop", "invoke", "每次提交前", P + "skills/poteto-mode/playbooks/multi-phase-plan.md#60"],
  ["pb-babysit", "ex-origin", "reads", "先试 origin", P + "skills/poteto-mode/playbooks/babysit.md#6"],
  ["pb-shipping", "ex-origin", "reads", "先试 origin", P + "skills/poteto-mode/playbooks/shipping.md#1"],
  ["sk-setup-benny", "cf-benny-config", "writes", "改配置", P + "automations/benny/skills/setup-benny/SKILL.md#2. Adapt the configuration"],
  ["sk-setup-benny", "ex-automate", "invoke", "建线上自动化", P + "automations/benny/skills/setup-benny/SKILL.md#19"],
  ["ex-automate", "pm-benny-triage", "reads", "按模板写", P + "automations/benny/templates/triage-automation-prompt.md"],
  ["ex-automate", "pm-benny-reproduce", "reads", "按模板写", P + "automations/benny/templates/reproduce-automation-prompt.md"],
  ["pf-automations", "pm-benny-triage", "invoke", "触发时运行", P + "automations/benny/templates/triage-automation-prompt.md"],
  ["pf-automations", "pm-benny-reproduce", "invoke", "触发时运行", P + "automations/benny/templates/reproduce-automation-prompt.md"],
  ["pm-benny-triage", "au-benny-triage", "invoke", "读技能", P + "automations/benny/templates/triage-automation-prompt.md#5"],
  ["pm-benny-reproduce", "au-benny-reproduce", "invoke", "读技能", P + "automations/benny/templates/reproduce-automation-prompt.md"],
  ["pm-benny-triage", "cf-benny-config", "reads", "", P + "automations/benny/templates/triage-automation-prompt.md#Configuration source"],
  ["pm-benny-reproduce", "cf-benny-config", "reads", "", P + "automations/benny/templates/reproduce-automation-prompt.md"],
  ["cf-plugin-json", "sk-poteto-mode", "reads", "声明 skills/", P + ".cursor-plugin/plugin.json#skills"],
  ["cf-plugin-json", "ag-poteto-agent", "reads", "声明 agents/", P + ".cursor-plugin/plugin.json#agents"],
];
for (const [from, to, type, label, source] of NE) add({ from, to, type, label, source }, false);
// skills whose frontmatter sets disable-model-invocation: true: the model never picks them from their description;
// a person types /name, or poteto-mode calls them by name. The benny pack is not registered as slash skills (README.md#255).
const ROOT = path.join(__dirname, "..", "..", "code-landing-refs", "pstack");
const skillFile = c => { const m = (c.source || "").match(/((?:automations\/benny\/)?skills\/[^/ #]+)\/SKILL\.md/); return m && path.join(ROOT, m[1], "SKILL.md"); };
comps["hu-direct"] = { id: "hu-direct", kind: "human", carrier: "human", name: "人敲 /技能名", label: "别处不调用、只由人敲的技能", purpose: "pstack 的技能几乎都设了 disable-model-invocation: true：模型不会凭描述自己选用，只能由人敲 /名字，或由 poteto-mode 按名字调用。这里连出的是除了人敲以外没有任何组件调用的技能。", source: P + "docs/guide/README.md; skills/*/SKILL.md#frontmatter", _new: true };
const inbound = new Set(edges.map(e => e.to));
for (const c of Object.values(comps)) {
  if (c.carrier !== "skill" || c.id.startsWith("au-")) continue;
  const f = skillFile(c); if (!f || !fs.existsSync(f)) continue;
  const fm = fs.readFileSync(f, "utf8").split("---")[1] || "";
  if (!/disable-model-invocation:\s*true/.test(fm)) continue;
  c.manual = true;
  if (!inbound.has(c.id)) add({ from: "hu-direct", to: c.id, type: "human", label: "/" + c.name, source: path.relative(path.join(__dirname, "..", "..", "..", ".."), f) + "#frontmatter" }, false);
}
// the two pf-automations -> skill edges now run through the prompt
for (let i = edges.length - 1; i >= 0; i--) if (edges[i].from === "pf-automations" && edges[i].to.startsWith("au-benny")) edges.splice(i, 1);
edges.forEach((e, i) => e.id = "e" + i);

(async () => {
  const out = { comps, edges,
    compare: Object.fromEntries(Object.entries(groups).map(([g, d]) => [g, d.compare])),
    notes: Object.fromEntries(Object.entries(groups).map(([g, d]) => [g, d.notes || []])) };
  out.notes["载体"] = [
    "typescript-best-practices：docs/guide/05-build-and-clean.md 说它在 agent 碰到 .ts / .tsx 文件时自己加载，但它的 SKILL.md frontmatter 设了 disable-model-invocation: true，这会让模型不自己选用它。两处原文互相矛盾；网里按 frontmatter 画成只由人敲。",
    "control-cli、control-ui、/deslop 在 cursor-team-kit 插件里（README.md 第 233–234 行），不是 pstack 的组件；网里画成外部工具，只保留 pstack 调用它们的连线。",
    "benny 的两个技能虽然也设了 disable-model-invocation: true，但 README.md 第 255 行说 benny 的文件不注册为斜杠技能；它们由 Cursor Automations 按提示词模板触发，所以不标「/斜杠」。",
    "orch 是一个命令行程序：agent 敲 orch 的 8 组子命令，子命令背后是 orch.ts / store.ts。网里把 8 组子命令画成命令，把 orch.ts / store.ts 画成脚本。",
  ];
  const tpl = fs.readFileSync(path.join(__dirname, "atlas.tpl.html"), "utf8");
  fs.writeFileSync(path.join(__dirname, "..", "pstack-atlas.html"), tpl.replace("__DATA__", () => JSON.stringify(out).replace(/<\//g, "<\\/")));
  console.log("components", Object.keys(comps).length, "edges", edges.length, "bytes", JSON.stringify(out).length, "missing", missing);
})();
