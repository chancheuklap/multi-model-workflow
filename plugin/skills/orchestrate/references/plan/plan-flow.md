# Plan · orchestrate 步(本步读这一份)

> plan 阶段第一步:判单/多计划、映射 plan 清单、写跨 plan 合同骨架、fan-out plan-writer、亲验返回、回填,加角色声音 + Git 纪律。**单计划的 plan 撰写在 write 步(`mmw step next` 进);就绪门自检在 selfcheck 步。**

## 模式(先判,决定派不派 subagent)

| | 单计划 · 主线程内联 | 多计划 · subagent fan-out(默认) |
|---|---|---|
| 何时 | **只一个大 issue、且不大不复杂** | 多个大 issue,或单个但大/需深探代码 |
| 怎么写 | **主线程自己**在 **write 步**(本步映射完 `mmw step next` 进)照 `task-pack.md` 写这份 plan,不派 plan-writer——省一次派发往返 | 本步 Step 3 逐 issue 派 `plan-writer` |
| 跨 plan 合同 | 无(单计划),跳 Step 2 / Step 5 | Step 2 写骨架、Step 5 回填 |

下面 Step 1–5 是本(orchestrate)步内容:**单计划**只走 Step 1 映射 → `mmw step next` 进 write 步自己写;**多计划**走 Step 1–5(映射→骨架→fan-out→亲验→回填)→ `mmw step next` 进 selfcheck 步。就绪门 + 收尾 handoff 都在 selfcheck 步。

## 两个角色(写作下放,编排上收)

| 角色 | 谁 | 职责 |
|---|---|---|
| **主 Agent(你)** | 本阶段 驱动者 | 读 design + issue → 写跨 plan 合同骨架进设计文档 → fan-out plan-writer → 亲验返回 → 回填合同细节 → 就绪门 → handoff |
| **plan-writer** | 派出的 sub-agent(`subagent_type: "plan-writer"`) | 拿(带合同骨架的)设计文档 + 单个大 issue + 方法论 reference,**自己把大 issue 拆成小 issue**,写出一份自洽 plan(Header + Task Pack + TDD 步骤 + 验收)。拆分、写作纪律、Self-Check 都在它身上 |

**合同分两层**:跨 plan 合同骨架(主 Agent 在 Step 2 写进设计文档 `## Cross-Plan Contract Anchors`,给并行 writer 不撞车的硬边界);每份 plan 的 Global Constraints / File Map / 内部 Dependency Graph(writer 从设计抄 + 自己写进 plan header)。

## 角色与声音(主 Agent)

你是计划编排器。把 plan 清单分发给 plan-writer,确保每份返回的 plan 真实、自洽、可验证;跨 plan 合同面一致。每份 plan 的 scope 用 issue + 文件名界定,不用模糊描述;plan 间依赖用 blocked_by 显式标注;不确定的拆分点标 `[needs-evaluation]`。

Good: "Plan 拆 4 个 pack。1→2→3→4 串行,2 依赖 1 的 schema。派 4 个 plan-writer,互不依赖的 1/3 并行。"
Bad: "制定了全面的实施计划,涵盖所有功能模块。"

禁止词:delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, crucial, additionally, pivotal。

## Step 1:读 design + issue,映射 plan 清单

读源设计文档(`prev_outputs` 里的设计文档路径),提取 goal / architecture / 合同边界 / 测试 seam——**只读,作为派发时给 plan-writer 的上下文**,不在主线程展开写作。

读每个大 issue(`to-issue` 阶段在 `docs/issues/<slug>/` 立的骨架),提取 What to build、Blocked by,定 **plan 清单**(一个大 issue → 一份 plan → 一个 plan-writer)。**小 issue 不在这拆**——它的 `## Small issues` 通常是 `<!-- PENDING -->`(to-issue 阶段故意留白),由 plan-writer 接手时自己拆,逼它认真读代码 + 规划。主 Agent 只到大 issue 粒度。

**映射规则**:源设计 → 全局上下文(喂每个 writer,只读);大 issue → 一份 plan;小 issue → 一个 Task Pack(writer 拆 + 写);小 issue 验收 → Pack 验收;小 issue blocked-by → Pack dependencies。
映射不成立:术语 / 验收不清 → handoff `needs-redirection --to-phase design` 回 design 改(`needs-repair` 是原地返工、回不到 design);架构假设与代码现实不符 → 用 `codebase-design` skill 厘清后再派。

**轻量核现状**:用 `rg`/`find` 确认设计涉及的 plan 落点目录、关键路径真实存在——够判断派几个 writer、各管哪个 issue 即可。**深度代码理解由 plan-writer 各自用 `codebase-design` 做**,主 Agent 不抢着探全。

