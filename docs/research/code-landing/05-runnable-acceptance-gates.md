# 可运行验收门：每条验收标准带 CHECK / EXPECT，收尾填 EVIDENCE

问题：要不要在出票时就要求每条验收标准可运行；UI 标准怎么办。候选机制来自 `00-synthesis.md` §「三份报告共同推荐、无分岔的改法」第四行（取自 unlazy）。

路径约定：参考快照的路径相对 `docs/research/code-landing-refs/`；本仓自己的文件相对仓库根；`~/.claude/skills/` 下的技能和 agentflow 仓库写绝对路径。`file:12-15` 指该文件第 12 到 15 行。`ABANDON:` 与失败词汇不在本文，归 `08`。

## 1. 一句话结论

unlazy 的 gate 是「一条命令 + 一个只有成功才会打印的标记 + 一行指纹式证据」，通过条件是 exit 0 **且** EXPECT 匹配（`unlazy/references/gates.md:50-53`）；我们的 `to-tickets` 四条规则（`mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:40-43`）已经把「标题写成可判的结果」这一半做到了，缺的是命令这一半和三条作者规则（success-only marker、负控制、不把 brief 里的数字抄成 EXPECT）；命令应在 `to-tickets` 出票时从 spec 的 Testing Decisions 推导，推导不出就沿用 `to-tickets/SKILL.md:43` 的「stop and return to `/to-spec`」；UI 标准可以写成 runnable gate，命令是从 `issue-534/EXP/run.py` 提炼出的像素比对工具，失败时按已定规则转给 `Seam` 里的人看，人的接受写进基线旁的清单而不是直接打勾，这样 gate 仍然是机器可重跑的。

## 2. unlazy 一条 gate 的完整语义

### 2.1 形态

最小形态在 `unlazy/references/gates.md:14-28`。一条 gate 是四行：

```markdown
- [ ] G1: valid fixture imports completely
  CHECK: node scripts/check-import.mjs fixtures/valid.json
  EXPECT: import verification passed
  EVIDENCE: pending
```

解析规则（`unlazy/scripts/lib/gates.mjs`）：

| 规则 | 出处 |
| --- | --- |
| gate 行是 `- [ ] ID: outcome` 或 `- [x] ID: outcome`；id 必须显式，用行号推的 id 在行移动后不稳定 | `gates.md:35`；`gates.mjs:111-131` |
| id 只允许 `[A-Za-z0-9][A-Za-z0-9._-]*`，同一文件内不得重复 | `gates.mjs:129`、`:133-136` |
| `CHECK:` `EXPECT:` `CWD:` `EVIDENCE:` 必须缩进在 gate 下；不缩进的属性报错，不会静默变成 manual gate | `gates.md:36`；`gates.mjs:150-156` |
| 同一 gate 内属性不得重复 | `gates.mjs:166-170` |
| `#` 开头或 `- ` 开头的行结束当前 gate 的属性区 | `gates.mjs:207` |
| fenced code block 内的行全部忽略，按 CommonMark 围栏规则 | `gates.md:31`；`gates.mjs:51`、`:97-106` |
| `EXPECT:` 写成 `/pattern/flags` 是 JavaScript 正则，否则是子串；正则非法是 parse error | `gates.md:43`；`gates.mjs:52`、`:58-75` |
| 包裹斜杠永远赢：`EXPECT: /etc/app/conf/` 是正则 `etc/app/conf`；内部有未转义斜杠时警告 | `gates.md:44`；`gates.mjs:55`、`:221-233` |
| 零 gate 的 ledger 是 parse error，不是 `ALL MET` | `gates.md:42`；`gates.mjs:239` |

### 2.2 runnable vs manual

`gates.md:37`：runnable gate 同时有 `CHECK:` 和 `EXPECT:`；manual gate 两者都没有；只有一个是 malformed（`gates.mjs:212-220` 报 `runnable gates require both non-blank CHECK and EXPECT`）。manual gate 的例子是 `gates.md:25-26` 的 G3「migration wording is reviewed against the product decision」，只有 `EVIDENCE:` 一行。`unlazy/SKILL.md:12`：「use a manual gate only when no command can decide the outcome」。

### 2.3 通过条件：exit 0 且 EXPECT 双条件

`gates.md:50-53`：runnable gate 通过当且仅当 (1) 进程启动并以 0 退出，(2) `EXPECT:` 匹配 stdout 与 stderr 的合并输出。`gates.md:55`：非零退出的进程「never passes merely because its error text contains the expected token」；超时（默认 120 秒）、shell 启动失败、命令不存在、输出超 1 MiB 都算失败。

### 2.4 EVIDENCE 记什么

自动 gate 的 `EVIDENCE:` 由脚本写入，格式在 `unlazy/scripts/gate-check.mjs:759-765`：

```
exit=0; shell=<resolved shell>; cwd=<resolved cwd>; path=<PATH sha256 前 12 位>/<PATH 条目数> entries; EXPECT=matched; output-sha256=<合并输出的 sha256>; output-bytes=<字节数>
```

上限 900 字符。`gates.md:57` 解释设计：成功时不保存原始输出，只存指纹，「prevents a success token from hiding a process failure」，并让环境差异（PATH 不同）可见。失败时终端打印裁剪过的输出（`gate-check.mjs:752-757` 最多 8 行、480 字符），不写进 ledger。

manual gate 的 EVIDENCE 由人手写：`gates.md:102`「record the smallest non-sensitive fact that proves the outcome; do not paste full logs into a ledger」；`gates.md:101` 要求「Cite exact evidence and obtain a second review when the consequence warrants it」。

状态判定在 `gates.mjs:254-260`：abandoned → 未勾 `unmet` → 勾了但 EVIDENCE 为空或 `pending` 的 `unmet-no-evidence` → `met`。所以「打了勾但没证据」在 unlazy 里就是未过（`gates.md:57` 末句）。

### 2.5 `--reverify` 与 `--status` 的区别

| | `--status` | 默认运行 | `--reverify` |
| --- | --- | --- | --- |
| 执行 CHECK | 否（`gates.md:59`：「without executing a command or changing a file」） | 只跑未过的 runnable gate（`gate-check.mjs:27`、`:682`） | 跑每一条 runnable gate，包括已勾的（`gates.md:59`；`gate-check.mjs:29`、`:682`） |
| 对旧证据 | 只读出来报告，不重验 | 已过的沿用 | 「returns a gate to unmet when the oracle no longer passes」（`gates.md:59`） |
| 用途 | 审阅继承的 ledger、读命令（`gates.md:63`；`unlazy/SKILL.md:14-18`） | 自己工作时推进 | 父级验收子级（`unlazy/templates/gates-node.md:5-8` 的 N1 明确「use --reverify, not --status」`:34-35`） |

`unlazy/references/orchestration.md:35`：「`--status` alone is not re-verification」。这条区别是 `06`（独立 verifier）的输入：verifier 做的事等价于 `--reverify`。

### 2.6 批准边界（只记一句）

`gates.md:65`：「Approval confirms that a command may run; it does not prove that the command measures the English outcome」。unlazy 的 `--approve` 机制是它的脚本安全模型，不装脚本就不存在；但这句话是本文 §3 全部作者规则的前提：机器只能证明命令说的，证明不了标题说的。

## 3. gate-lint 抓哪些「写得不可能失败」的模式

`unlazy/scripts/gate-lint.mjs` 不执行任何 CHECK（`:12`），只读 ledger 判断 oracle 的词面。作者自己承认这是「deliberately advisory and whole-command only」（`:73-75`）。七条规则：

| # | 规则名 | 判什么 | 出处 | 级别 |
| --- | --- | --- | --- | --- |
| 1 | `tautological-check` | 整条 CHECK 只是 `echo …`、`printf …`、`true`、`:`、`exit 0` | `:76`、`:113-116` | warn |
| 2 | `weak-expect` | 整条 EXPECT（去空白、小写后）等于 `ok / okay / done / pass / passed / success / successful / succeeded / complete / completed / finished / yes / true / 0 / good / fine / working` 之一——这些词在失败输出里也会出现 | `:78-81`、`:118-121` | warn |
| 3 | `path-read-as-regex` | EXPECT 是 `/…/` 形式且内部有未转义斜杠，像路径却被当正则，点号成了通配 | `:123-126`；`gates.mjs:55`、`:73` | warn |
| 4 | `manual-gate` | 没有 CHECK | `:128-130` | warn |
| 5 | `unmeasured-number` | 没有 CHECK **且**标题含数字：「title states a number that nothing measures」 | `:131-134` | warn |
| 6 | `activity-not-outcome` | 标题以 `work on / improve / enhance / handle / support / ensure / make sure / try / attempt / look at / look into / investigate / consider / review / refactor / clean up / polish / update / tidy / address / deal with / add support` 开头 | `:83`、`:137-140` | warn |
| 7 | `mostly-manual` | 未放弃的 gate 里 runnable 少于一半：「a mostly manual ledger is prose with checkboxes」 | `:143-146` | warn（文件级） |
| — | `parse` | `gates.mjs` 的任何 parse error（缺 id、重复 id、半个 runnable gate、正则非法、ABANDON 指向未知 id、零 gate） | `:100-104` | error，exit 2 |

`--strict` 让 warn 也算失败并 exit 1（`:149-151`、`:178`）。`gates.md:113` 自述这些是「lexical signals」，`:115`「A lint finding is a prompt to sharpen the gate, not proof that the outcome is wrong」。

`gates.md:97-102` 另有六条作者规则，其中三条 lint 抓不到，只能靠人：

- **Observe the outcome directly**（`:97`）：命令要读标题点名的那个制品、服务或测量值。
- **Test negative controls**（`:99`）：写「不存在 X」这类断言前，用一个已知含 X 的 fixture 跑同一段逻辑，确认它会失败；否则文件路径错、pattern 写错都长得像「确实不存在」。
- **Measure supplied numbers independently**（`:100`）：「Do not make a number copied from the brief its own expectation」——脚本从源数据算出值、套验收规则、打印独立的成功标记。

### 3.1 哪些能写成技能正文里的作者规则

全部七条 lint 规则都是词面判断，人或 agent 读一遍票就能执行；三条 prose 规则本来就是给人的。按「没有脚本也能执行」的可操作性重排：

| 能直接写进技能正文 | 措辞（操作性指令） | 来源 |
| --- | --- | --- |
| success-only marker | EXPECT 是一行只有全部断言通过后才会打印的文字；不用 `ok / passed / done / true / 0` 这种失败输出也含的词单独做 EXPECT | `gates.md:98`；lint #2 |
| 命令要能失败 | CHECK 不是 `echo`、`true`、`exit 0`；它读标题点名的制品 | `gates.md:97`；lint #1 |
| 标题是结果不是活动 | 标题不以 improve / ensure / support / review / update 这类动词开头；写陌生人能判真伪的状态 | lint #6 |
| 数字要被测量 | 标题里的数字必须有一条 CHECK 去量它；EXPECT 不是把 brief 里的数抄一遍 | `gates.md:100`；lint #5 |
| 负控制 | 「没有 / 不出现 / 为空」类标准，先对已知阳性样本跑同一条 CHECK 确认会失败，把这次结果写进 EVIDENCE | `gates.md:99`；`unlazy/templates/gates-leaf.md:30-31` |
| manual 比例 | 一张票里 manual 标准不过半；每条 manual 标准写明看哪个制品、谁看 | lint #4、#7；`gates.md:101-102` |
| 正则陷阱 | EXPECT 里写路径就不要用 `/…/` 包起来 | `gates.md:44`；lint #3 |

只有 parse 级别的规则（缩进、重复 id）依赖脚本才有意义，本仓不装脚本时改成「每条标准有稳定 id，评论里按 id 引用」即可。

## 4. 我们的验收标准四条规则 vs unlazy 作者规则

`to-tickets/SKILL.md:38-43` 四条：(1) 外部可观察行为，(2) 精确值从 spec 或 prototype 制品抄，(3) 一条一判，(4) 指明验证处，指不出就回 `/to-spec`。

| unlazy 规则 | 我们是否已覆盖 | 差在哪 |
| --- | --- | --- |
| 标题是 outcome 不是 activity（lint #6） | 已覆盖：规则 1「Observable external behaviour … Not internals」、规则 3「independently true or false」 | 无 |
| 精确值（lint #5 的反面） | 已覆盖：规则 2 要求 exact values | 规则 2 只管标题里有数；没说这个数要被一条命令量出来（`gates.md:100`） |
| 指明验证处 | 部分覆盖：规则 4 指到测试层或人工检查的设备；`## Seam`（`to-tickets/SKILL.md:120-122`）指到目录和先例 | 只到「层 + 目录」，没有到「命令 + 期望输出」；`implement/SKILL.md:22` 让 worker 事后自由填「the command run and what it printed」 |
| runnable / manual 二分（`gates.md:37`） | 部分覆盖：规则 4 和 `Seam` 允许「a human check on a named device」 | 没有要求「写不出命令」必须显式标出，也没有比例约束 |
| success-only marker（`gates.md:98`） | **缺** | 现状没有 EXPECT 字段，无从谈起 |
| 负控制（`gates.md:99`） | **缺** | `tdd/SKILL.md` 也没有对应条款 |
| 不把 brief 里的数字抄成 EXPECT（`gates.md:100`） | **缺，且与规则 2 有张力** | 规则 2 说「copied from the spec」，unlazy 说「Do not make a number copied from the brief its own expectation」。两者不矛盾：规则 2 说的是**标题**里写精确值，unlazy 说的是 **EXPECT** 不能只是那个数。`tdd/SKILL.md:31` 的 Tautological 反模式给了同一条原则的测试版：「Expected values must come from an independent source of truth: a known-good literal, a worked example, the spec」——spec 里的值作为断言的期望是对的；错的是断言的方式让它不可能失败。 |
| 命令要读制品（`gates.md:97`） | 隐含在规则 1 | 没有明说 CHECK 不能是 `echo` |
| 稳定 id（`gates.md:35`） | **缺** | `<issue-template>` 的 `- [ ] Criterion 1`（`to-tickets/SKILL.md:126-127`）没有 id；票评论无法按 id 引用 |

另一处张力：`to-tickets/SKILL.md:135` 禁止票里写「implementation file paths or code snippets」，但允许「paths to source material and test directories」。CHECK 命令里出现测试文件路径属于后者；出现被测源码路径属于前者。写规则时要点明这条线。

## 5. 命令在哪一步产生：`to-spec` 还是 `to-tickets`

### 5.1 `to-spec` Testing Decisions 现在给到的粒度

`mmw-v2/upstream/skills/engineering/to-spec/SKILL.md:66-72`，四样东西：

1. `:68` 第一句是 seam：两侧各是什么真东西、哪些外部 seam 可以 stub。
2. `:70` 什么是好测试（只测外部行为）。
3. `:71` 这个功能落在哪些测试层，每层的目录和要抄的先例；「every ticket cut from this spec will name one of these layers as the place it is verified」。
4. `:72` 提交前要跑的命令。

也就是「层 → 目录 → 先例 → 整套命令」，没有「每条标准一条命令」。`03` §8 已把这一点列为未确定。

### 5.2 建议：`to-spec` 给每层的「单文件调用形」，`to-tickets` 推导每条

理由：spec 写的时候还没有测试文件，没法给每条命令；票写的时候有了标准，才知道该跑哪个文件的哪个用例。`to-tickets/SKILL.md:41` 已经要求从 spec 抄精确值，抄命令是同一动作。

`to-spec` 只加一样：`:71` 每层除了目录和先例，写出**跑单个文件（或单个用例）的调用形**和它的成功输出长什么样。例如 `pnpm vitest run <file> -t "<name>"` 输出 `Tests  1 passed (1)`；`uv run pytest <file>::<test> -q` 输出 `1 passed`。UI 层写像素比对工具的调用形和基线所在目录（§6）。这仍是「层」级的信息，不违反 `:62` 不写实现路径的约束。

`to-tickets` 推导：每条标准 = 层的调用形 + 这条标准对应的测试文件与用例名（票里命名，worker 按 `/tdd` 红→绿去写）+ 该层的成功输出作为 EXPECT。用例名就是标准正文，这样 EXPECT 里出现用例名时它是 success-only 的（失败输出打印的是 `✗`/`FAILED` 行）。

### 5.3 推导不出来时

沿用 `to-tickets/SKILL.md:43`：「If you cannot name that place, the spec is missing a decision: stop and return to `/to-spec`. Do not invent it.」把「place」扩成「place and command」。两种例外允许写 manual：

- 结果本身没有机器可判的形式（文案措辞是否符合产品决定，`gates.md:25-26` 的 G3 型）。写明看哪个制品、由 `Seam` 里的谁看。
- 命令存在但本机跑不了（需要真机、需要付费服务）。这是 `06` verifier 的 `verifier-blocked` 场景，标准仍写 CHECK/EXPECT，EVIDENCE 记为何没跑。

manual 标准超过一半时，按 lint #7 的精神，回 `/to-spec` 补测试层，而不是出一张「prose with checkboxes」的票。

### 5.4 与 `/tdd` 的关系

`implement/SKILL.md:14`「Use /tdd where possible, at pre-agreed seams」；`tdd/SKILL.md:22`「Test only at pre-agreed seams」。出票时 CHECK 指向一个尚不存在的测试文件，不与 TDD 冲突：`/tdd` 的红→绿循环正是写出那个文件的过程，票只是先说了它的名字和它该断言什么。风险是 worker 写一个恒真的测试——这是 `tdd/SKILL.md:31` Tautological 反模式，和 lint #1 是同一件事在不同层；靠 `06` 的 verifier 和 `code-review` 的 Spec 轴抓，本文不解决。

## 6. UI 标准的 CHECK：像素比对怎么写成一条 gate

### 6.1 已定的比对方式与现有雏形

`00-synthesis.md` §「第一轮之后已定的事」：基线是从 Claude Design 下载回叶子目录的文件；按场景 × 窗口截图逐像素比对；差异非零不判失败，把基线、实现、diff 三张图贴到票上给人看。

雏形是 `/Users/cheuklapchan/agentflow/.worktrees/2026-07-07-douyin-banner-regenerate/docs/prototypes/2026-07-07-douyin-banner-regenerate/issue-534/EXP/run.py`（下称 `run.py`）。它的输入输出形态：

| 项 | 现状 | 出处 |
| --- | --- | --- |
| 两侧来源 | 写死：`MOCKUP` 目录和 `DIST` 目录，各起一个 `http.server` 静态服务（端口 18765/18766） | `run.py:26-29`、`:81-86`、`:117` |
| 场景 | 写死 43 条 `(name, query, extra wait ms)`；两侧打开同一个 `index.html?<query>` | `run.py:33-78`、`:136` |
| 窗口 | 写死 `1440×900`、`1180×720`，`device_scale_factor=1`，`reduced_motion="reduce"`，`locale="zh-CN"` | `run.py:30`、`:131` |
| 截图 | Playwright Python，`networkidle` 后再等 350 ms + 场景等待；viewport 截图 | `run.py:136-139` |
| 差异 | numpy + PIL：任一 RGB 通道差 > 16 记为差异像素；输出 count / total / pct / 外接矩形 box / `size_equal` | `run.py:31`、`:89-104` |
| 控制台 | 记两侧的 error / warning 行 | `run.py:133-135` |
| 输出 | `.scratch/…/issue-534/evidence/round-<N>/media/{name}-{w}x{h}-{mockup,react,diff}.png` + `index.html` 证据页；stdout 每场景一行 | `run.py:138`、`:143-146`、`:156-200` |
| 退出码 | **恒为 0**，没有阈值判定 | `run.py:153` |
| 前置 | 先 `vite build`（写死 `node_modules/.bin/vite`） | `run.py:112` |
| 依赖 | `numpy`、`PIL`（Pillow）、`playwright`（Python 包）；由 agentflow 的 `pyproject.toml` 提供（`numpy>=2.0.0` L135、`Pillow>=10.0.0` L133、`playwright>=1.54.0` 在 dev 组 L145/L156），`uv run` 从仓库根解析 | `run.py:20-22`；`/Users/cheuklapchan/agentflow/.worktrees/2026-07-07-douyin-banner-regenerate/pyproject.toml` |

`issue-534/README.md:9` 的门槛是「每个场景在两档窗口下差异像素占比 ≤ 0.1%，且差异不落在文字、边框或布局上；React 页面控制台无错误」；`:45` 第 2 轮 86 次比对全部 0.000%；`:73` 把 `run.py` 定为 S2/S3 的视觉验收工具，「差异 > 0 就看差异图」。

### 6.2 写成 gate：命令、EXPECT、失败后转人工

按 `gates.md:98` 的 success-only marker，工具必须改成：全部场景差异为 0（或 ≤ 阈值）且控制台 0 错误时打印一行标记并 exit 0；否则 exit 1，打印差异场景清单和证据页路径。这样它才是一条能失败的 runnable gate；`run.py:153` 恒 0 退出的形态不能直接当 CHECK。

gate 形态（票里）：

```markdown
- [ ] AC4: 商品项目库 library-populated、library-empty 两个场景在 1440×900 与 1180×720 下与基线逐像素一致，页面控制台 0 条 error
  CHECK: uv run mmw-v2/tools/visual-parity.py --baseline docs/prototypes/<task>/<issue>/UI/baseline --impl http://127.0.0.1:5173 --scenes library-populated,library-empty --out .scratch/<issue>/parity
  EXPECT: PARITY OK 4/4
  EVIDENCE: pending
```

差异非零时的处置与 gate 语义怎么兼容——三种写法，取第三种：

| 写法 | 与 unlazy 语义的关系 | 问题 |
| --- | --- | --- |
| A. 整条写成 manual gate（「人看三张图」） | 合法（`gates.md:37`） | 浪费了机器能判的 0 差异情况；lint #4/#7 会报；`03` C 候选明确要 diff 触发人看，不是全靠人 |
| B. runnable gate，失败后人直接打勾、EVIDENCE 写「某某看过接受」 | 违反 `gates.md:57`：勾和证据脱离命令结果；`--reverify` 语义下会被再次判 unmet | 一旦 `06` 的 verifier 重跑，勾被推翻 |
| **C. runnable gate；人的接受写成数据，不写成勾** | 保持双条件 | 需要工具支持一个「已接受差异」清单 |

写法 C 的流程：CHECK 失败 → worker 把该场景的基线、实现、diff 三张图（`run.py:166-168` 的三列）贴到票上，不打勾 → `Seam` 里命名的人看 → 接受则把 `{scene, viewport, box, 接受人, 日期, 理由}` 追加到基线目录旁的 `accepted-diffs.json`，工具重跑时把落在已接受 box 内的差异像素视为一致 → CHECK 变绿，EVIDENCE 记录命令结果并引用该清单条目。不接受则票留着，进 `08` 的失败词汇。这样「人看」发生在 gate 之外，gate 本身仍是机器可重跑的；人接受的是差异而不是勾。

清单放在票的 `## Seam` 段声明一次，不在每条标准下重复：`Seam` 已经是「where this ticket is verified … A ticket whose only verification is a human check names the device and the steps」（`to-tickets/SKILL.md:122`），把「diff 非零时贴图给 <人>，接受写入 accepted-diffs.json」放这里正合适。

### 6.3 提成 mmw-v2 通用工具要改什么

| 改动 | 为什么 |
| --- | --- |
| 两侧改成参数：`--baseline <目录或 URL>`、`--impl <目录或 URL>`；目录则自起静态服务，URL 则直接打开 | `run.py:26-29` 写死在 agentflow 的路径 |
| 场景表改成文件：`scenes.json`，每条 `{name, query, wait_ms}`，放在基线目录里随基线一起下载/维护 | `run.py:34-78` 写死 43 条；场景键要与 `UI-UX-COVERAGE.md` 一致（`README.md:9`） |
| 阈值与退出码：`--max-pct`（默认 0）；`--console-errors 0`；全部通过打印 `PARITY OK <n>/<n>` exit 0，否则 exit 1 并逐行打印 `DIFF <scene> <viewport> <pct>% box=<x0,y0,x1,y1>` | `gates.md:50-55`、`:98`；`run.py:153` 恒 0 |
| 尺寸不等即失败 | `run.py:92-93` 按最小尺寸裁剪后比，`size_equal`（`:104`）算了但没用在判定上；一侧页面更高时差异被静默丢掉 |
| `accepted-diffs.json` 支持 | §6.2 写法 C |
| 去掉 `vite build`（`run.py:112`）；构建是被测方自己的事 | 通用工具不该知道被测方的构建 |
| 证据页沿用 `run.py:156-200` 的三列格式，与 `prototype/evidence-page.md:14-18` 一致：header、legend、summary table、body、how it decided；`:16`「No verdict column: the page reports」——裁决在 stdout 标记和票评论里 | 已有格式，可直接搬 |
| 依赖用 PEP 723 内联元数据写在脚本头部，`uv run` 自动建环境：`numpy`、`Pillow`、`playwright`；首次需 `playwright install chromium` | `AGENTS.md` 首段：运行时只有 bash、python3 标准库和按需的 `uv`；不能依赖被测仓库的 `pyproject.toml` |

