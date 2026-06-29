# Closing · 收尾(阶段操作指南)

> 主线程进 closing 阶段加载本文。末阶段:确认任务真完整、可合并,然后交还。合并/清理是合并后的红线动作,本文下面讲。

`mmw where` → `prev_outputs` = verify 阶段钉的终审报告。

## 1. 收口清单(逐条确认,机器能核的就核)

- **落地完整**:分支无未提交改动(`git status` 干净);相关测试绿(跑一遍)。
- **遗留处置**:`task.json` 的 `open_items` / `subtasks`(spinoff)逐条——要么本任务做了,要么明确登记成独立后续(不静默丢)。
- **审都过**:①②③④ 都过、无开口 Critical(verify 的终审报告为准)。
- **文档对齐**:设计/计划与最终落地一致(③④已核;这里只确认没有事后漂移)。

## 2. 钉产出 → handoff

```bash
mmw handoff --conclusion pass
```

→ `STATUS=ready-to-close`:任务内容完成,等合并 + 清理(下面红线)。
还有没处理的遗留 / 测试没绿 → `--conclusion needs-repair`（回 build 补）。

## 3. 合并红线(合并后才清理)

**合并回主分支 = 唯一硬红线**(不可逆对外动作)。`guard-redline`(PreToolUse)拦 `git merge`/`push`/部署,**要你亲自批**(`release-approval` 令牌),不分在场/无人值守:

1. 你确认要合并 → 给批准令牌 → `git merge --no-ff <branch>`(禁 `--squash`)。
2. 合并进主线后,回主仓库删干净:
   ```bash
   mmw task cleanup --slug <slug>
   ```
   cleanup 有安全门:分支没并入当前 HEAD 直接拒,绝不先删后悔。worktree + 分支 + `.claude/` 临时状态一并清除。

worktree 使用期持久(可跨天);**合并后**才 cleanup。
