#!/usr/bin/env python3
"""_relay 把 graphify 的两条流交给调用方时丢没丢东西。

这份测试存在的原因是一个真实的坑：graphify 命令行把诊断分散在 stdout 与 stderr 上，
哪条都可能是唯一有用的那条。上一版失败时只读 stderr、成功时只读 stdout，于是

  - 名字有歧义（exit 1，候选清单在 stdout）→ 调用方只看到「exit 1」
  - 名字有歧义但能跑（exit 0，警告在 stderr）→ 调用方看到一句干净的
    「No directed path found」，也就是一个带十足信心的假阴性

后一种最坏。断言就照着这两种形状写。
"""

from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("graphify_mcp", HERE / "graphify_mcp.py")
assert _spec and _spec.loader
graphify_mcp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(graphify_mcp)

AMBIGUOUS_LIST = (
    "Ambiguous: 'main' matches 25 nodes in different files.\n"
    "  mmw-v2/mcp/resolve.py\n    id: mmw_v2_mcp_resolve_main\n"
    "Retry with the repo-relative path or the full node id."
)
AMBIGUOUS_WARNING = "warning: source match was ambiguous (top score 37852.4, runner-up 37852.4)"
NO_PATH = "No directed path found between 'main' and 'toml_table'."


def proc(returncode: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["graphify"], returncode=returncode,
                                       stdout=stdout, stderr=stderr)


class RelayTest(unittest.TestCase):
    def test_plain_success_returns_stdout_unchanged(self) -> None:
        self.assertEqual(graphify_mcp._relay(proc(0, "Shortest path (1 hops):\n  a --> b")),
                         "Shortest path (1 hops):\n  a --> b")

    def test_success_carrying_a_warning_keeps_both(self) -> None:
        """假阴性那一种：结果本身读起来很干净，警告是唯一的破绽。"""
        out = graphify_mcp._relay(proc(0, NO_PATH, AMBIGUOUS_WARNING))
        self.assertIn(NO_PATH, out)
        self.assertIn("source match was ambiguous", out)

    def test_failure_with_diagnosis_only_on_stdout(self) -> None:
        """歧义那一种：候选清单和 node id 全在 stdout，stderr 是空的。"""
        with self.assertRaises(graphify_mcp.GraphifyError) as caught:
            graphify_mcp._relay(proc(1, AMBIGUOUS_LIST, ""))
        message = str(caught.exception)
        self.assertIn("matches 25 nodes", message)
        self.assertIn("mmw_v2_mcp_resolve_main", message)

    def test_failure_with_diagnosis_only_on_stderr(self) -> None:
        with self.assertRaises(graphify_mcp.GraphifyError) as caught:
            graphify_mcp._relay(proc(1, "", "error: graph file not found: /x/graph.json"))
        self.assertIn("graph file not found", str(caught.exception))

    def test_failure_with_both_streams_keeps_both(self) -> None:
        with self.assertRaises(graphify_mcp.GraphifyError) as caught:
            graphify_mcp._relay(proc(1, AMBIGUOUS_LIST, "error: something else"))
        message = str(caught.exception)
        self.assertIn("matches 25 nodes", message)
        self.assertIn("something else", message)

    def test_failure_with_no_output_names_the_exit_code(self) -> None:
        with self.assertRaises(graphify_mcp.GraphifyError) as caught:
            graphify_mcp._relay(proc(3, "", ""))
        self.assertIn("exit 3", str(caught.exception))

    def test_empty_success_says_empty_is_not_absence(self) -> None:
        out = graphify_mcp._relay(proc(0, "", ""))
        self.assertIn("空结果不能证明关系不存在", out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
