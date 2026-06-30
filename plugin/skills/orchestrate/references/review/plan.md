# ② 计划文档 review

**Source**:源意图(source design + issue 层级)· 待审产物(plan 文档,含 Plan Header / Global Constraints / Dependency Graph / Task Pack)

## 轴 A 覆盖与质量
- Issue 质量:每个 small issue 是垂直切片(独立验收),不横切;zero-context 可读;粒度合理(单 issue ≤ ~8 步);AFK / HITL 标记对。
- 覆盖:plan 覆盖 design + issue 全部行为,每个 issue 有对应 Pack,无遗漏可感知行为。
- Task Pack 质量:大小合适;`Interfaces(Consumes/Produces)` 清晰;`Do Not Touch` / `Root cause`(修 bug)有;改既有行为有 `Verified current state` + Rollback。
- 无 Placeholder:无 "TODO 后补""此处略"。
- Critical:intent 无覆盖 / source intent 不清却直接落地 / Pack 不可执行 / 缺 Task Pack inventory / small issue 漏大 issue 行为 / small issue 不可独立验证。

## 轴 B 合规与交叉验证
- 交叉验证:plan 引用的每个 fixture / helper / function / 行号 / 表名 / API 用 grep / Read 验真存在(引不出 = finding);同文件多 Pack 的 merge 冲突风险;隐式顺序依赖有没有标注。
- 合规:跨边界合同变更同步全部 consumer + bump schema 版本 / 数据权威 / 项目不变量;新增可被外部引用之物入登记(端口 / 命令 / 收费动作 / capability 入项目的 registry·catalog);新 DB 字段有迁移;helper 放对边界;新文件标 Create;项目的约束覆盖文件(如 AGENTS.override)同步。
- 依赖:Dependency Graph 无环;Global Constraints 齐;Pack 顺序成立;跨 plan 合同图无 producer / consumer 缺失 / ownership 冲突。
- 验证规划:每条行为有 E2E / 合同 / 单元落点;修 bug 的 Pack 有挡同坑回归测试。
- Critical:依赖错误 / 循环依赖 / Task 逻辑矛盾 / 引用不存在路径 / 违反项目规则 / 允许弱类型裸结构当跨边界合同(如裸 dict 当合同)/ 高风险缺迁移回滚。
- finding 归类:每条标明是 plan 自身 / design-plan mismatch / source design gap / issue-plan mismatch / context ambiguity / architecture friction。
