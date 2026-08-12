#!/usr/bin/env python3
"""按规则表探测这个仓库该配哪些语言服务器与命令行检查器。

只读：读 Git 已跟踪和未忽略的新文件清单、读各工作区的 package.json 与 pyproject.toml、跑
`<bin> --version` 取版本。不写任何文件，不装任何东西。产出配置是下一步的事，
这一步只回答"该配什么、缺什么、版本对不对得上"。

工作区不是仓库根。agentflow 一个仓库里有三个 Electron 壳各带一份 node_modules，
Python 侧另有一个 .venv。语言服务器必须用它所服务的那个工作区里的二进制，否则
版本和持续集成判定的对不上——所以每条规则各自算工作区，不假定只有一个。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION_TIMEOUT = 15
VERSION_PATTERN = re.compile(r"(\d+\.\d+(?:\.\d+)?(?:[-.][0-9A-Za-z.]+)?)")


def die(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def repository_files(repo: Path) -> list[str]:
    """Git 已跟踪文件和未忽略的新文件。

    worker 会在第一次提交前运行 ``mmw toolchain apply``。只读已跟踪文件时，本轮
    新建的工作区永远不会进入探测结果。``--exclude-standard`` 继续使用仓库现有的
    ignore 规则排除 node_modules、构建产物和过程目录。
    """
    try:
        out = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
            ],
            capture_output=True,
            text=True,
            timeout=VERSION_TIMEOUT,
            check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        die(f"读不到 git 跟踪清单：{exc}")
    return out.stdout.splitlines()


def match_glob(paths: list[str], patterns: list[str]) -> list[str]:
    """只按扩展名匹配。规则表里的 tracked_glob 写成 "*.py" 这种形式，这里取后缀
    比较，不引入 fnmatch 的路径语义——规则要的是"这个仓库有没有这门语言"。"""
    suffixes = tuple(p[1:] for p in patterns if p.startswith("*."))
    return [p for p in paths if p.endswith(suffixes)]


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def ignored(rel_dir: str, ignore_prefixes: list[str]) -> bool:
    """含 package.json 不等于是本仓库的工作区：docs/ 下放着竞品软件解包后的完整目录，
    带它自己的依赖清单。规则表的 workspace_ignore 列出这类前缀。"""
    normalized = "" if rel_dir == "." else rel_dir.rstrip("/") + "/"
    return any(normalized.startswith(prefix) for prefix in ignore_prefixes)


def node_workspaces(repo: Path, paths: list[str], ignore_prefixes: list[str]) -> list[str]:
    """含 package.json 的目录，按仓库相对路径返回。"""
    dirs = sorted({str(Path(p).parent) for p in paths if Path(p).name == "package.json"})
    return [
        d
        for d in dirs
        if (repo / d / "package.json").is_file() and not ignored(d, ignore_prefixes)
    ]


def python_workspaces(repo: Path, paths: list[str], ignore_prefixes: list[str]) -> list[str]:
    dirs = sorted(
        {str(Path(p).parent) for p in paths if Path(p).name in ("pyproject.toml", "setup.py")}
    )
    kept = [d for d in dirs if (repo / d).is_dir() and not ignored(d, ignore_prefixes)]
    return kept or ["."]


def package_deps(repo: Path, workspace: str) -> dict:
    pkg = read_json(repo / workspace / "package.json")
    return {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}


def probe_version(executable: Path | str) -> str:
    """跑 `<bin> --version` 取版本号。取不到就返回空串——版本只用于报告和版本
    对齐检查，取不到不影响"这个二进制在不在"的结论。"""
    for flag in ("--version", "-V"):
        try:
            out = subprocess.run(
                [str(executable), flag],
                capture_output=True,
                text=True,
                timeout=VERSION_TIMEOUT,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""
        text = f"{out.stdout}\n{out.stderr}"
        found = VERSION_PATTERN.search(text)
        if found:
            return found.group(1)
    return ""


def which(name: str) -> str:
    from shutil import which as _which

    return _which(name) or ""


def version_of(spec: dict, executable: Path | str) -> str:
    """语言服务器的可执行文件常常不认 --version：pyright-langserver 喂它这个参数会
    打出一段 vscode-languageserver 的报错。规则表用 version_from 指向同一个包的
    另一个入口，版本从那个取。"""
    sibling = spec.get("version_from")
    if sibling:
        candidate = Path(executable).parent / sibling
        if candidate.is_file():
            return probe_version(candidate)
        found = which(sibling)
        if found:
            return probe_version(found)
        return ""
    return probe_version(executable)


def resolve_binary(repo: Path, workspace: str, spec: dict) -> dict:
    """先找工作区内的，再回落 PATH。顺序不能反：工作区内那个才是持续集成用的。"""
    for rel in spec.get("project_bin", []):
        candidate = repo / workspace / rel
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return {
                "found": True,
                "scope": "工作区",
                "path": str(candidate.relative_to(repo)),
                "version": version_of(spec, candidate),
            }
    name = spec.get("bin", "")
    path = which(name) if name else ""
    if path:
        return {
            "found": True,
            "scope": "PATH",
            "path": path,
            "version": version_of(spec, path),
        }
    return {"found": False, "scope": "", "path": "", "version": ""}


def check_same_version(repo: Path, workspace: str, constraint: dict) -> dict:
    """same_version：同一个二进制的工作区版本与 PATH 版本必须一致。"""
    name = constraint.get("left", {}).get("bin", "")
    project_hit = None
    for rel in (f".venv/bin/{name}", f"node_modules/.bin/{name}"):
        candidate = repo / workspace / rel
        if candidate.is_file():
            project_hit = probe_version(candidate)
            break
    global_path = which(name)
    global_hit = probe_version(global_path) if global_path else ""
    if not project_hit or not global_hit:
        return {"state": "跳过", "detail": f"{name} 只找到一处，无从比较"}
    if project_hit == global_hit:
        return {"state": "满足", "detail": f"{name} 两处都是 {project_hit}"}
    return {
        "state": "不满足",
        "detail": f"{name} 工作区 {project_hit}，PATH {global_hit}",
    }


def check_peer_upper_bound(repo: Path, workspace: str, constraint: dict) -> dict:
    """peer_upper_bound：装了需要编程接口的包时，typescript 主版本必须落在界内。"""
    deps = package_deps(repo, workspace)
    present = [p for p in constraint.get("packages", []) if p in deps]
    if not present:
        return {"state": "跳过", "detail": "没装需要编程接口的包"}
    spec = deps.get("typescript", "")
    # alias 形态："npm:@typescript/typescript6@6.0.2"。取最后一个版本号判主版本。
    found = VERSION_PATTERN.findall(spec)
    major = found[-1].split(".")[0] if found else ""
    who = "、".join(present)
    if not major:
        return {"state": "跳过", "detail": f"读不出 typescript 版本：{spec or '未声明'}"}
    if int(major) < 7:
        return {"state": "满足", "detail": f"{who} 拿到 typescript {found[-1]}"}
    return {
        "state": "不满足",
        "detail": f"{who} 需要 typescript<7，当前 {spec}",
    }


CONSTRAINT_CHECKS = {
    "same_version": check_same_version,
    "peer_upper_bound": check_peer_upper_bound,
}


def detect(repo: Path, rules_path: Path) -> dict:
    table = read_json(rules_path)
    rules = table.get("rules", [])
    if not rules:
        die(f"读不到规则表：{rules_path}")
    ignore_prefixes = table.get("workspace_ignore", [])
    paths = repository_files(repo)
    node_ws = node_workspaces(repo, paths, ignore_prefixes)
    python_ws = python_workspaces(repo, paths, ignore_prefixes)
    report = {"repo": str(repo), "rules": []}

    for rule in rules:
        detect_spec = rule.get("detect", {})
        hits: list[str] = []
        workspaces: list[str] = []

        if detect_spec.get("always"):
            # 不看仓库内容，一律命中。给那些"每个仓库都该有"的规则用，比如密钥扫描。
            workspaces = ["."]

        elif "tracked_glob" in detect_spec:
            hits = match_glob(paths, detect_spec["tracked_glob"])
            if not hits:
                continue
            if rule["id"] == "python":
                workspaces = python_ws
            elif rule["id"] == "typescript":
                workspaces = node_ws or ["."]
            else:
                workspaces = ["."]

        elif "package_dep" in detect_spec:
            wanted = detect_spec["package_dep"]
            workspaces = [
                ws for ws in node_ws if any(dep in package_deps(repo, ws) for dep in wanted)
            ]
            if not workspaces:
                continue
            hits = [f"{ws}/package.json" for ws in workspaces]

        entry = {
            "id": rule["id"],
            "title": rule.get("title", rule["id"]),
            "hit_count": len(hits),
            "workspaces": [],
        }

        for ws in workspaces:
            ws_entry = {"workspace": ws, "server": None, "checkers": [], "constraints": []}
            server = rule.get("server")
            if server:
                resolved = resolve_binary(repo, ws, server)
                ws_entry["server"] = {"name": server["name"], "install": server.get("install", ""), **resolved}
            for checker in rule.get("checkers", []):
                resolved = resolve_binary(repo, ws, checker)
                item = {"id": checker["id"], "install": checker.get("install", ""), **resolved}
                missing_companions = [
                    c for c in checker.get("companions", []) if c not in package_deps(repo, ws)
                ]
                item["missing_companions"] = missing_companions
                configs = checker.get("requires_config", [])
                item["config_found"] = (
                    any((repo / ws / c).is_file() for c in configs) if configs else None
                )
                ws_entry["checkers"].append(item)
            for constraint in rule.get("constraints", []):
                check = CONSTRAINT_CHECKS.get(constraint.get("kind", ""))
                if not check:
                    continue
                result = check(repo, ws, constraint)
                ws_entry["constraints"].append({"id": constraint["id"], **result})
            entry["workspaces"].append(ws_entry)

        report["rules"].append(entry)

    return report


def render(report: dict) -> int:
    """人读的报告。有任何"缺"或"不满足"时返回 1，让调用方能当门禁用。"""
    problems = 0
    print(f"仓库      : {report['repo']}")
    if not report["rules"]:
        print("命中      : 一条规则都没命中")
        return 0

    for rule in report["rules"]:
        print()
        print(f"{rule['title']}")
        print(f"  命中      : {rule['hit_count']} 个仓库文件")
        for ws in rule["workspaces"]:
            label = ws["workspace"] if ws["workspace"] != "." else "仓库根"
            print(f"  工作区    : {label}")
            server = ws["server"]
            if server:
                if server["found"]:
                    version = f" {server['version']}" if server["version"] else ""
                    print(
                        f"    语言服务器: {server['name']} — {server['path']}"
                        f"（{server['scope']}{version}）"
                    )
                else:
                    problems += 1
                    print(f"    语言服务器: {server['name']} — 缺，装它：{server['install']}")
            for checker in ws["checkers"]:
                if checker["found"]:
                    version = f" {checker['version']}" if checker["version"] else ""
                    extra = ""
                    if checker["missing_companions"]:
                        problems += 1
                        extra += f"，缺配套包 {'、'.join(checker['missing_companions'])}"
                    if checker["config_found"] is False:
                        problems += 1
                        extra += "，缺配置文件"
                    print(
                        f"    检查器    : {checker['id']} — {checker['path']}"
                        f"（{checker['scope']}{version}）{extra}"
                    )
                else:
                    problems += 1
                    print(f"    检查器    : {checker['id']} — 缺，装它：{checker['install']}")
            for constraint in ws["constraints"]:
                if constraint["state"] == "不满足":
                    problems += 1
                print(f"    约束      : {constraint['id']} {constraint['state']} — {constraint['detail']}")

    print()
    if problems:
        print(f"待办      : {problems} 处缺失或不满足")
    else:
        print("待办      : 无")
    return 1 if problems else 0


def main(argv: list[str]) -> int:
    repo = None
    rules_path = None
    as_json = False
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--repo":
            repo = Path(args.pop(0)).resolve()
        elif arg == "--rules":
            rules_path = Path(args.pop(0)).resolve()
        elif arg == "--json":
            as_json = True
        else:
            die(f"认不出的参数：{arg}")
    if repo is None or rules_path is None:
        die("用法：toolchain_detect.py --repo <仓库根> --rules <规则表> [--json]")

    report = detect(repo, rules_path)
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    return render(report)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
