# `setup-matt-pocock-skills` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/SKILL.md:1-5 -->

```yaml
---
name: setup-matt-pocock-skills
description: 为本仓库配置工程技能，包括设置 issue tracker、triage 标签词汇和领域文档布局。在首次使用其他工程技能前运行一次。
disable-model-invocation: true
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/SKILL.md:7-17 -->

# Setup Matt Pocock's Skills

建立工程技能所假定的仓库级配置：

- **Issue tracker**——issue 存放的位置。默认使用 GitHub；开箱即用地支持本地 Markdown。
- **Triage 标签**——五种规范分诊角色使用的字符串。
- **领域文档**——`CONTEXT.md` 和 ADR 的位置，以及读取它们的消费规则。

这是提示驱动的技能，不是确定性脚本。先探索，再展示发现，请用户确认，然后写入。

## 流程

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/SKILL.md:19-30 -->

### 1. 探索

查看当前仓库，理解起始状态。读取实际存在的内容，不作假设：

- `git remote -v` 和 `.git/config`：这是 GitHub 仓库吗？是哪一个仓库？
- 仓库根目录的 `AGENTS.md` 和 `CLAUDE.md`：是否存在其中任何一个？其中是否已经有 `## Agent skills` 章节？
- 仓库根目录的 `CONTEXT.md` 和 `CONTEXT-MAP.md`
- `docs/adr/` 和任何 `src/*/docs/adr/` 目录
- `docs/agents/`：是否已经存在本技能先前的输出？
- `.scratch/`：是否表明已经采用本地 Markdown issue tracker 约定？
- 是否安装了 `triage` 技能？检查本技能旁边是否有 `triage` 技能目录，或可用技能中是否有 `triage`。这决定 B 节是否运行。
- Monorepo 信号：`pnpm-workspace.yaml`、`package.json` 中的 `workspaces` 字段，或者非空的 `packages/*` 且其中有自己的 `src/`。只有真正大型的多软件包仓库才会出现这些信号；没有这些信号表示单 context，而几乎所有仓库都属于这种情况。

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/SKILL.md:32-36 -->

### 2. 展示发现并询问

总结已有内容和缺失内容。随后按顺序处理各节：一节、一个回答，然后进入下一节。

每节先给出推荐答案，使用户只用一个词就能接受。只有选项确实会形成分支时，才提供一行说明。探索已经决定答案时，完全跳过该节；未安装 `triage` 时跳过 B 节，没有 monorepo 时跳过 C 节。

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/SKILL.md:38-49 -->

**A 节——Issue tracker。**

> 说明：“issue tracker”是本仓库保存 issue 的位置。`to-tickets`、`triage` 和 `to-spec` 等技能会读写它；这些技能需要知道应该调用 `gh issue create`、在 `.scratch/` 下写 Markdown 文件，还是遵循你说明的其他工作流。选择本仓库实际跟踪工作的地方。

默认立场是：这些技能为 GitHub 设计。如果 `git remote` 指向 GitHub，就提议 GitHub。如果 `git remote` 指向 GitLab，包括 `gitlab.com` 或自托管主机，就提议 GitLab。否则，或者用户有其他偏好时，提供：

- **GitHub**——issue 位于仓库的 GitHub Issues，使用 `gh` CLI
- **GitLab**——issue 位于仓库的 GitLab Issues，使用 [`glab`](https://gitlab.com/gitlab-org/cli) CLI
- **本地 Markdown**——issue 是本仓库 `.scratch/<feature>/` 下的文件，适合个人项目或没有远程仓库的仓库
- **其他**，例如 Jira、Linear：请用户用一个段落说明工作流；本技能会把它记录为自由文本

把选择记录在 `docs/agents/issue-tracker.md`。GitHub 和 GitLab 模板带有“把 PR 作为请求入口”的标志位，默认**关闭**。保持关闭，不要主动提起；希望把外部 PR 加入 triage 队列的用户以后可以直接在文件中打开标志位。

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/SKILL.md:51-61 -->

**B 节——Triage 标签词汇。** 如果没有安装 `triage` 技能，就完全跳过本节；探索步骤已经提供答案。未安装的技能不需要标签。

如果已经安装，只询问一个问题：

> 你想保留默认 triage 标签吗？推荐答案：**是**。

默认值是五种规范分诊角色，每个标签字符串与角色名称相同：`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`。用户回答**是**时，原样写入。只有用户回答否时才收集覆盖值；通常是因为 tracker 已经使用其他名称，例如用 `bug:triage` 表示 `needs-triage`。这样，`triage` 会使用现有标签，不会创建重复项。

**C 节——领域文档。** 默认使用**单 context**，也就是仓库根目录的一个 `CONTEXT.md` 和 `docs/adr/`。这适合几乎所有仓库；无需询问，直接写入。

只有探索发现 monorepo 信号时，才提供**多 context**选项，也就是根 `CONTEXT-MAP.md` 指向各 context 的 `CONTEXT.md` 文件；随后确认用户想要哪种布局。

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/SKILL.md:63-70 -->

### 3. 确认并编辑

向用户展示以下草稿：

- 将要加入选定 `CLAUDE.md` 或 `AGENTS.md` 的 `## Agent skills` 区块；选择规则参见第 4 步
- `docs/agents/issue-tracker.md`、`docs/agents/domain.md` 和 `docs/agents/triage-labels.md` 的内容；最后一份只在安装了 `triage` 时展示

写入前允许用户编辑。

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/SKILL.md:72-84 -->

### 4. 写入

**选择要编辑的文件：**

- 如果存在 `CLAUDE.md`，编辑它。
- 否则，如果存在 `AGENTS.md`，编辑它。
- 如果二者都不存在，询问用户要创建哪一个；不要代替用户选择。

当 `CLAUDE.md` 已经存在时，绝不要创建 `AGENTS.md`，反之亦然；始终编辑已经存在的文件。

如果选定文件中已经有 `## Agent skills` 区块，就原地更新内容，不要追加重复区块。不要覆盖周围章节中的用户改动。

区块如下：

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/SKILL.md:86-100 -->

```markdown
## Agent skills

### Issue tracker

[用一行总结 issue 在哪里跟踪]。参见 `docs/agents/issue-tracker.md`。

### Triage 标签

[用一行总结标签词汇]。参见 `docs/agents/triage-labels.md`。

### 领域文档

[用一行总结布局，例如 "single-context" 或 "multi-context"]。参见 `docs/agents/domain.md`。
```

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/SKILL.md:102-116 -->

只有安装了 `triage` 且运行了 B 节时，才加入 `### Triage 标签` 子区块，并写入 `docs/agents/triage-labels.md`。否则，两者都省略。

随后使用本技能目录中的初始模板作为起点，写入文档文件：

- [issue-tracker-github.md](./issue-tracker-github.md)——GitHub issue tracker
- [issue-tracker-gitlab.md](./issue-tracker-gitlab.md)——GitLab issue tracker
- [issue-tracker-local.md](./issue-tracker-local.md)——本地 Markdown issue tracker
- [triage-labels.md](./triage-labels.md)——标签映射，只在安装了 `triage` 时
- [domain.md](./domain.md)——领域文档消费规则和布局

对于“其他”issue tracker，根据用户说明从零编写 `docs/agents/issue-tracker.md`。

### 5. 完成

告诉用户设置已完成，并说明哪些工程技能现在会读取这些文件。说明用户以后可以直接编辑 `docs/agents/*.md`；只有想更换 issue tracker 或从零重启时，才需要重新运行本技能。

## `domain.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/domain.md:1-15 -->

# 领域文档

工程技能探索代码库时，应该如何消费本仓库的领域文档。

## 探索前读取以下内容

- 仓库根目录的 **`CONTEXT.md`**；或者
- 如果仓库根目录存在 **`CONTEXT-MAP.md`**，就读取它；它会为每个 context 指向一份 `CONTEXT.md`。读取与当前主题相关的每一份。
- **`docs/adr/`**：读取涉及即将处理区域的 ADR。在多 context 仓库中，还要检查 `src/<context>/docs/adr/` 中的 context 专属决定。

如果其中任何文件不存在，**静默继续**。不要指出缺失，也不要提议预先创建。`/domain-modeling` 技能会在术语或决定真正得到解决时按需创建它们；该技能通过 `/grill-with-docs` 和 `/improve-codebase-architecture` 到达。

## 文件结构

单 context 仓库，多数仓库：

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/domain.md:17-39 -->

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

多 context 仓库，根目录存在 `CONTEXT-MAP.md`：

```
/
├── CONTEXT-MAP.md
├── docs/adr/                          ← 系统级决定
└── src/
    ├── ordering/
    │   ├── CONTEXT.md
    │   └── docs/adr/                  ← context 专属决定
    └── billing/
        ├── CONTEXT.md
        └── docs/adr/
```

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/domain.md:41-51 -->

## 使用术语表中的词汇

输出中为领域概念命名时，例如 issue 标题、重构提案、假设或测试名称，使用 `CONTEXT.md` 定义的术语。不要漂移到术语表明确要求避免的同义词。

如果需要的概念还不在术语表中，这是一个信号：要么你正在创造项目并不使用的语言，需要重新考虑；要么确实存在缺口，需要为 `/domain-modeling` 记录。

## 标记 ADR 冲突

如果输出与现有 ADR 冲突，就明确呈现，不要静默覆盖：

> _与 ADR-0007（event-sourced order）冲突，但值得重新讨论，因为……_

## `issue-tracker-github.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/issue-tracker-github.md:1-26 -->

# Issue tracker：GitHub

本仓库的 issue 和 spec 以 GitHub issue 保存。所有操作都使用 `gh` CLI。

## 约定

- **创建 issue**：`gh issue create --title "..." --body "..."`。多行正文使用 heredoc。
- **读取 issue**：`gh issue view <number> --comments`；使用 `jq` 过滤评论，并同时取得标签。
- **列出 issue**：`gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`，并使用适当的 `--label` 和 `--state` 筛选条件。
- **评论 issue**：`gh issue comment <number> --body "..."`
- **应用或移除标签**：`gh issue edit <number> --add-label "..."` 或 `--remove-label "..."`
- **关闭**：`gh issue close <number> --comment "..."`

从 `git remote -v` 推断仓库；在克隆仓库内运行时，`gh` 会自动完成。

## 把 PR 作为 triage 入口

**把 PR 作为请求入口：no。** _如果本仓库把外部 PR 当成功能请求，就设为 `yes`；`/triage` 会读取这个标志位。_

设为 `yes` 时，PR 使用与 issue 相同的标签和状态，并使用对应的 `gh pr` 命令：

- **读取 PR**：`gh pr view <number> --comments`，并用 `gh pr diff <number>` 取得 diff。
- **列出供 triage 的外部 PR**：`gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments`；随后只保留 `authorAssociation` 为 `CONTRIBUTOR`、`FIRST_TIME_CONTRIBUTOR` 或 `NONE` 的项目，删除 `OWNER`、`MEMBER`、`COLLABORATOR`。
- **评论、设置标签或关闭**：`gh pr comment`、`gh pr edit --add-label` 或 `--remove-label`、`gh pr close`。

GitHub 的 issue 和 PR 共用一个编号空间，因此单独的 `#42` 可能是任一类型；先用 `gh pr view 42` 解析，失败时回退到 `gh issue view 42`。

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/issue-tracker-github.md:28-45 -->

## 当技能说“发布到 issue tracker”时

创建一张 GitHub issue。

## 当技能说“取得相关 ticket”时

运行 `gh issue view <number> --comments`。

## Wayfinding 操作

供 `/wayfinder` 使用。**map** 是一张 issue，**child** issue 是 ticket。

- **Map**：一张带 `wayfinder:map` 标签的 issue，正文保存 Notes、Decisions-so-far 和 Fog。使用 `gh issue create --label wayfinder:map`。
- **Child ticket**：通过 GitHub sub-issue 把一张 issue 连接到 map，使用 sub-issue 端点的 `gh api`。没有启用 sub-issue 时，把 child 加入 map 正文的任务清单，并在 child 正文顶部写 `Part of #<map>`。标签为 `wayfinder:<type>`，其中 type 是 `research`、`prototype`、`grilling` 或 `task`。ticket 被认领后，分配给负责推进的开发者。
- **Blocking**：GitHub 的**原生 issue dependency**，这是规范且在 UI 中可见的表达。使用 `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>` 增加 blocking edge；`<blocker-db-id>` 是 blocker 的数字**数据库 ID**，通过 `gh api repos/<owner>/<repo>/issues/<n> --jq .id` 取得，**不是** `#number` 或 `node_id`。GitHub 报告 `issue_dependencies_summary.blocked_by`，只包含仍 open 的 blocker，是实时关卡。无法使用 dependency 时，回退到 child 正文顶部的 `Blocked by: #<n>, #<n>`。每个 blocker 都 closed 后，ticket 才 unblocked。
- **Frontier query**：列出 map 中 open 的 child，使用 `gh issue list --state open`，并限定在 map 的 sub-issue 或任务清单；删除有 open blocker 的项目，包括 `issue_dependencies_summary.blocked_by > 0` 或 `Blocked by` 行引用 open issue，以及有 assignee 的项目；按 map 顺序的第一张获胜。
- **Claim**：`gh issue edit <n> --add-assignee @me`，这是 session 的第一次写入。
- **Resolve**：运行 `gh issue comment <n> --body "<answer>"`，随后运行 `gh issue close <n>`，再把 context pointer，也就是概要和链接，追加到 map 的 Decisions-so-far。

## `issue-tracker-gitlab.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/issue-tracker-gitlab.md:1-27 -->

# Issue tracker：GitLab

本仓库的 issue 和 spec 以 GitLab issue 保存。所有操作都使用 [`glab`](https://gitlab.com/gitlab-org/cli) CLI。

## 约定

- **创建 issue**：`glab issue create --title "..." --description "..."`。多行描述使用 heredoc。传入 `--description -` 会打开编辑器。
- **读取 issue**：`glab issue view <number> --comments`。使用 `-F json` 取得机器可读输出。
- **列出 issue**：`glab issue list -F json`，并使用适当的 `--label` 筛选条件。
- **评论 issue**：`glab issue note <number> --message "..."`。GitLab 把评论称为 note。
- **应用或移除标签**：`glab issue update <number> --label "..."` 或 `--unlabel "..."`。多个标签可以用逗号分隔，也可以重复传入标志位。
- **关闭**：`glab issue close <number>`。`glab issue close` 不接受关闭评论，因此先用 `glab issue note <number> --message "..."` 发布说明，然后关闭。
- **Merge request**：GitLab 把 PR 称为 merge request。使用 `glab mr create`、`glab mr view`、`glab mr note` 等；形态与 `gh pr ...` 相同，只把 `pr` 换成 `mr`，并把 `comment` 或 `--body` 换成 `note` 或 `--message`。

从 `git remote -v` 推断仓库；在克隆仓库内运行时，`glab` 会自动完成。

## 把 Merge request 作为 triage 入口

**把 MR 作为请求入口：no。** _如果本仓库把外部 merge request 当成功能请求，就设为 `yes`；`/triage` 会读取这个标志位。_

设为 `yes` 时，MR 使用与 issue 相同的标签和状态，并使用对应的 `glab mr` 命令：

- **读取 MR**：`glab mr view <number> --comments`，并用 `glab mr diff <number>` 取得 diff。
- **列出供 triage 的外部 MR**：`glab mr list -F json`；随后只保留作者不是项目成员或所有者的 MR，也就是贡献者的 MR，不是维护者正在进行的工作。
- **评论、设置标签或关闭**：`glab mr note`、`glab mr update --label` 或 `--unlabel`、`glab mr close`。

GitLab 与 GitHub 不同，issue 和 MR 分别编号，因此知道 maintainer 所指入口后，`#42` 就没有歧义。

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/issue-tracker-gitlab.md:29-46 -->

## 当技能说“发布到 issue tracker”时

创建一张 GitLab issue。

## 当技能说“取得相关 ticket”时

运行 `glab issue view <number> --comments`。

## Wayfinding 操作

供 `/wayfinder` 使用。**map** 是一张 issue，**child** issue 是 ticket。

- **Map**：一张带 `wayfinder:map` 标签的 issue，正文保存 Notes、Decisions-so-far 和 Fog。使用 `glab issue create --label wayfinder:map`。（在支持原生 epic 的 GitLab 层级上，也可以让 epic 承载 map；带标签的 issue 适用于所有层级。）
- **Child ticket**：description 顶部带 `Part of #<map>` 的 issue，并带 `wayfinder:<type>` 标签，其中 type 是 `research`、`prototype`、`grilling` 或 `task`。ticket 被认领后，分配给负责推进的开发者。
- **Blocking**：GitLab 的**原生 blocking link**，这是规范且在 UI 中可见的表达。把 `/blocked_by #<n>` quick action 作为 note 发布，命令为 `glab issue note <child> --message "/blocked_by #<blocker>"`。原生 blocking link 是 Premium 或 Ultimate 功能；免费层级或无法使用时，回退到 description 顶部的 `Blocked by: #<n>, #<n>`。每个 blocker 都 closed 后，ticket 才 unblocked。
- **Frontier query**：运行 `glab issue list -F json` 并限定在 map child；删除有 open blocker 的项目，包括指向 open issue 的原生 `blocked_by` link，通过 `glab api projects/:id/issues/:iid/links` 取得，或者 `Blocked by` 行引用 open issue，以及有 assignee 的项目；按 map 顺序的第一张获胜。
- **Claim**：`glab issue update <n> --assignee @me`，这是 session 的第一次写入。
- **Resolve**：运行 `glab issue note <n> --message "<answer>"`，随后运行 `glab issue close <n>`，再把 context pointer，也就是 gist 和 link，追加到 map 的 Decisions-so-far。

## `issue-tracker-local.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/issue-tracker-local.md:1-30 -->

# Issue tracker：本地 Markdown

本仓库的 issue 和 spec 是 `.scratch/` 中的 Markdown 文件。

## 约定

- 每项功能一个目录：`.scratch/<feature-slug>/`
- spec 是 `.scratch/<feature-slug>/spec.md`
- 实施 issue 每张 ticket 一个文件，位于 `.scratch/<feature-slug>/issues/<NN>-<slug>.md`，从 `01` 开始编号；绝不使用单一合并 ticket 文件
- Triage 状态记录为每份 issue 文件顶部附近的 `Status:` 行；角色字符串参见 `triage-labels.md`
- Comment 和对话历史追加到文件底部的 `## Comments` 标题下

## 当技能说“发布到 issue tracker”时

在 `.scratch/<feature-slug>/` 下创建新文件；需要时创建目录。

## 当技能说“取得相关 ticket”时

读取所引用路径中的文件。用户通常会直接传入路径或 issue 编号。

## Wayfinding 操作

供 `/wayfinder` 使用。**map** 是一个文件，每张 ticket 对应一个 **child** 文件。

- **Map**：`.scratch/<effort>/map.md`，正文保存 Notes、Decisions-so-far 和 Fog。
- **Child ticket**：`.scratch/<effort>/issues/NN-<slug>.md`，从 `01` 开始编号，正文包含问题。`Type:` 行记录 ticket type，包括 `research`、`prototype`、`grilling`、`task`；`Status:` 行记录 `claimed` 或 `resolved`。
- **Blocking**：文件顶部附近的 `Blocked by: NN, NN` 行。所列每份文件都是 `resolved` 时，ticket 才 unblocked。
- **Frontier**：扫描 `.scratch/<effort>/issues/` 中 open、unblocked 且 unclaimed 的文件；编号最小者获胜。
- **Claim**：在执行任何工作前，把状态设为 `Status: claimed` 并保存。
- **Resolve**：把答案追加到 `## Answer` 标题下，把状态设为 `Status: resolved`，随后把 context pointer，也就是 gist 和 link，追加到 `map.md` 的 Decisions-so-far。

## `triage-labels.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/triage-labels.md:1-15 -->

# Triage Label

各技能使用五种规范分诊角色。本文件把这些角色映射到本仓库 issue tracker 实际使用的标签字符串。

| mattpocock/skills 中的标签 | 我们 tracker 中的标签 | 含义 |
| --- | --- | --- |
| `needs-triage` | `needs-triage` | 维护者需要评估这张 issue |
| `needs-info` | `needs-info` | 等待报告者提供更多信息 |
| `ready-for-agent` | `ready-for-agent` | 已完全明确，可以交给 AFK agent |
| `ready-for-human` | `ready-for-human` | 需要人工实施 |
| `wontfix` | `wontfix` | 不会执行 |

技能提到某个角色时，例如“应用 AFK-ready triage 标签”，使用本表中对应的标签字符串。

编辑右侧列，使它符合你实际使用的词汇。

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/agents/openai.yaml:1-5 -->

```yaml
interface:
  display_name: "Setup Matt Pocock Skills"
  short_description: "为仓库配置这些技能"
policy:
  allow_implicit_invocation: false
```
