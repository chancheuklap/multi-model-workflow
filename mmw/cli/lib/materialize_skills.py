#!/usr/bin/env python3
"""把共享 skill 物化成 Pi、Claude Code、Codex、Cursor 或 Grok 版本。

派发动作不在这里展开：技能正文写 `mmw launch …`，宿主差异由 cli/host-actions.json
在运行期回答。这里只处理宿主之间无法共用的字面差异和产物落盘。"""

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
SKILLS_SRC = PLUGIN_ROOT / "skills-src"
DEFAULT_OUT = {
    "pi": PLUGIN_ROOT / "skills-pi",
    "claude-code": PLUGIN_ROOT / "skills-claude-code",
    "codex": PLUGIN_ROOT / "skills-codex",
    "grok": PLUGIN_ROOT / "skills-grok",
    "cursor": PLUGIN_ROOT / "skills-cursor",
}
PI_PROMPTS_OUT = PLUGIN_ROOT / "prompts-pi"

CODEX_SKILL_REF_RE = re.compile(r"`/(mmw-[a-z0-9-]+)`")
SKIP_DIR_NAMES = frozenset({"mmw-setup"})
def die(message: str, code: int = 1) -> NoReturn:
    print(f"mmw skills: {message}", file=sys.stderr)
    raise SystemExit(code)


def expand_text(text: str, host: str) -> str:
    """物化只剩宿主之间真正无法共用的字面差异：Codex 的技能引用语法。

    派发动作不在这里展开。技能正文写 `mmw launch …`，五个宿主拿到同一句，
    动作由 cli/host-actions.json 在运行期回答。
    """
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


def render_pi_prompt(skill_dir: Path) -> str:
    skill_file = skill_dir / "SKILL.md"
    raw = skill_file.read_text(encoding="utf-8")
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
    body = expand_text(body, "pi")
    parts = [inline_reference_links(body, reference_names).rstrip()]
    for reference in references:
        text = strip_frontmatter(reference.read_text(encoding="utf-8"))
        text = expand_text(text, "pi")
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
        die(f"{skill_file} 还在用 [[mmw-…]] 占位符；派发改成 `mmw launch`")
    return rendered


def materialize_pi_prompts(*, check: bool) -> int:
    expected = {
        f"{name}.md": render_pi_prompt(SKILLS_SRC / name)
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

    # 只收自己产的 `.md`，不整目录重建：`mmw/package.json` 的 `pi.prompts` 指着这个
    # 目录，而没有 user-only 技能时 expected 为空——重建会连目录一起从 git 里消失，
    # 声明就指向一个不存在的路径。
    PI_PROMPTS_OUT.mkdir(parents=True, exist_ok=True)
    for path in PI_PROMPTS_OUT.glob("*.md"):
        if path.name not in expected:
            path.unlink()
    for name, content in expected.items():
        (PI_PROMPTS_OUT / name).write_text(content, encoding="utf-8")
    print(f"物化完成：pi 用户命令 → {PI_PROMPTS_OUT}")
    return 0


def materialize_host(host: str, out_root: Path, *, check: bool) -> int:
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
                text = expand_text(text, host)
                if "[[mmw-" in text:
                    die(f"{rel} 还在用 [[mmw-…]] 占位符；派发改成 `mmw launch`，见 cli/host-actions.json")
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

    hosts = (
        ["pi", "claude-code", "codex", "cursor", "grok"] if args.host == "all" else [args.host]
    )
    status = 0
    for host in hosts:
        out = args.out if args.out and args.host != "all" else DEFAULT_OUT[host]
        status |= materialize_host(host, out, check=args.check)
        if host == "pi" and args.out is None:
            status |= materialize_pi_prompts(check=args.check)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
