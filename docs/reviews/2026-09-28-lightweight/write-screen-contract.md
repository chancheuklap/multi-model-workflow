# write-screen-contract

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：开头一段（设计包管外观、合同管行为）、第 6 步 gap list 的"这是用户的判断，量级是几条不是几十条"，都是很好的判断句。缺的是后果：写合同的 agent 不知道每一行会被 worker 原样造出来、被审查和 boundary test 原样判；于是在决定没说话的地方，它会补一个看起来合理的值。另外，格式参考把 lint 的判定复述了一整列，这一列可删。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` 开头段之后 | Every row becomes a requirement a ticket owns: workers build from the row, not from the decisions behind it, and the review and the boundary test hold them to its four columns. A row that lints clean but rests on no decision is built and tested exactly as written. So where the decisions and the design are both silent about a column (most often `on_failure`), do not fill in the plausible default: ask the user and cite the answer as `conversation <YYYY-MM-DD>`, or put the question on the gap list. | 写到一个没人定过的失败提示时：没有它，agent 填一个 toast；有了它，去问，或者进 gap list。本仓 `docs/specs/task-board/screen-contract.yaml` 的 `backend_without_ui` 里 "conversation 2026-09-21: 本机只有一个人写配置…" 就是这种做法的真实例子。 |
| I2 | `### 4. Write each cross-component row from the App-page wiring` 开头 | A behaviour that crosses regions belongs to no Component page's ticket: the App row is the only place it gets an owner and a boundary test, so a link you leave out here is one nobody builds. | 没有它，agent 会以为"两个组件各自做好，联动自然成立"而漏写。`verify-ticket` 的 lint 要求每个 cross-component row 都有 boundary criterion，这一行是它唯一的来源。 |
| I3 | `### 5. Reverse sweep` 正文，整段替换（标题原样保留：`to-spec` 按标题名回指） | The forward pass finds only what the design draws. This pass finds what the backend decided that the design forgot, while the user is still here to settle it. The lint sweeps `openapi.json` for you; you sweep the decisions: every decision line an end user could notice (a value shown, a state reached, a failure seen) lands in a row's `source`, becomes a `backend-only` row, or gets one line under `backend_without_ui` saying why the interface has no place for it. | 原文让 agent 手工再核一遍 lint 已经做的 `openapi.json` 那一半，而对真正要判断的那一半（哪些决定是用户看得见的）没给标准。改后分工清楚，并说明这一步为什么要在用户还在场时做。 |
| I4 | `## Re-runs` "Row ids are never renumbered or reused." 之后 | Tickets, boundary tests and closed reviews name rows by id, so a reused or renumbered id silently points old evidence at a new behaviour. | 重跑时出于整洁想重排 id：有了理由，agent 会保留旧 id。 |
| I5 | `## Steps` 标题下第一句 | Steps 2 to 5 are four passes over the same rows; go back and forth between them as the rows fill. Step 1 comes first because the skeleton needs its keys, and step 7 comes last because nothing reaches `docs/specs/` until the user has settled the gap list. | 把真依赖的顺序（1 在前、7 在后）和可以来回迭代的部分（2–5）分开，agent 不必做完一步才敢回头改上一步。 |
| I6 | `## Done when` 整段替换 | `screen-contract.yaml` lints clean, the decisions have been swept as **Reverse sweep** says, and the user has answered every entry of the gap list. | 原文逐项列出 lint 已判定的条件，却没列 lint 判定不了的那一项（决定是否扫全）。 |

