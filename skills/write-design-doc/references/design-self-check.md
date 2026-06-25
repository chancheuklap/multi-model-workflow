# 设计自检（保存前 / 用户确认后读全文）

作者保存前自己过的闸。外部独立审（派第二个模型）见末节 §重大 / 碰红线。

## 自检（保存前逐条过）

- [ ] 不存在口头承诺，每一个设计都有具体的可落地方案
- [ ] 无 TODO / TBD / placeholder；不和领域文档 / 项目规则 / ADR / 代码冲突
- [ ] 每个目标行为可转成验收或测试（可观察、可度量）；对象 / 状态 / 合同有 owner / writer / reader / verifier
- [ ] 没混入实现 plan / Task Pack；每个保留元素有理由（YAGNI）
- [ ] 每条数据流有 happy + 三条影子路径；每个错误有名字、无 catch-all
- [ ] 每条新代码路径过失败三连判、无 critical gap；可观测性作为交付物列出
- [ ] 非平凡数据流 / 状态机 / 管线有 ASCII 图；"已有什么（复用 vs 重建）"已写且重建有理由
- [ ] **按输入类型**：Bug→current/desired/复现/regression；Issue→source/验收/依赖/AFK-HITL；Feedback→目标态/角色/文案/交互/验证；UI→每个 mockup 拆成视觉规格表
- [ ] **UI（有界面时）**：交互状态表填全；空状态有主操作；信息层级明确；响应式 + a11y；AI Slop 黑名单命中 = 0
- [ ] 各 section 无矛盾、架构与功能一致、无歧义需求；触碰合同 / 发布风险时有 anchors 和风险面

## 重大 / 碰红线 → 交外部审

判断重大或触碰不变量(agentflow 例:计费 / 合同墙 / 数据权威 / LINEAGE)时,自检过后把文档交 `second-model-review` 阶段①独立审。**Critical 必须修掉才能进 plan。**
