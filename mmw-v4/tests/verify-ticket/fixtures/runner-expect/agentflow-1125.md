## Parent

#1123, Implementation Decisions sections 1, 5 and 6（以及第 2 节中删除开发验收请求头的那一段）。

## What to build

1. **发送声明。** 两个产品的 Python 后端向 Gateway 请求运行时策略时，带上请求头 `X-AgentFlow-Config-Contract-Accept`，值为该产品共享合同模块里的声明常量（`PARROT_CONFIG_CONTRACTS_READ`、`HEDGEHOG_CONFIG_CONTRACTS_READ`，由前置工单定义）用逗号连接。请求头名字从 `shared.contracts.runtime_policy` 的常量读。只有拉取运行时策略的请求带这个头。由 AC1、AC2 判定：真实客户端连真实 Gateway 应用，拿到预期的合同。
2. **记下选中的合同。** 每次成功拉取后，在该产品现有的运行时策略日志里记下本次声明的列表，以及 Gateway 回显的 `X-AgentFlow-Config-Contract`；旧 Gateway 不回显时记为 `not_provided`。由 AC3、AC4、AC5 判定。这样以后"某版本拿到的目录不对"，从客户端日志就能看出来。
3. **删除开发验收请求头，客户端和 Gateway 两侧一起删。** 客户端的 `PARROT_DUBBING_LOCAL_ACCEPTANCE` 环境变量和 `X-AgentFlow-Local-Acceptance` 请求头；Gateway 的 `AGENTFLOW_LOCAL_CLIENT_ACCEPTANCE` 环境变量、对这个请求头的识别和 `local_acceptance` 分支；`docker/compose.local-prod.yml` 里的这个环境变量。源码运行版今后靠第 1 点的声明拿到 `parrot_dubbing-config-v2`，由 AC6 判定。用到这个环境变量的测试一并改写（`tests/contracts/test_parrot_error_reporting_wire.py`、`tests/parrot/test_parrot_runtime_policy_refresh.py` 的 `test_源码运行仅明确本地验收时声明新配置合同`）。
4. **防止下次遗漏的两项检查（#1123 第 5 节）。** 新建 `tests/contracts/test_config_contract_declaration.py`：
   - 每个已上线产品，客户端声明的最高一档合同在该产品 Adapter 的合同元组里，由 AC7 判定；
   - 小鹦鹉声明的每一档合同，在 Adapter 的目录批次映射里对应的每个音色，在 `src/parrot_dubbing/assets/voice-previews/` 里都有以该音色 `voice_id` 命名的试听文件，由 AC8 判定。
   两项都从权威源读出比对，不在测试里抄一份列表（`TESTING.md` › 写作规则 5）。

## Read first

- #1123 第 1、5、6 节：本票的依据（baseline）。
- #1123 第 2 节最后一段：删除开发验收请求头的理由。
- `src/shared/contracts/version_negotiation.py` 模块说明：协商头的形式。
- `CODING_STANDARDS.md` › Contracts and evolution：服务端先支持新请求字段，客户端再发送。前置工单已经让 Gateway 读这个头。
- `TESTING.md` › 外部 seam：真实客户端连真实 Gateway 应用，自家接缝不打桩。

## Seam

- L2 跨边界合同，`tests/contracts/test_config_contract_declaration.py`（新建）。真实客户端连真实 Gateway 应用的写法照抄 `tests/contracts/test_parrot_error_reporting_wire.py`：激活取得机器凭证，`httpx.ASGITransport(app=gateway)` 接到真实 Gateway。声明列表由真实客户端代码产生。
- L3 产品行为：小鹦鹉在 `tests/parrot/test_parrot_runtime_policy_refresh.py`，小刺猬在 `tests/hedgehog/test_hedgehog_runtime_policy_fetch.py`（新建）。写法照抄 `test_源码运行仅明确本地验收时声明新配置合同`：用 `httpx.MockTransport` 给出带或不带 `X-AgentFlow-Config-Contract` 的响应，再读该产品的结构化日志。

