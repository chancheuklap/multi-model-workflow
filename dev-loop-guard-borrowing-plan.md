# 开发主循环守卫补强方案（graph/loop 借鉴收敛稿）

> 状态：动作三已定案（用户 2026-07-20 拍板**删字段**，pi 版已删并落打转守卫三字段）；动作一 / 二 pi 版已落地（worktree-dev-loop-guards-pi），plugin 版待 Claude Code 落地，droid 版后定。
> 范围：三镜像（`plugin/` `droid-plugin/` `pi-plugin/`）同步。
> 来源：2026-07-20 双模型独立分析 + 三轮交叉审查收敛。
> 性质：本文件是双模型讨论工作稿，非长期设计文档。终稿定案后，长期约束折进 `AGENTS.md` / `references`、实现走 worktree 分支，随后删除本根目录文件（项目规则：不维护独立设计文档、修在 worktree）。
> 复审：2026-07-20 Claude Code 侧复审修订三处（动作一补 turnaround 判据、动作三修正 pi 视角偏差、行号纠错），变更记录见文末；行号以脚本为准、按镜像标注，禁跨镜像照抄。

## 背景与判据

loop engineering / graph 架构的核心课（验证器即工程、显式状态机、新鲜上下文 + 文件状态、类型化回边）mmw 主流程已具备。真正缺口：仓库内 `release-flow`（打包发布）已有全套自治守卫，而天天用的开发主循环（写码→审查→返工）在同一位置 fail-open——收敛只靠文档提醒文字，无引擎强制。这违背本项目「不静默兜底、fail-closed、行为分叉落 manifest 由脚本强制」（v6.5.0 决策）的既定原则。

借件判据：复用自己仓库已验证的模式，不引入外部框架，不过度设计。

## 动作清单

| # | 动作 | 定性 | 优先级 |
|---|---|---|---|
| 1 | 开发循环同根因打转强制上报 | 技术实现（需设计新分类器） | 最高 |
| 2 | unattended 墙钟 / 轮次软预算 | 纯技术实现 | 高 |
| 3 | `gate_fingerprints` 做实或删字段 | **已定案：删字段** | 中 |
| 4 | reward-hacking diff 预检 | 纯技术，backlog | 低 |
| 5 | progress 路线图可视化 | 纯展示层 | 最低（前四件完成后） |

## 动作一：开发循环同根因打转强制上报

### 现状（证据）

- 主循环返工 / 掉头只打 WARN 文字，无引擎动作：「已返工 N 轮……持续打转要主动交人」（`flow.sh`：plugin:190 / droid:192 / pi:200，三镜像同文）。
- 对照组 release-flow 四件套齐全：同根因熔断（`release-flow.sh:88` CIRCUIT-BREAK）、轮次 / 墙钟预算（:98/:110）、轮次到顶自动 surface 交人（:1202 ROUND-CAP）、逐动作 attempt_ledger。
- release-flow 的指纹来自其 diagnose 分类管线（把构建日志翻译成带 tier + fingerprint 的失败，`release-flow.sh:1012` 注释 + `release_contracts.py classify-findings`）；开发循环无此管线，**不能照抄**，同根因判定需重新设计。

### 目标形态

「打转」在 `flow.sh` 里本就是**两个独立计数器、两个独立阈值**，性质不同，需**两条判据**，共用同一套上报 / 硬停动作——不能用一条 findings 指纹糊住：

- **判据 A — 审查返工打转（`needs-repair` / `repair_count`；plugin `flow.sh:189` ≥3 只 WARN，pi / droid 行号各自核）**：计数对象是「同一 finding 的重现」，不是返工轮数（三轮修三个不同缺陷是健康迭代，同一缺陷反复修不掉才是打转）。
  - 数据源：审查留痕 `docs/reviews/<slug>-<stage>.md` 的 accepted findings 集合。
  - 指纹：文件 + 归一化缺陷签名（标题 / 类型级）；**行号只作弱信号**——返工改代码会挪行号，锚 `file:line` 会把同一缺陷误判成新缺陷而放过真打转。
  - 判据：连续两轮审出实质重合的 accepted findings = 打转。规模为几十行归一化比对，不碰 release-flow 的构建日志管线。
