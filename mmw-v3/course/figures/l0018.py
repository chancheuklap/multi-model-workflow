"""Figure of lesson 0018: the panorama of MMW v3, every component in six columns with its origin, and the data
the page's script uses to show each component's links when it is clicked."""
import html
import json
from pathlib import Path

from kit import tw

DATA = Path(__file__).with_name("l0018-graph.json")

LH, HEAD, GAP, TOP = 18, 28, 14, 46

# Columns left to right: where work starts, what decides how, the procedures, who does the work,
# the machinery, what it leaves behind. Each column is a list of (group title, kind class, node ids).
COLUMNS = [
    ("入口与你", 200, [("会话怎样开始", "other", "entry"), ("你的决定点", "other", "human")]),
    ("mmw-mode 与原则", 290, [("mmw-mode 的七节", "mode", "mode"), ("原则", "principle", "principle")]),
    ("playbook", 250, [("白天：地图、设计、spec、分诊", "playbook", "白天"), ("夜里：一夜与一张票", "playbook", "夜间"),
                       ("单项任务", "playbook", "单项"), ("维护技能集与仓库", "playbook", "维护"),
                       ("参考文件", "reference", "reference")]),
    ("技能与角色", 230, [("流水线核心", "skill", "流水线核心"), ("设计与界面", "skill", "设计与界面"),
                         ("规划与理解", "skill", "规划与理解"), ("工程", "skill", "工程 skill"),
                         ("写作", "skill", "写作"), ("只由人启动", "skill", "只由人启动"),
                         ("会话角色（脚本开）", "agent", "会话角色"), ("子代理角色", "agent", "子代理角色")]),
    ("脚本与外部系统", 240, [("dispatch 的脚本与钩子", "script", "dispatch 脚本"), ("verify-ticket 的脚本", "script", "verify-ticket 脚本"),
                             ("其他技能的脚本", "script", "其他 skill"), ("工具箱级", "script", "工具箱级"),
                             ("外部系统", "other", "外部系统")]),
    ("配置与产物", 270, [("配置", "config", "配置"), ("地图、设计、spec", "other", "spec 产物"),
                         ("票与夜里", "other", "票与夜间"), ("其他", "other", "其他产物")]),
]

# Names that read better shortened in the picture; the panel shows the full name.
LABELS = {"script.board": "board/（看板进程）", "hook.mode-hook": "mode-hook.py 钩子",
          "ref.skills-readme": "skills/README.md"}


def label(n):
    k, name = n["kind"], n["name"]
    if n["id"] in LABELS:
        return LABELS[n["id"]]
    if k in ("entry", "human", "artifact", "config", "external"):
        return n.get("label_zh") or name
    if k == "principle":
        return name.removeprefix("principle-")
    if k == "reference":
        return name.split("/")[-1].split(" ")[-1]
    if k == "script":
        return name.split("/")[-1] if " " not in name else name.split(" ")[-1].split("/")[-1]
    if k == "mode-section" and name != "mmw-mode":
        return "## " + name
    return name


def fit(text, room, size=12.0):
    if tw(text, size) <= room:
        return text
    while text and tw(text + "…", size) > room:
        text = text[:-1]
    return text + "…"


def members(data, key):
    nodes = {n["id"]: n for n in data["nodes"]}
    if key == "entry":
        ids = [n["id"] for n in data["nodes"] if n["kind"] in ("entry", "hook") and n["id"] in
               ("entry.owner-session", "hook.mode-hook", "entry.start-prompt", "entry.model-invoked")]
        return [nodes[i] for i in ids if i in nodes]
    if key in ("human", "reference", "principle"):
        return [n for n in data["nodes"] if n["kind"] == key]
    if key == "mode":
        return [n for n in data["nodes"] if n["id"] == "skill.mmw-mode" or n["kind"] == "mode-section"]
    for g in data["groups"]:
        if key in g["title_zh"]:
            return [nodes[m] for m in g["members"] if m in nodes and m != "skill.mmw-mode" and m != "hook.mode-hook"]
    raise KeyError(key)


