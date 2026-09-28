# diagram-design

## 定稿（主 agent 复核）

**判断**：上游正文的判断句大多很好，不删。要做的有三件：把 `e74e0140` 挪进 merge-note 的三句理由放回正文；修两处因"先嵌套、不拆图"改动而漏改的冲突；再补一句，防止客户品牌写进所有仓库共用的安装副本。

### 增加与修正

| # | 位置 | 最终文字或改法 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` §0 写明所用配色的那一句之后（恢复理由） | Name the one you used beside the deliverable, so a default-skinned diagram never reaches a branded context unannounced. | agent 知道为什么要写明配色，就不会省掉这一步。 |
| I2 | §0 "默认不停下来问品牌" 处（恢复理由） | Most diagrams are read once to understand something and never leave the room; stopping every one of them at a branding question costs more than it saves. | 给出默认值的理由；遇到正式对外的图，agent 能判断这时值得问。 |
| I3 | §7 "不拆图、先嵌套" 处（恢复理由） | A reader who has to hold two canvases in their head to see one system has lost the thing they came for. | 超预算时，agent 知道为什么先嵌套、不拆成两张。 |
| I4 | §0 客户品牌段末 | Keep the result out of the installed `style-guide.md`: this install is shared by every repository on the machine. Save it as a profile and bind this project with a `.diagram-design` marker (`references/profiles.md`). | 上游的品牌引导会把客户品牌写进安装副本，本机所有仓库共用这一份，品牌就会串到别的项目里。没有触发过，但正常使用能走到。 |
| I5 | 自检清单加一项 | Opened the rendered file and looked at every diagram in it? The checks above read the source; clipped text, crossing strokes and a picture that does not answer its question show only in the render. | 现有检查都只读源码，渲染后的问题只有打开看才发现。 |
| F1 | `SKILL.md` §6 rule 3 括号里的 "split"、`references/output-spec.md` §3 `faithful` "超过 24 个节点就拆" | 改为与本仓第 6 步一致的"先嵌套" | "超预算就拆图"改成"先嵌套"时漏改了这两处，现在两处规则直接冲突。 |
| F2 | 本仓"先嵌套"清单里的 `high-level` | 换成"有容器的图型"这一性质，并补上 Architecture 的 zone 写法 | `high-level` 是一个带参数的 Kubernetes 数据栈图型；选到它的 agent 会去读约 13k 词无关材料，还会向用户要参数。 |

### 不采纳

- 两处上游原文问题：单独列出，不为减字数改上游。

## 结论

技能目录 `mmw-v2/upstream-diagram-design/skills/diagram-design/` 正文约 96,200 词：`SKILL.md` 5,905 词（584 行，40,404 字节），56 个 reference 90,305 词；技能自带脚本 3,415 行（`scripts/` 下 4 个，全是上游原样）。本仓的改动很少：`SKILL.md` 比上游（squash 提交 `8a85636a`）多 228 词，`references/output-spec.md` 改了一句，加了一条 `repo-root` symlink，仓库根的 `scripts/verify-geometry.py` 加了约 60 行、测试加了 8 条。这些改动本身精简，没有历史注记，没有脚本能代替的复述，也没有过度防御；能删的只有约 30 词（一处重复的图型清单、默认路径那行说明里的四种改法）。主要问题有三个：(1) 前一轮减重（提交 `e74e0140`）把本仓加的三句"为什么"从正文挪进了 merge-note，恰好是 agent 做判断要用的理由，应当恢复；(2) 把"超预算就拆图"改成"先嵌套"时漏了几处：`SKILL.md` §6 rule 3 的括号里仍写着拆图，`output-spec.md` §3 `faithful` 的"超过 24 个节点就拆"和本仓改的第 6 步直接冲突；(3) "先嵌套"列出的四个图型里有 `high-level`，那是一个参数化的 Kubernetes 数据栈图型，会把 agent 引去读 3,849 词外加 9,524 词的图标库，还会让它向用户收集参数。一次普通调用（静态单图、项目里没有 marker）实际读 `SKILL.md` 5.9k、`style-guide.md` 2.7k、（很可能还有）`profiles.md` 2.2k、一份图型 reference（中位数 0.8k）和一个模板 0.3–1.7k，合计约 11–13k 词，约占全部正文的 12%；`SKILL.md` 除上面那条 `high-level` 以外，没有把 agent 引去读不需要的大文件。"灵魂"部分：上游自己的思想性段落（§1 Philosophy、§2 的"Would the reader learn more"、§11 的"An import is bounded by its source"等）都在，而且完整；本仓这一层的"灵魂"不完整，缺的就是被挪走的那三句理由，另外还缺一句"交付前打开渲染结果看一遍"。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
|---|---|---|---|---|---|
| A1 | `SKILL.md` §6 `### Mandatory connector rules` rule 3 末句 "If you find yourself stacking connectors, redesign the layout — … or the diagram is over budget (split into overview + detail)."（第 278 行） | 不属 1–6：本仓改拆图规则时漏改，与 §7 矛盾 | 这句从第一次 squash（`f23ee28b`）起就在，是上游原文。merge-note `mmw-v2/merge-notes/diagram-design.md` 说拆图规则只有"三处"（§1、§3、§7），漏了这一处。agent 在连线叠在一起时读到的是"拆图"，与 §7 本仓的"先嵌套、按层计预算"相反 | 不删功能，只改括号里的去向 | 括号改成 "(over budget: see §7)"；merge-note 把"三处"改成"四处"，并加一行记录 rule 3 |
| A2 | `references/output-spec.md` §3 `faithful` 条件 2 "If you can't route it without overlaps, you're over the real ceiling — split." 和条件 3 "**Above 24 nodes, split.** … Never ship a 40-node single canvas."；§6 Checklist "`faithful` above 9 nodes → zoned, and split above 24?"；`SKILL.md` §11 末段 "zoned above 9 nodes, split above 24" | 不属 1–6：同一文件里互相矛盾 | 本仓改的 `### Degrade ladder` 第 6 步 "Still over? Re-draw in a type that nests … split into overview + detail only when the source holds two independent questions" 同样适用于 `faithful`（它的上限是 24）。所以一份 30 个节点的 `faithful` 导入会读到两条相反的指令。merge-note 只把"各图型自己的上限"定为语法的物理极限，没有说 `faithful` 的 24 算不算 | 功能不丢；需要定一边 | 建议把 24 当成物理极限（上游的理由是 40 个节点的单张画布没法读，这与"全局性优先"并不冲突）：第 6 步句尾加 "(`faithful`'s 24-node ceiling in §3 still binds)"，merge-note 在"其余 55 个 reference"那段点名 `output-spec.md` §3 与 `SKILL.md` §11 属于物理极限 |
| A3 | "nested, layers, tree, high-level" 这份清单写了三遍：`SKILL.md` §3 Rules of thumb 第三条（第 130 行）、§7 `### Complexity budget` 末段（第 408 行）、`output-spec.md` 第 6 步（第 150 行） | 6 冗余 | 三处原文逐字相同 | §7 保留一份（它是完整规则，另外两处只是指向它） | §3 改成 "re-pick a type that nests (§7) and carry the whole subject on one canvas"；`output-spec.md` 第 6 步改成 "Re-draw in a type that nests (SKILL.md §7), with the budget binding per level."。清单本身的内容见 C1。约省 15 词 |

### 上游原文（单独列出：在 MMW 工作流里会让 agent 做错的）

| # | 位置 | 在 MMW 里会怎样做错 | 证据与可达性 | 建议 |
|---|---|---|---|---|
| U1 | `references/onboarding.md` 第 3 行 "rewrite `style-guide.md` so every future diagram inherits that skin"、第 160 行 "Write the new tokens to `style-guide.md`"；入口是本仓加的 `SKILL.md` §0 "When the artifact is going to a client … follow the selected method" | 在 MMW 里，"installed working copy" 是冻结的 git worktree `.worktrees/mmw-installed` 里一个受版本管理的文件，本机每个仓库共用它（根 `AGENTS.md` Gotchas："A skill directory is one symlink shared by every repository on the machine"）。onboarding 为一个客户写进去的品牌色，会变成本机所有仓库所有图的配色；而且下一次发布执行 `git -C .worktrees/mmw-installed checkout --detach main` 时，这个文件要么让 checkout 失败，要么被悄悄带着走 | 从没触发过：`~/.diagram-design` 不存在，`git -C .worktrees/mmw-installed status` 是干净的。但正常输入能走到：任何一张要送客户的图都会进这条路 | 在本仓自己写的 §0 客户段末尾加一句（草稿见 B 的缺口 4）。上游原文不改 |
| U2 | `SKILL.md` §2 "Quick unicode diagrams → use **wiretext**." | MMW 里没有叫 wiretext 的技能，agent 会找不到 | 影响很小：找不到时 agent 会回到"表格或一句话" | 不改 |

## B. 灵魂

### 保留，勿删

- `SKILL.md` §1 Philosophy 整节（"The highest-quality move is usually deletion." 到 "It's done when nothing can be removed."）：这是整份技能取舍的根据，§9 的 Remove test 只是它的操作形式。
- `SKILL.md` §2 "Before drawing, ask: *Would the reader learn more from this than from a well-written paragraph?* If no, don't draw."：`wait-what` 的 `VISUAL.md` 靠这句判断一页上放表格还是放图（merge-note `wait-what.md` 写明了这一点）。
- `SKILL.md` §5 Focal rule "If you're tempted to accent 4 things, you haven't decided what's focal yet."：它把一条数字上限还原成一个判断，让 agent 知道强调色超额说明的是什么问题。
- `SKILL.md` §6 rule 5 末段 "When in doubt, reroute. The exception exists for the narrow case …" 和 rule 6 对绘制顺序的解释（"Because nodes are painted after labels …"）：有了这个理由，agent 能处理规则没有列出的遮挡情况。
- `SKILL.md` §7 本仓加的 "These types are written for their own canonical subjects and will need bending; a Layers example that draws no connectors between its bands does not mean your connectors come off." 和 "The per-type caps above … are physical limits of their grammar and still bind absolutely."：前一句防止 agent 把示例当成限制，后一句划清哪些上限能按层计、哪些不能。这两句是本仓那条规则里需要判断的地方。
- `SKILL.md` §0 本仓加的 "anywhere the project's own visual identity is part of the message"：这是"先问品牌"的判断标准，比列场合好用。
- `SKILL.md` §11 "Redraw — never convert." 与 "An import is bounded by its source: never invent a component to fill a layout, and never silently drop one." 以及 "The user knows the source and will notice."：这几句定了导入时对原图的态度。
- `SKILL.md` §12 `### Accessible SVG contract` 第 5 条 "Describe the content, not the geometry … A shape-by-shape narration is worse than no useful description."：写 `<desc>` 靠的就是这个判断。
- `references/output-spec.md` §5 "The reader of the diagram can't see what's missing. The person who asked for it needs to."：这是 fidelity ledger 存在的理由。
- `references/style-guide.md` "Counting by script is the trap." 两段：说明了最容易算错的地方，中文图直接用得上。

### 缺口与补充草稿

- 缺口 1：`SKILL.md` §0 第 21 行 "Name the one you used beside the deliverable." 现在是一条没有目的的规定。提交 `e74e0140` 删掉了它的后半句，理由挪进了 merge-note。没有这半句，agent 不知道这行说明防的是什么，只能照格式每次都写，也判断不了该写在页上还是回复里。恢复原文：
  > Name the one you used beside the deliverable, so a default-skinned diagram never reaches a branded context unannounced.
- 缺口 2：`SKILL.md` §0 第 25 行默认路径。同一次提交删掉了"为什么不停下来问"。第 27 行"送客户就先问"之所以成立，靠的正是这个对照；没有它，agent 分不清一张图是"出门的"还是"留在屋里的"，只能照字面去匹配 "client, customer"。在第 25 行段末恢复原文：
  > Most diagrams are read once to understand something and never leave the room; stopping every one of them at a branding question costs more than it saves.
- 缺口 3：`SKILL.md` §7 第 410 行 "Split into overview + detail only when the subject genuinely holds two independent questions"。同一次提交删掉了这条规则的理由。"是不是两个独立问题"是 agent 在这里唯一要做的判断，没有理由它就只能凭字面猜。这一句正是 merge-note "总原则"（读一次就看懂一个系统）在正文里唯一的体现。在 "— then say which question each diagram answers." 之后恢复原文：
  > A reader who has to hold two canvases in their head to see one system has lost the thing they came for.
- 缺口 4（对应 U1）：`SKILL.md` §0 第 27 行本仓加的客户段，末尾缺一句"品牌写到哪里"。没有这句，agent 会按 `onboarding.md` 改写冻结的安装副本，结果影响本机所有仓库。草稿：
  > Keep the result out of the installed `style-guide.md`: this install is shared by every repository on the machine. Save it as a profile and bind this project with a `.diagram-design` marker (`references/profiles.md`).
- 缺口 5：`SKILL.md` §9 `## 9. Pre-Output Checklist` 从头到尾都是对源码的自查和脚本检查（`self_check.py` 查无障碍标注和单文件安全，`verify-geometry.py` 只查标签底板被节点遮住）。没有一句要求打开渲染出来的页面看一眼。连线交叉、文字溢出、图没有回答它要回答的问题，这些只有看渲染结果才发现得了。证据：Nowledge Mem 记忆"用户要求用技能画 HTML 介绍 MMW v2 时，明确否定了以长文和表格为主体……的初稿（2026-09-05，用户：『全是字……重做』）……交付前必须实际打开并逐图查看"。这份记录只说明了教训，没有说明那次退回是不是因为没看渲染结果，所以这里的因果是推断。草稿（放在 §9 `**Technical:**` 最后一条之后；按上游规则，这是改动上游正文，需在 merge-note 加一条）：
  > - [ ] Opened the rendered file and looked at every diagram in it? The checks above read the source; clipped text, crossing strokes and a picture that does not answer its question show only in the render.

  若坚持上游正文不加句子，退路是把同一句加到两个调用方（`mmw-v2/upstream/skills/productivity/wait-what/VISUAL.md` `## Draw the page` 与 `mmw-v2/upstream/skills/engineering/improve-codebase-architecture/HTML-REPORT.md` 开头段），代价是直接调用 diagram-design 时没有这一条。

以上 1–3 条与 `SKILL-SET-REVIEW.md` `### Redundancy and bloat` 的关系：`e74e0140` 依据该节 Sediment 表中 "the maintainer's reason for a design → an ADR" 把三句挪走了。但同一节 "These stay, though a trimming pass reads them as noise" 列有 "a reason the agent needs to decide an edge case"，三句都属于这一类。所以冲突出在那一轮对标准的应用，不在标准本身；按本任务书，以恢复为准。恢复三句约 60 词、约 330 字节，会让 `SKILL.md` 更加超出上游自己的字节上限（见"脚本"）。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
|---|---|---|---|
| C1 | `SKILL.md` §7 第 408 行（以及 A3 列出的另两处）"re-draw in a type that nests — nested, layers, tree, high-level" | 这里给的是一份封闭清单，而不是判断标准。清单里的 `high-level` 是 "end-to-end data stack overviews … deployed on a container orchestrator"，而且是参数化图型：`references/type-high-level.md` §1 要求 "Before drawing, collect these from the user … Don't invent geometry on the fly"，节点还要用 `primitive-icons.md` 里的图标（9,524 词）。一个在 `wait-what` 流程里、不许停下来问用户的 agent，照清单选中它，就会读 13k 词无关材料，还会被要求向用户收集参数。反过来，最常用的容器写法没在清单里：`type-architecture.md` 的 `## Zone grouping` 区块，`output-spec.md` 的 `faithful` 也正是靠 zone 分区。这是推断，没有查到实际选中 `high-level` 的运行记录 | 用性质代替清单：`re-draw in a type whose grammar has containers (Nested, Layer stack, Tree, or zones in Architecture) and hold the whole subject on one canvas.` 去掉 `high-level`，加上 Architecture zones；预算按层计那句不变 |
| C2 | `SKILL.md` §0 第 25 行 "keep the note beside the deliverable to one line and name in it the four ways to change it: from a website URL, from a local design-system directory, from pasted tokens, or from a saved client profile." | 默认路径是"图不出门"的场合，读者就是 owner，本来就不需要换品牌；可每一页 `wait-what` 页面、每一份架构报告的页脚都要重复同样四种改法。这是一行固定模板，替 agent 定了内容 | 改为 "keep the note beside the deliverable to one line, and say it can be rebranded (`references/onboarding.md`)."。剩余风险：用户不能从页面上直接看到四种方法的名字，但点开 `onboarding.md` 或走客户路径时都会看到。约省 20 词。补上缺口 1、2 的理由后，这一条也可以不改；两者选其一即可 |

`SKILL.md` §3 `### Confirm before drawing`、§9 检查清单、§10 `### To create a new diagram` 的编号步骤都是上游原文。在 MMW 里，前者已被两个调用方免掉，后两者不会让 agent 做错，所以不报。

## 脚本

- `mmw-v2/upstream-diagram-design/scripts/verify-geometry.py`（本仓改过，已全文读完）：本仓加了 `svg_spans`、`svg_index`、`labels_cjk`、`is_mask` 四个函数和 `Rect` 的 `svg`、`cjk_label` 两个字段。这些都对应真实问题：`b898a009` 的冷跑记录显示，一页多图时旧版把甲图的标签和乙图的节点算作重叠，架构报告因此永远通不过；`style-guide.md` 规定中日韩文字的标签底板高 16px，旧版只认 8–14px，中文标签一个都不查。`svg_spans` 里的 `elif depth:` 和 `svg_index` 返回 `-1` 是两处一行长的容错，对应 `</svg>` 不成对或 `<rect>` 在 `<svg>` 之外的情况，成本可以忽略，不算过度防御。没有死代码，没有重复逻辑。`scripts/test-verify-geometry.py` 新增的 8 条测试一一对应这两项改动，数量合适。从安装后的技能目录实际运行 `python3 repo-root/scripts/verify-geometry.py assets/example-architecture.html`，结果是 "0 finding(s)"，`repo-root` 路径能解析。
- `SKILL.md` §9 动效那一条，本仓把上游"仅在仓库 checkout 里跑"的 `lint-skin.py` 改成了每张动效图都要跑。`lint-skin.py` 允许的颜色和字体只从安装副本 `STYLE_GUIDE = ROOT / "skills/diagram-design/references/style-guide.md"` 读取（第 22、565 行），不认 project marker 选中的 profile。所以一张用 marker profile 配品牌色的动效图会被误报。这是推断：没有 profile 存在，这条路径从没走过。它只影响"动效 + marker profile"同时成立的情况，暂不需要改；若日后启用 profile，把 §9 那句改成"skin linter 只对默认或安装副本配色有效"即可。
- 上游 ADR `mmw-v2/upstream-diagram-design/docs/adr/0004-skill-md-byte-cap-and-trigger-rich-description.md` 把 `SKILL.md` 限在 40,000 字节，由 `scripts/verify-semantic-motion.py` 的 `MAX_SKILL_BYTES` 检查。上游原文 39,085 字节，本仓版本 40,404 字节，超了 404 字节。只有跑上游 CI 或向上游提交时才会碰到，MMW 不跑这套测试。记录在这里，下次拉上游时知道这项检查会失败。
- `skills/diagram-design/scripts/` 下的 `drawio_extract.py`、`excalidraw_extract.py`、`mermaid_extract.py`、`self_check.py` 是上游原样，本仓没改过。只读了头部说明和 `self_check.py --help`，结论不覆盖它们的主体代码。
- 可选，不建议现在做：§6 本仓加的 marker `id` 前缀那句，理论上可以做成 `self_check.py` 的重复 `id` 检查。但那要改上游脚本，而且重复的 marker 在默认配色下渲染结果相同，没有可见故障。

