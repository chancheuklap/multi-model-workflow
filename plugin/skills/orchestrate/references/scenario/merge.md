# Merge · 多 PR / 分支合并(场景操作指南,读全文)

> 用户要合并多个并行 worktree / PR 时,orchestrate 路由到这。**不开新 worktree**——Coordinator(你)在主仓库做。这些 PR 来自**同一大设计/大计划**,各自已过自己的 ④终审,但**它们之间的交互没验过**。
>
> **理念**:merge 的命门不是 git 文本冲突,是**业务意图 / 功能设计冲突** —— 两个 PR 各自正确、合起来语义打架(功能依赖被改、同一业务流被从不同环节改、领域假设不一致、migration 顺序错)。**git 能干净合 ≠ 设计不冲突。**
>
> **原则**:冲突是 **PR 与 PR 之间**的(不是 PR 与 main);代码冲突好解、**功能/意图冲突最难**;**系统性冲突先调查再修**,不盲改根因不明的冲突;**所有 PR 并行分析**不逐个;merge 是红线要人批。

## 1. 看全队 + 建 merge-brief(单一权威源)

```bash
mmw task team
```

逐个在管 worktree 一行:`slug / title / scenario / phase / status / branch / base_commit / design / open_items / subtasks`。

据此写 **merge-brief**:`状态平面/<slug>-merge-brief.md`(本场唯一"合并后正确状态"权威源,后续每次派 Codex 都引它的路径、不粘内容)。**merge 在主仓库跑,一切产物只落 `状态平面/` 状态平面(对 git 隐形),不写 `docs/`、不给主分支留残留。** 含:
- **PR 表**:PR / branch / 核心行为 / 各自 ④终审 verdict / 对应 issue。
- **合同地图**:所有跨 PR 合同面(model / API / schema / registry / migration)。
- **文件交叉矩阵**:被多个 PR 改的文件。
- **正确状态模型**:合并后系统该是什么样(你读各 design 文档建立)。
- **合并序**:按 base_commit / 依赖排(被依赖的先合)。
- **冲突解决记录**:边查边填(初始空)。

**只合 `status=ready-to-close`(已 ④终审过)的**;没跑完的先别合。排序拿不准问用户。

## 2. 冲突发现(六维度扫,Coordinator 读设计 + 验代码)

读各 PR 的 design 文档建立方向,**回仓库级架构验**(读 `CONTEXT.md` 类领域模型,需要时用 `improve-codebase-architecture` / `Explore` 验代码、省你 context)。**并行**扫所有 PR,六维度:

| 维度 | 扫什么 | 典型严重度 |
|---|---|---|
| 代码交叉 | 改同一文件/函数 | 低(git 多能合) |
| 功能交叉 | A 的功能依赖 B 改的接口/行为;同一业务流不同环节 | 中 |
| 意图交叉 | 对同一领域概念/对象/状态给了不同设计假设 | 高 |
| 合同交叉 | 同一 model/API/schema 两边各改,provider/consumer 对不上 | 高 |
| 状态交叉 | 共享状态/同一张表语义两边不一致 | 高 |
| **迁移顺序** | 各带 migration,合并后顺序错乱(漏了坏数据,严重度最高) | 高 |
| **隐式依赖** | A 没显式声明却依赖 B 的产出(各自测都过、合起来才炸,最隐蔽) | 最高 |

扫出的冲突填进 merge-brief。

## 3. 三级分类 → 路由(逐个冲突判)

| 分类 | 条件 | 路由 |
|---|---|---|
| **简单** | 代码级(import 序、同文件不同区);≤2 文件;修向明确 | Coordinator 直接修 |
| **复杂·根因明** | 功能/合同冲突;多文件;但谁该 win 清楚 | Coordinator 修,或派 Codex 定向修:先写一份定向修复 mini-plan(冲突点 + 谁该 win + 验收命令)落 `状态平面/`,作 `--plan` 传给 `mmw worker dispatch`(宿主后台派发(见 host-contract) 起,防 10 分钟超时) |
| **系统性·根因不明** | 意图冲突 / 隐式依赖 / 多冲突相互关联 / 要懂整体架构才能判 | **先按「系统性冲突调查」那步查清再修** |

判据:5 分钟看不懂冲突、或 explorer 初判"不确定"、或多冲突彼此关联、或意图冲突/隐式依赖 → 默认系统性。

## 4. 系统性冲突:Coordinator 调查(从"交互"不"错误"视角)

不是某段代码错,是两段各自正确合起来矛盾。五步:

1. **每个 PR 的意图链**:读它的 design/plan/issue(要实现什么)→ 读 diff(实际做了什么)→ 标注 **意图→实现→假设**。重点盯"假设"(A 假设某接口不变/某状态存在,B 恰好改了这前提)。
2. **映射交互点**(不逐行 diff,画交互图):共享文件改点 / 数据流交叉 / 控制流交叉 / 合同交叉 / 时序交叉 / 状态交叉。
3. **分类根因**(每冲突一个):**设计遗漏 / 实现偏离 / 缺失协调 / 隐式耦合 / 合同版本冲突 / 迁移顺序冲突**。
4. **提解决方案**(基于大设计):哪个 PR 方向更合设计意图、只改一边降复杂度、写清修向 + 验收(不写码)、要不要更新设计文档。
5. **评估关联**:多冲突相互影响 → 标关联 + 修复顺序。

**冲突在设计层(两 PR 目标本身矛盾)= `design_conflict` → 不自己定方向**,HITL 拍(回 design 重对齐,或当场问用户决策)。调查结论填进 merge-brief。

## 5. 逐个合(红线,要人批)+ 验

合回主分支是**唯一硬红线**(`guard-redline` 拦)。按合并序逐个:

1. 用户批 → 直接跑 `git merge --no-ff <branch>`(**禁 `--squash`**);`guard-redline` 对合并进主分支弹权限框,用户在框里亲批(无令牌可代批)。
2. git 文本冲突逐 hunk 解:先读双方改动的**原始意图**(commit / PR / issue),尽量两意图都保留、不凭空造新行为,解完跑仓库自动检查(typecheck → test → format)。**拿不准哪边该 win 且属 `design_conflict`(两 PR 目标本身矛盾)→ 不自己合,交用户拍**(回 §3/§4 HITL)。**业务/设计冲突**按「三级分类 → 路由」「系统性冲突调查」定的方向解(让两份设计语义自洽,不是单选一边文本)。
3. **每合一个就验**(不批量合完再查):跑该 PR 相关测试。**冒出意外冲突 → 回「三级分类 → 路由」重新分类**,别硬合。
4. 合进主线后 `mmw task cleanup --slug <slug>` 删该 worktree + 分支 + 临时状态。

## 6. 跨 PR 集成审(全合完跑一次)

```bash
mmw review start --stage merge-impl --source 状态平面/<slug>-merge-brief.md
```

按 host-contract §4 起审:`mmw review start --stage merge-impl` 已生成 brief——Claude 派独立 Codex 双路;Droid 派 `reviewer-final-a` + `reviewer-final-b`(跨模型)。审者读已装 `worktree-review` skill,按 `stage=merge-impl` 走七角度,**不信各 PR 的 ④终审、独立验组合行为**。findings 走 review 留痕(`状态平面/<slug>-merge-impl-review.md`,主仓库不落 docs/)、亲验、disposition。**修复软上限 1 轮**;修完自验 → 过即闭合,不过 → BLOCKED 报用户。

## 7. 清扫 + 返回

- **清扫纪律**:out-of-scope 项确认开独立后续(GitHub issue / 记录)、各队员 open_items 逐条处置、扫合并引入的新 `TODO/FIXME` —— 三选一,不留含糊。
- 全合完主分支跑一遍完整测试确认没合坏。
- **返回**(给用户):verdict(完成 / 待用户决策 / blocked)· 各 PR 合并状态 · 逐冲突(类型/PR/根因/解法/已验)· 集成审结果 · git 状态 · 测试结果 · 遗留项。

## 红线

- 不开新 worktree;主仓库做。
- merge/push 要人批;`--no-ff` 禁 `--squash`。
- 业务/设计冲突(尤其 `design_conflict`)交用户拍,不自己合掉语义分歧。
- 系统性冲突先调查再改,不盲改。
