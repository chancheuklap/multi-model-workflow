# R10 substrate 单元的归置

本文按 `docs/research/workflow-compare/reports/R4-mmw-architecture-form.md`（下称 R4）逐项归置 substrate 单元：`mmw-v2/prompt/`、`mmw-v2/install.sh`、`mmw-v2/skills.txt`、`~/.mmw/models.json` 与 `models.py config`、`mmw-v2/board/`、`mmw-v2/migrations/`、`mmw-v2/tests/`（含 `tests/lib/` 的三个检查）、`mmw-v2/merge-notes/`、`mmw-v2/downstream-notes/`、根 `AGENTS.md`、`CODING_STANDARDS.md`、`TESTING.md`、`CONTEXT-MAP.md` 与 `docs/contexts/`、`docs/adr/`、`docs/notes/`、消费仓库的 `.mmw/`（本仓根 `.mmw/` 为实例）与消费仓库 `AGENTS.md` 里指向 `mmw` 的那一行。

准绳：`docs/research/workflow-compare/reports/L7-pstack-component-contract.md`（下称 L7，本轮读了第 0、A、C、D 节）。事实清单：`N8-mmw-substrate.md`、`N9-mmw-adr-contexts-principles.md`、`N11-mmw-gaps.json`（下称 N8、N9、N11）；采用的结论都回到原文核对过，结果见第 1 节。

标注约定：「已核实」＝本轮读原文或跑只读命令看到；「推断」＝由原文推出、原文没写；做不出判断的放第 9 节。本文不改任何仓库文件。

---

## 0. 结论

1. **substrate 不产生 mode、playbook 或原则，它负责让它们被装上、被检查、有出处。** 装：`skills.txt` 加一行 `self/mmw`，`install.sh` 的代码一行不改（软链整个技能目录，`playbooks/`、`principles/`、`references/` 一并带过去，已核实 `install.sh` 第 143–230 行）。查：一个新 lint `tests/lib/check_wiring.py`，外加 `check_own_skill_frontmatter.py` 多一条。出处：原则的 `**Why:**` 取自 ADR 0008、0010、0017、0018、0019、0020，但运行时文本不写 `docs/adr/` 路径。
2. **12 个 `run.sh` 头部逐字相同的三行，合并进一个新脚本 `tests/lib/shared_lints.sh`。** 已核实：36 行逐字相同，分布在 12 个文件里。加 `check_wiring.py` 本来就要再改 12 处；合并后加这个检查只改一处，以后再加检查也只改一处。
3. **lint 的反例测试需要一个家，新建第 13 个套件 `mmw-v2/tests/lints/`。** 现有三个共用检查没有任何测试（已 grep 核实）；按 `mmw-v2/tests/AGENTS.md`，`lib/` 不是套件。
4. **R4 的 lint 第 6 类（技能名两两不同）不进 `check_wiring.py`，改为 `check_own_skill_frontmatter.py` 多查一条「frontmatter `name` 等于目录名」。** `install.sh` 第 158–159 行已按目录名查重名，今天 35 个技能的 `name` 全部等于目录名（已核实）。两条合起来就覆盖了宿主看到的名字，也不必再写第二个 `skills.txt` 解析器。
5. **`install.sh --check` 加一项：列出本机 `~/.mmw/state/*/watches.json` 里开着的 watch，不改退出码。** 收益是消除一处已核实的断点：`AGENTS.md` `## Gotchas` 要求「The third step waits while any watch is open」，但没有任何命令列出开着的 watch（`relay.py` 子命令只有 `start`、`add`、`stop`、`watching`、`run`、`ack`、`queue`，已核实）。它必须不改退出码，否则开夜前的 `dispatch.sh check` 会把「有别的 watch 开着」当作装得不齐，去跑完整的 `install.sh`（已核实 `dispatch.sh` 第 2344–2360 行）。
6. **`TESTING.md` 与新 lint 有冲突，要补一句。** `## What a test proves` 写「A test proves what a script does, never what a piece of text says」，Tests axis 照这句会把 `check_wiring.py` 和 relay 测试里对唤醒文字的相等断言（R4 V5）判成钉措辞。补一句：核对「脚本印出的名字在它指向的文本里存在」是接线检查；测试把这类输出与它取自的常量比较，不抄字面。
7. **R4 说在 SSR `### Scripts and judgement` 加一句「锚点由 lint 核对」，本文不采用，改写进 `CODING_STANDARDS.md` `## Skills and scripts`。** 读这句的是写脚本的人和 Standards axis。改标题的一侧由 lint 的拒绝文字给出路，SSR 不必另写一份。
8. **分叉（第 2 批）在本单元的实际改动面是 85 处路径。** `docs/contexts/` 里有 79 处 `_Home_` 或路径指向四个被分叉技能的 `mmw-v2/upstream/skills/engineering/…`（tickets 57、ticket-run 19、toolbox 2、ui-acceptance 1），加上 `docs/notes/` 2 处、四份 merge-note 各 1 处（已 grep）。这些必须和搬家在同一次提交里改。没有任何脚本依赖这些上游路径；`tests/verify-ticket/test_draft.py` 第 528 行那一处是夹具文字，不需要改（R4 K5 里的推断本轮已核实）。
9. **ADR 由一份改成三份，每批一份：0032（第 1 批，角色指针与按名锚点，`amends: [0020]`）、0033（第 2 批，分叉与调用开关的推导规则）、0034（第 3 批，`mmw` 及其 playbook 与原则，并取代 SSR 事实 7 的「no router」）。** 理由：`docs/adr/README.md` 规定一份 ADR 的决定就是它的标题加下一段；各批次独立落地，第 4 批还要以 T1 通过为前提。如果在第 1 批写一份描述 `mmw` 的 ADR，第 3 批一旦没落地，这份 ADR 记的就是一个没有做成的决定。
10. **残留 `ask-matt` 恢复上游原文，从 R4 的第 2 批挪到第 3 批，和新建 `mmw` 放在同一次提交里。** 这样头部判断、Context hygiene、阶段边界三块文字是「搬」，不是先删、隔一批再从 git 历史里捞回来。SSR `## Editing` 要求搬动时「carrying each sentence that still applies across verbatim」。
11. **不动的部分**：`shared.md`、`hosts/*.md`、`render.py`、`models.json` 的结构、`models.py`、board 全部、`migrations/` 全部（也不需要新迁移）、`downstream-notes/`、现有 ADR 正文，以及 `AGENTS.md` 的 Self-hosting boundary 正文。理由见第 6 节。

---

## 1. 本轮核实的事实

