# Plan-level Worker 行为规范（固定 handbook）

> **流程位置**：`orchestrate-execution` Step 5 · Worker 在 `Worker Loop` 启动序列 Step 2 读取本文件
>
> 本文件是 **plan-level 自治 Worker**（pack-executor / complex-pack-executor）的固定行为规范，与 agent 定义中的
> `Worker Loop` 段配套：`Worker Loop` 给出**循环骨架**（5 步启动 / Pack 循环 / verdict 枚举 / 失败次数协议 / repair / context 自监控），
> 本文件给出**执行细则**（TDD 纪律 / commit 规范 / Durable Return 与 Return Contract 格式）。
> Coordinator 派发时只在 DISPATCH_ENVELOPE 写 `plan_id` + `plan_path` + 运行时变量，**不粘贴任何 Pack 内容**——
> Worker 自读 plan 文件的 `## Pack Execution Manifest` 与每个 Pack 的完整定义。

> **Incoming envelope**：你的 dispatch prompt 以 Coordinator 构造的 `DISPATCH_ENVELOPE` 块开头。你只需读取 `repair_round`（≥1 → 进入 Repair Mode，见 `Worker Loop` 段）与 `disposition_refs`（accepted findings 引用）；其余字段（protocol_version / agent_role / idempotency_key / correlation_id 等）是 Coordinator 派发与 hook 校验职责，worker 端不构造、不校验。完整 envelope 规范见 `orchestrate-execution` SKILL.md。

你（worker）按 `Worker Loop` 段的 5 步启动序列自读 plan 文件（**及 plan 头 `Source issue` 指向的大 issue 文档**）与本 handbook，不依赖 Coordinator 粘贴 Pack 字段。Coordinator 只在 envelope 写明 `plan_id` + `plan_path` + 运行时变量。每个 Pack 的完整定义（goal / owned files / acceptance / verification / contract anchors / mockup specs / dependencies / risk flags）由你从 plan 文件自读；源 issue 文档提供 plan 编译前的原始 slice 意图（`What to build`），用于核对实现没有偏离意图。

## TDD 纪律

- 每个 Pack：先写 failing public-behavior test → **亲眼确认 RED** → 最小实现 → GREEN。先写实现再补测试 → 删实现重来；测试没失败过 → 测试无效，重写。
- 例外：`risk_flags: trivial`（配置常量 / 文档更新 / 样式调整）——验证通过即可，不强制红-绿。
- 测 public behavior，不测 private helper / 内部调用顺序；mock 只用于外部边界。
- trivial docs/config/style 同步：用 proof-oriented 检查（`git diff --check` / build/generator 检查 / manifest/schema 校验 / 路径链接验证），不为"措辞存在"加测试，除非该措辞是生成产物或 runtime contract anchor。

## Commit 规范

- 每个 Pack 完成后**独立 commit**，格式：`Pack <plan.id>.<pack.id>: <title> — <summary>`（`enforce-plan-commit.sh` hook 校验格式）。
- repair 模式：`Pack <plan.id>.<pack.id>: <title> — repair: <finding 摘要>`，每 finding 一个 commit，不批量。
- 不 push。

## Failure modes

见 agent `Worker Loop` 段「失败次数协议」+ verdict 枚举（始终在 worker 系统提示中，不在此重复）：三次失败→`blocked`、partial-pass、`needs-plan-revision`、`needs-context`、`need-fresh-worker` 的判定与阈值均以该段为准。

## 读盘与上下文纪律（尤其 Sonnet 档 200K）

- 大文件按行范围 / `grep` / `rg` 定位读，只读与当前 Pack 相关的片段，不整文件吞入上下文。
- 大命令输出（测试日志 / build / `git diff` / 数据 dump）先 `head` / `grep` / 重定向落盘再筛，不把全量直灌上下文。
- 定位优先 `rg` / `grep` / `git log -S`，而非全目录通读。
- **Sonnet 档窗口仅 200K**：若发现某个 Pack 必须读入的内容明显超出余量（单文件就接近窗口、或需通读大量文件），不要硬塞导致中途截断——返回 `needs-context` 并说明体量，由 Coordinator 改派 1M Worker（`complex-pack-executor`）。

## Durable Return（每 Pack + Plan 收尾，必须在最终 verdict 之前）

- **每 Pack**：写 `<STATE_DIR>/pack-returns/<run_id>/<pack-id>.json`（绝对路径；`<STATE_DIR>` 由 envelope 提供）：

```json
{
  "pack_id": "<N.M>",
  "verdict": "<pass | blocked | needs repair | needs context>",
  "changed_files": ["<path1>", "<path2>"],
  "open_items": [{"tag": "<out-of-scope|needs-evaluation|bug>", "summary": "..."}],
  "concerns": "<如有>"
}
```

- **Plan 收尾**：写 `<STATE_DIR>/plan-returns/<run_id>/<plan_id>/plan-return.json`（schema `plan-return-v1.json`）+ `open-items.json`（schema `open-items-v1.json`）。必须用绝对路径，确保 Coordinator 和 hooks 能读到。
- Open Items 三标签，格式 `- [标签] 简述问题 — 发现位置 — 影响判断`：
  - `[out-of-scope]` 不属于当前 Pack 或整个 scope 的问题
  - `[needs-evaluation]` 需要独立评估才能判断是否修复的问题
  - `[bug]` 执行中发现的已有代码 bug（非本次引入）

## Return Contract（最终输出格式）

```text
### Verdict
plan-level：pass / partial-pass / blocked / need-fresh-worker / needs-context / needs-plan-revision
### Evidence
### Result
- Changed files
- Completed behavior（each with verification evidence）
- Known gaps
- Needs review
### Verification（回归证据）
### Open Items
```

## 关键规则

- Pack 定义必须来自已通过 Plan Review 的 plan。无效字段先修回 plan（`needs-plan-revision`），不在派发时临场重切。
- 条件字段（Contract anchors / Mockup specs / Dependencies / 发布风险 / AFK·HITL）只在 plan 中该 Pack 有对应内容时才适用——plan 没写就不存在，不脑补。

## Coordinator 端最小职责

1. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`plan_id`、`plan_path`、`phase=execution`、`agent_role`。
2. 触发 `state.sh execution-plan start` 记录 Plan start_commit。
3. 等待 `SubagentStop` / `agent-return-handler.sh` 回收 plan-level 返回值。
4. 读取 `plan-returns/<run_id>/<plan_id>/plan-return.json`，推进下一步编排。

---
> **回到**：agent `Worker Loop` 段继续 Pack 循环 → Plan 收尾写 artifact → return。
