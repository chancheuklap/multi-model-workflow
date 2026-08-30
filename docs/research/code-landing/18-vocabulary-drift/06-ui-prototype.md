# 06 · 原型 / UI 设计交接 / UI 验收 —— 词与步骤的漂移

范围：`CONTEXT.md`、`mmw-v2/upstream/skills/engineering/prototype/`（5 个文件 + `agents/openai.yaml`）、`mmw-v2/merge-notes/prototype.md`、`mmw-v2/skills/claude-design-blocks/`（SKILL.md + 8 个脚本）、`mmw-v2/skills/verify-ticket/scripts/visual-parity.py` 与 `tests/test_visual_parity.py`、`mmw-v2/skills/verify-ticket/SKILL.md`、`mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`、`mmw-v2/upstream/skills/engineering/implement/SKILL.md`、`docs/adr/0002-ui-qa-binds-format-not-tool.md`、`docs/adr/0004-design-system-trust-comes-from-lint.md`。全部整篇读完。

## 三个点名要查的事，先给结论

- **`evidence-page.md` 没被删。** `mmw-v2/upstream/skills/engineering/prototype/evidence-page.md` 在，3673 字节，且被 `EXP.md:41`「Sections, shapes, and a drop-in skeleton: [evidence-page.md](evidence-page.md)」和 `mmw-v2/merge-notes/prototype.md:55`「### EXP.md、evidence-page.md」正常引着。活范围内没有指向它的死链，也没有任何文件声称它被删。
- **`ui-qa`、`ui-evaluator` 都在 `deprecated/`**（`deprecated/ui-qa/`、`deprecated/ui-evaluator/`），`mmw-v2/skills.txt` 和 `mmw-v2/agents/` 里都没有它们。但 `docs/adr/` 里两份**活的** ADR 整篇在讲它 —— 见发现 11。
- 另有一条本机状态（不算发现，仓库里无据）：`~/.agents/skills/ui-qa` 仍是一条软链，指向 `/Users/cheuklapchan/multi-model-workflow/mmw-v2/skills/ui-qa` 这个已经不存在的路径，所以宿主的技能清单里 `ui-qa` 还亮着。跑一次 `bash mmw-v2/install.sh` 应该清掉。

---

## 发现 1：`claude-design-blocks` 第 7 步下载出来的交接包，`visual-parity.py --baseline` 打不开