| # | 事实 | 出处 | 结果 |
|---|---|---|---|
| S1 | 12 个 `mmw-v2/tests/<name>/run.sh` 各有逐字相同的三行，依次跑 `check_module_paths.py`、`check_upstream_em_dashes.py`、`check_own_skill_frontmatter.py`；`prompt/tests/run.sh` 没有 | `grep -n` 三个文件名于 `tests/*/run.sh` | 已核实，共 36 行 |
| S2 | 三个共用检查没有任何测试文件引用 | `grep -rln` 于 `mmw-v2/tests/`，只命中 `run.sh` 与检查自身 | 已核实 |
| S3 | `install.sh` 按 `skills.txt` 的目录名查重名，重名就停；已是本仓软链的会被 `ln -sfn` 重指到新目标 | `install.sh` 第 143–230 行 | 已核实。分叉后 `implement` 等四条软链由重装自动改指 `mmw-v2/skills/<名>`，不需要改代码 |
| S4 | 35 个已装技能的 frontmatter `name` 全部等于目录名 | 逐个读 `SKILL.md` 第 2–6 行 | 已核实 |
| S5 | `install.sh --check` 从别的 checkout 运行时，`exec` 已安装 checkout 自己的 `install.sh --check` | `install.sh` 第 125–137 行 | 已核实。新加的检查项要等第一次提升之后才在已安装版本里生效 |
| S6 | `dispatch.sh check` 在 `--check` 非 0、且本 checkout 就是已安装 checkout 时，自动跑完整 `install.sh`；之后只把匹配 `缺|残留|不齐|不一致|没查|不是|没在跑` 的行作为警告印出 | `dispatch.sh` 第 2344–2360 行 | 已核实 |
| S7 | `watches.json` 是每个仓库状态目录里的一个 JSON，键为 `spec:<n>` 或 `tickets:<n>[,…]`；`relay.py` `read_watches` 只把同时有 `runner`、`session`，并且有 `spec` 或 `tickets` 的条目算作 watch。本机两个仓库当前都是 `{}` | `relay.py` 第 176–186、429–441 行；读本机两个文件 | 已核实 |
| S8 | 没有任何命令列出本机开着的 watch | `relay.py` 第 1761–1804 行的子命令表；`dispatch.sh` 的 `relay_watches` 只问一张票或一个 spec | 已核实 |
| S9 | `docs/contexts/` 里有 79 处路径指向 `mmw-v2/upstream/skills/engineering/{implement,code-review,to-tickets,to-spec}`，`docs/notes/` 2 处，merge-note 4 处，ADR 0012 1 处；脚本里 0 处 | `grep -rnoE` 全仓，排除 `docs/research/`、`docs/reviews/`、`archive/`、`deprecated/` | 已核实 |
| S10 | `tests/verify-ticket/test_draft.py` 第 528 行的上游路径在 `CAT_REVIEW_ROWS` 夹具里，测试只比较这一行文字，不解析路径 | 同文件第 527–545 行 | 已核实（R4 K5 的推断成立） |
| S11 | `manage-agents-md` 的 `scripts/check.sh` 只对「带斜杠的反引号词」检查路径是否存在 | `check.sh` 第 93–105 行 | 已核实。消费仓库 `AGENTS.md` 里写成「the `mmw` skill」能通过；写成 `mmw-v2/skills/mmw/SKILL.md` 或 `references/night.md` 会在消费仓库报路径不存在 |
| S12 | `TESTING.md` `## What a test proves` 原句：「A test proves what a script does, never what a piece of text says. Pinning the wording of a skill's `SKILL.md`, a reference, a refusal, or a start prompt's standing sentences forces a test edit…」 | `TESTING.md` 第 7 行 | 已核实 |
| S13 | `CODING_STANDARDS.md` `## Skills and scripts` 第 1 条把技能目录的内容列为「`SKILL.md`, reference files, `scripts/<…>`」 | 第 7 行 | 已核实 |
| S14 | `AGENTS.md` `## External References` 第 1 行写「six bounded contexts」，`CONTEXT-MAP.md` 第 3 行写「seven」并列出 7 个 | 两文件原文 | 已核实（N9 §10.1 成立） |
| S15 | `AGENTS.md` `## External References` 的 night runbook 一行，File 列是仓库路径 `mmw-v2/skills/dispatch/references/night.md`；同一文件 `## Self-hosting boundary` 要求一次运行只用已安装的 checkout，「Never run its copy of an MMW skill or script to control, interpret, repair or finish the run」 | `AGENTS.md` 第 10–12、43 行 | 已核实：两段文字方向相反。有没有 orchestrator 真的按这一行读了主工作树里的副本，没有记录 |
| S16 | 调用开关的理由在 merge-note 里重复出现：「免得漏输入指令时 agent 没法自己认出」5 处（to-spec、to-tickets、triage、wayfinder 的开关行，加上 implement 的同义句），「两处必须同增同删」4 处（to-spec 41、triage 36、to-tickets 50、wayfinder 27）；`to-questionnaire.md` 已改成「规则见 README」 | `grep` 于 `mmw-v2/merge-notes/*.md` | 已核实 |
| S17 | `SKILL-SET-RULES.md` 与 `REVIEWING-A-SKILL-SET.md` 在上游 subtree 的 `writing-for-agents/` 目录里，上游没有这两份文件（squash `5b1a4c51` 的树里只有 `SKILL.md`、`SKILL-MECHANICS.md`、`agents/openai.yaml`） | `git ls-tree 5b1a4c51`；`merge-notes/writing-for-agents.md` | 已核实：它们已经是 R4 d 类说的「上游目录旁新加的文件」 |
| S18 | SSR `### Paths and host neutrality` 写的检查是一次人工 `grep`，范围是「every `SKILL.md`, description and reference」 | SSR 第 120 行 | 已核实：`mmw/playbooks/`、`mmw/principles/` 两种新文件不在这个范围里 |
| S19 | 词表里没有 `playbook`、`principle` 两个词；已有 **permission mode** 词条、`MMW_CATALOG_MODE`，`install.sh` 自称有「两种模式」 | `grep` 于 `docs/contexts/*/CONTEXT.md` 与已装技能 | 已核实：裸词 **mode** 会与现有用法撞车 |
| S20 | `CODING_STANDARDS.md` `## State and configuration` 第 4 条写「a conflict or a red check becomes `ticket.bounced` for triage」；ADR 0027 定的是同一夜第一次 bounce 回 `ready-for-agent`，第二次才进 `needs-triage` | 两文件原文 | 已核实（N11 contradictions 第 3 条成立）；不属架构，见第 10 节 |
| S21 | board 按路径载入五个脚本，`codeversion.py` `LOADED` 里有 `statedir.py`，`TESTING.md` `## Which suites a change needs` 没列它 | `codeversion.py` 第 18–24 行；`supervisor.py` 第 21 行 | 已核实（N8 §4 成立）；不属架构，见第 10 节 |
| S22 | N8 §4 说 `NO_QUESTION` 与 `implement` 第 23 行的出路「基本一致」 | N11 thin_claims 第 1 条；R4 V9 | 不采用。原文两处出路不同，本文以 R4 V9 为准 |

没有读的：`install.sh` 第 460–580、800–895、1110–1230、1300–1600 行的实现体；`relay.py` 队列行的存储格式（关系到要不要迁移，见第 9 节 U-S3）；各 `tests/<name>/` 的测试文件本体（只读了 `run.sh` 与 `test_draft.py` 一段）；`docs/notes/stage-two-shared-experience-layer.md` 只读了前 30 行，以及用 grep 找出的引用它的位置。

---

## 2. 归置表

列：现在位置 → 新位置与层｜动作｜具体小节｜收益（只列用户要求 2 的六种，附证据）｜体量｜被取代的旧规则与原意怎样保住｜批次。「批」指 R4 第 11 节的四批。

### 2.1 宿主级提示：`mmw-v2/prompt/`

| # | 部件 | 新位置与层 | 动作 | 收益 / 不动理由 | 体量 | 旧规则 | 批 |
|---|---|---|---|---|---|---|---|
| P1 | `shared.md` 全文 | 原位；宿主级提示，不属 MMW 任何一层（R4 §12 末段） | 不动 | 它是 owner 对所有项目的规则（R4 §13 第 3 问）。第 1–5 条就是 pstack mode `## Autonomy`、`## Writing the reply` 在 MMW 里的对应物（N8 §9.2 第 5 条），`mmw` 不复述。第 11 行把无人会话的问与报交给「its skills」，新架构下去处就是角色操作文件，句子本身仍然成立 | 0 | ADR 0014 的两条理由都保留 | — |
| P2 | `shared.md` rule 11 | 同上 | 不动；由原则 `rerun-dont-reroute` 的 `**Boundaries:**` 在 MMW 内划界 | 消除一处已核实的冲突：rule 11 与 `ui-acceptance` 规则 4、5、`implement`「fault 后 stop」方向相反（N9 §9.3 第 1 条）。划界只写在原则文件里，`shared.md` 一字不改 | 0 | — | 3 |
| P3 | `hosts/{claude,codex,grok,pi}.md` | 原位 | 不动 | 不承载 MMW 路由：`hosts/claude.md` 为空，而按宿主分开写违反 SSR `### Paths and host neutrality` | 0 | ADR 0007 | — |
| P4 | `render.py`、`prompt/README.md`、`prompt/tests/` | 原位；安装机制 | 不动 | 与分层无关；首行哈希只由 `render.py` 写、只由它认（N8 §8） | 0 | — | — |

### 2.2 安装：`install.sh`、`skills.txt`

| # | 部件 | 新位置与层 | 动作 | 具体改什么 | 收益（证据） | 体量 | 旧规则与原意 | 批 |
|---|---|---|---|---|---|---|---|---|
| I1 | `install.sh` 技能安装主循环（第 143–230 行）、`stale_links`、retired 位置 | 原位 | 不动 | — | 装 `mmw` 与分叉只需改 `skills.txt`：整目录软链带上子目录；已是本仓软链的由 `ln -sfn` 重指（S3） | 0 | ADR 0006 | — |
| I2（已被 R12 K-32 改定） | `install.sh --check` | 原位；新加一个检查项 | 改写（加一项） | 另起一段，列出 `$HOME_DIR/.mmw/state/*/watches.json` 里开着的 watch：一行一个，写仓库、watch 键、`at`。读法调用 `relay.py` 的 `read_watches`，按路径 import，和 `install.sh` 已经按路径用 `models.py` 的做法一样，不在 bash 里重写一遍判定。**不改退出码**；措辞避开 S6 那组过滤词，所以开夜时同仓库另一个 watch 不会被当成安装问题印出 | 消除已核实的断点（S8）：`AGENTS.md` `## Gotchas` 第一条要求第三步等所有 watch 关掉，却没有任何命令能看到哪些 watch 开着 | +约 20 行 | Self-hosting boundary 的原文不改；这一项只把「看得见」补上。它只报告不拒绝，理由是 `dispatch.sh check` 每夜都会跑 `--check`（S6） | 1 |
| I3 | `install.sh` 头注释（九样） | 原位 | 不动 | — | 安装的种类不变 | 0 | — | — |
| I4 | `skills.txt` 的四行 `engineering/{implement,code-review,to-spec,to-tickets}` | 原位 | 改行成 `self/<名>` | 只改这四行，头注释不改 | 让上游回到原文（R4 C10、V11） | 0 | `merge-notes/README.md` `## 本仓自有正文的技能` 被取代，见 M1 | 2 |
| I5 | `skills.txt` 新行 `self/mmw` | 原位 | 新建一行 | — | 给今天无处安放的内容一个家（R4 C1：B1、B3、B5 只在未安装的 `ask-matt` 里） | +1 | SSR 事实 7「MMW ships no router skill」废止，原意见 T4、T5 与第 4 节 | 3 |

### 2.3 角色配置：`~/.mmw/models.json`、`models.py config`

| # | 部件 | 新位置与层 | 动作 | 理由 | 批 |
|---|---|---|---|---|---|
| R1 | `models.json` 的结构与四行 `junior-worker`、`senior-worker`、`reviewer`、`advisor`（`models.py` `ALLOWED_AGENTS`，已核实） | 原位；「角色 = 启动提示词点名的技能 + `models.json` 一行」的那一行（R4 §12） | 不动 | 已经是 pstack `pstack-models.mdc` 的对应物，并且由脚本显式读取（L7 D.4 指出 pstack 没有脚本解析它的文件）。新架构没有新角色：`mmw` 会话与 orchestrator 都由人启动，没有行 | — |
| R2 | `models.py config`、`dispatch/references/editing-models.md` | 原位 | 不动 | 唯一写入口（ADR 0024），与分层无关 | — |

