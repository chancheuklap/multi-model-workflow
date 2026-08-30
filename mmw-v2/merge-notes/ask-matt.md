# ask-matt

源目录：`mmw-v2/upstream/skills/engineering/ask-matt/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓库要求这个技能模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用这个技能。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| frontmatter 的 `description` | 「A router over the skills in this repo」改成「A router over the upstream skills in this repo」。本仓另装了七个自研技能（`dispatch`、`verify-ticket`、`exe-release` 等），这份地图一个都没有，原措辞是假承诺。上游把自研技能之外的技能补全 → 收上游措辞，`upstream` 这个限定保留，除非我们真把七个自研技能并进这张地图 |
| 主流程第 3 步末尾「a two-axis review (Standards + Spec) of the diff, before committing」 | 改成「a three-axis review (Standards, Spec, Tests) of the diff」。轴数以 `code-review/SKILL.md` 为准（我们加了 Tests 轴）；`before committing` 删掉，因为 `implement` 的收尾是先提交再 review，而三个子代理读的是 `git diff <base-commit>...HEAD`，未提交的改动不在 HEAD 上。上游改轴数或改先后 → 只在它自己也变成三轴、先提交后 review 时收 |
| Phase boundaries 段的 `/handoff` 一条与 `PHASE-BOUNDARIES.md` 的第 3 问 | `harness` 改成 `host`：同一样东西在 `models.md` 的表头、`AGENTS.md` 与本仓词表里都叫 host（宿主）。上游改这两句 → 收上游措辞，`host` 这个词保留 |
| 主流程第 2 步、技能清单里的 `/prototype` 条 | 跟上我们改造后的 prototype：三类问题（逻辑、UI、实现方式）；去掉 throwaway；处置是留在仓库 `prototypes/` 下当参考（完整路径规范归 prototype 技能，这里不复述），**没有** `prototype/<name>` 一次性分支。上游改措辞可跟，但这三点不能被上游的说法覆盖回去。改这里同时看 `merge-notes/prototype.md` |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |
