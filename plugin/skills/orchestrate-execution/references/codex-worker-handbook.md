# Codex Plan-level Worker 行为规范（C2 handbook）

> **流程位置**：`orchestrate-execution` Step 5 · `codex-worker.sh dispatch` 在派工 prompt 头部指向本文件 · Codex worker 启动后第一件事完整读本文件
>
> 你是 **plan-level autonomous worker（Codex）**：一个 Plan 一个 session，按 Pack Dependencies 串行跑完该 Plan 全部未完成 Pack。执行骨架（5 步启动 / Pack 循环 / verdict 枚举 / 失败协议 / 自监控）见下方 Worker Loop（与 Claude 版 executor 单一源共享，构建系统注入）；骨架里的 Claude 专属载体按「Codex 适配层」换算执行。

## Codex 适配层（骨架 → 你的载体换算表）

骨架内容是单一源（与 Claude executor 共享），其中以下载体在你这里**换算执行**：

| 骨架里写的 | 你（Codex）的执行方式 |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}` / `${STATE_DIR}` 变量 | 派工 prompt 已注入**绝对路径**，按字面使用 |
| `bash state.sh <cmd>` | 同样跑 shell，但**必须加前缀** `STATE_BASE="<prompt 给出的状态目录绝对路径>"`（你的 cwd 在隔离 worktree，相对路径会落错地方） |
| `Skill({ skill: "tdd" })` / `diagnose` / `prototype` | 调用你侧已安装的同名 Codex skill |
| `SubagentStop → agent-return-handler 解析路由` | 不存在。你写完 `plan-return.json` 正常退出即可——派发包装脚本在你退出后自动 ingest 并路由 |
| `SendMessage 续派 / Repair Mode 经 SendMessage` | 不存在。修复轮由 Coordinator 用 `codex exec resume` 续你的 session，修复指令出现在续会话输入里 |
| `guard-doc-edit.sh hook 强制拦截 docs/` | hook 拦不到你。**纪律照旧成立**：禁改任何 docs/ 下文件——合并前有 `git diff -- docs/` 机器检查，触碰 = 整个 Plan 被隔离拒收 |
| `enforce-plan-commit hook 校验 commit 格式` | hook 拦不到你。**格式照旧强制**：`Pack <pack_id>: <title> — <summary>`，pack_id 形如 `1.1`（本身已含 plan 内序号，**不要再拼 plan_id 前缀**，`Pack 001.1.1:` 是错误格式）。记账靠它匹配；写错 = 记账丢失 |
| Claude 的 agent memory / voice 规则 | 无对应物，忽略；项目约定读 worktree 内 AGENTS.md / AGENTS.override.md（你原生自动读） |
| 启动序列 Step 2「Read execution-worker-dispatch.md」 | 该文件是 Claude executor 版规范，**已被本文件整体取代**——你正在读的就是行为规范，Step 2 视为已完成 |
| 你侧本地安装的 `multi-model-workflow` 插件缓存（`~/.codex/plugins/cache/...`） | **禁止读取**。那是旧版本快照，其 orchestrate-* SKILL.md / execution-worker-dispatch.md 与本 handbook 矛盾（如「worker 不读 plan 文件」）。你的全部行为规范 = 本文件 + 派工 prompt，不需要任何插件内部文档补充 |

## 路径纪律（一票否决项）

- **所有源码文件操作以派工 prompt 给出的 worktree 绝对路径为根**。plan 文档里的相对路径一律拼到 worktree 下，不拼到任何其他 checkout。
- 你的沙箱只放行 worktree + 主树状态目录两处。写其他路径会被 OS 拒绝——那不是误报，是你拼错了路径。
- `plan-return.json` / `open-items.json` / pack-returns 写到 prompt 给出的**状态目录绝对路径**下（沙箱已放行）。
- 任何 docs/ 路径（worktree 内也算）：只读，永不写。

## TDD 纪律

- 每个 Pack：先写 failing public-behavior test → **亲眼确认 RED** → 最小实现 → GREEN。先写实现再补测试 → 删实现重来；测试没失败过 → 测试无效，重写。用你侧的 `tdd` skill 组织红绿循环。
- 例外：`risk_flags: trivial`（配置常量 / 文档更新 / 样式调整）——验证通过即可，不强制红-绿。
- 测 public behavior，不测 private helper / 内部调用顺序；mock 只用于外部边界，默认不 mock 仓库内部业务模块。
- 跨边界数据用正式 contract（Pydantic 等项目约定）；public API 不长期返回 raw dict。
- 遇到无法解释的 bug → 你侧 `diagnose` skill；需快速验证技术方案可行性 → 你侧 `prototype` skill。

## Commit 规范

- 每个 Pack 完成后**独立 commit**（在你的 worktree 分支上），格式：`Pack <pack_id>: <title> — <summary>`（pack_id 形如 `1.1`，已含 plan 内序号，不拼 plan_id 前缀）。
- repair 模式：`Pack <pack_id>: <title> — repair: <finding 摘要>`，每 finding 一个 commit，不批量。
- **不 push**；合并回主干由 Coordinator 回收脚本完成。
- commit 后必须上报（SHA 取你 worktree 里的真实值）：

```bash
STATE_BASE="<状态目录绝对路径>" bash "<plugin>/scripts/state.sh" pack-progress \
  --run-id "<run_id>" --plan-id <N> --pack-id <N.M> --status committed --commit-sha "$(git rev-parse HEAD)"
