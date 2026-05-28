# Plan 001：Phase 0 清理 + dispatch prompt 简化

**Design source**: `docs/orchestrate/design/2026-05-28-plan-level-worker-autonomy.md`（决策 1 / 第三轮决策日志）
**Issue ref**: ad-hoc 改造（不走 issue 拆分）
**Blocked by**: 无
**Risk profile**: trivial（最低风险，最先执行）
**Worker type**: `pack-executor`

## Plan Goal Behavior

清除阻碍 Document-as-Context 原则落地的两项遗留反模式，并按用户决策简化"dispatch prompt 写文件"这一步。完成后整个 plugin 的「Coordinator 副本同步」与「冗余写文件」两类负担消除。

## Plan Acceptance Criteria

- [x] `codex-review/SKILL.md` 的 `TEMPLATE_DEPS` 手工同步注释已删除（commit 7886e7a）
- [x] 孤儿 `decision-brief.md.tmpl` 模板 + resolver 已删除（commit b1f86dd）
- [x] `sendmessage-resume.md.tmpl` 移除"先 Write 到 `worker-prompts/...md`"指令，改为直接 inline SendMessage（commit eb86658）
- [x] 所有 dispatch reference 中的 `worker-prompts/` 路径引用已清理（commit 8a2decc）
- [x] `bash plugin/build/build.sh --check` 通过
- [x] `bash plugin/scripts/run-all-tests.sh` 通过（33/33）
- [x] `bash plugin/scripts/verify-maturity.sh` 通过（103/103）

**Plan 001 状态**：✅ 完成（2026-05-28，Worker agentId `ad28a86043081b5b5`，verdict=pass）

**已推迟项**：Pack 1.1 的「`<!-- BEGIN: review-dispatch -->` 锚点接入」推到 Plan 003 Pack 3.5——因 worker 发现 `review-dispatch.md.tmpl` 是 77 行 formal workflow 完整模板（含 registry / validate-review-dispatch.sh / formal prompts/ 路径），直接注入会覆盖 codex-review ad-hoc skill 的 Step 2-5 内容。Plan 003 Pack 3.5 需先拆 template variant（narrow 版仅含 confidence rubric + pre-emit gate + 证据表 + bias indicators）。

## File / Responsibility Map

| 文件 | 责任 | 操作 |
| --- | --- | --- |
| `plugin/skills/codex-review/SKILL.md` | ad-hoc review skill | Edit (L8-9 删除 TEMPLATE_DEPS) |
| `plugin/build/templates/decision-brief.md.tmpl` | 孤儿模板 | Delete |
| `plugin/build/resolvers/decision-brief.sh` | 孤儿 resolver | Delete |
| `plugin/build/templates/sendmessage-resume.md.tmpl` | SendMessage 续派模板 | Edit (变 inline) |
| 7 个 dispatch reference | 引用 worker-prompts 路径 | Edit (清理) |

## Pack Execution Manifest

| pack_id | title | risk | dependencies | owned_files (核心) |
| --- | --- | --- | --- | --- |
| 1.1 | 删除 codex-review TEMPLATE_DEPS 手工同步注释 | trivial | — | `plugin/skills/codex-review/SKILL.md` |
| 1.2 | 删除孤儿 decision-brief 模板 + resolver | trivial | — | `plugin/build/templates/decision-brief.md.tmpl`, `plugin/build/resolvers/decision-brief.sh` |
| 1.3 | 简化 sendmessage-resume.md.tmpl（取消 worker-prompts 写文件）| normal | — | `plugin/build/templates/sendmessage-resume.md.tmpl` |
| 1.4 | 清理 dispatch reference 中 worker-prompts 路径引用 | trivial | 1.3 | 各 dispatch reference 文件 |

---

## Pack 1.1：删除 codex-review TEMPLATE_DEPS 手工同步注释

### Goal behavior
消除"Coordinator 手工维护副本"反模式信号。`codex-review/SKILL.md` 的 review angles / confidence rubric / pre-emit gate / 证据表内容由 build template 注入。**本 Pack 仅删除手工同步注释；anchor 接入推到 Plan 003 Pack 3.5 处理**（需要 template 拆 variant，详见 Plan 003）。

