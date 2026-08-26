#!/usr/bin/env python3
"""把探测出来缺的语言服务器与检查器装上。

`mmw toolchain detect` 报「缺 oxlint，装它：pnpm add -D oxlint oxlint-tsgolint」，但它
只报不装。配好了判据、工具却不在，编辑后诊断就静默少跑一样——看起来在跑，其实漏了。
这一步补上那一环。

装什么、怎么装，都来自规则表里每个条目自己的 install 字段。这里不认识 pnpm 也不认识 uv，
只负责按工作区把命令跑起来。

默认只列不装。真要装得显式给 --yes：这些命令会往全局或工作区装东西，不该在别人没点头
的时候发生。
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path
from shutil import which

sys.path.insert(0, str(Path(__file__).resolve().parent))

from toolchain_detect import detect  # noqa: E402

INSTALL_TIMEOUT = 600


def missing_items(report: dict) -> list[dict]:
    """探测报告里所有「缺」的条目，连同它该在哪个工作区装。

    同一条命令可能在多个工作区各要跑一次（三个 Electron 壳各装各的 oxlint），所以按
    (工作区, 命令) 去重，不是按命令去重。
    """
    found: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for rule in report["rules"]:
        for ws in rule["workspaces"]:
            candidates = []
            server = ws.get("server")
            if server:
                candidates.append(("语言服务器", server))
            candidates.extend(("检查器", c) for c in ws.get("checkers", []))

            for kind, item in candidates:
                if item.get("path"):
                    continue
                command = item.get("install", "")
                if not command:
                    continue
                key = (ws["workspace"], command)
                if key in seen:
                    continue
                seen.add(key)
                found.append(
                    {
                        "rule": rule["title"],
                        "kind": kind,
                        "name": item.get("name") or item.get("id", "?"),
                        "workspace": ws["workspace"],
                        "command": command,
                    }
                )
    return found


def runnable(command: str) -> bool:
    """这条 install 是一句能直接跑的命令，还是一句让人去看文档的话。

    规则表里有「见 https://rustup.rs」这种条目——它不是命令。判据是第一个词在 PATH 上
    找不到。
    """
    try:
        first = shlex.split(command)[0]
    except ValueError:
        return False
    return which(first) is not None


def run_one(repo: Path, item: dict) -> bool:
    workdir = repo / item["workspace"]
    print(f"\n跑    {item['command']}")
    print(f"目录  {workdir}")
    try:
        done = subprocess.run(
            item["command"], shell=True, cwd=workdir, timeout=INSTALL_TIMEOUT
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f"失败  {exc}", file=sys.stderr)
        return False
    if done.returncode != 0:
        print(f"失败  退出码 {done.returncode}", file=sys.stderr)
        return False
    return True


def main(argv: list[str]) -> int:
    do_install = "--yes" in argv
    rest = [a for a in argv if a != "--yes"]
    if len(rest) < 2:
        print("用法：toolchain_install.py <仓库> <规则表> [--yes]", file=sys.stderr)
        return 2

    repo = Path(rest[0]).resolve()
    items = missing_items(detect(repo, Path(rest[1]).resolve()))

    if not items:
        print("语言服务器和检查器都在，没有要装的。")
        return 0

    print(f"缺 {len(items)} 样：")
    for item in items:
        where = "仓库根" if item["workspace"] == "." else item["workspace"]
        print(f"  {item['rule']} / {item['kind']} {item['name']}（{where}）")
        print(f"    {item['command']}")

    if not do_install:
        print("\n只列不装。要装就加 --yes。")
        return 1

    failed = 0
    for item in items:
        if not runnable(item["command"]):
            print(f"\n跳过  {item['command']}")
            print("      第一个词不是一条能跑的命令，自己按它说的做")
            failed += 1
            continue
        if not run_one(repo, item):
            failed += 1

    print()
    if failed:
        print(f"装完了，{failed} 样没成。上面每条失败都原样印了，自己看是什么挡着。")
        return 1
    print("都装上了。跑 mmw toolchain detect 再确认一遍。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
