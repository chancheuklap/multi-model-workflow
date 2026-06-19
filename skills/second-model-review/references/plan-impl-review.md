# ③ 每个计划落地 review

一份 plan 全部 Pack 提交后,审这个 plan 的 diff。

**Source**:源意图(plan 文档 + 各 Pack acceptance / Interfaces)· 待审产物(本 plan diff / 分支范围)

## 轴 A spec + 风险收口
- 逐 Pack 对账:每个 Pack 的 acceptance / Produces 达成,对照 plan 报 Missing / Extra / Misunderstood。
- 合同 & 风险:跨边界合同 bump schema 版本 + 同步全部 consumer;DB 字段配套迁移 + repository + read model;项目不变量在落地处真正收口(agentflow: 计费四态 hold→settle/release 禁估算金额、LINEAGE 穿透 handoff / 日志)。
- 落在未改代码 / 跨 Pack 无法从 diff 验 → 标 `⚠️ Cannot verify from diff`,不扩大搜索。

## 轴 B 代码质量 + 跨 Pack 一致
- 代码质量:职责分离;错误处理无 catch-all 吞错;DRY 不过早抽象;边界 case;测试测行为不测 mock,输出 pristine(warning = finding)。
- 跨 Pack 一致:Pack 间接口对得上;无两个 Pack 各写一份同逻辑;共享合同类型 / schema 版本一致(agentflow: Pydantic model);迁移顺序对;跨 Pack import 无环;共享 state 并发安全(无共享面 → 一行"已确认独立")。
- 撑大文件:本改动新建已过大 / 显著撑大既有文件(只看本改动贡献的)。
- 禁用捷径:见 `quartet.md` 附录。
- 回归:破坏既有功能没;必要时跑相关套件(不强制全套)。
- 只为具名风险(锁序 / 合同 / 共享可变状态)查 diff 外调用点,不漫游。

每条 finding 标 `[Pack N.M]`,结尾列 Affected packs。不信任 worker 报告,独立验证。
