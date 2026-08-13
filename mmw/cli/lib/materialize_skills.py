#!/usr/bin/env python3
"""把共享 skill 中的宿主动作整块物化成 Pi、Claude Code、Codex、Cursor 或 Grok 版本。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
CODEX_ROOT = PLUGIN_ROOT / "codex"
sys.path.insert(0, str(CODEX_ROOT))
from config import CodexConfigError, load_profiles as load_codex_profiles  # noqa: E402

SKILLS_SRC = PLUGIN_ROOT / "skills-src"
ROLES_PATH = PLUGIN_ROOT / "agent-src" / "roles.json"
DEFAULT_OUT = {
    "pi": PLUGIN_ROOT / "skills-pi",
    "claude-code": PLUGIN_ROOT / "skills-claude-code",
    "codex": PLUGIN_ROOT / "skills-codex",
    "grok": PLUGIN_ROOT / "skills-grok",
    "cursor": PLUGIN_ROOT / "skills-cursor",
}
PI_PROMPTS_OUT = PLUGIN_ROOT / "prompts-pi"

LAUNCH_RE = re.compile(
    r"\[\[mmw-launch:([a-z0-9-]+):(worktree|current|none)\]\]"
)
LAUNCH_GROUP_RE = re.compile(
    r"\[\[mmw-launch-group:([a-z0-9-]+):(worktree|current|none)\]\]"
)
RESUME_RE = re.compile(
    r"\[\[mmw-resume:([a-z0-9-]+):(worktree|current|none)\]\]"
)
ENTER_WORKTREE_RE = re.compile(r"\[\[mmw-enter-worktree\]\]")
# 没有续跑通道的宿主统一给这句退路。静默降级成全新派发会让调用方以为上下文还在，
# 所以退路必须显式写明重派时要带什么材料。
#
# 这里说的是「正文」不是「路径」：task 与报告都不落盘，task 走标准输入，报告走标准
# 输出，主 agent 手上有的就是那两段正文。
#
# 分两段：材料清单两处共用——没有续跑通道的宿主整块用它，有续跑通道的宿主在句柄失效
# 时也退回到它。前缀分开写，不然「这个宿主没有续跑通道」会出现在明明有通道的宿主里。
RESUME_MATERIAL = (
    "按对应的启动动作重派新实例，"
    "task 正文带上原 task 全文、原报告全文和本轮修复指令。"
)
RESUME_FALLBACK = f"这个宿主没有续跑通道：{RESUME_MATERIAL}"
CODEX_SKILL_REF_RE = re.compile(r"`/(mmw-[a-z0-9-]+)`")
SKIP_DIR_NAMES = frozenset({"mmw-dispatching-agents", "mmw-setup"})
POST_LAUNCH_RULE = (
    "派出 subagent 后，主 agent 不得执行与该 subagent task 重叠的 research、实现或审查。"
    "没有明确不重叠的协调工作时，立即等待 subagent 交回报告；"
    "报告交回后只按 `/mmw-verifying-agent-output` 验证关键断言，不重做整个 task。"
)


def die(message: str, code: int = 1) -> NoReturn:
    print(f"mmw skills: {message}", file=sys.stderr)
    raise SystemExit(code)


def load_role_agents() -> dict[str, str]:
    data = json.loads(ROLES_PATH.read_text(encoding="utf-8"))
    roles = data.get("roles") or {}
    agents: dict[str, str] = {}
    for role, metadata in roles.items():
        agent = (metadata or {}).get("agent")
        if not agent:
            die(f"roles.json 角色 {role} 缺 agent")
        agents[str(role)] = str(agent)
    return agents


ENTER_WORKTREE_NEW = (
    "运行 `mmw task new <任务分支名> \"<用户原话>\" --name <工作名> "
    "[--from <父分支或基点 SHA>]`。切换到返回的绝对路径。"
)
ENTER_WORKTREE_CODEX = (
    "这棵树由 Codex App 创建。宿主给出干净的 detached worktree 之后，运行 "
    "`mmw task bind <任务分支名> \"<用户原话>\" --name <工作名> "
    "[--from <父分支或基点 SHA>]`。"
)
ENTER_WORKTREE_CURSOR = (
    "停。请用户在 Agents Window 用 New Worktree 开新会话，树名用任务分支名。"
    "本技能上文点名了父分支时，基点用该父分支。"
    "把已经定下的任务分支名、工作名和用户原话写进请用户开新会话的那句话。"
    "新会话重新调用本技能，按 `detached` 行 bind。"
    "禁止 `mmw task new`。"
    "禁止 `herdr worktree create`。"
)
ENTER_WORKTREE_GROK = (
    "停。请用户用 `grok --worktree=<任务分支名>` 或 `-w` 开新会话。"
    "本技能上文点名了父分支时，启动命令加上 `--worktree-ref=<父分支>`。"
    "把已经定下的任务分支名、工作名和用户原话写进请用户开新会话的那句话。"
    "新会话重新调用本技能，按 `detached` 行 bind。"
    "禁止 `mmw task new`。"
    "禁止 `herdr worktree create`。"
    "禁止 `git worktree add`。"
    "禁止用终端 `cd` 代替把会话放进树。"
)


def expand_enter_worktree(host: str) -> str:
    # 每个有自己建树通道的宿主都要显式一行。兜底只留给 pi 与 claude-code
    # 这类「自己跑 mmw task new」的宿主——让具名宿主掉进兜底，它拿到的是
    # 另一个宿主的建树指令，而且不会报错。
    if host == "codex":
        return ENTER_WORKTREE_CODEX
    if host == "cursor":
        return ENTER_WORKTREE_CURSOR
    if host == "grok":
        return ENTER_WORKTREE_GROK
    return ENTER_WORKTREE_NEW


def expand_pi(role: str, agent: str, cwd_mode: str) -> str:
    if cwd_mode == "worktree":
        return (
            "启动：先运行 `mmw task new <结果分支> \"<目标栏原文>\" --name <工作名> --from <基点 SHA>`，"
            "使用命令返回的 worktree 绝对路径作为 cwd。然后调用原生 `subagent`，"
            f"agent 设为 `{agent}`，task 传四栏表全文，cwd 设为该绝对路径。"
        )
    if cwd_mode == "current":
        return (
            f"启动：调用原生 `subagent`，agent 设为 `{agent}`，task 传四栏表全文，"
            "cwd 设为当前任务 worktree 的绝对路径。"
        )
    return f"启动：调用原生 `subagent`，agent 设为 `{agent}`，task 传四栏表全文。"


def expand_grok(role: str, agent: str, cwd_mode: str) -> str:
    del role
    if cwd_mode == "worktree":
        return (
            "启动：先在当前任务 worktree 运行 `mmw task state`，确认输出以 `bound` 开头。"
            "再运行 `mmw task name` 取得工作名。"
            f"调用原生 subagent，agent 设为 `{agent}`，打开 worktree 隔离。"
            "把四栏 task 作为初始 prompt。"
            "工人先运行 "
            '`mmw task bind <结果分支 slug> "<目标栏原文>" '
            "--name <工作名> --from <基点 SHA>`，再完成工作并提交。"
            "交回结果分支名、HEAD SHA、基点 SHA。"
            "不要 `mmw task new`。"
            "提交前自己跑 `mmw toolchain check --changed-only`。"
        )
    if cwd_mode == "current":
        return (
            "启动：确认 `mmw task state` 以 `bound` 开头。"
            f"调用原生 subagent，agent 设为 `{agent}`，task 传四栏表全文。"
            "该 subagent 使用当前任务 worktree，不创建结果 worktree。"
            "cwd 设为当前任务 worktree 的绝对路径。"
        )
    return (
        f"启动：调用原生 subagent，agent 设为 `{agent}`，"
        "只读角色加上只读能力，task 传四栏表全文。"
        "互不依赖的实例在同一条消息中并行启动。"
    )


def expand_resume_grok() -> str:
    return (
        "恢复：调用原生 subagent，`resume_from` 设为原 subagent id。"
        "顶层 grok 会话则运行 `grok --resume <sessionId>`。"
        f"句柄取不到或命令失败时退回重派：{RESUME_MATERIAL}"
    )


def expand_claude(role: str, agent: str, cwd_mode: str) -> str:
    del agent
    if cwd_mode == "worktree":
        return (
            "启动：先运行 `mmw task new <结果分支> \"<目标栏原文>\" --name <工作名> --from <基点 SHA>`，"
            "使用命令返回的 worktree 绝对路径。后台执行 "
            f"`mmw dispatch {role} --cwd <结果 worktree 绝对路径>`。"
            "把四栏 task 正文作为命令的标准输入。"
            "当前 task 属于 decision ticket 时，加 `--issue <当前 decision ticket 编号>`。"
            "命令返回 `mode: host-tool` 时，使用输出中的 `params` 调用对应宿主工具。"
        )
    cwd = " --cwd <当前任务 worktree 绝对路径>" if cwd_mode == "current" else ""
    return (
        f"启动：后台执行 `mmw dispatch {role}{cwd}`。"
        "把四栏 task 正文作为命令的标准输入。"
        "当前 task 属于 decision ticket 时，加 `--issue <当前 decision ticket 编号>`。"
        "命令返回 `mode: host-tool` 时，使用输出中的 `params` 调用对应宿主工具。"
    )


def expand_cursor(role: str, agent: str, cwd_mode: str) -> str:
    if cwd_mode == "worktree":
        return (
            "启动：先在当前任务 worktree 运行 `mmw task state`，确认输出以 `bound` 开头。"
            "再运行 `mmw task name` 取得工作名。"
            "后台执行 `mmw-cursor-agent --mmw-role "
            f"{role} -p --force --trust --approve-mcps "
            "--worktree <结果分支> --worktree-base <当前任务分支>`。"
            "把四栏 task 正文作为命令的标准输入。"
            "worker 进入结果树后先运行 "
            "`mmw task bind <结果分支> \"<目标栏原文>\" --name <工作名> --from <基点 SHA>`，"
            "然后完成工作并提交。"
            "交回结果分支名、HEAD SHA、基点 SHA。"
        )
    if cwd_mode == "current":
        return (
            "启动：先在当前任务 worktree 运行 `mmw task state`，确认输出以 `bound` 开头。"
            f"调用原生 Task，agent 设为 `{agent}`，prompt 传四栏表全文。"
            "该 subagent 直接使用当前任务 worktree，不创建结果 worktree。"
            "互不依赖的实例在同一条消息中并行启动。"
        )
    return (
        f"启动：调用原生 Task，agent 设为 `{agent}`，prompt 传四栏表全文。"
        "互不依赖的实例在同一条消息中并行启动。"
    )


def expand_codex(role: str, cwd_mode: str, profiles: dict) -> str:
    if cwd_mode in {"none", "current"}:
        profile = (profiles.get("subagents") or {}).get(role)
        if not profile:
            die(f"Codex 没有原生 subagent profile：{role}")
        location = (
            "；该 subagent 直接使用当前任务 worktree，不创建后台 worktree 任务"
            if cwd_mode == "current"
            else ""
        )
        return (
            f"启动：按名称调用 Codex 原生 subagent `{profile['name']}`，task 传四栏表全文"
            f"{location}。互不依赖的实例在同一条消息中并行启动，全部完成后再汇总。"
        )

    profile = (profiles.get("background_roles") or {}).get(role)
    if not profile:
        die(f"Codex 没有后台 worktree profile：{role}")
    method = profile.get("method_skill")
    method_instruction = f"，并在工作前完整读取 `${method}`" if method else ""
    return (
        "启动：先在当前任务 worktree 运行 `mmw task state`，确认输出以 `bound` 开头。"
        "再运行 `mmw task name` 取得工作名。"
        "再用 `list_projects` 取得当前仓库的 projectId，并调用 `create_thread`。"
        "target 使用该 projectId，environment.type 设为 `worktree`，startingState.type 设为 "
        "`branch`，branchName 设为当前已提交的任务分支。"
        f"模型使用 `{profile['model']}`，思考档使用 `{profile['thinking']}`。"
        "任务提示包含四栏 task、完整结果分支名、派发前基点 SHA 和工作名；"
        "结果分支名使用独立的 `codex/<slug>`。后台 agent 先运行 "
        "`mmw task bind <完整结果分支名> <目标栏原文> "
        "--name <工作名> --from <基点 SHA>`"
        f"{method_instruction}，然后完成工作并提交。"
        "后台 agent 交回结果分支名、HEAD SHA、基点 SHA 和验证结果。"
        "`create_thread` 返回 threadId 后用 `wait_threads` 等待；只返回 clientThreadId 时先等 App 完成 "
        "worktree 设置，取得 threadId 后再等待。"
    )


def expand_resume_claude(role: str, cwd_mode: str) -> str:
    if cwd_mode == "worktree":
        cwd = " --cwd <原结果 worktree 绝对路径>"
    elif cwd_mode == "current":
        cwd = " --cwd <当前任务 worktree 绝对路径>"
    else:
        cwd = ""
    return (
        "恢复：后台执行 "
        f"`mmw dispatch {role} --resume <句柄原文>{cwd}`。"
        "把修复 task 正文作为命令的标准输入。"
        "句柄是原派发输出里的 `session:` 或 `handle:` 行原文。"
        "那一行不在手上时，运行 `mmw artifact path scratch --sub dispatch` "
        f"取得派发进度目录，读其中以 `{role}-` 开头的那个 `.session` 文件。"
        "命令返回 `mode: host-tool` 时，使用输出中的 `params` 调用对应宿主工具。"
        f"句柄取不到或命令失败时退回重派：{RESUME_MATERIAL}"
    )


def expand_resume_cursor(role: str, cwd_mode: str) -> str:
    del role, cwd_mode
    return (
        "恢复：后台执行 `mmw-cursor-agent --resume <句柄原文>`。"
        "把修复 task 正文作为命令的标准输入。"
        "句柄是原派发输出里的会话 id。"
        f"句柄取不到或命令失败时退回重派：{RESUME_MATERIAL}"
    )


def expand_reviewers(host: str, role_agents: dict[str, str], profiles: dict) -> str:
    if host == "codex":
        profile = (profiles.get("subagents") or {}).get("reviewer-gpt")
        if not profile:
            die("Codex 缺 reviewer-gpt subagent profile")
        return (
            "Codex 只使用一个审查角色。⓪、①、②、⑤ 每个视角各启动一个 "
            f"Codex 原生 `{profile['name']}` subagent。"
            "每个审查者使用独立上下文，可以与产物作者使用相同模型。"
            "⓪ 也一样：这个宿主换不了模型，只换上下文。"
            "互不依赖的审查任务在同一条消息中并行启动。"
        )
    for role in ("reviewer-gpt", "reviewer-claude"):
        if role not in role_agents:
            die(f"启动组角色不在 roles.json：{role}")
    if host == "pi":
        expand = expand_pi
    elif host == "grok":
        expand = expand_grok
    elif host == "cursor":
        expand = expand_cursor
    else:
        expand = expand_claude
    gpt = expand("reviewer-gpt", role_agents["reviewer-gpt"], "none")
    claude = expand("reviewer-claude", role_agents["reviewer-claude"], "none")
    return (
        "当前宿主使用两个审查角色。⓪ 启动一个 `reviewer-gpt`："
        "共同理解是主 agent 自己问出来的，复核它的审查者必须换一个模型。"
        f"{gpt}① 每个视角启动一个 `reviewer-gpt`。"
        f"{gpt}② 每个视角启动一个 `reviewer-claude`。{claude}"
        "⑤ 每个视角分别启动一个 `reviewer-gpt` 和一个 `reviewer-claude`。"
        "同一视角的两份 findings 并排比较；只由一个审查者报告的条目优先验证，"
        "两个审查者都报告的条目仍需验证出处。每个审查者只收到自己的四栏 task。"
    )


def expand_text(
    text: str,
    host: str,
    role_agents: dict[str, str],
    codex_profiles: dict,
) -> str:
    if host == "pi":
        expand = expand_pi
    elif host == "grok":
        expand = expand_grok
    elif host == "cursor":
        expand = expand_cursor
    else:
        expand = expand_claude

    def launch(match: re.Match[str]) -> str:
        role, cwd_mode = match.group(1), match.group(2)
        if role not in role_agents:
            die(f"占位符角色不在 roles.json：{role}")
        if host == "codex":
            instruction = expand_codex(role, cwd_mode, codex_profiles)
            return f"{instruction}\n\n{POST_LAUNCH_RULE}"
        instruction = expand(role, role_agents[role], cwd_mode)
        if host in {"grok", "cursor"} and cwd_mode == "worktree":
            return f"{instruction}\n\n{POST_LAUNCH_RULE}"
        return instruction

    def launch_group(match: re.Match[str]) -> str:
        group, cwd_mode = match.group(1), match.group(2)
        if group != "reviewers" or cwd_mode != "none":
            die(f"不认识的启动组：{group}:{cwd_mode}")
        instruction = expand_reviewers(host, role_agents, codex_profiles)
        if host == "codex":
            return f"{instruction}\n\n{POST_LAUNCH_RULE}"
        return instruction

    def resume(match: re.Match[str]) -> str:
        role, cwd_mode = match.group(1), match.group(2)
        if role not in role_agents:
            die(f"占位符角色不在 roles.json：{role}")
        # 只有 Claude Code 已验证续跑通道（codex exec resume 与 SendMessage）。
        # Grok 的 resume_from 与 grok --resume 写在展开里。
        # Cursor 的 CLI `--resume` 用于结果 worktree worker；原生 Task 还没有续跑通道。
        # Pi 的原生 subagent 与 Codex App 的 thread 后续消息工具都还没实测，
        # 先物化为显式退路，不做静默降级。
        if host == "claude-code":
            return expand_resume_claude(role, cwd_mode)
        if host == "grok":
            return expand_resume_grok()
        if host == "cursor" and cwd_mode == "worktree":
            return expand_resume_cursor(role, cwd_mode)
        return RESUME_FALLBACK

    text = LAUNCH_RE.sub(launch, text)
    text = LAUNCH_GROUP_RE.sub(launch_group, text)
    text = RESUME_RE.sub(resume, text)
    text = ENTER_WORKTREE_RE.sub(lambda _match: expand_enter_worktree(host), text)
    if host == "codex":
        text = CODEX_SKILL_REF_RE.sub(r"`$mmw:\1`", text)
    return text


def skill_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    return text[4:end] if end >= 0 else ""


def user_only_skill_names() -> set[str]:
    names: set[str] = set()
    for skill_file in SKILLS_SRC.glob("*/SKILL.md"):
        frontmatter = skill_frontmatter(skill_file.read_text(encoding="utf-8"))
        if re.search(r"(?m)^disable-model-invocation:\s*true\s*$", frontmatter):
            names.add(skill_file.parent.name)
    return names


def iter_skill_files(host: str) -> list[Path]:
    files: list[Path] = []
    hidden_from_pi = user_only_skill_names() if host == "pi" else set()
    for path in sorted(SKILLS_SRC.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(SKILLS_SRC)
        if any(part in SKIP_DIR_NAMES for part in rel.parts):
            continue
        if rel.parts[0] in hidden_from_pi:
            continue
        files.append(path)
    return files


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end < 0:
        die("SKILL.md frontmatter 没有结束标记")
    return text[end + 5 :]


def inline_reference_links(text: str, reference_names: set[str]) -> str:
    def replace(match: re.Match[str]) -> str:
        label, target = match.group(1), match.group(2)
        if target == "SKILL.md":
            return f"上文的「{label}」"
        if target in reference_names:
            return f"下文的「{label}」"
        die(f"Pi 用户命令含无法内联的相对链接：{target}")

    return re.sub(r"\[([^\]]+)\]\(([^):#]+\.md)\)", replace, text)


def render_pi_prompt(
    skill_dir: Path,
    role_agents: dict[str, str] | None = None,
    codex_profiles: dict | None = None,
) -> str:
    skill_file = skill_dir / "SKILL.md"
    raw = skill_file.read_text(encoding="utf-8")
    if role_agents is None:
        role_agents = load_role_agents()
    if codex_profiles is None:
        try:
            codex_profiles = load_codex_profiles()
        except CodexConfigError:
            codex_profiles = {}
    frontmatter = skill_frontmatter(raw)
    description_match = re.search(r"(?m)^description:\s*(.+?)\s*$", frontmatter)
    if not description_match:
        die(f"Pi 用户命令缺 description：{skill_file}")
    description = description_match.group(1).strip().strip('"')
    argument_hint_match = re.search(r"(?m)^argument-hint:\s*(.+?)\s*$", frontmatter)
    argument_hint = (
        argument_hint_match.group(1).strip().strip('"')
        if argument_hint_match
        else None
    )
    references = sorted(
        path for path in skill_dir.glob("*.md") if path.name != "SKILL.md"
    )
    reference_names = {path.name for path in references}
    body = strip_frontmatter(raw).replace("$ARGUMENTS", "$@")
    body = expand_text(body, "pi", role_agents, codex_profiles)
    parts = [inline_reference_links(body, reference_names).rstrip()]
    for reference in references:
        text = strip_frontmatter(reference.read_text(encoding="utf-8"))
        text = expand_text(text, "pi", role_agents, codex_profiles)
        text = inline_reference_links(text, reference_names).rstrip()
        parts.append(f"## {reference.name}\n\n{text}")
    rendered = (
        "---\n"
        f"description: {json.dumps(description, ensure_ascii=False)}\n"
        + (
            f"argument-hint: {json.dumps(argument_hint, ensure_ascii=False)}\n"
            if argument_hint is not None
            else ""
        )
        +
        "---\n\n"
        + "\n\n".join(parts)
        + "\n"
    )
    if "[[mmw-" in rendered:
        die(f"{skill_file} 仍有未识别的 MMW 物化标记")
    return rendered


def materialize_pi_prompts(
    role_agents: dict[str, str],
    codex_profiles: dict,
    *,
    check: bool,
) -> int:
    expected = {
        f"{name}.md": render_pi_prompt(
            SKILLS_SRC / name, role_agents, codex_profiles
        )
        for name in sorted(user_only_skill_names())
    }
    if check:
        if not PI_PROMPTS_OUT.is_dir():
            print(f"缺  {PI_PROMPTS_OUT}")
            return 1
        actual = {
            path.name: path.read_text(encoding="utf-8")
            for path in PI_PROMPTS_OUT.glob("*.md")
            if path.is_file()
        }
        drift = 0
        for name in sorted(expected.keys() | actual.keys()):
            if expected.get(name) != actual.get(name):
                print(f"异  {PI_PROMPTS_OUT / name}")
                drift = 1
        return drift

    if PI_PROMPTS_OUT.exists():
        shutil.rmtree(PI_PROMPTS_OUT)
    PI_PROMPTS_OUT.mkdir(parents=True)
    for name, content in expected.items():
        (PI_PROMPTS_OUT / name).write_text(content, encoding="utf-8")
    print(f"物化完成：pi 用户命令 → {PI_PROMPTS_OUT}")
    return 0


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
        for src in iter_skill_files(host):
            rel = src.relative_to(SKILLS_SRC)
            dst = tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            raw = src.read_bytes()
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                dst.write_bytes(raw)
                continue
            if src.suffix.lower() == ".md":
                text = expand_text(text, host, role_agents, codex_profiles)
                if "[[mmw-" in text:
                    die(f"{rel} 仍有未识别的 MMW 物化标记")
            dst.write_text(text, encoding="utf-8")

        if check:
            if not out_root.is_dir():
                print(f"缺  {out_root}")
                return 1
            drift = 0
            expected_files = {p.relative_to(tmp) for p in tmp.rglob("*") if p.is_file()}
            actual_files = {p.relative_to(out_root) for p in out_root.rglob("*") if p.is_file()}
            for rel in sorted(expected_files | actual_files):
                expected = tmp / rel
                actual = out_root / rel
                if rel not in actual_files:
                    print(f"缺  {actual}")
                    drift = 1
                elif rel not in expected_files:
                    print(f"多  {actual}")
                    drift = 1
                elif expected.read_bytes() != actual.read_bytes():
                    print(f"异  {actual}")
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
    parser = argparse.ArgumentParser(description="物化 skill 的宿主动作")
    parser.add_argument(
        "--host",
        required=True,
        choices=("pi", "claude-code", "codex", "cursor", "grok", "all"),
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    role_agents = load_role_agents()
    try:
        codex_profiles = load_codex_profiles()
    except CodexConfigError as exc:
        die(str(exc))
    hosts = (
        ["pi", "claude-code", "codex", "cursor", "grok"] if args.host == "all" else [args.host]
    )
    status = 0
    for host in hosts:
        out = args.out if args.out and args.host != "all" else DEFAULT_OUT[host]
        status |= materialize_host(
            host, out, role_agents, codex_profiles, check=args.check
        )
        if host == "pi" and args.out is None:
            status |= materialize_pi_prompts(
                role_agents, codex_profiles, check=args.check
            )
    return status


if __name__ == "__main__":
    raise SystemExit(main())
