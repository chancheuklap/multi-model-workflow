#!/usr/bin/env python3
"""Prepare an installed MMW home for rollback to the pre-B0 version."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_locations():
    path = ROOT.joinpath("mmw-v2", "skills", "mmw", "scripts", "locations.py")
    spec = importlib.util.spec_from_file_location("rollback_locations", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


locations = load_locations()
sys.path.insert(0, str(ROOT / "mmw-v2" / "skills" / locations.MODE_SCRIPTS))
sys.path.insert(0, str(ROOT / "mmw-v2" / "skills" / locations.UI_ACCEPTANCE_SCRIPTS))
import models  # noqa: E402
import relay  # noqa: E402
import statedir  # noqa: E402
from refusal import refusal  # noqa: E402

SWEPT = (
    (".claude/settings.json", "grouped", False),
    (".codex/hooks.json", "grouped", False),
    (".cursor/hooks.json", "cursor", False),
    (".grok/hooks/mmw-verify-ticket.json", "grouped", True),
    (".grok/hooks/mmw-turn.json", "grouped", True),
    (".grok/hooks/mmw-discipline.json", "grouped", True),
    (".grok/hooks/mmw-turn-guard.json", "grouped", True),
)


class Refusal(RuntimeError):
    pass


def refuse(fact, next_step):
    raise Refusal(refusal(fact, "运行中的 MMW 必须保持已安装版本不变。", next_step,
                          limit=2048))


def assert_safe():
    for repo_dir in statedir.repo_state_dirs():
        watches = relay.read_watches(repo_dir)
        for key in sorted(watches):
            watch = watches[key]
            command = (f"dispatch.sh land {watch['tickets'][0]}" if watch.get("tickets")
                       else f"dispatch.sh suspend {watch['spec']}")
            refuse(f"OPEN-WATCH {repo_dir.name} {key}（{repo_dir / 'watches.json'}）。",
                   f"在该仓库运行 {command} 后再准备回退。")
        for kind in ("relay", "watchdog"):
            holder = statedir.holder(repo_dir / f"{kind}.lock")
            if holder is not None:
                pid = holder["pid"]
                refuse(f"LIVE-LOCK {repo_dir.name} {kind} pid {pid}。",
                       f"运行 ps -p {pid} -o pid=,lstart=,command= 核对进程；由启动者停止后再准备回退。")


def remove_copy_links(home):
    copies = Path(os.path.abspath(home / ".mmw/skill-copies"))
    for directory in (home / ".agents/skills", home / ".claude/skills"):
        if not directory.is_dir():
            continue
        for link in sorted(directory.iterdir()):
            if not link.is_symlink():
                continue
            target = Path(os.path.abspath(link.parent / link.readlink()))
            if target.is_relative_to(copies):
                link.unlink()
                print(f"REMOVED skill-copy link: {link}")


def remove_launcher_hooks(home):
    mark = f"'{home / '.mmw/bin/hook-launcher'}' "
    for relative, fmt, exclusive in SWEPT:
        path = (Path(os.environ.get("CODEX_HOME") or home / ".codex") / "hooks.json"
                if relative == ".codex/hooks.json" else home / relative)
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        hooks = data.get("hooks")
        if not isinstance(hooks, dict):
            continue
        dropped = 0

        def survivors(handlers):
            nonlocal dropped
            kept = []
            for handler in handlers:
                if isinstance(handler, dict) and mark in str(handler.get("command", "")):
                    dropped += 1
                else:
                    kept.append(handler)
            return kept

        for event, entries in list(hooks.items()):
            if not isinstance(entries, list):
                continue
            if fmt == "cursor":
                kept = survivors(entries)
            else:
                kept = []
                for group in entries:
                    inner = group.get("hooks") if isinstance(group, dict) else None
                    if not isinstance(inner, list):
                        kept.append(group)
                        continue
                    remaining = survivors(inner)
                    if remaining:
                        group["hooks"] = remaining
                        kept.append(group)
            if kept:
                hooks[event] = kept
            else:
                del hooks[event]
        if not dropped:
            continue
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup = path.with_name(path.name + ".bak-" + stamp)
        shutil.copy2(path, backup)
        for old in path.parent.glob(path.name + ".bak-*"):
            if old != backup and (old.is_file() or old.is_symlink()):
                old.unlink()
        if exclusive and not hooks:
            path.unlink()
        else:
            statedir.write_atomic(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"REMOVED launcher hooks ({dropped}): {path}; backup: {backup}")


def remove_researcher():
    path = models.models_json_path()
    if not path.is_file() or "researcher" not in models.read_local_config().get("rows", {}):
        return
    with models.config_lock(purpose="prepare rollback"):
        config = models.read_local_config()
        rows = config.get("rows")
        if not isinstance(rows, dict):
            raise ValueError(f"{path} has no rows object")
        if "researcher" not in rows:
            return
        version = config.get("version")
        if not isinstance(version, int):
            raise ValueError(f"{path} has no integer version")
        config["version"] = version + 1
        saved = statedir.home() / "models-researcher-before-rollback.json"
        statedir.write_atomic(saved, json.dumps(rows["researcher"], ensure_ascii=False, indent=2) + "\n")
        del rows["researcher"]
        statedir.write_atomic(path, json.dumps(config, ensure_ascii=False, indent=2) + "\n")
        print(f"REMOVED researcher: {path}; saved: {saved}")


def main():
    home = Path(os.environ.get("MMW_V2_HOME") or os.environ["HOME"])
    if "MMW_V2_HOME" in os.environ:
        os.environ["MMW_HOME"] = str(home / ".mmw")
    else:
        os.environ["MMW_HOME"] = os.environ.get("MMW_HOME") or str(home / ".mmw")
    try:
        assert_safe()
        remove_copy_links(home)
        remove_launcher_hooks(home)
        remove_researcher()
        marker = home / ".mmw/board-bootstrapped-commit"
        if marker.exists():
            marker.unlink()
            print(f"REMOVED board commit: {marker}")
        return 0
    except Refusal as exc:
        print(f"prepare-rollback: {exc}", file=sys.stderr)
    except (OSError, ValueError, statedir.LockHeld) as exc:
        print("prepare-rollback: " + refusal(
            f"回退准备失败：{exc}。", "未完成安全回退。",
            "修正点名文件或等待配置写入者释放锁后，再运行 prepare-rollback.py。", limit=2048),
            file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
