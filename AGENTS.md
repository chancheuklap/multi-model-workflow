# AGENTS.md

# Codex 根规则

- Always think out of the box. 文档是讨论结果和方案设计，不是你的上限；目标是把实用、完整、能落地的系统实现出来。
- 用户不是代码工程师。沟通时默认面向项目负责人，先讲结论、影响和证据，再讲必要技术细节。
- 改代码或工作流时，同步维护对应目录的 `agents.overrides.md`。
- 只要下一步明确就继续做，不把显然该做的动作再推回给用户。
- 修根因，不修表面；不要用 workaround 掩盖系统缺口。

## 当前权威

本仓库同时保存 Claude Code 蓝本和 Codex 原子复刻，但两者边界必须清楚：

| 层级 | 路径 | 作用 |
| --- | --- | --- |
| Claude blueprint | `plugin/` | Claude Code orchestrated plugin 的行为蓝本 |
| Codex source | `codex-orchestrate/` | Codex 原生原子复刻源码真相 |
| Codex hooks source | `codex-orchestrate/hooks/hooks.json` 和 `codex-orchestrate/hooks/` | plugin hook manifest 与 hook 脚本 |
| Codex plugin marketplace | `.agents/plugins/marketplace.json` | repo-local Codex marketplace |
| Codex plugin runtime target | `~/.codex/plugins/cache/multi-model-workflow/codex-orchestrate/0.1.0/` | 完成 source 审计后安装到 Codex 的目标缓存路径；未安装时不得把它当作当前行为依据 |
| Codex custom-agent runtime | `~/.codex/agents/*.toml` | Codex 实际可调用的 managed agents |
| Legacy Codex archive | `archive/2026-05-24-codex-pre-atomic/codex/` | 只做审计参考，不作为当前行为依据 |

不要使用旧 `codex/` 目录、旧 `.agents/skills/orchestrate-*` runtime、或旧 Codex V1 文档来约束当前实现。

## 当前运行形态

六个 phase skill：

| Skill | 职责 |
| --- | --- |
| `orchestrate-workflow` | Entry Gate、route、phase handoff、closing |
| `orchestrate-discovery` | 模糊输入到 reviewed design |
| `orchestrate-plan-writing` | reviewed design + issue hierarchy 到 reviewed plan |
| `orchestrate-execution` | Task Pack dispatch、review、repair、release gate |
| `orchestrate-final-review` | final intent review、tail sweep、business report |
| `orchestrate-multi-pr-merge` | 多 PR 冲突发现、修复、集成审查、顺序合并 |

Managed Codex agents：

| agent_type | 模型 | reasoning | 职责 |
| --- | --- | --- | --- |
| `pack_executor` | `gpt-5.3-codex` | `xhigh` | 普通 Task Pack / repair |
| `complex_pack_executor` | `gpt-5.5` | `high` | 高风险实现、迁移、权限、运行时、共享合同 |
| `plan_writer` | `gpt-5.5` | `xhigh` | implementation plan |
| `root_cause_analyst` | `gpt-5.5` | `xhigh` | 未知根因 / systemic conflict |
| `code_explorer` | `gpt-5.3-codex` | `xhigh` | 小范围只读调查 |
| `complex_code_explorer` | `gpt-5.5` | `high` | 多模块只读调查 |
| `docs_worker` | `gpt-5.3-codex` | `xhigh` | 低风险文档整理 |

Review routing：

| Review kind | 模型 | reasoning |
| --- | --- | --- |
| Design / Plan document review | `gpt-5.5` | `xhigh` |
| Code / pack / bug / direct repair / final / integration / release-risk review | `gpt-5.4` | `xhigh` |

`gpt-5.4-mini` 不用于本工作流。

## 修改流程

1. 对照 `plugin/` 的实际文件理解行为蓝本，不轻信旧文档。
2. 修改 `codex-orchestrate/` source。
3. 同步对应目录的 `agents.overrides.md`。
4. 运行 source 级检查：结构覆盖、Codex native primitive、build check、必要的脚本语法检查。
5. 只有 source 覆盖审计完成且当前任务允许安装时，才安装到 user-level runtime；用户要求暂缓安装时停在 source 层。
6. 安装后验证 source/cache/custom-agent parity。

常用命令：

```bash
bash codex-orchestrate/tests/run-all-tests.sh
bash codex-orchestrate/build/build.sh --check --plugin-dir codex-orchestrate
bash codex-orchestrate/installers/install.sh --user --apply
bash codex-orchestrate/installers/verify-runtime-parity.sh --user
diff -qr codex-orchestrate ~/.codex/plugins/cache/multi-model-workflow/codex-orchestrate/0.1.0
for f in codex-orchestrate/agents/*.toml; do
  diff -q "$f" "$HOME/.codex/agents/$(basename "$f")"
done
python3 codex-orchestrate/installers/sync-agent-config.py verify \
  --config-file "$HOME/.codex/config.toml" \
  --source-agents-dir codex-orchestrate/agents \
  --target-agents-dir "$HOME/.codex/agents"
```

## 不合格信号

- 只改 source，没有安装或验证 runtime parity。
- 重新建立 `.agents/skills/orchestrate-*`。
- 从归档 `codex/` 复制旧 runtime 行为。
- 只复制 `~/.codex/agents/*.toml`，没有注册 `[agents.<name>] config_file`。
- review 默认走 Claude，而不是 native Codex Review。
- 文档 review 和代码 review 使用同一模型策略。
- 使用 `gpt-5.4-mini`。
- 只说文件复制成功，不验证 hook / state / dispatch / review lane。
