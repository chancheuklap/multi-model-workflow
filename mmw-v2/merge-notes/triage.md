# triage

源目录：`mmw-v2/upstream/skills/engineering/triage/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓库要求这个技能模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用这个技能。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| 开头「must **start** with this disclaimer」 | 改成放 ticket comment 最后一行，并写出理由：ticket comment 的 first line 是 landing pipeline 的 protocol slot（`REVIEW `、`ALL MET`、`HANDOFF REQUIRED:`、`VERDICT`、`self-run` 都靠 first line 认）。免责声明占了 first line，`dispatch.sh wait` 与 closeout 就都读不出这条 comment。上游改这句 → 收上游的措辞，位置留在末行 |
| Roles 的 `ready-for-human` 一条，与第 5 步 Apply the outcome 的 `ready-for-human` 一条 | 改成与 `to-tickets` 同一套：kind 是 `reaction` 或 `reach`，ticket 只有 the five things（Parent / 哪一类 / 看什么 / 什么算对 / Blocked by）。上游那四个理由（judgment calls、external access、design decisions、manual testing）删掉——`merge-notes/to-tickets.md` 已经判定这四个词是混的，「判断」大半归了 code review，「设计决定」是 the five questions 里的第五条。理由：user 在 morning 打开的是同一个 `ready-for-human` queue，两处出的 ticket 必须同一个形状。上游改这一条 → 不收，除非它自己也换成两类 |
| Roles 段「Every triaged issue should carry exactly one category role and one state role」 | 补一条例外：本仓自己规划的 ticket（spec 底下的 ticket、decision ticket）只带 state role、不带 category，出处指 `docs/agents/triage-labels.md`。本仓的 label 映射表里根本没有 `bug` / `enhancement` 两行。上游改这句 → 收上游，例外保留 |
| 「Show what needs attention」之后新增的一节「A ticket handed back by this repo's own pipeline」 | 我们加的整节：`needs-triage` 不只承接外来 issue，还承接本仓 agent 没做完的 ticket。最新 ticket comment 的 first line 是 `HANDOFF REQUIRED` / `WAKEUP LIMIT:` / `TIME LIMIT:` / `REDISPATCHED:` / `BLOCKED:` 的，读那条 comment 与 ticket 上的 `self-run` / `VERDICT` / `REVIEW` 痕迹，不按 reporter（上游对 user 的叫法，本节沿用同一文件第 3 步的措辞）的步骤复现、不查 `.out-of-scope/`。上游若自己写了这条支路 → 收上游，删掉我们这一节 |
| 第 5 步 Apply the outcome 的 `ready-for-agent` 一条 | 改成入 landing pipeline，不在这里 publish：判定这张 issue 该由 agent 做之后，用 `/to-spec` 写或扩一份 spec 并把这张 issue 列为来源，再用 `/to-tickets` publish ticket；`ready-for-agent` label 打在那些 ticket 上、不打在这张 issue 上，这张 issue 由 spec 的 publish 步骤关掉并挂到 spec 底下。理由：queue 里只能有一种 ticket 体。上游 `AGENT-BRIEF.md` 出的 agent brief 是 `**Current behavior:**` / `**Acceptance criteria:**` 那套粗体行，没有 `## Read first` / `## Seam` / `## Owns`，acceptance criterion 也没有 `CHECK:`；`implement` 按 fixed headings 读 ticket、`verify-ticket.py` 按 `CHECK:` 跑 acceptance criteria，两样都读不了 agent brief，而 `board.py` 只按 `ready-for-agent` label 取 ticket——agent brief 混进 queue 就是 night 里派出去一张没人验得了的活。the four outcomes 的名单不变；同一步 `ready-for-human` 一条的开头是「written here rather than routed」，不是上游的「not an agent brief」：agent brief 不从这个出口出。上游改这一条 → 不收，除非它自己也把这个出口接进 `/to-spec` → `/to-tickets` 的 publish 流程 |
| 第 5 步 `**Apply the outcome:**` 标题行 | 注明 the four outcomes 是 `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`，留在 `needs-triage` 不算 outcome。`CONTEXT.md` 与 `docs/agents/triage-labels.md` 都写「one of the four outcomes」，而这一节下面列了五条，读者数不出是哪四个。上游改这一节 → 收上游的条目，「四个」这个数与 `needs-triage` 不算出口这句保留 |

### AGENT-BRIEF.md

| 段落 | 我们的意图 |
| --- | --- |
| 开头对 agent brief 性质的定义（上游写的是「the authoritative specification that an AFK agent will work from」），以及各条原则里对着 agent 说话的句子 | 改成：agent brief 是 evaluation 阶段贴在 issue 上的调查记录——复现结果、根因线索、什么算满足这个请求、建议哪个 outcome——是之后写 spec 的素材，不是派给 worker 的 ticket。理由：`ready-for-agent` 出口走 landing pipeline（见上表），worker 手上那张 ticket 由 `/to-tickets` publish。agent brief 再自称权威的 spec，就有两份互相矛盾的 contract，而这一份还缺 `Seam` 与 `Owns`。模板与三份例子保留：它们记的内容照样是 spec 的输入。上游改这份文件 → 收上游的模板与例子，性质那几句仍然写成调查记录 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |
