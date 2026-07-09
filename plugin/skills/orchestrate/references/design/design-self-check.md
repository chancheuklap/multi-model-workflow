# Design · selfcheck 步(本步读这一份)

design 阶段末步:保存前自己过这道闸,过了就 `mmw handoff` 交还引擎(引擎触发 ①设计审,本阶段不自派审、不自己跳阶段)。

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

触碰不变量 / 合同 / 数据权威 / 权限 / 计费 / 发布风险时,尤其确保上面每条都过。此类高风险确认设计前:已 `Task`→`fable-advisor` 咨询过,或在 Open Decisions / 讨论中写明跳过理由(不强制每次 consult)。

## 收尾:handoff 交还引擎(`mmw where` 的 `then` 已给好钉产物的命令模板,照抄即可)

- 设计 OK → `mmw handoff --conclusion pass --produced docs/design/<slug>.md` → 引擎触发 ①设计审(独立 Codex 审,只审设计文档),审过进 `to-issue` 阶段切片。
- 缺关键输入没法定稿 → `--conclusion needs-context`。
- 方向本身存疑(解错问题 / 该换框架)→ `--conclusion needs-redirection`。
- ①设计审打回 design gap → 引擎回 design(`needs-repair`),停在本阶段改、改完 handoff 重审。**Critical 必须修掉才能进 to-issue / plan。**
