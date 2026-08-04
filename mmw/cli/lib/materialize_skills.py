#!/usr/bin/env python3
"""把技能源里的启动占位符物化成宿主写死的启动句。

源：mmw/skills/（可含 [[mmw-launch:角色:cwd模式]]）
物化：
  --host pi           → mmw/skills-pi/
  --host claude-code  → mmw/skills-claude-code/
  --host codex        → mmw/skills-codex/
  --host all          → 三者都写

cwd 模式：worktree | none
不物化 mmw-dispatching-agents（已废除，由安装面写死启动句）。

用法：
  materialize_skills.py --host pi|claude-code|codex|all [--check] [--out <dir>]
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SKILLS_SRC = PLUGIN_ROOT / "skills"
ROLES_PATH = PLUGIN_ROOT / "agent-src" / "roles.json"
DEFAULT_OUT = {
    "pi": PLUGIN_ROOT / "skills-pi",
    "claude-code": PLUGIN_ROOT / "skills-claude-code",
    "codex": PLUGIN_ROOT / "skills-codex",
}
CODEX_PROFILES_PATH = PLUGIN_ROOT / "codex" / "profiles.json"

# [[mmw-launch:worker:worktree]] 或 [[mmw-launch:investigator:none]]
LAUNCH_RE = re.compile(
    r"\[\[mmw-launch:([a-z0-9-]+):(worktree|none)\]\]"
)
LAUNCH_GROUP_RE = re.compile(
    r"\[\[mmw-launch-group:([a-z0-9-]+):(worktree|none)\]\]"
)
CODEX_SKILL_REF_RE = re.compile(r"`/(mmw-[a-z0-9-]+)`")

SKIP_DIR_NAMES = frozenset(
    {
        "mmw-dispatching-agents",
        "mmw-setup",  # 旧背景，不进发布面
    }
)


def die(msg: str, code: int = 1) -> NoReturn:
    print(f"mmw skills: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_role_agents() -> dict[str, str]:
    import json

    data = json.loads(ROLES_PATH.read_text(encoding="utf-8"))
    roles = data.get("roles") or {}
    out: dict[str, str] = {}
    for name, meta in roles.items():
        agent = (meta or {}).get("agent")
        if not agent:
            die(f"roles.json 角色 {name} 缺 agent")
        out[str(name)] = str(agent)
    return out


def load_codex_profiles() -> dict:
    import json

    try:
        data = json.loads(CODEX_PROFILES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"读不到 Codex profile：{exc}")
    text = json.dumps(data, ensure_ascii=False).lower()
    for banned in ('"family"', '"provider"', "claude", "grok"):
        if banned in text:
            die(f"Codex profile 不得包含 {banned}")
    return data


def expand_pi(role: str, agent: str, cwd_mode: str) -> str:
    if cwd_mode == "worktree":
        return (
            f"启动：`subagent({{ agent: \"{agent}\", task: <四栏表全文>, "
            f"cwd: <worktree 绝对路径> }})`"
            f"（可写；先确认该 worktree 上 `git status --porcelain` 为空）。"
        )
    return (
        f"启动：`subagent({{ agent: \"{agent}\", task: <四栏表全文> }})`"
        f"（只读）。"
    )


def expand_claude(role: str, agent: str, cwd_mode: str) -> str:
    del agent  # Claude dispatch 用角色名，不用 mmw-* 文件名
    if cwd_mode == "worktree":
        return (
            f"启动：四栏表写入 task 文件后，Bash（`run_in_background: true`）执行 "
            f"`mmw dispatch {role} --task <task 文件绝对路径> --cwd <worktree 绝对路径>`；"
            f"回执 `mode: host-tool` 时原样传入 `params` 调用对应工具（params 已含 task 正文）。"
        )
    return (
        f"启动：四栏表写入 task 文件后，Bash（`run_in_background: true`）执行 "
        f"`mmw dispatch {role} --task <task 文件绝对路径>`；"
        f"回执 `mode: host-tool` 时原样传入 `params` 调用对应工具（params 已含 task 正文）。"
    )


def expand_codex(role: str, cwd_mode: str, profiles: dict) -> str:
    if cwd_mode == "none":
        profile = (profiles.get("subagents") or {}).get(role)
        if not profile:
            die(f"Codex 没有只读 subagent profile：{role}")
        return (
            "启动：调用 Codex 原生 subagent，"
            f"agent 设为 `{profile['name']}`，task 传四栏表全文；"
            "同一批独立角度在一条消息中并行启动，全部完成后再汇总。"
        )

    profile = (profiles.get("background_roles") or {}).get(role)
    if not profile:
        die(f"Codex 没有后台 worktree profile：{role}")
    method = profile["method_skill"]
    return (
        "启动：先调用 `list_projects` 取得当前仓库的 projectId，再调用 `create_thread`；"
        "target 使用该 projectId，environment.type 设为 `worktree`，"
        "startingState.type 设为 `branch`，branchName 设为当前已提交的任务分支。"
        f"模型设为 `{profile['model']}`，思考档设为 `{profile['thinking']}`。"
        "把四栏 task 全文作为任务提示，并要求后台任务先用 "
        "`$mmw:mmw-start` 的绑定脚本创建独立 `codex/<slug>` 分支，"
        f"再完整读取 `${method}` 后工作。"
        "后台任务必须提交改动，并交回分支名、HEAD SHA 与测试结果；"
        "`create_thread` 交回 threadId 后，主 agent 用 `wait_threads` 等它完成。"
        "如果只交回 clientThreadId，先等 App 完成 worktree 设置，不能把 clientThreadId 传给 `wait_threads`。"
    )


def replace_exact(text: str, old: str, new: str, *, rel: Path) -> str:
    if old not in text:
        die(f"Codex override 已漂移：{rel} 找不到预期文本 {old[:40]!r}")
    return text.replace(old, new)


def replace_section(
    text: str,
    start: str,
    end: str,
    replacement: str,
    *,
    rel: Path,
) -> str:
    start_at = text.find(start)
    end_at = text.find(end, start_at + len(start)) if start_at >= 0 else -1
    if start_at < 0 or end_at < 0:
        die(f"Codex override 已漂移：{rel} 找不到 {start!r} 到 {end!r}")
    return text[:start_at] + replacement.rstrip() + "\n\n" + text[end_at:]


def apply_codex_overrides(rel: Path, text: str) -> str:
    """清除 Codex 产物中的旧宿主 worktree 与跨模型合同。"""
    if rel == Path("mmw-start/SKILL.md"):
        text = replace_section(
            text,
            "## 3. 建 worktree、进去、记原话",
            "## 下一步",
            """## 3. 绑定 Codex App 已创建的 worktree

