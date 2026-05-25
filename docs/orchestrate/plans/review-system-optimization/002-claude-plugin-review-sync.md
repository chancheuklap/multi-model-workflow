# Claude Code Plugin Review 系统同步计划

## 目的

本文档记录如何把 review 系统优化同步回 Claude Code plugin source，也就是 `plugin/`。

目标是行为层面对齐，不是机械替换。Claude plugin 和 Codex plugin 的宿主机制不同。两边应同步共同的 review 意图和流程能力，但 dispatch 方式、hook payload、agent 命名、state 路径和 runtime 合同必须保持各自宿主原生。

执行顺序上，先完成并验证 Codex 原生优化，再按本计划同步 Claude plugin。

## 范围

同步到 `plugin/` 的内容：

- Review 输出中的证据表。
- Plan Writing 到 Final Review 流程中的跨计划合同图。
- 基于 finding 风险和修复形态的统一 repair routing。
- Repair 工作的回归证据要求。
- `review_effectiveness` 降级为可选诊断。

明确不同步的内容：

- 不增加 Intent Ledger。
- 不做 review 内容风险分层。
- 不引入 Codex PR review 产品流程。
- 不增加额外 review phase。

## Claude Plugin 边界

Claude plugin 必须保留自己的宿主合同：

- Claude plugin agent 文件是 `plugin/agents/` 下的 Markdown agents。
- Claude dispatch 保留现有 `Agent` tool 和 `SendMessage` resume 语义。
- Claude hooks 位于 `plugin/hooks/`，并使用 Claude hook payload。
- 现有 plugin review 集成，例如 `gate-codex-review.sh`、`track-review-budget.sh`、`codex-companion.mjs` review dispatch，在没有明确 plugin-side bug 时必须保留。
- State 路径和 runtime 合同保持 Claude-plugin-native，不能改写成 `.codex/multi-model-workflow/`。

不得把 Codex-only 机制移植到 `plugin/`：

- 不写 `spawn_agent` / `send_input` / `wait_agent`，除非 Claude plugin 现有文本里已经把它们作为对照说明。
- 不引入 Codex custom-agent TOML 合同。
- 不假设 Codex hook payload。
- 不引入 Codex runtime sync 行为。

## 预检：Plugin Build 和 Anchor 健康度

修改 review 内容之前，先验证 plugin 的 build anchors。

历史 audit 曾指出部分 `<!-- BEGIN: review-dispatch -->` anchor 可能和前文同行，导致 build replacement 跳过。当前 source 必须现场检查，不能把历史 finding 自动当作当前 bug。

### 源码目标

- `plugin/build/templates/review-dispatch.md.tmpl`
- `plugin/build/resolvers/review-dispatch.sh`
- `plugin/skills/**/references/` 下的 review references
- `plugin/build/tests/`

### 验收

- `plugin/build/build.sh --check` 能验证 review-dispatch 生成片段。
- `review-dispatch` anchors 独占一行，并且能被稳定替换。
- 如果 build check 和 anchor 独占行检查都通过，不为了历史 audit 记录额外制造 anchor repair commit。
- Anchor repair 不引入 Codex-native 术语。

## 工作包 1：证据表

### 改动

把同样的半结构化证据表要求加入 Claude plugin review 输出合同。

建议字段与 Codex 计划一致：

| 字段 | 含义 |
| --- | --- |
| `已读设计 / mockup / plan 来源` | Reviewer 实际读过的文档。 |
| `已检查代码或产物路径` | 已检查的文件、生成产物、state schema、hooks、templates 或文档。 |
| `已运行命令或验证` | Reviewer 实际执行过的命令或验证。 |
| `Finding 证据` | 支撑 finding 的具体路径、行号、diff、命令或行为。 |
| `假设` | 可能影响 verdict 的假设。 |
| `未验证项` | 相关但未能验证的内容。 |

### Claude Plugin 源码目标

- `plugin/build/templates/review-dispatch.md.tmpl`
- `plugin/skills/**` 下所有生成的 `review-dispatch` anchor consumer，包括 `plugin/skills/orchestrate-execution/SKILL.md` 和 `plugin/skills/**/references/` 下的 references
- `plugin/skills/codex-review/SKILL.md`，因为 ad-hoc review skill 有独立 output contract，且没有从共享 template 生成
- `plugin/build/tests/`

### 验收

- 所有 Claude plugin review dispatch prompts 都要求证据表。
- Ad-hoc review 也要求证据表。
- 如果任意 `review-dispatch` anchor consumer 或 ad-hoc review skill 丢失证据表，build tests 必须失败。

## 工作包 2：跨计划合同图

### 改动

把跨计划合同图加入 Claude plugin 的 plan-writing 流程。

Artifact 路径应与 Codex 保持一致，确保文档产物与宿主无关：

`docs/orchestrate/plans/<slug>/cross-plan-contract-map.md`

### 产生时机

- 所有 plan 文档写完后生成。
- Plan Review 阶段 review。
- Final Review 阶段再次消费。

### Claude Plugin 源码目标

- `plugin/skills/orchestrate-plan-writing/SKILL.md`
- `plugin/skills/orchestrate-plan-writing/references/plan-review-dispatch.md`
- `plugin/skills/orchestrate-plan-writing/references/plan-gates.md`
- `plugin/skills/orchestrate-final-review/references/final-review-angles.md`
- `plugin/skills/orchestrate-final-review/references/final-review-preconditions.md`
- `plugin/architecture-draft.md`
- plugin build tests 或 grep assertions

### 验收

- Claude plugin Plan Writing 在 Plan Review 前生成合同图。
- Plan Review 检查 producer、consumer、ownership 和 verification 冲突。
- Final Review 使用合同图审查集成后的跨 plan 行为。

## 工作包 3：统一修复分流

### 改动

给 Claude plugin build system 增加共享 repair-routing block，并适配 Claude-native dispatch。

### Claude Plugin 源码目标

- 新增 `plugin/build/templates/repair-routing.md.tmpl`
- 新增 `plugin/build/resolvers/repair-routing.sh`
- `plugin/skills/orchestrate-plan-writing/references/plan-review-resolution.md`
- `plugin/skills/orchestrate-execution/references/execution-repair-truncation.md`
- `plugin/skills/orchestrate-final-review/references/final-review-repair.md`
- `plugin/skills/orchestrate-execution/references/execution-release-gate.md`
- `plugin/skills/orchestrate-final-review/references/final-review-release-gate.md`
- `plugin/skills/orchestrate-workflow/references/workflow-direct-repair.md`
- `plugin/skills/orchestrate-workflow/references/bug-investigation-route.md`
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md`
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md`
- `plugin/build/tests/`

### Claude-native 分流语言

分流逻辑在概念上与 Codex 一致，但文字和机制必须使用 Claude plugin 现有语言：

| Finding / 修复形态 | Claude plugin 修复 owner |
| --- | --- |
| 范围小、本地化、意图清楚、不碰合同边界 | 允许 Coordinator Path A 自修。 |
| 同一个 pack 内的普通修复，原 worker 能胜任 | 通过 plugin 现有 agent 机制 resume 或 re-dispatch 原 pack executor。 |
| 跨模块、migration、billing、permission、runtime、共享合同、state machine、生成模板问题 | 使用 complex pack executor 路径。 |
| 根因不清 | 先使用 plugin 的 explorer 路径。 |
| 系统性 bug、重复修复失败、未知 regression | 使用 plugin 现有 `root-cause-analyst` 路径。 |
| Final Review 发现跨 plan 合同问题 | 返回一次 `NEEDS_EXECUTION`，通过 execution repair 处理。 |
| 设计、mockup 或 plan 不足以判断正确性 | 回流 Discovery 或 Plan Writing。 |
| Path A repair targeted re-review 失败 | 升级 Path B。 |

### 验收

