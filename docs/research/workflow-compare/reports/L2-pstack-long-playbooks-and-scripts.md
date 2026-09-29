# L2 pstack 的长 playbook、流程 playbook 与脚本（lever）解剖

范围：`docs/research/code-landing-refs/pstack/`（cursor/plugins b0b9c7a0 的只读快照）下 `skills/poteto-mode/playbooks/` 的 10 个文件（babysit.md、shipping.md、autonomous-run.md、orchestrate.md、autopilot-full.md、autopilot-stack.md、session-pickup.md、pause-safely.md、multi-phase-plan.md、worktree-cleanup.md），以及 `skills/poteto-mode/scripts/` 下全部文件。下文路径若不带前缀，都相对 `pstack/skills/poteto-mode/`。

读法：上述 10 个 playbook 和 scripts 下每个源文件、测试文件、配置文件都完整读过（`bun.lock` 只读到能确认它是 bun 锁文件的程度，它是生成文件）。脚本只读未运行，所以「测试能否通过」未验证。为判断连线，另外读了 `SKILL.md` 全文（poteto-mode 的 mode 文件）、`agents/poteto-agent.md` 全文、`skills/principle-build-the-lever/SKILL.md` 开头、`references/bugbot-triage.md` 的开头与全部标题、`skills/swarm/SKILL.md`、`skills/show-me-your-work/SKILL.md`、`skills/figure-it-out/SKILL.md` 的 frontmatter 与标题，以及 README.md 和 `docs/guide/` 里提到这些文件的行。凡结论依赖这些只看了局部的文件，都标了出来。

标注约定：没有标记的陈述是「原文写明」并给出处；「推断」是我从写法归纳的，不是原文所说。

---

## 0. 这批 playbook 的共同形态（回答问题 2 的共性部分）

**没有 frontmatter。** 10 个 playbook 文件全部以 `### <标题>` 开头（例如 `babysit.md` 第 1 行 `### Babysit`），没有 YAML 头，因此没有 `name`、`description`、`disable-model-invocation`、`mode`、`reminder` 这些键。这些键只出现在它们的上级 `SKILL.md`：

```
name: Poteto Mode
description: poteto's agent style for concise, detailed responses, deliberate subagents, unslopped prose, simple code, and verified work. Use for poteto, /poteto-mode, or requests to work in this style.
disable-model-invocation: true
mode: true
icon: crown
color: yellow
reminder: New task? Playbook match or rigor needed -> apply /poteto-mode. Casual turn or user opts out -> don't.
```

推断：标题用 H3 而不是 H1，说明作者把每个 playbook 当成 `SKILL.md` 的 `## Playbooks` 一节的下属小节来写，文件只是为了按需加载而拆开的，不是独立技能。它们不能被模型按描述自动发现，只能经 `SKILL.md` 的 `## Playbooks` 清单或别的文件的相对路径到达。

**固定骨架，顺序一致：**

1. `### 标题`。
2. 一句加粗的「归属句」：`**You own X. ...**`。10 个文件全部如此，例如 `**You own the merge frontier. ...**`（babysit.md）、`**You own the program, never the code. ...**`（orchestrate.md）、`**You own the disk and the safety gate.**`（worktree-cleanup.md）。它同时说明这个 playbook 管什么、不管什么。
3. 可选的路由与边界句：何时来这里、何时去别处（例如 babysit.md 第 3 行 `A request to land or ship is playbooks/shipping.md, which begins where this playbook ends.`）。
4. 编号步骤。babysit、shipping、autopilot-full、autopilot-stack 的每一步以加粗短句开头（`1. **Declare the mode and resolve the forge before any poll.**`）；autonomous-run、session-pickup、pause-safely、multi-phase-plan、worktree-cleanup 用普通句子开头。只有 orchestrate.md 在编号步骤外另有 `####` 小节。
5. 结尾一行 `**Reply:** ...`，只列出本 playbook 独有的回复内容。`SKILL.md` `## Writing the reply` 写明：`Every playbook ends with a reply written this way ... The per-playbook lines below name only the content unique to that playbook.`

**编号步骤是给待办清单用的。** `SKILL.md` `## Playbooks`：`Open a todolist whose first items are the matched playbook's steps, copied in verbatim, before any task-specific todos. A step you choose not to do stays in the list with a one-line skip: <reason>.` 推断：这决定了编号步骤必须能逐条抄进待办清单；步骤之外的内容（orchestrate 的各 `####` 小节、multi-phase-plan 的模板）不进清单，而是执行这些步骤时要查的常设规则或输出格式。

**句式与语气：** 第二人称祈使句，短陈述句，一句一事；大量「Never ...」「Only ...」「X is not Y」式的禁令和定义句（如 `CI green is not a verdict`，shipping.md 第 1 步）。理由通常紧跟在规则后的同一句或下一句（如 orchestrate.md `#### Stack safety`：`Restacks run in cloud. A local restack at this scale takes the laptop down.`）。原则以括号附注的方式引用在规则之后，而不是展开讲。

---

## 1. 组件清单

| 文件 | 类型 | 管什么（一句话） | 行数 / 词数 |
|---|---|---|---|
| `playbooks/babysit.md` | playbook | 把一个 PR 或一个 stack 推到 merge-ready：冲突、review thread、CI；不合并 | 27 / 1291 |
| `playbooks/shipping.md` | playbook | babysit 之后的一半：逐个 PR 独立验证，只从底部合并连续已验证的一段 | 17 / 913 |
| `playbooks/autonomous-run.md` | playbook | 一个长任务，先定可检查的退出条件，再不停地推到条件满足 | 13 / 297 |
| `playbooks/orchestrate.md` | playbook（长） | 多日、多 PR、成百子代理的「项目级程序」，由一个常驻协调者只写 brief、排空队列、做决定 | 111 / 2636 |
| `playbooks/autopilot-full.md` | playbook（长段落） | 一队独立 PR，每个 PR 一个 owner 从构建做到合并，root 只做 swarm 验证、会签和巡检 | 13 / 1436 |
| `playbooks/autopilot-stack.md` | playbook | 同样的 owner 循环，但不合并，交付一条线性 base-branch stack 给操作者合并 | 16 / 823 |
| `playbooks/session-pickup.md` | playbook | 接手前一个代理的在途工作：读旧记录，不重做 | 11 / 257 |
| `playbooks/pause-safely.md` | playbook | 显式暂停：在安全边界停下，留下冷启动可恢复的检查点 | 10 / 202 |
| `playbooks/multi-phase-plan.md` | playbook（长，含输出模板） | 产出一份多 PR 计划文件（交付物是计划，不实现），并用脚本检查格式 | 156 / 2186（其中模板第 17–154 行约 1559 词） |
| `playbooks/worktree-cleanup.md` | playbook | 清理已合并或废弃的 git worktree 和 iOS 模拟器，以安全闸门代替代码评审 | 14 / 444 |
| `scripts/orch/orch.ts` | 脚本（CLI 入口） | orchestrate 的记账 CLI，子命令读写 store 里的纯文本表 | 578 |
| `scripts/orch/store.ts` | 脚本（库） | store 的读写、校验、锁、Graphite frontier 解析、status.md 生成 | 1607 |
| `scripts/orch/orch.test.ts` | 测试 | store 与 CLI 的 bun 测试，含假 `gt` 与真实临时 git 仓库 | 634 |
| `scripts/watch-pr/watch-pr` | 脚本（入口 shim） | bun 可执行入口：装依赖后调用 `cli.ts` 的 `main` | 6 |
| `scripts/watch-pr/cli.ts` | 脚本 | 参数解析、选择运行模式、输出最终 verdict、返回退出码 | 223 |
| `scripts/watch-pr/github.ts` | 脚本 | 经 `gh` 读取 GitHub（PR 事实、checks、review threads、commit rollup），全部严格解析、失败即关 | 699 |
| `scripts/watch-pr/policy.ts` | 脚本 | 合并就绪判定、阻塞优先级、轮询与退避、queued-stack 状态机 | 832 |
| `scripts/watch-pr/types.ts` | 脚本（类型） | 以判别联合类型定义快照、阻塞、verdict 事件与退出码 | 401 |
| `scripts/watch-pr/render.ts` | 脚本 | verdict 渲染为 JSON（默认）或人读文本（四列表格） | 169 |
| `scripts/watch-pr/types.compile.ts` | 测试（编译期） | 用 `@ts-expect-error` 证明非法状态在类型上不可表示 | 93 |
| `scripts/watch-pr/cli.test.ts`、`github.test.ts`、`policy.test.ts` | 测试 | CLI、GitHub 解析、判定策略与队列节奏的 bun 测试 | 224 / 306 / 420 |
| `scripts/watch-pr/fakes.test-helper.ts` | 测试辅助 | 假 `GitHubReader`，记录调用序列 | 118 |
| `scripts/watch-pr/tsconfig.json` | 配置 | watch-pr 的严格 TypeScript 检查配置 | 13 |
| `scripts/check-plan.mjs` | 脚本（lint） | 检查 multi-phase-plan 产出的计划文件是否符合模板 | 186 |
| `scripts/worktree-audit.sh` | 脚本（只读审计） | 列出每个 worktree 的大小、年龄、合并状态、未提交改动、PR、最近聊天，建议一个分桶 | 86 |
| `scripts/bootstrap.ts` | 脚本（依赖自举） | 首次运行时 `bun install --frozen-lockfile` 并重启自身 | 62 |
| `scripts/package.json`、`scripts/bun.lock` | 配置 | 依赖 `commander@14.0.0`；`test` 与 `typecheck` 两个 npm script | 16 / 67 |

