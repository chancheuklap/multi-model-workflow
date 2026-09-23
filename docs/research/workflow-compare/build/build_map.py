"""Build mmw-map.html: merge the C1/C2/C3/C5 flow data, add installed skills missing from the flow, and attach the T1-T5 root provenance (external project, file and section, clue chain) to each node."""
import json, re, collections, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
def load(n): return json.load(open(os.path.join(HERE, "..", "reports", n)))

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

# ---------- root provenance (T1-T5) ----------
PID = {"matt": "mattpocock", "mattpocock-skills": "mattpocock", "gh": "github"}
ROLE = {
 "subtree": ["mattpocock", "unlazy", "diagram"],
 "design": ["firstmate", "monomind", "bmad", "spec-kit", "factory-missions", "openai-cookbook", "anthropic-effective", "grok-bundled", "agentskills"],
 "runtime": ["claude-design", "playwright", "paseo", "orca", "herdr", "nowledge", "github", "git", "claude", "codex", "codex_source", "pi", "grok", "apple", "nuitka", "electron", "ruff", "pyrefly", "oxlint", "prek"],
 "replaced": ["superpowers", "planning-files", "ponytail", "caveman", "gstack", "pstack", "serena", "graphify", "context7", "showme", "manus"],
}
projects = {}
comps = []
for f in ["T1-front.json", "T2-night.json", "T3-ticket.json", "T4-toolbox.json", "T5-history.json"]:
    d = load(f); tg = f[:2]
    for p in d["projects"]:
        pid = PID.get(p["id"], p["id"])
        q = projects.setdefault(pid, {"id": pid, "name": p["name"], "repo": re.sub(r"^https://github\.com/([^/]+/[^/#]+).*$", r"\1", p.get("repo", "")), "snap": [], "what": p.get("what", ""), "first": p.get("first_seen", "")})
        if p.get("snapshot") and p["snapshot"] != "无" and p["snapshot"] not in q["snap"]: q["snap"].append(p["snapshot"])
    for c in d["components"]:
        if tg == "T5" and not c["origins"]: continue
        kind = "para" if tg == "T5" and c["id"].startswith("upstream-") else ("hist" if tg == "T5" and c["id"].startswith("history") else "comp")
        og = [{"p": PID.get(o["project"], o["project"]), "part": o["part"], "ver": o.get("version", ""), "took": o.get("what_was_taken", ""),
               "how": o["how"], "chain": o.get("chain", []), "conf": o.get("confidence", ""), "why": o.get("intent", "")} for o in c["origins"]]
        ns = list(dict.fromkeys(x for x in c.get("mmw_nodes", []) if x in nodes))
        how_m = "ids"
        if kind == "para" and len(ns) > 1:
            globals()["EXC"] = c["name"]
            nid, how_m = match(c["mmw_location"])
            ns = [nid] if nid in ns else ns[:1]
        if not ns and c.get("mmw_location"):
            globals()["EXC"] = c["name"]
            nid, how_m = match(c["mmw_location"].split(";")[0].strip())
            ns = [nid] if nid else []
        comps.append({"id": f"{tg}:{c['id']}", "t": tg, "k": kind, "name": c["name"], "loc": c.get("mmw_location", ""), "nodes": ns, "m": how_m,
                      "og": og, "orig": bool(c.get("original_to_mmw")), "searched": c.get("searched", "")})
used = collections.Counter(o["p"] for c in comps for o in c["og"])
role_of = {p: r for r, ps in ROLE.items() for p in ps}
proj_out = {pid: {**p, "role": role_of.get(pid, "design"), "n": used[pid]} for pid, p in projects.items() if used[pid]}
cited_only = len([p for p in projects if not used[p]])
hist_notes = load("T5-history.json").get("notes", [])
covered = {n for c in comps for n in c["nodes"]}
out = {"bands": [{"g": g, "stage": STAGE[g], "p": p} for g, p in order], "nodes": list(nodes.values()), "edges": edges,
       "comps": comps, "projects": proj_out, "citedOnly": cited_only, "hist": hist_notes, "notes": notes, "badband": bad}
tpl = open(os.path.join(HERE, "map.tpl.html"), encoding="utf-8").read()
open(os.path.join(HERE, "..", "mmw-map.html"), "w", encoding="utf-8").write(tpl.replace("__DATA__", json.dumps(out, ensure_ascii=False).replace("</", "<\\/")))
print("nodes", len(nodes), "edges", len(edges), "comps", len(comps), collections.Counter(c["k"] for c in comps), "match", collections.Counter(c["m"] for c in comps))
print("no node", [(c["id"], c["loc"][:60]) for c in comps if not c["nodes"]])
print("projects used", len(proj_out), "cited only", cited_only, "role default", [p for p in proj_out if p not in role_of])
print("nodes covered", len(covered), "/", len(nodes))
print("uncovered by band", collections.Counter(nodes[n]["_band"] for n in nodes if n not in covered))
print("bands used", collections.Counter(n["_band"] for n in nodes.values()))
print("manual skills", [n["name"] for n in nodes.values() if n.get("manual")])
