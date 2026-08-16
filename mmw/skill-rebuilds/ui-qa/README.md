# UI QA 重建区

MMW 原创技能，没有 Matt 上游。当前发布技能仍位于 `mmw/skills-src/mmw-ui-qa/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文接线（2026-08-16）

候选是 **6 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)、[`candidate/CRITERIA.md`](candidate/CRITERIA.md)、[`candidate/SEMANTIC.md`](candidate/SEMANTIC.md)、[`candidate/SETUP.md`](candidate/SETUP.md)、[`candidate/VERDICTS.md`](candidate/VERDICTS.md)、[`candidate/WINDOWS.md`](candidate/WINDOWS.md)，按将来位于 `mmw/skills-src/mmw-ui-qa/` 书写。现役技能源未改。

已叠进候选的接线：

- 两类九种检查项。A 类产出 violation，当场改并合成一个提交。B 类产出 finding，等用户裁决。
- 范围三档：默认 `this-change`；标签 `this-task`；标签 `full`。不再用 `本任务` / `全量`。
- 落点全部 `mmw artifact path`。设计系统路径走接线文件字段，不走产物落点。
- 语义层一条路径派一个 `designer`：`[[mmw-launch:designer:none]]`。
- 同轮改了 review 候选：⑤ 含界面时先跑 `/mmw-ui-qa` tagged `this-task`。

未叠：

- 第十种检查项。
- 把 Windows 侧做成第三条平台流程。
- 把设计系统改成可写。

leaf 草稿见 [`candidate/leaf-terms.md`](candidate/leaf-terms.md)。本轮不派冷读 subagent。
