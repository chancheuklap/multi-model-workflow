# `wait-what` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| wait-what | `wait-what` | 技能名 |
| re-pitch | 换一种方式重新说明 | 表达重新组织同一内容，不误写成补做工作 |
| ASD-STE100 Simplified Technical English | ASD-STE100 简化技术英语（Simplified Technical English） | 使用标准中文名称，并保留英文全称 |
| ubiquitous language | 通用语言 | 领域驱动设计的标准中文译名 |
| `CONTEXT.md` | 保留原文 | 文件名字面量 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | 技能名已保留 |
| `SKILL.md:3` | 停止、上一条未传达清楚和重新表述均已保留 |
| `SKILL.md:4` | 禁止模型隐式调用已保留 |
| `SKILL.md:5` | YAML 结束分隔符已保留 |
| `SKILL.md:7` | 不理解当前进度、补上下文、简化技术英语和 CONTEXT 通用语言均已保留 |
| `agents/openai.yaml:1` | interface 配置键已保留 |
| `agents/openai.yaml:2` | 显示名已保留 |
| `agents/openai.yaml:3` | 补缺少上下文并更简单重述的短描述已翻译 |
| `agents/openai.yaml:4` | policy 配置键已保留 |
| `agents/openai.yaml:5` | 禁止隐式调用已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部有效内容均有对应翻译 |
| 增写 | 无。没有加入可视化、HTML、文件保存或 Sites 行为 |
| 曲解 | 无。`re-pitch` 仍是重新组织上一条消息，没有变成开始新的解释任务 |
| 术语漂移 | 无。简化技术英语、通用语言和 `CONTEXT.md` 始终使用同一写法 |
