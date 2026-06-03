# 03 · 轻量旁路（Light Lane）与逃逸/升级门

> 本分册受 `00-overview.md` 骨架绑定。冲突以骨架为准。
> 锁定决策：**D1 激进默认轻档** / **D2 默认免外审、可手动加** / **D3 软继续+到顶停** / **D5 外部 skill 战略**。
> 北极星不变量（骨架 §6）：质量门最小集（子代理必验 / Worker 禁改 docs/ / 未勾选阻断 push）即使 Light Lane 也保留；核心红线（计费/权限/数据权威/用户可见合同）触碰必升 Formal。

---

## 0. 结论先行（给 plan-writing 直接消费）

1. **现在的"轻量旁路"是假的**：`phase_skip` 字段在 6 处出现（schema / `state.sh:152` 写 `[]` / SKILL.md:68,70 / 2 个 test），**零 hook 消费**——没有任何机器执行点。Light Lane 必须做成"机器能读、能豁免、能拦"的真东西，否则只是把假 `phase_skip` 换成假 Light Lane 散文。
2. **Light Lane 的机器执行点挂在 02 的 routes 清单上**：route 数据声明 `light` 的 phase 序列与 gate 豁免；`validate-plan-dispatch.sh` 在 `route==light` 时读清单跳过 design-exists / budget-init 前置；`state.sh` transition 允许 light 合法直跳。**本分册定义这些点的行为契约，02 提供清单数据结构。**
3. **Entry 判定线（D1 激进）**：默认 `light`；只有用户明说"大改造/新功能"或改动触碰**计费/权限/数据权威/用户可见合同**才自动升 `formal`。
4. **一键升级门（逃逸）是单向的**：`light → formal`，由新命令 `cmd_budget_reinitialize` 处理（现 `cmd_budget_initialize:911-912` 硬约束"只能从 `pending_plan_count` 进入"，无法处理 `unlimited→bounded`，是缺口）+ 补建 design/issue/plan。
5. **子模式**：`hotfix`（先 push 后审，`pending_post_push_reviews` 事后补审）、`spike`（临时目录、产出 verdict 即弃、不占编号）作为 Light Lane 的两个变体存在。
6. **删假 `phase_skip` 是收尾动作**，必须在真机器执行点（routes 清单 + hook 豁免 + 升级门）就位**之后**才删，否则把唯一记录"档位"的字段删了会让现状更乱。

---

## 1. 现状（源码锚点）

### 1.1 假轻量旁路：`phase_skip` 零消费

| 出现点 | 行为 | 证据 |
| --- | --- | --- |
| schema 定义 | `phase_skip` 是 array of enum（discovery/plan-writing/execution/final-review/plan-review） | `plugin/state-schema/workflow-state-v1.json:19-23` |
| init 写入 | 初始化恒为 `[]`，从不被 init 填值 | `plugin/scripts/state.sh:152` |
| SKILL 散文 | Route 1 Variant Table 让 Coordinator "`state.sh init` 后立即 `state.sh update` 设置 `phase_skip`" | `plugin/skills/orchestrate-workflow/SKILL.md:68,70-75` |
| 2 个 test | 只断言"`phase_skip` 是 array"、用 `state.sh update` 写值，不验证任何消费行为 | `plugin/scripts/tests/test_route_keyword_routing.sh:35-36`、`plugin/scripts/tests/test_hotfix_post_push_review.sh:23-25` |
| hook 消费 | **无**——`grep phase_skip plugin/` 命中以上全部，无任何 hook 读取它做控制 | `validate-plan-dispatch.sh` 全文无 `phase_skip` |

**结论**：跳不跳全靠主线程读 SKILL.md 散文后"自觉"。这与 SKILL.md:7 的 Hard Gate"**每个项目**都走 Discovery，无论看起来多简单"以及 SKILL.md:220"禁止：跳过 Discovery"**直接打架**——两条指令矛盾，机器一条都不强制。

### 1.2 Entry Gate 现状：route 4 值 enum，无 light