---

## 2. 逐个 playbook 解剖（问题 2、3）

### 2.1 `playbooks/babysit.md`

**结构：** 归属句 → 路由句（替代 Cursor 内置 babysit，落地请求去 shipping）→ 启动时机段 → 9 步 → 一句收尾 `drive ends at merge-ready.` → `**Reply:**`。

**各步装的内容：**

- 第 1 步：触发条件到模式的映射（`drive` / `background` / `threads-only` / `check`，各配用户原话），加 forge 选择的命令规则（`gh` 默认、`command -v origin` 成功则用 `origin pr ...`、`Never require Graphite (gt)`）。触发条件 + 命令。
- 第 2–4 步：做法与边界（只做 merge frontier、一个 stack 一个 babysitter、不改 stack 拓扑，唯一例外是 owning PR 已合并时新开 follow-up PR）。
- 第 5 步：顺序规则（`Order is conflicts, then review threads, then CI.`）加理由。
- 第 6 步（最长，约占全文三分之一）：命令与参数（`scripts/watch-pr/watch-pr`、`--pretty`、`--status-only`，Origin 的三条命令），以及按 forge 分开的停止条件（GitHub 的 `READY`、`WAITING`/`merge-queue`、`ADVANCE`、`COMPLETE`），外加「watcher 重新 arm 不授权合并」和冻结 PR 列表的规则。
- 第 7 步：CI 失败分类的判断规则（flake 只重跑一次；与 diff 无关的失败先用 `git merge-base --is-ancestor` 查是否 stale base）。
- 第 8 步：Bugbot 分诊做法，含两个 forge 的精确回复命令，以及安全规则 `Never interpolate comment text or a reply into a shell command.`
- 第 9 步：停在人的决定处；结束后把可复用的 dismiss 模式作为候选条目提交到 `../references/bugbot-triage.md`。

**调用与连线：** 由 `SKILL.md` 触发列表（`Any PR-status request → the **Babysit** playbook`）和 `## Playbooks` 清单路由进来；`orchestrate.md` `#### Stack safety` 让 babysitter 遵循它；`autopilot-full.md` 第 2 步和 `autopilot-stack.md` 第 1 步让每个 owner 跑它；`references/bugbot-triage.md` 第 3 行反向指明自己服务于它。它调用 `scripts/watch-pr/watch-pr`、`/loop`（dynamic mode），读 `../references/bugbot-triage.md`，把合并请求交给 `playbooks/shipping.md`。没有引用任何 principle 技能。

### 2.2 `playbooks/shipping.md`

**结构：** 归属句 → `This is the half after playbooks/babysit.md.` → 9 步 → `**Reply:**`。

**内容：** 第 1 步 forge 选择（与 babysit 第 1 步同文）加「每个 PR 一个 Cursor cloud agent 做独立验证，返回 `PASS` / `PASS+NOTES` / `FAIL`」，定义 `Safe means a verdict from an agent that did not write the code.` 第 2 步是判断规则（只合并从底部起连续已验证的一段）。第 3 步是本文件最重的做法：**patch-id 规则**（记录 verdict 的 head SHA、base SHA 与 `git patch-id`，rebase 后比较；只有测试、文档或 lint 配置不同时，在 verdict SHA 构建两次、在当前 head 构建一次，以判断差异是否噪声）。第 4–7 步是逐个 PR 落地的顺序与命令（`origin pr merge <pr> --squash [--auto]` 或 `gh pr merge ...`）。第 8 步是 GitHub 状态字段的失败判据（`CLOSED` 无 `mergedAt`、必需 check `FAILURE`/`CANCELLED`、`UNSTABLE`/`DIRTY` 且无 auto-merge），并把 `watch-pr --queued-stack --stack-prs <bottom>` 降为「只作事件唤醒」。

**连线：** 被 babysit 第 6、9 步和收尾句交接；patch-id 规则被 `autopilot-full.md` 第 4、5 步、`autopilot-stack.md` 第 7 步、`multi-phase-plan.md` 模板 `### Verdict and merge` 按文件名引用。推断：shipping.md 第 3 步实际上是 patch-id 规则的唯一出处，其他 playbook 引它而不复制它。

### 2.3 `playbooks/autonomous-run.md`

**结构：** 归属句 → 6 步 → `**Reply:**`。最短的「程序型」playbook。

**内容：** 第 1 步定可检查的退出谓词。第 2 步选唤醒方式：`Pick the wake mechanism using Cursor's /loop command (a built-in, not a pstack skill).` 有事件就派 watcher 子代理，另设长心跳兜底。第 3 步每轮做证据支持的最小改动，推进则提交，没帮助就丢弃，引 **sequence-verifiable-units** 原则。第 4 步：途中发现的问题自己修，另开 PR，只上报不可逆动作、真正的产品偏好或死路。第 5 步每轮用 **show-me-your-work** 记一行。第 6 步：平台期不是停止条件，不许放宽谓词。

**连线：** `SKILL.md` 路由；`orchestrate.md` 第 1 步在「一个代理能在预算内完成」时降级到它；`playbooks/hillclimb.md` 第 16 行只借用它的唤醒机制（`borrow only the wake mechanism ... not its stop rule`）。

### 2.4 `playbooks/orchestrate.md`（长）

**结构：** 归属句与路由段（与 Autonomous run、figure-it-out 的边界）→ `Ceremony must scale with the program.` → 三条总规则 → `#### Roles and placement` → `#### Store layout` → `#### The brief`（含 12 行模板代码块）→ `#### Steps`（7 步）→ `#### Queue and drain` → `#### Stack safety` → `#### Verification` → `#### Liveness and failure` → `#### Escalation` → `**Reply:**`。

**各节装的内容：**

- 三条总规则：`Completions are queue events, not interrupts.` / `Every spawn and every resume carries the standing orders verbatim.` / `The brief is the product.`（判断与理由）
- Roles：三种角色（Coordinator、Sub-coordinator、Worker / verifier）、放在本机还是云、并发上限（`roughly ten, as a rolling window`）、嵌套深度（`nesting works to depth 3`）、`Run a unit's verifier on a different model family from its worker.` 并说明「Hard-coded swarm trees were tried and parked as too rigid.」（角色定义 + 历史理由）
- Store layout：`orchestrate/<project-slug>/` 下 9 个文件，`Every file has exactly one writer.`，每个文件一句用途（状态存储规格）。
- The brief：9 字段模板（GOAL、SCOPE、CONTEXT、ACCEPTANCE、VERIFY、TIMEBOX、FORBIDDEN、REPORT、STANDING）、按单元大小缩放、`Missing fields are a refuse-to-spawn condition.`、按波次抽查一份子协调者的 brief（输出格式 + 规则）。
- Steps：Frame → Install the runtime → Pilot → Scale → Drain → Land → Close（步骤顺序）。
- Queue and drain：四个排空时点、先完成的「critical sections」、每次排空的分类（landed、needs-verify、failed、zombie、noise）和要跑的 `orch` 命令、排空回合只输出 `orch status` 的三行（协议）。
- Stack safety：frontier 由 `gt` 计算、每个 stack 一个 stacker、workers 不 rebase、关 PR 与改 base 只经 stacker（并发写入规则）。
- Verification：按单元缩放验证、`ledger.tsv` 的五个 verdict 值、`A new head SHA voids the row`、「产出一落地就外置」（判定词汇 + 规则）。
- Liveness and failure：不要 resume 来探活、静默死亡写合成 postmortem、按失败模式重试（`Two retries, then abandon the unit`）、僵尸回来的对账、全树停止线、自身基础设施重试上限与终止交接、Cursor 重启后的恢复顺序（恢复规程）。
- Escalation：会到人的四类与不会到人的清单、`When in doubt, act and log.`、中途发现只修阻塞 frontier 的（升级规则）。

**句式：** 与短 playbook 相同，但这里是「规则簇」而非步骤；只有 `#### Steps` 可抄进待办清单。

**连线：** `SKILL.md` `## Playbooks` 两处路由（清单条目与「standing project-scale program routes to Orchestrate instead」）；`multi-phase-plan.md` 第 4 步 `A standing program takes playbooks/orchestrate.md.` 它运行 `scripts/orch/orch.ts`（以 `bun scripts/orch/orch.ts`，文中简写为 `orch`），调用 show-me-your-work 技能（`decisions.tsv` 与收尾审计）、arena 技能（有争议的拆分）、loop 技能（frontier 唤醒），经 Task 工具派 sub-coordinator、worker、verifier，让 babysitter 遵循 `playbooks/babysit.md`，以括号形式引 principle-separate-before-serializing-shared-state 与 principle-encode-lessons-in-structure，外部依赖 `cursor-team-kit` 的 `control-ui` / `control-cli` 和 Graphite `gt`。

### 2.5 `playbooks/autopilot-full.md`

**结构：** 归属句 + 与 Orchestrate 的区别 → 7 步 → `**Reply:**`。只有 13 行，但第 2 步和第 6 步各是一大段（全文 1436 词）。

