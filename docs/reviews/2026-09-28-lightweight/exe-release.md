# exe-release


## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：这个技能的产出是付费客户安装的东西，它缺的"为什么"全都连着客户后果：
- 工作区必须干净，是因为构建机只拿得到 `git archive HEAD`。
- 共享代码改了，也要出包。
- 几个包不能来自不同的提交。
- 编译的目的是不把业务源码交出去。

**已定（2026-09-28）**：删除自动修复后端。三个产品仓库的全部历史里它没产生过一个提交，本机也从未设置过启用它的 `RELEASE_FIX_BACKEND`。删掉以后，整套受保护路径机制（`protection_source`、`editable_paths`、路径闸、修复后测试闸）也失去了唯一的用途：它们只审查"自动修复"改了什么，而驱动出包的 agent 自己提交时本来就不经过它们。出包修复的实际记录也不需要它们：出包时的修复改的是出包脚本、测试和 lint（agentflow `4a148ef4b`、`dd3fa834c`、`d0716eac3`），从没碰过计费、迁移或密钥。9 月 15 日改定价种子 `src/gateway/reference_data_seed.py` 的那次，是用户在同一会话里亲自要求的，不是出包修复（Codex 会话 `rollout-2026-09-15T09-10-05`，第 213 条用户消息）。所以不另加文字规则替代它们；`driving.md` 第 5 步原有的"计费、合同、产品决定停下来报告"保留。

调查员 G1 那段总体说明不采纳：它的三个"判断点"在下面各自的位置都已经写了，放在开头只是重复。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` `## 1. Preconditions`，整张表换成右栏（配合 D6） | The build machine receives `git archive HEAD` and nothing else. Uncommitted work does not ship, so a dirty tree means the user would test a package that differs from the code in front of them: stop and say which files are uncommitted. | 原文给的是次要原因（引擎不许自动修复的提交混入未提交改动，删除后端后这个原因也没了）。只知道次要原因的 agent，可能先 stash 再照常出包，做出的包和用户眼前的代码不一致。 |
| I2 | `SKILL.md` `## 2.`，"Match them against the paths each release manifest names…A hit means ship that product." 之后 | The paths are evidence, not the rule. What decides is whether the change reaches what this product's customer installs: a package the product lists in `python_backend.include_packages` that lives outside its own directory, a dependency lock, a hook script, or the release manifest itself all change the package. Leaving out a product the change reached ships it stale; including one it did not costs one build. | 真实缺口：`~/agentflow` 的 parrot 在 `include_packages` 里列了 `shared`（位于 `src/shared/`），改它不会命中原清单的任何一条，parrot 就不出包，客户拿到的仍是旧代码。末句给了两种错误的代价，拿不准时 agent 知道往哪边偏。 |
| I3 | `SKILL.md` `## 4. Same-commit check` 开头 | A set whose packages come from different commits is two versions of the product: whoever installs more than one gets a combination nobody built or tested together. | 有产品不匹配、agent 觉得"代码差不多"想跳过重出时，有理由不跳。依据：`cmd_close` 的注释。 |
| I5 | `references/key.md` `### build_hooks`，"On every build the skill already checks that no business source ships (the packages in `python_backend.include_packages`)" 之后（恢复 `66089d06` 删掉的理由，压成一句） | Compiling the backend exists so that no business source ships; a package that leaks it still installs and runs, so nothing but this check ever notices. | 写 hook 或 `extra_flags` 的 agent 想绕开这道检查时，有理由知道它守的是产品的商业前提。 |

