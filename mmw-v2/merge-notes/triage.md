# triage

源目录：`mmw-v2/upstream/skills/engineering/triage/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `description` 里 `record what the evaluation established` 一句 | 上游写 `write agent-ready briefs`，我们改成 `record what the evaluation established`：本仓的 `ready-for-agent` 出口是 landing pipeline（下表第 5 步一条），triage 不写 brief。上游改这一行 → 收上游对前半句的措辞，这一句仍按我们的 |
| frontmatter 的 `description` 结尾那两句 `Use when issues or external PRs you did not create are waiting to be judged.` 与 `Not for tickets this repository's own pipeline produced, which are already agent-ready.` | 本仓补的「什么时候用我」：host 启动时只扫这一行，一份只说「我是什么」的技能在列表里挑不出该不该用它；判据取自 `ask-matt/SKILL.md` 讲 triage 那一条（`Triage is only for issues **you didn't create**` 与 `don't triage them`）。上游改这一行 → 收上游对前面部分的措辞，这两句保留 |
| Roles 那张表下面「label 映射没给你就去装」那一句、`## Triage a specific issue or PR` 开头 `The maintainer invokes …` 那一句、第 4 步 Grill、第 5 步 `ready-for-agent` 一条，与 `## Quick state override` 末句 | host 中立：技能名一律写成散文形式（指自己那一处写成 `this skill`），要词汇的第 4 步写成读 `grilling` 与 `domain-modeling` 两份技能的 `SKILL.md`。共同理由与三种替换写法见 [README.md](README.md#host-中立) |
| 第 5 步 `ready-for-agent` 一条：判断表的 `New work in this batch` 一行，与它下面 `When the issue is work from outside` 那一段 | 两处都把票的节数从句子里拿掉，改成指 `<issue-template>`：判断表那一行说「模板里每一节都填」，下面那一段说形状由 `<issue-template>` 定、由 `verify-ticket.py` 读。理由是节数由 `to-tickets/SKILL.md` 的 `<issue-template>` 一处定，抄进散文就是一份会过期而无人发现的副本——本仓 `CONTEXT.md` 把 `七节`、`八节` 列在 `<issue-template>` 的 `_Avoid_` 上就是这个原因。本仓的模板删掉了 `## Worker` 与 `## Blocked by` 两节，节数一律以 `to-tickets/SKILL.md` 的 `<issue-template>` 为准。上游改这两处 → 收上游对这两句其余部分的措辞，但不收任何节数：upstream 对一张票长什么样有它自己的一套，它写几节都不是本仓的节数，而这两处一旦重新带上数字，就又是一份要维护的副本 |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓库要求这个技能模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用这个技能。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| 开头「must **start** with this disclaimer」 | 改成放 ticket comment 最后一行，并写出理由：ticket comment 的 first line 是 landing pipeline 的 protocol slot（`REVIEW `、`ALL MET`、`HANDOFF REQUIRED:`、`VERDICT`、`self-run` 都靠 first line 认）。免责声明占了 first line，`dispatch.sh wait` 与 closeout 就都读不出这条 comment。上游改这句 → 收上游的措辞，位置留在末行 |
| Roles 的 `ready-for-human` 一条，与第 5 步 Apply the outcome 的 `ready-for-human` 一条 | 改成与 `to-tickets` 同一套：kind 是 `reaction` 或 `reach`，ticket 只有 the five things，清单本身只写在 `to-tickets` 技能的 `references/person-ticket.md` 一处，这里指过去，不再抄。上游那四个理由（judgment calls、external access、design decisions、manual testing）删掉——`merge-notes/to-tickets.md` 已经判定这四个词是混的，「判断」大半归了 code review，「设计决定」是 the five questions 里的第五条。理由：user 在 morning 打开的是同一个 `ready-for-human` queue，两处出的 ticket 必须同一个形状。上游改这一条 → 不收，除非它自己也换成两类 |
| Roles 段「Every triaged issue should carry exactly one category role and one state role」 | 补一条例外：本仓自己规划的 ticket（spec 底下的 ticket、decision ticket）只带 state role、不带 category，出处指 `docs/agents/triage-labels.md`。本仓的 label 映射表里根本没有 `bug` / `enhancement` 两行。上游改这句 → 收上游，例外保留 |
| 「Show what needs attention」之后新增的一节「A ticket handed back by this repo's own pipeline」 | 我们加的整节：`needs-triage` 不只承接外来 issue，还承接本仓 agent 没做完的 ticket。最新 ticket comment 的 first line 是 `HANDOFF REQUIRED` 的（流水线把票交回 `needs-triage` 只走 `--closeout` 这一条路，别的 first line 都不是交回），读那条 comment 与 ticket 上的 `self-run` / `VERDICT` / `REVIEW` 痕迹，不按 reporter（上游对 user 的叫法，本节沿用同一文件第 3 步的措辞）的步骤复现、不查 `.out-of-scope/`。上游若自己写了这条支路 → 收上游，删掉我们这一节 |
| 第 1 步 Gather context | 我们加的：先读父 issue（`gh issue view <m>` 的 `parent:` 行，或 `gh api repos/{owner}/{repo}/issues/<m> --jq .parent_issue_url`；REST 对象没有 `parent` 字段），父是 ticket 就读那张票的 `self-run` / `VERDICT` / `REVIEW` 轨迹，不重现。理由：worker 开的 `needs-triage` 挂在本票下，出处在父票的收尾轨迹里。上游改 Gather context → 收上游措辞，先读父 issue 这句保留 |
| 第 5 步 Apply the outcome 的 `ready-for-agent` 一条 | 改成入 landing pipeline，不在这里 publish：判定这张 issue 该由 agent 做之后，用 `to-spec` 技能写一份 spec、或经它「Revising a published spec」那一步扩一份已发布的 spec，并把这张 issue 列为来源，再用 `to-tickets` 技能 publish ticket；`ready-for-agent` label 打在那些 ticket 上、不打在这张 issue 上，这张 issue 由 spec 的 publish 步骤关掉并挂到 spec 底下；父是 ticket 时按第 5 步表里的三去向改挂或转移（另一张票 / spec / 转到 toolbox 仓），命令在 `SKILL.md` 里，这里不抄。上游取舍：上游的 `ready-for-agent` 只改标签，我们要它同时回答「在哪做」 |
| `## Quick state override` 末句 | 上游问「要不要写 agent brief」，我们改成问「要不要现在就走 `to-spec` 技能再走 `to-tickets` 技能」，与第 5 步 `ready-for-agent` 一条同一个出口。上游改这一节 → 收上游措辞，末句仍指向 landing pipeline |
| 第 5 步 `**Apply the outcome:**` 标题行 | 注明 the four outcomes 是 `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`，留在 `needs-triage` 不算 outcome。`CONTEXT.md` 与 `docs/agents/triage-labels.md` 都写「one of the four outcomes」，而这一节下面列了五条，读者数不出是哪四个。上游改这一节 → 收上游的条目，「四个」这个数与 `needs-triage` 不算出口这句保留 |

### AGENT-BRIEF.md

| 段落 | 我们的意图 |
| --- | --- |
| 开头对 agent brief 性质的定义（上游写的是「the authoritative specification that an AFK agent will work from」），以及各条原则里对着 agent 说话的句子 | 改成：agent brief 是 evaluation 阶段贴在 issue 上的调查记录——复现结果、根因线索、什么算满足这个请求、建议哪个 outcome——是之后写 spec 的素材，不是派给 worker 的 ticket。理由：`ready-for-agent` 出口走 landing pipeline（见上表），worker 手上那张 ticket 由 `to-tickets` 技能 publish。agent brief 再自称权威的 spec，就有两份互相矛盾的 contract，而这一份还缺 `Seam` 与 `Owns`。模板与三份例子保留：它们记的内容照样是 spec 的输入。上游改这份文件 → 收上游的模板与例子，性质那几句仍然写成调查记录 |
| 开头那句对 agent brief 的定义、`Nothing is dispatched from an agent brief.` 一段、`**Good:**` 的第一个例子，与末段 `A finding nobody can check is an opinion.` | host 中立：这四处点技能名的地方一律写成散文形式，例子那句里的 `"When a user runs the triage skill with no arguments, …"` 连引号内的措辞一起改。共同理由见 [README.md](README.md#host-中立) |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |
