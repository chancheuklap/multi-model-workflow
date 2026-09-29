# R8 界面链（UI chain）逐项归置

本文按 `docs/research/workflow-compare/reports/R4-mmw-architecture-form.md`（下称 R4）把界面链单元逐项归置。准绳是 `docs/research/workflow-compare/reports/L7-pstack-component-contract.md`（下称 L7）第 C 节。清点底稿是 `docs/research/workflow-compare/reports/N6-mmw-ui-chain.md`（下称 N6）；采用 N6 的每条结论前都回到了原文，N11 `thin_claims` 里点名 N6 的一条（`ask-matt` 的边已不存在）已按原文改正。

单元范围：

- `ui-acceptance`、`design-pages`、`write-screen-contract` 三个自有技能的全部文件（`git ls-files` 共 29 个）。
- 交接：`to-tickets` 的 `references/cutting-interface-tickets.md`、`implement` 的 `references/writing-interface-code.md`、`code-review` 的 `references/ui-reviewer.md`、`prototype` 的 `UI.md`。

标注：「已核实」＝本轮读原文或跑只读命令看到的；「推断」＝由原文推出；「未确定」集中在第 10 节。没有改任何仓库文件。

---

## 0. 结论

1. **界面链整体原位不动，不新建界面 playbook。** 三个技能各产出一个能叫出名字的交付物（验收判据的 oracle 与 lease、design package、screen contract），都能脱离 mode 被调用（description、wayfinder 票首行、`contract` child 正文、`to-spec` 回指、`verify-ticket` 的交接），属于 L7 C.3 的能力技能。R4 D3.1、第 15 节已判定「新建界面 playbook」是 L7 C.6 信号 3、9，本轮核实后维持。
2. **真正要动的只有七处**，每处的收益都能指到原文：
   - (a) 三份交接 reference 随所属技能分叉搬进 `mmw-v2/skills/`，内容不改（R4 D5.3 f 类）。
   - (b) `ui-acceptance` 的 description 删「or before writing a page ticket's code」，`## Find your moment` 删第 1 行（R4 D5.2，重复声称，已核实）。
   - (c) `prototype` `UI.md` 第 6 步的 state list 格式段移到上游 `prototype` 目录旁新加的 `state-list.md`（d 类），`UI.md` 第 6 步留一个指针；`design-pages` 两处引用改指它。**这里修正 R4 的一处假设**：R4 D5.3 说 d 类 reference「由 playbook 那一步点名」，但 wayfinder map 上的 prototype 票不经过 `idea-to-tickets`，只点名在 playbook 里会让它们找不到格式，所以指针必须留在 `UI.md` 第 6 步。（已被 R12 K-14 改定：格式文件放进 MMW 自有的 `design-pages/references/state-list-format.md`，`UI.md` 第 6 步只留一句指针，上游目录不新增文件。）
   - (d) `UI.md` `## Next` 删去（c 类），由 `idea-to-tickets` 的 **Runnable questions** 接住（R4 D5.3 已定，第 4 批）。
   - (e) `write-screen-contract` `## Next` 删去「`to-spec` runs once the map is clear, as that skill says」。第 4 批删 `wayfinder` 第 6 步那句之后，这句就指向一句不存在的话（已核实 `wayfinder/SKILL.md` 第 126 行今天说这句），两处必须同一次提交。
   - (f) `idea-to-tickets` 的 `## Where you are` 加两行界面链重入点，**Runnable questions** 加一句换宿主的例外。R4 D3.3 给的行里，「有 prototype 结论、没有 spec → **Who checks**」会把一个已 pull、未写 screen contract 的界面工作直接送进 **Spec**，跳过 `write-screen-contract`，这是按 R4 原样落地会产生的断点。
   - (g) 两处文档改正：`merge-notes/to-tickets.md` 第 93 行指向已删除的 **The criterion** 小节；`docs/contexts/ui-acceptance/CONTEXT.md` 三个判据词条的 `_Home_` 指错文件。
3. **接线 lint 第 1 类的范围要包括界面链脚本印出的锚点**：`PRODUCT_RULES` 点名的 `Five rules while the product is running`、`journey.py`、`story-parity.py`、`target_config.py`、`lint_screen_contract.py` 拒绝文字里的 reference 名，以及 `pull_design.py` 解析的 `## State list` 字面。R4 D3.6 第 1 类列的范围只有 dispatch 一侧。
4. **本单元不产生新原则。** 在 `ui-acceptance` 里给 R4 的三条原则各加一个句末括注，放第 3 批。
5. **待用户决定一件**：没有 wayfinder map 的界面工作，从原型到 screen contract 是否仍必须在同一个会话里完成（第 9 节）。

---

## 1. 本轮核实的事实