### Implementation tasks
1. Read `plugin/skills/codex-review/SKILL.md`，定位 L8-9 的 `TEMPLATE_DEPS` HTML 注释段
2. 删除该注释段（保留正常 frontmatter 和正文）
3. **anchor 接入**：推到 Plan 003 Pack 3.5。本 Pack 不补 anchor（直接注入完整 review-dispatch.md.tmpl 会覆盖 ad-hoc skill 的 Step 2-5）
4. 跑 `bash plugin/build/build.sh --check --plugin-dir plugin` 验证 build 不受影响

### Owned files
- Edit: `plugin/skills/codex-review/SKILL.md` — 删除手工同步注释 + 确认 review-dispatch 锚点

### Read first
- `plugin/build/templates/review-dispatch.md.tmpl`（确认覆盖了 codex-review 需要的内容）
- `plugin/build/resolvers/review-dispatch.sh`（确认 resolver 包含 codex-review SKILL）

### Acceptance criteria
- [x] L8-9 的 `TEMPLATE_DEPS` 注释已删除
- [ ] ~~`<!-- BEGIN: review-dispatch -->` 锚点存在于 SKILL.md~~（推到 Plan 003 Pack 3.5）
- [x] `build.sh --check` 通过

### Verification commands
- `! grep -q 'TEMPLATE_DEPS' plugin/skills/codex-review/SKILL.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags
trivial（文档级清理）

### Out of scope
不修改 codex-review SKILL 的其他逻辑（Step 1 审查对象判定、Step 2 prompt 构造、Step 3+ dispatch 流程）

---

## Pack 1.2：删除孤儿 decision-brief 模板 + resolver

### Goal behavior
`decision-brief.md.tmpl` 内容已被 `preamble.md.tmpl` 的 T2/T3 variant 内联吸收，0 个目标文件引用。删除以减少 build 系统冗余。

### Implementation tasks
1. 确认 `decision-brief.md.tmpl` 没有任何 target 文件引用（grep `decision-brief` 模板锚点）
2. 删除 `plugin/build/templates/decision-brief.md.tmpl`
3. 删除对应 resolver `plugin/build/resolvers/decision-brief.sh`（如存在）
4. Read `plugin/build/build.sh` 确认 resolver 注册表是否需要更新
5. 跑 `bash plugin/build/build.sh --check` 验证

### Owned files
- Delete: `plugin/build/templates/decision-brief.md.tmpl`
- Delete: `plugin/build/resolvers/decision-brief.sh`（若存在）

### Read first
- `plugin/build/build.sh`（了解 resolver 注册机制）
- `plugin/build/README.md`

### Acceptance criteria
- [ ] `decision-brief.md.tmpl` 文件不存在
- [ ] `decision-brief.sh` resolver 不存在
- [ ] `bash plugin/build/build.sh --check` 通过
- [ ] grep `decision-brief` 在 SKILL.md / 锚点中找不到任何引用

### Verification commands
- `! test -f plugin/build/templates/decision-brief.md.tmpl` → Expected: exit 0
- `! test -f plugin/build/resolvers/decision-brief.sh` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- `! grep -rq 'BEGIN: decision-brief' plugin/skills/ plugin/agents/` → Expected: exit 0

### Risk flags
trivial

### Out of scope
不动 preamble.md.tmpl（它已吸收 decision-brief 内容）

---

## Pack 1.3：简化 sendmessage-resume.md.tmpl（取消 worker-prompts 写文件）

### Goal behavior
按用户决策 1：取消"先 Write 到 `worker-prompts/<pack-id>-repair-<round>.md` 再 SendMessage inline 内容"这一步。SendMessage 直接 inline，不写文件。compaction 恢复完全依赖 plan/design/workflow-state（不依赖 dispatch prompt 文件）。

### Implementation tasks
1. Read `plugin/build/templates/sendmessage-resume.md.tmpl`（所有 variants：worker / plan-writer / learning）
2. 对 `[variant=worker]`：
   - 删除"File-first repair prompt discipline: write to `worker-prompts/<pack-id>-repair-<round>.md` then SendMessage with `<full contents of ...>`" 这段
   - 改为直接 SendMessage 模板：`SendMessage({to: <agent_id>, message: "<DISPATCH_ENVELOPE>\n\n修复任务：..."})`
   - 在模板末尾加 1 行说明："Compaction recovery: 从 `workflow-state.cursor` + plan/design 文档重建；dispatch prompt 不需要 durable copy。"
3. 对 `[variant=plan-writer]`：同样处理
4. 跑 `bash plugin/build/build.sh --apply` 让模板传播
5. 跑 `bash plugin/build/build.sh --check` 验证

### Owned files
- Edit: `plugin/build/templates/sendmessage-resume.md.tmpl`

### Read first
- `plugin/skills/orchestrate-execution/references/execution-repair-truncation.md`（了解当前 SendMessage 修复流程）
- `plugin/skills/orchestrate-final-review/references/final-review-repair.md`
- `plugin/skills/orchestrate-plan-writing/references/plan-review-resolution.md`

### Acceptance criteria
- [ ] sendmessage-resume.md.tmpl 不再包含 "worker-prompts/" 路径写入指令
- [ ] 模板末尾说明了 compaction 恢复路径（不依赖 prompt 文件）
- [ ] `build.sh --apply` + `--check` 通过
- [ ] grep `worker-prompts/.*\.md` 在模板中无匹配（除非是历史 reference 注释）

### Verification commands
- `! grep -q 'write to .*worker-prompts/' plugin/build/templates/sendmessage-resume.md.tmpl` → Expected: exit 0
- `grep -q 'inline' plugin/build/templates/sendmessage-resume.md.tmpl` → Expected: exit 0（确认改为 inline 模式）
- `bash plugin/build/build.sh --apply --plugin-dir plugin && bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags
normal（影响所有 SendMessage 续派流程，需保证不破坏现有 repair 路径语义）

