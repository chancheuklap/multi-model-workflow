# 代码落地三阶段：第一轮调查汇总

三份分阶段报告：`01-pre-landing-worker-contract.md`、`02-during-landing-anti-drift.md`、`03-post-landing-evidence-review.md`。参考快照在 `docs/research/code-landing-refs/`。本文只做汇总与分岔，不做决定。

## 三份报告一致指出的根因

| 症状 | 根因（出处） |
| --- | --- |
| spec 很大，worker 用不上 | 票的 `## Read first` 只裁 Sources，`implement/SKILL.md` L10 仍要求读 spec 全文（`01` §3 末段） |
| 写码时自我发挥 | prototype 只是「reference」不是契约，写码中没有偏离上报条款，没有写路径边界，没有过度构建规则（`02` §5 第 1、2、4、5 条） |
| 无视 HTML mockup | 流程里「读过，但没有人验」：`code-review` 找 spec 的顺序不含 `prototypes/`，收尾三步不回头比（`03` §3 末行） |
| 无法无人看守 | 写码者自报、自评、自勾、自关票，没有第二个人重跑；失败/验不了/放弃是同一句话（`03` §5 第 1、5 条） |

## 三份报告共同推荐、无分岔的改法

每条只取一家（既定原则）。

| 议题 | 取自 | 内容 | 出处 |
| --- | --- | --- | --- |
| 写路径边界 | unlazy | 票加 `Owns:` 仓库相对 glob；并发票之间不相交；路径外的改动算偏离 | `01` C2、`02` D |
| prototype 胜出物即契约 + 偏离即上报 | pstack architect | 实现时发现契约装不下的需求，先在票上评论「缺什么、是 prototype 错/需求漏/实现越界」再继续，不默默加 | `02` A |
| 过度构建控制 | ponytail | 7 级梯子 + 例外清单 + `skipped: [X], add when [Y]` + 非平凡逻辑留一个可运行检查；措辞写成操作性指令 | `02` C、§4.2 |
| 每条验收标准怎么算过 | unlazy | 出票时每条带 `CHECK:`/`EXPECT:`，写不出命令的标 manual；收尾填 `EVIDENCE:`；exit 非零或不匹配不打勾 | `03` A |
| 谁来判 | pstack | 收尾前插一个不同模型家族的只读 verifier，重跑 `CHECK:`，按 commit SHA 写一行裁决（`live-ui-verified / unit-test-verified / type-check-only / verifier-blocked / verifier-failed`），覆盖 worker 自报 | `03` B |
| 失败、验不了、放弃 | unlazy | 未过的标准保留原文 + `ABANDON: <id> <reason>`；有 ABANDON 的票不关，评论首行 `HANDOFF REQUIRED`，末尾 met/unmet/abandoned 计数 | `03` D |

## 需要决定的分岔

1. **票裁 spec 的方式**（`01` C1-A vs C1-B）：A 把 `Parent` 指名的 Implementation Decisions 小节原文内联进票（grok），票自足；B 保持指针，只把 `implement` L10 改成只读指名小节 + Testing Decisions + Out of Scope（mattpocock），改动最小。无人看守跨宿主派发时 A 更稳。
2. **UI 票的验收形态**（`01` C3 vs `02` B / `03` C，同为 pstack 但机制不同）：C3 是每条验收写「看到什么 + 截图名 + pass predicate」，人眼看；visual-parity 是胜出 variant 与实现页各截同状态截图做 image diff。`03` C 提出折中：diff 非零不判 fail，而是把 diff 图贴到票上交给 `Seam` 命名的人看。前提是 `UI.md` L116 要求并入时重写 variant，像素不必相同。
3. **偏离走哪条通道**（`02` A 即时上报 vs `01` C5 / `02` E 收尾 summary 写 deviations，grok）：取 A 则 C5 只保留「Skipped」行。
4. **交接前自审**（`03` E swarm-forge 二次原样调用 vs unlazy「Audit the final report」）：同一议题二选一。

## 先于一切要定的前提