- 类型：断点 / 脚本与文档不符
- 后果：worker 按 `to-tickets` 写的 `CHECK:` 跑 UI 验收，第一行就是 `no scenes.json in <dir>`；就算补上 `scenes.json`，基线页还会因为目录里没有 `support.js` 而 404，渲染出空白，然后判「实现和基线不一致」。
- 证据：
  - `mmw-v2/skills/claude-design-blocks/SKILL.md:57` 「download the handoff package — the `README.md` Claude Design generates plus every `.dc.html` — into that same leaf directory. Those downloaded files are what the implementation is later held to」
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:7-9` 「The baseline is the Claude Design project downloaded into a leaf directory: the component's `.dc.html`, its `styles/`, `data/`, `support.js`, and a `scenes.json` listing every scene by name.」
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:428-430` 「`path = baseline / "scenes.json"` … `raise SystemExit(f"no scenes.json in {baseline}")`」
  - `mmw-v2/skills/claude-design-blocks/SKILL.md:44` 「`mcp__claude-design__create_support_js` writes `support.js` at the project root.」——写在 Claude Design 项目根，第 7 步没说要把它下载进叶子目录
  - `mmw-v2/skills/claude-design-blocks/SKILL.md:55` 「keep `src`, `styles`, and `data` in the repository」——说的是本地 `work/` 目录，没说落在叶子目录
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:71` 「`--baseline <handoff package dir>`」
  - `CONTEXT.md:536` 「a README plus every component page. … and the directory `visual-parity.py --baseline` renders and screenshots.」
- 建议正名：以 `visual-parity.py:7-9` 的五件东西为准（`.dc.html`、`styles/`、`data/`、`support.js`、`scenes.json`），把 `claude-design-blocks/SKILL.md:57` 的下载清单和 `CONTEXT.md:536` 的定义都补齐到这五件。

## 发现 2：同一份「场景清单」，一处是每组件一行的文本，一处是每场景一条的 `scenes.json`

- 类型：分岔 / 脚本与文档不符
- 后果：按 `claude-design-blocks` 写出来的「一行一个组件、列出它的 `scenario` 值」丢掉了 `visual-parity.py` 必需的两个字段——`page`（哪个 `.dc.html`）和 `props`（传给实现页的查询串）。执行者写完清单，工具仍然报「没有 scenes.json」。
- 证据：
  - `mmw-v2/skills/claude-design-blocks/SKILL.md:57` 「Beside them, write the scene list: one line per component naming its `scenario` values, so each scene can be rendered later without opening the project.」
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:431` 「`catalogue = {s["name"]: s for s in json.loads(path.read_text(encoding="utf-8"))}`」
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:453-455` 「`component = re.sub(r"\.dc\.html$", "", scene["page"])` … `wrapper_page(component, scene.get("props") or {})`」
  - `CONTEXT.md:532` 「where the handoff package and the scene list live」
  - `CONTEXT.md:544` 「One state listed in the scene list.」
- 建议正名：把这份东西正名成 `scenes.json`（它是文件名，按 CONTEXT.md 开头的规则「Terms whose name is itself a literal string … have exactly one name」只该有这一个名），字段以 `load_scenes` 实际读的 `name` / `page` / `props` 为准；`claude-design-blocks/SKILL.md:57` 和 `CONTEXT.md:532/544` 改写成这个名字和这个形状。

## 发现 3：`visual-parity.py` 住在 `verify-ticket` 技能里，但 `verify-ticket/SKILL.md` 一个字都没提它

- 类型：断点
- 后果：`verify-ticket/SKILL.md:26-34` 的「## The five runs」是这份技能对读者的全部承诺，五条全是 `verify-ticket.py` 的子命令。worker 和 verifier 读完这份正文，不知道同目录下还有一个 UI 验收工具、基线目录该放什么、`DIFF` 行怎么读、`NEGATIVE CONTROL FAILED` 是什么意思。这套词只在 `CONTEXT.md` 的「### UI acceptance」里存在，而 `CONTEXT.md` 是词表，不是操作说明。
- 证据：
  - `mmw-v2/skills/verify-ticket/SKILL.md` 全文 4937 字节，`parity` / `scene` / `baseline` / `visual` / `design` 零命中；`:19-20` 「`scripts/verify-ticket.py`, next to this file. Resolve its absolute path once. Every command below is written `<engine> <ticket>`」——「Every command below」把整份正文圈死在一个脚本上
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:71` 「A criterion that compares an interface against a downloaded handoff package gets `CHECK: uv run ~/.agents/skills/verify-ticket/scripts/visual-parity.py --baseline <handoff package dir> --impl <url> --scenes <name,name> --max-pct 1` and `EXPECT: PARITY OK <n>/<n>`.」
  - `CONTEXT.md:529-581` 「### UI acceptance」十三条词，其中 `PARITY OK <n>/<n>`、`DIFF …`、`NEGATIVE CONTROL FAILED`、`归一化`、`负控制` 全是这个脚本的输出与规则
- 建议正名：在 `verify-ticket/SKILL.md` 里加一段 UI 验收（基线目录要有哪五件、命令、三种退出码、`DIFF` 下面那几行怎么读），或者明说这个脚本只由 `to-tickets` 写进 `CHECK:`、正文不覆盖它——两条路选哪条待用户拍板，但现在这样「脚本在这个技能目录里、技能正文不认它」不能留。

## 发现 4：`?variant=<winner>` 什么时候拆掉——`prototype/UI.md` 说选出赢家就拆，`claude-design-blocks` 说要靠它开页取 CSS 和 DOM

- 类型：断点
- 后果：按 `UI.md` 第 6 步做完（挂载点、切换条、软链全删），再去跑 `claude-design-blocks`，第 2 步「open the real page at `?variant=<winner>`」打开的是已经不认这个参数的正式页面，取回来的 CSS 和 DOM 是重写后的正式实现，不是变体。两份文件谁都没提对方，也没说谁先谁后。
- 证据：
  - `mmw-v2/upstream/skills/engineering/prototype/UI.md:102` 「Once a variant has won, record the answer … Fold the winner into the real code, rewritten to production standard, then remove the scaffolding:」
  - `mmw-v2/upstream/skills/engineering/prototype/UI.md:109` 「Done when nothing outside the leaf directory imports it and `?variant=` reaches nothing」
  - `mmw-v2/skills/claude-design-blocks/SKILL.md:46` 「**Prototype leaf directory**: open the real page at `?variant=<winner>` and take the CSS and the DOM from what it renders」
  - `CONTEXT.md:632` 「the chosen artifact of a prototype — the winning UI variant until a handoff package supersedes it」——只有这一句暗示了先后，而且它在「Working discipline」的 `基线` 条下，不在任何一份操作文件里
- 建议正名：以 `CONTEXT.md:632` 的先后为准（赢家先当基线，交接包下载后才顶替它），把这个顺序写进 `UI.md:102` 那一段的开头（「先做 claude-design-blocks 的移植，再拆脚手架」）和 `claude-design-blocks/SKILL.md:41/46`（「此时挂载点必须还在」）。

## 发现 5：`叶子目录（leaf directory）`——词表说它只有 UI 一种，原型技能说三种都是

- 类型：重复定义 / 命名撞车
- 后果：写 EXP 或 LOGIC 原型的人查 `CONTEXT.md` 找「叶子目录」，得到的是一个 UI 专用路径，跟他手上的 `prototypes/<task>/<issue>/EXP/` 对不上；反过来，读到 `CONTEXT.md:531` 的人会以为 LOGIC 和 EXP 没有叶子目录这个概念。
- 证据：
  - `CONTEXT.md:531-532` 「**叶子目录（leaf directory）**: `prototypes/<task>/<issue>/UI/`, where the handoff package and the scene list live.」
  - `mmw-v2/upstream/skills/engineering/prototype/SKILL.md:22` 「Every prototype sits at `prototypes/<task>/<issue>/<UI|LOGIC|EXP>/`, with a `README.md` beside the code holding the question, the current conclusion, and which parts the real code has taken.」
  - `mmw-v2/upstream/skills/engineering/prototype/EXP.md:16` 「The leaf `README.md` is the experiment's memory across rounds」
  - `mmw-v2/upstream/skills/engineering/prototype/LOGIC.md:39` 「Write the file into the leaf directory.」
  - `mmw-v2/merge-notes/prototype.md:30` 「存放约定 `prototypes/<task>/<issue>/<UI\|LOGIC\|EXP>/` + 叶子 `README.md`」
- 建议正名：以 `prototype/SKILL.md:22` 为准，`CONTEXT.md:531-532` 改成 `prototypes/<task>/<issue>/<UI|LOGIC|EXP>/`，「交接包和 scenes.json 住在 UI 那一支」作为补充句而不是定义。

## 发现 6：`基线（baseline）`有三份成员清单，`implement` 那份漏了交接包

- 类型：重复定义
- 后果：`implement` 是 worker 唯一逐字读的那份。它列的三种基线里没有「从 Claude Design 下载回来的交接包」，所以 worker 不会把交接包当契约——而契约那三条（照抄精确值、不默默偏离、不为过检查掰基线）正是 UI 验收的全部前提。`to-tickets` 却按有它来写票。
- 证据：
  - `CONTEXT.md:632` 「the chosen artifact of a prototype — the winning UI variant until a handoff package supersedes it, the validated logic module, an experiment's Reusable parts with its Conclusion — a handoff package downloaded from Claude Design, the Decision of an ADR, the resolution of a decision ticket, and the spec sections `## Parent` names.」（五类，含交接包）
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:184` 「Whatever here records a settled conclusion — the chosen artifact of a prototype, a handoff package downloaded from Claude Design, the Decision of an ADR, the resolution of a decision ticket — is a **baseline**」（四类，含交接包）
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:12` 「every item under its **Read first**, each through to its conclusion — the last section of a research file, the chosen artifact of a prototype, the Decision of an ADR. A baseline in **Read first** — anything there that records a settled conclusion — is a contract, not a reference.」（三类，无交接包）
  - `mmw-v2/merge-notes/implement.md:12` 「`## Read first` 逐份读到结论（research 的末节、prototype 选定的 artifact、ADR 的 Decision），其中记录已拍板结论的条目是基线」（三类，无交接包）
- 建议正名：以 `CONTEXT.md:632` 的五类为准，`implement/SKILL.md:12` 和它的 merge-note 各补一项交接包。

## 发现 7：同一个目录四个名字——交接包 / 基线目录 / baseline directory / `--baseline`

- 类型：幽灵词 / 命名撞车
- 后果：`CONTEXT.md` 明令禁止的「基线目录」正出现在两份活的 merge-note 和一份活的上游 reference 里，而工具自己的参数就叫 `--baseline`。读者不知道 `code-review` 的 Spec 轴不许读的那个「基线目录」和票上 `Read first` 里那个「交接包」是不是同一个目录（是），也不知道 `基线` 这个更大的词（发现 6 的五类）跟它是什么关系。
- 证据：
  - `CONTEXT.md:537` 「_Avoid_: 开发交接包, 基线目录, UI 基线」
  - `mmw-v2/merge-notes/code-review.md:18` 「加了一条我们自己的禁令：不读 `prototypes/` 下的基线目录——照不照基线由某条验收标准跑的 `visual-parity` 判」
  - `mmw-v2/merge-notes/to-tickets.md:19` 「Read first 与 Seam 非空且指向基线目录时注明它是契约」
  - `mmw-v2/upstream/skills/engineering/code-review/references/spec-reviewer.md:46` 「**The baseline directory is out of scope for you.** A ticket with UI acceptance criteria names a baseline directory in its `## Read first`」
  - `CONTEXT.md:502` 「The second axis: does the change match what the ticket or the spec asked for. It does not look at the handoff package.」（同一条禁令，用的是「handoff package」）
- 建议正名：中文一律「交接包」、英文一律「handoff package」，两份 merge-note 和 `spec-reviewer.md:46` 改过来；`--baseline` 是命令行参数、不改，但在 `CONTEXT.md:535-537` 里点明「命令行参数写作 `--baseline`，指的就是它」，免得下一个人又造一次「基线目录」。

## 发现 8：`CONTEXT.md` 把交接包的来源写成「the design skill」，而做这件事的技能叫 `claude-design-blocks`

- 类型：断点 / 命名撞车
- 后果：读者拿「the design skill」去找，宿主的技能清单里真有一个名叫 `design` 的技能（画 canvas 的那个），它没有 Finish 步骤、也不下载任何交接包。找错技能，整条 UI 交接链就断在第一步。
- 证据：
  - `CONTEXT.md:536` 「What the Finish step of the design skill downloads: a README plus every component page.」
  - `mmw-v2/skills/claude-design-blocks/SKILL.md:55` 「7. **Finish.** Delete `Harness.dc.html` and any obsolete pages …」
  - `mmw-v2/skills/claude-design-blocks/SKILL.md:57` 「When the port started from a prototype leaf directory, download the handoff package …」
- 建议正名：`CONTEXT.md:536` 改成「What step 7 (**Finish**) of `claude-design-blocks` downloads」。技能名是字面串，按 CONTEXT.md 自己开头那条规则只该有一个名。

## 发现 9：归一化第三条规则——删的是里面那个 `main` 还是外面那个，三处说法各不相同