不用 `playwright-cli` 做截图这一步的理由：`~/.claude/skills/claude-design-blocks/scripts/serve.sh:5`、`:10` 的做法是 `playwright-cli resize 1440 900` 后 `playwright-cli screenshot --filename=…`，`~/.claude/skills/playwright-cli/SKILL.md:98-102` 的 `screenshot` 段只给了 `--filename`、`--hires` 和元素目标，没有 `device_scale_factor`、`reduced_motion`、等待策略的控制，逐像素比对需要这些固定（`run.py:131`）。`playwright-cli` 留给 `claude-design-blocks/SKILL.md:36` 那种交互式走查（`open_page / sel / clk / q / errs / shot`），不做比对。

依赖清单：`uv`（本机 `/opt/homebrew/bin/uv`）、Python 包 `numpy` `Pillow` `playwright`、Chromium（`playwright install chromium`）。`playwright-cli 0.1.18` 在 `~/dev-environment/node-global-tools/node_modules/.bin/`，本工具不需要它。

### 6.4 基线的形态（未确定，影响截图方式）

已定「下载回叶子目录的文件是基线」，但没定下载回来的是什么文件。若是 `.dc.html`：`claude-design-blocks/SKILL.md:35` 说 `mk.py` 的 helmet 把 `#dc-root` 固定成 `DC_FRAME`（默认 `1440x900`）居中在灰色页面上，`:59` 说组件依赖 `./styles/…` 相对路径和 `support.js`；那么基线截图要截 `#dc-root` 元素而不是 viewport，且要能离线渲染 `.dc.html`。若下载的是 PNG，工具只需读图，不需要起基线侧的浏览器。这是 §8 第一条。

## 7. 没有 unlazy 脚本时 EVIDENCE 记到什么粒度

unlazy 的 EVIDENCE 是脚本算的指纹（§2.4）。手写约定按同一原则——「能证明命令跑过、跑在哪、结果是什么，且不贴日志」——取以下字段，一行：

```
EVIDENCE: <commit 短 SHA>; cwd=<仓库相对目录>; exit=<码>; matched="<输出里匹配 EXPECT 的那一行，原样>"; <日期>
```

- `commit` 对应 pstack「A new head SHA voids the row」（`03` §2「不信自报的机制」列）：换了 SHA 证据作废。
- `matched` 只抄一行，是 `gates.md:102`「smallest non-sensitive fact」的手写版；不贴完整输出。
- 失败时 `exit≠0` 或 `matched=none`，后面接失败输出的最后两行（对应 `gate-check.mjs:752-757` 的裁剪），勾不打；措辞归 `08`。
- UI 标准另加 `evidence=<证据页路径>`；有已接受差异时加 `accepted=<accepted-diffs.json 里的条目 id>`。
- manual 标准：`by=<人>; artifact=<看的是哪个文件/截图>; fact=<一句话>`。
- 负控制（§3 规则）：`negative-control: <阳性样本> exit=<非零码>`，只在「不存在 / 为空」类标准写。

不记 shell 和 PATH 指纹：那是跨机器重跑的环境对照，本仓测试手工跑（`AGENTS.md` 首段），`06` 的 verifier 在同一机器重跑时用 commit 对齐即可。

## 8. 建议：票模板里每条验收标准的写法，implement 收尾怎么填

### 8.1 票里的写法

`<issue-template>` 的 `## Acceptance criteria`（`to-tickets/SKILL.md:124-127`）改成每条四行，id 稳定：

后端命令的例子：

```markdown
- [ ] AC1: POST /projects 用已存在的名字创建时返回 409，响应体 error 字段是 name-duplicate
  CHECK: pnpm vitest run tests/api/projects.create.test.ts -t "duplicate name returns 409 name-duplicate"
  EXPECT: /Tests\s+1 passed \(1\)/
  EVIDENCE: pending
```

- 标题：规则 1–3 不变，精确值（`409`、`name-duplicate`）从 spec 抄。
- CHECK：层的单文件调用形（§5.2，来自 Testing Decisions）+ 票命名的测试文件与用例名；测试文件路径属于 `to-tickets/SKILL.md:135` 允许的「test directories」。
- EXPECT：测试框架只在通过时打印的计数行；`passed` 单独一个词会触发 lint #2，带计数的整行不会。数字 `409` 不进 EXPECT，进测试断言（§4 张力的解法）。

