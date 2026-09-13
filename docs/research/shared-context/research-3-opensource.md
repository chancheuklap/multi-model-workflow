# 多 agent 共享上下文：开源实现调研（2026-09-13）

## 0. 范围、方法、可信度

- **问题**：多个 agent 之间的共享上下文如何组织、流转、更新。参照对象是 Cursor Projects（2026-09-10 发布）和 Fatih Arslan 的 plan/coordinator 工作流。
- **方法**：
  - 先用 `gh api repos/...` 取元数据，再用 `gh search repos/code` 和 WebSearch 发现新项目。
  - 仓库都浅克隆到 `mktemp -d` 临时目录，只读，没有运行其中任何脚本。
  - 实现文件分给 5 个子代理并行细读，另有 3 个项目我自己读（Evalir/dotfiles、planning-with-files、monomind project-context）。
  - 每节末尾列出读过的文件。
- **链接**：钉在克隆时的 commit SHA 上。部分章节开头给出"链接前缀"，正文里的 `X/path#Lnn` 表示"前缀 + path"。
- **星数 / 最后 push**：下表是我在 2026-09-13 用 `gh api repos/<o>/<r>` 亲眼看到的，标"子代理所见"的除外。
- **标记约定**：推断标"推断"，没查到的写"未找到"。

| 仓库（重定向后） | stars | pushed_at | 本报告读的 commit |
|---|---|---|---|
| Dicklesworthstone/mcp_agent_mail | 2139 | 2026-09-06 | ac4966c64d7e |
| gastownhall/beads（steveyegge/beads 已重定向） | 27106 | 2026-09-12 | f56632adcfab |
| gastownhall/gastown | 18031 | 2026-09-10 | 649b832b7672 |
| jayminwest/overstory | 1327 | 2026-05-28 | ff38f3f76f08 |
| MrLesk/Backlog.md | 6716 | 2026-09-12 | c0ec546a3b51 |
| github/spec-kit | 136043 | 2026-09-12 | d848fb4e18f4 |
| bmad-code-org/BMAD-METHOD | 52943 | 2026-09-12 | 94b6727b00c8 |
| buildermethods/agent-os | 5397 | 2026-08-29 | 475b0cac4c7c |
| gemini-cli-extensions/conductor | 3735 | 2026-09-01 | 6e8f9a860bcd |
| automazeio/ccpm | 8370 | 2026-03-18 | 7d7e4623bc6d（v1 快照 1cb9483a） |
| eyaltoledano/claude-task-master | 28065 | 2026-04-28 | c0c98d367c55 |
| humanlayer/humanlayer | 11511 | 2026-06-19 | 99abe673498c |
| Yeachan-Heo/oh-my-claudecode | 39120 | 2026-09-12 | 5281b19e0d64 |
| OthmanAdi/planning-with-files（2026-01-03 创建） | 26834 | 2026-09-09 | 1ec8f4eb5c68 |
| monomind-ai-lab/project-context（2026-08-25 创建） | 3 | 2026-09-09 | 72a0a22640f4 |
| Evalir/dotfiles（plan-* skills 于 2026-09-12 加入） | 1 | 2026-09-12 | 通过 gh api 读 main |
| ruvnet/ruflo（ruvnet/claude-flow 已重定向） | 72233 | 2026-09-12 | b02c0cacec22 |
| OpenHands/OpenHands（现在只放前端） | 87680 | 2026-09-12 | 实现在 OpenHands/software-agent-sdk 76e9e250（子代理所见 1101 stars） |
| letta-ai/letta（main 只剩 README） | 24714 | 2026-09-10 | archive 分支 56ba9c25；letta-ai/letta-code（子代理所见 3315 stars） |
| BloopAI/vibe-kanban | 28063 | 2026-09-12 | 4deb7eca8f38 |
| stravu/crystal（README 称 2026-02 已弃用） | 3115 | 2026-02-26 | 1e18e0bc9812 |
| imbue-ai/sculptor | 230 | 2026-09-11 | f74741c425b7 |
| niveshdandyan/teammate-tool / codexstar69/pi-agent-teams / OthmanAdi/planning-with-teams | 子代理所见 1 / 9 / 26 | — | 151b24e8 / 58f0a39e / 024def2f |

