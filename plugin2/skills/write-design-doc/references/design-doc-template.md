# 设计文档模板（写文档阶段读全文，按它写入）

**按本模板写入设计文档：用项目正式术语 / 不写只在聊天里能懂的句子 / 不用 TODO/TBD / 不写实现 plan 或 Task Pack。**

```markdown
# <功能 / 问题> 设计文档

## 背景和问题
用户视角的当前问题、触发场景、为什么需要解决、为什么现在做（blocking / 花钱 / 正确性 / 合规）。

## 目标结果
完成后用户或系统能稳定做到什么。每条可观察、可度量，不是 vibes。

## 用户场景
actor / action / benefit。覆盖 happy path、失败、空状态、权限不足、重复提交、并发、回滚。
**穷举式编号**：`<编号>. 作为 <actor>，我要 <feature>，以便 <benefit>`，每个 actor 的每个意图各一条，宁多勿漏——这是按 actor × 意图横向铺，和下面按失败维度纵向铺互补，两个都要。
**交互边界 case**：双击、操作中途离开、慢连接、状态过期、浏览器后退、首次用户 vs 老手。

## 方案设计
产品行为、系统行为、数据流、UI 状态、接口形状、错误处理。

### 架构与边界
组件边界与职责；依赖图与耦合点；数据流与瓶颈；扩展性与单点故障（SPOF）；安全架构（鉴权 / 数据访问 / API 边界）。
**非平凡的数据流 / 状态机 / 处理管线 / 依赖图 / 决策树用 ASCII 图画出来**（图比散文准，防漏分支）——本文档凡涉及这些流程一律配图。

### 数据流与失败路径（工程处理 + 用户可感知表现）
- **影子路径**：每条数据流除 happy path 外画出三条——空输入 / 零长度或空集 / 上游报错；四条都交代。
- **每个错误有名字**：异常类型 / 触发条件 / 谁捕获 / 用户看到什么 / 是否有测试。禁 catch-all（`except Exception` / `catch (e)` 一把抓）。
- **失败模式三连判**：每条新代码路径列一个真实生产故障（超时 / nil / 竞态 / 脏数据），答 (1) 有测试吗 (2) 有错误处理吗 (3) 用户看到明确错误还是静默失败。三个都缺 = critical gap，零静默失败。
- **用户可感知表现**：每个失败用户那一侧看到什么、有什么兜底。
- **可观测性是范围不是事后**：新代码路径要带的日志 / 指标 / 告警 / runbook 在此列为交付物。

### 已有什么（复用 vs 重建）
现有代码 / 流程里已部分解决本设计子问题的部分，以及本设计复用它还是重建——重建必须说明为什么不复用。

### 业务对象、角色和状态
对象、owner / writer / reader / verifier、状态、生命周期和关键关系。

### 实现决策
讨论中做出的实现决策。**不写会过时的实现细节路径 / code snippet**（prototype snippet 例外——仅 state machine / reducer / schema / type shape）；点名稳定模块 / 接口面用于复用图与合同锚点是允许的。

## 合同边界
涉及 API / 跨边界数据合同 / DB / JSON / sync / task payload / UI action / billing / permission / runtime 时填：
boundary type / owner / provider / consumer / 合同类型 / schema 版本 / 登记 / 迁移 / verification（agentflow 落点: Pydantic model · schema_version · registry · migration · catalog · repository · read model）。

## 发布风险和人工门禁
涉及 migration / billing / permission / runtime / cross-service / deploy order / rollback / manual gate 时填；新交付物（CLI / 包 / 镜像 / 独立应用）补"用户怎么拿到它"（发布渠道 + CI）。部署不是原子的——为部分状态、回滚、feature flag 留计划。

## 测试和验收
**测试 seam（在哪测）**：选能覆盖目标行为的**最高层** seam，别增殖插桩点（每个行为在其权威层测一次）；需要新 seam 时提在最高点并先与用户确认。
哪些行为要测 / 哪些模块 / 类似测试先例 / manual gate / visual verification / regression check。

## UI / UX 状态
mockup 目录: docs/mockups/<slug>/
**Mockup 是可视化设计文档，与文字设计文档地位平等。** 每个 mockup 拆成可验收的行为描述，不能只写"见 mockup 目录"：

| 页面 / 组件 | Mockup 文件 | Viewport | 视觉规格 | 交互行为 | 状态变体 | 验证方式 |
| --- | --- | --- | --- | --- | --- | --- |

**交互状态全覆盖**（每个 UI 功能一行，写用户**看到**什么不是后端行为）：

| 功能 | 加载 | 空 | 错误 | 成功 | 部分 |
| --- | --- | --- | --- | --- | --- |

设计细则（空状态 = 功能 / 信息层级 / 情绪弧 / 可用性三定律 / 用户行为事实 / AI Slop 黑名单 / 通用硬规则 / 响应式 + a11y）见 `design-rigor.md`，逐条对照填，**AI Slop 黑名单命中 = 重做**。

## 不在本次范围
被考虑过但显式推迟的工作，每条一句话说明为什么。

## Open Decisions
含 6 个月后视角：这个设计解了今天的问题，会不会造成下季度的噩梦？会就写明。

## Review History
| Round | Verdict | Reviewer | 重点建议 | 已知 gotcha | 日期 |
| --- | --- | --- | --- | --- | --- |
（可选，每轮 review 通过后追加一行；写 plan 时读它避免重复犯错）

## Cross-Plan Contract Anchors
<!-- 设计阶段不填本表：表里的 Owner / Provider / Consumer 都是 plan 名，plan 还不存在，设计期无从填起。 -->
<!-- 设计阶段只留本标题 + 这两行注释作占位锚点；由 write-plan-doc 在所有 plan 写完后回填（plan skill 的「跨计划合同锚点」步骤是单一源）。 -->
<!-- 这不算 TODO/TBD —— 是跨阶段交接的占位，回填责任明确在 plan 阶段。 -->
```
