# R4 MMW 的架构形态（定稿）

本文定稿 MMW（`mmw-v2/` 的技能合集与夜间落地流水线）改造成 pstack 分层架构后的形态。它的来源是三份设计（`R1-mmw-design-evolution.md` 演进派、`R2-mmw-design-pstack-faithful.md` 忠实派、`R3-mmw-design-night-first.md` 夜间优先派）和两份评审。本文只定架构：每类组件是什么、放在哪里、谁到达它、可以连向谁，以及下一轮逐项归置时用的判定顺序。逐个部件的归置不在本文范围内，文中出现的部件只作为检验规则的例子。

准绳是 `docs/research/workflow-compare/reports/L7-pstack-component-contract.md`（下称 L7，引用写成「L7 C.1 第 7 问」这种形式）。技能文本的现行规则 `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（下称 SSR）是被审视的对象，不是约束。

标注约定：

- 「已核实」：本轮回到原文或跑命令看到的。
- 「推断」：由原文推出，原文没有直接写。
- 「未确定」：做不出判断的，集中在第 16 节，并写明需要什么实测。

---

## 0. 结论（先读这里）

1. **骨架取 R1，夜间加固取 R3，优先级句取 R2。** 三份设计里 R1 的形式拆分最少，每项收益都对得上；R3 把夜间重入从「依赖宿主行为」改成「由脚本和消息保证」；R2 补上一条 pstack 自己没写的层级优先级。R2 的全局提醒行、把 `night.md` 和 `## On waking` 搬进新技能，以及 R3 把上游调用开关恢复原样，都不采用，理由见第 2 节。
2. **一个 mode：新建技能 `mmw`（`mmw-v2/skills/mmw/`），只服务人启动的会话。** 它不超过 100 行，内容是 `## Where you are`、`## Head judgement`、`## Routes`、`## Principles` 索引和一句层级优先级。
3. **`dispatch` 技能的 `SKILL.md` 仍是流水线的角色入口**，内容是角色表加 `## On waking`。它不改名，不算第二个 mode，夜里每次重入只读这份薄文件（这是 R3「两个入口」的实际形态）。
4. **脚本启动的会话不经过 mode。** 启动提示词的字面不变：`Use the implement skill …`、`Use the code-review skill …`、`Use the advisor skill.`（`dispatch.sh` 第 1949、1967、2072 行，已核实）。
5. **脚本送进活会话的每条消息，末尾都加一行固定的角色指针。** 这些消息是 relay 的唤醒、`dispatch.sh resume`、watchdog 告警。指针只写技能、文件和锚点，由一张表生成。这样被压缩后的会话回到正确位置时，不依赖任何宿主行为（取自 R3）。ADR 0020 相应修订一句。
6. **人启动的会话靠消费仓库 `AGENTS.md` 的 `## External References` 里一行加载 `mmw`**，`mmw` 自己的 description 是备用，`/mmw` 是手动入口（取自 R1）。不往 `mmw-v2/prompt/shared.md` 加任何内容。
7. **playbook 分两种。**
   - 头部 playbook 放在 `mmw/playbooks/`，起步只有一份：`idea-to-tickets.md`。
   - 角色操作文件原位不动，它们本身就是各角色的 playbook：worker 是 `implement`，reviewer 是 `code-review` 的 `references/session.md`，advisor 是 `advisor` 的 `references/advising.md`，orchestrator 是 `dispatch` 的 `references/night.md` 与 `one-ticket.md`。
   - 这符合 L7 C.1 第 7 问：单一入口、单一任务类型的流程用一个操作文件，不拆成三层。
8. **重入改由脚本算出，并按步骤标题指向文本，由一个 lint 核对。**
   - worker 的 `RESUME:` 改印步骤名；orchestrator 由 `dispatch.sh status` 印出同类的 `RESUME:`。
   - 一个接线 lint 放在 `mmw-v2/tests/lib/`，核对五类接线：脚本印出的锚点、`WAKES` 与处理行、技能可达性、原则索引、同名技能。
   - 同一批还修四处已核实的夜间断点：`night.md` 事实表缺一行、`## 3` 缺 `MMW turn guard:` 的处理行、`### Exit codes of resume` 被掏空、`NO_QUESTION` 与 `implement` 第 23 行给的出路不一致。
9. **原则是 `mmw/principles/<slug>.md` 文件，不是技能**，起步三条：`silence-is-never-a-pass`、`the-tracker-is-the-state`、`rerun-dont-reroute`。具体规则留在调用方的步骤里，句末括注原则名（取自 R3）。
10. **上游回到原文分两步。**
    - 上游行已不到一半的四个技能（`implement`、`code-review`、`to-tickets`、`to-spec`）分叉进 `mmw-v2/skills/`，名字不变；`mmw-v2/upstream/` 里的四份恢复原文、不安装（取自 R1）。
    - 其余上游技能的每段改动按 R3 的 a–f 六类判定，其中 b 类改成：调用开关由「是否被 mode、playbook 或启动提示词点名」推导，lint 检查。推导结果与现状相同。
11. **SSR 事实 7 的「MMW ships no router skill」废止。** 它原本防两件事：第二份副本漂移；某一跳找不到下一步（#538）。新做法是：路由只有一个家（`mmw`）；任务顺序只有一个家（playbook）；两者与实际一致由 lint 保证。
12. **落地分四批，全部作为本仓库的票，只在没有 watch 打开时发布。**
    1. 只加固，不搬文本；
    2. 分叉；
    3. 新建 `mmw`；
    4. 删上游与分叉技能里的「下一步」句。第 4 批以加载实测 T1 通过为前提，它是唯一在 mode 没被加载时会让情况变差的一步。

---

## 1. 本轮回到原文核实的事实

评审的结论和下面的决定依赖这些事实，每条都回到了原文。

| # | 事实 | 出处 | 结果 |
|---|---|---|---|
| V1 | `triage`、`wayfinder`、`to-questionnaire` 当前 frontmatter 没有 `disable-model-invocation`，模型可触发；上游原文（squash `5b1a4c51`）三者都是 `disable-model-invocation: true` | `mmw-v2/upstream/skills/*/SKILL.md` 头 5 行；`git show 5b1a4c51:skills/…` | 已核实。本会话的可用技能列表里有这三个，没有 `grill-with-docs` 等 7 个用户触发的技能 |
| V2 | 脚本文字按名点名 `night.md` 和 `## On waking` | `watchdog.py` 第 735、780 行「night.md's Exit codes of resume」；`dispatch.sh` 第 79 行「`ack` is in SKILL.md under `## On waking`」；第 4115 行「the dispatch skill's references/night.md」 | 已核实 |
| V3 | relay 的唤醒行带收件角色和 watch：`"to"`（只有 `WORKER`、`MAIN` 两值）与 `"watch"`（`spec:<n>` 或 `tickets:<n>[,…]`）；`relay.recovered` 行的 `watch` 为 `None`，但 `watches.json` 记着每个 watch 的 orchestrator 的 `runner`、`session` | `relay.py` 第 291–299、385–389、1022、1060 行，头注释第 180–181 行 | 已核实。所以 relay 能区分夜与单票的 orchestrator，也能取到 spec 号 |
| V4 | `ack` 按收件人加 ticket 加事件名匹配队列行，不解析唤醒文字 | `relay.py` `ack_wake` 第 919–927 行 | 已核实。加指针不影响 `ack` |
| V5 | `tests/relay/test_relay.py` 有多处断言要求 `send.sent` 与唤醒文字完全相等（第 365、436、545、558、570、611、621、770、879 行）；第 591、596 行用 `wake_text()` 计数 | 同文件 | 已核实。加指针后，前一类断言要在同一次提交里改，后一类不受影响 |
| V6 | `night.md` 事实表没有「`spec.retroed` 已记录、用户尚未验收」这一行（第 21 行要求没有 retroed，第 22 行要求用户已验收） | `night.md` 第 13–22 行 | 已核实 |
| V7 | 两处把 `MMW turn guard:` 送到 `## 3`，而 `## 3` 的表里没有处理它的行 | `night.md` 第 19 行；`one-ticket.md` 第 3 步 | 已核实 |
| V8 | `### Exit codes of resume` 只剩两句，没有任何退出码；`## 3` 表与 watchdog 告警都指向它 | `night.md` 第 102–104 行 | 已核实 |
| V9 | 两处对同一件事给了不同出路。`NO_QUESTION` 写的是：写 `ABANDON: AC<n> decision …`，并开 needs-triage 子票。`implement` 第 23 行写的是：`--sub-issue decision`，然后继续做。`tool-guard.py` 按工作树目录名 `issue-<n>` 生效，同一工作树里的 reviewer 也会收到这句 | `tool-guard.py` 第 76–80 行；`implement/SKILL.md` 第 23 行；N11 missing_edges 第 2 条 | 已核实 |
| V10 | `RESUME:` 按编号指向 `implement` `## Closing steps`；`resume_at` 的 docstring 引用的段首句「A ticket that already carries a run of your own」已不存在（现在是「A ticket you are prompted back into」，第 74 行）；`test_preflight.py` 第 463–517 行只钉脚本输出，没有测试核对编号与 `implement` 步骤的对应 | `verify-ticket.py` 第 2148–2181 行 | 已核实 |
| V11 | `to-spec` 的 merge-note 自认「不到一半的行是上游的」 | `merge-notes/to-spec.md` 第 31 行 | 已核实 |
| V12 | `improve-codebase-architecture` 的 `### 4. Hand the decision on` 整节是本仓加的，上游原文到 `### 3. Grilling loop` 结束；`wayfinder` 第 6 步整步是本仓加的，上游原文只有 5 步 | `git show 5b1a4c51:skills/engineering/…` | 已核实 |
| V13 | 残留的 `ask-matt` 目录相对上游改过三处文件：`PHASE-BOUNDARIES.md` 只有宿主中立的改写，`SKILL.md` 改了 74 行，`agents/openai.yaml` 删了 2 行；没有 merge-note；上游仍有这个技能 | `git diff 5b1a4c51:skills/engineering/ask-matt/ HEAD:…` | 已核实 |
| V14 | `setup-matt-pocock-skills` 第 4 步往消费仓库 `AGENTS.md` 的 `## External References` 加行；`manage-agents-md` 第 150 行规定「Other skills add rows under … `## External References`」 | 两份 `SKILL.md` | 已核实 |
| V15 | 状态目录是 `$MMW_HOME/state/<owner>__<name>/`，每个仓库一个，`watches.json` 在里面 | `statedir.py` 头注释；`relay.py` 第 180 行 | 已核实 |
| V16 | ADR 0014 否决「caller 那侧写进用户级提示词」，理由有两条：到不了 Cursor；为偶发之事付每回合的常驻 context | `docs/adr/0014-advisor-has-one-door.md` 第 29 行 | 已核实 |
| V17 | Memory `fe94802d` 原文排除的是「给 diagram-design 设置 `disable-model-invocation: true` 来强制层级调用」；`ce037679` 要求「不许过度设计过度防御，不许把 MMW 变复杂笨重」，并要求「一张与实际同步的总图」 | `nmem m show` | 已核实 |

没有读的：`dispatch.sh` 的 `resume_one` 退出码实现（第 2163 行以后）、`status.py` 与 `finish_preflight` 全文、各 runner 适配器、Codex、Grok、Pi、Cursor 的会话记录。依赖这些的地方都标了推断或放进了第 16 节。

---

## 2. 评审指出的致命缺陷：逐条处理

