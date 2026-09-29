# R13 pstack 的设计精髓：为什么好改、好扩展、好复用，换到 MMW 要怎样实现

本文回答一个问题：pstack 为什么好改、好扩展、好复用。它不复述组件清单（清单在 `docs/research/workflow-compare/reports/L7-pstack-component-contract.md`，下称 L7），而是把 pstack 的做法归结为十二条精髓。每条写四件事：

- pstack 怎么做，附出处；
- 它解决什么问题；
- 换到 MMW 的宿主条件下是否仍成立，对照硬约束 H1–H6；
- MMW 要怎样实现它。

最后一节单列「为了能直接搬入 pstack 的 playbook、原则、技能，MMW 必须具备的接口」。

**材料与出处写法。**

- pstack 快照在 `docs/research/code-landing-refs/pstack/`（`.cursor-plugin/plugin.json` `"version": "0.15.4"`）。下文不带前缀、以 `skills/`、`agents/`、`automations/`、`docs/guide/` 开头的路径都相对这个目录。本轮回到原文读了：`skills/poteto-mode/SKILL.md` 全文，`playbooks/` 下的 `bug-fix.md`、`feature.md`、`authoring-a-skill.md`、`investigation.md`、`opening-a-pr.md`、`prototype.md`、`session-pickup.md`、`pause-safely.md` 全文，`agents/` 两份全文，`principle-encode-lessons-in-structure`、`principle-attack-the-premise` 全文，`setup-pstack` 全文，`figure-it-out` 开头到 Phase C，`reflect` 开头与 `references/synthesizer.md` 第 17–22 行，`show-me-your-work` `## Composing this skill`，`automations/benny/FOR_AGENTS.md` 第 1–80 行，`reproduce-and-fix-issues/SKILL.md` 第 1–60 行与 `references/control-adapter.md` 第 1–60 行，`docs/guide/02-poteto-mode.md` 第 1–80 行、`07-overnight.md` 第 1–70 行、`09-make-it-yours.md` 全文。其余 pstack 内容只经 L7 引用，引用时注明「L7」。
- MMW 一侧的事实，凡是 `R4-mmw-architecture-form.md`（下称 R4）第 1 节 V1–V17、`R12-mmw-master-placement.md`（下称 R12）第 1 节 M1–M30 已核实的，直接引用编号。本轮另外回到原文核实的，写明文件与行号。R4、R12 的结论（只 1 份头部 playbook、5 个角色流程留在能力技能里、2 条原则等）不采用，理由见第 2 节 E12。
- 清点报告 N1–N10 只作线索，采用处已回原文核实；`N11-mmw-gaps.json` 列出的错误都不采用。

**标注。**「原文」＝文件里写着的；「已核实」＝本轮回到原文或跑命令看到的；「推断」＝由原文推出、原文没直接写；需要实测才能定的放第 5 节「未确定」，并写明怎么测。

**硬约束编号**（任务给定，只有这些算约束）：

- H1 宿主不换（Claude Code、Codex、Grok、Pi、Cursor；runner 用 Orca 等）；MMW 所在宿主没有 Cursor 的 `mode: true` / `reminder` 常驻机制。
- H2 Claude Code 上，带 `disable-model-invocation: true` 的技能不在模型的技能列表里，模型按名也调不到（R4 V1）；description 在宿主启动时扫入，改动要新会话才生效。
- H3 一个会话里派出的子 agent 跑在本会话所在宿主的模型上；跨厂商模型只能另起会话（`dispatch.sh start` / `advise`）（`docs/adr/0015-no-custom-subagents.md` `## Consequences`）。
- H4 脚本送进活会话的一条消息必须是一行（`mmw-v2/skills/dispatch/scripts/watchdog.py` 第 813 行，R12 M1）。
- H5 Self-hosting boundary：一次 watch 期间冻结已安装版本；运行中的流程不读工作树里正在被改的版本（根 `AGENTS.md` `## Self-hosting boundary`）。
- H6 夜里的会话屏幕前没人，不能向人提问。

---

## 0. 结论（先读这里）

1. **pstack 好改、好扩展、好复用，根源只有一条：每一类决定只有一个家，家与家之间只按名字、单向连线。**
   - 「先做什么后做什么」的家是 playbook；「一件事怎么做」的家是能力技能；「跨任务怎么判断」的家是原则；「每次结果都一样的状态与检查」的家是脚本；「哪个角色用哪个模型」的家是配置；「遇到 X 用 Y、自主权到哪、回复怎么写、任务该走哪个 playbook」的家是 mode。
   - 改一类决定只动一层；加一个组件只是加一个文件、在上一层加一行登记。
   - 这不是「把一切拆开」。pstack 大量内容没拆（L7 C.2–C.5），但没拆的都是「一件事怎么做」的细节留在唯一的调用方里。没有一处把「先后顺序」或「谁调用我」写进能力技能（L7 B.2 硬规律第 3 条）。
2. **MMW 今天在这条根源上是反的。**
   - 「下一步」的家是能力技能的结尾段。这是明文规定：`SKILL-SET-RULES.md` 事实 7「A skill's place follows from its own text: its description says when it starts, and its closing section says what comes next」，同一条还写着「this is why MMW ships no router skill」（第 17 行，R12 M8）。
   - 能力技能知道自己被谁调用。例如 `implement/SKILL.md` 第 99 行「Open no pull request: the orchestrator lands the ticket」，`verify-ticket/SKILL.md` 第 16 行「A worker's claim, criteria runs and closeout are steps of the `implement` skill.」，`retro/SKILL.md` 第 186 行「return to the dispatch skill's `references/night.md` `## 5`」（本轮已核实）。
   - 流水线顺序写进了上游文本。上游 subtree 相对 squash `5b1a4c51` 改了 +1674/−415 行（R12 M5）。N10 第 6 节的结论是：除 `code-review`、`prototype`、`resolving-merge-conflicts` 三处扩了能力，其余上游改动「全部是把 MMW 的流程写进上游文本」。
   - 跨任务的判断没有自己的层，散在 ADR（`0008-silence-is-never-a-pass.md`）、用户级提示词 `mmw-v2/prompt/shared.md`、`SKILL-SET-RULES.md`、`CODING_STANDARDS.md` 与各技能正文里。
   - 所以真正的升级不是「加一个 mode」，而是把这个方向倒过来。改造前后最直观的区别就是：能力技能里再也没有「下一步」「谁调用我」「我在流水线第几步」这类句子；这些句子全部集中到 playbook。
3. **pstack 的十二条精髓里，有八条可以原样在 MMW 成立，四条要换实现，没有一条因硬约束整体作废。**
   - 原样成立（文本组织层面的规则，与宿主无关）：E1 分层、E2 单向连线、E3 能力技能不知道调用方、E4 playbook 只编排、E5 原则只被点名、E8 脚本只管确定性部分、E11 教训按层回流、E12 不拆的纪律。
   - 要换实现：
     - E6 mode 常驻：H1 没有 `mode: true`。改成三条到达路径：脚本启动的会话由启动提示词点名 mode；人启动的会话由模型可触发的 description，加每回合一行的 hook 提醒（MMW 已在五个宿主装 hook）。
     - E7 执行协议：H6 夜里没人看 todo。跳过的步骤与理由写上票，写进早上有人读的地方。
     - E9 模型角色：H3 子 agent 不能换厂商。角色配置只对另起的会话生效，跨厂商面板要靠另起会话的脚本。
     - E10 自动化包：夜间流水线就是 MMW 的自动化包。它的操作文件是 playbook，不是能力技能。
   - 只有一种连线方式按硬约束不能照搬：pstack 运行中从 trunk 重读 playbook（`autopilot-full.md` 第 6 步，L7 B.1）。它与 H5 正面冲突。
4. **R4、R12 的保守结论来自对 L7 C.1 第 7 问（单一入口的自动化用一个操作文件）的误用。**
   - benny 的操作文件不注册成技能，也不被当作能力复用（`automations/benny/FOR_AGENTS.md` 第 31 行「its `SKILL.md` files are direct automation instructions, not registered plugin skills」）。它们占的是 playbook 那一层：规定顺序、不被别处调用。
   - MMW 的 `implement` 却同时是上游能力技能的名字，又是 worker 的操作文件。R4 以第 7 问为由把它留在能力技能层，实际是把两层压成一层。
   - 正确的读法是：worker、reviewer、orchestrator、单票 orchestrator 的操作文件都是 playbook，放进 playbook 层；同名的上游能力技能回到原文。第 2 节 E10、E12 展开。
5. **要能直接搬入 pstack 的组件，MMW 需要十六个接口**（第 4 节）。最关键的五个：
   - mode 目录照 `poteto-mode/` 的布局放 `playbooks/`、`principles/`、`references/`、`scripts/`，让 pstack 文件里的相对路径不改就能解析；
   - 原则是 mode 目录下的普通文件，不是技能。H2 让带 `disable-model-invocation` 的技能在 Claude Code 上按名调不到，而 pstack 的原则全都带这个键；
   - 三个「槽位」：control（驱动界面）、delivery（交付改动，替代 pstack 处处依赖的 PR）、forge（代码托管命令）。调用方只点名槽位，由 mode 的一张表或消费仓库配置解析到具体技能或命令；
   - 模型角色：`models.json` 扩出 pstack 的角色标签，并提供一条只读查询命令。「your configured <角色> model」在 MMW 上要能查到值，而且要写明 H3 下它只对另起的会话生效；
   - 外来组件按上游的做法以 subtree 引入，装一行 `skills.txt`，改动写 merge-note，机械改写由一个导入脚本做。
6. **pstack 自己也有写错的地方**（L7 E.1 共 31 条）：按步骤编号跨组件引用、原则引用五种写法、角色配置没有解析器、本地闸门与上层授权冲突却没写优先级。MMW 不照抄这些，而是按 pstack 自己的 `principle-encode-lessons-in-structure` 把它们做成 lint。MMW 已有 `mmw-v2/tests/lib/` 下每个套件先跑的三个检查（根 `AGENTS.md` Commands 表），在这里加规则是现成的做法。

