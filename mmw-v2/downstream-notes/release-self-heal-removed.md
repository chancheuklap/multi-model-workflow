# release-self-heal-removed

## 改了什么

`exe-release` 删除了自动修复后端和只为它存在的整套机制：`fix_executor`、`editable_paths`、`protection_source`、`post_fix_gate` 四个 release manifest 字段，连同引擎里执行它们的受保护路径闸、`post_fix_gate` 校验闸都已删除。`release_contracts.py` 的 `ReleaseAdapterManifest` 是 `model_config = ConfigDict(extra="forbid")`：一份 release manifest 只要还带着这四个字段中的任何一个，`<release> init`（先跑 `release_contracts.py validate-manifest`）就会立即拒绝，报 "Extra inputs are not permitted"。

`derive`（P2，产品仓库自己的确定性重生脚本）保留，行为不变：它的提交前仍只检查功能分支没有事先存在的未提交改动。

## 哪些产物失效

`~/agentflow` 与 `~/xiaohuangya` 的 release manifest（`*.release-adapter.json`）全部声明了这四个字段，构成失效的 `.mmw/target.json` 等价物；下面按仓库列出要删的字段、要删的文件、要改或删的测试。

### `~/agentflow`

**Release manifest**，删除以下四个字段（`editable_paths`、`protection_source`、`post_fix_gate`、`fix_executor`）：
- `scripts/release/adapters/hedgehog.release-adapter.json`
- `scripts/release/adapters/parrot.release-adapter.json`

**整个删除**（删完 release manifest 上的四个字段后，这三个文件没有任何调用者）：
- `scripts/release/release_protection.json`
- `scripts/release/release_protection.py`
- `scripts/release/post_fix_gate.py`

**测试：整份删除**（每一条都依赖被删的字段或被删的文件）：
- `tests/guards/test_release_manifests_conform.py`（`test_三把钥匙只引用唯一发布保护权威源`、`test_产品自动修复范围不触发布保护路径`）
- `tests/journeys/_release_fix_stub.py`（只为被删的 `fix_executor` 存在的桩）
- `tests/journeys/test_release_journey_p0_pause.py` 里的 `test_real_keys_reject_complete_protection_projection_without_dirtying_branch`（测的正是被删的路径闸）

**测试：改**：
- `tests/contracts/test_release_adapter_contract.py`：`test_release_key_enters_the_common_engine_with_only_current_stages` 断言 `manifest.protection_source == PROTECTION_SOURCE`；字段删除后 `ReleaseAdapterManifest` 上不再有这个属性，且真实 manifest 在这一步的 `model_validate` 就会先因为多余字段报错。删掉这条断言和 `PROTECTION_SOURCE` 常量。
- `tests/guards/test_release_nuitka_argv_parity.py`：`test_diagnose_and_fix_point_at_the_skill` 断言 `"${RELEASE_PLUGIN_DIR}/fix_dispatch.py" in v2["fix_executor"]`，删掉这条断言（或整个测试，视其余断言是否还有意义）。
- `tests/journeys/_release_journey.py`：删 `with_stub_fix_executor`（复制 manifest 并替换 `fix_executor`）和 `load_path_hard_deny_probes`（跑 `release_protection.py path-hard-deny-probes --json`）两个 helper。
- `tests/journeys/test_release_journey_e2e.py`：`test_release_p2_regenerates_only_derived_consumer` 里 "`release_protection.json` 出包前后不变" 的断言删掉；`test_release_p1_frozen_import_is_fixed_then_repackaged` 用 `with_stub_fix_executor` 且断言 ledger 里有 `action_kind=="fix"` 与 `action_kind=="post_fix_gate"` 的 attempt，这条测试要删或整条重写（P1 现在是"引擎写简报、驱动 agent 自己改代码提交"，不再有可以自动跑的 fix_executor）。

**不用改，但会因为字段删除而由红转绿**（现在测的是"真实 manifest 能通过引擎校验"，字段删除前会被四个多余字段挡住）：
- `tests/contracts/test_release_key_verification_wire.py` 的 `test_current_product_keys_pass_the_skill_preflight`
- `tests/guards/test_release_nuitka_argv_parity.py` 里靠 `_key()` 的另外几条（`test_parrot_nuitka_argv_unchanged`、`test_hedgehog_nuitka_argv_unchanged`、`test_every_key_validates_against_the_skill_contract`）

**其他**：`pyrefly-baseline.json` 第 1172 行是 `scripts/release/post_fix_gate.py` 的类型检查白名单项，删这个文件后这一行要删。`.worktrees/2026-07-07-douyin-banner-regenerate/` 与 `.worktrees/yellowtail/` 下各有一份 `hedgehog`/`parrot` release manifest 的副本，也带着同样四个字段；这两个是任务分支自己的 worktree，各自 merge 回来时按同一份改法处理，不必现在单独动。

### `~/xiaohuangya`

**Release manifest**，删除以下四个字段：
- `scripts/release/adapters/duck.release-adapter.json`

**整个删除**：
- `scripts/release/release_protection.json`
- `scripts/release/release_protection.py`
- `scripts/release/post_fix_gate.py`

**测试：整份删除**：
- `tests/local_agent/test_release_protection.py`（`test_受保护_matcher_漏报被指出`、`test_损坏规则源拒绝读取`、`test_规则源的_json_cli_只输出可消费规则`、`test_路径闸探针覆盖已跟踪与新建文件`，全都测 `release_protection.py`）
- `tests/local_agent/test_post_fix_gate.py`（`test_业务模块引入裸日志入口时语义闸拒绝`、`test_业务模块使用共享日志入口时语义闸放行`、`test_规则源声明的每个语义闸都有执行器`、`test_未知语义闸会成为_p0_失败`，全都测 `post_fix_gate.py`）
- `tests/guards/test_release_manifests_conform.py`（与 agentflow 同名文件，`PRODUCTS = ("duck",)`；两条测试同样依赖 `protection_source`/`editable_paths`）

**其他**：`pyrefly-baseline.json` 第 1112 行是 `post_fix_gate.py` 的类型检查白名单项，随文件删除一并删掉。`TESTING.md` 第 38 行把 `release_protection.json` 列为测试要读的 release 台账之一，字段和文件删除后这一行要删。`docs/design/2026-08-19-xiaohuangya-repo-split.md` 第 130 行的分仓设计记录点了 `post_fix_gate.py`、`release_fix_executor.py`（`scripts/release/` 下实际并不存在这个文件名）和 "duck adapter 的 `editable_paths`"；这份文件记的是分仓当时的决定，是否要跟着改由该仓库自己判断。`.worktrees/issue-876/` 下有一份 `duck.release-adapter.json` 的副本，同样带着四个字段，随该任务分支合并时一起处理。

## 怎么迁

每个仓库三步：

1. 从每份 `*.release-adapter.json` 里删掉 `editable_paths`、`protection_source`、`post_fix_gate`、`fix_executor` 四个键（agentflow 改 `hedgehog.release-adapter.json` 与 `parrot.release-adapter.json`；xiaohuangya 改 `duck.release-adapter.json`）。改完用 `uv run --with 'pydantic>=2' python <exe-release skill 的 scripts>/verify_key.py --adapter <manifest> --repo-root <repo>` 或直接 `<release> init --manifest <manifest>` 验一遍——不再报 "Extra inputs are not permitted" 就说明四个字段真的清干净了。
2. 删除 `scripts/release/release_protection.json`、`scripts/release/release_protection.py`、`scripts/release/post_fix_gate.py` 三个文件（xiaohuangya 同名三个文件）。
3. 按上面"哪些产物失效"里列的清单，删除或改写对应的测试文件，再删两个仓库各自 `pyrefly-baseline.json` 里那一条 `post_fix_gate.py` 的白名单项；xiaohuangya 另外删 `TESTING.md` 第 38 行。

判断依据说不清、需要人读代码定夺的只有一处：`docs/design/2026-08-19-xiaohuangya-repo-split.md` 第 130 行是否要跟着改——这是一份记录历史决定的设计文档，不在这份说明的强制范围内。
