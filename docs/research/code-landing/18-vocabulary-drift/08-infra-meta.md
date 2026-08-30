# 08 · 工具箱自身的基建与元技能

审计范围：`CONTEXT.md`、`AGENTS.md`、`CLAUDE.md`、`mmw-v2/install.sh`、`mmw-v2/skills.txt`、`mmw-v2/agents/`（assemble.py / advisor / claim-checker）、`mmw-v2/merge-notes/` 全部、`docs/adr/` 全部、`docs/agents/` 全部、`mmw-v2/skills/manage-agents-md/` 整个目录、`mmw-v2/skills/readable-docs/SKILL.md`、`mmw-v2/upstream/skills/productivity/writing-for-agents/`、`mmw-v2/upstream/skills/engineering/domain-modeling/`、`setup-matt-pocock-skills/SKILL.md`、两份 `README.md`、`mmw-v2/skills/exe-release/SKILL.md`。

---

## 发现 1：根 `CLAUDE.md` 里能不能写 `@import` 以外的内容——两个已安装技能给出相反的指令

- 类型：分岔
- 后果：跑 `setup-matt-pocock-skills` 的 agent 会把 `## Agent skills` 整块写进 `CLAUDE.md`；跑 `manage-agents-md` 的 agent 随后跑 `check.sh`，那一块的每一行都会被判成 `line N is not an @import`，两个技能互相拆对方的台。
- 证据：
  - `mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/SKILL.md:76` 「- If `CLAUDE.md` exists, edit it.」
  - `mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/SKILL.md:80` 「Never create `AGENTS.md` when `CLAUDE.md` already exists (or vice versa); always edit the one that's already there.」
  - `mmw-v2/skills/manage-agents-md/write.md:13` 「**Write the root `CLAUDE.md`**: the line `@AGENTS.md`, plus any other `@` line listed under `## Imports found in old CLAUDE.md files` in `inputs.md` that came from the root `CLAUDE.md`. Nothing else.」
  - `mmw-v2/skills/manage-agents-md/scripts/check.sh:65` 「`*) fail "$br: line $ln is not an @import: $line" ;;`」
  - 本仓已经默默选了一边：`docs/adr/0005-docs-layer-adopted-by-v2.md:10` 「并在根 AGENTS.md 落 `## Agent skills` 块」——与 setup 技能第 4 步的选择规则相反，且没有任何 merge-note 记这次偏离（`mmw-v2/merge-notes/` 下没有 `setup-matt-pocock-skills.md`）。
- 建议正名：以 `manage-agents-md` 的形态为准（`CLAUDE.md` 只放 `@` 行），并给 `setup-matt-pocock-skills` 补一份 merge-note，把第 4 步的选择规则改成「总是改 `AGENTS.md`」。

## 发现 2：本仓自己的 `AGENTS.md` 过不了自己技能的机械检查

- 类型：断点
- 后果：任何 agent 按 `manage-agents-md` 的收尾步在本仓跑一次 `check.sh`，第一行就报错，而 `verify.md` 要求「Fix every line it prints and run it again until it prints `ok`」——它会去改根 `AGENTS.md`，而那份文件谁也没说过归这个技能管。
- 证据：
  - `mmw-v2/skills/manage-agents-md/write.md:53` 「Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full.」，同文件 `write.md:58` 「The last line is written exactly as shown, in English whatever the file's language.」
  - `mmw-v2/skills/manage-agents-md/scripts/check.sh:48-49` 「`grep -qiE 'subdirector.*AGENTS\.md|AGENTS\.md.*subdirector'` … `fail "$r: subdirectory sentence missing …"`」
  - 实际运行 `bash mmw-v2/skills/manage-agents-md/scripts/check.sh .` 的第一行输出：`AGENTS.md: subdirectory sentence missing (tell agents to read a subdirectory's AGENTS.md before working there)`，退出码 1。根 `AGENTS.md` 全文 36 行里没有这句话。
  - `mmw-v2/skills/manage-agents-md/verify.md:13` 「Fix every line it prints and run it again until it prints `ok`.」
- 建议正名：待用户拍板，两条路二选一——(a) 根 `AGENTS.md` 补上那句英文，让本仓成为自己技能的合格样本；(b) 在 `AGENTS.md` 里明写「本仓不由 `manage-agents-md` 管辖」，否则每个读到这个技能的 agent 都会去改它。

## 发现 3：code-review 到底几个轴——「两个轴」和「三个轴」两种说法同时活着