Codex App 在任务创建时已经固定当前 worktree。确认任务范围之前只读，不建分支、不改文件。

任务范围确认后，先确认当前 checkout 满足三条：它是 linked worktree；`HEAD` 是 detached；`git status --porcelain` 为空。然后运行与本 `SKILL.md` 同目录的 `scripts/bind-current-worktree.sh`：

```bash
bash <本技能目录>/scripts/bind-current-worktree.sh "codex/<slug>" "<用户交代这件事时的原话>"
```

脚本只在干净的 detached worktree 上创建分支，并用空提交保存用户原话。分支已经存在、当前 checkout 不是 detached、工作区不干净时，脚本必须失败。

从 map 派生的任务必须在创建 Codex App 任务时把 `startingState` 选为 map 分支。当前 `HEAD` 不包含 map 分支提交时停下，不能在已经创建的 worktree 里改基点。

当前任务不是 Codex App worktree 时停下，让用户新建 Worktree 任务。主 agent 不创建替代目录，也不切换当前任务的工作根目录。
""",
            rel=rel,
        )

    if rel == Path("mmw-start/resuming.md"):
        text = replace_exact(
            text,
            "`.worktrees/` 下的每一棵都是一个进行中的任务，目录名就是它的 slug。只有一棵就直接查它；有好几棵就把清单连同各自的进度报出来，让用户挑。",
            "以 `git worktree list --porcelain` 和 Codex App 任务列表为准。分支名 `codex/<slug>` 给出任务 slug；detached 的 Codex worktree 还没有绑定，先报告该状态，不替用户猜 slug。",
            rel=rel,
        )
        text = text.replace(
            "`.worktrees/` 下以这个 slug 开头、但不等于这个 slug 的目录，每一棵是一条链",
            "Codex App 中从该任务分支创建的后台 Worktree 任务；每个任务的结果分支是一条链",
        )
        text = text.replace(
            "用户报的 slug 在 `.worktrees/` 下找不到",
            "用户报的 `codex/<slug>` 分支和对应 Codex App 任务都找不到",
        )

    worktree_checks = {
        Path("mmw-implement/SKILL.md"): (
            "`git rev-parse --show-toplevel` 以 `.worktrees/<slug>` 结尾",
            "当前 checkout 是已绑定 `codex/<slug>` 分支的 linked worktree",
            "`mmw task new <slug>` 建一个，或 `mmw task enter <slug>` 取路径再进去",
            "停下，让用户新建 Codex App Worktree 任务，确认范围后用 `$mmw:mmw-start` 绑定分支",
        ),
        Path("mmw-to-plan/SKILL.md"): (
            "`git rev-parse --show-toplevel` 以 `.worktrees/<slug>` 结尾；不在就 `mmw task new <slug>` 建一个，或 `mmw task enter <slug>` 取路径再进去",
            "当前 checkout 是已绑定 `codex/<slug>` 分支的 linked worktree；不满足就停下，让用户新建 Codex App Worktree 任务并用 `$mmw:mmw-start` 绑定分支",
            "",
            "",
        ),
        Path("mmw-closing/SKILL.md"): (
            "`git rev-parse --show-toplevel` 以 `.worktrees/<slug>` 结尾",
            "当前 checkout 是已绑定 `codex/<slug>` 分支的 linked worktree",
            "",
            "",
        ),
    }
    if rel in worktree_checks:
        old, new, old2, new2 = worktree_checks[rel]
        text = replace_exact(text, old, new, rel=rel)
        if old2:
            text = replace_exact(text, old2, new2, rel=rel)

    if rel == Path("mmw-implement/SKILL.md"):
        text = replace_exact(
            text,
            "一个 worktree 一次做一张 ticket，一个 worktree 上只站一个 `worker`。frontier 确实很宽、用户又要并行推进，就给每张 ticket 各跑一次 `mmw task new <slug>-<ticket 短语>`，它们都从你当前这条分支分叉。",
            "一个后台 Worktree 任务一次只做一张 ticket。frontier 确实很宽、用户又明确要求并行推进时，每张 ticket 各创建一个 Codex App 后台 Worktree 任务，`startingState` 都设为当前已提交的任务分支。",
            rel=rel,
        )

    if rel == Path("mmw-to-plan/SKILL.md"):
        text = replace_exact(
            text,
            "互不依赖的 plan：同一条消息里并行启动多个 `planner`。有依赖链：按依赖顺序启动。不开子 worktree；`planner` 不提交；各 plan 写不同文件，同在任务 worktree 内。",
            "互不依赖的 plan：同一条消息里创建多个 Codex App 后台 Worktree 任务。有依赖链：按依赖顺序创建。每个 `planner` 只写自己的 plan、提交自己的分支并交回分支名与 HEAD SHA；主 agent 逐个验证后用 `$mmw:mmw-integrate` 合入当前任务分支。",
            rel=rel,
        )
        text = text.replace("`planner` 不提交，改动一直是未暂存的，由你统一收。", "每个 `planner` 在自己的结果分支提交；主 agent 验证并合入后，再分别提交 plan 文档与合同回填。")

    simple_replacements: dict[Path, list[tuple[str, str]]] = {
        Path("mmw-improve-codebase-architecture/SKILL.md"): [
            (
                "挑中了就定 slug，跑 `mmw task new <slug> \"<原话加这张卡片的标题>\"`，再用宿主的工作目录切换工具进到它输出的那个路径（Claude Code 是 `EnterWorktree`，pi 是 `enter_worktree`；这一步脚本做不了，只有宿主工具做得到）。",
                "挑中了就定 slug。当前任务已经是 Codex App worktree 时，用 `$mmw:mmw-start` 的绑定脚本创建 `codex/<slug>` 分支；当前任务不是 worktree 时停下，让用户新建 Codex App Worktree 任务。",
            )
        ],
        Path("mmw-prototype/SKILL.md"): [
            (
                "还在主仓库里、没有任务 worktree 的，先 `mmw task new <slug> \"<原话>\"` 建一棵，用宿主的工作目录切换工具进到它输出的那个路径（Claude Code 是 `EnterWorktree`，pi 是 `enter_worktree`；这一步脚本做不了，只有宿主工具做得到），再动手。",
                "当前任务不是 Codex App worktree 时停下，让用户新建 Worktree 任务；当前任务是尚未绑定的 detached worktree 时，先用 `$mmw:mmw-start` 的绑定脚本创建 `codex/<slug>` 分支，再动手。",
            )
        ],
        Path("mmw-diagnosing-bugs/fixing.md"): [
            (
                "合并和清理 worktree 由用户批准，他批准后清理跑 `mmw task cleanup <slug>`",
                "合并由用户批准；结果提交已绑定分支后，用户可以在 Codex App 归档任务，由 App 管理 worktree 清理",
            )
        ],
        Path("mmw-integrate/SKILL.md"): [
            (
                "**集成在主仓库的主线上做，不建 worktree。** 各条分支的 worktree 留着，集成完了再由用户清理。当前不在主线上就停下——切分支归用户。",
                "**集成在本轮指定的目标分支上做。** 合入后台任务结果时，目标分支就是当前 Codex App 任务分支。各结果任务的 worktree 留到分支与提交验证完成；当前分支不是本轮目标分支时停下。",
            ),
            (
                "worktree 的清理由用户批准，他批准后跑 `mmw task cleanup <slug>`",
                "结果提交已绑定分支后，用户可以归档对应 Codex App 任务，由 App 管理 worktree 清理",
            ),
            ("当前不在主线上", "当前不在本轮目标分支"),
        ],
    }
    for old, new in simple_replacements.get(rel, []):
        text = replace_exact(text, old, new, rel=rel)

    if rel == Path("mmw-integrate/SKILL.md"):
        text = replace_exact(
            text,
            "按第 2 步定的顺序，一条一条来。",
            "后台 Worktree 任务交回后，先运行与本 `SKILL.md` 同目录的 `scripts/verify-worker-result.sh <结果分支> <报告的 HEAD SHA> <派发前基点 SHA>`；验证通过后再按第 2 步定的顺序，一条一条来。",
            rel=rel,
        )

    if rel == Path("mmw-review/SKILL.md"):
        for old, new in (
            ("两个视角都派另一个模型", "两个视角各派一个独立审查者"),
            ("每个视角各派两个模型", "每个视角各派两个独立审查者实例"),
            ("两个模型各派一个，各走全套", "派两个独立审查者实例，各走全套"),
        ):
            text = text.replace(old, new)
        text = replace_section(
            text,
            "**红线是每一道审至少有一个视角的审查者跟作者不是同一个模型。**",
            "## 1. 确定被审的东西",
            """Codex 只使用内置 GPT 模型。审查独立性由干净的 subagent 上下文、只读 sandbox、固定审查视角和主 agent 验证保证，不按模型供应商分角色。

