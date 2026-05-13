# Document Review — Phase 0 prompt template

Phase 0：调度 workflow-auditor 审查设计文档和计划文档。文档生成不代表文档正确。

## 发送给 workflow-auditor 的 prompt

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

**项目工程规则对照（最关键）**：读取项目根目录 CLAUDE.md 链入的工程规则文档（如有）。验证计划是否违反项目不变量、单一权威源、模块边界、数据权威归属等约束。违反 = Critical。

**Grep 验真（安全网）**：逐条验证计划中引用的文件路径、函数名、helper 真实存在。grep 返回 0 结果 = Critical。

**其他维度**：设计对齐、task 分解（2-5 分钟）、可执行性、依赖关系、section 分组。

校准：Critical = pack-executor 会卡住。Important = 应改善。Minor 不报。

**每个 finding 附置信度（0-100），只报 ≥ 80。**

Phase 0 finding 不标注路由——全部返回给编排器（主 session）直接处理。

最终："计划可执行"或"需修正：N Critical, M Important"。低于 80 置信度的观察列在"低置信度观察"段落供参考。
