# ask-matt

源目录：`mmw-v2/upstream/skills/engineering/ask-matt/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉，这个 skill 在本仓是模型可触发的；`agents/openai.yaml` 的 `policy.allow_implicit_invocation` 一起删。上游改这一行 → 仍然删。规则见 [README.md](README.md#disable-model-invocation) |
| frontmatter 的 `description` | 「A router over the skills in this repo」改成「A router over the upstream skills in this repo and the `design-pages` and `write-screen-contract` skills beside them」。限定 `upstream`，理由是 `mmw-v2/skills/` 下的自研 skill 这张地图大多不收、不加限定就是假承诺；主流程第 2 步收了 `design-pages` 与 `write-screen-contract` 两个自研 skill（见下一行），所以按名字把这两个列进来。`dispatch` 只在第 3 步作为已发布 ticket 的下一步被点名，它自己的各种用法与 `verify-ticket`、`exe-release` 都不收，因此也不能写成「全部 skill」。末尾那句「什么时候用我」（`Use when you know what you want to do but not which skill does it, or when you are choosing what to do at a phase boundary.`）是本仓补的：host 启动时只扫这一行，一份只说「我是什么」的技能在列表里挑不出该不该用它。上游改这一行 → 收上游对前半句的措辞，这个限定与末句都保留 |
| 主流程第 3 步：Yes 一支的后半句、No 一支、其后「Either way」那一段 | 我们改的，三处。(1) Yes 一支删掉上游的本地 tracker 那句（`.scratch/<feature>/issues/` 一票一文件、按 blocker 手工推进），blocking edge 直接写成 tracker 上的原生 blocking link，理由同 [to-tickets.md](to-tickets.md) 第 7 步 Local files 分支那一行：本仓的 ticket 要有 issue 号才走得动；上游「kick off `/implement` per ticket, `/clear`ing context」改成「`dispatch` 技能跑已发布的 ticket：一个 night，或 night 之外的一张」。理由：`implement` 的第一步是 `--preflight` 认领，自己捡的票还要在 `issue-<n>` worktree 里 `adopt`，只有 `dispatch` 起的 worker 进得去。(2) No 一支上游是「`/implement` right here, in the same context window」，改成在本会话用 `tdd` 技能先写测试再做，不出 spec 也不出票：没有 ticket 时 `implement` 走不了第一步。上游那句「Reach for `/tdd` on its own …」并进这一支。(3) 其后一段写成被派出的 worker 读 `implement`，它驱动 `tdd`、收尾经 `code-review`；只写收尾经 `code-review` 审这张票的 diff，不列 axis：axis 名单是 `code-review/SKILL.md` 的，路由这里只管用哪个技能，列一份会随那边的试点过期；`before committing` 删掉，因为 implement 先提交再跑 code review，axis 读的是 `git diff <base-commit>...HEAD`；上游「`/code-review` on its own whenever you want to review a branch or PR」改成 `code-review` 只审一张 ticket 的 diff、离开 ticket 没有用法：它的入口只有「prompt 点名本技能、一张 ticket 与一个 base commit」。上游改第 3 步 → 收上游措辞，这三处接回去；上游改 axis 的描述 → 不收，这里仍不列 axis；上游改先后 → 只在它自己也是先提交后 code review 时收 |
| On-ramps 的 triage 一条，与 wayfinder 一条的第二段 | 我们改的：triage 把判为 agent-ready 的活送进 `to-spec` 再 `to-tickets`（上游写「produces agent-ready issues, which `/implement` later picks up」），并写明 pipeline 退回 `needs-triage` 的 ticket 由 triage 再判一次，与 `triage` 技能 `references/pipeline-issues.md` 的 `## A ticket handed back` 一致。wayfinder 一条的「then `/to-tickets` and `/implement`」改成 `to-tickets` 与 `dispatch`，「go straight to `/implement`」改成走第 3 步的 No 一支，理由同上一行。上游改这两条 → 收上游措辞，这两处去向保留 |
| Phase boundaries 段的 Handoff 一条与 `PHASE-BOUNDARIES.md` 的第 3、5 问 | `harness` 改成 `host`：同一样东西在 `models.json` 的 `host` 字段、`AGENTS.md` 与 `CONTEXT.md` 里都叫 host。第 3 问第一条删掉上游的例子「(Claude → Codex)」：它点名两个 host，违反 host 中立（[README.md](README.md#host-中立)）。上游改这两句 → 收上游措辞，`host` 这个词保留，不带 host 名的例子 |
| 主流程第 2 步末尾「A UI question's answer goes on, not back」那一段 | 我们加的整段：winner 定下之后的界面链——`design-pages`（建用户在里面设计的 Claude Design 项目，需要时从 winner 建 design system，pull 回 design package）接 `write-screen-contract`（每个控件绑到接口、字段与后续状态），再进第 3 步写 spec；有 map 时是 design ticket 与 alignment ticket，没有 map 时在用户在场的同一个 session 里连着做。理由：这个路由器原来对整条界面链是哑的（三个技能名出现 0 次），而冷启动只有两条路能找到技能：description 与这张地图；断得最狠的是「已有产品加一块界面」那一支，它的正确走法全工具箱只写在链条第五个文件里。上游改第 2 步 → 收上游措辞，这一段接在它后面 |
| 主流程第 2 步、技能清单里的 prototype 一条 | 跟上本仓的 prototype 技能：三类问题（逻辑、UI、实现方式；第 2 步问题清单里加的「a library or approach you have to run」就是实现方式那一类）；prototype 长期留在仓库 `prototypes/` 下的 leaf directory 里当参考（完整路径规范归 prototype 技能，这里不复述），**没有** `prototype/<name>` 分支。另加一句：逻辑与实现方式的答案折进真实代码，而胜出的 UI variant 不折——它交给 Claude Design，真实代码从拿回来的 design page 写，与 `prototype/SKILL.md` 第 6 条一致（原文只写「折进真实代码」，对 UI 分支已经是错的）。上游改措辞可跟，但这三点不能被上游的说法覆盖回去。改这里同时看 `merge-notes/prototype.md` |
| 技能清单里 `resolving-merge-conflicts` 那一条 | 触发条件跟上本仓的 `resolving-merge-conflicts` 技能：进行中的 merge 或 rebase 冲突，以及一次合得干净却让仓库检查变红的合并（见 `merge-notes/resolving-merge-conflicts.md`）。上游改这一条 → 收它的措辞，两种触发都保留 |
| 全文的技能名写法、Phase boundaries 那张五个选项的清单（`SKILL.md` 与 `PHASE-BOUNDARIES.md` 各一份）、`## Phase boundaries` 与 `## The five options` 两节的开头 | host 中立：技能名一律写成 `` the `X` skill ``；`Clear` 与 `Compact` 两个选项写成清空上下文、压缩成摘要这两个动作本身，只有 Handoff 那一条在正文里点 `handoff` 技能的名；两节开头各加一句能力说明，说这两件事每台 host 都有、名字各不相同。共同理由见 [README.md](README.md#host-中立)，写法见 `writing-for-agents` 技能的 `SKILL-SET-REVIEW.md` `### Paths, tokens and host neutrality` 与 `### Hand-offs` |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉，跟 `SKILL.md` 的 `disable-model-invocation` 一起。规则见 [README.md](README.md#disable-model-invocation) |