**各步：** 第 1 步操作者的保留项与「state-then-wait」（被要求陈述计划时陈述后停下，明确 go 后才 arm `/goal`）。第 2 步是 owner 的完整生命周期清单：forge 选择、构建、首次推送、开 ready PR、self-proof（引 **prove-it-works**）、按 `../references/bugbot-triage.md` 分诊、`/deslop`、`/no-comments`、rebase、`playbooks/babysit.md` 循环、合并；另有 15 分钟内开 `decisions.tsv`（**show-me-your-work**）、`children.tsv` 登记子代理、rebase 时机规则、code-ready SHA 报告规则。第 3 步并行规则。第 4 步 swarm 验证轮次与各 lane（gates、live、两个以上 audit lane、Regression lane against trunk），引 **swarm** 技能与 shipping 的 patch-id 规则。第 5 步合并条件。第 6 步 root 层：pinned gate 抬高需会签、30 分钟巡检 tick（本地 `/loop` 加监控 shell 睡眠与哨兵输出，云端用 cloud-sleeper 唤醒链）、每 tick 用 `git show origin/main:pstack/skills/poteto-mode/playbooks/autopilot-full.md` 重读本文件、只以副作用计进度、卡住即替换。第 7 步收到停止令即全员零写入。

**连线：** `SKILL.md` 路由；`multi-phase-plan.md` 第 4 步二选一；`autopilot-stack.md` 多处按步号引用它（`the children.tsv of Autopilot-full step 2`、`per Autopilot-full step 6`、`per Autopilot-full step 4`、`The countersign rule is unchanged from Autopilot-full`）。

### 2.6 `playbooks/autopilot-stack.md`

**结构：** 归属句 `The sibling of **Autopilot-full**.` → 8 步 → `**Choosing between the autopilots.**`（二选一判据）→ `**Reply:**`。

**内容：** 第 1 步 owner 循环（与 autopilot-full 第 2 步大段同文，少了合并）。第 2 步巡检 tick（与 autopilot-full 第 6 步同文，末尾转引）。第 3 步操作者闸门（同 autopilot-full 第 1、7 步）。第 4 步 `STACK-READY` 代替 merge-ready。第 5 步只追加不合并。第 6 步拓扑单写者：只有 root 改 stack，给出 `--force-with-lease`、`ls-remote`、`origin pr create --status open --base <parent-branch>` 等命令。第 7 步在 root 吸收 trunk 漂移并按 patch-id 规则重验。第 8 步交付一条线性链。

**连线：** 二选一判据被 `multi-phase-plan.md` 第 4 步引用：`Pick between playbooks/autopilot-full.md and playbooks/autopilot-stack.md per the rule at the end of playbooks/autopilot-stack.md.`

### 2.7 `playbooks/session-pickup.md`

**结构：** 归属句 → 5 步 → `**Reply:**`。

**内容：** 第 1 步定位旧记录（本工作区的 `agent-transcripts/`，明令不跨 `~/.cursor/projects/*/` 读，理由是会读到无关项目的私聊），长记录交子代理解析（引 **principle-guard-the-context-window**）。第 2–3 步重建状态、对比已做与待做，`The prior trail is authoritative input.` 第 4 步路由到匹配的 playbook 并选结论类型（继续、交付、批准或推翻、事后分析），`The pickup playbook ends here. The routed playbook owns the rest.` 第 5 步在真实产物上验证继承的结论（引 **principle-prove-it-works**）。

**连线：** `SKILL.md` 路由；`skills/recall/SKILL.md` 第 17 行把「恢复某个具体旧聊天」分流到它；`docs/guide/03-understand.md` 同样区分。它路由回 `SKILL.md` 的 playbook 清单（第 4 步）。

### 2.8 `playbooks/pause-safely.md`

**结构：** 归属句 + `This is explicit only.` → 4 步 → `**Reply:**`。最短（202 词）。

**内容：** 在安全边界停下并取消嵌套子代理；不做不可逆动作；把未提交改动提交成一个 `wip:` commit；把恢复笔记写到上下文之外（压缩触发时写 `/tmp/<slug>-resume.md`），已有 show-me-your-work 记录就指向它而不复制。

**连线：** `SKILL.md` 条目称它为 `The complement to Session pickup.` 它本身不引用任何技能文件名，只提到 show-me-your-work 记录。

### 2.9 `playbooks/multi-phase-plan.md`（长，含输出模板）

**结构：** 归属句（`The plan is the deliverable. Do not implement.`）→ 7 步 → `**Verification.**` 段 → `**Control skill.**` 段 → 一个 138 行的 Markdown 计划模板（四个反引号围起）→ `**Reply:**`。

**各部分：**

- 7 步：何时跳过计划；用 `playbooks/prototype.md` 先解决开放问题（引 **never-block-on-the-human**）；用 `subagent_type: "poteto-agent"` 子代理探索（引 **guard-the-context-window**）；把模板复制进计划文件并填满（引 **sequence-verifiable-units**，指定执行 playbook 的选择规则）；用 `/technical-writing` 和 `/unslop` 写作；运行 `node pstack/skills/poteto-mode/scripts/check-plan.mjs <plan.md>` 修到无输出（引 **encode-lessons-in-structure**）；交回并停下。
- `**Verification.**`：验证规则全文（`Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.`，引 **prove-it-works**），live 块固定 `Ten lanes on grok-4.7-xhigh-fast`，按 **swarm** 技能执行，含 Regression lane 与双侧性能门槛，交互改动需操作者看截图和视频。
- `**Control skill.**`：按界面选 `control-ui` / `control-cli`（`cursor-team-kit`）。
- 模板：`# <Program> plan` → `## How to read this` → `## Program checklist`（`### Arm the program`、`### Spawn owners`、`### PR mechanics, for every PR`、`### Verdict and merge, for every PR`、`### Boot recipe, for every live lane`）→ 每个 PR 一节（9 个加粗子块 `Depends on.`、`Files.`、`Build.`、`You see.`、`Verify, unit.`、`Verify, live.`、`Verify, perf.`、`Review gate.`、`Merge.`）→ `## Close the program` → 附录 A–D。模板里嵌了一段逐字使用的 30 分钟巡检 tick 提示词，以及 forge、rebase、`/deslop`、`/no-comments`、Bugbot 分诊等 PR 机制条目。

**连线：** `SKILL.md` 路由。它调用 prototype playbook、poteto-agent 子代理、technical-writing、unslop、check-plan.mjs；生成的计划再指名 autopilot-full、autopilot-stack 或 orchestrate 作为执行 playbook（交接），并在 `### Arm the program` 要求每 tick 从 trunk 重读执行 playbook、`swarm/SKILL.md`、控制技能、`opening-a-pr.md` 和其他叶子技能。

### 2.10 `playbooks/worktree-cleanup.md`

**结构：** 归属句 + 为什么要闸门 → 6 步 → 一句 `This is the one playbook that deletes user state with no code review to catch a slip, so the gates above are the review.` → `**Reply:**`。

**内容：** 第 1 步 `df -h /` 快照后运行 `scripts/worktree-audit.sh`（引 principle-build-the-lever；路径取自 `git worktree list` 而非手打，引 principle-encode-lessons-in-structure），转录扫描慢所以放后台。第 2 步 `The bucket is advice, not permission.`，以用户 pin 的聊天为准（引 principle-prove-it-works），并记下一次教训：`The lever has marked safe a worktree the user had pinned, so the pinned set wins.` 第 3 步对 `verify-recent-chat` 行派子代理读转录（引 principle-guard-the-context-window）。第 4 步 `wip:N` 暂停问用户，`scratch:N` 可删但要列出文件，并引 `SKILL.md` `## Autonomy`（`Per Autonomy`）。第 5 步删除命令。第 6 步模拟器与缓存清理命令。

---

## 3. 脚本（lever）解剖（问题 2、3 与额外问题）

**归属：** 全部脚本放在 poteto-mode 技能自己的 `scripts/` 下，不按 playbook 分目录，由一个 `package.json`（名为 `@cursor-skill/poteto-mode-tools`）统一管依赖和测试。原文没有给其他技能的脚本；推断：pstack 把脚本视为 mode 技能的共享工具，由各 playbook 用相对路径 `scripts/...` 调用。

### 3.1 `scripts/orch/`（orch.ts + store.ts + orch.test.ts）

**被谁调用：** 只有 `orchestrate.md`。第 2 步 `Run orch init` 与 `orch frontier set --repo <repo-dir>`；`#### Queue and drain` 的 `orch inbox push <agent> <unit> <status> [--report PATH]`、`orch inbox drain`、`orch unit add`、`orch unit set`、`orch ledger record`、`orch status`；`#### Verification` 的 `orch ledger check`；`#### Liveness and failure` 说明锁的行为。

**管什么：** 只管状态。子命令：`init`；`unit add|set|get|list|counts`；`ledger record|check|summary`；`inbox push|drain [--peek]|count`；`gate park|list|resolve`；`frontier set|show`；`status`；`standing show|add`。全局选项 `--store <dir>`（或环境变量 `ORCH_STORE`）、`--json`、`--force`（抢锁）。

**不管什么：** 原文 `The CLI never spawns, waits, or wakes anything.`（orchestrate.md `#### Roles and placement`）。代码核对一致：store.ts 只读写文件，唯一的外部进程是 `gt --no-interactive log short --stack --reverse`、`gt --no-interactive info <branch>` 和 `git rev-parse`（`graphiteFrontier`、`graphitePullRequest`、`branchSha`）。它不做判断：`unit` 的 `state` 是任意非空字符串（`requiredCell(params.state, "state")`，没有枚举）；排空时对 inbox 指针的分类（landed、needs-verify 等）由协调者做，`inbox drain` 只是原子地取走全部指针（`rename` 整个 inbox 目录再重建）。它做的只是校验：verdict 必须是五个值之一（`parseVerdict`）、TSV 表头和列数、`gates.md` 与 `preferences.md` 的格式、frontier pin 顺序不符时报错（`validateFrontierPin`），以及派生量（`lowestUnmerged` 取第一个 `OPEN`，`status` 与上一次 `<!-- orch-summary ... -->` 注释比较得出 `changed`）。

**持久状态：** store 目录下 `units.tsv`、`ledger.tsv`（以 PR + SHA 为键，同键覆盖）、`inbox/*.tsv`（每个指针一个文件）、`gates.md`、`preferences.md`（编号行，`standing add` 追加）、`frontier.json`（每次 `set` 代数 +1）、`status.md`（由 `status` 生成）。所有写都是临时文件加 `rename` 的原子写（`atomicWrite`）。写操作先取 `.orch.lock`（内容为 pid）；持锁进程已死则自动替换（`holderIsDead` 用 `process.kill(pid, 0)`），活着则报错，除非 `--force`。`init` 幂等（`writeIfMissing`）。

**与 playbook 的差异（原文对照）：** orchestrate.md `#### Store layout` 列了 9 个文件，其中 `overview.md` 和 `decisions.tsv` 不由 orch 创建或写入（`init` 只建 6 个文件和 `inbox/`）。orchestrate.md 说遇到重复指令时 `append the line before you act`，但没点名 `orch standing add`；`#### Liveness and failure` 要求 `write a stop line at the top of the standing orders`，而 `standing add` 只能追加到末尾且 `readStanding` 要求编号连续。推断：「置顶停止线」要靠手工改文件并重排编号，CLI 不支持。

**接口：** 默认输出紧凑文本（TSV 行，列表最多显示 4 行，超出提示 `... N more; use --json`；`status` 输出三行 `counts:` / `changed:` / `gates open:`，正好对应 orchestrate 的 `A drain turn ends with the three lines from orch status`）；`--json` 输出完整 JSON（缩进 2）。退出码（`handleError`）：0 成功；1 用法错误或用户错误（错误信息与帮助写 stderr）；2 未找到（`NotFoundError`，包括 `ledger check` 查无记录时输出 `NOT-VERIFIED`，JSON 模式为 `{"pr","sha","verdict":"NOT-VERIFIED"}`，stderr 为空）。

**测试：** `orch.test.ts` 用 `bun:test`，覆盖 init 幂等与锁释放、unit 组合操作（含以 `=`、`+` 开头的单元格被加 `'` 前缀防表格公式注入）、ledger 覆盖与 NOT-VERIFIED、inbox 原子排空、死锁替换与 `--force` 抢锁、gate 与 standing 与 status 的 `changed` 文本、用 PATH 里的假 `gt` 脚本和真实临时 git 仓库测 frontier 顺序与 pin 不符、Graphite 输出不可解析时报错、各文件格式损坏时报错、关闭后拒绝操作；CLI 部分测 `--help`、`ORCH_STORE`、`--json` 与退出码 0/1/2。

### 3.2 `scripts/watch-pr/`

**被谁调用：** `babysit.md` 第 6 步（`On GitHub, status comes from scripts/watch-pr/watch-pr. Run it directly.`；`check` 模式加 `--status-only`；`drive` 用裸命令轮询到终态），`shipping.md` 第 8 步（`--queued-stack --stack-prs <bottom>`，只作事件唤醒）。babysit 的 `**Reply:**` 要求 `the watcher's four-column table on GitHub`，对应 `render.ts` `renderStatusTable` 的 `| PR | CI | Review | Merge |`。

**管什么：** 只读 GitHub 并做合并就绪判定，不写任何东西、不合并、不重跑 CI。判定是真正的判断逻辑，写在代码里：

- `policy.ts` `classifyPr` 与 `selectTierMajorStackDecision` 按层优先：冲突 → review threads → 失败 checks → merge gate（closed、draft、changes requested）→ pending → ready。stack 模式是「按层扫描」：上游 PR 的冲突优先于 frontier 的 CI 失败（测试 `scans stacks tier-major so an upstack conflict outranks frontier CI`）。这与 babysit.md 第 5 步 `Order is conflicts, then review threads, then CI.` 是同一规则的代码版。
- `assessGitHubMerge`：`mergeStateStatus` 为 `BLOCKED` 且 head rollup 为 `ERROR`/`FAILURE` 时判为 GitHub 拒绝（`ci-github-rejected`），即使可见 check 列表全绿。对应 babysit 第 6 步 `Trust the active forge's verdict, not a green check list.`
- `github.ts` `pendingOrGate`：名为 `Code Review Gate` 的 check 不算 pending，注释写明理由：算成 pending 会让 watcher 等人。对应 babysit 第 9 步 `Owner approval is a wait, not a blocker to fix.`
- Bugbot 线程识别与「pass 次数」计数（`isBugbot`、`passKey` 取 `RUN_ID:` 或 `CURSOR_AUTOMATION_ID:`），供 babysit 第 8 步 `use the watcher's Bugbot pass count`。
- 解析全部「失败即关」：未知枚举值抛 `WatcherQueryError`（`missing-key`，可重试，带原值）；两条 check 读取路径都为空则 `ChecksUnavailable`。

**三种模式：** `single`（默认）、`--stack`（从 `gh pr list` 按 base/head 关系排出连接的 stack，`orderStack`）、`--queued-stack`（冻结的自底向上列表，`--stack-prs` 只在此模式可用）。queued 模式是一个纯函数状态机（`createQueueState`、`planQueue`、`applyQueueSnapshot`、`evaluateQueue`）：周期性全量 sweep（默认 300 秒）之间只轮询 frontier；相同等待只发一次（`lastWaitKey`）；frontier 变化发 `ADVANCE` 且不睡眠直接读新 frontier；sweep 中某个 PR 读取失败后从该 PR 续读（测试 `resumes the sweep at the PR whose read failed`）。

**接口：** 选项 `--owner`、`--repo`、`--pr`、`--stack`、`--queued-stack`、`--stack-prs <n,...>`、`--interval`（默认 60）、`--sweep-interval`（默认 300）、`--timeout`（默认 0 即不限）、`--max-query-errors`（默认 5）、`--status-only`、`--allow-draft`、`--pretty`。输出：默认 JSON，轮询时是 NDJSON（每个进度事件一行，最后一行是终态 verdict），帮助文本原文 `JSON (NDJSON while polling) is the default; --pretty renders human text.` 每个事件带 `schemaVersion: 1`、`sequence`、`observedAt`、`mode`、`kind`、`terminal`。进度事件：`QUEUE`、`STATUS`、`WAITING`、`ADVANCE`、`RETRY`。终态与退出码（`types.ts` 以类型绑定）：`STATUS`/`READY`/`COMPLETE` → 0；`BLOCKER` merge-conflicts → 2、review-threads → 3、failing-checks → 4、merge-gate → 6、status-query → 7；`TIMEOUT` → 5；参数错误 → 64（`EX_USAGE`）。`READY` 只可能在 single/stack 模式出现，`COMPLETE` 只在 queued-stack 模式出现（类型参数限定）。查询失败按 `queryBackoffSeconds` 退避：`min(max(interval,60) * 2^(n-1), 300)`。

**测试：** `policy.test.ts`（就绪真值表、快照查询计划即 pending 时不查 commit rollup、按层扫描、等待归属到真正 pending 的 PR、draft 先等后拦、queued 节奏的五个用例、退避上下限）；`github.test.ts`（check 读取两级回退、rollup 节点映射、枚举严格解析、`reviewDecision` 空串视为 null、Bugbot pass 计数、context 推断、stack 排序）；`cli.test.ts`（默认值、非法参数一律 64 且 stdout 为空、JSON 与表格渲染、queued + status-only 绕过状态机、隐藏的 GitHub 拒绝返回 4、`--help` 不触碰 reader）；`types.compile.ts` 用 `@ts-expect-error` 证明四种非法状态不可构造，由 `package.json` 的 `typecheck`（`tsc --project watch-pr/tsconfig.json --noEmit --strict`）执行。测试全部用 `fakes.test-helper.ts` 的假 reader 与假时钟，不访问网络。

**代码注释里的历史：** `types.ts` 的 `WaitingDecision` 注释提到 `That is the Python watcher's contract`，`github.ts` 的 `pendingOrGate` 注释提到 `the behaviour #172004 removed from the Python`。推断：watcher 由一个更早的 Python 版本移植而来。

### 3.3 `scripts/check-plan.mjs`

**被谁调用：** `multi-phase-plan.md` 第 6 步，路径写作 `node pstack/skills/poteto-mode/scripts/check-plan.mjs <plan.md>`（相对仓库根，而其他 playbook 写 `scripts/...` 相对技能目录）。

**管什么：** 只查计划文件的结构与文风，不判断内容好坏。检查项与模板一一对应：无长破折号、无弯引号、无「冒号后接非空白」（即 mid-sentence colon）；有 H1、`## How to read this` 含五个标记串（包括验证规则全文）；引言少于十行；`## Program checklist` 按序含五个 H3 和四个标记（`/goal`、`git show origin/main:`、`30 minute`、`status message`）；每个 PR 节恰好 9 个加粗子块且顺序一致；三个 Verify 块以规则全文开头；live 块含 `Ten lanes on grok-4.7-xhigh-fast at the PR head` 且恰有 Lane 1–10，每条有 `Save \`...\`` 和 `Pass when`；perf 块四项依次为 `Metric.`、`Probe.`、`Baseline.`、`Rule.`；Review gate 为 `None.` 时不得有方框，否则须含 screenshot、video、operator；`## Close the program` 之后只能是附录且须有 Prototype evidence。

**接口：** stdout 每个 PR 一行方框计数 + 一行 `N PR sections, M problems`；stderr 每个问题一行 `file:line: message`；退出码 0 无问题、1 有问题、2 缺参数。没有测试。

**性质：** 这是 `principle-encode-lessons-in-structure` 的直接实现（multi-phase-plan 第 6 步括注），也把 playbook 里的规则文本复制成了代码常量（见第 5 节）。

### 3.4 `scripts/worktree-audit.sh`

**被谁调用：** `worktree-cleanup.md` 第 1 步。

**管什么：** 只读审计，文件头注释原文 `Never deletes anything; deletion stays a human-gated step in the playbook.` 对每个非主 worktree 输出 `SIZE AGE MERGED DIRTY REMOTE PR LAST_CHAT BUCKET WORKTREE`（TSV，按大小降序）。它给出一个建议分桶（`hold-wip`、`hold-open-pr`、`verify-recent-chat`、`safe`、`review`），这是一个粗判断，playbook 第 2 步明确把它降为建议。它不知道用户 pin 了哪些聊天，这一缺口靠 playbook 文字补（第 2 步）。

**接口与依赖：** 参数可选 `[repo-path]`；不在仓库里时 stderr 报错退出 1；`git fetch` 失败只警告。依赖 `gh`、`jq`、`rg`，并用 BSD 形式的 `stat -f` 与 `date -r`（推断：只在 macOS 上按预期工作）。转录目录由主 worktree 路径推出：`~/.cursor/projects/<slug>/agent-transcripts`。没有测试。

### 3.5 `scripts/bootstrap.ts`、`package.json`、`bun.lock`

`bootstrap.ts` 的 `ensureDependenciesInstalled` 以 `package.json` 与 `bun.lock` 内容的 sha256 作为安装键，键不符或 `commander` 缺失时运行 `bun install --frozen-lockfile`，写键文件，然后以相同参数重新执行当前进程并以其退出码退出。被 `orch/orch.ts` 和 `watch-pr/watch-pr` 在导入 `commander` 之前调用。推断：目的是让技能目录被复制到任何机器后，第一次调用脚本即可自举，无需单独的安装步骤。`package.json` 的 `test` 是 `bun test orch watch-pr`，`typecheck` 只覆盖 `watch-pr/tsconfig.json`；推断：`orch/` 不在类型检查命令范围内。`check-plan.mjs`、`worktree-audit.sh`、`bootstrap.ts` 不在测试命令范围内。

---

## 4. 边界判据（问题 4）

以下判据中，凡原文有明说的给出引文；多数判据原文没有写成规则，是我从写法归纳的，均标「推断」。

### 4.1 什么让一段内容成为 playbook 而不是技能

- **playbook 按任务类型划分，技能按能力划分。** `SKILL.md` `## Playbooks` 的每个条目以任务类型命名并给出用户的话（`"run until done", "/loop until X"`、`"autopilot this queue"`）；被调用的技能则以能力命名（swarm：`Fan out N parallel workers, drain them, and return one report.`；show-me-your-work：`Keep a reviewable decision trail ...`）。推断：一个 playbook 是「为某类任务把若干能力按顺序串起来，并规定谁拥有什么、何时停、回复什么」；一个技能是「一种可被多个 playbook 复用的做法」。
- **playbook 没有独立入口。** 没有 frontmatter，不能被描述匹配；必须在 `/poteto-mode` 的上下文里执行（`agents/poteto-agent.md` 要求先 `Read the poteto-mode skill's SKILL.md in full`），依赖 `SKILL.md` 的待办清单规则、`## Autonomy`、`## Subagents`、`## Writing the reply`。例如 worktree-cleanup 第 4 步只写 `Per Autonomy`，不重述规则。推断：playbook 可以省略通用规则正是因为它总在 mode 之下运行。
- **能力技能自带的 Step/Phase 为什么没拆成 playbook。** swarm（`## Phase A: Frame` 到 `## Phase D: Report`）、figure-it-out（Phase A–E）、show-me-your-work 都有内部多步流程。推断：这些步骤是「完成这一种能力」的方法，不含任务归属、停止条件或回复合同，而且被多个 playbook 调用（swarm 被 autopilot-full 第 4 步、multi-phase-plan 模板调用；show-me-your-work 被 autonomous-run、orchestrate、autopilot-*、pause-safely 调用）。拆成 playbook 反而会失去复用。figure-it-out 本身是「设计 playbook 的能力」（`When the task matches no playbook, design one.`），所以它是技能，产物才是 playbook。
- **反例：babysit 与 shipping 装了大量做法，仍是 playbook。** 它们是「PR 状态请求」「落地请求」这两类任务的全部内容，而且只有它们自己用这些做法；其他 playbook 通过「让 owner 跑 babysit 循环」「按 shipping 的 patch-id 规则」来复用它们。推断：pstack 在这里接受 playbook 装做法，条件是该做法只属于这一类任务；需要复用时，别人引用 playbook 的文件名或步号，而不是把做法抽成技能。

### 4.2 什么让内容成为原则而不是调用方里的一条规则

- **原则是领域无关的立场，调用方写的是它在本领域的具体用法。** 例：worktree-cleanup 第 1 步写具体规则「路径取自 `git worktree list`，不手打」，括注 `(principle-encode-lessons-in-structure)`；principle-build-the-lever 自身写的是一般立场 `Build the tool that does it or proves it ... The tool is the artifact a reviewer can rerun.`（其 frontmatter 同样是 `disable-model-invocation: true`）。推断：原则单独成技能，是因为同一立场被多处以不同具体规则落地（例如 encode-lessons-in-structure 在 orchestrate 用于 `preferences.md` 追加，在 multi-phase-plan 用于 check-plan.mjs，在 worktree-cleanup 用于路径来源），把立场写在任何一个调用方里都会让其他调用方失去出处。
- **引用方式是括注，不展开。** `SKILL.md` `## Non-negotiables` 要求 `name each principle that shaped a decision ... Cite only principles whose leaf SKILL.md you read this session.`，`## Principles` 要求 `Read the leaf skill in full for any principle you apply.` 推断：调用方只给指针，理由在叶子技能里，避免同一理由在多处漂移。
- **仍写在调用方正文、没有抽成原则的规则（逐条）：**
  - forge 选择规则（`gh` 默认、Origin 可用则用、`Never require Graphite`）：babysit 第 1 步、shipping 第 1 步、autopilot-full 第 2 步、autopilot-stack 第 1 步、multi-phase-plan 模板 `### PR mechanics`。
  - patch-id 重验规则：shipping 第 3 步（其他文件引用它）。
  - rebase 时机规则（code-ready 前 rebase 一次，之后只在 merge prep、`git merge-tree` 冲突或 trunk 引起的 CI 失败时再 rebase）：autopilot-full 第 2 步、multi-phase-plan 模板 `### PR mechanics`。
  - 只以副作用计进度、超时无副作用即判卡住并替换：autopilot-full 第 6 步、autopilot-stack 第 2 步、multi-phase-plan 巡检提示词。
  - 操作者停止即零写入：autopilot-full 第 7 步、autopilot-stack 第 3 步、multi-phase-plan `### Arm the program`。
  - CI 失败分类与只重试一次：babysit 第 7 步；按失败模式重试两次后放弃：orchestrate `#### Liveness and failure`。
  - 升级清单（只上报不可逆动作、无法用实验决定的产品偏好、死路）：autonomous-run 第 4 步、orchestrate `#### Escalation`，与 `SKILL.md` `## Autonomy` 的 `Always pause` 和 principle-never-block-on-the-human 的描述重叠。
  - 「不 resume 旧代理，用合并范围重新派」：orchestrate `#### The brief`（`Never resume-chain a brief. Respawn fresh with consolidated scope.`）与 `SKILL.md` `## Subagents`（`fire a fresh subagent with consolidated scope`）。
  推断：这些规则都绑定 PR、forge、代理队列等具体机制，不是领域无关的立场，所以没有成为原则；但它们也没有被收进一个共享 reference，于是形成了第 5 节列的重复。

### 4.3 什么让内容成为 reference 而不是正文

- 本批 playbook 只引用一个 reference：`references/bugbot-triage.md`（142 行，我只读了开头和全部标题）。它是一个分类表加「已学到的模式」目录，有固定条目格式，被 babysit 第 8、9 步、autopilot-full 第 2 步、autopilot-stack 第 1 步、multi-phase-plan 模板四处引用，而且 babysit 第 9 步要求把新模式作为候选条目以独立 PR 追加进去。推断：reference 的判据是「只在某个条件出现时才需要查（有 Bugbot 评论时）、会随经验增长、有多个调用方」。
- 反例：orchestrate 的 brief 模板和 multi-phase-plan 的 138 行计划模板都是 reference 形状的内容，却留在 playbook 正文里。推断：它们各只有一个调用方，而且就是该 playbook 的产物本身（「The brief is the product」「The plan is the deliverable」）；multi-phase-plan 的模板还有 check-plan.mjs 做机器检查，拆出去不减少任何重复。

### 4.4 什么让内容成为脚本而不是文字

从四个脚本归纳（推断），脚本出现在四种情形，每一种原文都给了对应的原则或理由：

