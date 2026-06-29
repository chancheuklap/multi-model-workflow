# plan-rigor — 计划期查询清单

> plan 阶段的"查得到就行"细则:测试规划（覆盖追踪 / E2E 决策矩阵 / 质量评级 / 回归铁律）+ Issue 质量标准 + 反模式。编排主流程在 `plan-flow.md`,Task Pack 模板在 `task-pack.md`;写到对应章节翻本文对照(这三份随 dispatch 一起给 plan-writer,读者手里有整套)。

## 测试规划（plan 必须自带完整测试，不留到后续补）

### 追覆盖
- **追每条 codepath**：每个分支（if/else / guard / early return）、每个错误路径（try/catch / fallback）、每条边界（null / 空集 / 非法类型 / 超长）都要有测试。
- **追用户流 + 交互边界 + 错误态 + 空/边界态**：双击重复提交 / 中途离开 / 过期数据 / 慢连接 / 并发；每个错误用户看到明确提示还是静默失败、能否恢复；零结果 / 万条 / 单字符 / 超长。

### 测试类型决策矩阵
- **E2E**：跨 3+ 组件的常见流 / mock 会掩盖真故障的集成点 / auth-payment-数据销毁。
- **EVAL**：LLM 调用 / prompt / 工具定义变更。
- **unit**：纯函数 / 无副作用 helper / 单函数边界。

### 测试质量评级
★★★ 测行为 + 边界 + 错误路径 / ★★ 只测 happy path / ★ 烟雾测试或存在性断言。plan 目标是 ★★★，别只写 ★。
**权威层(authoritative layer)**：每个行为在拥有它的那一层测一次,不为凑数加脆弱的实现细节测试,同一行为禁跨层重复断言——不追求"100% 覆盖"这种数字最大化（用项目自己声明的测试分层,别套陌生词汇）。

### 回归铁律（强制，无需问用户）
覆盖审计发现 diff 改了既有行为、既有测试没覆盖该路径、给既有调用方引入新失败模式 → 回归测试作为 **CRITICAL** 加进 plan，写明什么坏了。拿不准是不是回归就写测试。

### 验证语言对照 + seam
- API/contract → route test / 合同类型 parse；DB/migration → migration / repository test + downgrade；JSON/登记 → validator / unknown-field test；billing/permission → service test / 用户可见 gate test；runtime/browser → focused unit + log evidence；UI/UX → DOM 断言 / screenshot / responsive / manual visual gate。
- seam 锚到设计期定下的 seam，选最高层、别增殖插桩点。

## Issue 质量标准

- **Verified Current State**：改既有行为前先写现状真实行为 + `file:line` + 核实日期。
- **Quantified impact**：数字不用形容词。"几个文件"→"47 文件跨 12 目录"；"提升性能"→"500ms→50ms（10×）"；没数就说"未知，用 X 法测"。
- **Landscape 审计表**（改一族成员之一时，防隧道视野）：

  | 组件 | 有 X | 有 Y | 缺口 |
  | --- | --- | --- | --- |

- **Testable AC**：编号、pass/fail、无主观语言。
  - ✅ "30 天以上订单对全部 4 个角色返回 HTTP 410" / "10K 行查询 <100ms（EXPLAIN ANALYZE）"
  - ❌ "功能正常工作" / "处理好边界"
- **Schema / API 形状**：真实 SQL / 接口 / 请求响应，不写伪代码——精确到让落地者零设计决策。

## 反模式（命中即修）

模糊验收（"正常工作"）/ 模糊文件引用（"auth 模块某处"）/ effort 无按组件拆 / 非平凡 scope 缺 Out of scope / 改动无 Verified current state / 一个 pack 混了流程反馈和战术修复 / 20+ 项无分级和执行顺序 / 引用未定义未验真的 type/fixture / 写 "similar to Task N" 不重复写出来 / **plan mandate 了评审会判为缺陷的东西（断言为空的测试、整段逻辑逐字复制粘贴）**。
