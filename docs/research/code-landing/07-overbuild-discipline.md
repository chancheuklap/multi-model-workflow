# 过度构建纪律：把 ponytail 写进 implement 的可行范围

本文回答一个问题：`00-synthesis.md` 第 22 行「过度构建控制」这一条（取自 ponytail）到底采不采纳、采哪些句子、放在哪、怎么注入、怎么验证有效。参考快照在 `docs/research/code-landing-refs/ponytail/`，下文的 ponytail 路径省略这个前缀；我们自己的技能路径写全。

## 1. 一句话结论

ponytail 的规则文本只有两处有 baseline 对照的行为证据（root-cause 的「grep every caller」句在 Sonnet/Opus 上，rung 4「Native platform feature covers it?」在 Haiku 上），「input validation at trust boundaries」例外只在与七字裸提示 `yagni-oneliner` 的对照里有差异，其余各条只有聚合数字或没有证据；它的常驻注入靠插件 hook，而我们按 `docs/adr/0003-no-plugin-packaging.md` 不做插件、按 `AGENTS.md` 第 21 行只在调用时读技能正文，所以唯一能用的落点是 `mmw-v2/upstream/skills/engineering/implement/SKILL.md` 第 10 行读入段之后、第 14 行 `Use /tdd` 之前，插入不超过十行、对象换成票里的东西的操作性指令；采纳与否要按本仓记忆「文本忠实≠效果达成」用探针跑对比，不能只看文本。

## 2. ponytail 规则文本的完整清单

### 2.1 有几份、哪份是源

ponytail 同一套规则有三种形态：

| 形态 | 文件 | 行数 | 谁读 |
| --- | --- | --- | --- |
| 完整版（runtime source of truth） | `skills/ponytail/SKILL.md` | 120 行，其中第 1–18 行是 frontmatter | Codex、Grok、OpenCode、pi、Hermes、Qoder、Swival 等列出 `skills/` 的宿主（`docs/agent-portability.md` 第 12–16、25、31 行）；Claude Code 走插件清单（第 11 行），hook 读的也是这份（`hooks/ponytail-instructions.js` 第 9 行 `SKILL_PATH`） |
| 完整版的 OpenClaw 副本 | `.openclaw/skills/ponytail/SKILL.md` | 108 行 | OpenClaw。`diff` 显示与 `skills/ponytail/SKILL.md` 只有 frontmatter 不同（第 3–4 行 vs 第 3–16 行），正文逐字相同 |
| 精简版（compact） | `AGENTS.md` 32 行；`.agents/rules/ponytail.md`、`.windsurf/rules/ponytail.md`、`.clinerules/ponytail.md`、`.qoder/rules/ponytail.md`、`.github/copilot-instructions.md` 各 30 行；`.cursor/rules/ponytail.mdc`（前 5 行 frontmatter）、`.kiro/steering/ponytail.md`（前 4 行 frontmatter） | 走项目指令文件的宿主：Gemini CLI、Cursor、Windsurf、Cline、Antigravity、CodeWhale、Kiro、Zed 等（`docs/agent-portability.md` 第 17–24、26–30、32 行）；Qoder 同时有插件层和 `.qoder/rules/ponytail.md`（第 31 行） |
| hook 后备文本 | `hooks/ponytail-instructions.js` 第 43–74 行 `getFallbackInstructions` | 只在读不到 `skills/ponytail/SKILL.md` 时用（第 86–91 行） |

副本一致性由 `scripts/check-rule-copies.js` 保证：第 15–16 行取 `AGENTS.md` 去掉末尾括号句作为 canonical，第 19–36 行要求七份精简副本与它字节相等（`.cursor`、`.kiro` 两份先去掉 frontmatter，其余五份只 `trim()`，第 20–26 行）；第 44–58 行列九条 `INVARIANTS` 短语（`'in this codebase'`、`'naive heuristic'`、`'ONE runnable check'`、`'flimsier algorithm'`、四条安全例外、`'Lazy code without its check is unfinished'`），第 60–68 行要求它们在 `skills/ponytail/SKILL.md` 与 `AGENTS.md` 里都逐字出现。第 39–43 行注释承认完整版与精简版「cannot be byte-compared」，所以这是 canary 不是全等。`diff -q` 实测：`.agents/rules/ponytail.md` 与 windsurf、clinerules、copilot、qoder 四份无差异；`AGENTS.md` 只多第 32 行「(Yes, this file also applies to agents working on the ponytail repo itself. Especially to them.)」。

### 2.2 完整版逐段（`skills/ponytail/SKILL.md`）

| 段 | 行 | 内容 |
| --- | --- | --- |
| 开场 | 22–24 | "You are a lazy senior developer. Lazy means efficient, not careless… The best code is the code never written." |
| Persistence | 26–30 | "ACTIVE EVERY RESPONSE. No drift back to over-building. Still active if unsure. Off only: "stop ponytail" / "normal mode". Default: **full**. Switch: `/ponytail lite\|full\|ultra`." |
| The ladder | 32–42 | 七级："Stop at the first rung that holds" → 1 "Does this need to exist at all?"（YAGNI）2 "Already in this codebase?" 3 "Stdlib does it?" 4 "Native platform feature covers it?"（`<input type="date">` over a picker lib, CSS over JS, DB constraint over app code）5 "Already-installed dependency solves it?" 6 "Can it be one line?" 7 "Only then: the minimum code that works." |
| 梯子的前提 | 44–48 | "The ladder is a reflex, not a research project — but it runs *after* you understand the problem… Two rungs work → take the higher one and move on." |
| Bug fix | 50–54 | "**Bug fix = root cause, not symptom.** … Before you edit, grep every caller of the function you're about to touch. The lazy fix IS the root-cause fix: one guard in the shared function is a smaller diff than a guard in every caller… Fix it once, where all callers route through." |
| Rules | 56–64 | 七条：No unrequested abstractions（"no interface with one implementation, no factory for one product, no config for a value that never changes"）；No boilerplate, no scaffolding "for later"；Deletion over addition, Boring over clever；Fewest files possible, Shortest working diff wins（"The smallest change in the wrong place isn't lazy, it's a second bug"）；"Complex request? Ship the lazy version and question it in the same response, "Did X; Y covers it. Need full X? Say so." Never stall on an answer you can default."；Two stdlib options, same size → "Take the one that's correct on edge cases"；`ponytail:` 注释标记有已知天花板的简化，写明 ceiling 与 upgrade path |
| Output | 66–75 | "Code first. Then at most three short lines: what was skipped, when to add it… If the explanation is longer than the code, delete the explanation… Explanation the user explicitly asked for… is not debt" ；第 75 行 "Pattern: `[code] → skipped: [X], add when [Y].`" |
| Intensity | 77–88 | lite / full / ultra 三档表 + "Add a cache" 三档示例 |
| When NOT to be lazy | 90–112 | 第 92–95 行 "Never simplify away: input validation at trust boundaries, error handling that prevents data loss, security measures, accessibility basics, anything explicitly requested. User insists on the full version → build it, no re-arguing."；第 97–101 行 "Never lazy about understanding the problem… Read fully, then be lazy."；第 103–105 行硬件校准旋钮；第 107–112 行 "Lazy code without its check is unfinished. Non-trivial logic (a branch, a loop, a parser, a money/security path) leaves ONE runnable check behind… an `assert`-based `demo()`/`__main__` self-check or one small `test_*.py`. No frameworks, no fixtures, no per-function suites unless asked. Trivial one-liners need no test, YAGNI applies to tests too." |
| Boundaries | 114–120 | "Ponytail governs what you build, not how you talk… Level persists until changed or session end. The shortest path to done is the right path." |

### 2.3 精简版精简掉了什么（`AGENTS.md` 对照完整版）

整段删除：Persistence、Output（含 `skipped: [X], add when [Y]` 模式）、Intensity、Boundaries。

逐句改写（左为完整版，右为 `AGENTS.md`）：

| 完整版 | `AGENTS.md` | 丢了什么 |
| --- | --- | --- |
| rung 2 第 37 行 "Look before you write; re-implementing what's a few files over is the most common slop." | 第 8 行 "Reuse the helper, util, or pattern that's already here, don't re-write it." | 「先找再写」的动作提示 |
| rung 4 第 39 行含三个例子 | 第 10 行 "Does a native platform feature cover it? Use it." | 全部例子 |
| rung 5 第 40 行 "Never add a new one for what a few lines can do." | 第 11 行 + 第 22 行 "No new dependency if it can be avoided." | 「几行能做的」这个判据 |
| Rules 第 58 行三个具体禁例 | 第 21 行 "No abstractions that weren't explicitly requested." | 「一个实现的接口、一个产品的工厂、不变值的配置」 |
| Rules 第 62 行 "Ship the lazy version and question it in the same response… Never stall" | 第 26 行 "Question complex requests: "Do you actually need X, or does Y cover it?"" | **「先交懒版本再问、绝不停下等答案」这个动作**，精简版退回成只提问 |
| When NOT 第 97–101、103–105 行两段 | 第 30 行一句内并列 | 硬件段的解释；「Read fully, then be lazy」的推理 |
| Check 第 107–112 行 | 第 30 行括号内 "(an assert-based demo/self-check or one small test file; no frameworks, no fixtures)" | "no per-function suites unless asked"、"YAGNI applies to tests too" |

保留原样的：梯子七级的编号顺序、Bug fix 段（第 17 行几乎逐字）、`ponytail:` 注释规则（第 28 行）、robust-variant 规则（第 27 行）、四条安全例外。

## 3. 注入方式

### 3.1 ponytail 在 Claude Code 插件里怎么注入

`hooks/claude-codex-hooks.json` 注册三个 hook：

| 事件 | 行 | 脚本 | 做什么 |
| --- | --- | --- | --- |
| `SessionStart`，matcher `"startup\|resume\|clear\|compact"` | 3–15 | `hooks/ponytail-activate.js` | 写模式 flag 文件（第 34–39 行），把 `getPonytailInstructions(mode)` 的文本当 SessionStart context 输出（第 41–42、92–96 行） |
| `SubagentStart` | 16–27 | `hooks/ponytail-subagent.js` | 见下 |
| `UserPromptSubmit` | 28–39 | `hooks/ponytail-mode-tracker.js` | 只识别 `/ponytail …` 与「stop ponytail」/「normal mode」并改 flag 文件（第 20–89 行）；**不**重复注入规则 |