- `state.sh init` 的 route 只接受 4 值：`formal` / `direct-repair` / `multi-pr-merge` / `bug-investigation`（`state.sh:134-145` 的 `case` + schema enum `workflow-state-v1.json:18`）。
- hotfix/quickfix/spike/maintenance 在 SKILL.md:70-75 被"折叠"成 `formal` route + `phase_skip` flags（即上一轮 D10 折叠）。但因为 `phase_skip` 零消费，这个折叠等于把 4 个变体全部退化成"走完整 formal、靠主线程自觉跳步"。
- `formal` route 在 init 时 `budget_status` 恒为 `pending_plan_count`（`state.sh:140-145`），强制要求后续 `budget initialize`。

### 1.3 dispatch 前置门（被 light 需要豁免的对象）

`validate-plan-dispatch.sh` 在 plan-level dispatch 上设了多道前置，Light Lane 必须能合法绕开其中"为 formal 设计"的几道：

| Step | 门 | 行为 | 证据 |
| --- | --- | --- | --- |
| Step 4 | budget initialized | `budget_status == pending_plan_count` → `exit 2` "budget not initialized" | `validate-plan-dispatch.sh:58-63` |
| Step 5 | pending Direction Check | `pending_direction_check.ack_status == pending` 且非 codex-reviewer → `exit 2` | `validate-plan-dispatch.sh:65-72` |
| Step 5b | execution 必须 plan-level | `phase==execution` 时 `plan_id` 必非空、`pack_id` 必为 null | `validate-plan-dispatch.sh:74-84` |
| Step 6 | plan_path 解析 + plans entry | plan_path 必须是真文件；execution-state 必须有 plans entry | `validate-plan-dispatch.sh:88-115` |

其中 Step 3 idempotency（`:51-56`）、Step 6 的 plan_path 解析（`:90-93`）、Step 6 的"already in_progress with worker"（`:107-115`）是**承重护栏**（计费/状态权威），Light Lane **不豁免**。被豁免的只有 Step 4（budget init，因 light 默认 unlimited）。

### 1.4 transition 矩阵：硬编码白名单，无 light 直跳

`transition_allowed()`（`state.sh:100-114`）遍历硬编码数组 `TRANSITION_MATRIX`（`state.sh:73-98`）。formal 的合法链是 `workflow→discovery→plan-writing→execution→final-review→closed`（`:85-92`）。**没有任何一行允许 `workflow→execution` 直跳**——Light Lane 要直接派单 Worker，必须有合法的直跳转换，当前矩阵不支持。

### 1.5 升级门缺口：`cmd_budget_initialize` 只能从 `pending_plan_count` 进入

```text
state.sh:909-914
  current_status=$(jq -r '.budget.budget_status // "unknown"' "$sf")
  if [[ "$current_status" != "pending_plan_count" ]]; then
    echo "Error: budget already initialized (status=$current_status). Can only initialize from pending_plan_count." >&2
    exit 2
  fi
```

Light Lane 默认 `unlimited`（无界）。要从 Light 升级到 Formal，必须把 `unlimited` 改成 `bounded`（initialized + 公式算出的 `review_total`/`effort_total`）。但 `cmd_budget_initialize` 硬拒绝任何非 `pending_plan_count` 的入口，`cmd_budget_unlimited:939-944` 也只支持 `pending_plan_count→unlimited` 单向（明确拒绝 `initialized→unlimited`）。**`unlimited→bounded` 无任何命令支持 = 升级门物理上不存在。**

### 1.6 子模式现状

- **hotfix**：SKILL.md:72 让 hotfix 走 `phase_skip=["discovery","plan-writing","plan-review","final-review"]` + `commit_format_override="hotfix-unreviewed"` +"先 push 再事后 review；`pending_post_push_reviews` 保留；Closing 阶段手动清理"。`pending_post_push_reviews` 字段在 schema/init 存在（`state.sh:169`、schema required `:10`），test 能写入（`test_hotfix_post_push_review.sh:42-54`）——但 **Closing reference（`workflow-closing.md`）全文不读它**（grep 无命中）。即"事后补审"的机器消费点也不存在，靠"手动清理"散文。
- **spike**：SKILL.md:74 让 spike 走 `phase_skip=["plan-review","final-review"]` +"Discovery 简化为 1-page spike brief；产出 throwaway code + verdict 文档；不触发 release gate"。无任何机制保证 throwaway、不占编号、临时目录——全是散文。

---

## 2. 问题