### 删除

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | `references/screen-contract-format.md` `## Top level` 末段 "The lint checks these top-level keys: …" | 删 | 上方 YAML 清单已列出允许的键；多余键 lint 报错。这段还比脚本多承诺了一项（`retired_ids` 条目的键）。 |
| D2 | 两张表的 `Lint` 列 | 删这一列；`trigger`、`viewports`、`shows` 三格里 `Rule` 列没有的规则先并入 `Rule` | 每格都在复述 lint 的判定，lint 在违规那一刻给出同样的内容和改法。 |
| D3 | 格式参考 `## A cross-component row` 第二段，与 `SKILL.md` 第 4 步第二段前半 | 格式参考那段删；`SKILL.md` 只留判断："When an App page's wiring passes nothing from one region to another, that is a finding for the user: put it in the gap list of step 6." | 两处几乎逐句相同；前半是在复述 lint 的覆盖规则。 |
| D4 | `SKILL.md` `## Decision sources` 整节 | 删；"cite the decision ticket first, and the earlier spec for what no decision ticket covers" 并入格式参考 `source` 列的 `Rule` | 第一句与 `source` 列重复；对话来源 `## Inputs` 已说。 |
| D5 | `### 1.` "`extract_skeleton.py` reads `locale`, `viewports` and each page's own `viewports`; the rest establishes…" 与 "On a re-run the file is already there: keep those keys and extract again." | 删 | 前者复述脚本，缺键时脚本会拒绝；后者与 `## Re-runs` 重复。 |
| D6 | `### 7.` 第 1 条括号 "(a contract still in `<scratch>` finds `baselines.look` and `.mmw/target.json` through the directory the lint runs in)" | 删 | 解释实现细节；agent 只需 "from inside the repository"。 |
| D7 | 格式参考 "`pages` and `scenes` are filled at design time…" 与 "`baselines.look` is the design package directory."；桌面示例引导句里 "The lint prints `UNVERIFIED`…" 半句 | 删 | 与 `SKILL.md` 第 2、3 步、YAML 注释、`calls` 列重复。 |
| D8 | `## Inputs` 第二条 "a logic prototype's contract file" | 删这几个字 | `prototype` 的 `LOGIC.md` 没有这种产物（`prototype` 调查员发现）。 |
| D9 | 脚本 S1：`lint_screen_contract.py` 的 story 覆盖警告（`latest_story_out()`、`# -- story coverage` 一段、`IMPL_PNG`）及其测试 | 删 | 在合同目录找截图，而截图从不写在那里；两个仓库从未有过这种目录；页面覆盖由 `verify-ticket` 的 lint 负责。 |
| D10 | 脚本 S2：`.mmw/target.json` 检查（`target_config_mod()`、`target_file_problem()`、`# -- target runtime` 一段，以及只为它存在的 `--tools` 解析）及其测试 | 删 | drive-target 时期的遗留。写合同的 agent 对这条警告无事可做；`.mmw/target.json` 缺什么，由 `to-spec` 的 **How a test arrives at a state** 引用 `target_config.py --check` 负责。删后这个 lint 不再依赖 `ui-acceptance`。 |
| D11 | 脚本 S3：两个脚本的 `uv` 重启引导（约 40 行） | `SKILL.md` 第 1、7 步的命令改为 `uv run <scripts>/extract_skeleton.py …`、`uv run <scripts>/lint_screen_contract.py …`（这种写法会读 PEP 723 依赖块，调查员已在 uv 0.12.15 实测）；`dump_openapi.py` 要导入产品自己的模块，仍用 `uv run python`；然后删两段引导 | 引导只是为了兼容一种写法；换写法后它没有用处。 |
| D12 | 脚本 S4：`skeleton_scene_pages()` 从 `table` 推导的回退分支及其测试 | 删 | 每次运行都重新生成 skeleton，旧格式到不了 lint；回退也不完全等价。 |
| D13 | 过时注释：`repo_root()` 的 "(step 6 keeps it there…)"、lint 头部的 "the form a ticket CHECK writes" | 改正 | 注释与现状不符。 |

### 不采纳

- A10（删 `### 3.` 的 `source` 条前半句）：它列在 "the ones people get wrong" 之下，是 agent 填这一列时正要读的提醒，只多 20 词。
- 已删字段的迁移提示（`REMOVED_TOP_KEYS` 等）：agentflow 的合同仍带三个旧键，正常输入会走到，保留。

## 结论