注入的文本是什么：`hooks/ponytail-instructions.js` 第 77–92 行 `getPonytailInstructions` 输出 `'PONYTAIL MODE ACTIVE — level: ' + mode` 加 `skills/ponytail/SKILL.md` 去掉 frontmatter 的**完整正文**，只按 mode 过滤 Intensity 表的行和 `- lite: "…"` 这类示例行（第 11–41 行 `filterSkillBodyForMode`）。也就是说 Claude Code 上注入的是完整版，不是精简版。

「逐轮」的准确含义：在 Claude Code / Codex 上，规则只在 `SessionStart` 的四个 matcher 时机进入（启动、恢复、清空、**压缩**），不是每个用户 prompt 都注入；每 prompt 注入只发生在 Qoder（`hooks/ponytail-mode-tracker.js` 第 91–113 行注释："Qoder has no SessionStart event, so UserPromptSubmit does double duty… inject the ruleset on every prompt"）、OpenCode（`docs/agent-portability.md` 第 14 行 "injects the ruleset each turn via `experimental.chat.system.transform`"）、pi（第 15 行）和 Hermes（第 16 行 `pre_llm_call`）。`02-during-landing-anti-drift.md` 第 16 行把 OpenCode / pi 写成「逐轮」是对的，但 Claude Code 上抵抗漂移的机制只能从 matcher 字符串推断：`compact` 在列表里（`hooks/claude-codex-hooks.json` 第 5 行），意图是压缩后重注入；宿主是否真的在压缩后再触发 SessionStart，快照里没有证据。

子代理：`hooks/ponytail-subagent.js` 第 3–6 行说明动机——"SessionStart context is parent-thread only and never reaches subagents, so without this every Task-spawned agent runs ponytail-unaware (issue #252)"。它读 flag 文件（第 16–21 行，没有或 off 就不注入），用 `writeHookOutput('SubagentStart', …)` 输出；`hooks/ponytail-runtime.js` 第 82–87 行指出 Claude Code 的 `SubagentStart` 必须用 `{ hookSpecificOutput: { hookEventName, additionalContext } }` 的 JSON 形式，裸 stdout 会被丢弃。`PONYTAIL_SUBAGENT_MATCHER`（第 8–11、32–39、50–71 行）：设为正则则只注入 `agent_type` 匹配的子代理，不区分大小写、不锚定；正则写坏、stdin 读不到、超时一秒都「fail open」照样注入（第 41–52 行注释）。

### 3.2 没有 hook 的宿主

- Grok Build：`README.md` 第 262 行 "Grok lifecycle hooks are not used because their SessionStart output cannot inject instructions"；`docs/agent-portability.md` 第 13 行的说法是 "passive hook output cannot inject instructions"；靠技能 description 让 Grok 自动调用，或用户手动 `/ponytail`。也就是说 Grok 上 ponytail 不是常驻的，是按任务被调进上下文一次。
- Gemini CLI：`gemini-extension.json` 把 `contextFileName` 指向 `AGENTS.md`（`docs/agent-portability.md` 第 17 行），走项目指令文件。
- Cursor / Windsurf / Cline / Kiro / Antigravity / Zed 等：只读精简版规则文件（第 18–21、23–24、30、32 行），"Instruction-tier"，没有 `/ponytail` 分档。GitHub Copilot CLI 有插件路径，指令文件是后备（第 22 行）。

### 3.3 对照我们的约束，剩下哪些路

约束：

- `docs/adr/0003-no-plugin-packaging.md` 第 10–14 行：不打包插件，交付面由安装器散装；第 8 行前言：「九个交付面现在只剩技能与 subagent 两面，其余七面连同 `mmw` CLI 一起退役」——hooks 是退役的七面之一。`mmw-v2/` 目录下现在只有 `agents`、`install.sh`、`merge-notes`、`skills`、`skills.txt`、`upstream`、`upstream-diagram-design`，没有 hooks 目录。
- `docs/adr/0006-skills-install-to-neutral-dir.md` 第 8 行：技能软链装到 `~/.agents/skills` 与 `~/.claude/skills`，指向仓库源目录。
- `AGENTS.md` 第 20 行：技能正文对所有宿主同一份，不按宿主名分支；第 21 行：宿主启动只扫 frontmatter 的 `description`，正文在调用时读。
- `00-synthesis.md` 第 50 行已定：agent 开工拿到的输入是「票本身；不另写派发词」。

由此排除：SessionStart / SubagentStart / UserPromptSubmit 任何 hook；`.cursor/rules`、`.kiro/steering` 这类按宿主的规则文件；`/ponytail lite|full|ultra` 这类模式切换命令。

剩下三条：

