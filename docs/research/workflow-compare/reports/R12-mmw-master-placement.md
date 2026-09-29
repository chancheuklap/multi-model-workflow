# R12 MMW 分层总图

本文把架构形态定稿 `docs/research/workflow-compare/reports/R4-mmw-architecture-form.md`（下称 R4）与七份归置报告合成一张总图。七份报告是：

- `R5-mmw-place-night.md`（night）
- `R6-mmw-place-ticket-run.md`（ticket run）
- `R7-mmw-place-daytime.md`（白天定义）
- `R8-mmw-place-ui.md`（界面链）
- `R9-mmw-place-tooling.md`（独立与工具技能）
- `R10-mmw-place-substrate.md`（基座）
- `R11-mmw-place-principles.md`（原则）

准绳是 `docs/research/workflow-compare/reports/L7-pstack-component-contract.md`（下称 L7）。`mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（下称 SSR；第 2 批搬到 `docs/skill-set/`，K-38）是被审视的对象，不是约束。清点底稿是 N1–N10 与 `N11-mmw-gaps.json`（下称 N11）。

引用写法：「R5 B2」指 R5 归置表的 B2 行，「R4 D3.5 f」指 R4 的决定编号，「K-6」指本文第 5 节的裁定编号，「U-3」指第 9 节的用户决定编号，「X-4」指第 10 节的未确定编号。

标注：「已核实」＝本轮回到原文或跑命令看到的；「推断」＝由原文推出、原文没直接写；做不出判断的放第 10 节。

本文不改任何仓库文件。连线的去重与统计由一个临时脚本完成，脚本在会话的 scratchpad 目录，不在仓库里。第 3.2 节的组件类型分布按该节写明的归类规则重算。

---

## 0. 结论（先读这里）

1. **七份报告与 R4 在骨架上一致。合起来，新 MMW 在技能、脚本与 lint 层只多出 8 个文件。**
   - 一个 mode：`mmw` 技能（`mmw-v2/skills/mmw/SKILL.md`）。
   - 一份头部 playbook：`mmw/playbooks/idea-to-tickets.md`。
   - 两条原则：`mmw/principles/{silence-is-never-a-pass,rerun-dont-reroute}.md`。第三条 `the-tracker-is-the-state` 暂缓，等 X-13 证明它会改变白天重入的决定再建（K-41）。
   - 两份 reference：`mmw/references/phase-boundaries.md`；`design-pages/references/state-list-format.md`（放在 MMW 自有技能里，上游目录不新增任何文件，K-14）。
   - 一个锚点常量模块：`dispatch/scripts/anchors.py`，只由 `dispatch/scripts/` 里的脚本、`check_wiring.py` 与 `tests/relay` 读（K-2）。
   - 一个接线 lint：`mmw-v2/tests/lib/check_wiring.py`，做第 1、2、3、5 类；第 4 类暂缓（K-44）。
   - 此外还有：测试基础设施 `tests/lib/shared_lints.sh` 与第 13 个套件 `tests/lints/`；三份新 ADR（0032–0034）；一份新 merge-note `merge-notes/ask-matt.md`。
   - 技能文本的规则 SSR 与审查方法 RSS 是 MMW 自己的两份文件，第 2 批从上游 `writing-for-agents` 目录搬到仓库文档 `docs/skill-set/`，`writing-for-agents/SKILL.md` 第 8 行恢复上游原文（K-38）。
   - 五个角色操作文件都不并入 `mmw`、不拆分、不改名。其中 `implement/SKILL.md` 与 `code-review/references/session.md` 随第 2 批分叉整目录搬到 `mmw-v2/skills/`；`advisor/references/advising.md`、`dispatch/references/night.md`、`one-ticket.md` 原位不动。
2. **四个上游技能分叉进 `mmw-v2/skills/`，名字不变**：`implement`、`code-review`、`to-spec`、`to-tickets`。
   - 上游目录里的四份与残留的 `ask-matt` 恢复成 squash `5b1a4c51` 的原文，不安装。
   - 本轮实测：上游 subtree 相对 squash 的改动共 +1674/−415 行，其中这五个目录占 +1036/−186，`writing-for-agents` 目录占 +211/−2（M5、M12）。
   - 分叉、恢复原文、SSR 与 RSS 搬出之后，上游文本里的 MMW 改动约剩 +415/−224 行（推断，含第 4 批的 c 类删句）。
3. **全部连线去重后 484 条、208 个节点**（第 3 节）。
   - 按关系分：`reads-reference` 155、`runs-script` 119、`routes-to` 72、`hands-off-to` 38、`calls` 27、`re-enters-at` 24、`configured-by` 21、`enforced-by-hook` 10、`cites-principle` 9、`wakes` 5、`starts-with-prompt` 4。
   - 断点检查：每个 playbook 步骤、每个角色操作文件都有出边。
   - 没有入边的只有入口与行动者节点（宿主技能列表、斜杠、根 `AGENTS.md`、三个角色、测试入口、board 进程、三份新 ADR），都是预期的起点，没有「无人到达」的组件。
   - 方向检查：没有任何能力技能指向 playbook 或 mode 的边。分叉后的 `to-spec`、`to-tickets` 保留各自唯一的后继句（K-7）。
4. **七份报告之间有 37 处分歧（K-1–K-37），审查又提出 13 处需要新裁定的问题（K-38–K-50），都已按工程理由裁定**（第 5 节）。其中改变 R4 原文的有：
   - 角色指针接在同一行，不另起一行。已核实：`watchdog.py` 第 813 行写明 runner 把换行当提交。
   - 指针表与锚点放进一个不导入任何东西的 `anchors.py`，只有 `dispatch/scripts/` 里的脚本导入；别的技能的脚本（含 `verify-ticket.py` 的 `resume_at`）照写字面，由 lint 模式扫描核对（K-2）。
   - `night.md` 事实表的位置判定交给 `status` 首行的 `RESUME:`，取值里有「1b. Before the batch」（K-3、K-48）。
   - worker 的指针送它去跑 `--preflight`，照 `RESUME:` 做；还没有运行记录时 `RESUME:` 印「Claim, read in, write the code」（K-47）。
   - `watchdog.py` 的八种告警每种在自己的文字里写出下一步，再接指针（K-46）。
   - 原则括注写成「(the `mmw` skill's `principles/<slug>.md`)」，只加在 5 处本地没写理由的句子上（K-9）。
   - `verify-ticket/SKILL.md` 第 16 行、`retro/SKILL.md` 第 186 行、`to-spec` `## Next`、`to-tickets` 第 8 步末句都保留，不换成固定返回句（K-6、K-7）。
   - `exe-release`、`dispatch` 都不单列进 `## Routes`（K-16）；`mmw` 不设 `## Head judgement`，这段判断的家是 `idea-to-tickets` 的 **Who checks**（K-40）。
   - ADR 拆成三份，每批一份。
   - 残留 `ask-matt` 在第 3 批与 `mmw` 同一次提交恢复原文。
   - state list 格式放进 `design-pages/references/state-list-format.md`，`prototype/UI.md` 第 6 步只留一句指针（K-14）。文件名避开 Claude Design 项目里已有的 `state-list.md`（`design-pages/references/design-system.md` 第 42 行，已核实）。
   - SSR、RSS 搬出上游目录（K-38）。
5. **四批落地**（第 8 节）：
   1. 只加固；
   2. 分叉：移动已安装 checkout 与跑 `install.sh` 在同一次操作里连着做，`--check` 通过前不开任何会话、不开夜（K-45）；
   3. 新建 `mmw`：发布前先在隔离 home 里用开发版技能跑通实测 T1（K-39）；
   4. 删「下一步」句。
   - 全部作为本仓库的票，只在没有 watch 打开、也没有活着的 relay 或 watchdog 进程时发布（K-32）。
   - 体量：搬家约 1,450 行；删除约 110 行；新增文字约 390 行、代码约 700 行、测试约 250 行；改路径约 135 处。
6. **待你决定的事共 11 件**（第 9 节），其中 U-11 在本次重构之外。两件是本次核实新发现的规则冲突：
   - **U-5**：你写在 `AGENTS.md` 里的「`install.sh` 只在你授权时跑」与 `dispatch.sh check` 的自动重装互相矛盾。第 2、3 批发布后的第一次开夜就会触发自动重装；如果改成「只报告不修」，第 2 批之后没重装就开的夜会让 worker、reviewer 读到上游原版技能（M15）。
   - **U-4**：`mmw` 是否可以自动往你各个仓库的 `AGENTS.md` 加一行。
7. **未确定的事集中在第 10 节。** 最关键的是 T1：`AGENTS.md` 里一行能否让五个宿主在任务开头加载 `mmw`，以及脚本启动的 worker、reviewer 读到这一行时会不会误加载它。T1 是第 3 批发布的前提：不过，就改走宿主钩子注入，或者不建 mode，而不是先建、后删不掉（K-39）。

---

## 1. 本轮回到原文核实的事实

下表只列本轮新做的核实。各报告自己的核实（R4 V1–V17、R5 W1–W10、R6 F1–F17、R7 各行、R8 U1–U17、R9 R9-V1–V13、R10 S1–S22）照用，只在裁定依赖它们时引用。

| # | 事实 | 出处 | 结果 |
|---|---|---|---|
| M1 | `watchdog.py` 第 813 行注释原文：「One line: a runner types what it is handed into a terminal, where a newline submits.」多条告警在第 814 行用 ` \| ` 拼成一行 | `mmw-v2/skills/dispatch/scripts/watchdog.py` 第 808–818 行 | 已核实。角色指针必须接在同一行（K-1） |
| M2 | `NO_QUESTION` 现文只给 worker 的出路（`Decisions I made on my own`、`ABANDON: AC<n> decision`）。测试断言 `len("Hook denied: ") + len(NO_QUESTION) <= 256`。R5 的两角色写法加上 advisor 一条，本轮量得 292 字符，超限；本文 K-5 的三角色短写法量得 195 字符（含前缀） | `tool-guard.py` 第 76–80 行；`tests/dispatch/test_tool_guard.py` 第 35、450 行；`python3 len()` | 已核实 |
| M3 | `relay.py` 导入时加载 `statedir`、`ghlist`，并按路径加载 `events.py`；`tool-guard.py` 只导入 `refusal` | `relay.py` 第 231–264 行；`tool-guard.py` 第 49–62 行 | 已核实。R5 担心 hook 导入 `relay.py` 有开销，这一点成立（K-2） |
| M4 | `design-pages/references/design-system.md` 第 42 行把 Claude Design 项目里的一个文件叫作 `state-list.md` | 同文件 | 已核实。R8 提议的 `prototype/state-list.md` 会与它撞名；新文件取名 `state-list-format.md`（K-14） |
| M5 | 上游 subtree 相对 squash `5b1a4c51`：`skills/` 全部 +1674/−415；`implement` +203/−8，`code-review` +316/−81，`to-spec` +82/−16，`to-tickets` +383/−35，`ask-matt` +52/−46 | `git diff --shortstat 5b1a4c51:skills/… HEAD:mmw-v2/upstream/skills/…` | 已核实 |
| M6 | 上游技能目录里本仓新加、上游没有的文件共 19 个。分叉之后留在上游目录里的是 7 个：`prototype/EXP.md`、`prototype/evidence-page.md`、`triage/references/pipeline-issues.md`、`wayfinder/references/interface-and-remake.md`、`wait-what/VISUAL.md`、`writing-for-agents/SKILL-SET-RULES.md`、`REVIEWING-A-SKILL-SET.md` | `git ls-tree` 与 `git ls-files` 对比 | 已核实。SSR、RSS 第 2 批搬出后剩前 5 个（K-38）。R10 M7 `## 旁加的文件` 表只列了 SSR、RSS 与第 4 批 d 类新加的文件；本文按本行实测改为这 5 个，并把这一节从 R10 的第 4 批提前到第 2 批（K-50） |
| M7 | `dispatch.sh` 第 2344–2360 行：`--check` 失败、且本 checkout 就是已安装 checkout 时，自动跑完整 `install.sh`。根 `AGENTS.md` 第 64 行：「`install.sh` runs only when the user explicitly authorises it」 | 两处原文 | 已核实（U-5） |
| M8 | SSR 第 17 行（事实 7）含「this is why MMW ships no router skill」；第 70 行「A skill this repository wrote has no host-side manifest beside it」；第 81 行「by title rather than by number」 | SSR | 已核实 |
| M9 | `retro/SKILL.md` 第 186 行返回 `night.md` `## 5`；`triage/SKILL.md` 第 82 行把「写 spec、关 issue 链接 spec、切票」写在同一条；`wayfinder/SKILL.md` 第 126 行（第 6 步）让用户新会话跑 `to-spec` 再 `to-tickets`；`write-screen-contract/SKILL.md` 第 115 行「`to-spec` runs once the map is clear, as that skill says」 | 各文件 | 已核实。第 115 行的所指就是 wayfinder 第 126 行，两处必须同一次提交改（R8，K 表不另列） |
| M10 | `skills.txt` 有 35 项；装着的用户触发技能正好 7 个：`grill-with-docs`、`improve-codebase-architecture`、`setup-matt-pocock-skills`、`grill-me`、`handoff`、`teach`、`wait-what` | `grep` | 已核实 |
| M11 | 「Put no question on the screen」是 `implement/SKILL.md` 第 23 行列表项的开头，不是标题；`advising.md` 第 18 行是「**Missing information gets named precisely.**」；`session.md` 第 45 行是「Could not tell: …」 | 各文件 | 已核实。三者都作为逐字锚点登记，lint 按字面核对 |
| M12 | `writing-for-agents` 目录相对 squash：`SKILL-SET-RULES.md` +176、`REVIEWING-A-SKILL-SET.md` +33（两份上游都没有），`SKILL.md` 改 2 行（description 一行、第 8 行加「read SKILL-SET-RULES.md」一句）。指向 SSR 的地方：`docs/contexts/toolbox/CONTEXT.md` 26 处、`ticket-run/CONTEXT.md` 1 处、12 份 merge-note 共 19 处、`check_upstream_em_dashes.py` 与 `check_own_skill_frontmatter.py` 文件头各 1 处、根 `AGENTS.md` 第 49 行。`retro/SKILL.md` 第 11 步点名的是 `writing-for-agents` 的 `SKILL.md`，不是 SSR | `git diff --stat 5b1a4c51:skills/productivity/writing-for-agents HEAD:mmw-v2/upstream/skills/productivity/writing-for-agents`；`grep -c` | 已核实（K-38） |
| M13 | squash 的 `prototype/UI.md` `### 6. Capture the answer and clean up` 没有 state list；现 `UI.md` 第 108 行「Under the fixed heading `## State list` …」整段是本仓加的。`design-pages/SKILL.md` 第 25 行按编号写「the `prototype` skill's `UI.md` step 6 names」 | `git show 5b1a4c51:skills/engineering/prototype/UI.md`；两处现文 | 已核实（K-14） |
| M14 | squash 的 `to-spec/SKILL.md` 没有 `## Next`；现文第 125–127 行 `## Next`「The `to-tickets` skill.」与 `to-tickets/SKILL.md` 第 160 行「When the batch is a spec's night run, hand over to the `dispatch` skill」都是本仓加的 | squash 与现文对比 | 已核实（K-7） |
| M15 | squash 的 `implement`、`to-spec`、`to-tickets` frontmatter 都有 `disable-model-invocation: true`；squash 的 `code-review` 是「Two-axis review」，目录里只有 `SKILL.md` 与 `agents/openai.yaml`，没有 `references/session.md`。`install.sh` 第 181–186 行 `--check` 只比对软链的 `readlink`。`dispatch.sh` 第 2344–2347 行注释「So an incomplete install does not stop the night」 | 各原文 | 已核实（K-45、U-5） |
| M16 | `watchdog.py` 第 94–109 行「The alerts exactly」列出八种告警：`relay down`、`relay not reading`、`#<n> events unreadable`、`#<n> is held with no session to ask`、两种 `liveness unknown`、`silent since <time> with nothing to wait on`、`cannot read the tracker`。第 79–82 行：关于某张票的告警发给那张票所属 watch 的 orchestrator。`night.md` `## 3` 的表只有一行 `watchdog: #<n> silent since …`。`relay.py` 第 291–299 行 `WAKES` 不含 `worker.queued`、`relay.recovered`，两者另行定义。第 745–754 行 idle 告警正文带一条 `dispatch.sh resume <n> …` 命令 | 各原文 | 已核实（K-46） |
| M17 | `verify-ticket.py` `resume_at` 第 2158–2159 行：没有自己的运行、没有 `reviewer.reported`、没有 decided、没有 reverify 时返回 `None`，`--preflight` 不印 `RESUME:`。`implement/SKILL.md` 第 72 行「Once done, commit your work…」、第 74 行「A ticket you are prompted back into: claim it again first, `verify-ticket.py <n> --preflight`, and carry on at the step its `RESUME:` line names.」；第 10 行标题 `## Claim, read in, write the code` | 各原文 | 已核实（K-47） |
| M18 | `dispatch.sh` 里 `--lint` 出现 0 次；`night.md` 1b「Run this once, before the first `advance`」；事实表第 5 行原文带「from the paragraph that invokes the `retro` skill」 | `grep -c`；`night.md` 第 19–48 行 | 已核实（K-48） |
| M19 | `mmw-v2/tests/` 里没有任何文件引用 `AUTONOMOUS`、`PRODUCT_RULES` 的文字；`test_dispatch.sh` 第 2830、6984、7199 行只断言两条启动提示词的首句。`TESTING.md` `## What a test proves` 明文反对钉住「a start prompt's standing sentences」。`PRODUCT_RULES`（`dispatch.sh` 第 109 行）按字面点名 `ui-acceptance` 的「Five rules while the product is running」 | `grep -rln`；各原文 | 已核实（第 2.6 节） |
| M20 | SSR 第 70 行只管「A skill this repository wrote」，括号写「upstream skills keep their `agents/openai.yaml`」；第 106 行把 upstream skill 定义为「one kept in an upstream subtree, or adapted from one」。四个待分叉技能现在的 `agents/openai.yaml` 只有 `display_name` 与 `short_description`，没有 `policy` 行；squash 的 `implement/agents/openai.yaml` 带 `policy: allow_implicit_invocation: false` | 各原文 | 已核实（K-20） |
| M21 | `pull_design.py` 第 983 行在传入的叶子 `README.md` 里找 `^## State list`，不读技能里的任何格式文件；`design-pages/references/pull.md` `## After the first pull` 拆掉 `prototype` UI 原型的 scaffolding；`retro/SKILL.md` 第 198 行 `reviewer-rule` 是提案去处之一 | 各原文 | 已核实（第 3.3 节） |
| M22 | `board/board_data.py` 第 27 行按路径载入 `dispatch/scripts/ghlist.py`；`board/codeversion.py` 的 `LOADED` 列了它 | 各原文 | 已核实 |
| M23 | `advising.md` 第 18 行第 4 条是一般规则，原文没有「无人值守」 | 原文 | 已核实（第 2.2 节 advisor 行） |
| M24 | `ui-acceptance/scripts/` 入库脚本 9 个 | `git ls-files` | 已核实 |
| M25 | `to-tickets/SKILL.md` 第 84 行本身写了理由（「`ok`, `passed` or `done` on their own also appear in failing output」）；`dispatch/SKILL.md` 第 25 行前半句就是理由（「A wake can cut short a command you were running.」）；第 8 行「Where you are is what the ticket's events say, not what this session remembers.」就是 `the-tracker-is-the-state` 规则的前半句 | 各原文 | 已核实（K-9、K-41） |
| M26 | `~/agentflow/CLAUDE.md` 与 `~/xiaohuangya/CLAUDE.md` 都只有「@AGENTS.md」一行，所以 Claude Code 上脚本启动的 worker、reviewer 也读到消费仓库的 `AGENTS.md` | 两个文件 | 已核实（X-1） |
| M27 | `relay.py` 第 196 行：`relay.lock` 在 `run` 运行期间一直持有；`watchdog.py` 的 `run` 持有 `watchdog.lock`；`night.md` `summary` 的 exit 1 是「a relay was left running」 | 各原文 | 已核实（K-32） |
| M28 | 残留 `ask-matt/PHASE-BOUNDARIES.md` 的第 3 问原文是「**3. Do you need to hand off?**」；另有一句「Compacting mid-phase makes the agent lose the thread.」 | 原文 | 已核实（K-43、K-49） |
| M29 | 残留 `ask-matt/SKILL.md` 第 22–26 行：「谁来检查」是主流程第 3 步「Branch: is this a multi-session build?」的一个分支 | 原文 | 已核实（K-40） |
| M30 | `implement/references/writing-interface-code.md` 第 35、37、41 行三处按编号写「closing step 1」 | `grep -n` | 已核实（K-43） |

采用清点报告的结论时，N11 列出的错误都没有采用：

- N8 说 `NO_QUESTION` 与 `implement` 出路「基本一致」，不采用；
- N9 说 ADR 0012 与 `night.md` 同义，不采用；
- N3、N6 把 `ask-matt` 当成活的入边，不采用；
- N7 的字节数不采用，用 R9 的实测 41,198。

---

## 2. 新 MMW 的组件总表

### 2.1 mode

| 项 | 内容 |
|---|---|
| 名字与位置 | `mmw`，`mmw-v2/skills/mmw/SKILL.md`；`skills.txt` 加 `self/mmw`（R10 I5） |
| 读者 | 只服务人启动的会话。脚本启动的会话不经过它（R4 D1.1）；它们若因消费仓库 `AGENTS.md` 那一行加载了 `mmw`，由 `## Where you are` (a) 送回启动提示词点名的技能。会不会误加载、加载后首个动作是什么，由 X-1 的两个脚本会话场景实测（M26） |
| 入口 | 消费仓库 `AGENTS.md` `## External References` 的一行，File 列写「the `mmw` skill」，不写路径（R10 A5、Q2；S11：写成路径会被 `manage-agents-md` 的 `check.sh` 判为不存在）。另有 description（备用）和 `/mmw` |
| 篇幅 | 不超过 100 行（R4 D2.1）。上限由 T8 实测后决定是否写进 lint（R10 §4.3 暂不加） |
| `## Where you are` | (a) 首条消息由脚本拼出 → 按它点名的技能做；(b) 缺 `AGENTS.md` 那一行、有人在场、当前目录不在 `.worktrees/` 下 → 加上（是否自动加，见 U-4）；(c) 正在阶段边界 → `references/phase-boundaries.md`；(d) 一个人带来一件任务 → `## Routes`。唤醒行不在这里处理：第 1 批之后唤醒行自带指针，turn guard 的拦截文字自带步骤，orchestrator 的 `night.md` 事实表与 `one-ticket.md` 第 3 步已经处理这几种行（K-42）。不带原则括注（K-41） |
| `## Routes` | 1）一个想法、一个功能或改动 → `playbooks/idea-to-tickets.md`；2）太大、看不清路线 → `wayfinder`，map 清空后在新会话进 **Spec**；3）外来 issue、流水线退回的 `needs-triage` 票（含 `contract` child）→ `triage`，判为 agent-ready 的进 **Spec**，获批的 retro 提案也进 **Spec**；4）有东西坏了 → `diagnosing-bugs`，修法进 **Who checks**，没有好 seam 时告诉用户运行 `/improve-codebase-architecture`（K-40）；5）想整理代码架构 → 告诉用户运行 `/improve-codebase-architecture`（R7 G2），定下的决定进 **Who checks**；6）兜底一句：「某个已装技能的 description 认领的任务，交给那个技能；本表只列会改变去处或带门槛的行」（R9 U-R9-1）。**不列** `dispatch`、`exe-release`（K-16）以及 `research`、`diagram-design`、`advisor` 等本身完整的独立技能 |
| `## Principles` | 两行索引，格式 `**<Title>** (\`<slug>\`). <何时适用>.`，不写规则句；末句「应用时读 `principles/<slug>.md` 全文」。规则句只在原则文件里（K-27） |
| 层级优先级句 | 用户级提示词（`mmw-v2/prompt/shared.md`，owner 的话）高于本技能。playbook 步骤与能力技能正文冲突时：关于交付物之后做什么，以 playbook 为准；关于怎么做，以能力技能为准（R4 D2.2） |
| 自有 reference | `references/phase-boundaries.md`：照录残留 `ask-matt/PHASE-BOUNDARIES.md` 57 行（相对上游只有宿主中立改写，R4 V13）；其中 Handoff、Clear、Compact 三项写成「建议用户做」（R7 K1）；来源记在 `merge-notes/ask-matt.md`（R10 M5） |
| 不设的节 | `## Autonomy`、`## Writing the reply`、`## Subagents`：家在 `shared.md` 与 ADR 0015（R4 D2.4） |

### 2.2 playbook 与角色操作文件

| 名字 | 种类与位置 | 入口 | 步骤概要（粗体为稳定名） | 点名的组件 | 重入 | 交付物 |
|---|---|---|---|---|---|---|
| `idea-to-tickets` | 头部 playbook，`mmw/playbooks/idea-to-tickets.md`，新建 | `mmw` Routes 第 1 行；Routes 门槛直达 **Spec** 或 **Who checks**；`## Where you are` 直达各步；用户斜杠进 `/grill-with-docs` 的会话本身就处在 **Grill**（这是地址，不是调用） | **Grill**（`grilling` + `domain-modeling`；仓库外一手事实用 `research`）→ **Runnable questions**（`prototype`；LOGIC/EXP 结论写进叶子 `README.md` 后回 **Grill**，本 playbook 不写生产代码；UI winner 交给 `design-pages`；宿主没有 Claude Design 工具时，按 `phase-boundaries.md` 的「**3. Do you need to hand off?**」告诉用户运行 `/handoff`，这是 **Spec** 同一上下文门槛的唯一例外，R8、K-43；没有 map 时从原型到 screen contract 在一个用户在场的会话里跑完，是否保留见 U-6）→ **Someone else knows**（`to-questionnaire`，结束回合）→ **Who checks**（本步持有迁自残留 `ask-matt/SKILL.md` 第 22–26 行的判断：这件事要多个会话，还是小到用户自己检查就够；No → `tdd`，结束，K-40）→ **Spec**（调 `to-spec`。本步只写门槛：**Grill** 到 `to-tickets` 跑完，都在同一个未清空、未压缩的上下文里，临界时照 `phase-boundaries.md` 在边界压缩；宿主在阶段中间自动压缩了，就先把摘要里带着、`CONTEXT.md` 与 ADR 里没有的决定逐条与用户确认，再调 `to-spec`（K-49）。之后 `to-spec` 的 `## Next` 带到 `to-tickets`，`to-tickets` 第 8 步末句在批次是整夜运行时带到 `dispatch`，本 playbook 不复述这两跳，K-7）→ **Tickets**（重入点：spec 已发布、还没有票时调 `to-tickets`；门槛括注 `silence-is-never-a-pass`）→ **Hand to the night**（重入点与门槛：什么时候开夜由用户定） | `grilling`、`domain-modeling`、`research`、`prototype`、`design-pages`、`handoff`（只告诉用户）、`to-questionnaire`、`tdd`、`to-spec`、`to-tickets`、`dispatch`；`mmw/references/phase-boundaries.md`；原则 `silence-is-never-a-pass` | `## Where you are` 九行，第一个成立者胜：spec 无票 → **Tickets**；票已过 lint → **Hand to the night**；map 或首份 spec 列着未链接的 spec → **Spec**；map 清空、agent-ready issue、获批 retro 提案 → **Spec**；UI winner 已记录、没有 `prototypes/<effort>/claude-design/` → `design-pages`（R8）；`pull-report.md` 已提交、没有 `screen-contract.yaml` → `write-screen-contract`（R8）；用户本条消息带来已定下的决定、没有 spec → **Who checks**；带回填好的问卷 → **Grill**；其他 → **Grill**。本地一句：事实只取 tracker、仓库与用户本条消息，不取会话记忆（K-41、K-49） | 已发布并通过 `--lint` 的票，已交给 `dispatch`；或 `tdd` 结果加一句「由你检查」。`**Reply:**` 逐个交代没做的步骤 |
| worker | 角色操作文件，`implement/SKILL.md`（第 2 批分叉到 `mmw-v2/skills/implement/`） | 启动提示词 `Use the implement skill to work ticket #N. $AUTONOMOUS $PRODUCT_RULES` 加两份 Memory 索引；自拿票的会话走 `dispatch` → `inside-a-ticket.md` → 本文件 | 认领、读入、Shared experience、写码（前两节，不加名），再加 `## Closing steps` 八步：**Integrate and run** → **Post the decisions** → **Review round** → **Final run** → **Audit** → **Tell touched tickets** → **Draft the closing comment** → **Close out**（R6 I15、X5） | `dispatch.sh`（integrate、start reviewer、wait、ack）、`verify-ticket.py`、`verify-ticket/references/sub-issues.md`、`references/writing-interface-code.md`、`references/saving-memory.md`、`tdd`、`resolving-merge-conflicts`、`ui-acceptance` `## Five rules while the product is running`、`nmem`；原则括注两处（第 18、96 行） | 唤醒行末尾的指针 → `dispatch` `## On waking` → `verify-ticket.py <n> --preflight`，照 `RESUME:` 做（第 74 行）。`--preflight` 印 `RESUME: <步骤名> (<event>)`；已认领、还没有自己的运行记录时印 `RESUME: Claim, read in, write the code`（K-47） | 关闭或交回 `needs-triage` 的票、收尾评论、事件、推送的 `issue-<n>` 分支、子票、Memory 记录 |
| reviewer | 角色操作文件，`code-review/references/session.md`（随分叉） | 启动提示词 `Use the code-review skill to review ticket #N from base commit <base>. $AUTONOMOUS` 加 reviewer Rules；`code-review` 的表按提示词形状送到本文件 | **1. Pin the diff** → **2. Run the axes**（四个 axis 文件）→ **3. Verify every finding** → **4. Sort** → **5. Write one review report** | 四个 axis reference、`verify-ticket.py --review`、`dispatch.sh integrated`、`story-parity.py`、`CODING_STANDARDS.md`、`TESTING.md`、`tdd/tests.md`、`tdd/mocking.md` | 无：一次性会话；丢失时由 watchdog 写 `reviewer.lost`，worker 在 **Review round** 另起一个 | 票上以 `REVIEW <base>..<HEAD>` 开头的评论与 `reviewer.reported` 事件 |
| advisor | 角色操作文件，`advisor/references/advising.md`（原位） | `dispatch.sh advise <file>` 启动，提示词 `Use the advisor skill.` 加 brief | `## The brief tells you what the caller knows` → `## How to answer` 1–5（第 4 条「Missing information gets named precisely」是一般规则；`NO_QUESTION` 把被拦下提问的 advisor 送到这里，这是 R6 X3 的推断，由 X-14 实测）→ `## What you never do` | 无外部组件 | 无 | 会话里的回答，由发起方按 `consulting.md` 对待 |
| orchestrator（夜） | 角色操作文件，`dispatch/references/night.md`（原位） | 人说「今晚跑 spec #N」：`AGENTS.md` 一行 → `mmw` Routes 兜底句 → `dispatch` `## Find your moment` 第 3 行；或 `to-tickets` 第 8 步末句、`idea-to-tickets` **Hand to the night**；或 `dispatch` 的 description、`/dispatch` | **1. The user says the night starts** → **1b. Before the batch** → **2. First `advance`** → **3. Each time something wakes you** → **4. The closing pass** → **5. The night is over**（调 `retro`）→ **6. Merge the accepted night**；分支 **Suspending the night**（标题即稳定名，不改名） | `dispatch.sh` 的 13 个子命令、`verify-ticket.py --lint`、`events.py fold`、`target_config.py --check`、`lease.py release`、`to-tickets` 的 `<issue-template>`、`to-spec/references/revising-a-spec.md`、`design-pages/references/pull.md`、`retro`；原则括注两处（第 82、127 行） | 事实表改成四行（R5 B2）：唤醒行 → **3**；`MMW turn guard:` → 照它做；因流水线故障决定停夜 → **Suspending**；其他 → `dispatch.sh status <spec>` 首行 `RESUME:`（R5 J1 取值表，加 K-48 的两处改正）。唤醒指针（`by=open`）直达 **3**；`## 3` 的表为 `watchdog:` 告警加一行兜底「照告警写的下一步做」（K-46） | `NIGHT SUMMARY`、`NIGHT RETRO`、各决定的理由评论、合进 project branch 的一次 merge（第 5 行已写，不另加 `**Leaves:**`，K-21） |
| orchestrator（单票） | 角色操作文件，`dispatch/references/one-ticket.md`（原位，14 行） | `mmw` Routes 兜底句 → `dispatch` `## Find your moment` 第 4 行 | `open-ticket` → `start <n> worker` → 被唤醒时：`contract`、`relay.recovered`、`watchdog:` 借用 `night.md` **3** 的表行，`MMW turn guard:` 照它做（R5 C2）→ `land` | `dispatch.sh`、`events.py fold`、`night.md` **3** | 唤醒指针 `by=open-ticket` | 落地的一张票 |
| （worker 的分支）夜外自拿票 | 分支 reference，`dispatch/references/inside-a-ticket.md`（原位，不是 playbook） | `dispatch` 第 2 行；`implement` 第 12 行 | `adopt` → 回 `implement` → `## After the closeout`，末尾新加一句：本 watch 发来的其他唤醒与 `watchdog:` 行都关于你自己的票，读事件并告诉用户（R5 D1）；`watchdog.py` 对 `by=adopt` 的 watch 不附 `resume` 命令（K-46） | `dispatch.sh adopt/ack` | 唤醒指针 `by=adopt`（R5 H3） | — |