---

## 1. 总的回答：从「加一个东西要动几处」看 pstack 与 MMW

### 1.1 一句话

pstack 把每一类决定放进唯一的一层，层与层之间只按名字、单向连线（L7 第 0 节第 1 条、B.2）。这带来三个性质：

- **好改**：改一类决定，只改它那一层的一个文件。例：改 Bug fix 的顺序只改 `playbooks/bug-fix.md`；改「怎么做设计比较」只改 `skills/architect/`。
- **好扩展**：加一个组件，只是加一个文件，外加上一层的一行登记。例：加一种任务类型＝一个 playbook 文件加 mode 路由表一行（`skills/poteto-mode/SKILL.md` 第 121–143 行，每行一个 playbook）；加一条原则＝一个原则文件加 mode 索引一行（第 41–77 行）。
- **好复用**：能力技能不知道是谁调用它，所以 mode、playbook、agent 定义、别的技能、自动化包都能按名字调用它（L7 A.3「能力技能一般不知道是谁在调用它」；benny 按名复用 `how`、`why`、`tdd`、`unslop`，`FOR_AGENTS.md` 第 32 行）。

### 1.2 对照表：做同一件事，要动几处

| 要做的事 | pstack | MMW 现在 | MMW 现在的出处 |
|---|---|---|---|
| 加一种任务类型 | 1 个 playbook 文件，加 mode 路由表 1 行 | 新技能或改现有技能的 description；改上一个技能的结尾段让它指过来；改下一个技能的入口；可能要改上游文本并补 merge-note；再按事实 7 通读「从想法到关票」的整条结尾段链，确认无缝 | `SKILL-SET-RULES.md` 事实 7；`### Hand-offs` |
| 改一段流程的顺序 | 1 个 playbook 文件 | 界面链一跳一句，分在 5 个文件：`prototype` `UI.md` `## Next`、`design-pages` `edit-pages.md` `## Next`、`pull.md` `## Reached from here`、`write-screen-contract` `## Next`、`to-spec` | N10 第 9 节「界面链的结尾段」 |
| 加一条跨任务的判断 | 1 个原则文件，加 mode 索引 1 行 | 没有这一层。现有的判断写在 ADR（0008）、`shared.md`、`SKILL-SET-RULES.md`、`CODING_STANDARDS.md` 与各技能正文 | 本文 E5 |
| 换某个角色的模型 | 重跑 `setup-pstack`，覆盖一个文件（第 5 步） | `models.py config set`，改 `~/.mmw/models.json`（`dispatch/references/editing-models.md`）。**MMW 这里更好**：有解析器、有校验、只一个写者。但只对另起的会话生效（H3） | 本文 E9 |
| 在一条新自动化里复用一项能力 | 按名调用，如 benny 用 `how`（`FOR_AGENTS.md` 第 32 行） | `code-review` 的 description 是「Review of one ticket's diff」，`implement` 第 99 行假定有 orchestrator 来 land。离开夜间流水线复用，会把票的语义一起带过去 | 本轮已核实 |
| 拉一次上游更新 | 不适用（pstack 自己就是源头） | 上游文本里有 +1674/−415 行本仓改动（R12 M5），拉一次就在这些段落上冲突一次 | R12 M5 |
| 搬入一个外来 playbook | 不适用 | 没有 playbook 层可放 | — |

这张表就是「改造前后有没有区别」的检验：改造后，MMW 这几行都应当变成 pstack 那一列的样子（换模型那一行保留 MMW 的做法）。

### 1.3 pstack 自己没做好、MMW 不要照抄的部分

以下都出自 L7 E.1，逐条有原文实例：

- 按步骤或阶段编号跨组件引用，没有任何检查（E.1 第 2 条）。例：mode 第 25 行「(Feature step 3)」、`blast-radius` 的「Use `why` step 2」。
- 原则引用至少五种写法（第 1 条）。
- mode 第 143 行「Invoked at the end of every other playbook」与实际不符：23 个 playbook 里只有 7 个以 Opening a PR 收尾（第 3 条）。
- 角色配置没有任何脚本解析，标签对不上全靠模型理解（L7 D.4）。
- 能力技能的本地闸门与上层授权冲突，没写优先级（第 18 条）。例：`bugbot-triage.md`「When in doubt, ask.」与 `autonomous-run.md` 第 4 步「Do not park reversible work for the human」。
- 外部插件依赖（`deslop`、`control-ui`、`control-cli`）没有安装检查（第 27 条）。

按 pstack 自己的 `principle-encode-lessons-in-structure`（「Encode the rule as a lint, metadata flag, runtime check, or script instead of more text」），MMW 应当把「只按名连线、方向单一、不按编号引用、原则引用一种写法、外来依赖可解析」做成 lint，而不是写成更多规则文字。第 2 节 E2 展开。

---

## 2. 十二条精髓

### E1 按「谁决定」分层，而不是按「有没有步骤」分层

**pstack 怎么做。**

- L7 第 0 节第 1 条：「pstack 按『谁决定顺序、给谁复用』分层，不按『有没有步骤』分层。」阶段型技能 `architect`、`arena` 也有 todo 和阶段，但它们仍是能力技能（L7 C.3）。只在 playbook 之间复用的流程仍是 playbook（babysit、shipping、opening-a-pr、prototype，L7 A.2）。
- 每层回答一种问题：
  - mode：遇到 X 用 Y、原则索引、自主权、子代理默认、回复写法、执行协议、路由表（`skills/poteto-mode/SKILL.md` 的 8 个 `##` 节，原文）；
  - playbook：一类任务里能力的先后、门槛、谁拥有什么、何时停、交什么回复（L7 A.2）；
  - 能力技能：一项可以命名的能力或交付物（L7 A.3）；
  - 原则：跨任务的判断（L7 A.4）；
  - 脚本：确定性的状态与检查（L7 A.6）；
  - 配置：角色到模型的绑定（L7 A.8）；
  - guide：给人读，不被 agent 加载（L7 A.9）。

**解决什么。** 一次改动的影响范围可以预测。改「顺序」不会碰到「做法」，改「做法」不会碰到「顺序」。`docs/guide/02-poteto-mode.md` 的 Pitfall 写的正是反面：「a hand-written sequence usually reorders or drops steps the playbook would have kept」（L7 A.2）。

**换到 MMW。** H1–H6 都不影响。这是文本怎么组织的规则，与宿主机制无关。

**MMW 要怎样实现。**

- 给 MMW 的每段内容按「谁决定」归层。判别问题是：这段内容决定的是顺序、做法、判断、确定性状态、模型绑定，还是「何时进入哪条路」？
- 当前最大的错位有三处，改造必须全部处理：
  1. **顺序写在能力技能的结尾段。** N10 第 1 节「结尾段」一行列了 15 处。这些句子全部搬进 playbook；能力技能以「把什么交还调用方」结尾（pstack 的 `## Output Format`、`**Reply:**`，L7 A.3）。
  2. **角色知识写在能力技能里。** `implement`、`verify-ticket`、`code-review`、`retro`、`ui-acceptance` 的 description 或正文里都有「worker」「orchestrator」「night」。这些句子搬进对应角色的 playbook。
  3. **判断散在五处**（ADR、`shared.md`、`SKILL-SET-RULES.md`、`CODING_STANDARDS.md`、技能正文）。凡是满足原则四条门槛的（E5），进原则层。
- `SKILL-SET-RULES.md` 事实 7 里「a skill's place follows from its own text ... its closing section says what comes next」一句直接作废，改为「一个技能的位置由 playbook 决定」。这一句原本防两件事：第二份副本漂移，某一跳找不到下一步（N10 第 7 节、#538）。新做法下，顺序只有一个家（playbook）；用 lint 保证每个 playbook 步骤点名的组件存在（E2），两件事都防住了。

### E2 只按名字连线，方向单一

**pstack 怎么做。**

- 连线方式（L7 B.1）：相对路径（mode 到 playbook，技能到自己的 `references/`、`scripts/`）、粗体名字（「the **how** skill」「Run **Opening a PR**.」）、斜杠名、`subagent_type`、脚本命令、角色槽位（「the matching control skill」）、注入。
- 方向（L7 B.2「方向上的硬规律」）：
  1. 原则只指向原则，或往下指向能力技能；
  2. 脚本不往上调用任何东西；
  3. 能力技能不依赖 playbook。唯一例外是 `recall` 第 1 步往外分流到 session-pickup（L7 A.3）。
- 统计（L7 B.3，量级）：playbook → 能力技能 47 条、playbook → 原则 44 条、能力技能 → 原则 25 条。反向的「能力技能 → playbook」几乎为 0。

**解决什么。**

- 依赖图从上往下走。换掉、删掉或引入一个能力技能，只影响点名它的上层文件，这些文件用 grep 就能找全。
- 下层组件不因上层重组而改动。pstack 加了 23 个 playbook，没有一个能力技能因此改过（推断：能力技能正文里不出现 playbook 名字，L7 B.2 表「能力技能 → playbook：仅往外分流」）。

**pstack 在这条上最脆弱的地方**：按步骤编号跨组件引用（L7 E.1 第 2 条；C.6 信号 8「这正是它最脆弱的连线」）。步骤一重排，引用就指错，而且没有检查。

**换到 MMW。**

- H2 影响「按名字」的含义。pstack 的能力技能与原则全带 `disable-model-invocation: true`（47 个里 46 个，L7 A.3），仍能按名调用。在 Claude Code 上，这样的技能不在模型列表里，按名调不到（R4 V1）。所以 MMW 里「按名字连线」只能落在两种形式上：
  - 模型可触发的技能（在列表里）按名调用；
  - mode 目录下的普通文件按相对路径读取（playbook、原则、reference）。
