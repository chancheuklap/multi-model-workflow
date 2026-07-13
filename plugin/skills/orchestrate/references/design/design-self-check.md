# Design · selfcheck 步(本步读这一份)

design 阶段末步:保存前自己过这道闸,过了就 `mmw handoff` 交还引擎(引擎触发 ①设计审,本阶段不自派审、不自己跳阶段)。

## 自检（保存前逐条过）

- [ ] 文档读起来是「现状 + 决策 + 行为」的记录，不是维度填空；没有为不存在的面硬凑的内容；每个保留元素有理由（YAGNI）
- [ ] 无 TODO / TBD / placeholder / 口头承诺；每个设计点有具体可落地方案；不和领域文档 / 项目规则 / ADR / 代码冲突
- [ ] 每条目标结果和用户场景可转成验收或测试（可观察、可度量）；验收清单与失败路径对得上号；没混入实现 plan / Task Pack
- [ ] 现状与调研结论逐条带引用（file:line / url）；重建有为什么不复用；外部方案的采用与放弃都有理由
- [ ] 方案设计每个决策有为什么（取舍）、落点精确（file:line / 函数名，无「某个模块」「相应调整」悬空话）；新增 / 改变的对象、状态、角色有 owner / writer / reader / verifier 且已同步进领域文档；新代码路径的日志 / 审计 / 告警已列为交付物
- [ ] 失败路径自问（答不上就是决策缺口）：每个真实失败面——触发条件？谁捕获？用户看到什么？对应哪条验收？零静默失败，禁 catch-all；缺口补进方案设计或 Open Decisions
- [ ] 非平凡数据流 / 状态机 / 管线有 ASCII 图
- [ ] **按输入类型**：Bug→current/desired/复现/regression；Issue→source/验收/依赖/AFK-HITL；UI→每个 mockup 拆成可验收行为、交互状态表填全
- [ ] 触碰合同 / 发布风险时对应节已填、anchors 占位在；各 section 无矛盾、无歧义需求

触碰不变量 / 合同 / 数据权威 / 权限 / 计费 / 发布风险时,尤其确保上面每条都过。

## 收尾:handoff 交还引擎(`mmw where` 的 `then` 已给好钉产物的命令模板,照抄即可)

- 设计 OK → `mmw handoff --conclusion pass --produced docs/design/<slug>.md` → 引擎触发 ①设计审(独立 Codex 审,只审设计文档),审过进 `to-issue` 阶段切片。
- 缺关键输入没法定稿 → `--conclusion needs-context`。
- 方向本身存疑(解错问题 / 该换框架)→ `--conclusion needs-redirection`。
- ①设计审打回 design gap → 引擎回 design(`needs-repair`),停在本阶段改、改完 handoff 重审。**Critical 必须修掉才能进 to-issue / plan。**
