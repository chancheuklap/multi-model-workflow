# Codex Review 系统修复与优化计划

## 目的

本文档记录 `codex-orchestrate/` 这套 Codex 原生 review 系统的下一轮修复与优化计划。

目标不是增加更多 review 仪式，而是让现有 review 链条更忠于 workflow 的设计意图：

- 设计文档和 mockup 文档仍然是意图来源。Reviewer 必须直接读取这些文档，不能依赖二手摘要。
- Plan Review 要检查每份 plan 是否能落地设计意图，也要检查 plan 之间的合同是否能接上。
- Plan Implementation Review 要检查每个完成后的 plan 是否匹配已 review 的 plan、设计锚点和 mockup 锚点。
- Final Review 要检查所有 plan 合并后的整体结果，而不是只确认每个 plan 单独通过。
- 修复分流依据 finding 的风险和修复形态，而不是提前给 review 内容分风险等级。
- 测试或验证证据要证明修复后的行为，不制造没有价值的细碎测试膨胀。

本计划只针对 source。除非用户明确批准单独的 runtime 步骤，否则不得把修改同步到已安装 runtime 或 plugin cache。

## 明确不做

- 不增加 Intent Ledger。意图不稳定，必须由 reviewer 重新阅读 Design 和 Mockup 文档来判断。
- 不给 review 内容做风险等级排序。所有 review 内容都同等重要。
- 不增加新的 review phase，除非现有 phase 无法表达必要检查。
- 不把 Codex PR review 或安全审查产品功能当作本 workflow 的核心要求引入。
- 不在同一个改动里删除现有 `review_effectiveness` 实现；如需删除，单独做 cleanup。
- 本计划不修改 Claude plugin source。Claude plugin 同步由第二份计划处理。

## 工作包 1：证据表

### 改动

在 review 输出合同里加入必填的半结构化证据表。

证据表的作用是让 reviewer 明确展示自己实际检查过什么。它不是意图摘要，也不能替代阅读设计文档。

建议字段：

| 字段 | 含义 |
| --- | --- |
| `已读设计 / mockup / plan 来源` | Reviewer 实际读过的文档。 |
| `已检查代码或产物路径` | 已检查的文件、生成产物、state schema、hooks、templates 或文档。 |
| `已运行命令或验证` | Reviewer 实际执行过的命令或验证。 |
| `Finding 证据` | 支撑 finding 的具体路径、行号、diff、命令或行为。 |
| `假设` | 可能影响 verdict 的假设。 |
| `未验证项` | 相关但未能验证的内容。 |

### Codex 源码目标

- `codex-orchestrate/build/templates/review-dispatch.md.tmpl`
- `codex-orchestrate/skills/codex-review/SKILL.md`
- 由 `codex-orchestrate/build/build.sh --apply` 生成的 review references
- build tests：断言 phase review prompt 和 ad-hoc Codex review prompt 都包含证据表

### 实施说明

`review-dispatch.md.tmpl` 是主要入口，因为它已经承载了共享 review 行为：confidence rubric、pre-emit verification、rationalization prevention 和 bias indicators。

`codex-review/SKILL.md` 需要单独修改，因为 ad-hoc review 不完全依赖生成后的 phase reference。它即使不进入正式 Orchestrate phase，也必须使用同样的证据纪律。

### 验收

- 所有生成的 `review-dispatch` consumer 都必须要求证据表，包括 Design Review、Plan Review、Plan Implementation Review、Final Review、Release Gate、Multi-PR Integration Review、direct repair review、bug fix review 和 targeted re-review。
- Ad-hoc Codex Review 也必须要求证据表，即使它有独立 prompt 合同。
- Reviewer 被要求显式填写未验证项，而不是静默省略。
- 如果任意 `review-dispatch` anchor consumer 或 ad-hoc review skill 丢失证据表，build tests 必须失败。

## 工作包 2：跨计划合同图

### 改动

在所有 implementation plan 写完之后、Plan Review 开始之前，生成一份跨计划合同图。

这不是 Intent Ledger。它只记录明确的跨 plan 连接面：共享接口、state 字段、migration、生成产物、hook、合同、数据所有权、顺序假设和验证责任。

建议产物路径：

`docs/orchestrate/plans/<slug>/cross-plan-contract-map.md`

建议字段：

| 字段 | 含义 |
| --- | --- |
| `连接面` | 合同、产物、state 字段、hook、route、schema、UI 行为或共享模块。 |
| `生产方 plan` | 负责创建或修改该连接面的 plan。 |
| `消费方 plan` | 依赖该连接面的 plan。 |
| `Owner` | 后续由哪个 plan 或系统负责维护。 |
| `验证方式` | 如何检查集成后的合同是否成立。 |
| `Final Review 重点` | Final Review 必须重新检查的跨 plan 风险。 |