体量：`mmw-v2/skills/write-screen-contract/SKILL.md` 1,827 词，`references/screen-contract-format.md` 2,304 词，合计约 4,130 词；脚本 1,022 行（`scripts/lint_screen_contract.py` 728、`scripts/extract_skeleton.py` 266、`scripts/dump_openapi.py` 28）。文本整体是健康的：开头一段把"设计包管外观和原文、屏幕合同管调用和取值"这条分工讲清楚了，第 6 步把"哪一件事归用户判断"讲清楚了，这两处是技能的灵魂，而且都还在。主要问题不在文字啰嗦，而在三处：格式参考里每张表都有一列复述 lint 做了什么；lint 脚本里留着两块在现在的流程里走不到或不归它管的代码（story 覆盖警告、`.mmw/target.json` 检查，连带整套 `--tools` 查找）；以及文本缺了一句话告诉 agent"一行写错会被下游原样造出来"。估计文本可删约 500 词、补约 180 词（净减约 320 词），脚本可删约 115 行（若连 `uv` 重启引导一起去掉，约 155 行），不丢功能。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
|---|---|---|---|---|---|
| A1 | `references/screen-contract-format.md` `## Top level` 末段 "The lint checks these top-level keys: …"（第 46 行） | 1、6 | 上方 YAML 清单已经列出每个位置允许的键；lint 对多余键报 `<key> is not a contract field`，报错本身就告诉 agent 怎么改。这段还说 "a `retired_ids` entry (only `id` and `note`)" 会被查，但 `lint_screen_contract.py` 的 `lint()` 只查 `retired_ids` 条目里的 `page`、`trigger` 两个旧键，不查其余未知键，也接受裸字符串条目（`retired_entries` 把字符串转成 `{"id": e}`）。文字比脚本多承诺了一项 | 键的集合由 YAML 清单和两张表定义；多余键由 lint 报错。无剩余风险，且顺带去掉一处不实描述 | 整段删除（约 95 词） |
| A2 | `references/screen-contract-format.md` 两张表的 `Lint` 列（`## Pages, scenes, viewports, locale, states, retired_ids` 和 `## Column rules`） | 1 | 每一格都在复述 `lint_screen_contract.py` 的判定（合计 250 词）；lint 的报错信息在违规那一刻给出同样内容和改法 | lint 的报错信息。剩余风险：agent 多跑一两轮 lint 才改对，lint 离线、几秒完成。需先把三格里 `Rule` 列没有的规则挪进 `Rule`：`trigger` 的 "every skeleton control that is clickable or editable has ≥1 row"、`viewports` 的断点来源 "any `.css` in the package (including `_ds/`) or a page's `<style>` block"、`shows` 的 "no digits outside `{…}`" | 删 `Lint` 列，三条规则并入 `Rule`（净减约 200 词） |
| A3 | `references/screen-contract-format.md` `## A cross-component row` 第二段 "Every declared `App · ` page carries at least one such row…"（第 127 行） | 6 | 与 `SKILL.md` `### 4. Write each cross-component row from the App-page wiring` 第二段（第 74 行）几乎逐句相同 | 保留 `SKILL.md` 那份（agent 执行第 4 步时读的就是它），且只留判断部分："When an App page's wiring passes nothing from one region to another, that is a finding for the user: put it in the gap list of step 6." 前半句复述 lint 覆盖规则，lint 的 `page has no rows: App · <name>` 已说明 | 删格式参考里这一段；`SKILL.md` 第 74 行删前半句（合计约 70 词） |
| A4 | `SKILL.md` `## Decision sources` 整节（第 25 行） | 6 | 第一句 "A row's `source` may cite a wayfinder map's decision ticket, a spec section, an ADR, a domain document — or a conversation." 与格式参考 `source` 列的形状清单重复；`## Inputs` 第二条已经说了对话来源 | 格式参考 `source` 列。唯一独有的是引用顺序："cite the decision ticket first, and the earlier spec for what no decision ticket covers"，挪进格式参考 `source` 列的 `Rule` | 删整节标题和第一句，顺序规则并入 `source` 列（约 50 词） |
| A5 | `SKILL.md` `### 1. Declare the rendering inputs and extract the skeleton` 第一段后半 "`extract_skeleton.py` reads `locale`, `viewports` and each page's own `viewports`; the rest establishes…" 和 "On a re-run the file is already there: keep those keys and extract again."（第 38–41 行） | 1、6 | 前一句复述脚本读哪些键，缺键时 `extract_skeleton.py` 的 `load_conditions` 会拒绝并说明；后一句与 `## Re-runs` 第一句重复 | 脚本拒绝信息；`## Re-runs` | 删这两句（约 40 词） |
| A6 | `SKILL.md` `### 7. Lint and publish` 第 1 条括号 "(a contract still in `<scratch>` finds `baselines.look` and `.mmw/target.json` through the directory the lint runs in)"（第 95 行） | 1 | 解释 `repo_root()` 的实现；agent 要做的只是 "from inside the repository" | `repo_root()`。若 A-脚本 S2 执行，`.mmw/target.json` 这一半本就不存在 | 删括号（约 20 词） |
| A7 | `SKILL.md` `## Done when` "every scene of `scenes.json` has a declaration, every page has a `mount`, every `Component · ` page has a `component`" | 1 | 这三项和 "every row's `gap` is `aligned`" 都是 lint 的 error（`scenes: no declaration`、`pages: … mount`、`names no component`、`gap … unresolved`），"lints clean" 已包含 | lint | 改写见 C2 |
| A8 | `references/screen-contract-format.md` "`pages` and `scenes` are filled at design time…"（第 62 行）、"`baselines.look` is the design package directory."（第 64 行） | 6 | 前者与 `SKILL.md` 第 2、3 步重复；后者与 YAML 清单里 `look:` 的注释重复 | `SKILL.md` 第 2、3 步；YAML 注释 | 删两句（约 30 词） |
| A9 | `references/screen-contract-format.md` `## A row` 桌面示例的引导句 "The lint prints `UNVERIFIED` (no machine-readable source) and does not fail the run"（第 88 行） | 6 | 与 `calls` 列的规则重复 | `calls` 列 | 删这半句（约 15 词） |
| A10 | `SKILL.md` `### 3. Fill the behaviour columns…` 的 `source` 条 "cite the Implementation Decisions subsection that carries a story's conclusion, not the story." | 6 | 同一规则在格式参考 `source` 列（带理由 "A user story … is an audit trail no worker ever reads"）和 lint 的警告文字里各有一份，共三份 | 格式参考 `source` 列 + lint 警告。本条后半 "Existing code (`code:<path>`) is a last resort, and a row whose sources are all `code:` and README is a `design-only` candidate: check the decisions again before marking it." 是判断点，保留 | 删这一句（约 20 词）。低优先级：它在 "the ones people get wrong" 名下，若用户认为值得在 SKILL.md 再提醒，可不动 |

## B. 灵魂

### 保留，勿删

- `SKILL.md` 开头段 "A design package says what the interface looks like and what it says. … every downstream skill reads the two by that split."：整个技能存在的理由，也是下游 `to-spec`、`implement`、`code-review` 都依赖的分工。
- `SKILL.md` `## Inputs` "It is a read-only **baseline for look and copy**." 以及手写 `openapi.json` 那句 "describing exactly the routes, methods, fields and status codes its routing code implements"：告诉 agent 设计包不能改、手写接口清单要照实写而不是照理想写。
- `SKILL.md` `### 2.` "`mount` is your declaration, not a derivation: a page holds several components' rows, and the one with most rows can be a shared control borrowed from another page."：带理由的判断点，没有它 agent 会按行数最多的组件推导 mount。
- `SKILL.md` `### 2.` 两条 "A disabled state is a row. The end user sees the control…" 和 "A state the design package never shows … is still a row when the backend decisions reach it … so the gap in the design package is on record."：说明行是按用户能遇到的状态记，而不是按设计画了什么记。
- `SKILL.md` `### 3.` `shows` 条 "The literals in the page's data file under `data/` are seed data for tests, not copy, and so are their **counts**"：防止把样例数据当成产品文案，带理由。
- `SKILL.md` `### 3.` "Where an operation under `proposed_operations` is new or changed and other products share this backend, say so in the run's notes, so the spec carries it."：唯一提醒 agent 这份文件的影响可能超出本产品的一句。
- `SKILL.md` `### 6. Write the gap list and stop for the user` 全节，尤其 "this is the one judgement in this skill that is theirs, and it is a grilling, not a form. Expect a handful of entries, not dozens; dozens means a decision was skipped upstream" 和 "Two things a gap list does not carry…"：划清 agent 与用户的决策边界，并给出判断上游是否漏决定的量级标准。真实运行印证了这个量级：#554 的关票评论记录 68 行合同的 gap list 只有两条，都由用户裁决。注意 `to-spec` 的 `SKILL.md` 按标题名 **Reverse sweep** 和 **Write the gap list and stop for the user** 回指这里，改写时两个标题必须保留原文。
- `references/screen-contract-format.md` 开头 "The control axis and these declarations cannot be derived from each other — a page holds many rows, a row is visible on many scenes — so both are written, and the lint holds them to each other."：解释为什么要写两套声明，防止 agent 省掉一套。
- `references/screen-contract-format.md` "A server-rendered product and a desktop product use the same keys. … neither is a default the other must copy."：防止 agent 把 HTTP 示例当成桌面产品的默认写法。
- `references/screen-contract-format.md` `viewports` 格 "A viewport equal to a media-query breakpoint … compares two reflows and verifies nothing."、`scenes.<name>.input` 格 "The story adapter feeds the product component from that same merged value."、`on_failure` 格 "The four-column boundary test of the ui-acceptance skill reads this column."：这三句各自说明一列的后果（谁读它、错了会怎样），是 `SKILL-SET-REVIEW.md` `### Redundancy and bloat` "These stay" 所说的"agent 判断边界情况所需的理由"。
- `SKILL.md` `## Resolve <scripts> once` 的 "The path differs by machine and by host." 与 "Some hosts refuse `uv run … $VAR`."：防止已知误用（写死路径、用变量传路径）。

### 缺口与补充草稿

- `SKILL.md` 开头段之后：缺"做错的后果"。现在 agent 知道这份文件被谁读（格式参考首句列了读者），但不知道读者怎么用它：每一行会成为某张票拥有的需求，worker 只读合同行和 spec，不读原始决定；`code-review` 的 Spec 轴按行的 `calls` 判 `Missing` 并阻止关票；boundary test 断言四列。所以一行措辞通顺、lint 通过、但没有真实决定支撑的行，会被原样造出来、原样测过。没有这句，agent 容易把"lint 清零"当成完成，在决定沉默处按常理补一个看似合理的值（最常见的是 `on_failure` 的 toast）。
  > Every row becomes a requirement a ticket owns. Workers build from the row, not from the decisions behind it, and the review and the boundary test hold them to its four columns. A row that lints clean but rests on no decision is built and tested exactly as written, so where the decisions and the design are both silent about a column (most often `on_failure`), do not fill in the plausible default: ask the user and cite the answer as `conversation <YYYY-MM-DD>`, or put the question on the gap list.

  依据：`docs/specs/task-board/screen-contract.yaml` 的 `backend_without_ui` 里有一条 "conversation 2026-09-21: 本机只有一个人写配置，锁冲突不会发生，不为它设计提示"，说明真实运行里正确的做法就是问用户再引用对话；草稿把这个做法写成明确的判断点。

- `SKILL.md` `### 4. Write each cross-component row from the App-page wiring` 开头：只说"每处 A 影响 B 就写一行"，没说为什么。缺的是：跨区域的联动不属于任何一个 `Component · ` 页的票，App 行是它唯一能拿到负责人和 boundary 测试的地方（`verify-ticket` 的 `references/linting.md` 要求每个 cross-component row 都有 boundary criterion）。不知道这点，agent 会把联动当成"组件各自做好就自然成立"而漏写。
  > A behaviour that crosses regions belongs to no Component page's ticket. The app row is the only place it gets an owner and a boundary test; a link you leave out here is one nobody builds.

- `SKILL.md` `### 5. Reverse sweep`：只给了步骤，没给目的。缺的是：从控件出发的正向填写只能找到设计画出来的东西；反向扫是为了找出后端决定了、但设计漏掉的行为，否则这些缺口会在夜里由 worker 发现，那时已经没有人能拍板。草稿见 C1。

- `## Re-runs` "Row ids are never renumbered or reused."：只有规则没有理由。票的 `## Read first` 按 id 引用行（`screen-contract.yaml rows: a.b, a.c`），已关的票、boundary 测试和评审记录都按 id 指向行为；复用 id 会让旧证据指向新行为。没有理由，agent 在重跑时容易出于整洁把 id 重排。
  > Tickets, boundary tests and closed reviews name rows by id, so a reused or renumbered id silently points old evidence at a new behaviour.

- 前几轮删掉的内容：查了 `git log -p --since=2026-09-20` 对 `SKILL.md` 和 `references/` 的全部删行。删掉的"没有 map 时在一个会话里跑完 prototype 到合同"已由 `mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md` 第 22 行承担；删掉的"用户不在场时只写 gap list 并停下"对应的场景（夜里跑 alignment ticket）在现流程中不存在，alignment ticket 是 `wayfinder` 的 `grilling` 票，与用户一起做。没有找到值得恢复的灵魂段落。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
|---|---|---|---|
| C1 | `SKILL.md` `### 5. Reverse sweep` | 把两件性质不同的事写成一个手工步骤："every operation in `openapi.json` … lands in at least one row's `source` or `calls`"。其中 `openapi.json` 这一半 lint 已经机械完成（`reverse sweep: <METHOD> <path> has no row…` 是 error）；真正要 agent 判断的是另一半：哪些决定行是用户能观察到的。现在的写法让 agent 手工核对一遍脚本会核对的东西，而对判断那一半没有给任何标准 | 保留标题原文（`to-spec` 按名回指）。正文改成目的 + 分工 + 判断点：<br>> The forward pass finds only what the design draws. This pass finds what the backend decided that the design forgot, while the user is still here to settle it. The lint sweeps `openapi.json` for you; you sweep the decisions: every decision line an end user could notice (a value shown, a state reached, a failure seen) lands in a row's `source`, becomes a `backend-only` row, or gets one line under `backend_without_ui` saying why the interface has no place for it. |
| C2 | `SKILL.md` `## Done when` | 逐项列出 lint 已经判定的条件（见 A7），却没有列出 lint 判定不了、只有 agent 能保证的条件 | > `screen-contract.yaml` lints clean, the decisions have been swept as **Reverse sweep** says, and the user has answered every entry of the gap list. |
| C3 | `SKILL.md` `## Steps` 第 2–5 步的编号 | 第 1 步（先写 `locale`、`viewports`、页面自己的 `viewports`，`extract_skeleton.py` 要读）、第 6 步（用户拍板在前）、第 7 步（lint 清零后才复制到 `docs/specs/`）的顺序是真依赖，必须留。第 2–5 步其实是同一件事（填行）的四个视角，实际工作中会来回迭代；编号让人以为必须按序做完一步再做下一步。这一条影响小 | 编号可以保留（`to-spec` 引用的是标题文字不是编号），在 `## Steps` 下加一句：<br>> Steps 2 to 5 are four passes over the same rows; go back and forth between them as the rows fill. Step 1 comes first because the skeleton needs its keys, and step 7 comes last because nothing reaches `docs/specs/` until the user has settled the gap list. |

## 脚本

