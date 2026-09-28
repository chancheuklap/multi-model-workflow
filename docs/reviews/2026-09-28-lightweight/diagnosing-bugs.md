# diagnosing-bugs

## 定稿（主 agent 复核）

**判断**：本仓一字未改，不改。它的灵魂完整，并有真实使用为证：agentflow #997 的夜间 worker 自己加载了它，先写出 4 条排好序、可以被证伪的假设，逐条核实，没有停下来问人。

要提醒以后修剪的人：`SKILL-SET-REVIEW.md` 的 no-op 检查会把 "Be aggressive. Be creative. Refuse to give up." 判成空话。它不是空话：这句决定了 agent 把力气集中花在第一阶段（造出一个会在这个 bug 上失败的命令）。`writing-for-agents` 定稿里的新原则覆盖了这一类句子。

上游原文的三处小问题（Phase 5 悬空的 "Flag this for the next phase"、`hitl-loop.template.sh` 由 agent 直接运行时第一步就退出、`ask-matt` 过期的交接说法）只登记，不改。

## 结论

`mmw-v2/upstream/skills/engineering/diagnosing-bugs/` 是一个本仓一字未改的上游技能：`SKILL.md` 138 行、1402 词，`scripts/hitl-loop.template.sh` 44 行，`agents/openai.yaml` 3 行；与最近一次上游 squash 提交 `5b1a4c51` 的树逐字节相同（`git diff "5b1a4c51:skills/engineering/diagnosing-bugs" "HEAD:mmw-v2/upstream/skills/engineering/diagnosing-bugs"` 无输出），所以 `mmw-v2/merge-notes/` 下没有它的说明是对的，不是遗漏。本仓加进来的部分为零，A 类（删除/改脚本）没有可删的，估计可删 0 词、0 行。它的"灵魂"是完整的：整篇围绕"先造出一个会在这个 bug 上变红的命令，再谈原因"这一个思想展开，每一阶段都给了目的和完成标准，而不只是步骤。真实使用证据（下文 B 节）显示，夜里的 worker 和白天的交互会话都按这个思想做对了事。只记录三处上游原文的小缺陷，都没有在真实使用中触发，建议都不改。

## A. 删除或改成脚本

没有。

理由：任务书把 A 类的重点放在本仓加的部分，这个技能里本仓加的部分为零（证据见"结论"里的 diff 命令）。按 `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md` `### Upstream skills`，上游原文只在"在工作流里会让 agent 做错"时才改；为了减字数删上游原文不提。下面"上游原文"三条是在这一标准下检查过、结论为不改的记录。

### 上游原文（检查过，建议不改）

