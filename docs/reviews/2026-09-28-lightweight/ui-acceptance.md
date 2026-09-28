# ui-acceptance

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：技能里已有的理由句写得很好，调查员列的保留清单全部成立，例如 "another run's product looks exactly like a stuck one"、"the next run has no person in it"、harness guard 的 "a back door opened for automated acceptance that ships to a customer's machine"。缺的有两类。一类是被前几轮删掉、正好在 agent 想走捷径那一刻起作用的理由：规则 3、规则 5、break switch 为什么在产品里、mock 为什么落在 outbound call module 这一层。另一类是 `SKILL.md` 开头没说这四个判官在夜里是界面唯一的把关。真钥匙那一条涉及钱，也要把理由写出来。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md`，第 8 行定义段之后 | During a night these judges are the only eyes on an interface: when every criterion is green, the ticket closes and the code lands with no person looking at the screen. So write the story, the test, the journey and the harness so that green can only mean the product is right; when a judge is red, change the product, or open a child when the design or the contract is wrong, never the check. | 判官变红时，最自然的做法是放宽断言、在 story 页上补样式、在更低一层 stub 网络。这句说明为什么这些做法今晚能过、缺陷却交到了客户手里。调查员原稿括号里讲每个判官如何变红，那是各 reference 的内容，已删去。与 ADR 0008 的张力：那份 ADR 否决的是把闸口设计写进 `verify-ticket`，这句讲的是写测试的 agent 该怎么做，不冲突。 |
| I2 | `SKILL.md` 规则 3，把 "Report the ticket blocked: the next run has no person in it." 改为右栏（恢复 `cb45a515` 删掉的半句） | Report the ticket blocked: satisfying it makes a broken automation look healthy, and the next run has no person in it. | "手动点一下就能过""手动种一条数据"这类清单外的变体：有了这个理由，agent 能判断它们同样是在掩盖缺陷。 |
| I3 | `SKILL.md` 规则 5 末尾（恢复 `cb45a515` 删掉的原句） | A workaround built instead hides it from every ticket after yours. | 绕开一个坏掉的脚本、临时改一下 `.mmw/target.json` 时：有了它，agent 知道后面的票会踩同一个坑却看不见原因。 |
| I4 | `references/boundary-check.md` `## The four-column boundary test`，接在 "Mocking that module is the allowed seam." 之后 | Lower than that module, the test checks a request the product's own call layer never builds; higher, it skips the code that turns a click into a request. | 现在只列了被禁的名字（`fetch`、msw、nock、fetch-mock）。遇到清单外的写法（axios 拦截器、IPC 桥接层的 stub）时，有了理由，agent 能自己判断该不该用。"断言要依赖点击"这层意思，同文件末段已写（"a test whose assertion is true without the click stays green"），不重复。 |
| I5 | `references/journey.md` `## The break switch` 末尾（恢复 `cb45a515` 删掉的理由，改写为一句） | The switch lives in the product because only the product's own routing reaches every path its frontend takes; a forwarding proxy in front of it misses a frontend that calls its backend by another address. | 实现开关的 agent 想用一层代理代替时，有依据知道为什么不行。 |
| I6 | `references/product-answers.md` `## Rules`，把 "Real keys exist only on a paid-smoke ticket labelled `ready-for-human`." 改为右栏 | A night repeats every criterion unattended, often many times; with a real key each repeat can spend money or reach a real customer, and nobody is watching to stop it. So automation uses placeholder keys, vendor stubs and local accounts, records under `MMW_AUTOMATION=1` whatever would leave this machine (the `leaves_machine` answer), and real keys exist only on a paid-smoke ticket labelled `ready-for-human`. | 填 `.mmw/target.json` 的 agent 为省事想用真钥匙时，有了它会知道这件事的分量。涉及钱和真实客户。`leaves_machine` 字段本身由 `target_config.py --check` 说明，这里只补它背后的理由，不另起一条。 |
| I7 | `references/story-parity.md` `## The DIFF line` 末尾 | Fix the product component, not the story page: the story page only puts the real component into a scene, so a style or wrapper added there closes the `DIFF` while the product stays wrong. | 想在 story 页或 adapter 里补一层样式来消掉 `DIFF` 时。**推断**：没找到这样出过事的记录；`implement` 的 `writing-interface-code.md` `## Fix in place` 读起来默认改产品，但读 `DIFF` 的不只是 worker。代价是一句话。 |

### 删除

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | 四个 reference 的 `## The criterion, in one shape` 小节（各一句指针） | 删标题和指针；`harness-guard.md` 那一节里混进的 `leaves_machine` 段落（"What widens the allowed set…"）挪到文件开头第二段之后 | `SKILL.md` `## Find your moment` 第三行已路由到同一处。 |
| D2 | `story-parity.md` 开头 "Three agents use this page…" 中 render-only 的分句与 `## --render-only` 整节 | 删；**The two sides** 保留（values 的字段定义，`writing-interface-code.md` 指向它） | `implement` 的 `writing-interface-code.md` `## Before the first line` 已完整写了命令与输出。 |
| D3 | `story-parity.md` `## Exit codes` | 删三条退出码；"`--out <dir>` keeps both screenshots, their pixel difference image and the ARIA capture" 并入 `## The DIFF line` 末尾 | 与脚本头部重复。 |
| D4 | `journey.md` `## Exit codes` | 压成一句："On `JOURNEY FAILED`, what to fix is what the last line names: the script's own output, not this judge's words." | 其余各行由脚本打印并带修法。 |
| D5 | `harness-guard.md` `## Exit codes` 的 `0` 与 `2` 两条 | 删；`1` 那条里的修法保留 | 脚本只打印 `HARNESS LEAK <file>:<line>`，修法必须留在文字里；另两条是复述。 |
| D6 | `product-answers.md` **`checks`** 条后半（事件名、`met`/`unmet`、最后 20 行、形状不对算 `unmet`） | 删；前两句（形状、超时、在仓库根运行、`MMW_BASE_REF`）保留，末尾加 "A command that fails keeps the ticket open, so every entry must pass on the base branch as it stands." | 读这一条的是填 `.mmw/target.json` 的 agent，它需要的是"失败会让票关不掉"，不是事件的内部格式。 |
| D7 | `SKILL.md` `## Resolve <scripts> once` 第二、三句（`--tools` 与 PATH） | 换成一句 "A criterion names a judge bare; run one by hand as `<scripts>/<name>`." | `--tools` 是调用方的参数；PATH 那半句在 `verify-ticket` 的 `SKILL.md` 已有。 |
| D8 | `SKILL.md` 末行 "**A reviewer** never starts the product." 及其上的 "Which event depends on your role:" 列表 | 列表改为一句 "A worker opens a `fault` child, as the `implement` skill says, and stops." | reviewer 读不到这一节（`PRODUCT_RULES` 只拼进 worker 的启动 prompt）；`code-review` 的 `ui-reviewer.md` 已写明 story 服务不是产品。 |
| D9 | 规则 5 括号里的判官清单 | 删括号，保留 "a judge script" | 同文件第 8 行已列出。**规则编号和标题 `## Five rules while the product is running` 不动**：三个文件和 worker 的启动 prompt 逐字引用。 |
| D10 | `product-answers.md` 第 27–29 行对 outbound call module 的定义 | 改为 "**A boundary test replaces the outbound call module**, which the repository names ([boundary-check.md](boundary-check.md))." | 同一概念定义两处，写测试的 agent 读的是 `boundary-check.md`。 |
| D11 | `journey.md` "…there is no driver between the script and the page." | 改为 "Drive the page with Playwright's own API." | 后半句在说一个已经不存在的旧组件。 |
| D12 | `description` 第一句 "Acceptance criteria that start or compare a running product, and what a repository answers so they can run." | 删，只留 "Use when …" 那句 | 你定过 description 只写触发条件。改完要开新会话才生效。 |
| D13 | 脚本：`refusal.within_limit`、`lease.py env` 命令、`journey.py` 对 #455 之后再无人设置的环境变量的处理；`story-parity.load_stories_config()` 读到格式错误的 `.mmw/target.json` 时抛 Python 堆栈 | 删前三处死代码；最后一处改为一条三段式拒绝；五处各自解析 `.mmw/target.json` 的代码合成 `lease.py` 里的一个读取函数（放在 `lease.py` 是为了避免循环导入，见调查员 S6） | 调查员"脚本"一节逐条给了位置。最后一处是真实缺陷：agent 看到堆栈无从下手。 |

### 不采纳

- 缺口 2（"The four split one question so none answers all of it…"）：没有找到把检查放错判官的实例，`## Find your moment` 的表已经按问题分了路。
- 缺口 4 的前半（"An assertion that does not depend on the click reads exactly like one that does…"）：同文件末段已有同义句。

## 结论

体量：技能正文 4,709 词（`SKILL.md` 781 词，五份 reference 共 3,928 词：`product-answers.md` 1,074、`story-parity.md` 1,084、`boundary-check.md` 755、`journey.md` 682、`harness-guard.md` 333）；脚本 9 个共 3,192 行（`lease.py` 728、`story-parity.py` 695、`design_render.py` 627、`journey.py` 313、`target_config.py` 294、`harness-guard.py` 286、`boundary-check.py` 148、`refusal.py` 56、`pixel_diff.py` 45）。

这个技能不算臃肿。前几轮（`cb45a515`、`4372d901`、`013b2bb1`）已经删掉了大部分复述脚本的内容，剩下的正文多数是判官（judge）和产品之间的接口约定，是 agent 需要照着写的规则。现在的问题主要有三个：一是还剩几处小的重复和复述（四个只有一句话、指向 `to-tickets` 的 `## The criterion, in one shape` 小节，`story-parity.md` 的 `## --render-only` 和 `## Exit codes`，`journey.md` 的 `## Exit codes`，`product-answers.md` 的 `checks` 一条里讲 closeout 事件机制的部分）；二是脚本里有少量死代码和保护一条已不存在路径的代码；三是 `SKILL.md` 缺一段总的说明，告诉 agent 这些判官是夜里唯一看界面的眼睛，它的任务是让"绿"只能意味着产品真的对了。

