#!/usr/bin/env python3
"""在仓库自己的依赖环境里读出路由表。自包含单文件，只用标准库加仓库的框架。

这个文件由 `uv run --project <仓库>` 拉起，跑在仓库的虚拟环境里，所以它不能
import 插件的任何模块——插件不在仓库的依赖清单里。

它一个人住在这个目录里，不跟 graph 包的其他模块放一起：Python 会把脚本所在目录
排到 sys.path 最前，那里但凡有个 `http.py`，被拉起的框架 `import http` 就会抓到
它，而报出来的错跟真正的原因毫无关系。

它做的事只有一件：加载仓库声明的 provider，拿到 `{服务名: 应用对象}`，遍历路由
表，把每条路由的路径、方法、处理函数位置写成 JSON。

为什么不扫源码里的装饰器：路由器层层挂载时前缀在挂载处拼接，装饰器上只写得到
最后一段。扫出来的 `/hold` 连不上前端调用的 `/api/v1/hold`，边就断在这里。
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import sys
from pathlib import Path


def _fail(reason: str) -> None:
    print(f"[FAIL] stage=route_probe reason={reason}", file=sys.stderr)
    raise SystemExit(1)


def _load_callable(repo_root: Path, spec: str):
    """按 `相对路径.py:函数名` 加载仓库自己的函数。"""
    rel, _, func_name = spec.partition(":")
    path = (repo_root / rel).resolve()
    if not path.is_file():
        _fail(f"provider 文件不在：{rel}")
    module_spec = importlib.util.spec_from_file_location(
        f"_mmw_graph_provider_{path.stem}", path
    )
    if module_spec is None or module_spec.loader is None:
        _fail(f"provider 加载不了：{rel}")
        raise AssertionError  # 上一行必定退出，这一行只为类型收敛
    module = importlib.util.module_from_spec(module_spec)
    try:
        module_spec.loader.exec_module(module)
    except Exception as exc:
        _fail(f"provider 导入失败：{type(exc).__name__}: {exc}")
    func = getattr(module, func_name, None)
    if func is None or not callable(func):
        _fail(f"provider 里没有可调用的 {func_name}：{rel}")
    return func


def _relative(repo_root: Path, value: str) -> str:
    try:
        return Path(value).resolve().relative_to(repo_root).as_posix()
    except ValueError:
        _fail(f"处理函数的源文件在仓库外：{value}")
        raise AssertionError


def collect(repo_root: Path, src_root: str, provider: str) -> list[dict[str, object]]:
    src = str(repo_root / src_root)
    sys.path.insert(0, src)
    try:
        from fastapi.routing import APIRoute
    except ImportError as exc:
        _fail(f"仓库环境里没有 fastapi：{exc}")
        raise AssertionError
    try:
        apps = _load_callable(repo_root, provider)()
    except SystemExit:
        raise
    except Exception as exc:
        _fail(f"provider 调用失败：{type(exc).__name__}: {exc}")
        raise AssertionError
    if not isinstance(apps, dict) or not apps:
        _fail("provider 必须返回非空的 {服务名: 应用对象}")
    records: list[dict[str, object]] = []
    for service, app in apps.items():
        routes = getattr(app, "routes", None)
        if routes is None:
            _fail(f"{service} 返回的对象没有 routes")
        for route in routes:
            if not isinstance(route, APIRoute) or not route.methods or not route.path:
                continue
            endpoint = inspect.unwrap(route.endpoint)
            source = inspect.getsourcefile(endpoint)
            if source is None:
                _fail(f"{service} 有一条路由的处理函数找不到源文件")
                raise AssertionError
            source_file = _relative(repo_root, source)
            line = inspect.getsourcelines(endpoint)[1]
            for method in sorted(set(route.methods) - {"HEAD", "OPTIONS"}):
                records.append(
                    {
                        "service": str(service),
                        "method": method.upper(),
                        "path": route.path,
                        "handler_name": endpoint.__qualname__,
                        "source_file": source_file,
                        "line": line,
                    }
                )
    sys.path.remove(src)
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="读出仓库的 FastAPI 路由表")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--src-root", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    records = collect(repo_root, args.src_root, args.provider)
    Path(args.output).write_text(json.dumps(records, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
