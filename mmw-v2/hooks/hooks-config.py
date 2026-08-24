#!/usr/bin/env python3
"""把 mmw-hooks.json 里的三条 hook 合并进一个宿主的 hook 配置文件，或只读比对。只给 install.sh 调。

    hooks-config.py merge <file> <format> <hooks_root> <host>   合并写入；stdout 一行安装了的事件名；冲突退出 1、不写
    hooks-config.py check <file> <format> <hooks_root> <host>   只读比对；缺的打「缺」到 stderr，退出 1
    hooks-config.py strip <file> <hooks_root>                   摘掉本仓库的条目（退役清理）；摘空且文件里没别的就删文件

format：claude（settings.json 的 hooks 键）、codex / grok（hooks.json，同一 schema）、cursor（camelCase 事件、扁平条目）。
「本仓库的条目」= 命令串里含 <hooks_root>/ 的条目；命令里出现本层脚本名却指向别处的条目算冲突。
"""
import json
import os
import sys

TEMPLATE = "mmw-hooks.json"
SCRIPT_NAMES = ("mmw-activate.js", "mmw-subagent.js", "mmw-stop.mjs")
CURSOR_EVENTS = {"SessionStart": "sessionStart", "SubagentStart": "subagentStart", "Stop": "stop"}


def load(file, fmt):
    if os.path.exists(file):
        with open(file, encoding="utf-8") as f:
            raw = f.read().lstrip("﻿")
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            sys.exit(f"{file} 不是 JSON 对象")
    else:
        data = {}
    if fmt == "cursor":
        data.setdefault("version", 1)
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        sys.exit(f"{file} 的 hooks 不是对象")
    return data


def save(file, data):
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def commands(entry):
    """一个条目（Claude/Codex 的 matcher 组或 Cursor 的扁平条目）里所有 command 串。"""
    if not isinstance(entry, dict):
        return []
    found = []
    if isinstance(entry.get("command"), str):
        found.append(entry["command"])
    for h in entry.get("hooks", []) or []:
        if isinstance(h, dict) and isinstance(h.get("command"), str):
            found.append(h["command"])
    return found


def owned(entry, hooks_root):
    return any(hooks_root.rstrip("/") + "/" in c for c in commands(entry))


def conflicting(entry, hooks_root):
    return not owned(entry, hooks_root) and any(n in c for c in commands(entry) for n in SCRIPT_NAMES)


def render(fmt, hooks_root, host):
    with open(os.path.join(hooks_root, TEMPLATE), encoding="utf-8") as f:
        template = json.load(f)["hooks"]
    out = {}
    for event, groups in template.items():
        rendered = []
        for group in groups:
            group = json.loads(json.dumps(group).replace("${MMW_HOOKS_ROOT}", hooks_root))
            for h in group["hooks"]:
                h["command"] = f'{h["command"]} --host {host}'
            if fmt == "cursor":
                rendered.extend({"command": h["command"]} for h in group["hooks"])
            else:
                rendered.append(group)
        out[CURSOR_EVENTS[event] if fmt == "cursor" else event] = rendered
    return out


def merge(file, fmt, hooks_root, host):
    data = load(file, fmt)
    hooks = data["hooks"]
    ours = render(fmt, hooks_root, host)
    conflicts = []
    for event, entries in list(hooks.items()):
        if not isinstance(entries, list):
            continue
        for e in entries:
            if conflicting(e, hooks_root):
                conflicts.append(f"{file}:{event}: {commands(e)}")
        hooks[event] = [e for e in entries if not owned(e, hooks_root)]
        if not hooks[event] and event not in ours:
            del hooks[event]
    if conflicts:
        for c in conflicts:
            print(f"冲突  {c} 不是本仓库装的，跳过", file=sys.stderr)
        return 1
    for event, entries in ours.items():
        hooks.setdefault(event, []).extend(entries)
        print(event)
    save(file, data)
    return 0


def check(file, fmt, hooks_root, host):
    rc = 0
    try:
        data = load(file, fmt)
    except SystemExit:
        data = {"hooks": {}}
    hooks = data["hooks"]
    for event, entries in render(fmt, hooks_root, host).items():
        present = hooks.get(event, []) if isinstance(hooks.get(event, []), list) else []
        for e in entries:
            if e not in present:
                print(f"缺    {file}:{event}", file=sys.stderr)
                rc = 1
    return rc


def strip(file, hooks_root):
    if not os.path.exists(file):
        return 0
    data = load(file, "any")
    hooks = data["hooks"]
    for event, entries in list(hooks.items()):
        if isinstance(entries, list):
            hooks[event] = [e for e in entries if not owned(e, hooks_root)]
            if not hooks[event]:
                del hooks[event]
    if not hooks and set(data) <= {"hooks", "version"}:
        os.remove(file)
        print(f"摘掉  {file}")
        return 0
    save(file, data)
    return 0


def main(argv):
    if len(argv) >= 6 and argv[1] == "merge":
        return merge(argv[2], argv[3], os.path.abspath(argv[4]), argv[5])
    if len(argv) >= 6 and argv[1] == "check":
        return check(argv[2], argv[3], os.path.abspath(argv[4]), argv[5])
    if len(argv) >= 4 and argv[1] == "strip":
        return strip(argv[2], os.path.abspath(argv[3]))
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
