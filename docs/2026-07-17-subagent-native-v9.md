# 2026-07-17 Subagent 原生化 v9

用户拍板:废除无头 CLI 工人轨道,roster 全员注册为 pi-subagents 正式 agent;取消一切 max_turns;general-purpose / Explore / code-explorer 统一 openai-codex/gpt-5.6-sol + thinking medium。2026-05 Claude Code subagent 压缩教训不再约束 pi 设计(记忆文件已限定范围)。

## 已验证的机制事实

- 自定义 agent 加载目录:`.pi/agents/`(项目) > `.agents/agents/`(工作区) > `~/.pi/agent/agents/`(全局);加载器跟随软链接;同名覆盖内置,整份替换(覆盖内置须自带 description / 系统提示词)。
- frontmatter:`thinking` 合法值 off/minimal/low/medium/high/xhigh/max(roster 的 reasoningEffort 一比一改名);tools 数组可解析;`max_turns` 省略且 `subagents.json` `defaultMaxTurns: 0` = 无限。
- Agent 工具无 cwd 参数;worktree 绑定靠 prompt 钉绝对路径。扩展 worktree 清理会把未提交改动 commit 到分支,不丢工作。
- agent 注册表在内存,主会话重启后 resume 失效;恢复 = 每 Pack 一提交 + 重派。
- rpiv-advisor 只注册 `advisor` 工具,不注册 agent 类型;文档里 `Agent({subagent_type:"advisor"})` 配方现在就是断的,一并修。

## 改动清单

| # | 改动 | 位置 |
|---|---|---|
| 1 | `defaultMaxTurns` 50→0 | `~/.pi/agent/subagents.json` |
| 2 | 覆盖 general-purpose / Explore:model gpt-5.6-sol、thinking medium(自带原描述与提示词) | `~/.pi/agent/agents/*.md` |
| 3 | roster 全员 `reasoningEffort`→`thinking`;code-explorer 改 medium;删 decision-advisor.md | `pi-plugin/agents-roster/` |
| 4 | roster 12 员软链进全局 agents 目录 | `~/.pi/agent/agents/` |
| 5 | 审查派发改按名字(`subagent_type: reviewer-*`),删 roster_model 间接层 | `scripts/review.sh` |
| 6 | `decision-advisor` / `subagent_type:"advisor"` 引用全部改为 advisor 工具调用 | skills references + build/fragments(改后 `build.sh --apply`) |
| 7 | pack-executor / plan-writer 改会话内 `run_in_background` agent(persist_session: true);删 `lib/pi-exec.sh` 与 PID/轮询/resume 逻辑;worktree 创建、边界门、选择性发布保留;账本瘦身为边界检查所需 | `scripts/worker.sh`、`runtime-contract.md`、`scripts/tests/` |
| 8 | 更新 runtime-contract 与测试断言(现在 grep 旧派发字符串) | 同上 |

## 验证(2026-07-17 全部完成)

- live 派发 `code-explorer`(openai-codex/gpt-5.6-sol)答真实代码问题:注册、模型解析、只读白名单全部生效。
- `scripts/tests/` 全绿(含重写后的 test_pi_worker 40 条、test_investigate 31 条);py 测试 `uv run --with pytest --with pydantic` 53 条通过;`build.sh --check` 无 DRIFT。
- e2e:真 GPT pack-executor 以注册 agent 身份后台落地最小 Pack(TDD、commit 带 `Pack 1.1`、测试绿),`mmw worker verify` 边界门通过。
- 落地 commit:`7c1a5b3`(roster 转正)、`fad0747`(v9 无头轨道废除)。
