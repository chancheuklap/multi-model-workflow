## Parent

#1335, Implementation Decisions sections 1, 2, 3, 6, 7, 11 and 12

## What to build

下面每条前的【】是它来自的子主题；各子主题按列出的顺序做，前面的是后面的基础。

1. 【服务器值唯一写入口与完整存档】新增存档表 `server_value_versions` 的 Alembic 迁移，只建结构：主键 `(scope, revision)`，`(scope, request_id)` 唯一，列按规格第 1 节；数据库层拒绝 UPDATE、DELETE、TRUNCATE。由 AC1、AC2 判定。
2. 【服务器值唯一写入口与完整存档】新增模块 `gateway.server_values`，对外只有 `publish`、`load`、`history`，五个 scope（`gateway`、`parrot_dubbing`、`hedgehog`、`capability_defaults`、`commerce_catalog`）各有私有适配层，映射到今天的生效表，保留代理主键与外键。scope 文档的键：运行参数是今天 `system_settings` 里那份 overrides 的键；`capability_defaults` 用能力 `capability_key` 与 `seed:` 授权的 `grant_id`；`commerce_catalog` 用"种类前缀 + 现有稳定行标识"（规格第 1 节）。
3. 【服务器值唯一写入口与完整存档】变更种类 `Edit | AddMissing | RemoveRetired | Rollback | CaptureLive | ImportCopy` 与 `Draft.against` 按规格第 2 节的语义实现：`Edit` 每个预期旧值都要对上；`AddMissing` 只插入不存在的键；`CaptureLive` 每个 scope 一次、`before == after`、保留现有 `policy_epoch`，缺少的必需键必须恰好等于它带的 `pending_additions`（规格第 4 节）；`ImportCopy` 只接受空的非生产库。由 AC3–AC6 判定。
4. 【服务器值唯一写入口与完整存档】`publish` 在一个事务里：按固定顺序取 advisory 锁，锁内重读，按 `request_id` 查全部历史返回原版本，核对预期版本、完整旧内容摘要和 wire epoch，核对生效表等于存档最新一版，做规格第 3 节的完整性与范围检查，然后追加存档行、只更新变化的生效行、写 `audit_events`，一次提交。拒绝时抛 `PublishRefused`，什么都不写。由 AC3、AC7、AC8 判定。
5. 【服务器值唯一写入口与完整存档】运行参数每次发布让 `policy_epoch` 加一；`capability_defaults` 调用现有的共享能力版本更新逻辑；`commerce_catalog` 没有 epoch。
6. 【服务器值唯一写入口与完整存档】旧客户端读取证明：本票只在 `publish` 里留出"由下发内容推出是否需要证明"的判断，需要证明而 `Proposal.proof` 为空时拒绝；证明的计算与绑定核对由本票的「旧客户端读取证明」子主题实现。
7. 【服务器值唯一写入口与完整存档】Shared 新增 `require(frame, SettingKey(...))`，没有默认参数；缺失、scope 或类型不符、布尔冒充整数、非有限数、结构非法都抛 `RequiredValueUnavailable`，写明 scope、键和预期形状。
8. 【服务器值唯一写入口与完整存档】`Archive.export_copy()` 导出带来源版本、内容摘要和 epoch 的固定副本，去掉个人操作者标识。由 AC6 判定（导出后再 `ImportCopy` 到另一个空库，全部值相同）。
9. 【服务器值唯一写入口与完整存档】`docs/context/platform.md` `### 能力与运行参数` 补"服务器值""存档版本""唯一写入口"三个词条，说明存档版本与 `policy_epoch` 的区别（规格第 14 节）。
10. 【服务器值唯一写入口与完整存档】`Rollback` 的候选是目标版本的完整值，过全部检查；缺少当前必需键就拒绝；`owner_text()` 逐个标出会被删除的键和会降低的版本地板（规格第 2 节）。
11. 【服务器值唯一写入口与完整存档】本票不接任何调用者：启动、后台、闸门、扣费都由后面的票接。
12. 【旧客户端读取证明接进唯一写入口】`publish` 由实际下发内容推出一次改动是否会被客户端读到；会被读到时，必须带旧客户端读取证明，调用者不能豁免。只改 Gateway scope 或 commerce 的改动不需要证明。由 AC1、AC2 判定。
13. 【旧客户端读取证明接进唯一写入口】证明用现有 `scripts/ops/client_release_consumer_check.py` 机制生成：每个仍受支持的已发布客户端读一遍精确的候选投影；改动的下发内容不在现有快照探针范围内时扩展探针。
14. 【旧客户端读取证明接进唯一写入口】证明绑定候选摘要、来源版本、候选版本地板、受支持发布清单、正在服务的构建、目标构建（如有）、定义和投影快照。`publish` 在写入时按本机已安装与待发布产物重算绑定，绑定对不上就拒绝，什么都不写。
15. 【旧客户端读取证明接进唯一写入口】较慢的客户端读取在调用 `publish` 之前完成，`publish` 持锁期间只核对绑定，不运行客户端。
16. 【旧客户端读取证明接进唯一写入口】任何受支持旧版本读不通（例如它当必填读取的键被删掉）时，证明失败，写入被拒绝。
17. 【测试与本机开发的参数值改为从生产固定副本导入】把 `tests/fixtures/server_values/production-raw-2026-10-19/` 的生产原始行转成 `ImportCopy` 格式的固定副本，放在 `tests/fixtures/server_values/` 下，来源是 `RawSnapshot(taken_on=2026-10-19, alembic_revision=0090, rows_digest=原始行摘要)`（规格第 11 节；生产尚无存档，不编造存档版本号），并记录内容摘要和 epoch。转换脚本留在仓库里可重跑。由 AC1 判定（副本里每个值与原始行一致）。
18. 【测试与本机开发的参数值改为从生产固定副本导入】Gateway 测试库的准备改为：跑迁移，再经 `publish(ImportCopy)` 导入固定副本；不再从代码里的 `SYSTEM_SETTING_SEEDS`、`RECHARGE_PACKAGE_SEEDS`、`action_pricing_seed_rows()` 播种。
19. 【测试与本机开发的参数值改为从生产固定副本导入】本机 local-prod 与 source-run 建空库时同样经 `publish(ImportCopy)` 导入这份副本，提供一个命令完成导入；目标库非空时拒绝。
20. 【测试与本机开发的参数值改为从生产固定副本导入】`scripts/dev/macos/local_test_pricing.py` 改为经 `publish(Edit)` 改本机测试库的价格，不再直接写表。
21. 【测试与本机开发的参数值改为从生产固定副本导入】依赖代码种子值的现有测试改为从副本或 `history` 读期望值（`TESTING.md` `## 写作规则` 第 5 条）；本票只改测试支撑和因此必须改的测试，不改产品代码里的种子常量（它们由「Gateway 不再写值也不持值」票删除）。
22. 【测试与本机开发的参数值改为从生产固定副本导入】`TESTING.md` `## 权威源指针` 的"Runtime Policy 默认值"一行改为指向固定副本（规格第 14 节）。
23. 【测试与本机开发的参数值改为从生产固定副本导入】副本和转换脚本不被产品代码导入，不进客户端包。
24. 【扣费请求可带参数版本号】`BillingHoldRequest` 新增可选字段 `policy_epoch: int | None`；产品由已认证的机器与动作上下文推出。旧客户端不发送时请求形状与今天相同。
25. 【扣费请求可带参数版本号】预扣顺序按规格第 12 节：版本地板与认证；只读查找完全相同的已有预扣，找到就返回原结果（金额、标识和状态取自原来那次接受，另加今天就有的 `already_held: true`）、不产生新钱包变化、不重新计价；新预扣带了 `policy_epoch` 就和当前版本比较，不是最新就拒绝并告诉客户端先拉最新参数；没带就照今天放行；然后在一个 SQL 语句快照里冻结产品参数与 Gateway/commerce 价格输入，形成不可变的 `AcceptedHold`；之后才进入待补扣处理和钱包变化。由 AC2–AC5 判定。
26. 【扣费请求可带参数版本号】今天接口层和钱包冻结层各有一处待补扣处理，两处都在版本核对与冻结之后。由 AC3 判定（钱包处于待补扣状态时，带旧版本号的请求被版本拒绝，而不是被待补扣处理）。
27. 【扣费请求可带参数版本号】`AcceptedHold` 传给所有计价与阈值计算，它的标识（接受时的 `policy_epoch` 与各 scope 的存档版本）写进 invocation 已有的 `payload_json`，不新增列；预扣中途和结算时不重新读当前参数。
28. 【扣费请求可带参数版本号】普通读取不加共享行锁、不扫描存档历史。
29. 【扣费请求可带参数版本号】小刺猬现有的逐变体预扣与恢复补扣行为不变；本票不实现续扣的任务身份（第二份规格 #1331）。今天的客户端都不带 `policy_epoch`，所以所有现有扣费路径行为不变，由现有 `tests/billing/` 全部保持通过来证明。

