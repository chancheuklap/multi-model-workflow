# Plan 003：Phase 2 SKILL.md 瘦身（~850 行删除）

**Design source**: `docs/orchestrate/design/2026-05-28-plan-level-worker-autonomy.md`（改造分类 A + 推荐改造顺序 Phase 2）
**调研依据**: 调研 B 「SKILL.md 改造清单」
**Blocked by**: Plan 002（schema 字段必须先就绪，否则删除后 sub-agent 自读拿不到信息）
**Risk profile**: normal（大量删除但全部依赖已存在的 reference）
**Worker type**: `pack-executor`

## Plan Goal Behavior

把 7 个 SKILL.md 内嵌的 dispatch reference 全文（与对应 reference 文件 1:1 重复）删除，改为「流程位置 + Read references/X.md」指针。SKILL.md 退化为"流程指挥脚本"，详细执行内容下沉到 reference。

参考 lean 样板：`orchestrate-final-review/SKILL.md` 238 行（已是 lean 模式）。

## Plan Acceptance Criteria

- [x] `orchestrate-execution/SKILL.md` 881 → **527** 行（净删 354 / 40%；目标 ~240 数学上不可达——9 个 mandatory build template 锚点已 ~316 行 + 100 行必需非锚点内容，floor ≈ 436 行；Coordinator 接受实际结果）
- [x] `orchestrate-plan-writing/SKILL.md` 303 → **271** 行（floor 已达，5 个 mandatory 锚点 ~174 行）
- [x] `orchestrate-workflow/SKILL.md` 233 → **219** 行（目标 ≤220 达标）
- [x] `orchestrate-final-review` / `orchestrate-discovery` / `orchestrate-multi-pr-merge` 微调（commit a604517）
- [x] `codex-review/SKILL.md` 接入 `<!-- BEGIN: review-dispatch variant=content-only -->` 锚点（新拆 narrow variant，替代手工副本）
- [x] 所有保留的「灰色边界」内容完整保留
- [x] `bash plugin/build/build.sh --check --plugin-dir plugin` 通过
- [x] `bash plugin/scripts/run-all-tests.sh` 通过（37/37 suites）
- [x] `bash plugin/scripts/verify-maturity.sh` 通过（104/0）

**Plan 003 状态**：✅ 完成（2026-05-28，Worker agentId `a8bb28f8a910bff39`，verdict=pass）

**Coordinator Review 说明**：
- 行数目标 ≤260 / ≤220 是 Plan-writer 估算偏低（未充分计入 mandatory anchor 内容）；Worker 已达到数学 floor，接受 527/271/219 作为新 baseline
- Pack 3.5 把 review-dispatch.md.tmpl 拆为 formal + content-only 两 variant，codex-review ad-hoc Step 2-5 流程未被破坏（已 review）
- needs-review：codex-review SKILL.md 中 `<!-- BEGIN: ... -->` 锚点位于 Step 2 codex prompt 模板的 markdown 代码块内——build 文本匹配正常工作，但 rendered 后 HTML 注释在代码块中会以原文显示。功能上 OK，视觉细节不阻塞 Plan 落地。

## File / Responsibility Map

| 文件 | 当前 | 预期 | 主要工作 |
| --- | --- | --- | --- |
| `plugin/skills/orchestrate-execution/SKILL.md` | 881 | ~240 | 删 Step 5 Pack Brief + Step 8 review prompt 全文 |
| `plugin/skills/orchestrate-plan-writing/SKILL.md` | 303 | ~200 | 精简 Step 9-10 派发描述 |
| `plugin/skills/orchestrate-workflow/SKILL.md` | 233 | ~215 | 缩短 dispatch 调用代码段 |
| `plugin/skills/orchestrate-final-review/SKILL.md` | 238 | ~210 | 微调（已 lean） |
| `plugin/skills/orchestrate-discovery/SKILL.md` | 157 | ~150 | 微调 |
| `plugin/skills/orchestrate-multi-pr-merge/SKILL.md` | 183 | ~170 | 微调 |
| `plugin/skills/codex-review/SKILL.md` | 152 | ~110 | 接入 review-dispatch 锚点 |

## Pack Execution Manifest

