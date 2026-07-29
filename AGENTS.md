# AGENTS.md

## 仓库范围

本仓库是同一套多模型开发编排的四个单宿主实现：共享产品语义，接线、状态目录、派发后端各自独立；运行时不得互相探测或调用。

| 宿主 | 源码目录 | 发布入口 | 状态目录 | 任务 worktree | 角色执行后端 |
| --- | --- | --- | --- | --- | --- |
| Claude Code | `plugin/` | `plugin/.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` | `.claude/multi-model-workflow/` | `.claude/worktrees/` | Codex CLI 工人 + 宿主 sub-agent 审者 |
| Factory Droid | `droid-plugin/` | `droid-plugin/.factory-plugin/plugin.json`、`.factory-plugin/marketplace.json` | `.factory/multi-model-workflow/` | `.factory/worktrees/` | `droid exec` + Custom Droids |
| pi | `pi-plugin/` | `pi-plugin/package.json` | `.pi/multi-model-workflow/` | `.pi/worktrees/` | pi-subagents + 动态 workflows |
| Cursor | `cursor-plugin/` | `cursor-plugin/.cursor-plugin/plugin.json`、根 `.cursor-plugin/marketplace.json` | `.cursor/multi-model-workflow/` | `.cursor/worktrees/`（任务 wt 常 UI 悬空创建后 `mmw task adopt`） | Cursor Task + `~/.cursor/agents` |

`archive/plugin-v1/` 冻结归档：不参与行为判断、构建或测试；无明确指令不改。

## 当前工作流

阶段、结论词、审闸、场景预设以各宿主 `state-schema/routes.json` 为准；统一入口 `scripts/mmw.sh`。

| 场景 | 阶段 |
| --- | --- |
| `small-change` | build → final review → closing |
| `bug` | investigate → build → final review → closing |
| `develop` | 可选 wayfind → investigate → propose → design → to-issue → plan → plan review → build → final review → package → closing |
| `merge` | 不建任务 worktree；单独处理意图与实现冲突 |

- 正式任务先跑该宿主 `bash <源码目录>/scripts/mmw.sh where`（Cursor 本机也可用引擎根下 `mmw.sh`），按 `load` / `do` / `then` 行动。
- 设计只认 `/approve-design`；口头同意不过门。计划审与终审是模型闸（终审分档见 routes / runtime-contract）。package 有目标安装包时，功能测试与安装后测试仍需负责人确认。
- 状态、接力单、brief、账本、进度板只认该宿主状态目录。

## 事实源

同一宿主内按序核对：manifest / package → `state-schema/*.json` → `scripts/`、`hooks/`（pi 另含 `extensions/`、`workflows/`）→ `scripts/tests/`、`build/tests/` → 运行时 Markdown。

四宿主不必逐字一致；共性行为变更要四个都查。宿主专属路径、工具名、生命周期、派发后端禁止抄成兼容分支。

根文档只保留 `AGENTS.md`、`CLAUDE.md`、`TESTING.md`。勿新增 README / 架构 / 设计 / 调查 / 计划 / 审查类仓库说明。长期规则写本文件；运行行为写对应宿主 runtime 与测试。

运行时 Markdown（宿主加载或 Cursor install 后生效，不是说明文档）在各宿主 `agents|droids|agents-roster`、`commands`、`skills`、`build/fragments/`（pi 另有 `prompts/`；Cursor 源码整树在 `cursor-plugin/`，本机生效面见下）。

## 修改规则

- 改宿主前读该宿主 `skills/orchestrate/SKILL.md`、完整 reference、脚本与测试。测前读根 `TESTING.md`。
- 共用片段只改 `build/fragments/*.md`，再对该宿主 `build/build.sh --apply` 与 `--check`；锚点生成区禁手改。两份 `task-pack.md` 必须一致（`test_shared_refs_sync.sh`）。
- pi：GPT 公共提示词改 `agents-roster/_fragments/` 后跑 `render_agent_prompts.py`；workflow 改 `workflows/*.workflow.js` 后跑 `install-workflows.sh`（含 `--check`）。
- 版本：Claude 同步 plugin manifest + marketplace（含根版本）；Droid 同步 plugin + marketplace；pi 以 `package.json` 为准；Cursor 同步 `cursor-plugin/.cursor-plugin/plugin.json` 与根 `.cursor-plugin/marketplace.json`。
- **Cursor**：源码只改 `cursor-plugin/`。本机跑 `bash cursor-plugin/scripts/install-local-surface.sh` 复制到 `~/.cursor/{agents,skills,commands,rules,hooks}`，合并 `hooks.json` / `mcp.json`，引擎树落到 `~/.cursor/multi-model-workflow-engine/`（可用 `MMW_ENGINE_ROOT`）。花名册 frontmatter（`model` 含 `id[effort=…]`、`is_background`）生效；Task 只传 `subagent_type`（+prompt/background）。细合同见 `cursor-plugin/skills/orchestrate/references/control/runtime-contract.md`。改完须再 install + Reload；运行时不以 `plugins/local` 为发现面。
- 不用旧残留、兼容目录或静默默认值掩盖错误；脚本异常须非零退出或结构化告警。

## Git 与安全

- 正式改动在独立 worktree；合回主分支用 `git merge --no-ff`，禁止 squash。
- 写码工人禁改 `docs/`；计划工人只改自己的 plan 与对应 issue（`worker verify` / `plan-check`）。
- 本地 commit / merge 可自主；`git push`、远端合并、部署须用户批准。
- 子代理输出不是事实源；承重定位与测试结论写入前由主线程复核。

## 构建与测试

```bash
for host in plugin droid-plugin pi-plugin cursor-plugin; do
  bash "$host/build/build.sh" --check || exit 1
  bash "$host/build/tests/test_build.sh" || exit 1
  for test_file in "$host"/scripts/tests/test_*.sh; do
    bash "$test_file" || exit 1
  done
done

for host in plugin droid-plugin pi-plugin cursor-plugin; do
  uv run --with pytest --with pydantic pytest \
    "$host/scripts/tests/test_release_contracts.py" \
    "$host/scripts/tests/test_release_script_assembler.py" || exit 1
done

python3 pi-plugin/scripts/render_agent_prompts.py --check
bash pi-plugin/workflows/install-workflows.sh --check
```

提交前：`git diff --check`；本次改动的 JSON 用 `python3 -m json.tool` 校验。
