# To Spec 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW To Spec。当前发布技能仍位于 `mmw/skills/mmw-to-spec/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐段中文翻译。翻译保持只综合不采访、代码库现状、测试 seam、用户确认、tracker 发布和完整 spec 模板，不加入 MMW 的多入口、research、prototype 资产索引或 spec 审查接线。

第二阶段已经形成单文件精简稿。精简稿删除上游安装说明，明确 user story 只覆盖真实场景，并允许没有内容时删除 `Further Notes`；其余上游方法、步骤和完成判据保持不变。

第三阶段已经在 `candidate/` 形成两文件候选。`candidate/SKILL.md` 按执行顺序增加 MMW 调用方输入、领域上下文、按需 research、prototype 与 research 资产、① spec 审、spec 人工审批关卡、本地文件与 tracker 发布接线。`candidate/spec-template.md` 保存完整 spec 模板。候选不接收未决设计，不引用已经失效的旧版 evidence 文件，也不把中途处置放进文末“下一步”。当前发布技能仍不修改。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐段中文翻译基线 |
| `translation-audit.md` | 术语选择、逐段完整性与无新增语义检查 |
| `simplified.zh-CN.md` | 只应用用户已经确认的精简，不包含 MMW 路径、资产、审查或 tracker 接线 |
| `candidate/SKILL.md` | 在精简稿外层增加 MMW 输入、执行流程、审查、人工审批和发布接线 |
| `candidate/spec-template.md` | To Spec 候选使用的完整 spec 模板 |

当前发布技能保持不变。
