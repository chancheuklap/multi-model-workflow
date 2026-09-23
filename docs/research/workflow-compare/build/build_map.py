"""Merge C1/C2/C3/C5 flow data, add installed skills missing from the flow, attach C4a/C4b references to nodes."""
import json, re, collections, sys, os

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")
def load(n): return json.load(open(os.path.join(HERE, n)))

FLOW = ["C1-front-ui.json", "C2-night.json", "C3-ticket-ui-down.json", "C5-toolbox.json"]
PHASES = {
 "C1": ["路由", "探索与决定", "界面设计", "界面合同", "写 spec", "拆票", "界面票", "产品答案（target.json）", "发布与检查"],
 "C2a": ["开夜", "派发", "启动会话"],
 "C3": ["认领", "读入", "实现", "界面实现", "自验", "界面判据", "评审", "修复", "关票", "例外与子票"],
 "C2b": ["唤醒与活性", "落地", "夜末收尾", "复盘", "早晨与 finish", "暂停与恢复"],
 "C5": ["看板", "Memory", "模型与 runner", "辅助技能", "提示词与 hooks", "安装与发布"],
 "X": ["其他已安装技能"],
}
STAGE = {"C1": "白天：从想法到一批 ticket", "C2a": "夜里：开夜与派发", "C3": "夜里：一张票的循环", "C2b": "夜里：唤醒、落地与收尾", "C5": "支撑层：工具箱与运行环境", "X": "已安装但不在主流程上的技能"}
order = [(g, p) for g, ps in PHASES.items() for p in ps]

nodes, edges, own, notes = {}, [], {}, {}
for f in FLOW:
    d = load(f); g = f[:2]
    notes[g] = d.get("notes", [])
    for n in d["nodes"]:
        if n["id"] in nodes: continue
        n = dict(n); n["_g"] = g
        nodes[n["id"]] = n
    for e in d["edges"]:
        edges.append({k: e.get(k, "") for k in ("from", "to", "type", "label", "source")})

EXTRA = [
 ("upstream/skills/engineering/codebase-design", "codebase-design", "深模块设计词汇", "设计或改进模块接口、找加深机会、决定 seam 位置时使用；其他技能需要深模块词汇时也会读它。", False),
 ("upstream/skills/engineering/improve-codebase-architecture", "improve-codebase-architecture", "扫描架构改进机会", "扫描代码库找加深机会，做成 HTML 报告，再就选中的一项访谈。", True),
 ("upstream/skills/engineering/setup-matt-pocock-skills", "setup-matt-pocock-skills", "配置上游技能", "为仓库配置 issue tracker、triage 标签词汇和领域文档布局；首次使用上游工程技能前运行一次。", True),
 ("upstream/skills/engineering/wizard", "wizard", "生成人工步骤向导", "生成交互式 bash 向导，带人走完只有人能做的步骤（凭据、第三方后台、一次性迁移）。", False),
 ("upstream/skills/productivity/grill-me", "grill-me", "追问计划", "对一个计划或设计做连续追问。", True),
 ("upstream/skills/productivity/teach", "teach", "在工作区里教学", "在当前工作区教用户一个新技能或概念。", True),
 ("upstream/skills/productivity/wait-what", "wait-what", "重新讲一遍", "上一条消息没被理解时，换一种讲法重讲。", True),
 ("upstream-diagram-design/skills/diagram-design", "diagram-design", "画图表", "生成各类架构图、流程图、图表的独立 HTML / SVG。", False),
]
for path, name, label, what, manual in EXTRA:
    nid = f"skill:{path}/SKILL.md"
    if nid in nodes: continue
    nodes[nid] = {"id": nid, "carrier": "skill", "name": name, "label": label, "phase": "其他已安装技能", "actor": "main agent",
                  "what": what + ("（frontmatter 设 disable-model-invocation: true：只能由人手动调用）" if manual else ""),
                  "inputs": [], "outputs": [], "location": f"mmw-v2/{path}/SKILL.md#frontmatter", "ui": False, "_g": "X", "manual": manual}

