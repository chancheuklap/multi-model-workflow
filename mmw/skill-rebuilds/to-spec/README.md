# To Spec 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW To Spec。当前发布技能仍位于 `mmw/skills/mmw-to-spec/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐段中文翻译。翻译保持只综合不采访、代码库现状、测试 seam、用户确认、tracker 发布和完整 spec 模板，不加入 MMW 的多入口、research、prototype 资产索引或 spec 审查接线。

第二阶段已经形成单文件精简稿。精简稿删除上游安装说明，明确 user story 只覆盖真实场景，并允许没有内容时删除 `Further Notes`；其余上游方法、步骤和完成判据保持不变。

第三阶段已经在 `candidate/` 形成两文件候选。`candidate/SKILL.md` 只增加 MMW 所需的精确输入指针、领域上下文、① spec 审、spec 人工审批关卡、仓库文件与 tracker 发布接线。输入来源不改变 To Spec 的固定流程；缺少决定时只报告准确缺口并停止，不在 To Spec 内建立跨技能回退流程。`candidate/spec-template.md` 保留上游模板原文，并加入已经确认的条件式 MMW section。当前发布技能仍不修改。

## 已确认的接线边界

| 内容 | candidate 的处理 |
| --- | --- |
| 多种上游来源 | 只接收当前对话和精确 context pointer；不按调用方切换流程 |
| Grilling | 接收用户已经确认的共同理解 |
| Prototype | 接收 prototype 资产索引；再按索引读取选中产物和精确证据 |
| Research | 已保存时接收 research 索引和精确文件；未保存时使用当前上下文中的已验证事实、出处和未查清项 |
| Wayfinder | 只接收已关闭 map 的名称及其 URL 或编号；沿 `Decisions so far` 读取相关 decision ticket |
| 输入缺少决定 | 报告准确缺口并停止；不由 To Spec 调用其他技能形成决定 |
| spec 文件 | 使用 `mmw path spec <slug>` 返回的精确路径 |
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
