"""Figures of lesson 0008: the role table and what checks it, and one batch of briefs from start to close."""
import html
from kit import Fig, tw

SIZES = {"s": 11.5, "m": 12.0, "h": 14.0}


def _fits(text, cls, room):
    """Refuse a line wider than the room it is drawn in; monospace fallbacks run wider."""
    need = tw(text, SIZES[cls], cls == "m") * (1.12 if cls == "m" else 1.0)
    if need > room:
        raise ValueError(f"{text!r} needs {need:.0f}px and has {room}px")


def _t(f, x, y, t, cls="s", anchor="start", room=None):
    if room is not None:
        _fits(t, cls, room)
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    f.e(f'<text x="{x}" y="{y:.1f}" class="{cls}"{a}>{html.escape(t)}</text>')


def _box(f, kind, x, y, w, title, lines, mono_title=True, dashed=False):
    """A box with a title and lines below it; returns its height."""
    h = 30 + len(lines) * 17
    dash = ' style="stroke-dasharray:6 3"' if dashed else ""
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"{dash}/></g>', False)
    _t(f, x + 12, y + 20, title, "m" if mono_title else "h", room=w - 20)
    for i, line in enumerate(lines):
        _t(f, x + 12, y + 39 + i * 17, line, room=w - 20)
    return h


def table():
    f = Fig("m81", 1000)
    _t(f, 10, 20, "一张角色表，两种角色，一条检查管住两头", "h")

    # the table itself
    th = _box(f, "config", 330, 40, 340, "dispatch/roles.json", [
        "session，command start：",
        "  junior-worker、senior-worker、reviewer",
        "session，command brief：",
        "  advisor、researcher、explainer、synthesizer",
        "subagent：",
        "  code-review axis、grilling fact-finder",
        "每行写：做什么、交回什么、谁用它",
    ])

    # adding a session role
    f.zone(4, 34, 314, 300, "加一个独立会话角色：三处")
    y = 66
    for title, lines in (
        ("roles.json 一行", ["kind session，command brief，", "lead 或 brief 模板，sent_by"]),
        ("hosts.json 的 defaults 一行", ["新机器上它用的宿主、模型、effort"]),
        ("它开工读的文字", ["lead 文件，或调用方填的模板"]),
    ):
        y += _box(f, "config" if "json" in title else "reference", 16, y, 290, title, lines,
                  mono_title=False) + 10
    _t(f, 16, y + 14, "自动跟上的：", "h")
    _t(f, 16, y + 34, "models.py 从表里读角色名，install 给缺的", room=296)
    _t(f, 16, y + 51, "角色补上默认行；dispatch.sh brief 读 lead", room=296)
    f.ar([(306, 82), (326, 82)])

    # adding a subagent
    f.zone(682, 34, 314, 300, "加一个子代理角色：两处")
    y = 66
    y += _box(f, "config", 694, y, 290, "roles.json 一行", ["kind subagent，sent_by，", "prompt：提示词文件"], mono_title=False) + 10
    y += _box(f, "reference", 694, y, 290, "提示词文件", ["放在派它的技能的 references/"], mono_title=False) + 10
    _t(f, 694, y + 14, "子代理跟会话同一个模型。", room=290)
    _t(f, 694, y + 31, "要换模型的，做成独立会话。", room=290)
    f.ar([(690, 82), (674, 82)])

    # the check
    cy = 350
    checks = [
        "1  每个独立会话角色在 hosts.json 有默认行；defaults 里没有表外的角色",
        "2  表里点名的 lead、brief 模板、prompt 文件都在；lead 技能在",
        "3  sent_by 的技能在，且真的用它：写了 dispatch.sh brief <角色>，或点名了 prompt 文件",
        "4  任何 SKILL.md 和 playbook 写的 dispatch.sh brief <角色>，表里都是 brief 角色",
        "5  派子代理的 SKILL.md（send、spawn、dispatch 后接 subagent 或 sub-agent）是某个子代理行的 sent_by",
    ]
    f.zone(4, cy, 992, 34 + len(checks) * 22 + 8, "check-interfaces.py 第 6 条，每次跑都查")
    for i, line in enumerate(checks):
        _t(f, 16, cy + 46 + i * 22, line, room=970)
    f.ar([(500, 40 + th), (500, cy)])
    H = cy + 34 + len(checks) * 22 + 16
    return f.svg(H, "一张角色表 dispatch/roles.json，两种角色。独立会话角色里，junior-worker、senior-worker、reviewer 由 dispatch.sh start 开，advisor、researcher、explainer、synthesizer 由 dispatch.sh brief 开；子代理角色有 code-review axis 和 grilling fact-finder。加一个独立会话角色要改三处：roles.json 一行，hosts.json 的 defaults 一行，它开工读的文字。models.py 从表里读角色名，install 给缺的角色补默认行，dispatch.sh brief 从表里读开工的文字。加一个子代理角色要改两处：roles.json 一行，提示词文件放进派它的技能的 references。check-interfaces.py 第 6 条每次都查五件事：会话角色都有默认行；表里点名的文件都在；sent_by 的技能真的用它；技能写的 dispatch.sh brief 角色都在表里；派子代理的技能都在表里。")


LANES = [("上级会话", "playbook"), ("dispatch.sh", "script"), ("briefs/<批>/", "config"),
         ("中继 relay.py", "script"), ("子会话", "agent")]
