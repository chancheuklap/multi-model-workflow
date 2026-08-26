# `resolving-merge-conflicts` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/resolving-merge-conflicts/SKILL.md:1-4 -->

```yaml
---
name: resolving-merge-conflicts
description: "需要解决正在进行的 Git merge 或 rebase 冲突时使用。"
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/resolving-merge-conflicts/SKILL.md:6 -->

1. **查看 merge 或 rebase 的当前状态。** 检查 Git 历史和发生冲突的文件。

<!-- source: vendor/mattpocock-skills/skills/engineering/resolving-merge-conflicts/SKILL.md:8 -->

2. **找出每处冲突的一手来源。** 深入理解每项改动为何产生，以及它原本的意图。阅读提交信息，检查 PR，并检查原始 issue 或 ticket。

<!-- source: vendor/mattpocock-skills/skills/engineering/resolving-merge-conflicts/SKILL.md:10 -->

3. **逐个解决冲突区块。** 尽可能同时保留双方意图。双方意图不兼容时，选择符合当前 merge 已声明目标的一方，并记录取舍。**不得**发明新行为。始终解决冲突；绝不运行 `--abort`。

<!-- source: vendor/mattpocock-skills/skills/engineering/resolving-merge-conflicts/SKILL.md:12 -->

4. 找出项目的**自动检查**并运行。通常依次运行类型检查、测试和格式化。修复 merge 破坏的所有内容。

<!-- source: vendor/mattpocock-skills/skills/engineering/resolving-merge-conflicts/SKILL.md:14 -->

5. **完成 merge 或 rebase。** 暂存全部内容并提交。如果正在 rebase，继续执行 rebase，直到所有提交都完成 rebase。

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/resolving-merge-conflicts/agents/openai.yaml:1-3 -->

```yaml
interface:
  display_name: "Resolving Merge Conflicts"
  short_description: "解决 merge 和 rebase 冲突"
```