①、② 每个视角派一个 `mmw-reviewer`。⑤ 每个视角派两个独立 `mmw-reviewer` 实例。⑥ 派两个独立 `mmw-reviewer` 实例，各走全套七角度。
""",
            rel=rel,
        )
        replacements = (
            ("每个（视角 × 角色）一份。", "每个审查者实例一份。"),
            ("；`mmw skill-path <角色>` 有输出则加方法论路径", "；方法论由 `mmw-reviewer` agent 自动读取，不在 task 里重复"),
            ("**同一视角两个角色：** 四栏表内容相同；仅「读」中方法论路径可因角色而变。", "**同一视角两个实例：** 四栏表内容相同，两个实例保持独立上下文。"),
            ("角色只能是 `reviewer-gpt` 与/或 `reviewer-claude`（角色取自本文「六道审」下「这一道审的东西谁写的 → 派哪个角色」表）。", "agent 只能是原生只读 subagent `mmw-reviewer`。"),
            ("每个（视角 × 角色）各写一张四栏表并启动一次", "每个审查者实例各写一张四栏表并启动一次"),
            ("**同一个视角两个模型都派了的，把两个模型的 findings 并排对**：只有一个模型报出来的重点验证，两个模型同报的可信度高。", "**同一个视角派了两个实例的，把两份 findings 并排对**：只有一个实例报出来的重点验证，两个实例同报的可信度较高。"),
        )
        for old, new in replacements:
            text = replace_exact(text, old, new, rel=rel)

    if rel == Path("mmw-to-spec/SKILL.md"):
        text = replace_exact(
            text,
            "两个视角都来自另一个模型。",
            "两个视角分别使用独立的 `mmw-reviewer` subagent 上下文。",
            rel=rel,
        )

    for old in (
        "可选：四栏表写入 `.dispatch/<slug>-<ticket>.prompt.md`。",
        "可选：四栏表写入 `.dispatch/<slug>-research-<角度短名>.prompt.md`。",
        "可选：四栏表写入 `.dispatch/<slug>-plan-<编号>.prompt.md`。",
    ):
        text = text.replace(old, "")
    text = text.replace(
        "`.reviews/` 和 `.dispatch/` 随 worktree 存活，不进 git。",
        "`.reviews/` 随 worktree 存活，不进 git。",
    )

    if rel == Path("mmw-wayfinder/SKILL.md"):
        text = replace_exact(
            text,
            "**一个会话只进一次 worktree。** 认领一条链和收尾这两个入口，会话先在主仓库里读 map（`gh issue view`）和 map 分支上的文件（`git show <map 分支>:<路径>`），选定这次要做什么，再建自己那棵 worktree 并进去。建这张 map 那个入口没有 map 可读，`$mmw:mmw-start` 已经替它建好 map 的 worktree 并进去了，它不再建第二棵。从一棵 worktree 直接跳到另一棵会被拒绝；需要动别的 worktree 时用 `git -C <那棵 worktree 的路径> <git 命令>`，不切会话目录。",
            "**一个 Codex App 任务只使用创建时分配的一个 worktree。** map、每条链和每份 spec 各用独立 Worktree 任务。新任务创建时选择正确的父分支作为 `startingState`，进入后用 `$mmw:mmw-start` 的绑定脚本创建自己的 `codex/<slug>` 分支。任务不能切换到别的 worktree；跨任务结果只通过已验证的分支和 commit 交接。",
            rel=rel,
        )

    if rel == Path("mmw-wayfinder/walking.md"):
        text = text.replace("## 1. 在主仓库里读", "## 1. 在当前任务里只读")
        text = replace_section(
            text,
            "## 2. 挑一张，认领，建这条链的 worktree",
            "## 3. 解它",
            """## 2. 挑一张，认领，绑定这条链的任务分支

