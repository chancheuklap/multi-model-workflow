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
| R1 | hook 在真 Droid 会话的 payload 字段未验过 | hooks-reference 确认 Droid 支持 `permissionDecision` + exit-2 阻断 + SessionStart/PreToolUse/PostToolUse/SubagentStop 事件名一致;guard-redline.sh 用 `.tool_input.command` + `permissionDecision:ask`,guard-loop.sh 用 exit 2,session-triage.sh 用 stdout 注入——都与 Droid 文档对得上 | 在真 Droid 会话跑一次 `droid --debug`,核对 4 个 hook 实际触发 + payload 字段 + SessionStart stdout 是否注入 context。逻辑已对,这是"验而非改" | 高(验,非改) |
| R2 | worktree skill 两副本(plugin/skills + codex-skills)会漂移 | 现两份独立,改一份不自动同步另一份 | 单源化:让 `codex-skills/worktree-{build,review}` 软链到 `plugin/skills/` 同名(Claude 安装路径不变,源唯一)。或加一个 build 校验两副本一致 | 中 |
| R3 | hooks.json 双路径 `||` 回退略脆 | `bash "${DROID_PLUGIN_ROOT}/x" \|\| bash "${CLAUDE_PLUGIN_ROOT}/x"`:Droid 侧 CLAUDE_PLUGIN_ROOT 空时第一段成功即够;但第一段非零退出会落到一段必然失败的 CLAUDE 路径报噪 | 改成宿主分流(host.sh 已有 mmw_plugin_root):command 用一个 wrapper 按 host 选路径,或两段分别 `[ -n "${DROID_PLUGIN_ROOT:-}" ] && bash ...` 守卫 | 低 |
| R4 | Droid 无 `Skill` 工具,plan-writer 不能用 Claude 的 `codebase-design`/`ponytail` skill | Claude agent 调 `Skill({skill:"codebase-design"})`,Droid droid 已改成直接 Read CLAUDE.md + Grep/Glob 探代码 | 现状可接受;若要更深代码理解,可把 codebase-design 方法论也抽进 plugin/skills 给 Droid 读 | 低 |

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
