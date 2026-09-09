# multi-model-workflow

一个人同时用好几个 coding agent（Claude Code、Codex、Pi、Cursor、Grok），每一个都有自己的技能目录。同一套工作方法要在五个地方各维护一份，改一处漏四处。这个仓库把那套方法收成一份 symlink 出去：改仓库里的 `SKILL.md`，五个 host 下一次调用就是新的（只有 description 要重开会话，见文末）。

活跃的只有 `mmw-v2/`；`archive/` 是上一代的冻结归档，留着查历史，不当事实用。详细的维护规则在 [AGENTS.md](AGENTS.md)。

## 装

```bash
bash mmw-v2/install.sh
```

检查装齐没有（齐了回 0，缺东西回 1）：

```bash
bash mmw-v2/install.sh --check
```

`install.sh` 把 `mmw-v2/skills.txt` 列出的技能 symlink 出去；指回本仓库却不在 `skills.txt` 里的 stale link，它会删掉。

技能只装两处：`~/.agents/skills` 是各家通用的位置，Codex、Cursor、Grok、Pi 都原生扫它；Claude Code 只认 `~/.claude/skills`，所以那一处再装一份同样的 symlink。两处都直接指向 source directory。`~/.agents` 不属于任何 host，无条件创建。

本仓库不往各 host 的 `agents/` 目录装任何东西：技能要派活的时候用 host 自带的通用 subagent，跑在起它那个会话的模型上。上一代装在那里的定义文件，`install.sh` 每次运行都摘一遍。host 的主目录（如 `~/.codex`）不存在就当没装这个 host，跳过。来源：[mmw-v2/install.sh](mmw-v2/install.sh)。

## 里面有什么

**技能**——见 [mmw-v2/skills.txt](mmw-v2/skills.txt)。两个来源：

- 上游 [mattpocock/skills](https://github.com/mattpocock/skills) 的 Git subtree，在 `mmw-v2/upstream/`。它是可编辑的工作副本，不是只读的供应商目录；我们改过的技能在 [mmw-v2/merge-notes/](mmw-v2/merge-notes/README.md) 里记着改动意图，上游更新起冲突时按它取舍。
- 自研的在 `mmw-v2/skills/`：`exe-release`（用当前分支代码给产品出正式安装包）、`verify-ticket`（跑一张 ticket 的 acceptance criteria，把结果写成 ticket 上的评论）、`manage-agents-md`（建、重写或增量更新一个仓库的 AGENTS.md 与 CLAUDE.md）、`dispatch`（把 ticket 派成会话、推进一夜的 batch）、`claude-design-blocks`（把 HTML mockup 搬进 Claude Design，以及把设计好的项目取回成交接包）、`code-checkers`（给仓库装 linter / formatter / type checker）。

## 改完不生效时先看这一条

**改了 description 不生效。** 技能的 description 是 host 启动时扫进系统提示的，改了要重开会话。正文和 `scripts/` 改了不用：host 链的就是 source directory 里那个文件。
