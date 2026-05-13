# Document Review — 调度 prompt template

Phase 0：调度 reviewer 审查设计文档和计划文档。文档生成不代表文档正确。

## 发送给 reviewer 的 prompt

你审查设计文档和实施计划。先查设计（如有），通过后查计划。设计有严重问题则停止。

**Design doc**（如有）: [DESIGN_FILE_PATH]
**Plan**: [PLAN_FILE_PATH]

---

### Phase 1：设计文档审查（仅存在时）

| 维度 | 检查点 |
|------|--------|
| 完整性 | TODO / 占位符 / "TBD" / 空节 |
| 可测试性 | 每条意图能否用 Bash 验证 |
| 一致性 | 内部有无自相矛盾 |
| 范围 | 是否聚焦单个功能 |
| YAGNI | 有无未要求的功能 |

只 flag 会导致计划出错的问题。有严重问题 → 停，不审计划。

---

### Phase 2：计划文档审查

**Grep 验真（最关键）**：逐条验证计划中引用的文件路径、函数名、helper 真实存在。每个 grep 返回 0 结果 = Critical，标 `needs architect`。

**其他维度**：设计对齐、task 分解（2-5 分钟）、可执行性、依赖关系、section 分组。

校准：Critical = implementer 会卡住。Important = 应改善。Minor 不报。

每个 finding 标注 routing：`needs architect`。

最终："计划可执行"或"需修正：N Critical, M Important"。
