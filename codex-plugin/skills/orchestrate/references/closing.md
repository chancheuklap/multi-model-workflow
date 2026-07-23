# Closing · 收尾(阶段操作指南)

> 主线程进 closing 阶段加载本文。末阶段:确认任务真完整、可合并,然后交还。

`mmw where` → `prev_outputs` = build 阶段产物(含 ④终审闸钉的终审报告 `docs/<slug>-final-review.md`)。

## 1. 收口清单(逐条确认,机器能核的就核)

- **文档产出集中提交**:把设计 / issue / plan / 领域文档统一 commit 进分支(plan 阶段刻意不 commit,收口在这补上)。过程产物(investigating / reviews / 终审报告)已被 `docs/.gitignore` 忽略,不提交、随 cleanup 删。
- **落地完整**:分支无未提交改动(`git status` 干净;`.pi/multi-model-workflow/` 已被 gitignore,不算脏);相关测试绿(跑一遍)。
- **遗留标记扫描**(本任务新引入的,git 看 open_items 看不到):扫分支 diff 找新留下的临时标记——
 ```bash
 git diff <base_commit>..HEAD | grep -nE 'TODO|FIXME|TBD|XXX|HACK|placeholder|temporary|workaround|暂时|占位'
 ```
 **没有"非阻塞项"**:每条要么当场修掉,要么开成明确的独立后续(`mmw spinoff` 或 GitHub issue),要么确认它不是问题——三选一,不许留着含糊。
- **遗留处置**:`task.json` 的 `open_items` / `subtasks`(spinoff)逐条——要么本任务做了,要么明确登记成独立后续(不静默丢)。
- **审都过**:①②③④ 都过、无开口 Critical(build ④终审闸的终审报告为准)。
- **文档对齐**:设计/计划与最终落地一致(③④已核;这里只确认没有事后漂移)。

清单过完、承重产物已落盘并 commit 后,长于几步的任务在宣布完成前调一次 advisor 工具做最终检查(零参数，它自动看到全对话；关注点是 scope drift、未验证承重前提、必须停止的失败模式)。

顾问报具体 blocker → 回对应阶段修,别带病 closing；`no blockers, proceed` → 继续 handoff。短任务若最终动作已被刚完成的验证唯一决定可跳过。

## 2. 钉产出 → handoff

```bash
mmw handoff --conclusion pass
```

→ `STATUS=ready-to-close`:任务内容完成,等合并 + 清理(下面红线)。
还有没处理的遗留 / 测试没绿 → 回 build 补:`--conclusion needs-redirection --to-phase build`（`needs-repair` 是原地返工、回不到 build）。

## 3. 合并 + 发布(合并后才清理)

**本地合并进主分支是自主收尾动作,不拦**(可逆、不出站)。**出站发布才是硬红线**:`guard-redline`(PreToolUse)对 `git push` / `gh pr merge` / 部署弹权限框,**要用户在框里亲批**(无令牌可代批),不分在场/无人值守。

1. `exit_worktree({ action: "keep" })` 回主仓库,合并 → 直接跑 `git merge --no-ff <branch>`(禁 `--squash`)——**本地不弹框、无人值守也能自主推进**;真正要人批的是之后的 `git push`。
2. 合并进主线后,删干净:
 ```bash
 mmw task cleanup --slug <slug>
 ```
 cleanup 有安全门:分支没并入当前 HEAD 直接拒,绝不先删后悔。worktree + 分支 + 宿主状态平面临时状态一并清除。

worktree 使用期持久(可跨天);**合并后**才 cleanup。
