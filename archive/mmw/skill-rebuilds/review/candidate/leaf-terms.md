# review.md 本轮要改的术语

未改现役 `docs/context/review.md`。发布 `/mmw-review` 时用 `/mmw-domain-modeling` 换上。

**六道审**：
共同理解审、spec 审、plan 审和 final 终审。编号为 ⓪①②⑤。逐份验收和合同门已取消，不要发起。② 在本轮 plan 写完后发起，不等合同回填。多分支集成结果也进入 final 终审；集成调查属于 `/mmw-integrate`。
_Avoid_: 五道审、人工审批关卡、把③或④当成关卡、合同回填

**视角（任务名）**：
一名审查者在独立上下文中检查的一个角度。task 的目标栏第一句使用下面的英文名，与 reviewer 角度文件一一对应：`Shared understanding`、`Spec content`、`Spec alignment`、`Plan coverage`、`Plan compliance`、`Final trace`、`Final fresh`、`Final standards`。
_Avoid_: 五道审、自定义任务名、视角摘要、中文任务名

**共同理解审**：
审 shared-understanding record 的第一道审，视角名是 `Shared understanding`。由用户在 `/mmw-grilling` 里要求才发起，不是关卡。
_Avoid_: spec 审、走查

**Reviewed HEAD**（现用名 `被审 HEAD`）：
某轮审查实际检查的被审分支 HEAD。它用于发现审查期间的内容漂移，不表示该轮已经通过。
_Avoid_: 固定点、Final commit、当前 HEAD

**Final commit**（现用名 `终审提交`）：
一次 final 终审完成时的分支 HEAD。没有采信项时等于 Reviewed HEAD；有采信项时等于全部采信项修复后的 Repair commit。
_Avoid_: 固定点、Reviewed HEAD、当前 HEAD、分支名

**Repair commit**（现用名 `修复提交`）：
一次审查的全部采信项修复完成时的分支 HEAD。修复不派审查者。
_Avoid_: Reviewed HEAD
