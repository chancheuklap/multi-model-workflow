# N7 清点：retro、advisor、exe-release、code-checkers、manage-agents-md、diagram-design

本报告只做事实清点，为下一轮「pstack 组件规范」判断「拆不拆、放哪、值不值」提供证据，不做归置决定。日期 2026-09-29，基于 `dev` 分支 `f2ba7593`；安装检出 `.worktrees/mmw-installed` 在 `61f1065c`，两者在 `mmw-v2/` 下无差异（`git diff --stat 61f1065c HEAD -- mmw-v2` 为空，已核实），所以下文描述的就是当前生效的版本。

## 0. 读了什么、怎么读的

完整读完（逐行）：
- `mmw-v2/skills/retro/SKILL.md`（210 行）；`mmw-v2/skills/advisor/SKILL.md`、`references/consulting.md`、`references/advising.md`；`mmw-v2/skills/exe-release/SKILL.md`、`references/driving.md`、`references/key.md`、`references/new-product.md`；`mmw-v2/skills/code-checkers/SKILL.md`、`references/python.md`、`references/typescript.md`、`references/git-hooks.md`；`mmw-v2/skills/manage-agents-md/SKILL.md`、`references/create.md`、`references/rewrite.md`、`scripts/check.sh`（110 行，全读）。
- `mmw-v2/merge-notes/diagram-design.md`；`docs/contexts/release/CONTEXT.md`；`docs/adr/0014-advisor-has-one-door.md`、`docs/adr/0031-worker-start-memory-is-a-searched-index.md`、`docs/adr/0015-no-custom-subagents.md`；`mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md` 第 1–137 行（`## What skill text is for` 到 `### Refusals and output an agent reads`）。
- diagram-design：`SKILL.md` 第 1–140 行与第 395–585 行逐行读，其余按标题目录读；`SKILL.md` 与 `references/output-spec.md` 对上游 squash 提交 `8a85636a` 的完整 diff；`scripts/verify-geometry.py` 对上游的完整 diff；整个 subtree 对上游树的 `git diff --stat`。

脚本（只读头注释、`--help`、子命令分派、退出码，以及决定行为的函数）：
- `retro.py`：模块文档串、`main()`、`refusal_for()`、`gather()`、`search()`、`observed_check()`、`evidence_source()`、`check_analysis()`、`validate_prompt()`、`qualifies()`、`proposal_body()`、`create_or_reuse()`、`render()`、`receipt()`、`finalize()`（约 818 行中的约 600 行）；运行了 `retro.py --help`。
- `release-flow.sh`（1360 行）：头注释与退出码表、`usage_release`、`_convergence_guard`、`_run_derive`、`cmd_dispatch_p2`、`emit_event`、`_skill_fingerprint`、`_standard_stages`、`cmd_init`、`cmd_where`、`cmd_stage`、`_run_remote_build` 前段（参数、远端配置、路径白名单）、`cmd_stage_run`、`cmd_stage_done`、`cmd_stage_fail`、`cmd_dispatch`、`cmd_dispatch_p1`、`cmd_round`、`cmd_surface`、`cmd_resume`、`cmd_close`、`cmd_abort`、`cmd_same_commit`、`cmd_receipt`、末尾 `case` 分派；运行了 `release-flow.sh --help`。未读：`_run_remote_build` 的断线重连与轮询主体、`_remote_run_and_poll`、`_fetch_remote_build_log` 主体。
- `diagnose_core.py`：文档串与 `main()`；`fix_dispatch.py`：文档串与 `main()`；`release_contracts.py`：文档串、`main()`、`ReleaseFinding`；`release_script_assembler.py`：文档串与开头常量；`verify_key.py`：文档串与 `main()` 返回值；`builders/nuitka.py`：文档串；`release_templates/nuitka_electron.ps1.tmpl`：前 30 行。
- `check.sh`：全读；运行了 `check.sh --limit`（输出 `150`）。

只读命令：上述 `--help`；`git log`/`git show`/`git diff`；`nmem --json memories list --label mmw-retro` 与 `memories show`（三条 Retro Memory）；`gh issue view` 三张 agentflow issue；在 `~/agentflow`、`~/xiaohuangya` 里 `git log -1` 与 `grep`。

线索材料的用法：`docs/reviews/2026-09-28-lightweight/{retro,advisor,exe-release,code-checkers,manage-agents-md,diagram-design}.md` 与 `汇总.md`、`docs/reviews/2026-09-23-skill-set/汇总.md`、`docs/reviews/2026-09-29-vocabulary-recheck/DECISIONS.md`、`docs/research/mmw-structure/2026-09-06-handoff.md`、`reports/T4-toolbox.json`、`reports/I5-mmw-field-evidence.json`、`M2`/`M3` 相关段落。凡被采用的结论都标「已核实」（回到原文或现场看过）或「未核实」。

---

## 1. 部件清单

### 1.1 retro（本仓自有；`mmw-v2/skills.txt` 的 `self/retro`）

| 文件 | 是什么 | 给谁用 |
| --- | --- | --- |
| `mmw-v2/skills/retro/SKILL.md` | 一夜结束后的证据式复盘流程：`## Gather` → `## Analyze` → `## Decide` → `## Finalize`，加 `## Prevention destinations` 表 | 夜的 orchestrator（主 agent），在 `summary` 记下 `spec.closed` 之后、同一会话里加载 |
| `mmw-v2/skills/retro/scripts/retro.py` | 三个子命令：`gather <spec>` 盘点证据并输出 JSON；`search <category> <cause>` 在 `mmw-retro` label 的 Memory 里找旧发生；`finalize <spec> <analysis> <gather>` 复验分析、开 `needs-triage` proposal issue、写固定 id 的 Retro Memory、贴 `spec.retroed` 事件。退出码 0 成功（JSON 在 stdout），2 拒绝（三段式拒绝在 stderr）；参数错误也是 2 | 同上 agent；`finalize` 的产物由用户、triage、下一次 retro 读 |

脚本依赖：按文件路径加载 `verify-ticket/scripts/events.py`、`issue_tree.py` 与 `ui-acceptance/scripts/refusal.py`（`retro.py` `load()`，已核实）；外部命令 `gh`、`nmem`、`git`、`rg`。测试：`mmw-v2/tests/retro/`（`run.sh` 7 个场景）。

### 1.2 advisor（本仓自有；`self/advisor`）

| 文件 | 是什么 | 给谁用 |
| --- | --- | --- |
| `mmw-v2/skills/advisor/SKILL.md`（13 行） | frontmatter 触发条件 + 一张两行表：发起咨询的一方读 `consulting.md`，被启动为 advisor 的会话读 `advising.md` | 任何撞上决定的 agent（worker、主 agent）；以及 advisor 会话本身 |
| `references/consulting.md` | 何时值得咨询、怎么启动（`dispatch.sh advise <file>`）、回答怎么对待、brief 的五部分、不许引导 | 发起方 |
| `references/advising.md` | advisor 怎么读 brief、怎么回答、绝不做什么（不写文件、不评 diff、不越界） | advisor 会话 |

没有脚本；启动靠 dispatch 技能的 `dispatch.sh advise`（`advise_one`，已读）。模型行在 `~/.mmw/models.json` 的 `advisor` 行，默认值在 `mmw-v2/skills/dispatch/hosts.json`（`{"agent": "advisor", "host": "claude", "model": "fable[1m]", "effort": "medium"}`，已核实）。无测试套件（`AGENTS.md` `## Commands` 写明 "`advisor` and `code-checkers` have none"）；`advise` 场景在 `mmw-v2/tests/dispatch/test_dispatch.sh`。

### 1.3 exe-release（本仓自有；`self/exe-release`）

| 文件 | 是什么 | 给谁用 |
| --- | --- | --- |
| `SKILL.md`（76 行） | 出包五步：前提（干净工作树）→ 定本次出哪些产品 → 每个产品一个 release loop → same-commit 检查 → 用户安装实测 | 用户说 ship/package/installer 时的 agent |
| `references/driving.md` | 驱动一个产品的 release loop：按 `where` 的状态表行动、`PAUSED:needs-context` 怎么自己处理、`close`、断线的构建 | 同上，每个产品每次都读 |
| `references/new-product.md` | 把一个新产品带进出包体系：产品形态边界、仓库须先具备的六样、smoke module、三文件链、远端构建机配置、从旧打包脚本迁移 | 本次改动触及一个没有 release manifest 的产品时 |
| `references/key.md` | 写 release manifest：什么放哪（一问判别）、字段形状、每个字段防什么、`build_hooks` 阶段、不构建先验证 | 写或改 release manifest 时（从 `new-product.md` 转来） |
| `scripts/release-flow.sh` | release engine：状态机，`init/where/stage run|done|fail/round next/surface/resume/close/abort/same-commit/receipt/dispatch`；退出码 0/1/2（头注释表） | 驱动 agent；测试 |
| `scripts/release_contracts.py` | 三份 pydantic 合同 `ReleaseAdapterManifest`、`ReleaseFinding`、`ReleaseLoopEvent`；CLI `validate-manifest`、`classify-findings` | 引擎；产品的 `event_sink` |
| `scripts/verify_key.py` | 出包前把 manifest 对着仓库核一遍（秒级）；0 无发现，1 有发现 | 引擎 `verify_key` stage；`key.md` 手工验证 |
| `scripts/release_script_assembler.py` | 把 manifest 装配成构建机的 `release.ps1` 与上下文 JSON；`assemble`，退出码 0/2/3 | 引擎 `assemble` stage |
| `scripts/builders/nuitka.py`（+ `__init__.py`） | 由 manifest 的 `python_backend` 生成 Nuitka 编译命令片段，两个出口（argv、PowerShell） | 装配器、`verify_key.py` |
| `scripts/release_templates/nuitka_electron.ps1.tmpl`（743 行） | 构建机上执行的 PowerShell 模板 | 装配器 |
| `scripts/diagnose_core.py` | 把失败日志翻成带 tier 与根因指纹的 release finding；产品 `diagnose_rules` 先匹配；指纹前缀 `transient:`/`env:` 决定引擎动作 | 引擎 `stage run` 失败路径 |
| `scripts/fix_dispatch.py` | P1 失败时写修复简报 `release-fix-brief.md`，打印 `FIX-BRIEF=<path>`，退出 0 | 引擎 `cmd_dispatch_p1` |

测试：`mmw-v2/tests/exe-release/`（11 个测试文件 + PowerShell 检查）。术语表：`docs/contexts/release/CONTEXT.md`（168 行，整个 bounded context 只服务这一个技能）。下游说明：`mmw-v2/downstream-notes/release-self-heal-removed.md`。

### 1.4 code-checkers（本仓自有；`self/code-checkers`）