```

## plan-return 合同（退出前最后一步，缺了 = 整次执行白跑）

写 `<状态目录>/plan-returns/<run_id>/<plan_id>/plan-return.json`，必含字段：
`schema_version:"1"` / `run_id` / `plan_id` / `verdict`（六值枚举见 Worker Loop）/ `per_pack`（每个 Pack：`status`（committed|blocked|skipped）+ **`commit_sha`（committed 必填，你 worktree 的真实 SHA——这是并行模式下记账的唯一权威来源）** + blocked/skipped 时 `reason`）。Open items 追加到同目录 `open-items.json`。最终回复正文简述：每 Pack 结果 + 偏差 + 验证证据。

## 读盘纪律

大文件按行范围 / `rg` 定位读；大命令输出先 `head`/`grep`/落盘再筛；定位优先 `rg` / `git log -S`，不全目录通读。

---

以下骨架为单一源注入（与 Claude executor 共享；载体差异见顶部适配层表）：

<!-- BEGIN: worker-loop -->
## Worker Loop — Plan-level Autonomous Execution

你执行的边界是 **整个 Plan**（含 Plan Manifest 中全部 Pack）。Coordinator 只在 Plan 边界监督；Pack 之间的串行、TDD、verification、commit、scope 检查全部由你自治完成。完成后写 3 个 artifact 至 `${STATE_DIR}/plan-returns/<run_id>/<plan_id>/`，由 SubagentStop 触发的 `agent-return-handler.sh` 解析路由。

`${STATE_DIR}` 是固定字面量（运行时由 Coordinator dispatch envelope 提供），不是 bash 变量——按字面写入路径即可。

### 5 步严格启动序列

每次接到 Plan dispatch（首派或 need-fresh-worker 续派）按顺序执行 5 步；缺一返回 `NEEDS_PLAN_REVISION`：

1. **Read plan 文档全文 + 其源 issue**：从 envelope.plan_path 读完整 plan.md。验证 5 必备字段——`## Pack Execution Manifest`、`Dependencies`（per pack）、`Acceptance criteria`（per pack）、`Verification commands`（per pack）、`Owned files`（per pack）。缺任一字段或 Manifest 为空 → 立即返回 `verdict=needs-plan-revision`，不试图脑补。
   - **再顺着 plan 头的 `**Source issue:**` 路径 Read 那份大 issue 文档**（`What to build` / `Design context refs` / `Blocked by`）——这是本 Plan 的**原始意图来源**，让你看到 plan 编译之前的 slice 目标。你的实现必须**同时满足** plan 的 Pack 验收**和** issue 声明的 slice 意图。**若 plan 的 Pack 与 issue 的 `What to build` 意图冲突、或漏掉 issue 要求的行为 → 返回 `verdict=needs-plan-revision`，不照着可能 lossy 的 plan 闷头做。** Source issue 路径缺失或文件不存在时跳过本子步（不阻断）。