| # | 事实 | 出处 | 结果 |
|---|---|---|---|
| U1 | `implement/SKILL.md` 第 16 行末句「When **Read first** lists a screen contract, read `references/writing-interface-code.md`.」与 `ui-acceptance/SKILL.md` 第 3 行 description「or before writing a page ticket's code」、第 18 行表第 1 行认领同一时刻 | 两份原文 | 已核实 |
| U2 | `UI.md` 相对上游 squash `5b1a4c51` 的改动：第 3、16、28、81 行措辞（throwaway → prototype route / stay as reference）；新增 `### When there is no app yet`；第 2 步新增一句（Style with variables…）；第 3 步末新增 scaffolding 段；第 6 步改标题、首句、`## State list` 段、scaffolding 段，删除上游的折进真实代码与 throwaway branch；新增 `## Next` | `git show 5b1a4c51:skills/engineering/prototype/UI.md` 与现文 diff | 已核实。上游 112 行，现 121 行，多数行仍是上游的 |
| U3 | `pull_design.py` 第 983 行用正则 `^## State list` 解析 state list；`tests/design-pages/test_pull_design.py` 第 182、458 行的样例 README 用同一标题 | 两文件 | 已核实 |
| U4 | `design-pages/SKILL.md` 第 25 行按编号跨技能引用「the `prototype` skill's `UI.md` step 6」；SSR 第 81 行：「A heading or step that another skill finds by position is cited … by title rather than by number.」 | 两文件 | 已核实：现存冲突 |
| U5 | `design-system.md` 第 42 行括注「(one `### <region>` per region, one item per state the product shows)」与 `UI.md` 第 108 行的格式句是同一格式的两份写法 | 两文件 | 已核实：部分重复 |
| U6 | `wayfinder/SKILL.md` 第 126 行（第 6 步）：「Stop and tell the user the next move: in a fresh session, run `to-spec` against this map … and then `to-tickets`.」；`write-screen-contract/SKILL.md` 第 115 行：「`to-spec` runs once the map is clear, as that skill says.」 | 两文件 | 已核实：后一句的所指就是前一句，R4 D5.3 第 4 批要删前一句 |
| U7 | `wayfinder/references/interface-and-remake.md` 不在上游 squash 树里（`git show` 报 path does not exist），是本仓加在上游目录里的 reference；它让 design ticket、alignment ticket 在正文首行点名 `design-pages`、`write-screen-contract` | 同文件 | 已核实。wayfinder map 上的 prototype 票由 `prototype` 技能直接做，不经过任何 playbook |
| U8 | `prototype/evidence-page.md` 也不在上游 squash 树里，是本仓在上游 `prototype` 目录旁加的文件 | `git show 5b1a4c51:…/evidence-page.md` 失败 | 已核实：d 类「目录旁新加 reference」在同一目录已有先例 |
| U9 | `ask-matt` 不在 `mmw-v2/skills.txt` 里（grep 为 0）；它第 2 步的界面段（「with no map … they run in a single session with the user present, prototype through contract, before the `to-spec` skill」、「Hand off only for a reason on `PHASE-BOUNDARIES.md`'s question 3, such as a host with the Claude Design tools」）今天没有已安装的家 | `ask-matt/SKILL.md` 第 19–21 行；`PHASE-BOUNDARIES.md` 第 28–33 行 | 已核实。N6 edges 里 `ask-matt -> design-pages`、`ask-matt -> write-screen-contract` 是死边（N11 thin_claims） |
| U10 | `design-pages/SKILL.md` 第 21 行：没有 Claude Design MCP 工具的会话要停下、告诉用户换会话。R4 D3.3 **Spec** 的门槛要求 **Grill** 到 **Tickets** 在同一个没被清空的上下文里 | 两处 | 已核实：两处对「宿主没有工具」互相冲突，R4 没有写例外 |
| U11 | 本会话（Claude Code）的工具列表里有 `mcp__claude-design__*` 一组工具 | 本会话工具清单 | 已核实，只限 Claude Code 这一个宿主；其余四个宿主未查 |
| U12 | `contract` child 由 `verify-ticket.py` 第 1622 行以 `needs-triage` 与 `mmw:child` 标签开出；`triage/references/pipeline-issues.md` 第 5 行处理它；`writing-interface-code.md` 第 49 行让 child 正文带一句点名 `design-pages` 的 `references/pull.md` | 三文件 | 已核实：白天这张 child 经 `mmw` `## Routes` 的 triage 行、再经 child 正文到达 `design-pages`，不需要新路由行 |
| U13 | `merge-notes/to-tickets.md` 第 93 行仍写「各自的 **The criterion** 一节」；`ui-acceptance/references/` 下 grep「The criterion」为 0 | 两处 | 已核实（与 N6 第 5 节一致） |
| U14 | `docs/contexts/ui-acceptance/CONTEXT.md` 第 233 行 **harness guard criterion** 的 `_Home_` 是 `harness-guard.md`，但 `harness-guard.py .` 与 `HARNESS OK` 只在 `cutting-interface-tickets.md` **Criterion shapes**（第 51–58 行）；第 225、229 行的另两条部分成立（两遍规则在 `boundary-check.md` 第 3 行、`--break` 在 `journey.md`），判据写法仍只在 `cutting-interface-tickets.md` | 两文件 | 已核实 |
| U15 | 界面链脚本印出的、指向技能文本的字面：`dispatch.sh` 第 109 行 `PRODUCT_RULES`（'Five rules while the product is running'）；`journey.py` 第 228、235 行（The fault-injection switch in references/journey.md）；`story-parity.py` 第 466、472 行（the write-screen-contract skill's references/screen-contract-format.md，测试 `test_story_parity.py` 第 400、484 行钉住文件名）；`target_config.py` 第 91 行（references/product-answers.md）；`lint_screen_contract.py` 第 139 行 | 各文件 | 已核实 |
| U16 | 分叉会改变路径、但不会断开脚本的兄弟目录查找：引用 `ui-acceptance/scripts` 的脚本全在 `mmw-v2/skills/` 下（`tool-guard.py` 第 58 行、`verify-ticket.py`、`retro.py`、`extract_skeleton.py`、`pull_design.py`）；三个被分叉技能里没有脚本引用 `ui-acceptance` | grep `mmw-v2` 全部 `.py`、`.sh` | 已核实 |
| U17 | 随分叉要改路径的词表 `_Home_`：`docs/contexts/tickets/CONTEXT.md` 第 119–147 行 8 条指 `cutting-interface-tickets.md`；`docs/contexts/ticket-run/CONTEXT.md` 第 276 行指 `ui-reviewer.md`；`docs/contexts/ui-acceptance/CONTEXT.md` 第 194 行指 `to-spec/SKILL.md` | grep | 已核实 |

没有读的：`story-parity.py`、`pull_design.py`、`lease.py`、`design_render.py`、`lint_screen_contract.py`、`extract_skeleton.py` 的算法本体（归置不依赖它们）；`tests/ui-acceptance/` 等测试文件的全文（只 grep 了会被本方案影响的字面）；`to-spec` 在没有 screen contract 文件时的实际行为。

---

## 2. 归置表

列说明：**层**用 R4 第 12 节的类型名。**收益**只写用户要求 2 列的六种之一，编号：①去掉经 grep 核实的真重复；②给无处安放的内容一个家；③让上游回到原文；④被两个以上调用方复用；⑤以后加外来技能不必改现有文字；⑥消除已核实的断点或冲突。「—」＝不动。**批**指 R4 第 11 节的落地批次。

### 2.1 ui-acceptance（能力技能，`mmw-v2/skills/ui-acceptance/`）

| 现在位置 | 新位置与层 | 动作 | 具体小节 | 收益（证据） | 体量 | 被取代的旧规则 / 原意 | 批 |
|---|---|---|---|---|---|---|---|
| `SKILL.md` frontmatter `description` | 原位，能力技能 | 改写 | 删「, or before writing a page ticket's code」 | ① U1：`implement` 第 16 行已认领这一时刻；SSR `### Descriptions` 第 2 条（两个 description 争一件事） | −1 短语 | 无被取代规则；「写页面代码前读设计值」的原意由 `implement` 第 16 行加 `writing-interface-code.md` **Before the first line** 保住 | 2 |
| `SKILL.md` `## Find your moment` 第 1 行（Writing a page ticket's code …） | 删除 | 删除 | 表第 1 行 | ① 同上 | −1 行 | 同上 | 2 |
| `SKILL.md` `## Find your moment` 其余 7 行 | 原位 | 不动 | 第 2–8 行 | — | 0 | 第 3 行交给 `to-tickets`，是交给另一能力，不是重复声称（R4 D5.2） | — |
| `SKILL.md` 第 8、10、12 行（定义、立场、手跑说明） | 原位 | 不动，第 10 行句末加括注 `(the \`mmw\` skill's principle \`silence-is-never-a-pass\`)` | 第 10 行「During a night these oracles are the only eyes …」 | ④ 原则 `silence-is-never-a-pass` 多一个调用方（R4 D4.4 把 `ui-acceptance` 列为这条理由今天各写一版的地方之一） | +7 词 | 具体规则留在原句（R4 D4.2） | 3 |
| `SKILL.md` `## Five rules while the product is running` 引言与规则 1–4 | 原位 | 不动 | — | — | 0 | 标题、编号被 `PRODUCT_RULES`、`verify-ticket/references/sub-issues.md` 第 19 行、`implement/SKILL.md` 第 76 行逐字引用（lightweight review D9） | — |
| `SKILL.md` Five rules 规则 5 | 原位 | 句末加括注 `(the \`mmw\` skill's principle \`rerun-dont-reroute\`)` | 规则 5「A fault in the pipeline itself …」 | ④ 与 ⑥：R4 把 `shared.md` 规则 11（redo it yourself）在 MMW 内的适用范围写进这条原则的 `**Boundaries:**`；worker 撞上 `lease.py` 或 oracle 的拒绝时，正是这两条规则相遇的地方 | +7 词 | — | 3 |
| `SKILL.md` 第 38 行（Reporting blocked … goes through an event） | 原位 | 句末加括注 `(the \`mmw\` skill's principle \`the-tracker-is-the-state\`)` | 第 38 行 | ④ 原则多一个调用方；这句的理由（relay 只为事件唤醒人）就是这条原则 | +7 词 | — | 3 |
| `references/story-parity.md` | 原位，reference | 不动 | 全部 | — | 0 | 两类读者各一节，本身就按分支读（SSR 事实 5） | — |
| `references/boundary-check.md` | 原位 | 不动 | 全部 | — | 0 | `## Selecting one row's test` 是全仓唯一一处（N6 R18，已归一） | — |
| `references/journey.md` | 原位 | 不动 | 全部 | — | 0 | `journey.py` 第 228、235 行按名引用 **The fault-injection switch**，不改标题 | — |
| `references/harness-guard.md` | 原位 | 不动 | 全部 | — | 0 | — | — |
| `references/product-answers.md` | 原位 | 不动 | 全部 | — | 0 | 与 `journey.md`、`story-parity.md` 的部分重复（N6 R5、R6）读者不同：critical-flow 票的 worker 读 `journey.md` 不读本文件（`cutting-interface-tickets.md` 第 106 行只让 contract 票读三份）。按 L7 C.5 接受 | — |
| `scripts/story-parity.py`、`boundary-check.py`、`journey.py`、`harness-guard.py`（四个 oracle） | 原位，脚本 | 不动；它们印出的 reference 名进接线 lint 第 1 类 | U15 列的行 | lint 范围见第 4 节 | 0 | — | 1 |
| `scripts/lease.py`、`target_config.py` | 原位 | 不动 | — | — | 0 | 提交 `f74eb4f8`：一个技能拥有「怎样够到产品」的全部代码 | — |
| `scripts/design_render.py`、`pixel_diff.py` | 原位 | 不动 | — | — | 0 | 天然整体：三个脚本共用同一个渲染器与读取器（N6 第 8 节） | — |
| `scripts/refusal.py` | 原位 | 不动 | — | — | 0 | 已是单一出处，被五个技能导入；搬到 `dispatch` 或新目录拿不到任何一种收益（提案 Mem `5a337408` 的 `mmw-v2/runtime/` 没有被采纳） | — |