- 类型：脚本与文档不符
- 后果：读者按 `CONTEXT.md` 或按 `normalize_aria` 的 docstring 去推 ARIA 差异该怎么修，推出来的层级方向是反的：以为工具会保留内层、去掉外层，于是把实现页的 `<main>` 结构往错的方向改，`DIFF` 反而更多。
- 证据：
  - `CONTEXT.md:564` 「The three rules that standardise an accessibility tree: drop `generic` and `group`, drop landmark names, lift a nested `main` to the top.」
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:102` 「3. one outer ``- main:`` whose only job is to wrap another ``main``.」
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:112-113` 「Remove a ``main`` nested inside another ``main`` and dedent its children.」
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:128` 「`if ln.strip() == "- main:" and main_depths:`」——`main_depths` 非空意味着外层已经开着，被 `continue` 丢掉的是**内层**那一行
  - `mmw-v2/skills/verify-ticket/tests/test_visual_parity.py:82-83` 「Rule 3: the inner `main` goes and its children come up one level」
- 建议正名：以代码和测试为准（丢内层、子节点上提一级）。`visual-parity.py:102` 的「one outer」改成「one inner」，`CONTEXT.md:564` 的「lift a nested `main` to the top」改成「drop a `main` nested inside another `main` and lift its children one level」。

## 发现 10：`#dc-root` 只是基线那一侧的锚点，实现那一侧根本没用选择器

- 类型：脚本与文档不符
- 后果：读 `CONTEXT.md` 的人会以为实现页也要有 `#dc-root`，于是在正式代码里加一个只为过检查而存在的 id——而工具截的是整个视口、读的是 `body` 的 ARIA 树，那个 id 一点用没有，白改一遍正式代码。
- 证据：
  - `CONTEXT.md:551-552` 「**`#dc-root`**: The anchor selector for screenshots and for reading the accessibility tree.」
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:494-496` 「`base_shot = capture(page, f"{origin}/__parity-{name}.dc.html", "#dc-root", vp, …)`」
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:501-503` 「`impl_shot = capture(page, impl_url(args.impl, scene.get("props") or {}), None, vp, …)`」
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:352` 「`target = page.locator(selector or "body").first`」
- 建议正名：`CONTEXT.md:551-552` 改成「基线那一侧截图与读 ARIA 树的锚点；实现那一侧截整个视口、读 `body`」。

## 发现 11：两份活的 ADR 整篇在规定一个已经退役的技能怎么做事

- 类型：断点
- 后果：`docs/adr/` 是流水线的决策来源，票的 `## Read first` 会指过来。读者读完 0002 和 0004，会以为流水线里有一个「界面 QA」，有 A1–A4 / B1–B5 九种检查、有一份依赖声明、有一套三档准入规则；`mmw-v2/` 里这些一样都没有。`docs/adr/README.md` 也没把它们标成退役。而且「界面 QA」这个词在 `CONTEXT.md` 里根本没登记。
- 证据：
  - `docs/adr/0002-ui-qa-binds-format-not-tool.md:8` 「界面 QA 的 A3（设计系统 token 越界）与 B1（设计系统规则违反）需要一份机器可读的设计系统作为判据。」
  - `docs/adr/0004-design-system-trust-comes-from-lint.md:48` 「界面 QA 的依赖声明里，「设计系统作者」那一条的来源从 GitHub 稀疏检出改为 skills CLI 管理的 `~/.agents/skills/`。」
  - `docs/adr/README.md:8` 「| 0002 | 界面 QA 绑设计系统的格式规范，不绑生成它的工具 | 2026-08-13 | 无 | 0004 |」，`docs/adr/README.md:10` 「| 0004 | … | 2026-08-21 | 0002 | 无 |」——两行都没有退役标记
  - `mmw-v2/skills.txt:9-42` 全表无 `ui-qa`；`mmw-v2/agents/` 只有 `advisor`、`assemble.py`、`claim-checker`、`verifier`
  - 反证（`deprecated/` 不在审计范围，仅作旁证）：`deprecated/README.md:16-17` 说 A3、B1 现在由 `visual-parity.py` 承接——但 `visual-parity.py` 全文不读 `DESIGN.md`，它比的是基线，不是设计系统规则