不另建 playbook 的任务：wayfinder、triage、排错、代码健康、界面链、接入新仓库、出包、写组件。理由分别见 R4 D3.1、R8 §3、R9 §2：它们只调一个技能，或顺序已由能力技能按自身输出给出，都触发 L7 C.6 信号 3、5、9、10。

### 2.3 能力技能（36 个：已装 35 个加新建的 `mmw`）

来源分四类：

- **上游原文**：与 squash 逐字相同。
- **上游 + 能力改动**：留在 subtree，只保留 a、b、d、e 类改动（R4 D5.3）。
- **MMW 自有**：`mmw-v2/skills/`。其中标「分叉」的原为上游，第 2 批搬家。
- **外来合集**：非 mattpocock 来源。

「调用开关」一列按推导规则得出（R4 D1.3 加 R9 W-SSR-20 的扩展，K-24），今天的推导结果与现状相同。

| 技能 | 来源 | 持有的 reference（新旧位置） | 脚本 | 本次改动（批） | 调用开关 |
|---|---|---|---|---|---|
| `mmw` | MMW 自有（新） | `references/phase-boundaries.md`；`playbooks/idea-to-tickets.md`；`principles/*.md` ×2 | 无 | 新建（3） | 模型可触发 |
| `dispatch` | MMW 自有 | `references/night.md`、`one-ticket.md`、`inside-a-ticket.md`、`editing-models.md` | `dispatch.sh`、`relay.py`、`watchdog.py`、`status.py`、`models.py`、`statedir.py`、`ghlist.py`、`runners/{paseo,orca,herdr}.sh`、`tool-guard.py`、`turn-guard.py`、新 `anchors.py`；`hosts.json` | description 删「Start a reviewer from inside a ticket,」（2）；表第 1 行改为先 `## On waking`、再照 `--preflight` 的 `RESUME:`（1，K-47）；四处修补与指针（1）；`watchdog.py` 八种告警各带下一步（1，K-46）；不加原则括注（K-9）；`check` 缺行警告（3） | 模型 |
| `implement` | 分叉 | `references/writing-interface-code.md`、`saving-memory.md` | 无 | 搬家（2）；步骤名（1）；`writing-interface-code.md` 三处「closing step 1」改为 **Integrate and run**（1，K-43）；第 74 行补「没有 `RESUME:`」的去处（1，K-47）；两处括注（3）；删 `agents/openai.yaml`（2，K-20） | 模型（自有，无开关） |
| `code-review` | 分叉 | `references/session.md`、`standards-reviewer.md`、`spec-reviewer.md`、`tests-reviewer.md`、`ui-reviewer.md` | 无 | 搬家（2）；`spec-reviewer.md` 第 35 行删半句过时理由（2，R6 C7）；删 `agents/openai.yaml`（2，K-20） | 模型 |
| `to-spec` | 分叉 | `references/revising-a-spec.md`、`several-specs.md` | 无 | 搬家（2）；第 4 步加「关已分诊 issue 并链接 spec」一句（4，R7 A4）；`## Next` 保留（K-7）；删 `agents/openai.yaml`（2，K-20） | 模型 |
| `to-tickets` | 分叉 | `references/ambiguity-scan.md`、`cutting-interface-tickets.md`、`person-ticket.md` | 无 | 搬家（2）；第 84 行不加括注（K-9）；第 8 步末句保留（K-7）；删 `agents/openai.yaml`（2，K-20） | 模型 |
| `verify-ticket` | MMW 自有 | `references/linting.md`、`sub-issues.md` | `verify-ticket.py`、`events.py`、`issue_tree.py`、`gate-check/`（链到 `mmw-v2/upstream-unlazy/`） | `resume_at` 印步骤名，并在已认领、没有运行记录时印「Claim, read in, write the code」；步骤名写成字面，由 lint 第 1 类模式扫描核对，不导入 `anchors.py`（1，K-2、K-47）；第 16 行保留（K-6） | 模型 |
| `ui-acceptance` | MMW 自有 | `references/story-parity.md`、`boundary-check.md`、`journey.md`、`harness-guard.md`、`product-answers.md` | 四个 oracle、`lease.py`、`target_config.py`、`design_render.py`、`pixel_diff.py`、`refusal.py` | description 删「, or before writing a page ticket's code」与表第 1 行（2）；不加原则括注（K-9） | 模型 |
| `design-pages` | MMW 自有 | `references/edit-pages.md`、`draw.md`、`pull.md`、`design-system.md`、两份 `template-*-claude-md.md` | `pull_design.py`、`check_editable_selectors.py` | 新建 `references/state-list-format.md`，收下 `prototype/UI.md` 第 6 步的 state list 格式段；`## The state list` 与 `design-system.md` 第 42 行在同技能内引用它，第 25 行不再按编号引用「`UI.md` step 6」（2，K-14） | 模型 |
| `write-screen-contract` | MMW 自有 | `references/screen-contract-format.md` | `extract_skeleton.py`、`lint_screen_contract.py`、`dump_openapi.py` | `## Next` 删一个从句（4，与 `wayfinder` 第 6 步同一次提交） | 模型 |
| `retro` | MMW 自有 | 无 | `retro.py` | 不动（第 186 行保留，K-7） | 模型 |
| `advisor` | MMW 自有 | `references/consulting.md`、`advising.md` | 无（经 `dispatch.sh advise`） | 不动；三个锚点登记进 `anchors.py`（1） | 模型 |
| `exe-release` | MMW 自有 | `references/driving.md`、`new-product.md`、`key.md` | `release-flow.sh`、`release_contracts.py`、`verify_key.py`、`release_script_assembler.py`、`builders/nuitka.py`、`release_templates/…`、`diagnose_core.py`、`fix_dispatch.py` | 不动（F1–F4 另开普通票） | 模型 |
| `code-checkers` | MMW 自有 | `references/python.md`、`typescript.md`、`git-hooks.md` | 无 | 不动 | 模型 |
| `manage-agents-md` | MMW 自有 | `references/create.md`、`rewrite.md` | `check.sh` | `### What NOT to Add` 第 9 条加一句「指针行不是技能清单」、根模板 File 列加半句（3，R9 M6、M7） | 模型 |
| `triage` | 上游 + 能力改动 | 上游 `AGENT-BRIEF.md`、`OUT-OF-SCOPE.md`；旁加 `references/pipeline-issues.md` | 无 | 第 5 步 route 句移入 `pipeline-issues.md`（2）；第 5 步 `ready-for-agent` 拆分、`## Quick state override` 回上游、`pipeline-issues.md` 第 5 行改写（4） | 模型（Routes 调用） |
| `wayfinder` | 上游 + 能力改动 | 旁加 `references/interface-and-remake.md` | 无 | 第 6 步后半句移走（4）；`mmw:map` 回 `wayfinder:map`，建 label 的句子并进 tracker 文档（2，以 X-11 走查为前提） | 模型 |
| `prototype` | 上游 + 能力改动 | 上游 `LOGIC.md`、`UI.md`；旁加 `EXP.md`、`evidence-page.md` | 无 | `UI.md` 第 6 步的 state list 段移到 `design-pages/references/state-list-format.md`，原处留一句指针（2，K-14）；`UI.md` `## Next` 删（4）；规则 1 不动 | 模型 |
| `grilling` | 上游 + 能力改动 | 无 | 无 | 不动 | 模型 |
| `grill-me` | 上游 + 能力改动（a 类） | 无 | 无 | 不动 | 用户 |
| `grill-with-docs` | 上游 + 能力改动 | 无 | 无 | 第 7 行末句删（4） | 用户 |
| `domain-modeling` | 上游原文 | `CONTEXT-FORMAT.md`、`ADR-FORMAT.md` | 无 | 不动 | 模型 |
| `codebase-design` | 上游 + 能力改动 | `DEEPENING.md`、`DESIGN-IT-TWICE.md` | 无 | 不动 | 模型 |
| `improve-codebase-architecture` | 上游 + 能力改动 | `HTML-REPORT.md` | 无 | `### 4` 第 3 句移走，「This skill changes no code」留（4） | 用户 |
| `diagnosing-bugs` | 上游原文 | 无 | `scripts/hitl-loop.template.sh` | 不动 | 模型 |
| `research` | 上游原文 | 无 | 无 | 不动 | 模型 |
| `resolving-merge-conflicts` | 上游 + 能力改动（e 类） | 无 | 无 | 不动（R6 X2） | 模型 |
| `tdd` | 上游 + 能力改动（e 类） | 上游 `tests.md`、`mocking.md` | 无 | 不动（R6 X2） | 模型 |
| `to-questionnaire` | 上游 + 能力改动（b 类） | 无 | 无 | 不动 | 模型（playbook 调用） |
| `wizard` | 上游 + 能力改动 | 无 | `template.sh` | 不动 | 模型 |
| `handoff` | 上游 + 能力改动（a 类） | 无 | 无 | 不动；由 `phase-boundaries.md` 与 **Runnable questions** 以「告诉用户运行」点名（K-10） | 用户 |
| `teach` | 上游 + 能力改动 | 四份 `*-FORMAT.md` | 无 | 不动 | 用户 |
| `wait-what` | 上游 + 能力改动 | 旁加 `VISUAL.md` | 无 | 不动 | 用户 |
| `setup-matt-pocock-skills` | 上游 + 能力改动 | 五份种子 | 无 | 种子 `issue-tracker-github.md` **Map** 一条加建 label 句（2，随 `wayfinder`）；U4 不放这里 | 用户 |
| `writing-for-agents` | 上游 + 能力改动（a 类，只剩 description 一行） | 上游 `SKILL-MECHANICS.md` | 无 | 第 8 行恢复上游原文；SSR 与 `REVIEWING-A-SKILL-SET.md`（下称 RSS）搬到仓库文档 `docs/skill-set/`（2，K-38）。SSR 约 +40 行、RSS 约 +2 行的改写在新位置做（2、3，见第 7 节） | 模型 |
| `diagram-design` | 外来合集（`cathrynlavery/diagram-design` subtree） | 56 份 `references/` | 技能内 4 个、`repo-root/scripts/` | 不动（F5、F6 另开普通票） | 模型 |

上游里不安装的：分叉后的四份原文、残留 `ask-matt`（第 3 批恢复原文）、`in-progress/` 等其他 bucket 的技能。它们都保持上游原文，与安装无关。

### 2.4 原则

| slug | 规则一句（R11 §3.1 草稿） | 引用处（K-9，共 5 处括注加 `mmw` 索引） | 依据（只写进 ADR 0034，不写进原则文件，K-19） |
|---|---|---|---|
| `silence-is-never-a-pass` | 什么都没做的检查、什么都没交的交付，读起来与通过无异；所以检查要能失败，查不了就写「查不了」 | `mmw` 索引；`idea-to-tickets` **Tickets**；`implement` 第 96 行；`night.md` 第 127 行 | ADR 0008、0018 第 19 行、0020 第 20 行 |
| `the-tracker-is-the-state`（暂缓，K-41） | 你在哪一步由 tracker 上的事件决定，会话记忆只是会丢的副本；等别人就结束回合，由事件叫醒 | 第 3 批不建。前半句就是 `dispatch/SKILL.md` 第 8 行原话，后半句已由 relay、turn guard 与 `RESUME:` 在机制上强制（M25）。在它建成之前，`idea-to-tickets` `## Where you are` 本地写一句「事实只取 tracker、仓库与用户本条消息」。X-13 证明它会改变白天重入的决定，再建并加括注；否则并回 `dispatch/SKILL.md` 第 8 行，不建 | ADR 0010、0017、0019、0020（建成时写进 ADR 0034） |
| `rerun-dont-reroute` | 被唤醒打断的命令原样重跑；拒绝、产品连不上、流水线自身故障，按流水线给的路由上报，不绕路、不写重试循环、不换 host 或 runner。`**Boundaries:**` 三条（shared.md 规则 11 的读法见 U-7；拒绝文字写着「再跑一次」的照做一次；脚本自己拥有的重试归脚本） | `mmw` 索引；`night.md` 第 82 行；`implement` 第 18 行 | ADR 0010 第 35 行、0017、0018 第 18–19 行、提交 `0855d553` |

文件格式：`# Title`，一到三句写成事实的规则，`**Why:**`（用文字写观察到的故障与用户决定，不写 ADR 号、日期、issue 号），`**Applies when:**`，可选 `**Boundaries:**`、`**Not:**`。没有 frontmatter，不列调用方（R11 §3.2）。

括注写法（K-8）：`mmw` 目录内写 `(principle \`<slug>\`)`，其他自有技能写 `(the \`mmw\` skill's \`principles/<slug>.md\`)`，上游文本不写。

pstack 23 条原则原样引入 0 条（R11 §3.4）。其中 `make-operations-idempotent` 的内容以一条写脚本规则的形式进 `CODING_STANDARDS.md`（R11 E2）。

### 2.5 hook

| hook | 管谁 | 本次改动 |
|---|---|---|
| `dispatch/scripts/tool-guard.py`（PreToolUse 与提问钩子） | `issue-<n>` 工作树里的 worker、reviewer，以及在 worker 工作树里被起的 advisor（R6 F5，代码路径已核实，是否真发生未知，X-14） | `NO_QUESTION` 改成三角色（K-5）；锚点改从 `anchors.py` 取，由 lint 核对（1）；`REFUSAL`、`no_kill`、`governed_ticket` 不动 |
| `dispatch/scripts/turn-guard.py`（回合结束） | 被 relay 登记的 orchestrator | 不动。拦截文字自带步骤并以「Then end your turn」结尾，不接指针（R5 M1） |

### 2.6 角色

| 角色 | 定义（启动提示词 + `~/.mmw/models.json` 一行，ADR 0015 的延续） | 操作文件 |
|---|---|---|
| worker | `dispatch.sh` 第 1949 行提示词；`junior-worker` 或 `senior-worker` 行（由票上 **Worker** 一行决定） | `implement` |
| reviewer | 第 1967 行；`reviewer` 行 | `code-review/references/session.md` |
| advisor | 第 2072 行；`advisor` 行 | `advisor/references/advising.md` |
| orchestrator | 由人启动，没有行 | `night.md`、`one-ticket.md` |
| 人启动的一件事 | 没有行 | `mmw` → `idea-to-tickets` |

启动提示词、`AUTONOMOUS`、`PRODUCT_RULES` 三者字面都不变（R4 D1.1）。守住它们的方式（M19）：`test_dispatch.sh` 第 2830、6984、7199 行只核对启动提示词首句，也就是角色到技能的映射；`PRODUCT_RULES` 按字面点名的 `ui-acceptance` 标题「Five rules while the product is running」登记进 `check_wiring.py` 第 1 类的清单。`AUTONOMOUS` 的文字没有也不该有测试钉住（`TESTING.md` `## What a test proves`）。

### 2.7 配置

| 配置 | 写者 | 读者 | 本次改动 |
|---|---|---|---|
| `~/.mmw/models.json` | 只由 `models.py config` 写 | `dispatch.sh`、board `settings_api.py`、`install.sh` | 不动 |
| `mmw-v2/skills/dispatch/hosts.json` | 维护者 | `models.py`、`install.sh` | 不动 |
| `~/.mmw/installed-root` | `install.sh` | `dispatch.sh check`、`--check` | 不动 |
| `~/.mmw/state/<owner>__<name>/watches.json` 与同目录的 `relay.lock`、`watchdog.lock` | `relay.py`、`watchdog.py` | `relay.py`、`watchdog.py`、`install.sh --check`（新，只列开着的 watch 与持锁的活进程，不改退出码，K-32） | 每个 watch 多一个 `by: open \| open-ticket \| adopt` 字段（1，R5 H3） |
| `mmw-v2/skills.txt` | 维护者 | `install.sh`、`check_own_skill_frontmatter.py`、`check_wiring.py` | 四行改 `self/`（2）；加 `self/mmw`（3） |
| `dispatch/scripts/anchors.py`（新） | 维护者 | `relay.py`、`watchdog.py`、`status.py`、`tool-guard.py`、`dispatch.sh`（经 `relay.py pointer`）、`check_wiring.py`、`tests/relay`；别的技能的脚本不导入它（K-2） | 新建（1）：角色指针表 `POINTERS`（键为收件角色与 `by`，值只含技能名、技能内路径、小节标题）加锚点常量；不导入任何模块 |
| 消费仓库 `.mmw/target.json` 等 | 消费仓库 | 各 oracle、`verify-ticket.py`、`dispatch.sh` | 不动（R10 Q1） |

### 2.8 仓库文档

| 文档 | 本次改动 |
|---|---|
| `docs/adr/` | 新建 0032（第 1 批，`amends: [0020]`）、0033（第 2 批）、0034（第 3 批，含原则 slug 到依据的对照）；README 索引加三行；现有 31 份正文不动（R10 D2–D6，K-12） |
| `CONTEXT-MAP.md`、`docs/contexts/*` | 85 处路径改到 `mmw-v2/skills/<名>/`（2）；新词条 **role pointer**（night，1）、**fork**（toolbox，2）、**`mmw`**、**playbook**、**principle**（toolbox，3），`_Home_` 是 SSR `## Layers of the set`（K-17）；改写 `RESUME:`、**wake**、**shared lints**、**upstream skill**、**`disable-model-invocation` pairing**、**"Hand the decision on"** 六条；Toolbox 范围句（3）；`ui-acceptance/CONTEXT.md` 三条判据词条改 `_Home_`（2，R8）；`toolbox/CONTEXT.md` 26 处、`ticket-run/CONTEXT.md` 1 处指向 SSR 的路径改到 `docs/skill-set/`（2，K-38） |
| `mmw-v2/merge-notes/` | README：`## 本仓自有正文的技能` 废止，改为 `## 分叉的技能`（2）；`## disable-model-invocation` 改成推导规则（2）；新 `## 旁加的文件` 列 M6 的 5 个文件（2，K-50）。新 `ask-matt.md`（3）。六份 merge-note 删开关复述（2）。四份分叉 note 改源目录行与过时句（2）。12 份 note 共 19 处指向 SSR 的路径改到 `docs/skill-set/`，`writing-for-agents.md` 删掉 SSR、RSS 两段，只记 description 一处改动（2，K-38）。c 类条目删（4） |
| `mmw-v2/downstream-notes/` | 不动，不写新说明（R10 D1） |
| 根 `AGENTS.md` | `## Commands` 套件数改 13、共用检查改为一句、加 `shared_lints.sh` 命令（1）；`--check` 半句（1）；`## Gotchas` 第三步前先看 `--check` 列出的 watch 与活进程（1，K-32）；`## Gotchas` 第二、三步之间写明第 2 批那一次提升要把移动 checkout 与 `install.sh` 连着做（2，K-45）；night runbook 行改为技能名写法（1）；`## External References` 第 49 行 SSR 路径改到 `docs/skill-set/`（2，K-38）；加 `mmw` 行（3，发布后）；「six」改「seven」（3） |
| `CODING_STANDARDS.md` | `## Skills and scripts` 列举补 playbooks 与 principles（3）；加锚点规则一条（1，R10 C2）；加可重跑规则一条（1，R11 E2） |
| `TESTING.md` | `## What a test proves` 加接线检查一句（1）；`## Which suites a change needs` 加锚点模块一条（1） |
| `mmw-v2/tests/AGENTS.md` | `lib/` 一句（1） |
| `docs/skill-set/`（新目录） | 收下 SSR 与 RSS，文件名不变（2，K-38）。SSR 开头改为先指上游 `writing-for-agents` 的 `SKILL.md`（杠杆与失败模式的名字在那里）；两份内部的相对链接改成「the `writing-for-agents` skill's `SKILL.md`」写法 |
| `mmw-v2/tests/lib/check_upstream_em_dashes.py`、`check_own_skill_frontmatter.py` 文件头 | 指向 SSR 的一句改路径（2，K-38）。`check_upstream_em_dashes.py` 只扫 `mmw-v2/upstream/skills/` 下的 `.md`，SSR 搬出后不再被它扫；文件头原文说这条规则约束的是「this repository's text inside the subtree」 |
| `docs/contexts/night/how-it-works.md` 第 81 行 | 沉默 worker 的消息改指 `watchdog.py`（1，R5 Q1） |
| `docs/notes/stage-two-shared-experience-layer.md` | 两处路径（2） |
| `mmw-v2/upstream/docs/engineering/{implement,code-review}.md` | 回到上游原文（2，R6 I19、C11） |

---

## 3. 全部连线

### 3.1 做法

- 合并了七份报告与 R4 的 edges 块，并按第 5 节的裁定改正或删除。
- 节点名统一如下：
  - 技能用裸名；
  - 文件用「技能/相对路径」，技能里的锚点写成 `#<标题或步骤名>`；
  - 头部 playbook 步骤写成 `idea-to-tickets#<步骤名>`；
  - 其余节点带前缀：`principle:`、`role:`、`hook:`、`config:`、`prompt:`、`doc:`、`adr:`、`lint:`、`entry:`、`tracker:`、`artifact:`、`ext:`。
- 每个模型可触发的技能加一条 `entry:description -> <技能> : routes-to`，每个用户触发的技能加一条 `entry:slash -> <技能> : routes-to`。
- 同一对节点、同一关系只留一条。
- 关系词只用给定的 11 种。有四种关系不在词表里，借最近的词表示，并在注释里写明实际关系：
  - 「告诉用户运行 `/X`」记作 `routes-to`；
  - 「补写一行」记作 `hands-off-to`；
  - 「由 lint 强制」记作 `enforced-by-hook`；
  - 「拆掉别的技能留下的产物」（`pull.md` 拆 `prototype` 的 UI scaffolding）记作 `reads-reference`。
- 入边、出边按文件聚合：锚点并入所属文件，只有头部 playbook 的步骤单独检查。
- 组件类型按节点名归类：`entry:` 为 entry；`mmw` 为 mode；`idea-to-tickets` 及其步骤为 playbook；`principle:`、`role:`、`hook:`、`config:` 各为同名类型；`prompt:`、`doc:`、`adr:` 为 repo-doc；`lint:` 与 `tests/` 为 lint/test；`artifact:`、`tracker:`、`ext:` 为 artifact；五个角色操作文件单列；路径里有 `/scripts` 或以 `.py`、`.sh` 结尾的为 script；其余带路径的为 reference；裸技能名为 capability。

### 3.2 统计

**按关系**（484 条）：

| 关系 | 条数 |
|---|---|
| `reads-reference` | 155 |
| `runs-script` | 119 |
| `routes-to` | 72 |
| `hands-off-to` | 38 |
| `calls` | 27 |
| `re-enters-at` | 24 |
| `configured-by` | 21 |
| `enforced-by-hook` | 10 |
| `cites-principle` | 9 |
| `wakes` | 5 |
| `starts-with-prompt` | 4 |

**按组件类型对**（源 → 目标，条数；208 个节点的类型分布：reference 59、script 47、capability 34、repo-doc 17、playbook 步骤 9、artifact 9、lint/test 8、config 7、role 5、角色操作文件 5、entry 3、hook 2、principle 2、mode 1）：

| 源 → 目标 | 条数 | 源 → 目标 | 条数 |
|---|---|---|---|
| script → script | 62 | capability → reference | 53 |
| entry → capability | 34 | capability → capability | 31 |
| capability → script | 18 | reference → script | 18 |
| reference → reference | 18 | reference → capability | 14 |
| playbook → playbook（步骤之间） | 14 | playbook → capability | 13 |
| script → config | 12 | repo-doc → repo-doc | 11 |
| 角色操作文件 → script | 10 | script → artifact | 9 |
| 角色操作文件 → capability | 8 | lint/test → script | 8 |
| capability → 角色操作文件 | 7 | 角色操作文件 → reference | 7 |
| script → 角色操作文件 | 7 | repo-doc → capability | 7 |
| lint/test → lint/test | 7 | script → reference | 6 |
| capability → repo-doc | 6 | lint/test → 角色操作文件 | 5 |
| mode → capability | 4 | 角色操作文件 → principle | 4 |
| role → 角色操作文件 | 4 | role → hook | 4 |
| script → capability | 4 | script → role（wakes） | 4 |
| capability → artifact | 4 | entry → mode | 3 |
| mode → playbook | 3 | role → config | 3 |
| hook → script | 3 | hook → 角色操作文件 | 3 |
| 角色操作文件 → hook | 3 | repo-doc → lint/test | 3 |
| repo-doc → 角色操作文件 | 3 | lint/test → reference | 3 |
| mode → principle | 2 | playbook → reference | 2 |
| reference → 角色操作文件 | 2 | 角色操作文件 → repo-doc | 2 |
| reference → artifact | 2 | reference → repo-doc | 2 |
| principle → principle | 2 | script → hook | 2 |
| repo-doc → principle | 2 | lint/test → config | 2 |
| 其余 24 种各 1 条（含 repo-doc → mode） | 24 | | |

**方向规则检查**（R4 §12）：

- capability → playbook：0 条。能力技能不点名 playbook 的顺序。
- capability → mode：0 条。分叉后的 `to-spec`、`to-tickets` 保留各自的后继句，不再指回 `mmw`（K-7）。
- 仓库文档 → mode：1 条，是 SSR（搬到 `docs/skill-set/` 后）以 `mmw` 的文件为范例，只在写技能时读。上游目录里的文件不再指向任何 MMW 组件（K-38）。
- script → 角色操作文件：7 条。`dispatch.sh` 的启动提示词、Memory 索引尾句、reviewer Rules 包与第 4115 行拒绝文字；`watchdog.py` 指向 `### Exit codes of resume`；`verify-ticket.py` 的 `RESUME:` 两种取值（`## Closing steps` 的步骤名与「Claim, read in, write the code」）。都在 `check_wiring.py` 第 1 类范围内。

### 3.3 入边与出边是否齐全

| 检查 | 结果 |
|---|---|
| 没有入边的节点（14 个） | `entry:description`、`entry:slash`（宿主）；`doc:AGENTS.md(root)`（宿主每回合加载）；`role:reviewer`、`role:advisor`（行动者，它们的到达是 `dispatch.sh` 对 `code-review`、`advisor` 的 `starts-with-prompt`）；`tests/run.sh`、`tests/lints`、`tests/relay`（维护者手跑）；`board/board_data.py`、`board/settings_api.py`（board 进程）；`adr:0032`、`adr:0033`、`adr:0034`（维护者读）；`artifact:git commit`（用户提交）。**全是入口或行动者，没有「无人到达」的组件** |
| 36 个技能的入边 | 每个都有入边：模型可触发的有 `entry:description`；7 个用户触发的有 `entry:slash`。另外，`handoff`、`setup-matt-pocock-skills`、`improve-codebase-architecture` 有「告诉用户运行」的入边；`grill-with-docs`、`grill-me`、`teach`、`wait-what` 只有斜杠一个入口，与现状相同 |
| 头部 playbook 步骤的出边 | 9 个步骤节点（含 `## Where you are`）都有出边。**Someone else knows** 的出边是结束回合后经 `## Where you are` 重入。**Spec** 与 **Tickets** 之间、**Tickets** 与 **Hand to the night** 之间不再有步骤顺序边：后继由 `to-spec` `## Next`、`to-tickets` 第 8 步末句持有（K-7），**Tickets**、**Hand to the night** 是重入点 |
| 角色操作文件的出边 | 5 个都有。`advising.md` 唯一的出边是把回答交回发起方（`consulting.md`），它是终点，不是断点 |
| 没有出边的 playbook 步骤 | 0 |
| 已修的断点（今天存在、新连线里消除） | worker 到 `## On waking` 缺路（N10 B9）；`MMW turn guard:` 在 `night.md` `## 3` 没有处理行（R4 V7）；`### Exit codes of resume` 没有退出码（V8）；单票 orchestrator 收到 `relay.recovered` 没有处理行（R5 W3）；夜外 adopt 的会话收到 `ticket.refused`、`child.opened`、`worker.lost` 没有处理行（R5 W2）；reviewer 与 advisor 收到 `NO_QUESTION` 没有承接处（N11 missing_edges[1]、R6 F5）；`watchdog.py` 八种告警里七种在任何技能文本里都没有处理指令（M16，K-46）；被 `resume` 叫醒、还没有运行记录的 worker 没有 `RESUME:` 去处（M17，K-47）。N11 missing_edges 按 0 起的编号逐条处理：[0] 由 K-3 的 turn guard 行处理；[2] `triage/references/pipeline-issues.md` 跑 `events.py`、`--lint`，已补；[3] `retro` 的 `reviewer-rule` 去处，补为 `retro -> artifact:reviewer Rules : hands-off-to`，注明只是提案；[4] `retro.py` 读 `reviewer.reported`，已补；[5] 前半 `pull_design.py` 解析叶子 `README.md` 的 `## State list`，目标是消费仓库里的 `artifact:prototype leaf README`，不是技能里的格式文件（M21），后半 `pull.md` 拆 `prototype` 的 UI scaffolding，已补；[6] `dispatch.sh finish` 读 `spec.retroed`，已补 |

