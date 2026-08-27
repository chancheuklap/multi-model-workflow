# implement

源目录：`mmw-v2/upstream/skills/engineering/implement/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 第一句之后的开工核对一段 | 我们加的：先核对票的标题与 What to build 是同一片、Blocked by 全部已关闭，任一不成立就停下报告。理由：发布错位过的票和还被阻塞的票都不能开工。上游加了同类前置检查 → 收上游，这两条并进去 |
| 「开写之前先读」那一段 | 我们加的：票读全 → 票的 `## Read first` 逐份读到结论（research 的末节、prototype 选定的 artifact、ADR 的 Decision）→ 顺 Parent 读 spec 全文，票指名的小节、Testing Decisions、Out of Scope 是必须能复述的部分 → 有领域词汇表才读。没有 `Read first` 的旧票退回读 spec `## Sources` 全部。`## Read first`、`## Seam` 是我们在 `to-tickets` 模板里加的节名，`## Sources` 是 `to-spec` 里加的，改那边就同步改这里。上游自己写了开写前的读取步骤 → 收上游，只把它没有的那几项并进去，不并列两段 |
| 说出 seam 那一段 | 我们加的：seam 抄票的 `## Seam`；票没有这节时从 spec Testing Decisions 推出并先评论到票上再动手。上游有同类要求 → 收上游，「先写回票」这条保留 |
| 结尾「Commit your work」之后的三步 | 我们加的：评论验收证据并打勾 → push 分支开 PR → 关票。理由：不关票下游永远解不开阻塞（这是自动跑完全链的唯一硬阻塞）。远端合并与发布不在这里做，仍要用户授权。上游加了收尾步骤 → 收上游，关票这一步必须保留 |
| frontmatter 的 `disable-model-invocation` 与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation` | 我们删的：上游两处都设了只许人触发，我们要模型能自己派 implement，所以两处一起删。上游若再带回来 → 仍然删 |