- 建议正名：待用户拍板，两条路：① 给 0002、0004 各写一份取代它们的 ADR，说明界面 QA 退役后 `DESIGN.md` 只剩「Claude Design 精修时的设计系统」这一个用途，`README.md` 的表加一列或加一行标注；② 直接删这两份并在「删过哪几批」里记一笔。现在这样放着，`Read first` 指过来就会把一个不存在的检查体系当契约读。

## 发现 12：`claude-design-blocks` 让人跑 `create-design-md`，但 `install.sh` 不装它

- 类型：断点
- 后果：新机器上按 `AGENTS.md` 跑完 `bash mmw-v2/install.sh`，`claude-design-blocks` 的第一段就要求跑一个装不上的技能。它到底从哪来，只写在一份 ADR 的一句话里，而 `claude-design-blocks` 没引那份 ADR。
- 证据：
  - `mmw-v2/skills/claude-design-blocks/SKILL.md:12` 「if it has none, run the `create-design-md` skill to write one from that repository, then upload it in Claude Design under "Create new design system".」
  - `mmw-v2/skills.txt:9-42` 全表无 `create-design-md`（`self/` 段是 `claude-design-blocks`、`exe-release`、`verify-ticket`、`readable-docs`、`manage-agents-md`、`dispatch`）
  - `docs/adr/0004-design-system-trust-comes-from-lint.md:26` 「设计系统不存在时委派谁去建，同时改掉：从 `pbakaus/impeccable` 换成 `ibelick/ui-skills@create-design-md`。」
- 建议正名：在 `claude-design-blocks/SKILL.md:12` 把来源写全（`ibelick/ui-skills@create-design-md`，由 skills CLI 装进 `~/.agents/skills/`，`install.sh` 不管它），或者把它收进 `skills.txt`。选哪条待用户拍板。

## 发现 13：`mkallharness.py` 要不要传参——同一份 SKILL.md 前后两句相反

- 类型：分岔 / 脚本与文档不符
- 后果：第 5 步告诉读者「app page 不是 `src/*.py`，所以不用排除列表」，第 6 步却让他把 app page 的名字当参数传进去。传了也没用（脚本只拿这些名字去比 `src/*.py` 里的 `NAME`），但读者不知道自己传的是空的，会以为漏了什么。
- 证据：
  - `mmw-v2/skills/claude-design-blocks/SKILL.md:49` 「An app page is written by hand as a `.dc.html` (it is not a `src/*.py` source, so `mkallharness.py` needs no exclusion list for it)」
  - `mmw-v2/skills/claude-design-blocks/SKILL.md:51` 「`python3 scripts/mkallharness.py <app page names…>` generates `Harness.dc.html`, which renders every component in every scenario」
  - `mmw-v2/skills/claude-design-blocks/scripts/mkallharness.py:2` 「Usage (working directory): python3 mkallharness.py [app page names to exclude...]」
  - `mmw-v2/skills/claude-design-blocks/scripts/mkallharness.py:5-7` 「`for p in sorted(pathlib.Path("src").glob("*.py")):` … `if m.NAME in skip: continue`」——排除只对 `src/*.py` 生效
- 建议正名：以第 49 行的判断为准，第 51 行改成 `python3 scripts/mkallharness.py`（不传参），并在脚本 docstring 里说明这个参数只在 app page 恰好也是 `src/*.py` 时才有意义。

## 发现 14：负控制到底是「先跑」还是「最后跑」

