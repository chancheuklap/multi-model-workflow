# To Spec 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW To Spec。当前发布技能仍位于 `mmw/skills/mmw-to-spec/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐段中文翻译。翻译保持只综合不采访、代码库现状、测试 seam、用户确认、tracker 发布和完整 spec 模板，不加入 MMW 的多入口、research、prototype 资产索引或 spec 审查接线。

第二阶段已经形成单文件精简稿。精简稿删除上游安装说明，明确 user story 只覆盖真实场景，并允许没有内容时删除 `Further Notes`；其余上游方法、步骤和完成判据保持不变。

第三阶段已经在 `candidate/` 形成两文件候选。`candidate/SKILL.md` 保留上游三步流程，并在流程前写清四种真实入口怎样找到已经形成的产物。① spec 审、spec 人工审批关卡、仓库文件与 tracker 发布接线在第三步内部按执行顺序完成。缺少决定时只报告准确缺口并停止，不在 To Spec 内建立跨技能回退流程。`candidate/spec-template.md` 保留上游模板原文，并加入已经确认的条件式 MMW section。当前发布技能仍不修改。

## 已确认的接线边界

| 内容 | candidate 的处理 |
| --- | --- |
| 真实入口 | 只列用户直接调用、`/mmw-grilling`、`/mmw-prototype` 和已关闭的 `/mmw-wayfinder` map |
| 用户直接调用 | 使用当前对话中已经明确形成的决定 |
| `/mmw-grilling` | 使用用户确认的共同理解，以及共同理解引用的结论和精确产物路径 |
| `/mmw-prototype` | 使用交回的 prototype 资产索引，再读取索引点名的选中产物、长期证据和可复用内容 |
| `/mmw-wayfinder` | 使用已关闭 map 的 URL 或编号；沿 `Decisions so far` 读取相关 decision ticket 的 resolution comment 和精确产物链接 |
| research | 不是 To Spec 入口；只读取共同理解或 Wayfinder resolution comment 明确引用的 research 结论和精确文件 |
| 输入缺少决定 | 报告准确缺口并停止；不由 To Spec 调用其他技能形成决定 |
| spec 文件 | 使用 `mmw path spec <任务 slug>` 返回的精确路径 |
| MMW 质量关卡 | 依次完成 ① spec 审和 spec 人工审批关卡 |
| tracker | 用户批准后提交 spec，再创建带 `ready-for-agent` 的 spec issue |
| 下游 | 只移交 `/mmw-to-tickets`；To Spec 不拆 ticket、不写 plan、不开始实现 |
| 模板扩展 | 只保留已经确认的条件式 `Current State`、`Failure Paths`、`Visual Contract`、`Contract Boundaries` 和 `Release Risk` |

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐段中文翻译基线 |
| `translation-audit.md` | 术语选择、逐段完整性与无新增语义检查 |
| `simplified.zh-CN.md` | 只应用用户已经确认的精简，不包含 MMW 路径、资产、审查或 tracker 接线 |
| `candidate/SKILL.md` | 在精简稿外层增加精确输入指针、审查、人工审批和发布接线 |
| `candidate/spec-template.md` | 保留上游核心 section，并加入已确认的条件式 MMW section |

当前发布技能保持不变。