### 3.4 从今天的连线里删掉的边

| 删掉的边 | 取代它的边 | 出处 |
|---|---|---|
| `grill-with-docs -> to-spec`、`wayfinder -> to-spec`、`triage -> to-spec`、`triage -> to-tickets`、`improve-codebase-architecture -> to-spec` | `mmw` Routes 门槛与 `idea-to-tickets#Where you are` | R7 C3、C5、D1、E1、G1 |
| `prototype/UI.md -> design-pages : hands-off-to` | `idea-to-tickets#Runnable questions -> design-pages`；map 路径由 `interface-and-remake.md` 承担 | R7 F1、R8 |
| `write-screen-contract -> to-spec`（map 清空时的从句） | `mmw -> idea-to-tickets#Spec`（wayfinder 行门槛） | R8 2.3 |
| `ui-acceptance -> implement/references/writing-interface-code.md`（表第 1 行） | `implement -> …writing-interface-code.md`（第 16 行已有） | R4 D5.2、R8 |
| `dispatch(description) -> 起 reviewer` 的声称 | `implement` 的 **Review round** | R5 A1 |
| `writing-for-agents -> writing-for-agents/SKILL-SET-RULES.md`（第 8 行） | `doc:AGENTS.md(root) -> doc:SKILL-SET-RULES.md`（第 49 行，今天已有） | K-38 |
| `ask-matt -> implement`、`ask-matt -> tdd`、`ask-matt -> design-pages`、`ask-matt -> write-screen-contract` | 这些边今天就不存在（`ask-matt` 未安装，N11 thin_claims） | — |
| R4 草案中的 `mmw -> exe-release : routes-to`、`mmw -> dispatch : routes-to` | `entry:description -> exe-release`、`entry:description -> dispatch` 加 Routes 兜底句 | K-16 |
| R8 草案中的 `idea-to-tickets -> handoff : calls` | 改为「告诉用户运行 `/handoff`」 | K-10 |

### 3.5 连线全表

```edges
entry:AGENTS.md#mmw -> mmw : routes-to  # R4 D1.4; R10 A5/Q2
entry:description -> mmw : routes-to  # 备用
entry:slash -> mmw : routes-to  # /mmw
mmw -> entry:AGENTS.md#mmw : hands-off-to  # Where you are (b) 补写该行; R4 D1.4
mmw -> idea-to-tickets : routes-to  # Routes「一个想法」
mmw -> idea-to-tickets#Spec : routes-to  # Routes 门槛: map 清空 / triage agent-ready / 获批 retro 提案; R7
mmw -> idea-to-tickets#Who checks : routes-to  # Routes 第 4、5 行：排错后的修法、架构整理定下的决定; K-40
mmw -> wayfinder : routes-to  # Routes
mmw -> triage : routes-to  # Routes（含流水线退回的 needs-triage、contract child）
mmw -> diagnosing-bugs : routes-to  # Routes「有东西坏了」；修法进 Who checks
mmw -> improve-codebase-architecture : routes-to  # 告诉用户运行 /improve-codebase-architecture（不算调用）; R7 G2
mmw -> mmw/references/phase-boundaries.md : reads-reference  # Where you are (c)
mmw -> prompt:shared.md : reads-reference  # 层级优先级句
mmw -> principle:silence-is-never-a-pass : cites-principle  # Principles 索引
mmw -> principle:rerun-dont-reroute : cites-principle  # Principles 索引
mmw/references/phase-boundaries.md -> handoff : routes-to  # 告诉用户运行 /handoff; R7 H3
idea-to-tickets -> idea-to-tickets#Where you are : re-enters-at  # 可重入
idea-to-tickets#Where you are -> idea-to-tickets#Grill : re-enters-at  # 其他 / 带回问卷
idea-to-tickets#Where you are -> idea-to-tickets#Who checks : re-enters-at  # 已有定下的决定
idea-to-tickets#Where you are -> idea-to-tickets#Spec : re-enters-at  # map 清空等
idea-to-tickets#Where you are -> idea-to-tickets#Tickets : re-enters-at  # spec 无票
idea-to-tickets#Where you are -> idea-to-tickets#Hand to the night : re-enters-at  # 票已过 lint
idea-to-tickets#Where you are -> design-pages : re-enters-at  # winner 已记录、无 claude-design/; R8
idea-to-tickets#Where you are -> write-screen-contract : re-enters-at  # pull report 在、无 screen contract; R8
idea-to-tickets#Grill -> grilling : calls
idea-to-tickets#Grill -> domain-modeling : calls
idea-to-tickets#Grill -> research : calls  # R7 H2
idea-to-tickets#Runnable questions -> prototype : calls
idea-to-tickets#Runnable questions -> design-pages : hands-off-to  # UI winner
idea-to-tickets#Runnable questions -> mmw/references/phase-boundaries.md : reads-reference  # 按原文小节「**3. Do you need to hand off?**」点名; K-43
idea-to-tickets#Runnable questions -> handoff : routes-to  # 告诉用户运行 /handoff（宿主无 Claude Design 工具时）; 裁定 K-10
idea-to-tickets#Runnable questions -> idea-to-tickets#Grill : hands-off-to  # LOGIC/EXP 结论回 Grill
idea-to-tickets#Someone else knows -> to-questionnaire : calls
idea-to-tickets#Who checks -> tdd : calls  # No 分支
idea-to-tickets#Who checks -> idea-to-tickets#Spec : hands-off-to  # Yes 分支
idea-to-tickets#Spec -> to-spec : calls
idea-to-tickets#Spec -> mmw/references/phase-boundaries.md : reads-reference  # 上下文门槛
idea-to-tickets#Tickets -> to-tickets : calls
idea-to-tickets#Tickets -> principle:silence-is-never-a-pass : cites-principle  # R11 C1
idea-to-tickets#Hand to the night -> dispatch : hands-off-to
dispatch -> dispatch/references/night.md : routes-to  # Find your moment 第 3 行
dispatch -> dispatch/references/one-ticket.md : routes-to  # 第 4 行
dispatch -> dispatch/references/inside-a-ticket.md : routes-to  # 第 2 行
dispatch -> dispatch/references/editing-models.md : routes-to  # 第 5 行
dispatch -> dispatch/scripts/dispatch.sh : runs-script  # 第 6 行 board
dispatch -> dispatch#On waking : routes-to  # 第 1 行改为先 On waking; R5 A4
dispatch -> implement#Closing steps : routes-to  # 第 1 行：先 On waking，再按 --preflight 的 RESUME:; K-47
dispatch#On waking -> dispatch/scripts/dispatch.sh : runs-script  # ack
dispatch/references/night.md -> dispatch#On waking : reads-reference  # ## 3 第 1 步
dispatch/references/night.md -> dispatch/scripts/dispatch.sh : runs-script  # check/open/advance/status/resume/retract/findings/route/memory-list/reverify/summary/finish/suspend
dispatch/references/night.md -> verify-ticket/scripts/verify-ticket.py : runs-script  # --lint
dispatch/references/night.md -> verify-ticket/scripts/events.py : runs-script  # fold
dispatch/references/night.md -> ui-acceptance/scripts/target_config.py : runs-script  # --check
dispatch/references/night.md -> ui-acceptance/scripts/lease.py : runs-script  # release
dispatch/references/night.md -> to-tickets : reads-reference  # <issue-template>
dispatch/references/night.md -> to-spec/references/revising-a-spec.md : reads-reference  # contract
dispatch/references/night.md -> design-pages/references/pull.md : reads-reference  # contract child
dispatch/references/night.md -> retro : calls  # ## 5
dispatch/references/night.md -> principle:silence-is-never-a-pass : cites-principle  # 第 127 行; R11 C4
dispatch/references/night.md -> principle:rerun-dont-reroute : cites-principle  # 第 82 行; R11 C10
dispatch/references/one-ticket.md -> dispatch#On waking : reads-reference
dispatch/references/one-ticket.md -> dispatch/references/night.md#3 : reads-reference  # contract/relay.recovered/watchdog 行; R5 C2
dispatch/references/one-ticket.md -> dispatch/scripts/dispatch.sh : runs-script  # open-ticket/start/land/ack
dispatch/references/one-ticket.md -> verify-ticket/scripts/events.py : runs-script  # fold
dispatch/references/inside-a-ticket.md -> dispatch/scripts/dispatch.sh : runs-script  # adopt/ack
dispatch/references/inside-a-ticket.md -> implement : hands-off-to
dispatch/references/editing-models.md -> dispatch/scripts/models.py : runs-script  # config set/runner/show
role:orchestrator -> dispatch/references/night.md : re-enters-at  # status 首行 RESUME:; R5 J1
role:orchestrator -> dispatch/references/night.md#3 : re-enters-at  # 指针 by=open
role:orchestrator -> dispatch/references/one-ticket.md : re-enters-at  # 指针 by=open-ticket
role:orchestrator -> hook:turn-guard.py : enforced-by-hook
role:worker -> dispatch#On waking : re-enters-at  # 指针
role:worker -> implement#Closing steps : re-enters-at  # 指针 → --preflight 的 RESUME:（「A ticket you are prompted back into」一句）; K-47
role:worker -> dispatch/references/inside-a-ticket.md#After the closeout : re-enters-at  # 指针 by=adopt; R5 D1/H3
role:worker -> hook:tool-guard.py : enforced-by-hook
role:reviewer -> hook:tool-guard.py : enforced-by-hook
role:advisor -> hook:tool-guard.py : enforced-by-hook  # 在 issue-<n> 工作树里被咨询时; R6 F5
role:worker -> config:models.json : configured-by  # junior-worker/senior-worker
role:reviewer -> config:models.json : configured-by
role:advisor -> config:models.json : configured-by
dispatch/scripts/dispatch.sh -> implement : starts-with-prompt  # Use the implement skill（第 1949 行）
dispatch/scripts/dispatch.sh -> code-review : starts-with-prompt  # 第 1967 行
dispatch/scripts/dispatch.sh -> advisor : starts-with-prompt  # 第 2072 行
dispatch/scripts/dispatch.sh -> ui-acceptance#Five rules while the product is running : starts-with-prompt  # PRODUCT_RULES
dispatch/scripts/dispatch.sh -> implement#Shared experience while implementing : reads-reference  # Memory 索引尾句
dispatch/scripts/dispatch.sh -> code-review/references/session.md#Active Rules : reads-reference  # reviewer Rules 包
dispatch/scripts/dispatch.sh -> advisor/references/consulting.md#The brief : reads-reference  # 拒绝文字
dispatch/scripts/dispatch.sh -> dispatch/references/night.md : reads-reference  # 第 4115 行拒绝文字
dispatch/scripts/dispatch.sh -> resolving-merge-conflicts : routes-to  # integrate 拒绝文字
dispatch/scripts/dispatch.sh -> role:worker : wakes  # resume，同一行接指针
dispatch/scripts/dispatch.sh -> dispatch/scripts/relay.py : runs-script  # start/add --by/stop/watching/ack/pointer
dispatch/scripts/dispatch.sh -> dispatch/scripts/status.py : runs-script
dispatch/scripts/dispatch.sh -> dispatch/scripts/models.py : runs-script
dispatch/scripts/dispatch.sh -> dispatch/scripts/runners : runs-script
dispatch/scripts/dispatch.sh -> verify-ticket/scripts/events.py : runs-script
dispatch/scripts/dispatch.sh -> verify-ticket/scripts/verify-ticket.py : runs-script  # --reverify；import run_target_json_checks
dispatch/scripts/dispatch.sh -> ui-acceptance/scripts/lease.py : runs-script
dispatch/scripts/dispatch.sh -> artifact:checker command : runs-script  # .mmw/target.json checks
dispatch/scripts/dispatch.sh -> install.sh : runs-script  # check 调 --check
dispatch/scripts/dispatch.sh -> entry:AGENTS.md#mmw : reads-reference  # check 缺行只读警告
dispatch/scripts/dispatch.sh -> tracker:events : reads-reference  # finish 前置 spec.retroed; N11 missing_edges[6]
dispatch/scripts/dispatch.sh -> config:models.json : configured-by
dispatch/scripts/dispatch.sh -> config:hosts.json : configured-by
dispatch/scripts/relay.py -> role:orchestrator : wakes  # ticket.passed/returned/refused、child.opened、worker.lost、relay.recovered；同一行接指针
dispatch/scripts/relay.py -> role:worker : wakes  # reviewer.reported/lost（WAKES）、worker.queued（QUEUED，单独定义）
dispatch/scripts/relay.py -> dispatch/scripts/anchors.py : reads-reference  # 角色指针表
dispatch/scripts/relay.py -> dispatch/scripts/runners : runs-script  # send/liveness
dispatch/scripts/relay.py -> dispatch/scripts/statedir.py : runs-script
dispatch/scripts/relay.py -> dispatch/scripts/ghlist.py : runs-script
dispatch/scripts/relay.py -> verify-ticket/scripts/events.py : runs-script
dispatch/scripts/relay.py -> tracker:events : reads-reference
dispatch/scripts/relay.py -> config:watches.json : configured-by  # watch、runner、session、by
dispatch/scripts/watchdog.py -> dispatch/scripts/relay.py : runs-script  # 导入
dispatch/scripts/watchdog.py -> role:orchestrator : wakes  # 八种 watchdog: 告警，每种在同一行写出下一步并接指针；by=adopt 时收件人是 worker 自己; K-46
dispatch/scripts/watchdog.py -> dispatch/scripts/anchors.py : reads-reference
dispatch/scripts/watchdog.py -> dispatch/references/night.md#Exit codes of resume : reads-reference
dispatch/scripts/watchdog.py -> dispatch/scripts/runners : runs-script
dispatch/scripts/status.py -> verify-ticket/scripts/events.py : runs-script
dispatch/scripts/status.py -> verify-ticket/scripts/issue_tree.py : runs-script
dispatch/scripts/status.py -> dispatch/scripts/anchors.py : reads-reference  # RESUME: 小节标题
dispatch/scripts/models.py -> config:hosts.json : configured-by
dispatch/scripts/models.py -> config:models.json : configured-by
hook:turn-guard.py -> dispatch/scripts/watchdog.py : runs-script  # arm
hook:turn-guard.py -> role:orchestrator : wakes  # MMW turn guard: 拦回合
hook:tool-guard.py -> implement#Put no question on the screen : routes-to  # NO_QUESTION
hook:tool-guard.py -> code-review/references/session.md#Could not tell : routes-to  # NO_QUESTION
hook:tool-guard.py -> advisor/references/advising.md#Missing information gets named precisely : routes-to  # NO_QUESTION; R6 X3
hook:tool-guard.py -> dispatch/scripts/anchors.py : reads-reference
hook:tool-guard.py -> ui-acceptance/scripts/refusal.py : runs-script
implement -> dispatch/references/inside-a-ticket.md : reads-reference
implement -> dispatch/scripts/dispatch.sh : runs-script  # integrate/start reviewer/wait/ack
implement -> verify-ticket/scripts/verify-ticket.py : runs-script  # --preflight/判据/--decisions/--reverify/--touched/--draft/--closeout/--sub-issue
implement -> implement/references/writing-interface-code.md : reads-reference
implement -> implement/references/saving-memory.md : reads-reference
implement -> verify-ticket/references/sub-issues.md : reads-reference
implement -> tdd : calls
implement -> resolving-merge-conflicts : calls
implement -> ui-acceptance#Five rules while the product is running : reads-reference
implement -> ext:nmem : runs-script
implement -> doc:CONTEXT-MAP.md : reads-reference
implement -> doc:CODING_STANDARDS.md : reads-reference  # 票 Read first 点名时
implement -> principle:silence-is-never-a-pass : cites-principle  # 第 96 行; R11 C3
implement -> principle:rerun-dont-reroute : cites-principle  # 第 18 行; R11 C11
implement#Close out -> hook:tool-guard.py : enforced-by-hook
implement#Put no question on the screen -> hook:tool-guard.py : enforced-by-hook
implement/references/saving-memory.md -> ext:nmem : runs-script
implement/references/writing-interface-code.md -> ui-acceptance/scripts/story-parity.py : runs-script  # --render-only
implement/references/writing-interface-code.md -> ui-acceptance/references/story-parity.md : reads-reference
implement/references/writing-interface-code.md -> ui-acceptance/references/boundary-check.md : reads-reference
implement/references/writing-interface-code.md -> tdd : reads-reference
implement/references/writing-interface-code.md -> verify-ticket/scripts/verify-ticket.py : runs-script  # --sub-issue contract
implement/references/writing-interface-code.md -> design-pages/references/pull.md : hands-off-to  # child 正文点名
verify-ticket/scripts/verify-ticket.py -> implement#Closing steps : re-enters-at  # RESUME: <步骤名>
verify-ticket/scripts/verify-ticket.py -> implement#Claim, read in, write the code : re-enters-at  # resume_at 新取值（有认领、没有运行记录）; K-47
verify-ticket/scripts/verify-ticket.py -> verify-ticket/scripts/gate-check : runs-script  # gate-check.mjs、gate-lint.mjs
verify-ticket/scripts/verify-ticket.py -> verify-ticket/scripts/events.py : runs-script
verify-ticket/scripts/verify-ticket.py -> verify-ticket/scripts/issue_tree.py : runs-script
verify-ticket/scripts/verify-ticket.py -> config:.mmw/target.json : configured-by
verify-ticket/scripts/verify-ticket.py -> artifact:checker command : runs-script  # --closeout
verify-ticket/scripts/verify-ticket.py -> ui-acceptance/scripts/story-parity.py : runs-script  # CHECK:
verify-ticket/scripts/verify-ticket.py -> ui-acceptance/scripts/boundary-check.py : runs-script  # CHECK:
verify-ticket/scripts/verify-ticket.py -> ui-acceptance/scripts/journey.py : runs-script  # CHECK:
verify-ticket/scripts/verify-ticket.py -> ui-acceptance/scripts/harness-guard.py : runs-script  # CHECK:
verify-ticket/scripts/verify-ticket.py -> ui-acceptance/scripts/lease.py : runs-script
verify-ticket/scripts/verify-ticket.py -> write-screen-contract/scripts/lint_screen_contract.py : runs-script
verify-ticket/scripts/verify-ticket.py -> tracker:events : hands-off-to  # 贴事件
verify-ticket -> verify-ticket/references/sub-issues.md : routes-to
verify-ticket -> verify-ticket/references/linting.md : routes-to
verify-ticket -> implement : hands-off-to  # 第 16 行保留; 裁定 K-6
verify-ticket -> ui-acceptance : hands-off-to  # Reached from here
verify-ticket/references/sub-issues.md -> implement : reads-reference
verify-ticket/references/sub-issues.md -> ui-acceptance#Five rules while the product is running : reads-reference
verify-ticket/references/sub-issues.md -> verify-ticket/scripts/verify-ticket.py : runs-script
verify-ticket/references/linting.md -> verify-ticket/scripts/verify-ticket.py : runs-script  # --lint
code-review -> code-review/references/session.md : routes-to
code-review -> code-review/references/standards-reviewer.md : routes-to
code-review -> code-review/references/spec-reviewer.md : routes-to
code-review -> code-review/references/tests-reviewer.md : routes-to
code-review -> code-review/references/ui-reviewer.md : routes-to
code-review/references/session.md -> code-review : calls  # 每个 axis 一句提示词
code-review/references/session.md -> verify-ticket/scripts/verify-ticket.py : runs-script  # --review
code-review/references/session.md#Could not tell -> hook:tool-guard.py : enforced-by-hook
code-review/references/standards-reviewer.md -> doc:CODING_STANDARDS.md : reads-reference
code-review/references/spec-reviewer.md -> dispatch/scripts/dispatch.sh : runs-script  # integrated
code-review/references/tests-reviewer.md -> tdd/tests.md : reads-reference
code-review/references/tests-reviewer.md -> tdd/mocking.md : reads-reference
code-review/references/tests-reviewer.md -> doc:TESTING.md : reads-reference
code-review/references/ui-reviewer.md -> ui-acceptance/scripts/story-parity.py : runs-script
tdd -> codebase-design : reads-reference
advisor -> advisor/references/consulting.md : routes-to
advisor -> advisor/references/advising.md : routes-to
advisor/references/consulting.md -> dispatch/scripts/dispatch.sh : runs-script  # advise
retro -> retro/scripts/retro.py : runs-script  # gather/search/finalize
retro -> writing-for-agents : calls  # 第 11 步
retro -> dispatch/references/night.md#5 : hands-off-to  # 第 186 行保留; 裁定 K-7
retro -> triage : hands-off-to  # needs-triage 提案 issue
retro -> artifact:reviewer Rules : hands-off-to  # reviewer-rule 去处只是提案，retro 不直接写 Rule（retro/SKILL.md 第 198 行）; N11 missing_edges[3]
retro/scripts/retro.py -> verify-ticket/scripts/events.py : runs-script
retro/scripts/retro.py -> verify-ticket/scripts/issue_tree.py : runs-script
retro/scripts/retro.py -> ui-acceptance/scripts/refusal.py : runs-script
retro/scripts/retro.py -> tracker:events : reads-reference  # 含 reviewer.reported（N11 missing_edges[4]）
retro/scripts/retro.py -> ext:nmem : runs-script  # Retro Memory
to-spec -> to-spec/references/revising-a-spec.md : reads-reference
to-spec -> to-spec/references/several-specs.md : reads-reference
to-spec -> verify-ticket/scripts/verify-ticket.py : runs-script  # --publish/--lint
to-spec -> ui-acceptance/scripts/target_config.py : runs-script
to-spec -> write-screen-contract#Reverse sweep : re-enters-at
to-spec -> wayfinder : re-enters-at  # alignment ticket
to-spec -> doc:docs/agents : reads-reference  # issue-tracker.md、domain.md
to-spec -> artifact:screen-contract.yaml : reads-reference
to-spec -> setup-matt-pocock-skills : routes-to  # 告诉用户运行
to-spec -> to-tickets : hands-off-to  # ## Next（分叉后自有，保留）; K-7
to-tickets -> to-spec : re-enters-at  # 无 spec 或第 4 步第 2 问
to-tickets -> to-spec/references/revising-a-spec.md : reads-reference
to-tickets -> to-tickets/references/ambiguity-scan.md : reads-reference
to-tickets -> to-tickets/references/cutting-interface-tickets.md : reads-reference
to-tickets -> to-tickets/references/person-ticket.md : reads-reference
to-tickets -> verify-ticket/scripts/verify-ticket.py : runs-script  # --lint/--publish
to-tickets -> doc:docs/agents : reads-reference  # triage-labels.md
to-tickets -> setup-matt-pocock-skills : routes-to  # 告诉用户运行
to-tickets -> dispatch : hands-off-to  # 第 8 步末句（批次是整夜运行时，保留）; K-7
to-tickets/references/cutting-interface-tickets.md -> ui-acceptance/references/boundary-check.md : reads-reference
to-tickets/references/cutting-interface-tickets.md -> ui-acceptance/references/story-parity.md : reads-reference
to-tickets/references/cutting-interface-tickets.md -> ui-acceptance/references/journey.md : reads-reference
to-tickets/references/cutting-interface-tickets.md -> ui-acceptance/references/product-answers.md : reads-reference
to-tickets/references/cutting-interface-tickets.md -> to-tickets/references/person-ticket.md : reads-reference
triage -> triage/references/pipeline-issues.md : reads-reference
triage -> triage/AGENT-BRIEF.md : reads-reference
triage -> triage/OUT-OF-SCOPE.md : reads-reference
triage -> to-tickets/references/person-ticket.md : reads-reference
triage -> grilling : calls
triage -> domain-modeling : calls
triage -> doc:docs/agents : reads-reference  # triage-labels.md、issue-tracker.md
triage -> setup-matt-pocock-skills : routes-to  # 告诉用户运行
triage/references/pipeline-issues.md -> verify-ticket/scripts/events.py : runs-script  # N11 missing_edges[2]
triage/references/pipeline-issues.md -> verify-ticket/scripts/verify-ticket.py : runs-script  # --lint
triage/references/pipeline-issues.md -> dispatch/scripts/dispatch.sh : runs-script  # route/resume（含移入的 route 句; R7 C4）
triage/references/pipeline-issues.md -> to-tickets : reads-reference  # <issue-template>
triage/references/pipeline-issues.md -> design-pages/references/pull.md : hands-off-to  # contract child
triage/references/pipeline-issues.md -> dispatch : hands-off-to
wayfinder -> grilling : calls
wayfinder -> domain-modeling : calls
wayfinder -> prototype : calls
wayfinder -> research : calls
wayfinder -> wayfinder/references/interface-and-remake.md : reads-reference
wayfinder -> doc:docs/agents : reads-reference  # issue-tracker.md Wayfinding operations
wayfinder -> setup-matt-pocock-skills : routes-to  # 告诉用户运行
wayfinder/references/interface-and-remake.md -> design-pages : hands-off-to
wayfinder/references/interface-and-remake.md -> write-screen-contract : hands-off-to
grill-me -> grilling : calls
grill-with-docs -> grilling : calls
grill-with-docs -> domain-modeling : calls
domain-modeling -> domain-modeling/CONTEXT-FORMAT.md : reads-reference
domain-modeling -> domain-modeling/ADR-FORMAT.md : reads-reference
prototype -> prototype/LOGIC.md : reads-reference
prototype -> prototype/UI.md : reads-reference
prototype -> prototype/EXP.md : reads-reference
prototype/EXP.md -> prototype/evidence-page.md : reads-reference
prototype/UI.md -> design-pages/references/state-list-format.md : reads-reference  # 第 6 步留一句指针; K-14
improve-codebase-architecture -> codebase-design : calls
improve-codebase-architecture -> grilling : calls
improve-codebase-architecture -> domain-modeling : calls
improve-codebase-architecture -> diagram-design : calls
improve-codebase-architecture -> improve-codebase-architecture/HTML-REPORT.md : reads-reference
codebase-design -> codebase-design/DEEPENING.md : reads-reference
codebase-design -> codebase-design/DESIGN-IT-TWICE.md : reads-reference
diagnosing-bugs -> diagnosing-bugs/scripts/hitl-loop.template.sh : runs-script
wizard -> wizard/template.sh : runs-script
wait-what -> wait-what/VISUAL.md : reads-reference
wait-what/VISUAL.md -> diagram-design : calls
teach -> teach/FORMAT files : reads-reference
setup-matt-pocock-skills -> setup-matt-pocock-skills/seeds : reads-reference
setup-matt-pocock-skills -> doc:docs/agents : hands-off-to  # 写出落地件
design-pages -> design-pages/references/edit-pages.md : reads-reference
design-pages -> design-pages/references/draw.md : reads-reference
design-pages -> design-pages/references/pull.md : reads-reference
design-pages -> design-pages/references/design-system.md : reads-reference
design-pages -> design-pages/references/state-list-format.md : reads-reference  # ## The state list 改按文件名; K-14
design-pages/references/design-system.md -> design-pages/references/state-list-format.md : reads-reference  # 第 42 行格式括注改为同技能内引用; K-14
design-pages/references/design-system.md -> design-pages/references/template-design-system-claude-md.md : reads-reference
design-pages/references/edit-pages.md -> design-pages/references/template-project-claude-md.md : reads-reference
design-pages/references/edit-pages.md -> design-pages/references/pull.md : hands-off-to  # ## Next
design-pages/references/pull.md -> design-pages/scripts/pull_design.py : runs-script
design-pages/references/pull.md -> write-screen-contract : hands-off-to  # Reached from here
design-pages/references/pull.md -> write-screen-contract#Re-runs : re-enters-at
design-pages/references/pull.md -> wayfinder : hands-off-to
design-pages/references/pull.md -> artifact:prototype UI scaffolding : reads-reference  # ## After the first pull 拆掉 prototype 的 UI scaffolding（实际关系：移除，借最近的词）; N11 missing_edges[5]
design-pages/references/pull.md -> dispatch/scripts/dispatch.sh : runs-script  # reverify/route/resume
design-pages/references/pull.md -> verify-ticket/scripts/verify-ticket.py : runs-script
design-pages/scripts/pull_design.py -> design-pages/scripts/check_editable_selectors.py : runs-script
design-pages/scripts/pull_design.py -> ui-acceptance/scripts/design_render.py : runs-script
design-pages/scripts/pull_design.py -> ui-acceptance/scripts/refusal.py : runs-script
design-pages/scripts/pull_design.py -> artifact:prototype leaf README : reads-reference  # 解析消费仓库叶子 README.md 的 ## State list（第 983 行）; N11 missing_edges[5]
write-screen-contract -> write-screen-contract/references/screen-contract-format.md : reads-reference
write-screen-contract -> write-screen-contract/scripts/extract_skeleton.py : runs-script
write-screen-contract -> write-screen-contract/scripts/lint_screen_contract.py : runs-script
write-screen-contract -> write-screen-contract/scripts/dump_openapi.py : runs-script
write-screen-contract -> artifact:screen-contract.yaml : hands-off-to
write-screen-contract -> to-spec : hands-off-to  # ## Next
write-screen-contract -> to-spec/references/revising-a-spec.md : hands-off-to
write-screen-contract -> wayfinder : hands-off-to  # 只交回 wayfinder（第 4 批删 to-spec 从句）
write-screen-contract/scripts/extract_skeleton.py -> ui-acceptance/scripts/design_render.py : runs-script
write-screen-contract/scripts/lint_screen_contract.py -> write-screen-contract/references/screen-contract-format.md : reads-reference  # 拒绝文字
to-spec/references/revising-a-spec.md -> write-screen-contract#Re-runs : reads-reference
ui-acceptance -> ui-acceptance/references/story-parity.md : reads-reference
ui-acceptance -> ui-acceptance/references/boundary-check.md : reads-reference
ui-acceptance -> ui-acceptance/references/journey.md : reads-reference
ui-acceptance -> ui-acceptance/references/harness-guard.md : reads-reference
ui-acceptance -> ui-acceptance/references/product-answers.md : reads-reference
ui-acceptance -> to-tickets/references/cutting-interface-tickets.md : hands-off-to  # 表第 3 行
ui-acceptance -> ui-acceptance/scripts/target_config.py : runs-script
ui-acceptance -> ui-acceptance/scripts/harness-guard.py : runs-script
ui-acceptance -> ui-acceptance/scripts/lease.py : runs-script
ui-acceptance#Five rules while the product is running -> hook:tool-guard.py : enforced-by-hook  # 规则 1
ui-acceptance/scripts/story-parity.py -> ui-acceptance/scripts/design_render.py : runs-script
ui-acceptance/scripts/story-parity.py -> ui-acceptance/scripts/pixel_diff.py : runs-script
ui-acceptance/scripts/story-parity.py -> ui-acceptance/scripts/lease.py : runs-script
ui-acceptance/scripts/story-parity.py -> ui-acceptance/scripts/target_config.py : runs-script
ui-acceptance/scripts/story-parity.py -> ui-acceptance/scripts/refusal.py : runs-script
ui-acceptance/scripts/story-parity.py -> artifact:screen-contract.yaml : reads-reference
ui-acceptance/scripts/story-parity.py -> write-screen-contract/references/screen-contract-format.md : reads-reference  # 拒绝文字
ui-acceptance/scripts/story-parity.py -> config:.mmw/target.json : configured-by
ui-acceptance/scripts/journey.py -> ui-acceptance/scripts/target_config.py : runs-script
ui-acceptance/scripts/journey.py -> ui-acceptance/scripts/lease.py : runs-script
ui-acceptance/scripts/journey.py -> ui-acceptance/references/journey.md : reads-reference  # 拒绝文字
ui-acceptance/scripts/journey.py -> config:.mmw/target.json : configured-by
ui-acceptance/scripts/boundary-check.py -> ui-acceptance/scripts/lease.py : runs-script
ui-acceptance/scripts/boundary-check.py -> ui-acceptance/scripts/refusal.py : runs-script
ui-acceptance/scripts/harness-guard.py -> ui-acceptance/scripts/lease.py : runs-script
ui-acceptance/scripts/harness-guard.py -> config:.mmw/target.json : configured-by
ui-acceptance/scripts/target_config.py -> ui-acceptance/scripts/lease.py : runs-script
ui-acceptance/scripts/target_config.py -> ui-acceptance/references/product-answers.md : reads-reference  # 拒绝文字
ui-acceptance/scripts/lease.py -> config:.mmw/target.json : configured-by
exe-release -> exe-release/scripts/release-flow.sh : runs-script
exe-release -> exe-release/references/driving.md : reads-reference
exe-release -> exe-release/references/new-product.md : reads-reference
exe-release -> role:user : hands-off-to  # 第 5 步安装实测
exe-release/references/new-product.md -> exe-release/references/key.md : reads-reference
exe-release/references/driving.md -> exe-release/scripts/release-flow.sh : re-enters-at  # where
exe-release/references/key.md -> exe-release/scripts/verify_key.py : runs-script
exe-release/references/key.md -> exe-release/scripts/release_script_assembler.py : runs-script
exe-release/scripts/release-flow.sh -> exe-release/scripts/release_contracts.py : runs-script
exe-release/scripts/release-flow.sh -> exe-release/scripts/verify_key.py : runs-script
exe-release/scripts/release-flow.sh -> exe-release/scripts/release_script_assembler.py : runs-script
exe-release/scripts/release-flow.sh -> exe-release/scripts/diagnose_core.py : runs-script
exe-release/scripts/release-flow.sh -> exe-release/scripts/fix_dispatch.py : runs-script
exe-release/scripts/release-flow.sh -> config:release manifest : configured-by
exe-release/scripts/release_script_assembler.py -> exe-release/scripts/builders/nuitka.py : runs-script
exe-release/scripts/release_script_assembler.py -> exe-release/scripts/release_templates : reads-reference
code-checkers -> code-checkers/references/python.md : reads-reference
code-checkers -> code-checkers/references/typescript.md : reads-reference
code-checkers -> code-checkers/references/git-hooks.md : reads-reference
code-checkers -> manage-agents-md : reads-reference  # 第 8 步按其标题写行
code-checkers -> artifact:checker command : hands-off-to
artifact:checker command -> config:.mmw/target.json : configured-by
artifact:git commit -> artifact:prek pre-commit hook : enforced-by-hook  # 消费仓库的 git hook
manage-agents-md -> manage-agents-md/scripts/check.sh : runs-script
manage-agents-md -> manage-agents-md/references/create.md : reads-reference
manage-agents-md -> manage-agents-md/references/rewrite.md : reads-reference
manage-agents-md/references/create.md -> manage-agents-md : re-enters-at
manage-agents-md/references/rewrite.md -> manage-agents-md : re-enters-at
manage-agents-md -> code-checkers : routes-to  # 报告里建议（告诉用户）
manage-agents-md -> doc:AGENTS.md family : hands-off-to  # AGENTS.md、CLAUDE.md、CODING_STANDARDS.md、TESTING.md
diagram-design -> diagram-design/references : reads-reference
diagram-design -> diagram-design/scripts : runs-script
diagram-design -> diagram-design/repo-root/scripts : runs-script
diagram-design -> config:.diagram-design : configured-by
writing-for-agents -> writing-for-agents/SKILL-MECHANICS.md : reads-reference
doc:SKILL-SET-RULES.md -> doc:REVIEWING-A-SKILL-SET.md : reads-reference  # 两份第 2 批搬到 docs/skill-set/; K-38
doc:SKILL-SET-RULES.md -> mmw : reads-reference  # ## Layers of the set 以其文件为范例
doc:SKILL-SET-RULES.md -> writing-for-agents : reads-reference  # 开头先指上游 SKILL.md 的杠杆与失败模式名; K-38
doc:REVIEWING-A-SKILL-SET.md -> lint:check_wiring.py : runs-script
doc:AGENTS.md(root) -> doc:SKILL-SET-RULES.md : reads-reference  # External References 第 49 行改路径; K-38
principle:rerun-dont-reroute -> principle:silence-is-never-a-pass : cites-principle  # Not
principle:silence-is-never-a-pass -> principle:rerun-dont-reroute : cites-principle  # Not
principle:rerun-dont-reroute -> prompt:shared.md : reads-reference  # Boundaries 按原句引规则 11
install.sh -> config:skills.txt : configured-by  # 装全部技能（含 self/mmw、四个分叉）
install.sh -> prompt/render.py : runs-script
install.sh -> dispatch/scripts/models.py : runs-script
install.sh -> dispatch/scripts/relay.py : runs-script  # --check 列出开着的 watch（read_watches）与持锁的 relay、watchdog 进程; R10 I2、K-32
install.sh -> hook:tool-guard.py : configured-by  # 注册
install.sh -> hook:turn-guard.py : configured-by  # 注册
prompt/render.py -> prompt:shared.md : reads-reference
prompt/render.py -> prompt/hosts : reads-reference
doc:AGENTS.md(root) -> entry:AGENTS.md#mmw : routes-to  # 本仓也是消费仓库
doc:AGENTS.md(root) -> dispatch/references/night.md : reads-reference  # 改为技能名写法; R10 A4
doc:AGENTS.md(root) -> doc:CONTEXT-MAP.md : reads-reference
doc:AGENTS.md(root) -> doc:CODING_STANDARDS.md : reads-reference
doc:AGENTS.md(root) -> doc:TESTING.md : reads-reference
doc:AGENTS.md(root) -> doc:docs/adr : reads-reference
doc:AGENTS.md(root) -> doc:merge-notes : reads-reference
doc:AGENTS.md(root) -> doc:downstream-notes : reads-reference
doc:AGENTS.md(root) -> lint:shared_lints.sh : runs-script  # 只改技能文字时的最小检查
doc:CONTEXT-MAP.md -> doc:docs/contexts : reads-reference
doc:docs/contexts -> implement : reads-reference  # _Home_ 分叉后路径
doc:docs/contexts -> code-review : reads-reference  # _Home_
doc:docs/contexts -> to-spec : reads-reference  # _Home_
doc:docs/contexts -> to-tickets : reads-reference  # _Home_
doc:merge-notes -> implement : reads-reference  # 分叉表
doc:merge-notes -> code-review : reads-reference  # 分叉表
doc:merge-notes -> to-spec : reads-reference  # 分叉表
doc:merge-notes -> to-tickets : reads-reference  # 分叉表
doc:merge-notes -> mmw/references/phase-boundaries.md : reads-reference  # merge-notes/ask-matt.md
doc:merge-notes -> lint:check_wiring.py : enforced-by-hook  # 推导规则由第 3 类检查（非宿主 hook，借用最近的关系词）
adr:0032 -> adr:0020 : hands-off-to  # amends
adr:0033 -> doc:merge-notes : reads-reference  # 分叉与调用开关推导规则的决定，落地在 merge-notes/README.md
adr:0034 -> principle:silence-is-never-a-pass : reads-reference  # slug→依据对照（不在原则文件里写 ADR 号）
adr:0034 -> principle:rerun-dont-reroute : reads-reference
board/settings_api.py -> dispatch/scripts/models.py : runs-script
board/board_data.py -> verify-ticket/scripts/events.py : runs-script
board/board_data.py -> verify-ticket/scripts/issue_tree.py : runs-script
board/board_data.py -> dispatch/scripts/ghlist.py : runs-script  # 第 27 行按路径载入
board/supervisor.py -> dispatch/scripts/statedir.py : runs-script
dispatch/scripts/dispatch.sh -> board/supervisor.py : runs-script  # board
tests/run.sh -> lint:shared_lints.sh : runs-script  # 13 个套件
lint:shared_lints.sh -> lint:check_module_paths.py : runs-script
lint:shared_lints.sh -> lint:check_upstream_em_dashes.py : runs-script
lint:shared_lints.sh -> lint:check_own_skill_frontmatter.py : runs-script
lint:shared_lints.sh -> lint:check_wiring.py : runs-script
lint:check_own_skill_frontmatter.py -> config:skills.txt : configured-by  # 另查 name == 目录名
lint:check_wiring.py -> lint:check_own_skill_frontmatter.py : runs-script  # 复用解析
lint:check_wiring.py -> config:skills.txt : configured-by
lint:check_wiring.py -> dispatch/scripts/anchors.py : reads-reference  # 第 1 类
lint:check_wiring.py -> dispatch/scripts/relay.py : reads-reference  # 第 2 类 WAKES、worker.queued、relay.recovered; K-46
lint:check_wiring.py -> dispatch/scripts/watchdog.py : reads-reference  # 第 2 类：每种告警前缀都带下一步或指针; K-46
lint:check_wiring.py -> verify-ticket/scripts/verify-ticket.py : reads-reference  # 第 1 类模式扫描：resume_at 印的步骤名等于 implement 的标题与步骤名; K-2
lint:check_wiring.py -> dispatch/scripts/dispatch.sh : reads-reference  # 第 1 类模式扫描（含第 4115 行）；第 3 类启动提示词
lint:check_wiring.py -> implement : reads-reference  # 第 1 类步骤名；第 2 类 WORKER 处理行
lint:check_wiring.py -> dispatch/references/night.md : reads-reference  # 第 1、2 类
lint:check_wiring.py -> dispatch/references/one-ticket.md : reads-reference  # 第 2 类
lint:check_wiring.py -> dispatch/references/inside-a-ticket.md : reads-reference  # 第 2 类
lint:check_wiring.py -> code-review/references/session.md : reads-reference  # 第 1 类
lint:check_wiring.py -> advisor/references/advising.md : reads-reference  # 第 1 类
lint:check_wiring.py -> advisor/references/consulting.md : reads-reference  # 第 1 类
lint:check_wiring.py -> ui-acceptance : reads-reference  # 第 1 类 Five rules 标题
lint:check_wiring.py -> ui-acceptance/scripts : reads-reference  # 第 1 类模式扫描（journey/story-parity/target_config）
lint:check_wiring.py -> write-screen-contract/scripts/lint_screen_contract.py : reads-reference  # 第 1 类模式扫描
lint:check_wiring.py -> design-pages/references/state-list-format.md : reads-reference  # 第 1 类：pull_design.py 的 ## State list 字面与格式文件一致
lint:check_wiring.py -> mmw : reads-reference  # 第 3、5 类
lint:check_wiring.py -> idea-to-tickets : reads-reference  # 第 3、5 类
tests/lints -> lint:check_wiring.py : runs-script  # 每类一个反例
tests/relay -> dispatch/scripts/anchors.py : reads-reference  # 与常量比较，不抄字面; R10 T5
idea-to-tickets -> idea-to-tickets#Grill : hands-off-to  # 步骤顺序
idea-to-tickets#Grill -> idea-to-tickets#Runnable questions : hands-off-to  # 步骤顺序（要运行才能回答时）
idea-to-tickets#Grill -> idea-to-tickets#Someone else knows : hands-off-to  # 步骤顺序（答案在别人那里时）
idea-to-tickets#Grill -> idea-to-tickets#Who checks : hands-off-to  # 步骤顺序
idea-to-tickets#Runnable questions -> idea-to-tickets#Spec : hands-off-to  # UI 链经 write-screen-contract 结尾回到 Spec
idea-to-tickets#Someone else knows -> idea-to-tickets#Where you are : re-enters-at  # 结束回合，问卷带回后重入
advisor/references/advising.md -> advisor/references/consulting.md : hands-off-to  # 回答留在会话里，由发起方按 consulting.md 对待
entry:description -> code-review : routes-to  # 宿主技能列表
entry:description -> codebase-design : routes-to  # 宿主技能列表
entry:description -> diagnosing-bugs : routes-to  # 宿主技能列表
entry:description -> domain-modeling : routes-to  # 宿主技能列表
entry:slash -> grill-with-docs : routes-to  # 用户斜杠
entry:description -> implement : routes-to  # 宿主技能列表
entry:slash -> improve-codebase-architecture : routes-to  # 用户斜杠
entry:description -> prototype : routes-to  # 宿主技能列表
entry:description -> research : routes-to  # 宿主技能列表
entry:description -> resolving-merge-conflicts : routes-to  # 宿主技能列表
entry:slash -> setup-matt-pocock-skills : routes-to  # 用户斜杠
entry:description -> tdd : routes-to  # 宿主技能列表
entry:description -> to-spec : routes-to  # 宿主技能列表
entry:description -> to-tickets : routes-to  # 宿主技能列表
entry:description -> triage : routes-to  # 宿主技能列表
entry:description -> wayfinder : routes-to  # 宿主技能列表
entry:description -> wizard : routes-to  # 宿主技能列表
entry:slash -> grill-me : routes-to  # 用户斜杠
entry:description -> grilling : routes-to  # 宿主技能列表
entry:slash -> handoff : routes-to  # 用户斜杠
entry:slash -> teach : routes-to  # 用户斜杠
entry:description -> to-questionnaire : routes-to  # 宿主技能列表
entry:slash -> wait-what : routes-to  # 用户斜杠
entry:description -> writing-for-agents : routes-to  # 宿主技能列表
entry:description -> design-pages : routes-to  # 宿主技能列表
entry:description -> exe-release : routes-to  # 宿主技能列表
entry:description -> verify-ticket : routes-to  # 宿主技能列表
entry:description -> ui-acceptance : routes-to  # 宿主技能列表
entry:description -> manage-agents-md : routes-to  # 宿主技能列表
entry:description -> dispatch : routes-to  # 宿主技能列表
entry:description -> code-checkers : routes-to  # 宿主技能列表
entry:description -> diagram-design : routes-to  # 宿主技能列表
entry:description -> write-screen-contract : routes-to  # 宿主技能列表
entry:description -> advisor : routes-to  # 宿主技能列表
entry:description -> retro : routes-to  # 宿主技能列表
```

