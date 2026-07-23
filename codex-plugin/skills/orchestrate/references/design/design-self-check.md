# Design · selfcheck 步(本步读这一份)

design 阶段成文后:保存前自己逐条过,过了起设计预审、再请用户过门(流程在文末「收尾」)。

## 自检（保存前逐条过）

- [ ] 文档读起来是「现状 + 决策 + 行为」的记录，不是维度填空；没有为不存在的面硬凑的内容；每个保留元素有理由（YAGNI）
- [ ] 无 TODO / TBD / placeholder / 口头承诺；每个设计点有具体可落地方案；不和领域文档 / 项目规则 / ADR / 代码冲突
- [ ] 每条目标结果和用户场景可转成验收或测试（可观察、可度量）；验收清单与失败路径对得上号；没混入实现 plan / Task Pack
- [ ] 现状与调研结论逐条带引用（file:line / url）；重建有为什么不复用；外部方案的采用与放弃都有理由
- [ ] 方案设计每个决策有为什么（取舍）、落点精确（file:line / 函数名，无「某个模块」「相应调整」悬空话）；新增 / 改变的对象、状态、角色有 owner / writer / reader / verifier 且已同步进领域文档；新代码路径的日志 / 审计 / 告警已列为交付物
- [ ] 失败路径自问（答不上就是决策缺口）：每个真实失败面——触发条件？谁捕获？用户看到什么？对应哪条验收？零静默失败，禁 catch-all；缺口补进方案设计或 Open Decisions
- [ ] 非平凡数据流 / 状态机 / 管线有 ASCII 图
- [ ] **按输入类型**：Bug→current/desired/复现/regression；Issue→source/验收/依赖/AFK-HITL；UI→每个 mockup 拆成可验收行为、交互状态表填全
- [ ] `mmw where` 显示 `prototype_status=accepted`；只把 `prototype_selected` 回灌为状态、交互、视觉契约和验收，未选候选没有进入设计合同
- [ ] 触碰合同 / 发布风险时对应节已填、anchors 占位在；各 section 无矛盾、无歧义需求

触碰不变量 / 合同 / 数据权威 / 权限 / 计费 / 发布风险时,尤其确保上面每条都过。此类高风险设计定稿前:已调 advisor 工具咨询过,或在 Open Decisions / 讨论中写明跳过理由(不强制每次 consult)。

## 收尾:handoff 交还引擎(`mmw where` 的 `then` 已给好钉产物的命令模板,照抄即可)

- 自检全过 → 先钉产出:`mmw pin --phase design --produced docs/design/<slug>/<slug>.md`(布局门:主文档必须与文件夹同名;承重合同文档同在文件夹内可加 `--produced`);再**起设计预审**(不是闸,是给用户和你的参考):`mmw review start --stage design --source docs/design/<slug>/<slug>.md`,脚本自动把 accepted prototype README + selected 加进同一 Source；照 brief 派审者,findings 落盘亲验标处置。
- 预审收回后,把「设计文档定稿 + 预审发现与你的处置」一并摆给用户,请他审阅;**用户满意 → 由用户敲 `$multi-model-workflow:approve-design` 过门**(唯一人闸;引擎盖指纹、切 afk、推进 to-issue)。你不能代跑,也不能拿口头同意当过门。
- 用户要改 → 回讨论/成文改,改完重走自检;缺关键输入没法定稿 → `mmw handoff --conclusion needs-context`;方向本身存疑(解错问题/该换框架)→ `mmw handoff --conclusion needs-redirection` 回 propose。
- 预审的 Critical 发现:修掉或有理有据 reject 并在留痕里写明,再请用户过门——别把开口 Critical 埋着送审批。