估计不丢功能能删掉正文约 470 词（约 10%），脚本约 100 行（约 3%）；B 里建议补回约 250 词。灵魂部分：局部完整，各 reference 里保留了不少"为什么"（见 B"保留，勿删"）；全局不完整，`SKILL.md` 开头只有术语定义，没有讲这件事的意义和应有的态度；另外两次减重删掉了几句"为什么"，值得补回（见 B 缺口 3、4）。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| A1 | `story-parity.md` `## The criterion, in one shape`、`boundary-check.md` `## The criterion, in one shape`、`journey.md` `## The criterion, in one shape`、`harness-guard.md` `## The criterion, in one shape`（"The `to-tickets` skill's … holds it."） | 6、4 | 四节各只有一句指针；`013b2bb1` 把判据写法搬到 `to-tickets` 的 `references/cutting-interface-tickets.md` `## Criterion shapes` 后留下的。`SKILL.md` `## Find your moment` 第三行已经把"Writing a story, boundary, journey or harness guard criterion"路由到同一处 | `SKILL.md` 那一行路由；切票的 agent 加载的是 `to-tickets`。无剩余风险 | 删掉四个小节标题和指针（约 80 词）。`harness-guard.md` 那一节里混进了一段与判据写法无关的 `leaves_machine` 段落（"What widens the allowed set…"），挪到文件开头第二段之后 |
| A2 | `story-parity.md` 开头 "Three agents use this page. An agent taking design facts before implementation uses **`--render-only`**…" 和 `## --render-only` | 6 | `--render-only` 的命令、输出目录、values 文件路径在 `implement` 的 `references/writing-interface-code.md` `## Before the first line` 完整写了一遍，那是实现者动手那一刻加载的文件；它只指回本文件的 **The two sides** | `writing-interface-code.md`；`story-parity.py` 的 `--help`（`--render-only` 的 help 写了 values 路径）。无剩余风险 | 删 `## --render-only` 整节和开头那句中的 render-only 分句（约 75 词）；**The two sides** 保留（它是 values JSON 的字段定义，`writing-interface-code.md` 指向它） |
| A3 | `story-parity.md` `## Exit codes`（"`0`: one line `STORY OK <passed>/<total>`…"） | 1、6 | 与 `story-parity.py` 模块头 `Exit codes` 一节重复；exit 1 的意义在 `## The DIFF line`，exit 2 的意义在 `## Negative controls` 和每条拒绝自己的三段文字里。按 `SKILL-SET-REVIEW.md` `### Scripts and judgement`，完整退出码表留在脚本旁边 | 脚本头部；`## The DIFF line`。剩余风险：无 | 删掉三条退出码（约 40 词）；最后一句 "`--out <dir>` keeps both screenshots, their pixel difference image and the ARIA capture" 并入 `## The DIFF line` 末尾（人看证据图时需要知道去哪找） |
| A4 | `journey.md` `## Exit codes`（"**`0`**, `JOURNEY OK <name>`: the script passed…"） | 1、6 | 与 `journey.py` 模块头的六行输出表重复；`GREEN WITH BREAK`、`GREEN WITHOUT PRODUCT`、`LEFT THE PRODUCT UP` 三行本身就带修法（见 `journey.py` `_run_named` 的 `green_explanation` 和 `LEFT THE PRODUCT UP` 那段 print） | 脚本打印的行。剩余风险：无 | 整节压成一句判断："On `JOURNEY FAILED`, what to fix is what the last line names: the script's own output, not this judge's words." 删约 80 词 |
| A5 | `harness-guard.md` `## Exit codes` 的 `0` 和 `2` 两条 | 1 | 复述 `harness-guard.py` 头部；`2` 的拒绝自带下一步（`refuse_markers` 给出 `target_config.py --check` 命令） | 脚本。剩余风险：无 | 只留 `1` 那条里的修法（"Move a leak into `.mmw/`… or name the file in `leaves_machine`…; point it at `scenes.json` instead"）：脚本只打印 `HARNESS LEAK <file>:<line>`，不给修法，这段判断必须留。删约 40 词 |
| A6 | `product-answers.md` `## What the repository answers` 的 **`checks`** 条（"The run lands as a `ticket.checked` event of its own, run `repo-checks`…"） | 1 | 后半段复述 `verify-ticket.py --closeout` 的内部行为：事件名、`met`/`unmet`、最后 20 行、形状不对算 `unmet` 不算缺席。读这一条的是填 `.mmw/target.json` 的 agent，它需要的是形状、超时、在仓库根运行、收到 `MMW_BASE_REF`，以及"失败会让票留着不关"。事件怎么读，是 `implement` `SKILL.md` step 8 和唤醒它的那条事件的事 | `verify-ticket.py`；`implement` step 8。剩余风险：低 | 保留前两句（形状、`DEFAULT_TIMEOUT`、`{"run", "timeout"}`、`MMW_BASE_REF`），末尾加一句 "A command that fails keeps the ticket open, so every entry must pass on the base branch as it stands."；删掉事件机制那部分（约 70 词） |
| A7 | `SKILL.md` `## Resolve <scripts> once` 第二、三句（"Other skills that run these scripts take that directory as `--tools <scripts>`; `verify-ticket.py` puts it on the `PATH`…"） | 2、6 | `--tools` 是 `dispatch.sh`、`verify-ticket.py` 调用方的参数，加载本技能的 agent 用不到；PATH 那半句在 `verify-ticket` `SKILL.md` 第 22 行和 `SKILL-SET-REVIEW.md` 第 116 行各有一份 | `verify-ticket` `SKILL.md`。剩余风险：手跑判官的 agent 不知道要补 PATH | 换成一句 "A criterion names a judge bare; run one by hand as `<scripts>/<name>`."（约省 25 词） |
| A8 | `SKILL.md` 末行 "**A reviewer** never starts the product." | 2 | 放在 "Which event depends on your role" 下面，但它不是一个事件。reviewer 不会读到它：`dispatch.sh` 第 109 行的 `PRODUCT_RULES` 只拼进 worker 的启动 prompt（第 1946 行），`code-review` 各文件都不指向 `## Five rules while the product is running`；`code-review` 的 `references/ui-reviewer.md` 已经写了 "The story service that command starts takes no lease and is not the product" | `ui-reviewer.md` 那句。剩余风险：无 | 删掉这一条；"Which event depends on your role" 连同它的列表改成一句 "A worker opens a `fault` child, as the `implement` skill says, and stops."（`implement` `SKILL.md` 第 24 行是动作所在） |
| A9 | `SKILL.md` 规则 5 括号里的判官清单（"a judge script (`story-parity.py`, `boundary-check.py`, `journey.py`, `harness-guard.py`)"） | 6 | 同一份清单在同一文件第 8 行开头段已列出；整份"流水线故障"清单还出现在 `implement` `SKILL.md` 第 24 行和 `verify-ticket` `references/sub-issues.md` 表第 1 行 | 第 8 行。剩余风险：无 | 括号删掉，保留 "a judge script"（约 8 词）。规则编号和标题不要动，见"与其他技能的重复或交接问题" |
| A10 | `boundary-check.md` `## The four-column boundary test` 第二段 "The outbound call module is the layer the consuming repository names…" 与 `product-answers.md` 第 27–29 行 "**A boundary test replaces the outbound call module** the consuming repository names — the layer that emits the call…" | 6 | 两处定义同一个概念。写测试的 agent 那一刻读的是 `boundary-check.md` | `boundary-check.md`。剩余风险：无 | `product-answers.md` 那条只留保证本身："**A boundary test replaces the outbound call module**, which the repository names ([boundary-check.md](boundary-check.md))."（约省 25 词） |
| A11 | `journey.md` 第 26 行 "Playwright's own API is what drives the product; there is no driver between the script and the page." | 3 | 后半句是历史残留：这里原来有一个 `screen_driver.py`（见 `mmw-v2/downstream-notes/450-target-config-check.md`），"there is no driver" 是在告诉读者一个已经没有的东西 | 前半句。剩余风险：无 | 改成 "Drive the page with Playwright's own API." |
| A12 | `SKILL.md` frontmatter `description` 第一句 "Acceptance criteria that start or compare a running product, and what a repository answers so they can run." | 用户既定裁定（description 只写触发条件） | 这是一句"它是什么"，不是触发条件 | 第二句 "Use when …" 已含全部触发点。剩余风险：改 description 需要开新会话才生效 | 删第一句，或改写成触发条件；按用户裁定处理，不单独讨论 |

合计约 470 词。以下几处看起来像冗余，实际不是，不要删：
- `SKILL.md` 规则 2 里 "The script refuses without a lease and prints the command…" 与 `product-answers.md` **`start`** 条里 "It refuses to start with no lease and prints the command…"：前一处写给跑产品的 agent，后一处是对仓库 `start` 的要求，写给实现 `start` 的 agent。两处各在自己的读者动手时加载。
- `SKILL.md` 规则 4 与 `refusal.py` 的 `REPORT_BLOCKED`：拒绝文字是那一刻的副本，规则是事先的副本。`refusal.py` 头部记录的 2026-09-05 事故（三个 worker 拿到同一个正确的拒绝，各自发明了等待、重试循环、杀进程三种反应）证明两处都需要。
- `story-parity.md` 的 **The two sides** 字段表和 **Element parity** 的 `position` 规则：按 `SKILL-SET-REVIEW.md` `### Scripts and judgement`，"the exact rule the script will apply when it later judges the agent's output" 应当留下；实现者靠它预判会出哪条 `DIFF`。

## B. 灵魂

### 保留，勿删

- `SKILL.md` `## Five rules while the product is running` 开头段 "Several runs share one machine… You never choose a port, start a backing service, or work out who holds what"：告诉 agent 它身处一台多人共用的机器，端口和进程不是它的。
- `SKILL.md` 规则 1 "another run's product looks exactly like a stuck one"：一句话说清为什么"看起来卡住的进程"也不能杀。
- `SKILL.md` 规则 3 "the next run has no person in it"：说明人工步骤为什么是自动化的缺陷，而不是可以手动绕过的东西。
- `SKILL.md` 第 38 行 "an event on the ticket is the only thing the relay of the `dispatch` skill wakes anybody for: a plain comment carries none, and a session that ends its turn wakes nobody"：说明"只发评论"会让事情静默停住。
- `product-answers.md` 第 11–15 行 "An `App · ` page mounts the product's own composition module… so a region the product leaves unwired stays unwired on the story page"：说明 story 页为什么不能自己接线；否则产品漏接的地方在验收里是绿的（`to-tickets` merge-note 第 164 行记了这个真实问题）。
- `product-answers.md` "A `data-ui` id repeats only on the repeating part of a list… makes one of them unpairable"：规则带着原因。
- `product-answers.md` **`start`** 条 "returns only once the product is usable, not merely alive"，以及 "so a journey that saves changes nothing of this machine's own"：说明目标，不只说做法。
- `product-answers.md` **`stories`** 条 "presentational, fed by that data and nothing else… so the one thing it needs is a port"：说明 story 服务为什么不拿租约（lease）。
- `product-answers.md` 第 93–94 行 "Scripts a person runs on their own machine may stay where they are, provided they call the same start code"：只保留一条代码路径。
- `story-parity.md` "a scene stands for a state, so the clicked object needs no data of its own" 和 `input` 的理由 "it is what the design page itself drew the scene from"：没有这两句，写 story adapter 的 agent 会给被点击的对象另造数据。
- `story-parity.md` `## Element parity` 末句 "This leaves a whole top-level block move unreported, reports the parent whose movement carried its children…"，以及 `## The DIFF line` "The named id and property are the complete repair target; pixel images are supporting evidence, not another verdict"：告诉修 `DIFF` 的 agent 该改哪里、不该改什么。
- `journey.md` 第 6–8 行 "There are few of them on purpose: the user names which paths are worth one, and the default three are money, sign-in, and one submit chain"：告诉 agent 旅程（journey）很贵，只给真正要紧的路径用。
- `journey.md` **End by reading the result back from another page.** 整段：说明什么样的断言才算证明了东西。
- `journey.md` `## The negative control` "A helper that starts the stack when it finds nothing answering defeats the negative control"：来自 agentflow 2026-09-11 的真实事故（`journey.py` `still_up` 的 docstring 记了）。
- `boundary-check.md` `## Selecting one row's test` 第一段（前缀匹配会选中两条测试的陷阱）：这是 agent 自己想不到的知识。
- `boundary-check.md` "A row about choosing one item of a list… clicks one the starting scene has not already chosen, or its assertion holds without the click"：正好是最容易出错的那个判断点。
- `boundary-check.md` 末段 "The helper and the mock together make the second pass mechanical…"：说明负控制（negative control）为什么成立。
- `harness-guard.md` "it is a back door opened for automated acceptance that ships to a customer's machine with the release"：把一条文件规则和客户后果连在一起。
- `harness-guard.md` "never a name assembled at run time to get past it… a check that is evaded reports nothing about the leaks beside what evaded it"：说明规避检查的代价。

### 缺口与补充草稿

- **缺口 1：`SKILL.md` 开头只有定义，没有讲这件事的分量和应有的态度。** 刚加载技能的 agent 知道有四个判官、一个租约，却不知道：夜里没人看界面，判据全绿，票就关、代码就落地；每个判官都特意设计成能变红；它自己的任务是让"绿"只能意味着产品对了。缺了这层，判官变红时 agent 最自然的反应是让断言更宽松、在 story 页上补样式、在更低一层 stub 网络。这些做法今晚能过，缺陷却交到了客户手里。已删掉的原文 "These controls prevent accidental cheating caused by an agent following an old implementation habit; they are not intended to defeat deliberate sabotage"（`013b2bb1` 从 `story-parity.md` 删除）也属于这层意思：负控制兜不住所有情况，其余靠 agent 自己诚实。放在 `SKILL.md` 第 8 行定义段之后：

  > These judges are the only eyes on an interface during a night: when every criterion is green the ticket closes and the code lands with no person looking at the screen. Each judge is built to go red when what it guards is missing (the story judge perturbs its inputs, a boundary test reruns without the click, a journey reruns with one interface broken), but those controls catch habits, not every shortcut. Your part is the same discipline from the other side: write the story, the test, the journey and the harness so that green can only mean the product is right. When a judge is red, change the product, or open a child when the design or the contract is wrong; never make the check easier to pass.

  这里和 ADR 0008（`docs/adr/0008-silence-is-never-a-pass.md` `## Considered Options`）有一处张力：ADR 否决了把"沉默不是通过"写进 `verify-ticket/SKILL.md`，理由是 worker 用不上。本草稿不讲闸口怎么设计，只讲写测试、写旅程的 agent 应该怎么做，是 worker 在动手那一刻能照做的内容。按任务书，以任务书为准。

- **缺口 2：四个判官各管什么、问题该归谁，没有一处写明。** agent 遇到清单外的情况（例如一个布局问题被 journey 断言到、一个点击行为被 story 截图看到）时没有依据判断归属，容易把检查塞进最容易变绿的那个判官里。放在缺口 1 那段之后，一句：

  > The four split one question so none answers all of it: the story judge says whether the product looks like the design and nothing about what a click does; a boundary test whether one control does what its contract row says, with the network mocked at the outbound call module; a journey whether a few paths that matter still work against the real product; the harness guard whether anything built to make the product drivable leaks into what ships. A defect belongs to the judge whose question it is.

- **缺口 3：规则 3、规则 5 的"为什么"在减重时被删了。** `cb45a515` 删掉了规则 3 的 "Satisfying it makes a broken automation look healthy" 和规则 5 的 "A workaround built instead hides it from every ticket after yours."。这两句正是 agent 在"手动点一下就能过"或"绕开这个坏掉的脚本"那一刻需要的理由；没有它们，规则读起来只是禁令，agent 在清单外的变体上（例如手动种一条数据、临时改一下 `.mmw/target.json`）就没有依据。补回原文：

  > 3. … Report the ticket blocked: satisfying it makes a broken automation look healthy, and the next run has no person in it.
  >
  > 5. … a fault in one of those is not yours to route around and not a reason to keep trying: a workaround built instead hides it from every ticket after yours.

- **缺口 4：`boundary-check.md` 没有说断言该怎么写才能通过第二遍，也没说为什么 mock 要落在 outbound call module 这一层。** `013b2bb1` 删掉了 `## Why the second pass is not optional`（"An assertion that does not depend on the click reads exactly like one that does: both exit 0, both print a pass"）。现在的文件说了 `fetch`/msw/nock "is not allowed"，却没说理由；遇到清单外的写法（axios 拦截器、IPC 桥接层的 stub），agent 无从判断。放在 `## The four-column boundary test` 末段之后：

  > An assertion that does not depend on the click reads exactly like one that does: both exit 0. So assert what only the click can produce: the request the mock recorded, the marked value it returned, the scene only that click reaches. Mock at the outbound call module and nowhere else: lower, and the test checks a request the product's own call layer never builds; higher, and it skips the code that turns a click into a request.

- **缺口 5：`product-answers.md` 没有讲自动化里为什么不能有真钥匙、不能让动作离开本机。** `## Rules` 只剩一行 "Real keys exist only on a paid-smoke ticket labelled `ready-for-human`."；`leaves_machine` 的解释在 `4372d901` 被删（原文 "opening the system browser, calling a paid service, writing a machine-global location"），现在正文完全没提 `leaves_machine`，只剩 `target_config.py --check` 的一句提示。这一条涉及钱和真实客户，agent 需要知道分量。在 `## What the repository answers` 加一条，并改写 `## Rules`：

  > - **`leaves_machine`.** Everything a run would do that reaches past this machine (opening the system browser, calling a paid service, sending mail, writing a machine-global location) records under `MMW_AUTOMATION=1` instead of happening, and the file that records it is listed here. `[]` is an answer; a missing key is not.
  >
  > ## Rules
  >
  > A night repeats every criterion unattended, often many times; with a real key each repeat can spend money or reach a real customer, and nobody is watching to stop it. So automation uses placeholder keys, vendor stubs and local accounts, and real keys exist only on a paid-smoke ticket labelled `ready-for-human`.

- **缺口 6（推断，没有找到事故记录）：`story-parity.md` 没有告诉修 `DIFF` 的 agent 不能在 story 页上修。** story 页只是把真实组件放进一个 scene；在 story 页或 adapter 里补一层样式或包装来消掉 `DIFF`，会让 story 和设计一致而产品不一致。`implement` 的 `writing-interface-code.md` `## One code path` 管的是数据路径，不管样式。放在 `## The DIFF line` 末尾：

  > Fix the product component, not the story page: the story page only puts the real component into a scene, so a style or wrapper added there to close a `DIFF` makes the story match the design while the product does not.

- **缺口 7（可选）：`journey.md` `## The break switch` 没说为什么断路开关（break switch）必须由产品自己实现。** `cb45a515` 删掉了 "Two alternatives do not establish the same fact…"（用改动前的代码跑、在前面加转发代理）。实现开关的 agent 可能想用代理代替。补一句即可：

  > The switch lives in the product because only the product's own routing reaches every path its frontend takes; a forwarding proxy in front of it misses a frontend that calls its backend by another address.

## C. 死板的流程

这个技能里真正死板的结构不多。大部分硬规则是判官与产品之间的接口（`[data-story-root]` 的位置、`BREAK ARMED` 的逐字输出、`MMW_NEGATIVE=1` 时 helper 什么都不做），脚本按字面检查，必须保持硬。`## Five rules while the product is running` 也应保持硬规则：它们源于 2026-09-05 的真实事故，而且另外三个文件按编号引用（见下一节）。

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| C1 | `boundary-check.md` `## Selecting one row's test` 第三段 "The command is run by hand twice. Before the criterion is published, whoever cuts the ticket runs it…. Once the worker has written the test, the worker runs…" | 把一条完成标准写成了按角色分的两步流程，读者要自己拆出"什么算对" | 换成目标加完成标准，按运行器分的例子保留："A row's `--run` selects that one test and nothing longer. It is right when renaming the test makes the command exit non-zero (the cutter checks this before publishing) and the command as written reports exactly one test run (the worker checks this once the test exists). A runner that exits 0 on an empty selection needs its flag for failing on zero tests." 省约 40 词，也覆盖清单外的运行器 |
| C2 | `product-answers.md` **`start`** 条中 "A port check tests for a listener the way the product's server binds (with `SO_REUSEADDR`…)" | 在一份声明 "How a given repository meets them is its own" 的文件里规定了一种实现手法 | 先写目标，手法作为例子："A port that a product just stopped left in `TIME_WAIT` is free: a check that reports it held refuses a run nothing blocks. Test for a listener the way the server binds, for example with `SO_REUSEADDR` as Python's `http.server` does." 陷阱是真实的（#541），内容保留，只调换主次 |

## 脚本

