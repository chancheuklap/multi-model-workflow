# 票声明可写路径边界（`Owns:`）

本文回答一个问题：要不要给票加 `Owns:`，加了以后怎么用。候选机制来自 unlazy 的 `OWNS:`（`00-synthesis.md` 「三份报告共同推荐、无分岔的改法」表第一行，`01-pre-landing-worker-contract.md` C2，`02-during-landing-anti-drift.md` D）。参考快照在 `docs/research/code-landing-refs/`，下文路径省略这个前缀。unlazy 脚本只读了代码，没有运行。

## 1. 一句话结论

`Owns:` 在 unlazy 里是一份**并发协调用的声明**，不是隔离、不是沙箱、也不检查 worker 实际写了哪里；脱离 unlazy 脚本之后，它剩下的价值是三件事：出票时逼出票人想清楚这张票动哪些目录、开工时给 worker 一条「这里以外别碰」的边界、收尾时给人一条一行命令就能算出来的「路径外改动」清单。我们的票以串行为主，并发不相交那一层几乎用不上，但前两件事正是 `02` §5 第 5 条「票没有写路径声明，worker 可以改任何文件」的缺口。建议加，格式和用法见 §7。

## 2. unlazy 的 `OWNS:` 到底是什么

### 2.1 语法

- 位置：`OWNS:` 是 gate 账本（`GATES.md` / `gates/leaf-*.md`）的可选文件头，必须出现在第一条 gate 之前（`unlazy/references/gates.md` L39；解析在 `unlazy/scripts/lib/gates.mjs` L191-196，出现在 gate 之后报错 `OWNS must appear before the first gate`）。
- 形式：一行，逗号分隔多条路径（`gates.md` L39；`gates.mjs` L198 按 `,` 切分再 trim）。例子 `OWNS: src/import/**, tests/import/**`（`gates.md` L10）。空声明报错（`gates.mjs` L199）。
- 每条路径的合法性（`gates.mjs` L275-288 `normalizeOwnsGlob`）：
  1. 反斜杠换成 `/`，去掉开头的 `./`（L276）。
  2. 拒绝绝对路径、Windows 盘符、`//` 开头（L278-280）。
  3. 拒绝含 `..` 段或 NUL 的路径（L281-283）。
  4. 去掉空段和 `.` 段后若为空，报错 `OWNS path cannot claim an implicit root`（L285-286）；注意裸 `**` 不在拒绝之列，它会被当成一条合法的全仓库声明。
- 模板给的填法：`OWNS: <repository-relative globs this leaf may write, for example src/api/**, tests/api/**>`（`unlazy/templates/gates-leaf.md` L3）；模板注释要求「repository-relative, complete, and disjoint from every concurrently dispatched leaf」（L40-41）。`unlazy/templates/PLAN.md` L12 要求计划的 Contract 段列出「one complete set of repository-relative paths per leaf」，L54 要求「Every leaf repeats its complete ownership as an `OWNS:` header in its ledger」。

### 2.2 glob 规则与「不相交」的判定

判定函数是 `gates.mjs` L301-320 `globsOverlap`，注释写明「Prove disjointness only when literal path segments disagree. Everything else conflicts」。算法：

1. 两条 glob 都按 `/` 切段，逐段比较到较短者长度（L308-311）。
2. 任一段含 `* ? [ {` 之一，立刻判 conflict（L313）。
3. 两段都是字面量且不相等，判 disjoint（L314）。
4. 走完公共长度仍未分出，判 conflict（L317-319）：更短的那条被视为目录级声明，覆盖所有后代。

所以 `**` 只在**段尾**才有用（`src/api/**` 与 `src/web/**` 在第二段就分开）。`unlazy/references/parallel.md` L73-78 的例子表与代码一致：`src/shared/**` 对 `src/shared/util.mjs` 冲突；`src/a*.mjs` 对 `src/ab*.mjs` 冲突；`**` 对 `docs/**` 冲突。`parallel.md` L69 自述这是「deliberately conservative」，可能拒绝一对其实不相交的 glob，并要求「Treat over-conflict as a prompt to use simpler disjoint paths or sequential dispatch」。

### 2.3 claim / release 生命周期