# phase key per node
for n in nodes.values():
    g = n["_g"]
    if g == "C2": g = "C2a" if n["phase"] in PHASES["C2a"] else "C2b"
    n["_band"] = next((i for i, (gg, p) in enumerate(order) if gg == g and p == n["phase"]), None)
    if n["_band"] is None:
        n["_band"] = next((i for i, (gg, p) in enumerate(order) if p == n["phase"]), len(order) - 1)
bad = [n["id"] for n in nodes.values() if n["_band"] is None]

# manual (user-invoked) upstream skills already in the flow
for n in nodes.values():
    if n["carrier"] == "skill" and "manual" not in n:
        p = re.sub(r"^mmw-v2/", "", n.get("location", "").split("#")[0])
        fp = os.path.join("/Users/cheuklapchan/multi-model-workflow/mmw-v2", p)
        n["manual"] = bool(os.path.isfile(fp) and "disable-model-invocation: true" in open(fp, encoding="utf-8").read().split("---")[1]) if os.path.isfile(fp) and open(fp, encoding="utf-8").read().startswith("---") else False

# ---------- references ----------
def npath(x):
    x = re.sub(r"^git [0-9a-f]+:", "", x or "")
    x = re.sub(r"^[0-9a-f]{7,40}:", "", x)
    p = x.split("#")[0]
    p = re.sub(r":\d+$", "", p)
    return re.sub(r"^mmw-v2/", "", p).strip()
def nhead(x):
    h = (x or "").split("#", 1)[1] if "#" in (x or "") else ""
    return re.sub(r":\d+$", "", h).strip().lower()

by_path = collections.defaultdict(list)
for n in nodes.values():
    for src in (n.get("location", ""), n["id"].split(":", 1)[1] if ":" in n["id"] else ""):
        p = npath(src)
        if p: by_path[p].append(n["id"])
def dir_of(p):
    m = re.match(r"(.*?/skills/[^/]+/[^/]+|skills/[^/]+|upstream-unlazy|upstream-diagram-design/skills/[^/]+)(/|$)", p)
    return m.group(1) if m else None
by_dir = collections.defaultdict(list)
for p, ids in by_path.items():
    d = dir_of(p)
    if d: by_dir[d] += ids

OVERRIDE = {
 "upstream-diagram-design": "skill:upstream-diagram-design/skills/diagram-design/SKILL.md",
 "docs/adr/0009-night-orchestration-on-paseo.md": "script:skills/dispatch/scripts/runners/paseo.sh#start",
 "docs/adr/0006-skills-install-to-neutral-dir.md": "command:install.sh#install",
 "prompt/hosts/codex.md": "artifact:prompt/hosts/<host>.md",
 "docs/specs/task-board/screen-contract.yaml": "process:board supervisor",
}
STOP = {"the","a","an","of","to","and","in","on","for","is","it","md","py","sh","skill","skills","mmw","v2","usr","bin","env","python3","bash","node"}
def TOK(x): return {t for t in re.split(r"[^a-z0-9]+", (x or "").lower().replace("_", " ")) if len(t) > 2 and t not in STOP}
EXC = ""
_FN = {}
def func_at(p, line):
    fp = os.path.join("/Users/cheuklapchan/multi-model-workflow/mmw-v2", p)
    if not os.path.isfile(fp): return None
    if fp not in _FN:
        defs = []
        for i, l in enumerate(open(fp, encoding="utf-8", errors="replace"), 1):
            m = re.match(r"\s*(?:def|async def|class)\s+([A-Za-z_][A-Za-z0-9_]*)|^([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{|^\s*(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)", l)
            if m: defs.append((i, next(g for g in m.groups() if g)))
        _FN[fp] = defs
    return [d[1] for d in reversed(_FN[fp]) if d[0] <= line]