---

## 4. 现有部件去向总表

一行一个部件，按清点报告分组。

- 同一部件在几份报告里都出现时，只在第一次出现处写全，后面写「见 N?」。
- 「收益」只写用户要求 2 的六种：去重复、给家、上游回原文、复用、外来不改现有文字、消断点。
- 「不动」行写理由的出处，理由全文在第 6 节。
- 批次号写在动作后面的括号里。

### 4.1 N1 dispatch

| 部件 | 新位置与层 | 动作 | 收益或理由 | 出处 |
|---|---|---|---|---|
| `dispatch/SKILL.md` description | 原位，能力技能触发 | 改写（2）：删「Start a reviewer from inside a ticket,」 | 去重复（`implement` 已认领） | R5 A1 |
| `dispatch/SKILL.md` `## Find your moment` 第 1 行 | 原位，流水线角色表 | 改写（1）：worker 先 `## On waking`，再跑 `--preflight` 照 `RESUME:` 做 | 消断点 B9；消断点 M17 | R5 A4、K-47 |
| `dispatch/SKILL.md` 第 8 行 | 原位 | 不动。它就是 `the-tracker-is-the-state` 规则的前半句原话（M25），该原则暂缓 | — | K-41 |
| `dispatch/SKILL.md` 表第 2–6 行、第 12 行定义 | 原位 | 不动 | 各行是一个分支；读者不同 | R5 A3、A5 |
| `dispatch/SKILL.md` `## On waking` | 原位（所有被唤醒角色共用） | 不动；第 1 步前半句已带理由，不加括注（M25） | — | R5 A6、K-9 |
| `references/night.md` 开头五段 | 原位，orchestrator 操作文件 | 不动（不加括注，K-9） | 已带理由 | R11 §5 |
| `night.md` 事实表 | 原位 | 改写（1）：六行缩成四行，位置判定交给 `status` 的 `RESUME:`（取值含 1b 与 `5.` 的段落限定，K-48） | 去重复（与 `newest_field`、`finish` 前置同一判定）；消断点 V6、V7 | R5 B2、J1 |
| `night.md` `## 1`、`## 1b`、`## 2` | 原位 | 不动 | 只有一个调用方 | R5 B3 |
| `night.md` `## 3` 五步与处理表 | 原位 | `fault` 行（第 82 行）括注 `rerun-dont-reroute`（3）；不加 `MMW turn guard:` 行（K-3）；表里加一行兜底「其他 `watchdog:` 告警：照告警写的下一步做」（1，K-46） | 复用；消断点 M16 | R5 B4、B5、K-46 |
| `night.md` 第 96–100 行（worker 持有代码、contract 权威顺序） | 原位 | 不动 | 绑定机制，只有一个读者 | R5 B6 |
| `night.md` `### Exit codes of resume` | 原位 | 改写（1）：只补 exit 0 一句 | 消断点 V8 | R5 B7、K-4 |
| `night.md` `## 4. The closing pass` | 原位 | 第 127 行括注 `silence-is-never-a-pass`（3） | 复用 | R11 C4（取代 R5 B8 的选点） |
| `night.md` `## 5`、`## 6`、`## Suspending the night` | 原位 | 不动 | 每步要上一步的收据 | R5 B9–B11 |
| `references/one-ticket.md` | 原位，单票 orchestrator 操作文件 | 改写第 3 步末条（1） | 消断点 V7、W3 | R5 C1、C2 |
| `references/inside-a-ticket.md` | 原位，worker 的分支 reference | `## After the closeout` 末尾加一句，写明 `watchdog:` 行也关于自己的票（1） | 消断点 W2；消冲突（告警正文里的 `resume` 命令，K-46） | R5 D1 |
| `references/editing-models.md` | 原位 | 不动 | 分支 reference | R5 E1 |
| `hosts.json` | 原位，配置 | 不动 | 与适配器、`models.py` 是天然整体 | R5 K1 |
| `scripts/dispatch.sh`：启动提示词、`AUTONOMOUS`、`PRODUCT_RULES`、case 分支 | 原位 | 不动 | 启动提示词首句由 `test_dispatch.sh` 核对角色到技能的映射；`PRODUCT_RULES` 引用的标题由 `check_wiring.py` 第 1 类核对（M19） | R5 G3 |
| `dispatch.sh` `resume_one` | 原位 | 改写（1）：同一行接 worker 指针 | 消断点 B9；复用 `anchors.py` | R5 G1 |
| `dispatch.sh` `open_relay` | 原位 | 改写（1）：`--by open\|open-ticket\|adopt` | 消断点 W2 | R5 H3 |
| `dispatch.sh check_machine` | 原位 | 改写（3）：缺 `mmw` 行时打一行只读警告 | 消断点（`mmw` 的加载） | R5 G2 |
| `dispatch.sh` 第 4115 行拒绝文字 | 原位 | 不动；由 lint 第 1 类模式扫描 | — | R5 G4 |
| `dispatch.sh` 其余子命令、头注释 | 原位 | 不动；头注释漂移另开普通票 | 不属架构 | R5 G5 |
| `scripts/relay.py` `WAKES` | 原位 | 不动；`pointer` 子命令加在这里（1） | 复用 | R5 H1、K-2 |
| `relay.py` `wake_text` | 原位 | 改写（1）：`#<n> <event> · <指针>`；`relay.recovered` 列出该地址全部 watch 的指针 | 消断点 B8、B9；R4 T12 由此定下 | R5 H2 |
| `scripts/watchdog.py` 告警发送 | 原位 | 改写（1）：八种告警每种在同一行写出下一步，再接指针；`by=adopt` 的 watch 不附 `resume` 命令 | 消断点 B8；消断点 M16 | R5 I1、K-46 |
| `watchdog.py` idle 告警里给 worker 的文字 | 原位 | 改写（1）：缩成一句，其余交给指针；worker 指针送它跑 `--preflight`，照 `RESUME:` 做（K-47） | 去重复，并消除 W4 的分歧 | R5 I2 |
| `watchdog.py` 第 735、780 行 | 原位 | 改从 `anchors.py` 取（1） | 防 V8 复发 | R5 I3 |
| `scripts/turn-guard.py` | 原位，hook | 不动 | 拦截文字自带步骤 | R5 M1 |
| `scripts/tool-guard.py` `NO_QUESTION` | 原位，hook | 改写（1）：三角色短写法 | 消冲突 V9，并覆盖 R6 F5 | R5 L1、R6 X3、K-5 |
| `tool-guard.py` 其余 | 原位 | 不动 | 事前文字与事发拒绝，读者读到的时刻不同 | R5 L2 |
| `scripts/status.py` | 原位 | 改写（1）：`--table` 首行印 `RESUME:`；有 `spec.opened`、本批还没有任何 `worker.started` 时印「1b. Before the batch」；有 `spec.closed` 时印「5. The night is over, from the paragraph that invokes the `retro` skill」 | 去重复；消断点 V6；消断点 M18 | R5 J1、K-48 |
| `scripts/models.py`、`statedir.py`、`ghlist.py`、`runners/{paseo,orca,herdr}.sh` | 原位 | 不动 | 天然整体 | R5 K1 |
| 新 `scripts/anchors.py` | `dispatch/scripts/`，脚本常量 | 新建（1） | 复用：七个读者（`relay.py`、`watchdog.py`、`status.py`、`tool-guard.py`、经 `relay.py pointer` 的 `dispatch.sh`、`check_wiring.py`、`tests/relay`） | K-2 |
| `docs/contexts/night/CONTEXT.md` | 原位 | 加 **role pointer**，改 **wake**（1） | 给新词一个家 | R5 Q3、R10 X2、X3 |
| `docs/contexts/night/how-it-works.md` | 原位 | 第 81 行改指 `watchdog.py`（1） | 消断点 W9 | R5 Q1 |
| ADR 0009、0010、0016–0018、0020–0025、0027 | 原位 | 不动；新 ADR 0032 修订 0020 一句 | ADR 只记决定 | R10 D2、D6 |

### 4.2 N2 verify-ticket

| 部件 | 新位置与层 | 动作 | 收益或理由 | 出处 |
|---|---|---|---|---|
| `verify-ticket/SKILL.md` 第 8–12 行 | 原位，能力技能 | 不动 | 绑定事件格式 | R6 V1 |
| `SKILL.md` 第 16 行 | 原位 | 不动（与 R4 D5.2 不同） | 它是送回 `implement` 的出口 | R6 X1、K-6 |
| `SKILL.md` 表、`## Reached from here` | 原位 | 不动 | 属能力内部 | R6 V3 |
| `references/linting.md` | 原位 | 不动 | 删掉就要在两处重写它独有的一句 | R6 V4 |
| `references/sub-issues.md` | 原位 | 不动 | 两个调用方，是有序判定表 | R6 V5 |
| `scripts/verify-ticket.py` `resume_at` | 原位 | 改写（1）：印步骤名，写成字面、由 lint 第 1 类模式扫描核对（不导入 `anchors.py`）；已认领、没有运行记录时印「Claim, read in, write the code」；改正 docstring | 消断点 V10；消断点 M17 | R6 V6、K-2、K-47 |
| `verify-ticket.py` 其余 | 原位 | 不动 | 天然整体 | R6 V7 |
| `scripts/events.py`、`issue_tree.py` | 原位 | 不动 | 搬走要改六处导入与 Self-hosting boundary 点名的路径 | R6 V8 |
| `scripts/gate-check/` 三个 symlink；`upstream-unlazy` 的 `gate-check.mjs`、`gate-lint.mjs`、`lib/`、两份测试 | 原位 | 不动 | 上游行过半；每段有 merge-note | R6 V9 |
| `upstream-unlazy` 其余（上游 `SKILL.md`、`references/`、`stop-hook.mjs` 等） | 原位，不装 | 不动 | 上游原文 | N2 §1.2 |
| `scripts/__pycache__/`（未入库） | — | 不涉及 | 不在 git 里 | N2 §1.1 |
| `merge-notes/unlazy.md` | 原位 | 不动 | — | R6 V10 |
| `docs/contexts/ticket-run/CONTEXT.md` | 原位 | 19 处路径（2）；`RESUME:` 词条（1） | 消断点 | R6 M1、R10 X1、X8 |
| `docs/contexts/tickets/CONTEXT.md` | 原位 | 57 处路径（2）；第 352、360 行 `_Home_` 错指另开票 | 消断点 | R10 X8、R6 §7 |
| ADR 0008、0012、0013、0019、0026 | 原位 | 不动 | — | R10 D6 |
| `mmw-v2/tests/verify-ticket/`（26 个测试） | 原位 | `test_preflight.py` 第 450 行 docstring 与第 458–517 行断言改为步骤名，另加两条核对（步骤名；没有运行记录时的新取值）（1）；其余不动 | 与 V6 同一次提交 | R6 V11 |

### 4.3 N3 implement、code-review、tdd

| 部件 | 新位置与层 | 动作 | 收益或理由 | 出处 |
|---|---|---|---|---|
| `implement/SKILL.md` | `mmw-v2/skills/implement/`，worker 操作文件 | 移动（2）；八步加名（1）；第 74 行补「没有 `RESUME:` 时回到 `## Claim, read in, write the code`」（1，K-47）；第 18、96 行括注（3） | 上游回原文；消断点 V10、M17；复用 | R6 I1、I15、R11 C3、C11、K-47 |
| `implement` 其余各段（第 6、8、12–16、20–34、36–68、72、76 行） | 随移动 | 不动；`## Shared experience while implementing` 与 `Put no question on the screen` 登记为锚点（1） | worker 单一读者 | R6 I3–I14 |
| `implement/references/writing-interface-code.md` | 随移动 | 第 35、37、41 行三处「closing step 1」改为步骤名 **Integrate and run**（1，与八步加名同一次提交） | 消断点（按编号引用，L7 C.6 信号 8） | R6 I16、K-43 |
| `implement/references/saving-memory.md` | 随移动 | 不动 | — | R6 I17 |
| `implement/agents/openai.yaml` | 删除（2） | 删除 | 去重复：`short_description` 与 description 同义。依赖第 2 批 SSR 改写把分叉技能归入「this repository wrote」 | K-20 |
| `code-review/SKILL.md` | `mmw-v2/skills/code-review/`，能力技能 | 移动（2） | 上游回原文 | R6 C1、C3 |
| `code-review/references/session.md` | 随移动，reviewer 操作文件 | 不动；`Could not tell` 登记为锚点（1） | 消冲突 | R6 C5（C4 的括注不做，K-9） |
| `standards-reviewer.md`、`tests-reviewer.md`、`ui-reviewer.md` | 随移动 | 不动 | 每个 axis 子代理只读自己那一份 | R6 C6、C8、C9 |
| `spec-reviewer.md` | 随移动 | 第 35 行删半句（2） | 消冲突 F7 | R6 C7 |
| `code-review/agents/openai.yaml` | 删除（2） | 删除 | 同上（去重复） | K-20 |
| `tdd/SKILL.md` | 原位，上游能力技能 | 不动（e 类） | 挪走名词拿不到收益 | R6 T1、X2 |
| `tdd/tests.md`、`mocking.md`、`agents/openai.yaml` | 原位 | 不动 | 上游原文 | R6 T2 |
| `merge-notes/implement.md`、`code-review.md` | 原位，分叉意图记录 | 改写三处（2） | 去重复；消冲突 | R6 I21、C13 |
| `merge-notes/tdd.md` | 原位 | 不动 | — | R6 T3 |
| `upstream/docs/engineering/implement.md`、`code-review.md` | 原位 | 回到上游原文（2） | 上游回原文 | R6 I19、C11 |
| `upstream/docs/engineering/tdd.md` | 原位 | 不动 | — | N3 §1 |
| `upstream/skills/engineering/README.md` 的两行 | 原位 | 回到上游原文（2） | 上游回原文 | R6 I20、C12 |

### 4.4 N4 to-spec、to-tickets、triage