1. **mmw-v2 没有 spawn prompt。** 没有任何一处定义「派一张票给子代理时给它的那段文字」（`01` §7 第 5 条）。分岔 1 与 `01` C4「`Standing:` 常驻规则」都默认「票本身就是 brief」。
2. **mockup 的形态。** `prototype/UI.md` L77 的 variant 是挂在真实路由上用 `?variant=` 切换的组件，不是独立 HTML 文件；截图基准应是该路由下的渲染结果（`03` §3 首段、§8）。
3. **宿主能否截图和 image diff。** 技能表里有 `playwright-cli`，三份报告都没核对它的能力（`02` §7、`03` §8）。

## 这轮明确不动的

- 无人看守相关：提问出口、时限、常驻规则通道、决策日志（`01` G5–G10、`03` §5「可以后补的」第 5 条）。
- grok「0 issues 才退出」的无界循环：与本仓记忆「reviewer 权限限定在票的验收门」冲突（`03` §6 末段）。
- ponytail 探针法：只作技能改动验收工具，最小做法见 `03` §7。

## 第一轮之后已定的事（2026-08-28）

| 议题 | 决定 |
| --- | --- |
| agent 开工拿到的输入 | 票本身；不另写派发词 |
| spec 怎么进票 | 只给指针，不抄；`implement` 只读 `Parent` 指名的小节 + Testing Decisions + Out of Scope，不读 spec 全文 |
| UI 原型的路径 | `prototype` 出一版满意的 mockup → 上传 Claude Design 精修（做法沿用 `docs/research/code-landing-refs/` 之外的 claude-design-blocks 技能）→ 下载回叶子目录，下载回来的文件是基线 |
| 实现与基线怎么比 | 按场景 × 窗口截图逐像素比对；差异非零不判失败，把基线、实现、diff 三张图贴到票上给人看 |
| 写码中发现契约装不下 | 继续做，在 spec 下开 sub-issue 记录 |
| code-review 之后 | 修与票的验收标准或 spec 决策相关的发现，其余开 sub-issue；最多两轮，第二轮仍有票内发现则不关票 |

## 第二轮调查结果（2026-08-28）

五份报告各对应一个机制。下表是每份的结论、搬过来要动的地方、代价与不适用之处；细节看各文件。

| 机制 | 文件 | 结论 | 要动的地方 | 代价 / 不适用 |
| --- | --- | --- | --- | --- |
| 写路径边界 `Owns:` | `04-owns-write-boundary.md` | 加。unlazy 的 `OWNS:` 脱离脚本后剩三件事：出票时逼出票人想清楚动哪些目录、开工时给 worker 边界、收尾时一条 `git diff --name-only <base>..HEAD -- . ':(glob,exclude)<glob>'` 算出路径外改动（§3，本机 git 2.55 验证） | 票模板 `## Seam` 后加 `## Owns`（目录级 glob，一行一条，禁裸 `**`）；`to-tickets` 第 2 步不再可省、第 6 步回读加核对、L135 禁令改措辞；`implement` L8 开工核对加一项（§7） | 不引入 claim/lease 脚本；并发重叠在出票时人眼比对、加 Blocked by 边解决（§5） |
| 可运行验收门 `CHECK:`/`EXPECT:`/`EVIDENCE:` | `05-runnable-acceptance-gates.md` | 加。`to-tickets` 四条规则已做到"标题可判"，缺命令那一半和三条作者规则（success-only marker、负控制、不把数字抄成 EXPECT）（§4） | `to-spec` Testing Decisions 每层加"单文件调用形 + 成功输出样子"；`to-tickets` 出票时推导每条，推不出回 `/to-spec`，允许显式 `MANUAL:` 行且不过半（§5、§8）；`implement` 收尾只有 exit 0 且匹配才打勾（§8.3）；EVIDENCE 手写一行格式（§7） | UI 标准要一个通用工具 `visual-parity.py`（PEP 723 + `uv run`，依赖 numpy/Pillow/playwright-python + chromium），从 `issue-534/EXP/run.py` 提炼：参数化、场景文件、阈值与退出码、尺寸不等即失败；差异非零时人的接受写入 `accepted-diffs.json` 而不是直接打勾，gate 仍可重跑（§6） |
| 独立 verifier | `06-independent-verifier.md` | 加，但只对四类票派：有 `MANUAL:` 条目或 `Seam` 指向界面、无人看守、`Owns` 触及迁移/鉴权/对外接口/共用路径、`CHECK:` 要起 app/DB（§5.2）；其余 worker 自己重跑，裁决标 `self-reported` | 收尾三步改五步：code-review（≤2 轮）→ 最终 SHA 重验 → 评论 `VERDICT <sha> <level> by <model|self-reported>` + 逐条 EVIDENCE → push/PR → 关票或 HANDOFF（§8.1）；新增第四个 subagent `mmw-v2/agents/verifier/`，brief 只给验收标准原文、SHA、Seam、FORBIDDEN、REPORT，不给 diff/spec/prototype（§8.2-8.3） | "不同模型家族"在 pstack 只是断言无数据；Claude Code 只能选 Anthropic 内模型，Grok/Codex 能否按定义文件切模型未确定（§3）。技能正文只能写"能选模型时选一个和自己不同的"；不能派子代理时降级为自己从干净 shell 重跑（§6） |
| 过度构建纪律（ponytail） | `07-overbuild-discipline.md` | 有条件加。只有 S1"grep every caller"有 Sonnet/Opus 级 A/B 证据；rung 4"用原生元素"只有 Haiku LOC 证据且**会推向换掉 mockup 契约**，必须绑定契约（§4.3、S2）；安全例外与"无 unrequested abstraction"需加 Seam 例外（§5.2）；"Ship the lazy version and question it"、`demo()` 自检、Persistence/Intensity 不采（§5.3、§6、S8-S11） | `implement` L12 之后、L14 `Use /tdd` 之前插入 ≤10 行操作性指令（S1-S7，§7.1-7.2）；收尾评论加 `skipped: [X], add when [Y]` 行（S5） | 无 hook、无插件（ADR 0003），规则不常驻，压缩后是否还在未实测；采纳前必须按 §8 四个探针（P1 shared-caller、P2/P2′ native-vs-drawn、P3 over-contract、P4 trust-boundary）两臂实测，无差异的句子不入正文 |
| 失败词汇 | `08-failure-vocabulary.md` | 加。标准层 `met / unmet / abandoned` + 列首 `ABANDON: AC<n> <failed|blocked|impossible|decision> <理由>`；票层评论首行 `ALL MET` 或 `HANDOFF REQUIRED: n abandoned (kinds), m unmet, k met of total`，末尾 `Counts:`（§5.3） | `ALL MET` → `gh issue close --reason completed`；`HANDOFF REQUIRED` → 不关票不关 PR，`ready-for-agent → ready-for-human`；夜里开的 sub-issue 带 `needs-triage` 不带 `ready-for-agent`；`implement` 开工 `--add-assignee @me`（§7）；`gh` 2.96 实测支持 `--parent`、`--blocked-by`、`close --reason` | 下游被 block 的票什么都不做（frontier 定义已是"blocker 全关才解锁"，§6）；UI 票在无人看守下按已定"diff 非零给人看"几乎必以 `decision` HANDOFF 收尾（§8） |

### 第二轮之后仍要用户决定的

1. **路径外改动怎么记**：`04` §7.4 主张记在票的收尾评论 `Outside Owns:` 行（修正对象是票的 `Owns`），不是 spec 下的 sub-issue；与已定的"契约装不下 → sub-issue"分属两个通道。
2. **verifier 判 `verifier-failed` 之后**：pstack 是"修一次、新 SHA 再验一次"（`06` §4.3、§8.1），`08` §7.4 示例按 code-review 同一上限直接 HANDOFF；二选一。
3. **`decision` 类 HANDOFF 的标签**：`ready-for-human`（`08` 取此，因 `needs-info` 定义为等 reporter）还是改 `needs-info` 含义。
4. **ponytail 句子的采纳门槛**：`07` §8 要求探针实测有差异才入正文；同时本仓记忆"抄写纪律：参考项目内容逐字复制"与"操作性改写才有效"的证据相抵，需要裁决（`07` §7.3）。
5. **UI 票夜间必 HANDOFF**：是否接受；或允许第二次运行时 `accepted-diffs.json` 已有条目则自动过（`05` §6.2 写法 C 已支持）。

### 第二轮核实的事实

- Claude Design 项目文件可整体读回：`.dc.html`、`styles/`、`data/`、`support.js`（变色龙项目 `638b3e81…` 的 `list_files` 实测 21 个文件）。基线 = 下载回叶子目录的整个目录，静态服务即可渲染；像素工具截 `#dc-root`（`05` §6.4 的未定项由此定）。
- `playwright-cli` 能截图、能 diff ARIA snapshot，但无 `device_scale_factor`/`reduced_motion` 控制，逐像素比对用 playwright-python（`05` §6.3）。
- `gh` 2.96.0：`--parent`、`--blocked-by`、`close --reason`、JSON `blockedBy/parent/stateReason` 可用（`08` §5.1）。

## 第二轮之后的定案（2026-08-28）

| 议题 | 决定 |
| --- | --- |
| Worker 与 verifier 是谁 | Worker 是 Herdr 拉起的独立会话（可在任一宿主），每票一个 worktree，按阻塞关系决定启动顺序；verifier 是编排会话自己的只读子代理。"票即输入"= Herdr 启动 worker 时喂的提示词 |
| `Owns:` | 加；路径外改动记在收尾评论 `Outside Owns:` 行，不开 sub-issue |
| `CHECK:`/`EXPECT:`/`EVIDENCE:` | 加；写不出命令的标 `MANUAL:`，不过半 |
| verifier 次数 | 只审一次。worker 自跑 → verifier 一次 → 没过的 worker 修并自跑填证据 → 关票；不复审 |
| ponytail | 收：grep 每个调用方修共用处；写 helper 前先在仓库与 Read first 的 prototype 找现成；加文件/依赖/配置前说出已有的为何不够；安全与"票里明确要求的东西"不许简化；收尾 `skipped: [X], add when [Y]`。不收：原生控件替代自绘、先交懒版本再问、`demo()` 自检、`ponytail:` 注释、交互模式段。措辞写成动作 + 票字段；"逐字复制"改为保留骨架只换对象；用第一张真实票穿行验证 |
| UI 验收 | 两档自动判定：ARIA 树（去 Claude Design 运行时包裹）diff 必须为零；同场景同窗口截图差异像素 ≤ 3%（默认，Testing Decisions 可改）。没过即 `failed`，worker 修；不产生 `decision`；三张图贴票供人参考。不用 `accepted-diffs.json` |
| 失败词汇 | `ALL MET` 关票；`HANDOFF REQUIRED` 不关票、`ready-for-agent → ready-for-human`；`ABANDON: AC<n> <failed|blocked|impossible|decision> <理由>`；sub-issue 带 `needs-triage`；开工 `--add-assignee @me` |

下一步：`to-spec`。

## 第三轮调查结果（2026-08-28）

| 项 | 文件 | 结论 |
| --- | --- | --- |
| UI 验收实验 | `prototypes/code-landing/ui-gate/EXP/README.md` | **可行。** 下载回来的 Claude Design 页离线可渲染（本地化 `support.js` 从 unpkg 取的 React/ReactDOM/Babel 三个脚本）；ARIA 树经三条归一化（去 generic/group、去 landmark 名、提升嵌套 `main`）后与 React 实现 diff 为 0；像素差 0.027%/0.044%（只是字形抗锯齿）；负控制（错误场景）23–29% 像素、28 行树差，被抓住。默认阈值定 1%。未覆盖：非默认场景要靠 props 而非 URL 切换 |
| Herdr 派发模型 | `09-herdr-dispatch-model.md` | Herdr 只负责起会话、发 prompt、看生命周期；**没有完成信号**，"做完"= 票状态（关票或 `HANDOFF REQUIRED` 评论）+ agent idle。派发词最小形态"技能名 + 票号"，前提是 cwd 在票的 worktree、`gh` 已登录、权限参数随 `agent start -- <args>`。子代理对 Herdr 不可见。**冲突**：定案"verifier 是编排会话的子代理"在白天手工场景没有对象、在夜间场景要求 worker 停下等握手；verifier 作为运行 `implement` 的那个会话的子代理则两个场景同一份流程（§5.3–§6） |
| 上次尝试尸检 | `10-previous-attempt-postmortem.md` | 19 小时、34 个提交、77 文件 5345 行、无一张真实代码票即合 main；hook 事件注给了不该拿工人纪律的那组；纪律两处存放；关卡镜像文件重新引入漂移；抄参考漏了消费端、三态压两态、逐字校验全绿但无效；技能写成带出处的中文说明书。§5 十条"不能再犯"；§6 标出本轮可能漏项：交接前自审、每票派给哪个宿主/模型、新词集中定义 |

### 第三轮之后的定案

| 议题 | 决定 |
| --- | --- |
| verifier 的父会话 | 运行 `implement` 的那个会话派 verifier 子代理（白天手工、夜间 Herdr 派发同一份流程）；编排会话只读票上的 `VERDICT` 行。不能派子代理时按 `06` §6 降级为 `self-reported` |
| 交接前自审 | 采 unlazy "Audit the final report"：写收尾评论前重读票全文与 `Read first` 每项，把每条验收标准追到 `EVIDENCE:`，`Counts:` 重数后填；不做 swarm-forge 二次调用 |
| UI 验收阈值 | ARIA 树 diff = 0；像素 ≤ 1%（Testing Decisions 可改）；工具自带负控制，负控制不过则不信任本次结果 |
| 新词定义 | 进入 spec 阶段时由 `grill-with-docs`/`domain-modeling` 建根 `CONTEXT.md`，全英文术语（`Owns`、`CHECK`/`EXPECT`/`EVIDENCE`、`MANUAL`、`ABANDON` 四个 kind、`ALL MET`/`HANDOFF REQUIRED`、`VERDICT` 五级） |
| 技能正文纪律（沿用上次裁决） | 一律英文；不写出处、不写落地记录；每个角色的纪律只写在它自己的定义文件里 |
| 落地节奏（沿用尸检 §5） | 一次一份 spec、一组机制；没有一张真实代码票从头跑到尾不合 main；抄机制先列消费者 |

仍要用户定：**每张票派给哪个宿主、哪个模型，写在哪里**（上次的 `models.md` 六角色表与初/高级定级都已删；本轮定案未承接）。

### 每票派给谁（2026-08-28 定案）

沿用上次的角色表数值，只取本轮存在的角色；表以后放消费仓库 `docs/agents/`，派发时人现场选初级或高级，不写进票、不打定级标签。

| 角色 | 宿主 kind | 模型串 | 思考强度 |
| --- | --- | --- | --- |
| 初级工人 | cursor | cursor-grok-4.6-high | high |
| 高级工人 | grok | grok-4.6 | xhigh |
| 复验者（worker 会话的只读子代理） | 与 worker 同宿主 | 该宿主里与 worker 不同的模型（`06` §6） | high |
| 编排者（自动化阶段再用） | claude | opus | medium |

规划者、升级顾问本轮没有对应角色，不列。

## 块 A 定案：票的形态（2026-08-28）

| 议题 | 决定 |
| --- | --- |
| 验收标准编号 | 每条 `AC<n>`，出票时编号，之后不重排；评论按 id 引用 |
| 人工项写法 | 显式一行 `MANUAL: <谁> <看哪个制品>`；不写 CHECK/EXPECT |
| 人工项比例 | 出票硬规则：人工项过半不出票，回 `/to-spec` 补测试层 |
| `Outside Owns:` 的起点 | `git merge-base main HEAD` 自动算，不记进票（每票一个 worktree、按阻塞关系串行开工，分支都从 main 开） |
| `Owns` 两档规则 | 确认：为过本票 AC 不得不改的范围外文件 → 改并在收尾评论 `Outside Owns:` 逐条说明；与 AC 无关的顺手改动 → 不改，开 sub-issue |

新增待定：**F14** 验收标准的跑与判用手写约定还是直接装 unlazy `gate-check.mjs`（归块 B；`05` §2.5、`04` §2.4）。

## 讨论进度（2026-08-28）

- 已定：块 A（F1 AC 编号与 MANUAL 行、F2 Outside Owns 起点）。
- 块 B 全部定完（顺序、一轮、F3、F8、F9、F10、F14、子代理原则、code-review 形态与派发）；F15 后补。
- 块 C 定完（F7）。下一步：块 D（F4 prototype 产物怎么进 Claude Design、F5 to-spec 加调用形、F6 非默认场景基线、F12 工具放哪）。
- 未开：F3、F8、F10、F14（块 B 其余）；F7（块 C）；F4、F5、F6、F12（块 D）；F11（块 E）；F13（块 F）。
- 蓝图页：`11-target-pipeline.html`（artifact 9cb8f46c…），第 7 节登记表随每次定案更新。

## 块 B 定案（2026-08-28，进行中）

| 议题 | 决定 |
| --- | --- |
| verifier 与 code-review 的顺序 | **先验后审**：worker 自跑 CHECK → 在 worker 会话内派 verifier 重跑 → 没过 worker 修并自跑填证据（不派第二次）→ 全过后才 code-review。理由：verifier 若在后面发现漏项，返工后又要再 review，是浪费 |
| code-review 轮数 | **一轮**审、worker 修一轮、不复审（覆盖「第一轮之后已定的事」的 ≤2 轮）。修完在最终 commit 自跑 CHECK 填 EVIDENCE；`VERDICT` 行照实绑 verifier 验的那个 commit |
| verifier 与 code-review 是否合并 | 不合并：verifier 只跑票上的 CHECK，code-review 只读 diff；两者都是子代理 |
| verifier 派发条件 | **每票都派**，不分类型（否决 `06` §5.2 的四类票） |
| 子代理收什么 | **原则**：子代理只收此刻才知道的信息（票号、起点 commit）；固定的动作、禁令、汇报格式写进它自己的定义文件；票是事实与状态的唯一存放处，谁要都自己 `gh issue view`，不由另一个 agent 转述。跨宿主的 worker 同理：派发词只有技能名 + 票号 |
| verifier 的 brief 与产出 | brief = 票号。它自己读票、`git rev-parse HEAD` 取 commit、在同一 worktree 跑 CHECK；结果由它自己 `gh issue comment` 写 `VERDICT` 行与逐条结果到票上，worker 之后读票。`06` §8.2「原样粘贴」及其 pstack 理由作废 |
| code-review 的两个子代理 | 待改：smell baseline 与两轴 brief 固定 → 做成 `mmw-v2/agents/` 下两个定义；prompt 只给起点 commit + 票号，spec 沿票的 `Parent` 自读。改上游技能，写 merge-note。`ui-evaluator` 同样违反此原则，但 ui-qa 本轮不接入，只登记 |
| `verifier-blocked` | 不是交人的理由。verifier 不改仓库文件但可以动环境（装依赖、换端口、从项目配置找连接串/密钥）；先自修环境再跑；仍起不来才写 `verifier-blocked`，由 worker 修环境后自跑，与 `verifier-failed` 同路，不触发 HANDOFF。F10 关闭 |
| code-review 技能形态 | `SKILL.md` 只做路由 + 三个 reference：`dispatch.md`（派发者做什么）、`standards-reviewer.md`（brief + smell baseline）、`spec-reviewer.md`；派发 prompt 只给起点 commit + 票号 |
| code-review 谁派、reviewer 跑在哪 | worker 派（`implement` 加一段派发方式）。reviewer 模型必须够强，目前只有 Claude Code 的 opus 5 有资格；worker 是 cursor / grok build 会话，派不出 opus 子代理 → worker 用 Herdr 起一个 Claude Code 会话，派发词「`code-review <起点 commit> #<票>`」；该会话再派两个 reviewer 子代理。reviewer 的报告由它评论到票上，worker 读票，不经终端转述。白天你自己在 Claude Code 里做票时直接调 `/code-review` |
| code-review 方法论 | 暂用现役两轴；要加内容（发现闭环 `Status: fixed/wontfix`、Verification 一栏、更多人格）以后只改 `code-review` 技能。登记 F15，本轮不定 |
| code-review Spec 轴要不要看基线 | 不看。Spec 轴只读 spec 文本；照不照基线由 UI 验收标准的 visual-parity `CHECK:` 判（worker 写码期间迭代跑、步 8 自跑、步 9 verifier 重跑，三次都不需要人）。F8 关闭 |
| 验收标准怎么跑、怎么判 | **vendor unlazy `gate-check.mjs`**（MIT，6 个文件约 2000 行，需 Node ≥ 16），账本从票派生：`gh issue view` 取 AC 段 → 临时文件 → `gate-check --approve [--timeout N]`（verifier 加 `--reverify`）→ 更新后的账本贴回票评论。没有第二份文件；审批目录设 `UNLAZY_APPROVAL_DIR` 到仓库外的 0700 目录，`--approve` 每次都带。实测见 `05` §10。`05` §7 手写 EVIDENCE 格式作废。放哪、怎么到消费仓库并入 F12。F14 关闭 |
| `decision` 类 HANDOFF 的标签 | `ready-for-human`，与其余三种 kind 相同；不加新标签、不改既有标签含义（用户：agentflow 的标签已够乱，要清理到只剩合法标签）。区分 kind 靠收尾评论 `ABANDON:` 行第二个词。F3 关闭。**块 B 全部定完** |

## 块 C 定案（2026-08-28）

| 议题 | 决定 |
| --- | --- |
| ponytail 五句入 `implement` 正文的验证方式 | 先写进正文，用第一张真实的票跑一遍看有没有问题；不做有句/没句两臂的对照实验。真票跑出具体问题（例如又过度构建）时，再针对那一句做对照实验。`10` §5 第 2 条按此修正。F7 关闭。**块 C 定完** |

## 块 D 定案（2026-08-28，进行中）

| 议题 | 决定 |
| --- | --- |
| prototype 产物怎么进 Claude Design | 流程不变：`prototype` UI 分支在真实页面上挂载变体（叶子目录 + 挂载点，落地删挂载点）→ 胜出后上传 Claude Design 精修 → 下载回叶子目录做基线。上传时 `claude-design-blocks` 读叶子目录里胜出版本的源码（状态、交互）和真实页面 `?variant=<胜出>` 的渲染结果（DOM、CSS），不加转换步骤，`prototype` 技能不改。F4 关闭 |
| `claude-design-blocks` | 改第 1、2 步：输入可以是 `prototype` 叶子目录的框架组件——源码读组件文件，CSS 与 DOM 取自真实页面 `?variant=<胜出>` 的渲染结果，数据从组件 props 抽。收进 `mmw-v2/skills/`（`self/claude-design-blocks`），正文开头按能力判断：需要 claude-design MCP 工具（`get_claude_design_prompt`、`DesignSync`、`render_preview`），没有就停下说明；不写宿主名 |
| `CHECK:` 的命令与 `EXPECT:` 从哪来 | 不改 `to-spec`，不建 TESTING.md，不给 `AGENTS.md` 加规矩。命令只在出票时写一次：`to-tickets` 从 spec 的 Testing Decisions（层、目录、先例、提交前命令）和先例文件用的框架推出；`EXPECT:` 对先例测试跑一次抄成功那一行。之后 worker 写码中跑单测、步 8/9 跑 gate-check，读的都是票上的 `CHECK:` 行。UI 验收标准用 F14 的 gate-check 跑 visual-parity；场景列表放叶子目录随基线维护。参考资料无 TESTING.md 模板。F5 关闭 |
| 非默认场景的基线 | 场景 = 组件 + `scenario` 属性。visual-parity 为每个场景生成一页只含 `<dc-import name="<组件>" scenario="<场景>">` 的包装页（照 `claude-design-blocks/scripts/mkharness.py` 的模式），放临时目录引用下载回来的组件文件，离线渲染截 `#dc-root`；基线文件不动。做工具时验证一次写死 `scenario` 属性能生效。F6 关闭 |
| 两个脚本放哪 | 新自有技能 `mmw-v2/skills/verify-ticket/`：`scripts/gate-check/`（vendor 的 6 个文件）+ `scripts/visual-parity.py`；正文一段：取票 AC 段 → 临时账本 → `gate-check --approve [--reverify]` → 更新后的账本评论到票。`implement` 步 8 写 `/verify-ticket #n`，verifier 定义文件写 `/verify-ticket #n --reverify`。UI 验收标准的 `CHECK:` 写 `uv run ~/.agents/skills/verify-ticket/scripts/visual-parity.py …`。不放 `implement/scripts/`（上游 subtree、且 verifier 也用）。F12 关闭 |
| 措辞 | 票是纵切的，没有「UI 票」；说「UI 验收标准」 |

