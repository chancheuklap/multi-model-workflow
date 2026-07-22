## 建 worktree(进去之后才开干)

1. **起名**:从对话主题提一个人类可读、切题的 slug,格式 `YYYY-MM-DD-<theme>`(kebab,如 `2026-06-28-phone-login`)。这个名贯穿 worktree / 分支 / docs 目录,你要在 VSCode 里认得出。**把名字亮给用户但不阻塞**:`attended`(develop 讨论态)顺口让他改名;`afk` 路(bug / small-change)直接建,回执里带上名字,他不满意说一声再改(没动代码前重建零成本)。

2. **一条命令建好**(从本地最新 HEAD 分叉,scaffold docs,写 manifest):
   ```bash
   mmw task new --scenario {{SCENARIO}} --slug <slug> --title "<人类可读标题>" --request "<用户原始需求与验收条件>"
   ```
   回执给出 `worktree_path`;prepare 把本路径的阶段序列固化进 manifest 的 `phases`。
   仅 develop:用户开口已带明确方向(不用再摆备选)→ 加 `--direction-given`,propose 阶段引擎自动降级(`where` 的 `do` 会照 manifest 报降级指令:只落方向文档+一个最强对照,不重摆 2-3 方案)。
   仅 develop:终点明确但整件事还在雾里(连要决定什么都还没理清、单会话装不下)→ 加 `--with-wayfind`:phases 前加 wayfind 探路阶段,先与用户逐个拍清决策再进 investigate(`where` 会把 `load` 指到 `references/wayfind.md`)。

3. **进 worktree**(只有这步能切会话 cwd,脚本切不了):
   ```
   `EnterWorktree({ path: "<回执里的 worktree_path>" })`
   ```

提交进分支的文档:设计文件夹 `docs/design/<slug>/` 全部成员(主文档 `<slug>.md` 与文件夹同名 + direction/investigating/prototype/mockup/evidence 类型细分)、issue `docs/issues/`、计划 `docs/plans/`、领域 `docs/context/`(项目级资产)。**过程产物不永久存档**(`docs/.gitignore` 已忽略,随 worktree 删):审查留痕 `docs/reviews/`、终审报告。临时状态落 `.claude/multi-model-workflow/`。