| # | 位置 | 问题 | 触发过吗 | 为什么不改 |
|---|---|---|---|---|
| U1 | `SKILL.md` `## Phase 5: Fix + regression test` 第 120 行 "If no correct seam exists, that itself is the finding. ... Flag this for the next phase." | "the next phase" 已无所指。上游 changeset `mmw-v2/upstream/.changeset/user-invoked-skill-invocation.md` 记录了原先 Phase 6 把这一发现交给 `improve-codebase-architecture`，后被整段删掉（那个技能只能由用户点名触发）；这一句留了下来。 | 没有证据触发过。 | 紧跟的 `## Phase 6: Cleanup` 第 135 行 "Regression test passes (or absence of seam is documented)" 已经告诉 agent 该做什么（写下来）。在 MMW 里 `improve-codebase-architecture` 故意设成不能被模型触发（`mmw-v2/merge-notes/improve-codebase-architecture.md` 第 11 行正是担心 worker 夜里自己去触发它），所以这句悬空反而无害。 |
| U2 | `scripts/hitl-loop.template.sh` 第 4 行 "The agent runs the script; the user follows prompts in their terminal." 与 `SKILL.md` 第 35、64 行 | 描述与实际不符：agent 用自己的 shell 工具跑这个脚本时，标准输入不是用户的终端。我实测：不给标准输入直接跑，打印第一条提示后 `read` 读到 EOF，`set -euo pipefail` 让脚本以退出码 1 结束，用户什么都看不到；用管道喂入 `x\ny\nboom` 才走完并打印 `ERRORED=y`、`ERROR_MSG=boom`。 | 没有。查了 `~/.codex/sessions` 下所有提到 `hitl-loop` 的会话，只有 2026-08-07、08-09 两次上一代技能重建时读过它，没有一次在诊断中真正跑它；`~/.claude/projects` 里没有任何会话调用过这个技能。 | 它是第 10 条、明写 "Last resort"；夜里没有人可问，人工步骤由 `ui-acceptance` 技能 **Five rules while the product is running** 的第 3、4 条路由（`mmw-v2/upstream/skills/engineering/implement/SKILL.md` 第 97 行指过去），worker 不会走到这里。白天真走到时，agent 看到退出码 1 会自己改成请用户在自己终端里跑。改它等于改上游，收益只落在一个从未发生的路径上。可以作为上游 issue 报告，不在本仓改。 |
| U3 | `SKILL.md` 第 10 行 "read `CONTEXT.md` (if it exists)" | 本仓根目录没有 `CONTEXT.md`，词汇在根 `CONTEXT-MAP.md` → `docs/contexts/<name>/CONTEXT.md`；`mmw-v2/upstream/CONTEXT.md` 是上游自己的词汇。 | 不适用。 | 这是整组上游技能共有的一句（`tdd/SKILL.md` 第 10 行同样），本仓的连接在技能之外：根 `AGENTS.md` 的 `## External References` 第一行指向 `CONTEXT-MAP.md`。按 `SKILL-SET-REVIEW.md` `### Upstream skills` "Connect outside the upstream text first"，已经连接好，不需要改这一句。 |

## B. 灵魂

### 保留，勿删

以下全是上游原文，也是这个技能存在的理由；下一轮修剪的人按 `SKILL-SET-REVIEW.md` `### Redundancy and bloat` 的 "No-op / attitude" 标准看，可能把其中几句当成空态度删掉，这里逐条说明为什么不能删。

- `## Phase 1: Build a feedback loop` 开头 "**This is the skill.** Everything else is mechanical. ..."（第 20 行）：告诉 agent 力气该花在哪一步，并解释为什么（二分、假设、埋点都只是在消费这个信号）。没有它，agent 会平均分配力气，或者直接去读代码猜原因。
- 同节 "Spend disproportionate effort here. **Be aggressive. Be creative. Refuse to give up.**"（第 22 行）：字面上像空态度，`SKILL-SET-REVIEW.md` 的 No-op 条会把它判为废话。这里与任务书冲突，以任务书为准：这一句规定的是力气分配（在建循环这一步上别轻易退到"读代码推理"），会改变 agent 的做法。
- "Build the right feedback loop, and the bug is 90% fixed."（第 37 行）：给出这一步的价值判断，让 agent 在"再花十分钟把循环做好"和"先猜一个修法"之间选前者。
- `### Tighten the loop` 的 "Treat the loop as a product." 与 "A 30-second flaky loop is barely better than no loop; ..."（第 41、47 行）：定义什么叫好的循环，并给出可比较的尺度。
- `### Non-deterministic bugs` "The goal is not a clean repro but a **higher reproduction rate**."（第 51 行）：把"复现不了"的间歇性 bug 从死胡同改成一个可以推进的目标。
- `### Completion criterion` 末句 "If you catch yourself reading code to build a theory before this command exists, **stop**: jumping straight to a hypothesis is the exact failure this skill prevents."（第 66 行）：点名 agent 最容易犯的那个错，是全篇的核心判断点。
- `## Phase 2` "Wrong bug = wrong fix."（第 74 行）与 `### Minimise` 的 "Why bother:" 一段（第 82 行）：解释为什么要确认是用户说的那个症状、为什么要缩小复现，而不只是命令它做。
- `## Phase 3: Hypothesise` "Single-hypothesis generation anchors on the first plausible idea." 与 "If you cannot state the prediction, the hypothesis is a vibe"（第 90、96 行）：说明为什么要 3 到 5 个、为什么要可证伪。
- 同节 "**Show the ranked list to the user before testing.** ... Don't block on it; proceed with your ranking if the user is AFK."（第 98 行）：说明用户的价值（产品和部署上的知识），同时给了无人值守时的出路。夜里的 worker 正是按后半句做的（见下）。
- `## Phase 4` "Untagged logs survive; tagged logs die." 与 "Measure first, fix second."（第 110、112 行）：给出规则背后的后果。
- `## Phase 5` 关于 **correct seam** 的一段与 "If no correct seam exists, that itself is the finding."（第 118、120 行）：防止 agent 为了交差写一个给人假安全感的浅测试，并把"没有好测试点"本身当成要汇报的结论。
- `## Phase 6` 末条 "..., so the next debugger learns"（第 138 行）：说明产出是给谁读的。
- `## Redact`（第 12 至 16 行）与脚本头第 15、16 行 "`capture` prints its value back to the terminal ... leave signing in to the user as a `step`"：防止密钥和登录信息进入对话、issue 或提交记录。在 MMW 里 worker 的输出会进 GitHub issue 评论，这一段对本仓尤其要紧。