| 文件 | 是什么 | 给谁用 |
| --- | --- | --- |
| `SKILL.md`（66 行，1540 词） | 工具放哪的规则、装什么（语言→工具表与选型理由）、pin 规则、8 步（数文件 → 装 → 配置 → 首跑分拣 → 探针 → 一个 checker command → commit hook → 写进 AGENTS.md） | 给某仓库装/换 linter、formatter、type checker 的 agent |
| `references/python.md` | ruff、pyrefly、djlint 的配置与坑（pyrefly 在被忽略目录下的 worktree 扫不到文件、`search-path`、checker baseline） | Python 分支 |
| `references/typescript.md` | oxlint + oxlint-tsgolint、`typeAware` 只读根配置、探针、两个包共享工具链 | TS/JS 分支 |
| `references/git-hooks.md` | prek、`language: system`、三种 hook 形状、formatter 在 hook 里改哪些文件、`core.hooksPath` 陷阱、真实提交探针 | 第 7 步，每次都读 |

无脚本，无测试套件。

### 1.5 manage-agents-md（本仓自有；`self/manage-agents-md`）

| 文件 | 是什么 | 给谁用 |
| --- | --- | --- |
| `SKILL.md`（330 行，3981 词） | 固定格式的 `AGENTS.md`/`CLAUDE.md`：分流（create/rewrite）→ Survey（分组派 subagent、提示模板、合并成 `survey-list.md`）→ Ask the user（4+7 问与嵌套目的表）→ Write（不写什么、语言、步骤、根模板、代码与测试规则去 `CODING_STANDARDS.md`/`TESTING.md`、嵌套模板、`<important if>` 块、写作规则、指针）→ Prune → Verify and report | 被要求建或重写 `AGENTS.md` 的 agent |
| `references/create.md`（12 行） | create 情形的 Set up，然后回 `SKILL.md` `## Survey` | create 分支 |
| `references/rewrite.md` | rewrite 情形的 Set up 与 `## Migrate`（每条旧规则与命令记到 `destinations.md`，旧文件的去向，报告的两张清单） | rewrite 分支 |
| `scripts/check.sh` | 机械检查：根文件行数上限 `ROOT_LIMIT=150`、每个 `AGENTS.md` 旁的 `CLAUDE.md` 只含 `@` 行且有 `@AGENTS.md`、反引号路径存在、`<important>` 标签配对、子目录那句话（按英文词 grep）、不残留 `AGENTS.override.md`。`--list` 列出扫描的文件，`--limit` 打印上限；有失败时每行一条、退出 1，全过打印 `ok` | 技能的 agent；测试 `mmw-v2/tests/manage-agents-md/test_check.sh` |

### 1.6 diagram-design（上游 `cathrynlavery/diagram-design` 的 subtree；`dd/diagram-design`）

| 文件或目录 | 是什么 | 给谁用 |
| --- | --- | --- |
| `mmw-v2/upstream-diagram-design/skills/diagram-design/SKILL.md`（585 行，6039 词） | 画图技能正文：§0 选配色 → §1 理念 → §2 何时用 → §3 选型（语义模式、40 种图型路由表）→ §4 反模式 → §5 设计系统 → §6 SVG 原语与连线规则 → §7 布局与复杂度预算 → §8 摘要卡 → §9 出图前检查清单 → §10 模板 → §11 导入 draw.io/Mermaid/Excalidraw → §12 输出与无障碍合同 | 任何要画图的 agent；本仓里由 `wait-what` 的 `VISUAL.md` 与 `improve-codebase-architecture` 调用 |
| `references/`（56 份） | 每种图型、原语、导入、导出、风格、profile 的细则 | 按 §3/§11 路由按需读 |
| `assets/`、`scripts/`（技能内 4 个：三个 extract 脚本 + `self_check.py`） | 模板与示例 HTML；导入提取器与自检 | 画图时 |
| `repo-root -> ../..`（本仓加的 symlink） | 让技能目录里的 `repo-root/scripts/…` 指到 subtree 根 | 运行 `verify-geometry.py`、`verify-motion.py`、`lint-skin.py` |
| subtree 根的 `scripts/`（本仓改了 `verify-geometry.py` 与其测试）、`commands/`、`prompts/`、插件清单 | 上游仓库级校验器与各宿主的插件包装 | 校验器被 §6/§9 调用；插件包装本仓不用（ADR 0003 不走插件） |
| `mmw-v2/merge-notes/diagram-design.md` | 本仓对上游的每处改动与意图、谁调用它、subtree pull 命令 | 拉上游的维护者 |

---

## 2. 内容分类表

类型记号：顺序、做法、带理由的规则（下称「规则+理由」）、命令与接口、重入与分派、格式与模板、目的与立场、沉积。「读者/时刻」一栏写谁在什么时候读、是否每次都读。

### 2.1 retro/SKILL.md

整份只有一个文件，没有 reference，每次 retro 从头读到尾（只在夜尾跑一次，每个 spec 一次）。

| 段落 | 类型 | 读者/时刻 | 备注 |
| --- | --- | --- | --- |
| frontmatter `description` "Use right after the dispatch skill's `summary` records `spec.closed`" | 重入与分派（触发） | 宿主扫描；主 agent | 进入点只有这一个时刻 |
| 第 8 行 "Run `python3 scripts/retro.py` from a checkout … whose `HEAD` is `origin/<base branch>` … `finalize` reads repository files from that working tree" | 做法 + 规则+理由 | 每次 | 脚本不检查这一点（`gather()` 无 HEAD 比对，已核实） |
| 引言第 10–14 行 "Run an evidence-first retrospective … Retro Memory … Work the user approves applies the improvements later" | 目的与立场 | 每次 | |
| 第 16–20 行 "A problem exists only when a tracker event comment, commit, current repository file, or observed check proves it … Use Memory, Thread … to discover what to verify" | 规则+理由（认识论：线索与定案分开） | 每次 | 潜在原则 |
| 第 22–28 行 "Three readers act on this record …" | 目的与立场（谁依赖、做浅的代价："costs twice"） | 每次 | 2026-09-28 复审 I1 加入（已核实在现文中） |
| 第 30–35 行 "Look for what in the environment let the mistake through … blameless postmortem … record `none`" | 规则+理由 / 立场 | 每次 | 来自上游 `in-progress/retro` 的 "improvements to the coding agent's environment"（已核实上游原文） |
| 第 37 行 "The script writes outputs; the agent judges causes and dispositions." | 规则+理由（分工） | 每次 | 与 SKILL-SET-RULES 事实 2 同义 |
| `## Gather` 1 | 顺序 + 命令与接口（`gather`，保存 JSON）+ 做法（从 `tickets[].events`、`spec_events` 找偏航处） | 每次 | |
| `## Gather` 2 "A missing source narrows the analysis; it never means … did not happen" | 规则+理由 | 每次 | |
| `## Analyze` 3（上次 proposal 是否落地） | 做法 + 格式（证明形式：SHA、跨仓库 commit URL、`Rule:`、`nowledgemem://memory/`、文件路径）+ 规则（issue 关闭不是证据） | 每次；只有上一条 Retro Memory 有 proposal 时有实质工作 | 证明形式与 `check_analysis()` 的判定一一对应（已核实） |
| `## Analyze` 4（形成问题、证据形式、`check:` 命令约束） | 规则+理由 + 命令与接口（`check:` 只允许 `rg` 与七个只读 git 子命令，无 shell，无输出即拒绝） | 每次 | 命令约束复述 `observed_check()`（已核实）；这是「脚本将如何裁决」的原样规则，SKILL-SET-RULES `### Scripts and judgement` 第 2 条允许 |
| `## Analyze` 5（`search` 与旧发生的计数） | 命令与接口 + 规则（同一 ticket 两条评论算一次） | 每个 problem 一次 | |
| `## Analyze` 6（intent reconciliation） | 做法 + 目的（"catches a night that met every criterion yet delivered something other"） | 每次 | |
| `## Analyze` 7（review learning） | 做法 + 规则+理由 | 每次 | |
| `## Analyze` 8（七类及各自 "Use when"） | 做法（逐类检查清单） | 每次 | 七类原样来自上游 `in-progress/retro`（已核实） |
| `## Decide` 9（两种处置） | 做法 | 每个 problem | |
| `## Decide` 10（门槛与 stall event 定义） | 规则+理由（"Every prevention has a standing cost"）+ 定义 | 每个 problem | 门槛同时由 `qualifies()` 执行（已核实） |
| `## Decide` 11（`prompt_change` 字段与完整段落要求；读 `writing-for-agents`） | 格式与模板 + 规则 + 点名技能 | 只在有 prompt 类 proposal 时 | 复审记录 7 个真实 proposal 都没有 `prompt_change`（未核实，引自 2026-09-28 复审） |
| `## Finalize` 12（分析 JSON 形状） | 格式与模板 | 每次 | |
| `## Finalize` 13（`finalize` 命令，拒绝时照改） | 命令与接口 + 重入（拒绝即「从哪改起」） | 每次 | |
| "Done when … `spec.retroed` … `result=recorded`; then return to the dispatch skill's `references/night.md` `## 5. The night is over`" | 重入与分派（交回调用方） | 每次 | |
| `## Prevention destinations` 表 | 格式（`destination` 枚举，与 `retro.py` `DESTINATIONS` 相同） | 每个 problem | |
| 表后段 "Choose the destination whose reader acts on the lesson. Workers carry the heaviest context …" | 规则+理由（去处按读者选；机械违规归 check；先看已有 check） | 每个 problem | 潜在原则；来源之一是上游 changeset `retro-deterministic-checks.md`（引自复审，未核实） |

沉积：未发现。

### 2.2 advisor

| 文件/段落 | 类型 | 读者/时刻 |
| --- | --- | --- |
| `SKILL.md` frontmatter `description`（四个触发条件 + "or when you were started as the advisor. Not for what reading the code can settle."） | 重入与分派（唯一入口，ADR 0014 "技能的 frontmatter `description` 正是这样一个位置"） | 所有宿主启动时扫描 |
| `SKILL.md` 正文 "Two moments …" 表 | 重入与分派 | 两侧都读，13 行 |
| `consulting.md` 开头段 | 目的与立场（另起会话、不带上下文、慢而贵） | 发起方，每次咨询 |
| `## When it is worth a session` | 规则+理由（"The test is the cost of being wrong"；不为换答案再问；"the value is a session that has not spent the last hour convincing itself"） | 发起方 |
| `## Start it` | 命令与接口（写 brief 文件 → `dispatch.sh advise <file>` → 在 runner 里读回答）+ Done when | 发起方 |
| `## The answer` | 规则+理由（建议不是裁决；涉及用户决定的交给用户） | 发起方 |
| `## The brief` | 格式与模板（五部分）+ 检验（"a stranger with only this and the repository can reconstruct the decision"） | 发起方 |
| `## The question stays open` | 规则+理由（不给 advisor 划范围；"A second opinion you steered is your own opinion in a stronger model's voice."） | 发起方 |
| `advising.md` 开头 | 目的与立场 | advisor |
| `## The brief tells you what the caller knows` | 规则+理由（越过 brief 里的引导） | advisor |
| `## How to answer` 1–5 | 做法（第 1 条"先看再说"有先后，其余并列） | advisor |
| `## What you never do` | 规则+理由（不写文件："a rule you keep, not one that keeps you"；不评 diff；只答被问的决定） | advisor |

