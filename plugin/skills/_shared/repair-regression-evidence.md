> **使用场景**：repair worker 或 Coordinator Path A 自修返回时，按本表选择回归证据形态 · 核心要求（必须返回回归证据）已写在 worker agent 合同中，本文件是 finding-type → 证据类型的细化指引

**回归证据要求 (REQUIRED in repair return)**：

Repair agent 或 Coordinator Path A 返回时必须提供回归证据；不要求每个 finding 都新增一个测试。优先选择能证明用户可见行为、合同或发布风险已修好的证据，不新增低价值实现细节测试。

| Finding 类型 | 优先证据 |
| --- | --- |
| Public behavior bug | 现有或新增 behavior / integration test。 |
| 合同、schema、migration、生成产物 bug | 合同检查、schema validation、migration check 或 build check。 |
| UI 行为 bug | Browser smoke、screenshot、DOM state validation 或现有 UI test。 |
| permission、billing、runtime、state machine、hook 问题 | integration check、state transition check、hook test，或带 owner 和步骤的 manual validation gate。 |
| 文档或 plan mismatch | 文档一致性证据和修正后的 source 链接。 |
| 只能环境验证的问题 | 明确 owner、命令、预期结果和阻塞条件的 manual validation gate。 |

Repair Return Contract 必须补充：
- `Regression evidence`: 命令、测试、build/schema/migration/hook check、browser evidence，或 manual validation gate。
- `Test choice`: 说明为何使用现有测试、新增高层测试、合同检查或 manual gate；不得为纯实现细节新增脆弱测试。
- `Unverified`: 仍未验证的边界和原因；没有则写 `无`。
