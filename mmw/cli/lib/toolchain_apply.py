#!/usr/bin/env python3
"""按探测结果，把这个仓库该有的工具链配置写出来。

`mmw toolchain detect` 只回答"该配什么、缺什么"。这一步真的动手写文件，所以换一个仓库、
换一台电脑，配置不用靠人想起来——跑一次 `mmw init` 就在。

谁拥有哪份内容，由规则表里的 mode 决定：

  managed      MMW 拥有。每次 apply 比对内容，不一致就重写。想改判据就改 MMW 的模板，
               改仓库里那份会在下次 apply 被盖掉。
  create_only  仓库拥有。只在缺失时生成一份起步内容，之后再不碰。

宿主配置（Claude Code 的 enabledPlugins）走键级合并：只加自己那几个键。仓库的
permissions 和 hooks 是用户自己写的，整份覆盖会把它们抹掉。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from toolchain_detect import detect, read_json  # noqa: E402


class Plan:
    """一次 apply 要做的事。先收集再落盘，报告里能说清哪份写了、哪份没碰。"""

    def __init__(self) -> None:
        self.writes: list[tuple[Path, str, str]] = []  # (路径, 内容, 原因)
        self.skips: list[tuple[Path, str]] = []  # (路径, 原因)
        self.notes: list[str] = []

    def write(self, path: Path, content: str, reason: str) -> None:
        if path.is_file() and path.read_text(encoding="utf-8") == content:
            return
        self.writes.append((path, content, reason))

    def skip(self, path: Path, reason: str) -> None:
        self.skips.append((path, reason))


def dumps(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def relpath_between(from_dir: str, target: str) -> str:
    """从工作区目录指回仓库根某个文件的相对路径。oxlint 的 extends 要相对写。"""
    if from_dir in ("", "."):
        return f"./{target}"
    depth = len([p for p in Path(from_dir).parts if p not in ("", ".")])
    return "../" * depth + target


def toml_has_table(text: str, table: str) -> bool:
    """这份 TOML 里有没有这张表。只做行首匹配——够判断"要不要补"，不解析整份文件。"""
    return bool(re.search(rf"^\s*\[{re.escape(table)}\]\s*$", text, re.MULTILINE))


def toml_render_table(table: str, content: dict) -> str:
    """把一张表渲染成 TOML 文本。只支持字符串列表与标量，emit 里的内容就这两种。"""
    lines = [f"[{table}]"]
    for key, value in content.items():
        if isinstance(value, list):
            items = ", ".join(json.dumps(v, ensure_ascii=False) for v in value)
            lines.append(f"{key} = [{items}]")
        else:
            lines.append(f"{key} = {json.dumps(value, ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def plan_workflow(plan: Plan, repo: Path, templates: Path, item: dict, entry: dict) -> None:
    """持续集成工作流。判据和本地编辑后诊断同一套规则，所以它跟规则表走，不留在各仓库。

    模板里的 __WORKSPACES__ 填成这条规则实际命中的工作区清单，当矩阵取值用。
    """
    source = templates / item["template"]
    if not source.is_file():
        plan.notes.append(f"缺模板：{source}")
        return
    if not (repo / ".github" / "workflows").is_dir():
        plan.notes.append(f"没有 .github/workflows，跳过 {item['to']}")
        return

    content = source.read_text(encoding="utf-8")
    if "__WORKSPACES__" in content:
        listed = "\n".join(f"          - {w['workspace']}" for w in entry["workspaces"])
        content = content.replace("__WORKSPACES__", listed)
    plan.write(repo / item["to"], content, f"模板 {item['template']}")


def plan_template(plan: Plan, repo: Path, templates: Path, item: dict, entry: dict) -> None:
    source = templates / item["template"]
    if not source.is_file():
        plan.notes.append(f"缺模板：{source}")
        return
    raw = source.read_text(encoding="utf-8")

    if item.get("scope") == "workspace":
        targets = [(repo / w["workspace"] / item["to"], w["workspace"]) for w in entry["workspaces"]]
    else:
        targets = [(repo / item["to"], ".")]

    for path, workspace in targets:
        content = raw
        for placeholder, spec in item.get("substitute", {}).items():
            value = (
                relpath_between(workspace, spec.split(":", 1)[1])
                if spec.startswith("relpath_to:")
                else spec
            )
            content = content.replace(placeholder, value)

        if item.get("mode") == "create_only" and path.is_file():
            plan.skip(path, "已存在，仓库自己拥有")
            continue
        plan.write(path, content, f"模板 {item['template']}")


def plan_toml_table(plan: Plan, repo: Path, item: dict) -> None:
    path = repo / item["to"]
    table = item["table"]
    if not path.is_file():
        plan.notes.append(f"没有 {item['to']}，跳过 [{table}]")
        return

    text = path.read_text(encoding="utf-8")
    if toml_has_table(text, table):
        plan.skip(path, f"已有 [{table}]，仓库自己拥有")
        return

    joiner = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
    plan.write(path, text + joiner + toml_render_table(table, item["content"]), f"补 [{table}]")


def plan_claude_settings(plan: Plan, repo: Path, hit_rules: list[dict]) -> None:
    """Claude Code 的项目设置。只合并 enabledPlugins 这一个键。"""
    wanted = [
        name
        for rule in hit_rules
        for name in rule.get("hosts", {}).get("claude-code", {}).get("enabled_plugins", [])
    ]
    if not wanted:
        return

    path = repo / ".claude" / "settings.json"
    settings = read_json(path) if path.is_file() else {}
    if path.is_file() and not settings:
        plan.notes.append(f"读不出 {path}，跳过 enabledPlugins")
        return

    enabled = dict(settings.get("enabledPlugins", {}))
    missing = [name for name in wanted if name not in enabled]
    if not missing:
        plan.skip(path, "enabledPlugins 已齐")
        return
    for name in missing:
        enabled[name] = True
    settings["enabledPlugins"] = enabled
    plan.write(path, dumps(settings), "合入 enabledPlugins：" + "、".join(missing))


def build_plan(repo: Path, rules_path: Path, templates: Path) -> Plan:
    report = detect(repo, rules_path)
    by_id = {r["id"]: r for r in read_json(rules_path).get("rules", [])}
    hit_rules = [by_id[e["id"]] for e in report["rules"] if e["id"] in by_id]

    plan = Plan()
    for entry in report["rules"]:
        rule = by_id.get(entry["id"])
        if not rule:
            continue
        for item in rule.get("emit", []):
            kind = item.get("kind")
            if kind == "template":
                plan_template(plan, repo, templates, item, entry)
            elif kind == "workflow":
                plan_workflow(plan, repo, templates, item, entry)
            elif kind == "toml_table":
                plan_toml_table(plan, repo, item)
            else:
                plan.notes.append(f"{rule['id']} 的 emit `{item.get('id')}` 用了不认识的 kind：{kind}")
    plan_claude_settings(plan, repo, hit_rules)
    return plan


def main(argv: list[str]) -> int:
    written_to = ""
    rest: list[str] = []
    it = iter(argv)
    for arg in it:
        if arg == "--written-to":
            written_to = next(it, "")
        else:
            rest.append(arg)

    if len(rest) < 3:
        print("用法：toolchain_apply.py <仓库> <规则表> <模板目录> [--written-to 文件]", file=sys.stderr)
        return 2

    repo, rules_path, templates = (Path(x).resolve() for x in rest[:3])
    plan = build_plan(repo, rules_path, templates)

    for path, content, _reason in plan.writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    for path, reason in plan.skips:
        print(f"跳过  {path.relative_to(repo)}  （{reason}）")
    for path, _content, reason in plan.writes:
        print(f"写出  {path.relative_to(repo)}  （{reason}）")
    for note in plan.notes:
        print(f"提示  {note}")
    if not plan.writes:
        print("配置已齐，没有要写的。")

    # 写过的路径交给调用方。`mmw init` 用它登记这一轮要提交的文件——配置留在工作区
    # 没提交，任务 worktree 里就看不到。
    if written_to:
        lines = [f"{p.relative_to(repo)}\n" for p, _c, _r in plan.writes]
        Path(written_to).write_text("".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