两个 reference 各在自己的分支读，一次咨询每侧只读一份。沉积：未发现。

### 2.3 exe-release

`SKILL.md`（每次出包都读）：

| 段落 | 类型 | 备注 |
| --- | --- | --- |
| 第 8 行 "Ship an install package … far enough that the user can install it." | 目的与立场 | 完成线定在「用户能装上」 |
| 第 10 行 "**Ship what is on the current branch now.** … the user's call, already made" | 立场 / 规则+理由 | |
| `## 1. Preconditions`：release manifest 定义；"The build machine receives `git archive HEAD` and nothing else … stop and say which files are uncommitted. `bash scripts/release-flow.sh init` refuses to start on a dirty tree for the same reason." | 定义 + 规则+理由 + 命令与接口 | 最后一句与脚本不符，见 §9 缺陷 1 |
| `## 2.` 列 manifest、按改动路径匹配 | 做法 + 命令（`git ls-files`、`git diff --name-only $(git merge-base HEAD <parent>)..HEAD`） | |
| `## 2.` "The paths are evidence, not the rule …" | 规则+理由（拿不准就多出一个，漏出代价更大） | 潜在原则 |
| `## 2.` 新产品 → `new-product.md` | 重入与分派 | 分支 |
| `## 2.` 列表格式 "Show this list once and continue. Do not wait for a reply" | 格式 + 立场（不在已授权流程里停下） | |
| `## 3.` 每个产品：`init` → 读 `driving.md` → `close` | 顺序 + 命令 | 顺序由单一状态文件强制（`cmd_init` 拒绝第二个 loop，已核实） |
| `## 4.` same-commit | 规则+理由（混合 commit 的一组包 = 两个版本）+ 命令（`same-commit`）+ 重入（MISMATCH → 回第 3 步） | |
| `## 5.` 用户安装实测 | 顺序（最后）+ 立场（"The machine cannot judge install or use"） | |

`driving.md`（每个产品的 loop 每次都读）：

| 段落 | 类型 | 备注 |
| --- | --- | --- |
| "**The release engine owns the loop.** … Do not resume from session memory … You do not assign the tier" | 规则+理由 / 立场（agent 与引擎分工） | |
| `## State table: do what where says` | 重入与分派 + 命令与接口（`STAGE:`、`PAUSED:needs-context`、`SUCCESS:`、`PAUSED:needs-redirection`、`CORRUPT:`；退出码 0 不代表成功） | 这是 exe-release 的「Find your moment」，由引擎状态驱动 |
| `## Pause: missing context` | 做法（目标句）+ 规则+理由（为什么提交；同一根因两次或涉及计费/合同/产品决定就停） | 只在 needs-context 时 |
| `## Close` | 命令 + 规则（包路径只取 `DELIVERED` 行，不编造；不手删交付记录） | |
| `## An interrupted build` | 规则+理由 + 做法（重跑 `where` 指的 stage，不 `abort`/`init`） | 真实事故（`474afb36`，已核实提交标题） |

`new-product.md`（分支：产品没有 manifest）：

| 段落 | 类型 |
| --- | --- |
| 两种进入方式 | 重入与分派 |
| `## The product shape this skill packages` | 目的与立场（能力边界："a capability the skill does not have yet"） |
| `## What the repository must already have` 表 | 规则+理由（每项漏掉会在客户那里怎样） |
| `### The smoke module` | 做法 + 格式（`SMOKE_IMPORTS` 例子）+ 规则+理由 |
| `### The chain that carries the backend into the package` 三文件表 | 规则+理由 + 格式 |
| `### The installer name has to match the release manifest` | 规则+理由 |
| `## Remote build machine`（`RELEASE_REMOTE_HOST`/`ROOT`、`remote-build.json` 字段） | 命令与接口 + 做法 |
| `## Coming from existing packaging scripts` | 做法 + 规则+理由（常量原样搬、先对拍再删、新路径装得上前不删旧的） |

`key.md`（分支：写或改 manifest）：

| 段落 | 类型 |
| --- | --- |
| 开头 "Adding a product means writing a release manifest. It does not mean writing Python." | 规则+理由（潜在原则） |
| `## What belongs where`（"Move to a different app — does this have to be rewritten?"） | 规则+理由（潜在原则：值归 manifest、动作归技能、业务归产品仓库） |
| `## The shape` | 格式与模板 + 命令与接口（`stages` 排在引擎三段前、`${DESKTOP_DIR}`/`${BUILD_ROOT}`/`${RELEASE_PLUGIN_DIR}`、绝对路径被拒） |
| `toolchain`、`vendor_artifacts`、`runtime_assets`、`python_backend`、`native_ext_dll`、`electron`、`build_hooks`、`What is genuinely optional`、`diagnose_rules` 各节 | 格式与模板 + 规则+理由（每字段防什么客户后果）；`build_hooks` 编码一段是做法 |
| `## Prove it without building` | 命令（`verify_key.py`、`assemble` 到自己的临时目录）+ 做法（读生成的脚本）+ 规则（"proven by a package that installs"） |

沉积：`key.md` 第 5 行 "The filename and the `--adapter` flag … say `adapter`: both are literals the scripts read. Prose calls this file the release manifest." 是命名说明，不是沉积。脚本注释里有历史叙述（例如 `release-flow.sh` `emit_event` 注释 "已安装扁平 cache 与源仓库 plugin/scripts/ 两种布局……是 event 落地长期失败的根因"），agent 不读，属维护者文本。

### 2.4 code-checkers

`SKILL.md`（每次都读）：

| 段落 | 类型 | 备注 |
| --- | --- | --- |
| 引言 | 目的 | |
| `## The rule that decides where a tool goes` | 规则+理由（"A tool whose version changes what the repository produces belongs to the repository"；全局安装的三种后果） | 潜在原则 |
| `## What to install` 表 | 做法 / 格式 | |
| "Settled choices, and the fact that decides each" | 规则+理由；含时效事实（"TypeScript 7 ships no stable programmatic API"），并自带"Re-check both facts against the tools' own release pages" | 时效事实是准沉积，但有复查指令 |
| `## Pin the formatter exactly, the checkers loosely` | 规则+理由 | |
| `## Steps` 1–3 | 顺序 + 做法 | |
| 第 4 步（首跑分拣四级；baseline 或只看改动行；"useful on day one"；反向探针） | 做法 + 规则+理由（存量永不挡提交，否则人人 `--no-verify`） | |
| 第 5 步（探针：三种静默失效；每个目录；从新 worktree 跑） | 做法 + 规则+理由 + Done when | |
| 第 6 步（一个 checker command；按退出码判；在有 `.mmw/target.json` 的仓库它是 `checks`；`MMW_BASE_REF`） | 命令与接口 + 规则+理由 | 这一段是 MMW 流水线接线；不用 MMW 的仓库是条件句跳过 |
| 第 7 步 → `git-hooks.md` | 顺序 + 重入与分派（每次都去） | |
| 第 8 步 写进 `AGENTS.md`（`## Commands` 行、`## Key Conventions`） | 格式（照 `manage-agents-md` 的格式） | 跨技能约定 |
| 末尾总 Done when | 完成标准 | |

`python.md`、`typescript.md`：语言分支，各为做法 + 格式（配置块）+ 规则+理由（pyrefly worktree 陷阱、`typeAware` 只读根配置、oxlint-tsgolint 精确 pin）。`git-hooks.md`：每次都读（第 7 步不可跳），做法 + 规则+理由（`language: system`、`core.hooksPath` 陷阱、prek stash）+ 格式（hook 脚本）+ 探针步骤（顺序）。沉积：未发现（2026-09-28 复审 grep 同样无命中，未重跑）。

### 2.5 manage-agents-md

`SKILL.md` 两个情形都读全文，只有 `create.md`/`rewrite.md` 按分支读。

| 段落 | 类型 | 读者/时刻 |
| --- | --- | --- |
| 开头 "An `AGENTS.md` is loaded into every session of every agent … each line is obeyed as fact …" | 目的与立场 + 规则+理由（写什么的总判据） | 每次；潜在原则 |
| `## Find your situation` + `check.sh --list` + 表 | 重入与分派 + 命令 | 每次 |
| "When the user has already said what the file must say, survey only what verifies those facts" | 规则+理由（短路径） | 每次 |
| `## Survey` `### Groups` | 做法（默认切法：四个主题组 + 每顶层目录一组；按"一个会话装得下"合并） | 每次 |
| `### Dispatch` | 做法（宿主通用 subagent，不点模型；不能并行就顺序跑并落盘） | 每次 |
| 提示模板 | 格式与模板（给 survey subagent 的完整 prompt，含报告字段 `fact/evidence/place/type/when`）+ 规则+理由（只跑不改变外部状态的命令） | survey subagent |
| `### Collect` | 做法 + 格式（`survey-list.md`）+ Done when | 每次 |
| `## Ask the user`（Format、四个身份问题、七个约定问题、嵌套目的表、Record） | 格式与模板 + 规则+理由（"A nested file is one more file that drifts …"） | 每次 |
| `## Write` `### What NOT to Add` 12 条 | 规则（每条带 Bad 例）；第 6 条指向 `code-checkers` | 每次 |
| `### Language` | 规则+理由（标题固定英文，因为别的技能按英文标题加行；`check.sh` 按英文词找子目录那句） | 每次 |
| `### Steps` 1–5 | 顺序 | 每次 |
| `### Root template` + 身份行用途 + convention/gotcha 区分 + 根文件额外一节与行数上限 | 格式与模板 + 做法 + 命令（`check.sh --limit`） | 每次 |
| `### Code and test rules` | 规则+理由（reviewer 的 Standards/Tests 轴读 `CODING_STANDARDS.md`/`TESTING.md`） | 每次 |
| `### Nested template` | 格式与模板 | 有嵌套目录时 |
| `` ### `<important if>` blocks `` §1–§2 | 规则+理由 + 格式（Bad/Good 例） | 有 `when` 条目时 |
| `### Writing rules`、`### Pointers` | 做法 / 规则 | 每次 |
| `## Prune` | 做法 + Done when | 每次 |
| `## Verify and report` `### Checks` | 命令（`check.sh .`）+ 规则（两种可接受的失败） | 每次 |
| `### Report` | 格式与模板（create 与 rewrite 两种） | 每次 |

`create.md`：顺序（两步 Set up）+ 重入（"Continue at `SKILL.md` `## Survey`"）。`rewrite.md`：顺序（Set up → Survey → Migrate → 回 `## Ask the user`）+ 做法 + 格式（`destinations.md` 行格式）+ 规则（旧文件去向表）。沉积：未发现。

### 2.6 diagram-design/SKILL.md（上游）

| 节 | 类型 | 本仓是否改过 |
| --- | --- | --- |
| §0 First-time setup — which style guide | 目的与立场 + 重入与分派（marker → profiles.md；无 marker → 默认配色；送客户 → onboarding.md） | 改（§5 详） |
| §1 Philosophy | 规则+理由（"The highest-quality move is usually deletion."） | 末句改 |
| §2 When to Use | 目的 | 否 |
| §3 Selection（语义模式表、40 种图型表、Rules of thumb、Confirm before drawing） | 重入与分派（按内容路由到一份 type reference）+ 规则 + 顺序（先说计划再画） | Rules of thumb 第三条改 |
| §4 Anti-patterns、§5 Design System | 规则 / 格式 | 否 |
| §6 Core SVG Primitives（连线规则 1–6 等） | 做法 + 规则+理由 + 命令（`verify-geometry.py`） | 加 marker id 一句；rule 3 括号、rule 6 路径改 |
| §7 Layout & Spacing（复杂度预算） | 规则+理由 | 超预算处理改为「先嵌套、按层计」 |
| §8 Summary Card、§10 Templates | 格式与模板 + 顺序（新建图五步） | 否 |
| §9 Pre-Output Checklist | 做法（清单）+ 命令（三个校验脚本） | 两条路径改，加一条「打开渲染结果看」 |
| §11 Importing | 重入与分派（按源格式）+ 顺序 + 格式（四个 dial） | 否（末段 "split above 24" 保留上游原文，见 §9 缺陷 4） |
| §12 Output（单文件、无障碍合同、导出） | 格式与模板 + 规则 | 否 |

读者/时刻：每次画图读 `SKILL.md` 全文，再按 §3 读一份 type reference；导入时按 §11 读 import reference。

---

## 3. 连线

### 3.1 retro

- 被谁调用：dispatch 技能的 `references/night.md`。`## 5. The night is over` 写 "Immediately after `summary` records `spec.closed` … invoke the `retro` skill in this same orchestrator session for this spec; `finish` needs its `spec.retroed` event, recorded."；重入表一行 "The spec carries `spec.closed` and no later `spec.retroed` whose result is `recorded` → 5. The night is over, from the paragraph that invokes the `retro` skill"（已核实）。
- 读的输入：spec 的 body 三节（`Problem Statement`、`User Stories`、`Out of Scope`）、spec 与各 ticket 的事件评论（`events.fold`）、`spec.opened` 的 base/into/project、`spec.closed.payload.memory_closing`（night.md 收尾 pass 写的 Memory 决定，其中 `propose` 决定是给 retro 的线索）、`origin/<into>` 上的提交、最近一条 Retro Memory（`nmem memories list --label mmw-retro`）。
- 产出：`needs-triage` issue（在 proposal 的 `repository`，已存在同证据的 issue 则复用）；Retro Memory（id `mmw-retro-<space>-spec-<n>`，label `mmw-retro`）；`spec.retroed` 事件（`result=recorded|unrecorded`，带 `NIGHT RETRO` 行）。
- 谁读产出：用户读 `NIGHT RETRO`（night.md §5 让主 agent 指给用户）；`dispatch.sh finish` 检查最新 `spec.closed` 之后有 `result=recorded` 的 `spec.retroed`，否则退出 2（`dispatch.sh` 第 4165–4177 行，已核实）；triage 技能处理 `needs-triage` issue；下一次 retro 的 `gather`（`prior_retro`）与 `search`。
- 点名技能：`writing-for-agents`（第 11 步）。
- 引用文档：`night.md` §5（返回点）。

### 3.2 advisor

- 入口：frontmatter description（宿主扫描，任何 agent 自行加载）。没有别的技能点名 advisor：`grep` 在 `mmw-v2/upstream/skills` 里只命中 `writing-for-agents` 的两份规则文件（把 "consult an advisor" 当作 task 的例子），`mmw-v2/prompt/` 无命中（已核实）。dispatch 的 `SKILL.md` 不提 `advise`。
- 运行：`dispatch.sh advise <brief file>`：读 `models.json` 的 `advisor` 行 → 按选定 runner 在当前 worktree 起会话，初始 prompt 为 `Use the advisor skill.` + brief 全文 → 打印会话 id；不写事件，不重试（`advise_one` 注释与代码，已核实）。
- 产出：advisor 的回答只存在于 runner 显示的会话里；发起方自己去读（2026-09-28 用户定为"读法 A"，已核实 `汇总.md` 第 59 行与现文 `## Start it` Done when 一致）。会话 id 交给用户。
- 配置：`~/.mmw/models.json` `advisor` 行（`models.py` `ALLOWED_AGENTS` 含 `advisor`）；默认 `hosts.json`。

### 3.3 exe-release

- 入口：用户要求 ship/package/installer。没有别的技能启动它（M3 报告同此结论；本次 `grep` 命中只有测试、`docs/contexts/*` 与 `downstream-notes`，已核实）。
- 运行：`release-flow.sh` 各子命令；引擎自己运行 `release_contracts.py`（`validate-manifest`、`classify-findings`）、`verify_key.py`、`release_script_assembler.py`（→ `builders/nuitka.py`、`.ps1.tmpl`）、`diagnose_core.py`（或 manifest 的 `diagnose` 替代命令）、`fix_dispatch.py`（P1）、产品的 `derive`（P2）、`event_sink`、`build_hooks`、构建机上的 `release.ps1`（经 ssh/schtasks）。
- 写：`<repo>/.release/release-state.json`（活状态）、`.release/release-artifacts/`（每次 attempt 的日志与 findings、`_loop/` 交接目录）、主检出根的 `.release/delivered/<product>.json`（交付记录，`close` 写）、P2 时在当前分支自动提交 `chore(release): regenerate <fp>`、P1 时写 `release-fix-brief.md`。
- 读产出：驱动 agent 读 `where`/`receipt`/fix brief；`same-commit` 读交付记录；用户拿到包路径与 commit 后做安装实测。
- 配置：`*.release-adapter.json`（产品仓库）、同目录 `remote-build.json`、环境变量 `RELEASE_REMOTE_HOST`/`RELEASE_REMOTE_ROOT`（优先于文件）、`RF_MAX_SAME_FINGERPRINT`（默认 3）、`--max-rounds`（默认 6）、`--max-wall-clock`（默认 14400 秒）。
- 下游：`mmw-v2/downstream-notes/release-self-heal-removed.md` 要求 agentflow 两份、xiaohuangya 一份 manifest 删四个字段。现场核对：`~/agentflow/scripts/release/adapters/hedgehog.release-adapter.json`、`parrot.release-adapter.json`、`~/xiaohuangya/scripts/release/adapters/duck.release-adapter.json` 在各自当前检出里仍各有 4 处这些字段（已核实，仅查了当前检出的分支）；按下游说明，`init` 会在那里以 "Extra inputs are not permitted" 拒绝（推断，未运行）。

### 3.4 code-checkers

- 入口：description（仓库没有检查器、加语言、工具被取代、要 pre-commit hook）。点名它的地方：`manage-agents-md` `### What NOT to Add` 第 6 条 "suggest in the report wiring it as a pre-commit hook with the `code-checkers` skill"。
- 产出：仓库的依赖清单条目、checker 配置、checker baseline 文件、`.pre-commit-config.yaml` 与 hook、一个 checker command、`AGENTS.md` 的 `## Commands` 行与 `## Key Conventions` 条目。
- 谁读：每个在该仓库提交的 agent（hook）；在 MMW 消费仓库里 `.mmw/target.json` 的 `checks` 运行这个命令，由 `verify-ticket.py --closeout` 和 `dispatch.sh` 合并步骤执行，二者都设 `MMW_BASE_REF=origin/<into>`（`verify-ticket.py` 第 1873、2351 行，`dispatch.sh` 第 3640 行，已核实）；code-review 的 Standards 轴不查工具已查的内容（引自复审，未核实该句原文）。
- 引用：`manage-agents-md` 的格式（第 8 步）。

### 3.5 manage-agents-md

- 入口：description（建或重写 `AGENTS.md`/`CLAUDE.md`）。
- 运行：`check.sh --list`、`check.sh --limit`、`check.sh .`；派宿主通用 subagent 做 survey。
- 写：`AGENTS.md`、`CLAUDE.md`（根与嵌套）、`CODING_STANDARDS.md`、`TESTING.md`；scratch 目录里 `survey-list.md`、`destinations.md`（rewrite）。
- 谁读产出：该仓库每个会话的每个 agent；code-review 的 Standards/Tests 轴读 `CODING_STANDARDS.md`/`TESTING.md`（`standards-reviewer.md` 含 `CODING_STANDARDS.md`，已核实文件命中）；`code-checkers` 第 8 步与 `setup-matt-pocock-skills`（`SKILL.md` 第 26、75、82 行按 `## External References` 加行，已核实）按英文标题往里加行；retro 的 `repository-agents` 去处往这个文件提 proposal。
- 引用：`code-checkers`。本仓自己的根 `AGENTS.md` 就是按这份格式写的（含 `<important if>` 块与子目录那句话，已核实第 81 行）。

### 3.6 diagram-design

- 被谁调用：`mmw-v2/upstream/skills/productivity/wait-what/VISUAL.md` 第 16 行 "Read the `diagram-design` skill's `SKILL.md` and follow it … Skip its §3 'Confirm before drawing' pause"；`mmw-v2/upstream/skills/engineering/improve-codebase-architecture/SKILL.md` 第 41 行与 `HTML-REPORT.md` 第 3、28、41 行（已核实）。
- 运行：技能内 `scripts/self_check.py`、三个 `*_extract.py`；经 `repo-root/` 运行 subtree 根的 `verify-geometry.py`、`verify-motion.py`、`lint-skin.py`。
- 配置：项目里的 `.diagram-design` marker 与 profile（`references/profiles.md`）；安装副本的 `references/style-guide.md`。
- 安装：`mmw-v2/skills.txt` 的 `dd/diagram-design`，`install.sh` 的 `DD_SRC`（已核实）。

```edges
skill:dispatch/references/night.md#5 -> skill:retro : calls
skill:retro -> script:retro.py gather : runs-script
skill:retro -> script:retro.py search : runs-script
skill:retro -> script:retro.py finalize : runs-script
skill:retro -> skill:writing-for-agents : calls
skill:retro -> skill:dispatch/references/night.md#5 : hands-off-to
script:retro.py -> module:verify-ticket/events.py : reads
script:retro.py -> module:verify-ticket/issue_tree.py : reads
script:retro.py -> module:ui-acceptance/refusal.py : reads
script:retro.py gather -> event:spec.opened : reads
script:retro.py gather -> event:spec.closed : reads
script:retro.py gather -> artifact:spec.closed.payload.memory_closing : reads
script:retro.py gather -> artifact:Retro Memory (previous) : reads
script:retro.py search -> artifact:Retro Memory (label mmw-retro) : reads
script:retro.py finalize -> artifact:needs-triage issue : writes-artifact
script:retro.py finalize -> artifact:Retro Memory : writes-artifact
script:retro.py finalize -> event:spec.retroed : writes-event
event:spec.retroed -> script:dispatch.sh finish : gates
artifact:needs-triage issue -> skill:triage : hands-off-to
artifact:Retro Memory -> skill:retro : re-enters-at
skill:dispatch/references/night.md#4 -> artifact:spec.closed.payload.memory_closing : writes-artifact
skill:advisor -> skill:advisor/references/consulting.md : routes-to
skill:advisor -> skill:advisor/references/advising.md : routes-to
skill:advisor/references/consulting.md -> script:dispatch.sh advise : runs-script
script:dispatch.sh advise -> config:models.json#advisor : configured-by
script:dispatch.sh advise -> session:advisor : starts
session:advisor -> skill:advisor/references/advising.md : reads
skill:advisor/references/consulting.md -> user : hands-off-to
skill:exe-release -> skill:exe-release/references/driving.md : routes-to
skill:exe-release -> skill:exe-release/references/new-product.md : routes-to
skill:exe-release/references/new-product.md -> skill:exe-release/references/key.md : routes-to
skill:exe-release -> script:release-flow.sh : runs-script
script:release-flow.sh -> script:release_contracts.py : runs-script
script:release-flow.sh -> script:verify_key.py : runs-script
script:release-flow.sh -> script:release_script_assembler.py : runs-script
script:release_script_assembler.py -> script:builders/nuitka.py : reads
script:release_script_assembler.py -> template:nuitka_electron.ps1.tmpl : reads
script:release-flow.sh -> script:diagnose_core.py : runs-script
script:release-flow.sh -> script:fix_dispatch.py : runs-script
script:release-flow.sh -> product:derive : runs-script
script:release-flow.sh -> product:event_sink : writes-event
script:release-flow.sh -> machine:build machine (ssh) : runs-script
script:release-flow.sh -> config:*.release-adapter.json : configured-by
script:release-flow.sh -> config:remote-build.json : configured-by
script:release-flow.sh -> state:.release/release-state.json : writes-artifact
script:release-flow.sh close -> state:.release/delivered/<product>.json : writes-artifact
script:release-flow.sh same-commit -> state:.release/delivered/<product>.json : reads
skill:exe-release/references/driving.md -> script:release-flow.sh where : re-enters-at
skill:exe-release -> user : hands-off-to
doc:downstream-notes/release-self-heal-removed.md -> config:*.release-adapter.json : constrains
skill:code-checkers -> skill:code-checkers/references/python.md : routes-to
skill:code-checkers -> skill:code-checkers/references/typescript.md : routes-to
skill:code-checkers -> skill:code-checkers/references/git-hooks.md : routes-to
skill:code-checkers -> artifact:AGENTS.md#Commands : writes-artifact
skill:code-checkers -> skill:manage-agents-md : cites
artifact:checker command -> config:.mmw/target.json#checks : configured-by
script:verify-ticket.py closeout -> artifact:checker command : runs-script
script:dispatch.sh merge -> artifact:checker command : runs-script
skill:manage-agents-md -> script:check.sh : runs-script
skill:manage-agents-md -> skill:manage-agents-md/references/create.md : routes-to
skill:manage-agents-md -> skill:manage-agents-md/references/rewrite.md : routes-to
skill:manage-agents-md -> subagent:host general-purpose (survey) : starts
skill:manage-agents-md -> artifact:AGENTS.md : writes-artifact
skill:manage-agents-md -> artifact:CODING_STANDARDS.md : writes-artifact
skill:manage-agents-md -> artifact:TESTING.md : writes-artifact
skill:manage-agents-md -> skill:code-checkers : cites
artifact:CODING_STANDARDS.md -> skill:code-review (Standards axis) : reads
artifact:TESTING.md -> skill:code-review (Tests axis) : reads
skill:setup-matt-pocock-skills -> artifact:AGENTS.md#External References : writes-artifact
skill:retro -> artifact:AGENTS.md : proposes-change
skill:wait-what/VISUAL.md -> skill:diagram-design : calls
skill:improve-codebase-architecture -> skill:diagram-design : calls
skill:diagram-design -> skill:diagram-design/references/* : routes-to
skill:diagram-design -> script:self_check.py : runs-script
skill:diagram-design -> script:repo-root/scripts/verify-geometry.py : runs-script
skill:diagram-design -> script:repo-root/scripts/verify-motion.py : runs-script
skill:diagram-design -> script:repo-root/scripts/lint-skin.py : runs-script
skill:diagram-design -> config:.diagram-design marker : configured-by
doc:merge-notes/diagram-design.md -> skill:diagram-design : cites
```

自拟关系：`routes-to`（技能正文把读者送进本技能的某个 reference）；`starts`（起一个会话或 subagent）；`writes-artifact`（写出非事件的工件）；`gates`（事件作为另一命令的前置条件）；`proposes-change`（retro 通过 proposal 提议改某文件，不直接改）；`constrains`（下游说明约束消费仓库文件）。

---

## 4. 重复（全仓 grep 核实）

| 规则/定义 | 出现位置 | 判定 |
| --- | --- | --- |
| 构建机只拿 `git archive HEAD`，所以修复必须先提交 | `exe-release/SKILL.md` 第 16 行；`driving.md` 第 32、36 行；`key.md` 第 225 行；`fix_dispatch.py` 文档串第 11 行与 `_AGENT_RULES` 第 39 行；`docs/contexts/release/CONTEXT.md` 第 167 行 | 真重复（同一意思），分属不同时刻：出包前、暂停修复时、新 manifest 首次出包、P1 简报、术语表 |
| stall event 的定义 | `retro/SKILL.md` 第 131–134 行；`retro.py` `qualifies()`（代码执行）；`docs/contexts/night/CONTEXT.md` 第 402–403 行 | 真重复（文本、代码、术语表三份） |
| `propose` 的 `evidence` 必须是 retro problem 的来源之一 | `night.md` 第 155 行 "the retro counts the proposal only when that string is one of its problem's sources"；`retro/SKILL.md` 第 10 步 | 真重复，读者不同（写 decisions 的主 agent / 判门槛的主 agent，二者是同一会话的同一个 orchestrator 在不同时刻） |
| 七个 retro 类别 | `retro/SKILL.md` 第 8 步与第 12 步 JSON 模板；`retro.py` `CATEGORIES`；`night/CONTEXT.md` 第 386–388 行；来源 `mmw-v2/upstream/skills/in-progress/retro/SKILL.md` | 真重复（模板与代码是合同两端）；上游那份是出处，不装 |
| Prevention destinations 八值 | `retro/SKILL.md` `## Prevention destinations` 与 JSON 模板；`retro.py` `DESTINATIONS`；`night/CONTEXT.md` 第 415–417 行 | 真重复（同上） |
| advisor brief 五部分 | `consulting.md` `## The brief`；`dispatch.sh` 第 2057 行拒绝文字 "write the five parts consulting.md lists"（指针，不复述）；`docs/contexts/ticket-run/CONTEXT.md` `brief` 条目（复述五部分） | `consulting.md` 与术语表为真重复；`dispatch.sh` 只是指针 |
| 不许引导 advisor | `consulting.md` `## The question stays open` 与 `advising.md` `## The brief tells you what the caller knows` | 同一禁令的两半，ADR 0014 有意两份（每侧只读自己那份） |
| advisor 不写文件 | `advising.md` `## What you never do`；ADR 0014 `## Consequences` 第一条；ADR 0015 `## Consequences` 第一条；`ticket-run/CONTEXT.md` "It implements nothing." | 真重复（技能是执行处，ADR 是理由，术语表是定义） |
| "只跑不改变临时目录之外任何东西的命令" | `manage-agents-md/SKILL.md` 提示模板（第 62 行）与 `### Checks`（第 311 行） | 技能内真重复，读者不同（survey subagent / 主 agent） |
| 子目录那句话 | `manage-agents-md/SKILL.md` 第 197 行（模板）；`check.sh` 第 64 行按英文词 grep；`mmw-v2/tests/manage-agents-md/test_check.sh` 第 11 行；根 `AGENTS.md` 第 81 行 | 模板、检查、测试是一个合同；根 `AGENTS.md` 是产品实例 |
| `CLAUDE.md` 只含 `@AGENTS.md` 与其他 `@` 行 | `manage-agents-md/SKILL.md` `### Steps` 第 4–5 步；`check.sh` 检查 2；`docs/contexts/toolbox/CONTEXT.md` 第 87 行；`mmw-v2/merge-notes/setup-matt-pocock-skills.md` 第 27 行（为对齐它改了上游） | 真重复；merge-note 记录的是对齐决定 |
| 标题固定英文，因为别的技能按标题加行 | `manage-agents-md` `### Language`；`code-checkers` 第 8 步（按 `## Commands`、`## Key Conventions` 加）；`setup-matt-pocock-skills/SKILL.md` 第 26、75、82 行（按 `## External References` 加） | 不是重复，是生产方与消费方的同一约定两端 |
| 代码规则归 `CODING_STANDARDS.md`、测试规则归 `TESTING.md` | `manage-agents-md` `### Code and test rules` 与 `rewrite.md` 第 4 步；根 `AGENTS.md` External References；`code-review/references/standards-reviewer.md`；`to-spec`、`to-tickets` 的 `SKILL.md`；`SKILL-SET-RULES.md`；`toolbox/CONTEXT.md`（`grep -l` 命中，已核实文件；未逐一核对句子是否同义） | 至少部分真重复；需逐句再核（未确定） |
| checker command 就是 `.mmw/target.json` 的 `checks` | `code-checkers` 第 6 步；`toolbox/CONTEXT.md` 第 328–330 行；`ui-acceptance/references/product-answers.md` 第 77–78 行（`checks` 的定义） | 真重复（两端 + 术语表） |
| `--no-verify` 提交只剩 `checks` 这一道门 | `code-checkers` 第 6 步；`dispatch.sh` 第 1427 行真的用 `--no-verify` 提交半成品 | 前者是规则，后者是它所依据的事实，不算重复 |
| 安装目录被本机所有仓库共用 | `diagram-design/SKILL.md` §0 第 27 行（本仓加：品牌不要写进安装副本）；根 `AGENTS.md` Gotchas 第 68 行（凭据不要写进技能 `scripts/`） | 同一事实，不同后果；不是同一条规则 |
| `repo-root` symlink 的理由（"`../../` 会算到 host 目录去"） | `merge-notes/diagram-design.md` `### repo-root（symlink）`；`toolbox/CONTEXT.md` 第 429 行 | 真重复，且两处理由都不准确（见 §9 缺陷 7） |
| 超预算「先嵌套、按层计、独立问题才拆」 | `diagram-design/SKILL.md` §3 Rules of thumb、§7 末两段；`output-spec.md` §3 条件 3、Degrade ladder 第 6 步 | 本仓改动在四处写了同一规则；另有三处仍写"拆"（§9 缺陷 4） |
| release engine 的状态、预算、熔断等定义 | `docs/contexts/release/CONTEXT.md` 各条目；`driving.md` 状态表；`release-flow.sh` 头注释与代码 | 术语表按设计复述；`CONTEXT.md` 的 `diagnoser` 条目引 `references/key.md` 为 Home，但 `key.md` 没写 `diagnose` 字段（§9 缺陷 5） |
| smoke module 与 `smoke.modules` | `new-product.md` `### The smoke module`；`key.md` `python_backend` 与 "What each field prevents"；`builders/nuitka.py` 文档串；`release/CONTEXT.md` `smoke module`、`smoke` | 真重复（新产品时 / 写字段时 / 维护者 / 术语表） |
| `include_packages` 只带代码不带数据 | `key.md` "What each field prevents" 第一条；`builders/nuitka.py` 文档串 "Nuitka 的坑" 第一条 | 真重复（agent 读 / 维护者读） |
| 用宿主自带通用 subagent | `manage-agents-md` `### Dispatch`；`code-review` 的 `references/session.md`（`merge-notes/code-review.md` 第 171 行说明它采用了 `manage-agents-md` 的写法）；ADR 0015 | 同一做法，两个技能各写一次 |

只是同词、意义不同（不算重复）：
- round：release loop 的 `.round` 计数与 `fix round`（`release/CONTEXT.md` 第 98–100 行明确区分）vs ticket 的修复 round。
- finding：release finding（带 tier）vs code-review finding vs 技能复审 finding（`release/CONTEXT.md` `_Avoid_` 行已区分）。
- hook：release 的 build hook vs `code-checkers` 的 git hook vs 宿主 hook（`release/CONTEXT.md` `build hook` 的 `_Avoid_` 行已区分）。
- check / checks：retro 的 `check` 去处与 `check:` 证据 vs `.mmw/target.json` 的 `checks` vs `code-checkers` 的 checker。
- category：retro category vs code-review 的 review category（`night/CONTEXT.md` 第 387 行、`ticket-run/CONTEXT.md` 第 255 行已区分）。
- brief：advisor brief vs P1 fix brief（`release/CONTEXT.md` 第 83 行称二者同一族，意义相近但产生方式不同）。
- baseline：`code-checkers` 的 checker baseline vs 其他技能里的 baseline。
- 熔断：引擎按指纹计数（`RF_MAX_SAME_FINGERPRINT=3`）vs `driving.md` "Same root cause twice … stop"（agent 按真实原因判断）；复审判为互补，本次读代码与文本后同意（已核实两处文字）。

---

## 5. 上游差异

### 5.1 diagram-design（唯一在上游 subtree 里的技能）

- 上游基准：`git log --grep "Squashed 'mmw-v2/upstream-diagram-design/'"` 最近一次为 `8a85636a`（2026-09-18，"changes from 4faae669..9874ad73"）。
- 整个 subtree 对上游树的差异只有 5 个文件（`git diff --stat 8a85636a: HEAD:mmw-v2/upstream-diagram-design`，已核实）：`skills/diagram-design/SKILL.md`（+31/−22 行，现 585 行 vs 上游 578 行）、`references/output-spec.md`（2 行改写，行数不变）、`repo-root` symlink（新增）、`scripts/verify-geometry.py`（+71 行量级）、`scripts/test-verify-geometry.py`（+54 行）。其余 55 份 reference、`assets/`、`commands/`、`prompts/`、技能内 `scripts/` 全部原样。merge-note 的 "其余 55 个 reference 未改" 与此一致（56 份 reference 中改了 1 份，已核实）。
- 每处改动与 merge-note 行的对应（逐条对过 diff 与 `mmw-v2/merge-notes/diagram-design.md` `### SKILL.md` 表，全部有对应行）：

| 改动 | 内容类型 | merge-note 行 | 改变能力本身，还是写入 MMW 流程/立场 |
| --- | --- | --- | --- |
| §0 标题、粗体首句、"Name the one you used beside the deliverable…" | 目的与立场 | §0 标题行 | 立场（交付物旁写明配色） |
| §0 无 marker 时"draw with them"，不停下问品牌，一行说明四种改法 | 立场 + 规则+理由 | §0 markerless 行 | 写入 MMW 立场（图多数不出门）；改变了默认行为（上游是 pause） |
| §0 送客户先问，结果存 profile、用 marker 绑定，不写进安装副本 | 规则+理由 | §0 client 行 | 写入 MMW 安装拓扑（安装副本被所有仓库共用） |
| §0 末段半句 "all-default tokens … take the default path above" | 分派 | §0 末段行 | 跟随上一条 |
| §1 末句（先找能嵌套的图型） | 规则 | §1 行 | 写入 MMW 立场（全局性优先） |
| §3 Rules of thumb 第三条、§7 复杂度预算末段两段、§6 rule 3 括号改"see §7"、`output-spec.md` §3 条件 3 与第 6 步 | 规则+理由 | §3、§7、§6 rule 3、`output-spec.md` 两行 | 写入 MMW 立场（"读一次就看懂一个系统"）；改变 agent 在超预算时的动作 |
| §6 "When one page carries several diagrams, prefix each marker `id`…" | 做法 | §6 Arrow markers 行 | 服务 MMW 调用方（`improve-codebase-architecture` 每卡两张图）；改变输出 |
| §6 rule 6、§9 两条检查：`<repo-root>` → `repo-root/`，"run from this skill's own directory"，去掉"From a repository checkout"前提，motion 条加 `lint-skin.py` | 命令与接口 | §6 rule 6、§9 两条行 | 能力（让校验在安装后的技能里可运行）；配合 `repo-root` symlink |
| §9 新增 "Opened the rendered file and looked at every diagram in it?" | 做法 | §9 Technical 行 | 立场/做法（看渲染结果） |
| `repo-root -> ../..` | 命令与接口（路径） | `### repo-root（symlink）` | 能力（安装后脚本可达） |
| `verify-geometry.py` 按顶层 `<svg>` 分坐标系；16px CJK 标签底板 | 能力（校验器） | `### scripts/verify-geometry.py` 两行 | 改变能力本身：一页多图不再误报；中文标签被检查 |
| 测试 8 条 | — | 同上两行 | 锁住上面两项 |

- 判断「是否原样使用」：作为外来能力技能，图型、原语、设计系统、导入导出、56 份 reference 与自检脚本原样使用；本仓改动集中在三类：(1) 超预算策略（拆图 → 先嵌套），(2) 配色门槛默认值与品牌存放位置，(3) 安装后可运行性与多图/中文页面的校验器修正。第 (1)(2) 类是把 MMW 的立场写进上游正文；第 (3) 类改变能力本身。
- 本仓改动留下的不一致：见 §9 缺陷 4。上游 ADR 0004 的 `SKILL.md` 40,000 字节上限在本仓版本被超出（2026-09-28 复审测得 40,404 字节，未核实，本次未测字节数）。

### 5.2 其余五个技能

都在 `mmw-v2/skills/`，是本仓自有，没有 merge-note。与上游的关系：
- retro：七个类别与"改进 agent 的环境"取自上游 `mmw-v2/upstream/skills/in-progress/retro/SKILL.md`（44 行，`disable-model-invocation: true`，已核实）；`mmw-v2/merge-notes/README.md` 第 38 行 "`mmw-v2/skills/retro/` 是本仓自己的技能 … 上游的 `in-progress/retro` 是另一个技能，不合进来"（已核实）。上游版本是"对一次会话复盘、向用户列候选"，本仓版本是"对一夜复盘、脚本复验证据、开 issue、写 Memory、贴事件"，能力不同。
- code-checkers：上游 `mmw-v2/upstream/skills/misc/setup-pre-commit/SKILL.md`（Husky + lint-staged + Prettier）做相近的事，不在 `skills.txt` 里，未安装（已核实）；本仓选 prek + 仓库依赖清单。
- manage-agents-md：`<important if>` 块的名字，词汇复核 `DECISIONS.md` T9 记为 "the skill's and HumanLayer's own name"；`T4-toolbox.json` 记固定章节格式为 MMW 原创。两条线索互相不矛盾但都未在原始出处核实（未确定）。
- advisor、exe-release：没有上游对应（`T4-toolbox.json` 记 `original_to_mmw: true`；exe-release 的外部依赖是 Nuitka、electron-builder/NSIS，advisor 依赖 runner，未核实 T4 的外部出处条目）。

---

## 6. 价值证据

| 部件或段落 | 防的是什么失败 | 实地证据 | 核实 |
| --- | --- | --- | --- |
| retro 整体（`finalize` 复验 + 门槛 + 开 issue） | 夜里的问题只在一次会话里被看见、下一夜重犯；一次偶发被当作模式 | 本仓 Space 有 7 条 Retro Memory（spec 415、424、444、445、446、447、555）；spec-555 的 problem "The rename of tree.py to issue_tree.py (#508) left a caller on the old name …" 产生 proposal #587，落地为 `812a2141` "every suite first checks that the module files scripts load by path exist (#587)"，另有 `8c1a29f0` "fix(retro): load verify-ticket's issue_tree module"；spec-444 产生 proposal #478 | 已核实（`nmem memories list/show`、`git log`） |
| retro 第 3 步接受跨仓库 commit URL | 别的仓库已落地的 proposal 被记成"没找到证据" | 复审：agentflow retro spec-913 把 MMW `42b3e278` 修好的 #441 记为没找到证据；现 `check_analysis()` 已接受 `https://github.com/<o>/<n>/commit/<sha>` | 代码已核实；agentflow 那条记录未核实 |
| retro `## Gather` 2 "A missing source narrows the analysis" | 把"没查到"当"没发生" | 复审：#415、#424 两次 retro `Evidence: partial` | 未核实 |
| retro 引言 "Look for what in the environment…" | 原因写成"agent 没仔细看"，prevention 改变不了下一夜 | 无直接事件证据；来源为上游原文 | 无证据（设计理由） |
| retro "Three readers" | proposal 写成只有当晚上下文才懂的笔记 | 无直接事件证据 | 无证据 |
| advisor `## The question stays open` / advising 的对应段 | 发起方替 advisor 划范围，第二意见变成自己的意见 | ADR 0014 `## 要修的是什么`："派 advisor 的 main agent 经常替它划定调查范围" | ADR 原文已核实；原始事件未核实 |
| advisor `## The answer` 与读法 A | 更强模型的话被当裁决；或只交出会话 id 就结束 | 用户 2026-09-28 裁定（`汇总.md` 第 59 行）；复审未找到任何一次 `dispatch.sh advise` 的真实使用记录 | 裁定已核实；使用记录"无证据" |
| advisor 不写文件（文字规则） | advisor 写坏发起方正在改的文件 | ADR 0014/0015：没有只读权限档可用，只能靠文字 | 已核实 ADR 文字；无违规事件证据 |
| exe-release §1 干净工作树 | 用户测的包和眼前代码不一致 | 设计理由（`git archive HEAD`）；`init` 并未检查（§9 缺陷 1） | 理由已核实；检查不存在 |
| exe-release §2 "The paths are evidence, not the rule" | 共享包改了而产品不出包，客户拿到旧代码 | 复审：agentflow parrot 的 `include_packages` 含 `shared`（`src/shared/`） | 未核实 |
| exe-release §4 same-commit | 一组包来自不同提交 | `~/agentflow/.release/delivered/` 里并存 `douyin-master-resolve.json`、`duck.json`、`hedgehog.json`、`parrot.json` | 已核实（`ls`） |
| `driving.md` `## An interrupted build` | 新开一轮删掉构建机正在读的源码树 | `474afb36` "断线能接回正在跑的构建"；`release-flow.sh` 注释 "真发生过一次，代价是一轮四十分钟的编译要靠人手工收尾" | 已核实提交与注释 |
| `key.md` 各字段"防什么"、模板与脚本的防线 | 每条对应一次真实出包失败 | `git log -- mmw-v2/skills/exe-release` 72 个提交，其中大量 `fix(exe-release)` 标题描述具体失败（如 `4cf02e09` 钩子 UTF-8、`585e9719` 源码泄漏扫描、`0a140036` 编译中间产物随包发出）；`~/douyin-master-resolve/.release/release-artifacts/` 有 `a2-build`、`a4-build` findings | 已核实提交标题与目录存在；findings 内容未读 |
| exe-release 自动修复后端（已删） | — | 三个产品仓库全部历史无引擎格式提交；用户 2026-09-28 决定删除 | 决定已核实（`汇总.md`、`831de890`）；"无提交"未核实 |
| code-checkers pyrefly worktree 段 | 票 worktree 里 pyrefly 扫不到文件，只能 `--no-verify` | agentflow #712 "pyrefly 在 .claude/worktrees/ 下的工作树里扫不到任何文件，提交只能 --no-verify"（CLOSED） | 已核实 |
| code-checkers 第 5 步"每个目录都探" | 检查器覆盖不到的目录没人查 | agentflow #717 ".mmw/ is outside pyrefly, lint.sh Python paths, and oxlint"（CLOSED） | 已核实 |
| code-checkers 第 4 步"只看改动"与反向探针 | checker 对未改文件报存量挡住提交 | agentflow #871 "lint.sh 对未改动的 TypeScript 与 shell 文件做全仓检查，阻断 #854"（CLOSED） | 已核实 |
| code-checkers 第 6 步"按退出码判" | oxlint 不打印汇总行 | 复审引 Nowledge Mem `8c991c17` | 未核实 |
| manage-agents-md 嵌套文件门槛 | 嵌套文件随代码漂移无人更新 | `~/agentflow` `812e39309` "删掉全部嵌套 AGENTS.override.md 与 CLAUDE.md 桥"；`~/xiaohuangya` `190522b` "根文档并成一份 AGENTS.md，删掉 75 份嵌套治理文档" | 已核实 |
| manage-agents-md 标题固定英文 | 别的技能按英文标题加行，翻译后出现两节 | `setup-matt-pocock-skills/SKILL.md` 第 82 行确实按 `## External References` 加行 | 机制已核实；实际发生过两节"无证据" |
| manage-agents-md 完整 survey 流程 | 写出凭猜测的行 | 复审：唯一一次真实加载（2026-09-28 `~/ERP`）agent 没有跑完整流程，只用了格式与 `check.sh` | 未核实 |
| manage-agents-md `check.sh` | 行数超限、路径失效、CLAUDE.md 桥缺失 | 有测试 `test_check.sh`；本仓根 `AGENTS.md` 按此格式存在 | 测试存在已核实；运行未做 |
| diagram-design `verify-geometry.py` 本仓改动 | 一页多图误报重叠；中文标签不被检查 | merge-note 记测试 "第一条在上游版本上失败"；复审引 `b898a009` 冷跑 | merge-note 已核实；冷跑未核实 |
| diagram-design §0 品牌不写安装副本 | 客户品牌串到本机所有仓库的图 | 复审："从没触发过…但正常使用能走到" | 无证据（可达性推断） |
| diagram-design "先嵌套" | 读者要在脑中拼两张画布 | 无事件证据（用户立场，merge-note `## 总原则`） | 无证据 |

---

## 7. 约束

| 约束来源 | 内容 | 约束谁 |
| --- | --- | --- |
| `docs/adr/0014-advisor-has-one-door.md` | advisor 只是一个会话，入口只有技能 description；技能分 `consulting.md`/`advising.md` 两扇门；只读只能靠文字；advisor 跑在发起方的 workspace 里以看见未提交改动，不另开 worktree；否决了"写进用户级提示词"与"脚本生成 initialPrompt" | advisor 的形态与文件切分 |
| `docs/adr/0015-no-custom-subagents.md` | 不交付 subagent；需要派活的技能用宿主自带通用 subagent；同时修正 0014 的一句 | advisor（会话而非 subagent）；manage-agents-md `### Dispatch` |
| `docs/adr/0024-models-json-and-runner-extension-boundary.md` 第 12 行 | `models.json` 每个角色一行，含 `advisor` | advisor 的模型配置 |
| `docs/adr/0025-project-branch-and-finish.md` 第 13 行 | "`spec.retroed.result=recorded` 证明复盘收据已经写成，用户验收才授权 `finish`" | retro 是 `finish` 的前置门 |
| `docs/adr/0031-worker-start-memory-is-a-searched-index.md` | worker 开工 Memory 用短查询搜出、只放索引行；记录了 `memories search` 在查询含陌生具体标识时整批返回空（`unsupported_specific_anchor`） | 不直接约束本单元；与 retro 的关系是：night.md 收尾 pass 对 `mmw-experience` 记录做 `retain/propose/deprecate/supersede`，`propose` 是给 retro 的线索。`retro.py search` 用 `"<category> <cause>"` 做查询，cause 常含具体标识，可能碰到 0031 记的同一行为（推断，未验证） |
| `docs/adr/0003-no-plugin-packaging.md`、`0006`（技能装进中立目录，经 0015 修正） | 不走插件包装，技能用 symlink 装 | diagram-design 只作为技能目录装入，上游的 `.claude-plugin` 等不用；这是 `repo-root` symlink 存在的前提 |
| `SKILL-SET-RULES.md` 事实 1 | 技能要交代工作为何存在、谁依赖、做浅的代价，规则旁给理由 | retro "Three readers"、exe-release、code-checkers 等在 2026-09-28 补回的理由句 |
| 事实 2 与 `### Scripts and judgement` | 脚本承担确定性工作，文字承担判断；"Text that assigns the script's writes to the agent is a finding" | retro 的 `finalize` 自取 gather 值；exe-release 把派发、轮次、same-commit、close 检查收进 `release-flow.sh`（`831de890`） |
| 事实 5 与 `### Load and disclosure` | 每次运行都读的 reference 是 fragment，应内联，除非 `SKILL.md` 因此带上别的任务跳过的材料 | 可对照：`exe-release/references/driving.md` 每个产品每次都读；`code-checkers/references/git-hooks.md` 每次都读（第 7 步不可跳）；`advisor` 两个 reference 各在一个分支读（符合） |
| 事实 6–7 | 一个方法一个家；第二份是 finding | §4 的真重复都在此约束下；advisor 的两份禁令以"rule sits in the text of the agent that must follow it"（`### Load and disclosure`）为据保留 |
| `### Descriptions` | "A branch naming the role an agent was started as ('when you were started as the advisor') is a trigger." | advisor 的 description 写法 |
| `### Vocabulary` "Skill text is English." | 技能文本用英文 | `exe-release/references/new-product.md` 第 35–36 行代码例里的中文注释与此冲突（§9 缺陷 6） |
| `### Vocabulary` 术语表条目须由其 `_Home_` 文件支撑 | | `release/CONTEXT.md` `diagnoser` 的 Home 含 `references/key.md`，但 `key.md` 无 `diagnose` 字段（§9 缺陷 5） |
| `### Upstream skills` | 上游技能只在改变 agent 行为处改动，每处改动对应 merge-note 一行；merge-note 各行须与现文一致 | diagram-design（全部改动有对应行，已核实）；merge-note 称 `output-spec.md` §3 条件 3 已"与 §7、Degrade ladder 第 6 步一致"，但同文件其余两处与 `SKILL.md` §11 仍写"split"（§9 缺陷 4） |
| `mmw-v2/merge-notes/README.md` 第 38 行 | retro 是本仓自有，上游 `in-progress/retro` 不合入 | retro |
| `mmw-v2/merge-notes/setup-matt-pocock-skills.md` 第 27–28 行 | 上游 setup 技能改成按 `manage-agents-md` 的根文件形态写 | manage-agents-md 的格式成为其他技能的依赖 |
| 用户决定 2026-09-28（`docs/reviews/2026-09-28-lightweight/汇总.md` 第 56–59 行，已核实） | 删除 exe-release 自动修复后端与受保护路径机制；manage-agents-md 三处格式改动（嵌套门槛、英文标题、根文件可加一节与覆盖清单式提问），取代 2026-08-23 spec；advisor 读法 A | exe-release、manage-agents-md、advisor 的现形态 |
| 用户决定 2026-09-23（`docs/reviews/2026-09-23-skill-set/汇总.md` 第 17、118 行） | "advisor 的回答怎么读、发布修复路径"答复后不修 | 已被 2026-09-28 读法 A 部分取代 |
| `mmw-v2/downstream-notes/release-self-heal-removed.md` | 消费仓库须删 manifest 四个字段 | exe-release 与 agentflow、xiaohuangya 的兼容 |
| 根 `AGENTS.md` Gotchas 第 68 行 | 技能目录是本机所有仓库共用的一条 symlink | diagram-design §0 品牌存放；exe-release 的 `${RELEASE_PLUGIN_DIR}` |
| `docs/research/mmw-structure/2026-09-06-handoff.md` 第 110 行 | 当时 advisor 的判断："不把 `code-checkers` / `manage-agents-md` / `target-setup` 合并成一个「配仓库」技能。三者由不同的人在不同时刻触发，合并只是把路由再散一次。" | 是记录在讨论文档里的结论，不是 ADR 或用户明确裁定（未确定其约束力） |

---

## 8. 天然整体

- **retro 的 `SKILL.md` 与 `retro.py` 是一份合同的两端。** 分析 JSON 的形状（第 12 步）、证据形式（第 3、4 步）、同发生计数（第 5 步）、proposal 门槛与 stall event（第 10 步）、`prompt_change` 字段（第 11 步）逐条由 `check_analysis()`、`evidence_source()`、`qualifies()`、`validate_prompt()` 执行（已核实）。文字告诉 agent 脚本将如何裁决，脚本拒绝时指回文字。拆开任何一半，另一半就失去对照。`## Analyze` 第 3、6、7、8 步之间没有先后依赖，但 `gather → search → finalize` 三个命令的顺序是硬依赖。
- **advisor 的两份 reference 是同一禁令的两半，各自必须自足。** 发起方和 advisor 各只读一份（ADR 0014），所以不能合并成一份，也不能把禁令只放一侧；`SKILL.md` 只是 13 行的分流表。整个技能 1096 词。
- **exe-release 的 `driving.md` 状态表与 `release-flow.sh where` 是一个接口。** 状态表列的每一行就是 `cmd_where` 能打印的每种输出；`f1752183` 就是因为引擎打印了一个状态表里已删掉的 `RETRY-STAGE` 而修的（已核实提交说明）。`key.md` 与 `release_contracts.py` 同理：`key.md` 自称 "`scripts/release_contracts.py` is the authority on field names and shapes. This file is why each part exists"。`new-product.md` 的三文件链表（manifest `output_dir` / `electron-builder.yml` `extraResources` / Electron 主进程路径）只有三行一起才有意义。`SKILL.md` 第 2–4 步（产品清单 → 每产品一个 loop → same-commit 读 `close` 写的交付记录）是一条链。
- **code-checkers 第 4–7 步围绕两个目标连成一体**："day one 就有用"（存量不挡、只看改动、反向探针）与"不会静默失效"（三种静默失效、每目录探针、真实提交探针）。第 5 步的探针要验证的正是第 4、6、7 步建的东西。语言 reference 是天然分支；`git-hooks.md` 每次都读。
- **manage-agents-md 的 `survey-list.md` 流水线是一体的**：Survey 产生条目，Ask 追加条目，Write 只从条目写（"Each line you write comes from one entry"），`destinations.md` 在 rewrite 分支把旧行转成条目。根模板、`### Language`（英文标题、子目录那句英文）与 `check.sh`（按英文词 grep、行数上限）互相绑定；标题英文又被 `code-checkers`、`setup-matt-pocock-skills` 依赖。
- **diagram-design 的技能目录、56 份 reference、subtree 根的 `scripts/` 与 `repo-root` symlink 是一个整体。** merge-note 开头写明整个仓库都拉进来，因为 `verify-geometry.py`、`verify-motion.py` 住在仓库根，且按 `<repository root>/skills/diagram-design/assets/` 找资源；只取 `skills/` 会让校验永久缺失。

---

## 9. 本次核实发现的现状问题（事实，不含修法）

1. **exe-release `SKILL.md` `## 1. Preconditions` 称 "`bash scripts/release-flow.sh init` refuses to start on a dirty tree"，但 `cmd_init` 没有任何工作树检查。** 已核实：`cmd_init`（第 400–445 行）只做 manifest 校验、已有 loop 检查、清 artifacts、写状态；全脚本唯一的 `git diff --quiet HEAD` 在 `cmd_dispatch_p2`（第 280 行，P2 自动提交前）。`mmw-v2/tests/exe-release/` 里唯一的 dirty 场景是 `p2-preflight-dirty`。该句由 `831de890` 加入；2026-09-28 复审 D6 定的是"`init` 在工作区不干净时拒绝"，提交说明只写了 "P2 (derive) keeps a plain preflight dirty-tree check"。
2. **`release-flow.sh` 第 1160–1162 行注释说 `fix_dispatch.py` "打印它的路径、非零退出"，实际 `fix_dispatch.py` `main()` 成功时 `return 0`，`cmd_dispatch_p1` 也按退出 0 走成功分支。** 已核实。
3. **`release-flow.sh` 第 133–135 行注释说预算按"修复轮次"记账，但只有 P2 提交会 `.budget.fix_rounds += 1`（`cmd_dispatch_p2`），P1 与 `transient:` 重跑不计。** 已核实（`DECISIONS.md` "Found on the way" 第 1 条先记录，本次读代码确认）。`round next` 计数另走 `.round`。
4. **diagram-design 本仓"先嵌套"改动在三处未跟上**：`references/output-spec.md` 第 137 行 `faithful` 条件 2 "you're over the real ceiling — split."、第 219 行清单 "`faithful` above 9 nodes → zoned, and split above 24?"、`SKILL.md` 第 556 行 §11 "zoned above 9 nodes, split above 24"。同文件第 138 行（条件 3）已改为先嵌套，merge-note 称其"与 §7、Degrade ladder 第 6 步一致"。已核实（grep）。
5. **`key.md` 没有写 `build_machine`、`diagnose`、`diagnose_branches`、`diagnose_core_exe_glob` 四个字段**，它们在 `release_contracts.py` 里（`BuildMachine` 第 280 行、`diagnose_branches` 第 449 行、`diagnose` 第 456 行）。`release/CONTEXT.md` 的 `build machine` 条目提到 `build_machine` 的 `setup`/`teardown`，`diagnoser` 条目说 manifest 的 `diagnose` 字段可替换通用诊断，并把 `references/key.md` 列为 Home。已核实（grep 无命中）。复审称四份真实 manifest 都用了 `build_machine.setup`（未核实）。
6. **`exe-release/references/new-product.md` 第 35–36 行代码例里有中文注释**（"函数体里 lazy import 的原生依赖…"），与 `SKILL-SET-RULES.md` `### Vocabulary` "Skill text is English." 不一致。已核实。
7. **`repo-root` 的理由写得不准。** `merge-notes/diagram-design.md` 与 `toolbox/CONTEXT.md` 第 429 行都说 `../../` 会解析到宿主目录；实测 `ls ~/.claude/skills/diagram-design/../../scripts/verify-geometry.py` 能找到文件（内核按物理路径解析）。symlink 仍然让写法无歧义，但理由只对 shell 的逻辑路径（`cd ../..`）成立。已核实。
8. **消费仓库的 manifest 仍带着已删字段**（§3.3）：agentflow `hedgehog`、`parrot` 与 xiaohuangya `duck` 各有 4 处。已核实（仅当前检出分支）；这些仓库下次出包会被 `validate-manifest` 拒绝是推断。

---

## 10. 线索材料采用情况

| 线索结论 | 来源 | 状态 |
| --- | --- | --- |
| retro 2026-09-28 定稿的 I1–I7、D1、D10、D12 已落地 | `docs/reviews/2026-09-28-lightweight/retro.md` | 已核实（现文与 `retro.py` 对应处都在） |
| retro 7 个真实 proposal 都没有 `prompt_change` | 同上 C2 | 未核实 |
| advisor I1–I6、D1–D3 与读法 A 已落地 | `advisor.md` | 已核实（现文）；D4（删 `dispatch.sh` 死代码）未核实 |
| exe-release D0、D2、D4、D5 已落地；D6（`init` 拒绝脏树）未落地 | `exe-release.md` | 已核实（见 §9 缺陷 1） |
| code-checkers I1–I9、D1–D4 已落地 | `code-checkers.md` | 已核实（现文含 worktree 段、三种静默失效、"several hundred rules"、`MMW_BASE_REF`） |
| manage-agents-md I1–I5、D13 与三处格式改动已落地 | `manage-agents-md.md` | 已核实（现文开头、`### Language`、嵌套门槛句、`### What NOT to Add` 位于 `## Write` 下） |
| diagram-design I1–I5、F1、F2 已落地 | `diagram-design.md` | 已核实（diff）；复审 A2 关于 `faithful` 24 的部分未完全落地（§9 缺陷 4） |
| retro 的一次实际故障：`tree.py` 改名漏改 `retro.py` | `I5-mmw-field-evidence.json` | 已核实（spec-555 Retro Memory、`8c1a29f0`、`812a2141`） |
| 不合并 code-checkers/manage-agents-md/target-setup | `2026-09-06-handoff.md` | 原文已核实；其性质是讨论结论 |
| exe-release、advisor 为 MMW 原创；diagram-design 为 subtree 原样引入 | `T4-toolbox.json` | diagram-design 部分已核实（diff 只有 5 个文件）；其余未核实 |
| exe-release `M3` "不是 ticket 必经阶段" | `M3-mmw-ticket.md` | 已核实（无技能调用 exe-release） |

## 11. 未确定

- manage-agents-md 的 `### What NOT to Add` 清单与 `<important if>` 写法的外部出处（HumanLayer？）没有找到原始出处；首个提交 `2cb78305` 的说明未写来源。
- `CODING_STANDARDS.md`/`TESTING.md` 归属规则在 `to-spec`、`to-tickets`、`code-review/references/standards-reviewer.md`、`SKILL-SET-RULES.md` 里的具体句子是否与 `manage-agents-md` `### Code and test rules` 同义，只做了文件级 grep，未逐句比对。
- `release-flow.sh` 的远端构建主体（断线重连、轮询、日志回传）、`nuitka_electron.ps1.tmpl` 第 30 行之后、`release_script_assembler.py` 主体、`diagnose_core.py` 规则表、`verify_key.py` 检查项：只读了入口与注释，结论不覆盖这些实现。
- `retro.py search` 是否会因 cause 含具体标识而返回空（ADR 0031 记录的 `unsupported_specific_anchor` 行为）：推断，未运行。
- 是否有任何一次 `dispatch.sh advise` 的真实使用：复审称未找到；本次未另查。
- diagram-design `SKILL.md` 第 140–395 行只按标题读过，未逐行读；56 份 reference 除 `output-spec.md` 的 diff 外未读。
- diagram-design 本仓版本 `SKILL.md` 的字节数与上游 ADR 0004 上限的关系：本次未测。
- 消费仓库 manifest 在其他分支上的状态；这些仓库下次出包是否真的被拒：未运行。
