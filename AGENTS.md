# AGENTS.md — multi-model-workflow 维护协议

本仓库是 Codex / Claude 多代理工作流的源码和同步仓库。它的目标不是展示一套方法论，而是让 Codex 在真实项目里能自动完成：

1. 设计文档 review。
2. 计划文档 review。
3. Task Pack 切分、派发和执行。
4. 代码 review 与修复循环。
5. 未知根因调查。
6. 最终意图验证和生产风险 review。
7. 面向项目负责人的业务语言汇报。

后续 agent 进入这个仓库时，必须先按这个目的判断工作是否有效。不要把“文件存在、脚本能跑、安装成功、smoke prompt 能过”当成系统已经完整。

## 1. 源码层和运行层

这个仓库只是源码和储存层。Codex 实际使用的是安装后的 skill 和 agent 配置。

| 层级 | 路径 | 作用 |
| --- | --- | --- |
| Codex skill source | `.agents/skills/orchestrate-workflow/` | `orchestrate-workflow` skill 的源码真相 |
| Codex agent source | `codex/agents/*.toml` | 自定义 `agent_type` 指令模板 |
| Codex skill runtime | `/Users/cheuklapchan/.agents/skills/orchestrate-workflow` | Codex 实际可加载的 user-level skill |
| Codex agent runtime | `/Users/cheuklapchan/.codex/agents/*.toml` | Codex 实际可调用的自定义 subagent |
| Claude plugin source | `plugin/` | Claude Code plugin 兼容源 |

改 Codex 运行行为时，先改 source，再同步 runtime。不要只改 `/Users/cheuklapchan/.agents` 或 `/Users/cheuklapchan/.codex/agents`，也不要只改仓库 source 后忘记同步。

同步命令：

```bash
python3 codex/agents/validate-agents.py
bash codex/skills/install-orchestrate-workflow.sh --user --apply
bash codex/agents/sync-agents.sh --apply
diff -qr .agents/skills/orchestrate-workflow /Users/cheuklapchan/.agents/skills/orchestrate-workflow
for f in code-explorer code-reviewer coding-worker complex-code-explorer complex-coding-worker docs-worker release-reviewer; do
  diff -q "codex/agents/$f.toml" "/Users/cheuklapchan/.codex/agents/$f.toml"
done
```

## 2. 运行文件不是说明文档

这些文件会直接影响 Codex 行为，按执行文件维护：

- `.agents/skills/orchestrate-workflow/SKILL.md`
- `.agents/skills/orchestrate-workflow/references/*.md`
- `codex/agents/*.toml`

这些文件只写会改变行为的指令。不要写：

- 迁移背景说明。
- “这是从 Claude plugin / Superpowers / 某 GitHub skill 吸收来的”这类来源说明。
- “不是某某、不是某某”的大段定位解释。
- 方法名清单。
- 给人看的项目复盘。
- 安装说明、市场说明、README 式介绍。
- 为了证明自己理解而写的概念性段落。

允许写的内容：

- 触发条件。
- phase 顺序。
- 必读 reference。
- agent routing。
- review contract。
- worker contract。
- stop condition。
- finding severity。
- verification gate。
- sync / validation command。

如果一句话删掉后不会改变 agent 的下一步行为，就不要放进 runtime 文件。

## 3. 系统完整性的判断标准

评估这套系统是否“完成”，不能只看安装和 smoke test。必须判断它是否能端到端承接真实项目工作流。

合格标准：

- `orchestrate-workflow` 能在 design / plan 已存在后接管全流程，而不是只做代码执行。
- Phase 0a 能审设计文档的完整性、项目一致性、场景边界、合同边界和 UI/mockup 承接关系。
- Phase 0b 能审计划文档的覆盖率、真实路径、可执行性、验收标准、Task Pack 切分和风险任务。
- Phase A 能把 Task Pack 派给正确 subagent，实现后做 spec compliance 和 code quality review。
- Phase B 能把所有 pack 合起来审最终 intent，而不是只相信每个 pack 自报完成。
- 生产风险必须追加 `release_reviewer`，但不能替代 baseline `code_reviewer`。
- 未知根因必须先建立 feedback loop，再提出可证伪 hypotheses，再修复。
- worker 必须按 public behavior 做 vertical TDD，不做 horizontal slicing。
- API、Pydantic、DB、JSON、sync、billing、permission、runtime、UI action 和 helper placement 必须走正式 contract boundary。
- 最终汇报必须面向项目负责人说明产品能力、验证证据、残余风险和需要业务决策的事项。

不合格信号：

- 只说“已经安装 / 已经复制 / smoke 通过”。
- 只在 README 里提到 Claude plugin、Superpowers 或 mattpocock skills，却没有转成具体 runtime 规则。
- skill 里出现长篇解释、历史背景、方法论摘要。
- subagent TOML 只有泛泛角色描述，没有 review / implementation / diagnosis 的具体 contract。
- review 只审代码，不审 design、plan 和 final intent。
- release-risk review 覆盖掉 baseline review。
- Task Pack 按文件类型横切，而不是按可验证行为纵切。

## 4. Claude plugin 到 Codex 的转换关系

不要机械复制 Claude Code plugin 的 agent 名和 hook 名。Codex 版要转换为可用的 `agent_type` 和主线程编排。

