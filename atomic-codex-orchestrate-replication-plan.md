# Codex Orchestrate 原子级复刻计划

日期：2026-05-24

本文档定义把 `plugin/` 中 Claude Code orchestrated plugin 原子级复刻到 Codex 的交付合同。`plugin/` 是唯一行为蓝本；旧 `codex/` 目录和已安装旧 runtime 只作为归档，不参与当前设计。

## 1. 复刻原则

- 不重新发明 workflow。`plugin/` 已经有的 phase、gate、state、review、repair、budget、hook、test，都要在 Codex 侧有对应物。
- 不做总结版 agent。Claude agent 正文要迁移成 Codex TOML 的 `developer_instructions`，只替换 host primitive、模型、路径和工具字段。
- 不凭空加蓝本不存在的能力面。Claude plugin 没有 connector/MCP 定义，Codex manifest 不声明空占位。
- 不把“安装成功”当成复刻成功。必须验证 source、plugin cache、custom agent runtime 三者 parity，并跑测试。
- 不用旧 Codex runtime 限制能力。旧 `codex/` 已归档，新系统从 `codex-orchestrate/` 独立生效。

## 2. 交付形态

```text
codex-orchestrate/
  .codex-plugin/plugin.json
  skills/
  agents/
  hooks/
  scripts/
  state-schema/
  build/
  tests/
  installers/
```

| 目录 | 复刻对象 | Codex 责任 |
| --- | --- | --- |
| `skills/` | `plugin/skills/` | 六个 orchestrate phase skill + `codex-review` skill |
| `agents/` | `plugin/agents/*.md` | Codex custom agent TOML，保留原 agent 纪律和 return contract |
| `hooks/` | `plugin/hooks/` | Codex hook event + dispatcher + 原 gate 逻辑 |
| `scripts/` | `plugin/scripts/` | state、summary、learning、cleanup、review、dispatch |
| `state-schema/` | `plugin/state-schema/` | workflow、execution、dispatch、pack return、review result schema |
| `build/` | `plugin/build/` | template / resolver 架构，生成 Codex 原生片段 |
| `tests/` | plugin test categories | manifest、agent、dispatch、hook、review lane、installer test |
| `installers/` | Claude plugin install 语义 | user-level install / uninstall / parity verify |

## 3. Claude 配置到 Codex 配置的一一对应

### 3.1 Manifest

| Claude plugin 字段 | Codex 对应 | 处理 |
| --- | --- | --- |
| `.claude-plugin/plugin.json:name` | `.codex-plugin/plugin.json:name` | native |
| `version` | `.codex-plugin/plugin.json:version` | native |
| `description` | manifest `description` + `interface.shortDescription/longDescription` | native |
| `author` | manifest `author` + `interface.developerName` | native |
| `repository` | manifest `repository` | native |
| `license` | manifest `license` | native |
| `keywords` | manifest `keywords` | native |
| implicit skill loading | `skills = "./skills/"` | native |
| hook loading | `hooks/hooks.json` | native |
| plugin root env | `PLUGIN_ROOT` | Codex native env |
| plugin data env | `PLUGIN_DATA` | Codex native env |
| marketplace visibility | `.agents/plugins/marketplace.json` | repo-local marketplace |
| connectors | 无对应声明 | blueprint 没有，不声明空字段 |
| MCP servers | 无对应声明 | blueprint 没有，不声明空字段 |

### 3.2 Skill

| Claude skill 行为 | Codex 对应 | 处理 |
| --- | --- | --- |
| `SKILL.md` frontmatter `name` | Codex `SKILL.md` frontmatter `name` | native |
| `description` trigger | Codex progressive disclosure trigger | native |
| `references/` | Codex skill `references/` | native |
| `scripts/` | Codex skill `scripts/` | native |
| phase skill load | installed Codex skill name | substitute |
| `.claude/multi-model-workflow` | `.codex/multi-model-workflow` | substitute |

### 3.3 Agent

| Claude agent 字段 / 语义 | Codex 字段 / 机制 | 处理 |
| --- | --- | --- |
| frontmatter `name` | TOML `name` | native |
| frontmatter `description` | TOML `description` | native |
| markdown body | TOML `developer_instructions` | native |
| `model: sonnet` | `gpt-5.3-codex` / `xhigh` | substitute，用于普通 worker、普通 explorer、docs worker |
| 高级实现 / 根因 / plan writer | `gpt-5.5` | substitute |
| 高级 worker / explorer effort | `high` | native |
| plan/root-cause effort | `xhigh` | native |
| `tools: Read` | `sandbox_mode = "read-only"` + shell read tools | substitute |
| `tools: Edit/Write` | `sandbox_mode = "workspace-write"` + `apply_patch` + hook guard | substitute |
| `tools: Bash` | Codex unified exec + sandbox / permission / hooks | substitute |
| `tools: Skill` | `[[skills.config]]` | native |
| `skills: tdd/diagnose/...` | TOML `skills.config` path | native |
| agent registration | `~/.codex/config.toml` `[agents.<name>] config_file` | native；installer 必须写入托管 block，不假设裸 TOML 自动发现 |
| project memory | `.codex/multi-model-workflow/agent-memory/` + Codex memories when enabled | substitute |
| `maxTurns` | job timeout、durable return、repair-round cap | substitute |
| color / presentation | `nickname_candidates` | presentation-only |

### 3.4 Agent role defaults

| Codex agent type | 模型 | reasoning | sandbox | 预装 skills |
| --- | --- | --- | --- | --- |
| `pack_executor` | `gpt-5.3-codex` | `xhigh` | `workspace-write` | `tdd`, `diagnose`, `prototype` |
| `complex_pack_executor` | `gpt-5.5` | `high` | `workspace-write` | `tdd`, `diagnose`, `prototype`, `improve-codebase-architecture` |
| `plan_writer` | `gpt-5.5` | `xhigh` | `workspace-write` | `improve-codebase-architecture` |
| `root_cause_analyst` | `gpt-5.5` | `xhigh` | `workspace-write` | `diagnose`, `tdd` |
| `code_explorer` | `gpt-5.3-codex` | `xhigh` | `read-only` | `zoom-out` |
| `complex_code_explorer` | `gpt-5.5` | `high` | `read-only` | `zoom-out` |
| `docs_worker` | `gpt-5.3-codex` | `xhigh` | `workspace-write` | `grill-with-docs`, `triage` |

`gpt-5.4-mini` 不用于任何角色。

### 3.5 Review routing

| Review surface | Codex reviewer | 模型 | reasoning |
| --- | --- | --- | --- |
| Design Review | native `codex exec review` | `gpt-5.5` | `xhigh` |
| Plan Review | native `codex exec review` | `gpt-5.5` | `xhigh` |
| 文档 / issue hierarchy / PRD review | native `codex exec review` | `gpt-5.5` | `xhigh` |
| Pack / code / bug / direct repair review | native `codex exec review` | `gpt-5.4` | `xhigh` |
| Final / integration / release-risk review | native `codex exec review` | `gpt-5.4` | `xhigh` |
Review 不替换为 Claude Review，也不保留 Claude-only supplemental lane。所有正式和 ad-hoc review 统一走 Codex-native Review。

## 4. 无法硬复刻的地方和 Codex 替代方案

| Claude 行为 | Codex 差异 | Codex 替代方案 |
| --- | --- | --- |
| 后台 agent 派发并返回 agent id | Codex subagent API 名称和返回字段不同 | 使用 `spawn_agent({ agent_type, message })` 派发 `pack_executor` / `complex_pack_executor`，prompt 前置 `DISPATCH_ENVELOPE`，并立即记录返回的 `agent_id` |
| 给原 agent 发送修复消息 | host 可能关闭 / compact / 恢复失败 | 先 `send_input({ target, message })`，失败后 `resume_agent({ id })` 再 `send_input({ target, message })`；仍失败必须记录 exception code 并带完整 prior context replacement dispatch |
| Claude 3.6.1 的同分支串行 worker | Codex subagent 也在当前工作区执行，但 hook event 名称不同 | Codex 保持同分支、逐 Pack 严格串行；Coordinator dispatch 前创建 `.codex/multi-model-workflow/worker-active`，`guard-doc-edit.sh` 阻止 worker 修改 docs/，返回后移除 marker |
| Claude hook 条件表达式 | Codex hook matcher 语义不同，多个 hook 可能并发 | 每个 event 使用 dispatcher，脚本内部按顺序执行 gate；状态写入加 lock |
| Claude review companion job API | Codex Review 不是同一个 companion API，`codex review` 本身不暴露 resume 参数 | `scripts/review/review-lane.sh` 用 `codex exec review --json` 建立可恢复 thread，job 文件保存 `thread_id`；targeted re-review 用 `codex exec resume <thread_id>` 继续 baseline review session；找不到 baseline thread 直接失败 |
| Claude agent discovery | Codex sub-agent role 由 `~/.codex/config.toml` 注册 | installer 复制 TOML 后写入托管 `[agents.<name>]` block，verify 阶段检查 `config_file`、description、nickname |
| `maxTurns` | Codex agent TOML 没有同名字段 | job timeout、durable return、repair cap |
| project memory | Codex memory 可开关，不可作为唯一状态 | workflow state / learnings / run summaries 是事实源，memory 只是附加上下文 |
| tool hard allow/deny | Codex 工具由 sandbox、permission、hooks、instructions 共同控制 | read-only sandbox、workspace-write sandbox、protected path hook、permission policy |

## 5. Codex 最新功能使用点

截至 2026-05-24，本复刻使用这些 Codex 侧能力：

| 能力 | 用法 |
| --- | --- |
| Codex plugins | `.codex-plugin/plugin.json` + marketplace entry |
| Plugin hooks | `hooks/hooks.json` |
| Skills | `skills/<name>/SKILL.md` |
| Custom agents | `agents/*.toml` + `~/.codex/config.toml` `[agents.<name>] config_file`，含 `model`、`model_reasoning_effort`、`sandbox_mode`、`skills.config` |
| Multi-agent tools | interactive 场景使用 subagent dispatch / resume / wait |
| `spawn_agent` / `send_input` / `resume_agent` | worker 派发、原 worker 修复、host 恢复 |
| Native `codex exec review` / `codex exec resume` | `review-lane.sh` 统一模型路由、job 文件和 `thread_id` continuity |
| Hook manifest validation | installer / parity verifier 检查 `hooks/hooks.json`、feature flags、plugin cache parity；安装后由 Codex hook trust 流程确认生效 |
| Feature validation | `codex doctor`、feature check、strict config 检查 |
| Permission policy | publish、destructive command、protected docs/budget path gate |

## 6. State 合同

| 文件 | 内容 |
| --- | --- |
| `.codex/multi-model-workflow/active-run-id` | 当前 run id |
| `scope-<run_id>.md` | source artifacts、editable artifacts、out of scope |
| `workflow-state-<run_id>.json` | route、cursor、budget、disposition、direction check、mutation log |
| `execution-state-<run_id>.json` | plan / pack queue、agent id、commit sha、worker verdict、repair round |
| `pack-returns/<run_id>/<pack_id>.json` | worker durable return |
| `review-prompts/<gate>.md` | review prompt |
| `review-results/<gate>.md` | review result |
| `learnings/` | 可复用 workflow learning |
| `run-summaries/` | closing summary |

所有 state mutation 通过 `scripts/state.sh` 或 hook 脚本完成，写入时使用 lock。

## 7. Phase 复刻合同

| Phase | 必须保留的能力 |
| --- | --- |
| `orchestrate-workflow` | Entry Gate、七 route、Infrastructure、resume、closing、hard gates |
| `orchestrate-discovery` | 产品讨论、design doc、grill-with-docs、Design Review、issue splitting |
| `orchestrate-plan-writing` | Plan Entry Gate、plan_writer dispatch、Task Pack inventory、budget 初始化、Plan Review、plan repair |
| `orchestrate-execution` | plan/pack queue、worker dispatch、durable return、open item、checkpoint、Plan Implementation Review、disposition、repair、release gate |
| `orchestrate-final-review` | intent coverage、cross-pack regression、tail sweep、release-risk supplement、business report |
| `orchestrate-multi-pr-merge` | PR inventory、conflict discovery、RCA、repair、integration review、merge order |
| `codex-review` | ad-hoc independent review，不消耗 workflow budget |

## 8. Test / Verification 合同

必须通过：

```bash
bash codex-orchestrate/build/build.sh --check --plugin-dir codex-orchestrate
bash codex-orchestrate/scripts/run-all-tests.sh
bash codex-orchestrate/scripts/verify-maturity.sh
uv run --with pyyaml --no-project python ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py codex-orchestrate
```

安装后必须通过：

```bash
bash codex-orchestrate/installers/install.sh --user --apply
bash codex-orchestrate/installers/verify-runtime-parity.sh --user
diff -qr codex-orchestrate ~/.codex/plugins/cache/multi-model-workflow/codex-orchestrate/3.6.1
for f in codex-orchestrate/agents/*.toml; do
  diff -q "$f" "$HOME/.codex/agents/$(basename "$f")"
done
python3 codex-orchestrate/installers/sync-agent-config.py verify \
  --config-file "$HOME/.codex/config.toml" \
  --source-agents-dir codex-orchestrate/agents \
  --target-agents-dir "$HOME/.codex/agents"
```

## 9. Work Packs

### Pack 1：Manifest / Source Scaffold

交付 `codex-orchestrate/`、manifest、marketplace、README、override rules。验收：无旧 `codex/` 依赖，无空 connector/MCP 占位，plugin validator pass。

### Pack 2：State / Schema

交付 `state.sh`、lock、workflow/execution/dispatch/pack/review schema、transition matrix。验收：状态测试、非法 transition、duplicate dispatch、disposition evidence、schema validation 全部通过。

### Pack 3：Hooks

交付 Codex hook dispatcher、dispatch gate、review gate、budget tracker、doc edit guard、push guard、subagent start/stop。验收：fixture-based hook tests 通过，不依赖 hook 并发顺序。

### Pack 4：Review Lane

交付 `review-lane.sh`、Codex Review companion、job API。验收：文档 review 走 `gpt-5.5/xhigh`，代码 review 走 `gpt-5.4/xhigh`，baseline job 记录 Codex `thread_id`，targeted re-review 必须通过 `codex exec resume <thread_id>` 继续同一 review session。

### Pack 4A：Worker Dispatch

交付 Codex subagent dispatch / resume 合同、`worker-active` marker、`pack-return-v1.json` 和 hook/state 对接。验收：worker prompt 携带 `DISPATCH_ENVELOPE`，`agent_id` 被持久化，repair 通过 `send_input` / `resume_agent` 回到原 worker，所有 Task Pack 严格串行并直接在 Coordinator 分支提交。

### Pack 5：Build / Template

交付 template/resolver system。验收：`build.sh --check` 能抓 drift，`--apply` 幂等。

### Pack 6：Agents

交付七类 Codex TOML agent 和 `persona.md`。验收：模型、sandbox、skills.config、developer_instructions、return contract 全部存在，内容来自 Claude agent 正文迁移而非摘要。

### Pack 7：Skills

交付六 phase skill + ad-hoc review skill。验收：七 route、phase precondition、output、review gate、verdict、repair loop 全部在 Codex 语义下成立。

### Pack 8：Install / Parity

交付 install、uninstall、verify-runtime-parity、agent config registration。验收：dry-run 可审计，apply 只安装本插件管理文件并写入托管 `[agents.<name>] config_file` block，uninstall 只删除本插件管理文件和托管 config block，parity / config drift 会失败。

### Pack 9：Smoke / Cutover

交付 formal、bug、multi-PR、hotfix、quickfix、spike、maintenance fixtures 和 cutover/rollback 命令。验收：smoke 覆盖 state、hook、dispatch、review、repair、cleanup。

## 10. Cutover

1. 跑 build / tests / maturity / plugin validation。
2. Source 覆盖审计通过后再安装 `codex-orchestrate`；如果当前任务要求暂缓安装，停在 source 层，不提前 cutover。
3. 验证 source/cache/agent parity。
4. 新开 Codex session，review/trust plugin hook definitions，确认 SessionStart 注入新 plugin identity，并确认 `spawn_agent` role list 出现 `pack_executor`、`complex_pack_executor`、`code_explorer` 等新 agent type。
5. 在 fixture repo 跑 smoke。
6. 通过后把旧 runtime 维持归档状态，不恢复旧 `.agents/skills/orchestrate-*`。

## 11. 完成标准

复刻完成必须同时满足：

- `plugin/` 的 skill、agent、hook、script、schema、build、test 类别没有未解释缺口；
- Codex 无法硬复刻的 host 行为都有显式、可测试、可阻断的替代方案；
- source、plugin cache、custom agent runtime parity 机械验证通过；
- review lane 按文档/代码模型分流；
- `gpt-5.4-mini` 不出现在任何正式执行路径；
- 旧 `codex/` runtime 不参与新系统运行。
