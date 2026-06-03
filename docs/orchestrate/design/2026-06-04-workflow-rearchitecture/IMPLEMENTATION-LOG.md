# 实施决策日志（AFK 自主落地）

> 用户 2026-06-04 授权：生成设计文档后直接按文档完整真实落地；过程中决策自己拍板并执行、全程记录、最后汇报；不半路停。本文件记录所有判断，供用户回来复核。

## 运行框架决策

| 编号 | 决策 | 理由 |
| --- | --- | --- |
| R1 | **在 `main` 上直接实现**，frequent scoped commit，AFK 不 push | 本仓库开发历史全在 main；全局规则"不在主仓库直接切分支"指别建分支、非别提交；push 需显式授权 |
| R2 | **直接以架构师身份实现，不路由经 plugin 自身的 orchestrate workflow** | 用重型/有 bug 的旧 workflow 自我改造是循环依赖；其预算硬阻断（正是要修的 bug）会在 AFK 卡死我 |
| R3 | **不 merge/不 build-on/不删改 `control-flow-codification` worktree** | 它 v4.0.2、净增 1744 行+更多硬门（与 D3 反向）、落后 main 14 commit；用户要的是基于 main 的简化新设计；仅参考其可用子方案 |
| R4 | 主 `plugin/` 树无 `AGENTS.override.md`（仅 worktree 有）→ 无同步义务，不擅自新建 | 全局规则是"存在则同步"，主树不存在 |
| R5 | Codex 设计评审：文档定稿后若 codex 就绪则跑一轮对抗评审（用户珍视的模式），有效 finding 自己采纳并记录 | 在大规模落地前用外部模型把设计验一遍，降 AFK 风险 |
| R6 | hook 安全：已确认 `enforce-plan-commit`/`guard-premature-push`/`gate-codex-review` 无活跃 run 时全 no-op，commit 不以 `Pack ` 开头 → AFK 提交不被拦 | 见 hook 源码 |

## 设计文档集一致性复核（workflow 2 + 主线程亲验）

一致性审查 verdict=**needs_fixes，但无决策违反、无不变量违反**（"整体质量高"）。发现的是口径/路径瑕疵，处置如下：

| 发现 | 处置决策 |
| --- | --- |
| `dispatch-route-worker.sh` 被 02/07/08 误归类为 "hook"（实际在 `scripts/`，未注册 hooks.json） | **代码权威**：实现时按 script 处理（已亲验在 `plugin/scripts/`）。文档为草案，不做抛光绕路（#14）；最终报告标注 |
| routes-v1.json 字段命名在 02/03/05/07 不统一（`dispatch_shape` vs `dispatch_granularity`、`gate_exemptions` vs `gate_exempt`） | **我即实施者**，用代码里唯一一套命名消解漂移；以 P1 写的 `routes-v1.json` 实际字段为权威 |
| 05 内部 "5 vs 6 个 SKILL" 自相矛盾 | 实测：signpost phase 序列注入 5 个（workflow 除外）、voice/preamble 注入 6 个。实现时按实测 |
| 08 §4.2 部分 test 文件名未逐一验在 | 每期实际跑 `run-all-tests.sh` 时自然暴露不存在的 test，按实际处理 |

**亲验通过的承重引用**（子代理纪律）：`dispatch-route-worker.sh` 在 scripts/ + :48-54 case 白名单属实；`cleanup-before-push.sh:51` `route=="hotfix"` 死代码属实；`bug-investigation-route.md` 在 `orchestrate-workflow/references/`；`pending_post_push_reviews` 零被 `workflow-closing.md` 读。

## 落地分期（依据 08，按 6 期推进）

`P1 routes 数据 → P2 state/hook 改读 → P3 Light Lane+升级门+红线升级 → P6 删假字段`（关键路径串行）；`P4 预算降仪表`、`P5 skill/agent/hook 重构+漂移根治`（解耦并行）。铁律：加法先于减法、fail-open 回退、每期三件套（子集 test + verify-maturity + build --check）全绿才 commit、每期版本 minor+1 双处同步。

### 落地决策（按实施推进逐条追加）

**R7 版本号不逐期 bump（偏离 doc 08 §6.1）**：08 建议每期 minor+1（3.11→3.16）。但 6 期是一次重构的增量落地、未发布（不 push/不上架），逐期 bump 6 次是无意义 churn（违 #14）。改为整个重构完成时一次性 bump，中间各期维持 plugin.json/marketplace.json=3.10.0 一致（verify-maturity 版本同步检查照过）。最终版本号在收尾定（倾向 3.11.0，非破坏性对外 API；如需标志结构重构可 4.0.0）。

#### P1 建 routes-v1.json 数据清单 ✅

