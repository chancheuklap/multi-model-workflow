# design-pages

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：这个技能有一处真实的交接断口：`pull-report.md` 的 `覆盖` 和 `本地改过的说明` 两节没有人读。state list 里没画的状态、没有 `scene` 的页面，要到 design ticket 关掉以后才被 `write-screen-contract` 的 lint 拦下；被 pull 覆盖、再也找不回来的本地改动，没人告诉用户。另外有三句理由被前几轮删掉了，都在"为了省事而破坏约定"的那一刻起作用。`draw.md` 大半在复述 Claude Design 工具自己的说明，可以删减。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` 第 8 行引言之后 | What this skill pulls is copied exactly by implementation and compared element by element by the story judge, and only a session with the Claude Design tools can correct it: a page that is wrong in the repository becomes a wrong product, or a night ticket stalled on a `contract` child. So hold the pages to the conventions in the project `CLAUDE.md`; how they look is the user's call. | pull report 里的问题：没有它，会被当成可以放过的提示；有了它，按约定修到位。后半句划清分工：约定归这个会话把关，好不好看归用户。 |
| I2 | `references/pull.md`，`## Design problems in the report` 第一条之后 | Under `覆盖`, a state the state list names that no page draws, a page with no `scene`, and a page root with no `data-ui` are design fixes like the `设计检查` lines: acceptance cannot check what the pages do not declare, and the `write-screen-contract` lint refuses them after the design ticket has closed. When `本地改过的说明` says the package had local edits, those edits are gone now: tell the user, because a change they wanted has to be made again in Claude Design. | 交接断口，按功能缺口修。关闭条件同时改为 "closes after the first pull whose `设计检查` and `覆盖` have nothing left to fix"。依据：`lint_screen_contract.py` 的 `handoff_page_errors` 会拒绝这三类；`pull_design.py` 的 `prepare_staging` 与 `install` 在替换后删除备份，本地未提交的修改找不回来。 |
| I3 | `references/design-system.md` `## What it is for`，现有两句之前（恢复 `e74e0140`/`4372d901` 删掉的正面用途，改写为两句） | It gives every page one look: the agent inside Claude Design composes named parts and steps instead of guessing values, so a page drawn next month matches one drawn today. Built from an existing product, it is also where the product's inconsistencies are settled: each unified value is a row of `Unifications`, and the product follows once pages drawn with it are pulled. | 判断"值不值得建一个"时：现在这一节只有否定句，agent 只会倾向于不建；补回用途后，它能在两边之间权衡。 |
| I4 | `references/template-project-claude-md.md` `## Files`，"It loads no product code" 之后（恢复 `cb45a515` 删掉的理由） | Its look comes from the design system and its own markup: a page that runs the product's own code would make acceptance compare the product with itself, and product stylesheets bring in selectors the editor cannot reach. | 这份模板会写进 Claude Design 项目的 `CLAUDE.md`，由那边的 agent 读。"直接用产品样式表省事"的诱惑出现时，有理由才不会让步。真实事故见 spec #445 第三个问题：抄进来的生产 CSS 带来 18 条编辑器点不中的选择器，其中一条把指标数值缩成了 13px 灰字。 |
| I5 | `references/edit-pages.md` `## Next`，替换 "nothing checks them before that" | A pull is two tool calls and one command, and its report is the convention check: when you doubt the pages hold the conventions, pull and read the report rather than reading pages by hand. | 原句可以读成"所以现在自己查"，也可以读成"所以不用查"。改后说清楚：检查约定就是跑一次 pull。 |

### 与你之前裁定的冲突（需要你确认）

I3 与 I4 恢复的，正是你 9 月的一条裁定（Nowledge Mem `415f96d0`）明确说"已写在 ADR 0029/0030，不必再写回技能文本"的那一类理由。我仍建议恢复这两句，理由是它们过得了这一轮的检验：
- I4 的读者是 Claude Design 里的 agent，它根本读不到本仓的 ADR；"用产品样式表省事"的诱惑出现时，只有这句理由能让它不让步。ADR 0030 记录的正是这件事真实发生过两次。
- I3 让"建不建 design system"这个判断有了正反两面；现在这一节只剩否定句。

同一条裁定里提到的 Handoff 导出的理由（调查员原稿的 I6），我按你的裁定不写回：用户提议用导出功能时，agent 可以去读 ADR 0029，这句不改变 agent 在技能里做的任何选择。