### 删除、改正或交给脚本

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D0 | 自动修复后端，及只为它存在的全部机制 | **本仓**：`fix_dispatch.py` 删 `RELEASE_FIX_BACKEND`、`_run_backend` 与 `for_backend` 分支，只剩写修复简报；P1 时引擎调用它写简报后直接暂停，pause 的问题写成 "P1 handed to you: read <brief path>"（原 D3 并入这里），`driving.md` 状态表 `FIX-BRIEF=` 与 `ENV-ACTION:` 两行随之合并。`release-flow.sh` 删 `_load_path_hard_deny`、`_path_gate`、`_snapshot_baseline_untracked`、`_baseline_untracked_changed`、`_collect_candidate_paths` 中只为路径闸服务的部分、`_write_path_gate_patch`、`_restore_rejected_candidates`、`_post_fix_gate`，以及 `cmd_dispatch_direct` 的 P1 分支。`release_contracts.py` 删 `fix_executor`、`editable_paths`、`protection_source`、`post_fix_gate` 四个字段及其校验；`verify_key.py`、`release_script_assembler.py` 删对应检查；测试随之删改。文字：`key.md` `### What is genuinely optional` 只剩 `derive` 与 `event_sink`；`driving.md` 第 40 行只留 "You do not assign the tier (P0, P1 or P2)."，状态表 `needs-redirection` 行删 "Protected paths"，第 5 步删 "a protected path"。**保留**：`derive`（P2，产品仓库自己的确定性重新生成脚本）；它的提交仍先检查"没有事先存在的未提交改动"，这就够了。**产品仓库**：agentflow 的 `hedgehog`、`parrot` 两份 release manifest 与 xiaohuangya 的 `duck` 删这四个字段；两个仓库的 `scripts/release/release_protection.json`、`release_protection.py`、`post_fix_gate.py` 及其测试（agentflow `tests/contracts/test_release_adapter_contract.py`、`tests/journeys/_release_journey.py` 等引用处；xiaohuangya `tests/local_agent/test_release_protection.py`、`test_post_fix_gate.py`）删除或改写。写一份 downstream-note。 | 用户已定。原 D1（简报里 "The engine rejects edits to protected paths" 那句错话）随整段规则删除，不再换成新的规则句。 |
| D2 | `driving.md` `## After a stage fails` 全节与状态表 `RETRY-STAGE:<name>` 行 | `stage run` 失败时，自己接着做分诊派发（原 `dispatch`）和轮次计数（原 `round next`），然后返回；驱动 agent 只剩"问 `where`，跑它说的 stage"这一个循环。删这一节和这一行 | 固定的派发顺序，不需要判断；漏掉 `round next` 会让熔断永远不触发，agent 自己看不出来。不新增 `advance` 命令：删掉后端后派发只剩四种确定的去向，并进 `stage run` 比多一个命令更少。 |
| D4 | `SKILL.md` `## 4.` 的操作部分（记录在 main checkout 根目录、只读本轮清单、逐个比对 `source_commit`） | 新增 `<release> same-commit <product>...`，逐个输出 `OK` 或 `MISMATCH <product> <commit>`；第 4 步只留 I3 与循环 | 确定性比对；真实记录跨仓库混在一起（`~/agentflow/.release/delivered/` 里有别的产品）。 |
| D5 | `driving.md` `## Close` 第 3 条（`abort` 与 `close` 的区别）与状态表 `SUCCESS` 行的 "exit-check must return DONE…" | `close` 在状态不是 DONE 时拒绝，拒绝里写 "use `abort` to drop a round"；删掉 `exit-check` 这个不可能失败的比对和这两段文字 | `exit-check` 与 `where` 读同一份状态，`SUCCESS` 而无 `DONE` 不可能发生。`abort` 确实被真实用过，所以这个区分本身保留，只是交给脚本。 |
| D6 | `SKILL.md` `## 1. Preconditions` 两行表 | 由 I1 取代；`init` 在工作区不干净时拒绝，理由同 I1；没有 release manifest 的情况交给第 2 步 | 第二行与第 2 步重复；检查从文字搬进 `init`，是一行 `git diff --quiet HEAD`。 |
| D8 | `SKILL.md` `## 3.` "Do not run two at once — the repository has one state file." | 删 | `cmd_init` 已拒绝并说明。 |
| D9 | `new-product.md` `cache_root` 一段 | 缩成："`cache_root` defaults to `<root>-cache`; set it to share one cache folder across products. It must sit outside the build directory, which a successful build deletes." | 其余是维护者读的实现说明。 |
| D10 | `key.md` "Those three names are reserved; a release manifest that uses one is refused." | 删；后半句判断保留 | 合同的拒绝已说明并附改法。 |
| D11 | `driving.md` 状态表 `NO-STAGES:`；脚本 S1 所列走不到的分支（约 15 行，包括会生成坏脚本的 `Write-HookSkipped`） | 删 | 因为有三个标准 stage，`stages` 不可能为空；其余分支由合同保证走不到。 |
| D12 | `driving.md` `## Pause: missing context` 第 1–5 步 | 改为："Goal: the round resumes with the cause gone, or the user holds the one question only they can answer. The engine's receipt and the logs it names are the evidence; do not guess past them. Environment causes you act on; code or config causes you fix and commit (the build ships `git archive HEAD`); then `resume`." 接第 5 步的停止条件（按 D0 删去 "a protected path"）；第 52–55 行关于提交原因的说明保留 | 只有 `resume` 真依赖顺序；读 receipt、看日志是默认动作。 |
| D13 | 脚本 S3（`release_script_assembler.py` 的原子写与回滚）、S4（`check`、`render_metadata`、`_check_script`）、S5（每个事件都启动解释器做自我校验） | 删 | 四问前两问都是"否"；S4 的比对不可能失败，产品仓库也不读 `render_metadata`。 |
| D14 | 脚本 S6：assembler 重写了一遍 `nuitka._probe_var` 的变量名规则 | 改为直接调用 `nuitka._probe_var`（改成公开函数） | 两边改得不一致时，生成的 PowerShell 会遇到未定义变量。 |
| D16 | 脚本 S7：注释里的历史叙述与一处自相矛盾（第 815 行与第 1021 行对远端默认 shell 的说法） | 改正 | 注释描述的是已不存在的状态。 |

### 不采纳

- G1（开头总体说明）：见上文判断。
- 原 I4（"需要改受保护路径就停下报告"的规则句）与"`resume` 检查 agent 自己的提交"：删除后端后，受保护路径这个概念不再存在；出包修复的实际记录里也没有碰过这些路径的例子。加任何一样都是为没发生过的事加防御。
- 原 D7（新增 `dry-run` 子命令）、D15（给 `builders/nuitka.py` 加打印 argv 的命令行入口）：两者只在接入一个新产品时用一次，现有两段命令文字够用；为一年用几次的步骤加两个子命令和它们的测试，是新增负担。
- 脚本 S9（隐藏只给测试用的 `stage done`、`surface`）：已有限制，不改。

## 结论

`mmw-v2/skills/exe-release/` 的文字部分共 5,549 词（`SKILL.md` 约 700、`references/driving.md` 约 900、`references/new-product.md` 约 1,180、`references/key.md` 约 2,740），脚本 5,238 行（不算 `__pycache__`；`scripts/release-flow.sh` 1,642、`release_script_assembler.py` 836、`release_templates/nuitka_electron.ps1.tmpl` 743、`release_contracts.py` 587、`diagnose_core.py` 450、`verify_key.py` 430、`builders/nuitka.py` 330、`fix_dispatch.py` 220）。`key.md` 和 `new-product.md` 基本就是这个技能的灵魂：每个字段都写了"漏了它客户那边会出什么事"，大部分有真实出包事故作依据（见下文"证据来源"），不该按字数修剪。主要问题有三处。第一，`driving.md` 和 `SKILL.md` 让 agent 手工做了几件确定性的事：先 `dispatch`、再 `round next`、再重跑这套失败后的顺序；按约定路径去找 fix brief；第 4 步逐个比对交付记录的 commit；`close` 和 `abort` 二选一；`key.md` 里三条命令加一个临时目录的试装配。这些应该交给 `release-flow.sh`。第二，fix brief 对驱动 agent 说 "The engine rejects edits to protected paths"，但在驱动 agent 自己提交的那条路上，引擎并不检查路径，这句话是错的。第三，自动修复后端那一整套机制（`RELEASE_FIX_BACKEND`、`post_fix_gate`、提交后回滚、冻结保护规则快照、扫描被 gitignore 的受保护文件）在三个产品仓库的全部 git 历史里没有产生过一个提交，前两问都是"否"。不丢功能的前提下，文字估计能删约 560 词、补约 310 词，净减约 250 词；脚本估计能删 250–380 行，另外要为移过去的确定性工作新增约 60 行。灵魂大体完整，缺四处：agent 自己在哪里负判断责任（这段在 66089d06 被删）；工作区必须干净的真正原因；产品选择里的共享代码；以及在驱动 agent 这条路上，没有东西替它守受保护路径。