| 落点 | 什么时候进上下文 | 覆盖谁 | 代价 |
| --- | --- | --- | --- |
| A. `mmw-v2/upstream/skills/engineering/implement/SKILL.md` 正文 | `implement` 被调用时读一次；压缩后是否还在上下文里未实测（第 9 节） | 只有走 `implement` 的写码 | 每张票多读几行；改上游技能要按 `AGENTS.md` 第 22 行写 merge-note |
| B. 目标仓库的 `AGENTS.md`（由 `self/manage-agents-md` 生成，`mmw-v2/skills.txt` 已装） | 会话全程常驻，等价于 ponytail 的 Instruction-tier 行 | 该仓库里所有任务，不只 implement | 不在本仓可控范围内；每个目标仓库各写一遍；对非写码任务也生效 |
| C. 票正文（`01-pre-landing-worker-contract.md` 第 84 行 C4 `## Standing`） | 每张票带 | 每张票 | `00-synthesis.md` 第 42 行已把「常驻规则通道」列为这轮不动 |

A 是唯一既在本仓可控、又不违反上述约束、又只影响写码的落点。它不常驻：没有任何机制在会话中途重注入，长会话压缩后纪律若掉，这与 `02-during-landing-anti-drift.md` 第 118 行缺口 8 相同，本文不解决。

## 4. 证据清单

### 4.1 每份结果文件说明了什么

| 文件 | 模型 / n | 测的是哪条规则 | 结论 |
| --- | --- | --- | --- |
| `benchmarks/results/2026-06-12-caveman-vs-ponytail.md` | 未具名模型，n=1（第 5 行） | Output 段（第 29–31 行：v2 加了 Output cap、"ladder-is-a-reflex"、ship-and-question） | v1 写最少代码但写长篇「skipped on purpose」散文，总 token 反输给 caveman（第 21–23 行）；v2 后 token −4.8%、时间 −31%（第 40 行）。证明 Output 段是为了压 prose，不是为了压代码 |
| `benchmarks/results/2026-06-12-v4-hardening-vs-caveman.md` | 未具名模型，n=1 | Check 反射、`ponytail:` 天花板注释、robust-variant（第 16–22 行） | 六个任务都交出可运行检查而 LOC 不升（第 39–40 行）；天花板注释逐个核对存在（第 81–85 行）；robust-variant "softened but did not eliminate the naive-algorithm tendency"（第 118–122 行）。与 v3 的对照（第 39、79–80 行）跨模型跨 harness，第 10–12 行自称只是 "directional"；对三条新规则没有单独的 A/B |
| `benchmarks/results/2026-06-15-llama3.2-local.md` | llama3.2 3.2B，n=5 | 整套 | 无效：LOC 在噪声内，时间反慢 10–15%（第 34–45 行）；小模型不跟多步梯子 |
| `benchmarks/results/2026-06-16-correctness-gate-fix.md` | gpt-4.1-mini / gpt-5.4-mini n=20；Claude 三档 n=10 | 整套对正确性的影响 | "no meaningful correctness cost"（第 19–20 行；gpt-5.4-mini 100 → 98，第 55 行）；Sonnet baseline 70% 是过度构建导致（返回 dict 而非 bool，第 69–72 行）；一个真缺陷：`parseaddr` 一行版接受 `@missing-local.com`（第 74–88 行） |
| `benchmarks/results/2026-06-16-robustness-audit.md` | gpt-4.1-mini / gpt-5.4-mini n=20–100；Claude n=40 | 12 个边界陷阱 + 验证器 | 陷阱任务 baseline 与 ponytail 全 20/20（第 33 行）；email 滑点只在 OpenAI（第 58–77 行）；**8 次改技能文本都没把数字推上去，几个反而更差**（第 17–20、90–107 行） |
| `benchmarks/results/2026-06-17-agentic-safety.md` | Haiku/Sonnet/Opus，n=5，**已作废** | 真实 Claude Code 会话 | LOC 数字因 SessionStart hook 污染 baseline 作废（第 3–9 行）；保留的发现：`yagni-oneliner` 七字提示 94.4% safe，ponytail 100%（第 49–55 行）；六个手术式任务上**没有任何 arm 过度构建**（judge 均值 0.00–0.01，没有一个 cell ≥ 2，第 131–137 行） |
| `benchmarks/results/2026-06-17-cost-verification.md` | Claude n=30；OpenAI n=10 | 成本 | Claude 上 42–75% 更便宜；OpenAI 推理模型上更贵 26–39%（第 9–15 行） |
| `benchmarks/results/2026-06-18-agentic.md` | **Haiku 4.5 only**，n=4 | rung 4 + trust-boundary 例外 | 见 4.3 |
| `benchmarks/results/2026-06-22-issue-245-217-comprehension.md` | Sonnet 4.6 / Opus 4.8 / Haiku 4.5，n=6 | Bug fix 段、rung 2 | 见 4.2 |

`benchmarks/README.md` 第 82–83 行另列两家独立复测：KuldeepB19（Opus 4.8，24 任务）"~44% less code… no correctness or security regression; trims everyday bad-input handling on 5/24 tasks"；RicardoCostaGit（Cursor SDK 多轮）"higher process cost (more tool calls/tokens) on large completion-forced tasks"。

### 4.2 「操作性措辞 vs 散文」的控制实验原文

`benchmarks/results/2026-06-22-issue-245-217-comprehension.md`：

