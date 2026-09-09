# resolving-merge-conflicts

源目录：`mmw-v2/upstream/skills/engineering/resolving-merge-conflicts/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `description` | 值外面那对引号去掉。这个值里没有「冒号加空格」，`yaml.safe_load` 验过去掉引号后解析结果逐字不变，而不带引号是本仓 `description` 的常态。上游改这一行的内容 → 收上游，不带引号这一点保留，除非新值里含冒号加空格——那种值必须带引号，否则 YAML 把它当成一个 mapping，整份 frontmatter 解析失败 |
