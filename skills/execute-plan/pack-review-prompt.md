# Pack Review — 调度 prompt template

Phase A：调度 reviewer 合并审查 spec compliance + code quality。

## 发送给 reviewer 的 prompt

你审查一个 Task Pack 的实现。先查 spec compliance，通过后查 code quality。Spec 不过则停止。

**Plan**: [PLAN_FILE_PATH]

[FOR EACH TASK IN PACK]
**Task [N]**: [TASK_TITLE]
[FULL TASK TEXT]
[END FOR EACH]

**Implementer 报告**: [PASTE IMPLEMENTER REPORT]

重要：不信任报告。独立验证：`git diff [BASE_SHA]..HEAD`、跑测试、读变更文件。

---

### Phase 1：Spec Compliance

对每个 task：改了该改的？改了不该改的？多做？少做？误解？

跨 task：pack 内集成正确？安全问题默认 Critical。

不查：代码质量（Phase 2）、端到端功能（intent review）。

有 Critical → 停，不进 Phase 2。

---

### Phase 2：Code Quality（仅 Phase 1 通过时）

正确性、安全、质量、测试覆盖、文件健康。

不查：Spec compliance（已查）、端到端功能。

---

### 报告

每个 finding：severity + file:line + 问题 + 建议 + routing（`needs implementer` / `needs debugger` / `needs user decision`）。

结论："Spec + Quality 通过" / "Spec 不过：N Critical" / "Quality 阻塞：N Critical"。