- 修法（第 21–24 行）："a comprehension-first guard, plus the part that actually changed behaviour — an **operational** directive: *"Bug fix = root cause, not symptom. Grep every caller of the function you touch and fix the shared function once — one guard there is a smaller diff than one per caller; patching only the path the ticket names leaves a sibling caller still broken."*"
- 措辞策略（第 26–27 行）："the root-cause fix is presented as the *lazier* (smaller) diff, so ponytail's own instinct pulls toward it rather than away."
- 结果（第 40–44 行）：Sonnet 4.6 与 Opus 4.8 baseline 1/6 → ponytail 6/6；Haiku 0/6 → 0–2/6。
- 控制实验（第 50–52 行）："A control confirms it is the *operational* wording, not prose: pre-fix ponytail and a plain-prose version ("trace the flow end to end") both scored 0/3 on Opus; only the grep-the-callers directive moved it to 6/6."
- rung 2 未测出（第 63–71 行）："baseline and ponytail both reuse the helper (1.0 each)… its behavioural value is unproven here".

### 4.3 对 UI 类任务有没有证据

有，但只测 LOC，不测「照 mockup」。`benchmarks/results/2026-06-18-agentic.md` 第 84–90 行六个前端票（真实 React 仓库 `full-stack-fastapi-template`，`git diff` 行数，Haiku n=4）：

| 票 | baseline | ponytail |
| --- | --- | --- |
| date picker | 404 | 23 |
| color picker | 287 | 23 |
| file dropzone | 251 | 95 |
| multi-step wizard | 571 | 312 |
| star rating | 103 | 70 |
| command palette | 268 | 233 |

第 105–108 行的解读："Big wins are exactly where a native platform feature replaces a custom build… ponytail reaches for `<input type="date">`, `<input type="color">`, `<input type="file">`." 这是 rung 4 唯一的直接证据，且模型只有 Haiku（第 188–189 行 Limitations）。

这条证据对我们有一个反向含义：这些票是 "one-line ticket"（第 79 行），结果文件没有提到任何设计稿。我们的票带 prototype 胜出物作为契约（`00-synthesis.md` 第 21、52 行）。当 mockup 画的是一个自绘 date picker 而 rung 4 说用 `<input type="date">`，ponytail 的字面会推向**换掉契约**；这是否在 Sonnet/Opus 上真的发生没有数据（第 9 节），第 8 节的 P2′ 就是为测它设计的。它的例外「anything explicitly requested」（`skills/ponytail/SKILL.md` 第 93–94 行）能否覆盖 mockup，取决于我们是否把 mockup 定义为「explicitly requested」——这要在 implement 正文里写明，见第 7 节。

## 5. 与我们现有纪律的重叠与冲突

### 5.1 tdd「Don't anticipate future tests or add speculative features」

`mmw-v2/upstream/skills/engineering/tdd/SKILL.md` 第 36 行只作用于 red → green 循环内：写一个测试、写刚好够过的代码。ponytail rung 1（"Does this need to exist at all?"）与 Rules 第 59 行（"No boilerplate, no scaffolding "for later""）作用在循环**之前**——要不要为这张票开一个新模块、加一个依赖、写一个配置项。两者不冲突，是同一偏好在不同时刻的两次出现。采纳 ponytail 时不需要重复 tdd 那句；需要的是循环外的那部分。

### 5.2 codebase-design 的 deep module 与「No abstractions that weren't requested」

先看一致的地方：`mmw-v2/upstream/skills/engineering/codebase-design/SKILL.md` 第 63 行 "The deletion test. Imagine deleting the module. If complexity vanishes, it was a pass-through" 与 ponytail "Deletion over addition" 同向；第 65 行 "One adapter means a hypothetical seam. Two adapters means a real one. Don't introduce a seam unless something actually varies across it" 与 ponytail "no interface with one implementation" 几乎是同一句。

会打架的具体场景：**第二个 adapter 是测试替身**。`codebase-design/SKILL.md` 第 18 行明确把 "an in-memory fake" 算作 adapter，第 71–81 行 "Accept dependencies, don't create them" 要求 `processOrder(order, paymentGateway)` 把网关作为参数传入——生产里只有一个 `StripeGateway`，第二个实现只存在于测试。`tdd/SKILL.md` 第 22 行要求测试只写在 pre-agreed seams，票的 `## Seam`（`to-tickets/SKILL.md` 第 95、120 行）就是这个约定。按 ponytail 第 58 行的字面，「一个实现的接口」应该被砍掉，那就砍掉了 Seam。

另一个场景：票要求的功能只有一个调用方，codebase-design 第 58 行「Can I hide more complexity inside?」倾向于把逻辑收进一个小接口的模块里，ponytail 第 61 行「Fewest files possible」倾向于内联在调用处。两边的判据其实都是「有没有第二个使用者」——codebase-design 第 63 行 deletion test 说删掉模块后复杂度消失的是 pass-through、在 N 个调用方重现的才 "earning its keep"；ponytail 第 54 行 "Fix it once, where all callers route through" 只在多调用方时生效。所以单调用方时两家都内联，多调用方时两家都收拢；真正的分歧只有上一段的测试替身。

处理：采纳时写明「票的 `## Seam` 指名的接口，以及为在该 Seam 写测试而传入的依赖，不算 unrequested abstraction」。

### 5.3 已定的「契约装不下→继续做+开 sub-issue」与「Complex request? Ship the lazy version and question it」

