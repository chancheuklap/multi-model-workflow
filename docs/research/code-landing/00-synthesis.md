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

定案不在本文登记。第一、二、三轮调查之后的全部定案、今天六块讨论的全部定案，以及每一条的背景、选项、用户原话与落点，只登记在 `12-decisions.md`。

## 第二轮调查结果（2026-08-28）

五份报告各对应一个机制。下表是每份的结论、搬过来要动的地方、代价与不适用之处；细节看各文件。

| 机制 | 文件 | 结论 | 要动的地方 | 代价 / 不适用 |
| --- | --- | --- | --- | --- |
| 写路径边界 `Owns:` | `04-owns-write-boundary.md` | 加。unlazy 的 `OWNS:` 脱离脚本后剩三件事：出票时逼出票人想清楚动哪些目录、开工时给 worker 边界、收尾时一条 `git diff --name-only <base>..HEAD -- . ':(glob,exclude)<glob>'` 算出路径外改动（§3，本机 git 2.55 验证） | 票模板 `## Seam` 后加 `## Owns`（目录级 glob，一行一条，禁裸 `**`）；`to-tickets` 第 2 步不再可省、第 6 步回读加核对、L135 禁令改措辞；`implement` L8 开工核对加一项（§7） | 不引入 claim/lease 脚本；并发重叠在出票时人眼比对、加 Blocked by 边解决（§5） |
| 可运行验收门 `CHECK:`/`EXPECT:`/`EVIDENCE:` | `05-runnable-acceptance-gates.md` | 加。`to-tickets` 四条规则已做到"标题可判"，缺命令那一半和三条作者规则（success-only marker、负控制、不把数字抄成 EXPECT）（§4） | `to-spec` Testing Decisions 每层加"单文件调用形 + 成功输出样子"；`to-tickets` 出票时推导每条，推不出回 `/to-spec`，允许显式 `MANUAL:` 行且不过半（§5、§8）；`implement` 收尾只有 exit 0 且匹配才打勾（§8.3）；EVIDENCE 手写一行格式（§7） | UI 标准要一个通用工具 `visual-parity.py`（PEP 723 + `uv run`，依赖 numpy/Pillow/playwright-python + chromium），从 `issue-534/EXP/run.py` 提炼：参数化、场景文件、阈值与退出码、尺寸不等即失败；差异非零时人的接受写入 `accepted-diffs.json` 而不是直接打勾，gate 仍可重跑（§6） |
| 独立 verifier | `06-independent-verifier.md` | 加，但只对四类票派：有 `MANUAL:` 条目或 `Seam` 指向界面、无人看守、`Owns` 触及迁移/鉴权/对外接口/共用路径、`CHECK:` 要起 app/DB（§5.2）；其余 worker 自己重跑，裁决标 `self-reported` | 收尾三步改五步：code-review（≤2 轮）→ 最终 SHA 重验 → 评论 `VERDICT <sha> <level> by <model|self-reported>` + 逐条 EVIDENCE → push/PR → 关票或 HANDOFF（§8.1）；新增第四个 subagent `mmw-v2/agents/verifier/`，brief 只给验收标准原文、SHA、Seam、FORBIDDEN、REPORT，不给 diff/spec/prototype（§8.2-8.3） | "不同模型家族"在 pstack 只是断言无数据；Claude Code 只能选 Anthropic 内模型，Grok/Codex 能否按定义文件切模型未确定（§3）。技能正文只能写"能选模型时选一个和自己不同的"；不能派子代理时降级为自己从干净 shell 重跑（§6） |
| 过度构建纪律（ponytail） | `07-overbuild-discipline.md` | 有条件加。只有 PT1"grep every caller"有 Sonnet/Opus 级 A/B 证据；rung 4"用原生元素"只有 Haiku LOC 证据且**会推向换掉 mockup 契约**，必须绑定契约（§4.3、PT2）；安全例外与"无 unrequested abstraction"需加 Seam 例外（§5.2）；"Ship the lazy version and question it"、`demo()` 自检、Persistence/Intensity 不采（§5.3、§6、PT8-PT11） | `implement` L12 之后、L14 `Use /tdd` 之前插入 ≤10 行操作性指令（PT1-PT7，§7.1-7.2）；收尾评论加 `skipped: [X], add when [Y]` 行（PT5） | 无 hook、无插件（ADR 0003），规则不常驻，压缩后是否还在未实测；采纳前必须按 §8 四个探针（P1 shared-caller、P2/P2′ native-vs-drawn、P3 over-contract、P4 trust-boundary）两臂实测，无差异的句子不入正文 |
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

## 第三轮调查结果（2026-08-28）

| 项 | 文件 | 结论 |
| --- | --- | --- |
| UI 验收实验 | `prototypes/code-landing/ui-gate/EXP/README.md` | **可行。** 下载回来的 Claude Design 页离线可渲染（本地化 `support.js` 从 unpkg 取的 React/ReactDOM/Babel 三个脚本）；ARIA 树经三条归一化（去 generic/group、去 landmark 名、提升嵌套 `main`）后与 React 实现 diff 为 0；像素差 0.027%/0.044%（只是字形抗锯齿）；负控制（错误场景）23–29% 像素、28 行树差，被抓住。默认阈值定 1%。未覆盖：非默认场景要靠 props 而非 URL 切换 |
| Herdr 派发模型 | `09-herdr-dispatch-model.md` | Herdr 只负责起会话、发 prompt、看生命周期；**没有完成信号**，"做完"= 票状态（关票或 `HANDOFF REQUIRED` 评论）+ agent idle。派发词最小形态"技能名 + 票号"，前提是 cwd 在票的 worktree、`gh` 已登录、权限参数随 `agent start -- <args>`。子代理对 Herdr 不可见。**冲突**：定案"verifier 是编排会话的子代理"在白天手工场景没有对象、在夜间场景要求 worker 停下等握手；verifier 作为运行 `implement` 的那个会话的子代理则两个场景同一份流程（§5.3–§6） |
| 上次尝试尸检 | `10-previous-attempt-postmortem.md` | 19 小时、34 个提交、77 文件 5345 行、无一张真实代码票即合 main；hook 事件注给了不该拿工人纪律的那组；纪律两处存放；关卡镜像文件重新引入漂移；抄参考漏了消费端、三态压两态、逐字校验全绿但无效；技能写成带出处的中文说明书。§5 十条"不能再犯"；§6 标出本轮可能漏项：交接前自审、每票派给哪个宿主/模型、新词集中定义 |

