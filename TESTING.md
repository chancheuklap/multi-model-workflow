# TESTING.md（本仓库薄层）

> 通用测试方法在 `mmw-tdd/SKILL.md`、`mmw-tdd/tests.md` 和 `mmw-tdd/mocking.md`。本文记录本仓库的目录、分层、外部边界和运行命令。两者冲突时点名具体冲突，不静默覆盖。

## 目录分层

这个仓库不按单元与集成分层，按被测面分层。三层都在 `mmw/` 下。

| 层 | 位置 | 测什么 |
| --- | --- | --- |
| 命令行为 | `mmw/cli/tests/*.sh`、`mmw/release/tests/*.sh` | 在一次性 Git 仓库上跑真命令。护栏拒绝了什么、拒绝之后破坏有没有发生、命令写出了什么文件 |
| 纯函数 | `mmw/graph/tests/test_graph.py`、`mmw/release/tests/test_release_contracts.py`、`mmw/release/tests/test_release_script_assembler.py` | 给定输入返回什么。跨语言边解析、配置解析、出包合同、脚本装配 |
| 生成产物一致性 | `mmw/cli/tests/test_materialize_skills.py`、`mmw/cli/tests/test_materialize_agents.py`、`mmw/mcp/test_graphify_ensure.py` | 技能源与角色源物化成各宿主产物时展开了什么、什么必须当场失败 |

不收「版本号五处互相相等」这类断言。它只证明复制粘贴没出错，不证明任何行为，而且改内容忘了改版本号时它照样绿。

## 外部 seam

`mmw-tdd/mocking.md` 说只在系统边界上 mock。本仓库已确认的外部边界只有两处。

- GitHub Issues 的 `gh` 命令——换成 stub 可执行文件，放进一次性 `PATH` 前缀。做法见 `mmw/cli/tests/test_issue.sh:84` 起的 stub 与 `:214` 的 `PATH` 覆盖。stub 遇到没预置的命令时写标准错误并失败，不静默返回空。
- 目标仓库本身——每个用例用 `mktemp -d` 建一次性目录再 `git init`，不碰当前 checkout。做法见 `mmw/cli/tests/guardrails.sh:26` 与 `:34-35`。

系统时间和网络不在被测路径上，没有替代方式。

## 权威源指针

测试要对本仓库已持有的值作断言时，从下表的权威源解析，不在测试里复制第二份。

| 值 | 权威源 |
| --- | --- |
| 产物类别、类别根、类别内细分规则 | `mmw/cli/artifacts.json` |
| 各角色的模型、档位与宿主覆盖 | `mmw/cli/mmw.default.json` |
| 工作目录根的默认取值 | `mmw/cli/mmw.default.json` 的 `paths` |
| Codex 角色结构 | `mmw/codex/profiles.json` |
| 检索服务器声明 | `mmw/.mcp.json` |
| 目标仓库的标签、CLI 路径与领域文档形态 | 目标仓库根的 `.mmw.json` |

## 怎么跑

```bash
bash mmw/test.sh
```

单独跑一份聚焦测试时直接给它的路径，例如 `bash mmw/cli/tests/test_artifact.sh`。

Python 部分是 PEP 723 内联脚本，依赖写在被测文件头部，由 `uv` 装。没装 `uv` 时入口把没跑的那几份列出来并非零退出，不静默跳过。

改动 `mmw/` 下的 CLI、技能源、出包、图谱或检索之后必须跑一次完整入口。

## 这个仓库特有的边界

机械校验只覆盖机器能直接判定的事实：语法与固定结构可解析、路径与文件安全、配置完整性和生成产物一致性。

产物质量、方法选择、语义真实性和完成度由技能与主 agent 判断，不进测试。不用计数、列表形状、固定阈值或豁免清单伪装成机械校验。已有校验越过这条边界时删除该校验，不增加例外分支。

扫描技能正文的测试必须排除 `mmw/skills-src/mmw-setup/`。它只保存旧背景材料，不是技能。
