# Path A Re-Review Flow

> **流程位置**：`orchestrate-execution` Step 10 修复分流 · Path A（Coordinator 直接修复）后的强制 re-review

## 适用条件

Coordinator 选择 Path A（直接修复）且 finding confidence >= 7 时，**强制** targeted Codex re-review。
Confidence < 7 的 Path A 修复可以跳过 re-review（Coordinator 自检即可）。

## 7 步流程

### Step 1: Start
记录进入 Path A re-review：
```bash
state.sh path-a-escalation start --run-id <run_id> --finding-id <finding_id> --round 1
```

### Step 2: Coordinator 直接修复
修改 <= 2 个文件，不碰合同边界。跑受影响的测试确认修复。

### Step 3: Dispatch Targeted Re-Review
```text
resume_agent({
  id: "<baseline reviewer agent_id>"
})
send_input({
  target: "<baseline reviewer agent_id>",
  message: "<full contents of .codex/multi-model-workflow/review-prompts/<gate>.md>"
})
wait_agent({
  targets: ["<baseline reviewer agent_id>"],
  timeout_ms: 600000
})
```

Targeted prompt envelope 必须设置 `review_intent: "targeted-re-review"`、`exception_code: "path_a_self_fix"`，并把 `agent_id` 设置为 baseline reviewer `agent_id`。
将 reviewer 最终消息保存到 `.codex/multi-model-workflow/review-results/<gate>.md` 并完成 review bookkeeping 后，立即 `close_agent({ target: "<baseline reviewer agent_id>" })` 释放容量。

### Step 4: Update
记录 Codex 返回的 verdict：
```bash
state.sh path-a-escalation update --run-id <run_id> --finding-id <finding_id> --verdict <approved|needs_repair>
```

### Step 5a: Approved
Codex 确认修复正确：
```bash
state.sh path-a-escalation clear --run-id <run_id> --finding-id <finding_id>
```
→ 继续 Git Checkpoint → 下一 Pack / Plan

### Step 5b: Needs Repair
Codex 报告仍 needs repair → **必须升级 Path B**，不允许 Coordinator 再次直接修。
`path-a-escalation` entry 的 `blocked_for_self_fix = true` 阻止后续 Path A 尝试。

```bash
# state.sh 已自动设 blocked_for_self_fix = true
# validate-pack-dispatch.sh 会检查 path_a_escalation 中是否有 blocked entry
```

→ 走 Path B：`send_input` 给原 worker 执行修复

### Step 6: Clear
Path B 修复完成且 targeted re-review 通过后：
```bash
state.sh path-a-escalation clear --run-id <run_id> --finding-id <finding_id>
```

---
> **回到**：SKILL.md Step 10 或 `execution-repair-truncation.md` 修复分流。
