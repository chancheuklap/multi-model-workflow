#!/usr/bin/env python3
"""upsert_grok_config 往 Grok 的 config.toml 里写服务器时做了什么。

看的是写出来的文件：Grok 能不能解析、原有内容还在不在、连写两次是不是同一份。
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import tomllib

sys.path.insert(0, str(Path(__file__).resolve().parent))

from resolve import upsert_grok_config

SERVERS = {
    "serena": {"command": "serena", "args": ["start-mcp-server", "--project-from-cwd"]},
    "graphify": {
        "command": "python3",
        "args": ["/runtime/mmw/mcp/graphify_mcp.py"],
        "env": {"GRAPHIFY_ENSURE_BIN": "/runtime/mmw/mcp/graphify_ensure.py"},
    },
    "context7": {
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp"],
        "env": {"CONTEXT7_API_KEY": "ctx7sk-test"},
    },
}

# Grok 保存配置时把内联的 env 改写成子表，就长这样。
NORMALIZED = """[cli]
installer = "internal"

[[marketplace.sources]]
name = "xAI Official"
git = "https://github.com/xai-org/plugin-marketplace.git"

[ui]
theme = "grokday"

[mcp_servers.serena]
command = "serena"
args = ["start-mcp-server", "--project-from-cwd"]
[mcp_servers.graphify]
command = "python3"
args = ["/runtime/mmw/mcp/graphify_mcp.py"]
[mcp_servers.graphify.env]
GRAPHIFY_ENSURE_BIN = "/old/path/graphify_ensure.py"

[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]
[mcp_servers.context7.env]
CONTEXT7_API_KEY = "ctx7sk-old"
"""


class GrokConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "config.toml"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, text: str) -> None:
        self.path.write_text(text, encoding="utf-8")

    def parsed(self) -> dict:
        return tomllib.loads(self.path.read_text(encoding="utf-8"))

    def test_writes_three_servers_into_empty_file(self) -> None:
        upsert_grok_config(self.path, SERVERS)
        data = self.parsed()
        self.assertEqual(set(data["mcp_servers"]), {"serena", "graphify", "context7"})
        self.assertEqual(
            data["mcp_servers"]["graphify"]["env"],
            {"GRAPHIFY_ENSURE_BIN": "/runtime/mmw/mcp/graphify_ensure.py"},
        )

    def test_replaces_env_subtable_grok_wrote(self) -> None:
        # 子表留下来的话，新写的内联 env 就是同一个 key 的第二次定义，Grok 报
        # duplicate key 起不来。所以这里先看解析得动，再看值是新的。
        self.write(NORMALIZED)
        upsert_grok_config(self.path, SERVERS)
        data = self.parsed()
        self.assertEqual(
            data["mcp_servers"]["graphify"]["env"],
            {"GRAPHIFY_ENSURE_BIN": "/runtime/mmw/mcp/graphify_ensure.py"},
        )
        self.assertEqual(
            data["mcp_servers"]["context7"]["env"], {"CONTEXT7_API_KEY": "ctx7sk-test"}
        )

    def test_keeps_other_tables(self) -> None:
        self.write(NORMALIZED)
        upsert_grok_config(self.path, SERVERS)
        data = self.parsed()
        self.assertEqual(data["cli"]["installer"], "internal")
        self.assertEqual(data["ui"]["theme"], "grokday")
        self.assertEqual(data["marketplace"]["sources"][0]["name"], "xAI Official")

    def test_keeps_array_of_tables_after_servers(self) -> None:
        # 服务器块后面的 [[…]] 曾经被当成不算数的边界，整段被吃掉。
        self.write(NORMALIZED + '\n[[marketplace.sources]]\nname = "Second"\ngit = "x"\n')
        upsert_grok_config(self.path, SERVERS)
        names = [item["name"] for item in self.parsed()["marketplace"]["sources"]]
        self.assertEqual(names, ["xAI Official", "Second"])

    def test_second_run_changes_nothing(self) -> None:
        self.write(NORMALIZED)
        upsert_grok_config(self.path, SERVERS)
        once = self.path.read_text(encoding="utf-8")
        upsert_grok_config(self.path, SERVERS)
        self.assertEqual(self.path.read_text(encoding="utf-8"), once)

    def test_file_without_trailing_newline(self) -> None:
        self.write('[cli]\ninstaller = "internal"')
        upsert_grok_config(self.path, SERVERS)
        self.assertEqual(self.parsed()["cli"]["installer"], "internal")
        self.assertIn("serena", self.parsed()["mcp_servers"])


if __name__ == "__main__":
    unittest.main()
