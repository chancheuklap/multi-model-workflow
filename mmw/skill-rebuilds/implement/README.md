# Implement 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW 对 `implement` 的承接。当前发布技能仍位于 `mmw/skills/mmw-implement/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐段中文翻译。翻译保持上游 invocation、实施顺序、测试频率、审查和提交要求，不加入 MMW 的 `worker`、worktree、tracker 或六道审接线。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐段中文翻译基线 |
| `translation-audit.md` | 术语选择、逐段完整性与无新增语义检查 |

后续只有在用户确认精简方案后，才增加 `simplified.zh-CN.md`；只有在用户确认接线方案后，才增加 `candidate/`。