def match(loc):
    p, h = npath(loc), nhead(loc)
    ln = re.search(r":(\d+)$", (loc or "").split("#", 1)[-1])
    if ln and re.search(r"\.(sh|py|mjs|js|ts)$", p):
        for fn in (func_at(p, int(ln.group(1))) or []):
            hits = [c for c in dict.fromkeys(by_path.get(p, [])) if ("#" in c and c.split("#", 1)[1].split(":")[0].split(".")[-1] == fn) or nhead(nodes[c].get("location", "")).split(":")[0].split(".")[-1] == fn.lower()]
            if hits: return hits[0], "line"
    for k, v in OVERRIDE.items():
        if (p == k or p.startswith(k + "/")) and v in nodes: return v, "manual"
    cands = list(dict.fromkeys(by_path.get(p, [])))
    if cands:
        if h:
            for nid in cands:
                nh = nhead(nodes[nid].get("location", "")) or nhead(nid)
                if nh and ((len(nh) >= 8 and (nh[:14] in h or h[:14] in nh)) or nh == h): return nid, "heading"
        pool = [c for c in cands if nodes[c]["carrier"] in ("skill", "reference", "script", "prompt", "command")] or cands
        want = TOK(h + " " + (EXC or ""))
        best = max(pool, key=lambda c: len(want & TOK((nodes[c]["id"].split("#", 1)[1] if "#" in nodes[c]["id"] else "") + " " + nodes[c].get("name", "") + " " + nhead(nodes[c].get("location", "")))))
        return best, "file"
    d = dir_of(p)
    if d and by_dir.get(d):
        ids = list(dict.fromkeys(by_dir[d]))
        pri = [c for c in ids if nodes[c]["carrier"] == "skill"]
        return (pri or ids)[0], "dir"
    return None, None

a, b = load("C4a-upstream.json"), load("C4b-research-refs.json")
SRC = {}
for s in a["sources"] + b["sources"]:
    SRC.setdefault(s["id"], s)
# unify duplicate ids for the same upstream
ALIAS = {"mattpocock": "mattpocock-skills", "unlazy": "leonxlnx-unlazy", "diagram": "cathrynlavery-diagram-design"}
refs, unmatched = [], []
web_bg = collections.defaultdict(lambda: collections.Counter())
for grp, data in (("C4a", a), ("C4b", b)):
    for u in data["uses"]:
        sid = ALIAS.get(u["source"], u["source"])
        s = SRC.get(sid) or SRC.get(u["source"]) or {}
        if sid.startswith("webref"):
            dom = re.sub(r"^https?://", "", s.get("name", "") or s.get("location", "")).split("/")[0]
            web_bg[npath(u["mmw_location"])][dom or "?"] += 1
            continue
        globals()["EXC"] = u.get("mmw_excerpt", "")
        nid, how_m = match(u["mmw_location"])
        r = {"src": sid, "how": u["how"], "loc": u["mmw_location"], "mx": u.get("mmw_excerpt", ""), "sloc": u.get("source_location", ""),
             "sx": u.get("source_excerpt", ""), "chg": u.get("changes", ""), "why": u.get("intent", ""), "inf": u.get("inferred_intent", ""),
             "ev": u.get("evidence", []), "node": nid, "m": how_m, "g": grp}
        (refs if nid else unmatched).append(r)

src_out = {}
for sid in set([r["src"] for r in refs + unmatched]):
    s = SRC.get(sid, {})
    src_out[sid] = {"name": s.get("name", sid), "kind": s.get("kind", "other"), "loc": s.get("location", ""), "what": s.get("what_it_is", "")}
for k in ALIAS.values():
    if k in SRC: src_out.setdefault(k, {"name": SRC[k]["name"], "kind": SRC[k]["kind"], "loc": SRC[k].get("location", ""), "what": SRC[k].get("what_it_is", "")})

web = [{"note": k, "domains": v.most_common(), "n": sum(v.values())} for k, v in sorted(web_bg.items(), key=lambda kv: -sum(kv[1].values()))]
out = {"bands": [{"g": g, "stage": STAGE[g], "p": p} for g, p in order], "nodes": list(nodes.values()), "edges": edges,
       "refs": refs, "unmatched": unmatched, "sources": src_out, "web": web, "notes": notes, "badband": bad}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "map-data.json"), "w"), ensure_ascii=False)
mc = collections.Counter(r["m"] for r in refs)
print("nodes", len(nodes), "edges", len(edges), "refs", len(refs), mc, "unmatched", len(unmatched), "web notes", len(web), sum(w["n"] for w in web))
print("unmatched by src", collections.Counter(r["src"] for r in unmatched).most_common(12))
print("unmatched locs", collections.Counter(npath(r["loc"]) for r in unmatched).most_common(15))
print("bands used", collections.Counter(n["_band"] for n in nodes.values()))
print("manual skills", [n["name"] for n in nodes.values() if n.get("manual")])
