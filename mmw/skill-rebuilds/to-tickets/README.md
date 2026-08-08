# To Tickets 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW To Tickets。当前发布技能仍位于 `mmw/skills-src/mmw-to-tickets/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐行中文翻译。翻译保持 tracer bullet 垂直切片、blocking edge、wide refactor 的 expand–contract 例外、用户批准、两类 tracker 发布方式和完整模板，不加入 MMW 的 spec issue、CLI 或人工审批关卡接线。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |

接线候选已存在于 [candidate/](../candidate/skills/mmw-to-tickets/)：它以现役已接线版本为基础并入整棵候选树，翻译基线与审计仍是保真依据。本目录未单独保存精简稿。
