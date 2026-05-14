# Final Intent Review — Phase B prompt template

Phase B：仅当 design doc 存在时。调度 workflow-auditor 端到端验证功能是否符合设计意图。所有 pack 的 spec + quality review 已通过——现在验证的是"整体加起来是否做到了设计承诺的用户体验"。

## 发送给 workflow-auditor 的 prompt

你的任务：**实际运行功能**，验证它做到了 design doc 承诺的用户体验。不是读代码推断"应该能工作"——是真的跑起来看结果。

**Design doc**: [DESIGN_FILE_PATH]
**Plan**: [PLAN_FILE_PATH]
**起始 commit**: [STARTING_COMMIT_SHA]

---

### 步骤 1：意图提取

从 design doc 提取每条可验证意图。逐条列出：

| # | 意图 | 可验证？ | 验证方法 |
|---|------|---------|---------|
| 1 | "用户应该能 X" | 是 | 命令 / API 调用 / 测试 |
| 2 | "系统应该在 Y 时 Z" | 是 | 触发 Y，检查 Z |
| 3 | "体验应该流畅" | 否（模糊）| 标记为 Suggestion |

模糊意图（无量化标准、无法写验证命令）标记为 **Suggestion**，不计入通过/不通过。

### 步骤 2：端到端验证

**逐条意图执行验证**。对每条可验证意图：

1. **写出验证命令**（Bash / curl / pytest / 实际 UI 操作描述）
2. **执行命令**，捕获完整输出
3. **对比预期**：输出是否符合意图描述？
4. **判定**：通过 / GAP

**证据要求**：每个判定必须附带实际命令和输出片段。不接受"看起来正常"、"应该可以"。

```
意图 #1："用户能通过 API 创建订单"
验证：curl -X POST http://localhost:8797/api/v1/orders -d '{"product_id": 1}'
输出：{"order_id": 42, "status": "created"}
判定：✅ 通过
```

### 步骤 3：GAP 分类

每个 GAP 判断类型：

#### Implementation Gap（代码没做到，但设计合理）

- 代码层面可修复
- 描述 acceptance test：**输入是什么 → 执行什么操作 → 预期什么输出**
- 标注 `needs pack-executor`

#### Design Gap（设计本身有缺陷）

- 设计承诺了不可实现的东西
- 设计遗漏了关键约束（如项目工程规则限制）
- 设计的假设在实际代码中不成立
- 标注 `needs user decision` 并具体说明"设计的哪一条需要修正、为什么"

### 步骤 4：回归检查

验证新功能没有破坏已有功能：

1. `git diff [STARTING_COMMIT_SHA]..HEAD --stat` — 查看所有变更文件
2. 对变更文件涉及的**已有功能**跑相关测试
3. 有无已有测试因本次改动而失败？

回归问题 = **Critical**，标注 `needs pack-executor`。

### 步骤 5：代码级交叉审查

审查 `git diff [STARTING_COMMIT_SHA]..HEAD` 的全量变更，关注：

- 跨 pack 的集成问题（pack A 和 pack B 的改动是否冲突？）
- 跨模块的副作用（改了模块 A 是否影响了模块 B 的行为？）
- 项目约定违反（对照 CLAUDE.md 工程规则）

每个 finding：**file:line** + **问题** + **为什么重要** + **修复建议** + **置信度** + **routing**

---

### 假阳性排除

以下**不要报**：
- 已在 Phase A pack review 中报告并修复的问题（不重复审）
- 设计文档中标记为"后续迭代"的功能（不在本次范围）
- 模糊意图的"未满足"（已标为 Suggestion，不算 GAP）

---

### 报告格式

```
### 意图验证

**通过**: X / Y 条可验证意图

#### 通过的意图
1. ✅ 意图 #1："用户能 X" — 验证命令：`...` 输出符合预期
2. ✅ 意图 #3："系统在 Y 时 Z" — 验证命令：`...` 输出符合预期

#### GAP 列表
1. ❌ [Implementation Gap] 意图 #2："用户能批量操作"
   **验证命令**：`curl -X POST .../batch`
   **实际输出**：404 Not Found
   **预期输出**：200 + batch result
   **Acceptance test**：POST /batch 传入 [id1, id2, id3]，返回每个 id 的处理结果
   **routing**: `needs pack-executor`

2. ❌ [Design Gap] 意图 #5："离线时自动同步"
   **问题**：设计要求离线自动同步，但项目架构约束要求本地优先 + 云端掌权，离线时无法调用 Gateway 验证权限
   **routing**: `needs user decision` — 设计需修正

### 回归检查

**结论**：无回归 / N 个回归问题

[如有回归问题，逐个列出 file:line + 问题 + routing]

### 代码级交叉审查

[Critical/Important findings with file:line + confidence + routing]

### 低置信度观察（< 80，仅供参考）
- ...

### 总结

**结论**："功能符合设计意图" 或 "阻塞：N gaps（其中 M 个 implementation gap, K 个 design gap）+ J 个 Critical"
```

**routing 选项**：`needs pack-executor` / `needs root-cause-analyst` / `needs user decision`