- 类型：分岔
- 后果：worker 走到收尾第三步，按 `ask-matt` 的说法它以为 review 只查 Standards 与 Spec，看到报告里多出一份 Tests 会当成越界；按技能自身的说法它该等三份。
- 证据：
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:3` 「Review the changes since a base commit along three axes: Standards …, Spec …, and Tests …」
  - `mmw-v2/merge-notes/code-review.md:21` 「| 「Why two axes」 | `SKILL.md` 末尾，改成「Why three axes」 | 多一行 Tests 轴的对照 |」
  - `mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md:25` 「then closes out by running **`/code-review`**, a two-axis review (Standards + Spec) of the diff, before committing.」
  - `mmw-v2/upstream/skills/engineering/README.md:30` 「**[code-review](./code-review/SKILL.md)**: Two-axis review of the diff since a fixed point: **Standards** … and **Spec** …, run as parallel sub-agents.」
  - `CONTEXT.md:497` 起注册了 `Standards` / `Spec` / `Tests` 三个轴。
- 建议正名：三个轴。`ask-matt/SKILL.md:25` 与 `engineering/README.md:30` 改口，并把这条写进 `mmw-v2/merge-notes/ask-matt.md`（那份 merge-note 目前只覆盖 `/prototype` 一条，没盖住 code-review 这句）。

## 发现 4：「全部技能模型可触发」是九份 merge-note 的共同前提，但四个已装技能仍然只许人触发

- 类型：分岔
- 后果：merge-note 告诉解冲突的人「上游改这一行 → 仍然删」，他按这条去扫一遍会发现四个技能没删，分不清是漏了还是故意；同时两份上游 README 的「User-invoked」清单已经全错，照它挑技能的人会以为 `/implement`、`/to-spec`、`/triage` 都得手打才能起来。
- 证据：
  - `mmw-v2/merge-notes/ask-matt.md:11`（另有 grill-with-docs / improve-codebase-architecture / teach / to-questionnaire / to-spec / to-tickets / triage / wayfinder 八份逐字相同的一行）「删掉。本仓库要求全部技能模型可触发——不留上游的人工触发限制」
  - 仍带该行且在 `mmw-v2/skills.txt` 名单里的四个：`mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/SKILL.md:4`、`mmw-v2/upstream/skills/productivity/grill-me/SKILL.md:4`、`mmw-v2/upstream/skills/productivity/handoff/SKILL.md:5`、`mmw-v2/upstream/skills/productivity/wait-what/SKILL.md:5`，均为 `disable-model-invocation: true`
  - `mmw-v2/merge-notes/wait-what.md:36` 反过来要求保留：「`policy.allow_implicit_invocation: false` | 上游原文，没改。它和 `SKILL.md` 的 `disable-model-invocation: true` 必须同设」
  - `mmw-v2/upstream/skills/engineering/README.md:7` 「## User-invoked / Reachable only when you type them（Claude Code: `disable-model-invocation: true` …）」，其下 `README.md:9-17` 仍把 ask-matt、grill-with-docs、triage、improve-codebase-architecture、to-spec、to-tickets、implement、wayfinder 列在这一节里——这八个的该行都已被删掉。
  - `mmw-v2/upstream/skills/productivity/README.md:11-12` 同样把 teach、to-questionnaire 列在 User-invoked 下。
- 建议正名：把那句话收窄成「本仓库要求**这几个**技能模型可触发」并逐个点名，或者把四个例外各写一份 merge-note 说明为什么留；两份 `README.md` 的两节按现状重排。

## 发现 5：`ask-matt` 自称是「a router over the skills in this repo」，但七个已装技能它一个都没提

- 类型：断点
- 后果：用户问「这件事该用哪个技能」，router 给出的地图里没有 `dispatch`、`verify-ticket`、`readable-docs`、`manage-agents-md`、`exe-release`、`claude-design-blocks`、`diagram-design`——正好是这条流水线夜间跑起来最要紧的那几个，读者走到这里接不上。
- 证据：
  - `mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md:3` 「description: Ask which skill or flow fits your situation. A router over the skills in this repo.」
  - `mmw-v2/skills.txt:35-42` 「`self/claude-design-blocks` / `self/exe-release` / `self/verify-ticket` / `self/readable-docs` / `self/manage-agents-md` / `self/dispatch` / `dd/diagram-design`」——`ask-matt/SKILL.md` 全文（89 行）里这七个名字零命中。
  - `mmw-v2/merge-notes/ask-matt.md` 只有两条意图（删 `disable-model-invocation`、跟上 prototype 的改造），没有「补上自研技能」这一条。
- 建议正名：要么把七个自研技能并进 `ask-matt` 的分类里并写进它的 merge-note，要么把 description 改成「A router over the upstream skills in this repo」——两条都行，但现在的措辞对读者是假承诺。

## 发现 6：写 `AGENTS.md` 的规则同时住在两个技能里，其中三段逐字重复

- 类型：冗余
- 后果：同一条规则改一处、另一处不动，两个 agent 按不同副本写出不一样的文件；而这两份文本自己都写着「Keep each meaning in a **single source of truth**」。
- 证据（逐字相同，已用 `diff` 核过）：
  - `mmw-v2/skills/manage-agents-md/prune.md:41-44` 与 `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL.md:78-81` 四条 Pruning 项完全一致，首条即「Keep each meaning in a **single source of truth**: one authoritative place, so changing the behaviour is a one-place edit.」
  - `mmw-v2/skills/manage-agents-md/prune.md:48` 与 `writing-for-agents/SKILL.md:74` 的 Negation 整段完全一致：「**Negation** is the failure mode beside this lever: steering by prohibition drags the forbidden behaviour into context…」
  - `mmw-v2/skills/manage-agents-md/write.md:151-153` 与 `writing-for-agents/SKILL.md:16-18` 的三条 Pointers 完全一致：「**Front-load the leading word** … **One trigger per branch.** … **Cut identity the body already carries.**」
  - 两者互不引用：`grep -rn "writing-for-agents" mmw-v2/skills/` 无命中；`grep -rn "manage-agents-md"` 在 `mmw-v2/` 内除自身目录外无命中。
  - 职责也重叠：`writing-for-agents/SKILL.md:3` 「Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md.」；`mmw-v2/skills/manage-agents-md/SKILL.md:3` 「Create, rewrite, or incrementally update a repository's AGENTS.md and CLAUDE.md to one fixed format.」
- 建议正名：`manage-agents-md` 的 `prune.md` 与 `write.md` 删掉这三段，改成指向 `writing-for-agents` 的一行 pointer；`writing-for-agents` 的 description 去掉 `AGENTS.md` 那一支，只留「writing documents agents consume」的通用判据。

## 发现 7：根 `CONTEXT.md` 的写法与 `domain-modeling` 给出的 `CONTEXT.md` 规格互相排斥

- 类型：分岔
- 后果：任何 agent 被叫去「更新 CONTEXT.md」，会同时收到两条相反的指令：技能说这是纯词表、每条一两句、不许有实现细节；文件本身有 699 行、条目里写满命令签名、常量名和结构化输出格式。它按哪一份改，结果都会被另一份判成错的。
- 证据：
  - `mmw-v2/upstream/skills/engineering/domain-modeling/SKILL.md:64` 「`CONTEXT.md` should be totally devoid of implementation details. Do not treat `CONTEXT.md` as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else.」
  - `mmw-v2/upstream/skills/engineering/domain-modeling/CONTEXT-FORMAT.md:28` 「**Keep definitions tight.** One or two sentences max. Define what it IS, not what it does.」
  - `CONTEXT.md:169-170` 「**EVIDENCE structured line**: The fixed shape the gate checker writes into `EVIDENCE:` — `exit=…; shell=…; cwd=…; path=…; EXPECT=matched; output-sha256=…; output-bytes=…`.」
  - `CONTEXT.md:471-472` 「**`PARALLEL` / `COOLDOWN_SECONDS` / `WAKE_BACKOFF` / `WAKE_LIMIT` / `REDISPATCH_LIMIT` / `MAX_HOURS` / `SNAPSHOT_INTERVAL`**: The constants at the top of `board.py`…」
  - `CONTEXT.md:423-424`（唤醒闭环）与 `CONTEXT.md:631-632`（基线）各是一条五六行的规则，远超「one or two sentences max」。
  - `docs/agents/domain.md:43` 也把它当纯词表用：「When your output names a domain concept …, use the term as defined in `CONTEXT.md`.」
- 建议正名：待用户拍板。两条出路：(a) 承认本仓的 `CONTEXT.md` 是「词表 + 接口契约」两用，在 `mmw-v2/merge-notes/domain-modeling.md` 里补一条意图说明本仓不守 `CONTEXT-FORMAT.md` 的这两条；(b) 把命令签名、常量表、输出格式从 `CONTEXT.md` 挪到各自脚本旁的文档里，`CONTEXT.md` 只留名字与一两句定义。

## 发现 8：ADR 之间「谁改写谁」有三套写法，索引首句的编号已过期

- 类型：重复定义 + 脚本与文档不符
- 后果：写新 ADR 的 agent 从 `ADR-FORMAT.md` 读到要用 `superseded by ADR-NNNN`，从现有文件读到 `amends: [0002]`，从索引读到两列中文表头；三者不通约，它写哪一种都会让索引与文件对不上。而索引首句给出的「现有最大号」还停在 0005。
- 证据：
  - `mmw-v2/upstream/skills/engineering/domain-modeling/ADR-FORMAT.md:21` 「- **Status** frontmatter (`proposed | accepted | deprecated | superseded by ADR-NNNN`): useful when decisions are revisited」
  - `docs/adr/0004-design-system-trust-comes-from-lint.md:3` 「`amends: [0002]`」；`docs/adr/0001-tracker-repo-authority.md:3` 「`amends: []`」——`amends` 这个键在 `ADR-FORMAT.md` 里一个字都没有。
  - `docs/adr/README.md:5` 「| 编号 | 标题 | 日期 | 改写了哪几份 | 被哪几份改写 |」
  - `docs/adr/README.md:3` 「手工维护：新增 ADR 时追加一行，编号取现有最大号 + 1（ADR 0005）。」——同一份文件 `README.md:12` 已经列到 「| 0006 | 技能装进一个各家通用的位置 …」，下一个号是 0007 而不是 0006。
  - 第四种写法：`docs/agents/domain.md:51` 「> _Contradicts ADR-0007 (event-sourced orders) — but worth reopening because…_」用的是 `ADR-0007` 带连字符的形式，而索引与 `amends` 用的都是裸号 `0007`。
- 建议正名：以 `amends:` + 索引两列为准（它是本仓实际在用的、`docs/adr/0005` 明写过继下来的），在 `mmw-v2/merge-notes/domain-modeling.md` 里补一条意图声明本仓不用 `Status: superseded by`；`docs/adr/README.md:3` 的括号删掉，别把一个会过期的数字写进规则句。

## 发现 9：五个测试层在 `CONTEXT.md` 之外没有任何落点，且「自写脚本层 = unittest」与实际不符

- 类型：断点 + 脚本与文档不符
- 后果：`AGENTS.md` 说「测试手工跑」，命令表里却只有安装的三条；agent 想跑「自写脚本层」找不到入口，只能自己在 `mmw-v2/skills/*/tests/` 里猜，而四个带测试的技能里只有两个有 `run.sh`。
- 证据：
  - `CONTEXT.md:679-698` 定义了五个层：`结构核对` / `自写脚本层` / `vendor 脚本层` / `技能行为层` / `真票`——这五个词在 `mmw-v2/`、`AGENTS.md`、`docs/` 里再无第二次出现（`grep -rn` 只命中 `CONTEXT.md` 自己）。
  - `AGENTS.md:11-15` 的命令表三行全是安装：「`bash mmw-v2/install.sh`」「`bash mmw-v2/install.sh --check`」「`python3 mmw-v2/agents/assemble.py --check`」，没有一条测试命令。
  - `CONTEXT.md:686` 「Scripts written in this repository are tested with unittest against fixed samples」——但 `mmw-v2/skills/manage-agents-md/tests/test_check.sh:1` 是 `#!/usr/bin/env bash`，`mmw-v2/skills/dispatch/tests/test_dispatch.sh`、`mmw-v2/skills/exe-release/tests/test_release_flow.sh` 同样是 bash，`mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md:48` 的 vendor 层命令是 `cd tests && node run-tests.mjs && node lint-tests.mjs`。
  - `mmw-v2/skills/manage-agents-md/write.md:139` 把 `mmw-v2/skills/<name>/tests/run.sh` 当成一整类文件的路径写进规则——实际只有 `mmw-v2/skills/exe-release/tests/run.sh` 与 `mmw-v2/skills/manage-agents-md/tests/run.sh` 存在，`verify-ticket` 与 `dispatch` 的 `tests/` 下没有 `run.sh`。
- 建议正名：把每一层的入口命令写进 `AGENTS.md` 的命令表（`write.md:141` 自己说「Prefer file-scoped test/lint/typecheck commands」，那张表就是它们的家），并给 `verify-ticket` 与 `dispatch` 各补一个 `tests/run.sh`，或把 `write.md:139` 的例子换成真实存在的路径。

## 发现 10：同一个东西三个名字——宿主 / host / harness

- 类型：命名撞车
- 后果：`AGENTS.md` 的硬约定用「宿主」表述，`models.md` 在同一句里同时用 `host` 和 `harness` 指同一列，读者不知道 harness 是第三种东西还是同一个；`CONTEXT.md` 这三个词一个都没登记，新会话没有仲裁者。
- 证据：
  - `AGENTS.md:19` 「技能正文对所有宿主是同一份：不把任何宿主当默认或首选，不按宿主名分支」
  - `mmw-v2/skills/dispatch/models.md:8-9` 「Non-empty, and the agent runs as its own session in a Herdr pane: the host column says which harness that session is, and the arguments are handed to that harness untouched.」
  - `mmw-v2/skills/dispatch/models.md:16` 「every harness spells its models, its thinking levels and its arguments its own way.」
  - `mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md:66` 「Narrow: only for a **new harness**, a **new directory**, a **colleague**…」；`ask-matt/PHASE-BOUNDARIES.md:29` 「swapping to a **new harness** (Claude → Codex)」
  - `CONTEXT.md` 全文没有 `host` / `宿主` / `harness` 的词条。
- 建议正名：在 `CONTEXT.md` 立一条 `宿主（host）`，`_Avoid_: harness`，然后把 `models.md:8-9,16` 与 `ask-matt` 两处的 harness 换掉。

## 发现 11：「上游 / upstream」既指两个 subtree，又指从 unlazy 抄来的脚本；provenance 说明也有两套

- 类型：命名撞车 + 重复定义
- 后果：`AGENTS.md` 教的解冲突办法（`git subtree pull` + 看 merge-note）对 `gate-check` 一个字都不适用，而 `CONTEXT.md` 把 `gate-check` 说成「vendored from upstream」，读者会去 `mmw-v2/upstream/` 里找它，找不到。
- 证据：
  - `AGENTS.md:22` 「`mmw-v2/upstream/` 是 mattpocock/skills 的 git subtree（squash），`mmw-v2/upstream-diagram-design/` 是 cathrynlavery/diagram-design 的另一个。」
  - `CONTEXT.md:203-204` 「**`gate-check`**: The judging engine vendored from upstream.」；`CONTEXT.md:207-208` 「**`gate-lint`**: The ticket-face linter vendored from upstream.」
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md:1-4` 「# Vendored from unlazy / Source: https://github.com/Leonxlnx/unlazy, commit `da0b00a3`」——第三个来源，既不是 subtree 也不在 `mmw-v2/upstream/` 下。
  - 两套 provenance 说明并存：`CONTEXT.md:667-668` 「**merge-note**: The note written or updated whenever a skill inside the upstream subtree is changed.」 对上 `CONTEXT.md:235-236` 「**`UPSTREAM.md`**: The note written whenever upstream scripts are vendored: source repository, commit, date, and which lines were changed.」
  - `mmw-v2/merge-notes/README.md:4` 给的看 diff 办法只对 subtree 成立：「diff 用 `git diff <上一个 Squashed 提交> -- <技能目录>` 看」。
- 建议正名：`CONTEXT.md:204` 与 `:208` 把「vendored from upstream」改成「vendored from unlazy」（这是文件自己的说法，逐字可查），并在 `AGENTS.md:22` 那一段补一句：subtree 以外还有一份 vendored 脚本，它的记录在 `UPSTREAM.md` 而不是 merge-note。

## 发现 12：`install.sh` 自称「就这两件事」，实际装四样；`AGENTS.md` 的命令表也只写两样

- 类型：脚本与文档不符
- 后果：`--check` 报出 `缺 …/hooks.json PreToolUse` 或 `残留 …/.grok/skills …` 时，只读过 `AGENTS.md` 和脚本抬头的人不知道这两类东西是谁装的、为什么该有；`dispatch.sh run` 又拿 `install.sh --check` 当开夜前的硬门槛（`CONTEXT.md:439-440`），门槛卡住时排查的人手上没有清单。
- 证据：
  - `mmw-v2/install.sh:2` 「# 把 skills.txt 列出的技能和 agents/ 下的 subagent 装到本机，让每个宿主都读得到。就这两件事。」
  - 同一份文件 `mmw-v2/install.sh:15-16` 「# 除技能、subagent、hook 之外还装一样：dispatch 技能带的 Herdr agent 检测规则覆盖，拷进 `~/.config/herdr/agent-detection/` 再让服务端重读。」——自称两件的下面 13 行就承认是四件。
  - `AGENTS.md:13` 「`bash mmw-v2/install.sh` | 唯一安装入口，把技能软链进 `~/.agents/skills` 和 `~/.claude/skills`，subagent 成品软链进各宿主」——hook 与 Herdr 检测规则两样没进表。
  - 实跑 `bash mmw-v2/install.sh --check` 的输出里确实有第三、第四类行：`hook  /Users/…/.claude/settings.json  PreToolUse` 等五行。
- 建议正名：`install.sh:2` 改成四件事并逐条列出，`AGENTS.md:13` 那一格同步补上「hook 与 Herdr 检测规则」。

## 发现 13：`HOOKS-INSTALLED` 是幽灵词——安装器从不打印它

- 类型：脚本与文档不符 / 幽灵词
- 后果：谁按 `CONTEXT.md` 写一条 `EXPECT: HOOKS-INSTALLED` 的验收标准，命令跑得再对也永远匹配不上；现在两处测试里之所以过，是因为它们自己额外 `print("HOOKS-INSTALLED")` 造了一个假标记。
- 证据：
  - `CONTEXT.md:369-370` 「**`HOOKS-INSTALLED`**: The marker the installer prints after its own check of the hooks it just wrote.」
  - `mmw-v2/install.sh:507` 实际打印的是 `print(f"hook  {path}  {event}")`（check 模式），`mmw-v2/install.sh:517` 是 `print(f"已装  {count} 处 hook -> 五个宿主")`（install 模式）——全文没有 `HOOKS-INSTALLED` 这个字符串。
  - `mmw-v2/skills/verify-ticket/tests/test_closeout.py:256-261` 「`T=$(mktemp -d) && MMW_V2_HOME="$T" bash mmw-v2/install.sh >/dev/null` / `python3 - <<'EOF'` / `print("HOOKS-INSTALLED")` / `EOF` / `EXPECT: HOOKS-INSTALLED`」——标记是这条 CHECK 自己 echo 出来的，不是安装器给的。
- 建议正名：要么让 `install.sh` 在 hook 装完/查完之后真的打印 `HOOKS-INSTALLED`（`CONTEXT.md` 已经把它当成契约），要么把这个词条从 `CONTEXT.md` 删掉、改登记 `hook  <path>  <event>` 这一行。

## 发现 14：安装器输出里的两个计数与它实际做的事对不上

- 类型：脚本与文档不符
- 后果：只装了 Claude Code 的机器上，安装完照样看到「五个宿主」；`--check` 通过时的那行汇总只数技能，读的人以为 subagent 与 hook 也在这个数里。
- 证据：
  - `mmw-v2/install.sh:517` 「`print(f"已装  {count} 处 hook -> 五个宿主")`」——`count` 只数了 `host_home.is_dir()` 为真的安装点（`install.sh:501-514`），宿主没装的会走 `print(f"跳过  {host_home}（宿主没装）")`，但句尾的「五个宿主」是写死的。
  - `mmw-v2/install.sh:529` 「`[ "$rc" -eq 0 ] && echo "齐了：${installed_dests} 处 × ${#wanted_names[@]} 个技能"`」——`installed_dests` 只在技能那一段自增（`install.sh:101`），而这一行是整个 `--check` 的收尾，涵盖范围包括 subagent（`install.sh:240-249`）、hook（`install.sh:505-511`）与 Herdr 规则（`install.sh:309-314`）。
- 建议正名：把「五个宿主」换成 `count` 已经算出的那个数；`齐了` 那一行加上 agent 与 hook 的处数，或者改成只说「齐了」不报数。

## 发现 15：`skills.txt` 说「两种来源」，实际列了三种

- 类型：脚本与文档不符
- 后果：加一个 `dd/` 前缀的技能时，读注释的人会以为自己在用一个不受支持的前缀。
- 证据：
  - `mmw-v2/skills.txt:4` 「# 两种来源：」，紧接着 `skills.txt:5-7` 列了三种：「`<桶>/<名>`」「`self/<名>`」「`dd/<名>`」
  - `mmw-v2/install.sh:4-6` 「# 技能有三个来源：mattpocock 上游的在 upstream/skills/，我们自己写的在 skills/（名单里前缀 self/），diagram-design 上游的在 upstream-diagram-design/skills/（前缀 dd/）。三者装法完全一样。」
- 建议正名：`skills.txt:4` 改成「三种来源」。

## 发现 16：五个标签在三个地方各定义一遍

- 类型：冗余
- 后果：改一处漏两处；三份措辞不同的定义之间没有主从关系，读者不知道哪份是准的。
- 证据：
  - `CONTEXT.md:593-594` 「**`ready-for-agent`**: In the agent queue — waiting to be dispatched, or being worked right now; the assignee says which. Taken off at both exits, whether the ticket closes or is handed back.」
  - `docs/agents/triage-labels.md:19` 「`ready-for-agent` means the ticket is in the agent queue, waiting to be dispatched or being worked right now. Whether anyone is on it is the assignee's job to say. It comes off when the ticket closes and when the ticket leaves the agent queue.」
  - `AGENTS.md:32` 「五个规范角色用默认标签串（`needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`）。See `docs/agents/triage-labels.md`.」
  - `needs-triage` 同样三处：`CONTEXT.md:585-586`、`docs/agents/triage-labels.md:21`、`docs/agents/triage-labels.md:7`（表格行）。
- 建议正名：`docs/agents/triage-labels.md` 是技能约定读取的那一份（`setup-matt-pocock-skills/SKILL.md:68` 把它列为要写的三份配置之一），以它为准；`CONTEXT.md` 的 `### Labels and standing` 各条改成一行加一个指向它的路径。

## 发现 17：「结构核对」要跑的两条命令，其中一条已经被另一条包含

- 类型：冗余
- 后果：读者以为要跑两次，第二次是空转；真正需要单跑 `assemble.py --check` 的场合（不想碰宿主目录只想验成品）没人说明。
- 证据：
  - `CONTEXT.md:681-682` 「**结构核对（structural check）**: Run the installer's own check and the subagent assembler's own check.」
  - `AGENTS.md:14-15` 把它们列成两条并列命令：「`bash mmw-v2/install.sh --check` | 只看不动」「`python3 mmw-v2/agents/assemble.py --check` | 校验 subagent 成品 `mmw-v2/agents/<名>/out/` 与源一致」
  - `mmw-v2/install.sh:210-211` 「`if [ "$mode" = check ]; then` / `python3 "$AGENTS_SRC/assemble.py" --check || rc=1`」——`install.sh --check` 内部已经跑了 `assemble.py --check`。
- 建议正名：`AGENTS.md` 那一行注明「`install.sh --check` 已包含它；单跑用于只验成品不看宿主」，或者 `CONTEXT.md:682` 改成「Run the installer's own check（它内含成品校验）」。

## 发现 18：同一个技能脚本，两种路径写法

- 类型：分岔
- 后果：`implement` 写死 `~/.agents/skills/…`，只有在 `install.sh` 无条件建过通用位置时才成立；`verify-ticket` 与 `exe-release` 自己教的是「从加载到的 `SKILL.md` 现算绝对路径」。同一个 worker 在同一次任务里会看到两种做法，改安装位置时也不知道要改几处。
- 证据：
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:8` 「First run `python3 ~/.agents/skills/verify-ticket/scripts/verify-ticket.py <n> --preflight`.」；同文件 `:32` 「the engine at `~/.agents/skills/verify-ticket/scripts/`, with `python3`」
  - `mmw-v2/skills/verify-ticket/SKILL.md:19-20` 「`scripts/verify-ticket.py`, next to this file. Resolve its absolute path once.」
  - `mmw-v2/skills/exe-release/SKILL.md:14` 「`scripts/release-flow.sh`, next to this file. Resolve its absolute path once.」
  - `mmw-v2/skills/manage-agents-md/verify.md:10` 第三种写法：「`bash "$(dirname <path of this skill's SKILL.md>)/scripts/check.sh" .`」
- 建议正名：以「next to this file，现算绝对路径」为准（它对两处安装位置都成立，也是 `docs/adr/0006` 里两处各自直指仓库的直接后果）；`implement/SKILL.md:8,32` 改掉，并在 `mmw-v2/merge-notes/implement.md` 里记下这条。

## 发现 19：`exe-release` 把失败交给 `/implement`，但 `implement` 第一步就要票号

- 类型：断点
- 后果：安装测试失败的 agent 按 `exe-release` 去起 `/implement`，`implement` 第一句要它跑 `verify-ticket.py <n> --preflight`，手上没有 `<n>`，走不下去。
- 证据：
  - `mmw-v2/skills/exe-release/SKILL.md:95` 「Fail: take the symptoms and repro steps to `/implement`, then ship again.」
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:8` 「First run `python3 ~/.agents/skills/verify-ticket/scripts/verify-ticket.py <n> --preflight`. … If it prints `NOT_READY`, stop」
  - `CONTEXT.md:479-480` 「**`implement #<n>`**: The dispatch line for a worker: skill name plus ticket number.」——派发词的形态里票号是必需的。
- 建议正名：`exe-release/SKILL.md:95` 改成「把症状与复现步骤开成一张 `needs-triage` 的票，再按 `implement #<n>` 派」，与 `CONTEXT.md` 的派发词形态对齐。

## 发现 20：`docs/adr/0006` 的两条 Consequences 已经与现状不符

- 类型：脚本与文档不符
- 后果：这份 ADR 是「本仓装到哪里、还剩几处按宿主分支」的唯一说明，两个数都错了以后，照它判断「再加一个宿主要改几行」的人会低估工作量。
- 证据：
  - `docs/adr/0006-skills-install-to-neutral-dir.md:23` 「- 软链从 150 条降到 60 条（`skills.txt` 30 条 × 位置数，前提是两处的宿主主目录都在）。」——`mmw-v2/skills.txt` 现在是 32 条（`skills.txt:9-33` 二十五条上游、`:35-40` 六条 self、`:42` 一条 dd）。
  - `docs/adr/0006-skills-install-to-neutral-dir.md:24` 「安装器里剩下的按宿主分支只有两处：Claude Code 那一个额外目标目录，和四个写死的退役目录。」——实际另有两组按宿主名写死的表：`mmw-v2/install.sh:226-232` 的六行 subagent 安装点（`claude.md` / `codex.toml` / `pi.md` / `cursor.md` / `grok.md` / `grok.role.toml`），与 `mmw-v2/install.sh:486-497` 的五行 hook 安装点。
- 建议正名：ADR 是有日期的记录，正文不必改；把这两句在 `docs/adr/README.md` 或 ADR 顶部用一行引言注明「数目见 `mmw-v2/skills.txt` 与 `mmw-v2/install.sh`，本篇记的是 2026-08-26 当时的值」——`docs/adr/0003` 已经用过这个办法（`0003:6-8` 的引言块）。

## 发现 21：`reference` 一个词，四种意思

- 类型：命名撞车
- 后果：`## Read first` 里写着「这是 reference 不是 baseline」的条目，和 `references/` 目录里子代理的判据、和 `AGENTS.md` 的 `## External References` 表、和 `writing-for-agents` 的内容类型，是四件不同的东西；agent 读到「reference」不知道该往哪一侧理解。
- 证据：
  - `CONTEXT.md:631-632`（基线）「Material recording process rather than conclusions — the body of a research file, a blueprint page — is reference, not baseline.」（= 非契约的参考材料）
  - `mmw-v2/merge-notes/code-review.md:43` 「`references/` 下只放 reviewer 的判据，一个 reviewer 一份」（= 子代理判据文件）
  - `mmw-v2/skills/manage-agents-md/survey.md:63` 「reference for a document that already covers a need (give its path as the fact)」与 `write.md:35` 的 `## External References` 表（= 已有文档的指路行）
  - `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL.md:31` 「**reference** (definitions, rules, facts consulted on demand)」（= 一种内容类型）
- 建议正名：待用户拍板。最低成本是给 `CONTEXT.md:631` 那一处换词（例如「过程材料」），把 `reference` 留给技能体系里已有的三种技术用法。

## 发现 22：`_Avoid_` 里的死词仍在活文件里

- 类型：幽灵词
- 后果：读者在 merge-note 与 `models.md` 里看到 `CONTEXT.md` 明令避开的词，会以为它们是另一个东西。
- 证据：
  - `CONTEXT.md:535-537` 「**交接包（handoff package）** … _Avoid_: 开发交接包, 基线目录, UI 基线」，但 `mmw-v2/merge-notes/to-tickets.md:19` 「`Read first` 与 `Seam` 非空且指向基线目录时注明它是契约」、`mmw-v2/merge-notes/code-review.md:18` 「不读 `prototypes/` 下的基线目录」两处仍在用「基线目录」。
  - `CONTEXT.md:11-13` 「**main agent（主 agent）** … _Avoid_: coordinator, 编排者, orchestrator, 出票的主 agent, 落地 agent」，但 `mmw-v2/skills/dispatch/models.md:3-4` 「Every agent this pipeline sends out is here except the orchestrator, which is the session you started yourself from the CLI.」
- 建议正名：两处「基线目录」换成「交接包」，`models.md:4` 的 `orchestrator` 换成 `main agent`。

## 发现 23：`merge-notes/README.md` 首句划的范围与它自己的清单不符

- 类型：内部不一致（重复定义）
- 后果：找 `diagram-design` 的说明时，按首句会以为它不在这里。
- 证据：
  - `mmw-v2/merge-notes/README.md:3` 「`mmw-v2/upstream/` 里被我们改过的技能，每个一份说明」
  - `mmw-v2/merge-notes/README.md:33` 「- [diagram-design](diagram-design.md) — `mmw-v2/upstream-diagram-design/`，另一个上游、另一个 subtree」——它不在 `mmw-v2/upstream/` 下。
- 建议正名：`README.md:3` 改成「两个上游 subtree 里被我们改过的技能」。