| 部件 | 新位置与层 | 动作 | 收益或理由 | 出处 |
|---|---|---|---|---|
| `to-spec/SKILL.md` | `mmw-v2/skills/to-spec/`，能力技能 | 移动（2）；第 4 步加一句（4）；`## Next` 保留（K-7） | 上游回原文；去重复（第 4 批删掉其他四个家后，顺序只剩这一个家） | R7 A1、A4、K-7 |
| `to-spec` description、第 1–4 步、模板 | 随移动 | 不动 | 天然整体；description 分支都是本能力的输入 | R7 A5、A6 |
| `to-spec/references/revising-a-spec.md`、`several-specs.md` | 随移动 | 不动 | — | R7 A6 |
| `to-spec/agents/openai.yaml` | 删除（2） | — | 去重复（同 K-20） | R7 A2、K-20 |
| `to-tickets/SKILL.md` | `mmw-v2/skills/to-tickets/` | 移动（2）；第 84 行不加括注（本地已写理由，K-9）；第 8 步末句保留（K-7） | 上游回原文 | R7 B1、K-7、K-9 |
| `to-tickets` 第 1–8 步其余与 `<issue-template>` | 随移动 | 不动 | 天然整体 | R7 B5、B6 |
| `ambiguity-scan.md`、`cutting-interface-tickets.md`、`person-ticket.md` | 随移动 | 不动 | — | R7 B6、R8 2.4 |
| `to-tickets/agents/openai.yaml` | 删除（2） | — | 去重复（同 K-20） | R7 B2、K-20 |
| `triage/SKILL.md` 调用开关与 description | 原位，上游能力技能 | 不动 | 推导结果不变 | R7 C1、C2 |
| `triage` 第 5 步 `ready-for-agent`（第 82 行） | 原位 | 拆分（4）：留 agent brief 与 label 去处；route 句移走；关 issue 句移进 `to-spec` | 上游回原文；去重复 | R7 C3、K-15 |
| `triage` 第 5 步末段 route 句（第 90 行） | `triage/references/pipeline-issues.md` | 移动（2） | 上游回原文 | R7 C4 |
| `triage` `## Quick state override` 末句 | 原位 | 回到上游原文（4） | 上游回原文；去重复 | R7 C5 |
| `triage` 第 70、22 行，`## Roles`，宿主中立改写 | 原位 | 不动（e、a 类） | — | R7 C8、C9 |
| `triage/references/pipeline-issues.md` | 原位，旁加 reference | 第 5 行 retro 一句改写（4）；收下 C4 那一段（2）；第 3 行不加括注（K-9） | 去重复 | R7 C4、C6 |
| `triage/AGENT-BRIEF.md`、`OUT-OF-SCOPE.md`、`agents/openai.yaml` | 原位 | 不动 | — | R7 C9 |
| `docs/agents/issue-tracker.md` | 原位，消费仓库私有 | **Map** 一条加建 label 句（2，以 X-11 为前提） | 去重复 | R7 L1 |
| `docs/agents/triage-labels.md`、`domain.md` | 原位 | 不动 | — | R7 L3、L4 |
| `merge-notes/to-spec.md`、`to-tickets.md`、`triage.md` | 原位 | 改写（2、4） | 去重复；消冲突 | R7 A7、B7、C10 |

### 4.5 N5 其他上游技能

| 部件 | 新位置与层 | 动作 | 收益或理由 | 出处 |
|---|---|---|---|---|
| `prototype/SKILL.md`（含规则 1 的叶子目录形状、规则 6） | 原位 | 不动；B4 由调用方限定范围 | e 类；三个入口都读规则 1 | R7 F2、F3、K-14 |
| `prototype/LOGIC.md`、`EXP.md`、`evidence-page.md` | 原位 | 不动 | — | R7 F4 |
| `prototype/UI.md` 第 6 步的 state list 段 | 新 `design-pages/references/state-list-format.md`（MMW 自有技能的 reference）；第 6 步留一句指针，指向「the `design-pages` skill's `references/state-list-format.md`」 | 拆分（2） | 上游回原文（上游目录里的 MMW 文字从一整段减到一句，M13）；去重复（`design-system.md` 第 42 行的格式括注）；消断点（`design-pages` 第 25 行按编号引用「`UI.md` step 6」） | R8 2.4、K-14 |
| `prototype/UI.md` `## Next` | — | 删除（4） | 上游回原文 | R7 F1、R8 |
| `prototype/UI.md` 其余 e 类改动 | 原位 | 不动 | — | R8 2.4 |
| `wayfinder/SKILL.md` 第 6 步 | 原位 | 拆分（4）：留停止判据，移走下一步句 | 上游回原文 | R7 D1 |
| `wayfinder` 两处 `mmw:map` | 回到上游 `wayfinder:map`；建 label 句进 tracker 文档与种子 | 回原文 + 合并（2，以 X-11 为前提） | 去重复；上游回原文 | R7 D2 |
| `wayfinder` 其余与 `references/interface-and-remake.md` | 原位 | 不动 | — | R7 D3、D5 |
| `grilling` | 原位 | 不动 | 天然整体；用户裁定的原文摘录 | R7 §5 |
| `grill-me` | 原位 | 不动 | a 类 | R7 §5 |
| `grill-with-docs` 第 7 行末句 | — | 删除（4） | 上游回原文 | R7 E1 |
| `grill-with-docs` 其余与开关 | 原位 | 不动 | — | R7 E2、E4 |
| `domain-modeling` 三份文件 | 原位 | 不动 | 上游原文 | R7 E3 |
| `codebase-design` 三份文件 | 原位 | 不动 | — | R7 G3 |
| `improve-codebase-architecture` `### 4` 第 3 句 | — | 移走（4） | 上游回原文 | R7 G1 |
| `improve-codebase-architecture` 其余与 `HTML-REPORT.md` | 原位 | 不动 | — | R7 G3 |
| `research`、`resolving-merge-conflicts` | 原位 | 不动 | — | R7 H1、R6 RM1 |
| `diagnosing-bugs` 与 `hitl-loop.template.sh` | 原位 | 不动；B6 由 Routes 处理 | — | R7 G3 |
| `wizard` 与 `template.sh`、`handoff`、`teach` 与四份格式文件、`to-questionnaire`、`wait-what` 与 `VISUAL.md` | 原位 | 不动 | — | R7 H1 |
| `setup-matt-pocock-skills/SKILL.md` | 原位 | 不动 | e 类；U4 不放这里 | R7 J1、J2 |
| 种子 `issue-tracker-github.md` | 原位 | 加一句（2） | 随 `wayfinder` | R7 J3 |
| 其余四份种子 | 原位 | 不动；种子与落地件的漂移另开票 | — | R7 J4 |
| `writing-for-agents/SKILL.md` 第 8 行 | 原位 | 回到上游原文（2） | 上游回原文 | K-38 |
| `writing-for-agents/SKILL.md` 其余、`SKILL-MECHANICS.md`、`agents/openai.yaml` | 原位 | 不动 | — | R9 W1–W5 |
| `writing-for-agents/SKILL-SET-RULES.md` | `docs/skill-set/SKILL-SET-RULES.md`，仓库文档 | 移动（2）；改写（2、3），约 +40 行 | 移动：上游回原文（176 行离开上游目录）；消除上游目录对 `mmw` 的依赖。改写：给家；消冲突；外来不改现有文字 | R9 W-SSR-*、第 7 节、K-38 |
| `writing-for-agents/REVIEWING-A-SKILL-SET.md` | `docs/skill-set/REVIEWING-A-SKILL-SET.md` | 移动（2）；改写（3），约 +2 行 | 上游回原文（33 行）；消断点 | R9 W-RSS-*、K-38 |
| 残留 `ask-matt/SKILL.md` | On-ramps、Codebase health 两块移进 `mmw` `## Routes`；Head judgement 与 Context hygiene 移进 `idea-to-tickets` 的 **Who checks**、**Spec**（K-40）；原文件恢复上游原文，不安装 | 移动 + 回原文（3） | 给家（B1、B3、B5）；消断点 B10 | R7 K2–K7、K-13 |
| 残留 `ask-matt/PHASE-BOUNDARIES.md` | `mmw/references/phase-boundaries.md` | 移动（3） | 给家（B5）；复用（两个调用方） | R7 K1 |
| 残留 `ask-matt/agents/openai.yaml` | 回到上游原文（3） | — | 上游回原文 | R7 K7 |
| 各 `agents/openai.yaml`（上游技能的） | 原位 | 不动 | — | N5 §1 |
| `merge-notes/prototype.md`、`wayfinder.md`、`grill-with-docs.md`、`improve-codebase-architecture.md`、`teach.md` | 原位 | 改写相应条目（2、3、4） | 去重复；消断点 B11 | R7 D4、F5、G4、R8、R10 M6、M8 |

### 4.6 N6 界面链

| 部件 | 新位置与层 | 动作 | 收益或理由 | 出处 |
|---|---|---|---|---|
| `ui-acceptance/SKILL.md` description 半句、表第 1 行 | — | 删除（2） | 去重复 U1 | R8 2.1 |
| `ui-acceptance/SKILL.md` 其余（含 `## Five rules while the product is running`） | 原位 | 不动；不加括注（K-9）；Five rules 标题进 lint 第 1 类 | 被启动提示词逐字引用 | R8 2.1、§4 |
| `ui-acceptance` 五份 reference | 原位 | 不动 | 读者不同 | R8 2.1 |
| `ui-acceptance` 9 个脚本 | 原位 | 不动；四处拒绝文字进 lint 模式扫描 | — | R8 2.1、§4 |
| `design-pages/SKILL.md` `## The state list` | 原位 | 改指同技能的 `references/state-list-format.md`（2） | 消断点 U4 | R8 2.2、K-14 |
| `design-pages` 其余与 `edit-pages.md`、`draw.md`、`pull.md`、两份模板 | 原位 | 不动 | 下一步取决于自身输出 | R8 2.2 |
| `design-pages/references/design-system.md` 第 42 行括注 | 原位 | 改为引用同技能的 `state-list-format.md`（2） | 去重复 U5 | R8 2.2、K-14 |
| `pull_design.py`、`check_editable_selectors.py` | 原位 | 不动；`## State list` 字面进 lint，与 `state-list-format.md` 核对 | — | R8 2.2 |
| `write-screen-contract/SKILL.md` `## Next` 从句 | 原位 | 删除（4，与 `wayfinder` 同一次提交） | 消断点 U6 | R8 2.3 |
| `write-screen-contract` 其余、格式文件、三个脚本 | 原位 | 不动 | 脚本拒绝文字按文件名把 worker 送到格式文件 | R8 2.3 |
| `docs/contexts/ui-acceptance/CONTEXT.md` | 原位 | 第 67、194、225、229、233 行改 `_Home_`（2） | 消断点 U14、U17 | R8 2.5 |
| ADR 0002、0004、0011、0028、0029、0030 | 原位 | 不动 | — | R8 2.5 |
| `merge-notes/to-tickets.md` 第 93 行 | 原位 | 改写（2） | 消断点 U13 | R8 2.5 |
| `tests/ui-acceptance/`、`design-pages/`、`write-screen-contract/` | 原位 | 不动 | 被测字面不变 | R8 2.5 |

### 4.7 N7 retro、advisor、exe-release、code-checkers、manage-agents-md、diagram-design

| 部件 | 新位置与层 | 动作 | 收益或理由 | 出处 |
|---|---|---|---|---|
| `retro/SKILL.md` 全部（含第 186 行） | 原位，能力技能 | 不动 | 返回句点名唯一调用方（K-7） | R5 N1–N6 |
| `retro/scripts/retro.py`、`tests/retro/` | 原位 | 不动 | — | R5 O1 |
| `advisor/SKILL.md`、`consulting.md`、`advising.md` | 原位（`advising.md` 是 advisor 操作文件） | 不动；三个锚点登记（1） | 消冲突 F5 | R6 A1–A3 |
| `exe-release/SKILL.md`（`## 1.`–`## 5.`） | 原位 | 不动；第 16 行与脚本不符，另开票 F1 | — | R9 E1–E5 |
| `exe-release` 三份 reference | 原位 | 不动；`key.md` 缺字段、`new-product.md` 中文注释另开票 F3、F4 | — | R9 E6–E8 |
| `exe-release` 八个脚本与模板 | 原位 | 不动；注释漂移另开票 F2 | — | R9 E9 |
| `tests/exe-release/`、`docs/contexts/release/CONTEXT.md`、`downstream-notes/release-self-heal-removed.md` | 原位 | 不动；CONTEXT 随 F3 修 | — | R9 E10–E12 |
| `code-checkers/SKILL.md` 与三份 reference | 原位 | 不动 | — | R9 C1–C10 |
| `manage-agents-md/SKILL.md` `### What NOT to Add` 第 9 条、根模板 File 列 | 原位 | 改写（3）：加一句与半句 | 消冲突 R9-V3 | R9 M6、M7 |
| `manage-agents-md` 其余、两份 reference、`check.sh`、测试 | 原位 | 不动 | — | R9 M1–M12 |
| `diagram-design` `SKILL.md`（a、e 类改动） | 原位，外来合集 | 不动；三处漏改与超 40,000 字节另开票 F5 | — | R9 D1–D10、D17 |
| `diagram-design` 56 份 reference、`assets/`、脚本、`repo-root` symlink、subtree 根脚本与插件包装 | 原位 | 不动；symlink 理由写得不准，另开票 F6 | — | R9 D11–D15 |
| `merge-notes/diagram-design.md` | 原位 | 不动；下次拉 `diagram-design` 上游、这些行真要取舍时再顺带标类别 | 标类别只是格式统一，说不出用户要求 2 的收益 | R9 D16、第 6 节 |

### 4.8 N8 基座

| 部件 | 新位置与层 | 动作 | 收益或理由 | 出处 |
|---|---|---|---|---|
| `prompt/shared.md` | 原位，宿主级提示，不属 MMW 任何层 | 不动 | owner 的全局规则 | R10 P1、P2 |
| `prompt/hosts/*.md`、`render.py`、`prompt/README.md`、`prompt/tests/` | 原位 | 不动 | — | R10 P3、P4 |
| `skills.txt` | 原位 | 改四行（2）；加一行（3） | 上游回原文；给家 | R10 I4、I5 |
| `install.sh` | 原位 | `--check` 加一项：列出开着的 watch，以及各状态目录里 `relay.lock`、`watchdog.lock` 指向的活进程，不改退出码（1） | 消断点 S8 | R10 I1–I3、K-32 |
| `~/.mmw/models.json`、`models.py`、`editing-models.md` | 原位 | 不动 | 唯一写入口 | R10 R1、R2 |
| `tool-guard.py`、`turn-guard.py` | 见 4.1 | — | — | — |
| `board/` 全部（含 `AGENTS.md`、`page/`） | 原位 | 不动 | 不读任何被改的东西（推断） | R10 B1 |
| `migrations/remove-verifier.py`；新迁移 | 原位；不建新迁移 | 不动 | 不改存下的状态 | R10 B2、B3 |
| `tests/AGENTS.md` | 原位 | 改一句（1） | 消遗漏 | R10 T6 |
| 12 个 `tests/<name>/run.sh` 头部三行 | 新 `tests/lib/shared_lints.sh` | 合并（1） | 去重复（36 行）；以后加检查只改一处 | R10 T1 |
| `tests/lib/check_module_paths.py`、`check_upstream_em_dashes.py`、`parse_k.sh`、`run_unittests.py` | 原位 | 不动 | — | R10 T7 |
| `tests/lib/check_own_skill_frontmatter.py` | 原位 | 加一条「`name` 等于目录名」（1） | 消断点 K7（取代 R4 lint 第 6 类） | R10 T3、K-18 |
| 新 `tests/lib/check_wiring.py`、新 `tests/lints/` | 新建（1–3）；第 4 类暂缓（K-44） | 新建 | 给家；消断点复发 | R10 T2、T4 |
| 根 `AGENTS.md` | 原位 | 改写 A1–A6（1、3） | 去重复；消冲突 S14、S15 | R10 2.7 |
| `CODING_STANDARDS.md` | 原位 | 加两条、改一处列举（1、3） | 给家；消冲突 S13 | R10 C1、C2、R11 E2 |
| `TESTING.md` | 原位 | 加两句（1） | 消冲突 S12 | R10 K1、K2 |
| `merge-notes/README.md` 与 24 份说明 | 原位 | 见 2.8 | — | R10 M1–M9 |
| `downstream-notes/README.md` 与 19 份现行、7 份存档 | 原位 | 不动 | 不让消费仓库产物失效 | R10 D1 |
| ADR 0003、0005、0006、0007、0015 | 原位 | 不动 | — | R10 D6 |

### 4.9 N9 ADR、词表、原则候选

| 部件 | 新位置与层 | 动作 | 收益或理由 | 出处 |
|---|---|---|---|---|
| `docs/adr/README.md` | 原位 | 索引加三行（1–3） | — | R10 D5 |
| 31 份 ADR 正文 | 原位 | 不动；已失效的路径（0008、0012 的 `refusal.py`）另开票 | ADR 只记决定 | R10 D6、O4 |
| `CONTEXT-MAP.md` | 原位 | Toolbox 范围句（3） | — | R10 X10 |
| 七份 `CONTEXT.md` | 原位 | 见 2.8 | — | R10 X1–X12 |
| `CODING_STANDARDS.md`、`TESTING.md`、`shared.md` | 见 4.8 | — | — | — |
| 原则候选 PC1、PC2 | 并入 `silence-is-never-a-pass` | 新建（3） | 给家；复用 | R11 G |
| PC4、PC5 | 并入 `the-tracker-is-the-state`，该原则暂缓；在它建成前，PC4 的家仍是 `dispatch/SKILL.md` 第 8 行，PC5 由 relay、turn guard 与 `RESUME:` 在机制上强制 | 暂缓（X-13） | — | R11 G、K-41 |
| PC17、PC18 | 并入 `rerun-dont-reroute`；PC17 写脚本的部分进 `CODING_STANDARDS.md` | 新建（3）、加一条（1） | 给家；消冲突（规则 11） | R11 G、E2 |
| PC3、PC6、PC7、PC9、PC10、PC13–PC16 | 原处 | 不动 | 已有家，或已由机制强制 | R11 G |
| PC8、PC11、PC12 | 原处；PC12 提一个 lint 候选 | 不动 | R4 第 15 节的排除理由有事实错误，改用 R11 §3.3 的理由 | R11 §3.3、X-26 |

### 4.10 N10 路由与调用

| 部件 | 新位置与层 | 动作 | 收益或理由 | 出处 |
|---|---|---|---|---|
| 35 份 frontmatter | 原位 | 只删 B7 两处 description 短语（2）；开关由推导规则决定 | 去重复 | R4 D1.3、K-24 |
| 24 份 `agents/openai.yaml` | 分叉的四份删除（2），其余不动 | — | 去重复（同 K-20） | K-20 |
| 五张 `## Find your moment` 表及同类表 | 原位 | `dispatch` 第 1 行改、`ui-acceptance` 第 1 行删；其余不动 | 能力内部的分支表 | R4 D5.2 |
| 结尾段（N10 列的 16 处） | 按 D5.1 分类 | c 类移走（4）；取决于自身输出的保留；分叉后的 `to-spec`、`to-tickets` 与 `retro`、`verify-ticket`、`write-screen-contract` 一样保留各自的后继句 | 上游回原文；去重复 | 第 5 节 K-6、K-7 |
| `dispatch.sh` 提示词拼装 | 原位 | 不动 | 首句由测试核对角色到技能的映射，`PRODUCT_RULES` 的标题引用由 lint 核对（M19） | R5 G3 |
| `dispatch.sh` 头注释与 `--help` | 原位 | 另开票（B12） | 不属架构 | R5 G5 |
| `relay.py` `WAKES`、`wake_text`；`watchdog.py` 告警；`turn-guard.py` 消息；`tool-guard.py` | 见 4.1 | — | — | — |
| SSR 事实 7、`### Descriptions`、`### Hand-offs`、`### Prompts written for other agents`、`### Load and disclosure` | 随 SSR 搬到 `docs/skill-set/` | 改写或保留，见第 7 节 | — | R9、K-38 |
| `SKILL-MECHANICS.md` `## Router skills` | 原位 | 不动；分歧写在 SSR 与 merge-note | 上游原文 | R9 W4、W6 |
| `mmw-v2/upstream/.agents/invocation.md` | 原位 | 不动 | 上游维护者规则，本仓 agent 不加载 | N10 §1 |
| `merge-notes/README.md` `## disable-model-invocation` | 原位 | 改为推导规则（2） | 去重复 | R10 M2 |
| 提交 `06163a0f` | 历史 | 不涉及；它对残留目录的描述在第 3 批恢复后成立 | — | R7 K7 |
| 残留 `ask-matt` 目录 | 见 4.5 | — | — | — |
| Memory 记录（`411750f5`、`ce037679`、`fe94802d`、`f4c3d378`、`8ec53374`、`415f96d0`、`ec59cec8`、`0ac93ab8`、`9d6755c0`、`4756d4d3`） | Nowledge Mem | 不改；在第 7 节逐条写处理 | — | R4 §9、R6 F17、R11 |

### 4.11 N11 unread_parts 的去向

| # | 未被清点读过的部件 | 去向 | 本轮核实情况 |
|---|---|---|---|
| 1 | `docs/notes/stage-two-shared-experience-layer.md` | 只改两处路径（2），正文不动 | R6 读了标题与 §3–§9，R10 读了前 30 行。它第 7 行自称以代码为准，所以与技能的分歧不误导 agent |
| 2 | `docs/specs/task-board/screen-contract.yaml` | 不涉及：消费仓库私有组件，格式不变 | 未读。四批都不改 screen contract 格式（R10 D1），所以不影响结论 |
| 3 | `docs/research/shared-context/`（14 个文件） | 不涉及：研究笔记，运行时不读 | 未读 |
| 4 | `docs/research/mmw-artifact-wiring/`、`cursor-pi-cli/`、`code-landing/11-target-pipeline.html`；`mmw-structure/2026-09-06-handoff.md` | 不涉及；handoff 那份被 R9 §2、R11 §8 当证据引用 | R9、R11 读了引用段 |
| 5 | `mmw-v2/board/page/` | 不动 | 未读。board 按路径载入的五个脚本都不在改动里（R10 B1，推断），由 board 套件确认 |
| 6 | 各套件测试文件本体 | 受影响的已列出：`test_relay.py` 的相等断言、`test_tool_guard.py` 第 440–450 行、`test_preflight.py` 第 450–517 行、`test_status.py`、`test_dispatch.sh` 的 resume 与 check 场景；其余不动 | 部分读过。其他句子是否被钉住，实现前 grep 一次（X-25） |
| 7 | `downstream-notes/` 逐份说明 | 不动 | 未逐份读。只有 `release-self-heal-removed.md` 的执行状态与本次相关（U-11） |
| 8 | `runners/*.sh` 动词实现体；`dispatch.sh` 未读区段 | 不动 | 未读。但指针接在同一行后，`send` 能否整行送达取决于它们（X-8） |
| 9 | `mmw-v2/upstream/` 的非技能部分、`docs/productivity/*.md`、未安装的 `in-progress/` 等技能 | 不动：上游原文；只有 `docs/engineering/{implement,code-review}.md` 回原文 | 本轮只核实了技能树的 diff（M5） |
| 10 | 根 `.mmw/`、`prototypes/` | 不动：消费仓库私有组件（R4 D7.6） | 未读，格式不变 |

---

## 5. 单元之间的冲突与裁定

裁定都是工程决定，按 `shared.md` 规则 1 由本文做出，并写明被放弃的一方。凡改变产品可见效果、或改动 owner 规则的，转进第 9 节。

