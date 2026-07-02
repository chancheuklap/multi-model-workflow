# stage=merge-impl · 跨 PR 集成审角度(配 method.md 读)

不是单 plan 落地审、不是 final 意图审 —— 这是**多个并行 PR 合在一起后,系统是否正确**。各 PR 各自已过自己的 final 终审,但它们的**交互**没验过。

**Source** = merge-brief(PR 表 / 合同地图 / 冲突解决记录 / 大设计文档路径)。自跑 `git diff <base>..HEAD` 看合并后全貌。

## 七个审查角度(逐条出结论)

1. **组合行为正确**:全部 PR 合在一起,产出大设计描述的正确行为?各自对 ≠ 组合对,盯交互/顺序/依赖。
2. **合同一致**:跨 PR 的 model / API / DB schema / JSON / registry 一致?一个 PR 提供的合同被另一个正确消费?
3. **迁移完整**:多 PR 的 migration 合并后顺序对?有没有漏(A 改 model、B 没配套 migration)?回滚安全?
4. **状态一致**:跨 PR 对同一 shared state / cache / global config 的假设一致?并发访问安全?
5. **import / 依赖**:合并后有没有循环 import?依赖版本一致?
6. **回归**:合完既有功能完好?跑完整测试套件报结果。
7. **冲突修复质量**(若之前解过冲突):修复正确、完整?有没有引入新问题?

## Calibration

**不信各 PR 的 final 终审结论 —— 独立验组合行为。** 审基于合并后代码事实,不基于各 PR 独立审的结论。只标会导致实际问题的 finding,每条带 evidence。单 PR 内部代码质量已在各自 final 终审覆盖,不重复;措辞/命名/风格不是 finding。

## Result 字段(除 method.md 的 Finding/Verdict 外,逐角度给一行)

组合行为 / 合同一致 / 迁移完整 / 状态一致 / import依赖 / 回归 / 冲突修复质量 —— 各一行结论 + 证据。