证据来源：本机三个消费仓库 `~/agentflow`、`~/xiaohuangya`、`~/douyin-master-resolve` 的 `.release/` 状态、交付记录和 findings，四份真实 release manifest，这三个仓库的 `git log --all`，以及本仓 `git log -- mmw-v2/skills/exe-release/`（66 个提交，大部分标题写的是一次真实出包失败）。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| A1 | `references/driving.md` `## After a stage fails` 全节（"When `stage run` fails…"到 "`round next` records 'already handled once'…"），以及 `## State table` 里 `RETRY-STAGE:<name>` 这一行 | 1、4 | 这一节是一段固定的动作顺序，每一步都不需要判断：`where` 输出 `RETRY-STAGE` 就跑一次 `dispatch`；之后如果还是 `STAGE`/`RETRY-STAGE`，就 `round next` 再 `stage run`。`cmd_stage_fail`（`release-flow.sh` 第 1322 行起）已经完成分级，`cmd_dispatch`（第 1394 行起）按分级确定性地派发。漏掉 `round next` 只会让 `max_rounds` 熔断永远不触发，agent 也看不出来 | 在 `release-flow.sh` 加一个 `advance` 子命令（或者让 `stage run` 失败后直接分级并派发）：它一直往前跑，直到出现一个需要 agent 的状态（`PAUSED:*`、`SUCCESS`、`CORRUPT`）才停。剩余风险：派发的顺序从文字搬进代码，要补一个测试 | `driving.md` 删掉整节和那一行（约 170 词）。状态表只留需要 agent 的状态，开头一句改成 "Run `<release> advance` until it stops; it stops only where you are needed." 改法照搬 dispatch 技能已有的 `advance` 做法 |
| A2 | `references/driving.md` `## State table` 两行 `PAUSED:needs-context`（带 `FIX-BRIEF=` 的一行和普通的一行），以及 `## Pause: missing context` 第 3 步里 `ENV-ACTION:` 那一句 | 1 | 三种情况在 `where` 输出里一模一样，都是 `PAUSED:needs-context`，只能靠"上一条命令打印过什么"来区分。后来的会话只能按约定路径去找 `release-fix-brief.md`（"beside the findings file `receipt` lists"）。`fix_dispatch.py` 第 209 行只把路径打印到 stdout，引擎不存。另外，交接本来就是有意的，可 pause 的 question 写的是 "fix exited non-zero"（`cmd_dispatch_direct` 里 `ACTION_RC -ne 0` 那个分支），读 `receipt` 的人会以为修复器崩了 | 让 `fix_dispatch.py` 用一个专门的退出码表示"交给驱动 agent"。引擎据此把 pause 的 question 写成 "P1 handed to you: read <brief path>"，`ENV-ACTION` 也把 remediation 写进 question（这一点已经做到）。之后 `receipt` 一条命令就能说清该做什么。剩余风险：无 | 两行合并成一行："`PAUSED:needs-context` → read `<release> receipt`; its question names the brief or the environment action." 删约 60 词 |
| A3 | `SKILL.md` `## 4. Same-commit check` 的操作部分（"Delivery records live under `.release/delivered/`, at the **main checkout root**…"到 "Their `source_commit` values must all equal current HEAD."） | 1 | 这是一次确定性的比对：`main_root()`（`release-flow.sh` 第 32 行）已经知道记录放在哪里，`cmd_close`（第 1543 行）负责写记录。agent 要自己弄清"main checkout root 不是 task worktree"、"只读本轮清单上的产品"，都是脚本可以替它做的。真实记录确实跨仓库混在一起：`~/agentflow/.release/delivered/` 里就有 `douyin-master-resolve.json` 和 `duck.json`，这正是"只读本轮清单"这句提醒要防的混淆 | 新增 `<release> same-commit <product>...`，逐个输出 `OK <product>` 或 `MISMATCH <product> <commit>`。剩余风险：无 | 第 4 步只留原因和循环："After every product ships, run `<release> same-commit` with the step 2 products; reship each `MISMATCH` and run it again, since a reship can itself move HEAD." 删约 70 词，原因句见 B 的 G4 |
| A4 | `references/driving.md` `## Close` 第 3 条（"**A round that is not going to produce a package ends with `<release> abort`, never `close`.**…"），以及 `## State table` `SUCCESS` 行 "`<release> exit-check` must return `DONE`… Success without `DONE` is a release engine bug" | 1、5 | `cmd_close`（第 1543 行）不看状态就写交付记录，所以要靠一段文字挡住误用。`exit-check` 和 `where` 读的是同一个状态文件、用的是同一组条件（没有 pause、每个 stage 都是 done），`SUCCESS` 却没有 `DONE` 的情况不可能出现；这正是 `SKILL-SET-REVIEW.md` `### Scripts and judgement` 说的 "A check… that cannot fail proves nothing"。`abort` 确实被真实用过（`~/agentflow/.release/release-artifacts/aborted-parrot-20260915-151644.json`），所以这个区分本身不是过度防御，只是放错了地方 | 改成 `close` 在状态不是 DONE 时拒绝，拒绝信息里写 "use `abort` to drop a round that will not ship"；`exit-check` 并进 `close`。剩余风险：无，写假记录的路径被脚本堵死 | `driving.md` 第 3 条缩成一句 "`close` refuses a round that has not shipped; `abort` drops it and writes no record."；`SUCCESS` 行改成 "`<release> close`"；`SKILL.md` 第 3 步 "Done when `<release> exit-check` printed `DONE` and…" 改成 "Done when `<release> close` succeeded for every product…"。约减 60 词 |
| A5 | `references/key.md` `## Prove it without building` 的两个代码块和 "`$out` is this run's own directory. A fixed name under `/tmp` is shared…" | 1、5 | 三条命令加一个 `mktemp` 目录，全是固定动作。关于 `/tmp` 的那句防的是两次试装配同时进行，没有任何记录说明发生过（推断）。`release_script_assembler.py check` 也基本不可能失败（见"脚本"S4） | 在 `release-flow.sh` 加 `dry-run --manifest <path>`：先跑 `verify_key`，再装配到自己的临时目录，打印脚本路径。剩余风险：无 | 删两个代码块和 `/tmp` 那句（约 100 词），换成一句 "`<release> dry-run --manifest <path>` checks the release manifest against the repository and assembles the script; read the script it names."。其后 "Read the generated script. Every step it prints…" 保留，那是判断 |
| A6 | `SKILL.md` `## 1. Preconditions` 整张表 | 1、4 | 两条检查写成了一张表。第二条 "This repository ships something" 其实就是第 2 步的 `git ls-files` 列表为空，是重复的。第一条给的理由 "The release engine refuses to mix self-heal commits with uncommitted work" 只说对了一部分：引擎只在 `cmd_dispatch_direct` 查已跟踪文件（`git diff --quiet HEAD`，第 530 行），`init` 什么都不查 | 让 `init` 在工作区不干净时拒绝，理由写 "the build ships `git archive HEAD`"。没有 release manifest 的情况交给第 2 步。剩余风险：无 | 表换成一句（原因见 B 的 G2），约减 40 词 |
| A7 | `SKILL.md` `## 3.` "Do not run two at once — the repository has one state file." | 6 | `cmd_init`（第 752 行）在状态文件存在时已经拒绝："a release loop for X is already open; run where to continue it, or abort to drop it" | 由脚本的拒绝承担。剩余风险：无 | 删掉（12 词） |
| A8 | `references/new-product.md` `## Remote build machine` 里 `cache_root` 那一段（"`cache_root` is where uv, Nuitka, zig…"） | 2 | 默认值 `<root>-cache` 本身就能用（`release-flow.sh` 第 967 行）。加进 skill 的 agent 只需要知道什么时候该改它；为什么缓存不能放在构建目录里，已经写在模板 `Initialize-BuildMachine` 的注释和 `release-flow.sh` 里，这两处是维护者读的 | 由默认值承担。剩余风险：无 | 缩成一句："`cache_root` defaults to `<root>-cache`; set it to share one cache folder across products. It must sit outside the build directory, which a successful build deletes." 约减 60 词 |
| A9 | `references/key.md` `## The shape` 之后 "Those three names are reserved; a release manifest that uses one is refused." | 6 | `release_contracts.py` 里 `StageSpec._name_must_not_shadow_the_engine`（第 89 行）的拒绝信息已经说清楚，还附了改法 | 由合同的拒绝承担。同一段后半句 "If a product needs a different assemble… add it there" 是判断，保留 | 删前半句（12 词） |
| A10 | `scripts/fix_dispatch.py` `_AGENT_RULES` 第 57 行 "Change only files this release manifest's `editable_paths` allows. The engine rejects edits to protected paths." | 错误陈述，不在 1–6 类 | 在驱动 agent 这条路上：`fix_dispatch.py` 以退出码 1 结束 → 引擎 pause → agent 自己提交 → `resume`（`cmd_resume`，第 1513 行）。这个过程中不跑路径检查，这句话与事实不符。它还和同一份 brief 里 finding 的 remediation 冲突：`diagnose_core.py` 第 121 行叫 agent "add {group} to the release manifest's python_backend include_packages"，而 `*.release-adapter.json` 在 `_SKILL_HARD_DENY`（第 278 行），也不在任何产品的 `editable_paths` 里。照 brief 做，最常见的那个修复就做不了 | 见 B 的 G5 | 改成："Protected paths (the release manifest's `protection_source`) are a decision for the user, not a release repair: nothing on this path blocks your commit, so stop and report instead. Editing the release manifest itself is a normal repair." |
| A11 | `references/driving.md` `## State table` `CORRUPT:` / `NO-STAGES:` 行里的 `NO-STAGES:` | 5 | `cmd_init` 总会在 manifest 自己的 stages 后面追加三个标准 stage（`_standard_stages`，第 708 行），所以 `stages` 至少有 3 个，`NO-STAGES`（第 780 行）永远走不到 | 删掉之后没有需要处理的情况 | 行里只留 `CORRUPT:`（2 词），脚本对应的死代码见 S1 |

没有列入 A 的（看过，判断为该留）：

- `SKILL.md` `## Resolve <release> and <scripts> once`：防的是把本机路径写死这一已知误用，属于 `SKILL-SET-REVIEW.md` `### Redundancy and bloat` 里 "These stay" 的第一类。
- `driving.md` 第 15 行 "Every verdict, `PAUSED` and `CORRUPT:` included, exits 0: read the state from stdout, never from the exit code."：它和 `release-flow.sh` 头部的退出码表意思相同，但 agent 不读脚本头部。这一句是 agent 行动时唯一加载的那一份，防的是"退出码 0 就当成功"这种误读。保留。
- `key.md` `### build_hooks` 里编码那一段（"A hook's own logging has to survive the build machine's codepage…"）与 `diagnose_core.py` 的 `hook_output_encoding` remediation 重复，但两份出现在不同时刻：前者在写 hook 时预防，后者在出事后修复。事故有提交记录：8fe1d897、4cf02e09、81dba26b。两份都留。
- `driving.md` `## Pause: missing context` 第 5 步 "Same root cause twice…" 和引擎的 `RF_MAX_SAME_FINGERPRINT=3` 熔断有部分重叠。引擎按指纹计数，agent 认的是"同一个真实原因"，而同一个原因可能对应不同指纹。两者互补，保留。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 第 8 行 "Ship an install package for every product this change touched, far enough that the user can install it."：完成标准定在"用户能装上"，不是"构建通过"。
- `SKILL.md` 第 10 行 "**Ship what is on the current branch now.** Whether the code is reviewed… that is the user's call, already made when they asked."：划清这个技能不去重新评判代码，防止 agent 在出包时开始评审。
- `SKILL.md` 第 37 行 "If you cannot tell, include the product… A product whose release manifest names no path that could ever match is a release manifest to fix, not a product to skip."：拿不准时往哪边偏，是整个第 2 步唯一的判断点。
- `SKILL.md` 第 43 行 "Show this list once and continue. Do not wait for a reply"：防止在用户已经授权的流程里停下来等确认。
- `SKILL.md` 第 83 行 "The machine cannot judge install or use."：说明为什么最后一步必须交给人。
- `driving.md` 第 5 行 "**The release engine owns the loop.** … Do not resume from session memory. Do not pick the next stage yourself."：划清 agent 和引擎的分工，防止 agent 凭记忆恢复。
- `driving.md` `## After a stage fails` 最后一段 "**You do not assign the tier…** You do not edit the worktree to bypass a guard. You do not build a second executor."：A1 执行后这一节会删掉，这三句要移到状态表上方，它们不是流程，是边界。
- `driving.md` `## Pause: missing context` "**Resolve it yourself when you can.**" 和第 5 步的停止条件（"billing, a contract, a protected path, or a product decision the user must make"）：什么时候自己处理、什么时候交给人，是这个技能里最重要的判断。
- `driving.md` 第 52–55 行 "Step 3 says commit because the remote build ships `git archive HEAD`…"：说明不提交为什么等于没改，防止下一轮拿同一份代码再失败一次。
- `driving.md` `## Close` "If neither exists, say you have no path. Do not invent one."：防止编造安装包路径。
- `driving.md` `## An interrupted build` 全段：有真实事故（474afb36 的注释写着"真发生过一次，代价是一轮四十分钟的编译要靠人手工收尾"），而且"新开一轮会删掉正在被读的源码树"这个后果 agent 自己推不出来。
- `new-product.md` `## The product shape this skill packages`，"is not something to bend a release manifest into; it is a capability the skill does not have yet"：防止 agent 把不合适的产品硬塞进这个技能。
- `new-product.md` 第 16 行 "**A release manifest written before these exist fails at minute forty of a compile, not at minute zero.**" 和那张 "Missing shows up as" 表：每一项都写明了客户会看到什么。
- `new-product.md` `### The self-check module` "The only thing standing between a missing dynamic dependency and a customer finding it."
- `new-product.md` `### The chain that carries the backend into the package` "a package that installs cleanly and then does nothing… nothing checks them for you"，以及 "a stray copy of the sources beside it is the leak the whole compile exists to prevent"。
- `new-product.md` `## Coming from existing packaging scripts` 全节，尤其 "Do not re-decide any of them: a value in there is usually a fix for something that once broke, and the commit that explains it is long gone." 和 "two ways to build the same product is the state where the next person edits the one that no longer runs."：这是迁移时的思考方式，不是步骤。
- `key.md` 第 7 行 "**Adding a product means writing a release manifest. It does not mean writing Python.**…"，以及 `## What belongs where` 整节（"Move to a different app — does this have to be rewritten?" 和检查那一段）：这是技能的设计原则，遇到清单外的字段时 agent 靠它判断。
- `key.md` `toolchain` 段 "Restating the derived ones is how a release manifest ends up demanding a tool the build does not use"。
- `key.md` `### vendor_artifacts` 的 "**Nothing is downloaded.**"、"**The hashes are the point.**"、"**A copyleft binary travels with its licence.**" 三段：说的是客户机上悄悄变慢、许可证违约这类没人会报告的后果。
- `key.md` `### runtime_assets` "**The default `root` is not arbitrary.**…with every build step green."
- `key.md` `### python_backend` "What each field prevents" 下的每一条（`include_package_data` 会把内部 `CLAUDE.md` 打进客户的 exe、`console: false`、`isolate_dirs` 等）。
- `key.md` `### What is genuinely optional` 全段：第一份 manifest 为什么可以写得很少。
- `key.md` `### diagnose_rules` "Get that prefix wrong and a network blip is dispatched to a code fix…"。
- `key.md` 最后一句 "A release manifest is proven by a package that installs, not by a script that assembles."
- 模板 `release_templates/nuitka_electron.ps1.tmpl` 和 `release-flow.sh` 里那些带事故原因的注释（例如 `Initialize-BuildMachine` 里 `NUITKA_RESOURCE_MODE` 那段 "Measured on this machine: two targets in one round produced byte-identical exes"）：agent 不加载它们，但维护者改脚本时靠这些注释才不会把防线简化掉。只删其中的历史叙述（见 S7），原因要留下。

