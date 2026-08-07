# `implement` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| spec、ticket | `spec`、`ticket` | 上游产物词，也是 MMW canonical 术语 |
| seam | `seam` | Codebase Design 的 leading word |
| `/tdd`、`/code-review` | 保留原文 | 技能调用字面量 |
| typechecking | 类型检查 | 有稳定中文译名 |
| single test file | 单个测试文件 | 保留单文件粒度，不扩大成相关测试集 |
| full test suite | 完整测试套件 | 保留全量范围 |
| regularly | 定期 | 保留与实现过程交错的频率，不自创固定次数 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | 技能名已保留 |
| `SKILL.md:3` | 根据 spec 或一组 ticket 实施工作已保留 |
| `SKILL.md:4` | 禁止模型隐式调用已保留 |
| `SKILL.md:5` | YAML 结束分隔符已保留 |
| `SKILL.md:7` | 实施用户在 spec 或 ticket 中描述的工作已保留 |
| `SKILL.md:9` | 可行时在预先约定 seam 使用 TDD 已保留 |
| `SKILL.md:11` | 定期类型检查、定期单文件测试和最后一次全套测试均已保留 |
| `SKILL.md:13` | 完成后调用 code-review 已保留 |
| `SKILL.md:15` | 提交到当前分支已保留 |
| `agents/openai.yaml:1` | interface 配置键已保留 |
| `agents/openai.yaml:2` | 显示名已保留 |
| `agents/openai.yaml:3` | 从 spec 或 ticket 构建工作的短描述已翻译 |
| `agents/openai.yaml:4` | policy 配置键已保留 |
| `agents/openai.yaml:5` | 禁止隐式调用已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部有效内容均有对应翻译 |
| 增写 | 无。没有加入 `worker`、worktree、tracker、MMW 审查编号或测试命令 |
| 曲解 | 无。没有把 `regularly` 改成只在结束时运行，也没有自创固定频率 |
| 术语漂移 | 无。`spec`、`ticket`、`seam` 与技能名始终保留同一写法 |
