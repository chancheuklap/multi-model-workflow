# 派工简报模板

简报是工人唯一的工作来源，是封闭清单。规则逐字取自 unlazy `references/orchestration.md` @754d9a6「Driver loop」第 4 条（副本：`docs/specs/landing-orchestrator/unlazy-orchestration-blueprint.md`）：

> **Dispatch ready leaves.** Give each leaf only the shared contract, its exact ownership and dependencies, its own ledger, and the four-pass completion rule. Do not leak unrelated leaf histories.

本仓库的对应物：leaf = 票；shared contract = 规划者计划的「契约」节；ownership and dependencies = 票全文里的 What to build 与它的原生阻塞边；its own ledger = 票正文里的验收关卡（ADR 0022，关卡在票里，没有独立账本）；four-pass completion rule = implement 技能「Finishing a ticket」的九步。兄弟票的历史一律不进简报。

依赖是上下文接力，不只是顺序。逐字取自 pstack `orchestrate.md` @46125561「The brief」：

> CONTEXT      pointers to files and PRs; upstream reports pasted in full when this unit
>              depends on them, because workers cannot see siblings

> A dependency is a context relay, not just ordering: undeclared upstream context makes the worker guess. Missing fields are a refuse-to-spawn condition.

五段缺一段就不派发。

## 正文

```
你是票 #<票号> 的工人。按下面五段工作；简报之外不要找别的指令，也不要等人回答——整夜没有人。

## 1. 契约

<规划者计划评论「### 契约」节的全文，原样粘贴>

## 2. 票全文

<`gh issue view <票号> --comments` 的全部输出，含 Parent、What to build、Acceptance criteria 的每条关卡（CHECK/EXPECT 或 MANUAL）>
<规划者计划评论「### 简报定制段」里写给这张票的那一段，原样粘贴；没有就省略>

分支：ticket/<票号>-<slug>。worktree 已经建好，你就在里面。
完成规则：按 implement 技能「Finishing a ticket」九步走完，直到票关闭。关卡通过要附 EVIDENCE，勾选不算数。

## 3. 上游产出摘录

<对该票每条原生阻塞边指向的上游票：票号、标题、PR 链接、复验判决评论、以及规划者计划标为「关键产出」的内容全文。一张上游票一小节。没有上游票就写「无上游票」。>

## 4. 纪律块

<按宿主能力送达，见下文「纪律块的送达」>

## 5. 汇报格式

工作结束时（票关闭、或你被卡住、或做不下去），最后一条回复只写下面这些，逐项：

REPORT       status, branch, head SHA, PRs, verdict, what you actually ran, deviations,
             suggested follow-ups

读法：status 取 done / blocked / failed 之一；verdict 写你自己跑关卡的结果（每条 pass/fail 与 EVIDENCE），复验者的判决不由你写；blocked 时把卡住的问题写成一句话，并列出你看到的选项。
```

## 纪律块的送达

纪律正文只有一份：`mmw-v2/hooks/discipline/worker.md`（相对本技能目录是 `../../hooks/discipline/worker.md`）。简报里不另写，按工人宿主的能力送达：

- 宿主 CLI 有单次注入系统提示的参数（grok 的 `--rules`）：在 `herdr agent start … -- --rules "$(cat <worker.md>)"` 时注入，简报第 4 段写「纪律已随系统提示送达」。每轮重派（自动修一轮）时 `agent prompt` 的正文再贴一次全文——长跑指令会漂移。
- 宿主 CLI 没有单次注入参数（cursor）：第 4 段直接粘贴 `worker.md` 全文，每轮 prompt 都贴。
- 宿主装了本仓库的 hook 层（claude 及其他由 `install.sh` 覆盖的宿主）：SessionStart 已注入，第 4 段写「纪律由 hook 层送达」。

REPORT 那两行逐字取自 pstack `orchestrate.md`「The brief」的 `REPORT` 字段。
