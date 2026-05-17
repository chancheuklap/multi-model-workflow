# Final Review 合同

Phase B 验证所有 pack 合并后是否满足 design intent，并确认没有 release blocker。

每个 final gap 最多 2 轮修复。Phase B dispatch 总量上限 15；超过上限时先做方向检查，确认是继续 repair、回 design / plan，还是请求用户决策。

## Final Intent Review

派 `code_reviewer`。

输入：

- Read first：design doc、plan、相关 UI / UX mockup、根 `AGENTS.md`、相关 `PROJECT.md` / `ENGINEERING-RULES.md` / SPEC / ADR / GUIDE、changed files 涉及目录的 `AGENTS.override.md` / `agents.overrides.md`；
- Project baseline：最终验收必须满足的设计意图、项目不变量、数据权威、模块边界、contract wall、测试路由和发布 / 回滚约束；
- Contract baseline：最终 diff 涉及的 API、Pydantic、DB、JSON、task、sync、catalog、capability、helper 边界，以及 producer / consumer / verifier；
- Mockup baseline：最终页面必须满足的 mockup path、目标 viewport、关键 states、interaction、信息架构和允许偏差；
- design doc；
- plan；
- starting commit；
- current diff；
- pack completion summary；
- validation commands。

步骤：

1. 从 design doc 和 mockup 提取每条可验证 intent。
2. 为每条 intent 写出验证方法：pytest、curl、CLI、UI、browser、screenshot、DOM scan、VM、manual checklist。
3. 实际运行能运行的验证；不能运行时说明环境缺口。
4. 对每条 intent 判定：pass / implementation gap / design gap / unverifiable.
5. 跑 changed-files 相关回归检查。
6. 涉及合同边界时，逐项确认 Pydantic model、schema_version、registry、migration、repository、read model、catalog、producer / consumer 和 release gate。
7. 做跨 pack 代码交叉审查。
8. UI / UX 任务必须对照 mockup 检查最终页面，不接受只读代码推断。
9. 如果最终验收反馈暴露 desired behavior、domain term、UI role、target state、copy、interaction 或 verification method 不清，route 给 `orchestrate-discovery`，不要把它归为普通 implementation gap。

Implementation Gap：

- 设计合理，代码没做到；
- mockup 要求的关键页面状态、交互、视觉层级或响应式行为没有做到；
- 需要 acceptance test 或复现检查；
- 路由到 worker。

Design Gap：

- 设计承诺不可实现；
- 设计遗漏项目约束；
- 设计假设与当前系统不成立；
- 路由到用户决策或文档修正。

Context Gap：

- 用户 / reviewer 的最终反馈需要业务术语、对象 owner、UI target state、验收口径或项目文档确认；
- route 给 `orchestrate-discovery`；
- Discovery 结束后，把 clarified context 写回 design / plan / issue brief，再重新判断是 implementation gap、design repair、prototype question 还是 user decision。

## Independent Second Opinion

派另一个 `code_reviewer`，不要给它第一次 final review 的结论。

Prompt 必须包含同一组 Read first 和 Project baseline，但不要包含第一次 final review 的 finding。

检查：

- correctness；
- regression；
- security；
- integration；
- design alignment；
- contract boundary alignment；
- mockup alignment；
- empty-state / error path / retry / rollback / race / stale import。

所有 finding 必须基于代码读取或测试输出。推断必须明确标注。

## Release Risk Review

以下情况必须派 `release_reviewer`：

- database migration；
- billing / wallet / settlement；
- permissions / auth / tenant isolation；
- runtime / scheduler / browser takeover；
- deploy order / rollback；
- cross-service contract；
- API / Pydantic / DB / JSON / sync / task payload compatibility；
- production dependency / manual gate。

`release_reviewer` 只审 release-risk。它不能替代 Final Intent Review，也不能替代 independent diff review。Phase B 通过必须同时满足 baseline `code_reviewer` review 和必要的 `release_reviewer` gate。

Prompt 必须包含 Read first 和 Project baseline，并额外写清 migration / deploy / rollback / manual gate / online verification 事实。

Release blocker：

- 数据丢失或无法回滚；
- 权限绕过或授权状态漂移；
- 账务 hold / settle / release / auto_release 不一致；
- producer / consumer 合同字段未同步；
- Pydantic contract、JSON registry、DB migration、repository / read model 或 catalog 没有闭合；
- 部署顺序会让现役客户端或服务 401 / 500；
- release gate 或 manual production dependency 没有验证证据。

## Architecture After-Effects

Final review 可以记录架构后效应，但不能随意把架构摩擦升级成 blocker。

如果 final review 需要判断 module、interface、seam、adapter、depth、locality、deletion test 或 dependency category，使用 upstream `improve-codebase-architecture` 作为方法来源。Orchestrate 只定义 blocker threshold：architecture after-effect 只有造成 production risk、data risk、permission risk、billing risk、rollback failure 或当前验收不成立时，才成为 blocker；否则通过 upstream `triage` / `to-issues` 记录为 bounded issue candidate。

## Result Payload

```text
Final Intent Review:
通过: X / Y
Implementation Gaps:
Design Gaps:
Context Gaps:
Unverifiable:

Regression / Cross-Pack Review:
Critical:
Important:

Release Risk:
Blockers:
Manual verification:
Rollback concerns:

Phase Summary:
可以完成 / 阻塞
```

不要用 worker self-report 作为通过证据。

Coordinator 派发必须包含标准顶层 return headings。本 payload 放在 `### Result` 下。顶层 `### Verdict` 只使用 `pass / blocked / needs repair / needs context`；“可以完成 / 阻塞”只作为 phase summary。每条 finding 必须使用统一 shape：severity、confidence、locator、evidence、impact、remediation、routing。Final review result 必须能被主线程执行 Review Reception Gate。
