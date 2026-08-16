# To Questionnaire 重建区

这个目录用于从 Matt Pocock Skills 重新建立 MMW To Questionnaire。当前发布技能位于 `mmw/skills-src/mmw-to-questionnaire/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（vendor `1.2.3`：一份 `SKILL.md`），只叠必要接线。候选按将来位于 `mmw/skills-src/mmw-to-questionnaire/SKILL.md` 书写。现役技能源目录已改为 `mmw-to-questionnaire`。技能名是 `mmw-to-questionnaire`。

上游是 user-invoked。`/mmw-grilling` 要调得着它，所以候选去掉 `disable-model-invocation`，保持 model-invoked。问卷方法和模板原文留下。

已叠进候选的接线：

- 落点从「当前目录」换成 `mmw artifact path scratch --sub questionnaire/<slug>.md`。
- `/mmw-grilling` 调进来时交回路径，答案回到设计树。

未叠：

- 第 4 步吸收答案再删 scratch 的长手续。
- `agents/openai.yaml`。

本轮不派冷读 subagent。不改 leaf。

## 先前阶段（中文重建）

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐段中文翻译。旧中文接线候选在 `../candidate/skills/to-questionnaire/`，不是本轮英文底稿。

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐段中文翻译基线 |
| `translation-audit.md` | 术语选择、逐段完整性与无新增语义检查 |
| [candidate/](candidate/) | 本轮英文接线候选 |