## Read first

- #1335 Implementation Decisions sections 1, 2, 3, 6：本票要实现的决定
- 提交 `023b20571` 的 `efforts/server-param-defaults/prototypes/1294/SKETCH/contract.md`：唯一写入口合同（baseline）
- 提交 `023b20571` 的 `efforts/server-param-defaults/prototypes/1294/SKETCH/selected/server_values.py`、`selected/shared_values.py`、`selected/archive_schema.py`：类型与签名（baseline）
- `docs/adr/platform/0008-server-values-have-one-writer-and-full-version-history.md`：决定本身（baseline）
- `docs/adr/platform/0007-account-permission-is-capability-runtime-parameter-is-setting-def.md`：能力与运行参数各登记在一边
- `TESTING.md` `## 目录分层`、`## 写作规则`、`## 永久禁止`、`## fixture 与数据库基础设施`：测试层与写法
- #1335 Implementation Decisions section 3：证明的范围与绑定
- 提交 `023b20571` 的 `efforts/server-param-defaults/prototypes/1294/SKETCH/contract.md` `### One writer and one transaction`：证明进入写事务的方式（baseline）
- 提交 `023b20571` 的 `efforts/server-param-defaults/prototypes/1294/SKETCH/selected/server_values.py` 的 `ProofBinding`、`ConsumerProof`（baseline）
- `docs/adr/cross-cutting/0011-installed-base-sets-contract-evolution.md`：在网存量决定合同怎样演进
- `TESTING.md` `## 目录分层`（L2 跨边界合同）、`## 写作规则`
- #1335 Implementation Decisions sections 7 and 11：副本的来源与用法
- `tests/fixtures/server_values/production-raw-2026-10-19/README.md`：原始快照的来源与文件说明
- 提交 `023b20571` 的 `efforts/server-param-defaults/prototypes/1294/SKETCH/contract.md` `### Startup, migrations and initial values`：空库导入（baseline）
- `TESTING.md` `## fixture 与数据库基础设施`、`## 权威源指针`、`## 写作规则`
- #1335 Implementation Decisions section 12：预扣顺序与冻结
- 提交 `023b20571` 的 `efforts/server-param-defaults/prototypes/1294/SKETCH/contract.md` `## Hold version and running tasks`（baseline）
- `docs/adr/platform/0005-every-hold-reaches-a-terminal-state.md`：每笔预扣都走到终态
- `docs/context/platform.md` 预扣、结算、待补扣词条
- `TESTING.md` `## 目录分层`（L1 钱与账本）、`## 写作规则`

## Seam

L3 `tests/gateway/`（唯一写入口、测试副本，参照 `tests/gateway/test_runtime_policy_fail_loud.py` 的组织方式但用真实隔离 Postgres）、L2 `tests/contracts/test_server_values_consumer_proof.py`（参照 `tests/contracts/test_version_compat.py`）、L1 `tests/billing/test_hold_policy_epoch.py`（参照 `tests/billing/test_billing_four_state_lifecycle.py`）。版本历史经 `publish(ImportCopy)` 与 `publish(Edit)` 造出；生效表与存档不一致由测试自己的 SQL 造出；存档写入失败用临时触发器造出；"核对之后才提交的新发布"由两个连接控制提交顺序造出。

## Owns

- src/gateway/server_values.py (new)
- src/shared/contracts/runtime_policy_values.py (new)
- migrations/gateway/versions/0091_server_value_versions.py (new)
- tests/gateway/test_server_values_publish.py (new)
- docs/context/platform.md
- src/gateway/server_values.py
- scripts/ops/client_release_consumer_check.py
- tests/contracts/test_server_values_consumer_proof.py (new)
- tests/fixtures/server_values/**
- tests/support/gateway_test_support.py
- tests/support/runtime_policy.py
- tests/conftest.py
- scripts/dev/server_values_copy.py (new)
- scripts/dev/macos/local_test_pricing.py
- tests/gateway/test_local_prod_test_pricing.py
- tests/gateway/test_server_values_test_copy.py (new)
- tests/billing/**
- tests/gateway/test_runtime_policy_fail_loud.py
- TESTING.md
- src/shared/billing_contracts.py
- src/gateway/api.py
- src/gateway/wallet_billing_hold.py
- src/gateway/accepted_hold.py (new)
- src/gateway/services/billing_pricing_consumer.py
- src/gateway/product_billing_registry.py
- tests/billing/test_hold_policy_epoch.py (new)

## Acceptance criteria

- [ ] AC1: 迁移到 head 后存在 `server_value_versions`，`(scope, revision)` 是主键、`(scope, request_id)` 唯一
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t02 uv run pytest tests/gateway/test_server_values_publish.py -k "archive_table_has_scope_revision_key" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC2: 对存档表执行 UPDATE、DELETE、TRUNCATE 各自被数据库拒绝，存档行数不变
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t02 uv run pytest tests/gateway/test_server_values_publish.py -k "archive_refuses_update_delete_truncate" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC3: `Edit` 的预期旧值与当前值不同时抛 `PublishRefused`，当前值、epoch、存档条数都不变
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t02 uv run pytest tests/gateway/test_server_values_publish.py -k "edit_with_stale_old_value_is_refused" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC4: `AddMissing` 带一个已存在的键时整份被拒绝，已有键保持原值
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t02 uv run pytest tests/gateway/test_server_values_publish.py -k "add_missing_never_overwrites" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC5: `CaptureLive` 产生 revision 1，`before_values` 等于 `after_values` 等于生效值，`policy_epoch` 等于捕获前的值
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t02 uv run pytest tests/gateway/test_server_values_publish.py -k "capture_live_keeps_values_and_epoch" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC6: `export_copy()` 导出后 `ImportCopy` 到另一个空库，五个 scope 的全部值和 epoch 与源库相同
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t02 uv run pytest tests/gateway/test_server_values_publish.py -k "export_then_import_round_trips" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC7: 同一 `request_id` 在之后又有新版本时重发，返回原来那一版，存档条数不增加
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t02 uv run pytest tests/gateway/test_server_values_publish.py -k "same_request_id_returns_original_version" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC8: 存档插入失败时整个事务回滚，生效值与 epoch 都不变
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t02 uv run pytest tests/gateway/test_server_values_publish.py -k "archive_failure_rolls_back_everything" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC9: 一次运行参数 `Edit` 成功后 `policy_epoch` 恰好加一，存档恰好多一行且含完整改前、改后值和老板原话
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t02 uv run pytest tests/gateway/test_server_values_publish.py -k "runtime_edit_bumps_epoch_and_archives_once" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC10: `require` 遇到缺失键或布尔冒充整数时抛 `RequiredValueUnavailable`，不返回任何值
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t02 uv run pytest tests/gateway/test_server_values_publish.py -k "require_refuses_missing_and_bool_as_int" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC11: 回滚到一个缺少后来新增必需键的版本时 `publish` 拒绝，值与存档不变；`owner_text()` 列出该键为删除
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t02 uv run pytest tests/gateway/test_server_values_publish.py -k "rollback_missing_new_key_is_refused" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC12: 改小鹦鹉 scope 一个会下发的值、`proof` 为空时 `publish` 拒绝，值不变
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t03 uv run pytest tests/contracts/test_server_values_consumer_proof.py -k "client_visible_change_without_proof_is_refused" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC13: 改 Gateway scope 一个值、`proof` 为空时 `publish` 成功
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t03 uv run pytest tests/contracts/test_server_values_consumer_proof.py -k "server_only_change_needs_no_proof" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC14: 候选删去一个受支持旧版本当必填读取的键时，证明生成失败并写明是哪个版本、哪个键
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t03 uv run pytest tests/contracts/test_server_values_consumer_proof.py -k "proof_fails_when_supported_release_loses_required_key" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC15: 为另一份候选生成的证明交给这份候选时 `publish` 拒绝，值与存档不变
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t03 uv run pytest tests/contracts/test_server_values_consumer_proof.py -k "proof_bound_to_other_candidate_is_refused" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC16: 固定副本里三份运行参数、能力目录与 `seed:` 授权、套餐、充值档、钱包设置、动作单价的每个值都等于原始快照里的对应值
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t04 uv run pytest tests/gateway/test_server_values_test_copy.py -k "copy_matches_production_raw_snapshot" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC17: 测试库准备完成后，存档里每个 scope 恰好一行，来源种类是 `ImportCopy`，生效值等于固定副本
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t04 uv run pytest tests/gateway/test_server_values_test_copy.py -k "test_database_is_built_from_copy" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC18: 导入命令对非空库以非零退出，库里的值与存档条数不变
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t04 uv run pytest tests/gateway/test_server_values_test_copy.py -k "import_refuses_non_empty_database" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC19: `local_test_pricing.py` 改一个本机测试价后，存档多一行，新价出现在生效表
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t04 uv run pytest tests/gateway/test_local_prod_test_pricing.py -k "local_test_price_goes_through_publish" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC20: 不带 `policy_epoch` 的预扣请求得到与今天相同的冻结金额和 invocation 状态 `held`
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t06 uv run pytest tests/billing/test_hold_policy_epoch.py -k "hold_without_epoch_behaves_as_today" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC21: 带旧 `policy_epoch` 的新预扣被拒绝，钱包余额、冻结额、`metering_invocations` 行数都不变
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t06 uv run pytest tests/billing/test_hold_policy_epoch.py -k "stale_epoch_is_refused_before_any_wallet_change" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC22: 钱包处于 `pending_top_up` 时，带旧 `policy_epoch` 的请求得到版本拒绝，钱包状态不变
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t06 uv run pytest tests/billing/test_hold_policy_epoch.py -k "epoch_check_runs_before_pending_top_up" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC23: 预扣被接受后发布一个新单价，这笔预扣结算时仍按接受时的单价扣费
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t06 uv run pytest tests/billing/test_hold_policy_epoch.py -k "accepted_hold_settles_at_accepted_price" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC24: 同一笔预扣在之后发布了新版本时重发，返回的响应除 `already_held: true` 外与第一次完全相同，钱包只冻结一次
  CHECK: GATEWAY_TEST_DATABASE_URL=postgresql://agentflow:agentflow@localhost:5432/gateway_test_t06 uv run pytest tests/billing/test_hold_policy_epoch.py -k "identical_retry_returns_original_after_new_version" -rs
  EXPECT: /^\d+ passed(, \d+ deselected)? in [0-9.]+s$/m
  EVIDENCE: pending