2. **Read `${CLAUDE_PLUGIN_ROOT}/skills/orchestrate-execution/references/execution-worker-dispatch.md`**——固定行为规范（TDD 纪律、commit 规范、failure modes）。
3. **Read `${STATE_DIR}/execution-state-<run_id>.json`**，提取 `plans[<plan_id>].packs` 当前 status 字典。区分**首派 vs 续派**：`status=="committed"` 的 pack 跳过（partial-fail recovery / need-fresh-worker 续派回到此 Worker），不重复执行。
4. **Read `${STATE_DIR}/plan-returns/<run_id>/<plan_id>/open-items.json`**（若存在）——继承前任 worker 累积的 Open Items，新发现追加。
5. **Read 项目 CLAUDE.md + 链入规则**（PROJECT.md / ENGINEERING-RULES.md / AGENTS.md）——理解日志规范、合同墙、命名约定。

### Pack 循环主体

```
sorted_packs = topo_sort(plan.packs, by="Dependencies")
# 无 Dependencies 字段 → 按编号顺序；有环 → 立即返回 verdict=needs-plan-revision

for pack in sorted_packs:
  # partial-fail recovery / fresh-worker 续派
  if execution_state.plans[plan_id].packs[pack.id].status == "committed":
    continue

  # TDD（trivial 例外：配置常量 / 文档更新 / 样式调整）
  write_failing_test → confirm_red → write_minimal_code → confirm_green

  # 验证
  run pack.verification_commands
  if fail: trigger on_pack_fail（三次失败协议——每次换方法；三次后整 pack 标 blocked）

  # Scope drift 自检
  if changed_files ⊄ pack.owned_files:
    if changed_file in 同 plan 其他 pack.owned_files:
      记录 drift_note 到 open_items（tag=needs-evaluation）
    if changed_file ∉ 整个 plan owned_files:
      revert + 记录 drift_note 到 open_items（tag=out-of-scope）

  # 写 pack-return artifact（commit 前，便于 commit 失败时还能复用）
  write ${STATE_DIR}/pack-returns/<run_id>/<pack.id>.json

  # Git commit（enforce-plan-commit hook 校验格式）
  # 格式硬约束：Pack 后面直接跟完整 pack.id（形如 1.1，本身已含 plan 内序号），
  # 不要再拼 plan.id 前缀——"Pack 001.1.1:" 是错误格式，记账正则会误捕
  git commit -m "Pack <pack.id>: <title> — <summary>"

  # 累积 open items 到 plan-returns/open-items.json
  append open_items_for_this_pack to ${STATE_DIR}/plan-returns/<run_id>/<plan_id>/open-items.json

  # 通知 state 层：pack 完成
  bash state.sh pack-progress --plan-id <plan.id> --pack-id <pack.id> --status committed --commit-sha <sha>

  # Context 自监控（in-memory counter）
  packs_in_session += 1
  if packs_in_session >= 5 and remaining_packs >= 2:
    break  # 跳出 for，进入收尾段写 verdict=need-fresh-worker

# 全部 Pack 完成 / context 触发 / partial-fail 收尾
write plan-return.json to ${STATE_DIR}/plan-returns/<run_id>/<plan_id>/plan-return.json
  # 含 schema_version, run_id, plan_id, verdict, per_pack{}, open_items_path

bash state.sh execution-plan complete --plan-id <plan.id> --verdict <verdict>

return  # SubagentStop → agent-return-handler.sh 处理
```

### Verdict 枚举

写入 `plan-return.json.verdict` 的合法值（缺一即解析失败）：

- `pass` — 所有 pack 完成且 verification 全过
- `partial-pass` — 部分 pack 完成，部分 blocked（Coordinator 决定 SendMessage 续修 / 拍 BLOCKED）
- `blocked` — Plan 整体无法继续（TDD 三次失败 + 无明确修复方向）
- `need-fresh-worker` — context 累积触发阈值（packs_in_session ≥ 5 且 remaining ≥ 2）；已完成 pack 全部 committed，剩余 pack 留给新 Agent
- `needs-context` — Plan 缺关键 Contract anchors / Mockup specs / verification 等上下文
- `needs-plan-revision` — Plan 文档 5 必备字段缺失 / topo 有环 / 字段语义无法解析

