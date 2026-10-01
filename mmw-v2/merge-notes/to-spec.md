# to-spec

源目录：`mmw-v2/upstream/skills/engineering/to-spec/`

这个目录里 squash 原文有的文件与 `5b1a4c51` 逐字节相同，文档页 `mmw-v2/upstream/docs/engineering/to-spec.md` 也是原文。装的是分叉 `mmw-v2/skills/to-spec/`；分叉与拉 upstream 的规则见 [README](README.md) `## 上游目录只允许两类改动`。

## 本仓的文字在哪里

| 本仓的文字 | 现在在哪里 |
| --- | --- |
| 开头立场段与第 1–4 步、spec 模板各项、`Done when` | `mmw-v2/skills/to-spec/SKILL.md` |
| 修订已发布的 spec | `mmw-v2/skills/to-spec/references/revising-a-spec.md` |
| `references/several-specs.md` 的循环 | playbook **Write a spec and tickets** 的 `#### Several specs from one reference`（由 **Split into several specs when it is several** 进入） |
| `## Next` | 同一 playbook 的步骤顺序 |
| 第 2 步的两条退回路线 | playbook **Design a UI** |
| frontmatter 与 `agents/openai.yaml` 的开关 | 分叉不带 `agents/openai.yaml`，frontmatter 只有 `name` 与 `description` |
| 文档页 native parent 的两处 | 删去，`verify-ticket` 的 `--publish --map` 做并读回核对 |

各段当初为什么这样写，记在这份说明在 `1dc33ec5` 的版本里（`git show 1dc33ec5:mmw-v2/merge-notes/to-spec.md`）。