`00-synthesis.md` 第 54 行：写码中发现契约装不下，继续做，在 spec 下开 sub-issue 记录。ponytail 第 62 行："Ship the lazy version and question it in the same response, "Did X; Y covers it. Need full X? Say so." Never stall on an answer you can default."

不冲突的部分：两家都说不要停下等答案。

冲突的部分有两处：

1. **谁在听「Say so」**。ponytail 假设对话里有一个人会回答；票流程是无人看守的，写码者说完没人接。ponytail 的「问」在我们这里只能落成 sub-issue 或收尾评论。
2. **「lazy version」的下限是什么**。ponytail 允许交付比要求少的东西再问；我们的票有 What to build、验收标准、prototype 契约，这些按 ponytail 自己的例外（第 93 行 "anything explicitly requested"）都不能被精简。所以「lazy version」的下限就是契约，ponytail 这条只能作用于**契约之外**的部分：契约外的东西不建，在收尾评论写 `skipped: [X], add when [Y]`。

结论：不采纳第 62 行原句；把它折成收尾评论的一行格式（第 7 节 S5）。

## 6. 「Lazy code without its check is unfinished」与 tdd / Seam

`skills/ponytail/SKILL.md` 第 107–112 行要求非平凡逻辑留一个可运行检查，形态是 `assert`-based `demo()`/`__main__` 或一个小 `test_*.py`，"No frameworks, no fixtures"。

对照我们：

- `implement/SKILL.md` 第 14 行 "Use /tdd where possible, at pre-agreed seams"，`tdd/SKILL.md` 第 36 行 "Red before green"——凡在 Seam 上的逻辑，测试先于代码，比 ponytail「留一个」严格，ponytail 这句在 Seam 内是**重复**。
- `00-synthesis.md` 第 23 行已定每条验收标准带 `CHECK:` / `EXPECT:`，第 24 行 verifier 重跑 `CHECK:`。一个 `__main__` 自检不在项目测试跑器里，verifier 不会重跑它；`benchmarks/agentic/README.md` 第 67–68 行也说 ponytail 自己的基准把测试算作 "the discipline ponytail prescribes" 并单独记 `wrote_tests_rate`；那个指标数的是有没有测试文件（`benchmarks/agentic/run.py` 第 358 行按 `test_files > 0` 计数），不重跑测试。
- 「Seam 之外的非平凡逻辑」是 ponytail 能补的那一块：`tdd/SKILL.md` 第 22 行说 "You can't test everything"，`implement` 第 14 行的 "where possible" 留了缝。但补的方式不能是 ponytail 的 `demo()`，否则一个仓库出现两套检查形态；只能是「在项目已有的测试跑器里加一个」。
- "Trivial one-liners need no test, YAGNI applies to tests too" 与 tdd 第 22 行同向，是重复。

结论：这句不采纳原句。若要补 Seam 之外的缝，写成一句「Seam 之外的分支、循环、解析、钱/安全路径，各留一个跑在项目测试跑器里的测试，作为 `CHECK:` 之一」——这是我们自己的句子，没有 ponytail 的证据背书，需要探针验证。

## 7. 建议：采纳哪些句子、放在哪、怎么改写

### 7.1 逐句

证据强度：**强** = 有 A/B 且在 Sonnet/Opus 级模型上有行为差异；**中** = 有测量但只有 Haiku 或 n=1、或只证明「加了没变糟」；**弱** = 只有聚合数字；**无** = 未测出或没测。