### 2.2 design-pages（能力技能，`mmw-v2/skills/design-pages/`）

| 现在位置 | 新位置与层 | 动作 | 具体小节 | 收益（证据） | 体量 | 被取代的旧规则 / 原意 | 批 |
|---|---|---|---|---|---|---|---|
| `SKILL.md` description、开头两段、`## Find your moment`、第 21 行宿主门槛 | 原位 | 不动 | — | — | 0 | 第 21 行是能力自带的闸门（L7 A.3） | — |
| `SKILL.md` `## The state list` | 原位 | 改写 | 「the `## State list` of the leaf `README.md` the `prototype` skill's `UI.md` step 6 names」改为按文件名点名「the `prototype` skill's `state-list.md`」 | ⑥ U4：去掉一处跨技能按编号的引用 | ±0 | 「state list 在哪两个位置」的定义仍只在这一节 | 2 |
| `references/edit-pages.md` 全部（含 `## Next`） | 原位 | 不动 | — | — | 0 | `## Next` 指向本技能自己的 `pull.md`，属能力内部（R4 D5.1） | — |
| `references/draw.md` | 原位 | 不动 | — | — | 0 | — | — |
| `references/pull.md` `## When`、`## Steps`、`## After the first pull`、`## Design problems in the report`、`## A contract child answered by this pull` | 原位 | 不动 | — | — | 0 | 天然整体：预览地址约一小时有效、不得落盘，四步必须在同一会话接着做（N6 第 8 节） | — |
| `references/pull.md` `## Reached from here` | 原位 | 不动 | — | — | 0 | 下一步取决于本技能自身输出（有无 screen contract、`改动分类`），R4 D5.1。wayfinder 一段是「交回调用方」，调用方由输入决定，固定返回句（R4 D5.4）只对 playbook 成立，覆盖不到 wayfinder 这个技能 | — |
| `references/design-system.md` `## An existing product` 第 2 步括注 | 原位 | 改写 | 「(one `### <region>` per region, one item per state the product shows)」改为「(the state list, in the shape the `prototype` skill's `state-list.md` gives)」 | ① U5 | ±0 | — | 2 |
| `references/design-system.md` 其余；两份 `CLAUDE.md` 模板 | 原位 | 不动 | — | — | 0 | 模板的读者是 Claude Design 里的 agent，读不到仓库，平行副本是必要的（N6 R14、L7 C.5） | — |
| `scripts/pull_design.py`、`check_editable_selectors.py` | 原位 | 不动；`## State list` 解析字面进 lint 第 1 类 | 第 983 行 | 见第 4 节 | 0 | — | 2 |

### 2.3 write-screen-contract（能力技能，`mmw-v2/skills/write-screen-contract/`）

| 现在位置 | 新位置与层 | 动作 | 具体小节 | 收益（证据） | 体量 | 被取代的旧规则 / 原意 | 批 |
|---|---|---|---|---|---|---|---|
| `SKILL.md` description、开头、`## Inputs`、`## Steps` 1–7、`## Re-runs`、`## Done when` | 原位 | 不动 | — | — | 0 | 第 2–5 步是对同一批行的往返填写（原文第 25 行），是一个交付物的内部步骤（L7 C.3）；`### 5. Reverse sweep`、`### 6. Write the gap list and stop for the user` 两个标题被 `to-spec/SKILL.md` 第 22 行按名回指，不改名 | — |
| `SKILL.md` `## Next` 第一段末句 | 原位 | 删除一个从句 | 删「`to-spec` runs once the map is clear, as that skill says」，保留「return to the `wayfinder` skill to record the resolution」 | ⑥ U6：第 4 批删 `wayfinder` 第 6 步那句后，这个从句指向一句不存在的话；map 清空之后去哪里，由 `mmw` `## Routes` 的 wayfinder 行接住（R4 D2.2） | −1 从句 | SSR `### Hand-offs` 旧规则「Each skill ends by naming what comes next」由 R4 改写为「交回调用方或固定返回句」；这里交回调用方 wayfinder，原意保住 | 4（与 `wayfinder` 第 6 步同一次提交） |
| `SKILL.md` `## Next`「Otherwise」两条 | 原位 | 不动 | — | — | 0 | 首写与重跑两支取决于本技能自身输出（R4 D5.1、第 15 节） | — |
| `references/screen-contract-format.md` | 原位 | 不动 | — | — | 0 | SSR 第 28 行把「每次运行都打开的 reference」算作 fragment、要求内联；但 `story-parity.py` 第 466、472 行与 `lint_screen_contract.py` 第 139 行的拒绝文字把夜里的 worker 直接送到这份文件（测试钉住文件名），内联会让 worker 读 121 行的写合同步骤。④ 已成立，拆开是对的 | — |
| `scripts/extract_skeleton.py`、`lint_screen_contract.py`、`dump_openapi.py` | 原位 | 不动；`lint_screen_contract.py` 第 139 行的 reference 名进 lint 第 1 类 | — | — | 0 | — | 1 |

### 2.4 交接 reference 与 `prototype`

| 现在位置 | 新位置与层 | 动作 | 具体小节 | 收益（证据） | 体量 | 被取代的旧规则 / 原意 | 批 |
|---|---|---|---|---|---|---|---|
| `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md` | `mmw-v2/skills/to-tickets/references/cutting-interface-tickets.md`，能力技能 `to-tickets` 的 reference | 移动（随 `to-tickets` 分叉），内容不改 | 全部 152 行 | ③ 上游没有这个文件（N6 第 5 节，squash 树 0 行）；R4 D5.3 f 类 | 上游目录 −152，自有 +152 | SSR `### Upstream skills` 末条「fewer than half … reviewed as the set's own text」由 R4 改为分叉，原意（按自有文本审）保住 | 2 |
| `mmw-v2/upstream/skills/engineering/implement/references/writing-interface-code.md` | `mmw-v2/skills/implement/references/writing-interface-code.md`，worker 操作文件的 reference | 移动（随分叉），内容不改 | 全部 57 行 | ③ 同上 | ±0 | 同上。第 35、37、41 行按编号引用「closing step 1」，同一技能内部，见第 7 节不动清单 | 2 |
| `mmw-v2/upstream/skills/engineering/code-review/references/ui-reviewer.md` | `mmw-v2/skills/code-review/references/ui-reviewer.md`，reviewer 的 axis 文件 | 移动（随分叉），内容不改 | 全部 37 行 | ③ 同上 | ±0 | 同上 | 2 |
| `prototype/UI.md` 第 3、16、28、81 行措辞；`### When there is no app yet`；第 2 步新增句；第 3 步末 scaffolding 段；第 6 步标题、首句、scaffolding 段 | 原位（上游能力技能） | 不动（R4 D5.3 e 类），各有 `merge-notes/prototype.md` 条目 | — | — | 0 | 删掉后，即使 playbook 在上下文里，agent 也会按上游把 winner 折进真实代码、拆掉 scaffolding，与 `design-pages` 的做法相反。第 3 步末段括注「(the `design-pages` skill)」也不移：它说明拆 scaffolding 不是本 agent 的事（`merge-notes/prototype.md` 第 58 行），离开这个技能名，「the first pull of the design」没有所指 | — |
| （已被 R12 K-14 改定）`prototype/UI.md` 第 6 步 `## State list` 那几句（第 108 行「Under the fixed heading `## State list` …」到行末） | 新文件 `mmw-v2/upstream/skills/engineering/prototype/state-list.md`（上游目录旁新加的 reference，d 类）；`UI.md` 第 6 步首句末加「, with the winner's state list as [state-list.md](state-list.md) says」 | 拆分 + 新建 | 格式（每区域一个 `###`、每状态一个以状态名开头的列表项、`scene` 值与 pull report 按这些名字核对、一个界面只有一份）与 wayfinder map 上的位置规则 | ③ 上游文件里去掉一段只有 MMW 下游读、被 MMW 脚本解析的格式（U3）；① 与 `design-system.md` 第 42 行的格式括注合一（U5）；⑥ 顺带消除 `design-pages` 第 25 行的按编号引用（U4）；④ 调用方有两个：`UI.md` 第 6 步（写）、`design-pages` `## The state list` 与 `design-system.md`（读、为已有产品写） | `UI.md` −1 段，新文件约 +10 行，净约 +3 行 | 与 R4 的差异：R4 D5.3 d 类说「由 playbook 那一步点名」。wayfinder map 上的 prototype 票不经过 `idea-to-tickets`（U7），只在 playbook 点名会让它们写不出合格的 state list，所以 `UI.md` 第 6 步保留一个指针；上游第 6 步本来就是 e 类改动，多一个从句不增加冲突面 | 2 |
| `prototype/UI.md` `## Next`（第 119–121 行） | 删除；内容由 `mmw/playbooks/idea-to-tickets.md` 第 2 步 **Runnable questions** 的界面分支接住 | 回到上游原文 | 整节 | ③ R4 D5.3 已列为纯 c 类；上游没有这一节（U2） | −4 行 | SSR 事实 7「结尾段说下一步」由 R4 改写为「下一步的家是 playbook」。原意（一跳不断）靠三处保住：map 路径由 `interface-and-remake.md` 的 design ticket 首行接住（U7）；`mmw` 路径由 playbook 接住；单独 `/prototype` 的会话仍有第 6 步第二段与 `SKILL.md` 规则 6 说 winner 进 Claude Design | 4（以 T1 通过为前提） |
| `prototype/SKILL.md` 规则 1 的叶子目录形状 | 不在本单元 | — | — | 由负责 `prototype` 的单元定。本单元的约束：`design-pages` `pull.md` 第 2 步、`design-system.md` 第 42 行按粗体标题「rule 1 **Lives in `prototypes/`**」引用它，若它被移成 d 类 reference，这两处要在同一次提交里改 | — | — | — |

### 2.5 文档、配置与测试

| 现在位置 | 新位置与层 | 动作 | 具体小节 | 收益（证据） | 体量 | 被取代的旧规则 / 原意 | 批 |
|---|---|---|---|---|---|---|---|
| `mmw-v2/merge-notes/to-tickets.md` 第 93 行末句 | 原位（若 R4 分叉后这份说明保留；见第 10 节 X2） | 改写 | 「只点名 … 各自的 **The criterion** 一节」改为按现状：判据形状只在本文件 **Criterion shapes** | ⑥ U13；SSR `### Upstream skills` 第 2 条（仍写着被替换规则的条目是一个 finding） | ±0 | — | 2 |
| `mmw-v2/merge-notes/prototype.md` 第 57、59 行（State list 行、`## Next` 行，后者写「与 … ask-matt 一致」） | 原位 | 改写 | 第 57 行记 state list 移到 `state-list.md`；第 59 行随 `## Next` 删除改写，出处从 `ask-matt` 改为 `mmw` 的 `idea-to-tickets` | ⑥ `ask-matt` 在第 2 批恢复上游原文后，这里的出处失效（R4 D5.3 对 `merge-notes/triage.md`、`wayfinder.md` 的同类处理） | ±0 | — | 57：2；59：4 |
| `docs/contexts/ui-acceptance/CONTEXT.md` 第 67 行（**state list** `_Home_`） | 原位 | 改写 | `_Home_` 改为 `prototype/state-list.md` 与 `design-pages/SKILL.md` | 随拆分 | ±0 | — | 2 |
| 同文件第 225、229、233 行（三个判据词条的 `_Home_`） | 原位 | 改写 | 加上（harness guard 条改为）`mmw-v2/skills/to-tickets/references/cutting-interface-tickets.md` | ⑥ U14：SSR `### Vocabulary`（引用的文件不含那些事实是一个 finding） | ±0 | — | 2 |
| `docs/contexts/tickets/CONTEXT.md` 第 119–147 行 8 条、`ticket-run/CONTEXT.md` 第 276 行、`ui-acceptance/CONTEXT.md` 第 194 行 | 原位 | 改写路径 | `mmw-v2/upstream/skills/engineering/<名>/…` 改为 `mmw-v2/skills/<名>/…` | 分叉的必要伴随改动（U17），否则 10 条 `_Home_` 指向已恢复原文、不含这些词的上游文件 | ±0 | — | 2 |
| `docs/contexts/ui-acceptance/CONTEXT.md` 其余（含 10 条 `_Home_` 在 `prototype` 的词条） | 原位 | 不动 | — | — | 0 | 词条是否归本界定上下文不属于架构（N6 第 9.1 节） | — |
| ADR 0002、0004、0011、0028、0029、0030 | 原位 | 不动 | — | — | 0 | ADR 记决定，不改正文 | — |
| `tests/ui-acceptance/`、`tests/design-pages/`、`tests/write-screen-contract/` | 原位 | 不动 | — | — | 0 | U3：`## State list` 标题不变，`test_pull_design.py` 不受拆分影响；U15：`test_story_parity.py` 钉的文件名不变 | — |
| 消费仓库 `.mmw/`（`target.json`、`harness/`、`journeys/`、`stories/`）、`prototypes/<effort>/`、`docs/specs/<effort>/screen-contract.yaml` | 消费仓库私有组件（R4 D7.6） | 不动 | — | — | 0 | 都是数据与仓库规则，不含角色的步骤顺序 | — |

### 2.6 本单元参与的、不在本单元文件里的改动

这些改动写在别的单元的文件里，起因在界面链。

| 位置 | 动作 | 内容 | 收益（证据） | 批 |
|---|---|---|---|---|
| `mmw/playbooks/idea-to-tickets.md` `## Where you are` | 新建两行，放在 R4 D3.3「有 prototype 结论、没有 spec」那一行之前 | 「一个 UI prototype 的 winner 已记录（叶子 `README.md` 有 `## State list`），还没有 `prototypes/<effort>/claude-design/` → the `design-pages` skill」；「`prototypes/<effort>/claude-design/pull-report.md` 已提交，还没有 `docs/specs/<effort>/screen-contract.yaml` → the `write-screen-contract` skill」 | ⑥ 按 R4 原样，第二种情形会命中「有 prototype 结论、没有 spec → **Who checks**」，然后进 **Spec**；`to-spec/SKILL.md` 第 22 行假定「An effort with a UI has a screen contract」，没有这个文件时怎么做，原文没写 | 3 |
| 同文件第 2 步 **Runnable questions** 的界面分支 | 改写（R4 D3.3 的句子加一句） | 「当前宿主没有 Claude Design 工具时，照 `references/phase-boundaries.md` 第 3 问用 `handoff` 换宿主，新会话从 `## Where you are` 重入；这是 **Spec** 那条『同一上下文』门槛唯一的例外。」 | ⑥ U10：两处文字对同一情形给了相反的要求。② U9：`ask-matt` 第 2 步的「Hand off only for … a host with the Claude Design tools」今天没有已安装的家 | 3 |
| `dispatch/scripts/` 锚点常量与 `mmw-v2/tests/lib/check_wiring.py` 第 1 类 | 扩大范围 | 见第 4 节 | R4 C9 的收益（把按字面引用的锚点交给机制）；界面链没有已发生的断点，这一项是预防性的 | 1 |

---

## 3. playbook 草图

本单元**不产生 playbook**。L7 C.6 信号 3、5、9 都会触发：界面链的顺序已经由三个能力技能的结尾段按自身输出分支（`UI.md` 第 6 步 → `design-pages` `pull.md` `## Reached from here` → `write-screen-contract` `## Next`），一份界面 playbook 只能复述它们。

本单元参与三份 playbook 或角色操作文件。下面只写界面链在其中的部分。

### 3.1 `idea-to-tickets`（头部 playbook，R4 D3.3）中的界面分支

- **入口**：`mmw` `## Routes` 第 1 行；或 `## Where you are` 的两行界面重入点（第 2.6 节）。
- **所有权行**：沿用 R4 D3.3，本单元不改。
- **步骤中的界面部分**：
  2. **Runnable questions.** 一个界面问题要看到才能回答 → the `prototype` skill（`UI.md`）。winner 与 state list 写好后，交给 the `design-pages` skill。在当前会话做需要宿主有 Claude Design 工具；没有时照 `references/phase-boundaries.md` 第 3 问用 the `handoff` skill 换宿主（**Spec** 同一上下文门槛的唯一例外）。之后的链（`design-pages` → `write-screen-contract` → `to-spec`）由两个技能自己的结尾段按自身输出带回 **Spec**，本 playbook 不复述。
     - Done when：`docs/specs/<effort>/screen-contract.yaml` lint 通过，gap list 每一条用户都答了（即 `write-screen-contract` `## Done when`）。
  5. **Spec.** R4 原文，不改。界面分支从 `write-screen-contract` `## Next` 直接到这里。
- **重入**：`## Where you are` 的两行（第 2.6 节），事实全部取自仓库里看得见的文件。
- **Reply**：界面分支经过时，**Someone else knows**、**Who checks** 两步没做，各写一行：「界面链直达 **Spec**」。
- **有 wayfinder map 的界面工作不经过本 playbook的这一分支**：design ticket 与 alignment ticket 由 `interface-and-remake.md` 的首行点名技能（U7）；map 清空后由 `## Routes` 的 wayfinder 行进 **Spec**。

### 3.2 worker（`implement`）中的界面部分

- **入口**：启动提示词 `Use the implement skill to work ticket #<n>. $AUTONOMOUS $PRODUCT_RULES`（`dispatch.sh` 第 1949 行，字面不变）。`PRODUCT_RULES` 点名 `ui-acceptance` 的 **Five rules while the product is running**。
- **步骤**：`implement` 第 16 行在 **Read first** 列出 screen contract 时读 `references/writing-interface-code.md`。该文件四节依次是 **Before the first line**（runs-script `story-parity.py --render-only`）、**Write the product**（reads `ui-acceptance` `story-parity.md`、`boundary-check.md` `## Selecting one row's test`；`tdd` 的例外）、**Fix in place**、**When the design side is the defect**（runs-script `verify-ticket.py <n> --sub-issue contract`）。
- **重入**：`RESUME:` 与角色指针（R4 D1.2、D3.5 a），不变。
- **交付物**：关票；或设计侧缺陷时开出的 `contract` child，正文首行后那句点名 `design-pages` `references/pull.md`。

### 3.3 reviewer（`code-review` 的 `references/session.md`）中的界面部分

`session.md` `## 2. Run the axes`：票有 story criterion 时加 UI axis，axis 子代理读 `references/ui-reviewer.md`。一次性会话，不重入。不变。

### 3.4 orchestrator（`dispatch` 的 `references/night.md`）中的界面部分

`night.md` `## 3` 第 84 行：`child.opened` 的 kind 是 `contract`、且点名一个 Claude Design 页时，把受影响的未开工票移到 `needs-triage`，child 留给白天。第 55 行：用 `target_config.py --check` 判断消费仓库能否被驱动。都不变。

### 3.5 白天回收 `contract` child

这是一条交接链，不是 playbook：`mmw` `## Routes` 的 triage 行（child 带 `needs-triage`，U12）→ `triage` `references/pipeline-issues.md` → child 正文点名的 `design-pages` `references/pull.md` → `## A contract child answered by this pull` → `dispatch.sh route … fixed` 与 `dispatch.sh resume`。四端各有读者（N6 R11），不合并。

---

## 4. 接线 lint 第 1 类：界面链的锚点

R4 D3.6 第 1 类的首句是「脚本文字点名的每个技能文件、小节与步骤名都逐字存在」，列出的范围只覆盖 dispatch 一侧。界面链的脚本文字按同一句也在范围内：

| 脚本字面 | 指向 | 做法 |
|---|---|---|
| `dispatch.sh` 第 109 行 `PRODUCT_RULES` 的 'Five rules while the product is running' | `ui-acceptance/SKILL.md` 的 `## Five rules while the product is running` | 放进 R4 的锚点常量模块。它和模块在同一个技能（`dispatch`）里，不新增跨技能导入 |
| `journey.py` 第 228、235 行「The fault-injection switch in references/journey.md」 | `ui-acceptance/references/journey.md` `## The fault-injection switch` | 模式扫描：lint 在 `mmw-v2/skills/*/scripts/` 里找「references/<file>」与「the `<skill>` skill's references/<file>」两种形状，核对文件存在；带小节名的再核对标题 |
| `story-parity.py` 第 466、472 行 | `write-screen-contract/references/screen-contract-format.md` | 同上 |
| `target_config.py` 第 91 行 | `ui-acceptance/references/product-answers.md` | 同上 |
| `lint_screen_contract.py` 第 139 行 | `write-screen-contract/references/screen-contract-format.md` | 同上 |
| `pull_design.py` 第 983 行正则里的 `## State list` | 第 2 批后是 `prototype/state-list.md` 规定的标题 | 在 `state-list.md` 里断言这个字面出现 |

工程决定：界面链脚本不改为从 `dispatch` 的锚点常量模块取字面。改了就会新增 `ui-acceptance`、`write-screen-contract`、`design-pages` 三个技能对 `dispatch/scripts/` 的导入，而这五处都是文件级或标题级的字面，模式扫描已经能核对。放弃的做法：照 L7 A.6，所有脚本都从一个常量模块取字面。

每一类要有一个能让 lint 失败的反例测试（R4 D3.6 末段），例如把 `journey.md` 的标题改掉一个字。

---

## 5. 原则候选

### 5.1 本单元对 R4 三条原则的引用（全部是括注，第 3 批）

| 原则 | 规则（R4 D4.4） | 本单元的引用位置 | 理由出处 |
|---|---|---|---|
| `silence-is-never-a-pass` | 一道检查不能因为什么都没做而读起来像通过；检查要证明自己能失败 | `ui-acceptance/SKILL.md` 第 10 行句末 | ADR 0008；ADR 0011 记录 #640 的 worker 挪 mount、塞隐藏节点（N6 第 6 节，ADR 已核实）。各 oracle 的负控制（`story-parity.md` `## Negative controls`、`boundary-check.md` 第 38 行、`journey.md` `## The negative control`）是这条原则的机制，绑定具体脚本（L7 C.2），不加括注 |
| `rerun-dont-reroute` | 被拒绝或撞上流水线自身的故障，修拒绝点名的事或报 blocked，不绕路、不写重试循环 | `ui-acceptance/SKILL.md` Five rules 规则 5 句末 | `lease.py` 头注释 2026-09-05 五个 worker 抢三个端口；`refusal.py` 头注释三个 worker 对同一条拒绝各自发明了三种错误应对（N6 第 6 节，已核实）。R4 把这两条规则列为原则的依据 |
| `the-tracker-is-the-state` | 要等别人就结束回合，由事件叫醒 | `ui-acceptance/SKILL.md` 第 38 行句末 | 第 38 行原句「an event on the ticket is the only thing the relay … wakes anybody for」；ADR 0020 |

括注是否真的改变 agent 的决定，要看 R4 T13 的走查。T13 否定时，这三个括注随原则层一起撤掉。

### 5.2 像原则、但留在原处的规则

| 规则 | 出现处 | 留在原处的理由 |
|---|---|---|
| 两份基线各管一块：design package 管外观与逐字文案，screen contract 管 `calls`/`shows`/`next`/`on_failure` | `write-screen-contract/SKILL.md` 第 8 行；`screen-contract-format.md` 第 15 行；`writing-interface-code.md` 第 3 行；`to-spec/SKILL.md` 第 22 行；`cutting-interface-tickets.md` 第 122–123 行（N6 R1，本轮复核了前三处） | 绑定 UI 领域的具体参数（L7 C.2）；五个读者各自只读自己的文件，每处都必须有这句（SSR 第 32 行「A rule sits in the text of the agent that must follow it」）。做成原则也减不掉任何一处，所以 D4.3 第 7 条（读者群没有现成的家）不满足 |
| 改产品，不改检查；修产品组件，不修 story 页 | `ui-acceptance/SKILL.md` 第 10 行；`story-parity.md` `## The DIFF line` | 是 `silence-is-never-a-pass` 在本领域的具体化，按 R4 D4.2 留原句、加括注 |
| Never complete a human step by hand | Five rules 规则 3 | 没有事故记录（N6 第 6 节「无证据」），不满足 D4.3 第 6 条；只在「产品在跑」这一个领域 |
| 不填看似合理的默认值，问用户 | `write-screen-contract/SKILL.md` 第 10 行 | 已有家：`shared.md` 规则 1（产品决定归 owner），不满足 D4.3 第 7 条 |
| mock 只放在 gateway | `boundary-check.md` 第 34 行 | 绑定具体机制（L7 C.2），只有一个读者 |
| design package 只由 pull 写 | `edit-pages.md` `## Sign-off`、`writing-interface-code.md` 第 51 行、`night.md` 第 84 行；ADR 0029 | 与 R4 不收的 `one-writer-per-file`（N9 PC12）同形；三处读者不同、各有一句（N6 R15）；R4 第 15 节写明它的进入条件，今天不满足 |
| 行 id 不重排、不复用 | `write-screen-contract` `## Re-runs`、`screen-contract-format.md` `id` 列 | 只有写合同的 agent 一个读者 |

---

## 6. 连线

组件名用 R4 第 12 节的新名字。原关系词表里没有「导入」和「读产物」：脚本之间的导入写 `calls`；读一份基线产物（design package、screen contract）写 `reads-reference`。

```edges
mmw -> idea-to-tickets : routes-to
mmw -> triage : routes-to
mmw -> wayfinder : routes-to
idea-to-tickets#Runnable questions -> prototype : calls
idea-to-tickets#Runnable questions -> design-pages : hands-off-to
idea-to-tickets#Runnable questions -> mmw/references/phase-boundaries.md : reads-reference
idea-to-tickets#Runnable questions -> handoff : calls
idea-to-tickets#Where you are -> design-pages : re-enters-at
idea-to-tickets#Where you are -> write-screen-contract : re-enters-at
idea-to-tickets#Spec -> to-spec : calls
prototype/UI.md -> prototype/state-list.md : reads-reference
wayfinder -> wayfinder/references/interface-and-remake.md : reads-reference
wayfinder/references/interface-and-remake.md -> design-pages : hands-off-to
wayfinder/references/interface-and-remake.md -> write-screen-contract : hands-off-to
design-pages -> design-pages/references/edit-pages.md : reads-reference
design-pages -> design-pages/references/draw.md : reads-reference
design-pages -> design-pages/references/pull.md : reads-reference
design-pages -> design-pages/references/design-system.md : reads-reference
design-pages -> prototype/state-list.md : reads-reference
design-pages/references/design-system.md -> prototype/state-list.md : reads-reference
design-pages/references/edit-pages.md -> design-pages/references/template-project-claude-md.md : reads-reference
design-pages/references/design-system.md -> design-pages/references/template-design-system-claude-md.md : reads-reference
design-pages/references/edit-pages.md -> design-pages/references/pull.md : hands-off-to
design-pages/references/pull.md -> design-pages/scripts/pull_design.py : runs-script
design-pages/scripts/pull_design.py -> design-pages/scripts/check_editable_selectors.py : calls
design-pages/scripts/pull_design.py -> ui-acceptance/scripts/design_render.py : calls
design-pages/scripts/pull_design.py -> ui-acceptance/scripts/refusal.py : calls
design-pages/scripts/pull_design.py -> prototype/state-list.md : reads-reference
design-pages/references/pull.md -> write-screen-contract : hands-off-to
design-pages/references/pull.md -> write-screen-contract#Re-runs : re-enters-at
design-pages/references/pull.md -> wayfinder : hands-off-to
design-pages/references/pull.md -> dispatch.sh reverify : runs-script
design-pages/references/pull.md -> dispatch.sh route : runs-script
design-pages/references/pull.md -> dispatch.sh resume : runs-script
design-pages/references/pull.md -> verify-ticket.py --sub-issue contract : runs-script
dispatch.sh resume -> implement : wakes
write-screen-contract -> write-screen-contract/references/screen-contract-format.md : reads-reference
write-screen-contract -> write-screen-contract/scripts/extract_skeleton.py : runs-script
write-screen-contract -> write-screen-contract/scripts/lint_screen_contract.py : runs-script
write-screen-contract -> write-screen-contract/scripts/dump_openapi.py : runs-script
write-screen-contract/scripts/extract_skeleton.py -> ui-acceptance/scripts/design_render.py : calls
write-screen-contract -> prototypes/<effort>/claude-design : reads-reference
write-screen-contract -> to-spec : hands-off-to
write-screen-contract -> to-spec/references/revising-a-spec.md : hands-off-to
write-screen-contract -> wayfinder : hands-off-to
to-spec -> write-screen-contract#Reverse sweep : re-enters-at
to-spec -> docs/specs/<effort>/screen-contract.yaml : reads-reference
to-spec -> ui-acceptance/scripts/target_config.py : runs-script
to-spec/references/revising-a-spec.md -> write-screen-contract#Re-runs : reads-reference
to-tickets -> to-tickets/references/cutting-interface-tickets.md : reads-reference
to-tickets/references/cutting-interface-tickets.md -> ui-acceptance/references/boundary-check.md : reads-reference
to-tickets/references/cutting-interface-tickets.md -> ui-acceptance/references/story-parity.md : reads-reference
to-tickets/references/cutting-interface-tickets.md -> ui-acceptance/references/journey.md : reads-reference
to-tickets/references/cutting-interface-tickets.md -> ui-acceptance/references/product-answers.md : reads-reference
to-tickets/references/cutting-interface-tickets.md -> to-tickets/references/person-ticket.md : reads-reference
dispatch.sh start -> implement : starts-with-prompt
dispatch.sh start -> ui-acceptance#Five rules while the product is running : starts-with-prompt
implement -> implement/references/writing-interface-code.md : reads-reference
implement -> ui-acceptance#Five rules while the product is running : reads-reference
implement/references/writing-interface-code.md -> ui-acceptance/scripts/story-parity.py : runs-script
implement/references/writing-interface-code.md -> ui-acceptance/references/story-parity.md : reads-reference
implement/references/writing-interface-code.md -> ui-acceptance/references/boundary-check.md : reads-reference
implement/references/writing-interface-code.md -> tdd : reads-reference
implement/references/writing-interface-code.md -> verify-ticket.py --sub-issue contract : runs-script
implement/references/writing-interface-code.md -> design-pages/references/pull.md : hands-off-to
code-review/references/session.md -> code-review/references/ui-reviewer.md : calls
code-review/references/ui-reviewer.md -> ui-acceptance/scripts/story-parity.py : runs-script
verify-ticket -> ui-acceptance : hands-off-to
verify-ticket/references/sub-issues.md -> ui-acceptance#Five rules while the product is running : reads-reference
verify-ticket.py -> ui-acceptance/scripts/story-parity.py : runs-script
verify-ticket.py -> ui-acceptance/scripts/boundary-check.py : runs-script
verify-ticket.py -> ui-acceptance/scripts/journey.py : runs-script
verify-ticket.py -> ui-acceptance/scripts/harness-guard.py : runs-script
verify-ticket.py -> ui-acceptance/scripts/lease.py : calls
verify-ticket.py -> write-screen-contract/scripts/lint_screen_contract.py : calls
verify-ticket.py -> relay.py : wakes
relay.py -> implement : wakes
dispatch/references/night.md -> ui-acceptance/scripts/target_config.py : runs-script
dispatch/references/night.md -> design-pages/references/pull.md : hands-off-to
triage/references/pipeline-issues.md -> design-pages/references/pull.md : hands-off-to
dispatch.sh -> ui-acceptance/scripts/lease.py : runs-script
dispatch/scripts/tool-guard.py -> ui-acceptance/scripts/refusal.py : calls
retro/scripts/retro.py -> ui-acceptance/scripts/refusal.py : calls
ui-acceptance -> ui-acceptance/references/story-parity.md : reads-reference
ui-acceptance -> ui-acceptance/references/boundary-check.md : reads-reference
ui-acceptance -> ui-acceptance/references/journey.md : reads-reference
ui-acceptance -> ui-acceptance/references/harness-guard.md : reads-reference
ui-acceptance -> ui-acceptance/references/product-answers.md : reads-reference
ui-acceptance -> to-tickets/references/cutting-interface-tickets.md : hands-off-to
ui-acceptance -> implement : hands-off-to
ui-acceptance -> ui-acceptance/scripts/target_config.py : runs-script
ui-acceptance -> ui-acceptance/scripts/harness-guard.py : runs-script
ui-acceptance -> ui-acceptance/scripts/lease.py : runs-script
ui-acceptance#Five rules while the product is running -> dispatch/scripts/tool-guard.py : enforced-by-hook
ui-acceptance -> principle:silence-is-never-a-pass : cites-principle
ui-acceptance -> principle:rerun-dont-reroute : cites-principle
ui-acceptance -> principle:the-tracker-is-the-state : cites-principle
ui-acceptance/scripts/story-parity.py -> ui-acceptance/scripts/design_render.py : calls
ui-acceptance/scripts/story-parity.py -> ui-acceptance/scripts/pixel_diff.py : calls
ui-acceptance/scripts/story-parity.py -> ui-acceptance/scripts/lease.py : calls
ui-acceptance/scripts/story-parity.py -> ui-acceptance/scripts/target_config.py : calls
ui-acceptance/scripts/story-parity.py -> ui-acceptance/scripts/refusal.py : calls
ui-acceptance/scripts/journey.py -> ui-acceptance/scripts/target_config.py : calls
ui-acceptance/scripts/journey.py -> ui-acceptance/scripts/lease.py : calls
ui-acceptance/scripts/boundary-check.py -> ui-acceptance/scripts/lease.py : calls
ui-acceptance/scripts/boundary-check.py -> ui-acceptance/scripts/refusal.py : calls
ui-acceptance/scripts/harness-guard.py -> ui-acceptance/scripts/lease.py : calls
ui-acceptance/scripts/target_config.py -> ui-acceptance/scripts/lease.py : calls
ui-acceptance/scripts/story-parity.py -> .mmw/target.json : configured-by
ui-acceptance/scripts/journey.py -> .mmw/target.json : configured-by
ui-acceptance/scripts/harness-guard.py -> .mmw/target.json : configured-by
ui-acceptance/scripts/lease.py -> .mmw/target.json : configured-by
ui-acceptance/scripts/story-parity.py -> docs/specs/<effort>/screen-contract.yaml : reads-reference
ui-acceptance/scripts/story-parity.py -> write-screen-contract/references/screen-contract-format.md : reads-reference
ui-acceptance/scripts/journey.py -> ui-acceptance/references/journey.md : reads-reference
ui-acceptance/scripts/target_config.py -> ui-acceptance/references/product-answers.md : reads-reference
```

接线 lint 覆盖的边（第 4 节）：`dispatch.sh start -> ui-acceptance#Five rules…`、`ui-acceptance/scripts/journey.py -> …journey.md`、`story-parity.py -> …screen-contract-format.md`、`target_config.py -> …product-answers.md`、`lint_screen_contract.py` 的同类边、`pull_design.py -> prototype/state-list.md`。其余文本到文本的锚点（例如 `to-spec` 第 22 行回指 **Reverse sweep**、`sub-issues.md` 与 `implement` 第 76 行按编号引用 Five rules 规则 3、4）不在 lint 范围内。

---

## 7. 不动清单

| 部件或段落 | 理由 |
|---|---|
| 三个技能作为能力技能的整体与位置 | 产出可命名交付物、能脱离 mode 被调用（L7 C.3）；R4 D3.1 已判定不建界面 playbook |
| `ui-acceptance` 的 oracle、lease、refusal、渲染库放在同一技能 | 提交 `f74eb4f8` 的决定；拆开得不到六种收益中的任何一种 |
| `ui-acceptance` Five rules 的编号与标题；`sub-issues.md` 第 19 行、`implement` 第 76 行按编号引用规则 3、4 | 编号与标题同时被三个文件和启动提示词逐字引用（lightweight review D9）。按编号跨技能引用与 SSR 第 81 行不一致，但今天没有断，改成按标题会拉长两句外部文字，又修不了任何已发生的断点 |
| `ui-acceptance` 各 reference 之间的部分重复（N6 R4–R7、R9） | 读者不同（写 `start` 的、写 journey 的、建 story 的、读 `DIFF` 的），L7 C.5 |
| `design-pages` `## Find your moment`、`edit-pages.md`、`draw.md`、`pull.md` 全部、两份模板 | 下一步取决于本技能自身输出（R4 D5.1）；pull 四步是天然整体；模板的读者读不到仓库 |
| `pull.md` `## A contract child answered by this pull` 与 `triage/references/pipeline-issues.md` 都写「把停下的票移回 `ready-for-agent`」 | 同一个动作的两端，读者不同（带 Claude Design 工具的会话、triage 会话）；动作是改标签，重复执行无害（N6 R11） |
| `write-screen-contract` 除 `## Next` 一个从句外的全部 | 能力内部；两个步骤标题被 `to-spec` 按名回指 |
| `screen-contract-format.md` 独立成文件 | 见 2.3：脚本拒绝文字把夜里的 worker 送到这份文件，测试钉住文件名 |
| 三份交接 reference 的内容 | 随分叉整体搬家，不改文字。`writing-interface-code.md` 第 35、37、41 行的「closing step 1」是同一技能内部按编号引用；R4 D3.4 只给步骤加名、不改编号，所以不会断，改写拿不到六种收益之一 |
| `writing-interface-code.md` 第 49 行的中文固定句 | 它是写进 `contract` child 正文、给白天会话读的路由句，是白天到达 `design-pages` 的唯一文字入口（U12）。它是否属于 SSR「只在程序用到的名字里出现另一种语言」的例外，不属于架构 |
| `UI.md` 的 e 类改动（第 2.4 节所列）与第 3 步末段括注 | 删掉后 agent 会做错；括注是这条规则的一部分 |
| `interface-and-remake.md` | 本单元只读它；它已经是上游目录旁的 MMW 文件，首行点名技能的做法让 map 上的票不需要 playbook |
| `docs/contexts/ui-acceptance/CONTEXT.md` 结构、ADR 0011/0028/0029/0030 | 各有读者；ADR 不改正文 |
| 测试目录 | 本方案不改被测字面 |

---

## 8. 形式拆散自查（L7 C.6 十一个信号）

1. **新建前没有确认已有组件不是合适的归宿。** 未触发。（R12 K-14 改为放进 `design-pages` 的 reference：R8 排除 `design-pages` 的理由只针对它的 `SKILL.md`。）唯一的新文件是 `prototype/state-list.md`。已有的两个候选都看过：`UI.md` 第 6 步是上游文本，留在那里正是要消除的 d 类改动；`design-pages` `## The state list` 是另一个技能，prototype agent 在第 6 步要为十行格式去读一份带 `## Find your moment` 表的别的技能的 `SKILL.md`，可能被带进 `design-pages` 的工作。同一目录的 `evidence-page.md` 是同类先例（U8）。
2. **新增内容不改变决定。** 三个原则括注可能触发：它们在正常路径上不改变决定，只在规则没覆盖的情形给出理由，是否有用要看 R4 T13。每个括注只有几个词，T13 否定时撤掉。`## Where you are` 两行改变重入去处（不加时会跳过 `write-screen-contract`），不触发。
3. **重复已有的、位置得当的指引。** 部分触发，已说明：`## Where you are` 第二行与 `pull.md` `## Reached from here` 第一支说的是同一个去处，但触发不同（压缩或换会话后重入 vs 刚做完 pull），属 L7 C.5 可以接受的重复。
4. **本可由机制强制的规则写成了文字。** 未触发，而且反过来：把 lightweight review D9 那条「标题逐字引用、不得改」的文字约束，以及 `## State list` 这个解析字面，交给接线 lint（第 4 节）。
5. **playbook 只调一个技能，没有门槛、所有权、交付物。** 未触发：不建界面 playbook。
6. **reference 每次都读、只有一个调用方、读者是本代理自己。** 未触发：`state-list.md` 只在 UI 分支的第 6 步读，另有 `design-pages` 两处调用方。
7. **原则说不出改变哪个决定，或只适用一步。** 未触发：不新建原则。
8. **拆完需要按步骤编号引用。** 未触发，而且反过来：`design-pages` 第 25 行的「`UI.md` step 6」改为按文件名引用。
9. **拆出的内容没有第二个调用方，也不减少重复。** 未触发：`state-list.md` 有两个调用方，并合掉 `design-system.md` 的格式括注。
10. **把单入口的固定流程拆成三层。** 未触发：worker、reviewer 的界面部分仍在各自的操作文件和 reference 里。
11. **把只在流程之间复用的内容做成能力技能。** 未触发：没有新技能。

---

## 9. 待用户决定

| # | 决定 | 为什么是你的决定 | 建议 |
|---|---|---|---|
| D1 | 没有 wayfinder map 的界面工作（例如给已有产品加一个界面），从原型、在 Claude Design 里画页、pull、写 screen contract 到写 spec，是否仍必须在**同一个会话**里完成、你全程在场 | 这是原 `ask-matt` 第 2 步的规定（U9），它决定你怎样使用这套工具：在 Claude Design 里画页可能要几小时，这期间 Claude Code 的会话要一直开着。理由是没有 map 时，screen contract 引用的决定只存在于这段对话里（`write-screen-contract` 第 10 行把用户的回答记作 `conversation <date>`） | 保留这条规定，只允许一个例外：当前宿主没有 Claude Design 工具时，用 `handoff` 换到有工具的宿主，交接文件带走已定的决定。如果你希望画页期间可以关掉会话、之后再回来，就要另定一个在中断前把决定写下来的地方（例如先写一份 spec 草稿），这会改变 **Spec** 那一步 |
| — | 第 4 批删掉 `UI.md` `## Next` 后，你直接输入 `/prototype` 做界面原型时，技能结尾不再点名 `design-pages`（第 6 步仍会说 winner 进 Claude Design） | 可见行为变化 | 已含在 R4 第 11 节第 4 批的 owner 确认项里，这里不另开 |

---

## 10. 未确定

| # | 问题 | 需要的实测或信息 | 影响 |
|---|---|---|---|
| X1 | 五个宿主里哪些有 Claude Design MCP 工具。本轮只在 Claude Code 上看到（U11） | 在每个宿主的会话里列出可用工具 | **Runnable questions** 换宿主的例外会多常发生；D1 的建议是否可行 |
| X2 | R4 分叉之后，`merge-notes/to-tickets.md`、`implement.md`、`code-review.md` 是否保留（R4 D5.3 只写了分叉表） | 由负责 `merge-notes` 与分叉的单元定 | 第 2.5 节第 93 行的改正落在哪里，或随文件一起退役 |
| X3 | `to-spec` 遇到一个有界面、却没有 `screen-contract.yaml` 的 effort 时会怎么做（第 22 行只写了「A row whose `gap` is not `aligned`」的情形） | 读 `to-spec` 全文，或用一个无合同的测试 effort 走一遍 | 第 2.6 节两行 `## Where you are` 是否足够；`to-spec` 是否也该有一句兜底（`to-spec` 单元的事） |
| X4 | `mmw` 的 description 与 `design-pages` 的「when an existing product is to be designed in Claude Design」是否会抢同一个请求（例如「把现有产品重新设计一下」） | 按 SSR `### Descriptions` 第 2 条并排读，再用 R4 T1 的会话验证（R4 T11 的延伸） | 已有产品的改版是走 `idea-to-tickets` 先 **Grill**，还是直接进 `design-pages`；`write-screen-contract` 需要「backend decisions」作输入，直接进 `design-pages` 时这些决定可能还不存在 |
| X5 | 接线 lint 的模式扫描能否覆盖界面链脚本里所有指向技能文本的字面（字面写法不止一种，例如 `extract_skeleton.py` 只点技能名、`design_render.py` 第 92 行写「run write-screen-contract」） | 实现时对 `mmw-v2/skills/*/scripts/` 全量扫描，逐条对照；每类配反例测试（R4 T5） | 第 4 节的做法是否需要退回到常量模块 |
| X6 | 负责 `prototype` 的单元是否把 `SKILL.md` 规则 1（叶子目录形状）判为 d 类并移走 | 由那个单元定 | `design-pages` `pull.md` 第 2 步、`design-system.md` 第 42 行的引用要同一次提交改 |
