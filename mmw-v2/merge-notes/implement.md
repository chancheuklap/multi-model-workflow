# implement

源目录：`mmw-v2/upstream/skills/engineering/implement/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 第一句之后的开工段 | 我们改的：开工第一步跑 `verify-ticket.py <n> --preflight`——分支、未提交的 tracked 改动、票的 state、`ready-for-agent` 标签、未关的 blocker、assignee 六项核对，六项全过由它认领；打印 `NOT_READY` 就停，原因已由脚本评论到票上，不再写第二遍。六项逐项点名，是因为 `verify-ticket.py` 的 `refusals()` 就是这六条：worker 撞上标签或 assignee 那两条时，要认得出这是守卫的正常拒绝而不是脚本坏了。之后核对标题与 What to build 同一片、`## Owns` 每条 glob 匹配现存路径或标 `(new)`，旧票没有 Owns 就从 Seam 与 Parent 指名小节推导并评论到票上。理由：认领与前置核对是固定操作，交给脚本比写成正文指令可靠；`## Owns` 是后加的节，旧票要补齐才有写界。上游加了同类前置检查 → 收上游措辞，`--preflight` 第一步与 Owns 核对保留 |
| 「开写之前先读」那一段 | 我们改的：票读全 → `## Read first` 逐份读到结论（research 的末节、prototype 选定的 artifact、从 Claude Design 下载的交接包、ADR 的 Decision），其中记录已拍板结论的条目是基线、基线是契约不是参考 → 沿 Parent 只读票指名的 Implementation Decisions 小节 + Testing Decisions + Out of Scope，不读 spec 全文 → 根 CONTEXT.md 词表。没有 `Read first` 的旧票退回读 spec `## Sources` 全部。理由：整份 spec 会淹掉票指名的小节；基线的契约地位防默默偏离。`## Read first`、`## Seam` 是我们在 `to-tickets` 模板里加的节名，`## Sources` 是 `to-spec` 里加的，改那边就同步改这里。上游自己写了开写前的读取步骤 → 收上游，读法收窄与基线是契约保留 |
| 说出 seam 那一段 | 我们加的：seam 抄票的 `## Seam`；票没有这节时从 spec Testing Decisions 推出并先评论到票上再动手。上游有同类要求 → 收上游，「先写回票」这条保留 |
| 说出 seam 与 `/tdd` 之间的写码纪律段 | 我们加的：七条动作——`Read first` 里每件基线是契约，装不下或两件基线矛盾就在 spec 下开 sub-issue（`needs-triage`），不默默改基线、不默默绕过；改函数前 grep 每个调用方、修共用处，加分支或 guard 前先点名并删掉它让其多余的分支或文件；写 helper 前先在仓库与 `Read first` 找现成；加文件、依赖、配置前说出已有的为何不够；安全、防数据丢失、无障碍与票里明确要的（What to build、每条 AC、基线、Seam 接口）不许简化；收尾写 `skipped: [X], add when [Y]`；Owns 两档——为过 AC 不得不改的范围外文件照改、由收尾评论 `Outside Owns:` 记录，顺手想改的不改、开 sub-issue。措辞全部是动作 + 票字段，不写原则散文——散文措辞在对照实验里无效。上游加了写码期间的纪律段 → 收上游措辞，这七条并进去 |
| 「Once done」之后的收尾七步 | 我们改的：自跑 `verify-ticket.py <n>`（同一条标准至多三轮，第三轮写 `ABANDON: AC<n> failed`）→ 派 verifier（prompt 只有 `verify #<n>`，不派第二次）→ `dispatch.sh <n> reviewer <起点>` 起 reviewer、`dispatch.sh wait <n> "^REVIEW " 1800` 等评论（一轮、修一轮、不复审；完成判据是评论在票上；超时跳过这一轮；修 finding 受写码纪律七条同样约束，reviewer 的 suggestion 是加东西时先找可删的）→ Audit（重读票与 Read first，每条 AC 追到 EVIDENCE，重数 Counts）→ 把只等人拍一句话的标准切成 decision 类 sub-issue、收尾评论写成草稿文件（固定格式：首行 ALL MET / HANDOFF REQUIRED、`Branch: … Commit: … PR: …` 一行且没有 PR 时写 `PR: none — <理由>`、Post-verdict:、每条 AC 四行、Outside Owns:、skipped:、Sub-issues opened: 收本票工作期间开的四类 sub-issue（基线装不下、Owns 之外的顺手改动、票外 review finding、`ABANDON: decision`）、Counts:、Decisions I made on my own）→ push 开 PR → `--closeout` 由脚本贴评论并关票或换标签，worker 不亲手关票换标签（hook 拦）。三个 ABANDON kind 各有准入：failed 要票上数得出三条 self-run、stuck 不看轮次、decision 开 sub-issue 不挡 ALL MET。理由：关票是一道门不是一个动作，上游三步（评论证据 → PR → 关票）被这七步吸收。这三个值写一行、没有 PR 时把理由接在 `PR: none` 后面，是为了早上读票的人和以后想解析它们的脚本只面对一种形状；`Sub-issues opened:` 四类逐条点名，是因为正文里要求开 sub-issue 的地方就是这四处，只说「上面两类」会漏掉另外两处。上游改收尾 → 收上游措辞，七步顺序、三轮上限、`--closeout` 关票门必须保留 |
| frontmatter 的 `disable-model-invocation` 与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation` | 我们删的：上游两处都设了只许人触发，我们要模型能自己派 implement，所以两处一起删。上游若再带回来 → 仍然删 |

## Closeout: resume after a re-prompt

One sentence added to the "Once done" paragraph: a ticket that already carries a `self-run`, `VERDICT` or `REVIEW` comment is resumed at the step after the newest of them. `board.py` re-prompts a stopped worker with the dispatch line only, so the skill has to know it may be entering the closeout mid-way. On the next upstream pull keep this sentence with the seven-step closeout.