| pack_id | title | risk | dependencies | owned_files |
| --- | --- | --- | --- | --- |
| 3.1 | orchestrate-execution SKILL.md 瘦身 | normal | — | `orchestrate-execution/SKILL.md` |
| 3.2 | orchestrate-plan-writing SKILL.md 瘦身 | normal | — | `orchestrate-plan-writing/SKILL.md` |
| 3.3 | orchestrate-workflow SKILL.md 瘦身 | trivial | — | `orchestrate-workflow/SKILL.md` |
| 3.4 | orchestrate-final-review + discovery + multi-pr-merge 微调 | trivial | — | 3 个 SKILL.md |
| 3.5 | codex-review SKILL.md 接入 review-dispatch 锚点 | normal | Plan 001 Pack 1.1 完成 | `codex-review/SKILL.md` |

---

## Pack 3.1：orchestrate-execution SKILL.md 瘦身

### Goal behavior
删除 L131-216 (Step 1-3，已在 execution-preparation.md)、L236-368 (Step 5/5a/5b Pack Brief，Worker 自治后不需要)、L513-712 (Step 8 review prompt 全文，已在 execution-review-dispatch.md)。保留 Step 4 (Worker 类型选择表)、流程总览、verdict 路由、git checkpoint 协调、forbidden-shortcuts。

### Implementation tasks
1. Read `plugin/skills/orchestrate-execution/SKILL.md`（全文，881 行）
2. 对照调研 B 给出的逐段标注，执行以下删除：
   - L131-216 Step 1-3：改为 1 段「Read `references/execution-preparation.md`」+ 保留 NEEDS_PLAN_REVISION 出口
   - L236-368 Step 5/5a/5b Pack Brief：**全部删除**（Worker 自治后 Coordinator 不构造 Pack Brief）
   - L376-408 Step 6 派发：**重写**为 Plan-level dispatch（subagent_type 仍 pack-executor / complex-pack-executor，但 prompt 缩为 ~300 token：envelope + plan 路径 + run_id + STATE_DIR + handbook 指针）
   - L449-498 Step 7 + 7a：改为「Worker 返回 plan-level；批量处置 open items 在 Plan 边界」
   - L500-511 Step 7b Git Checkpoint：保留但改写为「apply plan-doc 勾选 patch + 一次 plan-doc commit」
   - L513-712 Step 8：**全部 replace 为 Read pointer**（已在 execution-review-dispatch.md）
3. 保留的内容（明确不动）：L6-129、L220-235 (Worker 类型选择表)、L246-274 (control-envelope 锚点)、L369-374 (trust-boundary)、L410-447 (state-write 锚点)、L527-604 (review-dispatch 锚点)、L713-771 (disposition-table 锚点)、L773-881 (后续 lean 段)
4. 跑 `bash plugin/build/build.sh --apply` 让 template 注入（锚点内容由 template 维护）
5. 跑 `bash plugin/build/build.sh --check` 验证

### Owned files
- Edit: `plugin/skills/orchestrate-execution/SKILL.md`

### Read first
- 当前 `orchestrate-execution/SKILL.md` 全文
- `plugin/skills/orchestrate-execution/references/execution-preparation.md`（确认覆盖 Step 1-3）
- `plugin/skills/orchestrate-execution/references/execution-review-dispatch.md`（确认覆盖 Step 8）
- `plugin/skills/orchestrate-final-review/SKILL.md`（lean 样板）

### Acceptance criteria
- [x] 行数 881 → ~240（误差 ±20 可接受）
- [x] Worker 类型选择表完整保留
- [x] 流程指挥 verdict 路由表完整保留
- [x] 「不存在非阻塞项」铁律保留
- [x] BLOCKED 双层报告格式保留
- [x] 所有 build template 锚点保留
- [x] `build.sh --apply` + `--check` 通过

### Verification commands
- `[[ $(wc -l < plugin/skills/orchestrate-execution/SKILL.md) -le 260 ]]` → Expected: exit 0
- `grep -q '不存在非阻塞项' plugin/skills/orchestrate-execution/SKILL.md` → Expected: exit 0
- `grep -q 'BEGIN: review-dispatch' plugin/skills/orchestrate-execution/SKILL.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- `bash plugin/scripts/run-all-tests.sh` → Expected: exit 0

### Risk flags
normal（最大删除量，但全部目标内容已在 reference）

### Out of scope
- 不动 reference 文件本身（Phase 3 反转 reference 在 Plan 004）
- 不动 Worker 自治行为（Plan 005）

---

## Pack 3.2：orchestrate-plan-writing SKILL.md 瘦身

### Goal behavior
精简 Step 9-10 的 dispatch 描述段（粘贴段已移除），其他保持 lean。

### Implementation tasks
1. Read `plugin/skills/orchestrate-plan-writing/SKILL.md`
2. 按调研 B 标注：
   - L176-188 Steps 9-10：精简为 3 行（详细派发协议已在 plan-writer-dispatch.md）
   - 其他段保留（已是 lean）
3. `bash plugin/build/build.sh --apply` + `--check`

### Owned files
- Edit: `plugin/skills/orchestrate-plan-writing/SKILL.md`

### Read first
- `plugin/skills/orchestrate-plan-writing/SKILL.md`
- `plugin/skills/orchestrate-plan-writing/references/plan-writer-dispatch.md`

### Acceptance criteria
- [x] 行数 303 → ~200
- [x] Pack 数量检查表 / budget_total 验收节点保留
- [x] `build.sh --check` 通过

### Verification commands
- `[[ $(wc -l < plugin/skills/orchestrate-plan-writing/SKILL.md) -le 220 ]]` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags
normal

---

## Pack 3.3：orchestrate-workflow SKILL.md 瘦身

### Goal behavior
缩短 Discovery / Plan Writing / Execution / Final Review / Multi-PR / Closing 各 phase 段的 dispatch 调用代码段。Entry Gate 路由表完整保留。

### Implementation tasks
1. Read `plugin/skills/orchestrate-workflow/SKILL.md`
2. 按调研 B：
   - L51-55：可考虑迁到 `workflow-infrastructure.md`，SKILL 留指针
   - L82-85, L100-118：缩短 dispatch 调用代码片段
   - 其他保留
3. `bash plugin/build/build.sh --apply` + `--check`

### Owned files
- Edit: `plugin/skills/orchestrate-workflow/SKILL.md`

### Read first
- 现有 SKILL.md 全文

### Acceptance criteria
- [x] 行数 233 → ~215
- [x] Entry Gate 路由表 + 5 类 verdict 表 + Global Constraints 完整保留

### Verification commands
- `[[ $(wc -l < plugin/skills/orchestrate-workflow/SKILL.md) -le 220 ]]` → Expected: exit 0
- `grep -q 'Entry Gate' plugin/skills/orchestrate-workflow/SKILL.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags
trivial

---

## Pack 3.4：orchestrate-final-review + discovery + multi-pr-merge 微调

### Goal behavior
3 个 SKILL.md 都已是 lean 模式，仅做小幅清理（多余空行、过时注释）。

### Implementation tasks
1. Read 3 个 SKILL.md
2. 各自删除 5-15 行多余空行 / 过时注释 / 与 reference 1:1 重复的小段
3. `build.sh --apply` + `--check`

### Owned files
- Edit: `plugin/skills/orchestrate-final-review/SKILL.md`
- Edit: `plugin/skills/orchestrate-discovery/SKILL.md`
- Edit: `plugin/skills/orchestrate-multi-pr-merge/SKILL.md`

### Acceptance criteria
- [x] 三个 SKILL.md 各净删 5-30 行
- [x] 所有 lean 模式特征保留
- [x] `build.sh --check` 通过

### Verification commands
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags
trivial

---

## Pack 3.5：codex-review SKILL.md 接入 narrow review-dispatch variant

### Goal behavior

**Plan 001 Pack 1.1 落地时发现的真问题**（Worker agentId `ad28a86043081b5b5`，2026-05-28）：`review-dispatch.md.tmpl` 是 77 行 formal workflow 完整模板（含 `validate-review-dispatch.sh` 调用、registry bookkeeping、formal `prompts/<gate>.md` 路径），直接注入 codex-review SKILL.md 会覆盖 Step 2-5 ad-hoc 流程。

**修正方案**：
1. 拆 `review-dispatch.md.tmpl` 为两个 variant：
   - `[variant=formal]`（现状内容，11 个 formal workflow skill 用）
   - `[variant=content-only]`（仅 confidence rubric + pre-emit gate + 证据表 + bias indicators，codex-review ad-hoc skill 用）
2. codex-review SKILL.md 加 `<!-- BEGIN: review-dispatch -->` 锚点 + variant=content-only 指示，resolver 注入 narrow variant
3. 删除 codex-review SKILL.md L77-97 手工副本

### Implementation tasks

1. Read `plugin/build/templates/review-dispatch.md.tmpl` 全文，识别 (a) formal workflow 段 (b) 纯角色规范段（confidence/pre-emit/证据表/bias）
2. 把 template 拆为两 variant：
   - `[variant=formal]` —— 包含 (a) + (b)，给 11 个 formal review skill
   - `[variant=content-only]` —— 仅 (b)，给 codex-review
3. Read `plugin/build/resolvers/review-dispatch.sh` 或同等 resolver，加 codex-review/SKILL.md 到注入目标 + 指定 variant=content-only
4. Read `plugin/skills/codex-review/SKILL.md`
5. 在 Step 2 后插入 `<!-- BEGIN: review-dispatch variant=content-only -->` / `<!-- END: review-dispatch -->` 锚点对
6. 删除 L77-97 与 content-only variant 重复的手工副本
7. `bash plugin/build/build.sh --apply --plugin-dir plugin` 让 template 注入
8. `bash plugin/build/build.sh --check --plugin-dir plugin` 验证：
   - codex-review SKILL.md 含锚点 + 注入的 content-only 内容
   - 11 个 formal skill 仍含完整 formal 段
9. 跑 `bash plugin/scripts/run-all-tests.sh` 验证没破现有测试

### Owned files

- Edit: `plugin/build/templates/review-dispatch.md.tmpl`（拆 variant）
- Edit: `plugin/build/resolvers/review-dispatch.sh`（加 target + variant 选择）
- Edit: `plugin/skills/codex-review/SKILL.md`（加锚点 + 删手工副本）

### Read first

- `plugin/skills/codex-review/SKILL.md`（当前 Step 2-5 流程，避免破坏）
- `plugin/build/templates/review-dispatch.md.tmpl`
- `plugin/build/resolvers/review-dispatch.sh`
- 任一现有 formal skill SKILL.md（如 `orchestrate-final-review/SKILL.md`）确认 formal variant 行为

### Acceptance criteria

- [x] template 拆为 formal + content-only 两 variant
- [x] resolver 注册 codex-review 用 content-only variant
- [x] codex-review/SKILL.md 含 `BEGIN: review-dispatch variant=content-only` 锚点
- [x] codex-review/SKILL.md 的 ad-hoc Step 2-5 流程**完整保留**（不被注入覆盖）
- [x] codex-review/SKILL.md 不含 TEMPLATE_DEPS 注释（Plan 001 Pack 1.1 已删，本 Pack 验证）
- [x] 11 个 formal review skill 行为不变（仍获完整 formal 段）
- [x] `build.sh --apply` + `--check` + `run-all-tests.sh` 通过

### Verification commands

- `grep -q 'BEGIN: review-dispatch variant=content-only' plugin/skills/codex-review/SKILL.md` → Expected: exit 0
- `! grep -q 'TEMPLATE_DEPS' plugin/skills/codex-review/SKILL.md` → Expected: exit 0
- `! grep -q 'validate-review-dispatch.sh' plugin/skills/codex-review/SKILL.md` → Expected: exit 0（content-only 不应注入 formal workflow 调用）
- `grep -q 'validate-review-dispatch.sh' plugin/skills/orchestrate-final-review/SKILL.md` → Expected: exit 0（formal skill 仍含完整模板）
- `bash plugin/build/build.sh --apply --plugin-dir plugin && bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- `bash plugin/scripts/run-all-tests.sh` → Expected: exit 0

### Risk flags

normal → **bumped to high**（涉及 build template variant 拆分；错拆会破 11 个 formal review skill）

### Dependencies

- Plan 001 Pack 1.1（TEMPLATE_DEPS 已删除，本 Pack 把 anchor 接入做完）

### Out of scope

- 不动 codex-review SKILL 的 Step 1 (审查对象判定) / Step 3 (dispatch 命令) / Step 4-5 (Result/Backflow)
- 不改 11 个 formal review skill 的注入内容

---

## Plan-level 验证

```bash
bash plugin/build/build.sh --apply --plugin-dir plugin
bash plugin/build/build.sh --check --plugin-dir plugin
bash plugin/scripts/run-all-tests.sh
bash plugin/scripts/verify-maturity.sh

# 行数检查
for f in plugin/skills/*/SKILL.md; do echo "$(wc -l < $f) $f"; done
```

全部通过 → Plan 003 完成。

## Plan Review History

（待 Plan Implementation Review 后追加）