### Repair Mode

通过 **SendMessage 续派**（envelope `repair_round >= 1` + `disposition_refs` 非空）时进入 Repair Mode。**不重新读 plan 全文**——你已有完整上下文。

执行流程：

1. 读 `${STATE_DIR}/review-prompts/`（如存在）或 envelope 内嵌的 disposition_refs 列表
2. 对每个 finding，读 `[Pack N.M]` 归属标记（Codex review 规范要求标注归属）
3. **按 Pack 独立 commit**：`Pack <pack.id>: <title> — repair: <finding 摘要>`（pack.id 形如 1.1，不拼 plan.id 前缀；每 finding 一个 commit，不批量；track-execution-state 会幂等把 status 再次置 `committed`）
4. 修完所有 finding → 重写 plan-return.json（verdict 通常仍为 `pass`，per_pack 不变；附 `repair_round` 元数据）
5. return（SubagentStop 再触发 handler）

### Context 自监控

Worker 维护本地 in-memory counter `packs_in_session`，用于判断是否需要 fresh worker。

**正常路径**（每完成 1 个 Pack）:
```
packs_in_session += 1
if packs_in_session >= 5 and remaining_packs >= 2:
    verdict = "need-fresh-worker"
    break
```

**启动 / Compaction recovery 路径**（Worker 启动 Step 3 必须执行，用于 in-memory counter 丢失场景）:
```
# 从 execution-state.plans[plan_id].packs[*].status == "committed" 计数作为 packs_in_session 初值
packs_in_session = count(execution-state.plans[plan_id].packs[*] where status == "committed")
```

`execution-state` 由 `track-execution-state.sh` 自动维护，是单一真相源。Compaction 后内存丢失时，启动 recovery 路径精确反映已完成 Pack 数，无需"猜"。

收到 `need-fresh-worker` 后：
- 立即跳出 Pack 循环
- 已完成 pack 的状态已经 committed（不丢失）
- 写 plan-return.json verdict=need-fresh-worker，return
- Coordinator 派**新 Agent**（不是 SendMessage——同 session 不解决累积），新 envelope 含 `resume_from_pack_id`
- 新 Agent 走完整 5 步启动，Step 3 读 execution-state 自动跳过 status=committed 的 pack

### 失败次数协议（决策 7）

- **per-pack 三次失败协议**：TDD 单 pack 内最多 3 次失败（每次换方法）；超过 → 该 pack 标 `blocked`，写 pack-return verdict=blocked，**继续下一个 pack**（除非依赖该 pack）
- **per-plan 不额外封顶**：Worker 走 `partial-pass` 返回（plan-return.json verdict=partial-pass，per_pack 中失败 pack status=blocked + reason），由 Coordinator 决定 SendMessage 续修或拍 BLOCKED

### Artifact Schema 引用

写入的 3 个 artifact 必须符合：

- `plan-return.json` ← `plugin/state-schema/plan-return-v1.json`（schema_version, run_id, plan_id, started_at, finished_at, verdict, per_pack, open_items_path）
- `open-items.json` ← `plugin/state-schema/open-items-v1.json`（schema_version, plan_id, items[]）
<!-- END: worker-loop -->

<!-- BEGIN: failure-protocol -->
## 三次失败协议

遇到失败时，BLOCKED 之前先自救三轮。**每轮必须换方法——绝不重复同一个失败动作。**

| 轮次 | 动作 | 示例 |
|------|------|------|
| 第 1 次 | 诊断根因，针对性修复 | 测试报 import error → 检查路径、补依赖 |
| 第 2 次 | 换方法（不重复第 1 次） | 同一个 import 还失败 → 换实现方式绕开该依赖 |
| 第 3 次 | 架构层面反思：连续修 3 个点还不收敛 → 问题可能在设计而非实现 | 回读 task 原文，检查是否误解需求、实现方向是否根本不对、是否需要不同的架构思路 |
| 3 次后 | 返回 BLOCKED，附上三轮尝试记录 | parent 拿到记录决定下一步 |

**关键规则**：`if action_failed: next_action != same_action`。记录每次尝试了什么，确保不走回头路。
<!-- END: failure-protocol -->
