# Propose · 给出方案(阶段操作指南)

> investigate 与 design 之间的**前置路由步**:把现状综合成 2-3 个方案,HITL 拍一个再进 design,或全否掉头回上游。这一步只**给方案 + 接用户决定**,不写设计文档(那是 design)。

阶段目标:让用户在深入设计**之前**先定大方向。**红线:方案是粗方向不是设计**——每个一句话讲清取舍,别在这写细方案。

## 0. 先看 `where` 的 `do`(引擎分叉,不自判)

任务建档时若用户开口已带明确方向(`task new --direction-given`),`mmw where` 在本阶段报的 `do` 是**降级指令**:跳过下面第 1、2 节,直接读现状报告 → 落 `docs/design/<slug>-direction.md`(选定方向 + 为什么 + **一个最强对照一句**,保留"挑战前提"的最小对照)→ 向用户确认一句 → 按第 3 节 handoff。`do` 没报降级 → 走完整 1→2→3。

## 1. 综合 → 给方案

`mmw where` → `prev_outputs` = investigate 钉的现状报告。读它(内部现状 + 外部方案),综合出 **2-3 个粗方向**,取舍要真张开:

- 至少一个**最小可行**(最少改动 / 最快落地)+ 一个**理想架构**(长期最优),可选一个**另辟蹊径**。
- 三个长得差不多 = 没张开,重想。
- 每个方向一句话:做什么 + 取舍(代价 / 风险 / 放弃了什么)。

## 1.5 可选 · Fable 关键咨询(0–1 次)

亮方案给用户**之前**,若 2–3 个方向在数据归属 / 计费 / 权限 / 不可逆架构上**真有张力**(不是三个近义词),可 consult 一次拿第二意见;否则跳过。

Claude Code:

```
Agent({
  subagent_type: "fable-advisor",
  prompt: "phase=propose; decision_point=用户拍板前选方向; baseline=<现状报告要点>; options_or_draft=<方案表原文>; evidence=<报告路径或 file:line>; ask=只要 stance/why/top_risk/next,不要重写方案表"
})
```

- 用户仍拍板;Fable 只补风险/取舍,不替用户选。
- 本阶段最多 1 次;降级 propose(`direction-given`)默认不 consult。

## 2. Checkpoint(固定格式亮给用户,等拍)

按**固定格式**亮出来(别每次自创),然后停,等用户拍:

```
方案(基于现状报告 <path>):
| # | 方向 | 一句话做什么 | 取舍 |
|---|---|---|---|
| A | <最小可行> | ... | ... |
| B | <理想架构> | ... | ... |
| C | <另辟蹊径,可选> | ... | ... |
```
跟一句:「选哪个?还是都不行、要回上游重查/重想?」

## 3. 两条路(handoff 分叉,复用引擎)

用户拍完,照他的决定 handoff:

| 用户 | 怎么 handoff | 引擎结果 |
|---|---|---|
| **选一个 / 同意某方案** | 把选定方向写进 `docs/design/<slug>-direction.md`(方向 + 为什么选它 + 放弃了什么),`mmw handoff --conclusion pass --produced docs/design/<slug>-direction.md` | advance → design(design 拿这份方向细化、写文档,不再提方案) |
| **全放弃,要回上游重来** | `mmw handoff --conclusion needs-redirection [--to-phase investigate]`(默认回首阶段;`--to-phase` 指定回 investigate 或更上游) | turn-around → 回上游重查/重想(回执指路) |
| **缺关键输入没法给方案** | `mmw handoff --conclusion needs-context` | 停下问用户 |

## 红线

- 方案全否 → 走 `needs-redirection` 回上游,**别硬在烂方向上往 design 走**。
- 选定方向必须落 `docs/design/<slug>-direction.md` 钉进接力单,design 照单读,不靠会话记忆。