注意：`CODING_STANDARDS.md` 第 10 行规定 "Script headers record dated, version-pinned measurements from real runs"。所以脚本注释里的日期和事故（`lease.py` 头部的 2026-09-05、`listener` 的 2026-09-12、`story-parity.py` `stop_tree` 的 "ten Vite servers"、`harness-guard.py` `tracked` 的 agentflow #703/#704、`design_render.py` `_Server` 的 2026-09-21 实测）都是按规定写的，不算发现。它们恰好说明 `lease.py` 的双重端口检查、`stop_tree`、`tracked()`、`request_queue_size = 128` 守的都是真实发生过的路径，不是过度防御。

- **S1 死代码**：`refusal.py` `within_limit()`。全仓库没有调用方（`grep within_limit` 只命中定义本身）。删 2 行，无风险。
- **S2 没有调用方的 CLI 动词**：`lease.py` 的 `env` 动词（`main` 里 `if verb == "env"`）在脚本、文档、测试中都找不到调用方。`count` 动词和 `count_under()` 只被测试用（`mmw-v2/tests/dispatch/test_dispatch.sh` 第 2885、2952–2990 行，`test_lease.py` 第 417–432 行）；`count_under` 的 docstring 说 "in a gate means the gate is open"，但没有任何闸口调用它。`env` 可以直接删（约 5 行）；`count` 若删，dispatch 测试要改用 `list` 数行（约 35 行）。剩余风险：人手动排查时少一个命令，`list` 可以替代。
- **S3 守一条已不存在的路径**：`journey.py` `RETIRED_PASS_SIGNAL = "MMW_" + "JOURNEY_NEGATIVE"` 和 `_run_named` 里的 `env.pop(RETIRED_PASS_SIGNAL, None)`。自 #455（`mmw-v2/downstream-notes/455-journey-break.md`）起，没有任何代码再设置这个变量；它只防一个"从外层 shell 继承来的旧变量"。四问：从没触发过（没有日志或状态证据），正常输入走不到，前提是推理出来的。删掉后没人处理这种情况，风险是一个仍 export 这个变量的旧 shell 让旧 journey 脚本提前退出第二遍，而 downstream-note 455 已要求删掉这类分支。删 3 行，`test_journey.py` 第 467–469 行的对应断言一并删。
- **S4 只剩测试在用的参数**：`design_render.py` `wrapper_page(inline_head=…)` 和 `navigate(reload=…)`。`inline_head` 的 docstring 说 "which is what the negative control needs: an error that is in the bytes the server sends"，但现在的负控制由 `story-parity.py` 的 `FONT_CONTROL_JS` / `REMOVE_IDS_JS` 在客户端注入，已不用它；两处的调用方只有 `mmw-v2/tests/ui-acceptance/test_design_render.py`（第 260、325 行）。删约 6 行，连带两条测试。
- **S5 过时的文字**：`story-parity.py` 模块 docstring 第 29 行说 exit 2 的原因之一是 "the contract still carries a key the judge no longer executes"，对应的 `retired_ids`/`trigger` 拒绝在 `7988611b`（2026-09-20）加入，之后已被删掉，代码里现在没有这条分支。`product_root()` 的 docstring "(AC1–AC3 `cd` there)" 引的是某张旧票的判据编号，读者用不上。两处删掉；`product_root()` 本身只是 `tc.repo_root()` 的一层包装，可以内联。
- **S6 同一个文件有五个读取器**：`.mmw/target.json` 被五处各自解析，错误措辞和容错各不相同：`target_config.target_config()`、`target_config.target_main()`、`lease.target_json()`、`harness-guard.load_target()`、`story-parity.load_stories_config()`。其中 `story-parity.load_stories_config()` 不捕获 `json.JSONDecodeError`，文件写坏时 agent 看到的是一段 Python traceback，而不是三段式拒绝（`main` 只接 `SystemExit`）。这是真缺陷，不只是重复。建议在 `lease.py` 里只留一个读取函数（`target_config` 导入 `lease`，反过来会循环导入，所以放在 `lease.py`），缺文件返回 None、坏文件抛异常，各调用方自己写拒绝措辞。省约 30 行，同时修掉 traceback。
- **S7 可能已无作用的保护**（推断）：`boundary-check.py` `main()` 用 `judge_run(Path.cwd(), stop=True)` 包住整个运行。`judge_run` 是 `a5d65b5d`（#370，2026-09-12）加的，当时 boundary-check 自己会拿租约；现在它不调用 `leased_environment`，从不拿租约，所以只有被测产品测试自己拿了租约时，这层包装才有作用，而四列边界测试（four-column boundary test）按规定 mock 掉网络，不该启动产品。在 `verify-ticket.py` 下运行时，外层已经有一个 `judge_run`（`MMW_JUDGE_LEASE_OWNER` 已设），这层是空操作。`test_boundary_check.py` 没有测试覆盖它。可以删掉包装和 `from lease import judge_run`；剩余风险：有人手跑一个违规启动产品的边界测试时，租约留在非票 worktree 上，`lease.py list` 能看到。
- **S8 正常输入走不到的分支**（推断）：`harness-guard.py` `iter_files()` 在 `git ls-files` 失败时退回 `os.walk`。判据总是在票的 git worktree 里跑，测试也都先 `git init`（`test_harness_guard.py` 第 55 行）或用仓库内的 fixture。退回后的行为正是 `tracked()` docstring 描述为缺陷的那种（把运行时写出的文件也算进来）。建议改成拒绝："not a git repository; the guard judges what git tracks"。约 8 行。
- **S9 小的重复逻辑**：`journey.py` `still_up()` 与 `lease.py` `busy()` 遍历同一组端口、调用同一个 `listener()`，差别只是一个返回全部、一个返回第一个。可在 `lease.py` 加一个返回全部的函数，两处共用。约 8 行。
- **S10 两种模块加载方式**：`target_config.py`、`journey.py`、`boundary-check.py`、`harness-guard.py`、`lease.py` 用 `sys.path.insert` 加普通 import；`story-parity.py` 用 `importlib` 的 `_load`；`design_render.py` 的 `_refusal` 又把 `refusal.py` 以另一个模块名 `_mmw_refusal` 再加载一次。`design_render.py` 这样做有原因：它被 `extract_skeleton.py`、`pull_design.py` 按路径从别的技能加载，`sys.path` 里没有这个目录。`story-parity.py` 没有这个理由，可以改成和其他脚本一样。收益小，只记录。
- 不算发现、但顺手记下：`design_render.py` 的 `load_contract`、`load_catalogue`、`wait_for_mount`、`capture`、`visible_box` 抛出的 `SystemExit` 消息不是 `refusal()` 三段式（没有下一步），不符合 `CODING_STANDARDS.md` 第 10 行。它们不属于减重范围。`story-parity.md` **The two sides** 说 values JSON "uses the fields in **The two sides**"，实际 JSON 还多一个 `interactive` 字段（`UI_VALUES_JS`，供 `extract_skeleton.py` 用），表里没列。