### 删除或交给脚本

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | `references/draw.md` `## When this session draws` 第 1–4 步 | 换成："Only when the user asks this session to write or change pages. The Claude Design tools say how to load the design prompt, plan writes and preview. Beyond them: follow the project `CLAUDE.md`; when a prototype's winning variant exists, it is the reference for layout and interaction; write with `if_match`, so an edit the user just made in the editor is not overwritten; a large generated file, such as a product's example data, stays in the repository for the agent inside Claude Design to read through its GitHub connection." 完成标准保留。 | 大部分与工具说明逐条重复。调查员 C1 草稿漏掉了 `if_match` 那一条，这是用户与本会话同时编辑时的真实风险，加回。 |
| D2 | `draw.md` `## Comments` 中 `author_is_you: false` 的处理 | 压成："Queued comments are the user's requests on the pages: take them, handle them as `list_comments` describes, and change pages as below." | `list_comments` 的 TRUST RULE 说得更细。 |
| D3 | `references/edit-pages.md` `## Create the project` 第 1–6 步 | 改为终态清单加一个判断点（调查员 C2 草稿），保留 `ui-ids.md` 的收集方法与 "Ids read from `scenes.json` alone miss elements that carry no text" | 除"项目先建、写入合在一个 `finalize_plan` 里、链接最后给"外，其余是一个终态，不是一串动作。 |
| D4 | `pull.md` 第 2 步命令里的 `[--tools <dir>]` | 删 | 默认值即可用；缺目录时脚本的拒绝会说明要传。 |
| D5 | `pull.md` 第 2 步末句 Chromium 安装命令 | 把安装命令写进 `render_scenes` 在浏览器缺失时的拒绝，再删这句 | 下一步应在失败那一刻给出。 |
| D6 | state list 的位置在 `edit-pages.md`、`pull.md`、`design-system.md` 各说一遍 | 在 `SKILL.md` 定义一次"the state list"（它在哪两个位置），其余只写 "the state list" | 三处同一事实，两个时刻的 agent 都先读 `SKILL.md`。 |
| D7 | `edit-pages.md` 开头 "This file sets the Claude Design project up…"；`design-system.md` `## After the design system changes` 第一句 | 删 | 与 `SKILL.md` 引言、`edit-pages.md` 的同名一节重复。 |
| D8 | 脚本：`pull_design.py` 的 `pages_from_list_files` 与第二种位置参数形式及其测试；package `README.md` 里 `## State list` 的保留逻辑及其两个测试；`previous_paths` 对 `{"path": …}` 行的兼容；读本次刚写下文件时的容错分支 | 删 | 死代码或守不会发生的路径（调查员"脚本"一节逐条给了位置与证据）。 |
| D9 | 脚本：`覆盖` 一节按页面去重（每页一行，写数量和不重复的标签） | 改 | 真实报告 131 行里 109 行是同一类标签逐 scene 重复，会淹没 I2 要求读的那几行。 |
| D10 | 脚本：scene 只从带 `Component · ` / `App · ` 前缀的页面生成，去掉只按文件名跳过 `overview.dc.html` 的特例 | 改 | 与模板 "are not pulled into acceptance" 的规则、`page_inventory` 的前缀规则统一。未观察到实际出错，属一致性修正。 |

### 不采纳

- A8（为收集产品侧 `data-ui` id 写脚本）：没有使用证据，调查员自己也建议这一轮不动。
- 调查员 I6（Handoff 导出的理由）：见上方"与你之前裁定的冲突"。
- `strip_injected_head` 合并两条路径、`check_editable_selectors.py` 豁免 `[data-ui…]`、删它的 `main()`：收益小。

## 结论

