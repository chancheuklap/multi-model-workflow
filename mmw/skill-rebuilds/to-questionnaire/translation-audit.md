# `to-questionnaire` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| questionnaire | 问卷 | 有稳定中文译名 |
| discovery questionnaire | `discovery questionnaire` | 没有足够稳定且不改变用途的中文专名，保留上游原词 |
| recipient | 收件人 | 准确指问卷接收和回答者 |
| send | 发送安排 | 本文指收件人、交付方式和期望结果，不是发送动作本身 |
| subject | 主题本身 | 与发送安排形成对照 |
| gap | 缺口 | 指收件人知识与用户需求之间的差距 |
| async | 异步 | 有稳定中文译名 |
| exchange | 一次问答 | 保留一轮内完成询问和回答的单位 |
| slug | `slug` | 文件名字面规则中的技术词 |
| answer stub | 回答占位 | 模板中的空白回答位置 |
| throwaway answer | 敷衍回答 | 指没有提供有效信息的随手答案 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | 技能名已保留 |
| `SKILL.md:3` | 无法完整回答的决定和交给其他人填写问卷已保留 |
| `SKILL.md:4` | 禁止模型隐式调用已保留 |
| `SKILL.md:5` | YAML 结束分隔符已保留 |
| `SKILL.md:7` | Markdown 问卷、单人异步或会议共同填写、知识持有者和提取知识均已保留 |
| `SKILL.md:9` | 只追问发送安排、收件人、所需结果和知识缺口均已保留 |
| `SKILL.md:11` | 收件人角色、专长、关系、语气、上下文量和完成判据均已保留 |
| `SKILL.md:13` | 具体决定或事实、最终能做或决定什么及完成判据均已保留 |
| `SKILL.md:15` | 根据缺口拟题、文档结构、文件名、当前目录、报告路径和逐项覆盖均已保留 |
| `SKILL.md:17` | 文档结构标题已翻译 |
| `SKILL.md:19` | discovery questionnaire、重要性排序、单次机会、主题分组和使用模板均已保留 |
| `SKILL.md:21` | questionnaire-template 起始标签已保留 |
| `SKILL.md:23` | 问卷标题占位已翻译 |
| `SKILL.md:25` | 目的和依赖答案的决定已翻译 |
| `SKILL.md:27` | 来自、发给和答案用途三个字段已翻译 |
| `SKILL.md:29` | 上下文标题已翻译 |
| `SKILL.md:31` | 一个段落、帮助收件人理解、足够回答且不写满一页均已保留 |
| `SKILL.md:33` | 回答方式标题已翻译 |
| `SKILL.md:35` | 截止时间、粗略投入、部分答案、不知道和标记不确定内容均已保留 |
| `SKILL.md:37` | 主题标题占位已翻译 |
| `SKILL.md:39` | 每主题一节、重要优先、单一问题、回答占位和条件式理由说明均已保留 |
| `SKILL.md:41` | question-example 起始标签已保留 |
| `SKILL.md:42` | 上线负载示例问题已翻译 |
| `SKILL.md:44` | 突发流量资源配置与延期取舍的理由已翻译 |
| `SKILL.md:46` | 引用块回答占位已保留 |
| `SKILL.md:47` | question-example 结束标签已保留 |
| `SKILL.md:49` | 还有其他内容的兜底标题已翻译 |
| `SKILL.md:51` | 未问但应知道内容的收尾问题已翻译 |
| `SKILL.md:53` | questionnaire-template 结束标签已保留 |
| `agents/openai.yaml:1` | interface 配置键已保留 |
| `agents/openai.yaml:2` | 显示名已保留 |
| `agents/openai.yaml:3` | 预先整理问题供他人回答的短描述已翻译 |
| `agents/openai.yaml:4` | policy 配置键已保留 |
| `agents/openai.yaml:5` | 禁止隐式调用已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部有效内容均有对应翻译 |
| 增写 | 无。没有加入 MMW 的 scratch、Grilling 回流、清理或保存审批 |
| 曲解 | 无。没有让 agent 采访用户不掌握的主题事实；三步完成判据保持原范围 |
| 术语漂移 | 无。问卷、收件人、发送安排、缺口、`discovery questionnaire` 和回答占位始终使用同一写法 |