1. **多个写者共享、需要跨会话存活的状态**：orch。原文 `Every file has exactly one writer.`、`State reads and writes go through scripts/orch/orch.ts at drain points, one command in and one line out.`，以及锁与原子写。
2. **要轮询外部系统并对结果做分类的判断**：watch-pr。判断规则（冲突 → threads → CI）同时写在 babysit 文字和 policy.ts 代码里，代码负责在每次轮询时一致地执行，文字负责告诉代理在哪种 verdict 下做什么、何时停。
3. **对产物格式的机器检查**：check-plan.mjs，multi-phase-plan 第 6 步括注 encode-lessons-in-structure。
4. **批量、只读的数据收集**：worktree-audit.sh，worktree-cleanup 第 1 步括注 build-the-lever。

脚本之外保留为文字的，是需要判断且后果不可逆的部分：排空时对指针的分类、是否合并、是否删除、何时升级。worktree-cleanup 第 2 步把脚本的分桶明确降为建议，就是这条边界的原文体现。

---

## 5. 重复与例外（问题 5）

### 5.1 同一规则多处重复

| 规则 | 出现位置 |
|---|---|
| forge 选择 + `Never require Graphite (gt)` | babysit 第 1 步；shipping 第 1 步；autopilot-full 第 2 步；autopilot-stack 第 1 步；multi-phase-plan 模板 `### PR mechanics`（五处近乎逐字） |
| owner 生命周期（ready PR 不开 draft、15 分钟内开 `decisions.tsv`、`/deslop`、`/no-comments`、Bugbot 分诊、babysit 到绿） | autopilot-full 第 2 步；autopilot-stack 第 1 步（逐字大段，`children.tsv` 一项改为转引）；multi-phase-plan 模板 `### PR mechanics` |
| rebase 时机规则 | autopilot-full 第 2 步；multi-phase-plan 模板 `### PR mechanics` |
| 30 分钟巡检 tick 与副作用计进度 | autopilot-full 第 6 步；autopilot-stack 第 2 步（大半逐字，末尾转引 autopilot-full 第 6 步）；multi-phase-plan 巡检提示词 |
| state-then-wait 与零写入停止 | autopilot-full 第 1、7 步；autopilot-stack 第 3 步；multi-phase-plan `### Arm the program` |
| swarm 轮次与 lane 组成、Regression lane against trunk 的措辞 | autopilot-full 第 4 步；multi-phase-plan `**Verification.**` 段、模板 `### Verdict and merge`、模板 Lane 1 |
| 验证规则全文 `Tests alone are not sufficient verification. ...` | multi-phase-plan 正文 1 次、模板 4 次（`## How to read this` 与三个 Verify 块）、check-plan.mjs 常量 `RULE`。原文有意为之：`That sentence is the verification rule. Every verification block opens with it.` |
| live lane 数量与模型 `Ten lanes on grok-4.7-xhigh-fast` | multi-phase-plan 正文、模板、check-plan.mjs 常量 `LANES` |
| 冲突 → threads → CI 的顺序 | babysit 第 5 步（文字）；watch-pr `policy.ts` `selectTierMajorStackDecision`（代码） |
| 升级清单 | autonomous-run 第 4 步；orchestrate `#### Escalation`；`SKILL.md` `## Autonomy` |
| 重新派而不 resume | orchestrate `#### The brief` 与 `#### Liveness and failure`；`SKILL.md` `## Subagents` |
| babysit 不授权合并 | babysit 第 6 步与第 9 步各说一次；`SKILL.md` 触发列表再说一次 |

推断：pstack 对「规则放哪」有两种解法并存。一种是单一出处加引用（patch-id 规则放 shipping 第 3 步，其他文件按文件名引用；autopilot-stack 按步号引 autopilot-full），另一种是逐字复制（forge 选择、owner 生命周期）。后者多出现在「会被子代理或巡检 tick 单独读取的文件」里；推断原因是 autopilot 的 root 每个 tick 只从 trunk 重读自己的 playbook 文件（`git show origin/main:.../autopilot-full.md`），owner 是云代理，只看到自己的 brief，所以需要的规则被复制到它们确定会读的那份文本里。这一点原文没有明说。

### 5.2 pstack 自己的分层例外

1. **playbook 里写做法（技术细节）。** babysit 第 6 步的 forge 专属停止条件与第 8 步的精确回复命令；shipping 第 3 步 patch-id 噪声判断的构建方法与第 8 步 GitHub 状态字段判据；worktree-cleanup 第 5–6 步的删除与缓存清理命令。它们没有被抽成技能或 reference（见 4.1 的反例说明）。
2. **playbook 里装模板与状态规格。** orchestrate 的 `#### Store layout` 与 `#### The brief`，multi-phase-plan 的 138 行模板。
3. **playbook 之间按步号互相依赖。** autopilot-stack 引 `Autopilot-full step 2`、`step 4`、`step 6`；multi-phase-plan 引 `the rule at the end of playbooks/autopilot-stack.md`。推断：步号变动会让引用失效，且没有脚本检查这些引用。
4. **原则引用写法不统一。** 同一批文件里有三种格式：`(principle-build-the-lever)`（orchestrate、worktree-cleanup）、`(the **principle-guard-the-context-window** skill)`（session-pickup）、`(the **guard-the-context-window** principle skill)`（multi-phase-plan、autonomous-run、autopilot-full）。
5. **Cursor 内置 `/loop` 的称呼不统一。** autonomous-run 第 2 步 `Cursor's /loop command (a built-in, not a pstack skill)`；orchestrate `#### Queue and drain` 写 `arm it via the loop skill`。
6. **脚本路径写法不统一。** multi-phase-plan 第 6 步 `node pstack/skills/poteto-mode/scripts/check-plan.mjs`（相对仓库根）；babysit、shipping、orchestrate、worktree-cleanup 写 `scripts/...`（相对技能目录）。
7. **orchestrate 依赖 Graphite，其他 playbook 禁止依赖 Graphite。** orchestrate `#### Stack safety`：`Recompute frontier.json from gt after every merge and stack mutation`，`Exactly one stacker per stack may run gt`，且 `orch frontier set` 在代码里只能通过 `gt` 取得 stack（`graphiteFrontier`）；而 babysit、shipping、autopilot-*、multi-phase-plan 都写 `Never require Graphite (gt)`。orchestrate 的 brief 模板 `FORBIDDEN` 写 `no gt`，那是对 worker 的禁令，不针对 stacker。推断：orchestrate 与其余 PR 类 playbook 处在两个不同的 forge 假设下，没有统一。
8. **模型名写死，绕过配置。** `SKILL.md` `## Subagents` 说模型由 `/setup-pstack` 按角色配置、可覆盖技能默认值；multi-phase-plan 与 check-plan.mjs 把 live lane 模型写死为 `grok-4.7-xhigh-fast`，check-plan 对其他值报错。推断：计划文件里的 live lane 模型不受 `/setup-pstack` 影响。
9. **自己施加的文风规则自己没全遵守。** `SKILL.md` `## Writing the reply` 禁止 mid-sentence colon（`unslop rule 14`），`Any prose surface → the unslop skill`；check-plan.mjs 对计划文件执行这条。但这批 playbook 正文有多处此类冒号，例如 babysit 第 6 步 `stop drive when the frontier is merge-ready: checks are green`、orchestrate `#### Roles and placement` `unless the task needs this machine: control-ui`、autopilot-full 第 4 步 `The lanes: re-run the gates`、session-pickup 第 4 步 `pick the verdict: continue the execution`。推断：该规则在实践中只对回复和计划机器检查，playbook 本身不在检查范围内（unslop 技能全文我没读，规则 14 的确切范围未核实）。
10. **规则与状态机代码的小出入。** shipping 第 8 步要求用 `--queued-stack` 时 `ignoring READY until mergedAt is non-null`，但 `types.ts` 规定 queued-stack 模式不可能发出 `READY`（babysit 第 6 步也写了 `Queued mode never emits READY`）。推断：shipping 这句是多余的防御性说法。
11. **worktree-cleanup 把一条教训留在文字而没进脚本。** 第 2 步 `The lever has marked safe a worktree the user had pinned`，修正方式是文字闸门，而 worktree-audit.sh 的分桶逻辑至今不知道 pin 状态。推断：pin 信息只在 Cursor 侧边栏，不可由脚本读取，所以这是 encode-lessons-in-structure 做不到时的退路。

---

## 6. 状态与重入（问题 6）

