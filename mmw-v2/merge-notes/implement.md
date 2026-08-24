# implement

源目录：`mmw-v2/upstream/skills/engineering/implement/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 第一句之后的「开写之前先读」那一段 | 我们加的：票读全 → 顺 Parent 读 spec 全文 → 读 spec 的 `## Sources` 链的 prototype 与 research 到结论 → 读 ADR 与领域词汇表 → 用一句话说出这张票在哪个 seam 上测，然后动手。`## Sources` 这个名字是我们在 `to-spec` 模板里加的，改那边就同步改这里。上游自己写了开写前的读取步骤 → 收上游，只把它没有的那几项（Sources、说出 seam）并进去，不并列两段。其余段落我们没改，全取上游 |
| 末尾的「## Finishing a ticket」九步（替换上游末两句「Once done, use /code-review」「Commit your work to the current branch」） | 我们加的，spec `docs/specs/landing-closeout/landing-closeout.md`「implement 的完成步骤」：开工写 `.mmw-ticket-state.json`（与 discipline-hooks 共享的契约：`ticket`、`branch`、`gates[]`，每 gate `text/kind/check/expect/manual/checked/evidence`）→ 实现 → `self-check` 技能 → 逐条跑关卡、勾选附 `EVIDENCE:`、同步状态文件 → commit 引用票号 → /code-review → 推 `ticket/<票号>-<slug>` → 开 PR → 关票。上游的 review 句原本在 commit 之前，而 code-review 只看已提交的 diff，所以挪到 commit 之后。上游改末尾收尾方式 → 仍以这九步为准；上游若自己加了关票或开 PR → 并进对应步，不并列两段。步骤 4 的双条件判定与「勾选不算数、证据才算数」承接 ADR 0022，不可弱化 |
| frontmatter 的 `disable-model-invocation` 与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation` | 我们删的：上游两处都设了只许人触发，我们要模型能自己派 implement，所以两处一起删。上游若再带回来 → 仍然删 |