- **S1 story 覆盖警告，现在的流程走不到**（`scripts/lint_screen_contract.py` 的 `latest_story_out()`、`lint_declarations()` 里 `# -- story coverage` 一段、常量 `IMPL_PNG`，约 34 行）。它在合同所在目录下找 `media/*-impl.png`。但 `story-parity.py` 的 `--out` 默认是当前目录下的 `./story-shots`（`mmw-v2/skills/ui-acceptance/scripts/story-parity.py` 第 510 行），`implement` 的 `references/writing-interface-code.md` 让 `--out` 用 `mktemp` 目录；没有任何文档让人把 `--out` 放进 `docs/specs/<effort>/`。本仓 `docs/specs/` 和 `~/agentflow/docs/specs/` 下都没有 `media` 目录。它加于 #221（2026-09-08，align-screens 时期），当时的文本也描述过它，`SKILL.md` 里的描述已在提交 `4372d901` 删掉，代码留下了。另外它在写合同时跑，此时产品还不存在。四问：没触发过；正常输入走不到；前提（`--out` 在合同目录下）不成立；删掉后，页面的 story 覆盖由 `verify-ticket` 的 lint 负责（`references/linting.md` 第 31 行：每个被认领的 mount 都必须出现在一条 story criterion 里）。建议删除，连同测试 `test_story_coverage_warns_for_app_pages_too`。
- **S2 `.mmw/target.json` 检查，不归这个 lint 管**（`target_config_mod()`、`target_file_problem()`、`lint_declarations()` 里 `# -- target runtime` 一段，以及只为它存在的 `HERE`、`SIBLING_UA`、`TOOLS`、`tools_dirs()` 和 `main()` 里手写的 `--tools` 参数解析，约 77 行）。它来自 2026-09-06 的提交 `dcb44c52`（drive-target 时期，当时合同带 `target` 键，现在 `target` 已在 `REMOVED_TOP_KEYS` 里）。它能触发（新产品写合同时一定报 "no .mmw/target.json yet"），所以不算过度防御；问题是写合同的 agent 对这条警告无事可做，警告正文自己也说 "the contract ticket lands it"。同一件事由 `to-spec` 的 `SKILL.md` 第 96–97 行（Testing Decisions 的 **Test surfaces**，跑 `target_config.py --check`）负责。属类别 2 + 6。删掉后 lint 不再依赖 ui-acceptance，`--tools` 参数整体消失。剩余风险：无；写 spec 时照样会检查。需删的测试：`test_missing_target_json_is_a_warning`、`test_an_incomplete_target_json_is_a_warning`、`test_target_validate_exit_2_is_a_warning`、`test_the_lint_runs_without_tools`、`test_explicit_tools_forms_reach_main`。
- **S3 `uv` 重启引导，可以用命令写法代替**（`lint_screen_contract.py` 的 `_BOOTSTRAP`、`_ensure_yaml()`，约 24 行；`extract_skeleton.py` 的 `_BOOTSTRAP`、`_ensure_script_env()`，约 16 行）。它们存在是因为 `SKILL.md` 让 agent 用 `uv run python <scripts>/…` 调用，这种写法不读 PEP 723 依赖块。我在 scratchpad 里实测（uv 0.12.15，本仓目录下）：`uv run <script>.py` 会装上依赖块里的 `pyyaml` 并成功导入；`uv run python <script>.py` 报 `ModuleNotFoundError: No module named 'yaml'`。本技能集里 `story-parity.py` 已经用 `uv run <ui-acceptance scripts>/story-parity.py` 的写法。lint 文档字符串给的理由 "(the form a ticket CHECK writes)" 已过时：全集 grep 不到任何票的 `CHECK:` 调用 `lint_screen_contract.py`。改法：`SKILL.md` 第 1、7 步两条命令改成 `uv run <scripts>/extract_skeleton.py …`、`uv run <scripts>/lint_screen_contract.py …`（`dump_openapi.py` 要导入产品自己的模块，保持 `uv run python`），然后删两段引导。剩余风险：消费仓库里按旧下游说明（`mmw-v2/downstream-notes/492-skeleton-by-data-ui-id.md`）写的 `uv run python …` 调用会直接报缺 `yaml`，报错一眼可懂。这一条是可选项，收益 40 行。
- **S4 `skeleton_scene_pages()` 的回退分支**（`lint_screen_contract.py` 第 235–241 行）：`scene_pages` 缺失时改从 `table` 推导。`extract_skeleton.py` 每次都写 `scene_pages`，而 skeleton 每次运行都在新的 `<scratch>` 里重新生成（`## Re-runs` 也要求重跑第 1 步），旧格式 skeleton 到不了 lint。回退还不完全等价：一个场景若没有任何带文字或可交互的元素，就不会出现在推导结果里。建议只留 `scene_pages` 一条路，连同测试 `test_page_coverage_uses_table_fallback_without_scene_pages`（约 5 行）。
- **保留：已删字段的迁移提示**（`REMOVED_TOP_KEYS`、`REMOVED_PAGE_KEYS`、`removed_field()`、`retired_ids` 条目的 `page`/`trigger` 检查）。`~/agentflow/docs/specs/work-monitor/screen-contract.yaml` 仍带 `target`、`volatile_values`、`readme_dispositions` 三个旧键，正常输入能走到，不算过度防御。等 agentflow 的合同迁完后可以并入 `unknown_keys` 的通用报错。
- **记录：lint 与格式参考不一致**：见 A1。格式参考说 `retired_ids` 条目只允许 `id` 和 `note`，lint 不查且接受裸字符串（`lint()` 的 `retired_entries`、`retired_lines()` 的 "(no note)" 分支）。建议删文字的承诺（A1），不加代码。
- **记录：过时的注释**：`repo_root()` 文档字符串 "(step 6 keeps it there until every gap is aligned)"，现在是第 7 步复制；`lint_screen_contract.py` 头部的 "the form a ticket CHECK writes"（见 S3）。
- **小的重复，不建议改**：`extract_skeleton.py` 的 `load_driver()` 与 `lint_screen_contract.py` 的 `target_config_mod()` 各有两条几乎相同的报错分支（是否传了 `--tools`）；S2 执行后后者消失。`lint_screen_contract.py` 自己解析 `viewports`（`VIEWPORT` 正则），与 `design_render.py` 的 `parse_viewports()` 重复，但 lint 为此引入 ui-acceptance 依赖不划算。`extract_skeleton.py` 的 `--tools` 覆盖只有测试在用，但它是全集约定（`pull_design.py`、`dispatch.sh`、`verify-ticket.py` 都有），单改这里会失去一致性，不提。