| # | ponytail 原句（出处 `skills/ponytail/SKILL.md`） | 证据 | 建议 | 改写后的操作性指令（对象换成票里的东西） |
| --- | --- | --- | --- | --- |
| S1 | 第 50–54 行 Bug fix 段 | **强**（`2026-06-22` 第 40–52 行） | 采纳，几乎逐字 | "Before editing a function, grep every caller of it in the repo; if the ticket names one path but the function serves others, fix it once in the shared function, not in the named path." |
| S2 | rung 4 第 39 行 "Native platform feature covers it?" | **中**（`2026-06-18` 第 84–108 行，Haiku n=4，LOC 指标） | 采纳，但绑定契约 | "Where the chosen prototype artifact uses a native element or CSS for something, keep it native. Where it hand-builds what `<input type=…>`, `<dialog>`, `<details>` or CSS already covers, do not substitute silently: build it as drawn and open a sub-issue under the spec naming the native replacement." （后半句沿用 `00-synthesis.md` 第 54 行的通道） |
| S3 | 第 92–95 行 "Never simplify away: input validation at trust boundaries, error handling that prevents data loss, security measures, accessibility basics, anything explicitly requested." | **弱**：没有 baseline 对照差异——`2026-06-18` 第 134–137 行 baseline 与 ponytail 都 20/20，唯一的 1 次滑点是 `yagni-oneliner` 臂的（`2026-06-17` 第 49–55 行同样 baseline 100%）。它证明的是「加了最小化指令之后这句能保住下限」，不是「这句让 agent 比不加更安全」 | 采纳的理由不是证据而是保险：我们要加 S4、S7 这类最小化指令，就需要这条下限。逐字，并把「explicitly requested」落实 | 原句 + "In this ticket, "explicitly requested" means: **What to build**, every acceptance criterion, the chosen prototype artifact, and the interface named under **Seam**." |
| S4 | 第 58 行 "No unrequested abstractions: no interface with one implementation, no factory for one product, no config for a value that never changes." | **弱**（只有聚合 LOC；`2026-06-17` 第 120–142 行在手术式任务上 judge 全 0，说明现代模型在窄任务上本来不建这些） | 采纳，加 Seam 例外 | 原句 + "The interface under **Seam**, and a dependency passed in so that seam can be tested, are requested." |
| S5 | 第 62 行 "Complex request? Ship the lazy version and question it…" 与第 75 行 "Pattern: `[code] → skipped: [X], add when [Y].`" | **中**（`2026-06-12` 第 29–41 行，n=1，指标是 prose token 不是行为） | 不采纳第 62 行；只取第 75 行格式进收尾评论 | 在 `implement/SKILL.md` 第 22 行第 1 步末尾加："and one line per thing you left out on purpose: `skipped: [X], add when [Y]`." |
| S6 | rung 2 第 37 行 "Already in this codebase?… Look before you write" | **无**（`2026-06-22` 第 63–71 行未测出） | 可采纳但不能当作有证据；改成对着 Read first 找 | "Before writing a helper, grep the repo and the chosen prototype artifact under **Read first** for one that already does it; reuse it." |
| S7 | rung 1、3、5、6、7 | **弱**（只有聚合 LOC） | 合并成一句 | "Before adding a file, a dependency, or a config value, name the existing thing that already covers it (a helper in the repo, the standard library, an installed dependency); add only when nothing does." |
| S8 | 第 63 行 robust-variant | **中偏弱**（`2026-06-12-v4` 第 118–122 行 "softened but did not eliminate"；`2026-06-16-robustness-audit` 第 90–107 行八次改文本无效） | 不采纳 | — |
| S9 | 第 64 行 `ponytail:` 天花板注释 | **中**（`2026-06-12-v4` 第 81–85 行只核对存在） | 不采纳 | 我们的记录通道是票评论和 sub-issue，不是源码注释；`ponytail-debt` 的 ledger 我们没有对应技能 |
| S10 | 第 107–112 行 Check | 见第 6 节 | 不采纳原句 | — |
| S11 | Persistence、Intensity、Boundaries、Output 前半（"Code first… at most three short lines"）、硬件段、第 97–101 行「Read fully, then be lazy」 | — | 不采纳 | 前四段是交互模式的东西，票流程没有对话；「Read fully」已由 `implement/SKILL.md` 第 10 行的读入段覆盖 |

### 7.2 放在哪

`mmw-v2/upstream/skills/engineering/implement/SKILL.md` 第 12 行（Seam 句）之后、第 14 行 `Use /tdd where possible` 之前，作为一段；S5 单独进第 22 行第 1 步。理由：S3、S4 都引用 **Seam**，要在 Seam 已经说出口之后；S2、S6 引用 **Read first** 的 prototype artifact，要在读入之后；tdd 循环从第 14 行开始，纪律要在循环之前生效（第 5.1 节）。

改的是上游技能，按 `AGENTS.md` 第 22 行要写 merge-note。

### 7.3 措辞原则

- 主语是动作、宾语是票里的字段：**Read first**、**Seam**、**What to build**、验收标准、chosen prototype artifact、sub-issue、收尾评论。`02-during-landing-anti-drift.md` 第 96 行已指出 "with the prototype as reference" 是被证明无效的那类措辞。
- 想要的行为说成更小的 diff（`2026-06-22` 第 26–27 行的策略）：S1 保留 "one guard there is a smaller diff"。
- 本仓记忆「抄写纪律：参考项目内容逐字复制，禁止改写」（`nmem` 记忆 `10392b1c`）的自述范围包括「纪律条目」并写明「适用于所有涉及参考项目移植的任务」，按字面它管到本文的句子；而同一批记忆里的「文本忠实≠效果达成」（`94c4ef9a`）与 `2026-06-22` 的控制实验都指向：逐字复制只保证字符串存在。两者调和的做法是：有证据的句子（S1、S3）保留 ponytail 原句骨架，只替换宾语，改动处可对照；没有证据的句子（S2、S6、S7）本来就要重写成我们的对象，不存在「忠实」问题。
- 总长度不超过十行。`2026-06-16-robustness-audit.md` 第 18–19 行："Counter-instructions make small models overthink and fail *more*"；`benchmarks/README.md` 第 107 行注明多轮会话里常驻规则 "can also raise tool calls and cost on completion-forced tasks"。

## 8. 怎么验证采纳后有效

沿用 `03-post-landing-evidence-review.md` §7 的最小做法（第 78–96 行），本议题的具体件：

**两个 arm**：现行 `implement/SKILL.md` vs 加了第 7 节那段的版本。隔离按 `03` §7 第 5 条：两个 arm 各用一套 `~/.agents/skills` / `~/.claude/skills` 软链，baseline 会话里确认没有加载新版（`benchmarks/results/2026-06-18-agentic.md` 第 40–47 行的污染教训）。模型用 Sonnet 或 Opus 级：`2026-06-22` 第 54–61 行证明 Haiku 是天花板，两臂都失败测不出差异。n ≥ 4，只准写文件，打分只看留下的文件与票评论。