### 真实使用证据（为什么判断"灵魂完整"）

- 夜里的 worker：`~/.codex/sessions/2026/09/18/rollout-2026-09-18T19-43-44-01a0b454-641f-78b2-a162-6cd81dee74e8.jsonl`，agentflow 仓库 `.worktrees/issue-997`，ticket #997 有三条 journey 失败。worker 自己加载了这个技能，把失败的 journey 命令当作现成的红色循环，写出 4 条按概率排序、带预测的假设，用静态证据逐条证实前三条、排除第四条，只改了三处过期断言，再逐条重跑到 `JOURNEY OK`，然后回到 `implement` 的收尾流程。它没有停下来问人（Phase 3 的 "proceed ... if the user is AFK" 与 `implement` 第 29 行 "Put no question on the screen" 一致），也没有机械地做"缩小复现"这一步（第 8 行 "Skip phases only when explicitly justified" 留了这个余地）。
- 白天交互：`~/.codex/sessions/2026/09/16/rollout-2026-09-16T13-24-03-01a0a8ac-108f-79e0-b50d-275075a2ed60.jsonl`（agentflow 主目录），agent 先列出三条可证伪假设及结果，再在真实 Adapter 测试点加一个先失败的回归测试、然后修复、再跑绿。`rollout-2026-09-15T08-44-42-01a0a285-...`（`.worktrees/jellyfish`）同样是先写出失败的测试、确认"复现已锁定"才去看代码。

### 缺口与补充草稿

没有需要补的。对一个只拿到触发句的新 agent，这个技能已经说清了意义（没有红色信号就不许推理）、下游读者（用户看假设清单，下一个排查的人读提交信息）和做浅的后果（修错 bug、浅测试带来假安全感）。上面的真实会话也显示 agent 在清单之外的情况（循环已经现成、无人可问）里做出了合理判断。

有一处是"在别的技能里运行时"的潜在盲点，只记录，不建议现在补：worker 在 ticket 里走到 Phase 5 "no correct seam" 时，`mmw-v2/skills/verify-ticket/references/sub-issues.md` `## Which kind it is` 的五种子票都不完全对应"这里缺一个测试点，值得以后做一次架构改造"这种发现（最接近的是 `deferred`）。没有任何会话出现过这种情况，所以按"不制造发现"不提议改文字；如果将来出现，补的位置应是 `implement` 或 `sub-issues.md`，不是这个上游技能。

## C. 死板的流程

没有需要放开的。