技能文本 7 个文件共约 4,600 词（`wc -w`：`SKILL.md` 323，`references/pull.md` 919，`references/template-project-claude-md.md` 891，`references/design-system.md` 853，`references/edit-pages.md` 778，`references/template-design-system-claude-md.md` 572，`references/draw.md` 268）；脚本 1,840 行（`scripts/pull_design.py` 1,728，`scripts/check_editable_selectors.py` 112）。前几轮已经把它削得很瘦，文本里的"废话"不多：主要是 `references/draw.md` 大半在复述 Claude Design MCP 工具自己的说明，以及 state list 放在哪里这件事在三个文件里各说一遍。更要紧的问题在两头：一是 `pull-report.md` 的 `覆盖` 一节在技能文本里一个字都没有，agent 不知道其中哪些行算设计缺陷，design ticket 的关闭条件也只看 `设计检查`；二是前几轮删掉了几段"为什么"，最明显的是 `design-system.md` 标题为 `## What it is for` 的那一节现在只剩"它不是做什么的"。估计文本可删约 350–450 词、补回约 200 词，净减约 200 词；脚本可删约 90–110 行死代码和过度防御，功能不丢。灵魂部分大体完整（"Claude Design 是唯一设计源头"、"那边的 agent 只看得见自己的项目"都写到了），缺的是"拉回来的页面在下游被当成必须照抄的基线"这层后果。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
|---|---|---|---|---|---|
| A1 | `references/draw.md` `## When this session draws` 第 1、3、4 步（"`get_claude_design_prompt` with the design system's id…"、"`finalize_plan` with `scope: "project"` once per session, and `create_support_js`…Every `write_files` carries `if_match`…"、"`render_preview` returns `serve_url` and `open_url`…"） | 6（重复 MCP 工具说明） | 这几句和工具说明逐条对得上：`get_claude_design_prompt` 的说明是"MUST be called before any write_files"，`read_design_skill` 写着"hifi-design for polished…, frontend-design for work outside an existing brand"，`finalize_plan` 写着"For an iterative editing session, pass scope:"project""，`create_support_js` 写着"call this once per directory that will contain .dc.html files"，`write_files` 写着"Pass each file's if_match…so a concurrent edit…is caught"，`render_preview` 写着"NEVER include serve_url in any user-facing text…open_url…is the ONLY link you give the user"。这个技能只在接了这些工具的会话里跑（`SKILL.md` 第 19 行），agent 调用工具时就能读到这些说明 | 由 MCP 工具说明承担，agent 调用时能看到。剩余风险：Claude Design 以后改了工具说明，而这里的复述本来也同样会过时 | 这一节按 C1 改写：保留"Only when the user asks"、"Follow the project `CLAUDE.md`"、prototype winner 作参照、大的生成文件留在仓库这几句，外加完成标准。约减 110 词 |
| A2 | `references/draw.md` `## Comments`（"When a comment or reply has `author_is_you: false`, show it to the user and wait…"） | 6 | `list_comments` 说明里的 TRUST RULE 讲的是同一件事，而且更细（逐段文字判断 `author_is_you`，处理完再 ack）；`ack_comments` 的说明也写着"ack AFTER handling"。这段的旧版本还直说"that is the rule in the `list_comments` description"（提交 cb45a515 删掉了这半句） | 由 `list_comments` / `ack_comments` 的说明承担。剩余风险低 | 压成一句："Queued comments are the user's requests on the pages: take them, handle them as `list_comments` describes, and change pages as below." 保留完成标准。约减 40 词 |
| A3 | `references/pull.md` `## Steps` 第 2 步命令里的 `[--tools <dir>]` | 2 | 默认值 `tool_scripts()`（`pull_design.py` 第 168–171 行）指向同一安装里的 `ui-acceptance/scripts`，本来就能用。只有一个测试传过这个参数（`mmw-v2/tests/design-pages/test_pull_design.py` 第 513 行，用的是隔离出来的脚本副本）。技能文本也从没说过什么时候该传 | 真缺这个目录时，`load_design_render` 的拒绝信息会说"Pass --tools with the ui-acceptance scripts directory"（第 732–736 行） | 从命令里删掉这个参数，脚本不动 |
| A4 | `references/pull.md` 第 2 步末句"The command renders in Chromium through Playwright; a machine without that browser installs it once with `uv run --with playwright python -m playwright install chromium`." | 1 | 这条安装命令 agent 只在 Chromium 缺失那一刻才用得上。那一刻 `render_scenes` 的拒绝信息（第 946–951 行）只说"Fix the named page or local Chromium runtime"，没给命令 | 改由脚本的拒绝信息承担。剩余风险：无 | 把安装命令挪进拒绝信息（按 Playwright "Executable doesn't exist" 这类错误区分出来），文本里删掉。约减 30 词 |
| A5 | state list 放在哪里，三处各说一遍：`references/edit-pages.md` 第 3 步（"the `## State list` of the leaf `README.md` the `prototype` skill's `UI.md` step 6 names, or of `prototypes/<effort>/README.md`…"）、`references/pull.md` 第 2 步第二段（"Pass `--state-list` pointing at the `README.md` that holds the state list…"）、`references/design-system.md` `## An existing product` 第 2 步 | 6 | 三处表达的是同一个事实 | 这两个时刻的 agent 都会先读 `SKILL.md`，所以放一份在 `SKILL.md` 就能都覆盖 | 在 `SKILL.md` 定义一次"the state list"（它在哪两个位置），另外几处只写 "the state list"。约减 60 词 |
| A6 | `references/edit-pages.md` 开头"This file sets the Claude Design project up so its pages carry what the repository reads back, and records sign-off." | 6 | `SKILL.md` 第 8 行和本文件标题已经说过同样的话 | 由 `SKILL.md` 引言承担 | 删除。约减 25 词 |
| A7 | `references/design-system.md` `## After the design system changes` 第一句"Changes are made in Claude Design, by the user or by its agent." | 6 | 和 `edit-pages.md` 第 20 行第一句一字不差 | 由 `edit-pages.md` 那一节承担 | 只保留指向 `edit-pages.md` 的那一句 |
| A8 | `references/edit-pages.md` `## Create the project` 第 4 步"open the product's story page for each scene of the last design package's `scenes.json` and collect every `[data-ui]` it renders" | 1（优先级低） | 这是一件固定步骤的收集工作（打开每个 story 页，读出所有 `[data-ui]`），脚本能做。现有的 `story-parity.py --render-only` 只渲染设计这一侧（见它的头部注释），做不了这件事。我在 tracker 和 git 里都没找到 `ui-ids.md` 实际被写过的证据 | 暂不改：这个分支只在"产品已经带 `data-ui` id"时才走到，没有使用证据的时候，为它写脚本是过度设计。文中"Ids read from `scenes.json` alone miss elements that carry no text"一句是真实的坑，保留 | 以后这个分支真的反复用到，再给 `story-parity.py` 加一个只列产品侧 id 的模式；这一轮不动 |