| # | 分歧 | 各方 | 裁定与理由 |
|---|---|---|---|
| K-1 | 角色指针另起一行，还是接在同一行 | R4 D1.2、R10 X2 写「加一行」；R5 第 0 节第 3 条写同一行用 ` · ` 隔开 | **同一行**。已核实（M1）：runner 把换行当提交，另起一行会变成第二条消息。R10 X2 的词条措辞随之改为「同一行末尾的角色指针」。ADR 0032 按此写 |
| K-2 | 指针表与锚点常量放哪里、谁导入 | R4：`dispatch/scripts/` 下一张表；R5：放进 `relay.py` 紧挨 `WAKES`，hook 不导入；R6：新模块 `anchors.py`，hook 与 `verify-ticket.py` 也读它；R8：界面链脚本不导入，改用模式扫描 | **一个不导入任何模块的纯常量文件 `dispatch/scripts/anchors.py`**，里面有 `POINTERS` 与锚点常量，**只由 `dispatch/scripts/` 里的脚本导入**：`relay.py`、`watchdog.py`、`status.py`、`tool-guard.py`；`dispatch.sh` 经 `relay.py pointer` 取。R5 反对 hook 导入的理由是 `relay.py` 导入时有开销（M3 已核实）；纯常量文件没有这个开销，所以采用 R6 的形态。R5 担心的「改事件时 `WAKES` 与指针不在一处」由 lint 第 2 类兜住。别的技能的脚本一律不导入它，用同一条标准：界面链脚本（`journey.py`、`story-parity.py`、`target_config.py`、`lint_screen_contract.py`）与 `verify-ticket.py` 的 `resume_at` 都把所引的标题或步骤名写成字面，由 `check_wiring.py` 第 1 类模式扫描核对。理由：导入会新增这些技能对 `dispatch/scripts/` 的依赖（`verify-ticket` 还会与 `dispatch.sh` 对它的依赖成环），而它们引用的只是文件级或标题级字面，模式扫描已能核对 |
| K-3 | `night.md` 的重入：R4 补两行，还是交给脚本 | R4 D3.5 c、d 在事实表补「retro 已记录、未验收」一行，并在 `## 3` 加 `MMW turn guard:` 行；R5 B2、J1 把按事件的判定交给 `status` 首行 `RESUME:`，事实表缩成四行，turn guard 单列「照它做」 | **R5**，取值按 K-48 改正两处。按事件判位置在 `dispatch.sh` 的 `newest_field` 与 `finish` 前置里已有一份（R5 W6），文本里再写一份就是 SSR 说的重复。turn guard 消息自带全部步骤（`turn-guard.py` 第 306–311 行），`## 3` 的五步对它不适用。R4 T9（能否算出）由 R5 读 `status.py` 与 `dispatch.sh` 后定为「按事件的能算，用户说开始、用户验收不能算」。与 L7 D.2 的对应（已对照原文）：pstack `session-pickup.md` 第 2 步「The prior trail is authoritative input」由旧会话记录重建状态；MMW 的「旧记录」是 tracker 上的事件，`RESUME:` 是由它算出的位置，所以同一原意由脚本承担。pstack 的 `pause-safely.md`「This is explicit only」对应 `night.md` 的 **Suspending the night**，也只在决定停夜时进入 |
| K-4 | `### Exit codes of resume` 补全表还是一句 | R4 D3.5 e 按实现补全；R5 B7 只补 exit 0 | **R5**。exit 2、3、4 的去处 stderr 已写全（R5 W5），抄进文本就是 SSR `### Scripts and judgement` 所说的复述 |
| K-5 | `NO_QUESTION` 覆盖哪些角色、怎么写 | R4 D3.5 f：worker 与 reviewer；R5 L1 给出两角色原文（约 190 字符）；R6 X3：还要 advisor | **三角色短写法**，草稿：「Nobody is at the screen. Worker: the implement skill, "Put no question on the screen". Reviewer: "Could not tell" in your report. Advisor: "Missing information gets named precisely".」量得含前缀 195 字符，在 256 上限内（M2）。按 R5 写法再加 advisor 会到 292 字符，超限。`test_tool_guard.py` 第 440–450 行的断言同一次提交改 |
| K-6 | `verify-ticket/SKILL.md` 第 16 行删不删 | R4 D5.2 删；R6 X1 留 | **留**。重叠在 description 首句；第 16 行是把凭这句进来的 agent 送回 `implement` 的出口，删了重叠还在、出口没了。改 description 首句要等 X-12 的并排读和实测 |
| K-7 | 能力技能的后继句换不换固定返回句：`retro` 第 186 行、分叉后的 `to-spec` `## Next` 与 `to-tickets` 第 8 步末句 | R4 D5.4、R9 W-SSR-15 列入；R5 N5 保留 `retro`；R7 A3、B3 把 `to-spec`、`to-tickets` 换成固定返回句 | **三处都保留，不设固定返回句**。`retro` 第 186 行点名唯一的调用方，正是 SSR `### Hand-offs`「or the caller it returns to」允许的写法；换掉后被压缩的 orchestrator 要多绕四跳才能回来。`to-spec`、`to-tickets` 用同一标准：squash 里两处都没有（M14），分叉后是 MMW 自有文本，「上游回原文」的收益不存在；`to-spec` 的后继永远是 `to-tickets`，与调用方无关，换掉要多绕 `mmw` → Routes → `idea-to-tickets#Where you are` → **Tickets** 几跳，直接斜杠进来的会话还会停住。R7 A3 列的「五个家」在第 4 批删掉 `triage` 第 82、94 行、`wayfinder` 第 126 行、`pipeline-issues.md` 第 5 行后只剩 `to-spec` 一处，所以留着不是重复；`idea-to-tickets` 的 **Spec**、**Tickets**、**Hand to the night** 只写门槛与重入，不再写后继。`write-screen-contract` 的 `## Next -> to-spec` 同样保留。SSR `### Hand-offs` 不再写固定返回句 |
| K-8 | 原则括注的写法 | R4 D4.1 与 R5–R9：`(the \`mmw\` skill's principle \`<slug>\`)`；R11：`(the \`mmw\` skill's \`principles/<slug>.md\`)` | **R11**。SSR `### Hand-offs` 规定别的技能里的文件按「技能 + 文件」点名；worker 从不加载 `mmw`，只凭 slug 找不到文件。`mmw` 目录内仍写 `(principle \`<slug>\`)`。改原则 slug 的人按这两种写法 grep；`check_wiring.py` 第 4 类若将来建成（K-44），也只认这两种 |
| K-9 | 原则括注加在哪些句子上 | R5 六处（含 `night.md` 第 7、11 行、`## 4` 一句）；R6 四处（含 `implement` 第 30 行、`session.md` §1）；R7 两处（含 `pipeline-issues.md` 第 3 行）；R8 三处（`ui-acceptance`）；R11 十一处，规则写作「每个调用方文件一处，只加在本地没写理由的句子上」 | **5 处**：`idea-to-tickets` **Tickets**、`implement` 第 18、96 行、`night.md` 第 82、127 行。规则改为「**每个调用方文件对每条原则只加一处**，只加在本地没写理由的句子上」：R11 的字面「每个调用方文件一处」与它自己在 `implement` 选的三处矛盾，实际执行的是每文件每原则一处。按这条规则去掉 R11 的四处：`to-tickets` 第 84 行、`dispatch/SKILL.md` 第 25 行本地已写理由（M25）；`dispatch/SKILL.md` 第 8 行、`implement` 第 74 行、`mmw` 与 `idea-to-tickets` 的 `## Where you are` 属于暂缓的 `the-tracker-is-the-state`（K-41）。选点规则直接回应 L7 C.6 信号 2（加在已带理由的句子上不改变决定）。每条原则仍有至少两处不同机制的调用方（`silence-is-never-a-pass`：playbook 步骤、worker 操作文件、orchestrator 操作文件；`rerun-dont-reroute`：orchestrator 与 worker 操作文件），R4 D4.3 门槛 5 不受影响。上游文本不加括注 |
| K-10 | 宿主没有 Claude Design 工具时 `handoff` 怎么点名 | R8 连线写 `idea-to-tickets#Runnable questions -> handoff : calls`；R7 H3 写「告诉用户运行 `/handoff`」 | **告诉用户运行**。`handoff` 是用户触发的技能；写成调用，推导规则就会把它翻成模型可触发，改变它的触发范围，而且没有收益 |
| K-11 | 「脚本印出的锚点由 lint 核对」这句写在哪 | R4 §9：SSR `### Scripts and judgement`；R9 W-SSR-13：不写；R10 C2：写进 `CODING_STANDARDS.md` `## Skills and scripts` | **R10**。读这句的是写脚本的人和 Standards axis；改标题的人由 lint 拒绝文字给出路 |
| K-12 | 新 ADR 几份 | R4：一份；R5 Q2：第 1 批一份；R11 F2：新 ADR 里加 slug 对照一节；R10：三份，每批一份 | **R10 的三份**：0032（第 1 批，`amends: [0020]`）、0033（第 2 批）、0034（第 3 批，含 R11 F2 的对照）。每批独立落地，第 4 批还有前提；只写一份的话，没做成的决定会先被记下 |
| K-13 | 残留 `ask-matt` 何时恢复原文 | R4、R7 K7：第 2 批；R10：第 3 批，与 `mmw` 同一次提交 | **第 3 批**。三块内容是「搬」，SSR `## Editing` 要求逐字搬仍然适用的句子；隔一批再从 git 历史里捞，容易丢句 |
| K-14 | `prototype` 的 d 类：叶子目录形状与 state list | R4 D5.3：两者都是 d 类，放旁加 reference、由 playbook 点名；R7 F2：都不移（有三个入口，只有一个经过 playbook）；R8：state list 拆进上游目录旁加的 `prototype/state-list.md`，`UI.md` 第 6 步留指针；R10 M7 放第 4 批 | **规则 1 不动（R7）；state list 格式放进 MMW 自有的 `design-pages/references/state-list-format.md`，`UI.md` 第 6 步那一段换成一句指针，指向「the `design-pages` skill's `references/state-list-format.md`」，第 2 批**。squash 的 `UI.md` 第 6 步没有 state list（M13），整段是 MMW 加的；放进上游目录的新文件只是把 MMW 文字换个位置（R8 自己量的净约 +3 行），「上游回原文」不成立。放进 `design-pages` 则上游目录里只剩一句指针，另外两项收益照样拿到：`design-system.md` 第 42 行的格式括注改为同技能内引用（去重复），`design-pages` 第 25 行不再按编号引用「`UI.md` step 6」（消断点）。R8 排除 `design-pages` 的理由是 prototype agent 要去读带 `## Find your moment` 表的别的技能的 `SKILL.md`；指针指向的是一份 reference，不是 `SKILL.md`，这条理由不适用。三个读者都在：`prototype` 写、`design-pages` 读并为已有产品写、`pull_design.py` 解析的字面由 lint 核对。文件名不用 `state-list.md`，因为它与 Claude Design 项目里的同名文件撞名（M4）。R4 D5.3 d 类的判据补一个前提（取自 R7 U-F2）：该技能的每个入口都能经上游文本里的一个指针读到这份文件 |
| K-15 | 「关闭已分诊 issue 并链接 spec」这句留在 `triage` 还是移走 | R4 D5.3 留在 `triage` 第 5 步；R7 A4 移进 `to-spec` 第 4 步 | **R7**。在 triage 会话里 spec 还不存在，只有发布 spec 的会话做得到；依据是 ADR 0001 第 20 行「spec 发布或修订后」。须与 `triage` 第 5 步的拆分同一次提交（第 4 批） |
| K-16 | `mmw` `## Routes` 列不列 `exe-release`、`dispatch` | R4 D2.2 草案两者都列；R9 E13 不列 `exe-release` | **都不列**，Routes 加一句兜底（R9 U-R9-1）。判据是「只列会改变去处或带门槛的行」。`exe-release` 那一行没有独有门槛，只是把 description 的触发再写一次；「跑一夜、跑一张票、改模型或 runner、开任务板 → `dispatch`」同样只是 `dispatch/SKILL.md` 第 3 行 description 的复述，也没有门槛（开夜前的 `--lint` 由 `night.md` 1b 自己要求）。R4 自己排除 `research` 等技能的理由正是这一条。SSR `### Descriptions` 加一条判据管住这类行（R9 W-SSR-9） |
| K-17 | 新词条放哪、叫什么 | R4：四条都进 toolbox；R5、R10：**role pointer** 进 night；R9：**mode** 词条，`_Home_` 是 SSR `## Layers of the set`；R10：词条名用 `mmw`，不用裸词「mode」；R11：**principle** 的 `_Home_` 是 SSR `### Principles`，并与上游 `## Principles` 区分 | **role pointer** 进 night（它的邻词 **wake**、**ack** 都在 night）。toolbox 加 **`mmw`**（定义里写「the set's one mode」，并与 **permission mode** 区分）、**playbook**、**principle**（写明与上游 `codebase-design`、`triage/AGENT-BRIEF.md` 里的 `## Principles` 不同义）。三者的 `_Home_` 都是 SSR `## Layers of the set`；R11 的 `### Principles` 作为它下面的一个小节（K-28） |
| K-18 | 技能名撞名的检查放哪 | R4 D3.6 第 6 类放 `check_wiring.py`；R10 T3 改为 `check_own_skill_frontmatter.py` 查 `name` 等于目录名 | **R10**。`install.sh` 已按目录名查重（R10 S3），两者合起来覆盖宿主看到的名字，也不必再写第二个 `skills.txt` 解析器 |
| K-19 | 原则文件的 `**Why:**` 写不写 ADR 编号 | R10 §2B：ADR 编号放括号里作出处；R11：只用文字写事实，slug 到 ADR 的对照只放新 ADR | **R11**。消费仓库没有本仓的 `docs/adr/`（ADR 0012 选项 2），在本仓写路径又会指向工作树里的副本；SSR 沉积表把 ADR 号归维护者文档。连线里 `principle -> ADR` 的边随之改为 `adr:0034 -> principle` |
| K-20 | 分叉技能的 `agents/openai.yaml` 删不删 | R6 I18、C10：留（说不出收益）；R7 A2、B2：删 | **四份都删**，收益是去重复：`short_description` 与 description 同义，是第二份。它依赖第 2 批的 SSR 改写：SSR `### Upstream skills` 第 106 行今天把「adapted from」上游的技能也算作 upstream skill，而第 70 行括号写「upstream skills keep their `agents/openai.yaml`」（M20），按现行文字分叉技能恰恰应当保留；第 2 批改写把分叉技能明确划出 upstream skill 的定义、归入「this repository wrote」，之后才与第 70 行一致。开关配对规则（`merge-notes/README.md` `## disable-model-invocation`「两处同增同删」）不受影响：四份现在都没有 `policy` 行（M20），分叉技能也不设 `disable-model-invocation`。Codex 上显示名会不会从 `display_name` 变成技能名，列为 X-21 |
| K-21 | 角色操作文件加不加 `**Leaves:**` 行 | R4 D3.2：下一轮编辑时顺带加；R5、R6：`night.md` 第 5 行与 `implement` 第 8 步已说清，不加 | **不加**，并从 SSR `## Layers of the set` 的角色操作文件格式里去掉这一项。改为：角色操作文件在开头段或 Done when 里写出留下什么、给谁（L7 C.6 信号 3） |
| K-22 | `implement` 第 3 步的步骤名 | R4 例子 `Start the reviewer`；R6 X5 `Review round` | **Review round**。`RESUME:` 在「reviewer 已报告、之后没有自己的运行」时指向它，那时要做的是修，不是起 reviewer |
| K-23 | 发给夜 orchestrator 的指针先点 `## On waking` 吗 | R4 D1.2：先 `## On waking`，再 `night.md` **3**；R5 B4：直指 **3** | **R5**。`## 3` 第 1 步本来就是「Do steps 1-3 of `## On waking`」，指针再点一次就是重复 |
| K-24 | 调用开关推导规则算不算能力技能之间的调用 | R4 D1.3 只算 Routes、playbook、角色操作文件、启动提示词；R9 W-SSR-20 把「另一个技能按名调用」也算进去 | **R9**。`diagram-design`、`writing-for-agents` 正是被能力技能调用的；上游哪天把它们改成用户触发，调用方就会断链（R4 V1）。今天推导结果不变 |
| K-25 | 消费仓库 `AGENTS.md` 那一行由谁写（R4 U4） | R7 J2、R9 M13：工程决定，由 `mmw` (c) 行写，`dispatch.sh check` 警告，不放进 `setup-matt-pocock-skills` 或 `manage-agents-md`；R10 U-A：要问 owner | **分两半**。不放进上游技能与通用技能：这是工程决定，按 R7、R9 定。`mmw` 是否自动改 owner 各个仓库的 `AGENTS.md`：它改的是 owner 所有仓库里的指令文件，转给 owner（U-4） |
| K-26 | `manage-agents-md` 重写时会不会删掉 `mmw` 行 | R9 M6、M7：改文字，承认指针行；R10 U-S2：先实测 | **两者都做**：第 3 批按 R9 改文字（R9-V3 已核实三处冲突），再按 R10 的办法实测（X-30） |
| K-27 | `mmw` `## Principles` 的索引行怎么写、算不算重复 | R9 W-SSR-12：在 Duplication 条加一句「索引行是指针」；R11 D1 第 4 条：「步骤里的具体规则与原则文件不算重复」；审查意见：索引行不写规则句 | **索引行只写 Title、slug 与何时适用，不写规则句**。规则句只在原则文件里，否则核心句写成两份（L7 C.6 信号 3、SSR 事实 7）。这是有意偏离 pstack：pstack 的索引行带「一句要点」（L7 A.1，已对照原文），理由是任务开始时读一遍索引就看得到全部原则；在 MMW，读 `mmw` 的是人启动的会话，何时适用足以让它在需要时打开原则文件，而真正用到原则的步骤（`idea-to-tickets` **Tickets** 与角色操作文件）各自带括注，要点句不会多改变一个决定。划界句合成 SSR 一处：放在 `## Layers of the set` 的 `### Principles` 小节里，同时覆盖索引行与步骤括注；Duplication 条原文不改，只在那里引一句 |
| K-28 | 写原则的规矩放 SSR 哪里 | R9：`## Layers of the set` 第 4 段；R11：新 `### Principles`，放在 `### Hand-offs` 之后 | **`## Layers of the set` 下的 `### Principles` 小节**，内容取 R11 D1 的五点 |
| K-29 | `night.md` 各步补不补 `Done when` | R4 D3.2 的 playbook 格式要求写；R5：退出码行已经是完成判据 | **不补**。`Done when` 只对头部 playbook 强制（SSR `## Layers of the set` 按此写）。与 L7 D.1 的对应（已对照原文）：pstack 的 todo 抄写让代理看得见跳过了哪步（「so you can see what it chose not to do」）；`night.md` 每步以退出码收尾，跳过的步骤会在下一条命令的拒绝里出现，`idea-to-tickets` 由 `**Reply:**` 逐个交代没做的步骤 |
| K-30 | lint 第 2 类的范围 | R4 D3.6：MAIN 看 `night.md` `## 3`，WORKER 看 `implement`；R5：MAIN 按 `by` 分三种 | **R5**，输入按 K-46 扩大：按指针表逐行核对，每个（角色，`by`）对应的操作文件对会发给它的每个事件恰好有一个处理行。事件取自 `relay.py` 的 `WAKES` 与单独定义的 `worker.queued`、`relay.recovered`，`child.opened` 按 kind 区分；`watchdog.py` 的每个告警前缀在自己的文字里带下一步或指针 |
| K-31 | e 类段里夹着的 MMW 名词挪不挪到调用方 | R4 D5.3 e 行举例 `tdd`、`resolving-merge-conflicts`；R6 X2：挪了段落仍与上游不同，拿不到回原文 | **不挪**（R6） |
| K-32 | `install.sh --check` 为 Self-hosting boundary 加什么可见检查、改不改退出码 | R4 C15：只报告；R10 I2：只列 `watches.json` 里开着的 watch，不改退出码，措辞避开过滤词 | **R10，并扩大范围**：同时列出各状态目录里 `relay.lock`、`watchdog.lock` 指向的活进程（M27）。`summary` 的 exit 1 明确允许「a relay was left running」；这样的旧版本 relay 若在提升之后被新的 `open` 接上，新代码写 `by` 字段、旧进程不读，唤醒不带指针，同一次运行就混用两个版本。四步提升的第三步要求 watch 与这些进程都不存在。不改退出码：已核实（M7）`--check` 非 0 会触发自动重装 |
| K-33 | `idea-to-tickets` `## Where you are` 的行 | R4：4 行；R7：7 行；R8：再加 2 行界面链重入点 | **合并成 9 行**（见 2.2）。R8 的两行放在「已有定下的决定」那一行之前，否则已 pull、未写 screen contract 的界面工作会跳过 `write-screen-contract` |
| K-34 | `wayfinder` 的 `mmw:map` 回不回上游 | R7 D2：回，以走查为前提 | **有条件采用**。X-11 的走查不过，就把 `mmw:map` 按 e 类留在 `wayfinder` |
| K-35 | SSR 的角色操作文件格式里写不写 `**Leaves:**`、`Done when` | R9 W-SSR-3 第 3 段写「无人值守的以 `**Leaves:**` 收尾」 | 随 K-21、K-29 改：只写「开头段或 Done when 说明留下什么」 |
| K-36 | 原则引入的来源 | R9 W-SSR-3 第 4 段写 pstack 引入的做法；R11 D1 第 5 条写 `retro` 的 `mmw-skill` 提案或用户决定 | **两条都写**：新原则来自 retro 的提案或用户决定；外来原则过七道门槛后照录 |
| K-37 | 根 `AGENTS.md` 里 night runbook 行写路径还是写技能名 | R4 未涉及；R10 A4 改为技能名 | **R10**。已核实同一文件的 Self-hosting boundary 要求运行时只读已安装副本（R10 S15） |
| K-38 | SSR、RSS 留在上游 `writing-for-agents` 目录，还是搬到 MMW 自己的家 | R9 §1.5.2：不搬，理由是「搬进 `mmw` 会让上游第 8 行去点名 `mmw` 的文件，`writing-for-agents` 从此依赖 `mmw`」；审查：第三种做法是第 8 行恢复原文、两份搬走，由已经指向 SSR 的读者点名 | **搬到仓库文档 `docs/skill-set/`，文件名不变；`writing-for-agents/SKILL.md` 第 8 行恢复上游原文；第 2 批**。R9 的理由在总图内部不成立：上一版连线本身就有 SSR 以 `mmw` 的文件为范例的边，上游目录里的文件已经依赖 `mmw`。两者全是 MMW 自己的规则（M12：上游没有这两份，+209 行），留在 subtree 里是上游目录中最大的一块 MMW 文字。收益：上游回原文（209 行离开上游目录，第 8 行恢复）；消除上游目录对 `mmw` 与 `check_wiring.py` 的依赖（依赖方向改为 MMW 文档指向上游 `writing-for-agents`）。读者不丢：在本仓改技能文字的 agent 每回合都加载根 `AGENTS.md`，它第 49 行已指向 SSR，只改路径；`retro` 第 11 步点名的是 `writing-for-agents` 的 `SKILL.md`（M12），它写提案的目标是所在仓库自己的文件，用不到 MMW 的规则；本仓自己跑夜时的 retro 照样加载根 `AGENTS.md`。成本：约 50 处路径（toolbox CONTEXT 26、ticket-run 1、merge-note 19、两个 lint 文件头、根 `AGENTS.md` 1），与第 2 批已有的 85 处同一类改动，同一次提交。放弃的另一个家是 `mmw/references/`：`mmw` 的读者是人启动的任务会话，不是写技能的人，按 `CODING_STANDARDS.md` `## Skills and scripts`「技能目录只放持有技能的 agent 读或跑的东西」，放进去会让它随安装进入每个消费仓库而没有读者 |
| K-39 | 第 3 批与实测 T1 的先后 | 上一版：第 3 批先建 `mmw` 与 `idea-to-tickets`，T1 只作为第 4 批的前提 | **T1（连同 X-10、X-29）是第 3 批发布的前提**。第 3 批新加的 playbook 是「想法 → 票」顺序的又一个家，原有的家要到第 4 批才删；T1 若在第 3 批之后才不过，第 4 批取消，重复就永久留下，`AGENTS.md` 那一行也不起作用（L7 C.6 信号 1、3）。第 10 节的实测本来就在隔离 home 里用开发版技能做，不需要先发布。T1 不过时，改走宿主钩子注入（R4 T1 的退路），或者不建 mode |
| K-40 | Head judgement 放 `mmw` 还是 playbook | R7 K2：迁进 `mmw` `## Head judgement`，playbook **Who checks** 引用它；R4 Routes「有东西坏了」行写「修法按 `## Head judgement` 走」，后来的 Routes 删了这半句 | **判断的原文放进 `idea-to-tickets` 的 Who checks 一步，`mmw` 不设 `## Head judgement`**；Routes 第 4、5 行把排错后的修法与架构整理定下的决定送到 **Who checks**。在残留 `ask-matt` 里它本来就是主流程第 3 步的一个分支（M29）。放在 mode 里时，上一版 `## Where you are` 的 (e) 行先判一次却不改变任何路由，真正起作用的只有 playbook 那一次（L7 C.6 信号 9）；现在判断只有一个家，却有三个入口（playbook 顺序、Routes 第 4 行、第 5 行） |
| K-41 | 原则 `the-tracker-is-the-state` 现在建不建 | R4、R11：建，十一处括注里有四处属于它 | **暂缓，第 3 批只建另外两条**。它的前半句就是 `dispatch/SKILL.md` 第 8 行原话，后半句「等别人就结束回合，由事件叫醒」已由 relay、turn guard 与 `RESUME:` 在机制上强制（M25）；括注里两处在 `mmw` 目录本身，另两处是原话所在的行和按 `RESUME:` 执行的行。它能改变的决定主要只有 `idea-to-tickets` 的白天重入，L7 C.6 信号 7 与信号 4 的风险都在。在它建成之前，`idea-to-tickets` `## Where you are` 本地写一句「事实只取 tracker、仓库与用户本条消息」。X-13 的走查证明它会改变白天重入的决定，再建并加括注；否则并回第 8 行 |
| K-42 | `mmw` `## Where you are` 要不要处理唤醒行 | 上一版：(b) 以 `#<n> `、`relay.recovered`、`watchdog:`、`MMW turn guard:` 开头的行照行尾指针做，没有指针走 `dispatch` `## On waking` | **删掉这一行**。第 1 批之后唤醒行自带指针，指针的设计前提就是不依赖 `mmw`（worker 从不加载它）；orchestrator 的 `night.md` 事实表第 3 行与 `one-ticket.md` 第 3 步已处理这四种行；唯一没有指针的 turn guard 行文字自带全部步骤（`turn-guard.py` 第 306–311 行）。这一行只会让它多绕一跳（L7 C.6 信号 3）。若 T2（X-2）实测证明压缩后确实丢了去处，再以测到的失败作为理由加回 |
| K-43 | 步骤命名之后残留的按编号引用 | 上一版：`writing-interface-code.md` 三处「closing step 1」算同一技能内部，不动；playbook 引用「`phase-boundaries.md` 第 3 问」 | **都改成按名引用**。三处「closing step 1」（M30）在第 1 批与八步加名同一次提交改为 **Integrate and run**，lint 第 1 类顺带核对；playbook 按原文小节「**3. Do you need to hand off?**」点名（M28）。第 1 批给步骤起名就是为了消除按编号引用（L7 C.6 信号 8），另一个文件的引用同样受编号变动影响 |
| K-44 | `check_wiring.py` 第 4 类（原则引用、文件、索引三方一致）现在加不加 | R10 T2：第 4、5 类「没有失败过的运行，它们的依据是事实 7 被废止这个决定本身」；本文第 11 节却以「找不到它防住过的失败运行」为由让 SSR `### Paths and host neutrality` 继续人工 grep | **第 4 类暂缓，第 5 类保留**，两处用同一条标准：加机制要有已核实的断点或失败。第 5 类以 `ask-matt` 路由表的真实漂移为依据（R4 §9）；第 4 类只守两个原则文件和 5 处括注，没有已核实的断点。X-13 证明原则确实被读、括注确实会漂移之后再加；在此之前 SSR `### Principles` 要求改原则 slug 的人 grep 两种括注写法 |
| K-45 | 第 2 批的发布顺序 | 上一版：第 2 批「授权一次 `install.sh`（软链目标变了）」，未规定与移动已安装 checkout 的先后，后果写成「改了但不生效」 | **移动已安装 checkout 与跑 `install.sh` 在同一次操作里连着做，中间不开任何会话；`install.sh --check` 通过之前不开夜**。分叉后上游目录恢复成 squash 原文，而宿主软链在 `install.sh` 重跑之前仍指向已安装 checkout 里的 `mmw-v2/upstream/skills/engineering/<名>`：checkout 一移动，宿主读到的就是上游原版，`implement`、`to-spec`、`to-tickets` 带 `disable-model-invocation: true`，`code-review` 是两轴审查、没有 `references/session.md`（M15）。后果是 worker、reviewer 和白天的 `to-spec`、`to-tickets` 会话读到错误的版本，不是「不生效」。夜间有 `dispatch.sh check` 的自动重装兜底；U-5 若选「只报告」，按 `dispatch.sh` 原文「an incomplete install does not stop the night」，夜会带着上游原版照常开。放弃的另一种做法是把第 2 批拆成两次发布（先装 `self/` 副本，再恢复上游目录）：它多一次提升和一次 `install.sh` 授权，收益只是避开一次「连着做」 |
| K-46 | `watchdog.py` 告警的处理指令放哪里 | 上一版：每条告警同一行接指针，把人送到 `night.md` `## 3`；但那张表只有 `watchdog: #<n> silent since …` 一行（M16） | **每种告警在自己的文字里写出下一步，再接指针；`night.md` `## 3` 的表加一行兜底「其他 `watchdog:` 告警：照告警写的下一步做」**。告警由脚本判定、由脚本拼字，下一步放在同一处只有一个家，单票 orchestrator 与 adopt 会话也读到同一段文字（SSR 事实 2：脚本说出发生了什么、下一步做什么）。放弃的做法是在 `night.md` 为八种告警各补一行：那样每改一次告警就要改两处。每种告警的具体下一步在第 1 批读 `watchdog.py` 全文后写定（X-35）。`check_wiring.py` 第 2 类的输入扩到 `watchdog.py` 的告警前缀、`worker.queued`、`relay.recovered`，并区分 `child.opened` 的不同 kind（`night.md` 里 `contract` 有两行）。adopt 会话本身就是自己那个 watch 的 orchestrator，也会收到告警；`watchdog.py` 对 `by=adopt` 的 watch 不附 `dispatch.sh resume <n> …` 命令，`inside-a-ticket.md` 那一句写明 `watchdog:` 行也照「告诉用户」处理，避免两条指令 |
| K-47 | worker 指针指向哪里，没有运行记录时 `RESUME:` 印什么 | 上一版：worker 指针固定写「the `dispatch` skill's `## On waking`, then the `implement` skill's `## Closing steps`」 | **指针改为「`dispatch` 的 `## On waking`，再跑 `verify-ticket.py <n> --preflight`，照它的 `RESUME:` 做」；`resume_at` 在已认领、没有运行记录时返回「Claim, read in, write the code」**。`resume` 常发给还在写代码的 worker：`contract` 子票改正后的 continue、`fault` 修好之后、watchdog 的 idle 告警。这些状态下 `resume_at` 今天返回 `None`，`--preflight` 不印 `RESUME:`（M17），原指针会把代码没写完的 worker 送进以「Once done, commit your work」开头的 `## Closing steps`。`implement` 第 74 行补一句：没有 `RESUME:` 行时回到 `## Claim, read in, write the code`。新取值写成字面，由 lint 第 1 类核对（K-2）。X-34 实测 |
| K-48 | `status` 首行 `RESUME:` 的两处取值 | R5 J1：已开夜、frontier 非空或有活 agent → 「3.」；有 `spec.closed` → 「5. The night is over」 | **加一个取值、改正一个**。有 `spec.opened`、本批还没有任何 `worker.started` → 「1b. Before the batch」：orchestrator 若在 `open` 之后、第一次 `advance` 之前被压缩，原取值送它去 `3.`，而 `3.` 第 4 步直接跑 `advance`，跳过 1b 的 `verify-ticket.py <spec> --lint` 与 `target_config.py --check`，`dispatch.sh` 自己不跑 `--lint`（M18），跳过后没有别的东西补上；这个状态可以从事件算出，重跑 `--lint` 只读不写。有 `spec.closed` → 「5. The night is over, from the paragraph that invokes the `retro` skill」：恢复原事实表的段落限定（M18），否则 summary 已记下 `spec.closed` 之后被压缩的 orchestrator 会回去重跑 `reverify` 与 `summary` |
| K-49 | `idea-to-tickets` 在宿主自动压缩后的重入 | 上一版：**Spec** 门槛要求 **Grill** 到 **Tickets** 在同一个未清空、未压缩的上下文里；`## Where you are` 有一行「对话里已有定下的决定、没有 spec → **Who checks**」 | **部分改**。**Spec** 加一条：宿主在阶段中间自动压缩了（不是用户发起的），就先把摘要里带着、`CONTEXT.md` 与 ADR 里没有的决定逐条与用户确认，再调 `to-spec`。依据是 `PHASE-BOUNDARIES.md`「Compacting mid-phase makes the agent lose the thread」（M28）与同文件「a fresh session that is confidently wrong about a decision the summary flattened」；这个 playbook 由人启动，用户在场，确认的成本是几轮问答。那一行改为「用户本条消息带来已定下的决定、没有 spec → **Who checks**」：用户的当前消息在上下文里看得见，不是会话记忆。不采用「先写进 spec 草稿或 tracker」：那会给决定一个新的存放处，要新定格式与读者。X-9 加一个中途压缩的走查场景 |
| K-50 | `merge-notes/README.md` `## 旁加的文件` 何时写、列哪些 | R10 M7：第 4 批，列 SSR、RSS 与第 4 批 d 类新加的文件 | **第 2 批，列 M6 的 5 个文件**（`prototype/EXP.md`、`prototype/evidence-page.md`、`triage/references/pipeline-issues.md`、`wayfinder/references/interface-and-remake.md`、`wait-what/VISUAL.md`）。这 5 个今天就在上游目录里，第 2 批本来就要改写 `merge-notes/README.md`（`## 分叉的技能`、推导规则）并写 SSR 的 a–f 表，d 类的家同一次提交写定；SSR、RSS 搬出（K-38），state list 格式不进上游目录（K-14），所以不在表里 |

R5 U-N1（夜外 `adopt` 是否继续支持）不列为用户决定。保留现状、补一句处理，不改变任何可见行为；只有 owner 主动想收窄这条用法时才需要决定。

---

## 6. 不动清单汇总

下列部件原样不动。各单元逐条理由见所引报告的「不动清单」一节。