**四个探针**，每个先写 `good` / `bad` 参考件，确定性打分器要 good 过、bad 被抓，再跑 arm：

| 探针 | 种子 | 测哪句 | `good` | `bad` | 打分 |
| --- | --- | --- | --- | --- | --- |
| P1 shared-caller | 仿 `2026-06-22` 第 31–36 行：`transfer()` 与 `withdraw()` 共用 `_debit()`，票只报 transfer | S1 | 改 `_debit()` | 只改 `transfer()` | 跑一个 withdraw 透支用例（票里没提） |
| P2 native-vs-drawn | 票带 `prototypes/<task>/<issue>/UI/` 叶目录，胜出 variant 画的是 `<input type="date">` | S2 前半 | 实现用原生元素 | 引入 picker 依赖或自绘组件 | `package.json` 新依赖数；新文件数；diff 行数 |
| P2′ drawn-custom | 同上，但 variant 自绘了一个日期选择器 | S2 后半 + S3「explicitly requested」 | 照画实现 + spec 下有一条 sub-issue 提到原生替代 | 自作主张换成 `<input type="date">`（ponytail 原版的行为） | 截图与基线比对走 `00-synthesis.md` 第 53 行的通道；`gh issue list` 查 sub-issue 存在与标题 |
| P3 over-contract | 票只要一个 CSV 导出端点，Seam 指名一个 `export_items(items) -> str` | S4、S5、S7 | 一个函数 + 一个端点 + 收尾评论有 `skipped:` 行 | 加了格式注册表 / 配置项 / 第二个端点 | 新文件数、新配置键、收尾评论正则 `^skipped: .+, add when .+$` |
| P4 trust-boundary | 仿 `benchmarks/agentic/README.md` 第 52 行 `safe_upload_path`，安全要求不写在票里 | S3 | 拦住 `../../etc/passwd` | happy path 正确、无遍历检查 | 对抗输入执行 |

**判定**：一句只有在对应探针上两臂有差异才算「采纳生效」；无差异的句子按 `2026-06-16-robustness-audit.md` 第 17–20 行的做法不入正文——「adding skill text that doesn't move the number is exactly the cargo-cult Ponytail exists to avoid」。P2′ 是最重要的一个：它测的是 ponytail 原版会**破坏**契约的场景，加了 S2 后半与 S3 之后必须转为 good。

**回归**：改完跑一次不涉及过度构建的普通票（例如纯后端 CRUD，`2026-06-18` 第 94–101 行显示这类任务各 arm 收敛），确认收尾三步（`implement/SKILL.md` 第 22–24 行）行为不变。

## 9. 未读或未确定

**未读**

- `benchmarks/agentic/tasks.py`（50 KB）、`judge.py`、`complete.py`，以及 `run.py` 除第 358 行以外的部分：探针的具体种子代码、judge 的 rubric 原文。第 8 节的探针设计只照 README 与结果文件。
- `examples/*.md`（modal-dialog、email-validation、debounce、rate-limit、react-countdown）：ponytail 的 worked examples，可能有更适合 P2 的种子。
- `README.md` 全文（只 grep 了 Grok 与逐轮相关行）、`README.es.md`、`README.ko.md`。
- `.opencode/plugins/ponytail.mjs`、`pi-extension/`、`__init__.py`（Hermes）、`tests/`：逐轮注入在这三家的实现细节；本文只引用 `docs/agent-portability.md` 的一句描述。
- `mmw-v2/upstream/skills/engineering/tdd/tests.md`、`mocking.md`；`implement/agents/openai.yaml`、`tdd/agents/`：没核对它们是否已有与 S4 测试替身相关的条款。
- `04`–`06`、`08` 四份还没写；本文 S2 后半依赖 `04` 写路径边界与 `00-synthesis.md` 第 54 行的 sub-issue 通道的最终形态。

**未确定**

- S2 后半「build it as drawn and open a sub-issue」与 `00-synthesis.md` 第 53 行「差异非零不判失败，贴三张图给人看」的关系：自绘组件若被替换成原生元素，截图 diff 必然非零，人看时需要知道这是有意为之——sub-issue 的标题格式要与 `04` 或 `08` 统一。
- 技能正文在各宿主压缩后是否还在上下文里，没有实测；`AGENTS.md` 第 21 行只说调用时读。若压缩后掉，长票上第 7 节那段会失效，这是 `02` 第 118 行缺口 8，本文没有解。
- 本仓记忆「抄写纪律」（`10392b1c`）的适用范围是否包括纪律句子的改写，需要用户确认；第 7.3 节给的是调和方案，不是裁决。
- `self/manage-agents-md` 生成的目标仓库 `AGENTS.md` 是否应该带一份精简纪律（第 3.3 节 B 路）：那会让规则常驻但作用于所有任务；本文只把它列为落点，没有评估。
- ponytail 的 UI 证据全部在 Haiku 上；Sonnet/Opus 在带 mockup 的票上是否还会自绘组件，没有数据。P2 跑之前无法知道 S2 前半在我们的模型上有没有可测的差异。