角色与操作文件的对应（事实，出处 `dispatch.sh` 第 1949、1967、2072 行与 `models.py` 第 31–32 行）：

| 角色 | `models.json` 行 | 启动提示词 | 操作文件 |
|---|---|---|---|
| worker | `junior-worker` / `senior-worker` | `Use the implement skill to work ticket #<n>. …` | `implement`（第 2 批分叉到 `mmw-v2/skills/implement/`） |
| reviewer | `reviewer` | `Use the code-review skill to review ticket #<n> …` | `code-review` 的 `references/session.md` |
| advisor | `advisor` | `Use the advisor skill.` | `advisor` 的 `references/advising.md` |
| orchestrator | 无（人启动） | 无 | `dispatch` 的 `references/night.md`、`one-ticket.md` |
| 人启动的一件事 | 无 | 无 | `mmw`，再到 `playbooks/idea-to-tickets.md` |

### 2.4 任务板 `mmw-v2/board/` 与迁移 `mmw-v2/migrations/`

| # | 部件 | 动作 | 理由 |
|---|---|---|---|
| B1 | `board/` 全部（`supervisor.py`、`server.py`、`board_data.py`、`settings_api.py`、`gates.py`、`codeversion.py`、`page/`、`AGENTS.md`） | 不动 | board 按路径载入的五个脚本（S21）都不在这次改动里。角色指针表与锚点常量模块放在 `dispatch/scripts/`，只要 `events.py`、`issue_tree.py`、`ghlist.py`、`models.py`、`statedir.py` 不 import 它们，board 就不受影响（推断，实现时由 `check_module_paths.py` 与 board 套件确认） |
| B2 | `migrations/remove-verifier.py` | 不动 | 一次性迁移，与分层无关 |
| B3 | 新迁移 | 不建 | 四批都不改 tracker 上的事件，也不改 `models.json`。唤醒文字和 `RESUME:` 是运行时生成的；提升只在没有 watch 开着时做，relay 随最后一个 watch 结束（`relay.py` 头注释 `relay.json` 一行）。旧格式的队列行是否可能跨过一次提升留下来，见第 9 节 U-S3 |

### 2.5 测试与 lint：`mmw-v2/tests/`

| # | 部件 | 新位置与层 | 动作 | 具体改什么 | 收益（证据） | 体量 | 旧规则与原意 | 批 |
|---|---|---|---|---|---|---|---|---|
| T1 | 12 个 `run.sh` 头部的三行 | `mmw-v2/tests/lib/shared_lints.sh`（新） | 合并 | 新脚本按顺序跑全部共用检查，任何一个失败就以非 0 退出；每个 `run.sh` 的三行换成一行调用它。`check_own_skill_frontmatter.py` 与 `check_wiring.py` 在它里面用 `uv run` 跑 | 去掉一处 grep 核实的真重复（S1：36 行、12 个文件）；让以后加检查只动一处（加 `check_wiring.py` 就是第一次）；被 13 个 `run.sh` 加上直接调用两类调用方复用（见 A1） | 新文件约 15 行；`run.sh` 共减 24 行 | 无旧规则被取代 | 1 |
| T2（已被 R12 K-44 改定） | 新文件 `tests/lib/check_wiring.py` | 与 `check_module_paths.py` 同层；由 `shared_lints.sh` 跑 | 新建 | R4 D3.6 的第 1–5 类：第 1、2 类在第 1 批，第 3 类在第 2 批，第 4、5 类在第 3 批。在 `uv run` 下跑，因为第 3 类要解析 frontmatter 与 `agents/openai.yaml`。已装技能的解析按路径复用 `check_own_skill_frontmatter.py` 的 `installed_skill_md_paths` 与 `frontmatter_text`，不写第二个 `skills.txt` 解析器。第 4 类扫全部已装技能的 `.md`，找两种原则引用写法（R4 D4.1），然后断言三件事：每个被引用的 slug 都有文件；每个文件在 `mmw` `## Principles` 里都有一行；`## Principles` 的每一行都有文件 | 消除已核实断点的复发：V7（`MMW turn guard:` 没有处理行）会被第 2 类抓到，V10（`RESUME:` 的 docstring 漂移）会被第 1 类抓到。第 3 类取代 `merge-notes/README.md` 手写的 7 个名单，去掉重复（S16）。第 4、5 类是废止「no router」时保住原意的条件：原意是路由表会漂移（R4 §9，`ask-matt` 的漂移） | 约 250 行（推断） | SSR 事实 7「no router」的原意由第 3–5 类保住；SSR `## Editing`「A fix that adds a mechanism names the run in which the failure occurred」：第 1–3 类各有已核实的断点，第 4、5 类没有失败过的运行，它们的依据是事实 7 被废止这个决定本身 | 1–3 |
| T3 | `check_own_skill_frontmatter.py` | 原位 | 改写（加一条） | 加一条：frontmatter `name` 等于技能目录名 | 消除断点（R4 K7：同名技能静默撞车）。`install.sh` 已按目录名查重（S3），加上这条，重名检查就覆盖到宿主看到的 `name`；今天 35 个全部一致（S4），所以加进来不会报出存量问题 | 约 +8 行 | 取代 R4 D3.6 第 6 类「在 `check_wiring.py` 里另查」，原意（名字不撞）保住 | 1 |
| T4 | 新套件 `mmw-v2/tests/lints/`（`run.sh` + 测试） | 第 13 个套件 | 新建 | 为 `check_wiring.py` 每一类放一个能让它失败的反例，外加 T3 新加的那一条。夹具用临时目录里造的小技能集，不读真实技能 | 给今天无处安放的内容一个家：`lib/` 不是套件（`tests/AGENTS.md` 第 8 行），现有三个检查没有任何测试（S2）。ADR 0008 `## Consequences` 要求新增闸口跑一遍失败路径 | 约 200 行（推断） | — | 1 |
| T5 | relay 测试里对 `send.sent` 与唤醒文字的相等断言（R4 V5：`tests/relay/test_relay.py` 第 365、436 行等） | 原位 | 改写（属 dispatch 单元的提交，依据在本单元） | 改成首行断言 `#<n> <event>`，第二行与指针表常量比较，不在测试里抄一份指针字面 | 消除冲突（S12）：把措辞钉进测试违反 `TESTING.md`；与常量比较时，以后改措辞不必改测试 | 与 R4 相同 | `TESTING.md` 原句不变，见 K1 | 1 |
| T6 | `tests/AGENTS.md` `## Key Conventions` 第 2 条（「`lib/` is not a suite: `-k` parsing … and the unittest verdict …」）与首段 | 原位 | 改写一句 | 加上：`lib/` 另放 `shared_lints.sh` 与它跑的检查 | 消除已核实的遗漏：N8 §4 最后一行指出这段没提三个检查，本轮读原文第 3、8 行确认 | +1 句 | — | 1 |
| T7 | `check_module_paths.py`、`check_upstream_em_dashes.py`、`parse_k.sh`、`run_unittests.py`、各套件的测试本体、`prompt/tests/` | 原位 | 不动 | 与分层无关。分叉后，四个技能的文字离开 `upstream/skills/`，自动不再受 em-dash 检查约束；它们成了自有技能，适用 SSR 的规则 | 0 | — | — |

### 2.6 维护记录：`mmw-v2/merge-notes/`、`mmw-v2/downstream-notes/`