- H5 不影响：名字解析到已安装 checkout 的软链（`~/.agents/skills/<名>`、`~/.claude/skills/<名>` 都指向 `.worktrees/mmw-installed`，本轮已核实），天然是冻结版本。
- H4 影响脚本送进活会话的指针：它必须和消息同在一行（R12 K-1）。

**MMW 要怎样实现。**

- 方向写成三条规则，由 lint 强制：
  1. 能力技能正文不出现 playbook 名、角色名（worker、reviewer、orchestrator）、`night`、票号语义；
  2. 原则只指向原则或能力技能；
  3. 脚本不写技能正文里的小节标题。现在 `watchdog.py` 第 735、780 行写「night.md's Exit codes of resume」（R4 V2），这是脚本往上指。R12 K-2 的锚点表 `anchors.py` 可以保留，但作用要变：它是脚本唯一点名文本锚点的地方，lint 核对锚点仍存在。
- 跨组件引用一律按名字或小节标题，禁止按步骤编号。MMW 已有同类教训：`implement/references/writing-interface-code.md` 三处按编号写「closing step 1」（R12 M30）；`design-pages/SKILL.md` 第 25 行按编号写「the `prototype` skill's `UI.md` step 6」（R12 M13）。
- 这个 lint 与 `check_module_paths.py` 同类，放进 `mmw-v2/tests/lib/`，每个套件先跑。这是 pstack 缺的那一环（L7 E.1 第 2、17 条）。

### E3 能力技能不知道是谁调用它

**pstack 怎么做。**

- 原文 `README.md` 第 97 行：「`/poteto-mode` runs most of these for you when a step needs them ... the table below is for when you want one directly」（L7 A.3）。
- 能力技能以交付物结尾：`## Output Format`（how、why、interrogate）、`**Reply:**`（teach）、`## Output contract`（recall）等（L7 A.3）。不写「然后去做 X」。
- 能力技能自带人工闸门，因为它可以脱离 mode 被单独调用（L7 A.3「自带人工闸门」，推断）。例：`interrogate` Step 2「If you're unsure about the intent, ask the user before proceeding.」
- 编排别的技能不会让它变成 playbook（`skills/automate-me/SKILL.md`「It sequences them. It doesn't replace them.」，L7 第 0 节）。判别在于：它产出一个可以命名的交付物，而且能脱离 mode 被直接调用（L7 C.3）。

**解决什么。** 复用。同一个 `how` 被 15 个调用方用（L7 B.3），包括 mode、playbook、agent 定义 Comment Sicko（`agents/comment-sicko.md` 第 26 行「I run `/how`, `/why`」）和 benny。一项能力改进一次，所有调用方都得到改进；加一个调用方不用改这项能力。

**换到 MMW。** H1–H6 都不影响这条规则本身。H2 只决定「能力技能要不要保持模型可触发」，这是接口问题，见第 4 节 I-9。H6 要求上层写明优先级：夜里的授权盖过能力技能的本地人工闸门（见 E6）。

**MMW 要怎样实现。**

- 每个能力技能用一个问题自检：离开 MMW 的流水线，在一个没有 `.mmw/`、没有票的仓库里，它还能用吗？不能用的句子不属于它。
- 按这个判据，MMW 现有的违例（本轮核实的原文，逐条）：
  - `implement/SKILL.md`：上游原文全文 15 行、正文五行，只点名 `tdd`、`code-review`（`SKILL-SET-RULES.md` 事实 4「Upstream's `implement` is five lines」）；现状 101 行（N10 第 6 节），第 23 行的 `--sub-issue decision`、第 74 行的 `RESUME:`、第 99 行「the orchestrator lands the ticket」都是 worker 角色的流程。
  - `verify-ticket/SKILL.md` 第 16 行把 worker 送回 `implement`。
  - `retro/SKILL.md` 第 186 行返回 `night.md` `## 5`。
  - `to-spec` 第 125–127 行 `## Next`「The `to-tickets` skill.」，`to-tickets` 第 160 行交给 `dispatch`（R12 M14）。
  - `ui-acceptance` 的 description「before writing a page ticket's code」与表第 1 行把读者送回 `implement` 的 reference（N10 B7）。
  - `dispatch` 的 description「Start a reviewer from inside a ticket」，表第 1 行写「No file: the `implement` skill's `## Closing steps`」（`dispatch/SKILL.md` 第 3、16 行，本轮已核实）。
- 这些句子不是删掉，而是搬进 playbook 的步骤。能力技能留下「怎么做」与「交回什么」。
- 能力技能自带的闸门保留，由 mode 写一句优先级：playbook 给出的授权盖过能力技能的本地闸门。pstack 缺这一句（L7 E.1 第 18 条）；R4 采用了 R2 的「层级优先级句」（R4 第 0 节第 1 条），这一点保留。

### E4 playbook 只编排

**pstack 怎么做。**

- 固定骨架（L7 A.2，原文）：`### <名字>`；粗体所有权行 `**You own ... **`；可选首段写本类任务的纪律；4 到 9 个编号步骤，每步首句是一个可以勾掉的祈使动作；可选尾段写边界与转交；末行 `**Reply:**` 只写本 playbook 独有的回复内容。范例 `playbooks/bug-fix.md` 全文 15 行（本轮已读）。
- 步骤里调用技能、点名原则、跑脚本、读 reference、交接给别的 playbook，但不复述技能的做法：`authoring-a-skill.md` 第 10 行「Delegate to other skills by path. Don't restate.」
- 可以装只属于这类任务的做法（patch-id 规则在 `shipping.md` 第 3 步）；长 playbook 用 `####` 规则簇放常设规则，只有 `#### Steps` 抄进 todo（`orchestrate.md`，L7 A.2、D.1）。
- 回复写法的通用部分在 mode，每个 playbook 只写独有部分：mode 第 109 行「The per-playbook lines below name only the content unique to that playbook.」
- mode 路由表每行一种格式：`- **<名字>.** <任务类型定义>. [用户原话]. [Distinct from ...]. [交付物限定]. \`playbooks/<file>.md\`.`（L7 A.1）。「Distinct from」一句专门防止两个 playbook 抢同一个请求（例：mode 第 124 行 Hillclimb「Distinct from Perf issue, which is a one-off fix.」）。

**解决什么。**

- 顺序只有一个家。加一个 playbook 不改任何能力技能，改一个 playbook 的顺序不影响别的 playbook。
- 固定骨架让任何一个 playbook 都能被新 agent 当作待办清单执行（E7）。

**换到 MMW。**

- H5：pstack 允许运行中从 trunk 重读 playbook，MMW 不行。MMW 的 playbook 从已安装 checkout 读，整个 watch 期间是同一版本。这不影响「playbook 只编排」本身。
- H6：夜间 playbook 的读者在屏幕前没人，而且会被压缩、被唤醒。pstack 的 playbook 没有「重入」这一节，只有 session-pickup 一个入口（`playbooks/session-pickup.md`）。MMW 需要多一样东西：由脚本算出「现在在哪一步」，按步骤标题指回 playbook。MMW 已有这个机制：`verify-ticket.py --preflight` 印 `RESUME:`（`implement/SKILL.md` 第 74 行），R12 K-3 让 `dispatch.sh status` 印同类的行。
- H4：唤醒消息里指回 playbook 的指针要和消息在同一行（R12 K-1）。

**MMW 要怎样实现。**

- 新建 playbook 层：`mmw-v2/skills/mmw/playbooks/<slug>.md`，骨架照 pstack：`### <名字>`、所有权行、编号步骤、`**Reply:**`。
- MMW 多一个可选段 `**Where you are.**`，只在跨会话、会被唤醒的 playbook 里有。它说明怎样读脚本印出的 `RESUME:`，而不是自己列一张事实表。R4 第 6 节的 playbook 模板已有此段，形式可以沿用。
- MMW 的每一种工作流都是一个 playbook。判据是 E1：它决定的是不是「一类任务里各种能力的先后」。按这个判据，至少下列工作流是 playbook：
  - 白天定义：从想法到票；
  - 夜间编排：`night.md` 的内容；
  - 单票编排：`one-ticket.md` 的内容；
  - 做一张票：worker，即 `implement` 现在的正文；
  - 评审一张票：reviewer，即 `code-review/references/session.md` 的票协议部分；
  - 自己接手一张票：`dispatch/references/inside-a-ticket.md`；
  - 早上验收与 finish；
  - 修 bug（`diagnosing-bugs` 之后接什么）；
  - 出包；
  - 分诊（`triage` 第 5 步的「接着写 spec、切票」）；
  - 调研；
  - 给仓库接入 MMW；
  - 写或改技能。
- 逐个是否成立、合并还是拆开，由下一轮按 E1、E12 的判据定。本文只定判据。
- 路由表格式照 pstack，每行带「Distinct from」。MMW 现在最需要它的地方：`wayfinder`（「Not for a well-scoped feature」）、`grilling`、`to-spec` 三个 description 在争头部请求（N10 B1、B2）。

### E5 原则只被点名，不被调用

**pstack 怎么做。**

