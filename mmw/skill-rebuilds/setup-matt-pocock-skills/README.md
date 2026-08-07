# Setup Matt Pocock Skills 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Setup。当前 MMW 没有把该上游 setup 作为活跃技能发布；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md`、五份配置模板和 `agents/openai.yaml` 的逐行中文翻译。翻译保留 tracker 选择、triage label、领域文档布局、用户确认、Agent skills block 和三种 tracker 的 Wayfinding 操作，不加入 MMW 配置或 CLI 接线。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |

后续只有在用户确认精简方案后，才增加 `simplified.zh-CN.md`；只有在用户确认接线方案后，才增加 `candidate/`。
