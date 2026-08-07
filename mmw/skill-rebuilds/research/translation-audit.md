# `research` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| research | `research` | 技能名与 MMW canonical 术语 |
| background agent | 后台 agent | 准确表达后台执行，不擅自改成特定 `subagent` 角色 |
| primary source | 一手来源 | 资料研究中的标准中文译名 |
| first-party API | 第一方 API | 有稳定中文译名，保留 `API` 缩写 |
| secondary write-up | 二手转述 | 与一手来源形成准确对照 |
| finding | 调查结论 | 本文指 research 产出的结论，不使用 MMW 审查中的 `finding` 对象 |
| claim | 断言 | 本文指需要出处支持的陈述，不是 tracker 的 `claim` 动作 |
| spec | `spec` | 上游产物词 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | 技能名已保留 |
| `SKILL.md:3` | 高可信一手来源、Markdown 产物和三类使用场景均已保留 |
| `SKILL.md:4` | YAML 结束分隔符已保留 |
| `SKILL.md:6` | 后台 agent 研究与当前 agent 继续工作的并行关系已保留 |
| `SKILL.md:8` | 后台 agent 的任务引导已翻译 |
| `SKILL.md:10` | 一手来源四类例子、排除二手转述和逐项追溯均已保留 |
| `SKILL.md:11` | 单一 Markdown 文件和逐项引用均已保留 |
| `SKILL.md:12` | 沿用仓库位置约定、无约定时合理保存并说明位置均已保留 |
| `agents/openai.yaml:1` | interface 配置键已保留 |
| `agents/openai.yaml:2` | 显示名已保留 |
| `agents/openai.yaml:3` | 高可信来源 research 的短描述已翻译 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部有效内容均有对应翻译 |
| 增写 | 无。没有加入 MMW 的 `investigator`、报告验证、保存审批或路径合同 |
| 曲解 | 无。没有把“后台执行”改成当前会话停止，也没有把一手来源范围缩成官方文档 |
| 术语漂移 | 无。`research`、一手来源、后台 agent 和调查结论始终使用同一写法 |