不列入 A 的：`SKILL.md` 的 `## Resolve <scripts> once` 属于 `SKILL-SET-REVIEW.md` `### Redundancy and bloat` 明确点名要留的"防误用"句；`pull.md` 第 1 步"do not print it or write it to a file"和工具说明部分重复，但这里的场景是往 shell 环境变量里填 token，容易被 `echo` 或写进脚本，保留。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 标题"a Claude Design project is the only source of the design"和第 8 行引言"The user designs in Claude Design, with the agent inside it…"：规定了本会话的角色，它负责设计和仓库之间的边界，不负责设计本身。
- `SKILL.md` 第 19 行"Only a session whose host has the Claude Design MCP tools can do this skill's work, and a dispatched worker never runs it…stop before writing anything"：挡住夜里的 worker 或没接这套工具的宿主半路动手。
- `references/edit-pages.md` `## Talking to the agent inside Claude Design` 整节（"That agent sees only its project…So the user never composes instructions"）：讲清楚另一个 agent 看不见本会话，因此交接必须写成项目里的文件。这是 `task.md` 机制存在的理由。
- `references/edit-pages.md` `## Sign-off`（"every design change is made in Claude Design…a local edit is overwritten by the next pull"）：把"唯一源头"落到具体动作上。
- `references/design-system.md` `## When, and from what` 表和"Skip it for a one-page change…"：这是判断什么时候不必建 design system 的依据，不是流程。
- `references/design-system.md` `## Who builds it` 首段（"That agent cannot see this conversation, and it reads the repository only through Claude Design's GitHub connection"）。
- `references/design-system.md` `## An existing product` 第 2 步"never inside it: each pull rewrites the design package to exactly the files the pages load"，以及第 4 步"On the first pull the pages differ from the product wherever the design system unified a value; element parity names each of those elements, and the tickets cut from the contract bring the product to the design"：事先告诉 agent 第一次 pull 出现大量差异是预期内的，不是故障。
- `references/pull.md` `## When`"Do not replace the design package while a worker is running a ticket; a ticket held at night on a `contract` question is not running…"：说的是和夜间流水线的时间关系。
- `references/pull.md` `## After the first pull`"the variants stay there as reference"。
- `references/pull.md` `## Design problems in the report` 末句"MCP tools cannot create a comment on a design page, so this does not go through comments"：防止 agent 去试一条走不通的路。
- `references/pull.md` `## Reached from here` 中 `只改外观或文案` 一条的"because no `data-ui` id did"和"tell the user that the spec's landed tickets were not re-run against the new package"：写的是后果，也写了该告诉用户什么。
- `references/pull.md` 末句"Git is the design's version history; Claude Design keeps none."：这是每次 pull 都必须提交的理由。
- `references/template-project-claude-md.md` 首段（"These conventions are what the repository reads back…Everything else about how pages are designed is open"），以及每条约定后面附的理由（"The ids are how the repository recognises a control across edits"、"so the repository can hand the product the same values"、"so it renders the same after it is pulled"）：Claude Design 里的 agent 靠这些理由处理约定没写到的情况。
- `references/template-design-system-claude-md.md` `## Unification` 整节和"The code is read only to find the parts…organised by part, not by the product's screen regions"。
- `references/draw.md`"Only when the user asks this session to write or change pages"和"When a prototype's winning variant exists, it is the reference for layout and interaction"。

