# codex/ agents.overrides.md

## 目录职责

`codex/` 存放 Codex user-level runtime 的安装和同步源码：

- `codex/agents/*.toml`：custom `agent_type` 模板；
- `codex/agents/sync-agents.sh`：复制 agent templates，并可更新 `~/.codex/config.toml`；
- `codex/skills/install-orchestrate-runtime.sh`：安装六个 Orchestrate skills 到 user-level 或 target repo；
- `codex/hooks/*.sh`、`codex/hooks/hooks.json`：Codex hook source 和安装器。
- `codex/reviewers/*.sh`：外部 reviewer runner，由 Orchestrate review lane 调用。

## 当前 managed agent_type

| agent_type | 文件 | 职责 |
| --- | --- | --- |
| `plan_writer` | `codex/agents/plan-writer.toml` | reviewed design + issue hierarchy → implementation plan |
| `coding_worker` | `codex/agents/coding-worker.toml` | normal Task Pack / clear repair |
| `complex_coding_worker` | `codex/agents/complex-coding-worker.toml` | high-risk Task Pack / migration / billing / permission / runtime / shared contract |
| `code_reviewer` | `codex/agents/code-reviewer.toml` | baseline design / plan / pack / final / integration review |
| `release_reviewer` | `codex/agents/release-reviewer.toml` | release-risk supplement |
| `code_explorer` | `codex/agents/code-explorer.toml` | narrow read-only investigation |
| `complex_code_explorer` | `codex/agents/complex-code-explorer.toml` | multi-module read-only investigation |
| `root_cause_analyst` | `codex/agents/root-cause-analyst.toml` | bug / repair truncation / Multi-PR systemic conflict investigation |
| `docs_worker` | `codex/agents/docs-worker.toml` | low-risk docs cleanup |

## 编辑规则

- 改 agent TOML 时同步 `sync-agents.sh` managed registry 和 `codex/agents/README.md`。
- 新增 agent_type 必须有 template、registry entry、README row，并能被 `--update-config` 写入 `~/.codex/config.toml`。
- 不在 agent TOML 中引用 custom agent 看不到的 Orchestrate reference；需要 reference 时由 parent dispatch 提供路径或内容。
- Review agent 保持只读。Worker / analyst 不 commit、merge、push 或 PR。
- 改 hooks 时同步 `install-hooks.sh` copy list 和验证命令。
