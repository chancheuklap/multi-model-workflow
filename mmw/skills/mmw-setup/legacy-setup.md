# 上一版的仓库配置做法（已被 `mmw init` 取代）

这份文档和同目录那五份种子记的是插件早期的做法：种子铺进目标仓库的 `docs/agents/`，技能再去读那些文件取仓库事实。**这个行为已经不存在了。** 现在配置仓库跑 `mmw init`，参数进仓库根的 `.mmw.json`，五份种子里的方法论回到了各技能正文里，`TESTING.md` 的骨架搬到了 `mmw/cli/seeds/TESTING.md`。

留着只作背景线索，不参与行为判断。当前的做法读 `mmw/cli/lib/init.sh`。正文里凡是提到 `docs/agents/` 落点的地方一律作废，提到的方法论要以对应技能的正文为准。

以下是原文。

---

本插件的技能一律读 `docs/agents/` 下的文件取仓库事实。这个技能负责把那些文件铺进当前仓库。

**不问问题。** 你要做的是铺文件、加指针、报一句完成。

## 1. 铺六份配置

把本技能目录下这六份原样复制到下表给的落点（目录不存在就建）：

| 种子 | 落点 |
| --- | --- |
| `issue-tracker.md` | `docs/agents/issue-tracker.md` |
| `triage-labels.md` | `docs/agents/triage-labels.md` |
| `domain.md` | `docs/agents/domain.md` |
| `worktrees.md` | `docs/agents/worktrees.md` |
| `wiki.md` | `docs/agents/wiki.md` |
| `testing.md` | `TESTING.md`（仓库根） |

除 `testing.md` 之外的五份是填好的事实，拿来就能用。`TESTING.md` 是一份**骨架**，铺的是空位——测试目录怎么分层、哪些边界允许打桩、值从哪个权威源读，由第一次写测试的技能顺手填。它放在仓库根，不放 `docs/agents/`。

**已存在的不覆盖。** 目标文件已在，跳过它并在最后报告里列出来。

## 2. 建标签

`gh label list` 查一遍，`docs/agents/triage-labels.md` 里的标签缺哪个建哪个，已有的跳过：

| 哪一组 | 标签 |
| --- | --- |
| 状态 | `needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix` |
| 类型 | `bug`、`enhancement`（GitHub 新仓库自带，仍要确认在） |
| wayfinder | `wayfinder:map`、`wayfinder:grilling`、`wayfinder:prototype`、`wayfinder:research`、`wayfinder:task` |

```bash
gh label create "<名字>" --description "<一句话，抄 triage-labels.md 的含义列>"
```

## 3. 让两个目录不进 git

目标仓库的 `.gitignore` 里缺哪行就加哪行，已有的跳过：

| 行 | 挡的是什么 |
| --- | --- |
| `.worktrees/` | 任务 worktree，还有 Wiki 的 clone（`.worktrees/.wiki/`） |
| `.reviews/` | 审查记录和终审报告，随 worktree 死 |
| `.dispatch/` | 派给 `worker` 的 task 和它交回的报告，随 worktree 死 |

## 4. 把方法论装给 headless subagent

跑 CLI 里的安装脚本，幂等，装过就跳过：

```bash
bash "<插件根>/cli/lib/install-agent-skills.sh"
```

`<本技能目录>` 就是这份 `SKILL.md` 所在的目录，不用去找插件根。

这一步是**每台机器一次**，不是每个仓库一次，重跑无害。

报「冲突」说明那个名字被别的东西占着。**不要覆盖**，把冲突的路径报给用户，让他确认后自己清理。

## 5. 加指针节

编辑目标仓库根的 `CLAUDE.md`，没有就编辑 `AGENTS.md`；两个都没有，问用户建哪个——不要替他选。已存在的那个不要换成另一个。

已有 `## 多模型工作流` 节就原地更新，不要追加第二份；不要动周围的内容。

```markdown
## 多模型工作流

本仓库装了多模型开发编排插件。以下配置是既定事实，技能不硬编码这些内容，一律读文件。

- **Issue 与文档**：`docs/agents/issue-tracker.md`
- **Issue 标签**：`docs/agents/triage-labels.md`
- **领域文档**：`docs/agents/domain.md`
- **任务隔离**：`docs/agents/worktrees.md`
- **spec 归档**：`docs/agents/wiki.md`
- **测试的仓库事实**：根目录的 `TESTING.md`（通用测试规范随插件走，那份只补本仓库事实）
```

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 五步都做完 | **停**：报铺了哪几份、跳过了哪几份连同原因、建了哪几个标签、方法论装没装上、指针加进了哪个文件。再提一句这六份可以直接改，重跑本技能不会覆盖已存在的；`TESTING.md` 是骨架，要人或后续技能填上仓库事实 |
| 目标仓库既没有 `CLAUDE.md` 也没有 `AGENTS.md` | **停**：问用户建哪一个，不要替他选 |
| 第 4 步报冲突 | **停**：把冲突的路径原样报给用户，删不删由他定，不要自己覆盖 |
| 下面三项前提缺了任何一项 | **停**：在报告里指出来。**不要因此改配置内容，也不要退化成本地文件方案** |

## 前提

三项，缺任何一项都在报告里指出来。

| 前提 | 怎么查 | 缺了会怎样 |
| --- | --- | --- |
| 有 GitHub 远端 | `git remote -v` | issue 那套全不可用 |
| `gh` 已登录 | `gh auth status` | issue 那套全不可用；顺手提醒跑一次 `gh auth setup-git`，推 Wiki 要用 |
| Wiki 已初始化 | `git ls-remote "https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner).wiki.git"` | spec 无处归档。**只能由用户去仓库的 `/wiki` 页手建一页**，没有 API 能替他建，别试着绕 |