## 与其他技能的重复或交接问题

- 调用方 `wait-what`（`VISUAL.md` `## Draw the page`）与 `improve-codebase-architecture`（`SKILL.md` 第 2 步、`HTML-REPORT.md`）各自免掉 §3 "Confirm before drawing"。两处各写一遍是对的，因为每条流程只加载自己那一份。
- 两个调用方逐字重复了同一段 "The reader knows nothing about this topic. Pictures show what things are and how they connect. …"（`VISUAL.md` 与 `HTML-REPORT.md` `## Candidate card`）。两边都该留：每个 acting agent 只加载其中一份。它属于"页面怎么组织"，不属于 diagram-design 的上游正文，不要为了去重把它挪进 `SKILL.md`。
- merge-note `mmw-v2/merge-notes/diagram-design.md` 的 `### SKILL.md` 表需要随 A1、A2 更新（"三处拆图规则"改成四处，并补上 `faithful` 的归类）。另外，它关于 `repo-root` 的理由写的是 "`../../` 会算到 host 目录去"，这只对 shell 的逻辑路径（`cd ../..`）成立。实测 `ls ~/.claude/skills/diagram-design/../../scripts/verify-geometry.py` 由内核解析，能找到文件。symlink 本身仍然有用，因为它去掉了占位符的歧义；只是理由写得不够准。

## 没查到的

- 全文读完：`SKILL.md`；`references/profiles.md`、`references/style-guide.md`、`references/output-spec.md`、`references/type-nested.md`、`references/type-layers.md`；仓库根 `scripts/verify-geometry.py`；本仓对 `SKILL.md`、`output-spec.md`、`verify-geometry.py`、`test-verify-geometry.py` 的完整 diff（对 `8a85636a`），以及 `7da54056`、`e74e0140` 两次提交的 `SKILL.md` diff；merge-note 与 `merge-notes/README.md` 前半；两个调用方文件 `VISUAL.md`、`HTML-REPORT.md`；上游 ADR 0004。
- 部分读：`references/type-high-level.md`（第 1–40 行）、`references/type-architecture.md`（用 grep 查 zone）、`references/onboarding.md`（用 grep 查写文件的行）、`references/semantic-patterns.md` 和所有 `type-*.md`（只用 grep 查 "split"）、`scripts/lint-skin.py`（第 1–80 行和 grep）、`scripts/verify-motion.py`（第 1–40 行和 `--help`）、`self_check.py`（头部和 `--help`）、三个 extract 脚本（头部）、`assets/template.html` 与 `template-full.html`（用 grep 查 marker 和 slug）。
- 没读：其余 35 个 `type-*.md`、`animation.md`、`export.md`、`export-registry.md`、三份 `import-*.md`、`doctor.md`、四份 `primitive-*.md`、`assets/` 下所有示例文件、`commands/`、`prompts/`、上游其余 ADR 和 `README.md`、extract 脚本主体。这些都是上游原样，本仓没改过；关于它们"没有问题"的结论没有验证过，只是依据它们没被改动。
- 一次普通调用加载量里 `profiles.md` 那 2.2k 词是推断：§0 写的是 "First resolve any project `.diagram-design` marker per `references/profiles.md`"，agent 多半会打开它，但也可能先确认 marker 不存在就跳过。同样，§7 的 4px grid 和 §9 提到 "role ramp in `references/output-spec.md`"，可能让非导入调用也读 `output-spec.md`（2.8k 词）；这两处都是上游原文，不会让 agent 做错，所以只记成本，不建议改。
- 没有找到 diagram-design 在 MMW 里的真实运行日志；使用证据只有 `b898a009`、`6702fd42` 两次冷跑的提交说明，和 Nowledge Mem 里的几条相关记忆。
