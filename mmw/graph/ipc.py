"""Electron 主进程与渲染进程之间的调用。

频道名住在一张常量表里，两侧各按键名引用。原生抽取看到的是两个互不相干的字符串
常量引用；这里把它们连到同一个频道节点上，于是「点了这个按钮，主进程哪个函数在
处理」就问得出来。

只认按键名引用的写法（`IPC_CHANNELS.SOMETHING`）。裸字符串频道名不认——认了就
得在整个壳里满找字符串，而那会把日志文案一起扫进来。
"""

from __future__ import annotations

from pathlib import Path

from . import tslex
from .config import IpcConfig
from .fragment import (
    CrossEdgeBuildError,
    GraphFragmentBuilder,
    UnresolvedItem,
    coverage,
    link,
    node,
)


def _call_patterns(channel_object: str) -> dict[tuple[str, ...], str]:
    """六个 token 的前缀，命中即调用点。值是这一侧的角色。"""
    return {
        ("ipcMain", ".", "handle", "(", channel_object, "."): "handle",
        ("ipcMain", ".", "on", "(", channel_object, "."): "handle",
        ("ipcRenderer", ".", "invoke", "(", channel_object, "."): "invoke",
        ("ipcRenderer", ".", "send", "(", channel_object, "."): "invoke",
    }


def extract_ipc_edges(
    repo_root: Path, builder: GraphFragmentBuilder, config: IpcConfig
) -> tuple[dict[str, object], list[UnresolvedItem]]:
    patterns = _call_patterns(config.channel_object)
    total = resolved = 0
    warnings: list[UnresolvedItem] = []
    inventory: dict[str, dict[str, set[str]]] = {}
    for shell in config.shells:
        authority = repo_root / shell / config.channel_table
        if not authority.is_file():
            raise CrossEdgeBuildError(
                "ipc", f"频道表不在：{shell}/{config.channel_table}"
            )
        rel = authority.relative_to(repo_root).as_posix()
        table = tslex.constant_object(
            authority.read_text(encoding="utf-8"), rel, config.channel_object
        )
        seen: dict[str, set[str]] = {"handle": set(), "invoke": set()}
        for key, (channel, line) in sorted(table.items()):
            channel_id = f"ipc-channel::{shell}::{channel}"
            builder.add_node(
                node(
                    channel_id,
                    f"channel {channel} ({shell})",
                    rel,
                    line,
                    {
                        "kind": "ipc_channel",
                        "shell": shell,
                        "channel": channel,
                        "channel_keys": sorted(
                            k for k, v in table.items() if v[0] == channel
                        ),
                    },
                )
            )
        shell_src = repo_root / shell / "src"
        for file in sorted(shell_src.rglob("*.ts")) + sorted(shell_src.rglob("*.tsx")):
            text = file.read_text(encoding="utf-8")
            source = file.relative_to(repo_root).as_posix()
            toks = tslex.tokens(text)
            found: list[tuple[str, str, int]] = []
            for i in range(len(toks) - 6):
                prefix = tuple(t[1] for t in toks[i : i + 6])
                kind = patterns.get(prefix)
                if kind:
                    found.append((kind, toks[i + 6][1], toks[i][2]))
            # 第二次独立走一遍 token 流数个数。两次数不一致说明上面的遍历漏了或者
            # 重了，那种错误不会让任何一条边看起来可疑，只会让图静默少几条。
            independent = sum(
                1
                for i in range(len(toks) - 6)
                if tuple(t[1] for t in toks[i : i + 6]) in patterns
            )
            if independent != len(found):
                raise CrossEdgeBuildError("ipc", f"IPC 调用点两次清点对不上：{source}")
            for kind, key, start in found:
                total += 1
                line = tslex.line_of(text, start)
                col = tslex.column_of(text, start)
                if key not in table:
                    raise CrossEdgeBuildError(
                        "ipc", f"频道表里没有这个键 {key}：{source}:{line}"
                    )
                channel = table[key][0]
                channel_id = f"ipc-channel::{shell}::{channel}"
                prefix_name = "ipc-handler" if kind == "handle" else "ipc-caller"
                relation = "ipc_handles" if kind == "handle" else "ipc_invokes"
                node_id = f"{prefix_name}::{shell}::{source}::L{line}::C{col}"
                label = ("handle" if kind == "handle" else "invoke") + f" {channel} ({shell})"
                builder.add_node(
                    node(
                        node_id,
                        label,
                        source,
                        line,
                        {
                            "kind": prefix_name,
                            "shell": shell,
                            "channel_key": key,
                            "channel": channel,
                        },
                    )
                )
                builder.add_link(
                    link(
                        node_id,
                        channel_id,
                        relation,
                        source,
                        line,
                        {"shell": shell, "channel_key": key, "channel": channel},
                    )
                )
                seen[kind].add(channel)
                resolved += 1
        # 有人调、没人处理，是真的会挂在运行时的缺陷，但不是建图失败——报出来。
        for channel in seen["invoke"] - seen["handle"]:
            warnings.append(
                UnresolvedItem(
                    "ipc_missing_handler", rel, 1, f"shell={shell} channel={channel}"
                )
            )
        if not seen["handle"] or not seen["invoke"]:
            raise CrossEdgeBuildError("ipc", f"{shell} 一个 IPC 调用点都没找到")
        inventory[shell] = seen
    return coverage(
        total,
        resolved,
        0,
        channels=sum(len(v["handle"] | v["invoke"]) for v in inventory.values()),
        shells=len(config.shells),
        invokes=sum(len(v["invoke"]) for v in inventory.values()),
        handles=sum(len(v["handle"]) for v in inventory.values()),
        warnings=len(warnings),
    ), warnings
