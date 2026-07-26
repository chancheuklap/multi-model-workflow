# AGENTS.md

## 仓库范围

本仓库发布同一套多模型开发编排的四个单宿主实现。四个实现共享产品语义，但宿主接线、状态目录、角色派发和部分文件布局各自独立；运行时不得互相探测或调用。

| 宿主 | 活跃目录 | 发布入口 | 状态目录 | 任务 worktree | 角色执行后端 |
| --- | --- | --- | --- | --- | --- |
| Claude Code | `plugin/` | `plugin/.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` | `.claude/multi-model-workflow/` | `.claude/worktrees/` | Codex CLI 工人和宿主 sub-agent 审者 |
| Factory Droid | `droid-plugin/` | `droid-plugin/.factory-plugin/plugin.json`、`.factory-plugin/marketplace.json` | `.factory/multi-model-workflow/` | `.factory/worktrees/` | `droid exec` 和 Custom Droids |
| pi | `pi-plugin/` | `pi-plugin/package.json` | `.pi/multi-model-workflow/` | `.pi/worktrees/` | pi-subagents 注册角色和动态 workflows |
| Cursor | `cursor-plugin/` | `cursor-plugin/.cursor-plugin/plugin.json`、根 `.cursor-plugin/marketplace.json` | `.cursor/multi-model-workflow/` | `.cursor/worktrees/`（工人）；任务 wt 常由 UI 悬空创建后 `mmw task adopt` | Cursor Task（插件 `agents/`） |

`archive/plugin-v1/` 是冻结归档，不参与当前行为判断、构建或测试；没有明确指令时不修改。

## 当前工作流

各宿主的 `state-schema/routes.json` 固化阶段、结论词、审闸和场景预设，`scripts/mmw.sh` 是统一命令入口。

| 场景 | 阶段 |
| --- | --- |
| `small-change` | build → final review → closing |
| `bug` | investigate → build → final review → closing |
| `develop` | 可选 wayfind → investigate → propose → design → to-issue → plan → plan review → build → final review → package → closing |
| `merge` | 不创建任务 worktree，单独处理业务意图与实现冲突 |

- 开始或续跑正式任务时，先运行对应宿主的 `bash <plugin>/scripts/mmw.sh where`，再按它返回的 `load`、`do`、`then` 行动。
- propose 和 design 承担人机对齐。设计只接受用户执行 `/approve-design` 过门；口头同意不推进。
- 计划审和终审是模型闸。终审按场景和风险分档：small-change/bug 用一个独立 GPT 审者覆盖两基线；develop 无 capable plan 且 diff 不超过阈值时用两个跨模型审者，其余及数据不全时用四个。package 有目标安装包时，开发模式功能测试和安装后测试仍需负责人确认。
- 状态、接力单、审查 brief、执行账本和进度板只认对应宿主的状态目录。

## 事实源

判断当前行为时按以下顺序核对同一宿主：

1. manifest 或 package 配置。
2. `state-schema/*.json`。
3. `scripts/`、`hooks/`、pi 的 `extensions/` 与 `workflows/`。
4. `scripts/tests/` 和 `build/tests/`。
5. 运行时 Markdown 源码。

不要假设四个镜像逐字一致。共同业务行为发生变化时逐个检查四个镜像；宿主专属路径、工具名、生命周期和派发后端不得复制成兼容分支。

仓库只维护 `AGENTS.md`、`CLAUDE.md` 和 `TESTING.md` 三份根文档。不要新增 README、独立架构文档、设计文档、调查报告、计划或审查记录；长期项目规则写入本文件，运行行为写入对应 runtime 源码和测试。

以下 Markdown 是 plugin 会直接加载或生成的运行时源码，不属于仓库说明文档：

- Claude Code：`plugin/agents/`、`plugin/commands/`、`plugin/skills/`、`plugin/build/fragments/`。
- Droid：`droid-plugin/droids/`、`droid-plugin/commands/`、`droid-plugin/skills/`、`droid-plugin/build/fragments/`。
- pi：`pi-plugin/agents-roster/`、`pi-plugin/prompts/`、`pi-plugin/skills/`、`pi-plugin/build/fragments/`。
- Cursor：`cursor-plugin/agents/`、`cursor-plugin/commands/`、`cursor-plugin/skills/`、`cursor-plugin/build/fragments/`。

