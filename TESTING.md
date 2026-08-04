# TESTING.md

本仓库不保留自动化测试、测试夹具或测试套件。`archive/` 与 `vendor/` 是冻结内容，不参与活跃仓库检查。

## 提交前静态检查

```bash
shellcheck --severity=warning mmw/cli/mmw mmw/cli/adapters/*.sh mmw/cli/lib/*.sh \
  mmw/mcp/install-mcp.sh mmw/release/release-flow.sh

git diff --check
python3 mmw/codex/runtime.py materialize --check
python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
python3 -m json.tool mmw/codex/profiles.json >/dev/null
python3 -m json.tool mmw/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool mmw/.mcp-codex.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool mmw/.claude-plugin/plugin.json >/dev/null
python3 -m json.tool mmw/package.json >/dev/null
```

## 真实宿主验证

Codex App、Claude Code、Pi、Cursor 和 Windows 出包行为只能在对应真实宿主上验证。静态检查不代表这些运行路径已经通过。
