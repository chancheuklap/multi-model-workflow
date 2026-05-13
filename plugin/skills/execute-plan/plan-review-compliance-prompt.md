# Plan Review — Compliance & Verification

Phase 0b 并行组 2：审查计划文档是否合规（项目工程规则）以及所有引用是否真实存在（grep 验真）。

## 发送给 workflow-auditor 的 prompt

你审查计划文档的**合规性与引用真实性**。另一个 auditor 同时在审查覆盖度与 task 质量——你不需要关注 task 粒度和 section 分组，专注于"计划是否合规"和"引用是否存在"。

**Plan**: [PLAN_FILE_PATH]

**首先**：读取项目根目录 CLAUDE.md 及其链入的所有规则文档（如 AGENTS.md、ENGINEERING-RULES.md、PROJECT.md）。你需要完整理解项目工程规则才能做此审查。

每个 finding 必须有：**具体位置**（plan 的哪个 task/行）+ **问题描述** + **为什么这会导致执行出错** + **置信度（0-100，只报 ≥ 80）**。

---

### 1. 项目工程规则对照

逐条对照项目工程规则：

- 计划是否违反项目不变量、单一权威源、模块边界？
- 新增的端口/命令是否标注了需注册到权威位置（ports.py / command_contract.py）？
- 新增的收费动作是否标注了需注册到 CHARGEABLE_ACTION_CATALOG？
- 涉及跨模块数据的 task 是否标注了合同墙要求（Pydantic 合同注册）？
- 涉及数据库变更的 task 是否标注了 Alembic 迁移（哪棵树？gateway / collection）？
- 涉及的目录如有 AGENTS.override.md，是否有 task 负责同步更新？
- 日志相关 task 是否使用 shared.logger.get_logger()？

**项目规则违反 = Critical**（引用具体规则条文）。

### 2. Grep 验真

**逐条验证**计划中引用的每一个文件路径、函数名、类名、配置项、环境变量：

```bash
# 对每个引用执行：
grep -r "引用的名称" --include="*.py" .
# 或
find . -path "引用的路径"
```

- 每个 grep 返回 0 结果 = **Critical**（引用不存在）
- **不跳过任何一个引用**——逐条执行，逐条报告结果
- 如果引用名称有多种可能的写法（驼峰/蛇形/带前缀），都试一遍

### 3. 环境与依赖验真

- task 中提到的外部依赖（pip 包、npm 包、系统工具）是否在项目中已存在？
- 环境变量引用（`os.environ["X"]`）是否在 `.env.example` 或文档中有记录？

---

### 校准

| 级别 | 定义 | 示例 |
|------|------|------|
| **Critical** | pack-executor 会卡住或产生违规代码 | 引用不存在的路径/函数、违反项目约束、依赖不存在 |
| **Important** | 不卡但降低代码合规性 | 未标注需注册的端口/命令、AGENTS.override.md 同步遗漏 |
| Minor | 不报 | |

### 假阳性排除

- task 中说"创建新文件 X"——这个文件当然不存在（是要新建的），不是引用错误
- 项目约定中没有明确禁止的做法
- 不确定的规则推断（项目文档没明确说，不要猜测）

### 报告格式

```
### 计划文档 — 合规与验真审查

**Grep 验真**：X / Y 个引用验证通过
**项目规则**：检查了 N 条约束

**结论**：合规 / 需修正（N Critical, M Important）

#### Critical
1. [confidence: 98] Task 5 引用 `src/collection/compass/pipeline.py::process_batch`
   **grep 结果**：`grep -r "process_batch" src/collection/compass/pipeline.py` → 0 results
   **实际**：该文件中函数名是 `process_compass_batch`
   **建议**：修正引用为 `process_compass_batch`

2. [confidence: 92] Task 8 计划在 Gateway DB 中新增 `runtime.video_jobs` 表
   **违反规则**：PROJECT.md §9 北极星 #2 "`runtime.*` schema = Collection DB 独占"
   **建议**：改为在 Collection DB 迁移树中新增

#### Important
1. [confidence: 84] Task 3 新增端口 9225 但未提及 ports.py 注册
   **项目规则**：ENGINEERING-RULES §2.2
   **建议**：补充 sub-task "注册 9225 到 shared/ports.py"

### 低置信度观察（< 80，仅供参考）
- ...
```

Phase 0 finding 不标注路由——全部返回给编排器（主 session）直接处理。