### Out of scope
- 不动 Codex `review-prompts/<gate>.md` 写文件（CLI 强制 `--prompt-file`，保留）
- 不动 worker-prompts/ 目录本身（如果 plan-returns 还有用就保留；本 Pack 仅取消 sendmessage 写入指令）

### Dependencies
无

---

## Pack 1.4：清理 dispatch reference 中 worker-prompts 路径引用

### Goal behavior
Pack 1.3 改了 template；本 Pack 把所有 dispatch reference 中提到 `worker-prompts/...` 写入的句子同步清理。dispatch reference 是 Coordinator 实际读到的指令，必须与 template 一致。

### Implementation tasks
1. Grep 所有 reference 文件找 `worker-prompts/` 引用：
   `grep -rn 'worker-prompts/' plugin/skills/*/references/ plugin/skills/*/SKILL.md`
2. 对每条引用判断：
   - 若是"指示 Coordinator 写文件"的句子 → 删除并改为"inline SendMessage"
   - 若是"compaction 恢复读文件"的说明 → 改为"从 plan/design + workflow-state 重建"
   - 若是"历史路径示例"且无害 → 保留并加 deprecated 标记（可选）
3. 跑 `bash plugin/build/build.sh --apply` 同步任何受 template 注入影响的目标文件
4. 跑 `bash plugin/scripts/run-all-tests.sh` 验证不破坏现有测试

### Owned files
预期触及（grep 结果决定）：
- `plugin/skills/orchestrate-execution/references/execution-repair-truncation.md`
- `plugin/skills/orchestrate-final-review/references/final-review-repair.md`
- `plugin/skills/orchestrate-plan-writing/references/plan-review-resolution.md`
- 可能：`plugin/skills/orchestrate-execution/SKILL.md`（被 sendmessage-resume 注入）

### Read first
- `plugin/build/templates/sendmessage-resume.md.tmpl`（Pack 1.3 改好的版本）

### Acceptance criteria
- [ ] `grep -rn 'write.*worker-prompts/' plugin/skills/` 无匹配
- [ ] 所有 reference 中的 SendMessage 续派说明都是 "inline" 模式
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过
- [ ] `bash plugin/scripts/verify-maturity.sh` 通过

### Verification commands
- `! grep -rq 'write.*worker-prompts/' plugin/skills/` → Expected: exit 0
- `bash plugin/scripts/run-all-tests.sh` → Expected: 全部测试通过
- `bash plugin/scripts/verify-maturity.sh` → Expected: 全部检查通过

### Risk flags
normal

### Dependencies
- 1.3（template 必须先改）

### Out of scope
- 不动 Codex review-prompts/ 相关（CLI 强制保留）
- 不动 worker-prompts/ 目录的 `.gitignore`（除非完全废弃）

---

## Plan-level 验证

完成所有 Pack 后跑：

```bash
bash plugin/build/build.sh --check --plugin-dir plugin
bash plugin/scripts/run-all-tests.sh
bash plugin/scripts/verify-maturity.sh
python3 -m json.tool plugin/.claude-plugin/plugin.json >/dev/null
python3 -m json.tool plugin/hooks/hooks.json >/dev/null
```

全部通过 → Plan 001 完成。

## Plan Review History

（待 Plan Implementation Review 后追加）
