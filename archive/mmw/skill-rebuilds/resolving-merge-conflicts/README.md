# Resolving Merge Conflicts 重建区

这个目录用于从 Matt Pocock Skills 重新建立 MMW Integrate。当前发布技能仍位于 `mmw/skills-src/mmw-integrate/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（一份 5 步 `SKILL.md`，vendor `1.2.3`）。候选是 **1 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)，按将来位于 `mmw/skills-src/mmw-integrate/SKILL.md` 书写。技能名仍是 `mmw-integrate`（`/mmw-implement` 已经这么调）。现役三文件技能源未改。

上游五步原句留下：看现状、找 primary sources、逐 hunk 保留双方意图、跑项目自己的检查、完成 merge/rebase。Always resolve; never `--abort`。不按 `ours` / `theirs` 选边。

已叠进候选的接线：

- 目标是当前任务分支。主 agent 不换工作目录，不合进默认分支。
- `mmw result integrate` 已经开了的 merge：接着解，不重跑那条命令。
- 未完成的结果分支：在那棵结果 worktree 里 rebase。本会话留在任务分支。
- 首次写入前 `[[mmw-require-task-branch]]`。
- 取舍写进提交说明。有 `TESTING.md` 时从它开始跑检查。
- 既定目标判不了就停下来问。不发明第三种行为（上游第 3 步已有）。

未叠：

- `merging.md` / `rebasing.md`（`ours`/`theirs` 对照表是上游要杀掉的解法）。
- 合之前的四角调查。组合对不对是 ⑤ Final trace。
- 「终审过了才合」。worker 做完就合。
- 合完自查三关、`mmw result verify` 单独跑、`integration-*.md` 审查记录。
- `agents/openai.yaml`。技能保持 model-invoked，implement 要调得着。

同轮改了 review 候选：⑤ 不再说「要不要先调查由 `/mmw-integrate` 判」。

本轮不派冷读 subagent。不改 leaf。`任务分支` / `结果分支` / `基点 SHA` 已在 `docs/context/agent-coordination.md`。
