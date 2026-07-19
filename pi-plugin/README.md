# multi-model-workflow · pi plugin

`pi-plugin/` 是 multi-model-workflow 的 pi 单宿主镜像。它保留两态一门、磁盘账本、worktree、计划与落地工人、跨模型审查、断点恢复、红线拦截和 release-flow；不探测或调用 Claude Code / Factory Droid 镜像。

## 安装

```bash
pi install npm:@quintinshaw/pi-dynamic-workflows
pi install npm:pi-subagents
pi install /Users/cheuklapchan/multi-model-workflow/pi-plugin
bash /Users/cheuklapchan/multi-model-workflow/pi-plugin/workflows/install-workflows.sh
```

重启 pi 或运行 `/reload`。`pi list` 应同时列出动态工作流包和本插件。本插件是本地路径安装，修改仓库内容后无需复制；重新加载即可生效。唯一例外是 `workflows/*.workflow.js`：改完必须重跑 `install-workflows.sh`（它把生成物写进仓库 `workflows/dist/` 并把 `~/.pi/workflows/saved/*.json` 软链到 dist；漂移由 `install-workflows.sh --check` 和 `scripts/tests/test_workflows_dist_sync.sh` 把守）。

## 入口

- 正式开发编排：加载 `orchestrate` skill，或按其触发描述让模型自动进入。
- 控制命令：`/progress`、`/attended`、`/unattended`、`/approve-design`、`/reassess`、`/rescope`、`/replan-remaining`、`/side-finding`、`/skip-current`、`/force-validate`、`/gather-context`。
- 调查工作流：`/investigate-internal topics=<紧凑JSON> repoRoot=<绝对路径>`、`/investigate-external topics=<紧凑JSON>`；`/workflows` 查看运行、失败、暂停与恢复。
- 确定层 CLI：`bash <plugin-root>/scripts/mmw.sh help`。

## 角色与模型

花名册 `agents-roster/*.md` 是所有工作角色的单一权威(模型、thinking、工具白名单、职责、系统提示词)。GPT 系角色正文开头的 `mmw:fragments` 生成块由 `scripts/render_agent_prompts.py` 从 `_fragments/`(厂商原生提示词片段,来源见其 MANIFEST.md)渲染,改片段后重跑脚本,不要手改生成块;`--check` 可做一致性校验。全员软链进 `~/.pi/agent/agents/` 注册为 pi 正式 agent，协调者用 subagent 工具按名字派(`agent: "<角色名>"`)；重角色(pack-executor / plan-writer)用 `async: true` 后台跑，会话天然落盘长效可 resume，worktree 与边界门仍由 `scripts/worker.sh` 准备和把关。强判断咨询用 rpiv-advisor 的 advisor 工具，不占花名册编制。

安装后若未注册，把花名册软链进全局目录：

```bash
for f in /Users/cheuklapchan/multi-model-workflow/pi-plugin/agents-roster/*.md; do
  ln -sf "$f" ~/.pi/agent/agents/"$(basename "$f")"
done
```

## Hooks 与安全边界

- 会话开始或压缩恢复后，扩展经 `before_agent_start` 注入一次磁盘书签和新鲜度信息。
- `git push`、GitHub 远端合并和部署命令在 `tool_call` 前拦截；交互会话弹确认框，无 UI 的 headless 会话 fail-closed。
- commit 完成后由 `tool_result` 读取 HEAD 的 `Pack N.M` 并更新执行账本。
- Worker 禁改 `docs/`；plan writer 只发布指定 plan 与 issue 的 Small issues。
- pi 没有 Codex 的原生只读 sandbox。reviewer 的 prompt 明确只读，审前记录 HEAD、tracked diff 和 untracked 文件内容指纹；审闸收口时指纹变化即拒绝放行。这是当前机器硬闸。

## 状态与恢复

- 状态平面：`<worktree>/.pi/multi-model-workflow/`
- worktree 根：`<repo>/.pi/worktrees/`
- 工人账本：角色、worktree、prompt、start SHA、边界基线、验收/发布状态(工人回执在会话内,不落 result 文件)
- 续接：`mmw worker resume` / `plan-resume` 准备 resume prompt 并读账本 run id;`subagent({action:"resume", id:<run id>, message:…})` 从落盘会话文件复活原工人，长效、无会话内外之分;仅会话文件不可用时重派同角色，靠 worktree 提交对齐进度
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