- **何时 claim**：并发派发前，逐个 leaf 执行 `gate-check.mjs --scope <scope> --leaf leaf-1.2.1 --claim`（`parallel.md` L57-61；`unlazy/references/orchestration.md` L21-27 是 driver loop 第 3 步；`unlazy/references/dispatch.md` L9 「Claim every leaf first」）。`READY` 状态的定义本身含「ownership is available」（`orchestration.md` L10）。
- **claim 做什么**（`gates.mjs` L592-616 `claimLeases`，入口 `unlazy/scripts/gate-check.mjs` L253-292）：在一把全局文件锁 `lease-registry` 下（L593），读账本里的 `OWNS`（没有则 `gate-check.mjs` L276 报 `declares no OWNS paths`），把每条 glob 对所有现存 lease 的每条 glob 跑 `globsOverlap`（L606-611），有冲突则一条都不写、打印 `CONFLICT <glob> overlaps <theirGlob> held by <scope>/<leaf>` 并以退出码 3 结束（`gate-check.mjs` L285-290，L53 用法文档 `3 lease conflict`）；没有冲突就写一个 JSON lease 文件 `{scope, leaf, globs, pid}` 到 `.unlazy/locks/`（L613-614）。`parallel.md` L63 「A claim is all-or-nothing」。
- **同名重复 claim 被拒**：lease 文件名是 `sha256(scope::leaf)`（L613），而冲突扫描不排除自己，所以同一 leaf 再 claim 会撞上自己的 lease（`parallel.md` L65 「Repeating the same claim is refused; release that exact leaf before claiming it again」）。
- **损坏的 lease 视为占有 `**`**（`gates.mjs` L579-581）：读不出 JSON 的 lease 文件按 `globs: ["**"]` 参与冲突扫描，即 fail closed。
- **何时 release**：父级 `--reverify` 通过之后（`parallel.md` L82-87；`orchestration.md` L44 「Release all scope leases after final verification」）。`releaseLeases`（`gates.mjs` L619-628）按 scope（可再限 leaf）删除 lease 文件。
- **不自动清陈旧锁**：`parallel.md` L67、`unlazy/SECURITY.md` L20——进程死了要人工核对 PID 再删那一个锁。

### 2.4 它明说自己不是什么

- 不是文件系统隔离：「It does not restrict a command's filesystem access」（`gates.md` L133）；「They do not sandbox shell commands, enforce operating-system permissions, or stop a process that ignores the protocol from writing any file」（`parallel.md` L3）；「Leases cover only declared paths and only participants that honor them. They are coordination records, not write isolation」（`parallel.md` L80）。
- 不是安全边界：`unlazy/SKILL.md` L38 「Treat scopes, leases, and wave state as coordination, never as filesystem isolation or a security boundary」；`SECURITY.md` L34-38 整节标题就是「Scopes and leases are not a sandbox」，要隔离用 worktree（只能减轻普通路径争用）或 OS / 容器。
- 不检查实际写了哪里：`unlazy/scripts/` 下没有任何地方拿 `OWNS` 去对 git diff 或文件系统；`doc.owns` 的唯一消费者是 `gate-check.mjs` L276-278 的 claim。dispatch 的证据边界也说明了「It does not prove … filesystem isolation」（`dispatch.md` L82）。
- 不是隔离级别的替代：`parallel.md` L117-121 列出三档——一个工作树多 scope（读多、简单不相交）、每 pipeline 一个 worktree（生成物会撞）、OS / 容器（不可信命令）。`OWNS` 只在第一档起作用。

## 3. 没有 unlazy 脚本时，`Owns:` 还剩什么

拆开看 unlazy 里 `OWNS` 参与的四件事：

| unlazy 里的用途 | 靠什么实现 | 没有脚本时 |
| --- | --- | --- |
| 出票前逼 driver 定清 ownership | `PLAN.md` L12「one complete set」+ `orchestration.md` L19「Fix … exact ownership before dispatch」——是写作纪律，不是脚本 | **保留**。写不出 `Owns` 就是没想清楚这张票动哪儿 |
| 告诉 worker 边界 | `orchestration.md` L28 派发时「Give each leaf only the shared contract, its exact ownership and dependencies, its own ledger」——是提示词 | **保留**。worker 读到一节 `Owns`，效果与 pstack `SCOPE`（`pstack/skills/poteto-mode/playbooks/orchestrate.md` L42）一样：纯文字约束 |
| 并发前拒绝重叠 | `--claim`（§2.3） | **失去**。替代见 §5：出票时人眼看两张 frontier 票的 `Owns`，重叠就加 Blocked by 边 |
| 路径外改动的发现 | unlazy 本来就没做（§2.4 第三条） | **本来就没有**，但 git 能补：见下 |

