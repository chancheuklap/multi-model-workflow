# to-spec

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：已有的几句判断都保留：第 14 行一份还是几份 spec 的判据、第 22 行 "A row whose `gap` is not `aligned` is a decision nobody has made"、第 28 行"观察与到达是两件事"、第 78 行 "a behaviour that is settled only in a story reaches nobody"。真正的缺口只有一个：spec 没说哪类没人定过的决定归 agent、哪类必须交给用户。spec #555 发布时带着两处产品层面的空缺，切票时才被扫出来。其余改动是把发布交给脚本，并删掉没人读的模板项。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` 第 6 行，把本仓加的末句 "Step 1 names the one judgement you put to them." 替换为右栏（上游的前两句不动） | A spec is the last text a person checks before agents build from it unattended: whatever it leaves open, a worker decides alone at night, and whatever it states is built as written, including what nobody decided. So record decisions rather than make them. An engineering call the sources leave open (a module boundary, a data shape, the seam) is yours: make it and mark it "this spec's decision". A call on what the user sees, what happens to money, or what is in scope that no source settles is not yours: put it to the user before you publish. That, and the division in step 1, are the only things you ask them. | 写到一处没人定过的产品行为（读失败时显示什么、一个默认值）时：没有它，agent 自己定下并标成 "this spec's decision"，问题拖到切票或夜里才暴露；有了它，发布前问用户。反过来，工程问题它不会拿去问用户。与上游 "Do NOT interview the user for facts" 不冲突：事实照旧自己查，只有产品决定交给用户。这与你全局 CLAUDE.md 第 1 条的分工一致。 |
| I2 | 模板 `## Implementation Decisions` 说明段（"…Each subsection can cover:" 那段）之后 | Each subsection is read on its own: a worker opens only the subsections its ticket names, so a subsection that depends on another names it. | 写一个依赖别处定义的小节时：没有它，agent 会写 "as above"；有了它，会点名依赖。依据是 `implement` 的读入规则（只读票点名的小节）；spec #555 的评论记录 #578 的 worker 因第 11 节一句话范围不清而做错。 |
| I3 | 模板 **Critical flows**，把 "Money, sign-in, a submit chain." 与 "`to-tickets` cuts one acceptance ticket per line." 两处替换为右栏 | Each line becomes an acceptance ticket: a journey that drives the real product end to end with nothing mocked, and runs again with the flow's last write broken to prove the journey notices. List the flows where a silent break costs the user money, access or submitted work, not every path through the interface. | 现在 agent 只有三个例子可比照。知道每一条的代价（一张真实跑全栈的票）和入选判据后，它不会把每条路径都列上，也不会漏掉"坏了没人察觉、用户会丢东西"的那条。依据是 `to-tickets` 的 `references/cutting-interface-tickets.md` `## acceptance ticket`。 |
| I4 | 第 2 步 `Done when` 前半 "you can name the modules this spec touches" 改为右栏 | you know which existing modules and ADRs each decision touches, or that none exists yet | 原判据不会失败（总能说出几个模块）；改后要求每个决定都对上现有代码或说明没有。后半（每行 `gap` 都是 `aligned`）不动。 |