| # | 部件 | 新位置与层 | 动作 | 具体小节 | 收益（证据） | 体量 | 旧规则与原意 | 批 |
|---|---|---|---|---|---|---|---|---|
| M1 | `merge-notes/README.md` `## 本仓自有正文的技能` | 同文件，新节 `## 分叉的技能` | 废止并改写 | 一张表：技能名、上游路径、分叉起点（squash 提交）、说明文件。规则写成：每次拉上游都读这四个技能的上游 diff，按判断移植；不再做「自动合进来的上游段落也改回本仓的」这一步 | 让上游回到原文；那一步手工操作会悄悄撤掉改动，分叉后不再需要 | 5 行换约 10 行 | 原意（拉上游时不让本仓正文被覆盖）由「分叉技能不在 subtree 里」保住 | 2 |
| M2 | `merge-notes/README.md` `## disable-model-invocation` | 原位 | 改写 | 保留第一段「两处同增同删」。第二段的手写 7 名单与「上游默认模型可触发」换成推导规则：被 `mmw` `## Routes`、`mmw/playbooks/` 的一步、角色操作文件或 `dispatch.sh` 启动提示词按名调用 → 两个开关都去掉；否则保持上游设置；「告诉用户运行 `/X`」不算调用；由 `check_wiring.py` 第 3 类检查 | 去掉真重复（S16）；名单由检查维护，不再手写 | 行数约持平 | 原意（不抢触发、夜里不被误触发、不往产品根写文件）保住：今天的推导结果与现状相同（R4 D1.3） | 2 |
| M3 | 六份 merge-note 的开关行：`implement.md` 24、`to-spec.md` 12 与 41、`to-tickets.md` 15 与 50、`triage.md` 15 与 36、`wayfinder.md` 11 与 27 | 原位 | 删除或合并 | 三个分叉技能的开关行删除（自有技能没有开关）；`triage`、`wayfinder` 各自的两行合成一行「按 README 的推导规则，被调用，两处都去掉」，写法照 `to-questionnaire.md` 第 11、19 行 | 去掉 grep 核实的真重复（S16） | 约 −6 行 | 同 M2 | 2 |
| M4 | `implement.md`、`code-review.md`、`to-spec.md`、`to-tickets.md` 四份说明的其余内容 | 原位，由 M1 的表链接 | 不动，只改「源目录」行 | — | 不动的理由：分叉后，它们仍是「本仓各段为什么这样写」的唯一记录，唯一读者是移植上游 diff 的人 | 各改 1 行 | — | 2 |
| M5 | 新文件 `merge-notes/ask-matt.md` | `merge-notes/`，按上游来源命名 | 新建 | 写明三件事：`mmw/references/phase-boundaries.md` 取自上游 `engineering/ask-matt/PHASE-BOUNDARIES.md`，只有宿主中立的改写（R4 V13，a 类）；`mmw` 的 `## Head judgement` 与 `idea-to-tickets` 的 Context hygiene 门槛出自残留目录里本仓写的段落，不是上游文字；上游再改 `PHASE-BOUNDARIES.md` 时怎么取舍 | 给今天无处安放的内容一个家：残留 `ask-matt` 的改动没有 merge-note（R4 V13） | 约 +12 行 | — | 3 |
| M6 | `triage.md`、`wayfinder.md` 里以 `ask-matt` 为出处的行 | 原位 | 改写 | 改指 `mmw` | 消除已核实的断点（R4 B10、B11：指向一个没安装的技能） | 各 1 行 | — | 3 |
| M7（已被 R12 K-50 改定） | `merge-notes/README.md` 新节 `## 旁加的文件` | 同文件 | 新建 | 列出本仓在上游技能目录旁加的、上游没有的文件：已有的 `writing-for-agents/SKILL-SET-RULES.md` 与 `REVIEWING-A-SKILL-SET.md`（S17），以及第 4 批 d 类新加的文件（`prototype` 叶子目录形状、`UI.md` 的 state list，R4 D5.3）。规则：拉上游不会冲突；上游自己加了同名或同主题的文件就读它，重合部分以上游为准 | 让以后加外来技能时不必改现有文字（d 类有了固定去处，第 4 批以及以后从 pstack 引入的技能都照此办）；给现有两份本仓文件的身份一个总的家（今天只写在 `writing-for-agents.md` 里） | 约 +8 行 | SSR `### Upstream skills`「Connect outside the upstream text first」由这一节落到具体位置 | 4 |
| M8 | 第 4 批 c 类句子移走后受影响的条目：`wayfinder.md`、`triage.md`、`improve-codebase-architecture.md`、`grill-with-docs.md`、`prototype.md` | 原位 | 改写 | 每个条目只记留下的 e 类部分；「点名下一步」的那部分从条目里删掉 | 让上游回到原文的记录跟上实际 | 约 −5 行 | — | 4 |
| M9 | `merge-notes/README.md` `## 上游更新时怎么用`、`## host 中立`，以及其余说明 | 原位 | 不动 | — | a 类规则与各技能的 e 类记录，照旧 | 0 | — | — |
| D1 | `downstream-notes/README.md` 与全部说明 | 原位 | 不动 | — | 四批都不会让消费仓库的 screen contract、票的 `CHECK:` 或 `.mmw/target.json` 失效。消费仓库 `AGENTS.md` 要加的那一行由 `dispatch.sh check` 的警告送到，是机制；触发范围不需要为它扩大 | 0 | — | — |

### 2.7 根 `AGENTS.md`

| # | 小节 | 动作 | 具体改什么 | 收益（证据） | 体量 | 批 |
|---|---|---|---|---|---|---|
| A1 | `## Commands` 的 `bash mmw-v2/tests/<name>/run.sh` 一行 | 改写 | 套件从「twelve」改为「thirteen」，加上 `lints`；删掉逐个检查的描述，改成「Every `run.sh` first runs `mmw-v2/tests/lib/shared_lints.sh`; each check's docstring states what it catches」。另加一行命令：`bash mmw-v2/tests/lib/shared_lints.sh`，用于只改了技能文字的改动 | 去掉 N8 §4 核实的真重复（这一行、toolbox **shared lints**、各检查 docstring 三处描述同一组检查）。只改技能文字的改动也有了一条最小的验证命令（`shared.md` rule 15），今天必须跑整个套件才顺带跑到这些检查 | 约 −40 词 | 1 |
| A2 | `## Commands` 的 `install.sh --check` 一行 | 改写（加半句） | 「…and lists every watch open on this machine」 | 同 I2 | +1 句 | 1 |
| A3 | `## Gotchas` 第一条（四个 promotion steps） | 改写一句 | 第三步前加：先跑 `bash mmw-v2/install.sh --check`，它不列出开着的 watch 时才移动已安装 checkout | 同 I2（S8）。原文「The third step waits while any watch is open」原样保留 | +1 句 | 1 |
| A4 | `## External References` night runbook 一行的 File 列 | 改写 | 从 `mmw-v2/skills/dispatch/references/night.md` 改成「the `dispatch` skill's `night.md` reference」 | 消除已核实的冲突（S15）：同一文件的 Self-hosting boundary 要求运行时只读已安装副本，这一行却把本仓里开夜的 orchestrator 指到主工作树的副本。按 S11，新写法能通过 `check.sh`。修改 `night.md` 的维护者仍然按技能目录找到它 | 0 | 1 |
| A5 | `## External References` 新行：指向 `mmw` 技能 | 新建 | Need 列写触发情境（「a task a person brings to this repository, with no skill named; a session whose context was compressed」）；File 列写「the `mmw` skill」，不写路径 | 给 `mmw` 的加载一个家（R4 D1.4）。本仓自己也是消费仓库（`AGENTS.md` 第 5 行）。File 列不写路径的理由同 A4 与 S11 | +1 行 | 3（在 `mmw` 随一次发布进入已安装 checkout、且 owner 授权跑过 `install.sh` 之后，R4 K6） |
| A6 | `## External References` 第 1 行「six bounded contexts」 | 改写 | 改为「seven」 | 消除已核实的冲突（S14）；同一张表在第 3 批正要改，顺带改 | 0 | 3 |
| A7 | 开头四段、`## Self-hosting boundary`、`## Package Manager`、`## Key Conventions`、`## Gotchas` 第 2–5 条、两个 important-if 块、末行 | 不动 | — | 见第 6 节 | 0 | — |

### 2.8 `CODING_STANDARDS.md`、`TESTING.md`

| # | 小节 | 动作 | 具体改什么 | 收益（证据） | 体量 | 旧规则与原意 | 批 |
|---|---|---|---|---|---|---|---|
| C1 | `## Skills and scripts` 第 1 条的列举 | 改写 | 「`SKILL.md`, reference files, `scripts/<…>`」→「`SKILL.md` and the files it names: references, the `mmw` skill's playbooks and principles, `scripts/<…>`」 | 消除冲突（S13）：原列举读起来是穷尽的，Standards axis 照它会把 `playbooks/`、`principles/` 判为不该放进技能目录 | 约 +8 词 | 原意（技能目录只放持有技能的 agent 读或跑的东西）不变 | 3 |
| C2 | `## Skills and scripts` 新加一条 | 新建 | 「A name a script prints for an agent to find in a skill's text (a step name, a heading, a skill file) comes from one constants module and is checked by `mmw-v2/tests/lib/check_wiring.py`; the script never types it as a literal」 | 给今天没有家的规则一个家：写脚本的人和 Standards axis 都读这个文件。R4 把这句放在 SSR `### Scripts and judgement`，本文不采用：SSR 的读者是写技能文字的人，他们改标题时由 lint 的拒绝文字给出路，SSR 不必再写一份 | +1 条 | 取代 R4 §9 表「`### Scripts and judgement` 新增一句」；原意（锚点受核对）由 lint 本身保住 | 1 |
| C3 | `## State and configuration` 五条 | 不动 | — | 与分层无关；第 4 条与 ADR 0027 的冲突（S20）另开票 | 0 | — | — |
| K1 | `TESTING.md` `## What a test proves` | 改写（加一句） | 段末加：「A check that a name a script prints exists in the file it names is wiring, run by `check_wiring.py`; a test compares such output with the constant it comes from, never with a literal copy.」 | 消除已核实的冲突（S12）：不加这句，Tests axis 会把新 lint 和 T5 的断言判成违规 | +1 句 | 原意（测试不钉措辞）保住，而且更严格：T5 连指针字面也不抄 | 1 |
| K2 | `TESTING.md` `## Which suites a change needs` | 改写（加一条） | 加：角色指针表与锚点常量模块由多个脚本按路径载入，改它们要连跑 `dispatch`、`relay`、`liveness`、`verify-ticket`、`lints` 五个套件。这份载入者清单是推断，实现时按实际 import 改 | 消除断点：一个被多处按路径载入的模块，改了却只跑一个套件，就会漏掉别的载入者；这和现有的 board 那条是同一个理由 | +1 条 | — | 1 |
| K3 | `TESTING.md` `## Layout` | 不动 | — | 新套件 `tests/lints/` 符合现有布局 | 0 | — | — |

### 2.9 词表：`CONTEXT-MAP.md` 与 `docs/contexts/`