worker 读到 `Owns` 会怎样：与 `FORBIDDEN` 一行「no fixes outside scope」（`orchestrate.md` L48）同一性质，只约束遵守协议的 worker——这正是 unlazy 对 lease 的自我定位（`parallel.md` L80「only participants that honor them」）。所以不能把 `Owns` 当成防线，只能当成「写了才有据可查」的基线。

路径外改动怎么发现：git 的 pathspec 支持 `:(glob,exclude)` 魔法，把 `Owns` 的每条 glob 作为排除项，剩下的就是路径外改动。本机 git 2.55.0 上验证过：

```text
git diff --name-only <base>..HEAD -- . ':(glob,exclude)src/import/**' ':(glob,exclude)tests/import/**'
```

对 `fa0fbb80~1..fa0fbb80`（110 个改动文件全在 `mmw-v2/upstream/` 下）排除 `mmw-v2/upstream/**` 后输出 0 行；只排除 `mmw-v2/upstream/skills/**` 则剩下 `.agents/` 下的文件。输出为空即全部落在 `Owns` 内；非空就是要在收尾评论里逐条交代的清单（§7.4）。这条命令不依赖任何参考脚本，任何宿主的 bash 都能跑，也符合 `03` 已定的「每条验收标准怎么算过」用命令说话的方向。

## 4. 与 `to-tickets` L135 路径禁令的关系

现行原文（`mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md` L135）：「In either form, avoid implementation file paths or code snippets: they go stale fast; paths to source material and test directories stay.」上游原句是「avoid specific file paths」（commit `818c2a9e` 之前），我们已收窄成「implementation file paths」并放行「source material and test directories」（`mmw-v2/merge-notes/to-tickets.md` L14「路径禁令收窄成『不写实现文件路径』」）。

禁令的理由「they go stale fast」对 `Owns` 的 glob 是否成立，分两层看：

1. **过期概率**。L135 反对的是散在 What to build 里的具体文件路径（`src/import/parser.ts`），文件一改名就错。`Owns` 按 unlazy 的用法是目录级 glob（`src/import/**`），目录改名的频率远低于文件改名；而且 `Seam` 已经在写「the test layer and directory」（L122），目录级路径这条线已经被我们自己放开了。
2. **过期后果**。散在描述里的路径过期是**静默误导**——worker 读到一个不存在的文件名，只能猜。`Owns` 过期是**可见失效**——开工核对时 glob 匹配不到任何现存路径（且这张票也不是要新建它），worker 按 `implement/SKILL.md` L8 既有的「stop and report」处理，不会被误导。这是 `Owns` 与 L135 所反对的东西的本质差别：`Owns` 写的不是「代码在哪」，而是「你可以写哪」，文件在 glob 内怎么挪都不影响它的真值。

共存措辞（只改 L135 那一句，模板加节见 §7.1）：

> In either form, avoid implementation file paths or code snippets: they go stale fast; paths to source material and test directories stay, and so do the directory-level globs under **Owns**, which say where this ticket may write, not where code lives. Exception: …（后文不动）

## 5. 两张并发票路径重叠时各家怎么办；我们的实际风险

| 来源 | 粒度 | 重叠时 |
| --- | --- | --- |
| unlazy | 账本级 glob | `--claim` 拒绝并退出码 3；`orchestration.md` L27「Change the plan or run the work sequentially; never bypass the refusal」；`parallel.md` L69 保守判定下的出路是「simpler disjoint paths or sequential dispatch」 |
| pstack | brief 级 `SCOPE`（`orchestrate.md` L42「paths this unit may write; paths it may not; its exclusive worktree or branch」）；计划级 `Hold the file boundaries. <PR id or class> touches only <glob>`（`pstack/skills/poteto-mode/playbooks/multi-phase-plan.md` L52）；PR 级 `**Files.**` 逐文件 Edit / Create / Delete（L82-86） | 靠依赖图串行：「Start dependent work only after its parent merges, or base it on the parent branch when the execution playbook stacks」（L49）；没有机器判定 |
| swarm-forge | 分支 / worktree 级（`swarm-forge/swarmforge/constitution/articles/workflow.prompt` L3-8「Work only in your assigned branch or worktree」） | 不谈路径；L7 禁止看别的分支，重叠留到合并时才暴露 |
| 我们现状 | 只有 `AGENTS.md` L19「正式改动在独立 worktree，合回用 `git merge --no-ff`」 | 没有规则。`to-tickets` L70「Work the frontier」允许 frontier 上多张票同时开工，重叠只在 `git merge --no-ff` 时以冲突形式出现 |