### 缺口与补充草稿

- **G1** `SKILL.md` 开头，`# Release` 下第 10 行之后：技能从没告诉 agent 它在这件事里负什么责任、产出给谁用。66089d06 删掉了 "The release engine is the deterministic layer… **You are the judgement layer:** name the products for this run, read the state and run the action it names, and diagnose the one class of pause the release engine cannot judge." 删除的理由是维护者设计说明应该放进 ADR。但这段恰好告诉 agent 哪些事交给引擎、哪些事要它自己用脑子。缺了它，agent 容易走向两个极端：要么把整个流程当成照着状态表执行的 SOP，遇到 `needs-context` 就上交；要么反过来去碰分级和守卫。建议补上下面这段，比原文多了"产出给谁用"：
  > The package is what a paying customer installs, on a machine you will never see. Everything that can be decided mechanically — stage order, retries, failure tiers, the guards — lives in the release engine. Your judgement is needed in three places: which products this change reaches, what a pause the engine cannot classify really means, and when a problem stops being a release repair and becomes the user's decision. A green log is not the goal; an installer that works is.

  这与 `SKILL-SET-REVIEW.md` "the maintainer's reason for a design → an ADR" 那一条冲突。按任务书的规定，以任务书为准：这段在行动时改变 agent 做什么，不只是解释设计。

- **G2** `SKILL.md` `## 1. Preconditions`（A6 改写后剩下的那一句）：现在给的原因是"引擎不许自修复提交和未提交的改动混在一起"，这是次要原因。真正的原因是构建机拿到的只有 `git archive HEAD`。agent 如果只知道次要原因，可能会自己把改动 stash 起来然后照常出包，结果做出的包跟用户眼前的代码不一致。
  > The build machine receives `git archive HEAD` and nothing else. Uncommitted work does not ship, so a dirty tree means the user would test a package that differs from the code in front of them: stop and say which files are uncommitted.

- **G3** `SKILL.md` `## 2. Name the products for this run`，"Match them against the paths each release manifest names…" 之后：现在的匹配规则只列了壳目录、编译入口、打包数据和 `asset_roots`，漏掉了共享代码。实例：`~/agentflow` 的 parrot manifest 在 `include_packages` 里写了 `shared`，而这个包在 `src/shared/`，不在 parrot 自己的目录下。改一次 `src/shared/` 不会命中上述任何一条，parrot 就会不出包，客户拿到的仍是旧代码。`pyproject.toml`、`uv.lock`、hook 脚本、`remote-build.json` 也是同样的情况。
  > The paths are evidence, not the rule. What decides is whether the change reaches what this product's customer installs: a package the product lists in `python_backend.include_packages` that lives outside its own directory, a dependency lock, a hook script or the release manifest itself all change the package. Leaving out a product the change reached ships it stale; including one it did not costs one build.