| 缺陷 | 出自 | 核实 | 处理 |
|---|---|---|---|
| 被压缩的 orchestrator 收到 `#n event` 后回到 `night.md`（B8），全靠「压缩后 `AGENTS.md` 还在上下文里」和「模型会主动加载 `mmw`」两个未核实的宿主行为 | R1（两份评审） | 成立：`wake_text` 只返回 `#<n> <event>`（V3） | 采用 R3 的角色指针（Q1 D1.2）。唤醒消息自己说出去哪里，B8、B9 都不再依赖宿主行为 |
| `AGENTS.md` 那一行由 `mmw` 自己加，是先有鸡还是先有蛋的问题；票工作树里的会话按 `Where you are` 第 (c) 行去改 `AGENTS.md`，会落成 Outside Owns 改动 | R1 | 成立 | 这一行改由三处保证：`dispatch.sh check` 只读地报缺（消费仓库开夜前必跑）；`mmw` 的对应行只在「有人在场、且当前目录不在 `.worktrees/` 下」时生效；接入新仓库时由人触发的一步写入（Q1 D1.4） |
| `wayfinder` 第 6 步、`triage` 第 5 步、`improve-codebase-architecture` `### 4` 里点名下一步的句子留在上游文本 | R1 | 成立（V12） | 按 a–f 逐句拆：点名下一步的句子（c 类）移进 playbook，停止判据与防错句（e 类）留在上游（Q5 D5.3） |
| 漏掉四处已核实的夜间断点 | R1（评审 B） | 成立（V6–V9） | 全部放进第 1 批（Q3 D3.5） |
| `shared.md` 全局提醒行让所有非 MMW 项目每回合付费，而且到不了 Cursor | R2 | 成立（V16）；R2 反驳 ADR 0014 第二条理由的论证对非 MMW 项目不成立 | 不采用；ADR 0014 两条理由都保留 |
| `night.md`、`one-ticket.md` 与 `## On waking` 搬进 `mmw`，脚本里的名字和相对路径全部断开 | R2 | 成立（V2）；`## On waking` 第 3 步的 `bash scripts/dispatch.sh ack` 是相对 `dispatch` 目录的 | 不搬，也不改名（第 15 节） |
| worker 每张票都要读整份 mode | R2 | 成立：R2 的 worker 启动提示词改为「Use the mmw skill's worker playbook」 | 不采用；启动提示词字面不变 |
| 删结尾句没有挂到加载实测上 | R2 | 成立 | 第 4 批以 T1 通过为前提 |
| 把 `triage`、`wayfinder`、`to-questionnaire` 恢复成用户触发，playbook 点名它们会断链 | R3 | 成立（V1）：在 Claude Code 上，用户触发的技能不在模型的技能列表里 | 不采用；b 类改为推导规则（Q1 D1.3） |
| `to-spec` `## Next`、`to-tickets` 第 8 步留作交还行，同时 `idea-to-tickets` 也编排这段顺序，下一步有两个家 | R3 | 成立 | 这两处换成固定返回句（Q5 D5.4） |
| `charting-a-map`、`handed-back-tickets` 接近「只包一个技能」 | R3 | 成立（L7 C.6 信号 5） | 不建，只作为 mode 的路由行 |
| relay 能否区分夜与单票的 orchestrator、能否取到 spec 号 | R3（评审 B 要求核实） | 已核实能（V3） | 指针按 `to` 加 `watch` 生成；`relay.recovered` 按收件地址反查 `watches.json` |
| `dispatch.sh` 第 4115 行拒绝文字里的 `references/night.md` 路径不在锚点 lint 范围内 | R3（评审 B） | 成立（V2） | lint 的第 1 类检查把「脚本文字里点名的技能文件与小节」纳入范围 |
| 三份设计都没列：给 `wake_text` 加指针后 relay 测试的断言 | 评审 B 补充 | 成立（V5） | 同一次提交改相等断言；计数断言不受影响 |

---

## 3. 总体形态

```
已安装的技能（install.sh 按 skills.txt 软链到 ~/.mmw/installed-root 记录的 checkout；watch 期间冻结）
│
├─ self/mmw                         mode：人启动会话的唯一路由（新）
│   ├─ SKILL.md                     Where you are / Head judgement / Routes / Principles 索引 / 层级优先级
│   ├─ playbooks/idea-to-tickets.md 头部 playbook（新）
│   ├─ principles/<slug>.md         原则（新，起步 3 条）
│   └─ references/phase-boundaries.md  （出自上游 ask-matt，只有宿主中立改写）
│
├─ self/dispatch                    流水线角色入口：角色表 + ## On waking（原位）
│   ├─ references/night.md          orchestrator 操作文件（原位）
│   ├─ references/one-ticket.md     单票 orchestrator 操作文件（原位）
│   └─ scripts/…                    dispatch.sh、relay.py、watchdog.py、两个 hook；新增角色指针表
│
├─ self/implement                   worker 操作文件（从 upstream 分叉，名字不变）
├─ self/code-review                 reviewer 能力技能（分叉），references/session.md 是操作文件
├─ self/to-spec、self/to-tickets    能力技能（分叉）
├─ self/advisor                     references/advising.md 是回答方的操作文件
├─ 其余自有能力技能                 verify-ticket、ui-acceptance、design-pages、write-screen-contract、retro、…
└─ 上游能力技能                     mmw-v2/upstream*/…，尽量原文；四个被分叉的与 ask-matt 恢复原文、不安装

mmw-v2/tests/lib/check_wiring.py    接线 lint（新）
消费仓库：AGENTS.md 里指向 mmw 的一行（新）、.mmw/、docs/agents/*.md、CODING_STANDARDS.md、TESTING.md、screen contract
用户级：~/.mmw/models.json（角色 → host、model、effort）、~/.mmw/installed-root、~/.mmw/state/
宿主级提示：mmw-v2/prompt/shared.md（不承载任何 MMW 路由）
```

---

## 4. Q1 调用模型

### 决定

**D1.1 三类到达，各走各的路。**

| 会话 | 怎样到达第一份文件 | 之后怎样重入 |
|---|---|---|
| 脚本启动（worker、reviewer、axis 子代理、advisor） | 启动提示词点名角色技能，字面不变 | worker：消息里的角色指针，加 `--preflight` 的 `RESUME:`。reviewer、axis、advisor 是一次性会话，不重入（`code-review` 的 `references/session.md` `## 2` 占住回合；reviewer 丢失时由 worker 另起一个） |
| orchestrator（人说「今晚跑 spec #N」或「跑票 #N」） | `AGENTS.md` 那一行，或 `dispatch`、`mmw` 的 description，或 `/dispatch`；然后是 `dispatch` 的角色表，再到 `night.md` 或 `one-ticket.md` | 消息里的角色指针，加 `dispatch.sh status` 的 `RESUME:`，加 `night.md` 事实表 |
| 人启动、要做一件事 | 消费仓库 `AGENTS.md` 的一行，然后是 `mmw`；备用 `mmw` 的 description；手动 `/mmw` | `idea-to-tickets` 的 `## Where you are`，事实取自 tracker 与仓库 |

**D1.2 角色指针。**

- **哪些消息带指针：** 所有由脚本送进活会话的文字，末尾加一行，包括 relay `wake_text`、`dispatch.sh resume` 的消息、watchdog 告警。
- **格式（措辞在实现时定）：**
  - 发给 worker：`For the worker of #<n>: the dispatch skill's "On waking", then the implement skill's "Closing steps".`
  - 发给夜的 orchestrator：`For the orchestrator of spec #<s>: the dispatch skill's "On waking", then its references/night.md "3. Each time something wakes you".`
  - 单票 orchestrator 对应的是 `references/one-ticket.md`。
- **怎样生成：**
  - 角色到指针的对应表只放一处，放在 `dispatch/scripts/` 下，三个发送方都从它取。
  - relay 从行的 `to` 与 `watch` 得知是哪个角色、哪个 spec（V3）。
  - `relay.recovered` 从收件地址反查 `watches.json`。一个地址同时持有夜与单票两种 watch 时写哪个指针，列入第 16 节 T12。
- **指针不带什么：** 不带规则，也不带 tracker 数据。ADR 0020 的原意（「nothing the tracker already says」）保留。
- **与 hook 的关系：** 同一张表也给 hook 的拒绝文字提供锚点。

**D1.3 调用开关由推导规则决定。**

- **规则：** 一个上游技能只要被 `mmw` 的 `## Routes`、`mmw/playbooks/` 的某一步、某个角色操作文件或 `dispatch.sh` 的启动提示词按名调用，两个开关都去掉（`SKILL.md` 的 `disable-model-invocation` 与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation`）；否则保持上游设置。
- **「告诉用户运行 `/X`」不算调用**，这种点名不要求模型可触发。
- **lint 检查：** 被调用的技能都在 `skills.txt` 里，且两个开关都不在。
- **今天的推导结果与现状相同：**
  - `triage`、`wayfinder`、`to-questionnaire` 被路由或 playbook 调用，保持模型可触发；
  - `implement`、`to-spec`、`to-tickets` 分叉后是自有技能，本来就没有开关；
  - 7 个用户触发的技能都没有被调用，保持用户触发。

**D1.4 `AGENTS.md` 那一行怎样落地。**

- **位置：** 消费仓库 `AGENTS.md` 的 `## External References` 加一行，Need 列写成「一个人带到本仓库的任务、不知道用哪个技能、一次被压缩的上下文」这类触发情境，File 列写 `the mmw skill`。
- **三处保证它存在：**
  1. 接入一个新仓库时，由人触发的那一步写入（今天就是 `setup-matt-pocock-skills` 第 4 步往同一张表加行的位置，V14）。归哪个技能在下一轮归置时定，见第 16 节 U4。
  2. `dispatch.sh check <spec>`（开夜前必跑）发现缺这一行时打一行警告，只读，不写仓库。
  3. `mmw` 的 `## Where you are` 有一行「本仓库 `AGENTS.md` 没有指向本技能的行 → 加上」，只在有人在场、且当前目录不在 `.worktrees/` 下时生效。这样票工作树里的会话不会去改 `AGENTS.md`。
- **发布顺序：** 按 R1 的 K6，`mmw` 先随一次发布进入已安装 checkout，并跑过 owner 授权的 `install.sh`，之后才给任何仓库（包括本仓库）加这一行。否则会话会看到一个不存在的技能名。

### 理由

- **启动提示词的字面由测试钉住。** 钉住的地方有 `tests/dispatch/test_dispatch.sh` 第 2830 行与 `tests/dispatch/test_profiles.py` 第 70 行（R1 核实），`RESUME:` 与 `implement` 的结构也钉在一起。不经过 mode 时，夜里改动面最小，worker 也不必多读路由表。
- **指针放进消息本身，在五个宿主上都成立。** 它不依赖「压缩后常驻文件还在」，也不依赖「description 会在一行裸唤醒上触发」。这是 SSR 事实 2（确定性交给脚本）的应用。
- **`AGENTS.md` 的一行按项目常驻**，只在接入 MMW 的仓库付一行成本，ADR 0014 的两条否决理由都不触发。
- **推导规则把「谁该模型可触发」从手写名单变成可以检查的事实。** 作者不必逐个判断，Memory `ce037679` 的「不系统区分用户调用与模型调用」的原意（不给作者加负担）也保住了。

### 放弃的备选

| 备选 | 出自 | 放弃的原因 |
|---|---|---|
| `shared.md` 加一行全局提醒 | R2 | ADR 0014 的两条理由都成立（V16）；`shared.md` 是 owner 以第一人称写的全局提示，不属于 MMW |
| 把唤醒行写进 `mmw` 的 description，当触发词 | R2 | 依赖 description 能在一行 `#12 ticket.passed` 上自动触发，这是未核实的宿主行为 |
| worker 经过 `mmw` 启动 | R2 | worker 每张票都多读一份路由表；违反 L7 C.1 第 7 问 |
| 上游调用开关回到上游设置 | R3 | 断链（V1） |
| pstack 原样：能力技能全部 `disable-model-invocation: true`，只由 mode 按名调用 | L7 A.1、A.3 | 在 Claude Code 上，关掉触发的技能对模型不可见，mode 调用也够不到 |
| 只靠 `mmw` 的 description 加载 | N10 模型 C | 同形的 `ask-matt` 在 Claude Code 会话里实际调用 0 次（N10 第 7 节）；保留作备用 |
| 宿主钩子每轮注入提醒（`UserPromptSubmit` 一类） | R1、R2 | 各宿主事件不同，也会在 worker 与 reviewer 会话里跑；只作为 T1 失败时的第一个后备方案 |
| worker 的启动提示词改为点名 `dispatch` 加角色名，`implement` 正文搬进 `dispatch/playbooks/worker.md` | R3 | B7、B9 已由指针和删重复声称解决；搬家要改启动提示词、测试和 `RESUME:` 的对象，拿不到新的收益 |

### 嫁接来源

- D1.1、D1.4：R1。
- D1.2：R3。
- D1.3：R1 的推导规则加 R3 的进门检查（「夜里被点名的必须模型可见」）。
- 核实与补漏：评审 B 的核实要求（V3、V5）。

### 未确定

- T1：`AGENTS.md` 一行能否让五个宿主在任务开头加载 `mmw`。
- T10：Cursor、Grok、Pi 是否读仓库根的 `AGENTS.md`。
- T3：worker 会不会把指针当成新指令。
- T12：`relay.recovered` 的指针在一个地址持有多种 watch 时怎么写。

以上都在第 16 节。

---

## 5. Q2 mode

### 决定

**D2.1 只有一个 mode，`mmw`。** 它只服务人启动的会话，篇幅不超过 100 行。超过时，先把只有某个分支才读的内容移进 `mmw/references/`（SSR 事实 5）。

**D2.2 `mmw/SKILL.md` 的章节。**

| 节 | 内容 | 收益或来源 |
|---|---|---|
| 开头两三句 | 本技能把一个人带来的任务送到对的 playbook 或技能；把被唤醒、被压缩的会话送回它的位置 | SSR 事实 1 |
| `## Where you are` | 第一行成立的事实就走那一行（写法同 `night.md` 事实表），见下表 | (a) 防止 worker 被 `AGENTS.md` 那一行带进 mode；(b) 是 B8 的兜底；(c) 见 D1.4；(d) 给 B5 一个家 |
| `## Head judgement` | 这件事要多个会话，还是小到用户自己检查就够。前者走 spec 流水线：每张票有脚本跑的验收判据、独立会话的 reviewer、关闭的票作为记录；后者在本会话用 `tdd`，并告诉用户检查的人是他 | 迁自残留 `ask-matt` 第 3 步末段（本轮读过原文）；给 B3 一个家 |
| `## Routes` | 每行：触发情境 → 去处 + 本行独有的门槛。只列会改变去处的行 | 给 B1 一个家；各行见下 |
| `## Principles` | 每条原则一行：`**<Title>** (\`<slug>\`). <何时适用>. <一句规则>.`，外加一句「应用某条原则时读 `principles/<slug>.md` 全文」 | pstack mode `## Principles` 的写法（L7 A.1） |
| 一句层级优先级 | `shared.md`（owner 的话）高于本技能。playbook 的一步与能力技能正文冲突时：关于交付物之后做什么，以 playbook 为准；关于交付物怎么做，以能力技能为准 | 取自 R2；L7 C.2 指出 pstack 的 mode 放宽了原则却没写优先级 |

`## Where you are` 的行：

- (a) 你的第一条消息由脚本拼出，点名了一个技能 → 按那个技能做，本技能不适用。
- (b) 一行以 `#<n> `、`relay.recovered`、`watchdog:` 或 `MMW turn guard:` 开头 → 照它末尾的指针做；没有指针时，走 `dispatch` 技能的 `## On waking`。
- (c) 本仓库 `AGENTS.md` 没有指向本技能的行，且有人在场、当前目录不在 `.worktrees/` 下 → 加上。
- (d) 正在一个阶段的边界 → `references/phase-boundaries.md`。
- (e) 一个人带来一件任务 → `## Head judgement` 与 `## Routes`。

`## Routes` 的行（架构粒度的草案）：

| 情境 | 去处 | 本行独有的门槛 |
|---|---|---|
| 一个想法、一个要做的功能或改动 | `playbooks/idea-to-tickets.md` | — |
| 太大、看不清路线 | `wayfinder` 技能 | map 清空后，在新会话进 `idea-to-tickets` 的 **Spec** |
| 外来 issue，或流水线退回 `needs-triage` 的票 | `triage` 技能 | 判为 agent-ready 的进 `idea-to-tickets` 的 **Spec** |
| 有东西坏了 | `diagnosing-bugs` 技能；修法按 `## Head judgement` 走 | 没有好的 seam 时，告诉用户运行 `/improve-codebase-architecture`（它只在用户点名时启动），定下的决定进 **Spec** |
| 跑一夜、跑一张票、改 host、model 或 runner、开任务板 | `dispatch` 技能 | — |
| 出安装包 | `exe-release` 技能 | — |

不列入路由的：本身就是一件完整任务、而且 description 已经能正确触发的独立技能，例如 `research`、`wizard`、`diagram-design`、`advisor`、`code-checkers`、`manage-agents-md`、`handoff`、`wait-what`。列进来就是同一个触发写两处，也就是 `ask-matt` `## Standalone` 那种会漂移的第二份地图。

**D2.3 `dispatch` 的 `SKILL.md` 保持为流水线的角色入口，不另称 mode。**

- 角色表第 1 行改为：worker → 先 `## On waking`，再 `implement` 技能的 `## Closing steps`。
- description 删去「Start a reviewer from inside a ticket」。这是 B7 的重复声称：`implement` 的 description 已经认领了这个时刻。
- `## On waking` 原位不动。

**D2.4 与 `shared.md` 的分工。** `mmw` 不复述 `shared.md` 的任何一条。pstack mode 的 `## Autonomy`、`## Writing the reply`，在 MMW 里的对应物就是 `shared.md` 规则 1–5，所以 `mmw` 不设这两节。`shared.md` 也不承载任何 MMW 路由，它的第 11 行把无人会话的问与报交给「its skills」，新架构下这个去处就是角色操作文件与启动提示词。

### 理由

- **一个 mode，避免两个路由争同一个开头**（SSR `### Descriptions` 第 2 条）。夜里的路由由脚本送到角色，不需要 mode。
- **`dispatch` 的 `SKILL.md` 是 `dispatch.sh`、relay、`WAKES` 的同一整体的入口。** 它留在原处，改唤醒表时只动一个技能，也就是「修改只动一处」；夜里每次重入读的也只是这份薄文件。
- **mode 设 100 行上限，因为加载后整份都在上下文里**（SSR 事实 3）。

### 放弃的备选

| 备选 | 出自 | 放弃的原因 |
|---|---|---|
| 工具箱一个 mode、流水线一个 mode | R3 的命名 | 实质就是本方案，只是把 `dispatch` 称作 mode；另设一个名字没有收益。定义表里 `dispatch` 的 `SKILL.md` 归「能力技能的角色表」 |
| 一个 mode 装 `## Non-negotiables`、`## Autonomy`、`## Subagents`、`## On waking`、`## Playbooks` 五大节 | R2 | mode 变胖；worker 也读；`## On waking` 搬走会让 V2 的脚本文字失效 |
| 每个角色一个 mode（pstack `poteto-agent` 式） | — | 启动提示词已经点名角色技能；ADR 0015 已决定不交付 agent 定义 |
| 不设 mode，只新建一个 `idea-to-tickets` 技能 | N10 模型 E 的变体 | 头部判断、原则索引、阶段边界、压缩后的兜底都没有家；把 playbook 做成技能就是 L7 C.6 信号 11 |

### 嫁接来源

- 结构、行与上限：R1。
- 层级优先级句：R2。
- 「`dispatch` 是薄的流水线入口」：R3。

### 未确定

- T11：`mmw` 的 description 与 `grilling`、`wayfinder`、`to-spec`、`dispatch` 的 description 是否抢同一个请求。
- T8：100 行上限是否够用，写成后实测。

---

## 6. Q3 playbook

### 决定

**D3.1 两种 playbook，位置不同。**

| 种类 | 位置 | 起步清单 |
|---|---|---|
| 头部 playbook（人带来的一类任务） | `mmw-v2/skills/mmw/playbooks/<task>.md` | 只有 `idea-to-tickets.md` |
| 角色操作文件（脚本启动或唤醒的角色） | 原位，不搬、不改名 | worker：`implement`（分叉后）；reviewer：`code-review` 的 `references/session.md`；advisor 回答方：`advisor` 的 `references/advising.md`；orchestrator：`dispatch` 的 `references/night.md`、`references/one-ticket.md` |

wayfinder、triage、改 bug、代码健康不另写 playbook，只在 `## Routes` 各占一行：它们各自只调一个技能，没有自己的门槛和交付物（L7 C.6 信号 5）。

**D3.2 头部 playbook 的格式**（pstack 骨架按 MMW 调整）：

```
# <Name>

**You own <对象>. <一句立场>.**

<一段：这类任务为什么要这个顺序、结果交给谁、与相邻路由的区别>

## Where you are          （只有跨会话、会被压缩的 playbook 才有；事实只取 tracker 与仓库里看得到的）
| The fact | Go to |

## Steps
1. **<Step name>.** <可勾掉的祈使动作>. <门槛、例外、理由>. (principle `<slug>`)
   Done when <完成判据>.

**Reply:** <本 playbook 独有的回复内容>；每个没做的步骤各一行：步骤名 + 理由。
```

| 相对 pstack 的调整 | 理由 |
|---|---|
| 以 `#` H1 开头，不用 `###` | 文件是被单独打开的，不是 mode 的一节 |
| 每步加粗短名作为稳定标识，别处按名字引用，不按编号 | 按编号跨组件引用是 pstack 最脆的连线（L7 E.1 第 2 条、C.6 信号 8）；SSR `### Vocabulary` 已要求「by title rather than by number」 |
| 每步写 `Done when` | SSR `### Rules and completion criteria` |
| 不采用 pstack 的「步骤抄进 todo、跳过的写 `skip:`」，改在 `**Reply:**` 里逐个交代没做的步骤 | todo 列表是会话记忆，压缩后会丢，也不是每个宿主都有；「看得见它没做什么」的原意保住（L7 D.1） |
| 可重入的 playbook 开头放 `## Where you are` | MMW 已跑通的做法（`night.md` 第 13–22 行）；状态在 tracker，不在 transcript（L7 D.2 的 `session-pickup` 靠读宿主专有的 transcript，不采用） |
| 无人值守的角色文件用 `**Leaves:**`（留在哪里、给谁），有人读回复的用 `**Reply:**` | 取自 R3。夜里读产物的是早上冷读的 owner 与下一个会话（`night.md` 第 5 段）。角色文件只在下一轮编辑它们时顺带加，不为此单独改文件 |

**D3.3 `idea-to-tickets.md` 的骨架**（取自 R1 6.3，步骤名是稳定标识）：

1. **Grill.** 同时运行 `grilling` 与 `domain-modeling` 两个技能，每解决一个术语就写进 `CONTEXT.md`，按 `domain-modeling` 的说法提出 ADR。
   - 这一步点名这两个技能，而不点名 `grill-with-docs`，因为后者是用户触发的，在 Claude Code 上模型够不到。
   - 修 B2。
2. **Runnable questions.** 一个问题要运行才能回答时，用 `prototype` 技能。
   - LOGIC 或 EXP 分支的结论写进叶子目录的 `README.md`，带回 **Grill**，这一步不写生产代码。这是调用方限定被调方的范围（L7 C.2 `no-comments` 的写法），上游 `prototype` 规则 6 不改。修 B4。
   - UI 胜出方案交给 `design-pages` 技能，在宿主有 Claude Design 工具的会话里做；之后的链由 `design-pages`、`write-screen-contract` 自己的结尾段带回本 playbook 的 **Spec**，本 playbook 不复述这条链。
3. **Someone else knows.** 答案在别人脑子里时，用 `to-questionnaire` 技能。
4. **Who checks.** 套用 `mmw` 的 `## Head judgement`。答案是 No 时用 `tdd`，本 playbook 到此结束。修 B3。
5. **Spec.** 用 `to-spec` 技能。
   - 门槛：**Grill** 到 **Tickets** 留在同一个没被清空、没被压缩的上下文里；接近上下文上限时，照 `references/phase-boundaries.md` 在最近的阶段边界压缩。
   - 修 B5 的 Context hygiene 部分。
6. **Tickets.** 用 `to-tickets` 技能（principle `silence-is-never-a-pass`：判据要能失败）。
7. **Hand to the night.** 交给 `dispatch` 技能：开一夜，或一张票在夜外跑。什么时候开由用户决定。

`## Where you are` 的行：

- 已发布的 spec 没有票 → **Tickets**；
- 票已发布并通过 lint → **Hand to the night**；
- 有 prototype 结论、没有 spec → **Who checks**；
- map 已清空、没有 spec，或 triage 判为 agent-ready → **Spec**。

**D3.4 脚本启动的会话直接进入角色文件**，启动提示词不变（D1.1）。`implement` 的 `## Closing steps` 八步各加一个粗体步骤名，作为 `RESUME:` 与指针的锚点，步骤内容不动。

**D3.5 重入由脚本算出。以下断点全部在第 1 批修，都已核实：**