| 组件 | 中断后如何继续 | 待办 / 跳步 | 持久状态放在哪 |
|---|---|---|---|
| 所有 playbook（经 `SKILL.md`） | — | 编号步骤逐字抄进待办清单，不做的步骤保留并写 `skip: <reason>` | 待办清单（会话内） |
| babysit | 每次推送波次后、每次据 verdict 行动后重新 arm watcher；queued stack 的 PR 列表一次捕获、每次 rearm 传同一冻结列表，只为第 4 步的 follow-up PR 修订 | 模式声明决定走哪些步骤（`check` 只做一次状态） | 不落盘；冻结列表在代理手里，watcher 每次调用无状态 |
| shipping | 每次合并后重算（第 7 步）；patch-id 让旧 verdict 在 rebase 后仍可判定有效 | 扩展已验证段落 = 从第 1 步重新走一遍（第 9 步） | verdict 贴在各自 PR 上（第 1 步）；记录的 SHA 与 patch-id 存哪原文未写 |
| autonomous-run | `/loop` 事件唤醒加心跳；每轮提交或丢弃 | 平台期继续，不停 | show-me-your-work 记录每轮一行；git 提交 |
| orchestrate | 完整恢复规程：Cursor 重启后本地代理已死、云端未死，重读 standing orders 与 `units.tsv`，重算 frontier，按 PR 和分支（而非代理 id）重新挂接云端工作，按存储的 brief 加当前状态重派每个 track 的子协调者；锁持有进程已死则下次写时自动替换；自身重试耗尽时写终止交接（已完成什么、在哪、恢复命令） | 第 1 步可整体「collapse」为不用 store 的直接做法，并且 `Collapsing must not depend on another document being present.` | `orchestrate/<project-slug>/` store（orch 管理其中 6 个文件与 `inbox/`，另有 `overview.md`、`decisions.tsv`、生成的 `status.md`）；`Leave the store intact. It is the postmortem.` |
| autopilot-full / autopilot-stack | `/goal` 跨回合延续；每个 tick 从 trunk 重读 playbook 与 `/goal` 并修正漂移；卡住的 lane 立即替换，`A stall never proves or drops the work.` | 操作者保留项停在 merge-ready | 每个 owner 未提交的 `decisions.tsv` 与 `children.tsv`，随报告返回；PR 本身 |
| session-pickup | 它就是重入入口：以旧记录为权威输入，不重做，找出恢复点后交给对应 playbook | 第 4 步后本 playbook 结束 | 读 `agent-transcripts/`、云代理 URL 或已推分支 |
| pause-safely | 它是暂停出口：安全边界停下，`wip:` 提交，恢复笔记 | 只在显式要求时执行；「keep going」类话语不执行 | `wip:` commit；`/tmp/<slug>-resume.md` 或已有 show-me-your-work 记录 |
| multi-phase-plan | 计划文件本身是可重入的清单：`Check a box only when its evidence exists`；每个 tick 从 trunk 重读执行 playbook 与各技能 | 第 1 步可跳过整个计划；模板要求填满每个占位符 | 计划文件（默认在代理 store 的 `docs/`）；`/goal` |
| worktree-cleanup | 无重入设计；每步前后 `df -h /` 与重新列出 | `wip` 与使用中的项暂停问人 | 无 |
| orch（脚本） | 幂等 `init`；原子写；死锁自动替换；`ledger record` 同键覆盖 | — | store 目录的纯文本文件 |
| watch-pr（脚本） | 单次调用内：查询失败退避重试，sweep 从失败处续读；跨调用无状态 | — | 仅内存（`QueueState`） |

---

## 7. 额外问题：长 playbook 为什么长

**多出来的不是步骤。** orchestrate.md 111 行里，`#### Steps` 只有 7 行（第 60–66 行）；其余是角色（`#### Roles and placement`）、状态存储规格（`#### Store layout`）、brief 输出模板与规则（`#### The brief`）、排空协议（`#### Queue and drain`）、并发写入规则（`#### Stack safety`）、验证词汇与外置规则（`#### Verification`）、恢复规程（`#### Liveness and failure`）、升级规则（`#### Escalation`）。multi-phase-plan.md 156 行里，步骤 7 行，验证与控制技能规则 2 段，模板 138 行（输出格式）。autopilot-full.md 行数少但词数第三（1436 词），因为第 2 步（owner 生命周期）和第 6 步（root 巡检、会签、卡住检测）各是一整段规则。

对照短 playbook：autonomous-run、session-pickup、pause-safely 只有「步骤 + 每步一两句理由」，没有角色、没有共享存储、没有多代理并发。推断：长度来自「多个代理 + 跨会话 + 共享状态」这三个条件，每多一个条件就多一类内容（角色与分工、存储与单写者、恢复与重入、升级边界）。

**为什么这些内容留在 playbook 里，没拆成技能或原则（原文无直接说明，以下为推断，附依据）：**

1. **只有一个调用方。** brief 模板、store 布局、drain 协议只被 orchestrate 用；计划模板只被 multi-phase-plan 用。拆出去不会减少重复。
2. **需要被原样整份重读。** autopilot 的巡检 tick 用 `git show origin/main:.../autopilot-full.md` 重读自己；multi-phase-plan 的 tick 要重读执行 playbook。把规则拆散会增加每个 tick 要读的文件数，且更容易漏读。
3. **降级路径要求自足。** orchestrate 第 1 步：`Collapsing must not depend on another document being present.`
4. **状态机的机械部分已经拆出去了。** 需要一致执行的部分（文件格式、锁、原子写、verdict 枚举、frontier 代数）进了 `scripts/orch/`；留在文字里的是需要判断的协议（何时排空、如何分类指针、何时升级）。原则则以括注方式引用（separate-before-serializing-shared-state、encode-lessons-in-structure），说明作者确实把可泛化的立场抽到了原则，把只属于本程序的机制留在了 playbook。
5. **orchestrate 明确不想要固定结构。** `Hard-coded swarm trees were tried and parked as too rigid.` 以及 `Author the track decomposition per project`。推断：把角色和分工写成可复用技能会把某种树形固定下来，这是作者试过并放弃的方向。

**脚本对照一览（额外问题）：**

| 脚本 | 归属 | 调用它的 playbook 与步骤 | 只管状态还是做判断 | 接口 | 测试 |
|---|---|---|---|---|---|
| `scripts/orch/orch.ts` | poteto-mode | orchestrate 第 2 步、`#### Queue and drain`、`#### Verification` | 只管状态与格式校验，不分类、不派代理、不唤醒 | 嵌套子命令；默认紧凑 TSV 行，`--json` 完整 JSON；退出 0/1/2 | 有（bun） |
| `scripts/watch-pr/watch-pr` | poteto-mode | babysit 第 6 步；shipping 第 8 步 | 只读，但做合并就绪判断与阻塞优先级 | 选项式；默认 JSON / 轮询时 NDJSON，`--pretty` 文本；退出 0/2/3/4/5/6/7/64 | 有（bun + 编译期类型测试） |
| `scripts/check-plan.mjs` | poteto-mode | multi-phase-plan 第 6 步 | 只判断结构与文风合规，不判断内容 | 单个位置参数；stdout 摘要、stderr `file:line: message`；退出 0/1/2 | 无 |
| `scripts/worktree-audit.sh` | poteto-mode | worktree-cleanup 第 1 步 | 只读收集，给建议分桶（playbook 降为建议） | 可选仓库路径；TSV 表；退出 0/1 | 无 |
| `scripts/bootstrap.ts` | poteto-mode | 不被 playbook 直接调用，被 orch.ts 与 watch-pr 导入 | 依赖自举 | 导出函数 | 无 |

---

## 8. 未确定

- Cursor 内置能力 `/loop`、`/goal`、Task 工具、cloud agent、「cloud-sleeper wake chain」、「monitored-shell 30-minute sleep」与「output-notification sentinel」都不在快照里，其确切行为未核实。
- `cursor-team-kit` 插件的 `control-ui`、`control-cli`、`deslop` 不在快照里。Origin CLI（`origin pr ...`）不在快照里。
- `references/bugbot-triage.md` 只读了开头 40 行与全部标题；swarm、show-me-your-work、figure-it-out 只读了 frontmatter 与标题（figure-it-out 另读了第 9、13、53 行）；unslop 未读，所以「mid-sentence colon」规则是否覆盖 playbook 正文未核实（第 5.2 节第 9 条）。
- shipping 第 3 步要求记录的 verdict head SHA、base SHA、patch-id 存放在哪里，原文没有写明。
- 测试未运行，不知道当前能否通过；`orch/` 是否能通过严格类型检查未知（`typecheck` 只覆盖 watch-pr）。
- playbook 为什么不用 frontmatter、为什么用 H3 标题，原文没有说明；第 0 节的解释是推断。
- 逐字复制与单一出处两种写法并存的原因（第 5.1 节末），原文没有说明，是推断。

---

