# multi-model-workflow · pi plugin

`pi-plugin/` 是 multi-model-workflow 的 pi 单宿主镜像。它保留两态一门、磁盘账本、worktree、计划与落地工人、跨模型审查、断点恢复、红线拦截和 release-flow；不探测或调用 Claude Code / Factory Droid 镜像。

## 安装

```bash
pi install npm:@quintinshaw/pi-dynamic-workflows
pi install /Users/cheuklapchan/multi-model-workflow/pi-plugin
bash /Users/cheuklapchan/multi-model-workflow/pi-plugin/workflows/install-workflows.sh
```

重启 pi 或运行 `/reload`。`pi list` 应同时列出动态工作流包和本插件。本插件是本地路径安装，修改仓库内容后无需复制；重新加载即可生效。

## 入口

- 正式开发编排：加载 `orchestrate` skill，或按其触发描述让模型自动进入。
- 控制命令：`/progress`、`/attended`、`/unattended`、`/approve-design`、`/reassess`、`/rescope`、`/replan-remaining`、`/side-finding`、`/skip-current`、`/force-validate`、`/gather-context`。
- 调查工作流：`/investigate-internal topics=<紧凑JSON> repoRoot=<绝对路径>`、`/investigate-external topics=<紧凑JSON>`；`/workflows` 查看运行、失败、暂停与恢复。
- 确定层 CLI：`bash <plugin-root>/scripts/mmw.sh help`。

## 角色与模型

| 角色 | 运行方式 | 默认模型 |
| --- | --- | --- |
| plan writer | 后台 `pi -p`，独立 Git worktree | `openai-codex/gpt-5.6-sol` |
| code worker | 后台 `pi -p`，独立 Git worktree | `openai-codex/gpt-5.6-terra`；capable 档用 sol |
| GPT reviewer | pi-subagents Agent | `openai-codex/gpt-5.6-terra` |
| Claude reviewer | pi-subagents Agent | `claude-provider/claude-opus-4-8` |
| investigate topic | pi-dynamic-workflows | `claude-provider/claude-sonnet-5:high` |

角色的模型、effort、工具白名单和职责以 `agents-roster/*.md` 为单一权威。

## GPT 无头提示词占位

`prompts-runtime/headless-agent.md` 已接入渲染路径，但当前只有 HTML 注释占位。`pi-exec.sh` 会识别占位、不把它注入 GPT 请求，并在工人的 `run.log` 留下：

```text
headless-agent prompt: placeholder, not injected
```

待与用户共同确定具体指导内容后，删除注释占位并写正文，后续 GPT worker 自动开始注入；无需修改派发脚本。

## Hooks 与安全边界

- 会话开始或压缩恢复后，扩展经 `before_agent_start` 注入一次磁盘书签和新鲜度信息。
- `git push`、GitHub 远端合并和部署命令在 `tool_call` 前拦截；交互会话弹确认框，无 UI 的 headless 会话 fail-closed。
- commit 完成后由 `tool_result` 读取 HEAD 的 `Pack N.M` 并更新执行账本。
- Worker 禁改 `docs/`；plan writer 只发布指定 plan 与 issue 的 Small issues。
- pi 没有 Codex 的原生只读 sandbox。reviewer 的 prompt 明确只读，审前记录 HEAD、tracked diff 和 untracked 文件内容指纹；审闸收口时指纹变化即拒绝放行。这是当前机器硬闸。

## 状态与恢复

- 状态平面：`<worktree>/.pi/multi-model-workflow/`
- worktree 根：`<repo>/.pi/worktrees/`
- 工人账本：PID、session ID、prompt、角色系统提示词、stdout、stderr、exit code
- 续接：`mmw worker resume` / `plan-resume` 复用账本里的 pi session ID
- 工作流续接：pi-dynamic-workflows journal

## 验证

```bash
for t in pi-plugin/scripts/tests/test_*.sh; do bash "$t" || exit 1; done
bash pi-plugin/build/build.sh --check
bash pi-plugin/build/tests/test_build.sh
uv run --with pytest --with pydantic pytest -q \
  pi-plugin/scripts/tests/test_release_contracts.py \
  pi-plugin/scripts/tests/test_release_script_assembler.py
```