## Step 2:写跨 plan 合同骨架进设计文档(多 plan 时;单 plan 跳过)

派 writer **之前**,从设计文档 `## 合同边界` + architecture + 大 issue 依赖图,判断有没有跨 plan 连接面(共享文件 / 模块 / schema、一份 plan 产出另一份消费的接口)。有就把**骨架**写进设计文档的 `## Cross-Plan Contract Anchors` 占位:

- **文件所有权划分**:哪份 plan 可碰哪些共享文件——一文件一 owner,防两个 writer 并行改同一文件。
- **跨 plan 接口**:owner / provider / consumer 按 plan 编号写("001 provide 鉴权 token 接口,002 consume"),命名到位、**精确字段 / 签名先标 `(字段待 plan 回填)`**——这是骨架,细节 Step 5 回填,不是 TBD。

无跨 plan 连接面 → 写明"无跨计划共享合同",跳 Step 3。骨架是给 writer 的硬边界:dispatch 时随设计文档进 writer 上下文,writer 不许认领别的 plan owner 的文件。

## Step 3:Fan-out 派 plan-writer

每个大 issue 派一个 `plan-writer`(`subagent_type: "plan-writer"`)。**互不依赖的 plan 用 宿主后台派发 并行;有 blocked_by 链的按依赖序派。** 每个 dispatch 给(且只给)该 writer 它那份 plan 需要的:

- **落点**:`docs/plans/<slug>/00N-<issue-slug>.md`(slug 与源设计 / issue 对齐,已含日期;多 plan 同一目录)
- **源设计文档路径**(含 Step 2 的合同骨架:architecture / `## 合同边界` / `## Cross-Plan Contract Anchors`——writer 据此知道能碰哪些文件、provide/consume 哪些接口)
- **该 writer 负责的 issue 文件路径**(`## Small issues` 多为 `<!-- PENDING -->`,writer 自己拆 + 写回)
- **方法论 reference 路径**:`${CLAUDE_PLUGIN_ROOT}/skills/orchestrate/references/plan/task-pack.md`(写作方法论一份读完,含 TDD 步骤 + 测试规划严谨度;给绝对路径)
- **mockup 目录**(若 `docs/design/<slug>/mockup/` 存在)

**不要**把别的 writer 的历史 / 别的 plan 内容粘进去——每个 dispatch 独立、零交叉污染。单 issue → 单 plan:派一个就行,不强行并行。

## Step 4:亲验返回

每份 `plan-writer` 返回 `pass` 后,对它声明的事实(plan 文件存在、Pack 数量、引用的 `file:line`、**小 issue 已写回 issue 文件 `## Small issues`**)至少抽验 1 个(`grep`/`Read`)再采信。失实 → 重派该 writer 或主 Agent 亲查修正。任一返回 `needs-context` / `needs-repair` / `blocked` → 按其内容补上下文或修源设计后重派;返回 `needs-redirection`(探代码撞破设计方向)→ handoff `needs-redirection` 交用户拍方向。全部 `pass` + 验过 → Step 5。

## Step 5:回填合同细节 + 核边界(多 plan 时)

Step 2 的骨架已划好边界,本步把**精确字段 / 签名**填实并核 writer 有没有越界。扫每份 plan 的 File/Responsibility Map + Contract anchors + migration/registry(plan-writer 返回的 `Cross-plan touchpoints` 区块是入口),把 Step 2 标 `(字段待 plan 回填)` 的格子补成真实 owner / provider / consumer / 字段,写回设计文档 `## Cross-Plan Contract Anchors`(单一源)。核边界:writer 有没有认领别人 owner 的文件、provider 接口与 consumer 期望对不对得上。provider/consumer 缺失、ownership 冲突、接口签名不匹配 → `SendMessage` 对应 writer 修。

## orchestrate 完 → 下一步(脚本导航)

- **单计划**:Step 1 映射完 → `mmw step next` 进 **write 步**(自己照 task-pack 写 plan)。
- **多计划**:Step 1–5(映射→骨架→fan-out→亲验→回填)做完、plan-writer 都 pass + 亲验过 → `mmw step next` 进 **selfcheck 步**(就绪门 + 跨 plan 覆盖自检 + handoff)。

## Git 纪律

写 plan 阶段不 commit、不 push,改动保持 unstaged,落地通过后统一提交。**plan-writer 不 commit;主 Agent 统一提交**(设计文档回填和 plan 文档分别提交)。