- **G4** `SKILL.md` `## 4. Same-commit check` 开头：现在只写了机制（"an earlier package may not match the final code"），没写后果。e74e0140 删掉了 "**Do not give the user a mixed-commit set of packages.**"，而 `cmd_close` 的注释里写着原因："把几个包混着发出去，客户装到的是两份不同的东西"。
  > A set whose packages come from different commits is two versions of the product: whoever installs more than one gets a combination nobody built or tested together.

- **G5** `driving.md` `## Pause: missing context` 第 3 步之后（紧接 "Code or config changes commit to the current branch"）：protection_source 里是计费（`~/agentflow/scripts/release/release_protection.json` 中的 `src/gateway/**`）、迁移、合同、密钥这类路径。自动修复碰到它们会被 P0 拦下，交给人决定；但驱动 agent 自己提交时，没有任何机制拦它。技能没告诉 agent 这一点，fix brief 反而说 "The engine rejects edits to protected paths"（A10），agent 于是会以为有守卫兜底。这是本报告里唯一牵涉钱的缺口。
  > On this path you commit, and no path gate runs on your commit. The release manifest's `protection_source` names the paths an automatic fix may never touch — billing, migrations, contracts, secrets. A fix that needs one of them is the user's decision, not a release repair: stop and report. Editing the release manifest itself (adding an `include_modules` entry, say) is a normal repair here.

  另一个选项是工程改动：`cmd_resume` 在 HEAD 变化时，把上一轮 `source_commit` 到新 HEAD 之间改动的路径和 protection_source 对一遍，碰到就 `needs-redirection`。这样守卫也能覆盖驱动 agent。它守的是会花钱的路径，是否这样做见文末"需要用户拍板"。

- **G6** `key.md` `### build_hooks` 最后一段 "A hook is an addition, never a substitute. On every build the skill already checks that no business source ships…"：66089d06 把原来三条检查的说明压成了一句罗列，丢了原因（原文："Compiling exists to not ship source. A package that ships it still installs and still runs, so nothing reveals the leak — the product's commercial premise is simply gone."）。缺了原因，写 hook 或 `extra_flags` 的 agent 不知道为什么这道检查绝不能绕过。
  > Compiling the backend exists so that no business source ships; a package that leaks it still installs and runs, so nothing but this check ever notices.

  插在这句之后："On every build the skill already checks that no business source ships (the packages in `python_backend.include_packages`)"。

- 看过、判断为不必恢复的：e74e0140 删掉的那些具体事故数字（"One product shipped 36 of those inside the customer's exe"、"one product carried 4 GB that way"、"NVIDIA driver from 2021… 2025"）。现在的通用写法已经把后果说到了客户层面，这些数字属于历史记录。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| C1 | `SKILL.md` `## 2.` 的匹配规则（"Match them against the paths each release manifest names — its shell directory, its compile entrypoints and packaged data, its `asset_roots`. A hit means ship that product."） | 用一张固定的字段清单代替了"这次改动会不会进客户的包"这个判断。清单外的情况（共享包、锁文件、hook 脚本）agent 没有方向，而且真实仓库里就有这种情况（G3） | 目标 + 判断点：保留这张清单作为证据来源，把 G3 那段写成规则本身 |
| C2 | `driving.md` `## After a stage fails` 和 `## State table` 里只有机械动作的几行 | 把引擎内部的派发顺序写成了 agent 要逐条执行的步骤（A1） | 交给 `advance`。文字只留需要 agent 的状态：`PAUSED:needs-context`（诊断并修复）、`PAUSED:needs-redirection`/`CORRUPT`（原样转给用户）、`SUCCESS`（`close`） |
| C3 | `driving.md` `## Pause: missing context` 第 1–5 步 | 编号步骤里只有第 4 步 `resume` 真正依赖顺序。第 1–2 步（读 receipt、从日志诊断）是 agent 默认就会做的事；第 3 步把 ENV-ACTION 的细节和"要提交"混在一起。编号让它读起来像一张检查单，其实是一个判断 | 写成："Goal: the round resumes with the cause gone, or the user holds the one question only they can answer. The engine's receipt and the logs it names are the evidence; do not guess past them. Environment causes you act on; code or config causes you fix and commit (the build ships `git archive HEAD`); then `resume`." 再加上第 5 步的停止条件和 G5。第 52–55 行关于提交原因的说明保留 |
| C4 | `SKILL.md` `## 1. Preconditions` 两行表 | 两条检查做成了表格，其中一条和第 2 步重复（A6） | 一句话 + `init` 的拒绝 |
| C5 | `SKILL.md` `## 4.` 和 `key.md` `## Prove it without building` | agent 手工执行的确定性比对和命令序列（A3、A5） | 交给脚本子命令，文字只留原因和"读生成的脚本"这个判断 |

以下顺序确实有依赖，必须留：`init` → 驱动 → `close`/`abort` 按产品逐个进行（状态文件只有一个）；修复后先提交再 `resume`（构建取的是 `git archive HEAD`）；第 4 步在所有产品出完包之后做；第 5 步最后做。

## 脚本

- **S1 走不到的分支（死代码）。** `release-flow.sh` `cmd_where` 第 780 行的 `NO-STAGES`、`cmd_exit_check` 第 1601 行的 `NOT-DONE:stages=EMPTY`：因为有三个标准 stage，`stages` 不可能为空。`cmd_stage_run` 第 1214 行 "stage $name has an empty argv"：`StageSpec.run` 有 `min_length=1`，标准 stage 的 argv 也不为空。第 1283 行 "manifest.diagnose is empty"：`_diagnose_argv_source` 在 manifest 不声明时会给默认值，结果永远不空。`verify_key.py` 第 128 行 `if backend is None`：合同里 `python_backend` 是必填字段，注释自己也写了"这里是防御"。第 160 行 `if manifest.build_target.desktop_dir:`：字段有 `min_length=1`，条件恒真。`builders/nuitka.py` `probe_names` 里的 `dll_source == "repo"` 分支和 `_native_ext_segments` 文档里的 "`repo` 来源"：合同是 `Literal["compile_interpreter", "system32"]`，没有 `repo`。`release_script_assembler.py` `_hook_line` 第 114 行 `Write-HookSkipped`：每个调用者都先判断了 `is not None`，模板里也没有定义这个函数，真走到这里反而会生成坏脚本。合计约 15 行。
- **S2 自动修复后端那一套（按四问判定为过度防御，删除要用户拍板，见文末）。** 涉及 `fix_dispatch.py` 的 `_run_backend`、`_unwind_worker_commits`、`_BACKEND_RULES`（约 80 行），`release-flow.sh` 的 `_post_fix_gate`（第 475 行，约 50 行，负责自动修复提交后跑检查、不过就回滚），`cmd_dispatch_direct` 第 539–546 行冻结保护规则快照（`PROTECTION_FROZEN`），以及 `_snapshot_baseline_untracked` / `_collect_candidate_paths` 里扫描被 gitignore 的受保护文件那两段（约 20 行）。四问如下。触发过吗：没有。`~/agentflow`、`~/xiaohuangya`、`~/douyin-master-resolve` 的 `git log --all` 里没有一个引擎格式的提交（`fix(release): <指纹>` 或 `chore(release): regenerate <指纹>`）；`~/.zshrc`、`~/.zprofile`、`~/.bashrc`、`~/.mmw` 里都没有设 `RELEASE_FIX_BACKEND`；冻结快照和 gitignore 扫描的来源提交 21ae185f、a876c515 自己写着 "plan-09 揪出"，是评审推理出来的，不是事故。正常输入走得到吗：`fix` 模式只有设了 `RELEASE_FIX_BACKEND` 才会产生改动，`fix_dispatch.py` 的默认路径总是以退出码 1 结束。前提实测过吗：它为之设计的外部 worker（`worker.sh`）已经删了，`fix_dispatch.py` 的文档字符串里写着。删掉后谁处理：驱动 agent 修复（现行默认路径），加上 G5。剩余风险：失去"接一个无人值守修复器"的能力；四个产品仓库各自维护的 `post_fix_gate.py` 从来没被调用过。另外，`derive`（P2）也走同一段"收集改动 → 路径检查 → 提交"的代码，产品的 `build_doctor.py` 能产出 P2，所以这段是可达的，只是从没提交过。收集和路径检查这部分如果还要保留 derive 就得留；冻结快照和 gitignore 扫描对 derive 来说前提也是推理出来的。
- **S3 `release_script_assembler.py` 的原子写和回滚。** `atomic_write`、`_restore`，以及 `assemble` 里 `output_existed`/`output_previous`/`output_replaced` 那一套（约 40 行）。触发过吗：没有记录。正常输入走得到吗：只有两次 `replace` 之间出操作系统错误时才会走到。删掉后谁处理：`assemble` 失败时退出码 3 → stage failed → build 不会运行；重新 assemble 会覆盖两个文件；`skill_fingerprint` 能挡住过期的脚本。前两问都是"否"，判定为过度防御，建议改成直接写两个文件。
- **S4 `release_script_assembler.py check` 与 `render_metadata`。** `check` 拿组装器自己刚写的输出去对照同一次运行生成的 metadata。`hook_calls[].skipped` 在第 658 行永远是 False，因为只有不是 None 的 hook 才会进 `step["hooks"]`，所以第 805 行那个比对不可能失败。BOM 检查也不可能失败，因为 `atomic_write` 固定用 `utf-8-sig`。标准流水线不跑 `check`，只有 `key.md` 里手工调用和两个测试用到。产品仓库里也没有读 `render_metadata` 的地方（`grep` 过 `~/agentflow/scripts`、`~/xiaohuangya/scripts`、`~/douyin-master-resolve/release`）。建议删掉 `check`、`render_metadata` 和 `_check_script`（约 70 行），A5 的 `dry-run` 不带它。剩余风险：手改过的 `release.ps1` 不会被发现，但它本来就会被下一次 assemble 覆盖。
- **S5 `emit_event` 校验自己生成的事件。** `release-flow.sh` 第 677 行：每发一个事件就 `uv run release_contracts.py validate-event` 一次，每次要启动一个解释器。事件由引擎用固定的 jq 拼出来，tier 来自已经校验过的 findings，失败时也只打印不阻断（`return 0`）。四问前两问都是"否"。建议删掉这次调用和 `validate-event` 这个 CLI 子命令；`ReleaseLoopEvent` 这个类要留，产品的 `event_sink` 通过 `--contracts` 在用。
- **S6 重复的逻辑。** `release_script_assembler.py` 第 486 行在同一个文件里又写了一遍 `builders/nuitka.py` `_probe_var` 的变量名规则（`"$Dll_" + 把 source:name 中非字母数字的字符换成下划线`）。两边一旦改得不一致，生成的 PowerShell 会在 StrictMode 下遇到未定义变量。建议 assembler 直接调用 `nuitka._probe_var`（改成公开函数）。`protection_source` 的"必须是相对路径"检查出现在两处（`release-flow.sh` `_load_path_hard_deny` 的 `case`，以及 assembler 的 `_validate_manifest_paths`），可以留一处，影响很小。
- **S7 脚本注释里的历史叙述（类别 3，维护者读，优先级低）。** `fix_dispatch.py` 文档字符串 `## 为什么它在技能里`（"这个文件原本在产品仓库…MMW 把那个插件整个删掉时"）；`diagnose_core.py` `## 为什么它在技能里` 的第二段；`release-flow.sh` 第 684–688 行 "已安装扁平 cache 与源仓库 plugin/scripts/ 两种布局……是 event 落地长期失败的根因"（plugin 布局已经不存在了）；第 822、990、1016、1110 行 "忠实复刻现役 build-pc-installers.sh"（那份脚本已经不是现役，原因句要留，"复刻现役"这类说法删掉）；`release_script_assembler.py` 第 71 行 "跟 v1 的差别"、第 777 行起 `_check_script` 的 "v1 的步号写死"；`release_contracts.py` 第 99 行 "（消灭深抽丢编译知识：F-A）"、第 217–220 行 "修正1 验齿 + 修正2 深抽 … 修正4 命根子"（评审编号和自造的词）；`verify_key.py` 第 324 行 `.v2.json` 后缀（旧命名，四份真实 manifest 没有一个用这个后缀）。另外有一处注释自相矛盾：第 815 行说远端 "DefaultShell 默认 cmd.exe"，第 1021 行说 "PC 默认 shell 是 PowerShell"。
- **S8 `builders/nuitka.py` 的 `argv` / `argv_all`（约 50 行）。** 没有任何调用者，测试里也没有；文档字符串说是"给对拍测试用：跟旧代码生成的 argv 比"，而那次比对早就做完了。但 `new-product.md` `## Coming from existing packaging scripts` 要求 agent "generate the command the release manifest produces… and compare them"，这恰好就是它的用途，只是文字没有指向它。两种处理：加一个 CLI 入口（`python <scripts>/builders/nuitka.py argv --adapter <m> --repo-root <r>` 打印每个 target 的真实 argv），再在 `new-product.md` 那句话里点名；或者直接删掉。前一种把 agent 手工做的比对变成一条命令，属于类别 1，建议选这个。
- **S9 公开 CLI 上只给测试用的入口。** `stage done`（`cmd_stage_done`，第 1298 行）和 `surface`（第 1496 行）在 `driving.md` 里都没出现，只有 `mmw-v2/tests/exe-release/test_release_flow.sh` 用 `stage done` 快进 fixture。`stage done` 能把没执行过的 stage 标成 done，已经有"只能确认最早未完成的 stage"这道限制。可以不改；如果要收紧，把它从 `usage_release` 里隐藏掉即可。
- 看过、判断为不是过度防御（有真实事故，或正常输入走得到）：远端根目录字符白名单（`diagnose_core` 有对应的 env 规则，用户手写路径时走得到）；接回正在运行的构建（474afb36，真实事故）；`schtasks /run` 启动确认和重试（沿用旧脚本的 build5 经验）；清理上一轮留下的 exitcode；只保留最近两个失败的构建目录；`Assert-OnefilePayloads` 及其兜底 `Assert-DistinctExeTails`（兜底只在 `--remove-output` 时生效，而 `verify_key` 会拒绝它，看起来重复；但它守的是"两个 exe 装的是同一个程序、每一步都显示通过"这种客户可见的事故，而且 Nuitka 改了目录命名时兜底也会生效，所以留着）；`env:missing_RELEASE_REMOTE_HOST`、`env:active_product_process` 这两条诊断规则真实触发过（`~/douyin-master-resolve/.release/release-artifacts/a2-build/build.findings.json`、`a4-build/build.findings.json`）。