我们的实际风险：

- **丢写**风险低：每票一个 worktree（`AGENTS.md` L19），两个 worker 写同一路径不会互相覆盖，这正是 `parallel.md` L120 说 worktree 能减轻的「ordinary path contention」。
- **合并冲突**风险中：frontier 上的两张票若都要动同一个汇聚文件（路由表、barrel export、schema、迁移编号），合并时必冲突，且第二个合入的人要在没有上下文的情况下解。`Owns` 的价值就在这里：出票时两张 frontier 票的 `Owns` 一比对，撞了就给后一张加一条 Blocked by 边，把 unlazy 的「sequential dispatch」翻译成我们已有的词汇（`to-tickets` L36 blocking edges）。不需要 claim 脚本，因为判定的时机是出票（`to-tickets` 第 4 步「Quiz the user」L47-61 已经在逐票核对 Blocked by），不是派发。
- 串行为主时，`Owns` 的并发用途退化为零成本：一条链上的票不用比对。

## 6. 出票时谁能写出 `Owns:`

`to-tickets` 第 2 步「Explore the codebase (optional)」（L18-22）目的是「understand the current state of the code」、用域词汇、尊重 ADR、找 prefactor 机会——它是可选的，而 `Owns` 需要知道目录布局。够不够：

- **测试目录**：已经够。`Seam` 要求从 spec 的 Testing Decisions 抄「the test layer and directory」（L95、L122），这部分照抄进 `Owns`。
- **实现目录**：要看 spec 的 Implementation Decisions 有没有点名模块。spec 点了名（「导入解析放在 `src/import/`」这类决策）就直接用；没点名就必须看一眼仓库——对 `Owns` 而言第 2 步不再可选。目录级的一次 `ls` / `git ls-files` 是很便宜的探索，不会碰到 `merge-notes/to-tickets.md` L15 担心的把切片推细的问题。
- **新建目录**：绿地票的 `Owns` 反而最容易写——目录还不存在，它本身就是一条决策（「本票新建 `src/import/`」），写的时候注明「(new)」。
- **写不出**时：套用 L43 验收标准第 4 条既有的规则——「If you cannot name that place, the spec is missing a decision: stop and return to `/to-spec`」。写不出 `Owns` 等价于说不清这张票落在代码的哪一块，是切片没切清（`<vertical-slice-rules>` L30 要求每片贯穿所有层，能列出层就能列出目录）。不接受用裸 `**` 或整个 `src/**` 蒙混：unlazy 代码放行裸 `**`（§2.1 第 4 条），但那等于没有边界。

## 7. 建议

### 7.1 字段格式与位置

`<issue-template>`（`to-tickets/SKILL.md` L106-133）在 `## Seam` 之后、`## Acceptance criteria` 之前加一节；`<local-ticket-template>`（L85-104）对应加一行 `**Owns:**`。放在 `Seam` 后面是因为两节是一对：`Seam` 说在哪验，`Owns` 说在哪写，且 `Seam` 的测试目录必然是 `Owns` 的一项。

```markdown
## Owns

The repository-relative directory globs this ticket may write, one per line, the test directory from **Seam** included. Mark a directory this ticket creates with "(new)". No absolute paths, no `..`, no bare `**`. Two tickets on the same frontier must not overlap here; when they do, add a **Blocked by** edge instead. Everything outside these globs is read-only for this ticket.

- src/import/**
- tests/import/**
```

规则照搬 unlazy `normalizeOwnsGlob` 的可读版本（相对、无 `..`、不许隐式根），再加一条 unlazy 没有的「不许裸 `**`」（理由见 §6 末）。一行一条而不是 unlazy 的逗号一行，是因为 GitHub issue 正文里列表更好读，也方便 `git diff` 命令逐条取用（§3）。

### 7.2 `to-tickets` 要动的三处

