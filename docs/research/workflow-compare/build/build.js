// Merge the six survey JSONs (../reports/A*.json) and the principle nodes into net-data.json for atlas.tpl.html.
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
edges.forEach((e, i) => e.id = "e" + i);

(async () => {
  const out = { comps, edges,
    compare: Object.fromEntries(Object.entries(groups).map(([g, d]) => [g, d.compare])),
    notes: Object.fromEntries(Object.entries(groups).map(([g, d]) => [g, d.notes || []])) };
  fs.writeFileSync(path.join(__dirname, "net-data.json"), JSON.stringify(out));
  console.log("components", Object.keys(comps).length, "edges", edges.length, "bytes", JSON.stringify(out).length, "missing", missing);
})();