### 产生时机

合同图应在 plan 生成之后产生，因为只有这时 plan 边界和 ownership 才可见。

合同图应在 Plan Review 阶段被 review，因为这是 implementation 前发现 plan 边界错误的最低成本节点。

合同图还应在 Final Review 阶段被再次消费，因为所有 plan 单独通过后，合并在一起仍然可能在共享合同上出错。

### Codex 源码目标

- `codex-orchestrate/skills/orchestrate-plan-writing/SKILL.md`
- `codex-orchestrate/skills/orchestrate-plan-writing/references/plan-review-dispatch.md`
- `codex-orchestrate/skills/orchestrate-plan-writing/references/plan-gates.md`
- `codex-orchestrate/skills/orchestrate-final-review/references/final-review-angles.md`
- `codex-orchestrate/skills/orchestrate-final-review/references/final-review-preconditions.md`
- `codex-orchestrate/architecture-draft.md`
- 相关 build tests 或 grep assertions

### 实施说明

第一版不创建脚本生成器。Coordinator 读取所有 plan 文件后直接生成 Markdown 合同图。只有当人工生成反复出错时，才考虑脚本。

合同图必须保持紧凑，只列跨 plan 合同，不列每个 plan 的全部 touched files。

### 验收

- Plan Writing 要求 Coordinator 在 Plan Review dispatch 前生成跨计划合同图。
- Plan Review 明确 review 合同图，检查 producer 缺失、consumer 缺失、ownership 冲突和不可验证合同。
- Final Review 明确使用合同图，审查从 starting commit 到 `HEAD` 的集成 diff。
- Final Review 发现跨 plan 合同需要实现层修复时，可以返回 `NEEDS_EXECUTION`。

## 工作包 3：统一修复分流

### 改动

新增共享 repair-routing 合同，供 plan review repair、execution repair、final review repair、release-gate repair、direct repair、bug investigation 和 multi-PR repair 使用。

这不是给 review 内容分风险等级，而是在 reviewer 已经发现问题之后，对 finding 和修复路径做分流。

### 分流规则

| Finding / 修复形态 | 修复 owner |
| --- | --- |
| 范围小、本地化、意图清楚、不碰合同边界 | 允许 Coordinator Path A 自修。 |
| 同一个 pack 内的普通修复，原 worker 能胜任 | resume 或重新派发原 `pack_executor`。 |
| 跨模块、migration、billing、permission、runtime、共享合同、state machine、生成模板问题 | 使用 `complex_pack_executor` 或回 execution。 |
| 根因不清 | 先派 `code_explorer` 或 `complex_code_explorer` 补证。 |
| 系统性 bug、重复修复失败、未知 regression | 使用 `root_cause_analyst`。 |
| Final Review 发现跨 plan 合同问题 | 返回一次 `NEEDS_EXECUTION`，通过 execution repair 处理。 |
| 设计、mockup 或 plan 不足以判断正确性 | 回流 Discovery 或 Plan Writing，不盲目 patch 代码。 |
| Path A 修复 targeted re-review 失败 | 升级 Path B。 |

### Codex 源码目标

- 新增 `codex-orchestrate/build/templates/repair-routing.md.tmpl`
- 新增 `codex-orchestrate/build/resolvers/repair-routing.sh`
- `codex-orchestrate/skills/orchestrate-plan-writing/references/plan-review-resolution.md`
- `codex-orchestrate/skills/orchestrate-execution/references/execution-repair-truncation.md`
- `codex-orchestrate/skills/orchestrate-final-review/references/final-review-repair.md`
- `codex-orchestrate/skills/orchestrate-execution/references/execution-release-gate.md`
- `codex-orchestrate/skills/orchestrate-final-review/references/final-review-release-gate.md`
- `codex-orchestrate/skills/orchestrate-workflow/references/workflow-direct-repair.md`
- `codex-orchestrate/skills/orchestrate-workflow/references/bug-investigation-route.md`
- `codex-orchestrate/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md`
- `codex-orchestrate/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md`
- build tests：证明生成后的 repair-routing block 出现在所有目标 reference 中

### 实施说明

共享模板是必要的，因为相同的 repair decision 现在分散在多个 phase 和 route 里。没有共享合同时，同一种 serious finding 可能在不同 phase 被路由到不同强度的修复路径。

