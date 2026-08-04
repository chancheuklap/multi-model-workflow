#!/usr/bin/env python3
"""把技能源里的启动占位符物化成宿主写死的启动句。

源：mmw/skills/（可含 [[mmw-launch:角色:cwd模式]]）
物化：
  --host pi           → mmw/skills-pi/
  --host claude-code  → mmw/skills-claude-code/
  --host all          → 两者都写

cwd 模式：worktree | none
不物化 mmw-dispatching-agents（已废除，由安装面写死启动句）。

用法：
  materialize_skills.py --host pi|claude-code|all [--check] [--out <dir>]
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
}

# [[mmw-launch:worker:worktree]] 或 [[mmw-launch:investigator:none]]
LAUNCH_RE = re.compile(
    r"\[\[mmw-launch:([a-z0-9-]+):(worktree|none)\]\]"
)

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


def expand_text(text: str, host: str, role_agents: dict[str, str]) -> str:
    expand = expand_pi if host == "pi" else expand_claude

    def repl(match: re.Match[str]) -> str:
        role, cwd_mode = match.group(1), match.group(2)
        if role not in role_agents:
            die(f"占位符角色不在 roles.json：{role}")
        return expand(role, role_agents[role], cwd_mode)

    return LAUNCH_RE.sub(repl, text)


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
                text = expand_text(text, host, role_agents)
                if "[[mmw-launch:" in text:
                    die(f"{rel} 仍有未识别的 mmw-launch 占位符")
            dst.write_text(text, encoding="utf-8")

        if check:
            if not out_root.is_dir():
                print(f"缺  {out_root}")
                return 1
            drift = 0
            for path in sorted(tmp.rglob("*")):
                if not path.is_file():
                    continue
                rel = path.relative_to(tmp)
                target = out_root / rel
                if not target.is_file():
                    print(f"缺  {target}")
                    drift = 1
                    continue
                if path.read_bytes() != target.read_bytes():
                    print(f"异  {target}")
                    drift = 1
            # 发布面不得再出现派发中转技能
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
    parser.add_argument("--host", required=True, choices=("pi", "claude-code", "all"))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--out", type=Path, default=None, help="覆盖默认输出目录")
    args = parser.parse_args(argv)

    role_agents = load_role_agents()
    hosts = ["pi", "claude-code"] if args.host == "all" else [args.host]
    status = 0
    for host in hosts:
        out = args.out if args.out and args.host != "all" else DEFAULT_OUT[host]
        status |= materialize_host(host, out, role_agents, check=args.check)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
