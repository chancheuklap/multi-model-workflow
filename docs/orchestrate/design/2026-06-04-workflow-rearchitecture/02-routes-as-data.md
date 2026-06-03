# 02 · 流程形态数据化（核心分册）

> 受 `00-overview.md` 骨架绑定。本分册落实骨架 §4 分层表第一行（**流程形态**层）：把"有哪些 phase、允许怎么跳、每 phase 的 gate 豁免与 budget 参数"从代码三处（实测四处）硬编码，抽成**一份声明式 routes 清单数据**；`state.sh` 与 hook 改读这份清单做 transition 校验与 gate 判定。
>
> - 锁定决策约束：D1（激进默认轻档）/ D2（默认免外审）/ D4（机器强制 > 散文自觉，更稳定）。本分册是 D4"地板=流程相对稳定"的物理载体——它把流程形态变成机器读得懂的数据，跳步与豁免不再靠主线程自觉。
> - 北极星不变量约束：**状态权威**（磁盘是断点续传唯一可信源）、**数据权威**（routes 清单不得改变 docs/ 的权威地位）、**计费/LINEAGE**（idempotency 不受影响）。
> - 本分册只动**控制平面**（routes 数据 + state.sh + hook 的薄读取逻辑）。不碰 worker-loop / Document-as-Context 派发层。

---

## 结论先行（给 plan-writing 直接消费）

1. **现状是"流程形态四处硬编码 + 一个假数据字段"**：合法跳转写死在 `state.sh:73-98` 的 `TRANSITION_MATRIX` bash 数组；route→budget 初始档写死在 `cmd_init` 的 `case "$route"`（`state.sh:134-145`）；"execution 必须 plan-level"写死成 `validate-plan-dispatch.sh:75` 的字面量 `if [[ "$PHASE" == "execution" ]]`；非 execution route 的合法 phase 白名单又写死成 `dispatch-route-worker.sh:48-54` 的 `case "$PHASE"`。而本该承载"轻档跳哪些 phase"的 `phase_skip` 字段**零 hook 消费**（仅在 init 写 `[]`、schema 声明、SKILL 表、架构散文、测试里出现），是一张没人执行的便签。
2. **目标是一份 `routes-v1.json` 声明式清单**：每个 route 一条记录，声明 `phases`（序列）、`transitions`（合法跳转 = 取代 `TRANSITION_MATRIX` 的 route-aware 部分）、`gate_exemptions`（哪些 gate 在本 route 豁免 = 取代假 `phase_skip`）、`budget`（初始档参数 = 取代 `cmd_init` 的 case）、`commit_format`（取代假 `commit_format_override` 写入）。清单放在 `plugin/state-schema/routes-v1.json`，由 `state.sh` 与 hook 在运行时 `jq` 读取。
3. **`state.sh` 与 hook 改读清单**：`transition_allowed()` 读 `routes-v1.json[route].transitions` + 一组 route-无关的全局 transition；`cmd_init` 读清单的 `budget` 段初始化预算；`validate-plan-dispatch.sh` 的 `PHASE==execution` 判定改为查清单"当前 phase 的 dispatch 形态是否为 plan-level";`dispatch-route-worker.sh` 的 phase 白名单改为"清单里非 execution 的 dispatch 形态"。
4. **死行清理**：`TRANSITION_MATRIX` 的 `Pack 2.14 / Plan 005` 注释行（`:75 / :78 / :96`）随迁移到清单时一并删除注释（行本身保留语义、并入清单 transitions）；`cleanup-before-push.sh:51` 的 `ROUTE=="hotfix"` 检测是**完全死代码**（D10 后无任何 init 把 route 设成 `hotfix`），改读 `commit_format` 标志。
5. **向后兼容硬保证**：`route` 字段仍是 workflow-state 的一等字段、值域不变（4 值 enum）；清单是**新增只读数据**，不改任何已落盘 state 文件结构；`cursor.phase`（断点续传唯一锚点）语义、`last_gate_timestamp` 写入路径、idempotency 全部不动。旧 state 文件零迁移即可被新逻辑读。这是 B+ 真结构性、而非"换皮"的命门论证（见 §6）。

---

## 1. 现状：流程形态的物理散落（源码锚点）

骨架 §2 把病根定性为"流程怎么走被写死在散文里、机器几乎不参与控制"。本分册把"机器侧那部分写死"逐一钉到行号——它分布在**四个**互不知情的消费点，外加一个零消费的假数据字段。

### 1.1 合法跳转：`TRANSITION_MATRIX` bash 硬编码白名单

`state.sh:73-98` 定义一个 27 行的 bash 数组，每行 `"actor:from:to"`，`transition_allowed()`（`state.sh:100-114`）线性扫描匹配，匹配不到 `exit 1`（被 `cmd_transition` 转成 `exit 2`，`state.sh:283-286`）：