分流语言必须保持 Codex-native：`spawn_agent`、`send_input`、`wait_agent`，以及已注册 agent type，例如 `pack_executor`、`complex_pack_executor`、`code_explorer`、`complex_code_explorer`、`root_cause_analyst`。

### 验收

- 所有 review repair 路径使用同一套 finding-to-owner 规则。
- 当 finding 超出原 worker 能力时，不能因为它来自该 worker 的 plan 就强行派回弱 worker。
- Final Review 对集成后的跨 plan 故障有清晰回流路径。
- Path A 仍可用于真正小范围修复，但 Path A 失败必须升级。

## 工作包 4：回归证据，而不是自动堆测试

### 改动

要求 repair agent 对 accepted findings 返回回归证据，但不要求每个 finding 都新增一个细碎测试。

### 证据指引

| Finding 类型 | 优先证据 |
| --- | --- |
| Public behavior bug | 现有或新增 behavior / integration test。 |
| 合同、schema、migration、生成产物 bug | 合同检查、schema validation、migration check 或 build check。 |
| UI 行为 bug | Browser smoke、screenshot、DOM state validation 或现有 UI test。 |
| permission、billing、runtime、state machine、hook 问题 | integration check、state transition check、hook test 或带 owner 和步骤的 manual gate。 |
| 文档或 plan mismatch | 文档一致性证据和修正后的 source 链接。 |
| 只能环境验证的问题 | 明确 owner、命令和预期结果的 manual validation gate。 |

### Codex 源码目标

- `codex-orchestrate/agents/pack_executor.toml`
- `codex-orchestrate/agents/complex_pack_executor.toml`
- `codex-orchestrate/agents/root_cause_analyst.toml`
- `codex-orchestrate/skills/orchestrate-workflow/references/workflow-direct-repair.md`
- `codex-orchestrate/skills/orchestrate-workflow/references/bug-investigation-route.md`
- `codex-orchestrate/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md`
- 工作包 3 更新的 repair references
- 工作包 3 更新的 release-gate references
- build 或 grep tests：断言 repair return contract 包含回归证据要求

### 实施说明

证据规则应优先选择高层行为证据，不鼓励测试实现细节。系统不应该因为 review finding 而制造大量脆弱的微型单测。

如果自动测试不合理，repair 输出必须明确说明，并提供具体 manual validation gate。不能静默省略。

### 验收

- Repair 输出包含回归证据，或明确的 manual validation gate。
- Agent prompt 明确警告不要增加低价值实现细节测试。
- Release Gate 在宣布 phase 完成前检查 accepted findings 是否有证据。
- `root_cause_analyst` 修复、Coordinator Path A 修复、direct repair 修复和 multi-PR repair 修复都使用同一证据规则。

## 工作包 5：Review Effectiveness 降级

### 改动

把 `review_effectiveness` 从核心成熟度信号降级为可选诊断或历史复制指标。

这个功能同时存在于 Claude plugin source 和 Codex source。它不是 Codex 修复过程中临时发明的功能。但它目前不能帮助 review loop 做出更好的决策，因此不应成为必要 gate。

### Codex 源码目标

- `codex-orchestrate/architecture-draft.md`
- `codex-orchestrate/scripts/verify-maturity.sh`
- 只有当降级需要改 wording 或 gate 时，才触碰现有 review-effectiveness scripts 和 tests

### 实施说明

本次优化不直接删除脚本、schema 字段或 tests，除非另有单独 cleanup 计划。删除可能牵涉 state schema、validators 和兼容假设。

第一步只做 wording 和 maturity-gate 降级：

- 架构文档把它描述为可选诊断。
- `verify-maturity.sh` 不把它当作 review 系统正确性的证明。
- 现有 script / test 暂时保留，后续如要删除，另开窄范围 cleanup。

### 验收

- Review 正确性不再依赖 `review_effectiveness`。
- 不扩展该功能。
- 如后续要删除，作为单独 cleanup 处理并单独验证。

## 提交顺序

每个有意义改动单独提交：

1. 证据表。
2. 跨计划合同图。
3. 统一修复分流。
4. 回归证据。
5. `review_effectiveness` 降级。

不要把 source 修改和 runtime 同步混在一起。Runtime 同步如果获批，必须在 source 验证后作为单独步骤执行。

## 验证

Source 修改后的最低验证：

```bash
bash codex-orchestrate/build/build.sh --check --plugin-dir codex-orchestrate
bash codex-orchestrate/scripts/verify-maturity.sh
bash codex-orchestrate/scripts/run-all-tests.sh
```

Plugin manifest validation 不属于本 review-system 计划的核心范围。如果 implementation 阶段要使用 validator，必须在当时现场核实 validator 行为，而不是预设成功或失败。
