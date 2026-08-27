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
