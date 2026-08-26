# docs/specs

每次交付的 spec。不放 plan。

## 关键约定

- 文件固定是 `docs/specs/<名字段>/<名字段>.md`（文件名即名字段，编辑器标签与搜索直接可辨；ADR 0017）；附件放同目录。
- frontmatter 字段：`slug`、`summary`、`date`、`branch`、`spec_issue`、`artifact_refs`。
- 同一名字段第二次做时原地覆盖，不在文件里写修订记录；历史看 `git log --follow`。
