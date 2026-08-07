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

## 逐段完整性检查

| 上游位置 | 结论 |
| --- | --- |
| `SKILL.md:1-5` | 技能名、description 与 user-invoked 设置均已保留 |
| `SKILL.md:7` | 实施对象仍是用户在 spec 或 ticket 中描述的工作 |
| `SKILL.md:9` | “只要可行”和“预先约定的 seam”两个限制均已保留 |
| `SKILL.md:11` | 类型检查与单个测试文件的定期频率，以及末尾只运行一次完整套件均已保留 |
| `SKILL.md:13-15` | 完成后的 `/code-review` 与提交到当前分支的顺序均已保留 |
| `agents/openai.yaml:1-5` | 展示信息和禁止隐式调用的 policy 均已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部有效内容均有对应翻译 |
| 增写 | 无。没有加入 `worker`、worktree、tracker、MMW 审查编号或测试命令 |
| 曲解 | 无。没有把 `regularly` 改成只在结束时运行，也没有自创固定频率 |
| 术语漂移 | 无。`spec`、`ticket`、`seam` 与技能名始终保留同一写法 |