```bash
# state.sh:73
TRANSITION_MATRIX=(
  "Coordinator:pending:dispatched"
  "Coordinator:pending:in_progress"        # Pack 2.14 / plan-level Worker first dispatch (Plan 005)
  ...
  "Coordinator:workflow:discovery"
  "Coordinator:workflow:plan-writing"
  "Coordinator:workflow:execution"
  "Coordinator:workflow:final-review"
  "Coordinator:discovery:plan-writing"
  "Coordinator:plan-writing:execution"
  "Coordinator:execution:final-review"
  "Coordinator:final-review:closed"
  ...
)
```

这个矩阵把**两类语义混在一张表里**：
- **phase 推进**（`workflow:discovery` / `discovery:plan-writing` / `plan-writing:execution` / `execution:final-review` / `final-review:closed`，`state.sh:85-92`）——这是真正的"流程形态"，且是**与 route 强相关的**（formal 走全序列；轻档要跳过其中某些）。
- **work-item 状态机**（`pending:dispatched` / `dispatched:returned` / `returned:committed` / `review_pending:pass` 等，`state.sh:74-83,95-97`）——这是 Worker/Pack 级别的状态流转，**与 route 无关**，对任何 route 都一样。

问题不在"用了矩阵"，而在 **phase 推进部分是 route 无关地全列**：`workflow:discovery` 对 quickfix 也合法、`plan-writing:execution` 对所有 route 都允许，没有任何机制说"quickfix route 不应该有 discovery 这一跳"。于是"轻档跳过 discovery"在矩阵层面**根本无法表达**——矩阵只管"这一跳本身合不合法"，不管"这个 route 该不该有这一跳"。轻档跳步只能靠主线程读 SKILL.md Variant Table 后自觉不调那一步（散文自觉 = 骨架 §2 的病根）。

### 1.2 route→budget 初始档：`cmd_init` 的 `case` 硬编码

`state.sh:134-145`，route 决定预算初始档，写死成 case 分支：

```bash
# state.sh:134
case "$route" in
  direct-repair|multi-pr-merge|bug-investigation)
    budget_status='"unlimited"'; review_total='"unlimited"'; effort_total='"unlimited"' ;;
  *)
    budget_status='"pending_plan_count"'; review_total='null'; effort_total='null' ;;
esac
```

"哪些 route 开局就 unlimited、哪些等 plan_count 再算预算"是**流程形态的一部分**，却和合法跳转分开、写在另一个文件位置的另一种语法里。新增一个 route 要同时改这里和 `TRANSITION_MATRIX`，两处无任何一致性约束。

### 1.3 "execution 必须 plan-level"：hook 字面量

`validate-plan-dispatch.sh:75`：

```bash
if [[ "$PHASE" == "execution" ]]; then
  # 要求 plan_id 非空、pack_id 为空（plan-level 自治 Worker）
```

这是把"execution phase 的派发形态 = plan-level（一 Plan 一 Worker）"这条流程形态规则，写死成 hook 里对 phase 字面量的字符串比较。

### 1.4 非-execution route 的 phase 白名单：第四处硬编码（实测新增）

`dispatch-route-worker.sh:48-54`：

```bash
case "$PHASE" in
  bug-investigation|direct-repair|multi-pr-merge|hotfix|quickfix|spike|maintenance) ;;
  *) echo "Error: route worker dispatch phase must be a non-execution route phase" >&2; exit 2 ;;
esac
```

这是**第四个**独立维护的"合法 phase 集合"硬编码，且它的清单（含 `hotfix/quickfix/spike/maintenance`）和 route enum（只有 4 值）已经漂移——`hotfix/quickfix/spike/maintenance` 在 D10 后不再是 route，而是 formal route 的 phase_skip 变体（`architecture-draft.md:149`），但这个白名单仍把它们当 phase 收。`validate-pack-manifest.sh:45-48` 还有第五处 `case "$PHASE" in execution) ;; *) exit 0 ;;`，性质相同。

### 1.5 零消费的假数据字段：`phase_skip` + `commit_format_override`

`grep` 全 plugin（已核验）：`phase_skip` 出现在 `state.sh:152`（init 写 `[]`）、`workflow-state-v1.json:19-23`（schema 声明 + enum）、`SKILL.md:68,70-75`（Variant Table）、`architecture-draft.md`（散文）、`test_route_keyword_routing.sh` / `test_hotfix_post_push_review.sh`（测试）。**没有任何 hook 或 state.sh 逻辑读取 `phase_skip` 的值去改变行为**。`commit_format_override` 同样：`state.sh:153` 写 `null`、schema `:24` 声明、SKILL 表里赋值，**零行为消费**（无任何脚本据其改 commit message 格式或跳过 release gate）。

这正是骨架 §2"僵硬（最痛）"症状的物理证据：轻档变体声明了 `phase_skip: ["discovery","plan-review"]`，但没有任何机器读它去真的豁免 discovery；SKILL.md:7 的 Hard Gate "**每个项目**都走 Discovery，无论看起来多简单"与之直接打架，最终跳不跳全靠主线程自觉。

### 1.6 schema 侧的流程形态

`workflow-state-v1.json:18` route enum 4 值；`:19-23` phase_skip 的 items enum（`discovery/plan-writing/execution/final-review/plan-review`）；`state-transition-matrix.md` 是 `TRANSITION_MATRIX` 的散文镜像（人读，机器不读），且自身也带 `Plan 005` 历史注释（`:9,11,13,38`）。

### 1.7 现状清单（5 个消费点 + 1 个假字段 + 1 段散文镜像）

| # | 消费点 | 锚点 | 承载的流程形态语义 | 与 route 的关系 |
| --- | --- | --- | --- | --- |
| C1 | `TRANSITION_MATRIX` bash 数组 | `state.sh:73-98` | 合法跳转（phase 推进 + work-item 状态机混在一起） | phase 推进部分**应**与 route 相关，现状 route 无关地全列 |
| C2 | `cmd_init` route case | `state.sh:134-145` | route→budget 初始档 | route 强相关 |
| C3 | `validate-plan-dispatch.sh` | `:75` `PHASE=="execution"` | execution 派发形态=plan-level | phase 相关 |
| C4 | `dispatch-route-worker.sh` | `:48-54` phase 白名单 | 非-execution route 合法 phase 集 | route/phase 相关，已漂移 |
| C5 | `validate-pack-manifest.sh` | `:45-48` `PHASE==execution` | 仅 execution 才查 manifest | phase 相关 |
| F1 | `phase_skip` 字段 | `state.sh:152` + schema + SKILL | 轻档跳哪些 phase（**零消费**） | route 相关，但未接线 |
| F2 | `commit_format_override` 字段 | `state.sh:153` + schema + SKILL | commit 格式 / release gate 豁免（**零消费**） | route 相关，但未接线 |
| M1 | `state-transition-matrix.md` | 全文 | C1 的散文镜像（人读） | — |

---

## 2. 问题：四处分散 + 假字段带来的四个具体故障

1. **轻档无法表达，更无法强制**（对应骨架 D1/D4）：C1 的矩阵无 route 维度，F1 零消费，所以"quickfix 跳 discovery"既写不进矩阵、写进 `phase_skip` 也没人读。结果只能靠主线程读 SKILL.md 自觉——这是僵硬+烧 token 的同源病根。
2. **新增/改 route 要改五处且无一致性兜底**：加一个 route 要碰 C1（跳转）、C2（预算）、schema enum、C4 白名单、SKILL 表，五处任一漏改就漂移；现状 C4 已经和 route enum 漂移（§1.4）。
3. **死代码沉积**：C1 带 `Pack 2.14 / Plan 005` 注释行（`:75/:78/:96`）；`cleanup-before-push.sh:51` 的 `ROUTE=="hotfix"` 在 D10 后**永不命中**（无 init 把 route 设成 `hotfix`，已核验 §4.2）。这正是骨架 §2"冗余（治标不治本）/ 文档代码系统性漂移"的实例。
4. **散文与机器双源**：M1（`state-transition-matrix.md`）必须人肉与 C1 对齐，已带历史注释漂移。

---

## 3. 目标设计：`routes-v1.json` 声明式清单

### 3.1 设计原则（受 §00 §4 与用户核心原则 #14 约束）

- **单一数据源**：一个 route 的全部流程形态（phase 序列 / 合法跳转 / gate 豁免 / 预算 / commit 格式）集中在清单里一条记录，消灭 C1–C5 + F1 + F2 的散落。
- **机器可读、薄逻辑**：清单是 JSON，`state.sh` 与 hook 用 `jq` 读，读取逻辑尽量薄（查表 + 比较），不引入解释器/状态机引擎（避免骨架 §4"不做一次性大重写引擎"的红线）。
- **不过度设计**（#14）：清单**只表达现在四档真实存在的流程形态差异**（formal 全序列 / light 跳 discovery+plan-review / bug-investigation 跳全 phase 走 RCA / multi-pr-merge 跳全 phase 走 merge-brief）。不引入条件跳转 DSL、不引入 per-user 可配置 route、不引入运行时热加载——这些现在和可预见的将来都不需要。新增 route = 清单加一条记录，足够。
- **work-item 状态机保持 route 无关**：C1 里那些 `pending:dispatched` / `returned:committed` 等与 route 无关的 work-item 流转**不进 route 清单**，它们抽成清单顶层的一个 `global_transitions` 段（对所有 route 生效）。只有 phase 推进进 route 的 `transitions`。这是关键切分——否则会把 route 清单污染成又一份大矩阵。

### 3.2 字段设计

`plugin/state-schema/routes-v1.json` 顶层结构：

```jsonc
{
  "schema_version": "1",
  "global_transitions": [
    // route-无关的 work-item 状态机（取代 TRANSITION_MATRIX 的非-phase 行）
    // 格式 "actor:from:to"，* 为通配
    "Coordinator:pending:dispatched",
    "Coordinator:pending:in_progress",
    "Coordinator:dispatched:returned",
    "Coordinator:returned:committed",
    "Coordinator:returned:review_pending",
    "Coordinator:review_pending:pass",
    "Coordinator:review_pending:needs_repair",
    "Coordinator:returned:repairing",
    "Coordinator:repairing:returned",
    "Coordinator:*:blocked",
    "Coordinator:*:execution_done",
    "Coordinator:*:closed",
    "agent-return-handler:dispatched:returned",
    "agent-return-handler:in_progress:returned",
    "track-execution-state:returned:committed"
  ],
  "routes": {
    "<route_name>": {
      "phases": ["..."],               // 本 route 实际经过的 phase 有序序列
      "phase_transitions": ["..."],    // 本 route 合法的 phase 推进（"Coordinator:from:to"）
      "gate_exemptions": ["..."],      // 本 route 豁免的 gate 名（取代假 phase_skip）
      "dispatch_shape": { "<phase>": "plan-level" | "route-worker" }, // 取代 C3/C4 字面量
      "budget": {
        "init": "pending_plan_count" | "unlimited",   // 取代 C2 case
        "formula": "3P+12" | null                     // 仅 init=pending_plan_count 时有意义；交由 04 分册参数化
      },
      "commit_format": null | "hotfix-unreviewed"      // 取代假 commit_format_override
    }
  }
}
```

字段语义说明：

| 字段 | 取代现状 | 谁读 | 语义 |
| --- | --- | --- | --- |
| `global_transitions` | C1 的 work-item 行 | `state.sh transition_allowed` | route 无关，对所有 transition 都允许匹配 |
| `routes[r].phases` | （新增显式化）SKILL Variant Table 隐含序列 | SKILL 渲染 / hook 诊断信息 | 本 route 经过哪些 phase，供主线程与诊断用 |
| `routes[r].phase_transitions` | C1 的 phase 推进行（route-aware 化） | `state.sh transition_allowed` | 只有列出的 phase 推进在本 route 合法 |
| `routes[r].gate_exemptions` | **F1 `phase_skip`**（真接线） | hook（discovery-gate / plan-review-gate / final-review-gate） | hook 读它判断本 route 是否豁免某 gate |
| `routes[r].dispatch_shape` | **C3 + C4 + C5** 字面量 | `validate-plan-dispatch.sh` / `dispatch-route-worker.sh` / `validate-pack-manifest.sh` | 某 phase 的派发形态：plan-level（execution）或 route-worker |
| `routes[r].budget.init` | **C2** case | `cmd_init` | 初始预算档 |
| `routes[r].budget.formula` | `state.sh:916` 公式（交 04 处理） | `cmd_budget_initialize`（04 分册） | 占位，本分册只搬家不改公式 |
| `routes[r].commit_format` | **F2 `commit_format_override`** | Closing / commit 逻辑（接线由 03 落地） | commit message 标签 |

> **gate 命名约定**：`gate_exemptions` 用 gate 名（`discovery` / `plan-review` / `final-review`）而非 phase_skip 那种 phase 名混 gate 名（现状 phase_skip enum 把 `plan-review` 这种 gate 和 `discovery` 这种 phase 混在一个数组，`workflow-state-v1.json:21`）。本分册借迁移机会把"跳过整个 phase"与"豁免某个 gate"分开：`phases` 表达前者，`gate_exemptions` 表达后者。Light Lane 的真豁免接线在 `03` 落地，本分册只提供数据载体。

### 3.3 四个示例 route

> 下列 `formal` / `bug-investigation` / `multi-pr-merge` 是现存 4-enum 中的 3 个（`direct-repair` 第 4 个形态同 bug-investigation，从略）。`light` 是 `03` 分册要落地的 Light Lane——本分册把它的数据形态先在清单里立好，**但 `03` 才接 hook 豁免逻辑**。`light` 在 `route` enum 上仍归 `formal`（不新增 enum 值，见 §6.1），通过清单 + gate_exemptions 区分；这里单列是为展示数据结构对轻档的表达力。

**formal**（完整管线，骨架 §4 Formal Lane）：

```jsonc
"formal": {
  "phases": ["discovery", "plan-writing", "execution", "final-review"],
  "phase_transitions": [
    "Coordinator:workflow:discovery",
    "Coordinator:workflow:dispatched",
    "Coordinator:discovery:plan-writing",
    "Coordinator:plan-writing:execution",
    "Coordinator:execution:final-review",
    "Coordinator:final-review:closed",
    "Coordinator:workflow:plan-writing",
    "Coordinator:workflow:execution",
    "Coordinator:workflow:final-review"
  ],
  "gate_exemptions": [],
  "dispatch_shape": { "execution": "plan-level" },
  "budget": { "init": "pending_plan_count", "formula": "3P+12" },
  "commit_format": null
}
```

**light**（D1 激进默认轻档；数据形态预置，hook 豁免由 `03` 接线）：

```jsonc
"light": {
  "phases": ["plan-writing", "execution", "final-review"],
  "phase_transitions": [
    "Coordinator:workflow:plan-writing",
    "Coordinator:plan-writing:execution",
    "Coordinator:execution:final-review",
    "Coordinator:final-review:closed"
  ],
  "gate_exemptions": ["discovery", "plan-review"],
  "dispatch_shape": { "execution": "plan-level" },
  "budget": { "init": "pending_plan_count", "formula": "3P+12" },
  "commit_format": null
}
```

> 注意 `light` 的 `phase_transitions` **没有** `workflow:discovery` 和 `discovery:plan-writing` —— 机器据此就能**拒绝**轻档误入 discovery（`transition_allowed` 查不到这一跳即 `exit 2`）。这就是 D4"不误跳"由机器强制、而非散文自觉的物理实现：轻档跳 discovery 不再是"主线程读 SKILL 后选择不调"，而是"机器层面这条跳转在 light route 下根本不存在"。

**bug-investigation**（跳全 phase，走 RCA；现状 `route=bug-investigation`）：

```jsonc
"bug-investigation": {
  "phases": ["bug-investigation"],
  "phase_transitions": [
    "Coordinator:workflow:dispatched",
    "Coordinator:*:closed"
  ],
  "gate_exemptions": ["discovery", "plan-writing", "plan-review", "execution", "final-review"],
  "dispatch_shape": { "bug-investigation": "route-worker" },
  "budget": { "init": "unlimited", "formula": null },
  "commit_format": null
}
```

**multi-pr-merge**（merge-brief 驱动；现状 `route=multi-pr-merge`）：

```jsonc
"multi-pr-merge": {
  "phases": ["multi-pr-merge"],
  "phase_transitions": [
    "Coordinator:workflow:dispatched",
    "Coordinator:*:closed"
  ],
  "gate_exemptions": ["discovery", "plan-writing", "plan-review", "execution", "final-review"],
  "dispatch_shape": { "multi-pr-merge": "route-worker" },
  "budget": { "init": "unlimited", "formula": null },
  "commit_format": null
}
```

### 3.4 清单放在哪 / 谁读它

- **放 `plugin/state-schema/routes-v1.json`**（不是 bash 关联数组，也不是 schema 内嵌）：
  - **为什么不是 bash 关联数组**：bash 关联数组无法表达嵌套（phases 数组 + budget 对象 + gate_exemptions 数组），且 hook（多个独立脚本）都要读，bash 数组无法跨进程共享、只能各 `source`，又退回多源。JSON + `jq` 是 plugin 已有依赖（CLAUDE.md 前置条件硬检查 `jq`），所有 hook 已在用 `jq` 读 envelope/state，零新依赖。
  - **为什么不内嵌进 `workflow-state-v1.json` schema**：那是 per-run 实例状态的 schema，routes 是**跨 run 的静态配置**，混进去会让每个 state 文件都背一份 route 定义（违反状态权威——状态文件应只存这一 run 的实例数据，不存全局配置）。独立文件 = 静态配置与实例状态分离。
  - **为什么放 `state-schema/`**：与 `workflow-state-v1.json` / `merge-brief-v1.json` 同目录，是 plugin 内"机器读的结构定义"的既有归属地（`state-schema/README.md` 已是该目录索引）。
- **`state.sh` 读它**：
  - `transition_allowed()`（`state.sh:100`）：先读 `routes-v1.json[route].phase_transitions` 与 `global_transitions`，把两者合并成候选集再做现有的 `actor:from:to` 通配匹配。route 从 state 文件 `.route` 读（已有字段）。**关键**：work-item 状态机走 `global_transitions`（route 无关），phase 推进走 route 的 `phase_transitions`——轻档在这里被机器拦住误跳。
  - `cmd_init`（`state.sh:134`）：把 `case "$route"` 换成读 `routes-v1.json[route].budget.init`，据此设 `budget_status`/`review_total`/`effort_total`（unlimited 时三者全 unlimited；pending_plan_count 时 review_total/effort_total 为 null，与现状一致）。
- **hook 读它**：
  - `validate-plan-dispatch.sh:75`：`if [[ "$PHASE" == "execution" ]]` 改为读 `routes-v1.json[route].dispatch_shape[PHASE] == "plan-level"`。route 从 `$SF`（`workflow-state-${RUN_ID}.json`）的 `.route` 读（hook 已在读 `$SF`，`:46-47`）。
  - `dispatch-route-worker.sh:48-54`：phase 白名单 `case` 改为"读清单：当前 phase 的 `dispatch_shape == "route-worker"` 即合法，否则 `exit 2`"。这自动消灭 §1.4 的白名单漂移（hotfix/quickfix/spike/maintenance 不再硬列，而是看它们实际属于哪个 route 的哪个 phase）。
  - `validate-pack-manifest.sh:45-48`：`case "$PHASE" in execution)` 改为读 `dispatch_shape[PHASE]=="plan-level"`（只有 plan-level 派发才查 manifest）。
  - **Light Lane 的 gate 豁免读取**（`03` 落地、本分册预留契约）：discovery-gate / plan-review-gate / final-review-gate 这类 hook 读 `routes-v1.json[route].gate_exemptions` 判断是否豁免。

