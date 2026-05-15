# Final Review Contract

Phase B 是最终意图验证，不是再做一次普通 pack review。目标是确认所有 pack 合起来真的满足 design intent，并且没有 release blocker。

## Final Intent Review

派 `code_reviewer`。

输入：

- design doc；
- plan；
- starting commit；
- current diff；
- pack completion summary；
- validation commands。

步骤：

1. 从 design doc 提取每条可验证 intent。
2. 为每条 intent 写出验证方法：pytest、curl、CLI、UI、browser、VM、smoke、manual checklist。
3. 实际运行能运行的验证；不能运行时说明环境缺口。
4. 对每条 intent 判定：pass / implementation gap / design gap / unverifiable.
5. 跑 changed-files 相关回归检查。
6. 做跨 pack 代码交叉审查。

Implementation Gap：

- 设计合理，代码没做到；
- 需要 acceptance test 或复现检查；
- 路由到 worker。

Design Gap：

- 设计承诺不可实现；
- 设计遗漏项目约束；
- 设计假设与当前系统不成立；
- 路由到用户决策或文档修正。

## Independent Second Opinion

派另一个 `code_reviewer`，不要给它第一次 final review 的结论。

检查：

- correctness；
- regression；
- security；
- integration；
- design alignment；
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
- production dependency / manual gate。

Release blocker：

- 数据丢失或无法回滚；
- 权限绕过或授权状态漂移；
- 账务 hold / settle / release / auto_release 不一致；
- producer / consumer 合同字段未同步；
- 部署顺序会让现役客户端或服务 401 / 500；
- release gate 或 manual production dependency 没有验证证据。

## 输出格式

```text
### Final Intent Review
通过: X / Y
Implementation Gaps:
Design Gaps:
Unverifiable:

### Regression / Cross-Pack Review
Critical:
Important:

### Release Risk
Blockers:
Manual verification:
Rollback concerns:

### Verdict
可以完成 / 阻塞
```

不要用 worker self-report 作为通过证据。