LANE_W = 196
LANE_X = [4 + i * (LANE_W + 3) for i in range(5)]
LANE_H = 690


def _step(f, lane, y, title, lines, kind=None, mono=True):
    x = LANE_X[lane] + 6
    return _box(f, kind or LANES[lane][1], x, y, LANE_W - 12, title, lines, mono_title=mono)


def life():
    f = Fig("m82", 1000)
    _t(f, 10, 20, "一批 brief 从开到关：两个 researcher", "h")
    top = 34
    for (name, kind), x in zip(LANES, LANE_X):
        f.e(f'<rect class="zone" x="{x}" y="{top}" width="{LANE_W}" height="{LANE_H}" rx="6"/>', False)
        f.e(f'<g class="k-{kind}"><text x="{x + 12}" y="{top + 20}" class="h">{html.escape(name)}</text></g>', False)

    y = top + 34
    _step(f, 0, y, "brief researcher", ["a.md b.md"])
    _step(f, 1, y, "认出上级", ["own_session：读不出", "会话号就拒绝，", "什么也不开"], mono=False)
    _step(f, 2, y, "batch.json", ["角色、份数、", "上级的 runner 和会话号"])
    _step(f, 3, y, "看守 briefs:<批>", ["上级就是这个看守", "的 orchestrator"])
    f.ar([(LANE_X[1] - 3, y + 30), (LANE_X[1] + 4, y + 30)])
    f.ar([(LANE_X[2] - 3, y + 30), (LANE_X[2] + 4, y + 30)])
    f.ar([(LANE_X[3] - 3, y + 30), (LANE_X[3] + 4, y + 30)])

    y += 104
    _step(f, 1, y, "每份 brief 开一个", ["开工的话三段：", "lead（表里写的）", "brief 文件全文", "交回说明"], mono=False)
    _step(f, 2, y, "1/started.json", ["子会话的 runner、", "会话号、模型"])
    _step(f, 4, y, "researcher × 2", ["各在自己的宿主上", "读、查、写答案"], mono=False)
    f.ar([(LANE_X[2] - 3, y + 30), (LANE_X[2] + 4, y + 30)])
    f.ar([(LANE_X[1] + LANE_W - 6, y + 90), (LANE_X[4] + 4, y + 90)])
    _t(f, LANE_X[0] + 10, y + 30, "然后结束回合", "h", room=180)
    _t(f, LANE_X[0] + 10, y + 50, "不轮询，不挂着等", room=180)
    _t(f, LANE_X[1] + 10, y + 120, "开第二份失败：已开的", room=180)
    _t(f, LANE_X[1] + 10, y + 137, "停掉，整批删掉，", room=180)
    _t(f, LANE_X[1] + 10, y + 154, "看守关掉", room=180)

    y += 120 + 58
    _step(f, 4, y, "report <批>/1 x.md", ["只认 started.json", "记的那个会话"])
    _step(f, 2, y, "1/result.md", ["复制过来的答案，", "然后写 reported.json"])
    f.ar([(LANE_X[4] - 3, y + 30), (LANE_X[2] + LANE_W - 2, y + 30)])

    y += 104
    _step(f, 3, y, "每 30 秒看一次", ["两份都 reported", "或 lost：排一行", "brief <批> done，", "写 woken.json"], mono=False)
    _step(f, 0, y, "醒来", ["runner 的 send", "把这一行送进来"], mono=False)
    f.ar([(LANE_X[3] - 3, y + 30), (LANE_X[0] + LANE_W - 2, y + 30)])

    y += 120
    _step(f, 0, y, "brief show <批>", ["每份的状态和", "答案文件路径"])
    _step(f, 1, y, "ack brief <批>", ["中继不再送"])
    f.ar([(LANE_X[1] - 3, y + 30), (LANE_X[1] + 4, y + 30)])
    y += 82
    _step(f, 0, y, "brief close <批>", ["用完再关"])
    _step(f, 1, y, "停掉子会话", ["关掉看守"], mono=False)
    _step(f, 2, y, "整个目录删掉", ["什么也不留"], mono=False)
    f.ar([(LANE_X[1] - 3, y + 30), (LANE_X[1] + 4, y + 30)])
    f.ar([(LANE_X[2] - 3, y + 30), (LANE_X[2] + 4, y + 30)])
    return f.svg(top + LANE_H + 8, "一批 brief 从开到关，以两个 researcher 为例。上级会话跑 dispatch.sh brief researcher a.md b.md。dispatch.sh 先认出上级的会话号，读不出就拒绝，什么也不开；然后在本机状态目录建 briefs/批/batch.json，记下角色、份数和上级；中继开一个看守 briefs:批，上级是它的 orchestrator。dispatch.sh 每份 brief 开一个会话，开工的话三段：表里写的 lead、brief 文件全文、交回说明，并写 1/started.json；上级随后结束回合，不轮询。开第二份失败时，已开的会话停掉，整批删掉，看守关掉。子会话做完跑 dispatch.sh report 批/1 x.md，只认 started.json 记的那个会话，答案复制成 result.md，再写 reported.json。中继每 30 秒看一次，两份都 reported 或 lost 时排一行 brief 批 done，写 woken.json，经 runner 的 send 叫醒上级。上级跑 brief show 看每份的状态和答案文件，ack brief 批，用完后 brief close 批：停掉子会话，关掉看守，删掉整个目录。")


FIGS = {"l8-table": table, "l8-life": life}