**搜"模仿 Cursor Projects"的仓库，结果如下：**
- `gh search repos` 的查询词包括 "plan-dispatch"、"cursor projects"、"coordinator agent inbox handoff" 等，限定 created > 2026-09-01，没有找到相关仓库。
- `gh search code "plan-dispatch" --filename SKILL.md` 命中 `Evalir/dotfiles`（commit d62872287001，2026-09-12T12:19，"add the plan-* skills"），这是唯一一个在 arslan 文章发表（2026-09-11）之后一天内出现、成套复刻 plan-* skills 的公开实现。另外两个命中 `firefly-events/plugin-hive` 和 `willfell/sauce` 更早就有 plan-dispatch，未深读。
- 按 coordinator-notes、From/To/Date/Why 头格式搜代码，没有找到相关实现。推断：GitHub 代码索引对最近几天的新提交有延迟。
- arslan 本人在文中说明不公开 skill 文件（据 [daily.dev 摘要](https://daily.dev/posts/how-i-manage-my-agents-qxohupab9)），`plan-skills` 仓库未找到。

---

## 1. 基准：Cursor Projects 与 arslan 的 plan/coordinator 工作流（闭源，只有文章）

来源：[Cursor changelog](https://cursor.com/changelog/projects)，[arslan.io 2026-09-11](https://arslan.io/2026/09/11/how-i-manage-my-agents/)。

**Cursor changelog 原文：**
- "Each Project maintains a set of files that sync across every cloud and local machine its agents use."
- "Agents add research and artifacts, along with what they learn about the codebase and how you prefer work to be done."
- changelog 页面本身没有出现 notes.md、User Context 这些文件名。文件名来自 arslan 的文章和第三方报道（[flaviocopes](https://flaviocopes.com/cursor-projects/)）。

**arslan 文章描述的布局与规则：**
- **Project Context**：
  - `notes.md` 只由 coordinator 写，固定分节 "Goal, PRs, Open, Next, Drafts, Done, Links, Research"；
  - `docs/`、`media` 给人看；
  - `internal/` 是 agent 的草稿区。
- **User Context**：`preferences.md` 由 coordinator 每轮读，但 "not passed down to agents"；`skills/` 同步给所有 agent。
- **coordinator 之间通信**：coordinator 之间不能直接发消息，也读不到彼此的 Context，所以通过 git 留言，文件放在 `docs/coordinator/`：
  - 文件：`preferences.md`、`handoff-billing-2026-09-04.md`、`inbox/hub.md`、`inbox/billing.md`；
  - 头部："Every file there starts with four lines: `From`, `To`, `Date`, and `Why`."；
  - 消息格式："A message is one checkbox line with the date, the sender, and one or two sentences."；
  - 写入权限："The `Hub` writes into a Project's file; a Project writes into `hub.md`… Projects do not write into each other's files, they ask the Hub."；
  - 读取时机：每个 coordinator 每轮开始 pull 并读自己的 inbox，然后提交回复。
- **计划流转**：`plans/{drafts,next,open,done,discarded}` 加 `README.md` 索引，由 skill 推进：
  - `/plan-add` 放入 drafts；
  - `/plan-write` 放入 next，要求 "you prove the cause, name the change, and write the commands that will prove it worked"；
  - `/plan-dispatch` 放入 open；
  - `/plan-sync` 核对已合并的 PR 后放入 done 或 discarded；
  - `/plan-status` 只做报告；
  - `/plan-retro` 读 done 和 discarded，提出修改 skill 的建议。
- **唤醒**：coordinator 订阅 worker 开出的每个 PR，"When CI finishes or a reviewer leaves a comment, the coordinator wakes up, reads it, and sends the worker back"。
- **恢复**：notes 丢失时，从 git 仓库重建（"rebuild its notes from the repo"）。

---

## 2. Evalir/dotfiles 的 plan-* skills（2026-09-12，arslan 工作流的公开复刻）

- **链接前缀**：`E=https://github.com/Evalir/dotfiles/blob/main/agents/skills/`（通过 gh api 读 main；最近两个提交是 d62872287001 和 4a05ce99bdc9，均为 2026-09-12）。
- **规模**：8 个 skill，全部读完：plan-spec、plan-init、plan-add、plan-write、plan-dispatch、plan-sync、plan-status、plan-retro。纯 prompt，没有脚本。

**1 文档类型与布局**
- 所有计划集中在一个私有仓库 `Evalir/plans`，每个代码仓库一个子树 `<repo>/{README.md,drafts,next,open,done,discarded}`。
- 代码仓库通过符号链接 `.claude/plans -> ~/dev/evalir/plans/<repo>` 访问自己的子树，这个链接写进 `.git/info/exclude`，不进 `.gitignore`（E/plan-init/SKILL.md、E/plan-spec/SKILL.md）。
- worktree 放在 `.claude/worktrees/<slug>/`，规则是 "A plan in `open/` owns exactly one worktree with the same slug"（E/plan-spec/SKILL.md）。

**2 格式**：plan 文件的 frontmatter（E/plan-spec/SKILL.md）：
```yaml
repo: owner/name
status: draft | next | open | done | discarded
appetite: hours | days | a week | longer
worktree:  branch:  pr:  issue:
stacked-on:   blocked-by:   slack:
```
- 正文分节：`## Problem / ## Change / ## Checks / ## Verify live / ## Not in this PR / ## Log`。
- 规则原文："The body sections are the PR body… for a cloud agent, the body *is* the task, so it must stand on its own."
- 索引 README 是几张表，规则 "`plan-status` regenerates the tables below. Do not hand-edit them."（E/plan-init/SKILL.md）。

**3 读者与写者**
- plan-add 只写 drafts，要求 "Blank beats guessed"，不许留空节。
- plan-write 调查后 `mv drafts→next`，只写计划，不写代码。
- plan-dispatch 建 worktree、开 PR，`mv next→open`，填 `worktree/branch/pr`，并追加 `## Log`。
- plan-sync 移动到 done 或 discarded，清理 worktree。
- plan-status 只重写索引表。
- 移动计划文件是 plan-sync 独有的职责，plan-status 的规则写着 "Do not move plans between folders. That is `plan-sync`."

**4 强制机制**
- 只有 prompt。每个 skill 开头要求 "Read `plan-spec` first"。
- 带拒绝条件，例如 plan-dispatch 的 "Refuse to start if… The plan is not in `next/`… `blocked-by:` names a PR that has not merged."
- 未找到 hook。

**5 更新时机与生命周期**：状态靠目录表达，每次迁移都是一次 `mv` 加一次提交。plan-sync 对已合并的计划有三类判定：
- **diff 与计划一致**：移到 done。
- **diff 比计划多**：移到 done，并在 `## Log` 里记下多出的部分。
- **diff 比计划少**：移到 done，并把没做的部分写成新的 draft。
- **关闭未合并**：移到 discarded，必须写原因，原文 "A discard with no reason is how the same idea gets planned twice"。
- **超过两周无 PR 无 worktree**：退回 next。

**6 并发**
- 没有锁。plans 仓库靠 git 的 commit/push，每次 status 和 sync 结束时执行 `git diff --quiet --cached || commit && push`。
- 推断：两台机器同时运行 sync 时，靠 git push 被拒来暴露冲突，skill 里没有写冲突处理。
- 保护同事分支的规则："Never force-push a branch you did not create"。

**7 流转**
- 本地 dispatch 和云端 dispatch 分开处理。云端 agent "sees neither your home directory nor the plans repo, so it gets **the plan body as its entire task**"，PR 保持 draft，因为沙箱跑不了 `## Verify live`。
- 反馈回路是 plan-retro：规定 "Something that happened three times is a rule that is missing"，只提建议，不擅自修改。

**读过的文件**：E/{plan-spec,plan-init,plan-add,plan-write,plan-dispatch,plan-sync,plan-status,plan-retro}/SKILL.md（全文）。

---

## 3. Dicklesworthstone/mcp_agent_mail：agent 间邮件与文件预约

链接前缀 `MA=https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/`

**1 文档类型与存储**
- 两份存储：
  - SQLite 数据库，默认 `./storage.sqlite3`（[config.py#L434](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/config.py#L434)）；
  - Git 存档仓库，默认 `~/.mcp_agent_mail_git_mailbox_repo`，按项目分目录 `projects/<slug>/`（[storage.py#L1424-L1436](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/storage.py#L1424-L1436)）。
- 数据库表：`projects, agents, messages, message_recipients`（记录 `read_ts`、`ack_ts`），以及 `file_reservations, agent_links, message_summaries`（[models.py#L23-L201](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/models.py#L23-L201)）。
- 存档目录：
  - `messages/YYYY/MM/<ISO>__<slug>__<id>.md`；
  - 同一份内容再复制到发件人的 `outbox/` 和每个收件人的 `inbox/`；
  - `messages/threads/<thread_id>.md` 是只追加的线程摘要；
  - `file_reservations/<sha1(path)>.json`（[storage.py#L1497-L1745](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/storage.py#L1579-L1650)）。

**2 格式**
- 消息文件是 `---json\n{frontmatter}\n---\n\n{body}`（[storage.py#L1612-L1620](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/storage.py#L1612-L1620)）。
- 预约表（[models.py#L117-L137](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/models.py#L117-L137)）：
```python
path_pattern: str = Field(max_length=512)
exclusive: bool = Field(default=True)
reason: str = Field(default="", max_length=512)
expires_ts: datetime
released_ts: Optional[datetime] = None
```
- 消息还带 `thread_id, reply_to, importance, ack_required, attachments`（[models.py#L89-L114](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/models.py#L89-L114)）。

**3 读者与写者**
- agent 只能通过 MCP 工具读写：`send_message / reply_message / fetch_inbox / acknowledge_message / file_reservation_paths`（[app.py](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/app.py#L7123)）。
- 人读 Git 存档或 Web 界面。
- 推断：写入全部经过 `storage.py` 的 `_commit`，服务进程是唯一写者。

**4 强制机制**
- AGENTS.md 里写着 "Reserve files before you edit"（[AGENTS.md#L76-L102](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/AGENTS.md#L76-L102)）。
- `macro_start_session` 一次完成注册、预约、拉取收件箱（[app.py#L10010-L10085](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/app.py#L10010-L10085)）。
- `integrate_claude_code.sh` 注册 Claude Code hook：SessionStart 列出当前预约和待确认消息；PreToolUse(Edit) 提示即将过期的预约；PostToolUse(Bash) 运行 `check_inbox.sh`（[integrate_claude_code.sh#L196-L230](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/scripts/integrate_claude_code.sh#L196-L230)）。
  - `check_inbox.sh` 限流为 120 秒一次。
  - 只有设了 `AGENT_MAIL_HOOK_FORMAT=json`，输出才进入模型上下文（[check_inbox.sh#L1-L33](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/scripts/hooks/check_inbox.sh#L1-L33)）。

**5 生命周期**
- 清理：`purge_old_messages` 默认保留 180 天，默认只是演练（dry_run），只删数据库行，不删 Git 存档（[app.py#L8466-L8517](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/app.py#L8466-L8517)）。
- 压缩：`summarize_thread` 用 LLM 把线程摘要写进 `message_summaries`（[app.py#L11039](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/app.py#L11039)）。
- 预约：
  - 默认 TTL 3600 秒；
  - 可续期（renew）、可释放（release）；
  - 后台每 60 秒释放一次过期或失活的预约（[http.py#L1105-L1139](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/http.py#L1105-L1139)）。

**6 并发（重点）**
- **预约只是提示，不拦截**：有冲突照样批准，只在返回值里附上冲突。原文 "Advisory model: still grant the file_reservation but surface conflicts"（[app.py#L11614](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/app.py#L11614)）。
- **原子性**：
  - 外层用项目级文件锁 `.archive.lock`（[storage.py#L1239-L1271](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/storage.py#L1239-L1271)）；
  - 内层 SQLite 用 `BEGIN IMMEDIATE`，读、判冲突、写在同一个事务里（[app.py#L11539-L11552](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/app.py#L11539-L11552)）；
  - Git 存档写失败时，删掉刚写入的数据库行作为补偿（[#L11674-L11690](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/app.py#L11674-L11690)）。
- **冲突判定**：路径按 gitignore 语义匹配；两边都带通配符时互相交叉匹配，原文 "approximate by cross-matching"（[app.py#L4315-L4378](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/app.py#L4315-L4345)）。
- **失活判定**：持有者超过 1800 秒不活跃，并且 900 秒宽限期内既没有邮件活动、没有改动相关文件、也没有 git 提交；或者持有者本身已被删除（[app.py#L4076-L4086](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/app.py#L4076-L4086)）。
  - 强制释放只对失活的预约生效，并可以通知原持有者（[#L11864-L11960](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/app.py#L11864-L11960)）。
- **真正的硬拦截在 git pre-commit hook**：
  - 读取 `file_reservations/*.json`，把暂存区路径（含重命名前后两个路径）和别人持有的独占预约比对，冲突就 `exit 1`（[guard.py#L268-L473](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/guard.py#L268-L473)）；
  - 可以用 `AGENT_MAIL_GUARD_MODE=warn` 降级为警告，或用 `AGENT_MAIL_BYPASS=1` 绕过。
- **服务端只对存档路径硬拦截**；对代码路径只返回 `enforcement_off_for_code_paths`（[#L11699-L11707](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/src/mcp_agent_mail/app.py#L11699-L11707)）。

**7 流转**
- 协作形式是线程加 ack。
- 跨项目通信要先通过联系人审批（`agent_links`）。
- 与 beads 的分工约定：任务状态交给 Beads，邮件负责对话和留痕；`thread_id` 和预约的 `reason` 都用 issue id（[AGENTS.md#L198-L218](https://github.com/Dicklesworthstone/mcp_agent_mail/blob/ac4966c64d7e39692a4fb9c707448a1718ab29db/AGENTS.md#L198-L218)）。
- 没有单独的交接文档（推断）。

**读过的文件**：src/mcp_agent_mail/models.py（全文），app.py（L3967-4420、5500-5625、8466-8520、10010-10090、11039-11060、11400-11710、11864-11960、12079-12120），storage.py（L88-128、1239-1275、1424-1750），guard.py（L1-120、268-476），config.py、http.py（L1105-1140），scripts/integrate_claude_code.sh（L150-232），scripts/hooks/check_inbox.sh，AGENTS.md，SKILL.md。

---

## 4. gastownhall/beads：给 agent 用的 issue 图与记忆

链接前缀 `BD=https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/`

**1 存储**
- 工作区的 `.beads/` 目录，存储是 Dolt（带 git 式版本管理的 SQL 数据库）（[beads.go#L504-L521](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/beads/beads.go#L504-L521)）。
- 表：`issues, dependencies, labels, comments, events, config, compaction_snapshots`。
- 不进版本历史的表：`wisps`（临时 issue）和 `leases`（[migrations 0019](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/storage/schema/migrations/0019_wisps_dolt_ignore.up.sql)、[0055](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/storage/schema/migrations/0055_move_leases_to_table.up.sql)）。
- 视图 `ready_issues`。
- 可选：git 提交前导出成受版本控制的 `issues.jsonl`（[hooks.go#L1514-L1566](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/cmd/bd/hooks.go#L1514-L1566)）。
- `bd remember` 写到 `config` 表的 `kv.memory.*` 键下。

**2 格式**：`issues` 表（[0001](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/storage/schema/migrations/0001_create_issues.up.sql)）：
```sql
id VARCHAR(255) PRIMARY KEY, content_hash VARCHAR(64),
title VARCHAR(500) NOT NULL, description TEXT NOT NULL, design TEXT NOT NULL,
acceptance_criteria TEXT NOT NULL, notes TEXT NOT NULL,
status VARCHAR(32) NOT NULL DEFAULT 'open', priority INT NOT NULL DEFAULT 2, assignee VARCHAR(255),
compaction_level INT DEFAULT 0, compacted_at DATETIME,
hook_bead VARCHAR(255) DEFAULT '', role_bead VARCHAR(255) DEFAULT '', agent_state VARCHAR(32) DEFAULT '',
```
依赖表主键是 `(issue_id, depends_on_id)`，`type` 默认 `'blocks'`。

**3 读者与写者**
- agent 和人都通过 `bd` CLI 读写同一个库：`bd ready / update --claim / assign / comment / close`（[coordination.md](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/docs/multi-agent/coordination.md)）。
- 跨机器同步用 `bd dolt push/pull`。

**4 强制机制**
- `bd prime` 输出一段写给 AI 的工作流说明，外加持久记忆，设计目的是 "prevent agents from forgetting bd workflow after context compaction"（[prime.go#L85-L125](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/cmd/bd/prime.go#L85-L125)）。
  - 可以用 `.beads/PRIME.md` 覆盖默认内容。
- `bd setup claude` 只注册 SessionStart，并删掉 PreCompact。理由：上下文压缩后 SessionStart 会以 `source=compact` 再触发一次（[setup/claude.go#L276-L300](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/cmd/bd/setup/claude.go#L276-L300)）。

**5 生命周期（压缩）**
- 状态：`open → in_progress → closed`，另有 `pinned` 和 `defer_until`。
- 分层压缩：关闭满 30 天为第 1 层，满 90 天为第 2 层（[compaction.go#L15-L85](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/storage/issueops/compaction.go#L15-L16)）。
- `CompactTier1` 的步骤（[compactor.go#L88-L172](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/compact/compactor.go#L88-L172)）：
  1. 调 Haiku 生成摘要，格式为 `**Summary:** / **Key Decisions:** / **Resolution:**`；
  2. 摘要不比原文短就放弃；
  3. 先把原文快照存进 `compaction_snapshots`，之后可用 `bd restore` 恢复；
  4. 覆盖 description，清空 design、notes、验收条件；
  5. 记录压缩层级和当时的 commit。
- `bd compact` 另外把 N 天前的 Dolt 历史压成一个提交（[compact_dolt.go](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/cmd/bd/compact_dolt.go)）。

**6 并发（重点）**
- **哈希 ID**：
  - 计算方式：`sha256("title|description|creator|纳秒时间|nonce")`，转 base36（[idgen/hash.go#L55-L85](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/idgen/hash.go#L55-L85)）。
  - 长度按生日悖论自适应：以当前 issue 数计算，碰撞概率不超过 0.25 的最短长度，取值 3 到 8 位（[helpers.go#L345-L395](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/storage/issueops/helpers.go#L345-L395)）。
  - 撞号时先换 nonce 重试 0 到 9 次，仍冲突再加长一位（[#L176-L215](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/storage/issueops/helpers.go#L176-L215)）。
  - 效果：多台机器离线各自建 issue 也不会撞号。
- **ready 队列**：视图用递归查询找出被 `blocks` 依赖阻塞的 issue，并沿父子关系往下传递，同时排除临时 issue 和延期 issue（[0044](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/storage/schema/migrations/0044_update_views_drop_depends_on_id.up.sql)）。
  - 排序：48 小时内新建的按优先级排，其余按创建时间从旧到新（[ready_work.go#L445-L468](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/storage/issueops/ready_work.go#L445-L468)）。
- **领取（CAS）**：`UPDATE … SET assignee=?, status='in_progress', row_lock=? WHERE id=? AND row_lock=? AND status IN (...)`（[claim.go#L36-L230](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/storage/issueops/claim.go#L36-L230)）。
  - 失败时返回 `ClaimConflictError`，里面带当前持有者。
  - 为什么需要 `row_lock`：Dolt 按单元格合并，两个写者改同一行的不同单元格不会冲突。所以规定每条改 status 或 assignee 的路径都必须同时换一个新的 `row_lock` 随机值，强制两边在这个单元格上冲突（[lease.go#L46-L100](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/storage/issueops/lease.go#L46-L100)）。
- **租约**：
  - TTL 5 分钟，靠心跳续期；
  - 存在不进版本历史的表里，所以心跳不会产生提交；
  - 只在授予租约的节点上有效；
  - `bd reclaim` 删除过期租约，把 issue 改回 open（[lease.go#L676-L762](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/storage/issueops/lease.go#L676-L762)）。
- **合并**：
  - `issues` 表按字段三方合并：只有一方改的字段取改动方；双方都改的取 `updated_at` 较晚的一方；`notes/metadata` 双方都改时拒绝自动合并（[automerge.go#L13-L50](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/storage/versioncontrolops/automerge.go#L13-L50)）。
  - `labels/comments/events` 取并集（[mergesettle.go#L429-L576](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/storage/versioncontrolops/mergesettle.go#L429-L576)）。
  - 解决冲突的工作用一个特殊 issue `<prefix>-merge-slot` 串行化，它的 metadata 里存持有者和等待者（[merge_slot.go#L80-L140](https://github.com/gastownhall/beads/blob/f56632adcfabed7da6ed0aabe4e760066b472c46/internal/storage/merge_slot.go#L80-L140)）。

**7 流转**
- 交接方式：`bd comment` 写一句加 `bd assign` 给下一个 agent，接手方再 claim。
- 被阻塞的 issue 在阻塞项关闭后自动进入 ready 队列。
- 没有消息通道，消息交给 mcp_agent_mail 或 gastown。

**读过的文件**：internal/idgen/hash.go，internal/types/id_generator.go，internal/storage/issueops/{helpers,claim,lease,ready_work,compaction,claim_next}.go（节选），internal/compact/{compactor,haiku}.go（节选），internal/storage/versioncontrolops/{mergesettle,automerge}.go，internal/storage/merge_slot.go，migrations 0001/0002/0010/0019/0025/0044/0054/0055，cmd/bd/{prime,agent_hook,compact_dolt,hooks}.go、cmd/bd/setup/claude.go（节选），docs/multi-agent/coordination.md，issues.jsonl（首行）。

---

## 5. gastownhall/gastown：多 agent 工作区管理器（beads 之上的角色、邮件、hook）

链接前缀 `G=https://github.com/gastownhall/gastown/blob/649b832b7672bc7a2dbef26f5983aba6198b819b/`（Go 模块路径仍是 `github.com/steveyegge/gastown`）

**1 存储**
- 所有协作状态都存成 beads：
  - 城镇级 `hq-*` 放 Mayor 邮件；
  - 每个 rig 一个库，按 ID 前缀路由（G/internal/templates/roles/polecat.md.tmpl#L171-L188）；
  - 每次写入都是一次 Dolt 提交（同文件 #L365）。
- 8 个角色：mayor、deacon、boot、witness、refinery、polecat、crew、dog（G/internal/cmd/prime.go#L53-L63）。每个角色有 TOML 配置和 prompt 模板（G/internal/config/roles/polecat.toml、G/internal/templates/roles/*.md.tmpl）。
- **邮件**：带 `gt:message` 标签的 bead，assignee 是收件人；`from/thread/reply-to/msg-type/queue/claimed-by` 等字段放在标签里（G/internal/mail/types.go#L298-L307）。
- **hook**：状态为 `hooked`、指派给某个 agent 的 bead，原文 "StatusHooked is the status for beads on an agent's hook (work assignment)"（G/internal/beads/handoff.go#L15-L23）；`gt hook` 称之为 "durability primitive"。
- **每个角色的交接 bead**：`pinned` 状态，标题为 `"<role> Handoff"`（G/internal/beads/handoff.go#L25-L105）。
- **convoy / merge-request**：convoy 在 bead 描述里用 `key: value` 行存字段（G/internal/beads/fields.go#L260-L300）；MR 是带 `gt:merge-request` 标签的临时 bead。
- **nudge 队列**：文件 `<town>/.runtime/nudge_queue/<session>/*.json`（G/internal/nudge/queue.go#L1-L9）。

**2 格式**
- 邮件结构 `Message{ID, From, To, Subject, Body, Priority, Type, Delivery, ThreadID, Wisp}`（G/internal/mail/types.go#L64-L96）。
- 协议消息靠主题前缀识别，如 `MERGE_READY <polecat>`，载荷为 `MergeReadyPayload{Branch, Issue, Polecat, Rig, Verified, Timestamp}`（G/internal/protocol/types.go#L19-L103）。
- 交接模板（G/internal/templates/messages/handoff.md.tmpl）：
```
## Current State
**Role**: {{ .Role }}
**Working on**: {{ .CurrentWork }}
**Status**: {{ .Status }}
## Next Steps
```
- merge slot 是 bead 描述里的 JSON `{"holder": "<actor>", "waiters": [...]}`（G/internal/beads/beads_merge_slot.go#L1-L10）。

**3 读者与写者**
- **polecat**：读自己 hook 上的工作（`gt prime` 的 `findAgentWork`，G/internal/cmd/prime.go#L743-L885）。完成时 `gt done` 写 MR bead，并 nudge refinery 和 witness（G/internal/cmd/done.go#L1884、#L1933）。模板规定每个会话 "mail budget is 0-1 messages"（polecat.md.tmpl#L540-L546）。
- **witness**：处理 POLECAT_DONE、HELP、HANDOFF，原文 "Beads over mail: survey-workers discovers completion state from agent bead metadata"（G/internal/formula/formulas/mol-witness-patrol.formula.toml）。
- **refinery**：merge queue 是它唯一的依据，原文 "Check beads merge queue (ONLY source of truth)"（G/internal/templates/roles/refinery.md.tmpl#L193-L199）。合并后发 MERGED。

**4 强制机制**
- Claude hook 模板（G/internal/hooks/templates/claude/settings-autonomous.json#L107-L140）：
  - `SessionStart` 和 `PreCompact` 调 `gt prime --hook`；
  - `UserPromptSubmit` 调 `gt mail check --inject`。
- `gt prime` 依次注入：角色模板 → hook 上的工作（有工作时进入 "AUTONOMOUS WORK MODE"）→ molecule 步骤 → 记忆 → 未读邮件（G/internal/cmd/prime.go#L124-L246）。
- 提示词里的推进原则："If you find something on your hook, YOU RUN IT."（polecat.md.tmpl#L257-L270）。
- 身份锁 `.runtime/agent.lock`，防止两个会话认领同一个身份（prime.go#L1200-L1249）。

**5 生命周期**
- **`gt handoff`**：收集状态 → 给自己发一封交接邮件（优先级 1，主题前缀 `HANDOFF:`）→ 重开窗格（G/internal/cmd/handoff.go#L30-L66）。
  - 注释写明交接邮件 "NOT ephemeral: handoff mail must be in issues table so gt hook can find it"（#L1262-L1322）。
  - 发新交接前先关闭上一次残留的交接邮件。
- **交接标记文件**：新会话读到后先删掉，再给出警告，防止新会话把上下文里残留的 `/handoff` 当成指令重复执行（G/internal/cmd/prime_session.go#L372-L393）。
- **协议消息自动存为临时 bead**（G/internal/mail/router.go#L826-L856）。
- **`gt mail drain`** 批量归档，原文 "HELP and HANDOFF messages are NEVER drained"（G/internal/cmd/mail_drain.go#L22-L29）。
- **`gt mol squash`** 把 molecule 压缩成一份摘要（G/internal/cmd/molecule_lifecycle.go#L138-L252）。

**6 并发**
- 每个 polecat 一个 git worktree。
- refinery 推送主干前拿 merge slot（G/internal/refinery/engineer.go#L697-L728）。推断：获取锁不是原子 CAS，靠每个 rig 只有一个 refinery 实例来保证。
- 合并冲突时建一个解决任务，把 MR 挂成被它阻塞，队列继续处理下一个，原文 "non-blocking delegation"（engineer.go#L1563-L1680）。
- nudge 队列用 rename 抢占条目；孤儿条目 5 分钟后放回队列（queue.go#L160-L240）。
- 邮件两阶段投递：`delivery:pending` → 注入上下文后改为 `delivery:acked`（G/internal/mail/delivery.go#L12-L40）。

**7 流转与唤醒**
- 发送邮件后异步通知收件人（G/internal/mail/router.go#L1592-L1700）：
  - 收件人空闲时，直接用 tmux 把消息敲进窗格；
  - 忙时进入 nudge 队列，由下一轮 `UserPromptSubmit` hook 取出。
- 兜底轮询：
  - 没有轮次 hook 的运行时由后台 poller 每 10 秒拉一次（G/internal/nudge/poller.go）；
  - 巡逻角色用 `gt mol await-signal` 读取 `~/gt/.events.jsonl` 的新增行，超时指数退避；
  - convoy 管理器每 5 秒或 30 秒扫描一次。
- 任务链：POLECAT_DONE → witness → MERGE_READY → refinery → MERGED → witness 清理（refinery.md.tmpl#L60-L75）。

**读过的文件**：internal/mail/{types,bd,store,router,delivery}.go（节选），internal/nudge/{queue,poller}.go，internal/cmd/{prime,prime_session,handoff,mail_check,nudge,done,hook,molecule_await_signal,molecule_lifecycle,remember}.go（节选），internal/beads/{handoff,beads_merge_slot,fields}.go，internal/protocol/types.go，internal/refinery/engineer.go，internal/convoy/operations.go，internal/daemon/{daemon,convoy_manager}.go，internal/config/roles/polecat.toml，internal/hooks/templates/claude/settings-autonomous.json，internal/templates/messages/handoff.md.tmpl，internal/templates/roles/{polecat,refinery}.md.tmpl，mol-witness-patrol.formula.toml。

---

## 6. jayminwest/overstory：多 agent 编排（SQLite 邮件、overlay、mulch 经验库）

链接前缀 `O=https://github.com/jayminwest/overstory/blob/ff38f3f76f084abcc34f519bcaa69580f6e53cf1/`

**1 存储**
- SQLite 三张表：
  - `.overstory/mail.db` 的 `messages`（O/src/mail/store.ts#L55-L68）；
  - `sessions`，记录 agent 状态机、父 agent、worktree（O/src/sessions/store.ts）；
  - `merge_queue`（O/src/merge/queue.ts）。
- `ov sling` 为每个 agent 在它的 worktree 里生成 `.claude/CLAUDE.md` overlay（O/templates/overlay.md.tmpl）。
- `.overstory/agents/<name>/` 下有 `identity.yaml / checkpoint.json / handoffs.json / applied-records.json`。
- 经验库 `.mulch/expertise/<domain>.jsonl` 进 git（O/.mulch/mulch.config.yaml）。

**2 格式**
- messages 表字段：`from_agent, to_agent, subject, body, type, priority CHECK(low|normal|high|urgent), thread_id, payload, read`。
- 消息类型：`status, question, result, error, worker_done, worker_died, merge_ready, merged, merge_failed, escalation, health_check, dispatch, assign, decision_gate`（O/src/types.ts#L293-L308）。
- overlay 片段（O/templates/overlay.md.tmpl）：
```
## Your Assignment
- **Agent Name:** {{AGENT_NAME}}
- **Task ID:** {{TASK_ID}}
- **Spec:** {{SPEC_PATH}}
- **Parent:** {{PARENT_AGENT}}
## File Scope (exclusive ownership)
{{FILE_SCOPE}}
```
- `SessionCheckpoint{agentName, taskId, sessionId, progressSummary, filesModified, currentBranch, pendingWork, mulchDomains}`（O/src/types.ts#L892-L902）。

**3 读者与写者**
- coordinator 读 manifest 和 mulch，用 sling 写 overlay 与 session（O/src/commands/prime.ts#L257-L359）。
- lead 被禁止写文件；每收到一个 `worker_done` 就发一个 `merge_ready`（O/agents/lead.md#L30-L85）。
- builder 只能改自己 file scope 内的文件，结束前要 `ml record`（O/agents/builder.md）。
- watchdog 在 agent 死亡时替它向父 agent 合成一封 `worker_died` 邮件（O/src/watchdog/daemon.ts#L366-L390）。

**4 强制机制**
- hook 模板（O/templates/hooks.json.tmpl）：
  - `SessionStart`：`ov prime --agent` + `ov mail check --inject`；
  - `UserPromptSubmit` / `PostToolUse`：`mail check --inject`（带防抖）；
  - `PreCompact`：`ov prime --compact`；
  - `Stop`：`ov log session-end` + `ml learn`；
  - `PreToolUse`：拦截 `git push`。
- prime 写入原文 "Do not wait for dispatch mail. Your assignment was bound at spawn time."（O/src/commands/prime.ts#L190-L250）。
- PreToolUse guard 在代码层面强制（O/src/agents/hooks-deployer.ts、O/src/agents/guard-rules.ts#L13-L24）：
  - 写入路径必须在本 worktree 内；
  - 禁用 Claude 原生的 Task/SendMessage；
  - merge_ready 数量不足时，lead 不能关闭任务。

**5 生命周期**
- `saveCheckpoint/initiateHandoff` 在 src/ 非测试代码中未找到调用方，只有 prime 会读 checkpoint（O/src/agents/checkpoint.ts、lifecycle.ts）。推断：checkpoint 功能还没接通。
- 会话状态机用 SQL 原子 CAS 迁移，`completed` 状态不再改变（O/src/sessions/store.ts#L20-L52）。
- mulch 上限：`max_entries: 100`、`hard_limit: 200`；过期：tactical 14 天、observational 30 天。

**6 并发**
- 每个 agent 一个 worktree。
- 规则原文 "Every file must have exactly one owner"（O/agents/lead.md#L33）。
- SQLite 用 WAL 模式，busy_timeout 5000 毫秒（O/src/mail/store.ts#L195-L202）。
- 合并锁 `.overstory/merge-<target>.lock` 用 `wx` 创建；持锁 PID 还活着就失败，已死则接管（O/src/merge/lock.ts）。
- 冲突解决分四级：clean-merge、auto-resolve、ai-resolve、reimagine（O/src/merge/queue.ts#L47-L55）。
- headless 模式下，每个 agent 同一时刻只跑一轮，靠 SQLite 实现的 turn lock 租约保证（O/src/agents/turn-lock.ts）。

**7 流转与唤醒**
- tmux 模式：高优先级邮件写入 `.overstory/pending-nudges/<agent>.json`，下一次 `mail check --inject` 时加 `PRIORITY:` 横幅（O/src/commands/mail.ts#L77-L141）。
- headless 模式：
  - `ov serve` 每 2 秒轮询 mail.db，有未读就用 `--resume` 起一轮新的 claude，退出码为 0 才标已读（O/src/agents/headless-mail-injector.ts#L110-L180）；
  - lead 的 prompt 禁止用 bash 循环等待，原文 "end your turn after dispatching … Worker mail arriving later will respawn you"（O/agents/lead.md#L66-L78）。
- 任务链：dispatch → sling builder → `worker_done` → lead 审查 → `merge_ready` → `ov merge` → `merged/merge_failed`。

**读过的文件**：src/mail/{store,client}.ts，src/commands/{prime,mail,nudge,sling,log,merge}.ts（节选），src/agents/{checkpoint,lifecycle,headless-mail-injector,turn-runner,turn-lock,guard-rules,hooks-deployer,overlay,identity}.ts（节选），src/sessions/store.ts，src/merge/{lock,queue}.ts，src/mulch/client.ts，src/watchdog/daemon.ts，src/types.ts（节选），templates/{hooks.json.tmpl,overlay.md.tmpl}，agents/{builder,lead,coordinator,supervisor}.md，.mulch/mulch.config.yaml，.mulch/expertise/mail.jsonl（首行）。

---

## 7. MrLesk/Backlog.md：git 里的 Markdown 任务板

链接前缀 `BL=https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/`

**1 布局**
- `backlog/` 目录下：
  - `config.yml`
  - `tasks/ drafts/ completed/ archive/{tasks,drafts,milestones}`
  - `decisions/decision-N - *.md`
  - `docs/doc-NNN - *.md`
  - `milestones/`
- 文件名形如 `back-200 - Title.md`，子任务形如 `back-222.1 - …`。
- 不用数据库。

**2 格式**
- 任务 frontmatter：
```yaml
id: BACK-200
status: To Do
assignee: []
updated_date: '2025-09-06 21:22'
dependencies:
  - task-24.1
priority: medium
```
- 正文用标记包住各节（[structured-sections.ts#L18-L23](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/markdown/structured-sections.ts#L18-L23)）：
  - `<!-- SECTION:DESCRIPTION|PLAN|NOTES|FINAL_SUMMARY:BEGIN/END -->`
  - 验收条件 `<!-- AC:BEGIN -->` … `- [ ] #1 …`
- 决策文件：`## Context / ## Decision / ## Consequences / ## Alternatives`（[serializer.ts#L130-L147](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/markdown/serializer.ts#L130-L147)）。

**3 读者与写者**
- agent 通过 `backlog` CLI 或 MCP 工具读写（[tools/tasks/index.ts#L25-L93](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/mcp/tools/tasks/index.ts#L25-L93)）。
- 禁止直接改文件，原文 "Do not edit Backlog task, draft, document, decision, or milestone markdown files directly. Use the backlog CLI"（[cli-agent-nudge.md](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/guidelines/cli-agent-nudge.md)）。
- 人用终端看板或 Web 界面。

**4 强制机制**
- 往 AGENTS.md、CLAUDE.md、GEMINI.md、copilot-instructions 里写一个带 `<!-- BACKLOG.MD GUIDELINES START/END -->` 标记的受管区块（[agent-instructions.ts#L10-L136](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/agent-instructions.ts#L10-L13)）。
- 区块要求每次对话开始先运行 `backlog instructions overview`。
- 任务上可以配 `onStatusChange` 命令，状态变化时执行，命令失败也不阻止状态变更（[backlog.ts#L2844-L2880](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/core/backlog.ts#L2844-L2880)）。
- 未找到 Claude Code hook。

**5 生命周期**
- 执行规程（[task-execution.md](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/guidelines/mcp/task-execution.md)）：
  1. 开工时改成 In Progress，并指派给自己；
  2. 实现前写 `planSet`，原文标注 "Non-negotiable"；
  3. 过程中用 `notesAppend` 记笔记；
  4. 讨论写进 `commentsAppend`。
  - 原文："You may be interrupted or replaced at any point, so the task record must contain everything needed for a clean handoff."
- 收尾：写 Final Summary，改为终态；终态任务由定期清理移到 `completed/`，原文 "Do not archive completed work"（[task-finalization.md#L20-L23](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/guidelines/cli-instructions/task-finalization.md#L20-L23)）。
- 移动文件用 `rename`，让 git 识别为移动（[operations.ts#L1071-L1119](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/file-system/operations.ts#L1071-L1119)）。
- 未找到压缩机制。

**6 并发（重点）**
- **建任务锁**：放在 git common dir 的 `backlog.md/locks/create`，所有 worktree 共用一把，保证 ID 分配串行（[operations.ts#L599-L636](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/file-system/operations.ts#L599-L636)）。
- **单任务锁**：`backlog/.locks/task-<id>`，`retries: 0`，拿不到立即失败，原文 "nothing is merged or overwritten behind their back"（[#L638-L660](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/file-system/operations.ts#L638-L660)）。
- **批量操作**：先排序再加锁，避免死锁。
- **ID 分配**：扫描本地和远端最近活跃的分支，以及所有 worktree（[backlog.ts#L1500-L1605](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/core/backlog.ts#L1500-L1605)）。
- **同一任务在不同分支上内容不同时**，默认 `most_progressed`（[task-identity-index.ts#L124-L143](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/core/task-identity-index.ts#L124-L143)）：
  - 当前工作区的副本优先；
  - 其次取状态在 `statuses` 列表中位置更靠后（更接近完成）的；
  - 再比最后修改时间；
  - 这个选择只在读取时做，不回写。
- **自动提交**：`auto_commit` 开启时最多重试 3 次，每次提交前检查暂存内容仍是自己写的（[git/operations.ts#L655-L697](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/git/operations.ts#L655-L697)）。

**7 流转**
- 没有消息通道。任务文件本身就是交接文档：状态、指派、计划、笔记、评论、Final Summary。
- `task list --ready` 在读取时计算依赖是否就绪（[readiness.ts#L66-L105](https://github.com/MrLesk/Backlog.md/blob/c0ec546a3b519c0c7b83070fe936f6bf49e14357/src/utils/readiness.ts#L66-L105)）。

**读过的文件**：backlog/config.yml，backlog/tasks/back-200 …md，src/markdown/{structured-sections,serializer}.ts，src/file-system/operations.ts（L596-760、1066-1125），src/core/{backlog,cross-branch-tasks,task-loader,task-identity-index,duplicate-task-repair}.ts（节选），src/utils/readiness.ts，src/git/operations.ts，src/agent-instructions.ts，src/guidelines/{cli-agent-nudge.md,mcp/agent-nudge.md,mcp/task-execution.md,cli-instructions/task-finalization.md}，src/mcp/tools/*/index.ts，.gitattributes。

---

## 8. github/spec-kit

链接前缀 `S=https://github.com/github/spec-kit/blob/d848fb4e18f44640ad6b42e60a280551ee90cdce/`

**1 布局**
- 项目级只有一份宪法 `.specify/memory/constitution.md`；CLI 会把模板里的 `memory/` 路径改写成这个位置（S/src/specify_cli/agents.py#L205）。
- 每个特性一个目录 `specs/<NNN>-<short-name>/`，包含 `spec.md, plan.md, research.md, data-model.md, quickstart.md, contracts/, tasks.md, checklists/`（S/templates/plan-template.md#L49-L57）。
- "当前是哪个特性"记在指针文件 `.specify/feature.json`（`{"feature_directory": ...}`，S/scripts/bash/common.sh#L131-L161）。

**2 格式**
- 任务行格式（S/templates/tasks-template.md#L16-L20）：
```
## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
```
- plan 模板里的门槛：`## Constitution Check` / `*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*`（S/templates/plan-template.md#L39-L43）。
- 宪法末行：`**Version**: … | **Ratified**: … | **Last Amended**: …`。
- 写进 agent 上下文文件的受管区块用 `<!-- SPECKIT START -->` / `<!-- SPECKIT END -->` 标记（S/extensions/agent-context/scripts/bash/update-agent-context.sh#L21-L22）。

**3 读者与写者**：每条命令相当于一个角色。

| 命令 | 读 | 写 |
|---|---|---|
| constitution | 模板、现有宪法 | 只写 constitution.md |
| specify | 宪法 | spec.md、feature.json |
| clarify | spec.md | 回写 spec.md 的 `## Clarifications / ### Session YYYY-MM-DD` |
| plan | spec、宪法 | plan/research/data-model/contracts/quickstart |
| tasks | plan、spec | tasks.md |
| analyze | 全部 | 不写，原文 "STRICTLY READ-ONLY"（S/templates/commands/analyze.md#L58） |
| converge | 全部 | 只追加 `## Phase N: Convergence` |
| implement | 全部 | 代码，并在 tasks.md 里打 `[X]` |

**4 强制机制**
- slash command 的 frontmatter `scripts:` 先跑 shell 脚本，检查前置文件是否存在，例如 `check-prerequisites.sh --require-tasks` 缺文件时报 `ERROR: plan.md not found`（S/scripts/bash/check-prerequisites.sh#L146）。
- frontmatter `handoffs:` 声明下一步交给哪个命令（S/templates/commands/specify.md#L3-L10）。
- 扩展的 `hooks.before_*/after_*` 不是宿主强制执行的，而是 prompt 要求模型去读 `extensions.yml` 后自己调用（S/templates/commands/plan.md#L27-L58）。

**5 生命周期**
- agent-context 扩展在 `after_specify/after_plan` 时只替换受管区块内的内容。
- 宪法修订按语义版本号递增，并生成临时的 Sync Impact Report（S/templates/commands/constitution.md#L100-L125）。
- 特性目录：未找到归档；spec 的 `Status: Draft` 也没有找到后续状态迁移的逻辑。

**6 并发**
- 编号取 `specs/` 下现有最大值加 1，冲突时顺延（S/scripts/bash/create-new-feature.sh#L290-L328）；目标目录已存在则报错。
- 没有锁。推断：`feature.json` 是整个仓库共用一个指针，同一工作目录里并行做两个特性时，后写的会覆盖先写的。可用 `SPECIFY_FEATURE_DIRECTORY` 环境变量绕开（S/scripts/bash/common.sh#L181-L206）。

**7 流转**
- 顺序：specify → clarify → plan → tasks → analyze → implement，交接物就是特性目录里的文件。
- implement 规定改同一文件的任务串行执行。
- `taskstoissues` 把任务转成 GitHub issue，用 `T\d{3,}` 去重。

**读过的文件**：templates/{constitution,spec,plan,tasks}-template.md，templates/commands/{specify,plan,implement,constitution,clarify,analyze,tasks,converge,taskstoissues}.md（全文或节选），scripts/bash/{create-new-feature,common,check-prerequisites,setup-plan}.sh，extensions/agent-context/{extension.yml,scripts/bash/update-agent-context.sh}，extensions/git/extension.yml，src/specify_cli/agents.py（grep）。

---

## 9. bmad-code-org/BMAD-METHOD（v6.12.0）

链接前缀 `B=https://github.com/bmad-code-org/BMAD-METHOD/blob/94b6727b00c8316557828c8a8ff2a48ff60d60cc/`

**与任务假设不符的地方（已核实）**
- SM agent 和 QA agent 已删除（B/removals.txt#L6-L9，B/CHANGELOG.md#L369）。
- `bmad-shard-doc` 已删除（B/CHANGELOG.md#L38）。
- `create-story → dev-story` 已弃用，当前第 4 阶段是 `bmad-sprint-planning → bmad-build → bmad-code-review`（B/CHANGELOG.md#L26,#L37）。
- 结论："SM→Dev→QA" 交接在当前代码里已不存在。

**1 布局**
- `_bmad-output/planning-artifacts`：PRD 运行目录（`prd.md`、`.memlog.md`）、架构、`epics.md`。
- `_bmad-output/implementation-artifacts`：`sprint-status.yaml`、每个故事一份 `spec-<slug>.md`、缓存 `epic-<N>-context.md`、`deferred-work.md`。
- 路径定义见 B/skills/bmad/assets/config.template.toml#L1-L8。

**2 格式**
- sprint-status（B/skills/bmad-sprint-planning/sprint-status-template.yaml#L45-L58）：
```yaml
development_status:
  epic-1: backlog
  1-1-user-authentication: done
  1-2-account-management: ready-for-dev
  epic-1-retrospective: optional
```
- 故事 spec frontmatter：`status: 'draft' # draft | ready-for-dev | in-progress | in-review | done`，另有 `route`、`review_loop_iteration`、`context: []`（B/skills/bmad-build/spec-template.md#L1-L9）。
- 冻结区块：`<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">`（#L16）。
- 三个只追加的节：`## Implementation Notes / ## Spec Change Log / ## Review Triage Log`（#L66-L84）。
- epic-context 有预算：800–1500 token（B/skills/bmad-build/compile-epic-context.md）。

**3 读者与写者**
- sprint-status 只能通过 `sprint_plan.py` 写（B/skills/bmad-sprint-planning/SKILL.md#L8）。
- 实现子 agent 原文 "no prior conversation context"，只读 spec 和 `context:` 里列出的文件（B/skills/bmad-build/customize.toml#L79-L85）。
- 评审子 agent 只拿 diff 路径（B/skills/bmad-build/step-04-review.md#L14-L24）。
- PRD 过程中每个决定都 `memlog.py append` 一行（B/skills/bmad-prd/SKILL.md#L14）。

**4 强制机制**
- step 文件逐个加载，原文 "NEVER load multiple step files simultaneously"；每步开头检查前置条件（PRECONDITION），不满足就停（HALT）（B/skills/bmad-build/workflow.md#L57-L80）。
- 确定性状态交给 Python 脚本处理。
- 定制用 `customize.toml` 三层合并：默认 → 团队 → 个人。
- 未找到 hook 或 MCP。

**5 生命周期**
- 状态迁移：spec 从 draft → ready-for-dev（人批准后冻结区块生效）→ in-progress（同时 sprint 置为 in-progress，所在 epic 自动变 in-progress）→ in-review → done（B/skills/bmad-build/sync-sprint-status.md，step-03-implement.md#L20-L26）。
- 重新生成 sprint-status 时，状态 "never downgrade"（sprint_plan.py#L241-L252）。
- epic-context 缓存的失效条件：planning 目录里有文件比它新（step-01#L56）。
- memlog 只追加。
- 未找到归档；控制上下文大小靠两点：epic-context 提炼，spec 限制在 900–1600 token。

**6 并发**
- `sprint_plan.py` 原子写入：临时文件 + fsync + `os.replace`，写后校验不通过则恢复原字节（#L325-L344,#L445-L457）。
- 未找到文件锁。
- step-01 要求工作树干净（#L79）。
- 批准前重新读盘，采纳外部修改（step-02-plan.md#L59）。
- 推断：故事状态同时存在 spec frontmatter 和 sprint-status 两处，只靠流程约定保证一致。

**7 流转**
- 故事 spec 是实现子 agent 的 "sole source of truth"。
- 评审分三层并行，结果写进 Triage Log，按类型分流：
  - `intent_gap`：交回人；
  - `bad_spec`：回滚代码、改 spec、重新实现；
  - `patch`：发回实现子 agent；
  - `defer`：记入 deferred-work.md；
  - 回环超过 5 次升级给人（step-04-review.md#L54-L80）。
- `bmad-build-auto` 按 `stories.yaml` 调度，停下时把 `blocked` 和原因写回故事文件（B/skills/bmad-build-auto/workflow.md#L1-L40）。

**读过的文件**：removals.txt，CHANGELOG.md（节选），skills/bmad/{assets/config.template.toml,scripts/memlog.py}，bmad-sprint-planning/{SKILL.md,sprint-status-template.yaml,references/generate-tracking.md,scripts/sprint_plan.py}，bmad-build/{workflow.md,step-01..05,spec-template.md,sync-sprint-status.md,compile-epic-context.md,customize.toml}，bmad-build-auto/workflow.md，bmad-code-review/step-04-present.md，bmad-project-context/{SKILL.md,references/template.md}，bmad-spec/assets/stories-schema.md，bmad-retrospective/workflow.md，bmad-correct-course/SKILL.md，bmad-prd/SKILL.md。

---

## 10. buildermethods/agent-os（v3.0）

链接前缀 `A=https://github.com/buildermethods/agent-os/blob/475b0cac4c7c5cf2336ad5a663b691a6d3415e05/`

- **1 布局**：
  - `agent-os/standards/<folder>/<name>.md` + `standards/index.yml`；
  - `agent-os/product/{mission,roadmap,tech-stack}.md`；
  - `agent-os/specs/YYYY-MM-DD-HHMM-<slug>/{plan,shape,standards,references}.md`（A/commands/agent-os/shape-spec.md#L181-L192）。
  - v3 已删除实现和编排两个阶段，原文 "frontier models handle this well on their own now"（A/CHANGELOG.md [3.0]）。
- **2 格式**：
  - index.yml 是三层结构 `folder → file → description`（A/commands/agent-os/index-standards.md#L68-L72）；
  - shape.md 分 `## Scope / ## Decisions / ## Context / ## Standards Applied`；
  - 所有文件都没有 frontmatter，也没有状态字段。
- **3 读写**：
  - `/discover-standards` 读代码，经用户逐条确认后写 standards；
  - `/shape-spec` 读 product 和 index，写 spec 目录；
  - `/inject-standards` 选择贴全文还是输出 `@agent-os/standards/...` 引用（A/commands/agent-os/inject-standards.md#L92-L226）。
- **4 强制**：
  - 只有 slash command 的 prompt；
  - `shape-spec` 必须在 plan mode 下运行（#L11-L23），并规定 "Task 1 always being 'Save spec documentation'"（#L125-L157），让批准后第一步就把 spec 落盘；
  - 未找到 hook。
- **5 生命周期**：spec 写完不再改动，原文 "months later, someone can find this spec"；未找到状态迁移。
- **6 并发**：
  - 没有锁；
  - 项目回推到 profile 时用 `sync-to-profile.sh` 检测冲突，冲突文件备份到 `.backups/<时间戳>/`（A/scripts/sync-to-profile.sh#L352-L451）。
- **7 流转**：未找到多 agent 设计。

**读过的文件**：config.yml，README.md，CHANGELOG.md，commands/agent-os/{shape-spec,inject-standards,index-standards,discover-standards,plan-product}.md（全文），scripts/project-install.sh（节选），scripts/sync-to-profile.sh（节选）。

---

## 11. gemini-cli-extensions/conductor（0.3.0）

链接前缀 `C=https://github.com/gemini-cli-extensions/conductor/blob/6e8f9a860bcdd6a2c423473c12e745200688c633/`

- **1 布局**：
  - `conductor/` 下有 `index.md`（称作 "Handshake"、"Single Source of Truth"）、`product.md, product-guidelines.md, tech-stack.md, workflow.md, code_styleguides/`；
  - 注册表 `tracks.md`；
  - 每个 track 一个目录 `tracks/<shortname_YYYYMMDD>/{spec.md, plan.md, metadata.json, index.md}`；
  - 归档到 `archive/<track_id>/`（C/skills/conductor-setup/SKILL.md#L196-L226，C/skills/conductor-new-track/SKILL.md#L144-L168）。
- **2 格式**：
  - tracks.md 条目：`- [ ] **Track: <desc>** *Link: [...](<track index.md>)*`；
  - plan.md 任务状态有三种：`[ ]` 未开始、`[~]` 进行中、`[x]` 完成；完成的任务后面追加 7 位提交 SHA，阶段标题后追加 `[checkpoint: <sha>]`（C/skills/conductor-setup/assets/workflow.md#L80-L90）。
- **3 读写**：
  - setup 写项目级文件；
  - new-track 写 spec、plan、metadata，并在注册表追加一行；
  - implement 改注册表和 plan 的复选框，完成后逐项询问用户是否回写 product/tech-stack（C/skills/conductor-implement/SKILL.md#L94-L127）；
  - review 把 styleguides 当作 "the **Law**"，用 plan 里的 SHA 圈定 diff 范围，结论追加为 `## Phase: Review Fixes`。
- **4 强制**：
  - 每个 skill 开头先读 `conductor/index.md` 并确认链接的文件都存在，缺文件就停下（implement/SKILL.md#L22-L37）；
  - `workflow.md` 写死 TDD 和每个任务单独提交；
  - 未找到 hook 或 MCP。
- **5 生命周期**：
  - 任务级：`[ ]` → `[~]` → 提交代码 → 用 `git notes` 挂上任务摘要 → plan 标 `[x]` 并记 SHA → plan 单独提交；
  - track 级：完成后可归档、删除或跳过；
  - 推断：metadata.json 的 status 只在创建时写入，之后没有代码更新它。
- **6 并发**：
  - 没有锁，完全靠 git 提交；
  - revert 能处理历史被改写后 SHA 失效的 "Ghost commits"：按提交信息相似度匹配，再由用户确认（C/skills/conductor-revert/SKILL.md#L75）；
  - 推断：tracks.md 是全局唯一注册表，多个分支同时修改会产生合并冲突。
- **7 流转**：在同一会话里依次切换角色（setup → new-track → implement → review），状态保存在复选框、SHA 和 git notes 里。

**读过的文件**：plugin.json，VERSION，.claude-plugin/marketplace.json，rules/conductor_antigravity.md，skills/conductor-setup/{SKILL.md,scripts/resume.py,assets/workflow.md}，skills/conductor-{new-track,implement,review,status,revert}/SKILL.md（全文）。

---

## 12. automazeio/ccpm

链接前缀 `CC=https://github.com/automazeio/ccpm/blob/7d7e4623bc6d4c0c9ba66ca6bfecd7e5261dc697/`；v1 快照 `CV=https://github.com/automazeio/ccpm/blob/1cb9483a74eb923fcd6c60de385bf2a0ac9c9a09/`

当前 HEAD（2026-03-18，"v2: relaunch as Agent Skills-compatible skill"）已删掉 `context/` 系列命令和 `parallel-worker` agent。这两部分读的是 v1 快照。

- **1 布局**：`.claude/` 下有 `prds/<name>.md`、`epics/<name>/{epic.md, <N>.md, <N>-analysis.md, github-mapping.md, execution-status.md}`、`updates/<N>/stream-X.md`、`epics/archived/`、`context/`（CC/skill/ccpm/references/conventions.md#L9-L28）。v1 的 `/context:create` 生成 9 份 context 文件（CV/ccpm/commands/context/create.md#L78-L96）。
- **2 格式**：任务文件 frontmatter（CC/skill/ccpm/references/conventions.md#L57-L68）：
```yaml
name: <Task Title>
status: open | in-progress | closed
github: https://github.com/<owner>/<repo>/issues/<N>
depends_on: []
parallel: true
conflicts_with: []   # issue numbers that touch the same files
```
- **3 读写**：
  - 主会话写 PRD、epic、analysis；
  - 每个 stream 子 agent 读任务文件和 analysis，只写自己那份 `stream-<X>.md`（CC/skill/ccpm/references/execute.md#L125-L134）。
- **4 强制**：
  - 只有 prompt，要求 "Before doing anything, read `references/conventions.md`"；
  - 只读查询先用 bash 脚本（Script-First Rule）；
  - v1 靠人手动运行 `/context:prime` 和 `/context:update`（CV/ccpm/commands/context/update.md#L7）。
- **5 生命周期**：
  - 同步到 GitHub 后，任务文件改名为 issue 号，依赖里的编号用 sed 替换（CC/skill/ccpm/references/sync.md#L71-L79）；
  - 进度作为 issue 评论发出，发出后在本地加 `<!-- SYNCED: <datetime> -->` 防止重发（#L126-L155）；
  - epic 合并后整个目录移到 `archived/`。
- **6 并发**：
  - 没有锁；
  - analysis 文件是 "the contract"，规定哪个 stream 管哪些文件；
  - 改共享文件前先 `git status`，被占用就 `sleep 30`；
  - 冲突时原文 "Never attempt automatic merge resolution"（CV/ccpm/rules/agent-coordination.md#L30-L121）。
  - 推断：`.claude/epics/` 在主 checkout 里，而 agent 在 worktree 里用相对路径写进度，文件实际写到哪里没有说明。
- **7 流转**：
  - v1 的 parallel-worker 只做协调、不写代码，原文 "Each sub-agent works independently - they don't communicate directly"（CV/ccpm/agents/parallel-worker.md#L19-L150）；
  - GitHub issue 是对外的权威状态，本地文件是镜像；
  - `next.sh` 只看 `depends_on` 是否为空，不检查依赖的 issue 是否已关闭（CC/skill/ccpm/references/scripts/next.sh）。

**读过的文件**：skill/ccpm/SKILL.md，references/{conventions,structure,execute,sync,track}.md，references/scripts/{next,standup,validate}.sh，CHANGELOG.md；v1：ccpm/agents/parallel-worker.md，ccpm/commands/context/{create,update,prime}.md，ccpm/rules/agent-coordination.md。

---

## 13. eyaltoledano/claude-task-master

链接前缀 `TM=https://github.com/eyaltoledano/claude-task-master/blob/c0c98d367c55296bfe69e65680625b6db437af02/`

- **1 布局**：
  - `.taskmaster/tasks/tasks.json` 是唯一的任务库；
  - 另有 `config.json`、`state.json`（记录当前 tag）、`reports/task-complexity-report.json`、`docs/prd.txt`（TM/packages/tm-core/src/common/constants/paths.ts#L7-L34）；
  - autopilot 状态不在仓库里，存在 `~/.taskmaster/{project-id}/sessions/workflow-state.json`。
- **2 格式**：
  - tasks.json 按 tag 分区：`{ master: { tasks: [...], metadata: {...} } }`（TM/scripts/modules/utils.js#L638-L646）；
  - Task 字段：`id, title, description, status, priority, dependencies, details, testStrategy, subtasks, complexity, metadata`；
  - status 取值：`pending | in-progress | done | deferred | cancelled | blocked | review | completed`（TM/packages/tm-core/src/common/types/index.ts#L20-L170）。
- **3 读写**：
  - 只通过 CLI 或 MCP 写；
  - 插件自带三个 agent：orchestrator 派发任务，executor 用 `update-subtask` 记笔记，checker 核验处于 review 状态的任务（TM/packages/claude-code-plugin/agents/）。
- **4 强制**：
  - 约 36 个 MCP 工具，默认 `core` 档只开 7 个（TM/mcp-server/src/tools/tool-registry.js#L110-L118）；
  - 加上规则文件 `dev_workflow.mdc`；
  - 未找到 hook。
- **5 生命周期**：
  - `update-subtask` 只追加：把新内容包进 `<info added on ISO>…</info added on ISO>` 接到 details 末尾（TM/scripts/modules/task-manager/update-subtask-by-id.js#L355-L360）；
  - 按 git 分支自动切换 tag 的功能已禁用（TM/scripts/modules/utils/git-utils.js#L300-L308）；
  - 未找到归档。
- **6 并发**：
  - 旧写入路径 `withFileLock`：用 `wx` 创建 `.lock`，10 秒算过期，最多 5 次指数退避重试（TM/scripts/modules/utils.js#L80-L181）；
  - 新写入路径 tm-core：proper-lockfile 加锁，steno 原子写，`modifyJson` 在锁内重读再改（TM/packages/tm-core/src/modules/storage/adapters/file-storage/file-operations.ts#L108-L179）；
  - 推断：已标 deprecated 的 `writeJSON` 在锁内会把当前 tag 整块替换，同一 tag 内并发写会丢更新，而 `scripts/modules` 里仍有 29 处调用；
  - 复杂度报告写入不加锁；
  - 官方建议每人或每个分支用一个 tag，避免合并冲突。
- **7 流转**：
  - 没有消息通道；
  - orchestrator 派发时用固定模板 `TASK ASSIGNMENT: Task ID / Objective / Dependencies / Success Criteria / Context / Reporting`（TM/packages/claude-code-plugin/agents/task-orchestrator.md#L69-L78）；
  - 状态路径：pending → in-progress → review → done。

**读过的文件**：packages/tm-core/src/common/{constants/paths.ts,types/index.ts}，.../storage/adapters/file-storage/file-operations.ts，.../workflow/managers/workflow-state-manager.ts，scripts/modules/{utils.js,utils/git-utils.js}，scripts/modules/task-manager/{analyze-task-complexity,update-subtask-by-id}.js，mcp-server/src/tools/{tool-registry,index}.js，packages/claude-code-plugin/agents/{task-orchestrator,task-executor,task-checker}.md，assets/rules/dev_workflow.mdc。

---

## 14. humanlayer/humanlayer：thoughts/ 与 research→plan→implement

链接前缀 `H=https://github.com/humanlayer/humanlayer/blob/99abe673498cf8bdcd5f989aebe9406a27185b3b/`

- **1 布局**：
  - 真实存储是独立的 git 仓库 `~/thoughts`，内部分 `repos/<repo>/{<user>,shared}` 和 `global/{<user>,shared}`（H/hlyr/src/thoughtsConfig.ts#L38-L40,#L310-L322）；
  - 代码仓库里的 `thoughts/` 只是符号链接：`<user>/`、`shared/`、`global/`；
  - `thoughts/searchable/` 是硬链接索引，每次 sync 全量重建（H/hlyr/src/commands/thoughts/sync.ts#L101-L196），原因原文 "search tools can find content without following symlinks"（H/hlyr/src/commands/thoughts/init.ts#L148-L162）；
  - 约定子目录 `shared/{research,plans,tickets,prs,handoffs/ENG-XXXX}`。
- **2 格式**：
  - research frontmatter（H/.claude/commands/research_codebase.md#L100-L111）：
```yaml
date: [ISO with timezone]
researcher: ...
git_commit: [hash]
branch: ...
topic: "[User's Question/Topic]"
tags: [research, codebase, ...]
status: complete
last_updated: YYYY-MM-DD
```
  - handoff 分节：`## Task(s) / Critical References / Recent changes / Learnings / Artifacts / Action Items & Next Steps / Other Notes`（H/.claude/commands/create_handoff.md#L28-L65）；
  - plan 每个 Phase 的成功标准分 Automated 和 Manual 两组（H/.claude/commands/create_plan.md#L172-L240）。
- **3 读写**：
  - research/plan/handoff 三个命令写 `shared/`；
  - `/implement_plan` 在 plan 里勾选完成项；
  - `/resume_handoff` 要求 "do NOT use a sub-agent to read these critical files"（H/.claude/commands/resume_handoff.md#L13-L28）；
  - 只读子 agent `thoughts-locator` 负责检索；
  - 人在个人区写。
- **4 强制**：
  - 每个写文档的命令结尾都要求运行 `humanlayer thoughts sync`；
  - git hook：pre-commit 拒绝把 `thoughts/` 提交进代码仓库，post-commit 在后台自动 sync，worktree 中跳过（H/hlyr/src/commands/thoughts/init.ts#L218-L260）。
- **5 生命周期**：
  - research 的追问追加到同一文档，更新 `last_updated`，并新增 `## Follow-up Research [timestamp]` 节；
  - handoff 本身就是压缩手段，原文 "compact and summarize your context"，同一 ticket 取最新的一份；
  - sync 流程：`add -A → commit → pull --rebase → push`（sync.ts#L32-L99）；
  - 未找到归档。
- **6 并发**：
  - 按用户分区，个人区只有本人写；`shared/` 交给 git 处理；
  - rebase 冲突时提示 "Please resolve conflicts manually" 并 exit 1；
  - 另有一套 Yjs/ElectricSQL 协同编辑表（H/packages/database/schema/thoughts.ts）。推断：这是实验，与 CLI 的 git 同步不相通。
- **7 流转**：
  - Linear 状态机："Research Needed → Research in Progress → Research in Review → Ready for Plan → Plan in Progress → Plan in Review → Ready for Dev → In Dev"（H/.claude/commands/linear.md#L296-L310）；
  - `ralph_research` 取对应状态列里优先级最高的小 ticket，写完文档后 sync，把链接挂到 ticket 上并推进状态（H/.claude/commands/ralph_research.md#L7-L55）；
  - `ralph_impl` 建 worktree，并启动一个运行 `/implement_plan` 的新会话（H/.claude/commands/ralph_impl.md#L23-L31）。

**读过的文件**：hlyr/src/commands/thoughts/{init,sync,status}.ts，hlyr/src/{thoughtsConfig,config}.ts，.claude/commands/{research_codebase,implement_plan,create_handoff,ralph_research,ralph_plan,ralph_impl,create_plan,resume_handoff,linear}.md，.claude/agents/thoughts-locator.md，.claude/settings.json，hack/spec_metadata.sh，packages/database/schema/thoughts.ts，apps/react/src/index.tsx。

---

## 15. Yeachan-Heo/oh-my-claudecode

链接前缀 `OM=https://github.com/Yeachan-Heo/oh-my-claudecode/blob/5281b19e0d64f8e6dc6767f2130299a88af2dc71/`

- **1 布局**：
  - `.omc/` 下有 `notepad.md, project-memory.json, notepads/<plan>/, plans/, research/, handoffs/`，以及 `state/sessions/{id}/, state/shared-memory/, state/team/{team}/`（OM/src/lib/worktree-paths.ts#L34-L49）；
  - team 目录包含 `config.json, tasks/task-{id}.json, workers/{name}/{heartbeat,status}.json, inbox.md, outbox.jsonl, events.jsonl, checkpoints/`（OM/src/team/state-paths.ts#L9-L160）。
- **2 格式**：
  - notepad 模板（OM/src/hooks/notepad/index.ts#L10-L23）：
```markdown
# Notepad
## Priority Context
<!-- ALWAYS loaded. Keep under 500 chars. Critical discoveries only. -->
## Working Memory
<!-- Session notes. Auto-pruned after 7 days. -->
## MANUAL
<!-- User content. Never auto-pruned. -->
```
  - team 任务文件：`{id, subject, description, status, owner, blocks, blockedBy, claimedBy?, claimedAt?, claimPid?}`（OM/src/team/types.ts#L39-L73）；
  - 阶段交接文档 `.omc/handoffs/<stage>.md` 分 `Decided / Rejected / Risks / Files / Remaining` 五项，限 10–20 行（OM/skills/team/SKILL.md#L153-L190）。
- **3 读写**：
  - notepad 通过 MCP 写（OM/src/tools/notepad-tools.ts#L120-L228）；
  - project-memory 有三个写入来源：SessionStart 检测、PostToolUse 的 learner、MCP 工具；
  - team 的 lead 写阶段状态和 handoff；
  - executor 把学到的东西追加进 `notepads/{plan}`。
- **4 强制**：hook 注入（OM/hooks/hooks.json）：
  - SessionStart 把项目记忆包成 `<project-memory-context>`、把 Priority Context 包成 `<notepad-context>` 注入（OM/scripts/session-start.mjs#L1225-L1262）；
  - PreCompact 在压缩后重新注入项目记忆和用户指令（OM/src/hooks/project-memory/pre-compact.ts#L29-L69）。
- **5 生命周期**：
  - Working Memory 条目 7 天后清理（OM/src/hooks/notepad/index.ts#L391-L452）；
  - project-memory 超过 24 小时重新扫描，合并时保留 customNotes、userDirectives、hotPaths；
  - shared-memory 按 TTL 过期；
  - team 阶段：`team-plan → team-prd → team-exec → team-verify → team-fix`，fix 次数有上限，取消后 handoff 保留（OM/skills/team/SKILL.md#L226-L280）。
- **6 并发**：
  - 锁用 `O_EXCL` 创建，过期要同时满足"超龄"和"持有 PID 已死"（OM/src/lib/file-lock.ts#L61-L80）；
  - notepad 在锁内重读，再原子写；
  - shared-memory 等锁 500 毫秒，拿不到就不加锁直接写（OM/src/lib/shared-memory.ts#L198-L204）；
  - 推断：project-memory 的 MCP 写和 SessionStart 重扫都不加锁，会丢更新；
  - CLI worker 用 O_EXCL 抢任务锁，在锁内复核 owner 和 blockedBy（OM/src/team/task-file-ops.ts#L290-L338）；
  - 原生 team 模式下，文档写明 "there is no atomic claiming"，改为由 lead 预先分配（OM/skills/team/SKILL.md#L318）。
- **7 流转**：
  - worker：CLAIM → WORK → COMPLETE → 给 lead 发消息；失败时不标完成；结束走 shutdown 握手（SKILL.md#L428-L476）；
  - lead 启动下一阶段前读上一阶段的 handoff；
  - CLI worker 用 JSONL inbox/outbox 加偏移游标（OM/src/team/inbox-outbox.ts#L25-L50）；
  - 发现一处路径不一致：inbox/outbox 在 `~/.claude/teams/...`，而 state-paths 定义在 `.omc/state/team/...`，哪个是现行的未核实；
  - `OMC_RUNTIME_V2=1` 时改为事件驱动，事件写入 `events.jsonl`。

**读过的文件**：hooks/hooks.json，src/hooks/notepad/index.ts，src/hooks/project-memory/{types,storage,index,pre-compact,learner,constants}.ts，src/lib/{shared-memory,file-lock,worktree-paths}.ts，src/tools/{notepad-tools,shared-memory-tools,memory-tools,state-tools}.ts，src/team/{state-paths,task-file-ops,inbox-outbox,types}.ts，src/hooks/team-worker-hook.ts，scripts/session-start.mjs，skills/team/SKILL.md（节选），skills/remember/SKILL.md，agents/executor.md。

---

## 16. OthmanAdi/planning-with-files（2026 年出现，26834 stars）

链接前缀 `P=https://github.com/OthmanAdi/planning-with-files/blob/1ec8f4eb5c683e31644856d98f9abde0d5a53448/`

- **1 布局**：
  - 旧模式：项目根目录放 `task_plan.md / findings.md / progress.md`；
  - 并行模式：`.planning/YYYY-MM-DD-<slug>/` 下放同样三份文件，加 `.mode`、`.attestation`、`.nonce`、`.stop_blocks`、`ledger-<agent>.jsonl`；
  - 活动计划指针 `.planning/.active_plan`（P/skills/planning-with-files/SKILL.md#L225-L253）。
- **2 格式**：
  - task_plan 模板分 `## Goal / ## Next Step / ## Current Phase / ## Phases`，每个阶段写 `- **Status:** pending|in_progress|complete`（P/templates/task_plan.md）；
  - ledger 每行一个 JSON（P/scripts/ledger-append.sh 头注释）：
```
{"tick":N,"ts":"ISO8601Z","agent":"...","phase":"...",
 "event":"progress|phase_complete|error|gate_block|attest|note","summary":"...","files":["..."]}
```
  - 原文 "tick = 1 + max tick across ALL ledger-*.jsonl in the plan dir, so concurrent agents share a monotonic counter"。
- **3 读写**：
  - 原文 "The orchestrator owns `task_plan.md` and shared summaries. Workers report through their own ledgers or assigned files"（SKILL.md#L85）；
  - 原文 "A worker joining an existing task uses its assigned plan; it must not create or overwrite a competing root plan"（#L46）；
  - 研究结果只写 findings.md，不进 task_plan.md，因为 task_plan.md 每轮都会被注入（#L482）。
- **4 强制**：
  - 插件 hook 覆盖 6 个事件：SessionStart（startup/resume/clear/compact）、UserPromptSubmit、PreToolUse、PostToolUse、PreCompact、Stop（P/hooks/hooks.json）；
  - `inject-plan.sh` 在轮次开始注入计划开头加进度摘要，每次工具调用前注入计划前 30 行（P/scripts/inject-plan.sh 头注释）；
  - 计划选择：`PLAN_ID` 一旦设了就必须解析到那份计划，否则停止，不回退到别的计划；有多份计划又没设 `PLAN_ID` 时拒绝选择（P/scripts/resolve-plan-dir.sh）。
- **5 生命周期**：
  - 阶段状态单向推进；
  - gated 模式下 Stop hook 可以阻止 agent 结束，但同时满足以下条件才阻止：有 in_progress 阶段、阻止次数低于上限 20、ledger 自上次阻止后有进展（SKILL.md#L395-L426）；
  - 原文 "it judges the plan artifact on disk, not the conversation transcript"。
- **6 并发**：
  - 按任务目录隔离；
  - "Parallel-write guard" 每轮比较已勾选项和已完成阶段的数量，数量下降就提示可能丢了工作。原文承认 "This is an advisory check after a write, not a lock or merge mechanism… Keep a single writer for shared summaries and separate files for workers"（#L385-L393）；
  - 防注入：SHA-256 attestation 发现计划被改就拒绝注入；v3 用随机 nonce 包裹注入内容；v3 注入结构化的 ledger 摘要，不注入 progress.md 的自由文本（#L461-L478）。
- **7 流转**：多个 agent 共用同一个 `PLAN_ID`，一个 orchestrator 持有计划，worker 各写各的 ledger；没有消息通道。

**读过的文件**：skills/planning-with-files/SKILL.md（全文），hooks/hooks.json，scripts/inject-plan.sh（L1-80），scripts/resolve-plan-dir.sh（L1-60），scripts/ledger-append.sh（L1-50），templates/task_plan.md（L1-40）。

---

## 17. monomind-ai-lab/project-context（2026-08-25 创建，3 stars）

链接前缀 `M=https://github.com/monomind-ai-lab/project-context/blob/72a0a22640f4577eddd615c6bd3a4dad2a6473b9/`

- **1 布局**（M/README.md "Where Context Lives"）：
  - `project-context/` 下有 `.project-context.json`（标记文件）、`SKILL.md`、`NOW.md`、`DECISIONS.md`、`LEARNINGS.md`、`decisions/ questions/ tasks/ designs/ incidents/`、`inbox/`（暂存 capsule，等待提升）；
  - `global/ blueprint/` 由 Hub 推送进来，本仓库只读；
  - AGENTS.md 和 CLAUDE.md 里各有一个受管区块。
- **2 格式**：
  - detail record 必须有 6 个 frontmatter 键：`id, kind, status, title, created, asserted_by`；
  - 每种 kind 有自己的状态流：decision/learning/capsule 为 `proposed → accepted → superseded | rejected`，question 为 `open → answered → superseded`，task 为 `proposed → active → done | dropped`；
  - 引用格式固定，如 `commit:<binding>:<sha>`、`pr:<binding>#<n>`、`doc:<binding>:<path>@<commit>`（M/README.md "One record model"）；
  - NOW.md 模板是 `Last reviewed:` 加 `Snapshot / Active work / Blockers / Known follow-up / Superseded state` 几张表（M/skills/project-context-init/assets/project-context/NOW.md）。
- **3–4 读写与强制**：
  - 开工前运行 `context_packet.py context --task ... --files ...`，按顺序汇总所有者约束、当前状态、与这些路径相关的记录（M/skills/project-context/SKILL.md "Start"）；
  - 更新靠触发条件，原文 "Update a document when its trigger fires — not when someone asks for an update"（"Triggers"）；
  - 写新决策前运行 `context_review.py --new-decision` 找出可能冲突的已接受决策，只有两种处理：旧决策被取代，或写明两者为什么都成立；
  - 没有触发就用 `context_triggers.py ack` 记录"已评估"，这条确认与当前 commit 绑定，下一次 commit 自动失效。
- **5 生命周期**：
  - 采集和提升分两步。`context_capture.py` 只往 `inbox/` 写一份 capsule，原文 "Capture has to be cheap enough to happen *during* the work"；判断它是决策、learning 还是无用，放到提升时再做；capsule 放久了由 review 报告出来（M/skills/project-context/scripts/context_capture.py 头注释）；
  - 证据写成 `path@commit`，路径变动后 doctor 报 `evidence-drift`。
- **6 并发**：
  - Hub 推送不直接改默认分支，而是开 `hub-sync` PR；
  - 推送文件的 sha256 记在标记文件里，本地改动过推送文件时，下一次推送整体拒绝；
  - 未找到锁。
- **7 流转**：没有消息机制；跨仓库只有 Hub 的 push 和 pull 两个方向。

**读过的文件**：README.md（L1-260），skills/project-context/SKILL.md（L1-135），skills/project-context/scripts/context_capture.py（头部），skills/project-context-init/assets/project-context/NOW.md。未读：planning/project-context-design.md 等设计文档、src/project_context_cli。

---

## 18. Claude Code agent teams：官方布局与三个开源复刻

官方文档 https://code.claude.com/docs/en/agent-teams（子代理用 WebFetch 读取，页面自述 "as of v2.1.178"）：
- 邮箱："Each agent's mailbox is a JSON file at `~/.claude/teams/{team-name}/inboxes/{agent-name}.json`"。
- 配置 `~/.claude/teams/{team-name}/config.json`，任务目录 `~/.claude/tasks/{team-name}/`；会话结束时删除 config，任务目录保留。
- 任务状态 pending / in progress / completed；依赖未完成的任务不能认领；"Task claiming uses file locking"。
- 上下文："a teammate loads the same project context as a regular session: CLAUDE.md, MCP servers, and skills… The lead's conversation history does not carry over."
- 投递："delivered automatically… The lead doesn't need to poll"。
- 质量门槛用 hook：`TeammateIdle / TaskCreated / TaskCompleted`，exit 2 表示阻止。

| 复刻 | 布局与格式 | 强制与流转 | 并发 |
|---|---|---|---|
| [niveshdandyan/teammate-tool](https://github.com/niveshdandyan/teammate-tool/blob/151b24e8a57946d2b6cffa51f49663d4cb0e8a7e/scripts/tasks.sh#L138-L159)（bash+jq） | `teams/<t>/config.json`、`inboxes/<a>.json`、`tasks/<t>/<id>.json`，任务字段 `{id,subject,status,assigned_to,depends_on,...}` | 靠 spawn prompt 要求 agent 自己去读邮箱，没有 hook；任务完成时解锁下游 blocked 任务；邮箱超过 200 条时截到 100 条 | claim 用 `flock -n`；fail/reset/join 三处先读后写且不加锁（推断：会丢更新） |
| [codexstar69/pi-agent-teams](https://github.com/codexstar69/pi-agent-teams/blob/58f0a39e3b8a829f2ec9fcf0234f0be9d992cdb7/extensions/teams/task-store.ts#L14-L27)（Pi 扩展） | 和官方路径一一对应（docs/claude-parity.md）；`TeamTask{id,owner,status,blocks,blockedBy,metadata}` | 代码里的 worker 循环轮询邮箱，空闲时自动 `claimNextAvailableTask`；消息类型 `task_assignment` / `idle_notification` | 锁用 `wx` 创建，记录 pid/hostname，持有进程已死或超过 60 秒则回收（[fs-lock.ts#L72-L120](https://github.com/codexstar69/pi-agent-teams/blob/58f0a39e3b8a829f2ec9fcf0234f0be9d992cdb7/extensions/teams/fs-lock.ts#L72-L120)）；认领时在锁内复核 |
| [OthmanAdi/planning-with-teams](https://github.com/OthmanAdi/planning-with-teams/blob/024def2fda6cdf465d2e6c10b5ae13256fabea35/skills/planning-with-teams/SKILL.md#L77-L90) | `team_plan.md`（lead 独占），`team_findings.md`、`team_progress.md`（所有人追加） | PreToolUse 匹配 `Task\|Teammate\|SendMessage\|TaskCreate` 时注入 `head -50 team_plan.md`；Stop hook 只报告不阻止 | 没有锁 |

---

## 19. ruvnet/ruflo（原 claude-flow）：hive-mind 与 swarm memory

链接前缀 `R=https://github.com/ruvnet/ruflo/blob/b02c0cacec225deea01f586b66a9694393369432/v3/@claude-flow/cli/src/`

- **1 存储**：
  - hive 状态存在单个 JSON `.claude-flow/hive-mind/state.json`，包含 queen、workers、consensus、`sharedMemory`（R/mcp-tools/hive-mind-tools.ts#L12-L41）；
  - 通用记忆存在 SQLite `.swarm/memory.db`（R/memory/memory-initializer.ts#L93-L161）。
- **2 格式**：`memory_entries(id, key, namespace DEFAULT 'default', content, type CHECK(semantic|episodic|procedural|working|pattern), embedding, owner_id, provenance_type, expires_at, status, UNIQUE(namespace,key))`，WAL 模式（R/memory/memory-initializer.ts#L232-L276）；namespace 由调用方随意填写，写入默认覆盖同键。
- **3–4 读写与强制**：
  - 所有读写都通过 `mcp__ruflo__*` 工具；
  - `hive-mind_broadcast` 只是把消息追加进 `sharedMemory.broadcasts`，保留最近 100 条，不推送给任何人（R/mcp-tools/hive-mind-tools.ts#L843-L889）；
  - `hive-mind spawn --claude` 生成 queen prompt，然后启动一个 claude 进程，prompt 原文 "You MUST use Ruflo MCP tools (mcp__ruflo__*) for ALL orchestration tasks"（R/commands/hive-mind.ts#L64-L325）；
  - `init` 生成的 hook：SessionStart 恢复会话，Stop 同步（R/init/settings-generator.ts#L294-L465）；
  - 推断：CLI 里没有找到 worker 进程轮询 hive 状态的代码，所以"worker"只是登记在 state.json 里的 ID。
- **6 并发**：
  - state.json 每次都是整份 `readFileSync → 改 → writeFileSync`，没有锁（R/mcp-tools/hive-mind-tools.ts#L177-L202）；推断：多进程同时写会丢更新；
  - "共识"只是投票记账，不是分布式协议：raft 模式不许改票，bft 模式把改票者标为拜占庭投票者并作废其票（#L609-L760）；
  - SQLite 检测到 `-wal/-shm` 旁路文件时拒绝以镜像方式写入。
- **7 流转**：queen 会话依次调用 MCP 工具 init → spawn → task_assign → memory set → consensus → broadcast；其他会话通过同一组工具读取结果。

**读过的文件**：mcp-tools/hive-mind-tools.ts（L1-60、95-202、600-1030），commands/hive-mind.ts（L64-325），memory/memory-initializer.ts（L60-276），mcp-tools/memory-tools.ts（L331-371），init/settings-generator.ts（hooks 段），mcp-tools/claims-tools.ts（grep），v3/@claude-flow/swarm/src/queen-coordinator.ts（头部）。

---

## 20. OpenHands：skills（原 microagents）

实现已迁到 `OpenHands/software-agent-sdk`，链接前缀 `OH=https://github.com/OpenHands/software-agent-sdk/blob/76e9e25078ed0ff7970f2c75e451274d3ed32bf2/openhands-sdk/openhands/sdk/`

- **1 布局**：
  - 按优先级加载 `.agents/skills/`、`.openhands/skills/`（legacy）、`.openhands/microagents/`（deprecated）；
  - 同时读取 `.cursorrules`、`AGENTS.md`、`CLAUDE.md`、`GEMINI.md`；子目录里的 AGENTS.md 变成按路径触发的规则（OH/skills/skill.py#L1027-L1110,#L346-L352）。
- **2 格式**：Markdown + YAML frontmatter（`name, description, triggers: [...]`）。触发类型按字段推断（OH/skills/skill.py#L545-L620）：
  - 有 `paths:` → PathTrigger；
  - 有 `inputs:` → TaskTrigger；
  - 有 `triggers:` → KeywordTrigger；
  - 都没有 → 始终生效。
- **3 读写**：
  - 读：每个 conversation；子 agent 只读自己定义里点名的 skill；
  - 写：人，以及 agent 本身，系统提示原文 "Use `AGENTS.md` under the repository root as your persistent memory"（OH/context/prompts/sections/static.py#L102-L137）。
- **4 强制**：
  - 没有触发条件的 skill 放进系统提示的 `<REPO_CONTEXT>`；
  - SKILL.md 形式的 skill 列在 `<available_skills>` 里，由 agent 按需读取；
  - 关键词整词匹配后，内容接在用户消息后面注入（OH/context/agent_context.py#L509-L565）。
- **5 生命周期**：已激活的 skill 名记在 `state.activated_knowledge_skills`，一个 conversation 内只注入一次（OH/conversation/state.py#L129-L150）。
- **6 并发**：同名 skill 按优先级取第一个；文件写入没有锁。
- **7 流转**：
  - 委托时新建子 conversation，与父 conversation 共享 workspace，结果以子 agent 的最终回复带回（[delegate/impl.py#L170-L337](https://github.com/OpenHands/software-agent-sdk/blob/76e9e25078ed0ff7970f2c75e451274d3ed32bf2/openhands-tools/openhands/tools/delegate/impl.py#L170-L230)）；
  - 父子之间只共享工作目录里的文件。

**读过的文件**：skills/{skill.py,trigger.py}，context/agent_context.py，context/prompts/sections/static.py，conversation/state.py，conversation/impl/local_conversation.py（节选），subagent/registry.py，openhands-tools/.../delegate/impl.py，.agents/skills/run-eval.md；OpenHands/OpenHands 的 AGENTS.md。

---

## 21. Letta：shared memory blocks

`letta-ai/letta` 的 main 分支只剩 README，实现在 archive 分支。链接前缀 `L=https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/`

- **1 存储**：表 `block` 加多对多表 `blocks_agents`，同一个 block_id 可以挂到多个 agent（L/orm/blocks_agents.py#L7-L34）；历史版本存在 `block_history`。
- **2 格式**（L/orm/block.py#L38-L61）：
```python
label: Mapped[str]; value: Mapped[str]
limit: Mapped[BigInteger] = mapped_column(Integer, default=CORE_MEMORY_BLOCK_CHAR_LIMIT)
read_only: Mapped[bool] = mapped_column(default=False)
version: Mapped[int] = mapped_column(Integer, doc="Optimistic locking version counter…")
__mapper_args__ = {"version_id_col": version}
```
  渲染进提示词时的结构是 `<memory_blocks><label><description><metadata read_only chars_current chars_limit><value>`（L/schemas/memory.py#L143-L172）。
- **3–4 读写与强制**：
  - agent 通过 memory 工具写，`read_only` 的 block 写入直接报错（L/services/tool_executor/core_tool_executor.py#L319-L326）；
  - 服务端每一步开始时按 block_id 从数据库重读所有 block，编译结果和当前系统消息不一致就重建系统提示（L/services/agent_manager.py#L1527-L1581,#L1805-L1823）；
  - 效果：A 写入的内容，B 在下一步就能看到，模型无法绕过。
- **5–6 更新与并发**：
  - 工具执行完逐个 label 比较，值变了才写库（L/services/agent_manager.py#L1747-L1797，注释写 "LRW"）；
  - 名义上有 SQLAlchemy 乐观锁（L/orm/sqlalchemy_base.py#L768-L790），但更新时先在同一个 session 里读出最新行再赋值，而新值是 agent 在本步开始时的快照算出的整段文本（L/services/block_manager.py#L211-L246）；
  - 推断：实际行为是后写覆盖先写。
- **7 流转**：
  - 共享的方式就是把同一个 block 挂给多个 agent；sleeptime 组自动把 block 挂到后台 agent 上；
  - 新的 letta-code 仍支持传 `block_ids`，但注释写着 "We no longer reuse shared blocks - each agent gets fresh blocks"（[letta-code src/agent/create.ts#L321-L356](https://github.com/letta-ai/letta-code/blob/bb281fcec287c67be00412cee00c9683eb96fc97/src/agent/create.ts#L321-L356)）。

**读过的文件**：orm/{block,blocks_agents,group,sqlalchemy_base}.py，schemas/{block,memory,group}.py，services/{block_manager,agent_manager,group_manager}.py、services/tool_executor/core_tool_executor.py（节选），agents/letta_agent.py（节选）；letta-code src/agent/create.ts、src/memory-frontmatter.ts（头部）。

---

## 22. 并行 agent 管理器：vibe-kanban、crystal、sculptor

- **BloopAI/vibe-kanban**：共享的是 issue 数据，不是文档。
  - 每个 agent 进程启动 `vibe-kanban-mcp`，按当前目录问本地服务器 `/api/containers/attempt-context`，拿到 `McpContext{project_id, issue_id, orchestrator_session_id, workspace_id, workspace_branch, workspace_repos}`（[task_server/mod.rs](https://github.com/BloopAI/vibe-kanban/blob/4deb7eca8f381f7cbc1f9d15515a9ab8f8009053/crates/mcp/src/task_server/mod.rs)）。
  - 首条 prompt 是 issue 的 "title\n\ndescription"（[task_attempts.rs#L68-L85](https://github.com/BloopAI/vibe-kanban/blob/4deb7eca8f381f7cbc1f9d15515a9ab8f8009053/crates/mcp/src/task_server/tools/task_attempts.rs#L68-L85)）。
  - 文本里的 `@tag` 会被替换成预存内容。
  - follow-up 会续接原会话；排队的消息存在内存 DashMap 里，推断：服务重启就丢。
  - orchestrator 只能操作本 workspace（[tools/mod.rs#L189-L204](https://github.com/BloopAI/vibe-kanban/blob/4deb7eca8f381f7cbc1f9d15515a9ab8f8009053/crates/mcp/src/task_server/tools/mod.rs#L189-L204)）。
  - worktree 之间共享上下文文件：未找到。
- **stravu/crystal**（README："Crystal Is Now Nimbalyst … Deprecated: February 2026"）：
  - 会话之间的共享上下文：未找到。
  - 单个会话在首条 prompt 里拼接全局和项目的 system prompt（[claudeCodeManager.ts#L651-L668](https://github.com/stravu/crystal/blob/1e18e0bc981225f75b5226f82a300fa741970c6f/main/src/services/panels/claude/claudeCodeManager.ts#L651-L668)）。
  - 压缩时由 `ProgrammaticCompactor` 生成 `<session_context>` 摘要，下一轮不续接旧会话，改开新会话带上摘要（[contextCompactor.ts#L305-L340](https://github.com/stravu/crystal/blob/1e18e0bc981225f75b5226f82a300fa741970c6f/main/src/utils/contextCompactor.ts#L305-L340)）。
- **imbue-ai/sculptor**：
  - 同一 workspace 内原文 "**Shared**: every tracked and untracked file in the checkout, and git state … There is **no file locking** between sibling agents. **Private to each agent**: conversation history; TODOs, status…"（[sculpt-cli/SKILL.md#L178-L186](https://github.com/imbue-ai/sculptor/blob/f74741c425b780456b086cd9a1cedd746d88dd18/sculptor/sculptor-plugin/skills/sculpt-cli/SKILL.md#L178-L186)）。
  - agent 之间用 `sculpt agent send <id> "..." -f` 同步发消息，等对方这一轮结束；`sculpt agent messages <id>` 可以直接读其他 agent 的对话记录（[agent.py#L716-L760](https://github.com/imbue-ai/sculptor/blob/f74741c425b780456b086cd9a1cedd746d88dd18/tools/sculpt/sculpt/commands/agent.py#L716-L760)）。
  - 共享记忆文档：未找到。

---

## 23. 横向对比表

| 项目 | 文档类型 | 写者 | 读写机制 | 生命周期 | 并发 | 流转 |
|---|---|---|---|---|---|---|
| Cursor Projects + arslan（闭源） | notes.md、docs/、internal/；inbox/<name>.md、handoff-*.md；plans/ 五个目录 | notes 只由 coordinator 写；inbox 按 hub 辐射式写入（hub→项目文件，项目→hub.md） | 产品内置；每轮读 inbox；skill 驱动 | 目录迁移 drafts→next→open→done/discarded；retro | git 提交；按文件划分写者 | PR 订阅唤醒；inbox 留言 |
| Evalir/dotfiles plan-* | 私有 plans 仓库，每个代码仓库一棵子树；frontmatter + 6 节正文 | 各 skill 分工；只有 plan-sync 移动文件；plan-status 重新生成索引 | 纯 prompt，写明拒绝条件 | 目录即状态；sync 核对 diff 与计划（多做/少做/关闭） | git push；不强推别人的分支 | 云端 agent 只拿计划正文；PR 作为回报 |
| mcp_agent_mail | 消息、线程摘要、文件预约（SQLite + Git 存档） | 服务进程唯一写者；agent 通过 MCP | MCP、宏工具、Claude hook、git pre-commit | 180 天清理；LLM 线程摘要；预约 TTL、续期、失活回收 | 预约只提示不拦截；BEGIN IMMEDIATE；pre-commit 硬拦截 | 线程 + ack；issue id 作为 thread_id |
| beads | issues/deps/comments/events/memory（Dolt） | 所有 agent 通过 bd CLI | SessionStart 钩 `bd prime`（压缩后会再触发） | 关闭 30/90 天后分层 LLM 压缩，保留原文快照可恢复 | 哈希 ID；row_lock CAS；5 分钟租约 + 心跳；按字段三方合并；merge-slot | ready 队列；comment + assign 交接 |
| gastown | beads 当作邮件、hook、交接、convoy、MR；nudge 文件队列 | 按角色分工（polecat/witness/refinery/mayor） | SessionStart/PreCompact 调 `gt prime`；UserPromptSubmit 注入邮件 | 交接邮件挂在 hook 上；协议消息存为 wisp 并清理；molecule 压缩成摘要 | 每个 worker 一个 worktree；merge slot；身份锁；两阶段投递 ack | 空闲时直接敲进窗格，忙时进队列等下一轮；无 hook 的运行时 10 秒轮询 |
| overstory | SQLite 邮件/会话/合并队列；overlay CLAUDE.md；mulch jsonl | coordinator 写 overlay；lead 不写文件；builder 只写自己的文件范围 | 5 类 hook 注入；PreToolUse 在代码层面强制 | 会话状态 CAS；mulch 条数上限与过期；checkpoint 未接通 | WAL；按目标分支的合并锁（检查 PID）；turn lock | 类型化邮件；headless 模式 2 秒轮询后续接会话 |
| Backlog.md | 任务/草稿/决策/文档 Markdown | 通过 CLI/MCP，禁止直接编辑文件 | 在 AGENTS.md 等文件写受管区块；onStatusChange | completed/archive 目录；定期清理 | git common dir 里的创建锁；单任务锁拿不到立即失败；跨分支按"状态更靠后"取值 | 任务文件本身就是交接文档 |
| spec-kit | constitution、specs/NNN/{spec,plan,tasks...} | 每条命令写固定文件；analyze 只读 | slash command + 前置检查脚本 + handoffs | 宪法按版本递增；特性目录无归档 | 编号顺延；无锁；feature.json 全仓库一个指针 | 命令链；tasks 复选框 |
| BMAD | sprint-status.yaml、故事 spec、epic-context、memlog | 状态只由脚本写；子 agent 只读 spec | step 文件、HALT、Python 脚本 | 故事状态机，状态不回退；缓存按时间戳失效 | 原子替换 + 写后校验；无锁 | spec 是唯一依据；评审结论分流 |
| agent-os | standards、product、specs | 人确认后由单个 agent 写 | slash command，要求 plan mode | spec 写完不再改动 | 无锁；回推 profile 时检测冲突 | 未找到 |
| conductor | index/product/tech-stack/workflow、tracks.md、track 目录 | 各 skill 分工 | 先读 index 做"握手"，缺文件就停 | 复选框 + SHA + git notes；track 归档 | git 提交；无锁 | 同一会话内切换角色 |
| ccpm | prds、epics/<N>.md、updates/stream-X.md、(v1) context/ | 主会话 + 每个 stream 只写自己的文件 | prompt；v1 靠手动 prime/update | 同步成 issue 后改名；SYNCED 标记；epic 归档 | analysis 规定文件归属；遇冲突交给人 | GitHub issue 是权威状态 |
| claude-task-master | tasks.json（按 tag 分区）、复杂度报告 | 通过 CLI/MCP；orchestrator/executor/checker | MCP 工具分档 + 规则文件 | update-subtask 只追加 | 锁文件 + 原子写（旧路径会整块覆盖） | 固定派发模板；review 状态 |
| humanlayer | ~/thoughts 仓库：个人区 + shared；research/plan/handoff | 按用户分区；命令写 shared | 命令结尾 sync；git hooks | 追问追加到原文档；handoff 作为压缩手段 | 分区单写者 + git rebase | Linear 状态机 + ralph 自动推进 |
| oh-my-claudecode | notepad、project-memory、shared-memory、team 任务/收发件箱、handoffs | MCP 工具 + hook 学习 | SessionStart/PreCompact 注入 | 7 天清理；24 小时重扫；TTL；阶段机 | O_EXCL 锁（部分路径不加锁） | 阶段交接文档 5 项；lead 预先分配 |
| planning-with-files | task_plan/findings/progress、ledger-<agent>.jsonl | orchestrator 独占计划；worker 写各自 ledger | 6 个 hook 事件注入；PLAN_ID 固定选中计划 | 阶段单向推进；gated 模式阻止提前结束 | 按目录隔离；只做写后检查；attestation/nonce | 共用计划 + 各自 ledger |
| monomind project-context | NOW/DECISIONS/LEARNINGS、inbox capsule、pushed 集合 | builder 写；Hub 推送的文件只读 | 汇总脚本 + 触发条件 + ack 绑定 commit | 先采集后提升；决策被取代时两边都标注；证据漂移检测 | 按 hash 拒绝推送；hub-sync PR | 未找到 |
| CC agent teams（官方与复刻） | inboxes/<a>.json、tasks/<id>.json、config | lead 建任务，队友认领 | 官方自动投递；复刻靠轮询或 prompt | config 会话结束删除；任务目录保留 | 文件锁认领；复刻用 flock/wx | 邮件 + idle 通知 |
| ruflo | state.json、memory.db 各 namespace | 任意会话通过 MCP | MCP + init hook | TTL/过期；broadcast 截断 | state.json 无锁；投票记账 | queen 调工具，其他会话读 |
| OpenHands | skills/AGENTS.md（带触发条件） | 人和 agent | 系统提示 / 关键词触发 / 路径触发 | 一个 conversation 内只激活一次 | 无 | 子 conversation 共享 workspace |
| Letta | 共享 memory block（数据库行） | 挂着该 block 的 agent 通过工具写 | 服务端每步重读，模型无法绕过 | 保留历史版本 | 名义乐观锁，实际后写覆盖 | 同一个 block 挂给多个 agent |
| vibe-kanban / crystal / sculptor | issue 数据 / 会话摘要 / 无共享文档 | 服务端 / 单会话 / — | MCP 上下文 / 首条 prompt / CLI | follow-up 续接会话 / 压缩后开新会话 | orchestrator 只能操作本 workspace / — / 明确不加锁 | 子 session / — / 直接读对方对话记录 |

---

## 24. 最值得借鉴的 5 个设计模式

每条写清：解决什么问题、依赖什么前提、在什么情况下失效，以及对"spec → issue 票 → 夜间 worker → reviewer/verifier → 合并关票；票状态是评论里事件块的 fold；靠事件唤醒"这条流水线的对应点。

### 模式 1：共享摘要只有一个写者，其他人写各自的追加日志

- **见于**：
  - Cursor notes.md 只由 coordinator 写，inbox 按 hub 辐射式划定写入方向；
  - planning-with-files："The orchestrator owns `task_plan.md`… Workers report through their own ledgers"，每个 worker 一份 `ledger-<agent>.jsonl`，共享一个单调递增的 tick；
  - humanlayer 按用户分区；
  - planning-with-teams 的 lead 独占 team_plan.md；
  - Evalir 的 plan-status 重新生成索引表，"Do not hand-edit them"。
- **解决的问题**：多个 agent 读到同一份旧内容再各自覆盖，造成丢失更新。planning-with-files 自己的写后检查也承认检测不到这类覆盖（"not a lock or merge mechanism"），最后给出的办法仍是单写者。
- **前提**：
  - 写者身份能被识别；
  - 汇总表可以从追加日志完整重新生成。
- **失效场景**：
  - 唯一写者宕机或上下文被压缩，汇总表停在旧状态。缓解办法是像 arslan 那样可以 "rebuild its notes from the repo"；
  - 写者按 prompt 约定而非代码强制，oh-my-claudecode 就有好几条不加锁的旁路写入。
- **对应到本流水线**：
  - 事件块 fold 已经是"只追加日志 + 派生状态"；
  - 值得补的是给人和 coordinator 看的"夜间汇总"，由单个脚本从 fold 重新生成，明确禁止 agent 手改。

### 模式 2：交接文档自包含，接手方不带发起方的对话上下文

- **见于**：
  - BMAD 实现子 agent "no prior conversation context"，spec 是 "sole source of truth"，意图部分放在 `<frozen-after-approval>` 冻结区块里，只追加的 Change Log 和 Triage Log；
  - Evalir 云端 dispatch 时 "the body *is* the task"；
  - oh-my-claudecode 阶段交接文档固定 `Decided / Rejected / Risks / Files / Remaining` 五项、10–20 行；
  - humanlayer 的 handoff 固定 7 节；
  - gastown 交接邮件挂在 hook 上，不是临时消息；
  - Backlog.md："You may be interrupted or replaced at any point, so the task record must contain everything needed for a clean handoff."
- **解决的问题**：worker、reviewer、verifier 都是新会话，发起方对话里的隐含假设传不过去。
- **前提**：
  - 有固定分节；
  - 人确认过的"意图"部分冻结不改，执行中的发现只追加；
  - 文档有长度预算（BMAD spec 900–1600 token）。
- **失效场景**：
  - 文档写完后被执行方改写，意图随之漂移，这正是冻结区块要防的；
  - 超出预算后被截断或跳读；
  - 链接到的外部文件后来变了。monomind 用 `path@commit` 加 evidence-drift 检测来发现这种情况。
- **对应到本流水线**：
  - 票正文相当于冻结的意图；
  - 评论里的事件块相当于只追加的日志；
  - 可以借鉴的是给 reviewer/verifier 的固定"交接块"格式（Decided/Rejected/Risks/Files/Remaining），以及对票正文的冻结标记。

### 模式 3：状态迁移同时写明"怎么跟现实对账"

- **见于**：
  - arslan/Evalir 的 plans 目录流转，plan-sync 不只移动文件，还用 `gh pr diff` 比对计划（相符 / 做多了记日志 / 做少了拆成新 draft / 关闭必须写原因 / 两周无动静退回 next）；
  - BMAD 状态 "never downgrade"；
  - Backlog.md 跨分支按"状态更靠后"取值；
  - conductor 在 plan 里记提交 SHA，review 按 SHA 圈定 diff 范围。
- **解决的问题**：状态记录与 GitHub 实际情况分叉，例如 PR 合并了但计划没动，或者合并的内容与计划不符。
- **前提**：
  - 有权威的外部事实源（PR diff、合并 SHA）；
  - 迁移由唯一的角色或脚本执行（Evalir 规定只有 plan-sync 能移动文件）。
- **失效场景**：
  - 状态存了两份，BMAD 的 spec frontmatter 与 sprint-status 并存，只靠约定保持一致；
  - 目录迁移在多个分支上并发发生；
  - 对账全靠 LLM 判断 diff 是否"相符"，结论不可复现。
- **对应到本流水线**：
  - 关票前的 reverify 已经对应"对账"；
  - 值得补的是 Evalir 那三种判定的明确事件（多做 / 少做后拆出新票 / 放弃并写原因），把"少做的部分变成新票"做成固定动作，而不是只在报告里提一句。

### 模式 4：在轮次边界由 hook 注入，并做两阶段投递确认；没有 hook 的宿主才用轮询兜底

- **见于**：
  - gastown：`UserPromptSubmit` 跑 `gt mail check --inject`；空闲时直接敲进 tmux，忙时进 nudge 队列；`delivery:pending → acked` 两阶段；交接标记文件防止新会话重复执行 `/handoff`；
  - overstory：同样的 hook 组合；headless 模式 2 秒轮询，只有这一轮退出码为 0 才标已读；lead 的 prompt 禁止 bash 等待循环，原文 "Worker mail arriving later will respawn you"；
  - beads：注册 SessionStart 而不注册 PreCompact，因为压缩后 SessionStart 会以 `source=compact` 再触发；
  - Claude Code 官方 agent teams："The lead doesn't need to poll"。
- **解决的问题**：
  - agent 在上下文压缩后忘了工作流；
  - 消息到了却没进模型上下文；
  - 用轮询代替唤醒浪费轮次。
- **前提**：
  - 宿主有轮次级 hook；
  - 注入内容有明确边界（gastown 用 system-reminder 包裹，planning-with-files 用 nonce 分隔并做 attestation）；
  - 有"已进入上下文"的确认信号。
- **失效场景**：
  - 宿主没有轮次 hook（gastown 对 Gemini/Codex 退回 10 秒 poller）；
  - hook 输出格式不对，只显示给人、没进模型上下文（mcp_agent_mail 需要设 `AGENT_MAIL_HOOK_FORMAT=json`）；
  - 注入的自由文本带来提示注入，planning-with-files 在 v3 改为只注入结构化 ledger 摘要；
  - 标已读的时机早于这一轮真正成功。
- **对应到本流水线**：
  - 本流水线已经靠事件唤醒；
  - 可以借鉴的是 overstory 的"这一轮成功结束才确认"和 gastown 的 pending/acked 两阶段，让"唤醒已送达"与"唤醒已被处理"成为两个可区分的事件；
  - 另外，交接标记文件的做法可以防止恢复的会话重复执行上一轮的指令。

### 模式 5：认领用 CAS 加有限期租约；文件预约只做提示，在提交时硬拦截

- **见于**：
  - beads：`UPDATE … WHERE row_lock=?` 做 CAS，失败返回当前持有者；租约 5 分钟靠心跳续期，放在不进版本历史的表里；`bd reclaim` 回收过期租约；为了绕开 Dolt 按单元格合并，强制每次改状态都换一个新的 `row_lock`；
  - mcp_agent_mail：预约有冲突也批准，只返回冲突列表；失活判定综合邮件、文件修改、git 提交三种活动；真正的拦截放在 git pre-commit；
  - overstory / pi-agent-teams / oh-my-claudecode：锁文件记录 PID，持有进程已死才接管；
  - Backlog.md 把锁放在 git common dir，所有 worktree 共用。
- **解决的问题**：
  - 两个 worker 抢同一张票；
  - 持有者崩溃后票永远卡住；
  - 并行 worker 改同一文件，到合并时才发现冲突。
- **前提**：
  - 有一个所有参与者都能原子写入的存储（SQL 事务、`O_EXCL`、git common dir）；
  - 有可观测的"仍在活动"信号；
  - 各机器时钟大致一致。
- **失效场景**：
  - 租约只在授予它的节点有效（beads 在注释里写明），跨机器时失效；
  - 活动信号误判，长时间思考被当成失活而遭抢占；
  - 预约只做提示时，没装 pre-commit hook 或 `AGENT_MAIL_BYPASS=1` 就等于没有保护；
  - 按 PID 判断在容器或跨主机时不可靠。
- **对应到本流水线**：
  - 票状态由评论事件 fold 得出，天然只追加，但"两个事件同时声称认领"要靠 fold 规则裁决，例如按评论 id 先到先得；
  - 可以借鉴的是：给认领事件带有效期，由 watchdog 发出显式的回收事件；
  - 文件范围冲突不在认领时拒绝，而是在 advance 合并前拦截，并点名冲突的票。

### 附带值得注意的做法（不在前 5）

- **beads 分层语义压缩**：关闭满 30 天或 90 天后由 LLM 摘要，原文快照保留、可恢复；摘要不比原文短就放弃压缩。
- **monomind 的"触发条件 + ack 绑定 commit"**：没有触发也要显式记录"已评估"，这条确认在下一次 commit 自动失效，所以不会变成长期跳过的借口。
- **monomind 的"先采集到 inbox，再提升"**：采集要足够便宜，才能在工作进行中顺手做；判断它是决策、learning 还是无用，放到提升时再做。
- **Evalir plan-retro 的"重复三次才立规则"**：只提建议，由人挑选后才应用。
