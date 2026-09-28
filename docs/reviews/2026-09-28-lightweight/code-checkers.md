# code-checkers

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：这是全集写得最好的技能之一。`## The rule that decides where a tool goes`、第 4 步 "everybody starts passing `--no-verify`, and the checker no longer checks anything"、第 5 步 "A checker that never ran reports the same zero as a clean repository"，都是改变判断的句子。它的问题是缺内容，不是多内容。唯一真实落地过的仓库 agentflow 暴露了三处洞：
- 票工作树里 pyrefly 一个文件都扫不到。
- 检查器覆盖不到的目录，没有任何人查。
- "存量不挡提交"只做到了两个工具。

这三处都有 tracker 记录。调查员的补充草稿我逐条核对过证据，基本全部采纳。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `references/python.md` `## pyrefly` 配置块加两行，并在其后加一段 | 配置：`disable-project-excludes-heuristics = true`、`use-ignore-files = false`。段落：**Worktrees under an ignored directory.** pyrefly matches ignore files and its default excludes against absolute paths, so a worktree whose path passes through a gitignored directory (`.worktrees/`, `.claude/worktrees/`) matches no file at all: the check fails with "No Python files matched", and every commit from that worktree needs `--no-verify`. List the excludes yourself and turn both of those off. | 功能缺口：MMW 的票工作树在 `.worktrees/issue-<n>`，下游仓库都忽略了 `.worktrees/`，照现在的样例配置每张票都会碰上（agentflow #712）。修后 #871 显示 pyrefly 在工作树里正常运行。 |
| I2 | `SKILL.md` 第 5 步开头，替换 "**Probe every checker.** A checker that never ran reports the same zero as a clean repository." | **Probe every checker.** A checker fails silently in three ways, and each reports the same zero as a clean repository: it never found its engine, its baseline swallows the new error, or its paths exclude the directory the code is in. Aim each probe at the mechanism you would otherwise be trusting: plant one in every directory that holds code of that language, including those outside the package layout (scripts, test harnesses, extensionless executables), and run the probes from a fresh worktree, which is where agents commit from. Reviewers skip what tooling enforces, so a directory no checker covers is checked by nobody. | 原探针只证明检查器"会报错"，不证明它"查到了代码所在的地方"。agentflow 的 `.mmw/` 连续四张票（#717、#768、#993、#996）在所有检查器范围之外；#717 记着一个调用已删方法的错误因此漏过。末句说明后果：`code-review` 的 Standards 轴明确不查工具已查的内容。现有四个探针例子留作例子。前半恢复了 `66089d06` 删掉的"三种无声失效"。 |
| I3 | `references/python.md` 样例 `project-includes` 旁 | `project-includes` lists every directory that holds Python; the four here are an example layout. | 这四项正是 agentflow 修之前漏目录的那份列表，照抄会把洞带进新仓库。 |
| I4 | `SKILL.md` 第 4 步第 4 小项末尾 | This holds for every checker in the set, including one that must see a whole package, and for the entry point below: by default it checks what this branch changed against its base, with a separate flag for the whole tree, and its fix flag rewrites only the files that scope selects. Probe it the other way too: add one clean line to a file that already has findings, and confirm the hook and the entry point both pass. | agentflow #871：入口脚本对票没碰过的文件报存量警告，挡住了一张票；`--fix` 一度对全仓运行，改写约 579 个文件（Nowledge Mem `dadc865e`）。原探针只查漏报，这里补上误报方向的探针。 |
| I5 | `SKILL.md` 第 6 步末尾 | In a repository with `.mmw/target.json`, this command is what its `checks` should run: the pipeline runs `checks` before a ticket closes and again at merge, and it is the only gate a commit made with `--no-verify` still passes through. Take the base branch from `MMW_BASE_REF` when it is set, so a ticket cut from any branch is compared against the branch it merges into. | 条件句，不影响不用 MMW 的仓库。依据：`ui-acceptance` 的 `product-answers.md` `checks` 条；`dispatch.sh` 的 `keep_unfinished_work` 用 `--no-verify` 提交半成品、注释写着由 `checks` 兜底。agentflow #660 记录 pyrefly 红了三天，三张票照样提交进来。基准分支写死为 `origin/dev` 会出错这一点是推断。 |
| I6 | `## The rule that decides where a tool goes`，"Everything else … belongs to the machine." 之后（恢复 `e74e0140` 删掉的原文，压短） | Installing a checker globally is the failure this rule prevents: a new worktree silently has none, a second machine has a different one, and when the global tool upgrades every branch fails at once with no commit to blame. | 在 MMW 里每张票都在新工作树里做，"新工作树里没有检查器"是最常见的情形；有了后果，agent 能判断表外工具。第 2 步的 "Never globally." 随之删去（D3）。 |
| I7 | 第 4 步第 4 小项两种机制之后（恢复 `e74e0140` 删掉的原句） | The point of both is that the checker is **useful on day one** rather than after a cleanup nobody schedules. | 碰到既没有 baseline、也不能输出行号的工具时，agent 用这个目标去选第三种做法（例如只对新文件开启）。 |
| I8 | `## Steps` 末尾，整个技能的完成标准 | Done when, from a fresh worktree, every checker reports a defect planted in each directory it covers, a one-line clean edit to a file with existing findings passes both the hook and the entry point, a probe commit is refused, and the repository's `AGENTS.md` names the tools, the one command, the hook and how to skip it. | 现在各步的完成线加起来，不包括"存量不挡人"和"在工作树里能跑"，而这两条正是真实出事的地方。第 7、8 步各自的完成线保留。 |
| I9 | 第 6 步 "Keep per-checker output to its summary line; a failing step prints its tail and the command to re-run for the full output." 改为右栏 | Its readers are agents with little attention to spare: a passing checker is one line, a failing one shows enough to act on and the command for the rest. Decide pass or fail by exit code, never by a printed summary; some tools print none. | 原文的前提"每个工具都有汇总行"实测不成立：oxlint 1.80 不打印汇总行（Nowledge Mem `8c991c17`）。 |

### 删除与改正

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | 第 3 步 "Configure before looking at the error count: most of a first run is misconfiguration, not debt." | 删，只留 "**Configure** — per-language detail in the reference files." | 第 4 步第 1 小项是 agent 分拣时读的那一处，说的是同一件事。 |
| D2 | `references/python.md` `## Commands` 六行 | 换成一行 `uv run djlint <template-dir> --lint`（不加 `--lint` 不做检查），或并进 `## djlint` | 其余是配置写好后任何 agent 都会写的命令；pyrefly 的命令已在 baseline 代码块里。 |
| D3 | 第 2 步 "… Never globally." | 删 | 理由由 I6 放回规则所在的一节。 |
| D4 | `references/python.md` `## ruff` "Recent `ruff` releases enable most rules by default." | 改为 "Recent `ruff` releases enable several hundred rules by default." | 事实错误：实测 0.16.5 默认启用 413 条，共 969 条。 |

### 不采纳

- C4（合并第 1–3 步）：可选，收益约 20 词。

## 结论

`mmw-v2/skills/code-checkers/` 共 3,000 词：`SKILL.md` 1,189，`references/git-hooks.md` 742，`references/python.md` 633，`references/typescript.md` 436；没有脚本，也没有测试套件。这个技能已经很精简：没有历史注记、没有 issue 号、没有空态度，编号步骤的顺序大多有真实的先后依赖。能删的只有约 60–90 词（两处重复、一段一眼就能写出的命令清单），另有一处我实测为错的事实。

主要问题不是多了，而是少了。它唯一真实的落地仓库 `~/agentflow`（`.pre-commit-config.yaml`、`scripts/dev/lint.sh`、`scripts/dev/lint_changed.py` 都照这个技能建）在上线后两周里出过 8 张与检查器有关的票：工作树路径让 pyrefly 一个文件都扫不到（agentflow #712）；`.mmw/` 不在任何检查器范围内，因此一个调用已删方法的错误没人发现（#717、#768、#993、#996）；入口脚本对没改过的 TypeScript 和 shell 文件做全仓检查，挡住了一张票（#871）；`lint.sh --fix` 改写全仓 579 个文件（Nowledge Mem 记忆 `dadc865e`）。这些都落在技能已经说过的原则之内（“存量不拦提交”、“没跑过的检查器和干净仓库一样报 0”），但技能只把原则用在了它点名的那几种情况上，也从没告诉 agent 检查器在 MMW 流水线里服务谁。