六个阶段是编号的，但每一阶段给的是完成标准（"Done when every remaining element is load-bearing"、Phase 1 的四项勾选）而不是逐条动作，且第 8 行 "Skip phases only when explicitly justified" 把跳过的判断交给了 agent。阶段之间的顺序（先有红色信号，再有假设，再修）正是这个技能的内容本身，不是作者偏好。数字（"3–5 ranked hypotheses"、"Loop the trigger 100×"、"1000 random inputs"）是上游原文里的尺度示例；真实会话里 agent 给了 3 条或 4 条，没有被数字卡住。

## 脚本

`scripts/hitl-loop.template.sh`（44 行）：一个给 agent 复制后编辑的模板，两个函数 `step`、`capture`，没有参数校验、没有恢复代码、没有死代码，也没有过度防御。唯一的问题是上文 U2 的描述与实际不符（不在终端里跑时第一步就以退出码 1 结束），建议不改，理由见 U2。

`agents/openai.yaml` 只有 `display_name` 和 `short_description`，没有 `policy.allow_implicit_invocation: false`，与 `SKILL.md` frontmatter 没有 `disable-model-invocation` 一致，符合 `mmw-v2/merge-notes/README.md` `## disable-model-invocation` 的"两处同增同删"。

## 与其他技能的重复或交接问题

- `mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md` 第 43 行 "Its post-mortem hands off to **the `improve-codebase-architecture` skill** ..." 与本技能不一致：本技能已经没有这次交接（见 U1）。两边都是上游原文（`ask-matt` 在这一行只被本仓改了调用写法），上游自己的文档页 `mmw-v2/upstream/docs/engineering/diagnosing-bugs.md` 第 21、54 行也还写着这次交接。在 MMW 里无害，因为 `improve-codebase-architecture` 只能由用户点名。应留本技能这边的现状；`ask-matt` 那一句归 `ask-matt` 的复审人判断。
- 与 `implement` 的关系：本技能三处说"问用户"（第 16 行 `## Redact`、第 55 行 `### When you genuinely cannot build a loop`、第 98 行 Phase 3）。在夜里由 `implement` 的规则接管：第 29 行 "Put no question on the screen"、第 97 行 `ABANDON` 的 `stuck`（"the reason names the routes tried"，与本技能的 "List what you tried" 同义）。#997 的会话证明两者一起加载时 worker 按 `implement` 做了。应留 `implement` 那一边，本技能不需要改。
- 与 `implement` 第 40 行 "Commit tests only where the ticket asks for them or this repository already keeps tests for this kind of change" 有轻微张力：本技能 Phase 5 要求先写回归测试。两者不矛盾，因为本技能自己也把回归测试限定在 "only if there is a correct seam"，而 bug 修复本身就是 ticket 要求的行为。记录，不需要改。
- 与 `triage` 的重复（上游文档页第 68 行承认 triage 第 3 步是本技能 Phase 1–2 的浅版）属上游设计，本仓的 `triage` 对流水线返回的票另走 `references/pipeline-issues.md`（读事件记录而不复现），不重叠。

## 没查到的

- 没跑本技能在 Claude Code 以外各宿主（Grok、Pi、Cursor）里的真实使用；只查了 `~/.codex/sessions` 和 `~/.claude/projects`。`~/.claude/projects` 里没有找到任何一次 Skill 工具调用 `diagnosing-bugs`，也没有在 MMW 维护会话以外读过它的文件；这一查是用固定字符串 grep 做的，若 Claude 以别的方式加载技能（例如系统注入正文），可能漏计。
- 上游 GitHub 当前 `main` 上的版本只通过 WebFetch 看了摘要，看到的内容与本仓一致，没有逐字比对。
- 上游文档页第 59 行说这个技能在 GPT 系模型上"过度触发"（对普通问题也走完整诊断流程）是最常见的抱怨。本仓的 Codex 会话里，2026-09-16 13:24 那次是由"查清楚到底要不要重新出包"这样的问题触发的，但最终确实找出并修复了一个真实 bug，没有看到拖慢回复的情形。样本只有约 7 个产品仓会话，不足以判断会不会过度触发，所以不建议关闭模型触发。
