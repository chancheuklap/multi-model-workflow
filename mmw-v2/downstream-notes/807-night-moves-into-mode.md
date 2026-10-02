# 807-night-moves-into-mode

## 改了什么

夜间流水线的说明文字改到已经落地的名字和路径。消费仓库里由 **Onboard a repository** 写进去的说明，还停在旧名字上。

- 开工提示词是一行。worker、reviewer、researcher：`Use the mmw skill. Role <role>, ticket #<n>, unattended: mmw <playbook>#<step>. Data: <file>.`，reviewer 另带 `base <commit>`。advisor：`Use the advisor skill. Role advisor, unattended: the mmw skill's ## Autonomy. Brief: <file>.`。Memory 索引、Rules 指针和简报路径在 `state/<owner>__<name>/prompts/<n>-<role>.md`。
- `dispatch` 技能不再安装。`implement` 不再安装；一张票的做法是 **Work a ticket**。`code-review` 回到上游，`mmw-v2/skills.txt` 的一行是 `engineering/code-review`。新的能力技能是 `setup-mmw` 和 `memory-records`。
- 流水线脚本在 `mmw-v2/skills/mmw/scripts/`。
- 七个 `dispatch.sh` 子命令改名：`open`→`open-night`，`open-ticket`→`open-ticket-watch`，`summary`→`close-night`，`wait`→`result`，`integrated`→`landed-since`，`memory-list`→`prepare-memory-decisions`，`route`→`resolve-child`。旧名在这一版里拒绝，一行里点名新命令。三个开关改名：`--preflight`→`--claim`，`--draft`→`--closing-draft`，`--sub-issue`→`--open-child`。在 `verify-ticket.py` 上调用旧开关时，它退出 2，一行里点名 `ticket_state.py` 和对应的新开关，不跑判据，也不写票。
- `verify-ticket.py` 跑一张票的判据并打印、lint、发布，不写事件。写票状态的命令在 `ticket_state.py`：认领、记录判据运行、决定、评审、`touched`、收尾草稿、closeout、开子票。

## 哪些产物失效

`mmw-v2/downstream-notes/README.md` 的四类里，前三类都不失效：screen contract、票的 `CHECK:`、`.mmw/target.json`。程序和消费仓库读的那些名字都还在。

第四类失效：技能写进消费仓库的说明。**Onboard a repository** 按 `mmw-v2/skills/mmw/references/issue-tracker-pipeline-sections.md` 写 `docs/agents/issue-tracker.md` 的标签节。已经写出去的副本仍用旧命令名。

2026-10-02 对两个仓库的默认分支只读重查。命令是 `git -C <repo> symbolic-ref --short refs/remotes/origin/HEAD`，再对那个 ref 在 `docs`、`AGENTS.md`、`CLAUDE.md`、`.mmw`、`.claude` 里用本票 AC1 的几组模式，加上 `dispatch, verify-ticket`、`skills/dispatch`、`verify-ticket.py --`。

- `agentflow-hq/agentflow`，`origin/dev`，`539b08f13e33e00e6938d275da32dd61ab8f978b`：
  - `docs/agents/issue-tracker.md`：`mmw:ticket` 一行仍写 the dispatch skill's `` `route … became-ticket` ``；`mmw:child` 一行仍写 the verify-ticket skill's `` `--sub-issue` ``；子票变成票的那句仍写 the dispatch skill's `` `route <ticket> <child> became-ticket` ``；grade 那句仍写 the dispatch skill starts a worker；frontier 那句仍写 computed by the dispatch skill。
  - `docs/agents/triage-labels.md`：仍写 the dispatch, verify-ticket and drive-target skills。这是说明文字，程序不读它。
  - `docs/adr/README.md`：技能用法索引里仍有一条 `` `implement` ``。这是说明文字，程序不读它。
  - 同一搜索还命中 `.claude/setup.sh` 里的 shell `wait`，和 `docs/teach/cloud-basics/NOTES.md` 里的 macOS `open`。两处都不是这条流水线的命令，不失效。
- `agentflow-hq/xiaohuangya`，`origin/main`，`1f93e1d3c069ddef73df7b30270d8610bd42dbca`：没有命中。

## 怎么迁

下次对那个仓库跑 **Onboard a repository**，或手工改上面点名的句子。本批不改消费仓库的任何文件。

- `mmw:ticket` 的「谁贴上」：`dispatch.sh resolve-child … became-ticket`。
- `mmw:child` 的「谁贴上」，以及缺标签时谁创建：`ticket_state.py --open-child`。
- 子票变成票：`dispatch.sh resolve-child <ticket> <child> became-ticket <new ticket>`。
- grade 每次开工时重读：`dispatch.sh start`。
- 一夜的 frontier：`mmw` 技能的 `scripts/status.py`。
- triage-labels 里读写这两个队列标签的，是 `mmw` 技能的脚本和 `verify-ticket`。`drive-target` 不是已安装的技能。
- ADR 索引里那条 `` `implement` ``：工人按 **Work a ticket** 做。一个只有人能定的 ADR 缺口，仍是开一张 `decision` 子票，按默认继续，而不是自己发明边界。
