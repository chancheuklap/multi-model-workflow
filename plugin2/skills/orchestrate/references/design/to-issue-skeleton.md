# to-issue 阶段 · 垂直切片立 issue 骨架(读本文全文)

> `to-issue` 是 ①设计审**之后**、plan **之前**的独立阶段:把已评审的设计垂直切片成可独立认领的 issue 骨架,钉进接力单交给 plan。主线程做。**只立骨架,内容由 plan 阶段(`write-plan-doc` / plan-writer)按计划 schema 丰富**——这里不写实施细节、不写 Task Pack。
>
> `prev_outputs` = design 钉的设计文档(已过 ①设计审)。读它来切片;不重提方案、不改设计(要改设计 → `mmw handoff --conclusion needs-redirection` 回 design)。

## 怎么拆

用 `to-issues` skill 把设计按 vertical-slice 拆成可独立认领的 issue(切片方法论在 to-issues,不复述)。每个大 issue:

- **落点**:`docs/issues/<YYYY-MM-DD>-<slug>/`,slug 与设计文档对齐(prepare 已 scaffold `docs/issues/<slug>/`)。
- **标 AFK / HITL**:这个 issue 落地时能无人值守还是要人盯。
- **`## Design context refs`**:至少一条,指向设计文档对应章节(下游零上下文靠它回设计找依据)。
- **`## Small issues` 留 `<!-- PENDING -->`**:小 issue 由 `write-plan-doc` 在 plan 阶段补全,这里不填。

## 收尾:钉进接力单 → handoff

本阶段只产 **issue 骨架**(设计文档已由 design 阶段钉过,plan 的 `prev_outputs` 会按 `reads:[design,to-issue]` 一单读全):

```bash
mmw handoff --conclusion pass --produced docs/issues/<slug>/
```

`mmw where` 的 `then` 已给好这条命令模板,照抄即可。→ advance 到 plan(无审闸:切片质量在 ②计划审随计划一起兜)。

切片中发现设计本身缺口 / 方向错 → 别在这硬切,回上游 design 改:`mmw handoff --conclusion needs-redirection --to-phase design`(`needs-repair` 是原地返工、回不到 design)。