### 缺口与补充草稿

- `SKILL.md` 第 8 行引言之后：文本没有说拉回来的页面在下游是什么地位。`implement` 把 design package 当作"copied exactly"的基线（`mmw-v2/upstream/skills/engineering/implement/SKILL.md` 第 20 行）；story judge 按 `data-ui` 逐个元素比对；screen contract 按 id 绑定行为。不知道这些，agent 会把 pull report 里的问题当成可以放过的提示，把定稿当成交差的时刻。
  > The pulled pages are not a reference to be interpreted. Implementation copies them exactly, the story judge compares the product with them element by element, and the screen contract binds each `data-ui` id to what it calls. A page that is wrong, or that breaks a convention, becomes a wrong product or a stalled night ticket, and only a session like this one can clear it. So the conventions in the project `CLAUDE.md` are what this skill holds the pages to; how the pages look is the user's.

- `references/pull.md` `## Steps` 第 3 步，以及 `## Design problems in the report` 第一条：`pull-report.md` 四节里有两节（`覆盖`、`本地改过的说明`）在整个技能集合里没有任何一句话提到（`grep -rn "覆盖\|本地改过"` 在 `mmw-v2/skills`、`mmw-v2/upstream/skills` 下都没有结果）。design ticket 的关闭条件只看 `设计检查`，所以 state list 里的状态没画、页面没有 `scene`、页面根元素没有 `data-ui` 这些真实缺陷都不会拦住它。这三项正是 `write-screen-contract` 的 `lint_screen_contract.py` `handoff_page_errors`（第 297–321 行）后面会当成错误拒绝的，那时 design ticket 已经关了。另外，`本地改过的说明` 报"有本地改动"时，这些改动已经被 pull 覆盖掉，而且找不回来：`prepare_staging` 删掉上次清单里的文件再重新下载（第 1543–1551 行），`install` 换完目录就删除备份（第 1594–1605 行），未提交的修改就此丢失。agent 应该告诉用户。试点里 agent 自己去查了 `覆盖`（#553 的关闭评论写着"覆盖状态清单全部 40 个状态"），但这是运气，文本里没有要求。
  > Under `覆盖`, a state the state list names that no page draws, a page with no `scene`, and a page root with no `data-ui` are design fixes like the `设计检查` lines: acceptance cannot check what the pages do not declare, and the `write-screen-contract` lint refuses them after the design ticket has closed. Text with no `data-ui` id is text acceptance will not compare; raise it with the user only for copy whose exact wording matters. When `本地改过的说明` says the package had local edits, those edits are gone now: tell the user, because a change they wanted has to be made again in Claude Design.

  同时把关闭条件"closes after the first pull whose `设计检查` has nothing left to fix"改成"whose `设计检查` and `覆盖` have nothing left to fix"。

- `references/design-system.md` `## What it is for`：这一节现在只说它不是用来做什么的（"No judge compares against the design system…It is not a step every design must pass through"）。正面的用途在提交 e74e0140 / 4372d901 中被删掉了（原文是"**For Claude Design**: every page drawn in the product's project uses one look, and the agent inside Claude Design has named parts to compose instead of guessing values. **For the product**: …inconsistent values in the code…are unified into one scale…"）。缺了这一段，agent 判断"值不值得建一个"时只有否定的理由，结果只会倾向于不建。
  > It gives every page one look: the agent inside Claude Design composes named parts and steps instead of guessing values, so a page drawn next month matches one drawn today. Built from an existing product, it is also where the product's inconsistencies are settled: each unified value is a row of `Unifications`, and the product follows once pages drawn with it are pulled.

  放在该节现有两句之前。