---

## 4. 死行清理方案

### 4.1 `TRANSITION_MATRIX` 的 `Pack 2.14 / Plan 005` 注释行

**对象**：`state.sh:75`（`Coordinator:pending:in_progress # Pack 2.14 / plan-level Worker first dispatch (Plan 005)`）、`:78`（`Coordinator:returned:review_pending # Pack 2.14 / plan-level Worker → Plan Implementation Review`）、`:96`（`agent-return-handler:in_progress:returned # Pack 2.14 / plan-level Worker auto-return (Plan 005)`）。

**注意：这三行的 transition 本身是活的、不能删**（plan-level 自治 Worker 真的用 `pending:in_progress` / `in_progress:returned` / `returned:review_pending`，由 `agent-return-handler.sh` 与 Coordinator 在用）。要清理的是**行尾的历史注释**——全局 CLAUDE.md 明确规定"变更历史属于 git commit message，不属于文档/代码注释"。

**清理动作**：迁移到 `routes-v1.json` 时，这三个 transition 归入 `global_transitions`（它们是 route 无关的 work-item 流转），且**去掉 `Pack 2.14 / Plan 005` 字样**。`global_transitions` 的 JSON 行不带历史注释（JSON 本就不支持注释，天然合规）。同步删除 `state-transition-matrix.md:9,11,13,38` 的同类历史注释——该散文文件迁移后降级为"指向 `routes-v1.json` 的人读说明"，不再镜像每一行。

### 4.2 `cleanup-before-push.sh:51` 的死 `hotfix` 路由检测

**核验结论（已 grep 确认）**：D10 后 `route` enum 只有 4 值（`formal/direct-repair/bug-investigation/multi-pr-merge`，`workflow-state-v1.json:18`）；hotfix 是 formal route + `commit_format_override="hotfix-unreviewed"`（`SKILL.md:72`、`architecture-draft.md:149`）。全 plugin 无任何 `state.sh init ... --route hotfix` 或把 `.route` 写成 `"hotfix"` 的路径。因此 `cleanup-before-push.sh:51` 的 `if [ "$ROUTE" = "hotfix" ]` **永不命中 = 死代码**。

**清理动作**：这段逻辑的真实意图是"hotfix 变体要延后清理 state（post-push review 还要用）"。意图仍有效，但判据用错了字段。改为读 `routes-v1.json[route].commit_format == "hotfix-unreviewed"`（或读 state 的 `commit_format` 标志，待 `03` 把 commit_format 接线后统一）。在本分册阶段，最小动作是把判据从死的 `route=="hotfix"` 改为活的 `commit_format` 标志判断——根因修复（骨架原则#4），不是把死代码留着。

### 4.3 假字段 `phase_skip` / `commit_format_override` 的归宿

- `phase_skip`（F1）：其语义被 `routes-v1.json` 的 `phases` + `gate_exemptions` 取代。**字段本身的删除/保留由 `03` 分册裁决**（`03` 负责 Light Lane 完整设计与"删假 phase_skip 的连带清理清单"，骨架 §7）。本分册的职责是提供取代它的数据载体，并明确：迁移后 `phase_skip` 不再是任何行为的输入。
- `commit_format_override`（F2）：语义被 `routes-v1.json` 的 `commit_format` 取代，接线（真的据它改 commit / 豁免 release gate）由 `03` 落地。本分册同样只提供载体。

> 跨分册边界声明：本分册**只搬流程形态到清单**，不删 state 字段、不改预算公式、不接 Light Lane hook 豁免。删字段属 `03`/`05`，改公式属 `04`，接豁免属 `03`。本分册产出 = `routes-v1.json` + `state.sh`/hook 改读它 + 死注释/死路由清理。

### 4.4 测试与 verify-maturity 的连带更新

- `test_route_keyword_routing.sh`：现测 4 enum 的 init 预算档（`:21-32`）+ formal 有 phase_skip 数组（`:35-38`）。迁移后改为：断言 `cmd_init` 据 `routes-v1.json[route].budget.init` 设档（行为不变，数据来源变）。
- `verify-maturity.sh:240-244`：现 grep SKILL.md 里有 `hotfix/spike/maintenance` 关键词。迁移后这些仍在 SKILL Variant Table（关键词识别仍由主线程做，见 §6.3），grep 仍通过；新增一项 check："`routes-v1.json` 存在且 `jq` 可解析、每个 enum route 有对应记录"。
- 新增测试：`test_routes_manifest.sh`——校验 `routes-v1.json` 与 `route` enum 一致（每个 enum 值有记录）、`transition_allowed` 读清单后对现有 transition 测试集行为不变（回归基线）。