| # | 改动 | 修的问题 |
|---|---|---|
| a | `verify-ticket.py` `resume_at` 改印步骤名（例如 `RESUME: Start the reviewer (worker.decided, no reviewer.reported)`），同一次提交改 `test_preflight.py` 第 463–517 行的断言，并改正 docstring | V10：按编号的跨组件引用；docstring 已漂移 |
| b | `dispatch.sh status <spec>` 首行印 orchestrator 的 `RESUME: <night.md 小节标题>`，从 `spec.opened`、`spec.suspended`、`spec.closed`、`spec.retroed` 与 frontier 算出；「用户已验收」不在事件里，脚本对这种情况印「recorded; waiting for the user's acceptance」 | 让 orchestrator 的位置判断成为确定性的；需要先读 `status.py` 与 `finish_preflight`（T9） |
| c | `night.md` 事实表补一行：spec 带 `spec.closed` 与一次 `result` 为 `recorded` 的 `spec.retroed`，而用户还没验收 → 告诉用户夜的结果等他验收，然后结束回合 | V6 |
| d | `night.md` `## 3` 的表加一行 `MMW turn guard:`，处理写法照 `turn-guard.py` 拦截消息自己给出的出路 | V7 |
| e | `### Exit codes of resume` 按 `dispatch.sh` `resume_one` 的实际退出码补全（实现时读第 2163 行以后） | V8 |
| f | 「不在屏幕上提问」三个载体各定唯一的家。禁令只在启动提示词的 `AUTONOMOUS`；worker 的出路只在 `implement` 第 23 行；`NO_QUESTION` 改成角色中立，只说「屏幕上没人；照你的操作文件里无人值守时提问的那一步做」，并点名 `implement` 的步骤名与 `code-review` 的对应处 | V9；N11 missing_edges 第 2 条（reviewer 没有承接处） |
| g | 接线 lint `mmw-v2/tests/lib/check_wiring.py`（D3.6） | 让以上接线不再漂移 |

**D3.6 接线 lint。** 一个文件，与 `check_module_paths.py` 同层，由每个套件的 `run.sh` 先跑。它合并了 R1 与 R3 的检查，查六件事：

1. 脚本文字点名的每个技能文件、小节与步骤名都逐字存在。范围：`RESUME:` 的取值、角色指针表、`watchdog.py` 告警、`dispatch.sh` 的拒绝文字（包括第 4115 行）、两个 hook 的拒绝文字。做法照 L7 A.6：脚本从一个锚点常量模块取这些字面，lint 断言每个常量在所指文件里出现。
2. `WAKES` 的每个事件，在收件角色的操作文件里恰好有一个处理行：MAIN 的看 `night.md` `## 3`，WORKER 的看 `implement`。
3. `mmw` `## Routes`、`mmw/playbooks/*`、角色操作文件与启动提示词按名调用的每个技能，都在 `skills.txt` 里，且两个调用开关都不在（D1.3）。
4. 每个原则文件都在 `mmw` 的 `## Principles` 里有一行；每个被括注的 slug 都有文件。
5. 每个 `mmw/playbooks/*.md` 都被 `## Routes` 点名，`## Routes` 点名的 playbook 都存在。
6. `skills.txt` 解析出的技能 `name` 两两不同。分叉后 `mmw-v2/upstream/` 里留有同名原文，ADR 0006 实测过撞名时宿主会静默取其中一份。

每一类都配一个能让 lint 失败的反例测试（SSR 事实 2、ADR 0008）。

### 理由

- **角色文件原位不动**，因为搬家拿不到任何一种所列收益，却要改 V2 列出的脚本文字、启动提示词和测试（L7 C.6 信号 9、10）。
- **头部内容今天没有已安装的家**：B1–B5 只在未安装的 `ask-matt` 里（本轮读过残留目录）。
- **`idea-to-tickets` 有所有权、有自己的门槛（**Who checks**、上下文不断）、有交付物（已发布并通过 lint 的票）**，被四个入口复用：直接路由、wayfinder 清图后、triage 判为可做后、`improve-codebase-architecture` 定下决定后。所以它不是信号 5。
- **把重入交给脚本、把接线交给 lint，是 SSR 事实 2 与 L7 C.1 第 2 问的应用。** lint 只有一个文件、六类检查，这是 Memory `ce037679` 要的「与实际同步的总图」的机械部分，没有加新的层。

### 放弃的备选

| 备选 | 出自 | 放弃的原因 |
|---|---|---|
| `night.md`、`one-ticket.md`、`implement` 正文搬进 `mmw/playbooks/` | R2 | V2；信号 9 |
| `dispatch/references/` 改名 `playbooks/` | R3 | 收益只是让 lint 的范围按目录划分，而 lint 可以直接列出角色文件；改名要改 `dispatch.sh` 第 4115 行与表中的路径 |
| 白天另建 `charting-a-map.md`、`handed-back-tickets.md`、`adopting-mmw.md` | R3 | 前两个只包一个技能（信号 5）；第三个的内容是一次性的接入步骤，归处见 D1.4 与第 16 节 U4 |
| 新建界面 playbook | — | 只会复述 `design-pages`、`write-screen-contract` 的结尾段（信号 3、9） |
| pstack 的 `session-pickup`、`pause-safely` | L7 D.2 | 夜的暂停已有 `dispatch.sh suspend`，未提交的改动由 `start` 做成 `wip(#<n>)` 提交保存，接手有 `RESUME:`；白天的暂停判断归 `references/phase-boundaries.md` |
| `RESUME:` 保留编号，靠测试钉住 | R2 | 没有测试钉住这种对应（V10） |
| 给 `implement` 加一句「被唤醒时先按 `## On waking`」 | R1 C9 | 指针已经带着这句，再写一处就是第二份副本 |

### 嫁接来源

- 两种 playbook 与 `idea-to-tickets` 骨架：R1。
- D3.5 a、b、d、f 与 lint 第 1、2、6 类：R3。
- D3.5 c：R2 与 R3 共同指出。
- `**Leaves:**`：R3。
- lint 第 3–5 类：R1。

### 未确定

- T9：`status.py` 与 `finish_preflight` 能否算出事实表的全部取值。
- T2：压缩后，只凭「唤醒 + 指针」能否回到正确的步骤。

---

## 7. Q4 原则

### 决定

**D4.1 形式。** 原则是 `mmw-v2/skills/mmw/principles/<slug>.md`，一条一个文件，没有 frontmatter。三份设计在这点上一致。

- 文件格式：`# <Title>`；一到三句规则，写成事实而不是程序（Memory `ec59cec8`）；`**Why:**`，写出依据（ADR、有记录的运行或用户的决定）；`**Applies when:**`（可观察的触发）；可选 `**Boundaries:**`，写明调用方的领域规则在哪些地方优先（L7 C.2）；可选 `**Not:**`，写与相近原则的界线。不写历史，不列调用方。
- 引用只有一种写法：
  - `mmw` 与 `mmw/playbooks/` 内：`(principle \`<slug>\`)`；
  - 其他技能：`(the \`mmw\` skill's principle \`<slug>\`)`。

**D4.2 调用方的写法（取自 R3）。** 具体规则留在调用方的步骤里，原则名只作为句末括注。理由：

- SSR `### Load and disclosure`「A rule sits in the text of the agent that must follow it」。
- worker 不加载 mode，正常路径一份原则都不必读；只有遇到规则没覆盖的情形才读原则全文，文件读不到也不影响那一步。
- 夜间文本不设原则索引。

**D4.3 够格的门槛。** L7 A.4 的四条，加 MMW 的三条：

1. 能用短名字说出口；
2. 有可观察的触发情境；
3. 能改变一个具体决定；
4. 跨任务；
5. 至少被两处引用，引用方可以是 `mmw`、头部 playbook、角色操作文件或能力技能；每处各是不同的机制；
6. 理由有依据：ADR、有记录的运行或用户的决定（SSR `## Editing` 第 1 条）；
7. 它的读者群没有现成的家：`shared.md` 规则、`CODING_STANDARDS.md`、SSR 已有的规则不收。

**D4.4 起步三条。**

| slug | 规则（一句） | 合并了 N9 哪几条 | 依据 | 引用处 |
|---|---|---|---|---|
| `silence-is-never-a-pass` | 一道检查、一次交付不能因为什么都没做而读起来像通过；检查要证明自己能失败；查不了就说查不了 | PC1、PC2 | ADR 0008；理由今天在 `implement` 第 22 行、`night.md` 第 7 段、`ui-acceptance` 各写一版 | `idea-to-tickets` **Tickets**；`implement` 收尾；`night.md` 收口；`to-tickets` 写判据 |
| `the-tracker-is-the-state` | 你在哪一步由票上的事件决定，不由会话记忆决定；要等别人就结束回合，由事件叫醒，不轮询 | PC4、PC5 | ADR 0010、0019、0020；`dispatch/SKILL.md` 第 8 行原句 | `mmw` `## Where you are`；`idea-to-tickets` `## Where you are`；`night.md`；`implement` 的 `RESUME:` 那句 |
| `rerun-dont-reroute` | 被打断的命令原样重跑；被拒绝或撞上流水线自身的故障，就修拒绝点名的事或报 blocked，不绕路、不写重试循环、不换 host 或 runner | PC17、PC18 | ADR 0010、0017、0018（用户 2026-09-10 否决重试与换 host）；`ui-acceptance` Five rules 第 4、5 条 | `## On waking` 第 1 步；`night.md` `## 3` 的 `fault` 行；`implement` 第 18 行 |

`rerun-dont-reroute` 的 `**Boundaries:**` 写明 `shared.md` 规则 11（「redo it yourself before replying」）在 MMW 里的适用范围：重做的是自己被打断的一步，不是绕过流水线自身的拒绝。它不改 `shared.md`，只在 MMW 内划界，消除 N9 §9.3 第 1 条记下的张力（取自 R2）。

**D4.5 `ask-matt` 的 `PHASE-BOUNDARIES.md` 进 `mmw/references/phase-boundaries.md`，不做成原则。**

- 它有 57 行，是一棵有序的判断树，只在阶段边界那一个分支读，按 L7 A.5 更像 reference。
- 正文取残留目录的现有文本，相对上游只有宿主中立的改写（V13，a 类）。来源与这处改写记进一份按来源开的 merge-note。

### 理由

- 做成文件，不进任何宿主的技能列表，没有常驻开销。按「技能名 + 文件」读到它是现有做法。它随技能一起冻结。
- 三条都满足七条门槛：有两个以上不同机制的引用方，有记录在案的依据，今天的理由只在 ADR 里或各处各写一版。

### 放弃的备选

| 备选 | 出自 | 放弃的原因 |
|---|---|---|
| 每条原则一个技能，并设成 `disable-model-invocation: true` | pstack | Claude Code 上按名够不到 |
| 每条原则一个模型可触发的技能 | — | 每条都在每个会话常驻一行 description，还会被自动触发，与 pstack「You don't invoke principles」相反 |
| 写进 `shared.md` 或 `CONTEXT.md` | — | ADR 0014；词表不是规则的家（SSR `### Load and disclosure`） |
| 起步只建两条 | R1 | `rerun-dont-reroute` 有三处引用，并能消除一处已核实的张力，够格 |
| 起步八条或七条 | R2、R3 | `baseline-is-a-contract`、`clues-are-not-evidence`、`one-writer-per-file` 的完整理由已经在唯一读者（worker）的文本里（`implement` 第 22、28、47–49 行），新建文件既不减少重复，也不改变决定。第 15 节写明它们的进入条件 |
| `phase-boundary` 做成原则 | R2、R3 | 形态是 reference（L7 A.5） |
| pstack 式「回复里写出每条改变了决定的原则」 | pstack mode | 夜里没有面向人的回复；白天的回复写法由 `shared.md` 管 |

### 嫁接来源

- 形式与门槛第 5 条：R1。
- 调用方写法、`**Boundaries:**`、门槛第 6、7 条、`rerun-dont-reroute`：R3。
- `shared.md` 规则 11 的划界：R2。

### 未确定

- K8、T13：原则文件是否真的改变 agent 的决定，要在第 3 批后的走查里看 agent 是否打开了原则文件、之后是否做了不同的选择。

---

## 8. Q5 能力技能与 playbook 的分界；上游回到原文

### 决定

**D5.1 分界判据。**

- **进 playbook 或 mode 的「任务顺序」：** 一段内容回答「这个技能的交付物之后，按任务类型下一步做什么」，或者按调用者的角色或任务类型把读者送到别处。
- **留在能力技能里的「能力内部」：** 一段内容回答「怎样产出本交付物」，包括按分支选 reference、为了完成本交付物调用别的能力、自带的人工闸门（L7 A.3），以及**只取决于本技能自身输出的下一步**（例如 `design-pages` `references/pull.md` `## Reached from here` 按 `改动分类` 与有无 screen contract 分支，`write-screen-contract` `## Next` 按首写与重跑分支）。

