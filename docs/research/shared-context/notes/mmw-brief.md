# MMW 简介（给调研 subagent 的背景，读完再开始）

MMW（multi-model-workflow）是一个人（产品 owner，不读代码）的多 agent 软件交付流水线，仓库在
`/Users/cheuklapchan/multi-model-workflow/.worktrees/rainbowfish`（只读，不要改任何文件）。只有 `mmw-v2/` 是活的。

## 流程

1. 白天：用户和 main agent 对话 → `wayfinder` 技能把大任务拆成 map（GitHub issue，含 Destination、Notes、Decisions so far、Not yet specified、Out of scope、`## Specs`）与决策票 → `to-spec` 写 spec（GitHub issue：Problem Statement / Solution / User Stories / Implementation Decisions 编号小节 / Testing Decisions / Out of Scope / Sources / Further Notes）→ `to-tickets` 切成竖切片票（GitHub sub-issue：`## Parent` `## What to build` `## Read first` `## Seam` `## Owns`（允许写的文件） `## Acceptance criteria`（每条 `CHECK:` 命令 + `EXPECT:` 输出行 + `EVIDENCE:`）），票之间用 blocking link。发布后 `--lint` 校验。
2. 夜里（`dispatch` 技能）：main agent `check` → `open <spec>` → `advance`。**多个 spec 可在同一仓库并行开夜**，一个仓库一个 relay 进程看多个 watch，每个 spec 一个 main agent。跨 spec 依赖是票上的 blocking link。
3. 每张票：`dispatch.sh start` 在 `.worktrees/issue-<n>` 起一个独立 worker 会话（host 可以是 claude/codex/grok/cursor/pi，runner 是 paseo/orca/herdr）。worker 跑 `implement` 技能：`--preflight` 认领 → 读票、Read first、spec 中 Parent 点名的小节、CONTEXT.md → 写代码 → `integrate` 合入 base branch 新进展 → 自跑验收 → 起 reviewer 会话（`code-review`：Standards/Spec/Tests 三轴，in-ticket 修一轮，out-of-ticket 开 `finding` 子票）→ `--decisions` → 起 verifier 会话（`verdict`：同一 commit 独立重跑全部验收）→ Audit → `--touched`（通知同 spec 下拥有被改文件的票）→ `--draft` → `--closeout`（关票门：`ALL MET` 或 `HANDOFF REQUIRED`）。
4. `advance` 把通过的票在专用 merge worktree 里合入 `origin/<base branch>`、跑仓库检查、fast-forward 推送；冲突或红检查 → `ticket.bounced` 交早间 triage。
5. frontier 空后 main agent 做收口轮：逐条 `route` finding 子票（自己修 / stale / 变成新票）→ `reverify` → `summary`（`NIGHT SUMMARY`）。用户验收后 `finish` 合回 project branch。
6. 早上：`needs-triage` 队列跑 `triage`（returned/bounced/regressed 票、contract/deferred/decision 子票），再看 `ready-for-human`。

## 关键不变量（ADR）

- 票的状态是票评论里 `<!-- mmw {...} -->` 事件块按评论顺序的 fold；事件只由脚本写，模型打字的不算（ADR 0019）。
- agent 之间靠事件唤醒，不许轮询；relay 把结果事件变成唤醒并要求 ack；watchdog 查沉默会话写 `worker.lost`（ADR 0010、0020–0022）。夜里没有时钟（0017）。
- tracker（GitHub）是事实权威（0001）；每道闸口拒绝时点名事实、给出路，沉默不算通过（0008）。
- base branch 以 origin 为准，先合再查再推（0023）；review finding 默认 main agent 自己修，四步门槛决定何时变票（0012）。
- 票的子票种类：finding（评审发现的票外缺陷）、contract（基线不成立）、deferred（票外顺手的改动）、decision（只有人能定，worker 先取默认）、fault（流水线自身坏了）。
- 票正文发布后不改；spec 正文可原地修订，改动原因写一条评论。
- 技能对所有 host 同一份文本，不按 host 分支。

## 已识别的缺口（本会话前面的调研结论，供参考，可质疑）

- A：一夜内学到的操作性知识（怎么起产品、哪个测试不稳、环境坑、verifier 修环境的办法）无处沉淀；worker 不读兄弟票，并行 spec 更读不到。
- `worker.touched` 只通知同一 spec；`## Owns` 不重叠检查只在单 spec 内做，没找到跨并行 spec 的检查。
- 没有跨夜 retro 从结果改进技能。
- 用户记忆里：同文件工单并行派出多次导致 bounce（#748、#750、#751），要求串成依赖链。

## 深入阅读入口（按需）

- `CONTEXT-MAP.md`，`docs/contexts/{tickets,ticket-run,night,toolbox,ui-acceptance,task-board}/CONTEXT.md`
- `mmw-v2/skills/dispatch/references/how-it-works.md`、`night.md`
- `mmw-v2/upstream/skills/engineering/{implement,to-spec,to-tickets,code-review,triage,wayfinder}/SKILL.md`
- `mmw-v2/skills/{verify-ticket,verdict,drive-target}/SKILL.md` 及其 `references/`
- `docs/adr/README.md`（ADR 索引）

## 本轮目标（用户原话要点）

让 MMW 更健壮、自动化回路更可靠、产出代码更符合设计初衷、落地返工更少完成度更高——让流水线里的 agent 像一个坐在同一办公室里齐心协力的软件工程团队。从 MMW 的设计意图出发，不为借鉴而硬套。

## 前一轮调研原始报告（可读，避免重复）

同目录下 `research-1-cursor.md`、`research-2-commercial.md`、`research-3-opensource.md`、`research-4-theory.md`。