---

## 5. 落地要点（给 plan-writing 的拆包提示）

1. **新增 `plugin/state-schema/routes-v1.json`** + 配套 `routes-v1.schema.json`（meta-schema，校验清单自身结构）。先把现状 4 enum 的形态如实编码（formal/direct-repair/bug-investigation/multi-pr-merge），`light` 作为 formal 的子形态预置但不接 hook（留 `03`）。
2. **`state.sh` 加一个 helper** `routes_load()` / `route_field <route> <jq-path>`：薄封装 `jq` 读 `routes-v1.json`（路径相对 `$SCRIPT_DIR/../state-schema/`）。`transition_allowed` 与 `cmd_init` 改调它。
3. **改 `transition_allowed`**：候选集 = `global_transitions` ∪ `routes[route].phase_transitions`。route 从 state `.route` 读；当 state 文件不存在或 route 缺失（极早期 / 测试 fixture）时**回退到全量旧矩阵**（兼容，见 §6.2）。
4. **改三个 hook** 读 `dispatch_shape`：`validate-plan-dispatch.sh:75`、`dispatch-route-worker.sh:48-54`、`validate-pack-manifest.sh:45-48`。统一一个 helper（hook 侧 `lib/` 里）避免三处各写 `jq`。
5. **改 `cleanup-before-push.sh:51`** 判据从死 `route=="hotfix"` 改活 `commit_format` 标志。
6. **删 `state.sh:75/:78/:96` 行尾历史注释**（迁移进 `global_transitions` 时天然去掉）；**降级 `state-transition-matrix.md`** 为指向清单的人读说明，删历史注释。
7. **更新测试 + verify-maturity**（§4.4）。
8. **同步 `architecture-draft.md`**（骨架称其已漂移，`05` 分册负责重写；本分册改动后留接口给 `05`：route 形态现以 `routes-v1.json` 为准）。

依赖顺序：步骤 1（清单）必须先于 3/4/5（读取方）。步骤 6/7/8 可与 3/4/5 并行。`03`（Light Lane 接 hook 豁免）依赖本分册步骤 1–4 完成。

---

## 6. 向后兼容与断点续传论证（B+ 真结构性的命门）

骨架 §6 北极星不变量"状态权威：磁盘状态是 compaction/断点续传唯一可信源"是硬约束。本分册改的是**控制平面的读取逻辑**，必须证明它不破坏已落盘状态的可读性与续传。

### 6.1 `route` 字段与值域不变

workflow-state 的 `route` 字段（`workflow-state-v1.json:18`，4 值 enum）**保持不变**。`light` 不新增 enum 值——它在 enum 上归 `formal`，靠 `routes-v1.json` + `gate_exemptions` 区分形态（`03` 决定 light 是否需要一个区分标志，本分册不引入）。因此**所有已落盘的 state 文件 `route` 字段照样合法**，schema 不破坏。

### 6.2 旧 state 文件零迁移

`routes-v1.json` 是**新增的只读静态配置**，不写进任何 state 文件、不要求 state 文件新增字段。`transition_allowed` 改读清单后，对**已存在的 state 文件**：从 `.route` 读出 route（旧文件都有此字段），查清单得到该 route 的合法跳转集——与旧矩阵对该 route 的有效子集**等价**（formal 的 phase_transitions = 旧矩阵的 phase 推进行；work-item 行进 global_transitions 对所有 route 仍全开）。**回退保证**：若 state 无 `.route` 或清单查不到该 route（理论上不会，留作 defensive），`transition_allowed` 回退到内置全量旧矩阵——行为退化为现状，绝不更严。这保证升级当天正在跑的 run 不被卡死。

### 6.3 `cursor.phase` 续传锚点不动

断点续传依赖 `cursor.phase`（`workflow-infrastructure.md` Step 0 / `SKILL.md:53` "已在工作树+有状态文件 → 断点续传，直接路由到对应 phase"）。本分册**不改 cursor.phase 的写入路径**（仍由 `cmd_transition` 在 `state.sh:313` 写）、不改其语义、不改 `last_gate_timestamp` 写入（`state.sh:314`，Source Stability 门依赖它，骨架 §5.4）。续传时主线程读 cursor.phase 路由——这条路径一行不碰。

### 6.4 关键词识别仍在主线程（不是机器抢了判断权）

D1"激进默认轻档"的**入口判定**（用户输入是不是轻档/要不要升 formal）是主线程的语义判断，仍在 SKILL Entry Gate 做（`03` 细化判定线）。`routes-v1.json` 不抢这个判断——它只在 route **已确定后**约束"这个 route 能怎么走"。所以本分册不改变"谁决定 route"，只改变"route 决定后流程形态从哪读"。这与骨架 §5.5"子代理返回必验"等人/模型职责无冲突。

