## 建 worktree(进去之后才开干)

1. **起名**:从对话主题提一个人类可读、切题的 slug,格式 `YYYY-MM-DD-<theme>`(kebab,如 `2026-06-28-phone-login`)。这个名贯穿 worktree / 分支 / docs 目录,你要在 VSCode 里认得出。**向用户确认一次**(可同时让他改名)。

2. **一条命令建好**(从本地最新 HEAD 分叉,scaffold docs,写 manifest):
   ```bash
   mmw task new --scenario {{SCENARIO}} --slug <slug> --title "<人类可读标题>"
   ```
   回执给出 `worktree_path`;prepare 把本路径的阶段序列固化进 manifest 的 `phases`。
   仅 develop:用户开口已带明确方向(不用再摆备选)→ 加 `--direction-given`,propose 阶段引擎自动降级(`where` 的 `do` 会照 manifest 报降级指令:只落方向文档+一个最强对照,不重摆 2-3 方案)。

3. **进 worktree**(只有这步能切会话 cwd,脚本切不了):
   ```
   `EnterWorktree({ path: "<回执里的 worktree_path>" })`
   ```

提交进分支的文档:设计 `docs/design/`(含 prototype/mockup)、issue `docs/issues/`、计划 `docs/plans/`、领域 `docs/context/`(项目级资产)。**过程产物不永久存档**(`docs/.gitignore` 已忽略,随 worktree 删):现状报告 `docs/investigating/`、审查留痕 `docs/reviews/`、终审报告。临时状态落 `.claude/multi-model-workflow/`。
