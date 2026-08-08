# Resolving Merge Conflicts 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW 对 `resolving-merge-conflicts` 的承接。当前发布技能仍位于 `mmw/skills/mmw-integrate/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐段中文翻译。翻译原样保留上游查看状态、追溯双方意图、逐块解决、自动检查和完成 Git 操作的顺序，也保留“始终解决，绝不 `--abort`”的上游原文；本阶段不加入 MMW 的安全停止边界。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐段中文翻译基线 |
| `translation-audit.md` | 术语选择、逐段完整性与无新增语义检查 |

后续只有在用户确认精简方案后，才增加 `simplified.zh-CN.md`；只有在用户确认接线方案后，才增加 `candidate/`。

## 2026-08 复审确认

上游「Always resolve; never `--abort`」是绝对规则。候选 `mmw-integrate` 的 `merging.md` 与 `rebasing.md` 有意改为条件规则：只有用户取消本次集成，或现有目标无法决定冲突取舍时才停止，并以「不要用停止代替冲突判断」压住滥用。理由：MMW 是多分支自动集成场景，双方意图真不兼容时强行 resolve 等于替用户做设计决定。用户已确认这是刻意的产品决策。