| 原能力 | Codex 转换 |
| --- | --- |
| workflow-auditor baseline review | `code_reviewer` |
| workflow-auditor production-risk supplement | `release_reviewer` |
| pack-executor 普通实现 | `coding_worker` |
| pack-executor 高风险实现 | `complex_coding_worker` |
| root-cause-analyst 只读调查 | `complex_code_explorer` |
| root-cause-analyst 紧耦合修复 | `complex_coding_worker` |
| Claude hooks 提醒 | Codex skill 中的 phase / stop / verification gate |
| Claude plugin memory/project awareness | coordinator dispatch 明确 project anchors，agent TOML 要求读取 active project instructions |

转换的重点是保留能力，不是保留名字。`workflow-auditor`、`pack-executor`、`root-cause-analyst` 这些名字可以出现在 Claude plugin source；Codex runtime 里优先使用 Codex 的真实 agent_type。

## 5. Superpowers 和外部 skills 的吸收方式

Superpowers 和 `mattpocock/skills` 的价值必须具体转成行为规则，不要停在引用和致谢。

必须保留的行为：

- brainstorming / writing-plans 之后由 `orchestrate-workflow` 接管。
- executing-plans 的 checkpoint 思路转成 Phase 0、Phase A、Phase B。
- requesting-code-review 转成每个 phase 的 baseline review。
- receiving-code-review 转成 finding 验证、无效 finding 驳回和 repair loop。
- systematic-debugging 转成 feedback loop、hypotheses、instrumentation、focused regression。
- test-driven-development 转成 public-behavior vertical TDD。
- subagent-driven-development 转成按真实可并行 Task Pack 派发，而不是为了派发而派发。
- verification-before-completion 转成最终证据门槛。
- grill-with-docs 转成 design / plan 对项目正式文档和业务场景的挑战。
- durable brief / to-issues 转成 Task Pack brief。
- architecture improvement 转成 finding 分类、seam 判断、adapter 判断和 blocker 升级条件。
- prototype 方法只在 design 无法靠文档判断时作为 throwaway gate。

禁止做法：

- 在 runtime 文件里列“吸收了哪些 skill”。
- 把外部 skill 整套复制进来。
- 引入新的 `CONTEXT.md` 或平行规则体系。
- 用外部方法替代本系统的 Phase 0 / Phase A / Phase B 主流程。

## 6. 修改方向

当用户要求“检查这套系统是否完善”时，先做概念和行为审计：

1. 读 `.agents/skills/orchestrate-workflow/SKILL.md`。
2. 读相关 `references/*.md`。
3. 读 `codex/agents/*.toml`。
4. 对照 Claude plugin 的原始能力、Superpowers 工作流和外部 engineering skills。
5. 判断每个能力是否已经变成可执行指令。
6. 只在发现明确缺口时改 runtime source。
7. 改完同步 runtime 并验证 diff。

不要一上来检查有没有安装。安装状态只能证明文件复制成功，不能证明系统设计成立。

当用户要求“清理垃圾解释性文字”时，直接扫描 runtime source 和 agent source：

```bash
rg -n "Claude plugin|workflow-auditor|pack-executor|root-cause-analyst|装饰文档|不纳入 Runtime|来自外部|只写成方法名|不是方法名称|不安装整套|issue tracker state machine" .agents/skills/orchestrate-workflow codex/agents
```

发现解释性文字后，优先删除；如果其中含有必要行为，只改写成直接指令。

## 7. 子代理使用规则

这个仓库的工作经常是 prompt / instruction 维护。不要把简单清理委派出去。

可以委派的情况：

- 一个 agent 审 `orchestrate-workflow` skill。
- 一个 agent 审 `codex/agents/*.toml`。
- 一个 agent 对照 Claude plugin source 找能力遗漏。

不要委派的情况：

- 只需要删几段解释性文字。
- 用户正在纠正方向，主线程需要直接承担判断。
- 下一步是关键路径，主线程等一个子代理才能继续。

委派时必须明确：

- 不写长篇说明。
- 不改 runtime 以外的文档来假装完成。
- 输出具体缺口和建议 patch。
- 禁止把安装成功当成能力完整。

## 8. 对用户的沟通方式

用户不是要看方法论汇报，而是要这套系统真的可用。沟通时：

- 先给结论，再给证据。
- 少讲“我理解了什么”，多讲“我检查了什么、改了什么、同步到了哪里”。
- 用户问概念判断时，不要用 smoke test 回避设计判断。
- 用户要求执行时，直接执行，不停在方案。
- 承认方向错了以后立刻修，不要用新增文档掩盖 runtime 缺口。
- 不要把 README、审计报告、设计文档当成 runtime 能力。

## 9. 验证清单

改动收尾至少执行：

```bash
python3 codex/agents/validate-agents.py
bash -n codex/agents/sync-agents.sh
bash -n codex/skills/install-orchestrate-workflow.sh
```

如果改了 user-level runtime：

```bash
bash codex/skills/install-orchestrate-workflow.sh --user --apply
bash codex/agents/sync-agents.sh --apply
diff -qr .agents/skills/orchestrate-workflow /Users/cheuklapchan/.agents/skills/orchestrate-workflow
```

如果改了 agent TOML，还要逐个对比 `/Users/cheuklapchan/.codex/agents/*.toml`。

收尾时报告真实结果。没跑的验证不能写成已通过。
