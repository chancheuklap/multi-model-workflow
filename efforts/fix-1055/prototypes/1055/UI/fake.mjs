// API fake for #1055: the fields GET /api/settings does not answer yet, added to the real answer.
// Everything else (models.json, the scan, PUT, rescan) is the board's real local back end; a PUT
// that carries `subagents` is already validated and written by models.py.
//
// Draft interface contract, added to the GET answer:
//   subagent_options: {
//     rows: ["review-axis", "reader", "default"],            // roles.json `subagents`, in order
//     claude: {models: [...], efforts: [...]},               // models.py's fixed claude choices
//     codex: {models: [{model, efforts}], inheritEfforts},   // the stored codex catalog, by id
//     labels: {<host>: {<id>: <name>}},  // the name the agent rows show for that model: models.py's
//                                       // _slug_everyday(id), plus " · <note>" when the catalog has one
//   }
//   subagents: {<row>: {claude: {model, effort}, codex: {model, effort}}}  // "inherit" when unset
//   scan.hosts.<host>: {read_at, failure?: {kind, detail, at}}            // read_at filled here when empty
//   stale: [{cell, host, stored, offered: [...]}]  // a saved model the host's catalog no longer lists
//
// State addresses, for states the local back end cannot be driven into (`?state=` on the page URL):
//   read-failed   codex's last catalog read failed (the stored catalog is still used)
//   stale-model   reviewer's saved claude model and review-axis's saved codex model are gone from the catalogs

const ROWS = ["review-axis", "reader", "default"];
const CLAUDE = {
  models: ["inherit", "sonnet", "opus", "haiku", "fable"],
  efforts: ["inherit", "low", "medium", "high", "xhigh", "max"],
};
const CODEX = [
  {model: "gpt-6.1-sol", efforts: ["low", "medium", "high", "xhigh", "max", "ultra"]},
  {model: "gpt-6-astra", efforts: ["low", "medium", "high", "xhigh", "max", "ultra"]},
  {model: "gpt-6-sol", efforts: ["low", "medium", "high", "xhigh", "max", "ultra"]},
  {model: "gpt-6-luna", efforts: ["low", "medium", "high", "xhigh", "max"]},
  {model: "gpt-5.6-sol", efforts: ["low", "medium", "high", "xhigh"]},
  {model: "gpt-5.6-terra", efforts: ["low", "medium", "high", "xhigh"]},
  {model: "gpt-5.6-luna", efforts: ["low", "medium", "high"]},
];
const READ_AT = {claude: "2026-10-17T03:18:59Z", codex: "2026-10-17T03:19:02Z"};

function state() {
  return typeof location === "undefined" ? "" : new URLSearchParams(location.search).get("state") || "";
}

function inheritEfforts(models) {
  const sets = models.map(m => new Set(m.efforts));
  return ["inherit", ...models[0].efforts.filter(e => sets.every(s => s.has(e)))];
}

// models.py _slug_everyday, which turns a catalog id into the name the agent rows store and show.
function slug(id) {
  let text = id.trim().replace(/^claude-/i, "").replace(/(?<=\D)(\d)-(\d)(?=\D|$)/g, "$1.$2");
  if (text.includes("/")) text = text.split("/").slice(1).join("/");
  return text.replace(/[-_]/g, " ").replace(/\s+/g, " ").trim().toLowerCase();
}

function labels(hosts, ids) {
  return Object.fromEntries(Object.entries(ids).map(([host, list]) => [host, Object.fromEntries(list.map(id => {
    const offered = (hosts?.[host]?.offered || []).find(o => o.model === slug(id));
    const name = offered?.model || slug(id);
    return [id, offered?.note ? `${name} · ${offered.note}` : name];
  }))]));
}

export function withFake(payload) {
  const out = structuredClone(payload);
  const codexModels = [{model: "inherit", efforts: inheritEfforts(CODEX)}, ...CODEX];
  // A field the answer already carries (a test's browser.route, or the back end once it has it) is kept.
  out.subagent_options = out.subagent_options || {
    rows: ROWS,
    claude: CLAUDE,
    codex: {models: codexModels, inheritEfforts: inheritEfforts(CODEX)},
    labels: labels(out.scan?.hosts, {claude: CLAUDE.models.slice(1),
      codex: [...CODEX.map(m => m.model), "gpt-5.5-sol"]}),
  };
  const saved = out.subagents || {};
  out.subagents = Object.fromEntries(ROWS.map(row => [row, {
    claude: {model: "inherit", effort: "inherit", ...(saved[row]?.claude || {})},
    codex: {model: "inherit", effort: "inherit", ...(saved[row]?.codex || {})},
  }]));
  for (const [host, entry] of Object.entries(out.scan?.hosts || {})) {
    if (!entry.read_at) entry.read_at = READ_AT[host] || "";
  }
  out.stale = out.stale || [];
  if (state() === "read-failed" && out.scan?.hosts?.codex) {
    out.scan.hosts.codex.failure = {kind: "timeout", detail: "codex app-server 30 秒没有回答", at: "2026-10-17T09:05:11Z"};
  }
  if (state() === "stale-model") {
    out.rows.reviewer = {...out.rows.reviewer, host: "claude", model: "opus[old]"};
    out.subagents["review-axis"].codex = {model: "gpt-5.5-sol", effort: "high"};
    out.stale = [
      {cell: "rows.reviewer.model", host: "claude", stored: "opus[old]", offered: CLAUDE.models.slice(1)},
      {cell: "subagents.review-axis.codex.model", host: "codex", stored: "gpt-5.5-sol",
        offered: CODEX.map(m => m.model)},
    ];
  }
  return out;
}
