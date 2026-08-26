"""一个服务发出的请求，和另一个服务上处理它的那条路由，之间的边。

只扫登记过的客户端：Python 侧是几个客户端类，TypeScript 侧是几份生成的客户端
文件。不满仓库找 `fetch(` 和 `requests.get(`——那会把测试夹具、脚本和文档示例
一起扫进来，而它们连出来的边全是假的。

路径必须是字面量，方法必须能静态定出来。定不出来的记进 unresolved，不默认成
GET：一次错误的 GET 会让「这个删除接口谁在调」这种问题答出错误答案，比答不出来
更糟。
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from . import tslex
from .config import HttpConfig
from .fragment import (
    CrossEdgeBuildError,
    GraphFragmentBuilder,
    UnresolvedItem,
    coverage,
    link,
    node,
    normalize_route_template,
    route_node_id,
)


def _add_call(
    builder: GraphFragmentBuilder,
    *,
    source: str,
    line: int,
    col: int,
    target: str,
    method: str,
    path: str,
    client: str,
) -> None:
    caller_id = f"http-caller::{source}::L{line}::C{col}"
    route_id = route_node_id(target, method, path)
    builder.add_node(
        node(
            caller_id,
            f"call {method} {path} ({target}; {client})",
            source,
            line,
            {
                "kind": "http_caller",
                "target_service": target,
                "method": method,
                "route_template": path,
                "client": client,
            },
        )
    )
    # 路由节点可能已经由路由探针建过了，那一份带着处理函数的位置，更准。只有调用
    # 打到一条没有注册过的路由时才在这里补一个——那本身就是值得看见的事实。
    if route_id not in builder.nodes:
        builder.add_node(
            node(
                route_id,
                f"{method} {path} ({target})",
                source,
                line,
                {
                    "kind": "http_route",
                    "target_service": target,
                    "method": method,
                    "route_template": path,
                    "registered_route": False,
                    "discovered_from": "http_call",
                },
            )
        )
    builder.add_link(
        link(
            caller_id,
            route_id,
            "http_calls",
            source,
            line,
            {
                "target_service": target,
                "method": method,
                "route_template": path,
                "client": client,
            },
        )
    )


def _extract_python(
    repo_root: Path, builder: GraphFragmentBuilder, config: HttpConfig
) -> tuple[int, int, list[UnresolvedItem]]:
    total = resolved = 0
    unresolved: list[UnresolvedItem] = []
    method_names = set(config.python_methods)
    for spec in config.python_clients:
        path = repo_root / spec.file
        if not path.is_file():
            raise CrossEdgeBuildError("http", f"客户端文件不在：{spec.file}")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        classes = [
            n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == spec.klass
        ]
        if len(classes) != 1:
            raise CrossEdgeBuildError(
                "http", f"登记的类不唯一或不存在：{spec.file}:{spec.klass}"
            )
        parents: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(classes[0]):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent

        def _enclosing_function(target_node: ast.AST) -> str:
            cursor = parents.get(target_node)
            while cursor is not None and not isinstance(
                cursor, (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                cursor = parents.get(cursor)
            return getattr(cursor, "name", "")

        for call in ast.walk(classes[0]):
            if not (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr in method_names
            ):
                continue
            # 私有 wrapper 自己递归重试（刷新令牌后重调自身）不是一个业务调用点。
            if (
                isinstance(call.func.value, ast.Name)
                and call.func.value.id == "self"
                and _enclosing_function(call) == call.func.attr
            ):
                continue
            total += 1
            method = config.python_methods.get(call.func.attr)
            path_node = None
            if (
                method is None
                and call.args
                and isinstance(call.args[0], ast.Constant)
                and isinstance(call.args[0].value, str)
            ):
                # `_request("PUT", "/x")`：动词由第一个实参给出。
                method = call.args[0].value.upper()
                path_node = call.args[1] if len(call.args) > 1 else None
            else:
                path_node = call.args[0] if call.args else None
            if (
                not method
                or not isinstance(path_node, ast.Constant)
                or not isinstance(path_node.value, str)
            ):
                unresolved.append(
                    UnresolvedItem(
                        "http_call", spec.file, call.lineno, "路径或方法是算出来的"
                    )
                )
                continue
            route = normalize_route_template(
                path_node.value.split("?", 1)[0].split("#", 1)[0]
            )
            _add_call(
                builder,
                source=spec.file,
                line=call.lineno,
                col=call.col_offset + 1,
                target=spec.target,
                method=method,
                path=route,
                client=spec.klass,
            )
            resolved += 1
    return total, resolved, unresolved


def _extract_typescript(
    repo_root: Path, builder: GraphFragmentBuilder, config: HttpConfig
) -> tuple[int, int, list[UnresolvedItem]]:
    total = resolved = 0
    unresolved: list[UnresolvedItem] = []
    helpers = config.ts_helpers
    join_helper = helpers.get("fetch_join", "joinBaseUrl")
    direct_helper = helpers.get("fetch_direct", "backendUrl")
    request_helper = helpers.get("request_json", "requestJson")
    json_init = helpers.get("json_init", "jsonInit")
    init_name = helpers.get("init_param", "init")
    for spec in config.ts_clients:
        path = repo_root / spec.file
        if not path.is_file():
            raise CrossEdgeBuildError("http", f"客户端文件不在：{spec.file}")
        text = path.read_text(encoding="utf-8")
        toks = tslex.tokens(text)
        # 各个 wrapper 里都有 `const path = ...`，同名局部常量会互相遮蔽。取调用点
        # 之前最近的那一次声明。
        constants: dict[str, list[tuple[int, str]]] = {}
        for i in range(len(toks) - 3):
            if (
                toks[i][1] == "const"
                and toks[i + 1][0] == "id"
                and toks[i + 2][1] == "="
                and toks[i + 3][0] == "str"
            ):
                constants.setdefault(toks[i + 1][1], []).append((i, toks[i + 3][1]))

        def _lookup_constant(name: str, call_index: int) -> str | None:
            best = None
            for decl_index, decl_value in constants.get(name, []):
                if decl_index < call_index:
                    best = decl_value
            return best

        def _normalize_template(value: str) -> str | None:
            """整段插值归一成 {param}；跨段或半段插值返回 None。

            `/items/${id}` 是一条路由。`/items/${a}${b}` 或 `/it${x}ems` 拼出来的
            是什么，静态看不出来。
            """
            if "${" not in value:
                return value
            out: list[str] = []
            for segment in value.split("/"):
                if "${" not in segment:
                    out.append(segment)
                elif re.fullmatch(r"\$\{[^{}]*\}", segment):
                    out.append("{param}")
                else:
                    return None
            return "/".join(out)

        def _resolve_method(call_index: int) -> str | None:
            """静态定出这个调用点的 HTTP 方法。定不出来返回 None，绝不默认成 GET。

            显式 `method: '<字面量>'` 且不早于 init 展开，用字面量；没有 init 参与
            也没有 jsonInit，是 GET（fetch 的默认）；有 jsonInit 没有 init 透传，
            按它的默认是 POST；init 透传进来而后面没有更晚的显式字面量，方法随调用
            方而变，返回 None。
            """
            depth = 0
            j = call_index + 1
            explicit = None
            explicit_pos = None
            init_pos = None
            has_json_init = False
            while j < len(toks):
                kind, val = toks[j][0], toks[j][1]
                if kind == "punct" and val == "(":
                    depth += 1
                elif kind == "punct" and val == ")":
                    depth -= 1
                    if depth == 0:
                        break
                elif kind == "id" and val == "method":
                    if (
                        j + 2 < len(toks)
                        and toks[j + 1][1] == ":"
                        and toks[j + 2][0] == "str"
                    ):
                        explicit = toks[j + 2][1].upper()
                        explicit_pos = j
                elif kind == "id" and val == json_init:
                    has_json_init = True
                elif kind == "id" and val == init_name:
                    init_pos = j if init_pos is None else init_pos
                j += 1
            if explicit is not None:
                if init_pos is None or (
                    explicit_pos is not None and explicit_pos > init_pos
                ):
                    return explicit
                return None
            if init_pos is not None:
                return None
            return "POST" if has_json_init else "GET"

        seen = 0
        for i in range(len(toks) - 8):
            seq = [x[1] for x in toks[i : i + 9]]
            path_token = None
            start = toks[i][2]
            if seq[:4] == ["fetch", "(", join_helper, "("]:
                path_token = (
                    toks[i + 6] if len(toks) > i + 6 and toks[i + 5][1] == "," else None
                )
            elif seq[:4] == ["fetch", "(", direct_helper, "("]:
                path_token = toks[i + 4]
            elif seq[:4] == [request_helper, "(", seq[2], ","]:
                path_token = toks[i + 4]
            if path_token is None:
                continue
            seen += 1
            total += 1
            line = tslex.line_of(text, start)
            if path_token[0] == "str":
                value = path_token[1]
            elif path_token[0] == "id":
                value = _lookup_constant(path_token[1], i) or path_token[1]
            else:
                value = None
            if value:
                value = _normalize_template(value.split("?", 1)[0])
            if not value or not value.startswith("/"):
                unresolved.append(
                    UnresolvedItem("http_call", spec.file, line, "路径是算出来的")
                )
                continue
            method = _resolve_method(i)
            if method is None:
                unresolved.append(
                    UnresolvedItem("http_call", spec.file, line, "方法是算出来的")
                )
                continue
            route = normalize_route_template(value.split("?", 1)[0].split("#", 1)[0])
            _add_call(
                builder,
                source=spec.file,
                line=line,
                col=1,
                target=spec.target,
                method=method,
                path=route,
                client=spec.name,
            )
            resolved += 1
        if seen == 0:
            raise CrossEdgeBuildError(
                "http", f"这份客户端里一个认得出的调用都没有：{spec.file}"
            )
    return total, resolved, unresolved


def extract_http_edges(
    repo_root: Path, builder: GraphFragmentBuilder, config: HttpConfig
) -> tuple[dict[str, object], list[UnresolvedItem]]:
    py_total, py_resolved, py_unresolved = _extract_python(repo_root, builder, config)
    ts_total, ts_resolved, ts_unresolved = _extract_typescript(
        repo_root, builder, config
    )
    return coverage(
        py_total + ts_total,
        py_resolved + ts_resolved,
        len(py_unresolved) + len(ts_unresolved),
    ), py_unresolved + ts_unresolved