**D5.2 五张「Find your moment」表的处理**（只列要动的；其余行属能力内部，不动）：

| 位置 | 处理 | 收益 |
|---|---|---|
| `dispatch` description「Start a reviewer from inside a ticket」 | 删；角色表第 1 行按 D2.3 改 | 去掉 B7 的重复声称 |
| `verify-ticket/SKILL.md` 第 16 行「A worker's claim, criteria runs and closeout are steps of the `implement` skill.」 | 删 | 同上（已核实原句） |
| `ui-acceptance` description「or before writing a page ticket's code」与表第 1 行 | 删；`implement` 第 16 行已点名 `references/writing-interface-code.md` | 同上（已核实） |
| `ui-acceptance` 表第 3 行（往票上写判据 → `to-tickets` 的 reference） | 不动：这是交给另一个能力，不是重复声称 | — |

**D5.3 上游改动按段分类。** 每一段上游文本上的 MMW 改动，按下表归类，第一个命中的决定去处：

| 类 | 判定 | 处理 |
|---|---|---|
| f 行数过半 | 这个技能上游的行已不到一半 | **分叉**：整体搬进 `mmw-v2/skills/<同名>/`，`skills.txt` 改为 `self/<名>`；`mmw-v2/upstream/` 里那一份恢复成最近一次 squash 的原文，不安装。`merge-notes/README.md` 用一张分叉表记下名字、上游路径、分叉起点提交，并规定每次拉上游都读一遍这些技能的上游 diff，按判断移植。当前命中：`implement`、`code-review`、`to-tickets`、`to-spec`（V11） |
| a 宿主中立 | 「the Skill tool」或斜杠改成按名点名，或会话命令改成动作 | 留，照 `merge-notes/README.md` `## host 中立` |
| b 调用开关与 description 触发句 | 两个开关 | 按 D1.3 推导，记 merge-note |
| b 同上 | description 里的触发句 | 只留本能力自己的触发；为 MMW 流程分支加的触发句移进 `## Routes`。例：`to-spec` 的「a wayfinder map or a triaged issue」随分叉成为自有文本，按自有技能的规则审 |
| c 下一步 | 只是点名下一个技能的句子 | 移进 playbook 或 `## Routes`，上游那句恢复原文 |
| d MMW 的存放位置与格式 | MMW 的存放位置、label、被脚本解析的格式，只有 MMW 下游读 | 放进上游技能目录旁**新加的** reference（上游没有这个文件，拉取不冲突），由 playbook 那一步点名（取自 R2；SSR `### Upstream skills` 第 3 条「Connect outside the upstream text first」）。例：`prototype` 规则 1 的叶子目录形状、`UI.md` 的 `## State list`（`pull_design.py` 解析） |
| e 改变能力或防错 | 改变能力本身；或删掉之后，即使 playbook 在上下文里 agent 也会做错 | 留，每段一个 merge-note 条目，段里夹着的 MMW 名词移到调用方（取自 R3）。例：`tdd` 的 seam 与重构去处、`prototype` 的 EXP 分支、`resolving-merge-conflicts` 的 clean-merge 分支 |
| 其他 | 文风、措辞 | 恢复上游原文（SSR `### Upstream skills` 现有规则） |

按这张表逐句拆开三处混合段（V12）：

| 段落 | 留在上游（e 类） | 移走（c 类） |
|---|---|---|
| `wayfinder` 第 6 步 | 清图的停止判据、「map 留着不关」 | 「新会话跑 `to-spec` 再 `to-tickets`」，由 `## Routes` 的 wayfinder 行接住 |
| `triage` 第 5 步 `ready-for-agent` 一条 | 「label 打在切出的票上，不打在这个 issue 上；关闭 issue 时链接 spec」，因为 triage 的状态机含义变了 | 「写 spec 用 `to-spec`，再用 `to-tickets` 切票」 |
| `improve-codebase-architecture` `### 4` | 「This skill changes no code」及其理由，因为用户直接斜杠进入时 mode 可能不在 | 「hand that decision to the `to-spec` skill」 |

另外两处是纯 c 类：`grill-with-docs` 末句「name the `to-spec` skill as the next step」、`prototype` `UI.md` `## Next`。它们整句移走。

残留的 `ask-matt` 目录整个恢复上游原文，不安装。需要的三块内容（头部判断、Context hygiene、阶段边界）已分别进 `mmw`。`merge-notes/triage.md` 与 `merge-notes/wayfinder.md` 里以它为出处的行改成 `mmw`（修 B10、B11）。

**D5.4 分叉后的自有技能怎样结尾。**

- **结尾只重述 playbook 顺序的，换成一句固定返回句：** 「Then return to the playbook that sent you; with none, the `mmw` skill routes what follows.」适用于 `to-spec` `## Next`、`to-tickets` 第 8 步末句、`retro` 第 186 行的「return to … `night.md` `## 5`」。这样顺序只有一个家；单独斜杠进入的会话也不会在这一跳断掉（#538 的教训）。
- **下一步取决于本技能自身输出的，保留分支**（D5.1）。

### 理由

- **分叉让 `merge-notes/README.md` 的特例消失。** 那个特例（`## 本仓自有正文的技能`）要求拉上游时手工把自动合进来的段落改回本仓的，属于会悄悄撤掉改动的手工步骤；分叉后拉上游变成机械操作，上游目录回到原文。
- **分叉不改名，所以启动提示词与测试都不动。**
- **R2 漏了 `to-spec`**，它的 merge-note 自认上游行不到一半（V11）。
- **按段分类比按技能整体分类细，而且可以复用到以后从 pstack 引入的技能。** d 类放进旁加的 reference，是 SSR 已有规则的直接应用。

### 放弃的备选

| 备选 | 出自 | 放弃的原因 |
|---|---|---|
| 调用开关回到上游设置 | R3 | 断链（V1） |
| `to-spec` `## Next`、`to-tickets` 第 8 步保留作交还行 | R3 | 顺序会有两个家 |
| `wayfinder` 第 6 步、`triage` 第 5 步、`improve-codebase-architecture` `### 4` 整段留在上游 | R1 | 其中点名下一步的句子可以拆出（D5.3） |
| d 类回退，由 playbook 那一步给出格式 | R3 | 格式要由读它的脚本与写它的技能共同遵守，放进旁加的 reference 更稳，而且不改上游 |
| 分叉时改名（例如 `ticket-review`） | R2 U3 | 好处只在「还想另装上游原版」时出现；那是范围决定，交给 owner（第 16 节 U3） |

### 嫁接来源

- 分叉门槛与名单：R1 加评审补的 `to-spec`。
- 六类：R3，其中 b 类按 R1 改写。
- d 类处理：R2。
- 固定返回句：R1。
- 删 `verify-ticket` 第 16 行：R3。

### 未确定

- T6：分叉并恢复原文之后，在丢弃分支上 `git subtree pull` 能否零冲突。
- 每个上游技能逐段的 a–f 归类是下一轮的工作，本文只给出规则和上面五处例子。

---

## 9. Q6 旧规则

### 决定

以 R1 的逐条表为底。嫁接 R3 对 ADR 0020 的修订、R3 对 `f4c3d378` 的纠正读法（原文是条件句，要求在技能层做路由）。ADR 0014 保留完整的两条理由。另写一份新 ADR，记录：

- 一个 mode，playbook 与原则放在它的目录里，由 `AGENTS.md` 一行负责加载；这取代事实 7 的「no router」；
- 上游行不到一半的技能分叉；
- 唤醒文字加角色指针（修订 ADR 0020）；
- 调用开关的推导规则。

### 旧规则处理表

| 规则 | 处理 | 原本防什么 | 新架构怎样解决、原意怎样保住 |
|---|---|---|---|
| SSR 事实 1 交出理解 | 保留，扩到 playbook 与原则 | 步骤覆盖不到的情形里 agent 无所适从 | 原则的 `**Why:**`、playbook 的开头段 |
| SSR 事实 2 脚本管确定性 | 保留，扩大应用 | 文字复述脚本；判断藏进脚本 | 重入位置由脚本算（D3.5）；接线由 lint 查（D3.6） |
| SSR 事实 3 注意力是预算 | 保留 | 读到用不上的材料 | `mmw` 不超过 100 行；worker 不经过 mode；原则不进系统提示 |
| SSR 事实 4 先定方向再信任 | 保留 | 流程僵硬、易碎 | 上游 `implement` 恢复原文后，「five lines」这个参照仍然成立 |
| SSR 事实 5 按分支渐进加载 | 保留 | 碎片、跳转 | playbook 按任务类型一个文件；`## On waking` 留在 `dispatch` 正文 |
| SSR 事实 6 技能是按名组合的平级件 | **改写** | 嵌套；复制、复述别的技能 | 加方向规则：能力技能之间平级；能力技能不点名 playbook 的顺序，结尾只说交回什么或用固定返回句；playbook 与原则是 `mmw` 目录里的文件，别的技能按「the `mmw` skill's …」点名。这不是嵌套技能，与 `fe94802d` 不冲突 |
| SSR 事实 7「一个家」 | 保留 | 第二份副本漂移 | — |
| SSR 事实 7「MMW ships no router skill」 | **废止** | 路由表会成为流程的第二份副本并漂移（`ask-matt` 的漂移：`docs/reviews/2026-09-23-skill-set/汇总.md` 第 44 行，N10 第 7 节） | 路由只有一个家（`mmw`）；顺序只有一个家（playbook）；能力技能里的顺序句是「搬」进 playbook，不是「加」一份地图；同步由 lint 第 3–5 类保证 |
| SSR 事实 7「description 说何时开始，结尾段说下一步」「结尾段从想法走到关票没有缺口」 | **改写** | #538：一跳找不到下一步 | description 仍只写触发；「下一步」的家是 playbook；「从想法到关票没有缺口」改成：从 `mmw` 出发，路由加 playbook 步骤连起来走到关票，由 `REVIEWING-A-SKILL-SET.md` 的走查从 `mmw` 起步检查 |
| SSR `### Load and disclosure`「找时刻的表在任何有副作用的步骤之前」 | 保留，分两类 | 重入时重复副作用 | 角色表与重入表在 `mmw`、`dispatch` 的 `SKILL.md` 与 playbook；能力内部的分支表在能力技能里 |
| SSR `### Load and disclosure`「A rule sits in the text of the agent that must follow it」 | 保留 | 规则写错读者 | 成为原则层的边界（D4.2） |
| SSR `### Redundancy and bloat`、`### Scripts and judgement` | 保留 | — | 后者新增：脚本印出的、指向文本的锚点由 lint 核对 |
| SSR `### Descriptions` | 保留，扩大并排检查的范围 | 两个 description 争一件事 | 删 B7 的三处；并排检查包括 `mmw` |
| SSR `### Vocabulary` | 保留 | 一词多义 | `docs/contexts/toolbox/CONTEXT.md` 加 **mode**、**playbook**、**principle**、**role pointer** 四个词条（本仓技能文本里目前没有 `playbook` 这个词，grep 为 0，不冲突） |
| SSR `### Hand-offs`「Each skill ends by naming what comes next, or the caller it returns to」 | **改写** | 产出无人接手 | playbook 的步骤点名下一步；能力技能以交回什么结尾；下一步取决于自身输出的自有技能保留分支；链上的自有技能以固定返回句结尾 |
| SSR `### Hand-offs`「Each event gets one instruction」 | 保留，变成机制 | 同一事件两种指令 | lint 第 2 类；`NO_QUESTION` 的修正（D3.5 f） |
| SSR `### Prompts written for other agents` | 保留，补一句 | 提示词替被启动方划范围 | 脚本送进会话的消息可以带角色指针；指针是地址，不是规则 |
| SSR `### Upstream skills`「fewer than half … reviewed as the set's own text」 | **改写** | 上游被改写后无法跟进 | 改为「分叉出 subtree」；加入 a–f 六类 |
| SSR `### Paths and host neutrality` | 保留，补一句 | 路径与宿主绑定 | grep 范围扩到 `mmw/`；运行时文本不指向工作树里的 `mmw-v2/` 或 `docs/`（冻结） |
| SSR `### Rules and completion criteria` 等其余节 | 保留 | — | playbook 步骤同样写 `Done when` |
| ADR 0003、0006、0007 | 保留 | 插件与安装器两条安装路径；各宿主各装一份；提示词手改漂移 | `mmw` 是普通技能；它不进 `shared.md` |
| ADR 0008 | 保留 | 闸口什么都没做却读起来像通过 | 成为原则 `silence-is-never-a-pass` 的依据 |
| ADR 0010、0017、0019 | 保留 | 轮询；会话记忆不可靠 | 成为原则 `the-tracker-is-the-state`、`rerun-dont-reroute` 的依据；`RESUME:` 由事件的 fold 算出 |
| ADR 0014 | **保留两条理由** | 到不了 Cursor；为不相干的事付每回合常驻成本 | 同样用来否决把 `mmw` 或原则写进 `shared.md`；`AGENTS.md` 一行不触发这两条理由（按项目常驻；是否每个宿主都读，待 T10） |
| ADR 0015 | 保留 | 五种壳、组装链 | 「角色 = 启动提示词点名的技能 + `models.json` 一行」就是它的延续 |
| ADR 0020「文字只带 `#<n> <event>`」 | **修订一句** | 唤醒文字复述 tracker 内容会过时或自相矛盾 | 文字是 `#<n> <event>` 加一行固定的角色指针；指针不含 tracker 数据 |
| ADR 0012、0027 与实现的分歧（N11 contradictions 第 2、3 条） | 不在本次范围 | — | 随 `night.md` 原位不动，另开票处理 |
| `merge-notes/README.md` `## disable-model-invocation`「两处同增同删」 | 保留 | 一半宿主用户触发、一半宿主模型触发 | — |
| 同节手写的 7 个名单与「上游默认模型可触发」 | **改写成推导规则** | 抢触发；夜里被 worker 触发；往产品根目录写文件 | D1.3 加 lint；推导结果与今天相同，原来防的问题照样防住；四份 merge-note 里对这条规则的复述删掉（N10 R2、R4） |
| 同文件 `## host 中立` | 保留 | — | a 类 |
| 同文件 `## 本仓自有正文的技能` | **废止**，由分叉表取代 | 拉上游时误合并本仓正文 | 分叉后不再存在这种情形 |
| Memory `411750f5`（description 只留触发；上游能不改就不改） | 保留并加强 | — | 分叉与 a–f 是它的落实 |
| Memory `ce037679`「写名字不写路径」 | 保留 | — | 指针写「技能名 + 技能内相对路径」 |
| Memory `ce037679`「MMW 不系统区分用户调用与模型调用」 | **改写** | 给作者加负担 | 只在一处区分：被调用的必须模型可触发，由 lint 推导检查，作者不必判断 |
| Memory `ce037679`「一张与实际同步的总图」 | 落实 | — | `mmw` `## Routes` 加 playbook 是给 agent 的图，lint 保证同步；给人看的图见第 16 节 U5 |
| Memory `fe94802d`「平级调用、禁止嵌套」 | 保留 | 可移植性 | playbook 与原则是文件，不是嵌套技能 |
| Memory `fe94802d`「不改上游 frontmatter；排除用 `disable-model-invocation` 强制层级」 | 读法：它排除的是「关掉开关来强制层级」（V17）；本规则只为可达性去掉开关，从不关掉 | 用开关强制层级会让调用方够不到被调方 | 原意保住；这个读法需 owner 确认（第 16 节 U2） |
| Memory `f4c3d378` | 保留，按原文读 | 不在技能层路由，agent 会乱走 | `mmw` 本身是技能，路由在技能层完成 |
| Memory `8ec53374`「agent 定义 = 读哪个 playbook + `models.json` 一行」 | 落实 | — | 不建文件，就是启动提示词加 `models.json` 一行 |

