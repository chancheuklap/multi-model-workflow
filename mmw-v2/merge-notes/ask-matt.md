# ask-matt

源目录：`mmw-v2/upstream/skills/engineering/ask-matt/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉，这个 skill 在本仓是模型可触发的；`agents/openai.yaml` 的 `policy.allow_implicit_invocation` 一起删。上游改这一行 → 仍然删。规则见 [README.md](README.md#disable-model-invocation) |
| frontmatter 的 `description` | 「A router over the skills in this repo」改成「A router over the upstream skills in this repo」。`mmw-v2/skills/` 下的自研 skill（`dispatch`、`verify-ticket`、`exe-release` 等）这张地图一个都没收，不加限定就是假承诺。上游把它自己那些 skill 补全 → 收上游措辞，`upstream` 这个限定保留，除非本仓真把自研 skill 也并进这张地图 |
| 主流程第 3 步末尾「a two-axis review (Standards + Spec) of the diff, before committing」 | 改成「a three-axis review (Standards, Spec, Tests) of the diff」。axis 数以 `code-review/SKILL.md` 为准（本仓是 Standards、Spec、Tests 三个 axis）；`before committing` 删掉，因为 implement 的 closing steps 是先提交再跑 code review，而三个 axis subagent 读的是 `git diff <base-commit>...HEAD`，未提交的改动不在 HEAD 上。上游改 axis 数或改先后 → 只在它自己也是三个 axis、先提交后 code review 时收 |
| Phase boundaries 段的 `/handoff` 一条与 `PHASE-BOUNDARIES.md` 的第 3 问 | `harness` 改成 `host`：同一样东西在 `models.md` 的 `host` 列、`AGENTS.md` 与 `CONTEXT.md` 里都叫 host。上游改这两句 → 收上游措辞，`host` 这个词保留 |
| 主流程第 2 步、技能清单里的 `/prototype` 条 | 跟上本仓的 prototype 技能：三类问题（逻辑、UI、实现方式）；prototype 长期留在仓库 `prototypes/` 下的 leaf directory 里当参考（完整路径规范归 prototype 技能，这里不复述），**没有** `prototype/<name>` 分支。上游改措辞可跟，但这三点不能被上游的说法覆盖回去。改这里同时看 `merge-notes/prototype.md` |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉，跟 `SKILL.md` 的 `disable-model-invocation` 一起。规则见 [README.md](README.md#disable-model-invocation) |
