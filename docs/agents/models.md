# Models

落地流水线的角色到宿主、模型、思考强度的映射。安装位置：消费仓库的 `docs/agents/models.md`（与 `issue-tracker.md` 同目录）。`landing-orchestrator` 技能运行时现读这张表；改表即生效，不改技能。

左列六个角色是固定的，顺序与名字都不能改；右三列随时可改。

| 角色 | 宿主 kind | 模型串 | 思考强度 |
| --- | --- | --- | --- |
| 编排者 | claude | opus | medium |
| 规划者 | claude | opus | high |
| 初级工人 | cursor | cursor-grok-4.6-high | high |
| 高级工人 | grok | grok-4.6 | xhigh |
| 复验者 | claude | opus | high |
| 升级顾问 | claude | fable | medium |

## 各列怎么填

- **宿主 kind**：`herdr agent start --kind` 接受的值（本机 `herdr agent start --help` 列出）。编排者、规划者、复验者、升级顾问必须与编排者所在宿主同 kind——它们是编排会话内的 subagent（ADR 0020）。
- **模型串**：该宿主 CLI 的 `--model` / `-m` 接受的字面值。cursor 的模型串自带强度（`cursor-grok-4.6-high`，`cursor-agent --list-models` 可查）；grok 用 `grok models` 查；claude 用别名 `opus` / `fable` / `sonnet`。
- **思考强度**：`low` / `medium` / `high` / `xhigh` / `max` 之一。cursor 这一列只供人读，实际强度以模型串为准。

## 机器读法

`python3 <landing-orchestrator 技能目录>/scripts/models.py <这个文件>` 把表解析成 JSON，键是角色的英文名：`orchestrator`、`planner`、`junior-worker`、`senior-worker`、`verifier`、`advisor`。缺角色、缺列、强度不在集合内都非零退出。
