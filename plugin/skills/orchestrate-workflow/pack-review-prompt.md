# Pack Review — Phase A prompt template

Phase A：调度 workflow-auditor 审查一个 Task Pack 的实现。先查 spec compliance，通过后查 code quality。Spec 不过则停止。

## 发送给 workflow-auditor 的 prompt

你审查一个 Task Pack 的实现。**不信任 pack-executor 的自我报告——独立验证一切。**

**Plan**: [PLAN_FILE_PATH]

[FOR EACH TASK IN PACK]
**Task [N]**: [TASK_TITLE]
[FULL TASK TEXT]
[END FOR EACH]

**pack-executor 报告**: [PASTE IMPLEMENTER REPORT]

**独立验证手段**（必做，不依赖报告）：
1. `git diff [BASE_SHA]..HEAD` — 查看实际代码变更
2. 跑相关测试 — 确认测试真的通过
3. 读变更文件 — 理解实际实现

---

### Phase 1：Spec Compliance

逐 task 检查，每个 finding 必须有：**file:line** + **问题描述** + **为什么这不符合 spec** + **置信度（0-100）**。

#### 1.1 逐 Task 对照

对每个 task：
- **该做的做了吗？** — task 描述的功能是否已实现？
- **没要求的做了吗？** — 有无超出 task 范围的改动？（scope creep = Important，除非是安全修复）
- **做对了吗？** — 实现方式是否符合 task 描述的 TDD 要求？
- **做漏了吗？** — task 描述的边界条件/错误处理是否实现？

#### 1.2 跨 Task 集成

- Pack 内多个 task 的改动是否互相兼容？
- 有无 task A 的改动破坏 task B 的实现？
- 共享文件的改动是否冲突？

#### 1.3 安全默认

安全问题无论 spec 有没有要求，一律 **Critical**：
- 注入漏洞（SQL / XSS / Command injection）
- 认证/授权绕过
- 敏感数据泄露（日志中打印密钥/token）
- 不安全的默认值

#### 校准

| 级别 | 定义 |
|------|------|
| **Critical** | 功能缺失、功能做错、安全漏洞 |
| **Important** | scope creep、边界条件遗漏、TDD 步骤跳过 |
| Minor | 不报 |

**有 Critical → 停止，不进 Phase 2。**

---

### Phase 2：Code Quality（仅 Phase 1 通过时）

每个 finding 必须有：**file:line** + **问题描述** + **为什么重要** + **具体修复建议** + **置信度（0-100）**。

#### 2.1 正确性

- 逻辑错误？（off-by-one、空值未处理、类型不匹配）
- 竞态条件？（异步操作未正确等待、共享状态无锁）
- 资源泄露？（未关闭的连接/文件句柄）

#### 2.2 项目约定合规

读取项目 CLAUDE.md 链入的工程规则文档（如有），**逐条对照**：
- 日志规范（是否使用项目指定的 logger？有无裸 `print`？）
- 合同墙（跨边界数据是否经 Pydantic 合同？JSONB 列是否在 registry 注册？）
- 模块边界（import 方向是否正确？有无反向依赖？）
- 单一权威源（是否修改了权威位置？还是在非权威位置创建了副本？）
- 命名约定（变量/函数命名是否符合项目惯例？）
- AGENTS.override.md（改动涉及的目录如有此文件，是否需要同步更新？）

**项目约定违反 = Critical**（引用具体规则）。

#### 2.3 测试质量

- 测试是否验证了真实行为？（不是只测 mock）
- 边界条件有测试覆盖吗？
- 测试能被未来重构意外破坏吗？（过度依赖实现细节）
- 测试是否真的跑过并通过？（你自己跑一次确认）

#### 2.4 文件健康

- 改动后文件是否超过项目规定的长度上限？
- 有无不必要的重复代码？（但不强求抽象——三行重复优于过早抽象）

---

### 假阳性排除

以下**不要报**：
- 已有的技术债（只审查本次变更引入的问题）
- linter / type checker 能自动发现的问题
- 纯风格偏好（除非项目 CLAUDE.md 明确规定）
- 看起来可疑但实际正确的代码（标记前先读上下文确认）

---

### 报告格式

```
### Spec Compliance

**结论**：通过 / 阻塞（N Critical, M Important）

#### Critical
1. [confidence: 92] Task 3："添加 CSRF 防护" — **未实现**。
   file: `src/api/routes.py:45`
   **为什么重要**：设计文档明确要求此功能，缺失 = 安全漏洞。
   **建议**：在 POST 路由添加 CSRF token 验证中间件。
   **routing**: `needs pack-executor`

### Code Quality（仅 Spec 通过时）

**结论**：通过 / 阻塞（N Critical, M Important）

#### Critical
1. [confidence: 88] `src/local_agent/worker.py:123` — 裸 `print()` 替代 structlog logger。
   **为什么重要**：违反项目 ENGINEERING-RULES §2.9 日志强制 structlog 规则。
   **建议**：改为 `logger.info("...", key=value)` 使用 `shared.logger.get_logger()`。
   **routing**: `needs pack-executor`

### 低置信度观察（< 80，仅供参考）
- ...
```

**routing 选项**：`needs pack-executor` / `needs root-cause-analyst` / `needs user decision`

**判断标准**：能说清"改哪里改什么" → `needs pack-executor`。只能说"有问题但不知为什么" → `needs root-cause-analyst`。涉及功能范围变更 → `needs user decision`。
