# 哪些设定会让 agent 停下，哪些会让它转圈

无人看守时，一张票有两种坏结局：**停**（本来能继续，却因为一条判定不通过而交给人）和**转圈**（两个 agent 互相返工，永不收敛）。#60 与 `12-decisions.md` 里防转圈的设定是齐的（code-review 一轮、不复审、verifier 一次），防停的设定则有缺口：本文逐条检查这些硬性判定，列出会触发的条件与改法。

检查范围：#60 全部十一节、`12-decisions.md` 块 A–G、`08-failure-vocabulary.md` §5、`05-runnable-acceptance-gates.md` §8 与 §10、`06-independent-verifier.md` §8。本文只调查、只提议；定案登记在 `12-decisions.md` H4–H6。

判断依据是用户 2026-08-29 定的原则：**约束 agent 的工作方法以提高结果质量，而不是轻易判定失败或让人接管；同时不许陷入 agent 之间的无限循环，遇到收不了的问题要完整、及时地记录下来供以后修**。

## 1. 会必然停的两处

### 1.1 `VERDICT` 的 commit 必须等于 HEAD——与 B2 的定案直接矛盾

`12-decisions.md` B2 的结论末句写的是：「修完在最终 commit 上再自跑 CHECK 填 EVIDENCE；**`VERDICT` 行照实绑 verifier 验过的那个 commit**」——也就是接受 VERDICT 的 commit 不是最终 commit。

而 #60 第 9 节第 6 步、`13-scriptable-steps.md`「第 2 节」、`12-decisions.md` G1 三处都把 `--closeout` 的一项写成「票上最后一条 `VERDICT` 的 commit **== `git rev-parse HEAD`**（不等 = 修后没再验）」。

两者不能同时成立。按收尾的实际顺序：

1. 第 2 步 verifier 在 commit A 上写 `VERDICT <A>`；B2 与 B5 都定「不派第二次」。
2. 第 3 步 code-review 有票内发现 → worker 修 → HEAD 变成 B → 再自跑 `verify-ticket.py`（自跑不产生 VERDICT）。
3. 第 6 步 `--closeout` 检查 `A == B` → 不成立 → 退出码非零。

**只要 code-review 提出任何一条票内发现，这张票就永远关不掉**，而 code-review 提出票内发现是常态（否则那一轮没有意义）。worker 唯一的出路是 `HANDOFF REQUIRED`。

改法：把这一项改成 B2 的语义——`git merge-base --is-ancestor <VERDICT 的 commit> HEAD`（验过的那个 commit 必须在当前历史里，即没有被回退或重写），并在收尾评论里多一行 `Post-verdict:` 列出 VERDICT 之后的 commit 与它们的来源（`code-review 票内发现`）。最终 commit 的可信度由第 3 步末尾那次自跑承担，这也正是 B2 写「修完在最终 commit 上再自跑 CHECK 填 EVIDENCE」的原因。

另一个选项——允许 verifier 在 code-review 引出代码修改时再派一次——**已定不采**（`12-decisions.md` H5）：verifier 第二次跑的命令、判定与环境都与 worker 第 3 步末尾那次自跑相同，`level` 大概率不变，增量只剩「换一个没有写码记忆的上下文」，而它防的「自评自勾」已被脚本挡住。

### 1.2 带 `MANUAL:` 的票在夜里必然 `HANDOFF REQUIRED`

`08-failure-vocabulary.md` §5 表第一行：manual gate 算 met 的条件是「勾了且 `EVIDENCE:` 非 `pending`」；`05-runnable-acceptance-gates.md` §8.2 第 4 条：「manual 标准 → 由 `MANUAL:` 里命名的人填 EVIDENCE，**worker 不代填、不代勾**」；#60 第 5 节：verifier 对 MANUAL 条目「标『manual, not run』」。

于是任何带一条 `MANUAL:` 的票，夜里跑完必然有一条 unmet，必然不得 `ALL MET`，必然 `HANDOFF REQUIRED`、换 `ready-for-human`、不关票。

这未必是错的——#60 的 User Story 3 本来就写「写不出命令的标准明写『谁看哪个东西』」。问题在于 `HANDOFF REQUIRED` 这个词此时同时表示两件事：**「出问题了，需要人来救」** 和 **「一切正常，只有一条等你看一眼」**。早上从首行分不清哪张票是真出了事。