- **判据 B — 方向掉头打转（`needs-redirection` / `turnaround_count`；plugin `flow.sh:210` ≥2 只 WARN，pi / droid 行号各自核）**：掉头往往没有 findings、是方向反复变，findings 指纹套不上；这里**裸计数反而正确**——同一 `to-phase` 被反复回退本身就是信号。
  - 判据：同一 `to-phase` 的 `turnaround_count` 达阈值 = 方向横跳打转。AFK 无人值守下方向反复横跳与审查打转同样烧 token，同样要堵。
- **阈值字段**：两条判据各一个阈值，落 `routes.json`，与 `review_gates` 同级（判断落 manifest、脚本强制）。
- **触发动作分 attendance**：
  - attended / afk → 引擎置 `waiting-user` + `mmw where` 置顶；**不锁死**，人来想继续就继续（保留 `routes.json` description 的既定决策：流水线态回上游「向用户汇报但不锁死」）。
  - unattended → 硬停写板，不问人（套用 `steer.sh:77` 默认策略 `review_fail=rework_then_hard_stop` 先例，`references/control/attendance.md:50`）。

## 动作二：unattended 墙钟 / 轮次软预算

- 严格限定 unattended（attended 时人就是预算，不需要）。
- 一份 plan 反复 resume 可在无人值守下长时间烧 token；给墙钟或总轮次软预算，超了 surface 写板，**不硬杀**。

## 动作三：`gate_fingerprints`（待拍板：做实 / 删字段）

### 缺口（已亲验）

- schema 声明了一整套行为：「gated 阶段过闸时记产物内容指纹（phase→hash），`mmw where` 再算比对，不同 = 过闸后被改 → 提示回该阶段重审」（pi `task-manifest.schema.json:119-124`，标「可选」）。
- 全仓脚本与文档**零引用**该字段——声明的守卫不存在，零上下文 agent 读 schema 会误判有保护。

### 仓库内可抄的指纹模式（含镜像差异，已复核）

1. **approval 文档指纹（三镜像通用，首选可抄）**：plugin `flow.sh:47-60` 实现比对（`approval_check`），算法单源在 `note.sh fingerprint`，`approval_stale` 硬停输出于 plugin **`flow.sh:492`**（原稿写 517，实测有误已纠）。这是最贴 `gate_fingerprints` 目标（过闸产物事后被改 → 提示重审）的模式，三镜像都有。
2. **审查窗口工作树基线（仅 pi 版有）**：`review_worktree_fingerprint` / `review_worktree_clean_check` 仅存在于 pi `review.sh:30-51`，plugin 与 droid **零实现**（已 grep 三镜像复核）；且其目标是「审查窗口内工作树没被偷改」，与 `gate_fingerprints`「过闸产物事后被改」**目标不同**，只是指纹 + 比对手法可借鉴。
   - **对分工的影响**：pi 版（Kimi 负责）动作三可直接复用这套；plugin / droid 版（plugin 由 Claude Code 负责）**没有现成 clean-check，得从 approval 模式自建**。所以「三镜像做实」不是三份复制同一份代码，而是各镜像基线本就不齐、各自按自家现状落。

### 选项

- **做实**（两模型均推荐）：复制 approval 模式到 plan / final 过闸产物；「过闸产物被偷改 → 提示重审」正是 fail-closed。注意 `where` 是热路径——只在闸点算指纹，不在每次 `where` 全量算。
- **删字段**（**已拍板采用**，pi 已删）：去掉空头承诺止血，不留「声明了行为却零实现」的字段误导后来人。

## 动作四：reward-hacking diff 预检（backlog）

- 落地 diff 自动扫：测试文件净删除行 / 断言计数下降 / 新增 `skip`·`xfail`·`only`。
- 只作验收回执里的注意力提示塞给验收人，**绝不做成闸**（已有跨模型全新审者重审兜底，硬闸即过度）。

## 动作五：progress 路线图可视化（最低优先）

- progress 板按 preset 阶段序列（`routes.json` `presets`）拼一小段路线链，标当前节点 + 各回边 repair 计数。
- 纯展示层零风险；数据全现成（presets + `task.json` `repair_count`）。

## 明确不借（过度设计红线）

- LangGraph 式图 DSL / 重写编排引擎（`routes.json` + `conclusions` 已是够用的状态机）。
- checkpoint 时间旅行 / 回放（git 已给）。
- typed state schema / reducer 注册表。
- 单 loop 内 context 压缩框架（subagent 隔离 + 落盘已解决 context rot；review 刻意「原样落盘不摘要」，摘要会丢审计证据）。
- 逐 tool-call 细粒度 trace、AutoGen 式多 agent 自由辩论（前者观测性过度，后者破坏可审计流水线）。

