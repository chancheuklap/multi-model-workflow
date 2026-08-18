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
REQUIRE_TASK_BRANCH_RE = re.compile(r"\[\[mmw-require-task-branch\]\]")
# 任务树由用户开。agent 只在已有的树上创建任务分支。各宿主正文相同：用户怎么开树
# 由宿主自己的界面负责，技能不替用户建任务树。
REQUIRE_TASK_BRANCH = (
    "Confirm where this repo is first. Judge top to bottom; stop at the first row that hits.\n"
    "\n"
    "| Case | How to tell | What you do |\n"
    "| --- | --- | --- |\n"
    "| Not in a git repo | `git rev-parse --is-inside-work-tree` fails | "
    "Ask the user for the target repo path. Enter that repo, then judge again |\n"
    "| In the main checkout | `git rev-parse --path-format=absolute --git-dir` equals "
    "`--git-common-dir` | Stop. Ask the user to open a worktree with this host, "
    "then start a session there |\n"
    "| No branch | `git symbolic-ref --quiet --short HEAD` is empty | "
    "Run `git switch -c <full task-branch name>` with the task-branch name decided above |\n"
    "| Task branch already there | None of the above holds | Use the current branch |\n"
)
# 没有续跑通道的宿主统一给这句退路。静默降级成全新派发会让调用方以为上下文还在，
# 所以退路必须显式写明重派时要带什么材料。
#
# 这里说的是「正文」不是「路径」：task 与报告都不落盘，task 走标准输入，报告走标准
# 输出，主 agent 手上有的就是那两段正文。
#
# 分两段：材料清单两处共用——没有续跑通道的宿主整块用它，有续跑通道的宿主在句柄失效
# 时也退回到它。前缀分开写，不然「这个宿主没有续跑通道」会出现在明明有通道的宿主里。
RESUME_MATERIAL = (
    "re-dispatch a new instance with the matching launch action, and let the task body "
    "carry the original task in full, the original report in full, and this round's "
    "repair instruction."
)
RESUME_FALLBACK = f"This host has no resume channel: {RESUME_MATERIAL}"
CODEX_SKILL_REF_RE = re.compile(r"`/(mmw-[a-z0-9-]+)`")
SKIP_DIR_NAMES = frozenset({"mmw-setup"})
# 只有 Codex 拿这条。别的宿主的主 agent 派完就等，Codex 的会自己把 subagent 的活再干
# 一遍（引入它的那次修的就是这个）。其他宿主没有这个行为时不发这条规则：一条没有对应
# 失败模式的禁令，只会把被禁的动作带进上下文。哪个宿主真出现同样的重做，再按证据加。
POST_LAUNCH_RULE = (
    "After dispatching a subagent, the main agent does not run research, implementation, "
    "or review that overlaps that subagent's task. With no clearly non-overlapping "
    "coordination work in hand, wait for the report. Do not redo the whole task once it arrives."
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


def expand_require_task_branch(host: str) -> str:
    if host in ("pi", "claude-code", "codex", "cursor", "grok"):
        return REQUIRE_TASK_BRANCH
    die(f"未支持的宿主 {host}")


def expand_pi(role: str, agent: str, cwd_mode: str) -> str:
    if cwd_mode == "worktree":
        return (
            "Launch: run `mmw worktree add <result branch>` first and use the worktree "
            "absolute path it returns as cwd. Then call the native `subagent` tool with "
            f"agent `{agent}`, the four-field task table in full as task, and cwd set to "
            "that absolute path."
        )
    if cwd_mode == "current":
        return (
            f"Launch: call the native `subagent` tool with agent `{agent}`, the four-field "
            "task table in full as task, and cwd set to the absolute path of the current "
            "worktree. That subagent uses the current worktree; it does not open a result tree."
        )
    return (
        f"Launch: call the native `subagent` tool with agent `{agent}` and the four-field "
        "task table in full as task."
    )


def expand_grok(role: str, agent: str, cwd_mode: str) -> str:
    del role
    if cwd_mode == "worktree":
        return (
            f"Launch: call the native subagent tool with agent `{agent}` and worktree "
            "isolation on. Pass the four-field task as the initial prompt. "
            "The worker completes the work and commits. "
            "It returns the result-branch name, the HEAD SHA, and the base SHA. "
            "It runs `mmw toolchain check --changed-only` itself before committing."
        )
    if cwd_mode == "current":
        return (
            f"Launch: call the native subagent tool with agent `{agent}` and the four-field "
            "task table in full as task. "
            "That subagent uses the current worktree; it does not open a result tree. "
            "Set cwd to the absolute path of the current worktree."
        )
    return (
        f"Launch: call the native subagent tool with agent `{agent}`, "
        "read-only capability for a read-only role, and the four-field task table in full as task. "
        "Instances that do not depend on each other launch in the same message."
    )


def expand_resume_grok() -> str:
    return (
        "Resume: call the native subagent tool with `resume_from` set to the original "
        "subagent id. For a top-level grok session, run `grok --resume <sessionId>` instead. "
        f"If the handle cannot be found or the command fails, {RESUME_MATERIAL}"
    )


def expand_claude(role: str, agent: str, cwd_mode: str) -> str:
    del agent
    if cwd_mode == "worktree":
        return (
            "Launch: run `mmw worktree add <result branch>` first and use the worktree "
            "absolute path it returns. In the background, run "
            f"`mmw dispatch {role} --cwd <result worktree absolute path>`. "
            "Pass the four-field task body as the command's standard input. "
            "Add `--issue <current decision ticket number>` when this task belongs to a "
            "decision ticket. "
            "When the command returns `mode: host-tool`, call the matching host tool with "
            "the `params` in its output."
        )
    cwd = " --cwd <current worktree absolute path>" if cwd_mode == "current" else ""
    return (
        f"Launch: in the background, run `mmw dispatch {role}{cwd}`. "
        "Pass the four-field task body as the command's standard input. "
        "Add `--issue <current decision ticket number>` when this task belongs to a "
        "decision ticket. "
        "When the command returns `mode: host-tool`, call the matching host tool with "
        "the `params` in its output."
    )


def expand_cursor(role: str, agent: str, cwd_mode: str) -> str:
    if cwd_mode == "worktree":
        return (
            "Launch: in the background, run `mmw-cursor-agent --mmw-role "
            f"{role} -p --force --trust --approve-mcps "
            "--worktree <result branch> --worktree-base <current task branch>`. "
            "Pass the four-field task body as the command's standard input. "
            "The worker enters the result tree, completes the work, and commits. "
            "It returns the result-branch name, the HEAD SHA, and the base SHA."
        )
    if cwd_mode == "current":
        return (
            f"Launch: call the native Task tool with agent `{agent}` and the four-field "
            "task table in full as prompt. "
            "That subagent uses the current worktree; it does not open a result tree. "
            "Instances that do not depend on each other launch in the same message."
        )
    return (
        f"Launch: call the native Task tool with agent `{agent}` and the four-field "
        "task table in full as prompt. "
        "Instances that do not depend on each other launch in the same message."
    )


def expand_codex(role: str, cwd_mode: str, profiles: dict) -> str:
    if cwd_mode in {"none", "current"}:
        profile = (profiles.get("subagents") or {}).get(role)
        if not profile:
            die(f"Codex 没有原生 subagent profile：{role}")
        location = (
            "; that subagent uses the current worktree and does not open a result tree"
            if cwd_mode == "current"
            else ""
        )
        return (
            f"Launch: call the Codex native subagent `{profile['name']}` by name, with the "
            f"four-field task table in full as task{location}. Instances that do not depend "
            "on each other launch in the same message; summarize after all of them finish."
        )

    profile = (profiles.get("background_roles") or {}).get(role)
    if not profile:
        die(f"Codex 没有后台 worktree profile：{role}")
    method = profile.get("method_skill")
    method_instruction = (
        f", and reads `${method}` in full before starting work" if method else ""
    )
    return (
        "Launch: get this repo's projectId with `list_projects`, then call `create_thread`. "
        "Use that projectId as target, set environment.type to `worktree`, set "
        "startingState.type to `branch`, and set branchName to the task branch as already "
        "committed. "
        f"Use model `{profile['model']}` and thinking level `{profile['thinking']}`. "
        "The task prompt carries the four-field task, the full result-branch name, and the "
        "base SHA at dispatch time; the result-branch name uses a separate `codex/<slug>`. "
        f"The background agent completes the work and commits{method_instruction}. "
        "It returns the result-branch name, the HEAD SHA, the base SHA, and the verification "
        "result. "
        "Once `create_thread` returns a threadId, wait with `wait_threads`; when only a "
        "clientThreadId comes back, wait for the App to finish setting up the worktree, get "
        "the threadId, then wait."
    )


def expand_resume_claude(role: str, cwd_mode: str) -> str:
    if cwd_mode == "worktree":
        cwd = " --cwd <original result worktree absolute path>"
    elif cwd_mode == "current":
        cwd = " --cwd <current task worktree absolute path>"
    else:
        cwd = ""
    return (
        "Resume: in the background, run "
        f"`mmw dispatch {role} --resume <handle text>{cwd}`. "
        "Pass the repair task body as the command's standard input. "
        "The handle is the `session:` or `handle:` line from the original dispatch output, "
        "verbatim. "
        "When that line is not in hand, run `mmw artifact path scratch --sub dispatch` for "
        f"the dispatch progress directory, and read the `.session` file there that starts "
        f"with `{role}-`. "
        "When the command returns `mode: host-tool`, call the matching host tool with the "
        "`params` in its output. "
        f"If the handle cannot be found or the command fails, {RESUME_MATERIAL}"
    )


def expand_resume_cursor(role: str, cwd_mode: str) -> str:
    del role, cwd_mode
    return (
        "Resume: in the background, run `mmw-cursor-agent --resume <handle text>`. "
        "Pass the repair task body as the command's standard input. "
        "The handle is the session id from the original dispatch output. "
        f"If the handle cannot be found or the command fails, {RESUME_MATERIAL}"
    )


def expand_reviewers(host: str, role_agents: dict[str, str], profiles: dict) -> str:
    if host == "codex":
        profile = (profiles.get("subagents") or {}).get("reviewer-gpt")
        if not profile:
            die("Codex 缺 reviewer-gpt subagent profile")
        return (
            "Codex uses one reviewer role. On ⓪, ①, ②, and ⑤, launch one Codex native "
            f"`{profile['name']}` subagent per perspective. "
            "Each reviewer works in an independent context and may run the same model as "
            "the author of the object. "
            "⓪ is no exception: this host swaps the context, not the model. "
            "Review tasks that do not depend on each other launch in the same message."
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
    elif host == "claude-code":
        expand = expand_claude
    else:
        die(f"未支持的宿主 {host}")
    gpt = expand("reviewer-gpt", role_agents["reviewer-gpt"], "none")
    claude = expand("reviewer-claude", role_agents["reviewer-claude"], "none")
    return (
        "This host uses two reviewer roles. ⓪ launches one `reviewer-gpt`: the shared "
        "understanding is what the main agent interviewed out itself, so the reviewer must "
        "be a different model."
        f"{gpt}① launches one `reviewer-gpt` per perspective."
        f"{gpt}② launches one `reviewer-claude` per perspective.{claude}"
        "⑤ launches one `reviewer-gpt` and one `reviewer-claude` per perspective. "
        "Compare the two sets of findings for the same perspective side by side, then "
        "dispose as `/mmw-review` specifies. "
        "Each reviewer receives only its own four-field task."
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
    elif host == "claude-code":
        expand = expand_claude
    elif host == "codex":
        expand = None
    else:
        die(f"未支持的宿主 {host}")

    def launch(match: re.Match[str]) -> str:
        role, cwd_mode = match.group(1), match.group(2)
        if role not in role_agents:
            die(f"占位符角色不在 roles.json：{role}")
        if host == "codex":
            instruction = expand_codex(role, cwd_mode, codex_profiles)
            return f"{instruction}\n\n{POST_LAUNCH_RULE}"
        assert expand is not None
        return expand(role, role_agents[role], cwd_mode)

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
        if host in {"pi", "codex"} or (host == "cursor" and cwd_mode != "worktree"):
            return RESUME_FALLBACK
        die(f"未支持的宿主 {host}")

    text = LAUNCH_RE.sub(launch, text)
    text = LAUNCH_GROUP_RE.sub(launch_group, text)
    text = RESUME_RE.sub(resume, text)
    text = REQUIRE_TASK_BRANCH_RE.sub(
        lambda _match: expand_require_task_branch(host), text
    )
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
            return f"“{label}” above"
        if target in reference_names:
            return f"“{label}” below"
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