- 新建 `plugin/state-schema/routes-v1.json`（4 enum: formal/direct-repair/bug-investigation/multi-pr-merge + 预置 light 子形态）、`routes-v1.schema.json`（meta-schema）、`plugin/scripts/tests/test_routes_manifest.sh`（46 断言）；更新 `state-schema/README.md` 索引。
- **流程形态切分决策**：work-item 状态机（pending/dispatched/returned/...）+ route-worker 入口（workflow:dispatched）+ 终态（*:closed/*:blocked/*:execution_done）→ `global_transitions`（route 无关）；phase 推进（workflow→discovery 等）→ `routes[r].phase_transitions`（route 相关）。`workflow:dispatched` 归 global（消解一致性审查指出的 02 formal 示例把它放 phase_transitions 的小瑕疵）。
- **light 数据形态预置但不接 hook**（留 P3）：light.phase_transitions 不含 `workflow:discovery`/`discovery:plan-writing` → 机器层 transition 不存在即拦轻档误跳（D4 物理实现的数据前提）。
- **行为等价锚点**：test 断言 `global ∪ formal.phase_transitions` 覆盖旧 TRANSITION_MATRIX 全部 8 条 Coordinator phase 推进 + 12 条 work-item → 保证 P2 改读清单后 formal 零回归。
- 验收：test_routes_manifest 46/46；全量 44 套件全绿；build --check 干净；verify-maturity 115/0。零行为变更（无读取方）。

#### P2 state.sh/hook 改读 routes 清单 ✅（派 sub-agent 实现，主线程复核）

- 派一个聚焦 sub-agent 实现，主线程亲验：重跑三件套全绿 + 读 state.sh 核心 diff + **正确姿势手动复验** 6 条 transition 行为。
- 改动：state.sh（`routes_load`/`route_field`/`_matrix_match`/`transition_allowed` route-aware+fail-open、`cmd_init` 读 `budget.init`、`cmd_transition` 传 route、删 :75/:78/:96 行尾历史注释、TRANSITION_MATRIX 留作 fallback）；新增 `hooks/lib/routes.sh`（共享 jq helper：dispatch_shape/commit_format/readable）；3 hook 改读 dispatch_shape 带 fail-open（validate-plan-dispatch / validate-pack-manifest / dispatch-route-worker）；cleanup-before-push 死 `route=="hotfix"` 改读 commit_format；state-transition-matrix.md 降级人读说明；verify-maturity C2 check 对齐新数据源（§4.4 要求，未弱化）；新增 `test_routes_transition.sh`（15 断言：formal 等价 / light 拦 discovery / fail-open）。
- **头号新行为已主线程手动复验**：formal workflow→discovery 允许、light workflow→discovery **拒绝**、light workflow→plan-writing 允许、fail-open（清单缺失/未知 route）回退旧矩阵放行但非法 actor 仍拒。
- **复核中纠错**：我首次手动测试误报"formal 被拒"，根因是没先 `update .cursor.phase`（cmd_transition 校验 --from==current）→ 姿势问题非 bug，正确姿势复验全过。
- 偏离记录：dispatch-route-worker 用 PHASE 作 route key（envelope 无 route 字段、route-worker 路由 phase 名恒等 route 名，已核验）；state.sh 另 3 处 `Plan 005 Pack 5.7` 是函数头"谁调用"说明、非 transition 历史、不在本期删注释范围，保留。
- 验收：全量 45 套件全绿；build --check exit 0；verify-maturity 115/0。CLAUDE.md 的 8 行外部仓库 URL 是用户开场改动，未 stage。

#### P3 Light Lane + 升级门 + 红线守卫 + 子模式 ✅（派 sub-agent，主线程重点亲验）

- P3 是 D1"激进默认轻档"的安全闸所在，主线程重点亲验：三件套重跑 + 4 项头号行为手动复验 + 审 cmd_budget_reinitialize/redline-check 源码 + 3 条设计约束核对。
- **修跨文档矛盾（代码即权威）**：doc02 把 light.budget 误抄成 pending_plan_count，doc03 §3.3 权威 light=unlimited → manifest 改 unlimited。
- 改/增：schema route enum +light（5 值）；routes-v1.json light.budget→unlimited；**新命令 `cmd_budget_reinitialize`**（只从 unlimited 入、原子写 budget initialized+公式+route 翻 formal = 一键升级门，补 unlimited→bounded 缺口）；**新 `redline-check.sh`** advisory CLI（4 类红线关键词，命中 exit0+类别名，**不注册 hooks.json**）；SKILL.md Entry Gate 加 D1 判定线+Light Lane 流程+hotfix/spike 子模式（全在 build 锚点外）；workflow-closing.md 加 Step 22b 读 pending_post_push_reviews（修 hotfix 事后补审缺口）；3 新测试（budget_reinitialize/redline_check/light_lane_dispatch）。
- **主线程手动复验通过**：① light init=unlimited；② reinitialize→initialized+route=formal+review_total=18；③ 从 formal(pending) 调 reinitialize 被拒 exit2；④ redline billing/auth 命中、纯文案不中。**3 约束核对**：redline 不在 hooks.json（advisory 非强 hook，符 #14+doc03§3.1）；workflow-closing 读 pending_post_push_reviews（缺口已修）；phase_skip 未提前删（留 P6）。
- 落地决策 D-A..D-E（light=unlimited / gate 豁免靠 unlimited 不加 hook 读 gate_exemptions / 红线 advisory 非 hook / 不删 phase_skip / reinitialize 公式暂同 initialize 待 P4 参数化）均落实。偏离：redline-check 用并行 case 替 `declare -A`（macOS bash 3.2 兼容，行为不变）。
- 验收：全量 48 套件全绿；build --check exit 0；verify-maturity 115/0。

#### P4 预算降为仪表 ✅（派 sub-agent，主线程独立复验全部头号行为）

- P4 是 D3"AFK 软继续到顶停 / 在场过半停"的落点，主线程不仅重跑三件套，还用**全新 state 独立手动复验** 6 项验收信号（不依赖 agent 自带测试）。
- **落地决策 D-P4-a..f 全部落实**：
  - **D-P4-a effort 维度走方案 A 全删**（doc04 §3.6 推荐）：删 `track-effort-budget.sh` + hooks.json 注册 + state.sh 全部 `effort_total`/`effort_used` 写点 + schema 字段 + 两个纯 effort 测试。依据：effort 零独立 gate，唯一作用是抢 `pending_direction_check` 槽位，纯冗余维度。
  - **D-P4-b `attendance_mode`** 顶层 enum default `afk`（安全默认偏向不卡死）；新 `cmd_set_attendance`。
  - **D-P4-c `review_credit` + `cmd_budget_credit`**：reflux 按受影响 Plan 数 ×`REVIEW_PER_PLAN` 归还；阈值判断全改用 `effective_used = review_used − review_credit`，保 `review_used` 审计真相。
  - **D-P4-d 公式抽常量** `REVIEW_PER_PLAN=3`/`REVIEW_FIXED_RESERVE=12`；`initialize` 加 `--review-total N`（custom）/`--profile {standard|generous=4P+16|tight=2P+6}`。
  - **D-P4-e 双模式钩子**：`track-review-budget.sh` 与 `cmd_budget_increment_review` 同步分叉——attended 80% 写 DC；afk 80% 仅软信号、100% 才写 DC（escape hatch，threshold_percent=100）。**改动点：现状 100% 原本不写 DC，本期改为 100% 两模式都写 DC，这是 AFK 硬停的实现。**
  - **D-P4-f R1 缓解**：`override_count` 上限 `MAX_OVERRIDES=2`，`budget check --allow-over-budget` 超限硬 BLOCKED exit2 报用户（防 Coordinator 失控自我放行无限烧）。
- **主线程独立手动复验通过**（全新 state，formal route，plan-count 4→review_total 24）：① afk increment 到 19/24(80%)→DC 仍 null + 软文案；② attended 到 20/24→DC pending threshold 80；③ afk 到 24/24(100%)→DC pending threshold 100；④ `credit --plans 2`→review_credit 6、effective 20→14；⑤ override#1/#2 放行(count 1/2)、#3 BLOCKED exit2；⑥ 公式无覆盖=24/standard、`--review-total 50`=50/custom、`--profile generous`=32/generous。
- **§5.14 防无限烧不丢**：到顶 100% 必有一次硬停（任意模式写 DC）+ 仪表全程可见 + override cap=2 + 在场模式保留过半停。删的是"过半永久卡死等人"，留的是"到顶必停 + 全程可见"。
- 偏离/遗留：① verify-maturity C3 check 从"track-effort 存在"改为"不存在"（更有语义价值，验删除意图）；② 6 个测试 fixture 的旧 effort 字段一并清理到新 schema；③ `architecture-draft.md`（架构权威文档）与 `reviews/*.md`（历史审计快照）仍含 effort_total 描述——前者属架构文档漂移，**归 P5 漂移根治**统一处理；后者是历史快照不动。
- 验收：全量 47 套件全绿；build --check exit 0；verify-maturity 115/0；json.tool 干净。

## 待用户复核的关键项

- **worktree 改道**（R3）：本次在 main 按新设计实现，未续 `control-flow-codification` worktree。若你本意是续那个 worktree，回来一句话我改道。
- **Codex 设计评审**（R5）：见实施中决定（若 codex 就绪则对高风险代码做评审）。
- 实施中的其他自主决策见上方"落地决策"。
