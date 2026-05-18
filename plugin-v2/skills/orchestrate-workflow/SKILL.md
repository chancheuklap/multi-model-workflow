---
name: orchestrate-workflow
description: "正式开发流程主入口。用户给出新功能、系统性改造、系统性 bug、wrong state、performance regression、design / SPEC / ADR、PRD / issue、backlog、implementation plan、Task Pack、bug brief、测试失败、UI / UX 反馈、截图反馈、已实现 diff，或要求根据设计 / issue / plan 开始实现、继续执行、修复、review、验收、收尾、业务汇报时主动使用。缺少可 review 设计文档的输入先交给 orchestrate-discovery；已有设计、计划、实现 diff 则进入对应 Phase。负责 Entry Gate 分类、Resume Gate、Scope Contract、Git Checkpoint 和全局约束；不自己执行 Phase——调用对应 phase skill。"
---

# Orchestrate Workflow

主线程入口。职责：Entry Gate 分类 → Resume Gate → Scope Contract → Git Checkpoint → 调用对应 phase skill。

## Flow

```
Step 1: Entry Gate classification.
        Answer-only → respond, stop.
        One-shot Review → review per user request, stop.
        Direct Repair → Step 3 → Step 4 → orchestrate-direct-repair.
        Bug Investigation → Step 3 → Step 4 → dispatch root-cause-analyst.
        Formal Orchestrate → Step 2.
        User Decision → ask one question, stop.

Step 2: Resume Gate.
        Within-conversation: resume from last passed gate.
        Cross-conversation: inspect artifact state —
          design exists but no Phase 0a pass → orchestrate-design-review.
          plan exists + Phase 0a passed → orchestrate-plan-review.
          packs partially done → orchestrate-execution (continue).
          Phase B passed → orchestrate-final-review.

Step 3: Write Scope Contract.
        - Source artifacts
        - Editable artifacts
        - Read-only context
        - Out of scope
        - Issue recording target
        Persist to .claude/multi-model-workflow/scope-<run_id>.md.
        规则：
          Source artifacts 只包含用户明确提供的文档 / tracker refs / diff，以及当前 phase 已确认的直接输入。
          Editable artifacts 只能是 source artifacts 或当前 phase 明确要求产出的 design / plan / pack / report。
          Read-only context 可以包含相关 issue、ADR、代码或 runbook，但 sub-agent 只能用来判断当前 source artifacts，不得把它们变成交付范围。
          Out of scope 必须明确列出容易被误纳入的相关 issue、ADR、未来能力、其它文档或环境。
          Issue recording target 说明 small issue hierarchy 写回哪里。

Step 4: Git Checkpoint.
        git status --short --branch。
        在 main / master / release branch 上先创建 work/<short-scope> 分支。
        区分当前 scope 改动和用户 / 其它线程改动；不 stage 不属于当前 scope 的 dirty files。

Step 5: Dispatch.
        Formal Orchestrate: create budget file + active-run-id → orchestrate-discovery.
        Direct Repair: → orchestrate-direct-repair.
        Bug Investigation: analyst dispatched in Step 1.
          Route by analyst Result.Resolution:
            - fixed → orchestrate-direct-repair (review only, analyst diff as scope).
            - root cause found, not fixed → orchestrate-direct-repair (analyst report = approved brief).
            - root cause in design/plan → Formal Orchestrate, seed Discovery with analyst report.
            - unable to reproduce → 报告用户，附 analyst 排除路径，请求更多重现信息。
            - unable to determine → 报告用户，附 analyst 排除路径，请求协助判断方向。
```

## Entry Gate

| 路线 | 条件 | 下一步 |
| --- | --- | --- |
| Answer-only | 只问概念/状态/解释 | 回答后停止 |
| One-shot Review | 只要 review，不要修复 | 写 scope，按用户请求审查 |
| Direct Repair | 已有批准 design/plan/mockup/acceptance/failing test，目标行为清楚 | Step 3 → Step 4 → orchestrate-direct-repair |
| Bug Investigation | bug report / error log / regression / failing test，但根因不明 | Step 3 → Step 4 → root-cause-analyst → 按 Resolution 路由 |
| Formal Orchestrate | 新功能、系统性改造、含混 feedback、缺 design/issue/plan | Step 2 → Discovery 开始 |
| User Decision | 产品/业务/权限/账务/发布策略无法判定 | 一次只问一个问题 |

## Hard Gates

- 没有验证证据，不得声称完成。
- 没有用户明确指令，不得 merge / push / PR / discard / 写生产环境。
- Formal Orchestrate 没有可 review 的 design document 时先进 Discovery，不跳到 plan / worker。
- Phase 0a / Phase 0b / Phase B 不可跳过（除非 Entry Gate 选择了 Answer-only / One-shot Review / Direct Repair）。
- upstream skill 结论必须写回 design / plan / bug brief，再继续当前节点。

## 禁止

- 跳过 Phase 0 或 Phase B。
- 用技术语言向用户汇报。
- 自己写生产代码（调度 worker）。
- 每 task 一个 subagent（用 Task Pack）。
- 超过循环上限不处理。
