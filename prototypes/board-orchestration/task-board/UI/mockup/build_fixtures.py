#!/usr/bin/env python3
"""Build the task board's example data with the pipeline's own event code.

    python3 build_fixtures.py

Every event of every example ticket is written with `events.build` from the
verify-ticket skill — so a payload the vocabulary refuses cannot get in — and each
ticket's state is `events.fold` of those comments, exactly what the board's local
process would hand the page. The result is written between the `FIXTURES:BEGIN` and
`FIXTURES:END` markers of `task-board-mockup.html` beside this file and of
`../work/data/fixtures.js`. The tickets obey the pipeline they depict: a ticket is
dispatched in the same `advance` that lands its last blocker, every result goes through
the closing steps of `implement`, and a ticket is handed back only for a `failed` or
`stuck` criterion; `check-fixtures.js` checks that after the build.

The data is an example, not the owner's tickets. Times are local wall-clock times of the
night of 2026-09-10; the board read the tracker at 07:39 on 09-11.

The settings page's data (#335: which host, model and effort each agent runs on, and the
runner, chosen on this machine) goes between the `SETTINGS:BEGIN` and `SETTINGS:END`
markers of the mockup only. It is built with the dispatch skill's own `models.py`: the
hosts, their CLI binaries and the default rows are `hosts.json` read by `load_hosts`, the
runners are the adapters under `scripts/runners/`, and each host's `model` and `effort`
options are `fillable_rows` of an example catalog in the shape `scan_cli_catalogs` returns
when it asks the hosts' CLIs — the everyday names `start` resolves. A saved configuration
holds the runner and all five agents' rows; a new machine's is MMW's initial values
(`hosts.json` `defaults`, `models.DEFAULT_RUNNER`), every other one is example data.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
DISPATCH_SCRIPTS = REPO / "mmw-v2" / "skills" / "dispatch" / "scripts"
sys.path.insert(0, str(REPO / "mmw-v2" / "skills" / "verify-ticket" / "scripts"))
sys.path.insert(0, str(DISPATCH_SCRIPTS))
import events  # noqa: E402
import models  # noqa: E402

# The machine's clock is UTC+8 (the owner's); events carry UTC, as events.now() writes them.
LOCAL = timezone(timedelta(hours=8))
NOW = "2026-09-10T23:40:00Z"   # 07:40 on 09-11, local
MACHINE = "cheuk-mbp"
WORKTREES = "/Users/cheuklapchan/multi-model-workflow/.worktrees/"
LOGIN = "chancheuklap"
REVIEWER = ("codex", "gpt-5.5", "medium")
VERIFIER = ("claude", "sonnet 5", "medium")


def iso(hm: str) -> str:
    """A local wall-clock time of the night, as the UTC timestamp events.now() writes:
    '22:14' belongs to the evening of 09-10, '06:38' to the morning of 09-11."""
    day = "2026-09-10" if hm >= "12:00" else "2026-09-11"
    local = datetime.fromisoformat(f"{day}T{hm}:00").replace(tzinfo=LOCAL)
    return local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def minutes(hm: str) -> int:
    h, m = map(int, hm.split(":"))
    return (0 if hm >= "12:00" else 1440) + h * 60 + m


def hm_of(total: float) -> str:
    m = round(total) % 1440
    return f"{m // 60:02d}:{m % 60:02d}"


def sha(*parts) -> str:
    return hashlib.sha1("-".join(map(str, parts)).encode()).hexdigest()


def session_id(n: int, kind: str, runner: str) -> str:
    return ("term_" if runner == "orca" else "w") + sha(n, kind)[:4]


class Ticket:
    """One example ticket: its events in the order the pipeline writes them."""

    def __init__(self, n: int, title: str, spec: int, blocked=(), closeout=None, slug="work"):
        self.n, self.title, self.spec = n, title, spec
        self.blocked, self.closeout, self.slug = list(blocked), closeout, slug
        self.bodies: list[tuple[str, str]] = []  # (at, body)
        self.runner = "herdr"
        self.acs = 4
        self.abandon_kind, self.abandon_reason = None, None

    def emit(self, hm: str, event: str, line: str, **fields):
        body = events.build(event, ticket=self.n, spec=self.spec, line=line, at=iso(hm), **fields)
        self.bodies.append((iso(hm), body))

    # ── the pipeline's steps, each written the way its script writes it ──
    # First lines and fields follow dispatch.sh (`*.started`, `ticket.landed`,
    # `child.closed`) and verify-ticket.py (claim, runs, queue, review, decisions, verdict,
    # closeout, `child.opened`); only titles, reasons and evidence are example prose.
    def _started(self, kind, hm, host, model, effort, runner, grade):
        sid = session_id(self.n, kind, runner)
        self.emit(hm, f"{kind}.started", f"{kind} started on {runner}: session {sid}, {host} {model} ({effort})",
                  session=sid, runner=runner, machine=MACHINE, host=host, model=model, effort=effort,
                  grade=grade, worktree=f"{WORKTREES}{self.n}-{self.slug}", branch=f"issue-{self.n}",
                  base=sha(self.n, "base"))
        return sid

    def start(self, hm, host, model, effort, runner="herdr"):
        self.runner = runner
        self._started("worker", hm, host, model, effort, runner, "senior-worker")
        self.emit(hm, "ticket.claimed", f"Claimed #{self.n} on issue-{self.n} as {LOGIN}",
                  login=LOGIN, branch=f"issue-{self.n}", commit=sha(self.n, "base"))

    def queued(self, hm, reason="product-full", run="self"):
        what, limit = (("this product's instance.max", 2) if reason == "product-full"
                       else ("every slot of this machine", 8))
        self.emit(hm, "worker.queued", f"Waiting for a product slot: {what} ({limit}) is held",
                  run=run, reason=reason, limit=limit,
                  holders=[f"{WORKTREES}126-work", f"{WORKTREES}127-work"],
                  worktree=f"{WORKTREES}{self.n}-{self.slug}")

    def _criteria(self, handoff_ac=None):
        ids = [f"AC{i}" for i in range(1, self.acs + 1)]
        crit = [{"id": i, "met": i != handoff_ac, "evidence": "pending" if i == handoff_ac else f"{i.lower()}.log"}
                for i in ids]
        abandons = ([{"ac": handoff_ac, "kind": self.abandon_kind, "reason": self.abandon_reason}]
                    if handoff_ac else None)
        counts = {"met": len(ids) - (1 if handoff_ac else 0), "unmet": 0,
                  "abandoned": 1 if handoff_ac else 0, "total": len(ids)}
        return crit, abandons, counts

    def checked(self, hm, run="self", slot=None, handoff_ac=None):
        head = sha(self.n, "head")
        if run == "repo-checks":
            self.emit(hm, "ticket.checked", f"Repository checks on {head[:12]}: 3/3 passed",
                      run=run, commit=head, result="met", stage="close",
                      counts={"passed": 3, "total": 3})
            return
        crit, abandons, counts = self._criteria(handoff_ac)
        result = "handoff" if handoff_ac else "met"
        summary = f"HANDOFF REQUIRED: {handoff_ac} {self.abandon_kind}" if handoff_ac else "ALL MET"
        extra = {} if run == "reverify" else {"outside_owns": []}
        self.emit(hm, "ticket.checked", f"{'Reverify' if run == 'reverify' else 'Own run'} on {head[:12]}: {summary}",
                  run=run, commit=head, result=result, counts=counts, criteria=crit,
                  failed=[c["id"] for c in crit if not c["met"]], abandons=abandons,
                  shape=hashlib.sha256(f"{self.n}-criteria".encode()).hexdigest(),
                  slot=slot, port_base=(21000 + 100 * slot) if slot else None,
                  actor="verifier" if run == "reverify" else "worker",
                  stage="verify" if run == "reverify" else "work", **extra)

    def review(self, hm, report=None, findings=0):
        host, model, effort = REVIEWER
        self._started("reviewer", hm, host, model, effort, "herdr", "reviewer")
        if report:
            base, head = sha(self.n, "base"), sha(self.n, "head")
            self.emit(report, "reviewer.reported", f"REVIEW {base}..{head}", base=base, head=head)

    def decided(self, hm):
        self.emit(hm, "worker.decided", "DECISIONS")

    def verify(self, hm, rerun=None, verdict=None, handoff_ac=None):
        host, model, effort = VERIFIER
        self._started("verifier", hm, host, model, effort, "herdr", "verifier")
        if rerun:
            self.checked(rerun, run="reverify", handoff_ac=handoff_ac)
        if verdict:
            # verify-ticket.py --verdict passes only a reverify whose result is `met`: a run
            # that carries an abandoned criterion is `handoff`, so its verdict is a failure.
            head, ok = sha(self.n, "head"), handoff_ac is None
            says = "every criterion met on HEAD" if ok else f"{handoff_ac} abandoned ({self.abandon_kind}); the rest met on HEAD"
            self.emit(verdict, "verifier.passed" if ok else "verifier.failed", f"VERDICT {head} by {model} — {says}",
                      commit=head, model=model, says=says, ran=True, failed=None if ok else [handoff_ac])

    def _closeout(self, hm, event, first, handoff_ac=None):
        _, abandons, counts = self._criteria(handoff_ac)
        self.emit(hm, event, first, commit=sha(self.n, "head"), branch=f"issue-{self.n}",
                  counts=counts, abandoned=abandons)

    def passed(self, hm):
        self._closeout(hm, "ticket.passed", "ALL MET")

    def returned(self, hm, ac):
        self._closeout(hm, "ticket.returned", f"HANDOFF REQUIRED: {ac} {self.abandon_kind}", handoff_ac=ac)

    def landed(self, hm):
        self.emit(hm, "ticket.landed", f"Landed issue-{self.n} into main",
                  branch=f"issue-{self.n}", into="main", commit=sha(self.n, "merge"))

    def child(self, hm, n, kind, title, resolution=None, at=None, became=None):
        """A child opened by the worker; `resolution` is routed by main on the closing pass."""
        self.emit(hm, "child.opened", f"Opened #{n} ({kind}): {title}", child=n, kind=kind, title=title)
        if resolution:
            line = {"fixed": f"Fixed #{n} on the closing pass",
                    "stale": f"Closed #{n}: what it states no longer holds",
                    "became-ticket": f"#{n} became ticket #{became} under #{self.spec}"}[resolution]
            self.emit(at, "child.closed", line, child=n, resolution=resolution, became=became,
                      commit=sha(self.n, "merge") if resolution == "fixed" else None)

    def handing_back(self, kind, reason):
        """The `ABANDON:` a hand-back carries: only `failed` or `stuck` turns a ticket back."""
        self.abandon_kind, self.abandon_reason = kind, reason
        return self

    def done(self, start, end, host="claude", model="opus 5", effort="high", runner="herdr"):
        """The whole closing sequence of `implement`, spread between two times."""
        s, e = minutes(start), minutes(end)
        at = lambda f: hm_of(s + (e - s) * f)  # noqa: E731
        self.start(start, host, model, effort, runner)
        self.checked(at(0.40), slot=1)
        self.review(at(0.45), at(0.58))
        self.decided(at(0.62))
        self.verify(at(0.66), rerun=at(0.76), verdict=at(0.80))
        self.checked(at(0.86), run="repo-checks")
        self.passed(at(0.90))
        self.landed(end)
        return self

    # ── the fold ────────────────────────────────────────────────────
    def fixture(self) -> dict:
        ordered = sorted(enumerate(self.bodies), key=lambda p: (p[1][0], p[0]))
        comments = [{"id": 3180000000 + self.n * 100 + i, "body": body} for i, (_, (_, body)) in enumerate(ordered)]
        state = events.fold(comments, self.n)
        records = [r for what, r in events._records(comments) if what == "event"]
        strip = lambda r: None if r is None else {k: r[k] for k in ("comment", "event", "at", "actor", "line", "payload")}  # noqa: E731
        fold = {k: v for k, v in state.items() if k not in ("last",)}
        for key in ("outcome", "review", "verdict", "waiting"):
            fold[key] = strip(fold[key])
        fold["results"] = {k: strip(v) for k, v in fold["results"].items()}
        fold["checks"] = {k: strip(v) for k, v in fold["checks"].items()}
        return {"n": self.n, "title": self.title, "blocked": self.blocked, "closeout": self.closeout,
                "fold": fold, "events": [strip(r) for r in records]}


def dq(n, kind, title, state="closed", blocked=()):
    return {"n": n, "kind": kind, "title": title, "state": state, "blocked": list(blocked)}


def spec(n, title, tickets):
    return {"n": n, "title": title, "tickets": [t.fixture() for t in tickets]}


def morning():
    # spec #123: the night before
    s123 = [
        Ticket(124, "事件表与校验", 123).done("20:05", "21:41", "cursor", "grok 4.6", "high"),
        Ticket(125, "折叠重放", 123, [124]).done("21:42", "23:33", "grok", "grok 4.6", "xhigh"),
        Ticket(127, "一次 GraphQL 读四层", 123, [124]).done("21:42", "23:04"),
        Ticket(126, "status.py 改读折叠", 123, [125]).done("23:34", "01:26", "codex", "gpt-5.5", "high"),
    ]
    # spec #131: tonight
    t132 = Ticket(132, "中继进程骨架", 131, slug="relay-skeleton")
    t132.start("04:30", "claude", "opus 5", "high")
    t132.child("05:05", 148, "deferred", "status 表头少一列 runner", "fixed", at="06:36")
    t132.checked("05:18", slot=1)
    t132.review("05:20", "05:48")
    t132.child("05:50", 147, "finding", "中继日志不轮转，一夜能写满磁盘", "became-ticket", at="06:36", became=141)
    t132.decided("05:52")
    t132.verify("05:55", rerun="06:10", verdict="06:15")
    t132.checked("06:18", run="repo-checks")
    t132.passed("06:20")
    t132.landed("06:36")

    t133 = Ticket(133, "折叠接入中继", 131, [132], slug="fold-relay")
    t133.start("06:38", "grok", "grok 4.6", "xhigh")
    t133.child("06:51", 150, "contract", "spec 没写队列为空时中继读什么")
    t133.child("07:10", 152, "deferred", "status.py 的表头还是旧词")
    t133.child("07:31", 151, "decision", "唤醒要不要跨过已暂停的 spec")

    t134 = Ticket(134, "唤醒队列持久化", 131, [132])
    t134.start("06:38", "codex", "gpt-5.5", "high")
    t134.checked("07:18", slot=2)
    t134.review("07:22")

    t138 = Ticket(138, "离线时唤醒去向", 131, [132]).handing_back("stuck", "离线投递要一个真的 main 会话来收，夜里起不来")
    t138.start("06:38", "grok", "grok 4.6", "high")
    t138.checked("06:58", slot=1, handoff_ac="AC3")
    t138.review("07:00", "07:14")
    t138.decided("07:16")
    t138.verify("07:18", rerun="07:22", verdict="07:24", handoff_ac="AC3")
    t138.returned("07:26", "AC3")

    t141 = Ticket(141, "中继日志轮转", 131, [132], closeout={"from": 132, "child": 147})
    t141.start("06:38", "pi", "kimi k2.6", "—", runner="orca")
    t141.checked("07:02", slot=1)
    t141.review("07:04", "07:24")
    t141.decided("07:28")
    t141.verify("07:32")

    t136 = Ticket(136, "重试与退避", 131, [132])
    t136.start("06:38", "claude", "opus 5", "high")
    t136.queued("07:32")

    s131 = [t132, t133, t134, t138, t141, t136,
            Ticket(135, "投递回执", 131, [133, 134]), Ticket(137, "中继自检命令", 131, [135])]
    s140 = [Ticket(143, "心跳读取", 140), Ticket(144, "回合守卫", 140, [143]),
            Ticket(145, "worker.lost 写入", 140, [144]), Ticket(146, "判活扫描", 140, [143])]
    s80 = [Ticket(81, "scenes.json 导出", 80).done("19:10", "20:31"),
           Ticket(82, "vendor 三个脚本", 80, [81]).done("20:32", "21:20", "cursor", "grok 4.6", "high"),
           Ticket(83, "断网渲染一遍", 80, [82]).done("21:21", "22:36", "codex", "gpt-5.5", "high")]
    s108 = [Ticket(109, "events.py 换成新名", 108), Ticket(110, "verify-ticket 读新名", 108, [109]),
            Ticket(111, "文档跟着改", 108, [109])]
    return {
        "name": "一夜之后", "readAt": iso("07:39"), "readFailed": False, "select": {"task": 98, "node": 133},
        "tasks": [
            {"n": 98, "kind": "wayfinder", "title": "落地流水线改造",
             "decisions": [dq(99, "grilling", "事件格式怎么定"), dq(100, "research", "读票用什么", "closed", [99]),
                           dq(104, "prototype", "唤醒要不要队列", "closed", [99]),
                           dq(105, "grilling", "槽位推到哪一步", "closed", [100, 104]),
                           dq(106, "task", "判活放哪一层", "closed", [105]),
                           dq(107, "grilling", "团队版什么时候做", "open", [105])],
             "specs": [spec(123, "事件评论格式", s123), spec(131, "唤醒回路", s131), spec(140, "判活三层", s140)]},
            {"n": 77, "kind": "grilling", "title": "交接包比对", "decisions": [], "specs": [spec(80, "交接包落盘", s80)]},
            {"n": 101, "kind": "grilling", "title": "子 issue 五种改名", "decisions": [], "specs": [spec(108, "child 用新名字", s108)]},
        ],
    }


def twenty_tickets():
    S = 211
    t = lambda n, title, b=(), **kw: Ticket(n, title, S, b, **kw)  # noqa: E731
    t218 = t(218, "Orca tui-idle 等待", [212]); t218.start("02:56", "pi", "kimi k2.6", "—", runner="orca")
    t218.checked("06:36", slot=1); t218.review("06:40", "07:05"); t218.decided("07:10"); t218.verify("07:28")
    t219 = t(219, "tmux pane 探活", [212]); t219.start("02:56", "grok", "grok 4.6", "high")
    t229 = t(229, "远程 --on 探活", [212]).handing_back("stuck", "远程机器上 orca 不回 hostScope，判不了")
    t229.start("02:56", "grok", "grok 4.6", "xhigh")
    t229.checked("04:40", slot=2, handoff_ac="AC2")
    t229.review("04:42", "05:10"); t229.decided("05:14"); t229.verify("05:16", rerun="05:40", verdict="05:50", handoff_ac="AC2")
    t229.returned("05:58", "AC2")
    t215 = t(215, "Stop hook 叠挂", [214]); t215.start("04:06", "claude", "opus 5", "high")
    t215.checked("04:50", slot=1); t215.review("04:52", "05:10")
    t215.child("05:12", 240, "finding", "install --check 不查叠挂顺序", "became-ticket", at="05:30", became=228)
    t215.decided("05:14"); t215.verify("05:15", rerun="05:21", verdict="05:24"); t215.checked("05:25", run="repo-checks")
    t215.passed("05:26"); t215.landed("05:30")
    t220 = t(220, "判活扫描循环", [213, 214]); t220.start("04:06", "claude", "opus 5", "high")
    t220.child("06:47", 241, "decision", "扫描发现心跳停了 5 分钟，算死还是算不知道")
    t223 = t(223, "扫描间隔配置", [214]); t223.start("04:06", "codex", "gpt-5.5", "medium")
    t223.checked("07:12", slot=2); t223.review("07:15")
    t225 = t(225, "陈旧绑定检测", [217]); t225.start("04:21", "cursor", "grok 4.6", "high"); t225.queued("07:26", "machine-full")
    tickets = [
        t(212, "心跳文件格式").done("02:00", "02:55"),
        t(213, "心跳写入钩子", [212]).done("02:56", "03:50", "codex", "gpt-5.5", "high"),
        t(214, "回合守卫骨架", [212]).done("02:56", "04:05", "grok", "grok 4.6", "xhigh"),
        t(216, "Paseo 回合字段读取", [212]).done("02:56", "03:45", "cursor", "grok 4.6", "high"),
        t(217, "Herdr 状态读取", [212]).done("02:56", "04:20", "codex", "gpt-5.5", "high"),
        t218, t219, t229, t215, t220, t223, t225,
        t(228, "install --check 覆盖叠挂", [215], closeout={"from": 215, "child": 240}).done("05:31", "06:50", "grok", "grok 4.6", "high"),
        t(221, "worker.lost 写入", [220]), t(222, "「不知道」与「死了」分开", [216, 217, 218, 219]),
        t(224, "误判回放测试", [221, 222]), t(226, "retract 联动", [221]), t(227, "夜间摘要一行", [221]),
        t(230, "判活文档", [222, 223]), t(231, "端到端夜跑", [224, 226, 227, 230]),
    ]
    return {
        "name": "一个 spec 二十张票", "readAt": iso("07:39"), "readFailed": False, "select": {"task": 210, "node": 220},
        "tasks": [{"n": 210, "kind": "wayfinder", "title": "判活三层落地",
                   "decisions": [dq(208, "grilling", "三层各看什么"), dq(209, "research", "runner 能不能证明它停了", "closed", [208])],
                   "specs": [spec(S, "判活：心跳、回合、扫描", tickets)]}],
    }


def bad_data():
    S = 301
    t307 = Ticket(307, "回收冲突告警", S, [302], slug="reclaim-alert"); t307.start("05:59", "grok", "grok 4.6", "xhigh")
    t307.child("06:34", 310, "fault", "verify-ticket.py 自跑判据时租约登记表读不出来，直接崩了")
    t306 = Ticket(306, "lease --check", S, [302]); t306.start("05:59", "codex", "gpt-5.5", "high")
    tickets = [Ticket(302, "租约登记表", S).done("05:00", "05:58"),
               Ticket(303, "回收脚本", S, [302, 304]), Ticket(304, "占用探测", S, [303]),
               Ticket(305, "回收日志", S, [399]), t307, t306]
    return {
        "name": "坏数据", "readAt": iso("07:12"), "readFailed": True, "select": {"task": 300, "node": 306},
        "tasks": [{"n": 300, "kind": "grilling", "title": "端口租约回收", "decisions": [],
                   "specs": [spec(S, "租约回收", tickets)]}],
    }


def build() -> dict:
    return {"morning": morning(), "twenty-tickets": twenty_tickets(), "bad-data": bad_data(),
            "empty": {"name": "还没有任务", "readAt": iso("07:39"), "readFailed": False, "select": {}, "tasks": []}}


# ── the settings page: what this machine's hosts offer, and what the owner saved ──

# What `cursor-agent models` prints: Cursor burns the effort into the model id, so one
# family comes back as one line per level the owner enabled in the Cursor app.
CURSOR_MODELS = """\
auto - Auto
composer-2.5 - Composer 2.5
grok-4.6-high - Grok 4.6 High
grok-4.6-xhigh - Grok 4.6 Extra High
grok-4.6-high-fast - Grok 4.6 High Fast
claude-opus-5-medium - Claude Opus 5 Medium
claude-opus-5-high - Claude Opus 5 High
claude-sonnet-5-high - Claude Sonnet 5 High
gpt-5.6-sol-high - GPT-5.6 Sol High
gpt-5.6-sol-xhigh - GPT-5.6 Sol Extra High
gemini-3.8-flash-medium - Gemini 3.8 Flash Medium
kimi-k3-high - Kimi K3 High
"""
CLAUDE_EFFORTS = ["low", "medium", "high", "xhigh", "max"]
PI_EFFORTS = ["off", "minimal", "low", "medium", "high", "xhigh", "max"]


def example_catalog(drop: dict | None = None) -> dict[str, list[dict]]:
    """Tonight's five CLI catalogs in the shape `models.scan_cli_catalogs` returns them.
    `drop` names, per host, the ids a later scan no longer lists."""
    grok = models._host_efforts("grok")
    catalog = {
        "cursor": models._parse_cursor_models(CURSOR_MODELS),
        "grok": [{"id": i, "name": i, "thinkingOptionIds": list(grok)} for i in ("grok-4.6", "grok-4.5")],
        # `claude --help` names the bare aliases too; `fillable_rows` skips them.
        "claude": [{"id": i, "name": i, "thinkingOptionIds": CLAUDE_EFFORTS}
                   for i in ("opus", "sonnet", "fable", "claude-opus-5", "claude-sonnet-5",
                             "claude-fable-5-1", "claude-fable-5")],
        "codex": [{"id": "gpt-6-astra", "name": "GPT-6-Astra", "thinkingOptionIds": CLAUDE_EFFORTS + ["ultra"]},
                  {"id": "gpt-5.6-sol", "name": "GPT-5.6-Sol", "thinkingOptionIds": CLAUDE_EFFORTS + ["ultra"]},
                  {"id": "gpt-5.6-luna", "name": "GPT-5.6-Luna", "thinkingOptionIds": CLAUDE_EFFORTS},
                  {"id": "gpt-5.5", "name": "GPT-5.5", "thinkingOptionIds": CLAUDE_EFFORTS[:4]}],
        "pi": [{"id": i, "name": i.split("/", 1)[1], "thinkingOptionIds": PI_EFFORTS}
               for i in ("deepseek/deepseek-v4-pro", "moonshot/k3", "xai/grok-4.6", "openai/gpt-5.6-sol")],
    }
    for host, ids in (drop or {}).items():
        catalog[host] = [o for o in catalog[host] if o["id"] not in ids]
    return catalog


def scanned(catalog: dict[str, list[dict]], missing: frozenset[str] = frozenset()) -> dict[str, dict]:
    """What the board's scan of this machine hands the page, host by host: whether the
    host's CLI is installed (`missing`), answered with nothing (`silent`), or answered
    (`ok`), and then one entry per `model` with the `effort` cells it may take. `—` is a
    legal cell of its own: a model that takes no effort."""
    out = {}
    for host in models.CLI_HOSTS:
        if host in missing:
            out[host] = {"state": "missing", "offered": []}
            continue
        by_model: dict[str, list[str]] = {}
        for model, cell in models.fillable_rows(host, catalog.get(host) or []):
            by_model.setdefault(model, []).extend(e.strip() for e in cell.split(",") if e.strip())
        offered = [{"model": m, "efforts": e} for m, e in by_model.items()]
        out[host] = {"state": "ok" if offered else "silent", "offered": offered}
    return out


def config(runner: str, rows: dict[str, tuple[str, str, str]]) -> dict:
    """One saved configuration: the runner, and every agent's host, model and effort."""
    return {"runner": runner, "rows": {a: dict(zip(("host", "model", "effort"), rows[a])) for a in models.ALLOWED_AGENTS}}


# What this example machine runs: the owner's own choices, not MMW's initial values.
MINE = {"junior-worker": ("grok", "grok 4.6", "high"),
        "senior-worker": ("codex", "gpt 5.6 sol", "high"),
        "reviewer": ("claude", "opus 5", "high"),
        "verifier": ("claude", "sonnet 5", "high"),
        "advisor": ("claude", "fable 5.1", "medium")}


def settings() -> dict:
    hosts = models.load_hosts()
    initial = {r["agent"]: (r["host"], r["model"], r["effort"]) for r in hosts["defaults"]}
    full = scanned(example_catalog())
    scenes = {
        "mine": {"name": "本机配置合法", "scannedAt": iso("07:02"), "hosts": full,
                 "saved": config("orca", MINE)},
        # A new machine: the first install filled in MMW's initial values, and one of them
        # names a host this machine does not have.
        "fresh": {"name": "新机器 · 初始值里的 cursor 没装", "scannedAt": iso("07:02"),
                  "hosts": scanned(example_catalog(), missing=frozenset({"cursor"})),
                  "saved": config(models.DEFAULT_RUNNER, initial)},
        # A saved model the host's CLI no longer lists.
        "retired": {"name": "选中的 model 本机已经没有", "scannedAt": iso("07:30"),
                    "hosts": scanned(example_catalog({"claude": {"claude-fable-5"}})),
                    "saved": config("orca", {**MINE, "advisor": ("claude", "fable 5", "medium")})},
        # Saved again elsewhere after the page opened: an agent changed reviewer from the command line.
        "changed": {"name": "打开后被别处改过", "scannedAt": iso("07:02"), "hosts": full,
                    "saved": config("orca", MINE),
                    "changedElsewhere": {"at": iso("07:44"),
                                         "saved": config("orca", {**MINE, "reviewer": ("codex", "gpt 5.6 sol", "xhigh")})}},
    }
    return {
        "store": "~/.mmw/models.json",
        "agents": list(models.ALLOWED_AGENTS),
        "hosts": list(hosts["hosts"]),
        "binaries": {h: models.HOST_BINARIES.get(h) for h in hosts["hosts"]},
        "runners": sorted(p.stem for p in (DISPATCH_SCRIPTS / "runners").glob("*.sh")),
        "scenes": scenes,
    }