## 修改规则

- 改任一宿主前先读该宿主的 `skills/orchestrate/SKILL.md`、它指向的完整 reference、对应脚本和测试。
- 编写、修改或审查测试前先读根目录 `TESTING.md`，按其中的本仓库分层、接缝、权威源和门控执行。
- 共用片段只改各宿主的 `build/fragments/*.md`，然后对该宿主运行 `build/build.sh --apply` 和 `--check`；带 `<!-- BEGIN: ... -->` 锚点的生成区不得手改。
- 每个宿主的两份 `task-pack.md` 是实体副本，必须保持一致并通过 `test_shared_refs_sync.sh`。
- pi 的 GPT 角色公共提示词只改 `pi-plugin/agents-roster/_fragments/`，随后运行 `python3 pi-plugin/scripts/render_agent_prompts.py`；Claude provider 角色不经过该渲染器。
- pi 的动态 workflow 以 `pi-plugin/workflows/*.workflow.js` 为源；修改后运行 `bash pi-plugin/workflows/install-workflows.sh` 生成 `dist/*.json`，再用 `--check` 验证。
- Claude Code 版本同时更新 plugin manifest、marketplace 中的 plugin 版本和 marketplace 根版本。Droid 版本同时更新 plugin manifest 与 marketplace。pi 版本以 `pi-plugin/package.json` 为准。Cursor 版本同时更新 `cursor-plugin/.cursor-plugin/plugin.json` 与根 `.cursor-plugin/marketplace.json`。
- Cursor 本地试装是实体拷贝，不是软链。改 `cursor-plugin/` 后必须跑 `bash cursor-plugin/scripts/install-local-surface.sh`：`rsync` 同步到 `~/.cursor/plugins/local/multi-model-workflow-cursor/`，合并用户级 `~/.cursor/hooks.json`（保留非 MMW 条目），并把 `commands/*.md` 拷到 `~/.cursor/commands/`。不跑则本机仍用旧拷贝；hooks/MCP/slash 以该脚本写出的生效面为准。
- 不用旧宿主残留、兼容目录或静默默认值掩盖错误。脚本异常必须返回非零或留下结构化告警。

## Git 与安全

- 正式改动在独立 worktree 完成；合回主分支使用 `git merge --no-ff`，禁止 `git merge --squash`。
- 写码工人不得修改 `docs/`；计划工人只可修改自己的 plan 和对应 issue，边界由 `worker verify`、`worker status` 或 `plan-check` 核验。
- 本地 commit 和本地 merge 可自主执行。`git push`、远端 PR 合并和部署必须由用户批准；无交互界面时红线动作失败关闭。
- 子代理输出不是事实源。路径、行号、计数、提交和测试结论写入交付前必须由主线程复核。

## 构建与测试

四个宿主都要通过片段漂移检查和完整 shell 测试：

```bash
for host in plugin droid-plugin pi-plugin cursor-plugin; do
  bash "$host/build/build.sh" --check || exit 1
  bash "$host/build/tests/test_build.sh" || exit 1
  for test_file in "$host"/scripts/tests/test_*.sh; do
    bash "$test_file" || exit 1
  done
done
```

Release 合同的 Python 测试要覆盖四个宿主：

```bash
for host in plugin droid-plugin pi-plugin cursor-plugin; do
  uv run --with pytest --with pydantic pytest \
    "$host/scripts/tests/test_release_contracts.py" \
    "$host/scripts/tests/test_release_script_assembler.py" || exit 1
done
```

pi 还要通过两道生成物同步检查：

```bash
python3 pi-plugin/scripts/render_agent_prompts.py --check
bash pi-plugin/workflows/install-workflows.sh --check
```

提交前运行 `git diff --check`，并用 `python3 -m json.tool` 校验本次修改涉及的 JSON。
