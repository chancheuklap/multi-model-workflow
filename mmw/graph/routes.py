"""前端调的那条路径，和后端处理它的那个函数，之间的边。

分两步：先在仓库自己的依赖环境里把路由表读出来（`route_probe.py` 那个子进程），
再把每条路由变成一个路由节点加一条 `handles_route` 边。

探针会真的把应用构造出来，所以它有副作用风险——构造过程若碰了用户的真实数据
目录，一次建图就动了用户的数据。前后各取一次目录指纹，变了就当场失败。
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .config import RoutesConfig
from .fragment import (
    CrossEdgeBuildError,
    GraphFragmentBuilder,
    RouteRecord,
    coverage,
    link,
    node,
    normalize_route_template,
    route_node_id,
)

_PROBE = Path(__file__).resolve().parent / "probe" / "route_probe.py"


def _tree_fingerprint(path: Path) -> tuple[object, ...]:
    """只读 lstat，绝不跟随符号链接——被守护的目录是用户自己的，不该被走进去。"""
    if not path.exists() and not path.is_symlink():
        return (False,)
    entries: list[tuple[str, int, int, int]] = []
    stack = [path]
    while stack:
        current = stack.pop()
        stat = current.lstat()
        relative = "." if current == path else current.relative_to(path).as_posix()
        entries.append((relative, stat.st_mode, stat.st_size, stat.st_mtime_ns))
        if current.is_dir() and not current.is_symlink():
            stack.extend(sorted(current.iterdir(), reverse=True))
    return (True, tuple(sorted(entries)))


def _guarded_dirs(repo_root: Path, config: RoutesConfig) -> list[Path]:
    """跑仓库声明的守护函数，拿到要盯住的真实数据目录。

    这个函数在 MMW 自己的进程里跑，不在仓库的虚拟环境里，所以它只能依赖标准库。它做的
    是路径计算，本来也不该需要别的东西。
    """
    if not config.user_data_guard:
        return []
    rel, _, func_name = config.user_data_guard.partition(":")
    path = (repo_root / rel).resolve()
    if not path.is_file():
        raise CrossEdgeBuildError("route_probe", f"user_data_guard 文件不在：{rel}")
    src = str(repo_root / config.src_root)
    sys.path.insert(0, src)
    try:
        spec = importlib.util.spec_from_file_location(f"_mmw_guard_{path.stem}", path)
        if spec is None or spec.loader is None:
            raise CrossEdgeBuildError("route_probe", f"user_data_guard 加载不了：{rel}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        func = getattr(module, func_name, None)
        if func is None or not callable(func):
            raise CrossEdgeBuildError(
                "route_probe", f"user_data_guard 里没有可调用的 {func_name}：{rel}"
            )
        result = func()
        if not isinstance(result, (list, tuple)):
            raise CrossEdgeBuildError(
                "route_probe", f"user_data_guard 必须返回目录列表：{rel}"
            )
        return [Path(item) for item in result]
    except CrossEdgeBuildError:
        raise
    except Exception as exc:
        raise CrossEdgeBuildError(
            "route_probe",
            f"user_data_guard 跑不起来（它只能依赖标准库）：{type(exc).__name__}: {exc}",
        ) from exc
    finally:
        sys.path.remove(src)


def enumerate_routes(
    repo_root: Path, config: RoutesConfig, services: tuple[str, ...]
) -> tuple[list[RouteRecord], bool]:
    guarded = _guarded_dirs(repo_root, config)
    before = [_tree_fingerprint(d) for d in guarded]
    with tempfile.TemporaryDirectory(prefix="mmw-graph-route-") as temp_root:
        temp = Path(temp_root)
        probe_output = temp / "routes.json"
        env = os.environ.copy()
        # 配置里的环境变量把应用的落盘位置全指向临时目录。`{tmp}` 是唯一的占位符。
        env.update(
            {key: value.replace("{tmp}", str(temp)) for key, value in config.env.items()}
        )
        # 不依赖调用方的 uv 缓存：在隔离的 worktree 里跑时那个缓存可能读不到。
        env.setdefault("UV_CACHE_DIR", str(temp / "uv-cache"))
        command = [
            "uv",
            "run",
            "--project",
            str(repo_root),
            "python",
            str(_PROBE),
            "--repo-root",
            str(repo_root),
            "--src-root",
            config.src_root,
            "--provider",
            config.provider,
            "--output",
            str(probe_output),
        ]
        try:
            completed = subprocess.run(
                command, env=env, capture_output=True, text=True, check=False
            )
        except OSError as exc:
            raise CrossEdgeBuildError(
                "route_probe", f"uv 子进程起不来：{exc}"
            ) from exc
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip().splitlines()
            raise CrossEdgeBuildError(
                "route_probe",
                f"uv 子进程退出码 {completed.returncode}："
                f"{detail[-1] if detail else '没有输出'}",
            )
        try:
            import json

            raw_records = json.loads(probe_output.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise CrossEdgeBuildError(
                "route_probe", f"子进程没有交回合法的路由 JSON：{exc}"
            ) from exc
    after = [_tree_fingerprint(d) for d in guarded]
    if before != after:
        raise CrossEdgeBuildError(
            "route_probe", "探针跑过之后真实用户数据目录变了"
        )
    records: list[RouteRecord] = []
    for raw in raw_records:
        try:
            record = RouteRecord(
                service=str(raw["service"]),
                method=str(raw["method"]).upper(),
                path=normalize_route_template(str(raw["path"])),
                handler_name=str(raw["handler_name"]),
                source_file=str(raw["source_file"]),
                line=int(raw["line"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CrossEdgeBuildError(
                "routes", f"子进程交回的路由记录不合法：{raw!r}"
            ) from exc
        if (
            record.service not in services
            or record.line <= 0
            or Path(record.source_file).is_absolute()
        ):
            raise CrossEdgeBuildError("routes", f"路由记录不合法：{record}")
        records.append(record)
    return sorted(
        set(records),
        key=lambda item: (
            item.service,
            item.method,
            item.path,
            item.source_file,
            item.line,
        ),
    ), True


def add_route_edges(
    builder: GraphFragmentBuilder,
    records: list[RouteRecord],
    services: tuple[str, ...],
) -> dict[str, object]:
    counts = {service: 0 for service in services}
    # 同一条路由挂着多个处理函数是合法的（同路径不同前缀挂载）。路由节点的位置取
    # 其中排序最小的那一个，这样它跟哪个处理函数先被遍历到无关。
    canonical_routes: dict[tuple[str, str, str], RouteRecord] = {}
    for record in records:
        key = (record.service, record.method, record.path)
        previous = canonical_routes.get(key)
        if previous is None or (
            record.source_file,
            record.line,
            record.handler_name,
        ) < (previous.source_file, previous.line, previous.handler_name):
            canonical_routes[key] = record
    for record in records:
        counts[record.service] += 1
        handler_id = (
            f"handler::{record.source_file}::{record.handler_name}::L{record.line}"
        )
        route_id = route_node_id(record.service, record.method, record.path)
        metadata: dict[str, object] = {
            "service": record.service,
            "method": record.method,
            "route_template": record.path,
        }
        builder.add_node(
            node(
                handler_id,
                f"{record.handler_name}() ({record.service})",
                record.source_file,
                record.line,
                {"kind": "route_handler", **metadata},
            )
        )
        route_source = canonical_routes[(record.service, record.method, record.path)]
        builder.add_node(
            node(
                route_id,
                f"{record.method} {record.path} ({record.service})",
                route_source.source_file,
                route_source.line,
                {"kind": "http_route", "registered_route": True, **metadata},
            )
        )
        builder.add_link(
            link(
                handler_id,
                route_id,
                "handles_route",
                record.source_file,
                record.line,
                metadata,
            )
        )
    empty = [service for service in services if counts[service] == 0]
    if empty:
        raise CrossEdgeBuildError(
            "routes", f"这几个服务一条路由都没枚举到：{empty}"
        )
    return coverage(len(records), len(records), 0, services=counts)