- 类型：脚本与文档不符
- 后果：读者以为工具会先自检、坏了就立刻停；实际它把第一个视口下每个场景都跑完之后才造负控制，而且只在第一个视口造一次。一次自检失败的运行会先烧掉整轮浏览器时间才打印 `NEGATIVE CONTROL FAILED`；等待时看到的中途输出也不代表自检已通过。
- 证据：
  - `CONTEXT.md:568` 「Every run first compares one deliberately wrong scene, to prove the tool itself is not broken.」
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:242` 「The negative control runs first and is the only thing reported when it fails」
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:491-511`（每个场景的比对循环）在前，`:512` 「`if control is None:`」在后
- 建议正名：以代码为准，把两处「first」改成说清它的真实位置——「负控制在第一个视口跑完全部场景后造一次，并在判定时先于所有场景生效」。`gate()` 判定顺序确实是先看负控制，这一半是对的，别把它和执行顺序混在一句话里。

## 发现 15：`?variant=<winner>` 被登记进「UI acceptance」，但 UI 验收实际往实现页上挂的查询串是场景的 `props`

- 类型：命名撞车
- 后果：读者在「### UI acceptance」这一节看到 `?variant=<winner>`，会去给实现页实现一个 `variant` 参数；`visual-parity.py` 往 `--impl` 上拼的却是 `scenes.json` 里那条场景的 `props`（现有用例是 `?scenario=…`）。实现了错的参数，每个非默认场景都判失败。
- 证据：
  - `CONTEXT.md:555-556` 「**`?variant=<winner>`**: The query string that switches a real page's mount point to the winning prototype variant.」（登记在「### UI acceptance」节内）
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:375-381` 「`query += [(k, v if isinstance(v, str) else json.dumps(v)) for k, v in props.items()]`」
  - `mmw-v2/skills/verify-ticket/tests/test_visual_parity.py:229-231` 「`vp.impl_url("http://127.0.0.1:8765/index.html", {"scenario": "queue-empty"})` == `"http://127.0.0.1:8765/index.html?scenario=queue-empty"`」
  - `mmw-v2/upstream/skills/engineering/prototype/UI.md:20` 「Variants are rendered **on the same route**, gated by a `?variant=` URL search param.」——`?variant=` 是原型阶段切三个变体用的，跟赢家无关
- 建议正名：把 `?variant=<winner>` 从「### UI acceptance」挪回原型那一段（它是 `prototype/UI.md` 的词），并在 UI acceptance 里补一条：实现页接收场景的方式是 `scenes.json` 里那条场景的 `props` 拼成的查询串。

## 发现 16：`DIFF` 行的形状比 `CONTEXT.md` 写的多一截，而且不是每次都跟着 ARIA 行

- 类型：脚本与文档不符
- 后果：按 `CONTEXT.md` 的形状去 grep 或写正则，会漏掉 `— …` 那一截；而失败原因恰恰只写在那一截里。更要紧的是尺寸不等和控制台报错这两种失败，`DIFF` 行下面一行 ARIA 都没有——读者按「followed by the `baseline` and `impl` lines」去找，什么都找不到，会以为输出被截断了。
- 证据：
  - `CONTEXT.md:575-576` 「**`DIFF <scene> <viewport> <pct>% box=…`**: The line printed for a scene and viewport that did not pass, followed by the `baseline` and `impl` lines of the accessibility tree that changed.」
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:257-258` 「`lines.append(f"DIFF {c.scene} {c.viewport} {c.pixel['pct']}% box={box} " f"— {'; '.join(r.en for r in reasons)}")`」
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:612-614` 「`out.append(f"  only in baseline  {role} {before}")` … `out.append(f"  only in impl      {role} {after}")`」——除了 `baseline` / `impl` 还有这两种前缀
  - `mmw-v2/skills/verify-ticket/scripts/visual-parity.py:212-235` `failures()` 的四种 `Reason`（`size` / `aria` / `pixel` / `console`），只有 `aria` 那种会带出下面的行
- 建议正名：`CONTEXT.md:575-576` 改成 `DIFF <scene> <viewport> <pct>% box=… — <reasons>`，并说明只有 ARIA 差异那一类会在下面带出 `baseline` / `impl` / `only in baseline` / `only in impl` 四种行。
