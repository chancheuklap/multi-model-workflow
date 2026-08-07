# `handoff` 1.2.2 翻译审查

## 本技能术语应用

共享术语只由 [上游技能翻译共享术语](../translation-terms.md) 定义。下表记录本技能的术语应用和独有术语，不建立第二份定义。

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

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | 技能名已保留 |
| `SKILL.md:3` | 压缩当前对话为供另一个 agent 接手的 handoff 文档已保留 |
| `SKILL.md:4` | 下一次 session 用途的参数提示已翻译 |
| `SKILL.md:5` | 禁止模型隐式调用已保留 |
| `SKILL.md:6` | YAML 结束分隔符已保留 |
| `SKILL.md:8` | 概括对话、供新 agent 继续、操作系统临时目录及排除当前 workspace 均已保留 |
| `SKILL.md:10` | suggested skills 章节及建议调用技能已保留 |
| `SKILL.md:12` | 六类既有产物不得重复并改用路径或 URL 引用均已保留 |
| `SKILL.md:14` | 隐去 API key、密码和个人身份信息已保留 |
| `SKILL.md:16` | 参数作为下一 session 重点并据此调整文档已保留 |
| `agents/openai.yaml:1` | interface 配置键已保留 |
| `agents/openai.yaml:2` | 显示名已保留 |
| `agents/openai.yaml:3` | 对话压缩为 handoff 的短描述已翻译 |
| `agents/openai.yaml:4` | policy 配置键已保留 |
| `agents/openai.yaml:5` | 禁止隐式调用已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部有效内容均有对应翻译 |
| 增写 | 无。没有加入 MMW 阶段边界、worktree 或宿主动作 |
| 曲解 | 无。保存位置仍是操作系统临时目录；没有改成仓库文件 |
| 术语漂移 | 无。`handoff`、`session`、`workspace`、`suggested skills` 和各产物名始终使用同一写法 |