**已定取甲**（`12-decisions.md` H6，与 `ABANDON: decision` 同一条逻辑）：worker 收尾时把每条未填 EVIDENCE 的 `MANUAL:` 标准开成 spec 下的 sub-issue（`--parent <spec> --label ready-for-human`，正文抄 `MANUAL:` 行原文与相关材料），列进收尾评论的 `Sub-issues opened:`；这些标准不计入 unmet，其余标准全过即 `ALL MET` 关票。`Counts:` 增加一个 `manual` 数，形如 `Counts: 5 met, 0 unmet, 0 abandoned, 1 manual of 6`。

## 2. 常见情况会触发的四处

| 处 | 现在的规定 | 什么时候会触发 | 改法 |
| --- | --- | --- | --- |
| verifier 的两次 `git status --porcelain` | `12-decisions.md` B4：跑 CHECK 前后各一次，**两次都空**才算没动东西 | CHECK 命令自己会产出文件：`visual-parity.py --out <目录>` 的证据页与截图（#60 第 2 节）、`pytest` 的 `.pytest_cache`、覆盖率报告。第二次必然不空，verifier 会报告「动了东西」 | 两次比较的是**被跟踪文件**：改成 `git status --porcelain --untracked-files=no`；未跟踪的产出物另外要求 `to-tickets` 把证据目录写进仓库的 `.gitignore` 或放 `/tmp` |
| `--closeout` 的 `git status --porcelain` 空 | #60 第 9 节第 6 步 | 同上：证据目录、临时账本 | 同上，或明确只查已跟踪文件 |
| `--closeout` 的 `git diff --name-only <merge-base>..HEAD` 非空 | 同上 | 一张票的结论是「不需要改代码」（验证型的票、或实现已在别处完成） | 允许一条例外：diff 为空但收尾评论首行是 `ALL MET` 且每条 AC 的 EVIDENCE 都指向已有代码时，改为警告而不是拒绝 |
| `--preflight` 要求 `assignee 为空` | #60 第 7 节、第 2 节 | 同一张票第二次开工：夜里 worker 崩了早上重派、或换一个宿主重试。它已经被上一个会话认领 | 改成「assignee 为空**或就是我**」。这是幂等性，不是放松 |

## 3. 没定「然后呢」的三处

这三处不是设定太严，是**根本没写遇到时怎么办**，agent 只能自己发挥或停下。

1. **`--preflight` 返回 `NOT_READY` 之后**。#60 第 7 节写「`NOT_READY` 就停下报原因」——报给谁？会话里打印一行，票上没有任何痕迹，Herdr 那边 agent 变 idle。早上看票，这张票和从没派过一模一样。**应当**：`--preflight` 失败时由脚本自己在票上评论一行 `NOT_READY: <原因>`（脚本已经会调 `gh`），worker 再停。另外 `blockedBy` 全 CLOSED 这一项应该由 `dispatch.sh` 在**派发前**查，不满足就根本不派，省掉一个会话。
2. **`dispatch.sh wait` 超时之后**。#60 第 9 节第 3 步让 worker 等 reviewer 的评论出现，超时 exit 1，然后没写做什么。reviewer 会话崩了、被墙挡住、或 `code-review` 本身出错，worker 就悬在那里。**应当**：超时后在票上评论一行说明 code-review 没能完成，跳过这一轮，继续走第 4 步收尾——一个挂掉的 reviewer 不该让整张票交给人。
3. **`visual-parity.py` 的负控制不过之后**。#60 第 2 节写「自带负控制（故意错的场景必须失败，否则本次结果不可信）」，没写不可信之后怎么办。**应当**：负控制不过时工具退出码与 CHECK 失败一致，并在输出首行说明是负控制失败（不是实现不对），worker 修工具或环境而不是修实现。

## 4. 唯一没有上限的循环

#60 第 9 节第 1 步：「`verify-ticket.py <n>`；没过的修，再跑，**直到全过或确认修不了**」。