## 与其他技能的重复或交接问题

- exe-release 是独立技能：`mmw-v2/skills.txt` 第 38 行安装它，集合里没有别的技能启动它或读它的产出（`grep -rn exe-release mmw-v2/ docs/agents/ AGENTS.md` 只命中测试说明和 `docs/contexts/toolbox/CONTEXT.md` 第 7 行的归属说明）。第 5 步失败时 "report the symptoms to the user and wait for their decision"，不再自动开票转 `dispatch`（0d6b1014 之后改的），交接关系清楚。
- 技能内部的重复："why commit"（构建取的是 `git archive HEAD`）写在 `driving.md` 第 52–55 行、`fix_dispatch.py` `_AGENT_RULES`、`key.md` 最后一段，以及 A6/G2 的新句子里。保留 `driving.md` 那份（它覆盖所有 needs-context 情况，agent 从头读到）和 G2（场景不同：出包之前）；`_AGENT_RULES` 缩成半句 "(the build ships `git archive HEAD`)"；`key.md` 那句是新产品首次出包时的提醒，保留。
- `remote-build.json` 缺字段时的处理写在 `new-product.md` 第 85 行（"Missing in both places is a `PAUSED:needs-context` you can often close yourself…"），和 `diagnose_core.py` 第 53–62 行 remediation 的意思相同。agent 在 pause 那一刻从 `receipt` 读到的是 remediation，所以 `new-product.md` 那句只需保留 "The environment variables win over the file — that is how a one-off switch to another machine is done."，其余可以删（约 30 词，没计入 A）。

## 没查到的

- 模板 `nuitka_electron.ps1.tmpl` 里 `Resolve-BuildDll`、`Invoke-BuiltExeSmoke`、`Assert-NoBusinessSource`、`Get-VendorArtifact`、`Copy-RuntimeAsset`、`Assert-LicensesShipped` 的函数体（大约第 50–407 行）只读了头部注释，没有逐行读；`builders/nuitka.py` 的 `commands()`（第 115–178 行）也只读了一部分。这些地方有没有过度防御，本报告没有下结论。
- 测试套件 `mmw-v2/tests/exe-release/`（3,023 行）没读，也没运行。S1、S3、S4 删掉代码时，要同步删测试里对应的断言，这一点是推断。
- "从未触发"的证据不完整：`close` 会删除状态文件，每轮 `init` 会清空 `release-artifacts/`，所以本机状态只能看到每个仓库最后一轮。S2 的主要证据是三个产品仓库完整的 git 历史里没有引擎格式的提交，这个证据比状态文件可靠；但"路径检查拒绝过、所以没有留下提交"这种情况无法排除。
- 用来判断"真实使用"的只有本机三个仓库，其他机器上有没有用法不知道。
- 没有在构建机上验证任何 PowerShell 行为。
- `key.md` 没写 `build_machine`（`setup`/`teardown`，stdout 的 `KEY=VALUE` 协议）、`diagnose_branches`、`diagnose_core_exe_glob`；四份真实 manifest 全都用到了 `build_machine.setup`。新产品是否需要它，说明目前只在 `release_contracts.py` `BuildMachine` 的文档字符串里。本报告判断第一份 manifest 用不到，所以没列为缺口；这一点是推断。

## 需要用户拍板

1. **是否删掉自动修复后端（S2）。** 这是范围决定：删掉等于去掉一个从没用过的能力。连带的后果有三：`post_fix_gate` 字段从合同里删除，而合同是 `extra="forbid"`，四个产品仓库的 manifest 都得改，还要为此写 downstream-note；各产品仓库里的 `post_fix_gate.py` 变成废文件；以后要接无人值守修复器就得重新做。不删的代价是大约 200 行从没运行过的代码，以及一个会误导 agent 的"引擎统一过路径闸"印象（A10）。
2. **G5 的另一个选项：要不要把路径检查扩展到驱动 agent 的提交。** 守的是计费、迁移、密钥这类路径，属于钱的问题。只改文字（A10 + G5）是工程上的最低做法；在 `resume` 时对新提交的路径做检查，能把"agent 修复时顺手改了计费代码然后出包"这条路径堵死，代价是 agent 编辑 release manifest 这种正常修复也要在规则里单独放行。