| # | 位置 | 动作 | 具体改什么 | 收益（证据） | 体量 | 批 |
|---|---|---|---|---|---|---|
| X1 | ticket-run `**\`NOT_READY:\`, \`READY:\`, \`RESUME:\`, \`CARRIED:\`**` | 改写 | `RESUME: step <k> (<event>)` 改成印步骤名的形式（R4 D3.5 a） | 词条跟着 `_Home_` 走（`CONTEXT-MAP.md` 第 3 行：两者不一致时以 `_Home_` 为准） | 约 0 | 1 |
| X2 | night **wake**；`night/how-it-works.md` 第 31 行 | 改写 | 「`#<n> <event>`, which says only where to look」改成「`#<n> <event>` and one **role pointer** line」 | 同上（R4 D1.2） | 约 +10 词 | 1 |
| X3 | night 新词条 **role pointer**（放在 **wake** 旁边） | 新建 | 定义：脚本送进活会话的每条消息末尾那一行，只写技能名、技能内文件与标题，由 `dispatch/scripts/` 里的一张表生成；Distinct from **wake**，也 Distinct from `RESUME:` | 给新词一个家。R4 把它放进 toolbox，本文改放 night：它的邻词 **wake** 和 `_Home_`（`dispatch/scripts/`）都在 night context，「Distinct from」只有在同一 context 里才写得出来 | +3 行 | 1 |
| X4 | toolbox **shared lints** | 改写 | 「The checks `mmw-v2/tests/lib/shared_lints.sh` runs before every suite's own tests」；`_Home_` 改为 `shared_lints.sh`；删掉逐个检查的描述 | 去重复（N8 §4；`CONTEXT-MAP.md` 第 5 行：词条不复述 `_Home_` 能读到的东西） | 约 −30 词 | 1 |
| X5 | toolbox 新词条 **fork** | 新建 | 一个上游技能，上游的行已不到一半，搬进 `mmw-v2/skills/<同名>/`；上游那一份恢复原文、不安装；`_Home_` 为 `merge-notes/README.md` `## 分叉的技能` | 给新词一个家 | +3 行 | 2 |
| X6 | toolbox **upstream skill** | 改写 | 加「Distinct from **fork**」 | 划清边界 | +4 词 | 2 |
| X7 | toolbox **`disable-model-invocation` pairing** | 改写 | 加一句推导规则，`_Home_` 不变 | 词条跟着 `_Home_` 走 | +1 句 | 2 |
| X8 | 79 处 `_Home_` 与路径：tickets 57、ticket-run 19、toolbox 2、ui-acceptance 1（S9） | 改写 | `mmw-v2/upstream/skills/engineering/<名>/` → `mmw-v2/skills/<名>/`，和搬家在同一次提交里 | 消除断点：`_Home_` 是权威出处，路径一断，词条就查不到出处 | 0 | 2 |
| X9 | toolbox 新词条 **`mmw`**、**playbook**、**principle** | 新建 | 词条名用字面 `mmw`，不用裸词「mode」（S19：**permission mode**、`MMW_CATALOG_MODE`、`install.sh` 的两种模式都已占用这个词），定义里写「the set's one mode」，并 Distinct from **permission mode**。**playbook** 同时覆盖头部 playbook 和角色操作文件两种。**principle** 写明它是文件，不是技能 | 给新词一个家（SSR `### Vocabulary`：一词一义） | +9 行 | 3 |
| X10 | `CONTEXT-MAP.md` `## Contexts` 的 Toolbox 一行 | 改写 | 范围里加「the `mmw` skill, its playbooks and principles」 | 目录跟上内容 | +8 词 | 3 |
| X11 | toolbox **"Hand the decision on"** | 改写或删除 | 跟着 `improve-codebase-architecture` `### 4` 的 c 类拆分走（R4 D5.3）：只剩「This skill changes no code」时，词条改成描述这一句；那一节被整个移走时，删除词条 | 词条跟着 `_Home_` 走 | 约 ±3 行 | 4 |
| X12 | 其余词条、`CONTEXT-MAP.md` 的读法与关系段 | 不动 | — | 与分层无关 | 0 | — |

### 2.10 决定记录：`docs/adr/`、`docs/notes/`

| # | 部件 | 动作 | 具体内容 | 收益（证据） | 体量 | 批 |
|---|---|---|---|---|---|---|
| D2 | 新 ADR 0032 | 新建，`amends: [0020]` | 标题的意思：脚本送进活会话的文字，只按名字指向技能文本，加一行由表生成的角色指针；这些名字由 lint 核对。Considered Options 写 R4 §4 里被放弃的备选：只靠 `AGENTS.md`、description 当触发词、宿主钩子注入、`RESUME:` 保留编号 | 给这个决定和被否决的方案一个家（`docs/adr/README.md` 规定决定写在 ADR 里） | 约 35 行 | 1 |
| D3 | 新 ADR 0033 | 新建，`amends: []` | 标题的意思：上游技能按改动多少分两种处理。上游行已不到一半的，分叉为同名自有技能；其余留在 subtree，调用开关由「是否被按名调用」推导。Considered Options 写 R3 的恢复上游开关（V1 断链）和 R2 的分叉时改名 | 同上 | 约 35 行 | 2 |
| D4 | 新 ADR 0034 | 新建，`amends: []`（引用 ADR 0014 作为不写进 `shared.md` 的理由，不修改它） | 标题的意思：MMW 有一个 mode，即 `mmw` 技能；playbook 与原则是它目录里的文件；由消费仓库 `AGENTS.md` 的一行负责加载。它取代 SSR 事实 7 的「MMW ships no router skill」。Consequences 记 T1 的实测结果（带日期），第 4 批以此为前提 | 同上；T1 这类实测，按 SSR 沉积表应当写进脚本头，`mmw` 没有脚本，所以这个 ADR 是它唯一的去处 | 约 40 行 | 3 |
| D5 | `docs/adr/README.md` 索引表 | 改写 | 加三行；0020 的「被哪几份改写」一格加 0032 | 索引手工维护（README 首句） | +3 行 | 1–3 |
| D6 | 现有 31 份 ADR 的正文 | 不动 | 包括 0012 里那一处上游路径（S9）和 0008、0012 里已失效的 `refusal.py` 路径 | ADR 记的是当时的决定（`shared.md` rule 13 的例外），变化另写新 ADR | 0 | — |
| D7 | `docs/notes/stage-two-shared-experience-layer.md` | 只改路径 | 头段两处 `mmw-v2/upstream/skills/engineering/implement/SKILL.md` → `mmw-v2/skills/implement/SKILL.md` | 消除断点（S9）；设计说明其余内容不动 | 0 | 2 |

与 R4 的差异：R4 §9 写的是「另写一份新 ADR」。本文拆成三份，理由见第 0 节第 9 条。这是新增的决定记录，不是拆散 MMW 的内容。

### 2.11 消费仓库的私有组件

| # | 部件 | 新位置与层 | 动作 | 理由 | 批 |
|---|---|---|---|---|---|
| Q1 | 消费仓库 `.mmw/`（`target.json`、`harness/`、`journeys/`、`stories/`，本仓根 `.mmw/` 为实例）、screen contract、`prototypes/`、`docs/agents/*.md`、`CODING_STANDARDS.md`、`TESTING.md` | 原位；消费仓库私有组件，只能是数据与仓库规则（R4 D7.6） | 不动 | 四批都不改它们的格式（D1） | — |
| Q2 | 消费仓库 `AGENTS.md` `## External References` 的 `mmw` 行 | 同 A5 | 新建一行 | 写法同 A5：File 列写「the `mmw` skill」（S11：写成路径会在消费仓库被 `check.sh` 判为不存在）。三处保证它存在：人在场时 `mmw` 的 `## Where you are` (c) 行补上它；`dispatch.sh check` 缺行时只读地警告；`manage-agents-md` 重写 `AGENTS.md` 时会不会保留这一行，要实测（第 9 节 U-S2）。按 manage-agents-md 第 204 行的规矩，这是一个情境对一个技能，不是「list of installed skills」 | 3 之后 |

---

## 2A. 新组件怎样被安装、测试、检查

| 组件 | 安装 | 冻结 | 测试 | 检查 |
|---|---|---|---|---|
| `mmw/SKILL.md` | `skills.txt` 加 `self/mmw`，`install.sh` 软链整个目录到 `~/.agents/skills/mmw` 与 `~/.claude/skills/mmw`；需要 owner 授权跑一次 `install.sh`，`--check` 为 0 才算装好 | 随已安装 checkout 冻结（Self-hosting boundary 已包括「its skills」，原文不用改） | 没有脚本，所以没有套件（同今天的 `advisor`）。行为由 SSR `## Verifying` 的走查证明（R4 T1、T2、T8），结果记进 ADR 0034 | `check_own_skill_frontmatter.py`：只有两个键，`name` 等于目录名；`check_wiring.py` 第 3、5 类 |
| `mmw/playbooks/*.md` | 随目录软链 | 同上 | 无 | `check_wiring.py` 第 5 类（`## Routes` 与文件一一对应）、第 3 类（步骤里按名调用的技能都已装，且两个开关都不在）；SSR `### Paths and host neutrality` 的人工 grep 范围扩到 playbook 与原则（S18） |
| `mmw/principles/*.md` | 随目录软链。它们不是 `SKILL.md`，宿主不扫描，不进技能列表，没有常驻开销（推断，依据 `install.sh` 头注释「只有 frontmatter 的 description 是 host 启动时扫的」；T1 时顺带看一眼技能列表确认） | 同上 | 无 | `check_wiring.py` 第 4 类（引用、文件、索引三方一致）。它还顺带管住顺序：某个技能在第 3 批之前先引用了原则，lint 就失败 |
| `mmw/references/phase-boundaries.md` | 随目录软链 | 同上 | 无 | 来源记录在 `merge-notes/ask-matt.md`（M5）；不在 `upstream/skills/` 下，em-dash 检查不管它 |
| 角色指针表、锚点常量模块（`dispatch/scripts/`，属 dispatch 单元） | 随 `dispatch` 目录 | 同上；和引用它的脚本在同一个提交里 | `dispatch`、`relay`、`liveness`、`verify-ticket` 套件；`lints` 套件的反例 | `check_wiring.py` 第 1、2 类；`check_module_paths.py` 管按路径载入 |
| `check_wiring.py`、`shared_lints.sh`、`tests/lints/` | 不安装：`tests/` 只存在于 checkout | 不参与运行 | `tests/lints/` | 自己由 `shared_lints.sh` 在每个套件里先跑 |
| 消费仓库 `AGENTS.md` 的 `mmw` 行 | 不由 `install.sh` 装 | 不涉及 | 无 | `dispatch.sh check` 缺行警告（dispatch 单元）；`manage-agents-md` 的 `check.sh` 不会误报（S11） |