| Claude Design 的两样产出 | 都进流程。① 「开发交接包」README 随基线下载进叶子目录，票 `Read first` 指向它，`to-tickets` 写 AC 的精确值与逐字文案从它抄。② 精修前用 `create-design-md` 生成 DESIGN.md，上传 Claude Design 建 design system；同一份放进消费仓库，`AGENTS.md` External References 指一行；每个项目一次。F16 关闭。**块 D 定完** |

- 块 D 定完（F4、F5、F6、F12、F16）。下一步：块 E 的 F11（派发三前提：各宿主权限参数、Herdr 名字、角色表放消费仓库哪个文件）。

## 块 E 定案（2026-08-28）

| 议题 | 决定 |
| --- | --- |
| worker 的 worktree | 宿主自己开：`cursor-agent -w issue-<n> --worktree-base main`、`grok --worktree=issue-<n>`；Herdr pane 开在仓库根，不用 `herdr worktree create` |
| 权限 | 全部放行：cursor `--force --trust`；grok / claude `--permission-mode bypassPermissions` |
| Herdr 名字 | `issue-<n>`（正则 `[a-z][a-z0-9_-]{0,31}` 不许数字开头）；claude / pi 同时 `-n issue-<n>`；cursor / grok 只有 Herdr 一侧有名 |
| `gh` | 电脑上一次性登好，不是派发前提 |
| 角色表 | 消费仓库 `docs/agents/models.md`，每行「角色 → 宿主 → 完整启动命令」。读法：`AGENTS.md` `## Agent skills` 段加「### Roles … See docs/agents/models.md」（与 issue-tracker 同一机制）；`implement` 派 reviewer 那段写「用 models.md 的 reviewer 行起会话」。读者：白天的用户、worker（起 reviewer）、以后的编排会话。F11 关闭。**块 E 定完** |
| `to-tickets` 正文补一句（F5 落地） | 「每条 AC 的 CHECK 从 spec Testing Decisions 的层与先例推出；EXPECT 把先例跑一次抄成功那行」 |

- 块 E 定完。剩块 F：F13（第一张真实的票在哪个仓库、落地顺序）。

## 块 F 定案（2026-08-28，进行中）

| 议题 | 决定 |
| --- | --- |
| `docs/agents/models.md` 的读者 | 不是用户（用户只改它里面的 agent 与模型安排）。读者：`implement`（起 reviewer 会话时抄 reviewer 行）、以后的编排会话 |
| 技能改动怎么验证 | 不用真实的票逐步跑。虚构一张结构完整的票（含 Owns、AC 四行、MANUAL、UI 验收标准、Blocked by），放在一个测试用的小仓库里，每改一步就用它快速测那一步 |
| 改动节奏 | 一次只改一处，测过再改下一处；不一次性改完 |