1. 第 2 步（L18）标题去掉「(optional)」不必，但正文加一句：写 `Owns` 需要知道目录布局，spec 没点名模块时这一步不可省。
2. 第 6 步「Read every ticket back」（L74-83）的核对清单加一项：`Owns` 非空、每条是目录级 glob、同一 frontier 上的票两两不重叠。
3. L135 改成 §4 的共存措辞。

### 7.3 `implement` 开工核对加的一句

在 `implement/SKILL.md` L8 的两项核对（标题与 What to build 同一片、在 frontier 上）之后加第三项：

> …and every glob under **Owns** matches at least one existing path or is marked "(new)". A ticket without **Owns** is an older one: derive the globs from **Seam** and the sections named under **Parent**, post them as a comment on the ticket before you start, and work to them.

后半句照搬 L12 处理缺 `Seam` 的既有模式（「derive it … post it as a comment on the ticket before you start」），让旧票不必回炉。

### 7.4 路径外改动的处置

已定规则（`00-synthesis.md` L54）：写码中发现契约装不下 → 继续做，在 spec 下开 sub-issue 记录。它对 `Owns` **形状适用、落点不适用**：

- 形状适用：路径外改动同样不能默默做、也不该为它中断切片（`<vertical-slice-rules>` L30 要求切片完整，barrel export、路由注册这类一行改动常在 `Owns` 外，为它停工不成比例）。所以同样是「继续做 + 记录」。
- 落点不适用：契约装不下说明 **spec / prototype** 缺东西，记录要挂在 spec 下，让 spec 得到修正。`Owns` 外改动说明的是**这张票的 `Owns` 写窄了**，修正对象是票本身；开 sub-issue 记一条「barrel 多了一个 export」没有后续动作，只会堆积。
- 因此分两档：
  1. 为了让本票验收标准通过而不得不动的路径外文件 → 做，并在收尾评论（`implement/SKILL.md` L22）固定加一行 `Outside Owns:`，列出 `git diff --name-only <base>..HEAD -- . ':(glob,exclude)<每条 Owns>'` 的输出和每条一句为什么；输出为空写 `None`。
  2. 与本票验收标准无关、但顺手想改的路径外文件 → 不做，开 sub-issue，与 `00-synthesis.md` L55 code-review 之后「其余开 sub-issue」同一通道。
- 判据只有一条：这处改动不做，本票哪条验收标准过不了？说得出就是第 1 档，说不出就是第 2 档。

### 7.5 不建议的

- 不引入 claim / lease 脚本或锁目录：并发判定的时机在出票（§5），frontier 串行为主，`.unlazy/locks/` 那套的收益不成比例。
- 不采用 pstack `**Files.**`（`multi-phase-plan.md` L82-86）的逐文件 Edit / Create / Delete 清单：那正是 L135 反对的会过期的文件路径，而且把实现顺序也定死了。
- 不采用 swarm-forge 的分支级约束作为「我能写哪里」的规则：`AGENTS.md` L19 已经有 worktree 约定，分支级不回答路径问题。

## 8. 未读 / 未确定

1. unlazy `references/token-economy.md`、`references/method.md` 未读；`gate-lint.mjs` 不读 `OWNS`（grep 无引用），所以 unlazy 对 `OWNS` 内容本身没有 lint，我们 §7.2 第 2 项的核对没有现成对照物。
2. pstack `skills/poteto-mode/playbooks/feature.md` L12「a specific scope (file paths, named data shape…)」只在 `02` §2 表里引用过，正文未读；它可能给出 SCOPE 的粒度惯例。
3. 未核对 mattpocock/skills 远端在 `6654f6b6` 之后是否改过 L135；本仓 subtree 停在该提交（squash 提交 `23138829`）。
4. `git diff` 的 `<base>` 怎么取（worktree 分叉点 `git merge-base main HEAD`，还是票评论里记的起始 commit）没有定；`code-review` 技能怎么找 base 未看。
5. GitHub issue 正文没有机器可读字段，`Owns` 只能靠 worker 读；若将来要让 `code-review` 或 verifier 自动跑 §3 的命令，需要约定从 issue 正文解析 `## Owns` 列表的方式。
6. `:(glob,exclude)` 的行为只在 macOS git 2.55.0 上验证过；远端宿主的 git 版本未核对。
