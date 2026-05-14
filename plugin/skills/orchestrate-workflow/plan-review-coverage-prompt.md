# Plan Review — Coverage & Quality

Phase 0b 并行组 1：审查计划文档的设计覆盖度、task 质量和可执行性。

## 发送给 workflow-auditor 的 prompt

你审查计划文档的**覆盖度与质量**。另一个 auditor 同时在审查项目规则合规与 grep 验真——你不需要做 grep 验证，专注于计划的结构和可执行性。

**Design doc**（如有）: [DESIGN_FILE_PATH]
**Plan**: [PLAN_FILE_PATH]

每个 finding 必须有：**具体位置**（plan 的哪个 section/task）+ **问题描述** + **为什么这会导致执行出错** + **置信度（0-100，只报 ≥ 80）**。

---

### 1. 设计覆盖度（仅当 design doc 存在时）

逐条核对设计文档的每条意图：

- 每条意图在计划中是否有**至少一个**对应 task？
- 列出遗漏的意图（设计要求了但计划没 task 覆盖）= Critical
- 列出多余的 task（计划做了但设计没要求的）= Important（scope creep）

### 2. Task 质量

逐 task 检查：

- **粒度**：每 task 2-5 分钟执行时间？过大（估计 > 5 分钟）= Important，需拆分
- **TDD 规格**：每 task 是否写清了"测试什么、预期什么结果"？缺少 = Important
- **可执行性**：pack-executor 拿到这个 task 能否直接开始？
  - 描述是否清晰到"知道该改哪个文件"？
  - 是否依赖外部资源但未说明如何获取？
  - 前置条件是否明确？
- **依赖关系**：task 之间依赖是否正确标注？有无循环依赖？= Critical

### 3. Section 分组

- 触碰同一文件的 task 是否在同一 section？
- 有强依赖关系的 task 是否在同一 section？
- Section 大小是否合理？（每 section 2-5 task）
- 独立 section 是否标记为可并行？

---

### 校准

| 级别 | 定义 | 示例 |
|------|------|------|
| **Critical** | pack-executor 会卡住或做错 | 设计意图遗漏、task 描述无法执行、循环依赖 |
| **Important** | 不卡但降低执行效率 | task 过大需拆分、TDD 步骤缺失、依赖未标注、scope creep |
| Minor | 不报 | |

### 假阳性排除

- 纯格式偏好
- 设计文档中标注为"后续迭代"的功能不算遗漏

### 报告格式

```
### 计划文档 — 覆盖度与质量审查

**设计覆盖**：X / Y 条意图有对应 task（如有设计文档）
**遗漏意图**：[列出]
**多余 task**：[列出]

**结论**：可执行 / 需修正（N Critical, M Important）

#### Critical
1. [confidence: 90] 设计意图 #4 "支持批量操作" — 计划中无对应 task。
   **为什么重要**：Phase B 意图验证时必然 GAP。
   **建议**：在 Section 2 补充"实现批量 API 端点"task。

#### Important
1. [confidence: 85] Section 3 Task 7："重构数据层"——估计 > 15 分钟，需拆分。
   **建议**：拆为"提取 repository interface"+ "迁移现有查询"+ "补测试"三个 task。

### 低置信度观察（< 80，仅供参考）
- ...
```

Phase 0 finding 不标注路由——全部返回给编排器（主 session）直接处理。
