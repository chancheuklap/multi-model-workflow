# 拆 issue 立骨架(设计通过、handoff 前读本文全文)

> 设计自检过、用户确认方向后的收尾步:把设计拆成可独立认领的 issue 骨架,钉进接力单交给 plan。**只立骨架,内容由 plan 阶段(`write-plan-doc`)按计划 schema 丰富**——这里不写实施细节、不写 Task Pack。

## 怎么拆

用 `to-issues` skill 把设计按 vertical-slice 拆成可独立认领的 issue(切片方法论在 to-issues,不复述)。每个大 issue:

- **落点**:`docs/issues/<YYYY-MM-DD>-<slug>/`,slug 与设计文档对齐(prepare 已 scaffold `docs/issues/<slug>/`)。
- **标 AFK / HITL**:这个 issue 落地时能无人值守还是要人盯。
- **`## Design context refs`**:至少一条,指向设计文档对应章节(下游零上下文靠它回设计找依据)。
- **`## Small issues` 留 `<!-- PENDING -->`**:小 issue 由 `write-plan-doc` 在 plan 阶段补全,这里不填。

## 钉进接力单(handoff 带两样)

design 阶段产**两样**:设计文档 + issue 骨架。handoff 两个都 `--produced`(`mmw where` 的 `then` 已给好钉全的命令模板),plan 的 `prev_outputs` 才能一单读全、不自己找:

```bash
mmw handoff --conclusion pass --produced docs/design/<slug>.md --produced docs/issues/<slug>/
```

> 设计是多文件目录(带 mockup / research)时,第一个 `--produced` 钉目录 `docs/design/<slug>/` 而非单文件。
