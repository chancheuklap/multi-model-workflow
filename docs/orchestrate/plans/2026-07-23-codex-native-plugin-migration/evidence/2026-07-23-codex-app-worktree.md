# Codex App Worktree 迁移证据

## 核验范围

- 日期：2026-07-23。
- 本机 Codex CLI：`0.145.0`。
- 资料：当前 Codex 官方 Worktrees 文档和本次 Codex App 任务实际暴露的线程工具。
- 目的：确定 MMW 能否在当前任务中途创建任意 Git worktree，再让 Codex App UI 和
  当前任务切入该目录。

## 官方当前能力

来源：[Codex Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees)

1. 用户可以在新任务 composer 选择 Worktree 和 starting branch；App 创建
   worktree，默认是 detached HEAD。
2. Handoff 在 Local 与当前任务关联的 Worktree 之间移动同一个任务和 Git 工作。
3. 当前任务后续返回 Worktree 时，App 回到同一个关联 worktree。
4. `Create branch here` 是用户准备在 worktree 上继续 commit/push/PR 时的可选
   动作，不是 worktree 工作的前置条件。
5. App-managed worktree 默认位于 `$CODEX_HOME/worktrees`，归档或容量管理可能
   触发 App 清理；App 在删除前保存 snapshot。
6. `.worktreeinclude`、ignored `AGENTS.override.md` 自动复制只适用于 App-created
   local managed worktree，不适用于命令行创建的 Git worktree。
7. permanent worktree 是 sidebar 中独立的长期项目，可承载多个任务；它不是 MMW
   每个正式任务的自动隔离原语。

官方文档没有提供把任意 shell-created Git worktree attach/register 到当前
Codex App 任务的接口。

## 当前任务工具边界

本次任务暴露的线程工具按当前 schema 核验：

- `handoff_thread` 可以移动另一个 task，但明确禁止调用 task 移动自己。
- `fork_thread(environment={type:"worktree"})` 会产生新的 child task；当前未完成
  turn 不会复制到 child。
- `create_thread` 也会产生新的用户可见 task，不是当前任务的 subagent/workspace
  切换工具。
- 当前 callable surface 没有 arbitrary worktree attach/register 或 current-task
  self-handoff。

因此，插件不能在当前 turn 内用线程工具把自己无缝迁进一个刚由
`git worktree add` 创建的目录。用 fork/create 替代会改变 sidebar、任务身份和
对话连续性。

## 当前原生 Subagent 的工作目录边界

Codex 官方 Subagents 文档确认 App/CLI/IDE 会在当前任务内产生可检查的 agent
threads；当前 callable `spawn_agent` schema 没有 per-child `cwd` 或 worktree
参数。子代理与父任务共享可见文件系统和启动 workspace。

因此只对需要独立写入的 plan/build 工人保留一层必要适配：

- worker 脚本先创建短命 inner worktree；
- spawn prompt 给出这一名工人的绝对 inner path；
- 子代理的命令显式使用该 path 作为 working directory；
- worker verify 只接纳该 inner worktree 中符合文件边界的结果。

这不构成主线程的 `TASK_ROOT` 方案。主线程始终自然使用 App 当前 cwd，不输出
第二条 root、不让 PreToolUse 解析路径、不维护全局 outer/inner allowset。

## Detached HEAD 私有引用实验

使用临时 Git repository 验证“不创建 branch 也能保护并合入 App outer commits”：

```text
git init -b main
git commit --allow-empty -m base
git worktree add --detach <app-wt> HEAD
git -C <app-wt> commit --allow-empty -m task-change
git -C <app-wt> update-ref refs/mmw/tasks/demo HEAD
git merge --no-ff refs/mmw/tasks/demo -m "merge task ref"
```

真实结果：

```text
*   8065c7b (HEAD -> main) merge task ref
|\
| * b1aefca task-change
|/
* 13b79c5 base
```

`git show-ref refs/mmw/tasks/demo` 在 merge 前返回：

```text
b1aefcadc2b5ef5c5165bf808e19c8021eed8d1a refs/mmw/tasks/demo
```

这证明 Git 原生 custom ref 可以同时满足：

- outer 继续使用 App 默认 detached HEAD。
- 不创建一个 App 不识别的 task branch。
- commits 在 worktree lifecycle 之外保持可达。
- closing 可以保持 `--no-ff` 合并语义。
- 合并验证后可以用 `git update-ref -d` 只删除 MMW 私有 ref。

## 对迁移设计的约束

| 约束 | 采用结论 |
| --- | --- |
| UI、terminal、diff 与真实修改必须同 checkout | 当前 Codex task 的 linked worktree 就是 outer 主任务 workspace。 |
| Local 任务不能 self-handoff | 初始化前返回一次 App Handoff 指令；不创建新 task。 |
| App 默认 detached HEAD | 用 `refs/mmw/tasks/<task-id>`，不强迫创建 UI branch。 |
| App owns managed worktree lifecycle | MMW 不删除、rename、detach 或 archive outer。 |
| App 可能清理/恢复 outer | durable task state 放 `$PLUGIN_DATA`，commits 由 task ref 钉住。 |
| Shell-created inner 没有 App setup | MMW 在 spawn 前显式 materialize ignored files/rules 并运行声明的 setup。 |
| plan/build 仍需隔离和并行 | MMW 只拥有短命 inner worktrees；验收后合回 outer。 |
| Native subagent 没有独立 cwd 参数 | 只有 plan/build worker prompt 携带 inner path；主线程不引入 `TASK_ROOT` 或路径代理。 |
