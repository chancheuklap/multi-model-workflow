## 建 worktree(进去之后才开干)

1. **起名**:从对话主题提一个人类可读、切题的 slug,格式 `YYYY-MM-DD-<theme>`(kebab,如 `2026-06-28-phone-login`)。这个名贯穿 worktree / 分支 / docs 目录,你要在 VSCode 里认得出。**向用户确认一次**(可同时让他改名)。

2. **一条命令建好**(从本地最新 HEAD 分叉,scaffold docs,写 manifest):
   ```bash
   mmw task new --scenario <你这条路径:small-change|develop|bug> --slug <slug> --title "<人类可读标题>"
   ```
   回执给出 `worktree_path`;prepare 把本路径的阶段序列固化进 manifest 的 `phases`。

3. **进 worktree**(只有这步能切会话 cwd,脚本切不了):
   ```
   EnterWorktree({ path: "<回执里的 worktree_path>" })
   ```

文档产出提交进分支(查清 `docs/investigating/`、设计 `docs/design/`、issue `docs/issues/`、计划 `docs/plans/`、领域 `docs/context/`);临时状态落 `.claude/multi-model-workflow/`(随 worktree 删)。