def panorama():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    out, x, H = [], 10, 0
    placed = set()
    for title, width, groups in COLUMNS:
        out.append(f'<text x="{x}" y="22" class="h">{html.escape(title)}</text>')
        y = TOP
        for gtitle, cls, key in groups:
            ms = members(data, key)
            h = HEAD + len(ms) * LH + 8
            out.append(f'<g class="k-{cls}"><rect class="box grp" x="{x}" y="{y}" width="{width}" height="{h}" rx="4"/></g>'
                       f'<text x="{x + 10}" y="{y + 19}" class="gh">{html.escape(gtitle)}<tspan class="s"> {len(ms)}</tspan></text>')
            for i, n in enumerate(ms):
                ty = y + HEAD + i * LH + 9
                o = n.get("origin")
                dot = f'<circle class="od o-{o}" cx="{x + 14}" cy="{ty - 4}" r="4"/>' if o else ""
                out.append(f'<g class="nd" data-id="{html.escape(n["id"])}" tabindex="0" role="button">'
                           f'<rect class="hit" x="{x + 4}" y="{ty - 13}" width="{width - 8}" height="{LH}" rx="3"/>{dot}'
                           f'<text x="{x + 24}" y="{ty}" class="nt">{html.escape(fit(label(n), width - 32))}</text></g>')
                placed.add(n["id"])
            y += h + GAP
        H = max(H, y)
        if x > 10:
            out.append(f'<text x="{x - 11}" y="22" class="s" text-anchor="middle">→</text>')
        x += width + 22
    W = x - 12
    missing = [n["id"] for n in data["nodes"] if n["id"] not in placed]
    if missing:
        raise ValueError(f"nodes not placed: {missing}")
    ids = {n["id"] for n in data["nodes"]}
    for name, path in FLOWS.items():
        bad = [i for i in path if i not in ids]
        if bad:
            raise ValueError(f"flow {name} names unknown nodes: {bad}")
    data["flows"] = FLOWS
    svg = (f'<svg id="pano" viewBox="0 0 {W} {H}" style="width:{W}px;min-width:{W}px" role="img" '
           f'aria-label="{html.escape(ARIA)}">' + "".join(out) + "</svg>")
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return svg + f'<script type="application/json" id="pano-data">{blob}</script>'


# The three typical paths, as ordered node ids: what a day request, a night and one bug fix pass through.
FLOWS = {
    "白天的一个需求": ["entry.owner-session", "skill.mmw-mode", "mode.playbooks", "pb.chart-a-map", "human.gate-map-destination",
                 "skill.grilling", "art.map", "pb.resolve-a-map-ticket", "art.decision-ticket", "pb.design-in-claude-design",
                 "ext.claude-design", "human.gate-design-signoff", "pb.pull-a-design", "script.pull-design", "art.design-package",
                 "pb.write-the-screen-contract", "human.gate-gap-list", "art.screen-contract", "pb.write-a-spec",
                 "human.gate-spec-calls", "script.verify-ticket-py", "art.spec", "pb.cut-tickets", "role.ambiguity-scanner",
                 "human.gate-approve-breakdown", "art.ticket"],
    "一夜": ["human.gate-start-night", "pb.run-a-night", "role.orchestrator", "script.dispatch-sh", "script.relay",
           "script.verify-ticket-py", "entry.start-prompt", "role.junior-worker", "pb.work-a-ticket", "skill.tdd",
           "art.ticket-worktree", "script.gate-check", "art.decisions-comment", "role.reviewer", "pb.review-a-ticket",
           "skill.code-review", "role.code-review-axis", "art.review-report", "art.closing-comment", "art.events",
           "art.base-branch", "art.child-issue", "art.memory-records", "art.night-summary", "skill.retro", "art.night-retro",
           "human.gate-accept-night", "art.project-branch", "human.gate-release-merge", "hook.turn-guard", "script.watchdog"],
    "修一个 bug": ["entry.owner-session", "skill.mmw-mode", "mode.playbooks", "pb.bug-fix", "skill.diagnosing-bugs",
                 "skill.ui-acceptance", "skill.how", "skill.why", "art.ticket", "script.verify-ticket-py", "pb.run-one-ticket",
                 "role.orchestrator", "script.dispatch-sh", "role.junior-worker", "pb.work-a-ticket", "art.events",
                 "script.relay", "art.base-branch", "principle.prove-it-works"],
}


ARIA = ("第 18 课全景图：MMW v3 的全部组件，分六列从左到右。第一列入口与你：会话怎样开始的四条路，以及你的十七个决定点。"
        "第二列 mmw-mode 的七节和十五条原则。第三列二十四份 playbook，分白天、夜里、单项任务、维护四组，以及参考文件。"
        "第四列技能，分流水线核心、设计与界面、规划与理解、工程、写作、只由人启动六组，以及会话角色和子代理角色。"
        "第五列脚本与外部系统。第六列配置与产物。每个名字前的色点标出它来自 pstack、来自 v2，还是 v3 新写的。"
        "点任一名字，与它相连的组件会高亮，图下列出它的用途、出处和全部连线。")

FIGS = {"l18-panorama": panorama}