“灵魂”基本完整：放在哪、怎么 pin、首跑怎么分拣、为什么只用 git hook，这几段都讲了理由。缺的是三件事：谁依赖这些检查器（夜里在新工作树里干活的 worker、不再检查工具已查内容的 reviewer、`.mmw/target.json` 的 `checks`），检查器“无声失效”有哪几种，以及“存量不拦提交”这条要落到每一个检查器和入口脚本上。建议补约 250 词，净体量略增。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| A1 | `SKILL.md` `## Steps` 第 3 步 "Configure before looking at the error count: most of a first run is misconfiguration, not debt." | 6 | 第 4 步第 1 小项 "**Misconfiguration.** … This is usually most of the count. Fix the config, not the code" 说的是同一件事，而且第 4 步是 agent 真正分拣时读的那一处 | 第 4 步第 1 小项承担；无剩余风险 | 第 3 步只留 "**Configure** — per-language detail in the reference files."，约减 15 词 |
| A2 | `references/python.md` `## Commands`（"uv run ruff format <paths>  # writes" 起六行） | 2、6 | `uv run pyrefly check` 在 `## pyrefly` 的 checker baseline 代码块里已经出现；其余几行（`ruff format`、`ruff check --fix`）是配置写好之后任何 agent 都会写的命令 | 各节的配置和 pyrefly 代码块承担；`--lint` 这个 djlint 参数不显然，保留那一行 | 整节换成一行：`uv run djlint <template-dir> --lint`（djlint 不加 `--lint` 不做检查），或并进 `## djlint`。约减 40 词 |
| A3 | `SKILL.md` `## Steps` 第 2 步 "… Never globally." | 6 | 与 `## The rule that decides where a tool goes` 重复，而且单独一句禁令不带理由 | 若采纳 B 的补充 B5（把全局安装的后果放回 `## The rule…`），这里的禁令就重复了 | 删 "Never globally."，理由只在 `## The rule…` 留一份。约减 2 词，主要是去掉一条无理由的硬规则 |

另有一处事实错误（不是删减项，是改正项）：`references/python.md` `## ruff` 开头 "Recent `ruff` releases enable most rules by default."。我在 `~/agentflow/.venv/bin/ruff`（0.16.5）上实测：`ruff check --isolated --show-settings` 列出默认启用 413 条，`ruff rule --all` 共 969 条，不到一半。建议改为 "Recent `ruff` releases enable several hundred rules by default."。这句的作用是让 agent 别去手动开规则族，改后作用不变。

没有第 1 类（技能没有脚本，也没有复述脚本行为的文字）、第 3 类（`grep` 查 "no longer / now / 日期 / #号" 无命中；唯一的 "no longer" 在第 4 步第 4 小项，说的是后果，不是历史）、第 5 类（见 C 表下的说明）。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 开头 "Give a repository the checkers its languages need, wired so a fresh clone or a new worktree has them …"：整个技能的完成目标，下面所有取舍都拿它来衡量。
- `SKILL.md` `## The rule that decides where a tool goes`：一条判据覆盖表里没列的工具（agent 碰到 `sqlfluff`、`stylelint` 时照它判断放哪），是技能的核心思想。
- `SKILL.md` `## What to install` 下的 "Settled choices, and the fact that decides each" 四条及 "Re-check both facts against the tools' own release pages before repeating them to a user."：触发条件里有“检查器已被取代”，agent 要向用户解释为什么换，而最后一句防止它把会过时的事实当成永久事实复述。
- `SKILL.md` `## Pin the formatter exactly, the checkers loosely`：理由（格式化器版本不同导致整文件 diff 在合并时冲突）让 agent 能给表外工具定 pin 法；"Pin exactly, too, anything whose version is coupled to another tool's" 是可推广的原则。
- `SKILL.md` 第 4 步引言 "reading it in the order the tool printed it is how the whole effort gets abandoned" 和第 4 小项 "everybody starts passing `--no-verify`, and the checker no longer checks anything"：这两句讲的是做浅了的全局后果。agentflow 的提交 `458c73a15`（2026-09-02）说它就是因为这个原因返工的。
- `SKILL.md` 第 4 步 "Filter to the changed lines" 里的 "Two traps"：来自真实踩坑（本仓提交 `e071fef6` 的说明："补进去的还有两个真踩到的坑"）。
- `SKILL.md` 第 5 步 "A checker that never ran reports the same zero as a clean repository."：探针存在的理由。
- `references/git-hooks.md` 开头一段（"The git hook is the only place every author passes through …"）：说明为什么不用各家 agent 的 hook。第 7 步 "Wire this even when per-agent automation is out of scope" 依赖它。
- `references/git-hooks.md` "`language: system` means … disagreeing with the manual entry point about whether the code passes."：只有一个版本，这是技能核心原则在 hook 里的应用。
- `references/git-hooks.md` "A fixer that rewrites semantics belongs in neither …"：划清了在 hook 里什么可以自动改、什么不可以。
- `references/git-hooks.md` `## The \`core.hooksPath\` trap` 和 "Whether a missing prek should skip or block is the repository's call"：前者是真实情况（agentflow 的 `core.hooksPath` 就是 `.githooks`）；后者把判断交还给 agent，正是本轮要的写法。
- `references/python.md` "Rules worth reading rather than fixing in bulk, because each one names a place the code can lose an error or a fact"：告诉 agent 哪些发现不能批量修，这段不是清单，是思路。
- `references/python.md` `## djlint` 末句 "The target is a clean run, so that the next non-zero count means something."：调校规则的目的。
- `references/typescript.md` "every type-aware rule in the config is decoration" 和 `## Two packages sharing one toolchain`：后者在 `66089d06` 被删后，由用户在 `fc45126c` 恢复（"agentflow has two Electron shells and the guard test it asks for"），属于已定事项，不要再删。

### 缺口与补充草稿

- **B1（功能缺口，优先级最高）`references/python.md` `## pyrefly` 配置块：MMW 的工作树里 pyrefly 可能一个文件也扫不到。** agentflow #712（2026-09-08 实测、已关）：工作树的绝对路径里含一个被 `.gitignore` 忽略的段（当时是 `.claude/worktrees/`），pyrefly 按绝对路径套用 ignore 规则和默认排除规则，整棵工作树都被判为忽略，`pyrefly check` 报 "No Python files matched patterns" 并退 1。每次提交都被挡，worker 只能 `--no-verify`，这道门就这样无声地关掉了。MMW 的票工作树就在主 checkout 的 `.worktrees/issue-<n>` 下，而 agentflow 和本仓的 `.gitignore` 都有 `.worktrees/`（agentflow 第 116 行、本仓第 6 行），所以按技能现在的样例配置，每个下游仓库的每张票都会碰上。agentflow 的修法是在 `pyproject.toml` `[tool.pyrefly]` 加两行，之后 #871 里的输出显示 pyrefly 在 `.worktrees/issue-854` 下正常跑出 "0 errors (91 suppressed …)"。在样例配置里加这两行，并在后面补一段：
  > ```toml
  > disable-project-excludes-heuristics = true
  > use-ignore-files = false
  > ```
  > **Worktrees under an ignored directory.** pyrefly matches ignore files and its default excludes against absolute paths, so a worktree whose path passes through a gitignored directory (`.worktrees/`, `.claude/worktrees/`) matches no file at all: the check fails with "No Python files matched", and every commit from that worktree needs `--no-verify`. List the excludes yourself and turn both of those off.

- **B2 `SKILL.md` 第 5 步：探针只证明检查器“会报错”，不证明它“查到了代码所在的地方”，也不在 agent 实际工作的地方跑。** `66089d06` 删掉的 `references/probing.md` 引言原本列出三种无声失效："a type-aware linter that never found its engine, a checker baseline that swallows everything, a rule set that excluded the directory it was aimed at. All three report success."，还有一句原则 "each aimed at the mechanism you would otherwise be trusting"。现行第 5 步只剩按检查器种类列的探针，第三种失效（范围漏了目录）完全没有探针覆盖。真实后果：agentflow 的 `.mmw/`（harness、stories、journeys）连续四张票（#717、#768、#993、#996）都不在 ruff、pyrefly、oxlint 的范围里。#717 写明 "A call to a deleted method in `seeds.py` went unnoticed because of this"。更糟的是，code-review 的 Standards 轴明确不查工具已查的内容（`mmw-v2/upstream/skills/engineering/code-review/references/standards-reviewer.md`："Skip anything tooling already enforces; a linter's job is not yours."），所以检查器漏掉的目录就没有任何人查。另外，`references/python.md` 的样例 `project-includes = ["src", "tests", "scripts", "migrations"]` 正是 agentflow 修之前的列表，照抄就把这个洞带进新仓库。建议第 5 步开头改成：
  > **Probe every checker.** A checker fails silently in three ways, and each reports the same zero as a clean repository: it never found its engine, its baseline swallows the new error, or its paths exclude the directory the code is in. Aim each probe at the mechanism you would otherwise be trusting. Plant one in every directory that holds code of that language, including those outside the package layout (scripts, test harnesses, `.mmw/`, extensionless executables), and run the probes from a fresh worktree, which is where agents will commit from. Reviewers skip what tooling enforces, so a directory no checker covers is checked by nobody.

  同时把 `references/python.md` 的 include 列表标成样例："`project-includes` lists every directory that holds Python, the four here are an example layout"。

- **B3 `SKILL.md` 第 4 步第 4 小项与第 6 步：“存量不拦提交”只落在了 ruff 和 pyrefly 上。** 技能把两种机制写成“linter 用改动行过滤、type checker 用 checker baseline”。但 `references/git-hooks.md` `## Three shapes of hook` 的 “Whole-project” 和 “Runs in a subdirectory” 两种形状（例子就是 oxlint）会查整个包；shellcheck 没有任何机制；第 6 步的入口脚本也没说默认查什么范围、`--fix` 改什么范围。真实后果：agentflow #871，`lint.sh` 对这张票没碰过的 TypeScript 和 shell 文件报了存量警告，票 #854 被挡；`lint.sh --fix` 一度对全仓跑 `ruff format` 和 `ruff check --fix`，实测改写约 579 个文件、1397 处（Nowledge Mem 记忆 `dadc865e`，2026-09-05）。技能的探针也只查漏报（该报的报了），从不查误报（存量没被报）。agentflow 的提交 `458c73a15` 自己补了这一项（“在一个有 5 条存量问题的文件里加一行干净代码，检查通过”）。建议在第 4 步第 4 小项末尾加：
  > This holds for every checker in the set, including one that must see a whole package, and for the entry point below: by default it checks what this branch changed against its base, with a separate flag for the whole tree, and its fix flag rewrites only the files that scope selects. Probe it the other way too: add one clean line to a file that already has findings, and confirm the hook and the entry point both pass.

- **B4 `SKILL.md` 第 6 步：没说入口脚本在 MMW 流水线里交给谁。** 在一个有 `.mmw/target.json` 的仓库里，这条入口命令就是 `checks` 键该跑的东西（`mmw-v2/skills/ui-acceptance/references/product-answers.md` 的 `checks` 条目：`--closeout` 在关票前跑它，每条命令都拿到 `MMW_BASE_REF=origin/<into>`，失败就不关票；`docs/contexts/night/how-it-works.md` 写明合并时也跑，红了就把票退回）。流水线还默认它会跑：`mmw-v2/skills/dispatch/scripts/dispatch.sh` `keep_unfinished_work` 用 `--no-verify` 提交 worker 留下的半成品，注释写 "the next worker's commits and the closeout's checks run them as usual"。agentflow 的 `checks` 实际只跑 `pytest tests/guards tests/contracts`，而 `lint.sh` 的基准写死为 `LINT_BASE:-origin/dev`，票不是从 `dev` 切出时基准就不对（这一点是推断，没有实测）。agentflow #660 的后果与此相符：pyrefly 这道门红了三天，三张票的 worker 照样把代码提交进来了。建议在第 6 步末尾加：
  > In a repository with `.mmw/target.json`, this command is what its `checks` should run: the pipeline runs `checks` before a ticket closes and again at merge, and it is the only gate a commit made with `--no-verify` still passes through. Take the base branch from `MMW_BASE_REF` when it is set, so a ticket cut from any branch is compared against the branch it merges into.

  这条要写成条件句，因为技能也服务不用 MMW 流水线的仓库。

- **B5 `SKILL.md` `## The rule that decides where a tool goes`：全局安装的后果被删了。** `e74e0140`（2026-09-22）删去："Installing a checker globally (`uv tool install ruff`, `npm i -g eslint`, `brew install shellcheck`) is the failure this skill exists to prevent: a new worktree silently has no checker, a second machine has a different one, and the day the global tool upgrades, every branch fails its checks at once with no commit to blame." 现在只剩第 2 步一句无理由的 "Never globally."。在 MMW 里每张票都在新工作树里做，“新工作树里没有检查器”正是最常见的情形；这句话还让 agent 在表外工具（例如 shellcheck 为什么是例外）上能自己判断。建议恢复成短版，放在 "Everything else … belongs to the machine." 之后：
  > Installing a checker globally is the failure this rule prevents: a new worktree silently has none, a second machine has a different one, and when the global tool upgrades every branch fails at once with no commit to blame.

- **B6 `SKILL.md` 第 4 步：“为什么要两种机制”的目的句被删了。** `e74e0140` 删去 "The point of both is that the checker is **useful on day one** rather than after a cleanup nobody schedules."。碰到一个既没有 baseline 也不能输出行号的工具时，agent 需要用这句目标去选第三种做法（例如只对新文件开）。建议放回第 4 小项的两种机制之后，原文照用。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| C1 | `SKILL.md` `## Steps` 整体：只有第 5、7、8 步有 `Done when`，没有整个技能的完成标准 | 各步的完成线加起来，只证明了“能抓到植入的错误、hook 能拒提交、AGENTS.md 写了”，不包括“存量不挡人”和“在工作树里也能跑”，而这两条正是 agentflow 真实出事的地方（B1、B3）。agent 按步打勾就会认为做完了 | 在 `## Steps` 末尾加一条总完成线，替代各步零散的标准（第 7、8 步的可以保留）：`Done when, from a fresh worktree, every checker reports a defect planted in each directory it covers, a one-line clean edit to a file with existing findings passes both the hook and the entry point, a probe commit is refused, and the repository's AGENTS.md names the tools, the one command, the hook and how to skip it.` |
| C2 | `SKILL.md` 第 6 步 "Keep per-checker output to its summary line; a failing step prints its tail and the command to re-run for the full output." | 规定了输出格式，而它依赖的前提“每个工具都有汇总行”实测不成立：Nowledge Mem 记忆 `8c991c17`（2026-09-03）记录 "oxlint 1.80 在本机不打印「Found N warnings and M errors」汇总行"，只能靠退出码判断 | 换成目标加一个判断点：`Its readers are agents with little attention to spare: a passing checker is one line, a failing one shows enough to act on and the command for the rest. Decide pass or fail by exit code, never by a printed summary; some tools print none.` |
| C3 | `SKILL.md` 第 5 步 "For each one, write a file that must fail …: a new type error … for a type checker with a baseline …; a floating promise … for a type-aware linter; an unclosed tag … for a template linter; a badly formatted file … for a formatter." | 只按四种检查器列了探针，没有设计原则。shellcheck、shfmt 以及“范围漏了目录”都不在表里，agent 碰到时没有方向 | 按 B2 的草稿先给原则（三种无声失效、探针对准你本来要信任的那个机制），现有四个例子保留为例子 |
| C4 | `SKILL.md` 第 1–3 步 | 不算死板，但这三步里真正需要 agent 判断的只有两句（“文件很少的语言不需要检查器”、“先配置再看数”），其余是任何 agent 都会做的动作 | 低优先级，可选：并成一段 "Pick the languages worth checking (a handful of files is not), add their tools to the project manifest, and configure them from the reference files before reading any count."，约减 20 词 |

顺序真正有依赖的部分要保留：先装再配，先配再看数（首跑的大多数报错是配置问题），分拣顺序（先修配置、再机器修、再格式化、最后才是真存量），先探针再接 hook，再写进 AGENTS.md。这些顺序都有理由，不是作者的偏好。

过度防御：逐条用四个问题查了 `references/git-hooks.md` 的 `core.hooksPath`、prek 的暂存行为、缺 prek 时跳过或阻断，以及 `references/typescript.md` 的 "stop and report" 和 `## Two packages sharing one toolchain`。`core.hooksPath` 在 agentflow 真实存在；双包那一节由用户恢复。其余几条我没找到触发记录，但都是一两句话，正常使用能碰到，删掉后没有别的机制兜底，所以不算过度防御。

## 脚本

无。

一个相关的判断，只记录，不建议改：第 4 步 "Filter to the changed lines" 让每个仓库自己写过滤器（agentflow 的 `scripts/dev/lint_changed.py` 有 146 行）。按“确定性工作交给脚本”，我查了现成工具：

- `reviewdog/reviewdog`（github.com/reviewdog/reviewdog，`gh api` 看到 9,628 star，最近一次推送 2026-09-26）：`-reporter=local -filter-mode=added -diff="git diff …"` 可以本地按 diff 过滤。本机 ruff 0.16.5 支持 `--output-format rdjson`，oxlint 支持 `-f checkstyle`，两者我都实测了参数列表。
- `Bachmann1234/diff_cover` 的 `diff-quality`（846 star，最近一次推送 2026-09-25）：读了 `diff_cover/violationsreporters/violations_reporter.py`（`ruff_check_driver` 跑 `ruff check --output-format pylint`）、`diff_cover/diff_reporter.py`（有 `include_untracked`）、`diff_cover/git_path.py`（路径转换）。这三处正好覆盖技能说的两个坑。但它的 `supported_extensions=["py"]` 会漏掉没有扩展名的 Python 脚本，agentflow #993 恰好就是这类文件（`.mmw/journeys/*/run`），而它是一个 Python 依赖，只服务 Python。

结论：维持“自己写”，不把过滤器做成技能脚本。原因是这个工具属于被检查的仓库（技能自己的核心规则），不能从技能目录的软链接去调；现成工具又各有覆盖不到的情况。可选的小改：`references/python.md` 的 "third-party diff wrappers break on its releases" 是从 darker 一例推出来的泛化说法，我没有证据说明 diff-quality 或 reviewdog 也会这样。可改为 "`darker` broke on ruff's releases; `diff-quality` (diff_cover) handles both traps but only files ending in `.py`"，让 agent 先试现成工具。

## 与其他技能的重复或交接问题

- `mmw-v2/skills/manage-agents-md/SKILL.md` 第 307 行（"Linter territory … suggest … wiring it as a pre-commit hook with the `code-checkers` skill"）是唯一指向本技能的入口，交接写得清楚。
- 本技能第 8 步复述了 manage-agents-md 的格式（`## Commands` 一行、其余进 `## Key Conventions`）。保留在本技能：做这一步的 agent 当时没有加载 manage-agents-md，这句防止它写坏格式。
- `mmw-v2/skills/dispatch/references/night.md` 第 149 行警告不要把仓库自己的全树检查器（"a `lint.sh`, a full type-check"）写进 `CHECK:`。保留在 night.md（写票的 agent 在那一刻读它）。如果采纳 B3、B4，入口脚本默认只查本分支改动，这个警告描述的风险会变小，但仍然成立（全树 type check 没有改动行的说法），不用改。
- 交接缺口（见 B4）：`ui-acceptance` 的 `checks`、`verify-ticket` 的 `--closeout`、`dispatch.sh` `keep_unfinished_work` 都默认仓库的检查器会在 `checks` 里跑，但本技能从没提 `checks`。补充应写在本技能第 6 步（建入口的 agent 在那一刻读它），不必改 ui-acceptance。
- `standards-reviewer.md` "Skip anything tooling already enforces" 依赖检查器覆盖完整。这一点应在本技能里写出来（B2），reviewer 那边不用改。

## 没查到的

- 没有核实这些事实：`references/git-hooks.md` 里 lefthook “不隔离暂存内容”的说法、prek 会 stash 未暂存改动的说法；`SKILL.md` 里 pyright 慢一个数量级、ty 未稳定的说法（技能自己已要求复述前重新核对）；`references/typescript.md` 里 `options.typeAware` 只从根配置读、`oxlint-tsgolint` 版本号编码 TypeScript 版本的说法。
- 没有核实 reviewdog 对绝对路径和未跟踪文件的处理，也没有在真实仓库里跑过 reviewdog 或 diff-quality。
- B1 的两行配置在 agentflow 里有效（#712 已关，#871 的输出显示工作树里 pyrefly 正常），但我没在其他 pyrefly 版本上验证这两个键名。
- B4 里“`lint.sh` 基准写死 `origin/dev`，票从别的分支切出时会比错”是读源码推断的，没有触发过的记录。
- 推断未证：`## Pin the formatter exactly, the checkers loosely` 说检查器用版本范围是对的，因为 "only adds diagnostics"。但对带 baseline 的 type checker，重新锁版本时拉进的新诊断同样会让所有分支一起变红。有 `uv.lock` 或 `pnpm-lock.yaml` 时，这只在更新锁文件时发生，而技能没有提锁文件。没找到真实触发，所以没列为发现。
- 真实使用证据只来自 agentflow 一个仓库（其 tracker、`pyproject.toml`、`.pre-commit-config.yaml`、`scripts/dev/lint.sh`、`AGENTS.md`，以及 Nowledge Mem 记忆 `dadc865e`、`6147ebf4`、`8c991c17`）；没有查其他下游仓库。