| 部件 | 理由（一句） | 出处 |
|---|---|---|
| 五个角色操作文件的名字与结构，以及三份（`advising.md`、`night.md`、`one-ticket.md`）的位置；`implement` 与 `session.md` 随分叉整目录搬家 | 单一入口、单一任务不拆三层（L7 C.1 第 7 问）；脚本文字、启动提示词、测试按字面点名它们（R4 V2） | R4 §15、R5 §5、R6 §7 |
| `dispatch/references/` 目录名与四个文件名 | 改名拿不到收益，脚本按路径点名 | R5 §5 |
| `night.md` 除事实表、exit 0 一句与两个括注外的全部 | 长内容只有一个调用方，机械部分已在脚本里（L7 C.4）；ADR 0012 要求 closing pass 的本体在这里 | R5 §5 |
| `one-ticket.md` 除第 3 步外；`inside-a-ticket.md` 除一句外；`editing-models.md` | 分支 reference，只有一个调用方 | R5 §5 |
| `dispatch.sh` 启动提示词、`AUTONOMOUS`、`PRODUCT_RULES`、「角色 → 技能」的 case 分支 | 改字拿不到收益；首句由测试核对角色到技能的映射，`PRODUCT_RULES` 引用的标题由 `check_wiring.py` 第 1 类核对（M19）；`AUTONOMOUS` 是 reviewer 唯一读到的「不提问」 | R4 §15、R5 G3 |
| `relay.py`、`watchdog.py` 的判定逻辑；`statedir.py`、`ghlist.py`、`models.py`、`hosts.json`、`runners/*.sh` | 已跑通；天然整体 | R5 §5 |
| `turn-guard.py` 全部；`tool-guard.py` 除 `NO_QUESTION` 外 | 拦截文字自带步骤；事前文字与事发拒绝读者读到的时刻不同 | R5 §5 |
| `retro` 全部 | 能力技能，内部步骤服务一个交付物（L7 C.3）；与 `retro.py` 是合同两端 | R5 §5、K-7 |
| `implement` 的全部内容（只加步骤名与括注）、两份 reference | worker 的操作文件 | R6 §7 |
| `code-review` 的分派表、`session.md`、三个 axis 文件；`spec-reviewer.md` 除半句外 | 每个 axis 子代理只读自己那一份（L7 C.5）；用户决定 `0ac93ab8`、`4756d4d3` | R6 §7 |
| `verify-ticket` 全部（第 16 行保留，`resume_at` 除外）；`events.py`、`issue_tree.py`、gate-check | 能力内部；被全流水线导入 | R6 §7、K-6 |
| `advisor` 全文 | ADR 0014 的两扇门；锚点只登记，不改字 | R6 §7 |
| `tdd`、`resolving-merge-conflicts` | e 类，挪名词拿不到收益 | R6 X2、K-31 |
| `to-spec`、`to-tickets` 的内部步骤、模板与五份 reference；`to-spec` `## Next` 与 `to-tickets` 第 8 步末句 | 天然整体；分叉只是整体搬家；后继句分叉后是自有文本，第 4 批后是这条顺序唯一的家（K-7） | R7 §5、K-7 |
| `grilling`、`grill-me`、`domain-modeling`、`codebase-design`、`research`、`diagnosing-bugs`、`wizard`、`teach`、`wait-what`、`handoff`、`to-questionnaire`、`setup-matt-pocock-skills` | 单一能力，改动是 a 类或 e 类，没有流程段要搬 | R7 §5 |
| 7 个用户触发技能的开关 | 推导结果与现状相同 | R7 §5 |
| `prototype` 规则 1、`LOGIC.md`、`EXP.md`、`evidence-page.md`、`UI.md` 其余 e 类改动 | 三个入口都读；删掉后 agent 会做错 | R7 F2、R8 §7、K-14 |
| `wayfinder` 的 effort 目录名、第 4 步与 `interface-and-remake.md`、第 5 步 | 跨技能的数据约定；按自身输入选 reference；e 类 | R7 §5 |
| `triage` 第 70、22 行、`## Roles`、`AGENT-BRIEF.md`、`OUT-OF-SCOPE.md`，`pipeline-issues.md` 其余 | e 类；已是 d 类的正确形态 | R7 §5 |
| 四处 setup 指针（`to-spec` 第 8 行、`to-tickets` 第 12 行、`triage` 第 43 行、`wayfinder` 第 24 行） | 有意的同句，SSR 范例表把它当范例 | R7 §5 |
| `ui-acceptance` 除 description 半句与表第 1 行外的全部（含 Five rules 的编号与标题） | 被三个文件和启动提示词逐字引用 | R8 §7 |
| `design-pages` 除两处改指外；`write-screen-contract` 除一个从句外；`screen-contract-format.md` 独立成文件 | 下一步取决于自身输出；脚本拒绝文字按文件名送 worker 过去 | R8 §7 |
| 三份交接 reference 的内容（`cutting-interface-tickets.md`、`writing-interface-code.md`、`ui-reviewer.md`），`writing-interface-code.md` 的三处「closing step 1」除外（K-43） | 随分叉整体搬家，不改字 | R8 §7 |
| `exe-release`、`code-checkers`、`manage-agents-md`（除一句半）、`diagram-design` | 能力技能，没有流程段；不进 Routes | R9 §5 |
| `merge-notes/diagram-design.md` | 给每行标 a 类或 e 类只是格式统一，说不出用户要求 2 的六种收益；等下一次拉 `diagram-design` 上游、这些行真要取舍时再顺带标 | R9 D16 |
| `dispatch/SKILL.md` 第 8、25 行与 `to-tickets` 第 84 行的文字 | 本地已写理由，加原则括注不改变决定（K-9）；第 8 行也是暂缓原则的原话所在（K-41） | K-9、K-41 |
| `shared.md`、`hosts/*.md`、`render.py`、`prompt/` | 宿主级提示，不是 MMW 组件；ADR 0014 | R10 §6 |
| `install.sh`（除 `--check` 一项）、`skills.txt` 格式、`models.json` 结构、board、`migrations/`；不建迁移 | 装 `mmw` 与分叉都不需要改代码；不改任何存下的状态 | R10 §6 |
| `check_module_paths.py`、`check_upstream_em_dashes.py`、`parse_k.sh`、`run_unittests.py` | 范围按目录自动跟上分叉 | R10 §6 |
| `downstream-notes/` 全部 | 四批都不让消费仓库产物失效 | R10 D1 |
| 根 `AGENTS.md` 开头四段、`## Self-hosting boundary`、`## Package Manager`、`## Key Conventions`、`## Gotchas` 第 2–5 条 | 原文「its skills」已覆盖 `mmw` | R10 §6 |
| 现有 31 份 ADR 正文 | ADR 记录当时的决定，变化另写新 ADR | R4 §15 |
| `docs/notes/` 正文（除两处路径） | 设计说明自称以代码为准 | R6 M3 |
| 消费仓库私有组件 | 数据与仓库规则，格式不变（R4 D7.6） | R10 Q1 |
| N9 PC3、PC6–PC16（不做成原则） | 已有家、由机制强制，或绑定单一机制 | R11 G、§3.3 |
| 七个不建的 playbook：wayfinder、triage、排错、代码健康、界面链、接入新仓库、出包与写组件 | 只调一个技能，或只会复述能力技能的结尾（L7 C.6 信号 3、5、9、10） | R4 D3.1、R8 §3、R9 §2 |
| 顺路发现、另开普通票的缺陷 | 不属架构：`dispatch.sh` 头注释漂移（N10 B12）；ADR 0012、0027 与实现不一致；`CODING_STANDARDS.md` 与 ADR 0027 不一致；`TESTING.md` 漏 `statedir.py`；merge worktree 名；ADR 里失效的 `refusal.py` 路径；`tickets/CONTEXT.md` 第 352、360 行；`exe-release` F1–F4；`diagram-design` F5、F6；种子与落地件漂移 | R5 G5、R9 §5、R10 §10、R6 §7、R7 J4 |

## 7. 旧规则处理汇总

| 规则 | 处理 | 原本防什么 | 新架构怎样解决、原意怎样保住 |
|---|---|---|---|
| SSR、RSS 放在上游 `writing-for-agents` 目录，由其 `SKILL.md` 第 8 行指过去 | **改为搬到 `docs/skill-set/`**（K-38） | 写技能的人一定读到这些规则 | 在本仓写技能文字的 agent 每回合加载根 `AGENTS.md`，第 49 行指向 SSR（今天已有，只改路径）；上游 `writing-for-agents` 恢复原文，不再依赖 MMW 的文件 |
| SSR 事实 1–5 | 保留 | 各自原意 | 事实 4 的「上游 `implement` 五行」在分叉后仍成立，因为上游那份恢复原文 |
| SSR 事实 6「Skills are peers composed by name」 | **改写**（R9 W-SSR-5） | 嵌套技能；复制别人的规则 | 能力技能之间仍是平级件；能力技能不点名 playbook 的顺序；playbook 与原则是 `mmw` 目录里的文件，按「the `mmw` skill's …」点名，不算嵌套 |
| SSR 事实 7「一个家」与「第二份就是 finding」 | 保留 | 副本漂移 | 原句不动（R9 W-SSR-6） |
| SSR 事实 7「MMW ships no router skill」 | **废止**（R4 §9、R9 W-SSR-7） | 第二份地图漂移（`ask-matt` 的漂移）；一跳找不到下一步（#538） | 路由只有一个家（`mmw` `## Routes`），顺序只有一个家（playbook 或角色操作文件），由 `check_wiring.py` 第 3、5 类保证一致；Routes 只列改变去处或带门槛的行（W-SSR-9、K-16）。取代它的决定记在 ADR 0034 |
| SSR 事实 7「结尾段说下一步；按流水线读结尾段从想法走到关票」 | **改写**（R9 W-SSR-8） | #538 | 改成「从 `mmw` 出发，路由、playbook 步骤与角色操作文件连起来能走到关票，一个时刻不被两处认领」；由 RSS 第 4 步的走查与 lint 检查 |
| SSR `### Load and disclosure` | 保留 | 规则写错读者；重入时重复副作用 | 「A rule sits in the text of the agent that must follow it」成为原则层的边界（R4 D4.2） |
| SSR `### Redundancy and bloat` Duplication 条 | 保留，在 `### Principles` 里引一句划界 | 一个意思写两处 | 索引行只写名字、slug 与何时适用，规则句只在原则文件里；步骤括注是指针；原则文件不复述调用方的具体规则（K-27） |
| SSR `### Scripts and judgement` | 保留，不加句 | — | 锚点规则写进 `CODING_STANDARDS.md`（K-11） |
| SSR `### Descriptions` | 保留，第 2 条扩大 | 两个 description 争一件事 | 并排读时把 `mmw` `## Routes` 一起读，与 description 重叠又没有门槛的 Routes 行删掉（W-SSR-9）；第 4 条（SSR 第 70 行，自有技能没有宿主清单）配合 `### Upstream skills` 改写后把分叉技能归入自有，分叉的四份 `openai.yaml` 因此删掉，收益是去重复（K-20） |
| SSR `### Vocabulary` | 保留 | 一词多义 | 四个新词条的归属见 K-17；「by title rather than by number」成为 `RESUME:` 改印步骤名的依据 |
| SSR `### Hand-offs`「Each skill ends by naming what comes next, or the caller it returns to」 | **改写**（R9 W-SSR-15） | 产出无人接手 | 上游技能里的 MMW 下一步句移走，下一步由 playbook 步骤点名；能力技能写交回什么；取决于自身输出的保留分支；MMW 自有技能（含分叉后的 `to-spec`、`to-tickets`）与 `retro` 一样，保留各自唯一的后继句或调用方（K-7）；不设固定返回句 |
| SSR `### Hand-offs`「Each event gets one instruction」 | 保留，部分变成机制 | 同一事件两种指令 | `WAKES` 事件、`worker.queued`、`relay.recovered` 与 `watchdog:` 告警由 lint 第 2 类检查（K-30、K-46）；`NO_QUESTION` 改为每个角色各一条出路（K-5） |
| SSR `### Hand-offs` 调用写法 | **补写**（R9 W-SSR-16） | lint 漏报（R4 K9） | 只认五种写法，包括「tell the user to run `/X`」 |
| SSR `### Prompts written for other agents` | 补一条（R9 W-SSR-18） | 提示词替被启动方定范围 | 脚本送进会话的消息可在同一行末带角色指针，指针只是地址 |
| SSR `### Upstream skills`（各条） | **改写**（R9 W-SSR-19–22） | 上游被改写后无法跟进 | 用 a–f 分类表；「不到一半是上游的行」改为分叉；d 类加前提（K-14）；调用开关推导规则（K-24）；外来技能四条进门检查 |
| SSR `## Editing`「A fix that adds a mechanism names the run in which the failure occurred」 | 保留，统一用于 lint 各类 | 机制堆积 | 第 1–3 类与第 5 类各有已核实的断点或漂移；第 4 类没有，暂缓（K-44）；`### Paths and host neutrality` 仍是人工 grep，理由相同 |
| SSR `### Paths and host neutrality` | 扩范围（W-SSR-23） | 路径与宿主绑定 | grep 扩到 `mmw/playbooks/`、`mmw/principles/`，并查指向 `mmw-v2/` 的路径（冻结） |
| SSR `## Verifying` 第 2 条 | 改半句（W-SSR-26） | 走查跳过路由 | 人带来的任务从 `AGENTS.md` 那一行加载 `mmw` 起步 |
| RSS 第 2、4 步 | 改写（W-RSS-3、5） | 走查的起点与实际不符 | 从 `mmw` 或唤醒行起步；先跑 `check_wiring.py`，它查过的不再手查 |
| `merge-notes/README.md` `## 本仓自有正文的技能` | **废止**，由 `## 分叉的技能` 取代（R10 M1） | 拉上游时误合并本仓正文 | 分叉技能不在 subtree 里，不会再被合并 |
| `merge-notes/README.md` `## disable-model-invocation` 的 7 个名单 | **改写成推导规则**（R10 M2、K-24） | 抢触发；夜里被误触发；往产品根写文件 | 没被调用的保持上游设置，今天的结果与名单相同；六份 merge-note 里的复述删除 |
| `merge-notes/README.md` 「两处同增同删」、`## host 中立` | 保留 | — | — |
| ADR 0003、0006、0007、0015 | 保留 | — | `mmw` 是普通技能，不进 `shared.md`；角色 = 提示词加 `models.json` 一行 |
| ADR 0008 | 保留 | 闸口什么都没做却读起来像通过 | 是 `silence-is-never-a-pass` 的依据（记在 ADR 0034） |
| ADR 0010、0017、0018、0019 | 保留 | 轮询；会话记忆不可靠；静默顶替 | 是另两条原则的依据 |
| ADR 0014 | 保留两条理由 | 到不了 Cursor；为不相干的事付每回合的常驻成本 | 同样否决把 `mmw` 或原则写进 `shared.md` |
| ADR 0020「唤醒文字只带 `#<n> <event>`」 | **修订一句**（ADR 0032） | 唤醒文字复述 tracker 会过时或自相矛盾 | 同一行末的角色指针只含技能名、文件、小节，不含 tracker 数据 |
| ADR 0012、0027 与实现的分歧 | 不在本次范围 | — | 另开票 |
| 根 `AGENTS.md` Self-hosting boundary | 保留，补一项可见检查 | 一次运行混用两个版本 | `--check` 列出开着的 watch 与持锁的 relay、watchdog 活进程（K-32）；指针只写技能名与技能内路径；四批都在没有 watch、没有这些进程时发布；第 2 批的提升把移动 checkout 与 `install.sh` 连着做，`--check` 通过前不开会话（K-45） |
| `TESTING.md`「测试不钉文字」 | 保留，加一句 | 改措辞就要改测试 | 接线检查另归 `check_wiring.py`；测试与常量比较，不抄字面（R10 K1） |
| `CODING_STANDARDS.md` `## Skills and scripts` 的列举 | 改写 | 技能目录只放持有技能的 agent 读或跑的东西 | 列举补 playbooks 与 principles（R10 C1） |
| Memory `411750f5`（description 只写触发；上游能不改就不改） | 保留并加强 | — | 分叉与 a–f 是它的落实 |
| Memory `415f96d0`（理由只放 ADR） | **改写** | 技能正文变长 | 跨任务的理由放原则文件，按需读，不常驻（R11 A1） |
| Memory `ce037679`「写名字不写路径」 | 保留 | — | 指针与括注都写「技能名 + 技能内路径」 |
| Memory `ce037679`「不系统区分用户调用与模型调用」 | **改写** | 给作者加负担 | 只在一处区分：被调用的必须模型可触发，由推导规则与 lint 决定，作者不必判断 |
| Memory `ce037679`「一张与实际同步的总图」 | 落实 | — | 给 agent 的图是 `mmw` Routes 加 playbook，由 lint 保证同步；给人看的图见 U-8 |
| Memory `fe94802d`「平级调用、禁止嵌套」 | 保留 | 可移植性 | playbook 与原则是文件，不是嵌套技能 |
| Memory `fe94802d`「不改上游 frontmatter」 | 按「只为可达性去掉开关、从不关掉」读 | 用开关强制层级会让调用方够不到被调方 | 读法待 owner 确认（U-2） |
| Memory `f4c3d378` | 保留 | 不在技能层路由时 agent 会乱走 | `mmw` 本身是技能 |
| Memory `8ec53374`（角色 = 读哪个 playbook + `models.json` 一行；每条只写一处） | 落实 | — | 不建角色定义文件；跨任务理由只写在原则文件里 |
| Memory `ec59cec8`（规则写成事实） | 保留 | — | 原则文件的规则句按此写 |
| Memory `0ac93ab8`、`9d6755c0`、`4756d4d3` | 保留 | — | review 的规则出处与轴不变 |

---

## 8. 体量估计与落地批次

### 8.1 体量（数量级；标「推断」的在实现后再量，X-32）

| 类别 | 内容 | 行数 |
|---|---|---|
| 搬走 | 四个分叉技能整目录（215 + 325 + 146 + 458 行，扣掉删去的 12 行 `openai.yaml`） | 约 1,130 |
| 搬走 | SSR 176 行、RSS 33 行，搬到 `docs/skill-set/`（K-38） | 约 210 |
| 搬走 | 残留 `ask-matt` 的 `PHASE-BOUNDARIES.md` 57 行；Head judgement、Context hygiene、On-ramps、Codebase health 约 25 行 | 约 80 |
| 搬走 | c 类「下一步」句约 10 行；`triage` route 句 1 段；关 issue 句；state list 段约 3 行 | 约 20 |
| **搬走合计** | | **约 1,450** |
| 删除 | 四份 `openai.yaml`（12）；`ask-matt` 不迁的 `## Vocabulary underneath`、`## Standalone`、`## Precondition`（约 30，随恢复原文消失）；12 个 `run.sh` 的重复行（净 −24）；merge-note 的开关复述与名单（约 −15）；`watchdog.py` idle 文字（−4）；`night.md` 事实表（−2）；上游文档页 `implement.md`（−14）；B7 的两处 description 短语；`spec-reviewer.md` 半句；`write-screen-contract` 一个从句 | **约 110** |
| 新增文字 | `mmw/SKILL.md`（≤100）；`idea-to-tickets.md`（约 70，推断）；两条原则（约 35）；`merge-notes/ask-matt.md`（12）；SSR（约 +40）与 RSS（+2）；词条（约 15）；三份 ADR（约 110）；`CODING_STANDARDS.md`、`TESTING.md`、根 `AGENTS.md`、`tests/AGENTS.md`、`manage-agents-md` 共约 10；`state-list-format.md`（约 10）；`night.md` `## 3` 的 watchdog 兜底行与 `implement` 第 74 行补句（约 2）；5 处括注（各约 8 个英文词，不增行） | **约 390**（不含从 `ask-matt` 搬来的 80 行） |
| 新增代码 | `anchors.py`（约 60）；`relay.py` 的 `pointer` 与 `wake_text`（约 20）；`open_relay --by`（约 8）；`watchdog.py` 八种告警的下一步与 `by=adopt` 分支（约 25，推断）；`resume_one`（3）；`status.py` 的 `RESUME:`（约 45）；`dispatch.sh check` 缺行警告（约 10）；`install.sh --check` 列 watch 与持锁进程（约 30）；`check_wiring.py`（约 230，推断，第 4 类暂缓）；`shared_lints.sh`（约 15）；`check_own_skill_frontmatter.py`（约 8）；`resume_at`（±20） | **约 450–700** |
| 新增测试 | `tests/lints/`（约 200，推断）；`test_preflight.py`（±25）；`test_relay.py`、`test_tool_guard.py`、`test_status.py`、`test_dispatch.sh` 场景（约 50） | **约 250** |
| 改路径 | 分叉：`docs/contexts/` 79 处、`docs/notes/` 2 处、merge-note 4 处；SSR、RSS 搬家：`docs/contexts/` 27 处、merge-note 19 处、两个 lint 文件头、根 `AGENTS.md` 1 处（M12） | **约 135 处**，行数不变 |
| 回到上游原文 | 分叉四目录加 `ask-matt`：从上游目录移走本仓加的约 1,036 行，恢复上游约 186 行（M5）；`writing-for-agents` 移走 209 行、第 8 行恢复（M12）；第 4 批再移走约 14 行 c 类文字；上游文档页两份 | 上游 subtree 的 MMW 改动从 +1674/−415 降到约 +415/−224（推断） |

### 8.2 落地批次

四批都作为本仓库的票，由当时已安装的冻结版本跑；只在 `install.sh --check` 既不列出开着的 watch、也不列出持锁的 relay 或 watchdog 活进程时，才做四步提升的第三步（R4 §11、R10 A3、K-32）。

| 批 | 内容 | 前提 | 需要 owner 做的 |
|---|---|---|---|
| 1 只加固，不搬文本 | `anchors.py`；指针接在同一行，用于 `wake_text`、`relay.recovered`、`watchdog.py`、`resume_one`；worker 指针送它跑 `--preflight`（K-47）；`watchdog.py` 八种告警各带下一步、`by=adopt` 不附 `resume` 命令（K-46）；`open_relay --by` 与 `watches.json` 的 `by` 字段；`status` 首行 `RESUME:`，含 1b 与 `5.` 的段落限定（K-48）；`night.md` 事实表四行、exit 0 一句与 `## 3` 的 watchdog 兜底行；`one-ticket.md` 第 3 步；`inside-a-ticket.md` 一句；`watchdog.py` idle 文字；`implement` 八个步骤名、第 74 行补句、`writing-interface-code.md` 三处改名（K-43）、`resume_at`（含「Claim, read in, write the code」）、`test_preflight.py`；`NO_QUESTION` 三角色及其测试；`check_wiring.py` 第 1、2 类（第 2 类含告警前缀、`worker.queued`、`relay.recovered`）；`check_own_skill_frontmatter.py` 查 name 等于目录名；`shared_lints.sh` 与 12 个 `run.sh`；`tests/lints/`；`install.sh --check` 列 watch 与持锁进程；根 `AGENTS.md` A1–A4；`CODING_STANDARDS.md` 两条；`TESTING.md` 两句；`tests/AGENTS.md`；`how-it-works.md` 第 81 行；词条 **role pointer**、**wake**、`RESUME:`、**shared lints**；ADR 0032。只跑 `dispatch`、`relay`、`liveness`、`verify-ticket`、`lints` 五个套件，外加 `shared_lints.sh` | 没有 watch 开着，没有持锁的 relay、watchdog 进程 | 无（技能列表与软链目标都不变，推断） |
| 2 分叉 | 四个技能搬到 `self/`，上游恢复原文，删四份 `openai.yaml`；SSR、RSS 搬到 `docs/skill-set/`，`writing-for-agents/SKILL.md` 第 8 行回原文（K-38）；约 135 处路径；`merge-notes/README.md` 的 `## 分叉的技能`、推导规则、`## 旁加的文件`（5 个文件，K-50）；各 merge-note 去重与改正；两份上游文档页与 README 两行回原文；删 B7 的两处 description 短语与 `ui-acceptance` 表第 1 行；`spec-reviewer.md` 半句；新建 `design-pages/references/state-list-format.md`，`UI.md` 第 6 步留一句指针，改 `design-pages` 两处引用（K-14）；`triage` route 句移进 `pipeline-issues.md`；`mmw:map`（X-11 通过后）；`check_wiring.py` 第 3 类；SSR 的 a–f 表、分叉规则（把分叉技能划出 upstream skill 的定义）、推导规则；词条 **fork** 等三条；ADR 0033；实测 T6。**发布顺序（K-45）**：移动已安装 checkout 与跑 `install.sh` 在同一次操作里连着做，中间不开任何会话；`install.sh --check` 通过之前不开夜 | 第 1 批后跑过一夜 | 授权一次 `install.sh`，与移动 checkout 连着做（软链目标变了）；U-5 先定 |
| 3 新建 `mmw` | `mmw/SKILL.md`、`idea-to-tickets.md`、两条原则、`phase-boundaries.md`；残留 `ask-matt` 恢复原文，写 `merge-notes/ask-matt.md`，改 `merge-notes/triage.md`、`wayfinder.md` 的出处；5 处括注；`check_wiring.py` 第 5 类；SSR `## Layers of the set`（含 `### Principles`）与事实 6、7、`### Descriptions`、`### Hand-offs`、`### Prompts written for other agents`、`### Paths and host neutrality`、`## Verifying`；RSS；词条 `mmw`、**playbook**、**principle** 与 `CONTEXT-MAP.md`；`CODING_STANDARDS.md` 列举；`manage-agents-md` 一句半；`dispatch.sh check` 缺行警告；ADR 0034；发布并装好之后再给各仓库加 `AGENTS.md` 那一行（R4 K6）；发布后跑 T2、T4、T8 | 第 2 批后跑过一夜；**发布前在隔离 home 里用开发版 `mmw` 跑通 T1（X-1，含 X-10、X-29）**，不过就改走宿主钩子注入或不建 mode（K-39） | 授权一次 `install.sh`（新技能）；U-4 |
| 4 删「下一步」句 | `grill-with-docs` 末句；`wayfinder` 第 6 步后半句与 `write-screen-contract` `## Next` 从句（同一次提交）；`triage` 第 5 步拆分与 `to-spec` 第 4 步关 issue 句（同一次提交）；`triage` `## Quick state override`；`pipeline-issues.md` 第 5 行；`improve-codebase-architecture` `### 4`；`prototype` `UI.md` `## Next`；merge-note 条目；词条 **"Hand the decision on"** | 第 3 批已发布（T1 已在第 3 批前通过） | 确认可见变化（U-9） |

---

## 9. 待用户决定的产品问题

只列会改变你看到的东西、你怎么用这套工具、范围，或你自己定的规则的事。其余都是工程决定，已在第 5 节做出。

| # | 决定 | 背景与后果 | 建议 |
|---|---|---|---|
| U-1 | 是否从 pstack 引入任何原则、能力技能或 playbook | R11 逐条看了 23 条原则：16 条在 MMW 已有位置得当的家，7 条没有运行时调用方。pstack 的 playbook 以开 PR 收尾，要先定它对应 `idea-to-tickets` **Who checks** 的哪条路线 | 现在不引入，只把引入的方式写进 SSR（进门检查、七道门槛） |
| U-2 | Memory `fe94802d`「不改上游 frontmatter」怎么读 | 本方案只为可达性去掉开关，从不关掉；今天已这样处理了六个技能，推导后仍是 `triage`、`wayfinder`、`to-questionnaire` 三个上游技能被翻成模型可触发 | 读作「允许去掉，不许为强制层级而加上」 |
| U-3 | 分叉后不改名，就不能再同时装上游原版的 `implement`、`code-review`、`to-spec`、`to-tickets` | 今天装的已经是 MMW 版，所以你看不到变化；只有想在 MMW 之外用上游的通用 `code-review`（「review since X」）时才受影响 | 现在不装原版；以后要用，就得给分叉版改名 |
| U-4 | `mmw` 在有人在场、且不在票工作树里的会话中，是否自动往你各个仓库的 `AGENTS.md` 加那一行 | 它会改动你所有接 MMW 的仓库里的 agent 指令文件；不自动加的话，只有开夜前 `dispatch.sh check` 提醒，由你来加 | 自动加，由 `dispatch.sh check` 的提醒兜底 |
| U-5 | 两条规则冲突：你写的「`install.sh` 只在你明确授权时跑」（根 `AGENTS.md` 第 64 行），与 `dispatch.sh check` 在装得不齐时自动跑完整 `install.sh`（第 2344–2360 行，M7 已核实） | 第 2、3 批改了软链目标，发布后的第一次开夜就会触发自动重装；它重装的是已安装 checkout 自己的版本，不会换版本。选「只报告不修」的后果：按 `dispatch.sh` 原文「an incomplete install does not stop the night」，夜照常开；第 2 批的提升之后若没有按 K-45 连着跑 `install.sh`，这一夜的 worker、reviewer 读到的是上游原版技能（`implement` 没有 `## Closing steps`、带 `disable-model-invocation: true`，`code-review` 是两轴审查、没有 `references/session.md`，M15），交付的票不会按 MMW 的判据与审查收尾 | 保留自动修复，把这个例外写进那条 Gotcha。如果你要坚持必须授权，就改 `dispatch.sh check`，让它只报告不修，并让它在技能软链与 `skills.txt` 不符时拒绝开夜，而不只是警告 |
| U-6 | 没有 wayfinder map 的界面工作，从原型、在 Claude Design 里画页、pull、写 screen contract 到写 spec，是否仍要在同一个会话里、你全程在场完成 | 这是残留 `ask-matt` 第 2 步的规定，理由是这时 screen contract 引用的决定只存在于这场对话里；但画页可能要几个小时，期间会话要一直开着 | 保留，只允许一个例外：宿主没有 Claude Design 工具时用 `/handoff` 换宿主。如果你想中途关掉会话，就要先定一个在中断前写下决定的地方（例如一份 spec 草稿），这会改 **Spec** 一步 |
| U-7 | 你的规则 11「When a step fails or is interrupted, redo it yourself before replying」在无人值守的流水线会话里怎么读 | 原则 `rerun-dont-reroute` 的 `**Boundaries:**` 读作：重做的是你自己被打断的一步；流水线自身的故障经提示词前言「what it reports goes in the formats its skills give」，以 `fault` 子票上报并停下。与你 2026-09-10 否决重试和换 host 的决定（ADR 0018）一致；`shared.md` 一字不改 | 按这个读法写。若你希望规则 11 自己写明这个例外，那是改你的全局提示词，由你决定 |
| U-8 | Memory `ce037679` 要的「一张与实际同步的总图」是指给 agent 的路由，还是给人看的图 | 本方案按给 agent 的路由加 lint 落实；本文第 3 节是一份一次性的人读连线表，不会自动同步 | 需要人看的图，就另做一个页面，由 `check_wiring.py` 的同一份数据生成 |
| U-9 | 确认第 4 批的可见变化 | 直接斜杠进入 `/grill-with-docs`、`/prototype`（UI 分支）、`/wayfinder`（清图时）、`/improve-codebase-architecture`、`/triage`（判为 agent-ready 时）时，结尾不再点名 MMW 的下一步。`mmw` 在上下文里时由它给出下一步；不在时会话停在这里。`/to-spec`、`/to-tickets` 不受影响：它们的后继句保留（K-7）。外来 issue 的关闭从 triage 会话挪到发布 spec 的会话，tracker 上看到的评论不变 | T1 已在第 3 批之前通过（K-39），第 4 批只需你确认这些变化 |
| U-10 | 第 2、3 批各授权跑一次 `install.sh` | 软链目标变了，或多了新技能。第 3 批不跑只是 `mmw` 不生效；第 2 批不跑则宿主读到上游原版技能（K-45、M15），所以第 2 批的授权要与移动已安装 checkout 连着执行 | 按批次表授权；与 U-5 一起定 |
| U-11 | （本次重构之外，顺路发现）`~/agentflow` 的 `hedgehog`、`parrot` 与 `~/xiaohuangya` 的 `duck` 三份 release manifest 仍带着已删的四个字段 | 按 `downstream-notes/release-self-heal-removed.md`，下一次出包时 `init` 会以多余字段为由拒绝（推断，未运行）；删字段是一次普通提交，可以撤回 | 定一个时间在那两个仓库执行这份 downstream-note |

---

## 10. 未确定事项与需要的实测

实测都在隔离的测试 home 里做，装开发版技能，不碰已安装的 checkout。

