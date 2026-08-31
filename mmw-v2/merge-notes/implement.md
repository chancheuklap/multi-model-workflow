# implement

源目录：`mmw-v2/upstream/skills/engineering/implement/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 第一句之后的开工段 | 我们改的：开工第一步跑 `verify-ticket.py <n> --preflight`——分支、未提交的 tracked 改动、票的 state、`ready-for-agent` 标签、未关的 blocker、assignee 六项核对，六项全过由它认领；打印 `NOT_READY` 就停，原因已由脚本评论到票上，不再写第二遍。六项逐项点名，是因为 `verify-ticket.py` 的 `refusals()` 就是这六条：worker 撞上标签或 assignee 那两条时，要认得出这是守卫的正常拒绝而不是脚本坏了。之后核对标题与 What to build 同一片、`## Owns` 每条 glob 匹配现存路径或标 `(new)`，旧票没有 Owns 就从 Seam 与 Parent 指名小节推导并评论到票上。理由：认领与前置核对是固定操作，交给脚本比写成正文指令可靠；`## Owns` 是后加的节，旧票要补齐才有写界。上游加了同类前置检查 → 收上游措辞，`--preflight` 第一步与 Owns 核对保留 |
| 「开写之前先读」那一段 | 我们改的：票读全 → `## Read first` 逐份读到结论（research 的末节、ADR 的 Decision、从 Claude Design 下载的交接包、prototype 叶子 `README.md` 读到它的 verdict），其中记录已拍板结论的条目是基线、基线是契约不是参考，且两类基线处理不同：交接包逐字照抄，prototype 按正式标准重写、保住 verdict 定下的形状 → 沿 Parent 只读票指名的 Implementation Decisions 小节 + Testing Decisions + Out of Scope，不读 spec 全文 → 根 CONTEXT.md 词表。没有 `Read first` 的旧票退回读 spec `## Sources` 全部。理由：整份 spec 会淹掉票指名的小节；基线的契约地位防默默偏离。prototype 那一项原先写的是「选定的 artifact」，而同一句里另外三项都指向一个打开就找得到的位置（研究文件的末节、ADR 的那一节、下载下来的整个目录），只有它指向「一块代码」，worker 打开叶子目录不知道是哪块；换成「叶子 README 读到它的 verdict」，与另外三项同构，位置由 `prototype` 技能规则 6 已经要求写的 verdict 给出，而照着哪一块写由 verdict 自己说，不必再写一条禁令去排除 HTML 外壳或 harness。两类基线的差别不写出来，worker 会对着一个 prototype 变体逐字抄，把原型阶段的粗糙一起抄进正式代码。`## Read first`、`## Seam` 是我们在 `to-tickets` 模板里加的节名，`## Sources` 是 `to-spec` 里加的，改那边就同步改这里。上游自己写了开写前的读取步骤 → 收上游，读法收窄与基线是契约保留 |
| 说出 seam 那一段 | 我们加的：seam 抄票的 `## Seam`；票没有这节时从 spec Testing Decisions 推出并先评论到票上再动手。上游有同类要求 → 收上游，「先写回票」这条保留 |
| 说出 seam 与 `/tdd` 之间的写码纪律段 | 我们加的：七条动作——`Read first` 里每件基线是契约，值、文案、状态与接口形状从基线抄而不是凭记忆重写，装不下或两件基线矛盾就在 spec 下开 sub-issue（`needs-triage`），不默默改基线、不默默绕过；过不了的检查用改代码或 abandon 那条标准来答，不弯基线、不弯 harness、不弯测试——这一款给的是正面动作接一句底线，而不是并排的第三个 never，且它指向的 abandon 就是同一份文件收尾第 1 步的三轮上限；改函数前 grep 每个调用方、修共用处，加分支或 guard 前先点名并删掉它让其多余的分支或文件；写 helper 前先在仓库与 `Read first` 找现成；加文件、依赖、配置前说出已有的为何不够；安全、防数据丢失、无障碍与票里明确要的（What to build、每条 AC、基线、Seam 接口）不许简化；收尾写 `skipped: [X], add when [Y]`；Owns 两档——为过 AC 不得不改的范围外文件照改、由收尾评论 `Outside Owns:` 记录，顺手想改的不改、开 sub-issue。措辞全部是动作 + 票字段，不写原则散文——散文措辞在对照实验里无效。上游加了写码期间的纪律段 → 收上游措辞，这七条并进去 |
| 「Once done」之后的收尾六步 | 我们改的：自跑 `verify-ticket.py <n>`（同一条标准至多三轮，第三轮写 `ABANDON: AC<n> failed`）→ 派 verifier（prompt 只有 `verify #<n>`，不派第二次）→ `dispatch.sh <n> reviewer <起点>` 起 reviewer、`dispatch.sh wait <n> "^REVIEW " 1800` 等评论（一轮、修一轮、不复审；完成判据是评论在票上；超时跳过这一轮；修 finding 受写码纪律七条同样约束，reviewer 的 suggestion 是加东西时先找可删的）→ Audit（重读票与 Read first，每条 AC 追到 EVIDENCE，重数 Counts）→ 把只等人拍一句话的标准切成 decision 类 sub-issue、收尾评论写成草稿文件（固定格式：首行 ALL MET / HANDOFF REQUIRED、`Branch: … Commit: … PR: …` 一行且没有 PR 时写 `PR: none — <理由>`、Post-verdict:、每条 AC 四行、Outside Owns:、skipped:、Sub-issues opened: 收本票工作期间开的四类 sub-issue（基线装不下、Owns 之外的顺手改动、票外 review finding、`ABANDON: decision`）、Counts:、Decisions I made on my own）→ `--closeout` 由脚本贴评论并关票或换标签，worker 不亲手关票换标签（hook 拦）。三个 ABANDON kind 各有准入：failed 要票上数得出三条 self-run、stuck 不看轮次、decision 开 sub-issue 不挡 ALL MET。理由：关票是一道门不是一个动作，上游三步（评论证据 → PR → 关票）被这六步吸收；PR 那一步整个退场，见下方「No pull request, and no push」。这三个值写一行、没有 PR 时把理由接在 `PR: none` 后面，是为了早上读票的人和以后想解析它们的脚本只面对一种形状；`Sub-issues opened:` 四类逐条点名，是因为正文里要求开 sub-issue 的地方就是这四处，只说「上面两类」会漏掉另外两处。上游改收尾 → 收上游措辞，六步顺序、三轮上限、`--closeout` 关票门、不开 PR 必须保留 |
| frontmatter 的 `disable-model-invocation` 与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation` | 我们删的：上游两处都设了只许人触发，我们要模型能自己派 implement，所以两处一起删。上游若再带回来 → 仍然删 |

## Waiting on the reviewer carries no number

`dispatch.sh wait <n> "^REVIEW "` passes no seconds: the timeout lives in the script
(`WAIT_DEFAULT_SECONDS`), and a number in the skill text is a number a worker shrinks —
one did, and skipped a review its reviewer was still writing. Upstream brings a number
back → drop it again.

## No pull request, and no push

Upstream's step 6 pushed the branch and opened a pull request. This pipeline opens
none, and the step is gone: nothing here reads a pull request — `code-review` takes its
diff from git, the verifier reads the ticket and the worktree, and the closing gate
reads neither. What does read a branch is `dispatch.sh advance`, which merges it into
`git config branch.issue-<n>.mmw-base-branch` once the ticket closes, on this machine,
with no `gh` call at all. A pull request would only be a second place to remember to
merge and pull back from.

The `Branch: … Commit: … PR: …` line stays, with `PR: none — will be merged into <base
branch> by dispatch.sh advance`. It is written in the future tense on purpose: the
closing comment is written before the ticket closes, and the merge happens after.

Upstream brings the push or the pull request back → drop them again, and keep the
recorded base branch, which `advance` needs.

## Closeout: resume after a re-prompt

One sentence added to the "Once done" paragraph: a ticket that already carries a `self-run`, `VERDICT` or `REVIEW` comment is resumed at the step after the newest of them. `board.py` re-prompts a stopped worker with `continue` and nothing else, so the skill has to know it may be entering the closeout mid-way. On the next upstream pull keep this sentence with the six-step closeout.

## Where a failing `visual-parity.py` criterion is read

One sentence added to closeout step 1. That script prints a single `DIFF <scene> <viewport> <pct>% box=… — <reasons>` line; which reasons bring sub-lines out under them, and what `NEGATIVE CONTROL FAILED` means, are written only in the verify-ticket skill. Every other refusal in this closeout explains itself in its own stderr, so this is the one place the worker has to be sent elsewhere. Upstream rewrites step 1 → keep the pointer.
