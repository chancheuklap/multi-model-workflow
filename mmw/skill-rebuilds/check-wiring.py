#!/usr/bin/env python3
"""扫候选技能树里所有可机械判定的引用，报出解析不开的。

只报机器能直接判定的四类：相对链接目标不存在、技能名不存在、
启动占位符的角色/组不认识、宿主动作名不认识。方法论对不对不在这里判。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "mmw/skill-rebuilds/candidate/skills")
REPO = Path.cwd()
ROLES = json.loads((REPO / "mmw/agent-src/roles.json").read_text())["roles"]
MATERIALIZE = (REPO / "mmw/cli/lib/materialize_skills.py").read_text()

# 物化脚本里实际支持的 host-action 名（if name == "xxx" 形式）
HOST_ACTIONS = set(re.findall(r'if name == "([a-z0-9-]+)"', MATERIALIZE))

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)#]+\.md)\)")
SKILL_REF = re.compile(r"`/((?:mmw-)?[a-z][a-z0-9-]*)`")
LAUNCH = re.compile(r"\[\[mmw-launch:([a-z0-9-]+):([a-z]+)\]\]")
LAUNCH_MANY = re.compile(r"\[\[mmw-launch-many:([a-z0-9-]+):(\d+):([a-z]+)\]\]")
LAUNCH_GROUP = re.compile(r"\[\[mmw-launch-group:([a-z0-9-]+):([a-z]+)\]\]")
HOST_ACTION = re.compile(r"\[\[mmw-host-action:([a-z0-9-]+)\]\]")

skills = {p.name for p in ROOT.iterdir() if p.is_dir()}
problems = []

for md in sorted(ROOT.rglob("*.md")):
    rel = md.relative_to(ROOT)
    text = md.read_text(encoding="utf-8")
    # 跳过代码块，避免把示例里的东西当真引用
    stripped = re.sub(r"```.*?```", "", text, flags=re.S)

    for target in MD_LINK.findall(stripped):
        if target.startswith(("http:", "https:")):
            continue
        if not (md.parent / target).resolve().exists():
            problems.append(("链接打不开", rel, target))

    for name in SKILL_REF.findall(stripped):
        if name.startswith("mmw-") and name not in skills:
            problems.append(("技能不存在", rel, f"/{name}"))

    for role, cwd in LAUNCH.findall(stripped):
        if role not in ROLES:
            problems.append(("角色不在 roles.json", rel, f"{role}:{cwd}"))

    for role, n, cwd in LAUNCH_MANY.findall(stripped):
        problems.append(("launch-many 物化层不支持", rel, f"{role}:{n}:{cwd}"))

    for group, cwd in LAUNCH_GROUP.findall(stripped):
        if group != "reviewers" or cwd != "none":
            problems.append(("启动组物化会 die", rel, f"{group}:{cwd}"))

    for action in HOST_ACTION.findall(stripped):
        if action not in HOST_ACTIONS:
            problems.append(("宿主动作不认识", rel, action))

by_kind = {}
for kind, rel, detail in problems:
    by_kind.setdefault(kind, []).append((rel, detail))

for kind in sorted(by_kind):
    print(f"\n## {kind}（{len(by_kind[kind])}）")
    for rel, detail in sorted(by_kind[kind]):
        print(f"  {rel}  →  {detail}")

print(f"\n扫了 {len(list(ROOT.rglob('*.md')))} 个文件，{len(skills)} 个技能，问题 {len(problems)} 条")
sys.exit(1 if problems else 0)