- `docs/guide/08-principles.md`：「You don't invoke principles. You use their names to steer.」（L7 A.4）。
- 原则文件很短，形态是「情境触发 + 一条规则 + 理由」。23 个文件在 16–34 行之间（L7 A.0）。模板：`# <Title>`、一到三句规则、`**Why:**`、`**Pattern:**`，可选 `**Stop:**`、`**The test:**`、「Distinct from ...」。范例 `principle-attack-the-premise`（本轮已读，23 行）。
- mode 的 `## Principles` 是索引，每条写「显示名、slug、何时适用、一句要点」，分五组（mode 第 37–77 行）。原则全文只在应用时读：「Read the leaf skill in full for any principle you apply.」（第 39 行）。
- 回复里必须点名改变了决定的原则：「name each principle that shaped a decision and the specific choice it changed. Cite only principles whose leaf SKILL.md you read this session.」（mode 第 15 行）。
- 调用方可以限定原则在本处的范围，不必为每个例外改原则（L7 C.2）。例：`no-comments` 第 22 行「... guide intent only. Neither authorizes widening the fence」；`prototype.md` 第 5 行「The one playbook where the Laziness Protocol's 'smallest change' and the verification bar invert.」
- 门槛（L7 A.4，推断）：能用短名字说出口；有可观察的触发情境；能改变一个具体决定；跨任务。「被按名复用」不是前提：`principle-attack-the-premise` 按名引用为 0。
- 分层规则的唯一原文：`principle-encode-lessons-in-structure` 第 25 行「Route to the right layer. One-off -> brain note. Recurring fix -> skill or lint rule. Systemic issue -> principle.」

**解决什么。**

- 跨任务的判断只写一次，每个用它的地方只写一个名字。判断改了，只改原则文件。
- 点名义务让判断可审计：读回复的人看得到「哪条原则改变了哪个决定」。
- 引入外来判断的成本极低：一个文件加索引一行。用户要搬 pstack 的原则进来，靠的就是这一点。

**换到 MMW。**

- H2 直接影响形式。pstack 的原则是带 `disable-model-invocation: true` 的技能。照搬到 MMW，Claude Code 上的模型按名调不到它们。所以 **MMW 的原则必须是普通文件**，放在 mode 目录下，由 mode 与 playbook 按相对路径读取。R4 第 0 节第 9 条已经这样定，这一点正确。
- 反过来，如果把原则装成模型可触发的技能，23 个 description 会进每个会话的技能列表，与 pstack「只被点名、不被调用」的设计相反，也会与能力技能的 description 抢触发（`SKILL-SET-RULES.md` `### Descriptions` 第 2 条「Two descriptions that claim the same job are a conflict」）。所以不走这条。
- H6 不影响：夜里的 agent 同样读原则文件。

**MMW 要怎样实现。**

- 位置：`mmw-v2/skills/mmw/principles/<slug>.md`。
- 文件格式与 pstack 相同，保留 pstack 的 frontmatter 两个键 `name`、`description`（第 4 节 I-7）。这样 pstack 的原则文件搬进来只需要改文件名，正文不改。
- mode 的 `## Principles` 索引由各原则文件的 `description` 生成，或由 lint 核对二者一致。这样修掉 pstack 的「一句话摘要在四处重复、措辞不一」（L7 E.1 第 14 条）。
- MMW 自己已有、满足四条门槛的判断，是原则层的第一批来源。只作线索列举，是否成立由下一轮逐条按门槛判定：
  - ADR 0008 的「一道闸口跑了一遍却什么都没做，有人会发现吗」（`docs/adr/0008-silence-is-never-a-pass.md` 第 8 行）；
  - `dispatch/SKILL.md` 第 8 行「Where you are is what the ticket's events say, not what this session remembers.」；
  - `shared.md` 规则 11「When a step fails or is interrupted, redo it yourself before replying」；
  - `SKILL-SET-RULES.md` 事实 2「Scripts carry what is deterministic; text carries judgement.」
- R12 只建 2 条，理由是「只加在 5 处本地没写理由的句子上」（R12 K-9）。这不是 pstack 的门槛：pstack 不以「现在有多少处引用」决定一条判断要不要成为原则（L7 A.4）。
- 点名义务照搬：回复里点名改变了决定的原则。对无人会话，写在它交出的产物里（票上的 closeout、reviewer 报告），因为早上的读者读的是这些（E7）。
- 原则与 `shared.md` 的关系：`shared.md` 是用户级、跨所有项目的常驻规则，层级高于 MMW 的 mode。它的「谁决定什么」「怎么汇报」对应 pstack mode 的 `## Autonomy` 与 `## Writing the reply`（对照 `shared.md` 规则 1、2、4–9 与 mode 第 79–109 行）。MMW 的 mode 不复述它，只写 MMW 独有的部分。

### E6 mode：集中路由，集中常驻纪律

**pstack 怎么做。**

- 一个 mode 文件持有所有「跨 playbook 的东西」（L7 A.1）：
  - `## Non-negotiables`：17 条「条件 → 技能名或 playbook 名」触发（mode 第 19–35 行）。例：「Nontrivial change, architecture decision, or "are we sure?" → the **how** skill.」「Any PR-status request → the **Babysit** playbook ..., and not Cursor's built-in babysit skill, whose description matches the same words.」
  - `## Principles` 索引；
  - `## Autonomy`：「**Just do it.**」「**Always pause** for irreversible writes」「**Session overrides:** "Don't stop" / "going to bed" ... → keep going.」（第 81–85 行）；
  - `## Subagents`：用哪个 `subagent_type`、每个 `Task` 的默认参数、模型角色的优先级（第 91–95 行）；
  - `## Writing the reply`、`## Comments`；
  - `## Playbooks`：执行协议、升级路由、路由表（第 117–143 行）。
- 路由目标不只有 playbook：大任务或无匹配时路由到能力技能 `figure-it-out`（第 119 行）。
- 常驻靠 Cursor 专有的 `mode: true` 与 `reminder:`（frontmatter 第 5、8 行）。`reminder` 原文：「New task? Playbook match or rigor needed -> apply /poteto-mode. Casual turn or user opts out -> don't.」
- 子代理也要读 mode：`agents/poteto-agent.md`「Read the `poteto-mode` skill's `SKILL.md` in full before doing any work」；mode 第 91 行要求 playbook 步骤里派的子代理都用它。
- 重新匹配只在用户说「new task」时发生（`docs/guide/02-poteto-mode.md` 第 56–64 行）。

**解决什么。**

- 「遇到 X 用 Y」集中一处。触发条件不再散在各技能的 description 里互相抢；Non-negotiables 第 31 行甚至专门写了「不要用 Cursor 内置的同名技能」来消歧。
- 所有执行者（主会话、子代理）在同一套常驻纪律下工作。
- 新 playbook 只加一行路由，别的都不用改。

**换到 MMW。**

- H1：MMW 的宿主没有 `mode: true` / `reminder`。常驻要换机制。
- H2：mode 若带 `disable-model-invocation: true`，Claude Code 上模型按名调不到它，脚本启动的会话就没法「Use the mmw skill」。所以 **MMW 的 mode 必须是模型可触发的技能**。代价是它的 description 进每个会话的技能列表，与任何一个技能相同，是一行。
- H3：pstack 的 `poteto-agent` 是注册的子代理类型。MMW 按 ADR 0015 不交付子代理，只用宿主的通用子代理。等价物是：派子代理的简报第一句要求读 mode 的指定小节（`poteto-agent.md` 的正文本来就只有这一句）。
- H6：夜里没人说「going to bed」。MMW 的无人会话是脚本启动的，「无人」是已知事实，不需要靠用户的原话来触发。
- ADR 0014 否决过把调用方侧规则写进 `shared.md`，两条理由：到不了 Cursor；为偶发之事付每回合的常驻上下文（R4 V16）。这两条理由约束的是「写进 `shared.md`」这一种做法，不约束 mode 本身。

**MMW 要怎样实现。**

- **一个 mode 技能 `mmw`**，模型可触发。章节照 pstack，只放 MMW 独有的内容：
  - `## Non-negotiables`：跨 playbook 的触发。MMW 里已有的来源是各技能 description 中「在某个时刻用我」的部分。例：`ui-acceptance`「before writing a page ticket's code」、`advisor`「before an architecture choice ... is committed」、`resolving-merge-conflicts`「when a clean merge makes the repository checks fail」。这些触发搬进 mode，description 只留「这项能力是什么、直接调用时怎么说」。这顺带消掉 N10 B7 的三处往返。
  - `## Principles` 索引。
  - `## Autonomy`：人在场与无人两种会话。无人会话的授权与 `tool-guard.py` 的 `NO_QUESTION` 出路写在这里，一处。现在 `dispatch.sh` 第 108 行 `AUTONOMOUS` 常量把这条规则放在启动提示词里，`SKILL-SET-RULES.md` `### Prompts written for other agents` 要求「规则经技能到达」，二者本就冲突（N10 第 8 节）。搬进 mode 后，启动提示词只说「unattended」这一数据。
  - `## Subagents`：派子代理的简报模板，第一句「Read the `mmw` skill's `## Principles` and the playbook step you are serving」；H3 下模型角色的边界。
  - `## Playbooks`：执行协议（E7）、路由表、层级优先级句。
- **三条到达路径**：
  1. **脚本启动的会话**：启动提示词点名 mode 与 playbook，例如「Use the mmw skill; your playbook is `playbooks/work-a-ticket.md`; ticket #n」。这条路径是确定的，不依赖任何宿主行为。R4 第 0 节第 4 条「脚本启动的会话不经过 mode」要反过来：worker 也要在 mode 的常驻纪律下工作，这正是 pstack 用 `poteto-agent` 保证的事。
  2. **人启动的会话**：mode 的 description 可被模型触发（覆盖 N10 B1「头部没有模型可达的入口」）。
  3. **每回合提醒**（pstack `reminder` 的替代）：一个 prompt 提交时触发的 hook，只在当前仓库有 `.mmw/` 时打印一行提醒。
     - 可行性已有基础：MMW 已在五个宿主各装 hook（`mmw-v2/install.sh` 第 314 行注释：claude 的 Stop、cursor 的 stop、pi 的 `agent_settled`；第 676–700 行登记 `PreToolUse` 与 `Stop`）。Codex 的事件表里有 `UserPromptSubmit`（第 768–774 行 `CODEX_LABELS`）。
     - 这条做法回应了 ADR 0014 的两条理由：非 MMW 项目不打印，所以不付费；Cursor 有自己的 hooks 文件（第 696 行）。
     - 各宿主有没有 prompt 提交事件，属于未确定，见第 5 节 U-2。
     - R4 选的「消费仓库 `AGENTS.md` 加一行」可作第四条备用路径，但它依赖「模型会照一行文字去加载技能」这一宿主行为，不如 hook 确定。
- **优先级写明**：用户级 `shared.md` > mode > playbook > 能力技能的本地闸门。pstack 没写（L7 C.2「pstack 没有写明哪一层优先」，E.1 第 30 条），MMW 要写。

### E7 执行协议：步骤抄进待办、跳步写理由、回复点名改变决定的原则

**pstack 怎么做。**

- mode 第 117 行原文：「Open a todolist whose first items are the matched playbook's steps, copied in verbatim, before any task-specific todos. A step you choose not to do stays in the list with a one-line `skip: <reason>`.」
- 理由（原文）：`docs/guide/01-setup.md` 第 45 行「so you can see what it chose not to do」；`02-poteto-mode.md` 第 38 行「A skipped step stays visible with `skip: <reason>`.」
- 变体：`feature.md` 第 3 步不适用的项写 `n/a: <reason>`；第 4 步「Mandatory: no skip-with-reason escape」禁止跳过（本轮已读）。
- 只有编号步骤进 todo，规则簇和模板不进（L7 D.1，推断）。
- 回复点名原则的义务（mode 第 15 行），见 E5。
- 长任务的决策轨迹交给 `show-me-your-work`（mode 第 35 行），它持有日志格式：「Other skills route their audit trail here instead of inventing one. Reference it by name and let it own the format. Don't restate the columns.」（`show-me-your-work` 第 81 行）。

**解决什么。**

- 模型最常见的失败是自己排顺序、悄悄漏步骤（guide 02 Pitfall）。逐字抄写让 playbook 的顺序真的被执行。
- 「跳过」变成可见的决定，不是沉默的遗漏。这与 MMW ADR 0008 同一个问题：「它跑了一遍却什么都没做，有人会发现吗？」
- 事后审计有据可查（`07-overnight.md` `## The morning audit`）。

**换到 MMW。**

- H1：五个宿主都要有 todo 工具才能照搬「抄进 todolist」。Claude Code 有；其余未核实，见第 5 节 U-4。
- H6：夜里 todo 屏幕没人看；会话被压缩后 todo 可能丢失。早上的读者读的是票（`shared.md` 第 11 行：无人会话「what it reports goes in the formats its skills give」）。所以无人会话里，「跳过了哪步、为什么」必须落到票上，不能只留在 todo 里。
- 其余硬约束不影响。

**MMW 要怎样实现。**

- mode `## Playbooks` 首段照抄 pstack 的执行协议。
- 为无人会话加一句：skip 行与点名原则的句子，写进本 playbook 的交付物。worker 写进 closeout 的 **Decisions I made on my own**（`implement/SKILL.md` 第 23 行已有这一段），reviewer 写进报告。这样不需要新格式：MMW 的票事件就是 pstack `show-me-your-work` 的等价物，只写一处。
- 「逐字抄写」能否被机器检查：在票的 closeout 里可以（`verify-ticket.py --closeout` 已有格式检查），在白天会话里不能。这是推断，是否值得加检查由下一轮定。

### E8 脚本只管确定性的状态与检查，判断留在文字里

**pstack 怎么做。**

- `orch` 只管状态与格式校验：「The CLI never spawns, waits, or wakes anything.」（L7 A.6）状态读写集中：「State reads and writes go through scripts/orch/orch.ts at drain points, one command in and one line out.」（L7 D.3）。
- `worktree-audit.sh` 只给建议分桶：`worktree-cleanup.md` 第 2 步「The bucket is advice, not permission.」（L7 A.6）。
- 接口约定：紧凑文本或 JSON；错误写 stderr；退出码有类型化含义；调用命令写在调用方正文里（L7 A.6）。
- 字面检查器持有被匹配的原文（`check-plan.mjs` 的 `RULE`，L7 A.6）。
- 什么时候做成脚本（L7 C.1 第 2 问）：跨会话的共享状态、轮询外部系统、已有机器检查的产物格式、批量只读收集。依据是 `principle-encode-lessons-in-structure` 与 `reflect/references/synthesizer.md` 第 20 行「Skill prose is for things mechanisms cannot enforce.」

**解决什么。**

- 机械部分不会因模型理解偏差而漂移。
- 判断部分不会被硬编码成错误的自动决定。
- 文字只讲 agent 要做的判断，不叙述脚本做什么。

**换到 MMW。**

- H6 让 MMW 的脚本比 pstack 多一类职责：唤醒。pstack 靠 Cursor 的 `/loop` 与云端 agent 唤醒（L7 E.2）；MMW 夜里没人，只能由 relay 与 watchdog 投递事件（ADR 0010、0020）。这仍是确定性的投递，不是判断，与精髓不冲突。精髓的边界是「脚本不做判断」，不是「脚本没有副作用」。
- H4：脚本送进会话的消息是一行。
- H5：脚本路径解析到已安装 checkout。

**MMW 要怎样实现。**

- MMW 在这一层本来就比 pstack 强：`SKILL-SET-RULES.md` 事实 2 与 pstack 同义；`verify-ticket.py`、`events.py` fold、relay、watchdog 都遵守「一条命令进、一行出」与类型化退出码；ADR 0008 规定每道闸口「点名它查的那个事实」。这一层保留。
- 要修的是三处越界：
  1. **脚本做了用户保留的决定**：`dispatch.sh` 第 2344–2360 行在 `--check` 失败时自动跑完整 `install.sh`，而根 `AGENTS.md` 写「`install.sh` runs only when the user explicitly authorises it」（R12 M7）。按「advice, not permission」，脚本只报告，决定交给人或写明授权。这件事改变用户已有的规则，属于用户决定（R12 U-5）。
  2. **脚本文字往上指技能小节**（E2 第 3 条）。
  3. **启动提示词里放规则**：`AUTONOMOUS`、`PRODUCT_RULES`（`dispatch.sh` 第 108–109 行）。规则的家是 mode 或 playbook；提示词只放数据。

### E9 模型角色配置与技能分离

**pstack 怎么做。**

- 技能正文只写角色标签和默认值：「your configured how-explorer model (default `grok-4.7-xhigh-fast`)」（`skills/how/SKILL.md` Step 2a）。
- 值在用户目录的一个规则文件里：`setup-pstack` 第 5 步整文件覆盖写 `~/.cursor/rules/pstack-models.mdc`，`alwaysApply: true`，每个角色一行，「using the same labels poteto-mode uses」；删掉一行就回到技能默认值；`inherit-parent` / `auto` 表示用父会话的模型（`skills/setup-pstack/SKILL.md` 第 5 步，本轮已读）。
- 面板角色的值是列表，列表长度就是扇出数（第 3 步 (c)）。
- 优先级：mode 第 93 行「Per-role lines in the `/setup-pstack` rule override these defaults and the model choices in the routed skills」。
- 配置在插件目录之外，插件更新不会覆盖它（L7 A.8，推断）。

**解决什么。**

- 换模型不改技能。
- 同一套技能适配不同用户可用的模型。
- 预算档（unlimited、large、medium、small）一次改全部角色的推理档位。

**pstack 的弱点**（L7 D.4）：没有解析器，标签靠模型理解（技能写 `how-explorer`，规则写 `how explorer:`）；默认值分散三处；`check-plan.mjs` 的 `LANES` 写死模型。

**换到 MMW。**

- H3 是决定性约束。pstack 的每个 `Task` 可以指定 `model`，同一会话里的子代理能跑在不同厂商的模型上。MMW 的宿主不行：子代理跑在本会话的模型上；要换厂商只能另起会话。ADR 0015 `## Consequences` 已经写出后果：「三个 axis subagent 跑在 reviewer session 的 model 上 ... 想单独给 axis 换模型，得先给它一扇自己的门。」
- 所以「角色 → 模型」在 MMW 只对另起的会话有意义。现有 4 个角色 `junior-worker`、`senior-worker`、`reviewer`、`advisor` 正是四种另起的会话（`~/.mmw/models.json` 与 `editing-models.md`，本轮已核实）。
- H2 不影响。H5：`models.json` 在 `~/.mmw/`，不在被冻结的 checkout 里，改动在下一次 `start` 生效（`editing-models.md`「The next `start` reads it again」）。这与 pstack「applies to new sessions」相同。

**MMW 要怎样实现。**

- 保留 `models.json` 与 `models.py`。它们已经修掉了 pstack 的弱点：有解析器、有唯一写者 `models.py config`、有校验。
- 为了接住 pstack 的组件，要补两件事（第 4 节 I-5、I-6）：
  - 一条只读查询命令，让技能正文里的「your configured <角色> model」有值可查。pstack 靠 `alwaysApply` 注入，MMW 没有注入，就显式查。
  - 面板角色（`arena runners`、`architect runners`、`interrogate reviewers`）的等价物。H3 下只能是「每个面板成员一个另起的会话」，由一个脚本像 `dispatch.sh advise` 那样起会话、收结果。没有这个脚本时，搬入的 arena、interrogate 只能在本会话模型上跑同模型面板，必须在 mode `## Subagents` 写明这一降级。
- 模型选择不进 playbook 或技能正文，只写角色标签，这一条与 pstack 相同。

### E10 自动化包怎样复用共享组件；项目私有组件落在目标仓库

**pstack 怎么做。**

- benny 是两个触发式自动化（triage、reproduce-and-fix）加一个配置向导，放在 `automations/benny/`，不注册成斜杠技能（`FOR_AGENTS.md` 第 5、31 行）。
- 每个自动化一个操作文件，单一入口、单一任务类型，不经过 mode 路由（L7 A.10）。两个自动化之间靠 thread 里的标记串接：「then wait for the trusted triage marker in the original thread」（`FOR_AGENTS.md` 第 18 行）。
- 共享组件按名字复用，不复述：「Use pstack's `principle-guard-the-context-window` for delegated analysis.」「Apply pstack's `principle-sequence-verifiable-units`, `principle-fix-root-causes`, and `principle-prove-it-works` ...」（`reproduce-and-fix-issues/SKILL.md` `## Hard safety rules` 末两条）。共享范围写明：「only for shared dependencies such as `how`, `why`, `tdd`, `unslop`, and the required principle skills」（`FOR_AGENTS.md` 第 32 行）。
- 不引用任何 playbook：`automations/` 下 grep「playbook」为 0（L7 第 0 节）。
- 外部能力用适配器契约：「The user must configure one control skill or adapter that implements this contract ... Set its skill name in `control.skill_name`.」缺失就 fail closed（`control-adapter.md` 第 3–9 行）。
- 用户配置放在包外：「i keep user-owned configuration, feature maps, routing maps, and secrets outside `.cursor/automations/benny/` so pack refreshes cannot overwrite them.」（`FOR_AGENTS.md` 第 34 行）。
- 安装后由一个新 agent 验证共享依赖能解析：「confirm that pstack's `how`, `why`, `tdd`, `unslop`, and the principle skills used by benny resolve in project scope」（第 79 行）。
- 项目私有组件由生成器写到目标仓库，由配对技能维护：`create-verification-skill` 生成 `.cursor/skills/verify-<app>/`，`maintain-verification-skill` 维护（L7 A.11）。

**解决什么。**

- 自动化能复用 mode 体系的能力与原则，而不必经过 mode。
- 自动化之间用外部状态串接，谁都不依赖另一个的内部。
- 包可以整体刷新而不毁掉用户配置。
- 依赖缺失时停下，而不是在半套环境里瞎跑。

**换到 MMW。**

- MMW 的夜间流水线就是一个自动化包：orchestrator、worker、reviewer、advisor 四类会话；靠票上的事件串接（ADR 0019「ticket state is a fold of events」、0020）；用户配置在包外（`~/.mmw/models.json`，消费仓库的 `.mmw/target.json`）。
- 与 benny 的差别有两点：
  1. MMW 的操作文件是能力技能，而且装进宿主的技能列表（`implement`、`code-review`）。benny 的操作文件不注册成技能。
  2. MMW 还有人启动的白天会话，需要 mode 路由；benny 没有。
- H2：benny 在 Cursor 上靠「按仓库相对路径读取」到达操作文件（`FOR_AGENTS.md` 第 33 行「each live automation prompt to read its committed operational file directly」）。MMW 的等价物是启动提示词点名 mode 里的 playbook 文件（E6 第 1 条到达路径）。
- H5：包的版本是已安装 checkout，watch 期间冻结，与 benny 的「提交到目标仓库」不同，但目的相同，都是运行时读到确定的版本。

**MMW 要怎样实现。**

- 角色操作文件进 playbook 层：`mmw/playbooks/` 下的 work-a-ticket、review-a-ticket、run-a-night、run-one-ticket 等（名字由下一轮定）。启动提示词直接点名它们，mode 路由表也列出它们（人说「今晚跑 spec #N」时要能路由到 run-a-night）。
- 与 benny 的「每个自动化一个操作文件、不拆三层」相容：每个角色一个 playbook 文件，不再拆成「playbook + 同名能力技能 + reference」。
- 同名的上游能力技能回到原文，成为真正的共享能力：`implement` 的上游原文正文五行，只点名 `tdd`、`code-review`（`SKILL-SET-RULES.md` 事实 4）。worker playbook 在步骤里点名它。
- 适配器契约的已有等价物：`.mmw/target.json`、`ui-acceptance` 的 harness、runner 适配器（ADR 0018 `runner-behind-one-boundary`、0024）。缺失就 fail closed，这与 ADR 0008 同义。第 4 节 I-8 的 control 槽位沿用这一形式。
- 「新 agent 验证共享依赖能解析」对应 `install.sh --check`，以及 `dispatch.sh check` 开夜前调用它（根 `AGENTS.md` Commands 表）。要补的一项是：检查 mode 路由表、playbook 步骤点名的每个技能和文件都已安装。这就是 E2 的 lint 在安装侧的一半。
- 项目私有组件：MMW 已有 `setup-matt-pocock-skills` 往消费仓库写 `docs/agents/*.md`（R4 V14），以及 `.mmw/`、screen contract。按 pstack A.11，「生成方 + 维护方 + 位置」要成对写明。这是仓库文档层的归置，由下一轮处理。

### E11 教训按层回流

**pstack 怎么做。**

- `principle-encode-lessons-in-structure` `**Feedback loop:**`：「Capture every correction ... Route to the right layer. One-off -> brain note. Recurring fix -> skill or lint rule. Systemic issue -> principle. ... Close the loop.」（第 24–26 行）
- `reflect` 让三个 reviewer 读会话，synthesizer 按四条原文规则分拣（`references/synthesizer.md` 第 17–22 行）：
  - Existing-skill-first：只有没有现成的家、模式反复出现、值得单独成技能时，才提议新技能；
  - Decision-changing：改动要让未来的 agent 做出不同的事，而不只是多读文字；
  - Structural-mechanism check：能由 lint、脚本、元数据、运行时检查低成本强制的，转 Backlog，不写成技能文字；
  - Already-covered：重复了已有的、位置得当的指引就拒绝；指引埋得太深，就改成「改写或挪位置让它生效」。
- 用户审批后才改技能（`docs/guide/09-make-it-yours.md`「waits for your approval before any skill changes」）。

**解决什么。** 分层不会随时间腐化。新教训总是落到对的层，不会全部堆进某个技能的正文。

**换到 MMW。** H1–H6 都不影响。

**MMW 要怎样实现。**

- MMW 已有 `retro`，它的去处枚举是 `check`、`script`、`repository-agents`、`repository-skill`、`reviewer-rule`、`mmw-skill`、`toolbox-memory`、`none`（`mmw-v2/skills/retro/scripts/retro.py` 第 31–32 行，本轮已核实）。
- 其中没有 `principle`、`playbook`、`mode` 三个去处。分层建好之后，`retro` 的去处要按层补齐，否则夜里学到的教训只能落进技能正文或 Memory，分层会重新变乱。
- synthesizer 的四条规则可以原样作为 `retro` `## Decide` 的判据。它们与 `SKILL-SET-RULES.md` `### Redundancy and bloat` 同向，是现成的外来组件。

### E12 不拆的纪律：什么留在原处，什么不能以「不拆」为由留下

**pstack 怎么做。** L7 C.2–C.5 列了 pstack 不拆的理由，每条有实例：

- 规则绑定了具体机制或领域参数，原则只写方向，调用方写具体化（forge 选择、patch-id 规则）；
- 读者读不到原则（跑在别的模型上的子代理），所以全文复述（`interrogate/references/rubric.md`）；
- 只有一个调用方；
- 长内容就是这个 playbook 的产物（`orchestrate.md`「The brief is the product.」）；
- 降级路径要求自足；
- 机械部分已拆成脚本，留下的是判断；
- 能力技能内部的多步流程服务于一个可以命名的交付物（`architect`、`arena`、`how`）。

**这些理由的共同点**：留在原处的都是「一件事怎么做」的细节，或某个产物本身。没有一条理由允许把「一类任务的先后顺序」或「我被谁调用、下一步交给谁」留在能力技能里。pstack 里也找不到这样的实例：L7 B.2 表中「能力技能 → playbook」只有 `recall` 往外分流一例。

**解决什么。** 防止为套分层而硬拆（L7 C.6 信号 5–11）。例如只包一个技能、没有门槛和交付物的 playbook，或只有一个读者、每次都读的 reference。

**换到 MMW。** H1–H6 都不影响。但任务给定的判据比 pstack 更严：留在原处只有一个理由，即已核实的硬约束。pstack 的「只有一个调用方」「它就是产物」在 MMW 里可以沿用，前提是被留下的东西确实属于这一层；不能拿来把错层的内容留在错层。

**MMW 要怎样实现，以及 R4、R12 错在哪里。**

- R4 第 0 节第 7 条、R12 第 0 节第 1 条以 L7 C.1 第 7 问为由，把五个角色流程留在能力技能里。这个理由不成立：
  - C.1 第 7 问说的是「单一入口、单一任务类型的流程，不必拆成 mode + playbook + 技能三层」。它允许一个操作文件同时承担顺序与做法。
  - 但它没有说「这个操作文件是能力技能」。benny 的操作文件不注册、不被复用（E10）。
  - MMW 把角色操作文件放在能力技能的名字下（`implement`）、装进技能列表、由 description 触发，于是一个名字承担两层。上游原文的 `implement` 是能力技能，本仓的 `implement` 是 worker playbook。
- 正确的应用：角色操作文件放进 playbook 层，每个角色一个文件，不拆三层（满足第 7 问）。同名能力技能回到原文（满足 E3）。
- R12 的「2 条原则」以「现在有几处句子缺理由」为门槛（R12 K-9）。pstack 的门槛是四条（E5），与现有引用数无关。
- R12 的「`exe-release`、`dispatch` 不单列进路由」（K-16）：出包、开夜、单票都是用户会直接提出的任务类型，按 E4 都应在路由表里有一行。
- 可以用 pstack 的「不拆」理由留下的内容，例：
  - `verify-ticket` 的闸口细节（机械部分已在脚本，留下的是判断）；
  - `code-review` 的四个 axis 做法（服务于一个交付物：评审报告）；
  - `advisor/references/advising.md`：它是交给另起会话的简报模板，照 pstack「给子代理的提示模板放 reference」（L7 A.5）留作 reference，是推断。
  - 同理，`code-review/references/session.md` 里给 reviewer 的评审方法可以留作 reference；「报告写上票、唤醒 worker」这类票协议是 reviewer playbook 的步骤。这一拆分是推断，由下一轮对照原文定。

---

## 3. 十二条精髓合起来，MMW 各层放什么

这一节不是逐件归置（那是下一轮的事），只写每层的定义、MMW 的来源与前后对比，好让「改造前后有什么区别」一眼可见。

### 3.1 各层的定义与 MMW 来源

| 层 | 放什么（判据） | MMW 现在这些内容在哪里 | 依据 |
|---|---|---|---|
| mode `mmw` | 跨 playbook 的触发、原则索引、自主权（人在场与无人两种）、子代理简报规则、层级优先级、执行协议、路由表 | 触发散在各 description；自主权在 `dispatch.sh` `AUTONOMOUS` 与 `tool-guard.py` `NO_QUESTION`；路由不存在（事实 7「ships no router skill」） | E6 |
| playbook | 一类任务的先后、门槛、所有权、停止条件、回复；跨会话的附 `**Where you are.**` | 能力技能的结尾段（N10 第 1 节 15 处）；`implement` 正文；`night.md`、`one-ticket.md`、`inside-a-ticket.md`；`session.md` 的票协议；上游 `triage` 第 5 步、`wayfinder` 第 6 步、`improve-codebase-architecture` `### 4` | E4、E10 |
| 能力技能 | 一项可命名的能力及其交付物；不知道调用方；可自带闸门 | 上游技能（回到原文）；MMW 自有技能里不含流水线位置的部分 | E3 |
| 原则 | 跨任务、短名、有触发情境、改变具体决定的判断 | ADR 0008、`dispatch` 第 8 行、`shared.md` 部分规则、`SKILL-SET-RULES.md` 部分事实（逐条待判） | E5 |
| reference | 分支才读的材料、交给另起会话或子代理的模板、会增长的目录、适配器契约 | 各技能 `references/` | L7 A.5 |
| 脚本 | 确定性状态、投递、检查；不做判断；不往上点名文本 | `dispatch/scripts/`、`verify-ticket/scripts/`、`ui-acceptance/scripts/` 等 | E8 |
| hook | 结构化强制（不许关票、不许向屏幕提问、回合结束检查）与每回合提醒 | `tool-guard.py`、`turn-guard.py`；提醒 hook 待建 | E6、E8 |
| 配置 | 角色 → 宿主、模型、档位；runner；消费仓库的目标配置 | `~/.mmw/models.json`、`.mmw/target.json` | E9、E10 |
| 仓库文档 | 给维护者与人读的：ADR、词表、runbook、技能写作规则 | `docs/`、`SKILL-SET-RULES.md`（R12 K-38 已定搬出上游目录） | L7 A.9 |
| 消费仓库私有组件 | 由生成器写入、由配对技能维护 | `docs/agents/*.md`、`.mmw/`、screen contract | E10 |
| 外来组件 | 以 subtree 引入的上游、diagram-design、unlazy，以及将来的 pstack | `mmw-v2/upstream*/`，由 merge-note 记录改动 | 第 4 节 I-12 |

### 3.2 目录形态（推断，由上表推出；名字待下一轮定）

```
mmw-v2/skills/mmw/                    mode（模型可触发）
├── SKILL.md                          Non-negotiables / Principles 索引 / Autonomy / Subagents / Playbooks
├── playbooks/<slug>.md               每种工作流一个：白天定义、开夜、单票、做一张票、评审一张票、
│                                     接手一张票、验收与 finish、修 bug、出包、分诊、调研、接入 MMW、写技能…
├── principles/<slug>.md              MMW 的原则；pstack 的原则按同一格式直接落位
├── references/                       只被 mode 与 playbook 读的材料（例：阶段边界 PHASE-BOUNDARIES）
└── scripts/                          只被 playbook 步骤调用的确定性脚本（或留在各技能的 scripts/ 由 playbook 点名）
mmw-v2/skills/<capability>/           MMW 自有能力技能：不含流水线位置
mmw-v2/upstream*/                     外来能力技能：回到原文，只在边缘接入
mmw-v2/tests/lib/check_wiring.py      连线 lint：方向、按名、无编号引用、原则引用一种写法、依赖可解析
```

### 3.3 改造前后，读者能直接看到的区别

| 看什么 | 改造前 | 改造后 |
|---|---|---|
| 想知道「做一张票要走哪些步」 | 读 `implement`，它再把你送到 `verify-ticket`、`dispatch` 的 moment 表、`code-review` 的 session | 读一个 playbook 文件，编号步骤从头到尾 |
| 想知道「从想法到关票的全流程」 | 按事实 7 把 15 处结尾段按顺序拼起来 | 读 mode 路由表，每类任务一行、指向一个文件 |
| 能力技能的结尾 | 「下一步用 X 技能」「返回 night.md ## 5」 | 「交回什么」 |
| 上游技能 | 带 +1674/−415 行本仓改动 | 回到原文，只在边缘接入 |
| 跨任务的判断 | 散在 ADR、提示词、写作规则、技能正文 | `principles/` 一个目录，mode 一张索引 |
| 加一个 pstack 的 playbook 或原则 | 没有地方放 | 放进 `playbooks/` 或 `principles/`，加一行路由或索引 |
| 夜里的会话被压缩后 | 靠会话里残留的上下文，或唤醒里的角色指针 | 唤醒里的指针点名 playbook，`RESUME:` 点名步骤标题 |

---

## 4. 为了能直接搬入 pstack 的 playbook、原则、技能，MMW 必须具备的接口

每行写：pstack 组件依赖什么（出处）→ MMW 对应成什么 → 状态（已有 / 要建 / 受哪条硬约束限制）。