## 落地范围与纪律

- **分工（2026-07-20 定）**：plugin（Claude Code 版）由 Claude Code 负责落地；pi 版由 Kimi 负责落地；droid 版后续再定。各自在自己宿主内实现 + 真跑验证，不替对方镜像定行号。
- **共用面协调**：纯文字片段仍走 `build/fragments` + `build.sh --apply` 单源，谁动片段谁跑 `build.sh --check` 保证三镜像无 DRIFT；`flow.sh` / `routes.json` 是各镜像单宿主实现，各负责人各改各的、判据语义对齐即可。
- **验证**：动作一 / 二改 `flow.sh` 引擎，各自补 `scripts/tests/test_flow.sh` 用例（判据 A 同根因打转 + 判据 B to-phase 掉头 × attendance 分支）；本镜像全量测试全绿。
- **责任**：Coordinator（主线程）落地；Worker 不碰本文档与 `docs/`。

## Claude Code 复审变更记录（2026-07-20；Kimi 复核回应见文末）

1. **动作一补 turnaround 判据（实质）**：原稿目标形态只写 findings 指纹一条，只治审查返工（`repair_count`），漏了方向掉头（`turnaround_count`）——`flow.sh` 里这是两个独立计数器、两个阈值。已拆成判据 A（findings 指纹）+ 判据 B（`to-phase` 掉头裸计数），共用同一套上报 / 硬停动作。否则方向反复横跳的 fail-open 洞没堵，它在 AFK 下同样烧 token。**请 Kimi 确认这条拆分在 pi 版是否同构。**
2. **动作三修正「pi 独有当三镜像通用」（事实）**：原稿把 `review_worktree_fingerprint` 当仓库通用可抄模式，实测**仅 pi 版有**、plugin/droid 零实现，且目标与 `gate_fingerprints` 不同。已改为分工事实：pi 版可直接复用，plugin/droid 版得从 approval 模式自建。
3. **行号纠错**：`approval_stale` 原稿 `flow.sh:517`，plugin 实测 **492**；已改并按镜像标注。行号一律以脚本为准、逐镜像重核，禁照抄。
4. **元层面（落地形态）**：本文件以独立设计文档形态直接 commit 到 main 根目录，触及项目「不维护独立设计文档、修在 worktree」两条硬规则。建议终稿定案后：长期约束折进 `AGENTS.md` / `references`、实现走 worktree、删除本根目录文件；`a5b20cb`（main 上、未 push、可逆）由用户定 revert 或转正式产物。

**对齐结果**：动作三已定案删字段（pi 已落）；判据 A、B 同批进首个 worktree 两边一致（pi 已同批落地）；plugin 版由 Claude Code 落地，droid 版后定。

## Kimi 复核回应（2026-07-20）

1. **判据 A/B 拆分：接受，pi 版同构已亲验**——pi `flow.sh:199`（返工 ≥3 WARN）、`:220`（掉头 ≥2 WARN）、`:216`（掉头时重置返工计数），与 plugin 逐字同构。**一处实现修正**：现有 `turnaround_count` 是全局计数（pi `:204` `tc+1`，不分目标阶段），判据 B 的「同一 `to-phase`」语义需新增按目标阶段的掉头账（小 ledger），不能只读现有计数器——否则不同阶段间合理精修（design→plan→回 design→回 plan）会被误伤，与判据 A「不误伤正常迭代」同一原则。
2. **`review_worktree_fingerprint` 仅 pi 有：接受**（已 grep 三镜像复核：plugin / droid 零命中）。动作三的可抄基线修正为：approval 指纹三镜像通用（首选），clean-check 仅 pi 可借手法。
3. **行号纠错：接受**（`approval_stale`：plugin `flow.sh:492` / pi `:517` / droid `:499`，三镜像各有该机制，原稿 517 是 pi 行号未标注镜像）。
4. **元层面**：根目录文档 + 直提 main 是用户明确指令，覆盖「不维护独立设计文档、修在 worktree」两条规则；采纳其生命周期建议——定案后长期约束折进 `AGENTS.md` / `references`、实现走 worktree、删除本文件；`a5b20cb` 保留（未 push、可逆、是用户要的产物）。
5. **判据 A、B 同批进首个 worktree：赞成**。两个计数器在同一个 handoff switch、共用同一套 attendance 分支动作、同一个测试文件，拆开等于同段代码改两遍。
