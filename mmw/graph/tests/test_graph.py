"""跨语言边构建的测试。

路由那一类不在这里：它要把仓库的应用真的构造出来，需要那个仓库自己的依赖环境。
它的验证方式是在真仓库上重建一次，跟已知的边数逐条比对。这里覆盖其余三类、配置
解析、词法扫描，以及自检与断言在什么情况下会断。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from graph import config as config_module  # noqa: E402
from graph import tslex  # noqa: E402
from graph.build import build  # noqa: E402
from graph.fragment import (  # noqa: E402
    CrossEdgeBuildError,
    GraphFragmentBuilder,
    coverage,
    link,
    node,
    normalize_route_template,
)

# ---------------------------------------------------------------- 路由模板归一


@pytest.mark.parametrize(
    ("raw", "want"),
    [
        ("/health", "/health"),
        ("//api/v1/items/", "/api/v1/items"),
        ("/items/{item_id}", "/items/{param}"),
        ("/items/{item_id:int}", "/items/{param}"),
        ("/", "/"),
    ],
)
def test_归一路由模板(raw: str, want: str) -> None:
    assert normalize_route_template(raw) == want


def test_相对路径的路由被拒() -> None:
    with pytest.raises(CrossEdgeBuildError):
        normalize_route_template("api/v1/items")


def test_参数名不同的同一条路由归一成同一个() -> None:
    assert normalize_route_template("/x/{id}") == normalize_route_template("/x/{uid}")


# ---------------------------------------------------------------- 片段构造


def _fixture_node(node_id: str = "one", label: str = "one") -> dict[str, object]:
    return node(node_id, label, "src/example.py", 1, {"kind": "fixture"})


def test_同一个节点写两次不冲突() -> None:
    builder = GraphFragmentBuilder()
    builder.add_node(_fixture_node())
    builder.add_node(_fixture_node())
    assert len(builder.nodes) == 1


def test_同一个_id_内容不同当场断() -> None:
    builder = GraphFragmentBuilder()
    builder.add_node(_fixture_node())
    with pytest.raises(CrossEdgeBuildError, match="身份冲突"):
        builder.add_node(_fixture_node(label="别的"))


def test_边的端点不在节点表里就断() -> None:
    builder = GraphFragmentBuilder()
    builder.add_node(_fixture_node())
    builder.add_link(link("one", "missing", "handles_route", "src/example.py", 1, {}))
    with pytest.raises(CrossEdgeBuildError, match="端点"):
        builder.payload({}, [])


def test_关系不在白名单里就断() -> None:
    builder = GraphFragmentBuilder()
    with pytest.raises(CrossEdgeBuildError, match="不认识的关系"):
        builder.add_link(link("a", "b", "invented_relation", "src/x.py", 1, {}))


def test_行号必须为正() -> None:
    with pytest.raises(CrossEdgeBuildError):
        node("x", "x", "src/x.py", 0, {})


def test_覆盖率加不起来就断() -> None:
    with pytest.raises(CrossEdgeBuildError, match="算术"):
        coverage(10, 5, 2)


def test_空覆盖率的支持率是零() -> None:
    assert coverage(0, 0, 0)["support_rate"] == 0.0


# ---------------------------------------------------------------- 词法扫描


def test_注释里的调用点不算数() -> None:
    text = """
    // ipcMain.handle(IPC_CHANNELS.FAKE, ...)
    /* ipcRenderer.invoke(IPC_CHANNELS.ALSO_FAKE) */
    const real = 1;
    """
    values = [token[1] for token in tslex.tokens(text)]
    assert "ipcMain" not in values
    assert "ipcRenderer" not in values
    assert "real" in values


def test_字符串字面量整体成一个_token() -> None:
    tokens = tslex.tokens('const path = "/api/v1/hold";')
    strings = [token for token in tokens if token[0] == "str"]
    assert [token[1] for token in strings] == ["/api/v1/hold"]


def test_读常量表() -> None:
    text = 'const IPC_CHANNELS = {\n  PING: "app:ping",\n  PONG: "app:pong",\n};'
    table = tslex.constant_object(text, "src/main/ipc.ts", "IPC_CHANNELS")
    assert table["PING"][0] == "app:ping"
    assert table["PONG"][1] == 3


def test_常量表出现两次就断() -> None:
    text = 'const IPC_CHANNELS = { A: "a" };\nconst IPC_CHANNELS = { B: "b" };'
    with pytest.raises(CrossEdgeBuildError, match="不唯一"):
        tslex.constant_object(text, "src/main/ipc.ts", "IPC_CHANNELS")


def test_常量表键重复就断() -> None:
    text = 'const IPC_CHANNELS = { A: "a", A: "b" };'
    with pytest.raises(CrossEdgeBuildError, match="键重复"):
        tslex.constant_object(text, "src/main/ipc.ts", "IPC_CHANNELS")


# ---------------------------------------------------------------- 配置解析


def _write_config(repo: Path, graph_section: dict[str, object]) -> None:
    (repo / ".mmw.json").write_text(
        json.dumps({"version": 1, "retrieval": {"graph": graph_section}}),
        encoding="utf-8",
    )


def test_没有配置文件就说清楚(tmp_path: Path) -> None:
    with pytest.raises(CrossEdgeBuildError, match="mmw init"):
        config_module.load(tmp_path)


def test_四类边都没配时未启用(tmp_path: Path) -> None:
    _write_config(tmp_path, {})
    assert config_module.load(tmp_path).enabled is False


def test_主题的关系名不认识就断(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        {"topics": [{"file": "a.py", "symbol": "T", "relation": "emits_topic"}]},
    )
    with pytest.raises(CrossEdgeBuildError, match="relation"):
        config_module.load(tmp_path)


def test_关系名决定节点前缀(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        {"topics": [{"file": "a.py", "symbol": "T", "relation": "drains_topic"}]},
    )
    assert config_module.load(tmp_path).topics[0].prefix == "sync-drain"


def test_provider_要写成文件加函数名(tmp_path: Path) -> None:
    _write_config(tmp_path, {"services": ["a"], "routes": {"provider": "probe.py"}})
    with pytest.raises(CrossEdgeBuildError, match="函数名"):
        config_module.load(tmp_path)


def test_配了路由却没列服务就断(tmp_path: Path) -> None:
    _write_config(tmp_path, {"routes": {"provider": "probe.py:collect"}})
    with pytest.raises(CrossEdgeBuildError, match="services"):
        config_module.load(tmp_path)


def test_只认得_fastapi_的路由表(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        {
            "services": ["a"],
            "routes": {"provider": "p.py:c", "framework": "django"},
        },
    )
    with pytest.raises(CrossEdgeBuildError, match="fastapi"):
        config_module.load(tmp_path)


# ---------------------------------------------------------------- 三类边的集成


@pytest.fixture()
def 假仓库(tmp_path: Path) -> Path:
    """一个有 Electron 壳、消息主题和两侧 HTTP 客户端的最小仓库。"""
    repo = tmp_path / "repo"
    (repo / "shell/src/main").mkdir(parents=True)
    (repo / "shell/src/renderer").mkdir(parents=True)
    (repo / "src/svc").mkdir(parents=True)
    (repo / "web/src").mkdir(parents=True)

    (repo / "shell/src/main/ipc.ts").write_text(
        'export const IPC_CHANNELS = {\n'
        '  SAVE: "doc:save",\n'
        '  LOAD: "doc:load",\n'
        '};\n',
        encoding="utf-8",
    )
    (repo / "shell/src/main/handlers.ts").write_text(
        'import { IPC_CHANNELS } from "./ipc";\n'
        "ipcMain.handle(IPC_CHANNELS.SAVE, save);\n"
        "ipcMain.on(IPC_CHANNELS.LOAD, load);\n",
        encoding="utf-8",
    )
    (repo / "shell/src/renderer/app.ts").write_text(
        'import { IPC_CHANNELS } from "../main/ipc";\n'
        "ipcRenderer.invoke(IPC_CHANNELS.SAVE, doc);\n"
        "ipcRenderer.send(IPC_CHANNELS.LOAD);\n",
        encoding="utf-8",
    )

    (repo / "src/svc/topics.py").write_text(
        'PRODUCED = ["doc.saved", "doc.deleted"]\n', encoding="utf-8"
    )
    (repo / "src/svc/consumer.py").write_text(
        'from typing import Literal\n\nConsumed = Literal["doc.saved"]\n',
        encoding="utf-8",
    )

    (repo / "src/svc/client.py").write_text(
        "class ApiClient:\n"
        "    def save(self):\n"
        '        return self._post("/api/docs")\n'
        "    def read(self):\n"
        '        return self._get("/api/docs/{doc_id}")\n'
        "    def drop(self):\n"
        '        return self._request("DELETE", "/api/docs/{doc_id}")\n'
        "    def _request(self, method, path):\n"
        "        return self._request(method, path)\n",
        encoding="utf-8",
    )
    (repo / "web/src/client.ts").write_text(
        'export async function listDocs() {\n'
        '  return fetch(backendUrl("/api/docs"));\n'
        "}\n"
        "export async function createDoc(body) {\n"
        '  return fetch(backendUrl("/api/docs"), jsonInit(body));\n'
        "}\n",
        encoding="utf-8",
    )

    _write_config(
        repo,
        {
            "services": ["svc"],
            "ipc": {"shells": ["shell"]},
            "topics": [
                {
                    "file": "src/svc/topics.py",
                    "symbol": "PRODUCED",
                    "relation": "produces_topic",
                },
                {
                    "file": "src/svc/consumer.py",
                    "symbol": "Consumed",
                    "relation": "consumes_topic",
                },
            ],
            "http": {
                "python_clients": [
                    {"file": "src/svc/client.py", "class": "ApiClient", "target": "svc"}
                ],
                "ts_clients": [
                    {"file": "web/src/client.ts", "target": "svc", "name": "WebClient"}
                ],
            },
        },
    )
    return repo


def _build_fixture(repo: Path) -> dict[str, object]:
    output = repo / "cross.json"
    build(repo, output)
    return json.loads(output.read_text(encoding="utf-8"))


def _relations(graph: dict[str, object]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in graph["links"]:  # type: ignore[index]
        counts[item["relation"]] = counts.get(item["relation"], 0) + 1
    return counts


def test_三类边都建得出来(假仓库: Path) -> None:
    counts = _relations(_build_fixture(假仓库))
    assert counts["ipc_handles"] == 2
    assert counts["ipc_invokes"] == 2
    assert counts["produces_topic"] == 2
    assert counts["consumes_topic"] == 1
    assert counts["http_calls"] == 5


def test_两侧引用同一个频道时连到同一个节点(假仓库: Path) -> None:
    graph = _build_fixture(假仓库)
    save = [
        item
        for item in graph["links"]  # type: ignore[index]
        if item["target"] == "ipc-channel::shell::doc:save"
    ]
    assert {item["relation"] for item in save} == {"ipc_handles", "ipc_invokes"}


def test_生产方与消费方连到同一个主题(假仓库: Path) -> None:
    graph = _build_fixture(假仓库)
    saved = [
        item
        for item in graph["links"]  # type: ignore[index]
        if item["target"] == "sync-topic::doc.saved"
    ]
    assert {item["relation"] for item in saved} == {"produces_topic", "consumes_topic"}


def test_动词由实参给出的调用也解析得出来(假仓库: Path) -> None:
    graph = _build_fixture(假仓库)
    methods = {
        item["metadata"]["method"]
        for item in graph["links"]  # type: ignore[index]
        if item["relation"] == "http_calls"
    }
    assert methods == {"GET", "POST", "DELETE"}


def test_自己递归的_wrapper_不算调用点(假仓库: Path) -> None:
    graph = _build_fixture(假仓库)
    callers = [
        item
        for item in graph["nodes"]  # type: ignore[index]
        if item["metadata"].get("kind") == "http_caller"
        and item["source_file"] == "src/svc/client.py"
    ]
    assert len(callers) == 3


def test_没有_init_也没有_jsonInit_的是_GET(假仓库: Path) -> None:
    graph = _build_fixture(假仓库)
    ts_calls = {
        (item["metadata"]["method"], item["metadata"]["route_template"])
        for item in graph["links"]  # type: ignore[index]
        if item["relation"] == "http_calls"
        and item["source_file"] == "web/src/client.ts"
    }
    assert ts_calls == {("GET", "/api/docs"), ("POST", "/api/docs")}


def test_配了那一类却一条边都没有就断(假仓库: Path, tmp_path: Path) -> None:
    (假仓库 / "web/src/client.ts").write_text(
        "export const nothing = 1;\n", encoding="utf-8"
    )
    with pytest.raises(CrossEdgeBuildError, match="认得出的调用"):
        build(假仓库, tmp_path / "out.json")


def test_频道表里没有的键当场断(假仓库: Path, tmp_path: Path) -> None:
    (假仓库 / "shell/src/main/handlers.ts").write_text(
        "ipcMain.handle(IPC_CHANNELS.UNKNOWN, x);\n", encoding="utf-8"
    )
    with pytest.raises(CrossEdgeBuildError, match="没有这个键"):
        build(假仓库, tmp_path / "out.json")


def test_主题拓扑变了就断(假仓库: Path, tmp_path: Path) -> None:
    config = json.loads((假仓库 / ".mmw.json").read_text(encoding="utf-8"))
    config["retrieval"]["graph"]["assertions"] = {
        "topic_relations": {"doc.deleted": ["produces_topic", "consumes_topic"]}
    }
    (假仓库 / ".mmw.json").write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(CrossEdgeBuildError, match="关系集合变了"):
        build(假仓库, tmp_path / "out.json")


def test_断言里的方法没覆盖到就断(假仓库: Path, tmp_path: Path) -> None:
    config = json.loads((假仓库 / ".mmw.json").read_text(encoding="utf-8"))
    config["retrieval"]["graph"]["assertions"] = {"http_methods": ["PATCH"]}
    (假仓库 / ".mmw.json").write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(CrossEdgeBuildError, match="没有覆盖到"):
        build(假仓库, tmp_path / "out.json")


def test_产出可复现(假仓库: Path, tmp_path: Path) -> None:
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    build(假仓库, first)
    build(假仓库, second)
    assert first.read_bytes() == second.read_bytes()


def test_命令行给相对路径就拒(假仓库: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parent.parent / "build.py"),
            "--repo-root",
            "relative/path",
            "--output",
            "/tmp/out.json",
        ],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert "绝对路径" in completed.stderr
