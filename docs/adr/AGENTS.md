# docs/adr

决策记录。不记录 spec 或 plan。

## 关键约定

- 编号 = 现有最大号 + 1（ADR 0017，不再调用冻结区命令）；多个会话可能并行写时先命名 `draft-<ticket>-<slug>.md`，合回后再取号。
- 被改写的 ADR 不重写：新 ADR 的 `amends:` 列旧编号，旧文件顶部加一行引用块指向现行读法，旧正文原样保留。`amends` 是两份 ADR 之间唯一的机器可读关联。
- 每份必须有 `---` frontmatter（`date`、`amends`）和一个 H1。

## 陷阱

- 少一份合规的 frontmatter 或 H1，整个索引生成都中止。
- 上游 `domain-modeling` 技能教的 ADR 格式没有 frontmatter，照它写会打破索引。