- `references/template-project-claude-md.md` `## Files`"It loads no product code"：给 Claude Design 里那个 agent 的这条规则没有附理由。提交 cb45a515 删掉了"a page drawn from product code would make element parity compare the product with itself"。spec #445 第三个问题记录过真实事故：生产 CSS 被抄进 design page，带来 18 条编辑器点不中的选择器，其中一条把指标数值缩成了 13px 灰字。没有理由的规则，碰到"用产品的样式表省事"这种诱惑时最容易被让掉。
  > It loads no product code: its look comes from the design system and its own markup. A page that runs the product's own code would make acceptance compare the product with itself, and product stylesheets bring in selectors the editor cannot reach.

- `references/edit-pages.md` `## Next`"nothing checks them before that"：这句可以读成"所以现在自己去查"，也可以读成"所以不必查"。原意（提交 f70b9224）是约定只在 pull 时检查。agent 不知道 pull 很便宜、可以反复跑（spec #445 用户故事 15），就可能逐页手工核对约定。
  > A pull is two MCP calls and one command, and its report is the convention check; when you doubt the pages hold the conventions, pull and read the report rather than reading pages by hand.

- `references/edit-pages.md` `## Sign-off`（优先级低）：只写了"never by Claude Design's "Handoff to Claude Code" export"，删掉了理由（ADR 0029 里还在）。用户提议用这个导出功能时，agent 解释不出为什么不行。
  > …never by Claude Design's "Handoff to Claude Code" export, which writes a README that does not follow later design changes and would be a third account of the design beside the pages and the screen contract.

与 `SKILL-SET-REVIEW.md` 的冲突：它在 `### Redundancy and bloat` 的 Sediment 表里把"the maintainer's reason for a design"归到 ADR。上面第三、四条被删的句子，前几轮正是按这一行删的；但它们是给干活的 agent（本会话、Claude Design 里的 agent）做取舍用的理由，属于同一段里"a reason the agent needs to decide an edge case"那种例外。本任务书以"灵魂"为准，建议恢复。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
|---|---|---|---|
| C1 | `references/draw.md` `## When this session draws` 第 1–4 步 | 四步编号流程里大部分是 MCP 工具的调用方法（见 A1），真正需要判断的只有"照项目 `CLAUDE.md`"、"不覆盖用户刚在编辑器里的改动"、"有 prototype winner 就以它为参照"三点，却和工具调用混在同一个层级 | 目标 + 两个判断点 + 完成标准。草稿："Only when the user asks this session to write or change pages. The Claude Design MCP tools say how to load the design prompt, plan writes and preview. Beyond them: follow the project `CLAUDE.md`; when a prototype's winning variant exists, it is the reference for layout and interaction; a large generated file, such as a product's example data, stays in the repository for the agent inside Claude Design to read through its GitHub connection. Done when each changed page renders with no console error, missing file or blank render, and the user has its `open_url`." |
| C2 | `references/edit-pages.md` `## Create the project` 第 1–6 步 | 真正有先后依赖的只有：项目先建出来；第 2–5 步所有写入放在同一个 `finalize_plan` 里，让用户只批准一次；链接最后给出。其余步骤逐条列出的是"项目里该有哪些文件"，这是一个终态，不是一串动作 | 改写成终态清单 + 一个判断点。草稿："Before the user says `开始`, the project holds: `CLAUDE.md` (the template block, unchanged); `state-list.md` when a state list exists; `ui-ids.md` when the product already carries `data-ui` ids; a fresh `_ds/<folder>/` when bound; and a first `task.md` (one `Component · ` page per region, the reference named by branch and repository path, one region first). Declare all of them in one `finalize_plan`, so the user approves once; `CLAUDE.md` is a reserved path and needs that token." 保留 `ui-ids.md` 的收集方法和"miss elements that carry no text"那个坑 |
| — | `references/pull.md` `## Steps`、`## A contract child answered by this pull`；`references/design-system.md` `## Who builds it` | 查过，不死板 | `pull.md` 的顺序由脚本决定（先拿 `serve_url` 再跑命令，读完报告再提交）；contract child 那段的顺序由 `dispatch` 的事件机制决定（先 `route` 再 `resume`，标签移动夹在中间）；design system 那五步是跨两个 agent 加用户的交接顺序。都应保留 |

## 脚本