| # | pstack 的依赖 | 出处 | MMW 对应成什么 | 状态 |
|---|---|---|---|---|
| I-1 | **playbook 的位置与相对路径**。mode 用 `playbooks/<file>.md` 路由；playbook 用 `references/<file>`、`scripts/<file>`、`../references/bugbot-triage.md` | mode 第 121–143 行；L7 B.1 | `mmw` 技能目录照 `poteto-mode/` 的布局建 `playbooks/`、`references/`、`scripts/`，pstack 的相对路径不改就能解析。H5 下这些路径落在已安装 checkout，自然冻结 | 要建 |
| I-2 | **playbook 的写法**：`### <名字>`、所有权行、编号步骤、`**Reply:**`；按粗体名点名技能与 playbook（「the **how** skill」「Run **Opening a PR**.」） | L7 A.2；`bug-fix.md` | MMW 的 playbook 用同一骨架，点名方式与 `SKILL-SET-RULES.md` 的「`/X` or the `X` skill」相容。MMW 自己的 playbook 多一个可选段 `**Where you are.**`（E4），pstack 的 playbook 没有它也能用 | 要建；格式相容 |
| I-3 | **执行协议**：抄步骤进 todo、`skip: <reason>`；各 playbook 的 `**Reply:**` 只写独有内容，通用回复写法在 mode | mode 第 109、117 行 | mode `## Playbooks` 首段照抄；通用回复写法由 `shared.md` 承担。无人会话把 skip 行写上票（E7）。todo 工具在各宿主是否都有，见 U-4 | 要建；H1、H6 限制 |
| I-4 | **`subagent_type: "poteto-agent"`**：子代理开工前先读 mode | mode 第 91 行；`agents/poteto-agent.md` | ADR 0015 不交付子代理（H3 环境下也无从注册跨宿主的类型）。等价物是 mode `## Subagents` 里的一份简报模板，第一句要求读 mode 的 `## Principles` 与所服务的 playbook 步骤。搬入 pstack playbook 时，「`subagent_type: "poteto-agent"`」统一读作「用宿主的通用子代理，带这份简报」，这条映射写在 mode 一处 | 要建 |
| I-5 | **`Task` 的 `model` 与「your configured <角色> model (default ...)」** | how Step 2a；mode 第 93 行；`setup-pstack` 第 5 步 | H3：会话内的子代理不能换厂商。映射分两种：<br>(a) 单个子代理的角色（how explorer、bug-fix、feature…）一律按 `inherit-parent` 处理，即跑在本会话模型上，在 mode 写明；<br>(b) 需要另起会话的角色进 `~/.mmw/models.json`，由 `models.py config` 管理，另加一条只读查询命令供技能正文查值 | (a) 要写一句；(b) 查询命令要建 |
| I-6 | **面板角色**（`arena runners`、`architect runners`、`interrogate reviewers`，值为列表，一项一个子代理）与 `arena cross-judge pool`（「model family differs from the parent's」） | `setup-pstack` 第 3 步 (c)；arena Phase C（L7 D.4） | H3 下跨厂商面板只能是多个另起的会话。需要一个脚本：按 `models.json` 里的面板列表逐项起会话、送简报、收结果。`dispatch.sh advise`（ADR 0014）是单成员的先例。没有这个脚本时，搬入的 `arena`、`architect`、`interrogate` 退化为同模型面板，失去「Agreement is high-signal」（mode 第 95 行）的价值，必须在 mode 写明 | 要建；受 H3 限制 |
| I-7 | **原则的形式**：`skills/principle-<slug>/SKILL.md`，带 `disable-model-invocation: true`；引用写法多样（「the **prove-it-works** principle skill」「**principle-model-the-domain**」、相对链接 `../principle-build-the-lever/SKILL.md`） | L7 A.4、E.1 第 1 条 | H2：不能装成技能。落位为 `mmw/principles/principle-<slug>.md`，保留 pstack 的 `name`、`description`。mode 写一条解析规则：「`principle-*` 名字指 `principles/` 下的同名文件」。原则之间的相对链接由导入脚本（I-12）机械改写。索引由 `description` 生成或由 lint 核对 | 要建 |
| I-8 | **control 槽位**：「the matching control skill」；外部插件 `cursor-team-kit` 的 `control-ui`、`control-cli`；benny 的 `control.skill_name` 适配器契约 | mode 第 30 行；`bug-fix.md` 第 1 步；`control-adapter.md` | mode 一张表：表面 → 技能。浏览器与 Web 界面 → `playwright-cli` 或 `ui-acceptance` 的 harness；本机原生窗口 → `computer-use`；Orca 内置浏览器 → `orca-cli`；CLI → 直接跑命令。消费仓库可在 `.mmw/target.json` 覆盖。缺失就 fail closed（ADR 0008） | 要建（技能已有） |
| I-9 | **能力技能的调用开关**：pstack 46/47 带 `disable-model-invocation: true`，靠 mode 与 playbook 按名调用 | L7 A.3、E.2 | H2：照搬会让模型在 Claude Code 上调不到。搬入规则：去掉这个键；description 只写「是什么、直接调用时怎么说」；跨技能的「何时用」写进 mode `## Non-negotiables`。Codex 侧同时处理 `agents/openai.yaml` 的 `policy` 行（`merge-notes/README.md` 的「两处开关同增同删」）。是否对少数只该由用户启动的技能保留用户触发，按 `c9f4e5c7` 的先例逐个判断（N10 第 6 节） | 规则要写 |
| I-10 | **delivery 槽位（对 PR 的依赖）**：7 个 playbook 最后一步「Run **Opening a PR**」；babysit、shipping、autopilot 全建立在 PR 与 `gh`/Origin 上 | L7 E.1 第 3 条；`opening-a-pr.md` | MMW 夜里不开 PR：worker「Open no pull request: the orchestrator lands the ticket」（`implement` 第 99 行），合并进 project branch（ADR 0025），`finish` 收尾。所以「Run **Opening a PR**」要映射到一个 delivery 槽位：<br>• 在票里：closeout，由 orchestrator land；<br>• 白天直接改：按该仓库的交付约定（本仓库是根 `AGENTS.md` Gotchas 的四步发布）；<br>• 在用 PR 的仓库：原样用 pstack 的 opening-a-pr。<br>babysit、shipping、autopilot 只对用 PR 的仓库有意义，搬入时要在路由表写明适用条件 | 要建 |
| I-11 | **forge 槽位**：`gh` 默认，`command -v origin` 探测，不依赖 Graphite；在 6 个 playbook 里各写一份 | L7 A.2 | MMW 的 tracker 操作集中在 `docs/agents/issue-tracker.md`（根 `AGENTS.md` External References）。映射为「forge 命令见该文件」一处，搬入时把 6 份复制替换成这一个指针 | 要写 |
| I-12 | **外来组件的引入方式** | — | 与 `mmw-v2/upstream/`、`upstream-diagram-design/`、`upstream-unlazy/` 相同：pstack 以 squash subtree 引入（例如 `mmw-v2/upstream-pstack/`），`skills.txt` 加来源前缀（现有 `engineering/`、`productivity/`、`self/`、`dd/` 四种，`mmw-v2/skills.txt` 头注释），每个改过的组件写 merge-note。playbook 与原则不进 `skills.txt`，由导入脚本（确定性的机械改写：相对链接、`principle-*` 路径、上表各槽位的固定替换）复制进 `mmw/playbooks/`、`mmw/principles/`，并在路由表或索引加一行。搬入后跑 `install.sh --check` 与连线 lint | 要建 |
| I-13 | **宿主专有的工具与命令**：`AskQuestion`、`/loop`、`/goal`、cloud agent、`create-skill`、`Task` 的 `run_in_background`、`readonly`（「readonly strips MCP」） | L7 E.2 | `AskQuestion` → 人在场时按 `shared.md` 规则 1 在对话里问；无人时写 decision 子票（`tool-guard.py` 的出路）。`/loop`、`/goal` → MMW 的 relay 唤醒与 watchdog（ADR 0010、0020）；白天会话用宿主自带的循环（如有）。cloud agent → `dispatch.sh start` 起的另一会话。`create-skill` → `writing-for-agents`。`readonly` → 简报里一句「You are read-only」（ADR 0015 的做法）。`run_in_background` → 按宿主，未核实（U-4）。这张映射表写在 mode 一处 | 要写 |
| I-14 | **transcript 的位置**：`~/.cursor/projects/<slug>/agent-transcripts/`，被 session-pickup、reflect、worktree-audit 使用 | L7 E.2；`session-pickup.md` 第 1 步 | 五个宿主各有自己的位置与格式。照 pstack `why/references/sources/*.md` 的做法，做成「按宿主一份」的 reference 变体。MMW 另有 Nowledge Mem 的会话记录（`install.sh` 装 `mmw-toolbox` Space，根 `AGENTS.md` Commands 表），可作一个来源。未核实 | 要建；未确定 U-8 |
| I-15 | **worktree 约定**：`opening-a-pr.md` 的「Work from a git worktree off main」 | `opening-a-pr.md` 第 5 行 | MMW 的 worktree 名字归流水线所有：`.worktrees/issue-<n>`、`merge-<branch>`（根 `AGENTS.md` Key Conventions）。搬入的 playbook 自建 worktree 时，要落在 `.worktrees/` 下、避开这两种名字。写成 mode 的一条触发 | 要写 |
| I-16 | **回复写法冲突**：pstack「No long-dash character anywhere」「A colon as a mid-sentence connector is also out」 | mode 第 102–103 行 | `shared.md` 自己用 em dash（例：第 27 行「— every word」），规则 7 管的是修辞，不管标点。搬入 `unslop`、`technical-writing` 时，对「回复给用户」以 `shared.md` 为准，对其他产物按导入的技能。优先级写在 mode（E6） | 要写 |

**搬入时的判断顺序（推断，由上表归纳）**：

1. 组件依赖的每个槽位（control、delivery、forge、子代理简报、模型角色、宿主工具）在 mode 里都有映射吗？
2. 它依赖 PR 吗？依赖的话，只在用 PR 的仓库路由到它。
3. 它依赖跨厂商面板吗？依赖的话，I-6 的脚本在不在？不在就在 mode 写明降级。
4. 它运行中从 trunk 重读自己吗（`autopilot-full.md` 第 6 步、`multi-phase-plan.md` 模板）？这一句按 H5 删去。
5. 导入脚本改写完，连线 lint 与 `install.sh --check` 通过吗？

---

## 5. 未确定（需要实测）

| # | 问题 | 为什么重要 | 怎么测 |
|---|---|---|---|
| U-1 | 模型可触发的 `mmw` 技能，加启动提示词「Use the mmw skill; your playbook is `playbooks/<x>.md`」，在五个宿主上能否让新会话读到该 playbook 文件 | E6 到达路径 1、E10 的前提 | 照 ADR 0006 的方法：隔离 HOME 里放一个探针技能，带 `playbooks/probe.md`（内含一个随机标记），用各宿主的非交互进程送这条提示词，看回复是否出现标记。Claude Code、Codex、Grok、Pi、Cursor 各一次 |
| U-2 | 各宿主有没有「用户提交 prompt 时」的 hook 事件，能否向上下文注入一行 | E6 到达路径 3（pstack `reminder` 的替代） | 已知 Codex 事件表有 `UserPromptSubmit`（`install.sh` 第 768–774 行）。Claude Code、Grok、Cursor、Pi 各装一个只打印标记的探针 hook，在有与没有 `.mmw/` 的目录各提交一次，看模型能否复述标记 |
| U-3 | `mmw/principles/*.md`、`mmw/playbooks/*.md` 这类技能目录下的嵌套文件，会不会被某个宿主当成技能扫入 | 若会，原则与 playbook 会进技能列表，与 E5「只被点名」相反 | 在探针技能目录下放嵌套的 `.md` 与名为 `SKILL.md` 的嵌套文件，看各宿主的技能列表（Grok `grok inspect --json`，其余用非交互进程问） |
| U-4 | 五个宿主是否都有 todo 工具与后台子代理 | E7 执行协议；I-13 | 各宿主非交互进程列出可用工具 |
| U-5 | worker、reviewer 每次启动都读 mode（约 150 行量级，推断）的上下文成本，与它换来的常驻纪律相比是否划算 | E6 到达路径 1；R4 曾以此否决 R2 | mode 写好后量字节数；在隔离 home 用开发版技能跑一张测试票，比较启动后首个动作前的上下文用量 |
| U-6 | 面板脚本（I-6）起多个另起会话的耗时与费用，以及在无人夜里能否可靠收齐结果 | 决定 arena、interrogate 类组件在 MMW 是否值得搬 | 用 `dispatch.sh advise` 的现有机制起 3 个会话，测到齐时间；看 relay 能否把「面板收齐」作为一个事件 |
| U-7 | 能力技能去掉 `disable-model-invocation` 后，description 数量增加对触发准确度的影响 | I-9 | 搬入前后各跑一组固定的用户请求（取自 N10 第 3.2 节的起点），数每个请求加载了哪个技能 |
| U-8 | 各宿主的会话记录位置与格式，Nowledge Mem 的会话记录能否作为 session-pickup 的来源 | I-14 | 各宿主跑一个短会话，找记录文件；`nmem t search` 查同一会话 |

---

## 6. 本文没有读或没有核实的部分

- pstack 的其余 15 个 playbook、多数能力技能、20 条原则、benny 的 `triage-issue-reports` 与 `setup-benny`、`scripts/` 全部源码，只经 L7 引用。
- MMW 的 `night.md`、`one-ticket.md`、`inside-a-ticket.md`、`code-review/references/session.md`、`advisor/references/advising.md` 本轮没有重读全文。E12 对 `session.md`、`advising.md` 的拆分建议标了推断。
- 第 2 节 E5 列出的原则候选只作线索，没有逐条按四条门槛核对。
- 第 3.2 节的目录形态是由判据推出的推断，名字与合并方式由下一轮逐件归置时定。
