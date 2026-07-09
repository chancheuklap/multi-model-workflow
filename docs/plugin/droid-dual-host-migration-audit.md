# Droid 双宿主迁移审计(2026-07-09)

> 范围:评估 `plugin/` 在 Droid 宿主的迁移完整度,对照 Claude Code 侧(用户已满意),找出剩余缺口与完美对齐路径。前提硬约束:**Claude Code 侧使用不受任何影响**。
>
> 证据基线:本审计基于 live source(`plugin/` 当前 HEAD = `f4bef66`)+ Factory 官方文档(hooks-reference / plugins / skills / custom-droids)。所有"已验"标记均经 Read / grep / 文档核对。

## 1. 结论先行

迁移**主体已通**,本次会话修掉两处真缺口后,Droid 与 Claude 在流程语义上已对齐。剩余风险集中在**需 Droid runtime 实跑验证**的 hook payload 边界(脚本逻辑已对,但 Droid 实际 payload 字段未在真会话验过),以及一处可优化的双副本 skill 漂移风险。

| 维度 | Droid 现状 | Claude 对照 | 判定 |
|---|---|---|---|
| 入口路由(orchestrate SKILL)| 宿主中立,路径自检 | 同 | OK |
| 路径/状态平面 | `.factory/`(host.sh 自动) | `.claude/` | OK |
| 写码工人 | Task→pack-executor + worktree-build skill(plugin 内) | codex exec + worktree-build skill(hub) | OK(本次修) |
| 审闸 reviewer | Task→reviewer-* + worktree-review skill(plugin 内) | codex exec / claude sub-agent + skill(hub) | OK(本次修) |
| plan-writer | Task→plan-writer droid(已补齐 5 块方法论) | Agent→plan-writer(内联方法论) | OK(本次修) |
| investigate | Task→investigate-topic(可并行) | Workflow({scriptPath}) | OK |
| fable-advisor | Task | Agent | OK |
| hooks(4 个) | `${DROID_PLUGIN_ROOT}` 双路径回退 | `${CLAUDE_PLUGIN_ROOT}` | 逻辑 OK,payload 待真跑验 |
| commands(/attended 等) | 宿主中立 mmw 定位 | 同 | OK |
| plugin manifest(.factory-plugin) | 自动发现 skills/droids/commands/hooks | 同 | OK |

## 2. 本次会话已修的两处真缺口(commit `8054c22` + `f4bef66`)

1. **worktree skill 不随插件发布**:Droid reviewer/pack-executor 引用的 worktree-build/review 原只靠手工软链进 `~/.agents/skills`,全新装 plugin 时 skill 不存在 → worker/reviewer 全断。现已复制进 `plugin/skills/`,Droid 派发传 plugin 内绝对路径;Claude 侧外部 Codex/Claude CLI 仍读自己 hub 装的(`codex-skills/` 原样保留)。
2. **Droid plan-writer 比 Claude 薄 10x,缺 5 块方法论**(Plan Header 模板 / 拆小 issue / Return Contract / three-failure / 核心原则)。其中 Return Contract 的 `Cross-plan touchpoints` 区块是主线程合同回填的入口 → 功能性断链。已内联补齐(工具名按 Droid 适配,去 Skill 依赖),dispatch 补传 `plan-self-check.md` 路径。

两处都保证 Claude 侧零改动。

## 3. 架构原则(完美对齐靠它)

Droid 子代理**上下文隔离、不自动加载 skill**,只知道(a)自己 .md 写的 + (b)dispatch prompt 传的。因此"Droid 侧薄"成立的两条充要条件:

1. **方法论单源进 plugin/skills/**(随插件发布,Droid 够得到);Claude 侧外部 CLI 读自己 hub 装的同名 skill(两副本同方法论、宿主框架各异)。
2. **dispatch 传绝对路径**给子代理,不赌自动加载。

按这两条判每个 droid 该多薄:

| droid | 方法论谁扛 | 该薄/该厚 |
|---|---|---|
| reviewer ×6 / pack-executor | worktree-{review,build} skill(dispatch 传路径) | 薄得合理,不动 |
| review-coordinator | review-brief.md(全步骤) | 薄得合理,不动 |
| fable-advisor | 自带 | 已厚,不动 |
| plan-writer | task-pack.md + plan-self-check.md(dispatch 传路径)+ 内联 5 块 | 已补齐 |
| investigate-topic / code-explorer | 简单取证,自带输出契约 | 已补契约 |

## 4. 剩余风险与建议(按优先级)

| # | 风险 | 证据 | 建议 | 优先级 |
|---|---|---|---|---|
| R1 | hook 在真 Droid 会话的 payload 字段未验过 | **脚本侧已验**(2026-07-09):用 Droid 官方完整 payload(`hook_event_name`/`source`/`tool_name`/`tool_input`/`stop_hook_active`/`cwd`)喂 4 个 hook——guard-redline 输出 `permissionDecision:"ask"`+`hookEventName:"PreToolUse"`、session-triage stdout 注入 `host=droid`、record-step 读 `.tool_input.command` 不崩、guard-loop exit-2 顶回未完成 review loop。`test_hooks.sh`(35 断言)亦已覆盖两宿主共有的 `tool_input.command` 字段。剩"真 Droid 会话触发"是平台行为,脚本侧无不确定性 | 剩一步:真 Droid 会话 `droid --debug` 确认 4 个 hook 实际触发 + SessionStart stdout 注入 context | 低(仅平台侧验) |
| R2 | worktree skill 两副本(plugin/skills + codex-skills)会漂移 | **已单源化(甲路线)**:`codex-skills/worktree-{build,review}` 改成软链→`../plugin/skills/worktree-{build,review}`(git mode 120000)。源唯一在 `plugin/skills/`(宿主中立版)。Claude 侧 Codex CLI 经 `~/.agents/skills` 软链链最终读到 `plugin/skills/` 中立版(称呼从"你(Codex)被主线程 Claude 派进..."变"你(落地执行者)被主线程派进...",方法论 references 不变、功能不变)。`test_skill_parity.sh` 升级为 14 断言,守护软链完整 + SKILL.md + references 全单源一致;有人把软链改回真实目录就 FAIL | 改 `plugin/skills/` 一处两宿主自动同步,不会再漂移 | 已解决(甲) |
| R3 | hooks.json 双路径 `\|\|` 回退略脆 | **已修**:hooks.json 4 个 command 改成 `if [ -n "${DROID_PLUGIN_ROOT:-}" ]; then ...; else ...; fi` 守卫。原 `A \|\| B` 在 guard-loop exit-2(正常顶回)时会落到 CLAUDE 路径报噪;现按宿主只跑一段,失败就失败 | 已修,JSON valid + test_hooks 35 绿 + 4 command bash -n 过 | 已解决 |
| R4 | Droid 无 `Skill` 工具,plan-writer 不能用 Claude 的 `codebase-design`/`ponytail` skill | Claude agent 调 `Skill({skill:"codebase-design"})`,Droid droid 已改成直接 Read CLAUDE.md + Grep/Glob 探代码 | **已决定:不做**。当前 plan-writer 能写出合格计划,搬 codebase-design/ponytail 进 plugin 是中等工程且过度设计风险;Droid 侧探代码用 Read+Grep+Glob 已覆盖需求 | 已关闭(不做) |

## 5. "Claude 不受影响"的保证机制

- `plugin/skills/orchestrate/` 内所有 reference 宿主中立,Claude 路径(`codex exec` / `claude -p` / Agent)一字未改。
- `codex-skills/` 原样保留,Claude 侧 Codex CLI 仍读 `~/.agents/skills/` 装的。
- hooks.json 双路径回退,Claude 侧 `${CLAUDE_PLUGIN_ROOT}` 照常生效。
- Droid 派发路径(worker.sh build_prompt / review.sh overlay)用 `mmw_host()` 分流,Claude 分支保持原 prompt 措辞(测试断言守护:`test_review.sh` 验 Claude brief 仍含 `worktree-review skill,按 stage=X`、无 `codex exec` 串到 Droid)。
- 全量测试 466 断言 + build check 绿,Claude 路径行为未变。

## 6. 验证门槛(后续真跑 Droid 时)

```bash
# source 侧(已绿)
for t in plugin/scripts/tests/test_*.sh; do bash "$t" || break; done
bash plugin/build/build.sh --check

# runtime 侧(R1:真 Droid 会话验)
droid --debug  # 看 4 个 hook 触发 + payload + SessionStart 注入
mmw where      # Droid 主线程自检
# 跑一个小 develop 任务:investigate→propose→design→plan→build→final,逐闸看 Droid 派发对不对
```

## 7. 不建议做的事

- 不要为"统一"把 Claude `agents/plan-writer.md` 改成指 plugin reference(会动你满意的 Claude 侧,且 Claude agent 内联方法论本就无单一源可指)。
- 不要把 worktree skill 方法论搬进 `plugin/skills/orchestrate/`(那是路由 skill,方法论单源已在 worktree-{build,review} skill)。
- 不要给 Droid 加"没装 skill 也降级跑"的兜底(违反 fail-closed;没装就报错才是对的)。
- 不要把 `codex-skills/worktree-{build,review}` 软链改回真实目录(会破坏单源;`test_skill_parity.sh` 守护软链完整)。源唯一在 `plugin/skills/`。

## 8. 收尾状态(2026-07-09)

4 条风险全部关闭:R1 脚本侧已验(剩平台侧真会话触发)、R2 已单源化(甲,Claude 侧称呼中立化功能不变)、R3 已修、R4 不做。本次会话 5 个 commit:

| commit | 内容 |
|---|---|
| `8054c22` | worktree skill 随插件发布 + Droid 派发指向 plugin 内副本 + design/plan 审者单模型对齐(6.7.0→6.8.0) |
| `f4bef66` | Droid plan-writer 内联补齐 5 块方法论 + code-explorer/investigate-topic 输出契约 |
| `01709ab` | 本审计报告 |
| `d89c165` | R3 hooks.json 宿主守卫 + R2 防漂移校验初版 + R1 hook Droid payload 验 |
| (本提交) | R2 升级为单源化(甲):codex-skills 软链→plugin/skills + test_skill_parity 升级 14 断言 + README 同步 |

全量测试 490 断言绿 + build check 绿。Claude 侧零功能改动(仅 worker/reviewer 读到的 SKILL.md 称呼中立化)。
