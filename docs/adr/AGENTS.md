# docs/adr

决策记录。不记录 spec 或 plan。

- 编号来自 `mmw domain adr-next`（在冻结的 `mmw/cli/` 里）；多个会话可能并行写时先命名 `draft-<ticket>-<slug>.md`，合回后再取号。
- 被改写的 ADR 不重写：新 ADR 的 `amends:` 列旧编号，旧文件顶部加一行引用块指向现行读法，旧正文原样保留。`amends` 是两份 ADR 之间唯一的机器可读关联。
- 每份必须有 `---` frontmatter（`date`、`amends`）和一个 H1；少一份，整个索引生成都中止。
- 上游 `domain-modeling` 技能教的 ADR 格式没有 frontmatter，不要照它写。