## Owns

- src/parrot_dubbing/gateway_client.py
- src/hedgehog/gateway_client.py
- src/gateway/api.py
- src/gateway/client_config_compat.py
- docker/compose.local-prod.yml
- tests/contracts/test_config_contract_declaration.py (new)
- tests/contracts/test_parrot_error_reporting_wire.py
- tests/parrot/test_parrot_runtime_policy_refresh.py
- tests/hedgehog/test_hedgehog_runtime_policy_fetch.py (new)
- tests/gateway/test_runtime_policy_fail_loud.py

## Acceptance criteria

- [ ] AC1: 真实小鹦鹉 Gateway 客户端连真实 Gateway，拉取运行时策略后拿到 `parrot_dubbing-config-v2` 和 29 项音色
  CHECK: uv run pytest tests/contracts/test_config_contract_declaration.py -k "小鹦鹉真实客户端声明后拿到新合同"
  EXPECT: /^1 passed(, \d+ deselected)?(, \d+ warnings?)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC2: 真实小刺猬 Gateway 客户端连真实 Gateway，拉取运行时策略后拿到 `hedgehog-config-v1`
  CHECK: uv run pytest tests/contracts/test_config_contract_declaration.py -k "小刺猬真实客户端声明后拿到合同"
  EXPECT: /^1 passed(, \d+ deselected)?(, \d+ warnings?)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC3: 小鹦鹉拉取运行时策略后，日志记下声明列表和 Gateway 回显的合同
  CHECK: uv run pytest tests/parrot/test_parrot_runtime_policy_refresh.py -k "拉取运行时策略后日志记下回显的合同"
  EXPECT: /^1 passed(, \d+ deselected)?(, \d+ warnings?)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC4: 小鹦鹉连到不回显合同的 Gateway 时，日志把回显的合同记为 `not_provided`
  CHECK: uv run pytest tests/parrot/test_parrot_runtime_policy_refresh.py -k "旧Gateway不回显合同时日志记为未提供"
  EXPECT: /^1 passed(, \d+ deselected)?(, \d+ warnings?)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC5: 小刺猬拉取运行时策略后，日志记下声明列表和 Gateway 回显的合同
  CHECK: uv run pytest tests/hedgehog/test_hedgehog_runtime_policy_fetch.py -k "拉取运行时策略后日志记下回显的合同"
  EXPECT: /^1 passed(, \d+ deselected)?(, \d+ warnings?)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC6: 版本为 `source-run`、不设任何开发验收环境变量的小鹦鹉客户端，拉取运行时策略时声明里含 `parrot_dubbing-config-v2`
  CHECK: uv run pytest tests/parrot/test_parrot_runtime_policy_refresh.py -k "源码运行版靠声明拿到新合同"
  EXPECT: /^1 passed(, \d+ deselected)?(, \d+ warnings?)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC7: 每个已上线产品，客户端声明的最高一档合同，该产品 Adapter 都认识
  CHECK: uv run pytest tests/contracts/test_config_contract_declaration.py -k "客户端声明的最高合同Gateway都认识"
  EXPECT: /^1 passed(, \d+ deselected)?(, \d+ warnings?)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC8: 小鹦鹉声明的每一档合同所含的每个音色，在客户端源码里都有试听文件
  CHECK: uv run pytest tests/contracts/test_config_contract_declaration.py -k "小鹦鹉声明的每档合同所含音色都有试听文件"
  EXPECT: /^1 passed(, \d+ deselected)?(, \d+ warnings?)? in [0-9.]+s$/m
  EVIDENCE: pending
- [ ] AC9: 小鹦鹉报错上报合同测试和 Gateway 运行时策略下发测试全部通过
  CHECK: uv run pytest tests/contracts/test_parrot_error_reporting_wire.py tests/gateway/test_runtime_policy_fail_loud.py
  EXPECT: /^\d+ passed(, \d+ warnings?)? in [0-9.]+s$/m
  EVIDENCE: pending
  TIMEOUT: 1200