- `pull_design.py` 的 `pages_from_list_files`（第 211–239 行），加上 `parse_args` 的第二种位置参数形式（第 1629–1637 行）、模块 docstring 第 10、13–14 行，以及 `run` 里"lists 0 `.dc.html` pages"那个拒绝（第 1654–1659 行，只有走 JSON 形式才到得了，因为 `--pages` 的 `nargs="+"` 至少要一个）：都是**死代码**。"A saved `list_files` result may stand in for `--pages`"这句在提交 4372d901 从 `pull.md` 删掉后，技能文本里就再没有入口；agent 手上的 `list_files` 结果本来在模型上下文里，专门存成文件再传进来是绕远路。只剩一个测试在用（`test_pull_design.py` 第 352 行 `test_a_saved_list_files_result_gives_the_root_pages_and_nothing_else`）。删掉后由 `--pages` 承担，剩余风险：无。约 45 行，那个测试一起删。
- package `README.md` 里 `## State list` 的保留逻辑：`state_list_section(target / "README.md")`（第 1012–1018、1530 行）、`HandoffPackage.state_list`、`scenes_from_pages` / `render_until_settled` 的 `state_list` 参数、`write_readme` 第 1007–1008 行。这是**死路径**：它来自 #473 时期 state list 写在 package README 里的设计（提交 583872cb），现在 state list 在 leaf `README.md` 或 `prototypes/<effort>/README.md`，由 `--state-list` 读入。实际仓库里的 package README（`prototypes/task-board/claude-design/README.md`）没有这一节，`~/agentflow` 的 package 没有用 pull 拉过。有两个测试护着它（第 465、884 行）。删掉后剩余风险：有人手工往脚本生成的 README 里写 state list，会被下次 pull 冲掉，但这本来就不是 state list 该放的地方。约 20 行。
- `previous_paths` 兼容 `{"path": …}` 行（第 1507–1508、1519 行）：这种形状只出现在提交 8b089dff 的清单里，从 1c79064f 起所有提交过的 `design-manifest.json` 都是字符串列表（逐个版本查过），磁盘上也没有别的 package 带清单。**过度防御**，删掉约 2 行。
- 读"本脚本刚写下的文件"时的容错分支：`page_root` 和 `app_page_wiring` 在 `OSError/UnicodeError` 时返回 `None`（第 587–589、624–625 行），`wiring_changes` 因此多出"页面无法读取，接线未核对"一行（第 638–640 行），`selector_audit` 的 `OSError` 分支（第 1099–1102 行）也是这类。这些文件是本次运行刚下载到自己临时目录的，或者刚被 `design_pages` 成功解析过；正常输入到不了这些分支。前后也不一致：`off_scale_values` 读同样的文件就没有加容错。删掉后由 `main()` 的通用异常处理承担（退出 2，目标目录不变）。**过度防御**，约 12 行。`pull.md` 第 3 步里"a line saying `未核对`"那句仍然需要，因为"state list 未给出"、"screen contract 未给出"、"页面没有自己的样式"这些 `未核对` 是真实会出现的。
- `strip_injected_head`（第 306–339 行）有两条路径：一条匹配 2026-09-21 实测的注入形状，一条是通用循环。两者只差在要不要去掉注入之后那个换行，可以合成一条（通用循环 + 去掉紧跟的一个换行），约减 10 行。优先级低；后面那个"`data-omelette-injected` 仍在页面里"的拒绝要保留，它保证拉下来的字节就是项目里存的页面。
- `design_pages` 只按文件名跳过 `overview.dc.html`（第 656 行），而 `scenes_from_pages` 会把**任何**带 `scene` prop 的页面变成 scene；模板则说不带 `Component · ` / `App · ` 前缀的页面"are not pulled into acceptance"（`template-project-claude-md.md` 第 17 行）。`page_inventory` 里用的是前缀规则（第 1070–1076 行）。两套规则不一致：用户在 Claude Design 里复制一个 Component 页当草稿、改成不带前缀的名字，它的 scene 就会进 `scenes.json`。没有观察到实际发生。建议 scene 只从带前缀的页面生成，去掉 Overview 这个特例。
- `覆盖` 一节在真实报告里太吵：`prototypes/task-board/claude-design/pull-report.md` 共 131 行，其中 109 行是"带文字但没有 `data-ui` id"（`span: agent`、`span: ·` 这类标签，同一组在每个 scene 重复一遍）。state list 缺状态这类真正要紧的行会被淹没。建议按页面去重，每页一行，写数量和不重复的标签。这和 B 的第二条草稿配套。
- `check_editable_selectors.py` 把 `App · ` 页里的 `[data-ui="任务列表.root"]` 报成"attribute selector"（真实报告 4 行）。可是模板本来就要求 `App · ` 页用自己的样式控制每个区域怎么填满它的位置（`template-project-claude-md.md` 第 15 行），按 `data-ui` 选中区域是最自然的写法。这类行已经被定为"information"，不会误导 agent，只是噪声。可以豁免 `[data-ui…]` 选择器，也可以让模板建议用类名。优先级低。
- `check_editable_selectors.py` 的命令行入口 `main()`（第 87–108 行）和 docstring 里的 Usage：`pull_design.py` 只导入 `selectors` 和 `why`；技能文本在提交 4372d901 之后不再让 agent 单独运行它；`~/agentflow` 里也已经没有引用。只剩 `test_check_editable_selectors.py` 通过子进程在用。可选：删掉 `main`，测试直接调 `why()`，约减 25 行；留着当调试入口也无害。
- 查过、建议保留的：`install()` 先备份再原子替换（第 1582–1605 行），保护的是 package 旁边没提交的文件；`safe_path` 保护的是删除操作不越出临时目录（第 1543–1547 行）；`fetch` 重试三次，头部注释记录了 2026-09-21 实际失败过一次；`render_until_settled` 的五轮渲染是为了把运行时才请求的数据文件拉全。`vendor_urls` 里的"filename 重复"检查（第 527–532 行）是守不会发生的情况，但只有 6 行，不值得动。

