# Route 7: Maintenance

> **入口**：`orchestrate-workflow` Step 1 Entry Gate 匹配 升级 / upgrade / CVE / 依赖 / 重构 / refactor / 清理 / tech debt

维护任务路径。依赖更新、文档更新、配置调整、chore。

**触发关键词**: maintenance, 依赖更新, 文档更新, chore, cleanup, refactor, bump

**行为差异**（相对 formal route）:

## Phase 简化

- **skip Discovery**：maintenance 不需要设计文档。
- **Plan Writing 简化**：Coordinator 直接写 maintenance plan，不派 plan_writer。
- **Plan Review 简化**：Coordinator 自检。
- `budget_status = "unlimited"`, `review_total = "unlimited"`, `effort_total = "unlimited"`

## Codex Review Focus

Maintenance 的 Codex review 不审设计，专注三个维度：

1. **Breaking changes**：
   - API 签名变更
   - 公共接口移除或重命名
   - 配置格式变更
   - 数据格式变更

2. **Regression surface**：
   - 修改是否导致现有测试失败
   - 修改是否触碰 CI/CD pipeline
   - 依赖版本升级是否有 breaking change notes

3. **Dependency compatibility**：
   - 升级的依赖是否与其他依赖有版本冲突
   - 升级的依赖是否 drop 了当前使用的 API
   - 升级的依赖是否有已知安全漏洞修复

## 执行约束

- 每个 maintenance task 是一个独立的 Pack
- Dependency update: `uv lock --upgrade-package <pkg>` + 跑全量测试
- 文档更新：不需要 TDD（risk_flags: trivial）
- 配置调整：需要验证配置生效（可用 integration test 或手动确认）

## Final Review 简化

Final Review 降级为 **lint + test pass check**：
- `uv run pytest` 全部通过
- `uv run ruff check` 无新 error
- 无 breaking change（或 breaking change 有 migration guide）

不做 intent coverage、cross-plan integration 等完整 Final Review angle。

---
> **下一步**：Final Review 通过 → orchestrate-workflow Closing。needs repair → 修复循环。
