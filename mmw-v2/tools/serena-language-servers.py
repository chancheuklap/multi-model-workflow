#!/usr/bin/env python3
"""把 serena 的语言服务器指到 mmw-v2/tools/ 装的那一份。

serena 默认自己下一份：pyright 走 uvx 且版本在它源码里钉死（PYRIGHT_VERSION，
实测 1.1.403），typescript 与 bash 下载到 ~/.serena/language_servers/。于是同一台
机器上同一个引擎会有好几个版本——2026-08-19 实测 pyright 有四个数字：serena 的
1.1.403、我们装的 1.1.411、PATH 上的 1.1.411、~/dev-environment 声明的 1.1.408。

覆盖的口子按语言分两种，清单里的 lookup 字段说明是哪一种：

    ls_path  serena 的 ls_specific_settings.<语言>.ls_path 给一个可执行文件路径，
             它就直接启动那个、完全绕过自己的下载与版本钉死（这一句是它
             dependency_provider.py 的文档原文）。python、typescript、bash、rust
             走这条。
    path     serena 把命令写死成 ProcessLaunchInfo(cmd="gopls") 这种形状，不经过
             create_launch_command，所以 ls_path 对它是空转。go 与 swift 走这条：
             我们能做的是保证 PATH 上只有一个，写配置反而会造成「配了但没生效」的
             假象。

只改我们这几种语言那几行，别的键原样保留。用 uv 临时带 pyyaml：系统 python3 没有它，
而 uv 本来就是这个安装器的硬依赖。

    serena-language-servers.py --tools <tools.json> --bin-dir <dir> [--node-bin-dir <dir>]
                               --config <serena_config.yml> [--check]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

# pyright: reportMissingModuleSource=false
# yaml 由调用方在运行时提供（install.sh 用 uv run --with pyyaml 起它），不在任何
# 环境的依赖清单里，所以静态检查看不到它。
import yaml


def locate(name: str, dirs: list[Path]) -> str:
    """先找我们装的那几个目录，再退回 PATH。找不到回空串。

    退回 PATH 不是让步：brew 装的那几个（gopls、rust-analyzer、shellcheck）本来就
    落在 /opt/homebrew/bin，那也是这台机器上唯一的一份。
    """
    for directory in dirs:
        candidate = directory / name
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name) or ""


class Plan:
    """接线计划：哪些语言写 ls_path、哪些靠 PATH、哪些缺、哪些这台机器就没有。"""

    def __init__(self) -> None:
        self.override: dict[str, str] = {}   # 语言 → 要写进 ls_path 的路径
        self.on_path: list[str] = []         # 靠 PATH 且找到了
        self.missing: list[str] = []         # 我们负责装却没装上 —— 要红
        self.absent: list[str] = []          # 这台机器装不了 —— 说一句，不红


def plan(tools_path: Path, dirs: list[Path]) -> Plan:
    """算出接线计划。

    找不到可执行文件的那一条不写 ls_path，不是写一个不存在的路径：serena 拿到坏路径
    会起不来，而它自己下一份至少还能用。宁可退回它的默认行为，也不要把它弄挂。
    """
    payload = json.loads(tools_path.read_text(encoding="utf-8"))
    out = Plan()
    for tool in payload.get("tools", []):
        spec = tool.get("language_server")
        if not spec:
            continue
        lang = spec["serena_language"]
        path = locate(spec["bin"], dirs)
        if not path:
            # 我们能装的却没装上，是装坏了，要红。装不了的（sourcekit-lsp 归 Xcode
            # 命令行工具管）只是这台机器没有那门语言的能力，说一句就够，不能让它
            # 一直红 —— 红久了就没人看了。
            if tool.get("install"):
                out.missing.append(f"{lang}：找不到 {spec['bin']}")
            else:
                out.absent.append(f"{lang}：这台机器没有 {spec['bin']}，serena 不做这门语言的符号")
            continue
        if spec.get("lookup") == "path":
            out.on_path.append(f"{lang}：PATH 上的 {path}")
        else:
            out.override[lang] = path
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tools", type=Path, required=True)
    parser.add_argument("--bin-dir", type=Path, required=True)
    parser.add_argument("--node-bin-dir", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    opts = parser.parse_args()

    dirs = [opts.bin_dir] + ([opts.node_bin_dir] if opts.node_bin_dir else [])
    todo = plan(opts.tools, dirs)
    want = todo.override
    for line in todo.on_path:
        print(f"就位  serena 的 {line}")
    for line in todo.absent:
        print(f"跳过  serena 的 {line}")
    for line in todo.missing:
        print(f"未配  serena 的 {line}", file=sys.stderr)
    rc = 1 if todo.missing else 0

    if not want:
        print("跳过  tools/ 里还没有要接的语言服务器，serena 继续用它自己那份", file=sys.stderr)
        return 1

    if not opts.config.is_file():
        if opts.check:
            print(f"未配  {opts.config} 不在", file=sys.stderr)
            return 1
        print(f"跳过  这台机器没有 serena 配置（{opts.config} 不在）")
        return rc

    config = yaml.safe_load(opts.config.read_text(encoding="utf-8")) or {}
    current = config.get("ls_specific_settings") or {}

    stale = [lang for lang, path in want.items() if (current.get(lang) or {}).get("ls_path") != path]
    if opts.check:
        if stale:
            print(f"未配  serena 的 {', '.join(stale)} 还没指向 mmw-v2/tools", file=sys.stderr)
            return 1
        print(f"已配  serena 的 {', '.join(sorted(want))} 都指向 mmw-v2/tools")
        return rc

    if not stale:
        print(f"已配  serena 的 {', '.join(sorted(want))} 都指向 mmw-v2/tools")
        return rc

    for lang, path in want.items():
        entry = dict(current.get(lang) or {})
        entry["ls_path"] = path
        current[lang] = entry
    config["ls_specific_settings"] = current

    # 原子写：先写同目录临时文件再替换，中途失败保留原文件。
    tmp = opts.config.with_suffix(opts.config.suffix + ".mmw-tmp")
    tmp.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    tmp.replace(opts.config)
    print(f"配好  serena 的 {', '.join(sorted(want))} → mmw-v2/tools")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