### 放弃的备选

| 备选 | 出自 | 放弃的原因 |
|---|---|---|
| 按字面恢复上游 frontmatter | R3 | 死守字面，让 playbook 断链，违反用户要求 1 |
| 判 ADR 0014 第二条理由不适用 | R2 | 对非 MMW 项目仍然成立 |

### 未确定

- U2：`fe94802d` 的读法需要 owner 确认。

---

## 10. Q7 扩展路径

### 决定

**D7.1 加一个组件，只动三张登记表：** `skills.txt`、`mmw` 的 `## Routes`、`mmw` 的 `## Principles`。lint 核对三者与实际一致，不改任何现有技能的正文。唯一的例外是原则：用到它的步骤要加一个括注。

**D7.2 能力技能的引入方式。**

| 来源 | 做法 |
|---|---|
| 源仓库本身就是技能合集 | `git subtree`，照 mattpocock、diagram-design、unlazy 的现有做法 |
| 多插件的大仓库（pstack 在 `cursor/plugins` 的 `pstack/` 子目录），要跟随更新 | 本地克隆上 `git subtree split --prefix pstack`，再对切出的分支 `subtree add/pull` |
| 同上，只要几个文件 | 钉住提交的快照目录 `mmw-v2/upstream-pstack/`（快照 `b0b9c7a0`，`plugin.json` 0.15.4；pstack 是 MIT 许可，R2 核实），配一个按清单重拷并显示差异的小脚本 |
| 要改成宿主中立（pstack 里带 `Task` 参数、`subagent_type` 或模型 slug 的编排型技能） | 分叉进 `mmw-v2/skills/` |

每种来源开一份 merge-note，记下源、提交、改了什么。研究快照 `docs/research/code-landing-refs/pstack/` 不是来源：根 `AGENTS.md` 写明它只读、不当事实。

**D7.3 进门检查。** 每个外来能力技能都要过四条：

1. 它产出一个能叫出名字的交付物，能脱离 mode 被调用。否则它是 playbook。
2. 它用到的 Cursor 专有机制都有替代（下表）。替代不了的（依赖 `/loop`、cloud agent、`agent-transcripts/`）不收。
3. 与已装技能的 description 并排读，不抢同一件事。
4. 夜里会被点名的，必须模型可触发。

**D7.4 原则与 playbook 的引入。**

- **原则：** 过 D4.3 的七条门槛。多数 pstack 原则在 MMW 已有同义的家，例如 `prove-it-works` 对应 `shared.md` 规则 4、`encode-lessons-in-structure` 对应 SSR 事实 2；这些不收。收下的正文照录（SSR `## Editing`「keeps its authors' wording」），去掉 frontmatter，把 description 改成 `**Applies when:**`，原则之间的相对链接改成 slug。
- **playbook：** pstack 的 Bug fix、Feature、Refactoring 等以开 PR 收尾，并用到 MMW 没有的技能。引入前要先定它对应 MMW 的哪条路线（`## Head judgement` 的 Yes 或 No），这是 owner 的范围决定（R2 U5）。

**D7.5 Cursor 专有机制的替代**（L7 E.2 逐项）：

| pstack 机制 | MMW 的替代 |
|---|---|
| `mode: true`、`reminder:` | 夜里：角色指针。白天：`AGENTS.md` 一行，加 `mmw` 的 description；钩子注入是后备方案 |
| `disable-model-invocation: true` 集中调用权 | D1.3 的推导规则加 lint；playbook 与原则不是技能，没有开关 |
| `paths:` | 不引入；需要时写成 description 的一个分支，或写成 playbook 里「改到 X 类文件时读 Y」 |
| `alwaysApply` 的 `pstack-models.mdc` | `~/.mmw/models.json`，只由 `models.py config` 写（ADR 0024），脚本显式读取 |
| `agents/*.md` 加 `subagent_type` | 启动提示词加 `models.json` 一行；会话内子代理用宿主自带的通用 subagent（ADR 0015） |
| `Task` 的 `model`、`readonly` 参数 | 按能力写；只读靠文字 |
| `/loop`、`/goal`、云代理 | relay 唤醒、watchdog、turn guard |
| 运行中从 trunk 重读组件 | **禁止**（Self-hosting boundary）；外来 playbook 里的这一步删掉 |
| 内置 `create-skill` | `writing-for-agents` |
| `AskQuestion` | 有人值守时直接问；在 `issue-<n>` 工作树里被 `tool-guard.py` 拒绝，出路按 D3.5 f |
| `agent-transcripts/` | 不支持；重入读 tracker |
| `cursor-team-kit` 的 `control-ui`、`control-cli` | `playwright-cli`、`computer-use`、`ui-acceptance` 的 oracle，在 playbook 里按能力点名 |

**D7.6 项目私有组件。** 它们可以是数据与仓库规则，不能是流水线角色的步骤顺序。

- **可以有的：**
  - `.mmw/target.json`、`harness/`、`journeys/`、`stories/`；
  - screen contract、`prototypes/`、`docs/agents/*.md`；
  - `AGENTS.md`、`CODING_STANDARDS.md`、`TESTING.md`。worker 本来就从工作树读这些。
- **不能有的：** 替代 `implement` 或 `night.md` 的私有 playbook。
- **理由：** 脚本印出的锚点（`RESUME:`、指针）只对已安装的角色文件核对过，一份在夜里可能被改的私有顺序文件没有这种保证。这是 Self-hosting boundary 的同一个用意（取自 R3，本文收窄了理由：R3 说消费仓库不放任何给流水线角色的指令，但 `AGENTS.md` 本来就是 worker 会读的指令）。
- **仓库专有的多步工作流**：沿用 `retro` 已有的 `repository-skill` 去处（`retro/SKILL.md` `## Prevention destinations`，取自 R2），不另开 `.mmw/playbooks/` 槽位。

### 理由

「扩展只加不改」落在三张登记表加 lint 上。进门检查把 MMW 的两条运行约束（宿主中立、夜里可达）写成门槛。

### 放弃的备选

| 备选 | 出自 | 放弃的原因 |
|---|---|---|
| `.mmw/playbooks/` 扩展点 | R1 推断 | 现在没有需求（用户要求 2） |
| 对整个 `cursor/plugins` 做 subtree | — | 带进无关插件 |
| 原样安装 Cursor 插件 | — | 只有一个宿主能用 |

### 嫁接来源

- 登记表：R1。
- 两种拉取方式：R1 与 R2。
- 快照目录加重拷脚本、进门检查、私有组件边界：R3。
- 开 PR 的对应关系、`repository-skill`：R2。

### 未确定

- 是否从 pstack 引入任何内容，属于 owner 的范围决定（U1）。

---

## 11. Q8 风险与验证

### 与 Self-hosting boundary 的兼容

- 运行时读的一切（`mmw` 的 playbook、原则、reference，角色操作文件，指针所指的文件）都解析到已安装技能目录；指针只写技能名加技能内路径，不写仓库路径。
- 每一批都作为本仓库的票，由当时已安装的冻结版本跑。变更自己的测试只在隔离的测试 home 里、对着假 tracker、假 runner 跑。
- 发布照 `AGENTS.md` `## Gotchas` 的四步提升。第三步（移动已安装 checkout）只在没有 watch 打开时做；技能列表变了的那几批，需要 owner 授权跑一次 `install.sh`。
- `install.sh --check` 新增一项（取自 R3）：列出 `~/.mmw/state/*/watches.json` 里仍然打开的 watch（V15）。这把「只在两次 watch 之间迁移」从文字变成可见的检查。它只报告，不拒绝。
- 脚本与它引用的锚点在同一个提交里，一起装进已安装 checkout、一起冻结；lint 保证它们在这个提交里彼此一致。

### 落地批次

| 批 | 内容 | 前提 | 需要 owner 做的 |
|---|---|---|---|
| 1 只加固，不搬文本 | 角色指针（D1.2，同一次提交改 V5 的断言）；`RESUME:` 印步骤名与 `implement` 的步骤名；`status` 的 `RESUME:`（T9 读完 `status.py` 之后）；D3.5 c–f；接线 lint 第 1、2、6 类；`install.sh --check` 报告打开的 watch；新 ADR 修订 0020 | 无 watch 打开 | 无（技能列表不变，`install.sh` 不需要重跑，推断） |
| 2 分叉 | 四个技能搬到 `self/`，上游恢复原文；残留 `ask-matt` 恢复原文；`merge-notes` 改写（分叉表、推导规则）；删 B7 的三处；lint 第 3 类；T6 | 第 1 批后跑过一夜 | 授权一次 `install.sh`（软链目标变了） |
| 3 新建 `mmw` | `mmw`（`SKILL.md`、`idea-to-tickets.md`、三条原则、`phase-boundaries.md`）；lint 第 4、5 类；SSR 事实 6、7 与 `### Hand-offs`、`### Upstream skills` 的改写；词条；新 ADR 其余部分；发布后按 K6 顺序给消费仓库加 `AGENTS.md` 那一行；`dispatch.sh check` 的缺行警告；跑 T1、T2、T4、T8 | 第 2 批后跑过一夜 | 授权一次 `install.sh`（新技能） |
| 4 删「下一步」句 | c 类上游句子（D5.3）；分叉技能与 `retro` 的固定返回句 | **T1 通过** | 确认可见的变化：直接斜杠 `/wayfinder`、`/grill-with-docs`、`/prototype` 时，技能结尾不再提示 MMW 的下一步 |

