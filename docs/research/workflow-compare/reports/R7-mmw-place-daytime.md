# R7 MMW 逐项归置：白天定义单元（daytime definition）

本文按 `docs/research/workflow-compare/reports/R4-mmw-architecture-form.md`（下称 R4）把白天定义单元的每个部件归到新架构里。准绳是 `docs/research/workflow-compare/reports/L7-pstack-component-contract.md`（下称 L7）第 C 节。技能文本规则 `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（下称 SSR）是被审视的对象。

单元范围：`to-spec`、`to-tickets`（含三份 reference）、`triage`、`wayfinder`、`grilling`、`grill-me`、`grill-with-docs`、`domain-modeling`、`prototype`（含 `LOGIC.md`、`UI.md`、`EXP.md`）、`research`、`to-questionnaire`、`codebase-design`、`improve-codebase-architecture`、`diagnosing-bugs`、`wizard`、`handoff`、`teach`、`wait-what`、`setup-matt-pocock-skills`；未安装的 `ask-matt` 与其中现在无家的内容（`N10-mmw-routing-and-invocation.md` §4 B1–B5）；`docs/agents/*.md`。

标注：「已核实」＝本轮回到原文或跑命令看到；「推断」＝由原文推出；做不出判断的放第 8 节。

---

## 0. 结论

1. **本单元是 R4 头部改动的主体。** `mmw` 的 `## Head judgement`、`## Routes` 里四行、`## Where you are` 的 (d)(e) 两行，`playbooks/idea-to-tickets.md` 全文，`references/phase-boundaries.md` 全文，内容都出自本单元（残留 `ask-matt` 与各技能结尾句）。
2. **两个技能分叉**：`to-spec`、`to-tickets` 整体搬进 `mmw-v2/skills/`，名字不变。它们内部一字不拆，只把结尾的下一步句换成固定返回句（第 4 批）。其余 17 个技能都留在上游目录。
3. **从上游文本移走的 MMW 句子共 9 处**（第 1 节表中「回到上游原文」的各行）：`grill-with-docs` 末句、`wayfinder` 第 6 步后半句与两处 `mmw:map`、`triage` 第 5 步后半与 `## Quick state override` 末句与 route 句、`improve-codebase-architecture` `### 4` 的交接句、`prototype` `UI.md` `## Next`。每处都说得出新家。
4. **对 R4 的两处细化，都是工程决定，已自行定下：**
   - R4 D5.3 把 `prototype` 规则 1 的叶子目录形状、`UI.md` 的 `## State list` 列为 d 类（移到旁加 reference，由 playbook 点名）。本文不移：`prototype` 有三个入口（description、`wayfinder` 的 prototype 票、playbook），只有一个经过 playbook；另外两个入口读不到旁加 reference，而这两处格式被 `pull_design.py` 与 `design-pages` 读，读错就断。这两处按 e 类留在原处。建议 D5.3 的 d 类补一个前提：该技能的每个入口都会读到那份 reference。
   - R4 D5.3 让 `triage` 第 5 步保留「关闭 issue 时链接 spec」。本文把这一句移进分叉后的 `to-spec` 第 4 步：triage 会话里 spec 还不存在，这句只有在发布 spec 的会话里才做得到；它的依据 ADR 0001 第 20 行说的正是「spec 发布或修订后」。
5. **R4 第 16 节 U4（`AGENTS.md` 指向 `mmw` 那一行由谁写）按工程决定定为**：`mmw` `## Where you are` 的 (c) 行，加 `dispatch.sh check` 的只读警告；`setup-matt-pocock-skills` 不动。理由见第 1 节 J 行。
6. **本单元不产生新原则**；给 R4 的三条原则中的两条补了引用位置（第 3 节）。
7. **没有需要 owner 做的新产品决定**；第 7 节只列 R4 已有决定在本单元的具体可见效果，请 owner 确认。

---

## 1. 归置表

列说明：「批」＝R4 §11 落地批次；「收益」只用用户要求 2 的六种，编号如下：
**G1** 去掉一处经 grep 核实的真重复；**G2** 给现在无处安放的内容一个家；**G3** 把 MMW 流程从上游文本移走、让上游回到原文；**G4** 被两个以上 playbook 或调用方复用；**G5** 以后加外来技能不必改现有文字；**G6** 消除一处已核实的断点或冲突。

### A. `to-spec`

| # | 现在位置 | 新位置与层 | 动作 | 移动的小节（原标题） | 收益与证据 | 体量 | 被取代的旧规则与原意 | 批 |
|---|---|---|---|---|---|---|---|---|
| A1 | `mmw-v2/upstream/skills/engineering/to-spec/`（`SKILL.md` 127 行、`references/revising-a-spec.md` 11 行、`references/several-specs.md` 5 行） | `mmw-v2/skills/to-spec/`，能力技能（自有） | 移动（分叉），`skills.txt` 改 `self/to-spec` | 整个目录，小节不拆 | G3：`merge-notes/to-spec.md` 第 31 行自认「不到一半的行是上游的」（R4 V11 已核实）；N4 §5 实测上游非空行 45 行中只保留 31 行，词数 493 → 2509 | 自有目录 +143；上游目录恢复原文 127 → 75（不安装） | SSR `### Upstream skills`「fewer than half … reviewed as the set's own text」改为「分叉」（R4 D5.3 f）。原意（上游被改写后无法跟进）由分叉表与每次拉上游读 diff 保住 | 2 |
| A2（已被 R12 K-20 改定） | `to-spec/agents/openai.yaml`（3 行） | 删除 | 删除 | — | G6：SSR `### Descriptions` 第 4 条「A skill this repository wrote has no host-side manifest beside it」，分叉后仍带它就与该条冲突；它的 `short_description` 与 description 是同一件事的第二份 | −3 | 无 | 2 |
| A3（已被 R12 K-7 改定） | `to-spec/SKILL.md` `## Next`「The `to-tickets` skill.」（第 125–127 行） | 同位置，改写成固定返回句「Then return to the playbook that sent you; with none, the `mmw` skill routes what follows.」；`to-spec → to-tickets` 这一步的家是 `idea-to-tickets` 的 **Tickets** | 改写 | `## Next` | G1：`to-spec → to-tickets` 的先后今天写在 `to-spec` `## Next`、`triage` 第 82、94 行、`wayfinder` 第 126 行、`triage/references/pipeline-issues.md` 第 5 行（grep 已核实），顺序有五个家 | 0 | SSR 事实 7「closing section names the next step」改写（R4 §9）。原意（#538：一跳找不到下一步）由固定返回句保住：单独斜杠进来的会话被送回 `mmw` | 4 |
| A4 | `triage/SKILL.md` 第 82 行「close this issue with a comment linking that spec」 | `to-spec` 第 4 步加一句：引用是一张已分诊的 issue 时，发布后以一条链接到 spec 的评论关闭它 | 移动 | 第 4 步（接在 `--publish` 之后） | G3（triage 回到上游这一句）；G6：句子留在 triage 里时，一旦去掉点名 `to-spec` 的半句，「that spec」无所指 | +1 句 | ADR 0001 第 20 行「spec 发布或修订后，带 agent brief 的原 issue 以一条链接到 spec 的评论关闭」，规则从此写在发布 spec 的技能里 | 4（须与 C3 同一次提交） |
| A5 | `to-spec` description 的四支触发 | 原位 | 不动 | — | 四支都是 `to-spec` 自己的输入分支（第 1 步 map、`## Sources` 的 triaged issue、`references/revising-a-spec.md`），按自有技能规则是本能力的触发；R4 D5.3 b 已点名这句按自有技能审 | 0 | — | — |
| A6 | 第 1–4 步、`<spec-template>`、两份 reference | 原位 | 不动 | — | 天然整体（N4 §8）；第 2 步「回 `write-screen-contract` 的 **Reverse sweep**」「回 alignment ticket」取决于本技能自身输入，属能力内部（R4 D5.1） | 0 | — | — |
| A7 | `mmw-v2/merge-notes/to-spec.md` | 原位，改为分叉技能的意图记录 | 改写 | 删第 12、41 行对开关规则的复述；更正 N4 §5.1 核实的两处过时条目（第 22 行 `## Sources` 与 `implement` 的关系、第 31 行 Done 判据措辞） | G1：第 12、41 行复述 `merge-notes/README.md` 第 20 行的规则，违反同文件第 24 行「不复述这条规则」（N10 R2，grep 已核实）；G6：SSR `### Upstream skills`「An entry that still states a replaced rule is a finding」 | −2 行，改 2 行 | — | 2 |
| A8 | `docs/contexts/tickets/CONTEXT.md`、`ui-acceptance/CONTEXT.md` 里指向 `mmw-v2/upstream/skills/engineering/to-spec/…` 的 `_Home_` 行（约 17 处） | 改指 `mmw-v2/skills/to-spec/…` | 改写（路径） | — | G6：分叉后这些地址失效（grep 已列出） | 0 | — | 2 |

### B. `to-tickets`

| # | 现在位置 | 新位置与层 | 动作 | 移动的小节 | 收益与证据 | 体量 | 被取代的旧规则与原意 | 批 |
|---|---|---|---|---|---|---|---|---|
| B1 | `mmw-v2/upstream/skills/engineering/to-tickets/`（`SKILL.md` 206 行、`references/ambiguity-scan.md` 83、`cutting-interface-tickets.md` 152、`person-ticket.md` 14） | `mmw-v2/skills/to-tickets/`，能力技能（自有） | 移动（分叉） | 整个目录，小节不拆 | G3：`merge-notes/README.md` `## 本仓自有正文的技能`（第 34–36 行）已声明「正文几乎全是本仓写的，拉 upstream 时不合并」；N4 §5 上游非空行 60 行只保留 30 行 | 自有 +455；上游恢复 206 → 105 | 废止 `## 本仓自有正文的技能`（要求把自动合进来的上游段落手工改回，属会悄悄撤掉改动的手工步骤），由分叉表取代（R4 D5.3 f） | 2 |
| B2（已被 R12 K-20 改定） | `to-tickets/agents/openai.yaml` | 删除 | 删除 | — | 同 A2 | −3 | — | 2 |
| B3（已被 R12 K-7 改定） | `### 8. Read every ticket back` 末句「When the batch is a spec's night run, hand over to the `dispatch` skill …」（第 160 行） | 同位置换成固定返回句；「交给 `dispatch`」的家是 `idea-to-tickets` 的 **Hand to the night** | 改写 | 第 8 步末句 | G1：与 A3 同一条顺序的第二个家 | 0 | 同 A3 | 4 |
| B4 | `### 4. Write each acceptance criterion` 里 `EXPECT:` 一条（「`EXPECT:` is a **success-only marker** … take the whole counted line.」） | 原位，句末加 `(the `mmw` skill's principle `silence-is-never-a-pass`)` | 改写（括注） | 第 4 步第二个列表第 2 条 | G4：原则被 `idea-to-tickets` **Tickets**、本处、`implement` 收尾、`night.md` 收口引用（R4 D4.4） | +1 括注 | — | 3 |
| B5 | 第 1 步「A plan or a conversation with no published spec goes through the `to-spec` skill first」、第 4 步第 2 问与「return to the `to-spec` skill」、第 6 步经 `revising-a-spec.md` 回写 | 原位 | 不动 | — | 前置条件与横向调用，属能力内部；不是「交付物之后做什么」（R4 D5.1） | 0 | — | — |
| B6 | 第 1–8 步其余、`<issue-template>`、三份 reference | 原位 | 不动 | — | 天然整体（N4 §8）；`<issue-template>` 被 `night.md` 与 `pipeline-issues.md` 按名读；`ambiguity-scan.md` 是交给子代理的提示模板（L7 A.5 第一行）；`person-ticket.md` 被 `triage` 共用 | 0 | — | — |
| B7 | `mmw-v2/merge-notes/to-tickets.md` | 原位，改为分叉技能的意图记录 | 改写 | 删第 15、50 行开关复述；更正 N4 §5.2 核实的过时条目（第 28 行与 part 3 第 40、42 行关于 `linting.md` 的描述） | 同 A7 | −2 行，改 3 处 | — | 2 |
| B8 | `docs/contexts/tickets/CONTEXT.md`、`toolbox/CONTEXT.md` 指向 `…/engineering/to-tickets/…` 的 `_Home_` 行（约 40 处） | 改指 `mmw-v2/skills/to-tickets/…` | 改写（路径） | — | G6 | 0 | — | 2 |

### C. `triage`（留在上游）

| # | 现在位置 | 新位置与层 | 动作 | 移动的小节 | 收益与证据 | 体量 | 被取代的旧规则与原意 | 批 |
|---|---|---|---|---|---|---|---|---|
| C1 | frontmatter 无 `disable-model-invocation`、`agents/openai.yaml` 无 `policy` | 原位 | 不动（推导结果与现状相同） | — | `mmw` `## Routes` 按名调用 `triage`，按 R4 D1.3 两个开关都去掉 | 0 | 手写 7 个名单改为推导规则（R4 §9） | — |
| C2 | description 两支触发 | 原位 | 不动 | — | 两支都是本能力的触发；流水线退回的票就是本仓 `needs-triage` 队列的实际来源（N4 §6：本仓 585 张、agentflow 717 张 issue 作者都是 owner，外来分支从未发生） | 0 | — | — |
| C3 | `## Triage a specific issue or PR` 第 5 步 `ready-for-agent` 一条（第 82 行） | 留：「when the issue is work from outside, post an agent brief comment on it ([AGENT-BRIEF.md](AGENT-BRIEF.md)); the label goes on the tickets later cut from it, not on this issue.」。移走：「route it into the ticket pipeline: write a spec with the `to-spec` skill, or extend a published one through that skill's `references/revising-a-spec.md` … then cut tickets from the spec with the `to-tickets` skill」→ `mmw` `## Routes` 的 triage 行进 `idea-to-tickets` 的 **Spec**；「close this issue …」→ A4 | 拆分 | 第 5 步第 1 条 | G3（上游这一条回到「post an agent brief comment」，只多一句 e 类的 label 去处）；G1（顺序的第三个家） | −1 句 | R4 D5.3 的三处混合段之一；原意（外来 issue 必须经 spec 与票落地）由 Routes 行与 `idea-to-tickets` 保住 | 4 |
| C4 | 第 5 步末段 route 句（第 90 行「A child whose default was right … `dispatch.sh route <ticket> <child> fixed` … `wontfix` means nobody will do it」） | `triage/references/pipeline-issues.md` `## ready-for-agent` 之后新增一段（或并入开头段的 child 列表之后） | 移动 | 第 5 步末段 | G3：这句只适用于流水线 child；`pipeline-issues.md` 是这类 issue 必先读的旁加 reference（`triage` 第 70 行），移过去后上游第 5 步只剩上游的四个 outcome | 上游 −1 段，reference +1 段 | — | 2 |
| C5 | `## Quick state override` 末句「ask whether they want to route it into the ticket pipeline now: the `to-spec` skill, then the `to-tickets` skill」 | 恢复上游「ask whether they want to write an agent brief」 | 回到上游原文 | `## Quick state override` | G3、G1 | 0 | `merge-notes/triage.md` 第 22 行删去 | 4 |
| C6 | `triage/references/pipeline-issues.md` 第 5 行 retro 提案一句「approved work goes through the `to-spec` and `to-tickets` skills」 | 同位置改为：获批的提案像外来工作一样成为一份 spec 的来源，不写 agent brief（retro 已收齐证据）；去处由 `mmw` `## Routes` 的 triage 行给 | 改写 | 开头第二段 retro 一句 | G1：顺序的第四个家 | 0 | — | 4 |
| C7 | `pipeline-issues.md` 第 3 行「read a ticket's events with the `verify-ticket` skill's `events.py fold <n>` rather than reproducing」 | 原位加括注 `(the `mmw` skill's principle `the-tracker-is-the-state`)` | 改写（括注） | 第 3 行 | G4：原则的第五处引用 | +1 括注 | — | 3 |
| C8 | 第 70 行路由句与 `## Reference docs` 第 22 行 | 原位 | 不动 | — | e 类：删掉后，经 description 或 `docs/agents/issue-tracker.md` `## Morning queries` 直接进 triage 的会话（不经 mode）会对流水线产物按外来 issue 复现、查 `.out-of-scope/`，而这正是本仓 triage 的全部实际输入（N4 §6） | 0 | — | — |
| C9 | `## Roles` 的 `ready-for-human` 定义与「Work this repo plans for itself carries no category role」；免责声明放末行；第 5 步 `ready-for-human` 一条；第 4 步宿主中立；`AGENT-BRIEF.md` 改动 | 原位 | 不动 | — | e 类（改变能力，各有 merge-note）或 a 类 | 0 | — | — |
| C10 | `mmw-v2/merge-notes/triage.md` 第 12 行（出处写成「取自 `ask-matt/SKILL.md`」）、第 15、36 行（开关规则复述）、第 21、22 行（随 C3、C5 改） | 原位 | 改写 | — | G6：N10 B11（出处指向已不安装的技能）；G1：N10 R2 | 约 −2 行 | — | 2（第 21、22 行随 4） |

### D. `wayfinder`（留在上游）

| # | 现在位置 | 新位置与层 | 动作 | 移动的小节 | 收益与证据 | 体量 | 被取代的旧规则与原意 | 批 |
|---|---|---|---|---|---|---|---|---|
| D1 | `### Work through the map` 第 6 步（第 126 行） | 留：「If no child ticket of the map is still open and **Not yet specified** is empty, the map is clear: stop and tell the user. Leave the map open: it stays this effort's index of decisions.」。移走：「in a fresh session, run `to-spec` against this map, passing the map's full reference … and then `to-tickets`」→ `mmw` `## Routes` 的 wayfinder 行 | 拆分 | 第 6 步 | G3（R4 V12：上游原文只有 5 步）；G1（顺序的又一个家） | −1 句 | 停止判据（用子票是否开着，不用 frontier）是 e 类，留下 | 4 |
| D2 | `## The Map` 第 20 行与 `### Chart the map` 第 3 步里的 `mmw:map`，含「create `mmw:map` as `docs/agents/issue-tracker.md` `## Three label sets` gives, when the repository lacks it」 | 恢复上游「labelled `wayfinder:map`」；建 label 的一句并进 `docs/agents/issue-tracker.md` 与种子 `setup-matt-pocock-skills/issue-tracker-github.md` 的 `## Wayfinding operations` **Map** 一条 | 回到上游原文 + 合并进已有的家 | `## The Map`、第 3 步 | G1：`docs/agents/issue-tracker.md` 第 79 行与种子第 69 行已写 `gh issue create --label wayfinder:map --label mmw:map`（grep 已核实；agentflow 的落地件第 87 行同样有，`gh api` 已核实）；G3：上游第 24 行本来就让 agent 去 tracker 文档的「Wayfinding operations」查本仓的做法 | wayfinder −2 处；tracker 文档与种子各 +1 句 | — | 2（先过第 8 节 T-D2 走查） |
| D3 | `frontmatter` 开关、description 两句触发 | 原位 | 不动 | — | 推导结果不变（`## Routes` 点名）；两句都是本能力的触发与反触发 | 0 | — | — |
| D4 | `mmw-v2/merge-notes/wayfinder.md` 第 11、27 行（开关复述）、第 21 行（出处 `ask-matt`）、第 18 行（随 D1 改） | 原位 | 改写 | — | G1（N10 R2）；G6（N10 B11） | 约 −2 行 | — | 2（第 18 行随 4） |
| D5 | map body 模板 `## Notes` 里的 effort 目录名、第 4 步指向 `references/interface-and-remake.md`、第 5 步 research 子代理交代、宿主中立各处、`references/interface-and-remake.md` 全文 | 原位 | 不动 | — | 见第 5 节 | 0 | — | — |

### E. `grilling`、`grill-me`、`grill-with-docs`、`domain-modeling`

| # | 现在位置 | 新位置与层 | 动作 | 移动的小节 | 收益与证据 | 体量 | 被取代的旧规则与原意 | 批 |
|---|---|---|---|---|---|---|---|---|
| E1 | `grill-with-docs/SKILL.md` 第 7 行第 3 句「When the session settles a change to build, name the `to-spec` skill as the next step, in this same session.」 | 删除；下一步由 `idea-to-tickets` 的 `## Where you are`（对话里已有定下要建的决定 → **Who checks**）接住，「同一会话」由 **Spec** 的门槛接住 | 回到上游原文（c 类） | 第 7 行末句 | G3；G1（顺序的又一个家） | −1 句 | SSR 事实 7 的「结尾点名下一步」改写；原意（上游文档称「结束语开放、不知道下一步」是最常见的毛病，`merge-notes/grill-with-docs.md` 第 14 行）由 `mmw` 保住 | 4 |
| E2 | `grill-with-docs` 第 2 句「these writes are part of the session, not the acting on it that `grilling` holds back」 | 原位 | 不动 | — | e 类：删掉后 agent 会把写 `CONTEXT.md` 当成「用户确认前不动手」的一部分而不写 | 0 | — | — |
| E3 | `grilling`、`grill-me`、`domain-modeling` 全文 | 原位 | 不动 | — | 见第 5 节 | 0 | — | — |
| E4 | `grill-with-docs` 的调用开关（用户触发） | 原位 | 不动 | — | `idea-to-tickets` **Grill** 点名 `grilling` 与 `domain-modeling`，不点名 `grill-with-docs`，推导结果仍是用户触发；原意（与 `grilling` 抢同一个请求，`merge-notes/grill-with-docs.md` 第 11 行）保住 | 0 | — | — |

### F. `prototype`

| # | 现在位置 | 新位置与层 | 动作 | 移动的小节 | 收益与证据 | 体量 | 被取代的旧规则与原意 | 批 |
|---|---|---|---|---|---|---|---|---|
| F1 | `UI.md` `## Next`（第 119–121 行，一句） | 删除；交给 `design-pages` 由 `idea-to-tickets` **Runnable questions** 点名；经 wayfinder 的界面由 `wayfinder/references/interface-and-remake.md` 的 design ticket 接住 | 回到上游原文（c 类） | `## Next` | G3；R4 D5.3 已列 | −3 | 原意（UI 胜出方案走 Claude Design，ADR 0029）仍由 `SKILL.md` 规则 6「A UI prototype's winner is not folded in here: it is handed to Claude Design」与 `UI.md` 第 6 步第二段承担，这两处是 e 类，留 | 4 |
| F2 | `SKILL.md` 规则 1（叶子目录 `prototypes/<effort>/<issue>/<UI\|LOGIC\|EXP>/`）、`UI.md` 第 6 步 `## State list` 格式 | 原位 | 不动（按 e 类，不按 R4 例子的 d 类） | — | 见第 0 节第 4 条：三个入口里只有一个经 playbook；`pull_design.py`、`design-pages` 读这两处格式（N5 §2.1、§3.1 已核实） | 0 | — | — |
| F3 | `SKILL.md` 规则 6 的「fold the validated decision into the real code」（LOGIC、EXP 分支，B4） | 原位；在 `idea-to-tickets` **Runnable questions** 由调用方限定范围：结论写进叶子 `README.md` 后回 **Grill**，本 playbook 不写生产代码 | 不动（上游原句，MMW 只改了「rewritten to production standard」） | — | G6（修 B4：无 map 时绕过 spec 与票）；限定写在调用方，是 L7 C.2 `no-comments` 的写法 | 0 | — | 3 |
| F4 | `LOGIC.md`、`EXP.md`、`evidence-page.md`、`UI.md` 其余 | 原位 | 不动 | — | 能力本身（N5 §5.2 标「能力」） | 0 | — | — |
| F5 | `mmw-v2/merge-notes/prototype.md` 第 59 行（`## Next` 条目） | 删去该条 | 改写 | — | 随 F1 | −1 行 | — | 4 |

### G. `improve-codebase-architecture`、`diagnosing-bugs`、`codebase-design`

| # | 现在位置 | 新位置与层 | 动作 | 移动的小节 | 收益与证据 | 体量 | 被取代的旧规则与原意 | 批 |
|---|---|---|---|---|---|---|---|---|
| G1 | `### 4. Hand the decision on`（第 73–75 行） | 留：「This skill changes no code. What the grilling settles is a decision … refactoring here would skip the tickets and the acceptance checks that make the change safe to land. Take one candidate per session, and tell the user the report's path so the others can be picked up later.」。移走：「When the user confirms it, hand that decision to the `to-spec` skill, which turns this conversation into a spec the landing pipeline can build and verify」→ `idea-to-tickets` `## Where you are`（对话里已有定下的决定 → **Who checks**） | 拆分 | `### 4` 的第 3 句 | G3（R4 V12：整节是本仓加的）；G1 | −1 句 | 留下的「不改代码」是 e 类：`merge-notes/improve-codebase-architecture.md` 第 16 行记录它防的是 `grilling` 末句被读成「确认后即可动手」；用户直接斜杠进入时 mode 可能不在 | 4 |
| G2 | 残留 `ask-matt/SKILL.md` 第 44 行「Its post-mortem hands off to the `improve-codebase-architecture` skill when the real finding is that there's no good seam」与第 54 行 `## Codebase health` | `mmw` `## Routes` 两行：「有东西坏了」的门槛列，与「想整理代码架构」一行 | 移动（从未安装的文件） | — | G2 + G6：B6（`diagnosing-bugs` `## Phase 5` 只写「Flag this for the next phase」，从未交接，N10 B6 已核实）；这句上游 `ask-matt` 原本就有（本轮 `git show 5b1a4c51` 已核实），所以是把上游路由的原意放回路由层 | mode +2 行 | — | 3 |
| G3 | `diagnosing-bugs` 全文、`hitl-loop.template.sh`；`codebase-design` 全文；`improve-codebase-architecture` `### 1`–`### 3`、`HTML-REPORT.md` | 原位 | 不动 | — | 见第 5 节 | 0 | — | — |
| G4 | `mmw-v2/merge-notes/improve-codebase-architecture.md` 第 11 行「另外六个保留这一行的是 …」、`teach.md` 第 22 行同句 | 删掉名单，只留本技能站在哪一边 | 改写 | — | G1：N5 R10、N10 R4（名单三处完整列出，README 第 24 行要求不复述，grep 已核实） | 各 −1 句 | — | 2 |

### H. `research`、`to-questionnaire`、`wizard`、`handoff`、`teach`、`wait-what`

| # | 现在位置 | 新位置与层 | 动作 | 收益与证据 | 批 |
|---|---|---|---|---|---|
| H1 | 六个技能的全部文件 | 原位，能力技能 | 不动 | 见第 5 节 | — |
| H2 | 残留 `ask-matt` 第 85 行「research … take *into* the main flow」、第 86 行「to-questionnaire … What comes back is material for grill-with-docs or to-spec」 | `idea-to-tickets` **Grill** 一句（仓库外的一手事实用 `research`，spec 才能在 `## Sources` 的 Research files 引用文件）；**Someone else knows** 与 `## Where you are`「用户带回填好的问卷 → **Grill**」 | 移动（从未安装的文件） | G2：两句只在未安装的 `ask-matt` 里（N5 §3.1 `to-questionnaire` 行、§3.2 末条：除 `ask-matt` 外没有已安装技能点名它们，grep 已核实） | 3 |
| H3 | `handoff`：无任何已安装技能点名（N10 B5） | 由 `mmw/references/phase-boundaries.md` 的 Handoff 选项点名，写成「告诉用户运行 `/handoff`」 | 不动技能本身 | G2 | 3 |

### J. `setup-matt-pocock-skills`

| # | 现在位置 | 新位置与层 | 动作 | 收益与证据 | 批 |
|---|---|---|---|---|---|
| J1 | `SKILL.md` 全文（含本仓加的第 17 行、Section A/B/C 的本仓句、第 4 步 `## External References` 与 `CLAUDE.md` 形状） | 原位 | 不动 | 这几处都改变本技能写出什么，属 e 类（N5 §5.2）；它只被「告诉用户运行」，没有 playbook 步骤可以承载 d 类的旁加 reference | — |
| J2 | R4 U4：消费仓库 `AGENTS.md` 指向 `mmw` 的一行由谁写 | `mmw` `## Where you are` (c) 行 + `dispatch.sh check` 只读警告；本技能不加 | 工程决定 | 若加进本技能第 4 步，就是往上游文本里加 MMW 流程（违反 G3 的方向）；本技能一个仓库只跑一次，而 (c) 行在每次有人在场的会话都能补上 | 3 |
| J3 | 种子 `issue-tracker-github.md` `## Wayfinding operations` **Map** 一条 | 加「建 `mmw:map` label」一句 | 改写 | 随 D2 | 2 |
| J4 | 种子与本仓落地件已漂移（N5 R5、R6；N4 R8） | — | 不动（架构外） | 不属于分层；另开普通票 | — |

### K. 未安装的 `ask-matt` 与其中无家的内容（N10 B1–B5）

| # | 现在位置（残留 `mmw-v2/upstream/skills/engineering/ask-matt/`） | 新位置与层 | 动作 | 收益与证据 | 被取代的旧规则与原意 | 批 |
|---|---|---|---|---|---|---|
| K1 | `PHASE-BOUNDARIES.md` 全文（57 行，相对上游只有宿主中立改写，R4 V13） | `mmw-v2/skills/mmw/references/phase-boundaries.md`，mode 的 reference；Handoff、Clear、Compact 三个选项写成「建议用户做」，其余照录 | 新建（照录） | G2（B5）；G4：`mmw` `## Where you are` (d) 与 `idea-to-tickets` **Spec** 门槛两处读；G6：SSR `### Paths and host neutrality` 要求点名会话命令的文件带一次固定句，现在唯一带它的是未安装的 `ask-matt`（N5 §5.3 第 6 条，grep 已核实），照录后重新有已安装文件满足该条 | 06163a0f 的删除理由「每个技能结尾已点名下一步」不覆盖阶段边界这一判断；原意（不留会漂移的第二份地图）保住：这份 reference 不列技能路由 | 3 |
| K2（已被 R12 K-40 改定） | `SKILL.md` 第 22–26 行 Yes/No 分支与「In this repository the branch also decides who checks the work …」 | `mmw` `## Head judgement` | 移动 | G2（B3，N10 已核实无第二处） | — | 3 |
| K3 | `SKILL.md` `### Context hygiene`（第 30–34 行，上游原文加宿主中立改写） | `idea-to-tickets` **Spec** 的门槛 | 移动 | G2（B5） | `grill-with-docs` 末句的「in this same session」（E1）由此取代 | 3 |
| K4 | 第 19–21 行 prototype 在同一会话跑、UI 胜出方案走 `design-pages` → `write-screen-contract`、无 map 时 prototype 到 screen contract 在一个有用户在场的会话里跑完 | `idea-to-tickets` **Runnable questions** | 移动 | G2（这几句只在未安装的 `ask-matt` 里） | — | 3 |
| K5 | `## On-ramps` 三条、`## Codebase health`、第 92 行「When neither this map nor those fit, tell the user so instead of assembling a flow of your own」 | `mmw` `## Routes` 的行与结尾一句 | 移动 | G2（B1）；结尾一句防的正是 #538 那种「自己发明一套做法」（N10 §7 已核实） | SSR 事实 7「MMW ships no router skill」废止（R4 §9） | 3 |
| K6 | `## Vocabulary underneath`、`## Standalone`、`## Precondition` | 不迁 | 删除（随恢复上游原文消失） | 这些技能的 description 已能触发（R4 D2.2「不列入路由的」）；迁入就是同一触发写两处 | — | 2 |
| K7 | 残留目录三份文件 | 恢复上游原文（`git show 5b1a4c51:skills/engineering/ask-matt/…`），不安装 | 回到上游原文 | G6：N10 B10（目录不是「unmodified copy」且没有 merge-note，下次拉上游会冲突）；G3 | 06163a0f 提交说明的描述不再失真 | 2 |
| K8 | 新开一份按来源的 merge-note（例如 `merge-notes/phase-boundaries.md`），记来源 `ask-matt/PHASE-BOUNDARIES.md`、squash 提交与宿主中立改写 | `mmw-v2/merge-notes/` | 新建 | R4 D4.5 要求；拉上游时维护者知道要不要跟 | — | 3 |

### L. `docs/agents/*.md`（消费仓库私有组件，R4 D7.6）

| # | 部件 | 动作 | 理由 | 批 |
|---|---|---|---|---|
| L1 | `issue-tracker.md` `## Wayfinding operations` **Map** 一条 | 加建 label 的一句（随 D2） | 见 D2 | 2 |
| L2 | `issue-tracker.md` 其余各节，含 `## Morning queries` | 不动 | 仓库数据与仓库规则；`## Morning queries` 是给早上的人两条查询命令，与 `mmw` 的 triage 路由行说的不是同一件事（一个是查什么，一个是去哪） | — |
| L3 | `triage-labels.md` | 不动 | `ready-for-human` 含义与 `triage` `## Roles` 第 36 行、词表同句（N4 R5）；三处读者不同（映射表、状态定义、维护者），L7 C.5 可接受 | — |
| L4 | `domain.md` | 不动 | 第 11 行「reached via grill-with-docs and improve-codebase-architecture」是种子原句，不改变任何决定 | — |

---

## 2. playbook 草图：`idea-to-tickets`

**文件**：`mmw-v2/skills/mmw/playbooks/idea-to-tickets.md`（R4 D3.3 骨架，本文补了 `## Where you are` 的三行与 **Grill** 的一句）。

**入口**：

- `mmw` `## Routes`「一个想法、一个要做的功能或改动」行；
- `## Routes` 的门槛列交接进 **Spec**：wayfinder map 清空后、triage 判为 agent-ready 的外来 issue 或获批的 retro 提案；
- `## Where you are` 进 **Who checks**：`improve-codebase-architecture` 定下的候选、一次 `grilling` 的共识、一份 prototype 结论；
- 用户直斜杠 `/grill-with-docs` 开的会话，本身就在 **Grill**（这一句是地址，不是调用，D1.3 的 lint 不算它）。

**所有权行**：**You own the way from an idea to a batch of published, linted tickets. Settle here what can be settled: the night has no one to ask.**

**开头段要说的**：为什么这个顺序（spec 是人最后看的一份文本，票被没参加这场对话的会话读）；结果交给 `dispatch`；与 `wayfinder`（一次会话装不下）、`triage`（从外面来的）的区别。

**`## Where you are`**（第一行成立的事实就走那一行；事实只取 tracker 与仓库，principle `the-tracker-is-the-state`）：

| The fact | Go to |
|---|---|
| 本次引用或本对话发布的 spec（`mmw:spec`）还没有 `mmw:ticket` 子票 | **Tickets** |
| spec 的票已发布，`--lint` 无 `ERROR` | **Hand to the night** |
| map 的 `## Specs` 或第一份 spec 的 `## Further Notes` 列着一份还没有链接的 spec | **Spec** |
| wayfinder map 没有开着的子票、**Not yet specified** 为空、没有 spec 挂在它下面；或一张带 `## Agent Brief` 评论、判为 agent-ready、仍开着的 issue；或一份获批的 retro 提案 | **Spec** |
| 对话里已有定下要建的决定（`grilling` 的共识、用户确认的架构候选、叶子 `README.md` 里的 prototype 结论），还没有 spec | **Who checks** |
| 用户带回一份填好的问卷 | **Grill** |
| 其他 | **Grill** |

**`## Steps`**：

1. **Grill.** 读 `grilling` 与 `domain-modeling` 两个技能并一起运行：每解决一个术语就写进 `CONTEXT.md`，按 `domain-modeling` 的说法提出 ADR。一个决定依赖仓库之外的一手事实时，用 `research` 技能，让 spec 能在 `## Sources` 引用那份文件。Done when `grilling` 自己的完成判据成立。
2. **Runnable questions.** 一个问题要运行才能回答时，用 `prototype` 技能，能在本会话跑就在本会话跑（要不要交出去，照 the `mmw` skill's `references/phase-boundaries.md` 第 3 问）。LOGIC、EXP 分支：结论写进叶子 `README.md` 后回 **Grill**，本 playbook 不写生产代码，代码随票落地。UI 分支：胜出方案交给 `design-pages` 技能，在宿主有 Claude Design 工具的会话里做；之后由 `design-pages`、`write-screen-contract` 自己的结尾段带到 **Spec**。没有 map 时，从 prototype 到 screen contract 在一个用户在场的会话里跑完，因为这场对话是 screen contract 所引决定的唯一记录。Done when 每个要运行的问题在叶子 `README.md` 有结论；有界面时，screen contract 每行 `gap` 为 `aligned`。
3. **Someone else knows.** 答案在别人脑子里时，用 `to-questionnaire` 技能，然后结束回合，等答案回来（重入走 `## Where you are`）。Done when 问卷文件已写好、用户知道发给谁。
4. **Who checks.** 套用 `mmw` 的 `## Head judgement`。答案是 No：用 `tdd`，告诉用户检查的人是他，本 playbook 到此结束。Done when 答案写进回复。
5. **Spec.** 用 `to-spec` 技能，引用是 map、已分诊的 issue 或本对话。门槛：**Grill** 到 **Tickets** 留在同一个没被清空、没被压缩的上下文里；接近上下文上限时，照 `references/phase-boundaries.md` 在最近的阶段边界压缩。Done when spec 已发布。
6. **Tickets.** 用 `to-tickets` 技能，从 spec 的编号切票（principle `silence-is-never-a-pass`：判据要能失败）。Done when `to-tickets` 的回读检查全部通过。
7. **Hand to the night.** 交给 `dispatch` 技能：开一夜，或一张票在夜外跑；什么时候开由用户决定。Done when 用户知道 spec 编号和这两种跑法。

**重入**：`## Where you are`；问卷、wayfinder、多份 spec 三种情况都跨会话。

**Done when**：票已发布并通过 lint，且已交给 `dispatch`；或 **Who checks** 答 No，`tdd` 完成。

**Reply**：spec 与票的编号（或 `tdd` 的结果与「由你检查」）；每个没做的步骤各一行：步骤名加理由。

本单元不产生别的 playbook。wayfinder、triage、排错、代码健康各在 `## Routes` 占一行（R4 D3.1；L7 C.6 信号 5）。

---

## 3. 原则候选

### 3.1 本单元对 R4 起步三条的引用位置

| 原则 | 本单元的引用位置 | 引用写法 |
|---|---|---|
| `silence-is-never-a-pass` | `idea-to-tickets` **Tickets**；`to-tickets` 第 4 步 `EXPECT:` 一条（B4） | playbook 内 `(principle …)`；技能内 `(the `mmw` skill's principle …)` |
| `the-tracker-is-the-state` | `idea-to-tickets` `## Where you are`；`mmw` `## Where you are`（R4 已列）；`triage/references/pipeline-issues.md` 第 3 行（C7） | 同上 |
| `rerun-dont-reroute` | 本单元无 | — |

### 3.2 本单元没有新的够格原则

按 R4 D4.3 的七条门槛，下面这些看起来像原则，但留在原处：

| 候选 | 出现处（已核实） | 不做成原则的理由 |
|---|---|---|
| 「读者不能再问：能定的现在定，写值不写指针」 | `to-spec` 第 6 行、`to-tickets` 第 10 行、`prototype` 规则 6、`to-tickets/references/person-ticket.md`「read later, on a phone」、`pipeline-issues.md` 第 3 行末句 | 门槛 7 不过：它就是 `mmw-v2/prompt/shared.md` 规则 10（「name who will pick it up … what they can and cannot see」）的具体应用；各处写的是本领域的具体读者，按 L7 C.2 留在调用方 |
| 「只把属于用户的决定交给用户」 | `grilling` 第 28 行、`to-spec` 第 6 行 | 门槛 7 不过：`shared.md` 规则 1。`grilling` 里那份是有记录的有意重复（N5 R14；merge-note 说全局规则压不住上游第 26 行） |
| 「同时能跑的两张票不写同一文件」 | `to-tickets` 第 107 行、`implement` 第 28 行 | R4 §15 已列 `one-writer-per-file` 的进入条件；两处各带理由 |
| 「每次读列表都读全」 | `docs/agents/issue-tracker.md` `## Conventions` | 绑定 `gh` 的具体参数（L7 C.2）；树的读取已由 `issue_tree.py` 强制（exit 2） |
| 「阶段边界的五个选项，按序排除」 | 残留 `PHASE-BOUNDARIES.md` | 形态是 reference（有序判断树、只在边界读），R4 D4.5 |
| 「每个决定写出出处」 | `to-spec` `<spec-template>` | 只有一个调用方，是格式 |

---

## 4. 连线

两类边不在给定关系词里，写在这里：

- **告诉用户运行**：`to-spec`、`to-tickets`、`triage`、`wayfinder` → `setup-matt-pocock-skills`；`mmw` → `improve-codebase-architecture`；`mmw/references/phase-boundaries` → `handoff`。按 R4 D1.3 这些不算调用，被点名的技能保持用户触发。
- **写出产物**：`setup-matt-pocock-skills` 写 `docs/agents/*.md` 与 `AGENTS.md` 的行；`to-spec`、`to-tickets` 写 tracker；`prototype` 写叶子目录。接线 lint `check_wiring.py` 第 3–5 类核对下面 `routes-to`、`calls` 与 `skills.txt`、调用开关、playbook 文件是否一致。

```edges
consumer-AGENTS.md -> mmw : routes-to
mmw -> mmw/playbooks/idea-to-tickets : routes-to
mmw -> mmw/playbooks/idea-to-tickets#Spec : routes-to
mmw -> wayfinder : routes-to
mmw -> triage : routes-to
mmw -> diagnosing-bugs : routes-to
mmw -> dispatch : routes-to
mmw -> mmw/references/phase-boundaries : reads-reference
mmw -> mmw/principles/the-tracker-is-the-state : cites-principle
mmw/playbooks/idea-to-tickets -> mmw : reads-reference
mmw/playbooks/idea-to-tickets -> mmw/references/phase-boundaries : reads-reference
mmw/playbooks/idea-to-tickets -> mmw/principles/the-tracker-is-the-state : cites-principle
mmw/playbooks/idea-to-tickets -> mmw/principles/silence-is-never-a-pass : cites-principle
mmw/playbooks/idea-to-tickets -> grilling : calls
mmw/playbooks/idea-to-tickets -> domain-modeling : calls
mmw/playbooks/idea-to-tickets -> research : calls
mmw/playbooks/idea-to-tickets -> prototype : calls
mmw/playbooks/idea-to-tickets -> design-pages : calls
mmw/playbooks/idea-to-tickets -> to-questionnaire : calls
mmw/playbooks/idea-to-tickets -> tdd : calls
mmw/playbooks/idea-to-tickets -> to-spec : calls
mmw/playbooks/idea-to-tickets -> to-tickets : calls
mmw/playbooks/idea-to-tickets -> dispatch : hands-off-to
to-spec -> skills.txt : configured-by
to-spec -> to-spec/references/revising-a-spec : reads-reference
to-spec -> to-spec/references/several-specs : reads-reference
to-spec -> verify-ticket : runs-script
to-spec -> ui-acceptance : runs-script
to-spec -> write-screen-contract : re-enters-at
to-spec -> wayfinder : re-enters-at
to-spec -> docs/agents/domain.md : configured-by
to-spec -> mmw : hands-off-to
to-tickets -> skills.txt : configured-by
to-tickets -> to-spec : re-enters-at
to-tickets -> to-spec/references/revising-a-spec : reads-reference
to-tickets -> to-tickets/references/ambiguity-scan : reads-reference
to-tickets -> to-tickets/references/cutting-interface-tickets : reads-reference
to-tickets -> to-tickets/references/person-ticket : reads-reference
to-tickets/references/cutting-interface-tickets -> ui-acceptance : reads-reference
to-tickets -> verify-ticket : runs-script
to-tickets -> docs/agents/triage-labels.md : configured-by
to-tickets -> mmw/principles/silence-is-never-a-pass : cites-principle
to-tickets -> mmw : hands-off-to
triage -> triage/references/pipeline-issues : reads-reference
triage -> triage/AGENT-BRIEF : reads-reference
triage -> triage/OUT-OF-SCOPE : reads-reference
triage -> to-tickets/references/person-ticket : reads-reference
triage -> grilling : calls
triage -> domain-modeling : calls
triage -> docs/agents/triage-labels.md : configured-by
triage -> docs/agents/issue-tracker.md : configured-by
triage/references/pipeline-issues -> verify-ticket : runs-script
triage/references/pipeline-issues -> dispatch : runs-script
triage/references/pipeline-issues -> to-tickets : reads-reference
triage/references/pipeline-issues -> dispatch : hands-off-to
triage/references/pipeline-issues -> mmw/principles/the-tracker-is-the-state : cites-principle
wayfinder -> grilling : calls
wayfinder -> domain-modeling : calls
wayfinder -> prototype : calls
wayfinder -> research : calls
wayfinder -> wayfinder/references/interface-and-remake : reads-reference
wayfinder/references/interface-and-remake -> design-pages : hands-off-to
wayfinder/references/interface-and-remake -> write-screen-contract : hands-off-to
wayfinder -> docs/agents/issue-tracker.md : configured-by
grill-me -> grilling : calls
grill-with-docs -> grilling : calls
grill-with-docs -> domain-modeling : calls
domain-modeling -> domain-modeling/CONTEXT-FORMAT : reads-reference
domain-modeling -> domain-modeling/ADR-FORMAT : reads-reference
prototype -> prototype/LOGIC : reads-reference
prototype -> prototype/UI : reads-reference
prototype -> prototype/EXP : reads-reference
prototype/EXP -> prototype/evidence-page : reads-reference
improve-codebase-architecture -> codebase-design : calls
improve-codebase-architecture -> grilling : calls
improve-codebase-architecture -> domain-modeling : calls
improve-codebase-architecture -> diagram-design : calls
improve-codebase-architecture -> improve-codebase-architecture/HTML-REPORT : reads-reference
codebase-design -> codebase-design/DEEPENING : reads-reference
codebase-design -> codebase-design/DESIGN-IT-TWICE : reads-reference
tdd -> codebase-design : calls
diagnosing-bugs -> diagnosing-bugs/scripts/hitl-loop.template.sh : runs-script
wizard -> wizard/template.sh : runs-script
wait-what -> wait-what/VISUAL : reads-reference
wait-what/VISUAL -> diagram-design : calls
teach -> teach/FORMAT-files : reads-reference
setup-matt-pocock-skills -> setup-matt-pocock-skills/seeds : reads-reference
dispatch -> mmw : hands-off-to
```

最后一行是 `dispatch.sh check` 报告消费仓库 `AGENTS.md` 缺指向 `mmw` 的行（R4 D1.4），列在这里是因为它与 J2 共同保证那一行存在。

**删掉的边**（今天存在，新架构没有）：`to-spec -> to-tickets : hands-off-to`、`to-tickets -> dispatch : hands-off-to`、`grill-with-docs -> to-spec : hands-off-to`、`wayfinder -> to-spec : hands-off-to`、`triage -> to-spec : hands-off-to`、`triage -> to-tickets : hands-off-to`、`improve-codebase-architecture -> to-spec : hands-off-to`、`prototype/UI -> design-pages : hands-off-to`。它们都换成了 `mmw` 或 `idea-to-tickets` 出发的边。

---

## 5. 不动清单

| 部件或段落 | 理由 |
|---|---|
| `grilling` 全文（含本仓第 28 行与第 30–44 行） | 天然整体（N5 §8 第 1 条）；第一性原理块是用户裁定的原文摘录（Memory `09af4c99`，N5 §7 引）；改变能力，不是流程写入 |
| `grill-me` | 只有宿主中立改写（a 类） |
| `domain-modeling` 三份文件 | 与上游逐字节相同（N5 §5 开头） |
| `codebase-design` 全文（含「This skill is a reference, not a process」） | 那句防止它被当流程跑（e 类）；词汇表天然整体 |
| `research`、`diagnosing-bugs`（含 `hitl-loop.template.sh`） | 与上游逐字节相同；B6 由 `## Routes` 处理，不改 `diagnosing-bugs` |
| `wizard`（含 `template.sh`）、`teach`、`wait-what`（含 `VISUAL.md`）、`handoff` | 单一能力，改动都是能力修正或宿主中立（N5 §5.2）；没有流程段要搬 |
| `to-questionnaire` 全文与调用开关 | `idea-to-tickets` **Someone else knows** 按名调用，推导结果仍是模型可触发 |
| 7 个用户触发技能的开关（本单元全部 7 个：`setup-matt-pocock-skills`、`grill-me`、`grill-with-docs`、`handoff`、`teach`、`improve-codebase-architecture`、`wait-what`） | 逐个核对：都只被「告诉用户运行」点名或不被点名，推导结果与现状相同 |
| `setup-matt-pocock-skills` 全部文件（种子只加 J3 一句） | e 类；U4 不放这里（J2） |
| `prototype` 的 `SKILL.md` 六条规则、`LOGIC.md`、`EXP.md`、`evidence-page.md`、`UI.md` 除 `## Next` 外 | 规则 1 与 `## State list` 的理由见 F2；其余是能力改变 |
| `wayfinder` 的 `## Notes` effort 目录名 | 跨技能数据约定（`prototype` 规则 1 读它），模板是唯一写入点；移走没有第二个调用方，也不减少重复 |
| `wayfinder` 第 4 步指向 `references/interface-and-remake.md` 与该 reference 全文 | 按本技能自身输入（目的地有无界面）选 reference，是能力内部（R4 D5.1）；让 mode 伸进 wayfinder 第 4 步会成为按步骤编号引用（L7 C.6 信号 8） |
| `wayfinder` 第 5 步 research 子代理交代、`## Ticket Types` 宿主中立改写 | e 类（防嵌套派发）与 a 类 |
| `triage` 第 70 行、第 22 行、`## Roles`、免责声明末行、`AGENT-BRIEF.md`、`OUT-OF-SCOPE.md` | 见 C8、C9 |
| `triage/references/pipeline-issues.md` 除 C4、C6、C7 外 | 本仓写的旁加 reference，已经是 d 类的正确形态；`## ready-for-agent` 末段交给 `dispatch` 取决于本技能自身的判定，属能力内部 |
| `to-spec` 第 1–4 步、模板、两份 reference；`to-tickets` 第 1–8 步（除第 8 步末句）、模板、三份 reference | 天然整体（N4 §8）；分叉只是整体搬家 |
| `to-spec` 第 8 行、`to-tickets` 第 12 行、`triage` 第 43 行、`wayfinder` 第 24 行的 setup 指针 | 有意的同句（SSR `## Upstream examples` Hand-offs 行把它当范例，N4 R15） |
| `to-tickets` 第 8 步第一条「再跑一次 `--lint`」 | N4 R2 称它与 `--publish --drafts` 末尾的 lint 重复执行；本轮没有读 `run_publish_drafts` 实现，不采用，放进第 8 节 |
| `improve-codebase-architecture` `### 1`–`### 3`、`HTML-REPORT.md`、`### 4` 留下的部分 | 能力换底（`diagram-design`）与 e 类 |
| `docs/agents/triage-labels.md`、`domain.md`、`issue-tracker.md` 除 L1 外 | 见 L2–L4 |
| 上游说明页 `mmw-v2/upstream/docs/engineering/*.md` 与技能正文矛盾处（N4 R11、R12） | 不装进宿主；上游原样 |

---

## 6. 形式拆散自查（L7 C.6 十一个信号）

1. **没有先确认已有组件不是归宿。** 未触发。`idea-to-tickets` 的每一句先找过已安装的家：结尾句（A3、B3、C3、D1、E1、F1、G1）是搬过来，不是新加；`ask-matt` 的内容（K1–K5）今天没有已安装的家（N10 §10.1 grep 已核实）。`research` 那一句用的是现有技能。
2. **新增内容不改变决定。** 未触发。每行 `## Routes` 改变去处；`## Where you are` 每行改变从哪一步开始；**Grill** 的 `research` 一句改变结果是否成为可引用的文件；「想整理代码架构」一行把请求从 `codebase-design`（「a reference, not a process」）改送到 `improve-codebase-architecture`。
3. **重复已有的、位置得当的指引。** 触发一处，保留。**Grill** 一步复述了 `grill-with-docs` 前两句（读 `grilling` 与 `domain-modeling`、写 `CONTEXT.md`）。原因：`grill-with-docs` 是用户触发，Claude Code 上模型够不到（R4 V1）；改成点名它，推导规则会把它翻成模型可触发，重新引出与 `grilling` 抢请求的问题（`merge-notes/grill-with-docs.md` 第 11 行）。复述两句是三个办法里代价最小的。
4. **本可由机制强制的规则写成文字。** 未触发。开关由推导规则加 lint；「告诉用户运行」的写法由 lint 识别；**Spec** 的上下文门槛要判断，脚本查不了。
5. **playbook 只调一个技能。** 未触发。只建 `idea-to-tickets`，它调九个技能，有所有权、门槛与交付物。
6. **reference 每次都读、只有一个调用方、读者是本代理。** 未触发。`phase-boundaries.md` 只在阶段边界读，有 `mmw` 与 `idea-to-tickets` 两个调用方。C4 移进 `pipeline-issues.md` 的一段只在流水线 child 分支读。
7. **原则说不出改变哪个决定。** 未触发。本单元不建原则，只加引用。
8. **拆完需要按步骤编号引用。** 未触发。`## Routes` 按步骤名（**Spec**、**Who checks**）引用 playbook；A4 在 `to-spec` 里写「引用是一张已分诊的 issue 时」，不写 triage 的步骤号；D1 的交接由 Routes 行写「map 清空后」，不写 wayfinder 第 6 步。
9. **拆出的内容没有第二个调用方、也不减少重复。** 未触发。C4、A4 只有一个读者，但收益是 G3（上游回到原文）；K1 有两个调用方；A3、B3、C3、C5、C6、D1、E1、G1 都减少同一条顺序的家（G1）。
10. **把单入口固定流程拆成三层。** 未触发。`to-spec`、`to-tickets`、`triage`、`wayfinder`、`prototype` 都保持一个技能，内部一字不拆。
11. **把只在流程之间复用的内容做成能力技能。** 未触发。`idea-to-tickets` 是 `mmw` 目录里的文件，不是技能；`phase-boundaries` 是 reference。

---

## 7. 待用户决定

本单元没有新的产品决定。以下是 R4 已有决定在本单元的具体可见效果，第 4 批落地前请确认（R4 §11 批次表已要求 owner 确认第 4 批）：

1. **直接斜杠进入时结尾不再提示 MMW 的下一步。** 受影响的是 `/grill-with-docs`（不再说「下一步 `to-spec`」）、`/prototype` 的 UI 分支（不再说「交给 `design-pages`」）、`/wayfinder` 清图时（只说「map 已清」，不再说「新会话跑 `to-spec` 再 `to-tickets`」）、`/improve-codebase-architecture`（只说「本技能不改代码」）、`/triage` 判为 agent-ready 时（贴完 brief 即停；`## Quick state override` 改问「要不要写 agent brief」）。`/to-spec`、`/to-tickets` 结尾改成「回到派你来的 playbook；没有就由 `mmw` 路由」。`mmw` 被加载时，这些下一步由它给出；没被加载时，会话停在这里，不会自己做下一步。
2. **外来 issue 与获批 retro 提案的关闭时点不变，执行者从 triage 会话换成发布 spec 的会话。** tracker 上看到的评论与关闭动作相同（A4、C6）。

---

## 8. 未确定

| # | 问题 | 需要什么实测或阅读 |
|---|---|---|
| T-D2 | `wayfinder` 去掉 `mmw:map` 后，charting 的 agent 是否照 tracker 文档 `## Wayfinding operations` 的命令打上 `mmw:map`。漏打的后果是开夜时 `dispatch.sh` 第 1674 行拒绝路由这份 spec（「native parent … has no mmw:map label」），会被发现，但发现得晚 | 在隔离测试 home 用假 tracker 跑一次 `/wayfinder` 画图，看 map 的 label；不过就把 `mmw:map` 按 e 类留在 `wayfinder`，D2 取消 |
| U-F2 | R4 D5.3 d 类的前提是否要补「每个入口都会读到旁加 reference」 | 这是对 R4 规则的细化，本文按工程判断采用；若 R4 作者另有理由把 `prototype` 规则 1 移出，需要说明 wayfinder 入口怎样读到它 |
| U-B | `to-tickets` 第 8 步第一条是否与 `--publish --drafts` 的内部 lint 重复执行（N4 R2） | 读 `verify-ticket.py` `run_publish_drafts` 全文，确认它对已发布 spec 跑的 lint 是否看得到 label、子票与阻塞边；若是，删第 8 步第一条（G1），作为普通票 |
| T1 | 第 4 批的全部项（A3、A4、B3、C3、C5、C6、D1、E1、F1、G1）以 R4 T1 通过为前提 | R4 §16 T1 |
| T6 | `to-spec`、`to-tickets` 分叉并恢复原文后，`git subtree pull` 能否零冲突 | R4 §16 T6 |
| T8 | `idea-to-tickets` 的 `## Where you are` 能否只凭 tracker 与仓库判出每一行（例如「带 `## Agent Brief`、判为 agent-ready、仍开着的 issue」没有专门 label，要读评论） | R4 §16 T8 的走查里加一个 triage 判为可做后的场景 |
| K9 | `phase-boundaries.md` 与 `## Routes` 里「告诉用户运行 `/X`」的写法能否被接线 lint 与「调用」区分开 | 写 lint 第 3 类时统一一种写法，并给反例测试 |
| — | 分叉后删掉 `agents/openai.yaml`，Codex 上技能列表的显示名是否变化（只影响显示，推断） | 在 Codex 会话里看一次技能列表 |

没有读的原文：`verify-ticket.py` 的 `run_publish_drafts` 实现、`pull_design.py` 解析 `## State list` 的代码（沿用 N5 §3.1 的核实）、`wizard/template.sh` 第 40–150 行、`teach` 的四份格式文件、`to-tickets/references/cutting-interface-tickets.md` 与 `ambiguity-scan.md` 的正文（只读了标题与开头，它们整体不动，结论不依赖正文）。

采用的清点结论与核实：N4 §5 上游行数、§6 issue 作者统计、§8 天然整体；N5 §5 diff 行数、§5.3 过时条目；N10 B1–B11、R2、R4。其中 B6 的交接、B10 的改写、`Context hygiene` 与 `PHASE-BOUNDARIES.md` 的上游出处、`mmw:map` 的各处出现、ADR 0001 第 20 行、`triage` 第 5 步与 `wayfinder` 第 6 步的上游原文、`merge-notes/README.md` 第 20–24、34–36 行，本轮都回到原文核实过。N11 标出的错误（N3、N6 把 `ask-matt` 当作活的入边）本文没有采用。
