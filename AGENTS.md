# AGENTS.md

用户跨宿主、跨仓库、跨电脑共用的工作流工具箱：技能和 subagent。个人使用，没有 CI，测试手工跑。
只有 `mmw-v2/` 是活的。`archive/` 是上一代的冻结归档，`deprecated/` 是 v2 自己退役的技能与 subagent：两者都不改、不当事实，`archive/` 里的安装脚本一个都不要跑。
仓库里的技能是交付物，不是你的工作指南。

## 命令

没有包管理器和构建步骤。运行时只有 bash、`python3` 标准库和按需的 `uv`。

| 命令 | 干什么 |
| --- | --- |
| `bash mmw-v2/install.sh` | 唯一安装入口，装四样：技能软链进 `~/.agents/skills` 和 `~/.claude/skills`，subagent 成品软链进各宿主，hook 写进各宿主自己的配置，Herdr agent 检测规则拷进 `~/.config/herdr/agent-detection/` |
| `bash mmw-v2/install.sh --check` | 只看不动 |
| `python3 mmw-v2/agents/assemble.py --check` | 校验 subagent 成品 `mmw-v2/agents/<名>/out/` 与源一致。`install.sh --check` 已内含它；单跑用于只验成品 |
| `bash mmw-v2/skills/<名>/tests/run.sh` | 单个技能的测试 |

## 约定

- 技能正文对所有宿主是同一份：不把任何宿主当默认或首选，不按宿主名分支；能力差异用按能力判断的自然语言写。
- 装哪些技能只改 `mmw-v2/skills.txt`。宿主软链直接指向源目录，改完下一次调用即生效；只有 frontmatter 的 `description` 是宿主启动时扫进去的，改它要重开会话。
- 起会话的命令、每个 agent 用哪个宿主哪个模型哪档思考强度，只改 `mmw-v2/skills/dispatch/models.md`。它跟着技能软链走，是这台机器的一份，消费仓库里不放。
- `mmw-v2/upstream/` 是 mattpocock/skills 的 git subtree（squash），`mmw-v2/upstream-diagram-design/` 是 cathrynlavery/diagram-design 的另一个。两者都可编辑；上游自带的 `AGENTS.md`、`CLAUDE.md`、`CONTEXT.md` 原样不动——`mmw-v2/upstream/CONTEXT.md` 是上游自己的词表，本仓的词表只有根 `CONTEXT.md`。拉上游和解冲突见 `mmw-v2/merge-notes/README.md`；改了上游技能就写或更新它的 merge-note。
- 两个 subtree 之外还有一份从 unlazy 抄进来的脚本：`mmw-v2/skills/verify-ticket/scripts/gate-check/`。它没有 subtree，`git subtree pull` 和 merge-note 都不管它，来源、commit 与改过哪几行记在 `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md`。

## Agent skills

### Issue tracker

本仓 issue 在 GitHub Issues，全部操作走 `gh` CLI。See `docs/agents/issue-tracker.md`.

### Triage labels

五个规范角色用默认标签串（`needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`）。See `docs/agents/triage-labels.md`.

### Domain docs

单 context：根 `CONTEXT.md`（这条流水线的全部固定词，动词汇先读它）加 `docs/adr/`。See `docs/agents/domain.md`.

Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full.
