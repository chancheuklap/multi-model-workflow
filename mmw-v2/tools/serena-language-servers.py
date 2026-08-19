#!/usr/bin/env python3
"""把 serena 的语言服务器指到 mmw-v2/tools/ 装的那一份。

serena 默认自己下一份：pyright 走 uvx 且版本在它源码里钉死（PYRIGHT_VERSION，
实测 1.1.403），typescript 与 bash 下载到 ~/.serena/language_servers/。于是同一台
机器上同一个引擎会有好几个版本——2026-08-19 实测 pyright 有四个数字：serena 的
1.1.403、我们装的 1.1.411、PATH 上的 1.1.411、~/dev-environment 声明的 1.1.408。

serena 提供了正规的覆盖口子：serena_config.yml 的 ls_specific_settings.<语言>.ls_path
给一个可执行文件路径，它就直接启动那个、完全绕过自己的下载与版本钉死（这一句是它
dependency_provider.py 的文档原文说的）。

只改我们这几种语言那几行，别的键原样保留。用 uv 临时带 pyyaml：系统 python3 没有它，
而 uv 本来就是这个安装器的硬依赖。

    serena-language-servers.py --tools <tools.json> --bin-dir <dir> [--node-bin-dir <dir>]
                               --config <serena_config.yml> [--check]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# pyright: reportMissingModuleSource=false
# yaml 由调用方在运行时提供（install.sh 用 uv run --with pyyaml 起它），不在任何
# 环境的依赖清单里，所以静态检查看不到它。
import yaml


def wanted(tools_path: Path, dirs: list[Path]) -> dict[str, str]:
    """回 {serena 的语言名: 可执行文件绝对路径}。找不到可执行文件的那一条不写。

    找不到就不写，不是写一个不存在的路径：serena 拿到一个坏路径会起不来，而它自己
    下一份至少还能用。宁可退回它的默认行为，也不要把它弄挂。
    """
    payload = json.loads(tools_path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for tool in payload.get("tools", []):
        spec = tool.get("language_server")
        if not spec:
            continue
        for directory in dirs:
            candidate = directory / spec["bin"]
            if candidate.is_file():
                out[spec["serena_language"]] = str(candidate)
                break
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
    want = wanted(opts.tools, dirs)
    if not want:
        print("跳过  tools/ 里还没有语言服务器，serena 继续用它自己那份", file=sys.stderr)
        return 1

    if not opts.config.is_file():
        if opts.check:
            print(f"未配  {opts.config} 不在", file=sys.stderr)
            return 1
        print(f"跳过  这台机器没有 serena 配置（{opts.config} 不在）")
        return 0

    config = yaml.safe_load(opts.config.read_text(encoding="utf-8")) or {}
    current = config.get("ls_specific_settings") or {}

    missing = [lang for lang, path in want.items() if (current.get(lang) or {}).get("ls_path") != path]
    if opts.check:
        if missing:
            print(f"未配  serena 的 {', '.join(missing)} 还没指向 mmw-v2/tools", file=sys.stderr)
            return 1
        print(f"已配  serena 的 {', '.join(sorted(want))} 都指向 mmw-v2/tools")
        return 0

    if not missing:
        print(f"已配  serena 的 {', '.join(sorted(want))} 都指向 mmw-v2/tools")
        return 0

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