| # | 问题 | 需要的实测或阅读 | 定下什么 | 出处 |
|---|---|---|---|---|
| X-1 | `AGENTS.md` 里的一行能否让五个宿主在任务开头加载 `mmw`，以及脚本启动的会话会不会误加载它（T1） | 在隔离 home 里装开发版技能，临时消费仓库带这一行（Claude Code 上经 `CLAUDE.md` 的「@AGENTS.md」读到，M26）。五个宿主各一个新会话，给 R4 T1 的六个提示，外加「出包」「跑一下 #N 的验收」「triage 判为可做之后」三个提示；再用真实的 `Use the implement skill to work ticket #N. …` 与 `Use the code-review skill to review ticket #N from base commit …` 提示词各起一次会话。从 transcript 看打开了哪些文件、脚本会话是否打开了 `mmw`、它的首个动作是什么、worker 的常驻读量多了多少 | 第 3 批发不发（K-39）；不过就试宿主钩子注入，或不建 mode；脚本会话误加载时 `## Where you are` (a) 的措辞 | R4 T1、R9 U-R9-1、R6 U4、R7 T8 |
| X-2 | 被压缩后，只凭「唤醒 + 指针」与 `RESUME:` 能否回到正确的小节（T2） | 假 runner 开一夜，压缩 orchestrator 后投 `#3 ticket.passed · <指针>` | 指针措辞 | R4 T2、R5 X2 |
| X-3 | worker 会不会把指针当成新指令（T3） | 假 runner 投递；真实 worker 上跑一次 `resume` | 指针措辞 | R4 T3 |
| X-4 | 没加载过 `mmw` 的会话能否按「技能名 + 路径」打开原则文件、`to-spec` 等（T4） | 照 `idea-to-tickets` 走到 **Spec**；worker 遇到一条带括注的规则 | 推导规则与括注写法是否够用 | R4 T4、R11 §8 #2 |
| X-5 | lint 每一类都能失败（T5） | `tests/lints/` 的反例 | — | R4 T5 |
| X-6 | 分叉并恢复原文后，`git subtree pull` 能否零冲突（T6） | 在丢弃分支上拉一次 | 第 2 批完成 | R4 T6 |
| X-7 | `mmw/` 下没有仓库路径、没有爬出技能目录的相对路径（T7） | 扩大现有 grep；发布后跑 `--check` | — | R4 T7 |
| X-8 | 三种 runner 的 `send` 能否整行送达带 ` · ` 的指针（长度、特殊字符） | 读 `runners/{paseo,orca,herdr}.sh` 的 `send`；假 runner 加一次真实 Orca 投递 | K-1 的分隔符 | R5 X1、N11 unread 8 |
| X-9 | 新文件的实际效果与 `mmw` 的篇幅（T8）；`idea-to-tickets` 的 `## Where you are` 能否只凭 tracker 判出「agent-ready」 | SSR `## Verifying` 走查：任务板的小想法、wayfinder 清图、triage 判可做三个场景，外加一个在 **Grill** 与 **Spec** 之间被宿主自动压缩的场景（K-49）；量 `mmw` 行数 | 100 行上限；`## Where you are` 措辞；**Spec** 的压缩规则够不够 | R4 T8、R7 T8 |
| X-10 | Cursor、Grok、Pi 读不读仓库根的 `AGENTS.md`（T10） | X-1 的前置检查 | U-4 那一行在这三个宿主上有没有用 | R4 T10、R10 U-S6 |
| X-11 | `wayfinder` 去掉 `mmw:map` 后，画图的 agent 会不会照 tracker 文档打上这个 label | 假 tracker 上跑一次 `/wayfinder` 画图 | K-34：不过就保留 `mmw:map` | R7 T-D2 |
| X-12 | description 之间是否抢同一个请求：`mmw` 与 `grilling`、`wayfinder`、`to-spec`、`dispatch`、`design-pages`；`verify-ticket` 的 description 首句（T11） | 按 SSR `### Descriptions` 第 2 条并排读，再用 X-1 的会话验证 | `verify-ticket` 首句改不改（K-6） | R4 T11、R6 U4、R8 X4 |
| X-13 | 原则文件是否真的改变 agent 的决定（T13） | 第 3 批后走查：给新 worker 一张开工前就绿的判据的票，给新 orchestrator 一条 `advance` exit 4；看是否打开原则文件、选择是否不同。另给白天重入一个场景：会话记忆与 tracker 不一致时，`idea-to-tickets` 按哪一边走 | 原则层增减；`the-tracker-is-the-state` 建不建（K-41；不建就并回 `dispatch/SKILL.md` 第 8 行）；`check_wiring.py` 第 4 类加不加（K-44） | R4 T13、R11 §8 #1 |
| X-14 | advisor 在 `issue-<n>` 里是否真会调用宿主的提问工具；它的启动提示词不带 `AUTONOMOUS`，在非票工作树里提问时有没有人答 | `tests/dispatch` 加一个场景；隔离 home 里起一次 advisor 并给一个缺信息的 brief | K-5 的 advisor 一条是否必要；要不要给 `advise_one` 加 `AUTONOMOUS` | R6 U1、U2 |
| X-15 | `NO_QUESTION` 的三角色短写法只按长度核过，Grok 实际截断位置没有实测 | 在 Grok 上触发一次提问钩子 | K-5 的措辞 | M2 |
| X-16 | `status.py` 读 spec 自己的评论要多一次 `gh` 请求，耗时是否可以接受；测试里对表格首行有多少断言 | 实现时量一次；grep `test_status.py`、`test_dispatch.sh` | K-3 的实现方式 | R5 X4 |
| X-17 | retro 中途被压缩，`RESUME:` 会把 orchestrator 送回 `5.` 重跑；重跑 `retro.py finalize` 会不会重复开 issue、重复写 Memory | 读 `retro.py` 的 `finalize` | 是否要在 `5.` 加一句 | R5 X6 |
| X-18 | 没有唤醒时读到 `RESUME: 3. …`（例如用户中途问进度），orchestrator 会跑一次 `advance`，推断无害 | `tests/dispatch` 加场景 | — | R5 X7 |
| X-19 | 夜外 `adopt` 的 `child.opened`、`ticket.refused` 是否真的发生过；adopt 的会话是否总有人在场 | `gh search` 查含 `adopted` 的 `worker.started`；读一次 adopt 会话记录 | R5 D1 那一句的措辞 | R5 X3 |
| X-20 | `resume_at` 的全部取值组合 | 读 `events.fold` 的 `apply()` 全文，补 `test_preflight.py` | 步骤名映射完整 | R6 U6 |
| X-21 | 删掉 `agents/openai.yaml` 后 Codex 技能列表的显示名会不会变（推断只影响显示） | Codex 会话里看一次技能列表：显示名是否从 `display_name`（如「Implement」）变成技能名 | K-20 | R6 U5、R7 |
| X-22 | `to-tickets` 第 8 步的「再跑一次 `--lint`」是否与 `--publish --drafts` 内部的 lint 重复 | 读 `run_publish_drafts` 全文 | 能删就作为普通票删 | R7 U-B |
| X-23 | `to-spec` 遇到有界面、却没有 `screen-contract.yaml` 的 effort 时怎么做 | 读 `to-spec` 全文，或拿一个无合同的测试 effort 走一遍 | `## Where you are` 的两行界面重入点是否足够 | R8 X3 |
| X-24 | 五个宿主里哪些有 Claude Design MCP 工具（本轮只在 Claude Code 上看到） | 各宿主会话里列工具 | U-6 的例外多常发生 | R8 X1 |
| X-25 | 测试是否还钉住别的会被改的句子；lint 的模式扫描能否覆盖所有脚本指向技能文本的字面写法（例如 `design_render.py` 第 92 行「run write-screen-contract」）；启动提示词里的技能名要不要先放进 `anchors.py` | 实现前 grep `mmw-v2/tests/` 与 `mmw-v2/skills/*/scripts/`；每类配反例 | lint 第 1、3 类的实现方式 | N11 unread 6、R8 X5、R10 U-S4 |
| X-26 | 「能并行的两张票不写同一个文件」能否由 `verify-ticket.py <spec> --lint` 精确检查 | 读 `--lint` 实现，看它拿不拿得到整批的 `## Owns` 与阻塞边 | 能的话开一张普通票 | R11 §8 #3 |
| X-27 | `diagram-design` 超出 40,000 字节后，上游 `verify-semantic-motion.py` 会不会失败 | 临时检出里跑一次 | 随 F5 票 | R9 U-R9-5 |
| X-28 | SSR 加约 40 行后，写能力技能的人多读的内容值不值得按分支拆出去 | X-9 走查时量 SSR 被读多少、用了多少 | 「减少读量」不在用户要求 2 的收益清单里，现在不拆 | R9 U-R9-4 |
| X-29 | 宿主是否只把 `SKILL.md` 当技能，不会把 `playbooks/`、`principles/` 下的文件扫进技能列表 | X-1 装好后在五个宿主上各看一次列表 | — | R10 U-S1 |
| X-30 | `manage-agents-md` 改文字之后，重写时是否真的保留 `mmw` 行 | 临时仓库里重写一次 | K-26 | R10 U-S2 |
| X-31 | relay 队列行存的是事件名还是渲染好的文字；一次提升前后留下的旧行会不会以旧格式送出 | 读 `relay.py` 的 `queue`、`ack_wake` 行格式 | 是否需要迁移（推断不需要） | R10 U-S3 |
| X-32 | `anchors.py` 的全部载入者清单；各处标「推断」的行数 | 模块写成后按实际 import 填 `TESTING.md` 那一条；实现后量 | 8.1 的数字 | R10 U-S5、U-S7 |
| X-33 | 你 2026-09-06 的判据「不要修修补补，要最根本的最优解」在现行规则里没有对应句；`refusal.py` 头注释「三个 worker 各自发明三种应对」本轮没重读 | 前者要问你这条判据是否仍然有效，候选的家是 SSR `## Editing`；后者写原则 `**Why:**` 前回到原文 | — | R11 §8 #4、#6 |
| X-34 | 被 `resume` 叫醒、还没有自己运行记录的 worker，按新指针能否回到写代码 | 假 runner 给一个刚认领、还在写代码的 worker 发 `resume` 加指针（`contract` 子票改正后的 continue 与 watchdog idle 两种）；看 `--preflight` 印的 `RESUME:` 与 worker 的下一步 | K-47 的指针与第 74 行补句 | 审查、M17 |
| X-35 | `watchdog.py` 八种告警各自该写什么下一步（例如 `relay down` 是否就是重新 `open`，`events unreadable` 是否等 tracker 恢复后重读） | 读 `watchdog.py` 全文与 `relay.py` 的恢复逻辑；每种告警在 `tests/dispatch` 或 `tests/liveness` 里配一个场景 | K-46 的告警文字 | M16 |

---

## 11. 本总图自身的形式拆散自查（L7 C.6 十一个信号）

| # | 信号 | 结果 |
|---|---|---|
| 1 | 新建前没确认已有组件不是归宿 | 未触发。8 个新文件各自排除过已有的家：`mmw`、`idea-to-tickets`、两条原则、`phase-boundaries.md` 的内容今天没有已安装的家；`anchors.py` 取代了三份报告各自想放的位置；`state-list-format.md` 放进已有的 `design-pages`，排除了上游 `UI.md`（M13：那段本来就是 MMW 加的）与上游目录旁的新文件（K-14）；`check_wiring.py`、`shared_lints.sh`、`tests/lints/` 各有一个已核实的断点或重复作为依据。SSR、RSS 不是新建，是搬到已有的仓库文档层（K-38）。新组件都要先能被到达：`mmw` 与 playbook 以 T1 在第 3 批发布前通过为前提（K-39） |
| 2 | 新增内容不改变决定 | 有风险，已收窄。原则括注从各单元提出的 26 处（有重叠）收到 5 处，规则是每个调用方文件对每条原则只加一处、只加在本地没写理由的句子上（K-9）；是否真的改变决定待 X-13；`**Leaves:**` 与 `night.md` 的 `Done when` 都不加（K-21、K-29） |
| 3 | 重复已有的、位置得当的指引 | 未触发，反向删了几处：`night.md` 事实表里的事件判定、`watchdog.py` idle 文字、merge-note 的开关复述、`run.sh` 的三行、`ask-matt` 的 `## Standalone`、R4 草案的 `exe-release` 与 `dispatch` 路由行（K-16）；`mmw` `## Where you are` 不处理唤醒行（K-42）；`## Principles` 索引行不写规则句（K-27）；`mmw` 不设 `## Head judgement`（K-40）；playbook 的 **Spec**、**Tickets** 不复述 `to-spec`、`to-tickets` 的后继（K-7） |
| 4 | 本可由机制强制的规则写成了文字 | 部分触发，用同一条标准处理（SSR `## Editing`：加机制要有已核实的断点或失败）：SSR `### Paths and host neutrality` 仍是人工 grep，`check_wiring.py` 第 4 类暂缓（K-44），两者都没有失败过的运行。反向：锚点、`WAKES` 与告警的处理行、调用开关、登记表、同名、开着的 watch 与持锁进程都交给了 lint 或 `--check`；`the-tracker-is-the-state` 的后半句已由机制强制，所以该原则暂缓（K-41） |
| 5 | playbook 只调一个技能 | 未触发：只有一份头部 playbook，点名十一个技能 |
| 6 | reference 每次都读、只有一个调用方 | 未触发：`phase-boundaries.md` 只在边界读，有两个调用方；`state-list-format.md` 有三个读者（`prototype` 写、`design-pages` 读并为已有产品写、lint 核对 `pull_design.py` 的字面） |
| 7 | 原则说不出改变哪个决定，或只适用一步 | `the-tracker-is-the-state` 有风险，已暂缓（K-41）：前半句是 `dispatch/SKILL.md` 第 8 行原话，后半句已由机制强制，能改变的主要只有白天重入，待 X-13。另两条未触发：`silence-is-never-a-pass` 跨 playbook 步骤、worker 与 orchestrator 操作文件三种机制，`rerun-dont-reroute` 跨 worker 与 orchestrator 操作文件两种机制；只适用一步的规则留在原处（R11 §3.3） |
| 8 | 拆完需要按步骤编号引用 | 未触发，反向：`RESUME:`、`design-pages` 第 25 行、`writing-interface-code.md` 三处「closing step 1」由按编号改为按名（K-43）；playbook 按原文小节「**3. Do you need to hand off?**」点名 `phase-boundaries.md` |
| 9 | 拆出的内容没有第二个调用方、也不减少重复 | 未触发：`anchors.py` 有七个读者；`state-list-format.md` 合掉一处重复；分叉是整体搬家，不拆内容；Head judgement 只有一个家、三个入口（K-40） |
| 10 | 把单入口的固定流程拆成三层 | 未触发：五个角色操作文件都保持一个文件；`exe-release`、`dispatch` 连路由行都不加 |
| 11 | 把只在流程之间复用的内容做成能力技能 | 未触发：playbook、原则、reference 都不是技能；唯一的新技能是 mode |

---

## 12. 本轮读了什么

- **任务附带、全文读过**：R4 与 R5–R11。
- **全文读过**：
  - `N11-mmw-gaps.json`；
  - N1–N10 的第 1 节部件清单（N1 §1、N2 §1、N3 §1、N4 §1、N5 §1 与 §5.1、N6 §1、N7 §1、N8 §1、N9 §1、N10 §1）；
  - N1–N10 的全部标题。
- **回到原文核实**（第 1 节 M1–M11）：
  - `watchdog.py` 第 808–818 行；
  - `tool-guard.py` 第 49–82 行；
  - `tests/dispatch/test_tool_guard.py` 第 35、450 行；
  - `relay.py` 第 231–264 行；
  - `design-pages/SKILL.md` 第 25 行、`design-system.md` 第 42 行；
  - `retro/SKILL.md` 第 180–190 行；
  - `triage/SKILL.md` 第 82 行、`wayfinder/SKILL.md` 第 126 行、`write-screen-contract/SKILL.md` 第 115 行；
  - `dispatch.sh` 第 2344–2362 行、根 `AGENTS.md` 第 64 行；
  - SSR 第 17、70、81 行；
  - `implement/SKILL.md` 第 23 行、`advising.md` 第 18 行、`session.md` 第 45 行；
  - `skills.txt` 与 7 个用户触发技能的 frontmatter；
  - 上游 subtree 相对 squash `5b1a4c51` 的 diff 统计与新增文件清单。
- **审查时回到原文核实**（第 1 节 M12–M30）：
  - `writing-for-agents` 目录相对 squash 的 diff，SSR 在 `docs/contexts/`、merge-notes、两个 lint 文件头、根 `AGENTS.md` 的引用计数；`retro/SKILL.md` 第 135–146、195–200 行；
  - squash 的 `prototype/UI.md`、`to-spec`、`to-tickets`、`implement`、`code-review` 的 `SKILL.md` 与 `implement/agents/openai.yaml`；现行四份 `agents/openai.yaml`；
  - `install.sh` 第 175–190 行、`dispatch.sh` 第 100–112、2335–2362 行；
  - `watchdog.py` 第 75–112、735–760 行，`relay.py` 第 196–210、285–302 行与 `QUEUED`、`RECOVERED` 的定义处；
  - `verify-ticket.py` 第 2148–2162 行；`implement/SKILL.md` 全部标题与第 20–24、70–76 行；`writing-interface-code.md` 第 35–41 行；
  - `night.md` 第 1–110、175–190 行；`one-ticket.md` 全文；`dispatch/SKILL.md` 第 1–30 行；`to-tickets/SKILL.md` 第 84、153–160 行；`to-spec/SKILL.md` 第 125–127 行；
  - `pull_design.py` 第 975–990 行、`pull.md` 第 20–24 行、`board_data.py` 第 20–30 行、`codeversion.py` 第 15–26 行、`advising.md` 第 15–20 行、`ui-acceptance/scripts/` 文件清单；
  - 残留 `ask-matt/SKILL.md` 第 15–32 行、`PHASE-BOUNDARIES.md` 全文；
  - `mmw-v2/tests/` 对 `AUTONOMOUS`、`PRODUCT_RULES` 文字的 grep，`test_dispatch.sh` 第 2830、6984、7199 行，`TESTING.md` `## What a test proves`；
  - `~/agentflow/CLAUDE.md`、`~/xiaohuangya/CLAUDE.md`；
  - L7 第 0 节与 A.0–A.5（第 30–300 行）、C.6（第 682–701 行）、D 节（第 703–793 行）原文；R4 D4.3 门槛、R8 第 110–116、150–158、374–380 行、R9 第 126、140–150 行、R10 第 111、128 行、R11 第 56–70 行、R7 第 36、49、180–186 行、N10 第 258–262 行。
- **没有读**：
  - L7 的 A.6–A.11、B、C.1–C.5、E、F 节（这些节只经 R4 与各报告的引用使用；K-3、K-29 注明了与 D.1、D.2 的对应，K-27 注明了与 A.1 索引格式的差异）；
  - 各报告自己列为未读的部分：runner 适配器实现、`retro.py`、`events.fold`、`run_publish_drafts`、`status.py` 的函数体、board 前端；
  - N11 unread_parts 第 2、3、4、7、10 项的原文。
- **依赖未读部分的结论**：已标为推断，或列入第 10 节。

**本总图的使用方式**：按第 8.2 节逐批开票。每张票的 `## Read first` 点名本文对应的节、裁定号（K-*）与所引归置报告的行号（如 R5 B2），票的判据按 R4 D3.6 与本文第 3 节的连线写。本文第 3.5 节的连线表是一次性的人读快照，不会随实现自动同步（U-8）。

---

## 审查记录

审查对上一版总图提出 34 条问题。逐条回到原文核实（第 1 节 M12–M30 为本次核实），处理如下。

| # | 问题 | 处理 | 理由 |
|---|---|---|---|
| 1 | SSR、RSS 留在上游 `writing-for-agents` 目录，还要再加约 40 行 | **采纳** | 已核实（M12）：两份全是本仓加的（+209 行），`SKILL.md` 第 8 行为指向它们改过；上一版连线里 SSR 已依赖 `mmw`，R9 不搬的理由在总图内部不成立。改为第 2 批搬到 `docs/skill-set/`、第 8 行回原文（K-38），第 5 节比较了成本（约 50 处路径）与另一个候选 `mmw/references/`。一处细节不属实：`retro` 第 11 步点名的是 `writing-for-agents` 的 `SKILL.md`，不是 SSR，所以它不需要改为点名新位置 |
| 2 | 新建 `prototype/state-list-format.md` 的「上游回原文」收益不实 | **采纳** | 已核实（M13）：squash 的第 6 步没有 state list，整段是本仓加的。格式放进 `design-pages/references/state-list-format.md`，`UI.md` 第 6 步只留一句指针（K-14）；第 2.3、4.5、4.6、11 节随之改 |
| 3 | 分叉后 `to-spec` `## Next`、`to-tickets` 第 8 步末句不该换成固定返回句 | **采纳** | 已核实（M14）：squash 里两处都没有，分叉后是自有文本；与 K-7 保留 `retro` 第 186 行、保留 `write-screen-contract` `## Next` 用同一标准。两处保留，playbook 的 **Spec**、**Tickets** 只写门槛与重入，SSR 不再写固定返回句，U-9 缩小（K-7） |
| 4 | 第 3 批先建 `mmw`，T1 只作第 4 批的前提 | **采纳** | T1（含 X-10、X-29）改为第 3 批发布的前提，在隔离 home 里用开发版技能做；不过就走宿主钩子注入或不建 mode（K-39） |
| 5 | `mmw` `## Head judgement` 与 playbook **Who checks** 重复判断 | **采纳，选第一种** | 已核实（M29）：它在残留 `ask-matt` 里是第 3 步的分支。判断原文放进 **Who checks**，`mmw` 不设这一节；另把 Routes 第 4 行（排错后的修法）与第 5 行接到 **Who checks**，使它有三个入口（K-40） |
| 6 | `to-tickets` 第 84 行、`dispatch/SKILL.md` 第 25 行本地已写理由，不该加括注 | **采纳** | 已核实（M25）。两处删去；与第 13 条合起来，括注从 11 处减为 5 处（K-9）。审查说「rerun 仍有三处调用方」：实际括注剩 `night.md` 第 82 行与 `implement` 第 18 行两处，加上 `mmw` 索引；两处属不同机制，门槛 5 仍满足 |
| 7 | `## Principles` 索引行再写一句规则是第二份 | **采纳** | 索引行只写 Title、slug 与何时适用（K-27）。补读 L7 A.1 发现 pstack 的索引行带「一句要点」，K-27 写明有意偏离的理由 |
| 8 | `mmw` `## Where you are` (b) 处理唤醒行是重复 | **采纳** | 已核实：`night.md` 事实表第 3 行、`one-ticket.md` 第 3 步已处理这四种行，turn guard 文字自带步骤。删去，T2 测到失败再加回（K-42） |
| 9 | Routes 第 6 行只是 `dispatch` description 的复述 | **采纳** | 已核实 `dispatch/SKILL.md` 第 3 行；开夜前的 `--lint` 由 `night.md` 1b 自己要求，不是这一行的门槛。删去，交给兜底句（K-16） |
| 10 | 残留的按编号跨文件引用 | **采纳** | 已核实（M30、M28）。三处「closing step 1」第 1 批改为 **Integrate and run**；playbook 按原文小节「**3. Do you need to hand off?**」点名（K-43） |
| 11 | `check_wiring.py` 第 4 类与第 11 节信号 4 的标准不一 | **采纳，选暂缓** | 两处统一用 SSR `## Editing` 的标准；第 4 类暂缓到 X-13 之后，第 5 类有 `ask-matt` 漂移为依据，保留（K-44） |
| 12 | `merge-notes/diagram-design.md` 标类别说不出收益 | **采纳** | 改为不动，写进第 6 节不动清单 |
| 13 | 原则 `the-tracker-is-the-state` 的信号 7、4 风险被低估 | **采纳** | 已核实（M25）：前半句是 `dispatch/SKILL.md` 第 8 行原话。第 3 批只建两条原则，这一条待 X-13；`idea-to-tickets` `## Where you are` 本地写一句（K-41）；第 11 节信号 7 改为「有风险，已暂缓」 |
| 14 | 第 0 节第 1 条说五个角色操作文件全部原位 | **采纳** | 改为「不并入、不拆分、不改名；`implement` 与 `session.md` 随分叉整目录搬家，其余三份原位」；第 6 节同一行一并改 |
| 15 | 第 2 批发布顺序会让宿主读到上游原版技能 | **采纳** | 已核实（M15）：squash 版带 `disable-model-invocation: true`，`code-review` 没有 `session.md`，`--check` 只比对 `readlink`，`dispatch.sh` 装不齐不拦夜。移动 checkout 与 `install.sh` 连着做、`--check` 通过前不开夜（K-45）；U-5、U-10 补上后果 |
| 16 | watchdog 八种告警只有一种有处理行；lint 第 2 类覆盖不到；adopt 会话收到让自己 `resume` 自己的告警 | **采纳，选告警文字自带下一步** | 已核实（M16）。每种告警在自己的文字里写下一步再接指针，`night.md` `## 3` 加一行兜底；lint 第 2 类输入扩到告警前缀、`worker.queued`、`relay.recovered` 与 `child.opened` 的 kind；`by=adopt` 不附 `resume` 命令（K-46）。每种告警的具体下一步列为 X-35 |
| 17 | worker 指针把还在写代码的 worker 送进 `## Closing steps` | **采纳** | 已核实（M17）：`resume_at` 在没有运行记录时返回 `None`。指针改为跑 `--preflight` 照 `RESUME:` 做，新增取值「Claim, read in, write the code」，`implement` 第 74 行补一句（K-47）；X-34 实测 |
| 18 | `RESUME:` 在首次 `advance` 前会跳过 1b；`5.` 丢了段落限定 | **采纳** | 已核实（M18）：`dispatch.sh` 不跑 `--lint`。加「1b. Before the batch」取值，恢复 `5.` 的段落限定（K-48）；R5 J1 同步标注 |
| 19 | 第 3.3 节对 N11 missing_edges 的声称不实；几条边写错 | **采纳** | 已核实（M21）。补 `pull.md` 拆 scaffolding 的边与 `retro` 的 reviewer-rule 提案边；`pull_design.py` 那条改指 `artifact:prototype leaf README`；补 `adr:0033`；`user` 改为 `role:user`；第 3.3 节按 0 起编号逐条写明处理 |
| 20 | 第 0 节第 1 条与第 2 条矛盾 | **采纳** | 同第 14 条 |
| 21 | X-1 没有测脚本启动的会话 | **采纳** | 已核实（M26）：消费仓库的 `CLAUDE.md` 是「@AGENTS.md」。X-1 加两个脚本会话场景 |
| 22 | **Spec** 门槛与 `## Where you are` 在宿主自动压缩后的重入 | **部分采纳** | 加自动压缩规则：先与用户逐条确认摘要里带着、`CONTEXT.md` 与 ADR 里没有的决定；「对话里已有定下的决定」改为「用户本条消息带来已定下的决定」；X-9 加场景（K-49）。不采用「先写进 spec 草稿或 tracker」：那会给决定一个新的存放处，要另定格式与读者，而这个 playbook 由人启动，用户在场，确认的成本低 |
| 23 | Self-hosting boundary 的可见检查不查活着的 relay、watchdog | **采纳** | 已核实（M27）。`--check` 同时列出 `relay.lock`、`watchdog.lock` 指向的活进程，提升第三步要求两者都不存在（K-32） |
| 24 | K-2 对界面链脚本与 `verify-ticket.py` 用了不同标准 | **采纳，选第二种** | `resume_at` 也把步骤名写成字面、由 lint 模式扫描核对，`anchors.py` 只由 `dispatch/scripts/` 里的脚本导入（K-2）；另可避免 `verify-ticket` 与 `dispatch` 互相依赖 |
| 25 | K-20 的「消冲突」是误读 | **采纳** | 已核实（M20）：SSR 第 106 行把「adapted from」上游的技能也算作 upstream skill。收益改为去重复，并写明依赖第 2 批 SSR 改写。补充一点审查未提的事实：现行四份 `openai.yaml` 都没有 `policy` 行，所以删文件不影响开关配对规则 |
| 26 | 「三者字面都由测试钉住」不属实 | **采纳** | 已核实（M19）。第 2.6、4.1、4.10、6 节改为「首句由测试核对角色到技能的映射；`PRODUCT_RULES` 引用的标题由 `check_wiring.py` 第 1 类核对」 |
| 27 | 第 0 节第 1 条（同第 14 条） | **采纳** | 同第 14 条 |
| 28 | 第 8.1 节写「B7 的三处短语」 | **采纳** | 改为两处，与 K-6、第 4.10、8.2 节一致 |
| 29 | 第 4.6 节「`ui-acceptance` 11 个脚本」 | **采纳** | 已核实（M24）：9 个 |
| 30 | M6 说它们是 R10 M7 表的内容 | **采纳** | R10 M7 只列了 SSR、RSS 与第 4 批新文件。M6 改写；因 K-38、K-14，`## 旁加的文件` 只列 5 个现有文件，并由 R10 的第 4 批提前到第 2 批（K-50） |
| 31 | K-9「每个调用方文件一处」与所选各处矛盾 | **采纳** | 规则改为「每个调用方文件对每条原则只加一处」；R11 第 56 行同步标注；第 4 类 lint 已暂缓，无需同步 |
| 32 | 第 3.5 节漏了 `board_data.py -> ghlist.py` | **采纳** | 已核实（M22）。补边后连同其他改动重算：484 条、208 个节点；组件类型按第 3.1 节写明的规则重算 |
| 33 | advisor 第 4 条「无人值守时的出路」不是原文 | **采纳** | 已核实（M23）。改为「一般规则；`NO_QUESTION` 送 advisor 到这里是 R6 X3 的推断，由 X-14 实测」 |
| 34 | 没有对照 L7 D 节原文 | **采纳** | 补读 L7 第 0 节、A.0–A.5、C.6、D 节原文。C.6 与第 11 节一致；K-3 注明与 D.2 Session pickup、Pause safely 的对应，K-29 注明与 D.1 todo 抄写的对应，K-27 写明与 A.1 索引格式的差异 |

同步修改的归置报告（只在被改定的行号或段落上标注「已被 R12 K-xx 改定」，正文不重写）：`R5` A4、D1、G1、I1、I2、J1；`R6` V6、I16、I18、C10；`R7` A2、A3、B2、B3、K2；`R8` §0 第 (c) 条、state list 那一行、§8 信号 1；`R9` §1.5.2 位置理由、W7、D16、W-SSR-15；`R10` M7、T2、I2；`R11` 选点规则一段、C2、C5–C9。