## 与其他技能的重复或交接问题

- **设计页约定的检查做了两遍**：`lint_screen_contract.py` 的 `HandoffPageParser` / `handoff_page_errors()` 查三件事（可交互元素没有 `data-ui`、`Component · ` 页没有 `scene` prop、页面根元素没有 `data-ui`），`mmw-v2/skills/design-pages/scripts/pull_design.py` 在拉取报告里报同样三件事（报告行"可点或可输入却没有 `data-ui` id"、"没有 `scene` prop 的页面"、"页面根元素 … 没有 `data-ui` id"），其中找根元素的解析器 `_RootParser` 与 lint 的根元素逻辑几乎逐行相同。`mmw-v2/skills/design-pages/references/edit-pages.md` 第 36 行明确把两者都当作检查者。该留哪边：拉取报告是修设计的时刻（问题回到 Claude Design），lint 是写合同时的阻断（缺 `data-ui` 的控件不会进 skeleton，行就会被静默漏掉）。两边都有用；建议保留两处检查，但把根元素解析器只留一份，放进两个脚本都已加载的 `mmw-v2/skills/ui-acceptance/scripts/design_render.py`（lint 目前不加载它，若 S2 执行后 lint 不再依赖 ui-acceptance，则保持现状、只记录）。
- **`.mmw/target.json`**：见 S2，留 `to-spec` 的 Testing Decisions 与 `ui-acceptance` 的 `target_config.py --check`，删本 lint 的那份。
- **story 覆盖**：见 S1，留 `verify-ticket` 的 lint。
- **浏览器安装那句**（`uv run --with playwright python -m playwright install chromium`）在本技能第 1 步和 `design-pages` 的 `references/pull.md` 第 2 条各有一份。两份分属不同时刻、可能在不同机器上执行，且本技能这句是因 #502（"agent instructions omit write-screen-contract's browser requirement"）才加的，两份都留。
- **标题被其他技能按名引用**：`mmw-v2/upstream/skills/engineering/to-spec/SKILL.md` 第 22 行引用 **Reverse sweep** 和 **Write the gap list and stop for the user**；`mmw-v2/skills/design-pages/references/pull.md` 第 40 行和 `to-spec` 的 `references/revising-a-spec.md` 第 9 行引用 **Re-runs**。任何改写都不能改这三个标题。
- 与 `SKILL-SET-REVIEW.md` 的关系：本报告的删减建议都落在其 `### Redundancy and bloat` 的 Cache、Duplication、Over-defense 范围内；B 里的四段补充草稿属于它 "These stay" 所说的"agent 判断边界情况所需的理由"，这里没有发现与任务书冲突的地方。

## 没查到的

- 没有跑测试套件（任务书不要求）；S1–S4 删除后需要删改的测试名是从测试文件的函数名得出的，没有读每个测试的全文。
- `mmw-v2/skills/ui-acceptance/scripts/design_render.py`、`target_config.py`、`refusal.py` 只读了与本技能调用有关的函数签名和片段，没有通读。
- S1 的"走不到"依据是：全集文档中 `--out` 的写法、`story-parity.py` 的默认值、两个已知消费仓库的 `docs/specs/` 下没有 `media` 目录。没有查每一次历史运行的日志，也不知道是否还有第三个消费仓库。
- S3 的 `uv run <script>` 行为只在本机 uv 0.12.15 上实测过。
- `~/agentflow/docs/specs/work-monitor/screen-contract.yaml`（3,428 行）只看了顶层键和统计，没有逐行读；它是否已按 `494-screen-contract-format.md` 迁移、是否会再次被 lint，未核实。
- `docs/specs/task-board/screen-contract.yaml`（1,588 行）同样只看了顶层键、`states`、`backend_without_ui` 和 `app` 行的分布。
- tracker 上只读了 #221、#554、#574、#583。唯一一次在本仓完整跑过这个技能的记录是 #554（任务板的 alignment ticket）：68 行全部 aligned，lint 0 错误 5 条提示，gap list 两条由用户 2026-09-21 裁决。agentflow 的 #650 没有查。
