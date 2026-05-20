# Pack Review Codex Dispatch Template

> **流程位置**：`orchestrate-execution` Step 8 · Worker 返回后派发 Reviewer 时读取

Worker 返回 `pass` 或处理完 `needs repair` concerns 后，派发 **1 个** baseline Codex reviewer。

**Codex review 派发步骤**（`CODEX_SCRIPT` 未定义时先执行 `CODEX_SCRIPT="$(find ~/.claude/plugins -path "*/codex/scripts/codex-companion.mjs" -type f 2>/dev/null | head -1)"`）：
1. 写 prompt → `review-prompts/<gate>.md`
2. `node "$CODEX_SCRIPT" task --background --prompt-file .claude/multi-model-workflow/review-prompts/<gate>.md --model gpt-5.4 --effort xhigh` → 记录 JOB_ID
3. `node "$CODEX_SCRIPT" status <JOB_ID> --wait --timeout-ms 600000`（run_in_background: true）
4. `node "$CODEX_SCRIPT" result <JOB_ID>` → 存到 `review-results/<gate>.md`

以下是 review prompt 内容（写入 `.claude/multi-model-workflow/review-prompts/pack-review-N.M.md`）：

```markdown
## Scope
Review the implementation of Task Pack N.M: <title>

## Source artifacts
- Plan: <path>
- Source design: <path>
- Pack acceptance criteria: <paste>
- Verification commands: <paste>

## Changed files
<list from worker return>

## Contract anchors
<paste if this pack touches contract boundaries>

## Mockup anchors
<paste if this pack has UI work>

## Review angles (single integrated review)

### Spec Compliance
验 worker 是否实现了 pack 要求的一切（不多不少）：
- 每条 acceptance criteria 是否满足
- 是否有 missing requirements
- 是否有 extra/unneeded work（YAGNI）
- goal behavior 是否可从代码中确认

### Code Quality
验实现是否正确、可维护：
- TDD 纪律：测试测的是 public behavior，不是 mock behavior。检查测试是否先失败再通过——没失败过的测试不可信
- Mock 纪律：mock 只用在外部边界（网络、文件系统、第三方 API），不 mock 仓库内部业务模块。测试断言的是结果和行为，不是调用顺序或内部状态
- 合同纪律：跨边界数据用正式 Pydantic contract，不是 bare dict
- 文件职责清晰、接口定义好
- 遵循项目既有模式
- Forbidden shortcuts（以下默认是 finding；影响验收/数据/权限/账务/runtime/发布时是 Critical）：
  · bare dict 作跨模块长期合同
  · route/host 内临时拼 nested dict 绕过正式 contract
  · 新增 route-local schema/helper 而不放 domain service/shared contract
  · public API 返回 dict[str, Any]
  · silent unknown-field drop / extra=allow 无版本策略
  · 直接写 JSONB/SQLite JSON 不注册不走 validator
  · 新 DB 字段没有 migration/repository/read model/回归测试
  · 新 port/command/chargeable action/capability 没进 registry/catalog
  · 测试 mock 仓库内部业务模块
  · helper 只为绕过边界而存在

### Contract & Risk
验高风险面是否正确处理：
- Contract anchors 闭合（owner / provider / consumer / verification）
- Migration / registry / catalog 完整
- 发布风险标注准确
- rollback / compatibility 考虑

## Calibration
**不要信任 worker 的报告——独立验证一切。** Worker 可能遗漏了失败的边界情况、跳过了困难的 acceptance criteria、或报告了实际未通过的测试。你的 review 必须基于代码事实，不是 worker 的自述。

只标记会导致实际问题的 issue。实现者做出错误的东西或卡住——这是 issue。
措辞、风格偏好、nice-to-have 建议——不是。
除非有严重缺口（spec 不符、合同破损、测试不覆盖核心行为、引入安全风险），否则 approve。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
### Result
Pack Review 结果：
Spec compliance:
Code quality:
Contract & risk:
Critical:
Important:
低置信度观察:
Disposition required:
### Verification
### Open Items
```
