## 采用 Codex App 当前 worktree

1. 从对话主题起一个切题的 slug，格式 `YYYY-MM-DD-<theme>`。任务 branch 固定为
   `codex/<slug>`，让 Codex App 的 sidebar、terminal、diff 和 branch 始终指向同一份
   checkout。

2. 在当前 checkout 运行：

   ```bash
   mmw task new --scenario {{SCENARIO}} --slug <slug> --title "<人类可读标题>" --request "<用户原始需求与验收条件>"
   ```

   仅 develop：用户已经给出明确方向时加 `--direction-given`；整件事仍在雾里时加
   `--with-wayfind`。

3. 按回执继续：

   - `NEEDS_APP_WORKTREE`：当前是 local checkout。请用户在 Codex App 为这个仓库创建
     Worktree task，然后在那个 task 重跑同一条命令。plugin 不在后台创建另一个
     outer worktree。
   - `NEEDS_APP_BRANCH`：当前 App task 还是 detached 或 branch 名不对。请用户在
     App 当前 task 选择 **Create branch here**，创建回执给出的
     `codex/<slug>`，然后重跑同一条命令。
   - `PREPARED`：当前 App worktree/branch 已原地采用。保持当前 task 和 cwd，运行
     `mmw where` 进入第一阶段。

CLI 或 IDE 入口也只接受已经进入的 linked worktree 和 `codex/<slug>` branch；
plugin 不替宿主创建 outer。任务文档提交进当前 App branch；过程审查产物由
`docs/.gitignore` 忽略；临时状态固定落 `.codex/multi-model-workflow/`。
