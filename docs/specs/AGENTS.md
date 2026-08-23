# docs/specs

每次交付的 spec。不放 plan。

- 文件固定是 `docs/specs/<名字段>/spec.md`，名字不重复进文件名。
- frontmatter 字段：`slug`、`summary`、`date`、`branch`、`spec_issue`、`artifact_refs`。
- 同一名字段第二次做时原地覆盖，不在文件里写修订记录；历史看 `git log --follow`。