```edges
poteto-mode/SKILL.md -> playbooks/babysit.md : routes-to
poteto-mode/SKILL.md -> playbooks/shipping.md : routes-to
poteto-mode/SKILL.md -> playbooks/autonomous-run.md : routes-to
poteto-mode/SKILL.md -> playbooks/orchestrate.md : routes-to
poteto-mode/SKILL.md -> playbooks/autopilot-full.md : routes-to
poteto-mode/SKILL.md -> playbooks/autopilot-stack.md : routes-to
poteto-mode/SKILL.md -> playbooks/session-pickup.md : routes-to
poteto-mode/SKILL.md -> playbooks/pause-safely.md : routes-to
poteto-mode/SKILL.md -> playbooks/multi-phase-plan.md : routes-to
poteto-mode/SKILL.md -> playbooks/worktree-cleanup.md : routes-to
poteto-mode/SKILL.md -> setup-pstack : configured-by
agents/poteto-agent.md -> poteto-mode/SKILL.md : reads-reference
recall -> playbooks/session-pickup.md : routes-to
playbooks/hillclimb.md -> playbooks/autonomous-run.md : reads-reference
references/bugbot-triage.md -> playbooks/babysit.md : serves
playbooks/babysit.md -> cursor:babysit : supersedes
playbooks/babysit.md -> scripts/watch-pr/watch-pr : runs-script
playbooks/babysit.md -> references/bugbot-triage.md : reads-reference
playbooks/babysit.md -> cursor:/loop : calls
playbooks/babysit.md -> ext:gh : calls
playbooks/babysit.md -> ext:origin : calls
playbooks/babysit.md -> playbooks/shipping.md : hands-off-to
playbooks/shipping.md -> scripts/watch-pr/watch-pr : runs-script
playbooks/shipping.md -> cursor:cloud-agent : spawns-subagent
playbooks/shipping.md -> cursor-team-kit:control-ui : calls
playbooks/shipping.md -> cursor-team-kit:control-cli : calls
playbooks/shipping.md -> cursor:/loop : calls
playbooks/shipping.md -> ext:gh : calls
playbooks/shipping.md -> ext:origin : calls
playbooks/autonomous-run.md -> cursor:/loop : calls
playbooks/autonomous-run.md -> watcher-subagent : spawns-subagent
playbooks/autonomous-run.md -> principle-sequence-verifiable-units : cites-principle
playbooks/autonomous-run.md -> show-me-your-work : calls
playbooks/autonomous-run.md -> poteto-mode/SKILL.md : routes-to
playbooks/orchestrate.md -> playbooks/autonomous-run.md : routes-to
playbooks/orchestrate.md -> figure-it-out : routes-to
playbooks/orchestrate.md -> scripts/orch/orch.ts : runs-script
playbooks/orchestrate.md -> cursor:Task : spawns-subagent
playbooks/orchestrate.md -> show-me-your-work : calls
playbooks/orchestrate.md -> arena : calls
playbooks/orchestrate.md -> cursor:/loop : calls
playbooks/orchestrate.md -> playbooks/babysit.md : hands-off-to
playbooks/orchestrate.md -> principle-separate-before-serializing-shared-state : cites-principle
playbooks/orchestrate.md -> principle-encode-lessons-in-structure : cites-principle
playbooks/orchestrate.md -> cursor-team-kit:control-ui : calls
playbooks/orchestrate.md -> cursor-team-kit:control-cli : calls
playbooks/orchestrate.md -> ext:gt : calls
playbooks/autopilot-full.md -> cursor:/goal : calls
playbooks/autopilot-full.md -> cursor:/loop : calls
playbooks/autopilot-full.md -> cursor:cloud-agent : spawns-subagent
playbooks/autopilot-full.md -> principle-prove-it-works : cites-principle
playbooks/autopilot-full.md -> references/bugbot-triage.md : reads-reference
playbooks/autopilot-full.md -> cursor-team-kit:deslop : calls
playbooks/autopilot-full.md -> no-comments : calls
playbooks/autopilot-full.md -> playbooks/babysit.md : calls
playbooks/autopilot-full.md -> show-me-your-work : calls
playbooks/autopilot-full.md -> swarm : calls
playbooks/autopilot-full.md -> cursor-team-kit:control-ui : calls
playbooks/autopilot-full.md -> cursor-team-kit:control-cli : calls
playbooks/autopilot-full.md -> playbooks/shipping.md : defers-rule-to
playbooks/autopilot-full.md -> playbooks/autopilot-full.md : reads-reference
playbooks/autopilot-stack.md -> playbooks/autopilot-full.md : defers-rule-to
playbooks/autopilot-stack.md -> playbooks/shipping.md : defers-rule-to
playbooks/autopilot-stack.md -> playbooks/babysit.md : calls
playbooks/autopilot-stack.md -> references/bugbot-triage.md : reads-reference
playbooks/autopilot-stack.md -> cursor-team-kit:deslop : calls
playbooks/autopilot-stack.md -> no-comments : calls
playbooks/autopilot-stack.md -> show-me-your-work : calls
playbooks/autopilot-stack.md -> cursor:/goal : calls
playbooks/autopilot-stack.md -> cursor:/loop : calls
playbooks/autopilot-stack.md -> cursor:cloud-agent : spawns-subagent
playbooks/autopilot-stack.md -> playbooks/autopilot-stack.md : reads-reference
playbooks/session-pickup.md -> principle-guard-the-context-window : cites-principle
playbooks/session-pickup.md -> principle-prove-it-works : cites-principle
playbooks/session-pickup.md -> transcript-parser-subagent : spawns-subagent
playbooks/session-pickup.md -> poteto-mode/SKILL.md : routes-to
playbooks/pause-safely.md -> show-me-your-work : reads-reference
playbooks/pause-safely.md -> playbooks/session-pickup.md : hands-off-to
playbooks/multi-phase-plan.md -> playbooks/prototype.md : calls
playbooks/multi-phase-plan.md -> principle-never-block-on-the-human : cites-principle
playbooks/multi-phase-plan.md -> agents/poteto-agent.md : spawns-subagent
playbooks/multi-phase-plan.md -> principle-guard-the-context-window : cites-principle
playbooks/multi-phase-plan.md -> principle-sequence-verifiable-units : cites-principle
playbooks/multi-phase-plan.md -> technical-writing : calls
playbooks/multi-phase-plan.md -> unslop : calls
playbooks/multi-phase-plan.md -> scripts/check-plan.mjs : runs-script
playbooks/multi-phase-plan.md -> principle-encode-lessons-in-structure : cites-principle
playbooks/multi-phase-plan.md -> principle-prove-it-works : cites-principle
playbooks/multi-phase-plan.md -> swarm : calls
playbooks/multi-phase-plan.md -> cursor-team-kit:control-ui : calls
playbooks/multi-phase-plan.md -> cursor-team-kit:control-cli : calls
playbooks/multi-phase-plan.md -> playbooks/autopilot-full.md : hands-off-to
playbooks/multi-phase-plan.md -> playbooks/autopilot-stack.md : hands-off-to
playbooks/multi-phase-plan.md -> playbooks/orchestrate.md : hands-off-to
playbooks/multi-phase-plan.md -> playbooks/opening-a-pr.md : reads-reference
playbooks/multi-phase-plan.md -> playbooks/shipping.md : defers-rule-to
playbooks/multi-phase-plan.md -> references/bugbot-triage.md : reads-reference
playbooks/multi-phase-plan.md -> cursor-team-kit:deslop : calls
playbooks/multi-phase-plan.md -> no-comments : calls
playbooks/multi-phase-plan.md -> how : reads-reference
playbooks/multi-phase-plan.md -> interrogate : reads-reference
playbooks/multi-phase-plan.md -> show-me-your-work : reads-reference
playbooks/multi-phase-plan.md -> cursor:/goal : calls
playbooks/multi-phase-plan.md -> cursor:/loop : calls
playbooks/worktree-cleanup.md -> scripts/worktree-audit.sh : runs-script
playbooks/worktree-cleanup.md -> principle-build-the-lever : cites-principle
playbooks/worktree-cleanup.md -> principle-encode-lessons-in-structure : cites-principle
playbooks/worktree-cleanup.md -> principle-prove-it-works : cites-principle
playbooks/worktree-cleanup.md -> principle-guard-the-context-window : cites-principle
playbooks/worktree-cleanup.md -> transcript-reader-subagent : spawns-subagent
playbooks/worktree-cleanup.md -> poteto-mode/SKILL.md#Autonomy : reads-reference
scripts/orch/orch.ts -> scripts/bootstrap.ts : imports
scripts/orch/orch.ts -> scripts/orch/store.ts : imports
scripts/orch/store.ts -> ext:gt : calls
scripts/orch/store.ts -> ext:git : calls
scripts/orch/orch.test.ts -> scripts/orch/store.ts : tests
scripts/orch/orch.test.ts -> scripts/orch/orch.ts : tests
scripts/watch-pr/watch-pr -> scripts/bootstrap.ts : imports
scripts/watch-pr/watch-pr -> scripts/watch-pr/cli.ts : imports
scripts/watch-pr/cli.ts -> scripts/watch-pr/github.ts : imports
scripts/watch-pr/cli.ts -> scripts/watch-pr/policy.ts : imports
scripts/watch-pr/cli.ts -> scripts/watch-pr/render.ts : imports
scripts/watch-pr/policy.ts -> scripts/watch-pr/github.ts : imports
scripts/watch-pr/github.ts -> ext:gh : calls
scripts/watch-pr/github.ts -> ext:git : calls
scripts/watch-pr/policy.test.ts -> scripts/watch-pr/policy.ts : tests
scripts/watch-pr/github.test.ts -> scripts/watch-pr/github.ts : tests
scripts/watch-pr/cli.test.ts -> scripts/watch-pr/cli.ts : tests
scripts/watch-pr/types.compile.ts -> scripts/watch-pr/types.ts : tests
scripts/watch-pr/types.compile.ts -> scripts/watch-pr/tsconfig.json : configured-by
scripts/bootstrap.ts -> scripts/package.json : configured-by
scripts/bootstrap.ts -> scripts/bun.lock : configured-by
scripts/check-plan.mjs -> playbooks/multi-phase-plan.md : enforces
scripts/worktree-audit.sh -> ext:git : calls
scripts/worktree-audit.sh -> ext:gh : calls
scripts/worktree-audit.sh -> ext:jq : calls
scripts/worktree-audit.sh -> ext:rg : calls
```

自拟关系说明：`supersedes`：本组件声明取代另一个同名能力（babysit.md 第 3 行 `This playbook replaces Cursor's built-in babysit skill`）。`serves`：reference 反向声明自己服务于哪个 playbook。`defers-rule-to`：按文件名或步号引用另一个 playbook 的某条规则作为唯一出处，而不复制它。`imports`：脚本之间的模块导入。`tests`：测试文件覆盖的模块。`enforces`：脚本对某文件定义的格式做机器检查。节点前缀：`cursor:` 为 Cursor 内置能力，`cursor-team-kit:` 为外部插件技能，`ext:` 为外部命令行工具；不带前缀的短名（swarm、show-me-your-work 等）为 `pstack/skills/<name>/SKILL.md`；`watcher-subagent`、`transcript-parser-subagent`、`transcript-reader-subagent` 是 playbook 里派出的、没有专门定义文件的临时子代理。
