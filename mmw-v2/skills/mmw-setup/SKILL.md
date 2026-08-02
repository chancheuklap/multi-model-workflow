---
name: mmw-setup
description: 把本插件的工作流约定铺进当前仓库。每个仓库跑一次，其它技能才有配置可读。
disable-model-invocation: true
---

本插件的技能不硬编码任何仓库事实——issue 存哪、领域文档在哪、谁写谁审，全读 `docs/agents/` 下的文件。这个技能负责把那些文件铺进当前仓库。

**不问问题。** 这些选择在本插件里是固定的，不存在每仓库变数。你要做的是铺文件、加指针、报一句完成。

## 1. 铺七份配置

把本技能目录下这七份原样复制过去（目录不存在就建）。前六份进 `docs/agents/`，第七份落在仓库根：

| 种子 | 落点 |
| --- | --- |
| `issue-tracker.md` | `docs/agents/issue-tracker.md` |
| `triage-labels.md` | `docs/agents/triage-labels.md` |
| `domain.md` | `docs/agents/domain.md` |
| `models.md` | `docs/agents/models.md` |
| `worktrees.md` | `docs/agents/worktrees.md` |
| `wiki.md` | `docs/agents/wiki.md` |
| `testing.md` | `TESTING.md`（仓库根） |

前六份是填好的事实，拿来就能用。`TESTING.md` 不一样，它是一份**骨架**：测试怎么写、够不够格进仓库由 `/mmw-tdd` 随插件带着，而测试目录怎么分层、哪些边界允许打桩、值从哪个权威源读，只有这个仓库自己知道。铺的是空位，第一次写测试的技能顺手填。它放在仓库根而不是 `docs/agents/`，因为它同时是给人读的仓库文档。

**已存在的不覆盖。** 目标文件已在，跳过它并在最后报告里列出来——用户可能改过 `models.md` 的型号，或者早就写了自己的 `TESTING.md`，那份比种子新。

## 2. 让两个目录不进 git

目标仓库的 `.gitignore` 里缺哪行就加哪行，已有的跳过：

| 行 | 挡的是什么 |
| --- | --- |
| `.worktrees/` | 任务 worktree，还有 Wiki 的 clone（`.worktrees/.wiki/`） |
| `.reviews/` | 审查留痕和终审报告，随 worktree 死 |
| `.dispatch/` | 派给工人的提示词和它交回的报告，随 worktree 死 |

在这里一次挡掉，技能写文件时 `mkdir -p` 就行，不用在每个 worktree 里铺一份脚手架。

## 3. 加指针节

编辑目标仓库根的 `CLAUDE.md`，没有就编辑 `AGENTS.md`；两个都没有，问用户建哪个——不要替他选。已存在的那个不要换成另一个。

已有 `## 多模型工作流` 节就原地更新，不要追加第二份；不要动周围的内容。

```markdown
## 多模型工作流

本仓库装了多模型开发编排插件。以下配置是既定事实，技能不硬编码这些内容，一律读文件。

- **Issue 与文档**：`docs/agents/issue-tracker.md`
- **Issue 标签**：`docs/agents/triage-labels.md`
- **领域文档**：`docs/agents/domain.md`
- **模型角色**：`docs/agents/models.md`
- **任务隔离**：`docs/agents/worktrees.md`
- **spec 归档**：`docs/agents/wiki.md`
- **测试的仓库事实**：根目录的 `TESTING.md`（通用测试规范随插件走，那份只补本仓库事实）
```

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 七份铺完，`.gitignore` 和指针节都加好 | **停**：报铺了哪几份、跳过了哪几份连同原因、指针加进了哪个文件。再提一句这七份可以直接改，重跑本技能不会覆盖已存在的；`TESTING.md` 是骨架，要人或后续技能填上仓库事实 |
| 目标仓库既没有 `CLAUDE.md` 也没有 `AGENTS.md` | **停**：问用户建哪一个，不要替他选 |
| 下面三项前提缺了任何一项 | **停**：在报告里指出来。**不要因此改配置内容，也不要退化成本地文件方案** |

## 前提

三项，缺任何一项都在报告里指出来。这些是既定选择，不是可协商的默认值。

| 前提 | 怎么查 | 缺了会怎样 |
| --- | --- | --- |
| 有 GitHub 远端 | `git remote -v` | issue 那套全不可用 |
| `gh` 已登录 | `gh auth status` | 同上；顺手提醒跑一次 `gh auth setup-git`，推 Wiki 要用 |
| Wiki 已初始化 | `git ls-remote "https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner).wiki.git"` | spec 无处归档。**只能由用户去仓库的 `/wiki` 页手建一页**，没有 API 能替他建，别试着绕 |