## 与其他技能的重复或交接问题

- 页面根元素 / `scene` prop / 可点控件没有 id：这三项检查 `pull_design.py`（`_RootParser` 第 561–589 行、`coverage_lines`、`render_scenes` 的 `controlsMissing`）和 `mmw-v2/skills/write-screen-contract/scripts/lint_screen_contract.py`（`handoff_page_errors` 第 297–321 行，根元素解析器在第 251–268 行）各写了一套，解析代码几乎一样。两个时刻都该保留：pull 时最早，还能回 Claude Design 改；lint 是写合同前的硬关口。重复的是**代码**。建议把根元素和 `data-props` 的解析放进两边都已经加载的 `ui-acceptance/scripts/design_render.py`，只留一份。
- `references/pull.md` `## A contract child answered by this pull` 和 `mmw-v2/skills/dispatch/references/night.md` 第 86 行的 `child.opened` of kind `contract` 一行，是同一件事的两半：夜里挂起，白天拉回后收口。这是交接，不是重复，两边都留。
- `references/pull.md` `## Reached from here` 的 `只改外观或文案` 一条带着 `dispatch` 的生命周期知识（`reverify`、`summary`、`finish` 之后 base branch 就没了）。本会话不是夜里的主 agent，只能从这里读到这些，应留在这里；`dispatch` 那边不必再写。
- 措辞：`pull_design.py` 里的类名 `HandoffPackage`，以及实际提交的 `pull-report.md` / package `README.md` 里的"handoff package"，都是 `docs/contexts/ui-acceptance/CONTEXT.md` 标为 _Avoid_ 的旧名（现行代码输出的已经是"design package"，仓库里的文件是旧版本生成的，下次 pull 会自动更新）。只记录，不影响行为。

## 没查到的

- 我没有接 Claude Design 项目，所以无法确认 `create_project` 绑定 design system 时会不会立即生成新的 `_ds/<folder>/`。如果会，`edit-pages.md` 第 5 步"refresh its `_ds/<folder>/` copy first"在新建项目时就是空操作；我没有把它列成发现。
- `ui-ids.md`、`design-system.md` 里"已有产品"那条分支的真实使用次数：tracker 和 git 里只看到任务板试点（#541、#553，提交 f8f84f18"redrawn on the unified design system"），看不到 `ui-ids.md` 被写过。A8 的"暂不改"就是基于这一点。
- `pull_design.py` 第 1–1728 行全部读过；测试文件 `test_pull_design.py` 只读了与上面结论有关的片段（第 330–380 行和几处 grep 结果），没有通读；测试套件没有跑（任务书不要求）。
- `design_render.py`（ui-acceptance）只看了 `pull_design.py` 调用它的接口名，没读实现，所以不判断它与本技能之间有没有重复逻辑。