UI 像素比对的例子：见 §6.2 的 AC4，配 `## Seam` 段一句：「视觉标准用 `visual-parity.py`；diff 非零时把该场景三张图贴到票上给 <人> 看；接受写入 `UI/baseline/accepted-diffs.json` 后重跑」。

manual 标准的例子（`gates.md:25-26` 型）：

```markdown
- [ ] AC7: 欠费门禁的文案与 #540 决议第 3 条一致
  MANUAL: <人> 对照 #540 评论 <链接> 逐句读实现页 billing-debt-gate 场景
  EVIDENCE: pending
```

`MANUAL:` 不是 unlazy 的属性；unlazy 的 manual gate 是「什么都不写」（`gates.md:37`），但本仓不装解析器，显式一行「谁看什么」比空着更能被 `06` 的 verifier 和 `code-review` 读到。若将来装脚本，这行要拿掉。

### 8.2 出票时的自检（替代 gate-lint）

`to-tickets/SKILL.md:74-83`「6. Read every ticket back」现有四项检查，加一项：每条验收标准过一遍 §3.1 的七行表——CHECK 不是 echo/true；EXPECT 不是单个弱词；标题不以活动动词开头；标题里的数字有命令在量；「不存在」类标准写了负控制；manual 不过半；EXPECT 里的路径没被 `/…/` 包住。

### 8.3 implement 收尾

`implement/SKILL.md:22` 现在是「the evidence for each acceptance criterion — the command run and what it printed — and tick the criteria that passed」。改成：

1. 逐条原样运行票上的 CHECK，不改命令；改了命令等于改了标准，要先在票上评论。
2. exit 0 且 EXPECT 匹配 → 填 EVIDENCE（§7 格式）→ 打勾。任一条件不满足 → EVIDENCE 记失败、不打勾，措辞按 `08`。
3. UI 标准失败 → 贴三张图，不打勾，等 `Seam` 里的人；人接受后按 §6.2 写法 C 重跑，再回到第 2 步。
4. manual 标准 → 由 `MANUAL:` 里命名的人填 EVIDENCE，worker 不代填、不代勾。
5. 评论末尾一行计数：`met <n> / unmet <n> / manual-pending <n>`（`unlazy/SKILL.md:82` 要求报 met / unmet / abandoned 计数；abandoned 归 `08`）。

`implement/SKILL.md:25`「A ticket with an unmet criterion stays open」不变。

## 9. 未读 / 未确定

- 未确定：Claude Design 下载回叶子目录的基线是什么文件（`.dc.html`、PNG、还是别的）；决定像素比对工具要不要渲染基线侧、截 viewport 还是截 `#dc-root`（§6.4）。
- 未确定：`playwright-cli screenshot` 的默认行为（viewport 还是整页、`device_scale_factor`、是否遵守 `prefers-reduced-motion`），`~/.claude/skills/playwright-cli/SKILL.md:98-102` 没写；本文因此选 Playwright Python 做比对，若确认 `playwright-cli` 能固定这些参数，工具可以少一个依赖。
- 未确定：`to-spec/SKILL.md:71` 加「单文件调用形」后，wayfinder map 或 prototype 阶段产生的 UI 场景键（`README.md:9` 的 `UI-UX-COVERAGE.md`）由谁维护成 `scenes.json`——属于 `01` 落地前议题。
- 未读：`unlazy/scripts/gate-check.mjs` 只读了 `:27-29`、`:52`、`:675-780` 与 grep 命中行；`scripts/lib/check-supervisor.mjs`、`SECURITY.md`、`references/orchestration.md`（只读了 `:20`、`:32-35`、`:43`、`:53`、`:70`、`:80`）、`references/parallel.md`、`method.md`。
- 未读：`issue-534/EXP/react-library/src/App.tsx`（73 KB，与比对工具无关）；agentflow 的 `pyproject.toml` 只 grep 了依赖行。
- 未运行：按任务要求没有运行 `run.py`、`gate-lint.mjs`、`gate-check.mjs`；§6.1 的行为描述来自读代码，第 2 轮结果引自 `issue-534/README.md:45` 和 `.scratch/…/evidence/round-2/index.html` 的表头。