用户点了名就用他点的那张，没点就取 frontier 上的第一张。

**先认领**：`mmw issue claim <编号>`。它已经被别的任务占住就会失败，那就取下一张。认领成功之前不要做任何事。

一条链必须运行在独立的 Codex App Worktree 任务中。创建任务时把 `startingState` 设为 map 分支，并在任务提示里写明 map、链首 ticket 和四栏 task。当前任务不是从 map 分支创建的独立 worktree 时停下，让用户新建对应任务。

进入 detached worktree 后，运行 `$mmw:mmw-start` 的绑定脚本，创建 `codex/<map-slug>-<链首-ticket-短语>` 分支。脚本保存用户原话；当前任务不得再创建或切换 worktree。
""",
            rel=rel,
        )
        text = replace_section(
            text,
            "## 7. 这条链走完之后",
            "## 下一步",
            """## 7. 这条链走完之后

1. 这条链写的每一份 `draft-<ticket 编号>-<kebab-标题>.md` 逐个改成正式编号并提交。
2. 确认工作区干净，交回结果分支名、HEAD SHA、创建任务时的 map 分支基点 SHA 和 frontier 状态。
3. map 的主任务用 `$mmw:mmw-integrate` 中的结果验证脚本检查分支、HEAD SHA 与基点，再用 `git merge --no-ff` 合回 map 分支。链任务不直接进入 map 的 worktree。
""",
            rel=rel,
        )

    if rel == Path("mmw-wayfinder/closing.md"):
        text = replace_exact(
            text,
            "- **刚解完最后一条链**，这个会话还在那条链的 worktree 里。就地做，收尾写的文件跟着这条链的分支一起合回 map 分支。\n- **新会话进来发现 frontier 空了**，这个会话还在主仓库。用宿主的工作目录切换工具（Claude Code 是 `EnterWorktree`，pi 是 `enter_worktree`）进 map 的 worktree 做。map 的 worktree 不在就先 `mmw task new <map 的 slug>` 建回来——分支还在时它挂回那条分支，不新建也不打空提交。",
            "- **刚解完最后一条链**：在链任务中完成收尾并提交，交回结果分支与 HEAD SHA；map 主任务验证后合入。\n- **新任务进来发现 frontier 空了**：该 Codex App Worktree 任务必须从 map 分支创建，进入后用 `$mmw:mmw-start` 绑定独立收尾分支。基点不对时停下，让用户从 map 分支新建任务。",
            rel=rel,
        )
        text = replace_exact(
            text,
            "每份 spec 的 worktree 从 map 分支分叉（`mmw task new <spec 的 slug> \"<原话>\" --from <map 的 slug>`），做完合回 map 分支。**整个 effort 收尾之前不合回主线**——map 分支才是这几份 spec 的汇合点。",
            "每份 spec 各建一个 Codex App Worktree 任务，`startingState` 设为 map 分支，进入后绑定独立 `codex/<spec-slug>` 分支；做完后由 map 主任务验证结果分支与 SHA，再用 `git merge --no-ff` 合回 map 分支。**整个 effort 收尾之前不合回主线**——map 分支是这些 spec 的汇合点。",
            rel=rel,
        )

    return text


def expand_text(
    text: str,
    rel: Path,
    host: str,
    role_agents: dict[str, str],
    codex_profiles: dict,
) -> str:
    expand = expand_pi if host == "pi" else expand_claude

    def repl(match: re.Match[str]) -> str:
        role, cwd_mode = match.group(1), match.group(2)
        if role not in role_agents:
            die(f"占位符角色不在 roles.json：{role}")
        if host == "codex":
            return expand_codex(role, cwd_mode, codex_profiles)
        return expand(role, role_agents[role], cwd_mode)

    def repl_group(match: re.Match[str]) -> str:
        group, cwd_mode = match.group(1), match.group(2)
        if group != "reviewers" or cwd_mode != "none":
            die(f"不认识的启动组：{group}:{cwd_mode}")
        if host == "codex":
            profile = (codex_profiles.get("subagents") or {}).get("reviewer")
            if not profile:
                die("Codex 缺 reviewer subagent profile")
            return (
                "每个审查视角分别启动一个 Codex 原生 subagent，"
                f"agent 都设为 `{profile['name']}`，task 传该视角的四栏表全文；"
                "各实例使用相同 GPT profile 和不同审查角度，在一条消息中并行启动。"
            )
        lines = []
        for role in ("reviewer-gpt", "reviewer-claude"):
            if role not in role_agents:
                die(f"启动组角色不在 roles.json：{role}")
            lines.append(f"`{role}`：{expand(role, role_agents[role], cwd_mode)}")
        return "\n".join(lines)

    text = LAUNCH_RE.sub(repl, text)
    text = LAUNCH_GROUP_RE.sub(repl_group, text)
    if host == "codex":
        text = CODEX_SKILL_REF_RE.sub(r"`$mmw:\1`", text)
        text = apply_codex_overrides(rel, text)
    return text


def iter_skill_files(src_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(src_root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(src_root).parts
        if any(part in SKIP_DIR_NAMES for part in rel_parts):
            continue
        if path.suffix.lower() not in {".md", ".sh", ".json", ".txt"}:
            # 仍复制其它文件
            pass
        files.append(path)
    return files


def materialize_host(
    host: str,
    out_root: Path,
    role_agents: dict[str, str],
    codex_profiles: dict,
    *,
    check: bool,
) -> int:
    if not SKILLS_SRC.is_dir():
        die(f"找不到技能源 {SKILLS_SRC}")

    tmp = Path(tempfile.mkdtemp(prefix=f"mmw-skills-{host}-"))
    try:
        for src in iter_skill_files(SKILLS_SRC):
            rel = src.relative_to(SKILLS_SRC)
            dst = tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            raw = src.read_bytes()
            # 文本才替换
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                dst.write_bytes(raw)
                continue
            if src.suffix.lower() == ".md":
                text = expand_text(text, rel, host, role_agents, codex_profiles)
                if "[[mmw-launch:" in text:
                    die(f"{rel} 仍有未识别的 mmw-launch 占位符")
            dst.write_text(text, encoding="utf-8")

        if check:
            if not out_root.is_dir():
                print(f"缺  {out_root}")
                return 1
            drift = 0
            expected_files = set()
            for path in sorted(tmp.rglob("*")):
                if not path.is_file():
                    continue
                rel = path.relative_to(tmp)
                expected_files.add(rel)
                target = out_root / rel
                if not target.is_file():
                    print(f"缺  {target}")
                    drift = 1
                    continue
                if path.read_bytes() != target.read_bytes():
                    print(f"异  {target}")
                    drift = 1
            # 反向：输出树多出来的文件也算漂移
            for path in sorted(out_root.rglob("*")):
                if not path.is_file():
                    continue
                rel = path.relative_to(out_root)
                if rel not in expected_files:
                    print(f"多  {out_root / rel}")
                    drift = 1
            banned = out_root / "mmw-dispatching-agents"
            if banned.exists():
                print(f"禁  不应存在 {banned}")
                drift = 1
            return drift

        if out_root.exists():
            shutil.rmtree(out_root)
        shutil.copytree(tmp, out_root)
        print(f"物化完成：{host} → {out_root}")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="物化技能启动句")
    parser.add_argument(
        "--host", required=True, choices=("pi", "claude-code", "codex", "all")
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--out", type=Path, default=None, help="覆盖默认输出目录")
    args = parser.parse_args(argv)

    role_agents = load_role_agents()
    codex_profiles = load_codex_profiles()
    hosts = ["pi", "claude-code", "codex"] if args.host == "all" else [args.host]
    status = 0
    for host in hosts:
        out = args.out if args.out and args.host != "all" else DEFAULT_OUT[host]
        status |= materialize_host(
            host, out, role_agents, codex_profiles, check=args.check
        )
    return status


if __name__ == "__main__":
    raise SystemExit(main())