1. **僵硬根源**：轻量旁路无机器执行点，主线程读完散文靠自觉跳步，且与 Hard Gate 散文自相矛盾。日常小改被完整 formal 流程拖完。
2. **升级门不存在**：用户 Light Lane 跑到一半发现"这其实是大改造"，没有任何命令能把 unlimited 预算转成 bounded、补建 design/issue/plan——只能整个推倒重来一个 formal run。
3. **子模式是散文**：hotfix 的"事后补审"、spike 的"产出即弃"都没有机器锚点，承诺无法兑现。
4. **删字带来的漂移**：`phase_skip` 留着是死字段（零消费），删掉又会丢掉唯一记录档位的位置——必须先建真机器点再删。

---

## 3. 目标设计

### 3.1 Entry 判定线（D1 激进，可操作规则）

Entry Gate 输出 `route ∈ {light, formal, direct-repair, bug-investigation, multi-pr-merge}`（在现 4 值 enum 上**新增 `light`**，由 02 的 routes 清单声明，schema enum 同步扩展）。

判定算法（默认 light，只在命中升级条件时升 formal）：

```text
route = "light"   # D1: 默认轻档

# 升级触发条件（任一命中 → route = "formal"）：
if 用户明说大改造信号:        # "大改造" / "新功能" / "重构整个X" / "新增一个模块/系统"
    route = "formal"
if 改动触碰核心红线:           # 北极星：必升（骨架 §6）
    route = "formal"
```

**核心红线判定表**（machine-checkable 的近似 + 人工兜底）：

| 触碰对象 | 升级 formal 的信号（启发式，Coordinator 自判 + 可用 path/keyword 辅助） |
| --- | --- |
| **计费** | 改动路径/diff 命中 billing / pricing / charge / quota / idempotency / metering / subscription |
| **权限** | 命中 auth / permission / role / acl / rbac / token / session / credential |
| **数据权威** | 改 schema / migration / 数据库写入路径 / docs/ 下 source-of-truth 文档 / LINEAGE |
| **用户可见合同** | 改 public API 签名 / 对外 endpoint / pricing 文案 / 用户协议 / 收费项上下架 |

> 规则定位：这是**业务决策红线**（用户能感知/要付钱/数据权威），按全局 CLAUDE.md"灰色地带按业务决策处理"——拿不准就升 formal。判定线写进 SKILL.md Entry Gate 散文 + 一张可被主线程快速匹配的关键词表；**不**做成 fire-on-every-Bash 的强 hook 门（避免过度设计，骨架 §核心原则#14；路径关键词匹配误报率高，强拦会卡住正常 light 改动）。机器侧的硬兜底仍由"升级门存在 + 北极星不变量"承担：即便误判为 light，用户/Coordinator 一句话即可走 §3.4 一键升级。

### 3.2 Light Lane 流程（保留的硬线只有三条）

```text
用户输入
  │
  ▼
Entry Gate → route=light（默认）
  │  intent 一句确认（"这是个小改：<一句话>，我直接动手了"——不阻塞，除非用户喊停）
  ▼
state.sh init --route light          # budget 默认 unlimited（见 §3.3）
  │
  ▼
直接派单 Worker（plan-level dispatch，dispatch envelope 走现有契约）
  │  envelope: plan_id 可为轻量内联 plan，或 plan_path 指向 Coordinator 现写的简短 plan
  ▼
Worker 自治执行 + commit（worker-loop 派发层原样保留，骨架 §5.1/§5.2）
  │
  ▼
Coordinator 自审（Read/grep 验 Worker 返回的 hash/路径/计数 — 硬线①）
  │  D2: 默认不派 Codex；保留"手动加一次外审"入口（§3.5）
  ▼
Closing（push 前未勾选任务阻断 — 硬线③；Worker 禁改 docs/ — 硬线②）
```

**Light Lane 保留的三条硬线（北极星 §6 质量门最小集，机器强制不变）**：

1. **子代理返回必验**：Coordinator 必 `Read`/`grep` 验证 Worker/reviewer 返回的 hash/路径/计数后才采信（骨架 §5.5）。这是纪律 + idempotency hook（`validate-plan-dispatch.sh:51-56`）双重保证。
2. **Worker 禁改 docs/**：`guard-doc-edit.sh` worker-active marker 原样生效（骨架 §5.10）。Light Lane 不豁免。
3. **未勾选任务阻断 push**：plans 下有 `- [ ]` 时 `git push` / `gh pr create` 被 hook 阻断（CLAUDE.md 硬规则、骨架 §5.16）。Light Lane 不豁免。

**Light Lane 相对 formal 砍掉的**（由 routes 清单声明为 light 的 phase 序列不含这些）：Discovery（含 Design Review）、独立 Plan-writing（Coordinator 自写简短 plan）、Plan Review、Final Review 的完整 Codex 增强审查。

### 3.3 预算：Light Lane 默认 unlimited（与 04 衔接）

`state.sh init --route light` 走 unlimited 分支（在 `state.sh:134-145` 的 `case` 中把 `light` 并入 `direct-repair|multi-pr-merge|bug-investigation` 的 unlimited 分支，或由 02 routes 清单的 `budget` 参数声明 `unlimited`）。Light Lane 默认无界，因为它本就是小改、不需要成本护栏的硬卡。**D3 的"软继续+到顶停"主要作用于 formal 的 bounded 预算**（详见 `04`）。

### 3.4 机器执行点（本分册核心 · 引用 02 的 routes 清单）

Light Lane 之所以"真"，全靠以下三个机器消费点。**routes 清单数据结构由 `02-routes-as-data.md` 定义**；本分册定义清单字段被消费时的行为契约。

#### 点 A：`validate-plan-dispatch.sh` 读 routes 清单做 gate 豁免

现状 hook 用字面量 `phase==execution`（`:75`）判断，且 Step 4 硬要求 budget initialized（`:58-63`）。目标改造：

```text
# 在 hook 早段，读出本 run 的 route 与该 route 的 gate 豁免清单
ROUTE=$(jq -r '.route' "$SF")
# 从 02 routes 清单查 route 的 phase 序列 + gate 豁免集（02 提供查询入口，如 state.sh route-gates）

# Step 4 改造：budget-init 前置仅对"声明需要 bounded budget"的 route 生效
if route 清单标记 light 为 budget=unlimited:
    跳过 Step 4 的 budget-init 检查      # light 合法绕过 design-exists/budget-init 前置
```

**关键边界**：被豁免的只有"为 formal 设计的前置"（Step 4 budget-init）。承重护栏**不豁免**：idempotency（`:51-56`）、plan_path 解析为真文件（`:90-93`）、already-in-progress 重派守卫（`:107-115`）。Light Lane 仍是合法的 plan-level dispatch，只是跳过 design-exists / budget-init 这两道"formal 才需要"的前置。

> 实现取舍：不在 hook 里硬编码"light 跳哪些 step"，而是让 hook 读 02 routes 清单的 `gate_exempt` 字段（声明式数据驱动），这是骨架 §4 控制平面切分的要求——避免把"档位跳哪步"再写死回 hook 字面量（重蹈 `phase==execution` 覆辙）。

#### 点 B：`state.sh` transition 允许 light 合法直跳

现 `TRANSITION_MATRIX`（`state.sh:73-98`）无 `workflow→execution` 直跳。目标：

- **不再往硬编码数组里塞 light 专用行**（那是 02 要根治的硬编码三处之一）。
- 02 把 transition 合法性从 `TRANSITION_MATRIX` bash 数组迁到 routes 清单数据；`transition_allowed()`（`:100-114`）改为"读当前 route 的 phase 序列，判 `from→to` 是否是该序列里的合法相邻或合法 gate 豁免跳转"。
- Light Lane 的 phase 序列（由 routes 清单声明）形如 `workflow → execution → closed`（直接派单 Worker），于是 `cmd_transition --actor Coordinator --from workflow --to execution` 对 `route==light` **合法**，对 `route==formal` 仍**非法**（formal 必须经 discovery/plan-writing）。

**行为契约**：transition 的合法性必须随 route 不同而不同——同一个 `from→to`，light 合法、formal 非法。这是"轻档成为清单一等公民"的物理体现（骨架 §4）。

#### 点 C：Entry Gate 写入 route（init 时定档）

`state.sh init --route light`（schema enum 扩 `light`）一次性把档位写进磁盘状态。之后所有 hook/transition 读 `route` 字段就知道当前档位——**档位是磁盘状态权威（北极星 §状态权威），不靠主线程上下文记忆**。这取代了"靠 `phase_skip` 数组 + 主线程自觉"的假机制。

### 3.5 D2 外审策略：默认免、保留手动入口

- **默认**：Light Lane 不派 Codex（D2）。Coordinator 自审 = Read/grep 验证 Worker 返回 + 自己读 diff 判断质量。
- **手动入口**：用户对单次改动可明说"这个让 Codex 看一眼"。Coordinator 据此**单次**派一个 Codex review（走现有 `_shared/review-dispatch.md` 派发契约 + Execution tier GPT-5.4 xhigh，骨架 §5.6 模型分层）。
- **入口实现**：不需要新机制——Light Lane 不禁止 Codex 派发，只是默认不主动派。"手动加一次外审"= 用户触发 → Coordinator 派一个 reviewer agent。判定标准写进 SKILL.md Light Lane 段，不做成强 hook（D2 是"可选"，强制反而违背 D2）。

### 3.6 一键升级门（逃逸）：`light → formal` 单向

升级是 Light Lane 跑到一半发现"这其实是大改造/触碰红线"时的逃逸阀。**单向**：只允许 `light → formal`，不允许反向降级（防止已建立的 formal design/issue/plan 被无声丢弃）。

升级门做两件事：(1) 预算从 `unlimited` 转 `bounded`；(2) 补建 design/issue/plan 占位，让 formal 流程有 source-of-truth 可读。

#### 3.6.1 新命令 `cmd_budget_reinitialize`（补 `unlimited→bounded` 缺口）

新增 `state.sh budget reinitialize --plan-count N`，与 `cmd_budget_initialize` 平行，但入口约束相反——**只接受 `unlimited` 入口**（专为升级门）：

```text
cmd_budget_reinitialize():
  current_status = jq '.budget.budget_status'
  if current_status != "unlimited":
      error "reinitialize only valid from unlimited (escape-hatch upgrade). Use 'budget initialize' for fresh formal runs." ; exit 2
  acquire_lock
  review_total = <04 参数化后的公式>(plan_count)    # 见 04，不在此硬编码 3P+12
  effort_total = <04 参数化系数> * review_total       # 04 可能删 effort 2×；此处随 04
  jq '.budget.budget_status = "initialized"
      | .budget.review_total = $rt
      | .budget.effort_total = $et
      | .plan_count = $pc
      | .route = "formal"'                            # 升级门同步把 route 翻成 formal
```

**为什么不直接放宽 `cmd_budget_initialize:911` 的约束**：那个约束保护"fresh formal run 必须从 pending_plan_count 进入"的正常路径，放宽会让任何状态都能重置预算（破坏审计可追溯）。升级门是独立语义（escape-hatch），用独立命令表达，入口约束相反、且强制 `route` 同步翻 formal——语义清晰、不污染正常路径。

#### 3.6.2 升级状态机转换

```text
                    用户喊"升级"/红线被触碰
  [route=light]  ───────────────────────────►  [route=formal, bounded]
  budget=unlimited                              budget=initialized(review_total=公式)
  cursor.phase=execution/workflow               cursor.phase=discovery（回流补设计）

  机器动作序列（Coordinator 执行）：
  1. state.sh budget reinitialize --plan-count <暂估或 1> --run-id <rid>
        → budget unlimited→initialized + route light→formal（原子，单命令）
  2. 补建 design/issue/plan 占位：
        - 已有 light 改动 → 把改动意图写成 design doc（docs/orchestrate/design/<slug>/）
        - 生成对应 issue + plan 占位
  3. state.sh transition --actor Coordinator --from <当前> --to discovery --force
        → 回流到 formal 的 discovery 起点（--force 因为是非常规直跳，:277 允许 force 绕 from 校验）
  4. 进入 formal 流程，已 commit 的 light 改动作为既成事实纳入 plan 的 manifest
```

**状态机不变量**：升级后 `route=formal` 且 `budget_status=initialized`，于是 `validate-plan-dispatch.sh` 的 Step 4 budget-init 门重新生效、transition 矩阵切回 formal 的严格链——**升级门一翻，所有 formal 护栏自动回到岗位**。这正是"route 是磁盘权威"的红利：改一个字段，整套门禁形态切换。

**升级门最小集**：升级门本身需要测试（骨架 §8 验收信号 4"一键升级门存在且经测试"）。最小测试 = `init --route light`（unlimited）→ `budget reinitialize --plan-count 2`（断言 budget_status=initialized、route=formal、review_total=公式值）→ 断言再次 dispatch 时 Step 4 门重新生效。

### 3.7 子模式：hotfix 与 spike（Light Lane 的两个变体）

子模式不是新 route，而是 Light Lane 上**额外声明几个机器锚点的变体**（由 02 routes 清单的子字段表达，或 light route + 一个 `submode` 字段）。

#### 3.7.1 hotfix（先 push 后审）

| 维度 | 行为 | 机器锚点 |
| --- | --- | --- |
| 流程 | Light Lane 直派 Worker → **先 push**（生产救火）→ 事后补审 | route=light + submode=hotfix |
| commit | `commit_format_override="hotfix-unreviewed"`（标记未审提交，便于事后定位） | 现 `commit_format_override` 字段（`state.sh:153`）原样复用 |
| 事后补审 | push 后写 `pending_post_push_reviews` 一条；Closing **读它**派一次事后 regression review | **新机器消费点**：Closing reference 必须读 `pending_post_push_reviews`（现状不读，是缺口）→ 清空前必须补审 |
| 未勾选阻断 | hotfix 仍受未勾选阻断 push 约束？→ **豁免**：hotfix 本就是"先 push"，但要求 push 后 `pending_post_push_reviews` 非空作为"欠一次审"的机器记账 | hotfix submode 下 push hook 放行 + 强制写 post-push 记账 |

**关键修复（现状缺口）**：`pending_post_push_reviews` 字段存在、test 能写（`test_hotfix_post_push_review.sh:42-54`），但 **Closing reference 不读它**（`workflow-closing.md` grep 无命中）——"事后补审"是空头承诺。本设计要求 Closing reference 新增一步：`pending_post_push_reviews` 非空 → 必须派一次事后 regression review 并清空，否则 Closing 不算完成。这是 hotfix"先 push 后审"从散文变机器的核心。

> hotfix 豁免"未勾选阻断 push"是经过权衡的：生产救火必须能立即 push，但用 `pending_post_push_reviews` 记账把"欠一次审"做成磁盘状态，Closing 强制兑付——既不丢救火速度，也不丢质量门（北极星 §质量门以"延后兑付"而非"取消"的形式保留）。

#### 3.7.2 spike / POC（产出 verdict 即弃）

| 维度 | 行为 | 机器锚点 |
| --- | --- | --- |
| 目录 | 临时目录（如 `.claude/multi-model-workflow/spikes/<slug>/`），不进 `docs/orchestrate/` 正式树 | route=light + submode=spike；产物路径与正式编号树物理隔离 |
| 产出 | throwaway code + 1-page verdict 文档（可行/不可行 + 证据），verdict 写完即弃 | verdict 文档是唯一交付物；code 不要求 commit 到主分支 |
| 编号 | **不占 plan/issue 编号**（不写 `docs/orchestrate/plans/` `issues/`） | 不调用占编号的写入路径；spike 产物在临时目录 |
| budget | unlimited（spike 是探索，不卡预算） | route=light 默认 unlimited |
| release gate | 不触发（不进 Closing 的 push/PR） | spike 终点是 verdict 返回，不走 Closing 的 push/PR |

**机器保证**：spike submode 下，(a) 写入路径指向临时目录而非编号树；(b) 不调用任何分配 plan/issue 编号的命令；(c) 终点是 verdict 文档 + 返回，不进 Closing push。这让"产出即弃、不占编号"从散文变成"物理上写不进正式树"。spike 升级路径：若 verdict=可行且用户要落地 → 走 §3.6 一键升级门转 formal，spike 产物作为 design 输入。

---

## 4. 落地要点

| # | 动作 | 文件 | 依赖 |
| --- | --- | --- | --- |
| L1 | schema route enum 加 `light` | `plugin/state-schema/workflow-state-v1.json:18` | 无 |
| L2 | `cmd_init` 的 route `case` 把 `light` 并入 unlimited 分支（或由 routes 清单 budget 参数声明） | `plugin/scripts/state.sh:134-145` | 02 routes 清单 |
| L3 | Entry Gate 判定线：默认 light + 红线升 formal 关键词表 | `plugin/skills/orchestrate-workflow/SKILL.md` Step 1 | 无 |
| L4 | Light Lane 流程段（intent 确认→直派 Worker→自审→commit；三条硬线显式） | `SKILL.md` 新增 Light Lane 段 | 无 |
| L5 | hook gate 豁免读 routes 清单（点 A）：Step 4 budget-init 仅对 bounded route 生效 | `plugin/hooks/validate-plan-dispatch.sh:58-63` | **02 必须先就位** |
| L6 | transition 读 routes 清单判合法性（点 B）：light 允许 `workflow→execution` 直跳 | `plugin/scripts/state.sh:100-114`（随 02 迁移） | **02 必须先就位** |
| L7 | 新命令 `cmd_budget_reinitialize`（unlimited→bounded + route 翻 formal） | `plugin/scripts/state.sh`（新增 + dispatch 在 `:880` 旁注册 `reinitialize)`） | 04（公式参数化） |
| L8 | Closing reference 读 `pending_post_push_reviews` → 派事后审 → 清空（修 hotfix 缺口） | `plugin/skills/orchestrate-workflow/references/workflow-closing.md` | 无 |
| L9 | spike submode：临时目录写入 + 不占编号 + verdict 终点 | `SKILL.md` Light Lane spike 段 + 临时目录约定 | 无 |
| L10 | 升级门测试 + Light Lane dispatch 豁免测试 | `plugin/scripts/tests/`（新增） | L5/L6/L7 |
| L11 | **删假 `phase_skip` 连带清理**（见 §5，**最后做**） | 见 §5 清单 | L1–L10 全部就位 |

---

## 5. 删假 `phase_skip` 的连带清理清单（**真机器点就位后才删**）

> **时序硬约束**：必须在 §4 的 L1–L10（真机器执行点：routes 清单 + hook 豁免 + transition 直跳 + 升级门 + 子模式锚点）**全部就位并测试通过**后，才执行本清单。否则把唯一记录"档位"的字段删了，现状会比现在更乱（骨架 §核心原则：修根因不修表面；先建替代再拆旧）。

| # | 删除点 | 现状 | 删后 |
| --- | --- | --- | --- |
| C1 | `state.sh:152` `"phase_skip": []` 写入 | init 恒写空数组 | 删除该行；档位由 `route` 字段（含 light + submode）承载 |
| C2 | `SKILL.md:68` Route 1 Variant Table 引导语（"`state.sh update` 设置 `phase_skip`"） | 让 Coordinator 手动写 phase_skip | 删除；替换为 Entry Gate 判定线（§3.1）+ Light Lane 流程（§3.2） |
| C3 | `SKILL.md:70-75` Variant Table 整张（phase_skip 列） | hotfix/quickfix/spike/maintenance 折叠成 formal+phase_skip | 替换为 route=light + submode 表（§3.7）；quickfix/maintenance 并入 Light Lane 默认流 |
| C4 | `schema:19-23` `phase_skip` 属性定义 | array of enum | 删除属性（或保留为 deprecated 注释一个版本周期，08 决定迁移节奏） |
| C5 | `test_route_keyword_routing.sh:34-36` "formal route has phase_skip array" 断言 | 断言 phase_skip 是 array | 替换为"light route 走 unlimited + transition 允许 workflow→execution"断言 |
| C6 | `test_hotfix_post_push_review.sh:22-25` 用 `update` 写 phase_skip | 模拟 hotfix 设 phase_skip | 替换为 route=light + submode=hotfix setup；保留 `pending_post_push_reviews` 写入/消费断言（这部分是真的，要加强成"Closing 读它"） |

**注**：`commit_format_override` 字段**不删**（hotfix 仍用 `hotfix-unreviewed` 标记，§3.7.1）。删的只有 `phase_skip` 这个零消费的假机制。

---

## 6. 风险

| 风险 | 说明 | 缓解 |
| --- | --- | --- |
| **R1 误判档位（D1 激进副作用）** | 默认 light，红线关键词表是启发式，可能把"其实碰了计费"的改动误判 light | 升级门（§3.6）是兜底：误判 light 后，用户/Coordinator 一句话即可升 formal，所有护栏自动回岗。北极星红线靠"升级门存在"而非"判定零误报"保证。拿不准就升 formal（业务决策红线） |
| **R2 删 `phase_skip` 时序错位** | 若在 L5/L6/L7 之前删 phase_skip，档位无处记录 | §5 时序硬约束：L1–L10 全绿才执行 §5；08 迁移分期把 §5 排在最后一期 |
| **R3 hook 豁免读 02 清单失败** | 若 routes 清单查询入口未就位，hook 豁免逻辑空转 | L5/L6 标注"02 必须先就位"；02 提供稳定查询入口（如 `state.sh route-gates`）后本分册才落地 |
| **R4 hotfix 豁免 push 阻断被滥用** | hotfix 豁免"未勾选阻断 push"，可能被误当常规通道 | hotfix submode 必须由 Entry Gate 明确的 hotfix 信号（紧急/P0/生产事故）触发；push 后强制写 `pending_post_push_reviews`，Closing 不补审不放行——欠的审跑不掉 |
| **R5 升级门丢失已 commit 的 light 改动** | 升级回流到 discovery 时，已 commit 的 light 改动可能不在新 plan 的 manifest 里 | §3.6.2 步骤 4：已 commit 的 light 改动作为既成事实纳入 plan manifest；升级是单向不回退，不丢已落地代码 |
| **R6 spike 临时目录泄漏到正式树** | spike 产物误写进 `docs/orchestrate/` | submode=spike 物理隔离写入路径（临时目录）；不调用占编号命令；测试断言 spike run 不产生 plan/issue 文件 |

---

## 7. 验收信号

对应骨架 §8 验收信号 2/3/4：

1. **Light Lane 真省**：`init --route light` 的小改动**完全跳过** Discovery（~9.5KB 指令 + 2 次 xhigh Codex job，骨架 §8.1）；从输入到 commit 不经 discovery/plan-writing/plan-review/final-review 完整阶段。
2. **机器执行点存在（非散文）**：
   - `validate-plan-dispatch.sh` 在 `route==light` 时跳过 Step 4 budget-init 前置（可测：light run 未 budget initialize 仍能 dispatch）。
   - `state.sh transition --actor Coordinator --from workflow --to execution` 对 `route==light` 返回 0、对 `route==formal` 返回非 0（可测）。
3. **升级门存在且经测试**（骨架 §8.4）：`init --route light`（unlimited）→ `budget reinitialize --plan-count N` → 断言 `budget_status=initialized` + `route=formal` + `review_total=公式值` + 后续 dispatch 时 Step 4 门重新生效。
4. **hotfix 事后补审兑付**：hotfix run push 后 `pending_post_push_reviews` 非空；Closing 不补审则不返回完成 verdict（可测：模拟 pending 非空 → Closing 阻断）。
5. **spike 不占编号**：spike run 结束后 `docs/orchestrate/plans/` `issues/` 无新增文件；产物在临时目录（可测：grep 编号树无 spike slug）。
6. **假 phase_skip 归零**：`grep -rn phase_skip plugin/` 在 §5 清理后**零命中**（除 08 决定保留的 deprecated 注释）；不存在"字段在 schema、零 hook 消费"的死字段。

---

## 8. 与其他分册的交接

- **依赖 02**（核心）：routes 清单数据结构 + `transition_allowed()` 改读清单 + hook 读清单查 `gate_exempt`。本分册的点 A/点 B 直接消费 02 的清单与查询入口。L5/L6 在 02 就位后才落地。
- **依赖 04**：`cmd_budget_reinitialize` 的 `review_total` 公式随 04 参数化（不在此硬编码 3P+12）；effort 2× 是否删随 04。
- **被 07 关联**：Light Lane 自审用 Coordinator 自身 Read/grep；D2 手动外审走现有 reviewer 派发（07 的 hook 层不阻断 reviewer，`validate-plan-dispatch.sh:68` codex-reviewer 已豁免 Direction Check）。
- **被 08 排期**：§5 删 phase_skip 连带清理排在迁移最后一期（L1–L10 全绿后）；升级门 + hotfix Closing 补审是独立可测增量，可早期落地。
- **守 §5 保留清单**：Light Lane 复用 worker-loop 派发层（§5.1/5.2）、磁盘状态断点续传（§5.3）、子代理必验（§5.5）、Worker 禁改 docs/（§5.10）、未勾选阻断 push（§5.16）——一个不丢。