### 6.5 为什么这是"真结构性"而非换皮

判据：改造后**新增/改 route 的修改点数**从 5 处（C1+C2+C4+schema+SKILL）降到 1 处（清单加一条记录）+ SKILL 关键词表（人读那一份）；**轻档跳步从"零机器执行点"变成"机器层 transition 不存在即拦截"**（§3.3 light 示例）；**假字段 phase_skip/commit_format_override 从零消费变成有真载体**。这三点都是行为可观测的结构变化，不是把 bash 数组改写成等价 JSON 的换皮。换皮的反例会是"JSON 里仍 route 无关地全列 phase 推进"——本设计明确把 phase 推进 route-aware 化（§3.1 work-item vs phase 切分），这是结构差异的核心。

---

## 7. 风险与缓解

| 风险 | 说明 | 缓解 |
| --- | --- | --- |
| 运行时 `jq` 读清单的开销/失败 | hook 在每次 Agent 派发都读清单 | 清单极小（< 100 行），`jq` 已是热路径依赖；读失败时 `transition_allowed` 回退旧矩阵（§6.2），hook 读失败时回退到"按 execution 字面量"旧行为（fail-open 到现状，不更严） |
| 清单与 route enum 漂移 | 加 enum 忘了加清单记录 | `verify-maturity.sh` 新增 check：每个 enum route 必有清单记录（§4.4） |
| `global_transitions` 与 `phase_transitions` 切分错误 | 把 route 相关的跳转误放进 global，轻档又能误跳 | 切分判据明确（§3.1）：work-item 状态机（pending/dispatched/returned/...）→ global；phase 名（discovery/plan-writing/execution/final-review）的推进 → route。新增回归测试锁定（§4.4） |
| 死注释清理误删活 transition | §4.1 三行 transition 是活的 | 明确只删行尾注释、transition 迁入 global_transitions；回归测试覆盖这三个 transition |
| 与 `03`/`04` 的边界含混 | 字段载体 vs 接线/公式 | 本分册只搬流程形态 + 死行清理；删字段(`03`/`05`)、改公式(`04`)、接 gate 豁免(`03`) 明确划出（§4.3） |

---

## 8. 验收信号（对齐骨架 §8）

1. **单源**：`grep` 全 plugin，phase 推进的合法跳转、route→budget 初始档、execution-plan-level 判定、非-execution phase 白名单——四处不再各自硬编码，统一指向 `routes-v1.json`。
2. **轻档机器可拦**：构造一个 `route=light`（或 formal + light 形态）的 state，`state.sh transition --to discovery` **被拒**（`exit 2`），证明轻档跳 discovery 由机器强制而非散文自觉。
3. **死代码归零**：`grep 'Pack 2.14\|Plan 005' state.sh` 无命中；`cleanup-before-push.sh` 不再含死 `route=="hotfix"` 分支。
4. **续传不破**：升级前落盘的 state 文件（旧结构）被新 `transition_allowed` / `cmd_init` 读取，行为与升级前对该 route 等价；现有 transition 测试集全绿。
5. **零新增依赖**：清单用 `jq`（已有），无新运行时依赖。
6. **新增 route 一处改**：演示加一个假想 route 只需 `routes-v1.json` 加一条 + SKILL 关键词表加一行，不碰 `state.sh`/hook 逻辑。

---

## 附：本分册涉及的源码锚点清单（全部已亲自 Read 核验）

| 锚点 | 内容 |
| --- | --- |
| `state.sh:73-98` | `TRANSITION_MATRIX` bash 硬编码（含 `:75/:78/:96` 历史注释行） |
| `state.sh:100-114` | `transition_allowed()` 线性匹配 |
| `state.sh:134-145` | `cmd_init` route→budget case |
| `state.sh:152-153` | init 写 `phase_skip: []` / `commit_format_override: null` |
| `state.sh:313-314` | `cmd_transition` 写 `cursor.phase` / `last_gate_timestamp` |
| `validate-plan-dispatch.sh:75` | `PHASE=="execution"` 字面量 |
| `dispatch-route-worker.sh:48-54` | 非-execution phase 白名单 case（第四处硬编码，已漂移） |
| `validate-pack-manifest.sh:45-48` | `PHASE==execution` 才查 manifest（第五处） |
| `cleanup-before-push.sh:50-55` | 死 `ROUTE=="hotfix"` 检测 |
| `workflow-state-v1.json:18` | route enum 4 值 |
| `workflow-state-v1.json:19-23` | `phase_skip` schema + items enum |
| `workflow-state-v1.json:24` | `commit_format_override` schema |
| `state-transition-matrix.md` | C1 散文镜像（带历史注释） |
| `SKILL.md:56-77` | Entry Gate + Route 1 Variant Table |
| `architecture-draft.md:143-149` | Route 对比表 + D10 折叠说明 |
