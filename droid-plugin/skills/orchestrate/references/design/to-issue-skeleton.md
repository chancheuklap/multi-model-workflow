# to-issue 阶段 · 垂直切片立 issue 骨架(读本文全文)

> `to-issue` 是用户 `/approve-design` 过门**之后**、plan **之前**的独立阶段:把已确认的设计垂直切片成可独立认领的 issue 骨架,钉进接力单交给 plan。主线程做。**只立骨架,实施细节由 plan-writer 按计划 schema 丰富**——这里不写 Task Pack。
>
> `prev_outputs` = design 钉的设计文档(已由用户确认、盖了指纹)。读它来切片;不重提方案、不改设计(要改设计 → `mmw handoff --conclusion needs-redirection --to-phase design`,改完请用户重新 `/approve-design`)。

## 怎么拆:委托外部 `to-tickets` skill(方法论单源,不在此复制)

切片方法论本体在外部 `to-tickets` skill —— tracer-bullet / vertical-slice(每个 issue 切穿所有集成层、端到端可独立验证、单个适配一个 fresh context window)。用它来拆;**粒度和依赖(blocking edges)自己定,不再向用户确认循环**(已过 /approve-design,流水线态自主跑):切片清单落盘、编号列表进汇报和进度板亮给用户,他有异议随时口头调整或 /rescope;质量闸 = ②计划审兜底。

**宽重构例外**:改列名 / 改共享类型这种爆炸半径大、单次编辑会破上千调用点的机械改动,不套 vertical slice,按 `to-tickets` 的 **expand–contract** 拆:先 expand(新旧并存不破)→ 分批 migrate(按爆炸半径分包,每批一个 issue、blocked by expand)→ contract(删旧,blocked by 全部 migrate 批)。

plugin 在 `to-tickets` 结果上做两件**适配**:

**适配 1 · 产物落我们的目录、一个大 issue 一个文件**:每个大 issue 落 `docs/issues/<slug>/<issue>.md`(slug 与设计文档对齐,prepare 已 scaffold `docs/issues/<slug>/`)。**override `to-tickets` 的 Step5 发布**——既不合并成单个 `tickets.md`、也不发线上 tracker,写成本地一 issue 一文件(下游 plan 死绑一文件一大 issue)。

**适配 2 · issue 文件模板**(= `to-tickets` 单条 issue 模板 + plugin 扩展两节,缺一下游读不到):

```markdown
## What to build
<这条 vertical slice 的端到端行为,不写逐层实现、不写文件路径>

## Acceptance criteria
- [ ] ...

## Blocked by
<依赖的其它 issue,或 "None - 可立即开始">

## Design context refs ← plugin 扩展,至少一条
<指向设计文档对应章节,下游零上下文靠它回设计找依据>

## Small issues ← plugin 扩展
<!-- PENDING --> ← 小 issue 由 plan-writer 按 worktree-plan skill 拆分补全,这里不填
```

每个大 issue 头部标 **AFK**(可无人值守落地)或 **HITL**(要人盯)。**优先多个 thin slice,而非少数 thick slice。**

## 收尾:钉进接力单 → handoff

本阶段只产 **issue 骨架**(设计文档已由 design 阶段钉过,plan 的 `prev_outputs` 按 `reads:[design,to-issue]` 一单读全):

```bash
mmw handoff --conclusion pass --produced docs/issues/<slug>/
```

`mmw where` 的 `then` 已给好命令模板,照抄即可。→ advance 到 plan。

切片中发现设计本身缺口 / 方向错 → 别硬切,回上游:`mmw handoff --conclusion needs-redirection --to-phase design`(`needs-repair` 是原地返工、回不到 design)。
