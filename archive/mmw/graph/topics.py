"""消息主题：谁往这个主题写、谁把它排空、谁消费它。

三侧各有一份权威清单（一个常量），互相之间没有任何静态引用——生产方写下字符串，
消费方也写下同一个字符串，中间隔着一条队列。这里把三份清单里的同名主题连到同一
个主题节点上，于是「这个主题少了消费方」这种缺陷在图上直接看得见。

只读字面量。主题名要是算出来的，那一条记进 unresolved，不猜。
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from .config import TopicSpec
from .fragment import (
    CrossEdgeBuildError,
    GraphFragmentBuilder,
    UnresolvedItem,
    coverage,
    link,
    node,
)


def _literal_strings(
    tree_node: ast.AST, assignments: dict[str, ast.AST]
) -> list[tuple[str, int]]:
    """把一个表达式摊成 (字符串, 行号) 列表。展不开就抛 ValueError。"""
    if isinstance(tree_node, ast.Constant) and isinstance(tree_node.value, str):
        return [(tree_node.value, tree_node.lineno)]
    if isinstance(tree_node, (ast.List, ast.Tuple, ast.Set)):
        return sum((_literal_strings(e, assignments) for e in tree_node.elts), [])
    if isinstance(tree_node, ast.Name) and tree_node.id in assignments:
        return _literal_strings(assignments[tree_node.id], assignments)
    raise ValueError(type(tree_node).__name__)


def _top_level_assignments(tree: ast.Module) -> dict[str, ast.AST]:
    assigns: dict[str, ast.AST] = {
        n.targets[0].id: n.value
        for n in tree.body
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Name)
    }
    assigns.update(
        {
            n.target.id: n.value
            for n in tree.body
            if isinstance(n, ast.AnnAssign)
            and isinstance(n.target, ast.Name)
            and n.value is not None
        }
    )
    return assigns


def extract_topic_edges(
    repo_root: Path, builder: GraphFragmentBuilder, specs: tuple[TopicSpec, ...]
) -> tuple[dict[str, object], list[UnresolvedItem]]:
    total = resolved = 0
    unresolved: list[UnresolvedItem] = []
    topic_sets: dict[str, set[str]] = {}
    for spec in specs:
        path = repo_root / spec.file
        if not path.is_file():
            raise CrossEdgeBuildError("sync", f"主题清单文件不在：{spec.file}")
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        assigns = _top_level_assignments(tree)
        if spec.symbol not in assigns:
            raise CrossEdgeBuildError("sync", f"{spec.file} 里没有 {spec.symbol}")
        value = assigns[spec.symbol]
        try:
            if isinstance(value, ast.Dict):
                # 表的键就是主题名，值是模型或处理函数。
                values = sum(
                    (_literal_strings(k, assigns) for k in value.keys if k), []
                )
            elif isinstance(value, ast.Subscript):
                # 形如 `SyncTopic = Literal["a", "b"]`。
                values = _literal_strings(value.slice, assigns)
            else:
                values = _literal_strings(value, assigns)
        except ValueError as exc:
            raise CrossEdgeBuildError(
                "sync", f"{spec.symbol} 展不开：{exc}"
            ) from exc
        bucket = topic_sets.setdefault(spec.relation, set())
        bucket.update(v for v, _ in values)
        if spec.enqueue_call:
            # 权威清单之外还有直接调用入队的地方，那些主题同样算生产方。
            for call in ast.walk(tree):
                if not (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == spec.enqueue_call
                ):
                    continue
                topic_arg = next(
                    (kw.value for kw in call.keywords if kw.arg == "topic"), None
                )
                if topic_arg is None:
                    continue
                try:
                    call_values = _literal_strings(topic_arg, assigns)
                except ValueError as exc:
                    unresolved.append(
                        UnresolvedItem(
                            "sync_topic",
                            spec.file,
                            call.lineno,
                            f"主题名是算出来的：{exc}",
                        )
                    )
                    continue
                values.extend(call_values)
                bucket.update(v for v, _ in call_values)
        for topic, line in values:
            digest = hashlib.sha256(topic.encode()).hexdigest()[:12]
            topic_id = f"sync-topic::{topic}"
            role_id = f"{spec.prefix}::{spec.file}::L{line}::C0::T{digest}"
            # 主题节点的位置取第一个发现它的那一侧。遍历序由配置里 specs 的顺序决定，
            # 所以同一份配置每次建出来的图都一样。
            if topic_id not in builder.nodes:
                builder.add_node(
                    node(
                        topic_id,
                        f"sync topic {topic}",
                        spec.file,
                        line,
                        {"kind": "sync_topic", "topic": topic},
                    )
                )
            builder.add_node(
                node(
                    role_id,
                    f"{spec.prefix.split('-')[1]} {topic}",
                    spec.file,
                    line,
                    {
                        "kind": spec.prefix,
                        "topic": topic,
                        "role": spec.relation,
                        "authority": spec.symbol,
                    },
                )
            )
            builder.add_link(
                link(
                    role_id,
                    topic_id,
                    spec.relation,
                    spec.file,
                    line,
                    {"topic": topic, "role": spec.relation},
                )
            )
            total += 1
            resolved += 1
    producer = topic_sets.get("produces_topic", set())
    drain = topic_sets.get("drains_topic", set())
    consumer = topic_sets.get("consumes_topic", set())
    return coverage(
        total + len(unresolved),
        resolved,
        len(unresolved),
        producer_topics=len(producer),
        drain_topics=len(drain),
        consumer_topics=len(consumer),
        producer_not_drained=sorted(producer - drain),
        producer_not_consumed=sorted(producer - consumer),
        drain_not_produced=sorted(drain - producer),
        drain_not_consumed=sorted(drain - consumer),
        consumer_not_produced=sorted(consumer - producer),
        consumer_not_drained=sorted(consumer - drain),
    ), unresolved