这是整条流水线上唯一没有轮次上限的地方。「确认修不了」是模型的主观判断，一个不肯放弃的 worker 可以在同一条 AC 上修到天亮。其余的循环都有上限：code-review 一轮不复审（B2）、verifier 一次（B2、B5）、`stop` hook 在 `stop_hook_active` 为真且票状态没变时放行（#60 第 2 节）、宿主自己的续跑上限（Grok 8 次、Cursor 5 次，`13-scriptable-steps.md`「五个宿主的 hook 能力」）。

**应当**给它一个上限，并且把停下来的方式写死：同一条 AC 连续三轮自跑仍未过 → 停止修这一条，写 `ABANDON: AC<n> failed <三次尝试各做了什么>`，继续处理其余标准。理由与用户定的原则一致：不轻易判失败，所以给三次；但不许无限，所以到三次就完整记录下来交给以后修。三这个数取自 `07-overbuild-discipline.md` 之外的现成先例——`rcosteira79/herdr-autocontinue` 的重试上限是五次，`unlazy/scripts/stop-hook.mjs` 的同状态放行阈值是六次（`13-scriptable-steps.md` 附录）；三是更紧的一档，因为每一轮包含一次完整的修改与重跑。

## 5. 不要动的：防转圈的设定

下面这些看起来「严」，但它们正是防止两个 agent 互相返工的东西，都保留：

| 设定 | 出处 | 为什么保留 |
| --- | --- | --- |
| code-review 只审一轮、worker 修一轮、不复审 | `12-decisions.md` B2（用户裁决原话在案） | 复审必然引出新一轮修改 |
| verifier 只派一次 | B2、B5 | 同上；§1.1 的「上限二次」是唯一的例外提案 |
| `verifier-failed` 不触发 HANDOFF，worker 修完自跑继续 | B5 | 已经是「不轻易交人」 |
| `verifier-blocked` 前 verifier 先自己动环境 | B5（用户裁决原话在案） | 同上 |
| `pretool` hook 拦下没经过 `--closeout` 的关票 | #60 第 2 节、第 9 节第 6 步 | 它拦的是绕过检查，不是拦工作；deny 的 reason 直接告诉它去跑哪条命令 |
| `stop` hook 顶回半途结束 | 同上 | 有 `stop_hook_active` 兜底，最多顶一次 |
| gate-check 的双条件（exit 0 **且** EXPECT 匹配） | `12-decisions.md` B8 | 这是「判过没过」的定义本身 |

## 6. 汇总

| 编号 | 事项 | 性质 | 落点 |
| --- | --- | --- | --- |
| S1 | `--closeout` 的 `VERDICT` commit 检查改为「是 HEAD 的祖先」，收尾评论加 `Post-verdict:` 行 | 修矛盾（必然停） | #60 第 9 节第 6 步与第 5 步；#63 |
| S2 | verifier 仍然只派一次（不采二次） | 已定（H5） | 无改动；B2、B5 不变 |
| S3 | MANUAL 项开成 sub-issue，不计入 unmet，其余全过即 `ALL MET` | 已定（H6） | #60 第 9 节第 5–6 步；#63、#73 |
| S4 | 两处 `git status --porcelain` 改成只查已跟踪文件 | 修（常见触发） | #60 第 5 节、第 9 节第 6 步；#63、#69 |
| S5 | `--closeout` 的 diff 非空改为警告 | 修（少见触发） | #60 第 9 节第 6 步；#63 |
| S6 | `--preflight` 的 assignee 条件改成「空或就是我」 | 修（幂等） | #60 第 7 节；#63 |
| S7 | `--preflight` 失败时由脚本在票上评论 `NOT_READY: <原因>` | 补缺口 | 同上 |
| S8 | `dispatch.sh` 派发前查 `blockedBy` 全 CLOSED | 补缺口 | #67 |
| S9 | `dispatch.sh wait` 超时后：票上评论 + 跳过 code-review 继续收尾 | 补缺口 | #60 第 9 节第 3 步；#67、#73 |
| S10 | `visual-parity.py` 负控制失败的退出码与首行说明 | 补缺口 | #60 第 2 节；#65 |
| S11 | 第 1 步自跑修复循环上限三轮，超出写 `ABANDON: AC<n> failed` 继续其余标准 | 补上限（防转圈） | #60 第 9 节第 1 步；#73 |