## 2B. 哪些非技能部件承担 mode 的常驻规则或原则的出处

| 部件 | 承担的内容 | 对应的 pstack 部件 | 读得到的会话 | 新架构下 |
|---|---|---|---|---|
| `shared.md` 第 1–5 条、第 11 行、rule 11 | owner 的自主边界与回复写法；无人会话怎样套用这些规则 | mode `## Autonomy`、`## Writing the reply`（N8 §9.2 第 5 条） | Claude Code、Codex、Pi、Grok 的每个会话；Cursor 不在内（ADR 0007） | 不动；`mmw` 不复述；rule 11 由原则 `rerun-dont-reroute` 划界 |
| 消费仓库 `AGENTS.md` 的 `mmw` 行 | 触发加载 `mmw` | mode 的 `reminder:` 与 `mode: true`（L7 A.1、E.2） | 读仓库根 `AGENTS.md` 的宿主（T10 待实测） | 新建 |
| 本仓 `AGENTS.md` `## Self-hosting boundary` | 本仓运行安全的常驻规则 | 没有；pstack 反过来，运行中从 trunk 重读组件（L7 0 第 5 条） | 本仓的每个会话 | 正文不动；`--check` 补上「看得见开着的 watch」（I2） |
| `tool-guard.py`、`turn-guard.py` | 票工作树里三条不可越过的规则，以及 orchestrator 不得在 watchdog 不健康时结束回合 | mode `## Non-negotiables` 的一部分，但 pstack 只写成文字 | 五个宿主（提问闸门只在三个宿主上注册，N8 §9.3） | 不动；拒绝文字里的锚点进 lint 第 1 类（dispatch 单元） |
| 启动提示词里的 `AUTONOMOUS`、`PRODUCT_RULES`（属 dispatch 单元） | 无人会话的自主规则 | mode 对子代理的约束 | 所有由脚本启动的会话，包括 Cursor | 不动 |
| `~/.mmw/models.json` | 角色 → host、model、effort | `pstack-models.mdc` | 只由脚本读 | 不动 |
| ADR 0008 | 原则 `silence-is-never-a-pass` 的理由来源 | 原则的 `**Why:**` | 只有维护者（不安装） | 原则文件用自己的话写出理由，带日期的运行事实照写，ADR 编号只作出处标注，**不写 `docs/adr/` 路径**：消费仓库没有这个目录（ADR 0012 Considered Options 第 2 条），在本仓写路径又会指向工作树里的副本 |
| ADR 0010、0017、0019、0020 | 原则 `the-tracker-is-the-state` 的来源 | 同上 | 同上 | 同上 |
| ADR 0017、0018（含用户 2026-09-10 否决重试与换 host） | 原则 `rerun-dont-reroute` 的来源 | 同上 | 同上 | 同上 |
| `CODING_STANDARDS.md` `## Skills and scripts` 第 4 条、`## State and configuration` 第 3 条 | 前两条原则在代码一侧的对应规则 | 无 | Standards axis | 不动，也不加原则引用：它已经引 ADR 0008，读者是审代码的人，不需要原则文件 |
| `TESTING.md` `## What a test proves` | 看起来像原则（近 pstack `test-behavior-not-implementation`） | 原则 | Tests axis | 不动，见第 4 节 |

---

## 3. playbook 草图

substrate 单元**不产生 playbook，也不产生角色操作文件**。单元里有两段带顺序的文字，按 R4 §13 第 4、5 问判定后都留在原处：

| 顺序段 | 位置 | 判定 |
|---|---|---|
| 四个 promotion steps | `AGENTS.md` `## Gotchas` 第一条 | 维护者发布的固定流程，单一入口、单一任务，读者只有本仓维护者（L7 C.1 第 7 问）。不做成 playbook；只按 A3 补一句 |
| 拉上游 | `merge-notes/README.md` `## 上游更新时怎么用` 1–4 | 同上；分叉表（M1）加进去之后仍是一个操作文件 |

单元以连线的方式参与别的 playbook（见第 5 节）：

- `idea-to-tickets` 的 **Hand to the night** 交给 `dispatch`，`dispatch.sh check` 再跑 `install.sh --check`；
- `night.md` 的开夜一步经 `dispatch.sh check` 读消费仓库 `AGENTS.md`，缺 `mmw` 行时警告；
- worker 的 `implement` 按票的 `## Read first` 读 `CONTEXT-MAP.md`、`CODING_STANDARDS.md`、`TESTING.md`；
- reviewer 的 Standards axis 与 Tests axis 读 `CODING_STANDARDS.md`、`TESTING.md`。

---

## 4. 原则候选

### 4.1 本单元提供出处的原则（原则本身由 `mmw` 单元建）

| slug | 规则一句 | 本单元里的出处 | 本单元里的实例（不改、不加括注） |
|---|---|---|---|
| `silence-is-never-a-pass` | 一道检查、一次交付不能因为什么都没做而读起来像通过；检查要证明自己能失败；查不了就说查不了 | ADR 0008 全文（「这条规则是从哪一批故障里得出的」：2026-09-05 一夜五处） | `install.sh --check` 的 `没查`；`run_unittests.py` 跳过数非 0 即失败；`check_own_skill_frontmatter.py` 缺 PyYAML 时退出 2；`CODING_STANDARDS.md` `## Skills and scripts` 第 4 条；新套件 `tests/lints/` 的反例测试本身就是它的应用 |
| `the-tracker-is-the-state` | 你在哪一步由票上的事件决定，不由会话记忆决定；要等别人就结束回合，由事件叫醒 | ADR 0010、0017、0019、0020 | `CODING_STANDARDS.md` `## State and configuration` 第 3 条 |
| `rerun-dont-reroute` | 被打断的命令原样重跑；被拒绝就修拒绝点名的事或报 blocked，不绕路、不换 host 或 runner | ADR 0017、0018 | `shared.md` rule 11（「When a step fails or is interrupted, redo it yourself before replying」）由这条原则的 `**Boundaries:**` 划界：重做的是自己被打断的那一步，不是绕开流水线自身的拒绝。原则文件引 rule 11 时，要同时引用原句，不能只写编号：Cursor 会话读不到 `shared.md`（ADR 0007），而且按编号引用正是 L7 C.6 信号 8 说的脆弱写法 |

这些原则的出处都在 `docs/adr/`，不安装。所以原则文件的 `**Why:**` 必须自成一体：写出事实本身（哪一夜、哪一次运行、用户哪天的决定），ADR 编号只放在括号里作维护者的出处标注。这是 SSR `### Load and disclosure`「A rule sits in the text of the agent that must follow it … in a merge-note … reaches no worker」在原则层的应用。

### 4.2 看起来像原则、但留在原处

| 规则 | 位置 | 留在原处的理由（R4 D4.3 的门槛） |
|---|---|---|
| 测试证明脚本行为，不钉文字 | `TESTING.md` `## What a test proves` | 门槛 7 不过：已经有一个家，读者只有 Tests axis 与写 MMW 测试的人；门槛 4 不过：只适用于本仓的测试 |
| 一次运行不接受它自己在改造的版本 | `AGENTS.md` `## Self-hosting boundary` | 门槛 4 不过：只对本仓消费自己流水线时成立；门槛 7 不过：`AGENTS.md` 每个会话都读 |
| hook 只按宿主自己的 payload 判断，不读环境变量 | `AGENTS.md` `## Gotchas` 第 4 条，加上 `install.sh`、两个 hook 头、ADR 0021，共五处（N8 §4） | 绑定具体机制（L7 C.2 第 1 类）；各处是写在执行点上的注释，读者不同 |
| 一个配置只有一个写入口 | `CODING_STANDARDS.md` `## State and configuration` 第 1 条；`models.py` | 已由机制强制（`models.py` 加锁、原子替换）；只有一个领域 |
| 词条只在用户定过或 `_Home_` 证实后才写 | `CONTEXT-MAP.md` 第 7 行 | 只有一种读者（写词条的人） |
| merge-note 给意图不给 diff；没有说明的段落取上游 | `merge-notes/README.md` 开头与 `## 上游更新时怎么用` 第 2 条 | 只在拉上游这一个流程里用 |
| downstream-note 的触发范围 | `downstream-notes/README.md` `## 什么改动必须写一份` | 同上 |
| 脚本头记带日期、钉版本的实测 | `CODING_STANDARDS.md` `## Skills and scripts` 第 4 条第二句 | 只对写脚本的人成立 |
| `shared.md` rules 1–15 | `shared.md` | 门槛 7 不过：owner 自己的全局规则已经有家；R4 §13 第 3 问 |
| 每样东西只有一个家 | SSR 事实 7 | 读者是写技能的人，家就是 SSR |