### 风险

| # | 风险 | 可能性 | 后果 | 验证 |
|---|---|---|---|---|
| K1 | `mmw` 没被加载（H1、H3 不成立） | 中到高（`ask-matt` 调用 0 次） | 头部照旧即兴发挥；第 4 批之后比现在更差 | T1；不过就不做第 4 批，改试钩子注入 |
| K2 | worker 把指针当成新指令 | 低（推断） | 偏离 `implement` | T3 |
| K3 | `mmw` 的 description 抢了别的技能的请求 | 中 | 多绕一跳，不会断 | T11 |
| K4 | 票工作树里的会话被 `AGENTS.md` 那一行带进 `mmw` | 低 | 多读一份文件；(a) 行把它送回 | T1 第 6 个提示；`tests/dispatch` 的一个假 runner 场景 |
| K5 | 分叉改了源路径，宿主仍读旧软链 | 确定会发生 | 改了但不生效 | 第 2 批授权跑 `install.sh`；`--check` 为 0 才算完。`tests/verify-ticket/test_draft.py` 第 528–529 行含上游 `code-review` 路径，看起来是样例文字、不需要改（推断，实现时确认） |
| K6 | `AGENTS.md` 那一行早于 `mmw` 进入已安装 checkout | 确定会遇到 | 会话看到一个不存在的技能名 | 批次顺序 |
| K7 | 同名技能静默撞车 | 低 | reviewer 读错技能 | lint 第 6 类，附反例测试 |
| K8 | 原则被引用，却改变不了任何决定 | 中 | 多读的文字 | T13 |
| K9 | lint 漏报（调用写法有多种） | 中 | 同步只停在表面 | lint 只认一种调用写法与一种「告诉用户」写法；SSR `### Hand-offs` 统一规定 |
| K10 | 一次 watch 期间有人移动已安装 checkout，旧 relay 发旧格式、新会话读新文件 | 低 | 同一夜两个版本混用 | `install.sh --check` 的 watch 报告；四步提升的第三步 |

---

## 12. 组件类型在 MMW 里的定义表

| 类型 | 在 MMW 的位置 | 格式 | 谁到达它 | 可以连向谁（方向规则） | 与 pstack 规范的差异 |
|---|---|---|---|---|---|
| mode | `mmw-v2/skills/mmw/SKILL.md`，全集只有一个 | frontmatter 只有 `name`、`description`（description 只写触发）；正文依次是 `## Where you are`、`## Head judgement`、`## Routes`、`## Principles`、一句层级优先级；不超过 100 行 | 消费仓库 `AGENTS.md` 一行；description；`/mmw` | playbook（相对路径）；能力技能（按名）；原则（索引）；自己的 reference；「告诉用户运行 `/X`」 | 模型可触发，不用 `mode`、`reminder`；只服务人启动的会话；没有 `## Autonomy`、`## Writing the reply`、`## Subagents`、`## Comments`（家在 `shared.md` 与 ADR 0015）；多了 `## Where you are` |
| 头部 playbook | `mmw/playbooks/<task>.md` | D3.2：H1、所有权行、`## Where you are`（可重入时）、带粗体名与 `Done when` 的步骤、`**Reply:**` | 只由 `mmw` `## Routes` 到达，或别的 playbook 按文件名与步骤名交接 | 能力技能、原则、别的 playbook（按步骤名）、`mmw` 的 reference | 用 H1 不用 `###`；不抄 todo；按名不按编号；多了 `Done when` 与 `## Where you are` |
| 角色操作文件（角色的 playbook） | 原位：`implement/SKILL.md`、`code-review/references/session.md`、`advisor/references/advising.md`、`dispatch/references/night.md` 与 `one-ticket.md` | 保持现有格式；步骤带稳定名；重入由脚本的 `RESUME:` 或事实表决定；无人值守的用 `**Leaves:**` | 启动提示词；角色指针；`dispatch` 的角色表 | 能力技能、原则（括注）、脚本命令、`dispatch` 的 `## On waking` | pstack 的对应物是 benny 的操作文件（L7 A.10、C.1 第 7 问），不是 mode 下的 playbook |
| 能力技能 | `mmw-v2/skills/<名>/`（自有，含分叉的四个）；`mmw-v2/upstream*/…`（上游） | 自有：frontmatter 只有两个键；上游：尽量原文，改动按 a–f 类记 merge-note | description、斜杠、playbook、角色文件、启动提示词、其他能力技能 | 其他能力技能（横向）、原则、自己的 reference 与脚本；不点名 playbook 的顺序；结尾写交回什么，或用固定返回句；下一步只在取决于自身输出时点名 | 保持模型可触发（开关由推导规则决定）；`dispatch` 的 `SKILL.md` 是带角色表的能力技能 |
| 原则 | `mmw/principles/<slug>.md` | 无 frontmatter；`# Title`、规则、`**Why:**`、`**Applies when:**`、可选 `**Boundaries:**`、`**Not:**` | `mmw` 索引；调用方括注；应用时读全文 | 其他原则；往下指向能力技能 | 是文件不是技能；具体规则留在调用方；起步三条 |
| reference | 所属技能的 `references/`；只被 `mmw` 读的放 `mmw/references/`；d 类放在上游技能目录旁新加的文件里 | 无 frontmatter | 所属技能按相对路径；别的技能按「the `X` skill's `references/y.md`」 | 能力技能、原则 | 多了「上游目录旁加的 reference」（d 类） |
| 脚本 | 拥有它的技能的 `scripts/` | 照 `CODING_STANDARDS.md` | playbook 与角色文件写出命令 | 只导入与测试，不往上调用；它印出的锚点由 lint 核对 | 与 pstack 相同；多了锚点常量模块与角色指针表 |
| hook | `dispatch/scripts/tool-guard.py`、`turn-guard.py`，由 `install.sh` 注册 | 拒绝文字：事实加唯一出路（ADR 0008） | 宿主在工具调用前、回合结束时调用 | 拒绝文字只点名存在的锚点（lint）；不承担路由 | pstack 没有这一层 |
| 角色 | 启动提示词（`dispatch.sh` `start_one`、`advise_one`）加 `~/.mmw/models.json` 一行（`junior-worker`、`senior-worker`、`reviewer`、`advisor`）；orchestrator 由人启动，没有行 | 提示词只带技能名与启动时已知的数据 | `dispatch.sh start`、`advise` | 角色技能或角色操作文件 | 不建 agent 定义文件（ADR 0015） |
| 配置 | `~/.mmw/models.json`（只由 `models.py config` 写）、`~/.mmw/installed-root`、`~/.mmw/state/` | 由脚本读写 | 脚本 | — | 相当于 `pstack-models.mdc`，但由脚本显式读，不靠注入 |
| 仓库文档 | `docs/adr/`、`docs/contexts/`、`CONTEXT-MAP.md`、`mmw-v2/merge-notes/`、`mmw-v2/downstream-notes/`、本仓 `AGENTS.md`、`CODING_STANDARDS.md`、`TESTING.md`、`docs/research/` | 各自已有的格式 | 维护者与写技能的 agent；review 的 axis 读 `CODING_STANDARDS.md`、`TESTING.md` | 可以解释理由，但 agent 行动时依据的那句话必须写在技能文本里（SSR `### Load and disclosure`） | 相当于 pstack 的 guide 与 merge 记录；运行时从不读 |
| 消费仓库私有组件 | 消费仓库的 `.mmw/`、screen contract、`prototypes/`、`docs/agents/*.md`、`AGENTS.md`（含指向 `mmw` 的一行）、`CODING_STANDARDS.md`、`TESTING.md` | 由生成它的技能维护 | 能力技能、票的 `## Read first`、worker 读工作树 | 只能是数据与仓库规则，不能是角色的步骤顺序（D7.6） | 对应 L7 A.11；多了「不放私有角色 playbook」这条边界 |

宿主级提示 `mmw-v2/prompt/shared.md` 不属于 MMW 的任何一类组件。它是 owner 面向所有项目的规则，MMW 的组件不复述它，也不往里写。

---

## 13. 归置判据

下一轮逐项归置时，对每一段内容按下面的顺序问，第一个「是」决定去处。它在 L7 C.1 的基础上按 MMW 调整。

0. **它是给维护者看的历史、理由或取舍吗？** 是 → 仓库文档（ADR、merge-note、downstream-note、`docs/`）。agent 行动时依据的那句话仍要写在技能文本里。
1. **它需要判断、后果不可逆，或需要 owner 拍板吗？** 是 → 留在文字里（playbook 步骤或技能正文），不做成脚本（L7 C.1 第 1 问）。
2. **它能确定性地执行或检查吗？** 是 → 按形态选：
   - 脚本，调用方写出命令；
   - 要在工具调用时拦截的 → hook，拒绝文字给唯一出路；
   - 要求文本与脚本一致的 → lint。
3. **它是 owner 对所有项目的规则吗？** 是 → 它的家是 `shared.md`，MMW 不复述，也不往里写。
4. **它是脚本启动或被唤醒的某个角色的步骤顺序吗？**（单一入口、单一任务类型） 是 → 那个角色的操作文件，原位，不拆成三层（L7 C.1 第 7 问）。
5. **它是一个人带来的某类任务从头到尾的顺序，决定了两个以上能力的先后与门槛，并有自己的交付物吗？** 是 → `mmw/playbooks/` 的一份 playbook。只调一个技能、没有自己门槛的 → `mmw` `## Routes` 的一行。
6. **它是产出可命名交付物、能脱离 mode 被调用的能力吗？** 是 → 能力技能，内部步骤留在里面。下一步只在取决于本技能自身输出时写在结尾，否则用固定返回句。
7. **它是跨任务的判断，并且过了 D4.3 的七条门槛吗？** 是 → 原则；具体规则仍留在调用方步骤里并括注。
8. **它只在某个分支才需要、写给另一个读者、会增长，或是模板、样例吗？** 是 → 所属技能的 reference。所属技能是上游的，且内容是 MMW 的存放位置或格式 → 上游目录旁新加的 reference（d 类）。
9. **它是上游文本上的 MMW 改动吗？** 是 → 按 D5.3 的 f、a、b、c、d、e 顺序判定。
10. **它是某个消费仓库特有的数据或规则吗？** 是 → 那个仓库的私有组件（D7.6）。

**不拆、不动的条件**（任一成立就原样不动，并在不动清单里写明理由）：

- **说不出收益。** 移动、拆分、新建说不出以下六种收益之一：去掉一处经 grep 核实的真重复；给无处安放的内容一个家；让上游回到原文；让内容被两个以上调用方复用；让以后加外来技能不必改现有文字；消除一处已核实的断点或冲突。
- **规则绑定具体机制或领域参数，或只有一个调用方**（L7 C.2）。
- **多步内容服务一个可命名的交付物**（L7 C.3）。
- **长内容只有一个调用方、本身就是产物、机械部分已在脚本里**（L7 C.4，例如 `night.md` 的 closing pass）。
- **读者是只读一份文件的独立代理，复述是必要的**（L7 C.5）。
- **它被脚本文字、启动提示词或测试按字面引用，而移动拿不到上述收益**（V2；`dispatch.sh` 第 1949、1967、2072 行）。
- **移动之后需要按步骤编号引用它**（L7 C.6 信号 8）。

每一次归置提案都要逐条过 L7 C.6 的十一个信号（第 14 节是本文自己的一次）。

---

## 14. 改动清单、收益与 C.6 自查

