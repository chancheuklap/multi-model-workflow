# `handoff` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| handoff | `handoff` | 技能名和文档类型 |
| agent | `agent` | 上游角色词 |
| session | `session` | agent 工作单位 |
| workspace | `workspace` | 宿主工作区术语 |
| suggested skills | `suggested skills` | 要写入文档的章节标题字面值 |
| artifact | 产物 | MMW canonical 术语 |
| spec、plan、ADR、issue、commit、diff | 保留原文 | 产物和版本控制对象字面词 |
| redact | 隐去 | 表达保留文档、去除敏感内容的动作，不误写成删除文件 |
| personally identifiable information | 个人身份信息 | 标准中文译名 |

## 逐段完整性检查

| 上游位置 | 结论 |
| --- | --- |
| `SKILL.md:1-6` | 技能名、description、参数提示和 user-invoked 设置均已保留 |
| `SKILL.md:8` | 概括当前对话、供新 agent 继续、保存到操作系统临时目录和不写当前 workspace 均已保留 |
| `SKILL.md:10` | `suggested skills` 章节及其推荐调用用途均已保留 |
| `SKILL.md:12` | 六类既有产物不得重复，以及改用路径或 URL 引用均已保留 |
| `SKILL.md:14` | API key、密码和个人身份信息三类敏感信息均已保留 |
| `SKILL.md:16` | 参数用于说明下一次 session 重点并据此定制文档均已保留 |
| `agents/openai.yaml:1-5` | 展示信息和禁止隐式调用的 policy 均已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部有效内容均有对应翻译 |
| 增写 | 无。没有加入 MMW 阶段边界、worktree 或宿主动作 |
| 曲解 | 无。保存位置仍是操作系统临时目录；没有改成仓库文件 |
| 术语漂移 | 无。`handoff`、`session`、`workspace`、`suggested skills` 和各产物名始终使用同一写法 |