### 4.3 不加的机械检查（看起来该加，但说不出所列收益）

| 候选 | 不加的理由 |
|---|---|
| lint 查「每条原则至少被两处引用」（R4 D4.3 门槛 5） | 数量能机械地查，但门槛 5 的关键是「每处各是不同的机制」，这要判断；而且说不出一处已核实的断点。第 4 类已经顺带算出引用，不另设失败条件 |
| lint 查 `mmw/SKILL.md` 不超过 100 行 | 没有失败过的运行；R4 T8 本来就要量行数 |
| 把 SSR `### Paths and host neutrality` 的人工 grep 做成脚本 | L7 C.6 信号 4 算是触发了（见第 7 节）。但 SSR `## Editing` 要求新加的机制点名一次它本可以防住的失败运行，这里找不到这样的运行；所以只扩大 grep 的范围（S18） |
| lint 查原则文件的格式（没有 frontmatter，有 `**Why:**`、`**Applies when:**`） | 宿主只扫 `SKILL.md`，格式错了不会造成误加载；也没有失败过的运行 |

---

## 5. 连线

```edges
install.sh -> skills.txt : configured-by
install.sh -> mmw : calls (symlinks the whole skill directory, playbooks and principles included)
install.sh -> implement : calls (re-points the symlink to mmw-v2/skills/implement after the fork)
install.sh -> code-review : calls (same)
install.sh -> to-spec : calls (same)
install.sh -> to-tickets : calls (same)
install.sh -> prompt/render.py : runs-script
install.sh -> models.py : runs-script (first-install defaults, imported by path)
install.sh -> relay.py read_watches : runs-script (--check lists open watches, imported by path)
install.sh -> installed checkout install.sh : hands-off-to (--check from another checkout)
install.sh -> tool-guard.py : configured-by (registers the host hook)
install.sh -> turn-guard.py : configured-by (registers the host hook)
dispatch.sh check -> install.sh : runs-script (--check; full install when this checkout is the installed one)
dispatch.sh check -> consuming AGENTS.md mmw row : reads-reference (read-only warning when missing)
consuming AGENTS.md mmw row -> mmw : routes-to
root AGENTS.md mmw row -> mmw : routes-to
root AGENTS.md -> dispatch night.md : reads-reference (names the skill's reference, not the worktree path)
root AGENTS.md -> CONTEXT-MAP.md : reads-reference
root AGENTS.md -> docs/adr/README.md : reads-reference
root AGENTS.md -> CODING_STANDARDS.md : reads-reference
root AGENTS.md -> TESTING.md : reads-reference
root AGENTS.md -> merge-notes/README.md : reads-reference
root AGENTS.md -> downstream-notes/README.md : reads-reference
root AGENTS.md -> prompt/README.md : reads-reference
root AGENTS.md -> SKILL-SET-RULES.md : reads-reference
root AGENTS.md -> tests/lib/shared_lints.sh : runs-script (text-only change check)
mmw -> consuming AGENTS.md mmw row : hands-off-to (Where you are row (c) adds the missing row when a person is present outside .worktrees/)
host session (claude|codex|pi|grok) -> shared.md : configured-by
render.py -> shared.md : reads-reference
render.py -> prompt/hosts/*.md : reads-reference
mmw -> shared.md : cites-principle (precedence sentence: the user-level instructions outrank the mode)
principle rerun-dont-reroute -> shared.md : cites-principle (Boundaries on rule 11, quoted)
principle silence-is-never-a-pass -> ADR 0008 : reads-reference (maintainer attribution only, never read at runtime)
principle the-tracker-is-the-state -> ADR 0010 : reads-reference (maintainer attribution only)
principle the-tracker-is-the-state -> ADR 0019 : reads-reference (maintainer attribution only)
principle the-tracker-is-the-state -> ADR 0020 : reads-reference (maintainer attribution only)
principle rerun-dont-reroute -> ADR 0018 : reads-reference (maintainer attribution only)
worker role -> models.json junior-worker|senior-worker : configured-by
reviewer role -> models.json reviewer : configured-by
advisor role -> models.json advisor : configured-by
dispatch.sh start -> implement : starts-with-prompt
dispatch.sh start -> code-review : starts-with-prompt
dispatch.sh advise -> advisor : starts-with-prompt
dispatch.sh start -> models.py : runs-script
board settings_api.py -> models.py : runs-script
board board_data.py -> verify-ticket events.py : runs-script (loaded by path)
worker session -> tool-guard.py : enforced-by-hook
reviewer session -> tool-guard.py : enforced-by-hook
orchestrator session -> turn-guard.py : enforced-by-hook
tests/<name>/run.sh -> tests/lib/shared_lints.sh : runs-script
tests/lints/run.sh -> tests/lib/shared_lints.sh : runs-script
tests/lib/shared_lints.sh -> tests/lib/check_module_paths.py : runs-script
tests/lib/shared_lints.sh -> tests/lib/check_upstream_em_dashes.py : runs-script
tests/lib/shared_lints.sh -> tests/lib/check_own_skill_frontmatter.py : runs-script
tests/lib/shared_lints.sh -> tests/lib/check_wiring.py : runs-script
tests/lib/check_own_skill_frontmatter.py -> skills.txt : configured-by
tests/lib/check_wiring.py -> tests/lib/check_own_skill_frontmatter.py : runs-script (imports the installed-skill resolver by path)
tests/lib/check_wiring.py -> skills.txt : configured-by
tests/lib/check_wiring.py -> dispatch anchor constants module : reads-reference (class 1)
tests/lib/check_wiring.py -> dispatch role pointer table : reads-reference (class 1)
tests/lib/check_wiring.py -> implement : reads-reference (class 1 step names; class 2 WORKER handler rows)
tests/lib/check_wiring.py -> dispatch night.md : reads-reference (class 1 headings; class 2 MAIN handler rows)
tests/lib/check_wiring.py -> dispatch relay.py WAKES : reads-reference (class 2)
tests/lib/check_wiring.py -> mmw : reads-reference (classes 3, 4, 5: Routes, Principles)
tests/lib/check_wiring.py -> mmw/playbooks : reads-reference (classes 3, 5)
tests/lib/check_wiring.py -> mmw/principles : reads-reference (class 4)
tests/lib/check_wiring.py -> dispatch.sh start prompts : reads-reference (class 3)
tests/lints/* -> tests/lib/check_wiring.py : runs-script (one counter-example per class)
tests/relay/test_relay.py -> dispatch role pointer table : reads-reference (compares with the constant, not a literal)
code-review Standards axis -> CODING_STANDARDS.md : reads-reference
code-review Tests axis -> TESTING.md : reads-reference
implement -> CONTEXT-MAP.md : reads-reference
implement -> CODING_STANDARDS.md : reads-reference (when ## Read first names it)
CONTEXT-MAP.md -> docs/contexts/*/CONTEXT.md : reads-reference
docs/contexts/*/CONTEXT.md -> mmw-v2/skills/{implement,code-review,to-spec,to-tickets} : reads-reference (_Home_ after the fork)
docs/adr/0032 -> docs/adr/0020 : hands-off-to (amends)
merge-notes/README.md -> implement : reads-reference (fork table)
merge-notes/README.md -> code-review : reads-reference (fork table)
merge-notes/README.md -> to-spec : reads-reference (fork table)
merge-notes/README.md -> to-tickets : reads-reference (fork table)
merge-notes/README.md -> tests/lib/check_wiring.py : enforced-by-hook (derivation rule checked by class 3; not a host hook, the closest listed relation)
merge-notes/ask-matt.md -> mmw references/phase-boundaries.md : reads-reference (source record)
merge-notes/triage.md -> mmw : reads-reference (source of the moved passages)
merge-notes/wayfinder.md -> mmw : reads-reference (same)
```

说明：`install.sh -> <技能> : calls` 用「calls」表示「把技能装上」，`mmw -> consuming AGENTS.md mmw row : hands-off-to` 表示「补写这一行」，`merge-notes/README.md -> check_wiring.py` 用「enforced-by-hook」表示「由检查强制」。这三种都不在给定的关系词里，括注写明了实际关系。

---

## 6. 不动清单