| # | 改动 | 收益（用户要求 2 所列） |
|---|---|---|
| C1 | 新建 `mmw`（`SKILL.md`） | 给无处安放的内容一个家（B1、B3、B5）；以后加外来技能时不必改现有文字（登记表） |
| C2 | `idea-to-tickets.md` | 给无处安放的内容一个家（`ask-matt` 主流程、Context hygiene）；把 MMW 流程移出上游文本（五句）；被四个入口复用；消除断点（B2、B4） |
| C3 | 三条原则 | 给无处安放的内容一个家（理由只在 ADR 里）；去重复（理由各处各写一版）；被两个以上调用方复用；消除张力（`shared.md` 规则 11 的适用范围） |
| C4 | `mmw/references/phase-boundaries.md` | 给无处安放的内容一个家（B5） |
| C5 | 角色指针 | 消除断点（B9 已核实、B8） |
| C6 | `RESUME:` 印步骤名、`status` 的 `RESUME:` | 消除断点与漂移（V10） |
| C7 | `night.md` 三处修补（D3.5 c–e） | 消除断点（V6–V8） |
| C8 | `NO_QUESTION` 角色中立 | 消除冲突（V9） |
| C9 | 接线 lint | 把「总图同步」从文字要求变成机制（L7 C.6 信号 4）；消除以上断点的复发 |
| C10 | 分叉四个技能；`ask-matt` 恢复原文 | 让上游回到原文；消除断点（B10、B11） |
| C11 | 删 B7 的三处 | 去掉经 grep 核实的真重复 |
| C12 | 调用开关改成推导规则 | 去掉真重复（四份 merge-note 复述，N10 R2、R4） |
| C13 | c 类句子移走，换成固定返回句 | 让上游回到原文；顺序只有一个家 |
| C14 | SSR 事实 6、7 与两节的改写；新 ADR；ADR 0020 修订 | 消除已核实的规则冲突（事实 7 与已定方向） |
| C15 | `install.sh --check` 报告打开的 watch | 把 Self-hosting boundary 的一条文字规则变成可见的检查 |
| C16 | 消费仓库 `AGENTS.md` 一行，与 `dispatch.sh check` 的缺行警告 | 消除断点（`mmw` 的加载） |

**L7 C.6 十一个信号自查：**

1. **没有先确认已有组件不是合适的归宿。** 未触发：头部内容没有已安装的家；界面链与角色文件已有家，所以不建界面 playbook、不搬角色文件。
2. **新增内容不改变决定。** 未触发：每行路由都改变去处或门槛；指针改变重入时读哪个文件；原则各写明改变的决定（K8 待实测）。
3. **重复已有的、位置得当的指引。** 部分触发，已说明：原则与调用方原句并存，这是 L7 C.5 允许的读者不同的重复，调用方只留具体句；`mmw` 不复述 `shared.md`。
4. **本可由机制强制的规则写成了文字。** 未触发：同步、锚点、`WAKES` 与处理行、同名，都交给 lint；打开的 watch 由 `--check` 报告。
5. **playbook 只调一个技能，没有门槛、所有权、交付物。** 未触发：只建 `idea-to-tickets`。
6. **reference 每次都读、只有一个调用方、读者是本代理。** 未触发：`phase-boundaries.md` 只在阶段边界那一行读。
7. **原则说不出改变哪个决定，或只适用一步。** 未触发：三条都跨三处以上。
8. **拆完需要按步骤编号引用。** 未触发，而且反过来：把现有的编号引用（`RESUME:`）改为按名引用。
9. **拆出的内容没有第二个调用方、也不减少重复。** 未触发：角色文件不搬，理由正是这一条。
10. **把单入口的固定流程拆成三层。** 未触发：worker、reviewer、orchestrator、advisor 都保持一个操作文件。
11. **把只在流程之间复用的内容做成能力技能。** 未触发：playbook 与原则都不是技能。

---

## 15. 不动清单

| 部件 | 不动的理由 |
|---|---|
| 启动提示词三种字面、`AUTONOMOUS`、`PRODUCT_RULES` | 测试钉着；`PRODUCT_RULES` 已经是「一句数据加一个指针」 |
| `night.md`、`one-ticket.md` 的位置与结构（只做 D3.5 的三处修补） | 单一入口、单一任务（L7 C.1 第 7 问）；L7 C.4 的不拆理由都成立；V2 |
| `dispatch/references/` 的目录名 | 改名拿不到收益；脚本按路径点名它 |
| `dispatch` 的 `## On waking` 与 `inside-a-ticket.md`、`editing-models.md` | 三个角色共用前者；后两个是能力内部的分支 |
| `implement` 的全部内容（只加步骤名、改 docstring；分叉只是整体搬家） | worker 的操作文件 |
| `code-review` 的门表、`references/session.md` 与四个 axis 文件；`advisor` 的两扇门 | 按提示词形状区分角色，属能力内部；ADR 0014 |
| `verify-ticket` 除第 16 行外的全部；`ui-acceptance` 除 B7 两处外的全部（包括 `## Five rules while the product is running`） | 能力内部；`PRODUCT_RULES` 指向它 |
| `design-pages` 全部（包括 `pull.md` `## Reached from here`、`edit-pages.md` `## Next`）；`write-screen-contract` `## Next` | 下一步取决于自身输出（D5.1） |
| `exe-release`、`code-checkers`、`manage-agents-md`、`diagram-design`、`research`、`wizard`、`handoff`、`teach`、`wait-what`、`grill-me`、`grilling`、`domain-modeling`、`codebase-design`、`diagnosing-bugs` | 单一能力，入口靠 description 或调用方，没有要搬的流程段；B6 的缺口由 `## Routes` 处理，不改 `diagnosing-bugs` |
| 上游 e 类改动（`tdd`、`prototype` EXP、`resolving-merge-conflicts` 等） | 改变能力本身，已有 merge-note |
| 7 个用户触发技能的调用开关 | 按推导规则得到的结果与现状相同 |
| `relay.py`、`watchdog.py`、两个 hook 的位置与判定逻辑；`models.json` 结构、`models.py` | 已跑通；只改它们发出的文字 |
| `dispatch.sh` 里「角色 → 技能」的 case 分支（不做成数据文件） | 只有三行；加新角色本来就要改 `WAKES` 与脚本（R3 10.3） |
| `shared.md`、`hosts/*.md`、`render.py` | 宿主级提示，不是 MMW 的组件 |
| `CODING_STANDARDS.md`、`TESTING.md`、`CONTEXT-MAP.md` 的结构 | 各有其读者；词表只加四个词条 |
| 现有 ADR 的正文 | ADR 记录决定；变化另写新 ADR（`shared.md` 规则 13 的例外） |
| N9 其余原则候选：`baseline-is-a-contract`（PC8）、`clues-are-not-evidence`（PC11）、`one-writer-per-file`（PC12） | 完整理由已经在唯一的主要读者（worker）的文本里（`implement` 第 22、28、47–49 行），新建文件不减少重复，也不改变决定。进入条件：第二个不同机制的调用方开始需要它的理由，且那里今天没有这条理由 |
| N9 的 PC3、PC6、PC7、PC9、PC10、PC13–PC16 | 已有家（`shared.md`、`CODING_STANDARDS.md`、SSR），或已由机制强制，或只在两处（PC15） |
| `dispatch.sh` 头注释与 `--help` 的漂移（N10 B12）；ADR 0012、0027 与实现的分歧 | 真问题，但不属于架构，另开普通票 |
| task board、`migrations/`、`tests/` 的结构 | 与分层无关 |

---

## 16. 未确定、需要的实测、需要 owner 决定的事

### 需要实测

全部在隔离的测试 home 里做，装开发版技能，不碰已安装的 checkout。

| # | 问题 | 实测办法 | 定下什么 |
|---|---|---|---|
| T1 | `AGENTS.md` 一行能否让五个宿主在任务开头加载 `mmw` | 临时消费仓库（假 tracker），五个宿主各起新会话，给六个提示：「我有个想法想做出来」「这个页面坏了」「grill me on X」「/to-spec」「今晚跑 spec #N」，以及一条 worker 形状的启动提示词；从 transcript 或宿主日志记录打开了哪些文件。通过标准：线上跑角色的宿主（claude、codex、grok）在前五个提示里至少 4 次打开 `mmw`，第六个提示不偏离 `implement`；Cursor 与 Pi 如实记录 | 第 4 批做不做；不过就试钩子注入 |
| T2 | 压缩后，只凭「唤醒 + 指针」能否回到正确的步骤 | 用 `tests/dispatch` 的假 runner 开一夜，对 orchestrator 执行宿主的压缩命令后投一条 `#3 ticket.passed`，检查它先 ack、再跑 `status` 与 `advance`；另给一个全新会话只发一条「唤醒 + 指针」作代理测试 | 指针的措辞 |
| T3 | worker 会不会把指针当成新指令 | 假 runner 投递；再在一个真实 worker 上跑一次 `resume` | 指针的措辞 |
| T4 | 持有 `mmw` 的会话能否在五个宿主上按名加载 `to-spec` 等被调用的技能 | 照 `idea-to-tickets` 做到 **Spec** | 推导规则是否够用 |
| T5 | lint 每类都能失败 | 反例测试 | — |
| T6 | 分叉与恢复原文后拉上游零冲突 | 丢弃分支上 `git subtree pull` | 第 2 批完成 |
| T7 | `mmw/` 下没有仓库路径、没有爬出技能目录的相对路径、没有「from trunk」 | 扩展现有的路径 grep；发布后 `install.sh --check` | — |
| T8 | 新文件的实际效果，以及 `mmw` 的篇幅 | SSR `## Verifying` 走查：给全新 agent 一个任务板的小想法，走 `idea-to-tickets`；另给一个 map 已清空的 wayfinder 场景；报告它打开的文件、在哪里猜、在哪里停；量 `mmw` 的行数 | — |
| T9 | `status.py` 与 `finish_preflight` 能否算出事实表的全部取值 | 读两处全文，写出取值表，加 `tests/dispatch` 场景 | D3.5 b 的具体做法 |
| T10 | Cursor、Grok、Pi 是否读仓库根的 `AGENTS.md`（Grok 有 `[compat.claude]`） | T1 的前置检查 | — |
| T11 | `mmw` 的 description 是否抢别的技能的请求 | 按 SSR `### Descriptions` 第 2 条并排读，再用 T1 的会话验证 | — |
| T12 | 一个地址同时持有夜与单票两种 watch 时，`relay.recovered` 的指针写哪个 | 读 `watches.json` 的实际形状，看这种情况是否会出现 | 指针表的一行 |
| T13 | 原则文件是否改变 agent 的决定 | T8 的走查里记录是否打开了原则文件、之后是否做了不同的选择 | 原则层增减 |

### 需要 owner 决定

这些是范围、可见效果或 owner 自己的规则，按 `shared.md` 规则 1 由 owner 决定。

| # | 决定 | 建议 |
|---|---|---|
| U1 | 是否从 pstack 引入任何原则、能力技能或 playbook；引入 playbook 时，它对应 `## Head judgement` 的哪条路线 | 本文只给进入的方式，不建议现在引入 |
| U2 | `fe94802d`「不改上游 frontmatter」的读法：只为可达性去掉开关、从不关掉，算不算在允许之内 | 算；今天已经这样做了六个技能，推导后剩三个上游技能被翻转 |
| U3 | 分叉后不再能同时装上游原版的 `implement`、`code-review`（同名）；是否需要在 MMW 之外使用上游原版 | 现在不装；要装就得给分叉版改名，这是范围决定 |
| U4 | 接入一个新消费仓库时写 `AGENTS.md` 那一行的一步，归哪个技能：`setup-matt-pocock-skills` 第 4 步（上游技能，会往上游文本加 MMW 流程）、`manage-agents-md`（自有），还是 `mmw` 自己的一行 | 工程上倾向 `mmw` 的 (c) 行加 `dispatch.sh check` 的警告，不改上游；下一轮归置时定。这一步不改变任何客户可见的东西，列在这里只因为它涉及 owner 的所有消费仓库 |
| U5 | Memory `ce037679` 的「一张与实际同步的总图」指给 agent 的路由，还是给人看的图 | 本文按给 agent 的路由加 lint 落实；要人看的图，另做一份由 lint 同源生成的页面 |
| — | 第 2、3 批各需要 owner 授权跑一次 `install.sh`；第 4 批会改变直接斜杠进入上游技能时看到的结尾 | 按批次表 |

### 未能核实的事实

- `dispatch.sh` 的 `resume_one` 的实际退出码（D3.5 e 的内容来源），实现时读第 2163 行以后。
- `tests/verify-ticket/test_draft.py` 第 528–529 行的上游路径是不是纯样例文字（推断是）。
- Codex、Grok、Pi、Cursor 上 `disable-model-invocation` 与 `allow_implicit_invocation` 的实际效果：只在 Claude Code 上核实过。本方案不依赖它们，因为推导规则只把开关去掉。
- 第 1 批不需要重跑 `install.sh`（推断：技能列表与软链目标都不变）。