### 删除或交给脚本

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | 第 4 步第 34–40 行：建 `mmw:spec` label、`--parent <map>`、读回 `parent.number`、"`## Sources`, `## Further Notes`, the spec title, and semantic similarity do not replace the native parent."、非 map 来源不编 parent、`Done when` | 与 `to-tickets` 共用 `verify-ticket.py` 的同一个发布命令 `--publish`（`to-tickets` 定稿 D1），这里是它发布 spec 的形式：`--publish --spec-body <file> --title <t> [--map <n>]`；复用 `run_sub_issue` 的创建调用和 `setup-matt-pocock-skills` 定稿 D2 那份 label 定义，建完读回 `parent`，不符则非零退出。文字缩成：一句命令；"Give it no triage label: a spec is a container for the tickets underneath it…" 那句理由保留；"map 来源传 `--map`，非 map 来源不传"。`mmw-v2/tests/verify-ticket/test_to_spec_native_parent.py` 逐字钉住这几句，改为测脚本行为。 | 三件确定性的事；native parent 的重要性真实存在（`retro.py`、看板都靠它找 map），正因如此交给脚本保证。 |
| D2 | 模板 `## Testing Decisions` **Test surfaces** 一项 | 删；`mmw-v2/merge-notes/to-spec.md` `## 一个概念一个名字` 随之清理 | 要 agent 把脚本输出抄进 spec，抄完即过时；全仓没有技能或脚本读它（只有测试夹具）。 |
| D3 | **How a test arrives at a state** 后半，从 "On a new product the contract ticket builds the story service…" 到 "…or say that nothing is." | 改为："On a new product all three are new. On a product whose `.mmw/` already answers, say which is missing, counting what `target_config.py --check` of the `ui-acceptance` skill reports and any answer built for a design package, scene shape or control lookup other than the current ones, or say that nothing is." | 哪种票建哪个机制，是切票一方的判断，已写在 `to-tickets` 的 `cutting-interface-tickets.md` `## contract ticket`；写 spec 时票还不存在。 |
| D4 | **Critical flows** 里 "`to-tickets` reads this bullet only when it cuts interface tickets, so a spec without one leaves it out." 与 "(for example, `Implementation Decisions 第 2、4 节` reads the same)" | 删 | 前者是维护者理由，条件已由 "Only with a screen contract" 给出；后者与同句 "in one shape" 矛盾。 |
| D5 | `references/revising-a-spec.md` `## When the rows change` 三条 bullet | 改为接在第 3 行后的一句："When the `write-screen-contract` skill's **Re-runs** rewrote the rows, the same holds row by row, and a new row gains one boundary criterion on the ticket that owns it." | 三条里两条是第 3 行通则按合同行重说一遍。 |
| D6 | 第 1 步 "(asked by the user, or sent back from the `to-tickets` skill)" | 删括号 | 列举调用方且不全；判据是前半句。 |

### 不采纳

- 调查员 B-1 中间"`to-tickets` 切票、worker 读哪几节、Spec axis 按什么审"那几句：是别的技能的复述，I1 只留改变选择的部分。
- B-2（seam 不问用户的理由）：I1 已经说了工程决定归 agent。
- B-3（修订评论的目的，worker 不改 spec 的理由）：`revising-a-spec.md` 已有 "rewrite the section so it reads as if written that way from the start"；`implement` 已有 "Once a batch is published, only its main agent or the user edits a spec"。
- B-4（native parent 的理由）：D1 交给脚本后，agent 不再需要这句。
- B-6（一次只写一份 spec 的理由）：调查员自己标了"推断，没找到原始依据"。不为填空写一个编出来的理由。

## 结论

`mmw-v2/upstream/skills/engineering/to-spec/` 现在是 `SKILL.md` 130 行、2556 词，加两个 reference（`references/revising-a-spec.md` 317 词、`references/several-specs.md` 275 词），共约 3150 词；上游原版（squash 提交 `5b1a4c51` 的 `skills/engineering/to-spec/SKILL.md`）只有 493 词，所以八成以上是本仓加的，技能自己没有脚本。本仓加的部分大多有真实事故作依据（#541 任务板试点、spec #555 的 `Critical flows` 行、#447 第 6 节），不是凭空的防御；真正该删的集中在四处：发布一步里可由脚本完成的建 label、挂 native parent、读回校验（`SKILL.md` 第 34–40 行），**Test surfaces** 一项（第 97 行）抄脚本输出且没人读，**How a test arrives at a state** 里替 `to-tickets` 分配"哪张票建哪个机制"（第 96 行），以及 `references/revising-a-spec.md` 的 `## When the rows change` 把上一段的通则再按行说一遍。估计能删约 270 词（占全部 9%）而不丢功能，其中约 120 词要靠给 `verify-ticket.py` 加一个发布 spec 的入口。灵魂方面缺一块：技能没有告诉 agent spec 在 MMW 里是"人最后一次看过、之后 agent 无人值守照着干"的那份文本，也没有区分它可以自己定的工程决定与必须交还用户的产品决定；spec #555 的两处产品歧义一直留到切票时才被扫出来，缺的就是这一块。补上约 180 词，净体量基本不变。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
|---|---|---|---|---|---|
| A1 | `SKILL.md` `## Process` 第 4 步，第 34 行 "publish it to the project issue tracker with one label, the layer label `mmw:spec`; when the repository lacks it, create it as …"、第 36 行 "When the reference is a wayfinder map, publish each spec from that map as a native sub-issue …"、第 38 行 "When the reference is not a wayfinder map, do not invent a map parent"、第 40 行 `Done when` | 1、6 | 建 label（缺时建）、`gh issue create --label mmw:spec --parent <map>`、读回 `parent.number` 与 map 号比对，这三件都是确定性的事，现在要 agent 手做。`verify-ticket.py` 已有同类代码：`ensure_label`（第 1564 行）按 `CLASS_LABELS`（第 61–66 行，含 `mmw:spec` 的颜色与说明）建 label，`run_sub_issue`（第 1585 行起）就是"建 label + `gh issue create --parent`"的样子。第 36 行里 "before reporting the publish as complete. A missing or different native parent is a failed publish …" 与第 40 行 `Done when` 说的是同一个完成标准（类别 6）。native parent 本身不是过度防御：`retro.py` 第 236–241 行按 native parent 判定 task root，`mmw-v2/board/board_data.py` 也读它；Nowledge Mem 里有同类真实事故（ticket #77、#78 只在正文写 `## Parent`、没有 native 链接，#68 AC8 的检查因此零次循环后报 `LINT-CLEAN`） | 一个新脚本入口承担（例如 `verify-ticket.py --publish-spec <body-file> --title <t> [--map <n>]`，复用 `ensure_label`，建完读回 `parent`，不符则非零退出并说明）。剩余风险：要新写代码和测试；`mmw-v2/tests/verify-ticket/test_to_spec_native_parent.py` 逐字钉住 "publish each spec from that map"、"parent.number"、"semantic similarity"、"native sub-issue of the map" 这几串文字，改文本时要一起改成测脚本行为 | 第 34–40 行缩成：命令一句；"Give it no triage label: a spec is a container …" 那句理由保留（灵魂，见 B）；map 来源传 `--map`、非 map 来源不编 parent 一句；再加一句为什么要 native 链接（草稿见 B 缺口 1 之后的 B-4）。约 220 词变约 100 词 |
| A2 | `SKILL.md` 模板 `## Testing Decisions` 第 97 行 "**Test surfaces.** With a screen contract: the **product answers** …, as `target_config.py --check` of the `ui-acceptance` skill prints them, each `ok` or missing." | 1、2、6 | 要 agent 把一个脚本的输出抄进 spec，抄完就会过时。全仓 `grep "Test surfaces"`：除了本技能和 merge-note，只在 `mmw-v2/tests/verify-ticket/test_screen_contract.py` 第 825、831 行作为测试夹具出现，没有任何技能或脚本读它；`to-tickets` 的 contract ticket 读的是 **How a test arrives at a state**（`references/cutting-interface-tickets.md` `## contract ticket` 第 86 行 "fill only what the spec's **How a test arrives at a state** names as missing"）。spec #555 的这一行里真正有用的是 "它看不到的欠缺（break switch、按 scene input 的 s…" 那半句，而这半句本该在 How a test arrives | 第 96 行 **How a test arrives at a state** 已经要求写出 "what `target_config.py --check` … reports plus any answer built for …"，缺什么由它承担；要看现状的人自己跑 `--check`。剩余风险：无读者依赖 | 删掉这一项；`mmw-v2/merge-notes/to-spec.md` 的 `## 一个概念一个名字` 一节随之只剩 CONTEXT 里的登记，可删 |
| A3 | `SKILL.md` 模板第 96 行 **How a test arrives at a state** 后半 "With a screen contract, three mechanisms are named here, each with the ticket that builds it: … On a new product the contract ticket builds the story service with the first story adapter, the interaction helper and `start`, and each component page ticket adds its own page's adapter; on a product whose `.mmw/` already answers, name the ticket that builds whatever is missing …" | 6、4 | "哪种票建哪个机制"别处已经写了三份：`to-tickets` 的 `references/cutting-interface-tickets.md` `## contract ticket` 第 90–98 行列出 contract ticket 交付 story service 与第一个 adapter、interaction helper、`.mmw/target.json`（切票 agent 在切票那一刻加载）；`ui-acceptance` 的 `references/story-parity.md` 第 12–14 行 "The contract ticket builds the **story service** … later interface tickets add one story adapter per design page"；`implement` 的 `references/writing-interface-code.md` 第 27 行要 worker 同时写本页的 story adapter。写 spec 时票还不存在，spec 这里写的"ticket"只能是票的种类，是那份 reference 的复述。`to-tickets` 第 4 步第 4 问只要求机制"named in the spec's Testing Decisions" 且 "owned under some ticket's **Owns**"，Owns 由切票的一方定 | 归属由 `cutting-interface-tickets.md` 承担（切票 agent 行动时加载的那一份）。剩余风险：spec 里看不到归属，要看的人去 ticket 的 **Owns** | 改成："With a screen contract, three mechanisms are named here: the story adapter …, the interaction helper …, and `start` in `.mmw/target.json` …. On a new product all three are new. On a product whose `.mmw/` already answers, say which is missing, counting what `target_config.py --check` of the `ui-acceptance` skill reports and any answer built for a design package, scene shape or control lookup other than the current ones, or say that nothing is. How each is shaped is that skill's references." 约省 45 词 |
| A4 | `SKILL.md` 模板第 98 行 **Critical flows** 里 "`to-tickets` reads this bullet only when it cuts interface tickets, so a spec without one leaves it out." 与 "(for example, `Implementation Decisions 第 2、4 节` reads the same)" | 2、6 | 前一句是维护者理由（为什么只在有 screen contract 时写），agent 需要的是条件本身，条件已由 "Only with a screen contract" 给出。后一句告诉 agent 另一种写法也行，与同一句 "Each line sits nested under the bullet in one shape" 自相矛盾；merge-note `## Critical flows 每一行的形状` 说"接受的形状只留一种"，而 `verify-ticket.py` `critical_flows`（第 3245 行起）实际接受至少三种写法 | "Only with a screen contract" 与那一个形状承担。剩余风险：无 | 删这两处；同时把 "`to-tickets` cuts one acceptance ticket per line" 换成对 agent 判断有用的后果（草稿见 B-5），让它知道列一条流程的代价 |
| A5 | `references/revising-a-spec.md` `## When the rows change` 三条 bullet（第 7–13 行） | 6、4 | 第 3 行已给通则："Tickets already cut from the section and not yet landed are checked against the new text and corrected where they no longer match; a landed one is followed by a correction ticket." 三条里第一、三条是这条通则按合同行再说一遍，只有第二条 "A new row gains one boundary criterion on the ticket that owns it" 是新内容 | 第 3 行通则承担。剩余风险：无 | 整节改成一句接在第 3 行后："When the `write-screen-contract` skill's **Re-runs** rewrote the rows, the same holds row by row, and a new row gains one boundary criterion on the ticket that owns it." 约省 50 词 |
| A6 | `SKILL.md` 第 12 行 "(asked by the user, or sent back from the `to-tickets` skill)" | 4 | 列举调用方，且不全：`triage` 第 5 步、`write-screen-contract` `SKILL.md` 第 123 行、`dispatch` `references/night.md` 的 `contract` child 也送 agent 来这里。判据是前半句 "one of its sections has to change"，列举不增加判断 | 前半句承担。剩余风险：无 | 删括号 |

考虑过、判定不删的：第 22 行 "A decision that no row carries and the design package does not draw … is written in the subsection it belongs to as 'this spec's decision'" 看似与第 76 行模板里的同一规则重复，但 merge-note `## 没有合同行的决定` 记录了 #541 起草 spec 时 agent 在这里猜过，它挡的是"每个行为都必须有合同行，否则就停"这个真实误读，按 `SKILL-SET-REVIEW.md` `### Redundancy and bloat` "a sentence that prevents a known misuse" 保留。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 第 6 行 "Do NOT interview the user for facts; just synthesize what you already know."（上游）：定下 agent 的姿态，事实自己去查，不把问题推给用户。
- `SKILL.md` 第 14 行 "Then judge whether what you have read is one spec or several. … forcing it into one spec produces one nobody can read. What the dependencies may not do is run backwards or in a circle"：给的是判据加理由，不是规则表；agent 能据此处理清单外的划分。
- `SKILL.md` 第 22 行 "A row whose `gap` is not `aligned` is a decision nobody has made: stop rather than write a spec around it."：spec 记录决定、不替人补决定，这一句是全技能最清楚的表态。
- `SKILL.md` 第 26 行 seam 的五句（上游）："Use the highest seam possible … the ideal number is one"：测试思路的核心。
- `SKILL.md` 第 28 行 "A seam says where a test **observes**. Ask the other half in the same breath …"：教的是一种思考方式（观察和到达是两件事），后面 ticket 能不能写出判据取决于它。
- `SKILL.md` 第 30 行 "The seam is yours to decide, not the user's"：工程决定归 agent，与用户的分工原则一致（理由可补，见 B-2）。
- `SKILL.md` 第 34 行 "a spec is a container for the tickets underneath it, not a piece of work, and a triage label would put it in a queue somebody has to sort back out"：说明 spec 在树里的位置和打错 label 的后果。A1 改脚本时这一句要留在文本里。
- `SKILL.md` 第 76 行 "**Every decision names where it came from** … the worker reads the spec, not that file"：告诉 agent 下游读者只读 spec，出处与仓库规则必须经 spec 到达。
- `SKILL.md` 第 78 行 "A worker reads the Implementation Decisions subsections its ticket names and never a story, so a behaviour that is settled only in a story reaches nobody."：这是技能里唯一一处直接说"谁读、读哪一部分、漏写的后果"的句子，是 B-1 草稿的样板。
- `SKILL.md` 第 86 行 "Paths to source material (…) are what the tickets and the implementer read from: write them."：给了规则的理由，agent 能据此判断哪些路径该写。
- `SKILL.md` 第 96 行前半 "Whoever cuts the tickets reads this section to know whether a criterion can be written at all"：说明这一节的用途，是它存在的理由。
- `references/revising-a-spec.md` 第 3 行 "never publish a new one: a new issue gets a new number, and every ticket's **Parent** points at the old one" 与 "rewrite the section so it reads as if written that way from the start"：给出后果，让 agent 不走捷径另开一份。
- `references/several-specs.md` 第 3 行 "this is the one judgement in this skill you hand to the user"：标出用户拍板的边界。

