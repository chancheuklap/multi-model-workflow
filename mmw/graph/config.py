"""跨语言边的配置：这个仓库有哪些服务、哪几个壳、哪些客户端。

算法在别的模块里，跟仓库无关；这里只装名单。分界的判据是：换一个仓库还成立的
写进代码，只对这个仓库成立的写进 `.mmw.json` 的 `retrieval.graph` 一节。

四类边各自独立开关：某一类没配就不提取，也不因此失败。一个只有后端没有 Electron
壳的仓库照样能建出路由与 HTTP 调用的边。
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from .fragment import CrossEdgeBuildError

# 关系名决定节点前缀，不另外配一份——两处写法一定会漂移，那时同一条主题会分裂成
# 两个节点，而图上看起来只是「少了一条边」。
TOPIC_PREFIX = {
    "produces_topic": "sync-producer",
    "drains_topic": "sync-drain",
    "consumes_topic": "sync-consumer",
}


@dataclasses.dataclass(frozen=True)
class RoutesConfig:
    """后端路由怎么枚举。

    扫源码里的装饰器拿不到路由器层层拼接的前缀，扫出来的 `/hold` 连不上前端调的
    `/api/v1/hold`。所以这里要仓库自己给一个 provider：把应用构造出来，返回
    `{服务名: 应用对象}`，插件在隔离的子进程里跑它、读它的路由表。

    provider 写成 `相对路径.py:函数名`。它在仓库自己的依赖环境里跑（`uv run
    --project`），所以插件不需要装仓库的依赖。
    """

    provider: str
    src_root: str
    env: dict[str, str]
    user_data_guard: str | None
    framework: str

    @property
    def provider_file(self) -> str:
        return self.provider.split(":", 1)[0]

    @property
    def provider_function(self) -> str:
        return self.provider.split(":", 1)[1]


@dataclasses.dataclass(frozen=True)
class IpcConfig:
    """Electron 壳的进程间调用。

    频道名住在一张常量表里，主进程与渲染进程各按键名引用它。表的位置每个壳一样，
    所以只配壳的根目录加一条相对路径。
    """

    shells: tuple[str, ...]
    channel_table: str
    channel_object: str


@dataclasses.dataclass(frozen=True)
class TopicSpec:
    file: str
    symbol: str
    relation: str
    enqueue_call: str | None

    @property
    def prefix(self) -> str:
        return TOPIC_PREFIX[self.relation]


@dataclasses.dataclass(frozen=True)
class PythonClient:
    file: str
    klass: str
    target: str


@dataclasses.dataclass(frozen=True)
class TsClient:
    file: str
    target: str
    name: str


@dataclasses.dataclass(frozen=True)
class HttpConfig:
    """服务之间的 HTTP 调用。

    只扫登记过的客户端类与生成的客户端文件，不满仓库找 `requests.get`：跨服务调用
    在这类项目里一律走客户端封装，满仓库找只会把测试夹具和脚本一起扫进来。
    """

    python_clients: tuple[PythonClient, ...]
    python_methods: dict[str, str | None]
    ts_clients: tuple[TsClient, ...]
    ts_helpers: dict[str, str]


@dataclasses.dataclass(frozen=True)
class Assertions:
    """业务拓扑断言：提取器静默退化时当场断在这里。

    覆盖率是数字，数字掉了没人看得出来。断言钉的是具体事实——某条路由必须解析到
    某个函数、某个主题必须既有人生产又有人消费。这些是仓库自己的事实，所以在配置
    里，不在代码里。
    """

    route_handler: tuple[dict[str, str], ...]
    route_per_service: str | None
    http_methods: tuple[str, ...]
    topic_relations: dict[str, tuple[str, ...]]


@dataclasses.dataclass(frozen=True)
class GraphConfig:
    services: tuple[str, ...]
    routes: RoutesConfig | None
    ipc: IpcConfig | None
    topics: tuple[TopicSpec, ...]
    http: HttpConfig | None
    assertions: Assertions
    exclude_roots: tuple[str, ...]

    @property
    def enabled(self) -> bool:
        return bool(self.routes or self.ipc or self.topics or self.http)


def _require(section: dict[str, object], key: str, where: str) -> object:
    if key not in section:
        raise CrossEdgeBuildError("config", f"{where} 缺 {key}")
    return section[key]


def _str_tuple(value: object, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise CrossEdgeBuildError("config", f"{where} 必须是字符串数组")
    return tuple(value)  # type: ignore[arg-type]


def _parse_routes(raw: object) -> RoutesConfig:
    if not isinstance(raw, dict):
        raise CrossEdgeBuildError("config", "retrieval.graph.routes 必须是对象")
    provider = _require(raw, "provider", "retrieval.graph.routes")
    if not isinstance(provider, str) or ":" not in provider:
        raise CrossEdgeBuildError(
            "config", "retrieval.graph.routes.provider 要写成 路径.py:函数名"
        )
    framework = raw.get("framework", "fastapi")
    if framework != "fastapi":
        raise CrossEdgeBuildError(
            "config", f"暂时只认得 fastapi 的路由表，收到 framework={framework!r}"
        )
    env = raw.get("env", {})
    if not isinstance(env, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in env.items()
    ):
        raise CrossEdgeBuildError("config", "retrieval.graph.routes.env 必须是字符串表")
    guard = raw.get("user_data_guard")
    if guard is not None and (not isinstance(guard, str) or ":" not in guard):
        raise CrossEdgeBuildError(
            "config", "retrieval.graph.routes.user_data_guard 要写成 路径.py:函数名"
        )
    return RoutesConfig(
        provider=provider,
        src_root=str(raw.get("src_root", "src")),
        env=dict(env),  # type: ignore[arg-type]
        user_data_guard=guard,
        framework=framework,
    )


def _parse_ipc(raw: object) -> IpcConfig:
    if not isinstance(raw, dict):
        raise CrossEdgeBuildError("config", "retrieval.graph.ipc 必须是对象")
    shells = _str_tuple(
        _require(raw, "shells", "retrieval.graph.ipc"), "retrieval.graph.ipc.shells"
    )
    if not shells:
        raise CrossEdgeBuildError("config", "retrieval.graph.ipc.shells 不能是空数组")
    return IpcConfig(
        shells=shells,
        channel_table=str(raw.get("channel_table", "src/main/ipc.ts")),
        channel_object=str(raw.get("channel_object", "IPC_CHANNELS")),
    )


def _parse_topics(raw: object) -> tuple[TopicSpec, ...]:
    if not isinstance(raw, list):
        raise CrossEdgeBuildError("config", "retrieval.graph.topics 必须是数组")
    specs: list[TopicSpec] = []
    for index, item in enumerate(raw):
        where = f"retrieval.graph.topics[{index}]"
        if not isinstance(item, dict):
            raise CrossEdgeBuildError("config", f"{where} 必须是对象")
        relation = str(_require(item, "relation", where))
        if relation not in TOPIC_PREFIX:
            raise CrossEdgeBuildError(
                "config", f"{where}.relation 只能是 {sorted(TOPIC_PREFIX)} 之一"
            )
        enqueue = item.get("enqueue_call")
        specs.append(
            TopicSpec(
                file=str(_require(item, "file", where)),
                symbol=str(_require(item, "symbol", where)),
                relation=relation,
                enqueue_call=str(enqueue) if enqueue else None,
            )
        )
    return tuple(specs)


def _parse_http(raw: object) -> HttpConfig:
    if not isinstance(raw, dict):
        raise CrossEdgeBuildError("config", "retrieval.graph.http 必须是对象")
    python_clients: list[PythonClient] = []
    for index, item in enumerate(raw.get("python_clients", []) or []):
        where = f"retrieval.graph.http.python_clients[{index}]"
        if not isinstance(item, dict):
            raise CrossEdgeBuildError("config", f"{where} 必须是对象")
        python_clients.append(
            PythonClient(
                file=str(_require(item, "file", where)),
                klass=str(_require(item, "class", where)),
                target=str(_require(item, "target", where)),
            )
        )
    ts_clients: list[TsClient] = []
    for index, item in enumerate(raw.get("ts_clients", []) or []):
        where = f"retrieval.graph.http.ts_clients[{index}]"
        if not isinstance(item, dict):
            raise CrossEdgeBuildError("config", f"{where} 必须是对象")
        ts_clients.append(
            TsClient(
                file=str(_require(item, "file", where)),
                target=str(_require(item, "target", where)),
                name=str(_require(item, "name", where)),
            )
        )
    # 方法名到 HTTP 动词：值为 null 表示动词由第一个实参给出（`_request("PUT", ...)`）。
    methods = raw.get("python_methods") or {"_request": None, "_get": "GET", "_post": "POST"}
    if not isinstance(methods, dict):
        raise CrossEdgeBuildError("config", "retrieval.graph.http.python_methods 必须是对象")
    helpers = raw.get("ts_helpers") or {
        "fetch_join": "joinBaseUrl",
        "fetch_direct": "backendUrl",
        "request_json": "requestJson",
    }
    if not isinstance(helpers, dict):
        raise CrossEdgeBuildError("config", "retrieval.graph.http.ts_helpers 必须是对象")
    return HttpConfig(
        python_clients=tuple(python_clients),
        python_methods={str(k): (str(v) if v else None) for k, v in methods.items()},
        ts_clients=tuple(ts_clients),
        ts_helpers={str(k): str(v) for k, v in helpers.items()},
    )


def _parse_assertions(raw: object) -> Assertions:
    if raw is None:
        return Assertions((), None, (), {})
    if not isinstance(raw, dict):
        raise CrossEdgeBuildError("config", "retrieval.graph.assertions 必须是对象")
    handlers: list[dict[str, str]] = []
    for index, item in enumerate(raw.get("route_handler", []) or []):
        where = f"retrieval.graph.assertions.route_handler[{index}]"
        if not isinstance(item, dict):
            raise CrossEdgeBuildError("config", f"{where} 必须是对象")
        handlers.append(
            {
                "service": str(_require(item, "service", where)),
                "method": str(_require(item, "method", where)).upper(),
                "path": str(_require(item, "path", where)),
                "file": str(_require(item, "file", where)),
                "handler_contains": str(_require(item, "handler_contains", where)),
            }
        )
    topic_relations: dict[str, tuple[str, ...]] = {}
    for topic, relations in (raw.get("topic_relations") or {}).items():
        topic_relations[str(topic)] = _str_tuple(
            relations, f"retrieval.graph.assertions.topic_relations[{topic}]"
        )
    per_service = raw.get("route_per_service")
    return Assertions(
        route_handler=tuple(handlers),
        route_per_service=str(per_service) if per_service else None,
        http_methods=_str_tuple(
            raw.get("http_methods", []) or [],
            "retrieval.graph.assertions.http_methods",
        ),
        topic_relations=topic_relations,
    )


def load(repo_root: Path) -> GraphConfig:
    config_path = repo_root / ".mmw.json"
    if not config_path.is_file():
        raise CrossEdgeBuildError("config", f"没有 {config_path}，先跑 mmw init")
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CrossEdgeBuildError("config", f"{config_path} 读不出来：{exc}") from exc
    section = ((raw.get("retrieval") or {}).get("graph")) or {}
    if not isinstance(section, dict):
        raise CrossEdgeBuildError("config", "retrieval.graph 必须是对象")
    services = _str_tuple(
        section.get("services", []) or [], "retrieval.graph.services"
    )
    routes = _parse_routes(section["routes"]) if section.get("routes") else None
    ipc = _parse_ipc(section["ipc"]) if section.get("ipc") else None
    topics = _parse_topics(section.get("topics") or [])
    http = _parse_http(section["http"]) if section.get("http") else None
    if (routes or http) and not services:
        raise CrossEdgeBuildError(
            "config", "配了 routes 或 http 就必须列出 retrieval.graph.services"
        )
    return GraphConfig(
        services=services,
        routes=routes,
        ipc=ipc,
        topics=topics,
        http=http,
        assertions=_parse_assertions(section.get("assertions")),
        # 这几个根目录下的东西不该出现在图里。graphify 自己读 .graphifyignore，
        # 这一层是发布前的双保险：漏进去一次，此后每次问「谁引用了它」都会答出
        # 归档里的旧代码。
        exclude_roots=_str_tuple(
            section.get("exclude_roots", []) or [], "retrieval.graph.exclude_roots"
        ),
    )