## 与其他技能的重复或交接问题

- **标题和规则编号被外部按字面引用，改写时不能动**：`## Five rules while the product is running` 这个标题被 `dispatch.sh` 第 109 行 `PRODUCT_RULES`（拼进每个 worker 的启动 prompt）、`verify-ticket` `SKILL.md` 第 35 行、`references/sub-issues.md` 表第 1 行、`implement` `SKILL.md` 第 97 行引用；"rules 3 and 4" 和 "rule 1" 按编号被 `sub-issues.md` 和 `implement` 第 97 行引用。所以 C 节不建议合并规则 3–5。
- **流水线故障清单有三份**（`verify-ticket.py`、`dispatch.sh`、判官脚本、`lease.py`、hook、`.mmw/target.json`）：本技能规则 5、`implement` `SKILL.md` 第 24 行、`verify-ticket` `references/sub-issues.md` 表第 1 行。保留 `implement` 第 24 行（worker 动手时的那份，带命令）和 `sub-issues.md`（分类用）；规则 5 保留原则和缺口 3 补回的理由，清单按 A9 缩短。
- **`--render-only` 有两份**：`implement` 的 `references/writing-interface-code.md` `## Before the first line` 和本技能 `story-parity.md` `## --render-only`。保留前者（见 A2）。
- **判据写法**已移到 `to-tickets` 的 `references/cutting-interface-tickets.md` `## Criterion shapes`，本技能剩下四个指针小节（见 A1）。
- **reviewer 没有通往五条规则的路**：`dispatch.sh` 只给 worker 拼 `PRODUCT_RULES`；`code-review` 的各 reference 只借用本技能的 `<ui-acceptance scripts>` 令牌。所以本技能里写给 reviewer 的那一行无人读到（见 A8）。reviewer 只跑 story 服务，不碰产品，这样没有问题，只是那一行应该删掉。
- **`Resolve <ui-acceptance scripts> once` 在 `implement` 的 `writing-interface-code.md` 和 `code-review` 的 `ui-reviewer.md` 各有一份**：这是 `SKILL-SET-REVIEW.md` 脚本令牌规则要求的"每个文件自己定义令牌"，不是冗余。

## 没查到的

- 没有查 tracker（`gh issue list`）里 fault 子票的真实分布，所以 S3、S7、S8 的"从没触发过"只基于代码和测试推断，没有核对运行记录。`~/.mmw/leases/` 当前为空，`~/.mmw/instances/` 里有 `issue-556` 到 `issue-560` 等遗留数据目录，没有追查它们为什么还在。
- `story-parity.py` `_ensure_script_env()`（缺依赖时用 `uv run --script` 重新执行自己）只在 `python3 story-parity.py` 或 `uv run python story-parity.py` 这种调用方式下才会走到；本仓文档都不这么写。没有查消费仓库的旧票里有没有这种写法，所以没有把它列为过度防御。
- `story-parity.py` `parse_origin()` 接受三种格式（`origin=`、JSON、裸 URL），而 `story-parity.md` 只写了 `origin=<url>`。宽松解析没有坏处，没有列入。
- 没有读 `verify-ticket.py` 全文（约 4,000 行），只读了与租约相关的段落（第 69–74、1640–1750、1840–1860 行）；A6 中"closeout 自己负责事件"的判断依据是这些段落和 `implement` `SKILL.md` 第 95 行。
- 没有读 `docs/adr/0011`、`0028` 全文；缺口 1、2 的措辞没有对照这两份 ADR 的决定核对。
- 测试套件没有跑（任务书规定只读）。A、S 各条删改后要跑的测试集：`bash mmw-v2/tests/ui-acceptance/run.sh`；S2 还要跑 `mmw-v2/tests/dispatch/test_dispatch.sh` 中用到 `count` 的场景。
