# TESTING.md

本文只记录本仓库的测试事实。测试方法论由 `/mmw-tdd` 提供；审查方法论由 `/mmw-reviewer` 提供。

## 测试分层

| 层 | 位置 | 验证内容 |
| --- | --- | --- |
| CLI 合同 | `mmw/cli/tests/test_*.sh` | 配置、任务 worktree、issue、Wiki、领域文档、检索接入、技能引用和跨宿主派发参数 |
| Release Shell | `mmw/release/tests/test_*.sh` | finding 分类、修复派发、远端构建状态和失败清理 |
| Release Python | `mmw/release/tests/test_release_*.py` | 发布合同解析和脚本装配 |
| MCP | `mmw/mcp/test_graphify_ensure.py` | 图谱新鲜度、主仓库复用和失败边界 |
| Graph | `mmw/graph/tests/test_graph.py` | 原生抽取、跨语言边、路由桥、合并与发布校验 |
| 仓库形态 | `mmw/cli/tests/test_repository_shape.sh` | MMW 是唯一活跃插件、旧发布面只存在于归档、版本同步 |

`archive/` 和 `vendor/` 不参与活跃插件测试。

## 外部接缝

- Codex CLI：派发测试通过 PATH 前置 fake Codex，验证参数、报告路径和退出状态。
- Claude Code Agent 与 Pi subagent：Shell 测试验证 adapter 生成的宿主工具参数；真实模型判断通过安装后的烟雾测试验证。
- GitHub CLI：issue 和 Wiki 测试使用 stub 或本地 bare 仓库，不访问真实远端。
- MCP：测试启动本地 fake server，验证协议握手、工具裁剪和配置合并。
- Windows 远端构建：`mmw/release/tests/fixtures/fake-remote/` 模拟文件系统与 Task Scheduler 最终状态。

## Mac 无法自动验证的行为

以下行为需要 Windows 构建机实测，不能用假测试宣称覆盖：

- Task Scheduler 脱附会话的日志落盘。
- PowerShell 5.1 原生重定向与 UTF-16LE 转 UTF-8。
- Windows 路径长度限制。
- `run-release.ps1` 在真实构建机上的执行结果。

fake remote 只验证外围合同：文件上传、源码解压、旧产物清理、任务清理和危险路径拒绝。

## 版本合同

版本号必须同步：

- `mmw/.codex-plugin/plugin.json`
- `mmw/.claude-plugin/plugin.json`
- 根 `.claude-plugin/marketplace.json` 的插件版本
- 根 `.claude-plugin/marketplace.json` 的顶层版本
- `mmw/package.json`

根 Claude marketplace 只能发布一个插件，名称为 `mmw`，source 为 `./mmw`。

## 完整门控

```bash
for test_file in mmw/cli/tests/test_*.sh; do
  bash "$test_file" || exit 1
done

for test_file in mmw/release/tests/test_*.sh; do
  bash "$test_file" || exit 1
done

(cd mmw/mcp && uv run --quiet --with pytest pytest test_graphify_ensure.py -q) || exit 1
(cd mmw/graph && uv run --quiet --with pytest pytest tests/test_graph.py -q) || exit 1
(cd mmw/release/tests && uv run --quiet --with pytest --with pydantic pytest \
  test_release_contracts.py test_release_script_assembler.py -q) || exit 1

shellcheck --severity=warning mmw/cli/mmw mmw/cli/adapters/*.sh mmw/cli/lib/*.sh \
  mmw/cli/tests/test_*.sh mmw/mcp/install-mcp.sh \
  mmw/release/release-flow.sh mmw/release/tests/test_*.sh

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