def between(text: str, name: str) -> re.Match:
    found = re.search(rf"(/\* {name}:BEGIN \*/\n)(.*?)(/\* {name}:END \*/)", text, re.S)
    if not found:
        raise SystemExit(f"no {name}:BEGIN / {name}:END markers")
    return found


def splice(text: str, name: str, block: str) -> str:
    found = between(text, name)
    return text[:found.start(2)] + block + text[found.end(2):]


def main() -> int:
    data = build()
    fixtures = (f"const NOW = {json.dumps(NOW)};\n"
                f"const FIXTURES = {json.dumps(data, ensure_ascii=False, separators=(',', ':'))};\n"
                f"const SCENES = {json.dumps(list(data))};\n")
    mockup_path = HERE / "task-board-mockup.html"
    mockup = splice(mockup_path.read_text(encoding="utf-8"), "FIXTURES", fixtures)
    mockup = splice(mockup, "SETTINGS",
                    f"const SETTINGS = {json.dumps(settings(), ensure_ascii=False, separators=(',', ':'))};\n")
    mockup_path.write_text(mockup, encoding="utf-8")
    # The Claude Design pages load one script: the same data, and the mockup's board logic
    # copied over, so the two never disagree on how a fold is shown.
    js_path = HERE.parent / "work" / "data" / "fixtures.js"
    js = splice(js_path.read_text(encoding="utf-8"), "FIXTURES", fixtures)
    js = splice(js, "BOARD", between(mockup, "BOARD").group(2))
    js_path.write_text(js, encoding="utf-8")
    for path in (mockup_path, js_path):
        print(f"wrote {path.relative_to(HERE.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