| 部件 | 理由 |
|---|---|
| `mmw-v2/prompt/shared.md` 全文 | owner 对所有项目的规则（R4 §13 第 3 问）；五条读者事实是后面全部规则的理由，是天然的整体（N8 §8）；ADR 0014 否决往里写偶发场景的规则 |
| `prompt/hosts/*.md`、`render.py`、`prompt/README.md`、`prompt/tests/` | 发布路径是一个整体（N8 §8）；不承载 MMW 路由 |
| `install.sh`，除 `--check` 新加的一项 | 装与查是同一段代码的两种模式（N8 §8）；装 `mmw` 和分叉都不需要改代码（S3） |
| `install.sh` 头注释（九样） | 安装的种类不变 |
| `skills.txt` 的头注释与格式 | 只改行 |
| `~/.mmw/models.json` 的结构、`models.py`、`editing-models.md` | 已经是角色配置的唯一写入口，由脚本显式读取；新架构不加角色 |
| `mmw-v2/board/` 全部 | 不读任何被改的东西（B1）；守护、服务、自重启是一个运行单元（N8 §8） |
| `mmw-v2/migrations/`；不建新迁移 | 不改任何存下来的状态（B3） |
| `check_module_paths.py`、`check_upstream_em_dashes.py`、`parse_k.sh`、`run_unittests.py` | 与分层无关；前两个的范围按目录自动跟上分叉 |
| 各套件测试本体（T5 的相等断言除外，那一处归 dispatch 单元改） | 与分层无关 |
| `merge-notes/README.md` `## 上游更新时怎么用`、`## host 中立` 及其余说明（M3、M4、M6、M8 以外） | a 类规则与 e 类记录，照旧 |
| 分叉的四份 merge-note 的正文 | 移植上游 diff 时唯一的意图记录，只有一个读者 |
| `downstream-notes/` 全部 | 四批都不让消费仓库的产物失效（D1） |
| `AGENTS.md` 开头四段、`## Self-hosting boundary`、`## Package Manager`、`## Key Conventions`、`## Gotchas` 第 2–5 条、两个 important-if 块 | 原文已经覆盖新组件（「its skills」包括 `mmw`）；分叉技能照旧由 `skills.txt` 与 merge-notes README 描述，不需要在 Key Conventions 另写一句 |
| `CODING_STANDARDS.md` `## State and configuration` | 与分层无关；第 4 条的冲突另开票（第 10 节） |
| `TESTING.md` `## Layout` | 新套件符合现有布局 |
| `CONTEXT-MAP.md` 的读法与关系段、X1–X11 以外的词条 | 与分层无关 |
| 现有 ADR 正文（包括 0012、0008 里已失效的路径） | ADR 记的是当时的决定，变化另写新 ADR |
| `docs/notes/stage-two-shared-experience-layer.md`，除两处路径 | 设计说明自己声明以代码与技能为准，不复制正文 |
| 消费仓库 `.mmw/`、screen contract、`prototypes/`、`docs/agents/*.md`、`CODING_STANDARDS.md`、`TESTING.md` | 数据与仓库规则，格式不变（R4 D7.6） |
| `tests/AGENTS.md`（T6 以外）、`board/AGENTS.md` | 与分层无关 |
| `SKILL-SET-RULES.md`、`REVIEWING-A-SKILL-SET.md` 的位置 | 已经是上游目录旁新加的文件（S17）；内容的改写归 writing-for-agents 单元；本单元只在 M7 里给它们登记身份 |

---

## 7. 形式拆散自查（L7 C.6 十一个信号）

| # | 信号 | 结果 |
|---|---|---|
| 1 | 没有先确认已有组件是否是合适的归宿 | 未触发。`shared_lints.sh`：12 份逐字相同的副本之外没有别的家。R4 的 lint 第 6 类放进已有的 `check_own_skill_frontmatter.py`，不另开。`install.sh --check` 的新项复用 `relay.py` 的 `read_watches`。锚点那句规则放进已有的 `CODING_STANDARDS.md`，不在 SSR 另写 |
| 2 | 新增内容不改变决定 | 未触发。C1 改变 Standards axis 对 `playbooks/` 的判定；C2 改变写脚本的人用常量还是字面；K1 改变 Tests axis 对 lint 与 T5 的判定；A3 改变第三步之前的动作；A4 改变本仓 orchestrator 读哪份 `night.md` |
| 3 | 重复已有的、位置得当的指引 | 未触发，而且反过来删了几处：A1、X4 去掉共用检查描述的三份副本；M3 去掉开关理由的九处复述；C2 不在 SSR 另写一份 |
| 4 | 本可由机制强制的规则写成了文字 | 部分触发。SSR `### Paths and host neutrality` 的人工 grep 本可以写成脚本，本文只扩大了它的范围，没有改成脚本，理由见 §4.3。反方向：A3 的「等 watch 关掉」原来只有文字，现在有 `--check` 可看 |
| 5 | playbook 只调一个技能 | 未触发：本单元不产生 playbook |
| 6 | reference 每次都读、只有一个调用方 | 未触发：本单元不产生 reference。`merge-notes/ask-matt.md` 是维护记录，不是 reference |
| 7 | 原则说不出改变哪个决定 | 未触发：本单元不产生原则；§4.2 列出了没有做成原则的规则 |
| 8 | 拆完后需要按步骤编号引用 | 部分触发，已处理。A3 在第一条之内引用「the third step」，沿用原文自己的说法（「The third step waits…」），没有跨文件。原则 `rerun-dont-reroute` 引用 `shared.md` 的 rule 11 时同时引原句（§4.1） |
| 9 | 拆出的内容没有第二个调用方、也不减少重复 | 未触发。`shared_lints.sh` 有 13 个 `run.sh` 加直接调用两类调用方；`tests/lints/` 装的是今天无处安放的测试；三份 ADR 各记一个在不同批次落地的决定 |
| 10 | 把单入口的固定流程拆成三层 | 未触发。四个 promotion steps 与拉上游的流程都留作单个操作文件（§3） |
| 11 | 把只在流程之间复用的内容做成能力技能 | 未触发。本单元不新建技能；`mmw` 由 `mmw` 单元负责 |

---

## 8. 待用户决定

只列产品层面的决定：它们改变 owner 看到的东西、改变 owner 怎样用这套工具，或涉及范围。

| # | 决定 | 为什么是你的决定 | 建议 |
|---|---|---|---|
| U-A | 你名下每个消费仓库的 `AGENTS.md` 都要加一行指向 `mmw`（R4 U4）。人在场时，是由 `mmw` 自动补上这一行，还是只由开夜前的 `dispatch.sh check` 提醒、由你来加？ | 它会改动你所有仓库里的 agent 指令文件 | 自动补上。它只在有人在场、且不在票的工作树里时才动；开夜前的提醒作兜底 |
| U-B | 今天 `AGENTS.md` `## Gotchas` 写「`install.sh` runs only when the user explicitly authorises it」，而 `dispatch.sh check` 在本 checkout 就是已安装 checkout、又发现装得不齐时，会自己跑完整的 `install.sh`（S6）。第 2、3 批改了软链目标，下一次开夜就会碰到这种情况。哪一条算数？ | 这是你为自己机器定的规则，两处现在互相矛盾 | 保留自动修复（它只重装已安装 checkout 自己的版本，不会换版本），并把这件事写进那条 Gotcha。如果你要坚持「必须授权」，就得改 `dispatch.sh check`，让它只报告不修 |

R4 第 11 节已列的「第 2、3 批各需要授权跑一次 `install.sh`」照旧，这里不重复。

---

## 9. 未确定

| # | 问题 | 需要什么实测或阅读才能定 |
|---|---|---|
| U-S1 | 宿主是否只把 `<技能>/SKILL.md` 当作技能，而不会把 `mmw/principles/*.md`、`mmw/playbooks/*.md` 也扫进技能列表 | R4 T1 装好之后，在五个宿主上各看一次技能列表：应当只出现 `mmw` 一项 |
| U-S2 | `manage-agents-md` 重写一个已有 `mmw` 行的 `AGENTS.md` 时，会不会因为这一行不来自 survey list 而删掉它（`manage-agents-md/SKILL.md`「every line in every file traces to one survey-list entry」） | 在临时仓库里对带这一行的 `AGENTS.md` 跑一次重写，看这一行是否保留。如果不保留，就要在 `manage-agents-md` 里认这一行（归 manage-agents-md 单元）；在那之前，`dispatch.sh check` 的警告能兜住 |
| U-S3 | relay 队列行存的是事件名还是渲染好的文字；如果是文字，一次提升前后留下的旧行，会不会以旧格式（没有指针）送出 | 读 `relay.py` 的 `queue` 与 `ack_wake` 的行格式。提升只在没有 watch 时做，relay 也随最后一个 watch 结束，所以推断不需要迁移 |
| U-S4 | `check_wiring.py` 第 3 类要从 `dispatch.sh` 的启动提示词里取出被点名的技能。启动提示词是 bash 字符串，按正则取会不会漏 | 实现时先把三处启动提示词的技能名放进锚点常量模块，由 `dispatch.sh` 引用。这样第 3 类读常量即可，不必解析 bash |
| U-S5 | K2 里「载入锚点常量模块的脚本」的清单 | 模块写成后，按实际 import 与按路径载入的调用方填写 |
| U-S6 | Cursor、Grok、Pi 是否读仓库根的 `AGENTS.md`（R4 T10）。这决定 A5、Q2 那一行在这三个宿主上是否有用 | R4 T1 的前置检查 |
| U-S7 | 体量里标了「推断」的数字（`check_wiring.py` 约 250 行、`tests/lints/` 约 200 行） | 实现后再量 |

---

## 10. 顺带核实、不属于架构的问题（建议另开普通票）

| # | 问题 | 出处 | 已核实 |
|---|---|---|---|
| O1 | `CODING_STANDARDS.md` `## State and configuration` 第 4 条「a conflict or a red check becomes `ticket.bounced` for triage」，与 ADR 0027 的「同一夜第一次 bounce 回 worker 队列」不一致 | S20 | 是 |
| O2 | `TESTING.md` `## Which suites a change needs` 没把 `statedir.py` 列进 board 按路径载入的脚本 | S21 | 是 |
| O3 | merge worktree 的名字：`CODING_STANDARDS.md` 与 `AGENTS.md` 写 `merge-<branch>`，night `CONTEXT.md` **worktree** 写 `merge-<slug>` | N9 §4.2（本轮未重读） | 否 |
| O4 | ADR 0008、0012 正文里的 `refusal.py` 路径已经失效 | N9 §10.3（本轮未重读） | 否 |