- Repair routing 覆盖所有 Claude plugin review repair 路径，包括 formal plan / execution / final review、release gates、direct repair、bug investigation 和 multi-PR integration review。
- 共享 block 使用 Claude plugin agent names、hook names 和 resume 机制。
- Plugin 不引入 Codex-only tool names 或 state paths。
- 现有手写 targeted re-review 命令，例如 multi-PR integration re-review，要么迁入共享 `review-dispatch` template，要么明确更新为满足 plugin 的 `--resume` gate。

## 工作包 4：回归证据

### 改动

更新 Claude plugin repair agents 和 repair references，要求 accepted findings 的修复返回回归证据或明确 manual validation gate。

### Claude Plugin 源码目标

- `plugin/agents/pack-executor.md`
- `plugin/agents/complex-pack-executor.md`
- `plugin/agents/root-cause-analyst.md`
- `plugin/skills/orchestrate-workflow/references/workflow-direct-repair.md`
- `plugin/skills/orchestrate-workflow/references/bug-investigation-route.md`
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md`
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md`
- 工作包 3 触碰的 repair references
- 工作包 3 触碰的 release-gate references
- plugin tests 或 grep assertions：断言 repair return contract 包含回归证据

### 验收

- Repair agent output 包含回归证据。
- Prompt 明确避免低价值微型测试，不测试实现细节。
- Release Gate 在宣布 review repair 完成前检查证据。
- `root-cause-analyst` 修复、Coordinator Path A 修复、direct repair 修复和 multi-PR repair 修复都使用同一证据规则。

## 工作包 5：Review Effectiveness 降级

### 改动

把 Claude plugin 中的 `review_effectiveness` 从核心成熟度证明降级为可选诊断。

Claude plugin 很可能是该功能的原始来源，因此 plugin-side 降级比 Codex 降级更敏感。第一步应是 wording 和 gate status 调整，不直接删除。

### Claude Plugin 源码目标

- `plugin/architecture-draft.md`
- `plugin/scripts/verify-maturity.sh`
- `plugin/scripts/lib/review-effectiveness.sh`
- `plugin/state-schema/workflow-state-v1.json`
- `plugin/scripts/state.sh`
- 只有当 gate wording 或 maturity assertion 需要改变时，才触碰相关 tests

### 验收

- Plugin maturity 不再依赖 `review_effectiveness` 来证明 review 正确性。
- 如果为了 observability compatibility 保留字段和脚本，`verify-maturity.sh` 可以保留 existence check，但 warning generation 不能被描述为 correctness gate。
- 如果 implementation 选择让该字段真正 optional，必须在同一个 commit 里同步 schema、state 初始化和 state tests。
- 现有脚本可以暂时保留以维持兼容。
- 如后续要删除，作为单独 cleanup 处理。

## 验证

每个 plugin 工作包完成后使用 plugin-native 验证：

```bash
bash plugin/build/build.sh --check --plugin-dir plugin
bash plugin/scripts/verify-maturity.sh
bash plugin/scripts/run-all-tests.sh
```

同时检查 plugin diff：

```bash
git diff -- plugin/
```

Diff 不得引入 Codex-native host terms 到 Claude plugin runtime contracts。

## 提交顺序

Claude plugin 同步必须和 Codex source 修改分开：

1. Plugin anchor 和 build-health repair，如现场验证确实需要。
2. Plugin 证据表。
3. Plugin 跨计划合同图。
4. Plugin 统一 repair routing。
5. Plugin 回归证据合同。
6. Plugin `review_effectiveness` 降级。

不要把 Codex 和 Claude plugin source 修改混在同一个 commit 里，除非该 commit 只是记录两条路线的 documentation-only plan。

## 执行顺序

1. 完成并验证 Codex-native source optimization。
2. 对照本同步计划检查最终 Codex source changes。
3. 使用 Claude-native 机制把同样的 review-system 行为应用到 `plugin/`。
4. 运行 plugin validation。
5. 专门检查 plugin diff，确认没有误引入 Codex host terminology。
6. 按独立原子 commit 提交 plugin changes。