### 缺口与补充草稿

- **B-1 开头缺"spec 在 MMW 里是干什么的"以及"哪些决定不归你"**（`SKILL.md` 第 6–8 行之后，新起一段；不改上游那两行，只把本仓加的 "Step 1 names the one judgement you put to them" 一并改掉）。现在的技能从上游继承的只有"合成已讨论的内容"，没有说这份文本之后没人在场：`to-tickets` 从它切票，worker 夜里只读自己的票点名的 Implementation Decisions 小节加 Testing Decisions 和 Out of Scope（`implement` `SKILL.md` 第 20 行），code review 的 Spec axis 按同一小节审（`to-tickets` `SKILL.md` 第 59 行）。上游说明页 `mmw-v2/upstream/docs/engineering/to-spec.md` `## The spec is a decision record` 有这层意思（"Anything the spec asserts that you never actually said is a defect."），但说明页不进 agent 的上下文。本仓又允许 "this spec's decision"（第 76 行），却没说哪类决定 agent 可以自己下。结果：agent 遇到没人定过的产品问题时，会自己定下并标成 "this spec's decision"，问题要到切票或夜里才暴露。证据：spec #555 的第一条修订评论 "第 2 节补上顶栏读失败时时间的写法与'从未读成功'时的写法：用户对切票时扫出的两处歧义的决定"，两处产品层面的空缺发布时没被发现；同一 spec 2026-09-22 04:23 的评论记录 #578 的 worker 因第 11 节一句话的范围不清做错。
  > A spec is the last text a person checks before agents work from it unattended. The `to-tickets` skill cuts it into tickets; a worker, at night and with nobody to ask, reads only the Implementation Decisions subsections its ticket names, Testing Decisions and Out of Scope; code review judges the diff against those same subsections. Whatever the spec leaves open is decided again by whichever worker meets it, alone; whatever it states is built exactly as written, including what nobody decided. So record decisions rather than make them. An engineering call the sources leave open (a module boundary, a data shape, the seam) is yours: make it and mark it "this spec's decision". A call on what the user sees, what happens to money, or what is in scope, that no source settles, is not yours: put it to the user before you publish. Those, and the division in step 1, are the only things you ask them.

- **B-2 seam 不问用户的理由缺了**（`SKILL.md` 第 30 行句末）。理由只在 merge-note 第 13 行（"user 看不懂 seam，问他等于把自己该做的判断推给读不懂的人"）。没有理由时，谨慎的 agent 会"为保险起见"仍然去问。
  > They cannot judge a seam from the code, and a question they cannot answer only hands your call to someone who cannot make it.

- **B-3 修订评论的目的在 2026-09-22 的减重里被删了**（`references/revising-a-spec.md` 第 3 行 "What changed and why goes in one comment on the spec."）。`git log -p` 显示提交 `e74e0140` 删掉了原文 "so the body stays the clean current version and the reasons stay findable"。没有这半句，agent 只知道规则，不知道正文里留"原为 X、改为 Y"会让 worker 和 reviewer 读到已作废的决定。同一行末句 "edited only by the main agent or by a session the user is working in" 也只有规则没有理由；worker 可以通过模型触发加载本技能，这一句是挡它的地方。
  > What changed and why goes in one comment on the spec: everyone who reads the body later (a worker, the reviewer, the next ticket cut from it) takes each sentence as current, and the comment keeps the reason findable.

  > … edited only by the main agent or by a session the user is working in. A worker that finds the spec wrong reports it rather than edits it: the spec is what its own work and its reviewer are judged against.

- **B-4 native parent 规则缺理由**（`SKILL.md` 第 36 行 "`## Sources`, `## Further Notes`, the spec title, and semantic similarity do not replace the native parent."）。现在这一句列举了四种不能替代的东西，却没说为什么；有理由的一句能覆盖所有列举不到的替代品。与 A1 一起改。
  > The board, the retro and the lint find a spec's map only through that native link; nothing written in the body stands in for it.

- **B-5 列一条 Critical flow 的代价没说**（`SKILL.md` 第 98 行）。现在写的是 "Money, sign-in, a submit chain" 和 "`to-tickets` cuts one acceptance ticket per line"，agent 不知道每一条意味着什么，就只能照三个例子判断。依据：`to-tickets` `references/cutting-interface-tickets.md` `## acceptance ticket` 第 141–145 行（journey 驱动真实产品、不 mock，带 `--break`，`senior-worker`）。
  > Each line becomes an acceptance ticket: a journey that drives the real product end to end with nothing mocked, and runs again with the flow's last write broken to prove the journey notices. List the flows where a silent break costs the user money, access or submitted work, not every path through the interface.

- **B-6 一次只写一份 spec 的理由缺了**（`references/several-specs.md` 第 3 行 "Then write the first spec only; publish it, fill its link into that line, and stop"）。merge-note 第 17 行只描述流程不解释。没有理由，agent 遇到两份都很小的 spec 时没有依据判断能不能一起写。真实使用确认这条流程在走：spec #444 的 `## Further Notes` 写着五份 spec 的划分与链接（#444–#448，用户 2026-09-19 确认）。下面草稿的理由是我的推断，没找到原始依据，需要维护者确认或换成真实理由。
  > (推断的理由) Each spec gets a run of its own: writing one means reading its sources through to their conclusions, and the next spec deserves a session that starts from the written division, not one already full of the last spec's sources.

- **B-7 Implementation Decisions 小节要能单独读懂，这一点没说**（`SKILL.md` 第 66 行模板说明之后）。worker 只读自己的票点名的小节（`implement` `SKILL.md` 第 20 行），一个依赖另一小节才读得懂的小节，对 worker 来说是残缺的。这条是推断，我没找到因此出错的实例。
  > Each subsection is read on its own: a worker opens only the subsections its ticket names, so a subsection that depends on another names it.

与 `SKILL-SET-REVIEW.md` 的冲突：`### Redundancy and bloat` 的 **Sediment** 表把 "the maintainer's reason for a design" 归到 ADR，按字面会把 B-3、B-4、B-6 这类"为什么"当沉积物删掉；B-3 那半句正是这样在 `e74e0140` 被删的。同一节末段 "a reason the agent needs to decide an edge case" 本可以保住它，但修剪时没这样读。按任务书，这类理由是 agent 做判断的依据，应保留。另外，`### Upstream skills` 末条（"When fewer than half of a skill's lines are upstream's, it is reviewed as the set's own text"）本应让 to-spec 按本仓自有技能审；它的上游行不到两成，这与任务书"按上游技能、重点查本仓加的部分"实际上是同一个范围。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
|---|---|---|---|
| C1 | `SKILL.md` 第 96 行 **How a test arrives at a state** 的界面部分 | 按票种规定每个到达机制归谁（contract ticket / component page ticket），这是切票一方的判断，写在 spec 模板里就成了固定映射；遇到映射外的产品（例如只有 journey、没有 story 页），agent 只能硬套 | 同 A3：spec 只点名机制，并判断现有产品缺什么；归属交给 `to-tickets` |
| C2 | `references/revising-a-spec.md` `## When the rows change` | 用 if-then 清单把一条通则按"未落地 / 新行 / 已落地"拆开重述，清单外的情况（例如一行被删）就没有依据 | 同 A5：通则一句，加上唯一新的规则（新行加一条 boundary criterion） |
| C3 | `SKILL.md` 第 24 行第 2 步 `Done when you can name the modules this spec touches …` 前半 | 前半句不会失败（agent 总能说出几个模块），按 `SKILL-SET-REVIEW.md` `### Scripts and judgement` "A check or completion criterion that cannot fail proves nothing" 是空判据；后半（每行 `gap` 都 `aligned`）能失败，有用 | 前半改成能失败的："you know which existing modules and ADRs each decision touches, or that none exists yet"；或只留后半 |

考虑过、判定不算死板的：
- 模板 `## Sources` 固定十二类、每类无则写 `none`（第 107–120 行）。像清单，但它同时是第 1 步"来源读全"的核对表，`none` 让读的人分得清"没有"和"漏写"；真实使用里 agent 并没有被它卡住（spec #555 的 Sources 自行加了"后端形状的示例数据"一类，没有造成问题）。保留。
- **Critical flows** 的四个分支条件（有 screen contract 才写、写 `none`、永远不能整体启动时省略、`.mmw/target.json` 尚不存在仍要写）。每一条都有 merge-note 记录的真实来源（#447 第 6 节、"从零做新产品"走流程时发现、#555）。保留。
- 第 1 步读 map 的顺序（map 正文 → Decisions so far → 每张已关票的 resolution comment → prototype 与 research file）。这不是凭空的步骤：它告诉 agent 决定存在 resolution comment 里，不在 ticket 正文里，这正是 agent 容易判断错的地方。保留。

## 脚本

to-spec 自己没有脚本。与它的产出直接相关的脚本问题：

- `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py` 第 61–66 行 `CLASS_LABELS` 与 `docs/agents/issue-tracker.md` `## Three label sets` 的表各写了一份四个层级 label 的颜色与说明，而 `mmw-v2/merge-notes/to-spec.md` 第 15 行说"颜色与说明只写在那一处"。两份现在一致，但属于类别 6 的重复。A1 落地后，建 label 全由脚本做，文档表可以只留"哪个技能打哪个 label"一列，颜色与说明以 `CLASS_LABELS` 为准。
- `verify-ticket.py` `critical_flows`（第 3245–3305 行）接受的写法比技能文本宽：`Implementation Decisions` 后面跟任意数字、"sections 2 and 3 of Implementation Decisions"、流程写在标记行上、裸的首词作流程名。技能只让 agent 写一种形状，这些宽容分支是否真有输入会走到，属于 `verify-ticket` 审查的范围，这里只记录。
- `mmw-v2/tests/verify-ticket/test_to_spec_native_parent.py` 全文是逐字检查散文的测试：它断言 `SKILL.md`、`docs/contexts/tickets/CONTEXT.md`、merge-note 和上游说明页里出现某几串英文，不测任何行为。按 `SKILL-SET-REVIEW.md` `### Redundancy and bloat` "When a third thing exists to reconcile two copies …, that is the reason to delete a copy, not to keep the reconciler"，这类测试维持的是多处副本。A1 落地后，应换成用假 `gh` 测发布入口的行为测试。

## 与其他技能的重复或交接问题

- **How a test arrives 的归属 vs `to-tickets` `references/cutting-interface-tickets.md` `## contract ticket`、`ui-acceptance` `references/story-parity.md` 第 12–14 行、`implement` `references/writing-interface-code.md` 第 27 行**：留 `to-tickets` 那一份（切票 agent 行动时加载）和 `implement` 那一份（worker 写代码时加载），spec 模板删（A3）；`story-parity.md` 那一句是否多余归 `ui-acceptance` 的审查。
- **`references/revising-a-spec.md` 的调用方**：`triage` `SKILL.md` 第 82 行、`to-tickets` `SKILL.md` 第 59 行与第 135 行、`write-screen-contract` `SKILL.md` 第 123 行、`dispatch` `references/night.md` 的 `contract` child 都按文件名指向它；这份文件改名或并回 `SKILL.md` 时要同步改这几处。交接本身没有问题。
- **merge-note 与现行文本不一致**（`SKILL-SET-REVIEW.md` `### Upstream skills` 算作发现）：
  - `mmw-v2/merge-notes/to-spec.md` 第 24 行说 "`implement` 技能靠这个节名往回读，改名要同步改 `implement`"。`implement` `SKILL.md` 现在已不提 `## Sources`；实际靠这个节名的是 `to-tickets` 模板 `## Read first`（"The implementer reads these and nothing else from the spec's Sources"）。该行应改指 `to-tickets`。
  - 第 15 行"颜色与说明只写在那一处"不成立（见"脚本"第一条）。
  - 第 58 行"接受的形状只留一种"与 `critical_flows` 的实际解析不符（见"脚本"第二条）。
- **上游说明页 `mmw-v2/upstream/docs/engineering/to-spec.md`**：它写的是上游行为，与 MMW 有多处相反（"You invoke this by typing `/to-spec`; the agent won't reach for it on its own"、"Why does the spec get the `ready-for-agent` label?"、seams "checks them with you"、"Nothing keeps it in sync … Treat it as throwaway"、"it doesn't link them"）。agent 运行本技能时不加载这一页，所以不会让 agent 做错，按任务书不列为上游问题；只提醒用户：读这一页了解 MMW 的 to-spec 会被误导。它的 `## The spec is a decision record` 一节是 B-1 草稿的来源。
- **上游原文在 MMW 里会让 agent 做错的**：没有找到。模板 `## User Stories` 的 "A LONG, numbered list … extremely extensive" 在 MMW 里没有下游读者（worker 不读 story），但本仓第 78 行"把 story 的结论折进实现小节"已经接住，不会做错，不报。

## 没查到的

- 没有全文读 `verify-ticket.py`（约 4000 行），只读了 `CLASS_LABELS`、`ensure_label`、`run_sub_issue`、`reads_as_spec`、`run_lint`、`lint_spec`、`critical_flows`；A1 说"可以复用"是按这几段推断的。
- 没有验证 `gh issue create --parent` 在挂 sub-issue 失败时是整体非零退出，还是建了 issue 却没挂上；这决定读回校验是否真有必要（我倾向保留读回，因为它便宜）。
- 没读 `mmw-v2/board/board_data.py` 读 parent 的具体代码，只用 `grep` 确认它引用了 parent；`retro.py` 第 236–241 行已读。
- B-6 的理由是推断；#444–#448 五份 spec 同一天发布，我没查它们是否出自不同 session，所以不知道"一次只写一份"在实际中是否被遵守。
- B-7 没有找到因小节不能单独读懂而出错的实例，是推断。
- 模板第 84 行末句 "Each design page's `mount` is the story page id." 的作用没弄清：它读起来像 screen contract 格式的事实陈述，而不是要 spec 写什么；没有列为发现。
- 没有查 agentflow 等其他 consuming repository 的 tracker 上 to-spec 产出的 spec。
