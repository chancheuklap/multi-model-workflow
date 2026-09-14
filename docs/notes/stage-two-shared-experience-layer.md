# 阶段二与阶段三：共享经验和跨夜学习闭环

日期：2026-09-14

对象：[《Project Context 调研与 MMW 方案》](https://claude.ai/code/artifact/b9520c08-eb0d-40f1-872e-228662445954?via=auto_preview)第 6 节“阶段二 · 共享经验层 · NOWLEDGE MEM 自带机制优先”、第 7 节“阶段三 · 跨夜学习”和第 9 节“决定”

性质：阶段二与阶段三共同实施前的研究结论，不修改产品代码

## 结论

阶段二与阶段三必须作为同一条经验反馈闭环一起实施，不能把“执行时共享经验”和“执行后改变下一次行为”拆成两个互不相干的方案：阶段二让一个 task 内的 agent 立即写入、主动取得并复用已经证实的经验；阶段三在每份 spec 的 night 完成后，把 Memory、ticket event、review 结果、`git log` 和交付意图放在一起复盘，识别跨 ticket、跨 spec 或跨 night 重复的问题，形成可核对的 proposal；owner 批准后，再通过现有 issue 和 ticket 流程把它变成机器检查、reviewer Rule、repository authority、MMW skill/reference/script 或 `mmw-toolbox` Memory。批准后的结果又会在下一次阶段二读取时生效。

task root 仍按已经确认的语义解析：spec 有 native map parent 时，map 是 task root；spec 没有 map parent 时，该 standalone spec 自己就是 task root。一个 map 可以拆成多份 spec 并行执行，这些 spec 下的 worker 和 reviewer 使用同一个 task scope；standalone spec 下的全部 ticket 使用该 spec 的 task scope。task root 决定执行时谁共享经验，不限制阶段三在 repository 内识别跨 task、跨 night 的重复问题。

阶段二使用三个互补读取通道：

1. `dispatch.sh open <spec>` 和 `dispatch.sh start <ticket> worker|reviewer` 根据 GitHub native parent 得到 task root，精确列出这个 task root 已有的 Memory，直接交给 main agent、worker 或 reviewer。
2. `dispatch.sh start <ticket> worker|reviewer` 另用当前 ticket 的执行合同主动检索 repository 与 `mmw-toolbox` 历史经验，解决新 task 还没有 scoped Memory 的冷启动。
3. agent 遇到具体的非显然故障时，以当时的错误、命令和组件主动做 semantic search。先搜当前 task root，仍没有答案时再搜当前 repository Space 和已批准的 `mmw-toolbox`。

worker 一旦证实一条同一 task 其他 ticket 可复用的经验，就立即写入 repository Space，并带当前 task root 的 scope label。后来启动的 worker 或 reviewer 会自动得到它；已经运行的 agent 在遇到相同问题时通过主动检索得到它。

不增加实时消息系统、Memory relay、retro 状态机或新的审批队列。必须立即改变其他 ticket 行为的信息不是经验，继续使用现有 `contract`、`fault` 或 `decision` tracker event。retro 报告不是 ticket state：它使用已有 spec comment 留下结构稳定、可追溯的 `NIGHT RETRO` 记录；需要 owner 决定的 proposal 使用已有 `ready-for-human` 队列。

## 文档覆盖范围

本文件覆盖阶段二与阶段三组成的完整闭环，而不只覆盖当前任务的检索：

1. repository Space 与 `mmw-toolbox` 的布局；
2. worker、reviewer 的 Identity，以及 main agent 的读取边界；
3. task root 的解析：有 map 时使用 map，没有 map 时使用 spec；
4. worker 何时写 Memory、写什么和如何证明；
5. dispatch 如何主动把当前 task root 的经验交给 agent；
6. 已经运行的 agent 如何主动取得后来出现的经验；
7. Thread capture、Working Memory 和跨夜 retrieval；
8. reviewer 的独立性与 reviewer Rule；
9. 每夜 Memory 收口、supersede/deprecate 与 retro 的衔接；
10. retro 的触发点、完整证据输入、跨 night 聚合与缺失证据语义；
11. 上一次行动项核验、交付意图对照、review 结果学习和 proposal 格式；
12. owner 决定、长期载体及其如何回流到下一次阶段二读取；
13. 不可用时的行为、实施范围、验收与效果指标。

## 已定决定与本次更新

### 保留的阶段二决定

- 经验不是 ticket state，不写成 tracker event；agent 直接写 Nowledge Mem。
- 能用 Nowledge Mem 的 Space、Identity、Memory、Thread、Working Memory、Rule、supersede 和 deprecate 完成的部分，不另造存储或生命周期。
- 每个客户 repository 有自己的 Space；不同客户 repository 互不可见。只有 `mmw-toolbox` 可以作为所有 repository 明确批准的共享来源。
- pipeline worker/reviewer 的 Memory 与自动采集 Thread 进入 repository Space，不进入个人 Default；owner 自己的普通会话保持现状。
- 普通经验无需 owner 逐条批准。把经验变成跨 repository 内容或常驻行为，只能形成提案，由 owner 批准后执行。
- 当前流水线没有独立 verifier；阶段二只设计 main agent、worker 和 reviewer。

### 阶段二与阶段三共同实施

- 阶段二的 Memory closing pass 只判断单条经验是否保留、纠正或失效；它不能只靠一夜的 Memory 判断问题是否跨 ticket、跨 spec 或跨 night 重复。
- 阶段三的 retro 负责把完整运行证据聚合起来，验证上一次行动项，形成 proposal，并把 owner 批准后的改动送回下一次阶段二读取。它不是一个以后再补的独立模块。
- 一份 spec night 是 retro 的触发与本次证据范围；repository 是重复问题的历史聚合范围；task root 是执行时共享 Memory 的范围。三者分别回答“何时复盘”“与哪些历史比较”“当前哪些 agent 共用”，不能互相替代。
- 同一 map 的多份 spec 可以并行结束。每份 spec 各自 retro；后完成的 sibling spec 能读取先完成 spec 的 `NIGHT RETRO` 和 proposal。整个 map 不增加第二次强制 retro，也不等待所有 sibling spec 才学习。
- retro 只提出长期改动，不直接修改 Rule、`AGENTS.md`、gate、script、skill 或 `mmw-toolbox`。proposal 进入已有 `ready-for-human` 队列；owner 批准后，正常发布成 spec/ticket 并按 frozen runtime 边界落地。

### 被最新事实替代的旧结论

| Artifact 或早期调查中的说法 | 最新结论 | 原因 |
| --- | --- | --- |
| 用 ticket title 与 `## Owns` 检索“本票经验” | title 与 `## Owns` 不决定共享范围 | 它们分别是切片名称与写入边界；同一 task 可能包含多份并行 spec |
| Parent spec 是一次任务的共同上下文 | task root 是 `map if present, otherwise spec` | map 是多 spec task 的顶层；standalone spec 自己是顶层 |
| `--time today` 表示当夜 | 不按日期定义 task | 夜会跨午夜，日期也不能说明两条经验属于同一个 task |
| repository 使用 `strict` 同时读取 toolbox | repository 使用 `shared`，只链接 `mmw-toolbox` | Nowledge `strict` 只读当前 Space，不能读取 shared Space |
| Context Bundle 或 Working Memory 会提供当前任务经验 | 它们只提供 Identity、Space、Rule 与 Space 级简报 | 都没有 task root、label filter 或 task query |
| reviewer 不接收任何 worker 经验 | reviewer 接收同一 task root 的已验证操作经验，但不接收 worker Thread、推理或正确性结论 | task 经验服务所有执行角色；独立审查隔离的是推理与待验证结论 |

## 已确认事实

### MMW 当前结构

- `tree.py`、Task Board 和 tracker 文档共同定义四层 native parent graph：`map → specs → tickets → children`。
- Task Board 的 `The Night` 是一个顶层 map 及其全部 specs/tickets；没有 open map parent 的 spec 自己成为一项 task。小写 `night` 仍是 `dispatch.sh` 对一份 spec 的一次运行。
- 真实 tracker 已验证 `#384 map → #374 spec → #375 ticket`；同一个 `tree.py 384 --root map` 调用读出了 #374 下的七张 tickets。
- `dispatch.sh read_ticket()` 已经从 ticket native parent 取得 spec。`## Parent` 是给 agent 读的 spec section 指针，不是机器归属关系。
- `to-spec` 已允许一个 map 拆成多份 specs，但发布步骤尚未明确保证这些 specs 是 map 的 native children。

### Nowledge Mem 当前能力

| 能力 | 已确认行为 | 阶段二用途 |
| --- | --- | --- |
| `memories add` | 可指定 Space、Identity、unit type、labels；写入后即可检索 | worker 即时保存显式经验 |
| `memories list` | 可按一个 label 精确列出；本机重复 `--label` 实测为 OR | 列出当前 task root 或当前 spec 夜间产生的经验 |
| `memories search` | semantic + text search，约 0.5 秒；可按 label、unit type、时间和 metadata 过滤 | agent 按真实问题主动找经验 |
| `ask` | 本机一次约 130 秒 | 不进入派发路径 |
| Space | `strict` 只读当前 Space；`shared` 读取当前 Space 和显式 shared Spaces | repository 隔离并只共享 `mmw-toolbox` |
| Identity | provenance、默认 Space 与 agent Rule 的选择，不是授权，也不是 Memory 可见性过滤器 | 区分 worker/reviewer 来源与常驻 Rule |
| Thread capture | connector 在 session 结束/compact 时保存完整会话；后台可能蒸馏成 Memory | 跨夜证据与宽背景，不承担同夜保证 |
| Working Memory | 每个 Space 一份简报，早晨生成，新 Memory 后异步刷新 | session start 的宽背景 |
| Context Bundle | Identity、active Space、active Rules、Working Memory | startup 背景；不含 task retrieval |
| supersede/deprecate | supersede 保留旧条目并建立 replacement；deprecate 使其退出普通 recall | 纠正或结束经验 |
| active Rules | 编译进 Context Bundle；普通 Memory 不会自动变 Rule | owner 批准后的 reviewer/Space 常驻行为 |

### 当前安装状态

- 本机 CLI/server 是 `0.10.78`，官方最新版本是 `0.10.81`；本文只使用 `0.10.78` 已实测接口。
- Spaces 功能已经启用，目前只有 Default；repository Spaces、`mmw-toolbox` 和 MMW Identities 尚未建立。
- 当前只有 `default` Identity；active Rules 为 0，已有 Rule 全部是 draft。
- MMW 目前只由 `install.sh` 配置 Cursor 的 Nowledge MCP；dispatch、implement 和 runner adapter 里还没有阶段二路由。

### MMW 当前收口与 review 证据

- `mmw-v2/skills/dispatch/references/night.md` 的 `## 4. The closing pass` 要求 main agent 读取本 spec 的每张 ticket，把每个 `finding` 以 `fixed`、`stale` 或 `became-ticket` 路由；`dispatch.sh summary <spec>` 在仍有未路由 finding 时拒绝关闭 night。
- `dispatch.sh summary <spec>` 当前只生成 `NIGHT SUMMARY`、写入 `spec.closed` 并停止该 spec 的 relay。它没有 retro，也不会比较更早的 spec 或 night。
- 每个 ticket 的 comment 中已经有完整的 script-written event fold；`ticket.bounced`、`ticket.returned`、`worker.lost`、`reviewer.reported`、`child.opened`、`child.closed` 和 `ticket.checked` 足以作为第一版 process evidence，不需要先保存全部 agent transcript。
- reviewer comment 已固定分成 `Standards`、`Spec`、`Tests` 三个 axis，并将 finding 分成 `In-ticket` 与 `Out-of-ticket`。但每条汇总行只有 axis、path、line 与自由文本 claim，缺少可稳定聚合的 finding class。
- 当前 `route ... stale` 只说明 finding 在 `HEAD` 已不成立，没有区分“原 finding 本来就是误报”和“finding 曾经成立但被其他 ticket 修复”。阶段三不能把两者混成 reviewer false positive。
- `git log` 能给 closing pass 自行修复、ticket merge、proposal 后续落地和当前 base revision 提供独立证据；它不能单独说明 agent 为什么失败，所以原因仍以 event、finding body 和 review comment 为准。

### 可借鉴实现与适配结论

- BMAD-METHOD 当前 `bmad-retrospective` 的实现会读取完整 spec、全部 story、整段 diff、逐 story commit、上一次 retrospective 和可用的 session log；每个 finding 必须带来源，缺失证据必须明确缩小结论范围。MMW 采用它的 evidence inventory、previous-action verification 和“无来源不成 finding”，不采用它的独立 retrospective 文档树、sprint status 和团队讨论流程。
- Devin Session Insights 在 session 完成后按需生成可执行建议，证明“结束后分析真实轨迹”是成熟产品形态；MMW 已有更结构化的 tracker event，因此第一版不依赖完整 Thread。
- Augment Code Review 把 repository `AGENTS.md`/`CLAUDE.md` 与按 path 生效、带稳定 id 和 severity 的 review guideline 分开。MMW 采用“长期规则必须有明确载体和适用范围”，不引入 Augment 的专有配置格式。
- OpenAI 的 harness engineering 经验明确反对把全部知识堆进一个巨大 `AGENTS.md`，并主张把可执行 invariant 交给机器检查。MMW 因此只把不可从代码推得、对全 repository 通用的约束放进 `AGENTS.md`；能机械判断的 proposal 优先进入 target、judge、lint 或 script。
- mattpocock 上游 `retro/SKILL.md` 仍是针对单个 coding session 的 design notes，分类包括 Navigation、Automated checks、Coding standards、Global `AGENTS.md`、Tool economy、No-ops 和 Information access。MMW 复用这些改进目的地作为辅助分类，但分析对象改成一份 spec night 的完整 tracker evidence，并与 repository 历史比较。
- 调查过的现成方案都没有直接覆盖 MMW 的 GitHub native parent、event fold、`route` 和 frozen runtime。因此采用“扩展现有 MMW + Nowledge Mem”，不直接引入外部库，也不 fork 另一套工作流。

## Working Memory 是什么

Nowledge Mem Working Memory 是每个 Space 一份、由 AI 维护的每日简报，内容是当前 focus areas、open questions 和 recent activity。

- 每天早晨生成并归档上一份；新 Memory 写入后也会异步刷新，但延迟比其他后台任务更长。
- 支持的 connector 在 session start 时通过 Context Bundle 注入它；正在运行的 session 不会收到后来刷新出的内容。
- Context Bundle 还包含 Identity、active Space 和 active Rules，但不包含“按当前 task root 搜出的 Memory”。
- shared retrieval 只扩大 Memory search 的读取范围，不合并 Working Memory。repository Space 共享 `mmw-toolbox` 后，Context Bundle 仍只带 repository Space 自己的一份 Working Memory。
- 一个 repository Space 同时运行多个 map 时，它只有一份 Working Memory，不能按 map 过滤。

因此 Working Memory 是 repository 的宽背景，不是 map 级共享经验，不是实时 scratchpad，也不是确定性的任务输入。阶段二不写它、不 patch 它，也不为每个 map 新建 Space。

这一区分由本机 `nmem 0.10.78` 的 CLI、Context Bundle、Working Memory API 和 Codex connector 源码验证。Codex connector 的 `SessionStart` 读取 Context Bundle；`UserPromptSubmit` 只注入“需要时主动搜索”的提示，不重新注入 Working Memory。

## 1. 共享地址

一条经验的完整地址由两部分组成：

| 部分 | 值 | 作用 |
| --- | --- | --- |
| storage boundary | repository Space `owner__name` | 隔离不同客户仓库；该 Space 使用 shared retrieval，只共享读取 `mmw-toolbox` |
| task scope | `mmw-map-<map number>` | 把同一 map 下的全部 spec 放进同一个当前任务经验域 |

没有 map parent 的 standalone spec 使用 `mmw-spec-<spec number>`。

### Space 布局

| Space | 内容 | Retrieval mode | 可以读取 |
| --- | --- | --- | --- |
| repository Space `owner__name` | 该 repository 的 Memory、worker/reviewer Thread 和 Working Memory | `shared` | 自身与 `mmw-toolbox` |
| `mmw-toolbox` | owner 已批准、可以跨 repository 使用的 MMW 工具经验 | `strict` | 仅自身 |
| Default | owner 的普通跨工具会话与个人背景 | 保持现状 | 不进入 pipeline retrieval |

repository Space 的 `sharedSpaceIds` 只包含 `mmw-toolbox`。不同客户 repository 不互相链接；阶段二也不迁移 Default 的历史内容。`mmw-toolbox` 不是所有 Memory 的公共池，只接收 owner 明确批准晋升的通用经验。

不为每个 map 或 standalone spec 建 Space。那会把同一 repository 的跨任务历史切碎，要求在任务结束时搬运 Memory，并产生大量短命 Working Memory。task root 是 repository Space 内的 scope label，不是新的存储边界。

### Identity 布局

| Identity | 使用者 | 默认 Space | 作用 |
| --- | --- | --- | --- |
| `mmw-worker` | ticket worker | 不固定；dispatch 显式传入当前 repository Space | 记录 provenance，接收 worker active Rules |
| `mmw-reviewer` | ticket reviewer | 不固定；dispatch 显式传入当前 repository Space | 记录 provenance，接收 owner 批准的 reviewer active Rules |
| `default` | owner 的普通会话与非 pipeline 工作 | Default | 保持个人上下文，不由 dispatch 改写 |

Identity 不承担授权：Memory 是否可见由 active Space、retrieval mode 和 shared Spaces 决定。Identity 只回答“谁产生了这条记录”和“哪个角色的 active Rules 应进入 Context Bundle”。固定 Identity 不能把 default Space 设成“当前 repository”；本机 `nmem agents enroll` 的 `--default-space` 是一个固定 Space id，所以 pipeline 必须每次显式传 `NMEM_SPACE`。

main agent 不新建 `mmw-main` Identity。`dispatch.sh open <spec>` 是在 owner 已经开始的会话里运行，不能倒回 session start 改写该会话的 Context Bundle 或 Thread 路由。它通过 `open` 的显式结果读取同一 task set；需要搜索或写入时显式传 repository Space 与 task scope。这样 main、worker、reviewer 共用同一 task Memory，而 owner 会话的完整 Thread 不会被自动搬进客户 repository Space。

### 建立和解析

- `install.sh` 幂等建立全局的 `mmw-toolbox`、`mmw-worker` 与 `mmw-reviewer`；`install.sh --check` 只报告缺失或形状不一致。
- `dispatch.sh open <spec>` 幂等建立当前 repository Space；已有正确 Space 时不重建。
- repository Space id 是 tracker repository 的 `lowercase(owner) + "__" + lowercase(name)`；显示名保留 `owner/name`，避免两个同名 repository 冲突。
- dispatch 每次从当前 tracker repository 和 native parent graph 重新解析 Space 与 task root，不把它们缓存进 ticket body。

首次建立使用当前 `nmem 0.10.78` 已存在的接口：

```sh
nmem --json spaces create "MMW Toolbox" \
  --id mmw-toolbox --retrieval-mode strict
nmem --json agents enroll mmw-worker \
  --name "MMW Worker" --role worker
nmem --json agents enroll mmw-reviewer \
  --name "MMW Reviewer" --role reviewer

nmem --json spaces create "$REPOSITORY_SLUG" \
  --id "$NMEM_SPACE" \
  --retrieval-mode shared \
  --share-with mmw-toolbox
```

`agents enroll` 已有 create-only/no-op 语义；`spaces create` 没有同样承诺，所以 adapter 先 `spaces show <id>`，缺失才 create。MMW 命名空间下的 repository Space 已存在但 retrieval shape 不一致时，adapter 用 `spaces update <id> --retrieval-mode shared --share-with mmw-toolbox` 恢复固定形状；不会触碰 Default 或其他 Space。

正常路由只读 tracker graph：

```text
ticket --native parent--> spec --native parent--> map
```

`read_ticket()` 已经从 ticket 的 native parent 得到 spec。`dispatch.sh` 再读取 spec 的 native parent；parent 带 `mmw:map` 时使用 map scope，没有 parent 时使用 standalone spec scope。

真实数据已经验证这条链：GitHub `#384 → #374 → #375` 分别是 map、spec、ticket；`tree.py 384 --root map` 一次读出 `#384 → #374 → 七张 tickets`。Task Board 也用同一条 native parent graph 把“一个 map 及其全部 spec/ticket”定义为 The Night。

不使用以下内容决定共享范围：

- ticket title：只是一个工作切片的名称；
- `## Owns`：只是可写路径和并行冲突边界；
- Parent spec 正文：只描述一个 seam，不能代表同一 map 下其他并行 spec；
- semantic similarity：只能判断内容相似，不能证明两个 agent 属于同一项任务。

## 2. `dispatch.sh` 主动提供当前 task root 经验

### `dispatch.sh open <spec>`

`open` 在现有开夜动作完成后：

1. 读取 spec 的 native parent，得到 `map:<n>` 或 `spec:<n>`；
2. 得到当前 repository Space；
3. 用唯一 scope label 列出当前任务的全部显式经验；
4. 把 task root、scope、查询结果和每条 Memory 的 id、title、content、source 打印给调用它的 main agent。

读取命令的实际形状是：

```sh
nmem --json memories list \
  --space "$NMEM_SPACE" \
  --label "$MMW_EXPERIENCE_SCOPE" \
  --limit 1000
```

这里故意只用一个 scope label。本机实测 `memories list` 的重复 `--label` 是 OR，不是 AND；`--label mmw-experience --label mmw-map-384` 会把别的 map 经验和 map 内非经验一起返回。所有带 task scope label 的 Memory 都必须是共享经验，`mmw-experience` 只用于跨 task semantic search。

### `dispatch.sh start <ticket> worker|reviewer`

`start` 在调用 runner adapter 前做两次不同目的的读取：

1. **current task set**：按唯一 task scope label 精确列出本次 task 已写入的全部经验；
2. **historical seed**：用当前 ticket 的 `## What to build`、`## Seam` 和 `## Acceptance criteria` 做一次 `--label mmw-experience` semantic search，从 repository Space 与 `mmw-toolbox` 取前 10 条，再按 Memory id 去掉 current task set 已有的重复项。

historical seed 使用 ticket 的执行合同，因为它描述这一名 worker 实际要构建和验证的 vertical slice。它不使用 ticket title 或 `## Owns`，也不把 Parent spec 的 Problem Statement、Solution、Implementation Decisions 和 Testing Decisions 拼成一份宽查询。`## Owns` 只规定可写边界，整份 Parent spec 又可能同时覆盖多个不同执行面；两者都不是这名 worker 需要哪条历史经验的可靠信号。

`start` 把两组结果分开追加到首次 prompt：

```text
MMW task root: map #384
MMW task scope: mmw-map-384
Nowledge Space: chancheuklap__multi-model-workflow

Current task shared experience:
- <memory id> — <title>
  <content>
  Source: <source>

Relevant repository/toolbox history for this ticket:
- <memory id> — <title>
  <content>
  Source: <source>

When an unexplained failure is not covered above, search with the exact error,
command and component. A Memory is guidance, not authority; verify it against
the ticket, repository and current command output.
```

每次 start 都重新读取，不保存一份会过期的 experience package。这样，map 内 spec A 的 worker 写完一条经验后，稍后启动的 spec B worker 或 reviewer 会直接收到它；standalone spec 内的后续 agent 使用同一机制。新 task 尚无 scoped Memory 时，historical seed 仍会主动提供与当前 vertical slice 相关的 repository/toolbox 经验。

`start` 同时把下面的值交给 agent 进程：

- `NMEM_SPACE=<repository Space>`
- `NMEM_AGENT_ID=mmw-worker|mmw-reviewer`
- `MMW_EXPERIENCE_SCOPE=mmw-map-<n>|mmw-spec-<n>`
- `MMW_SPEC=<spec number>`
- `MMW_TICKET=<ticket number>`

这些值只负责路由和 provenance。Identity 不决定谁可以读取哪条经验；task scope 才决定当前任务的共享集合。

runner 差异留在现有 adapter：Paseo 使用 `paseo run --env`；Orca 在 `terminal create --command` 的启动命令前设置环境；Herdr 在 pane 启动 host 前设置环境。无论 connector 是否自动注入 Context Bundle，各 host 都从统一的首次 prompt 得到同一份 task root 经验。

## 3. agent 主动获取后来出现的经验

开工时的精确 task root 列表由 dispatch 保证，agent 不需要重复搜索。agent 只在一个明确时刻主动检索：命令或工具出现 ticket、repository 文档和当前 task 经验都没有解释的行为，在尝试 workaround 之前。

查询使用真实问题，而不是 spec 摘要：

```sh
nmem --json memories search \
  "<exact error + command + component>" \
  --space "$NMEM_SPACE" \
  --label "$MMW_EXPERIENCE_SCOPE" \
  --limit 10
```

如果当前 task root 没有答案，再查历史的 repository 和 toolbox 经验：

```sh
nmem --json memories search \
  "<exact error + command + component>" \
  --space "$NMEM_SPACE" \
  --label mmw-experience \
  --limit 10
```

repository Space 的 shared retrieval 会让第二次搜索同时覆盖当前 repository 与 `mmw-toolbox`，但不会读取其他客户 repository 或个人 Default。

这条行为写进 `implement/SKILL.md` 和 reviewer 的 read-in / troubleshooting 规则，而不是依赖某个 connector 恰好注入提示。它解决已经运行的并行 agent：Memory 写入后即可搜索；agent 真正遇到相关问题时，用最具体的信号取回它。没有相关问题时不轮询、不打断工作。

## 4. worker 写入可复用经验

worker 在以下三项都成立时立即写，不等 closeout：

1. 同一 task 的另一张 ticket 或后续 agent 可能再次遇到；
2. 已由实际命令结果或当前权威文件证实；
3. 只读 ticket 和代码不能立即得知。

写入命令是：

```sh
nmem --json memories add --stdin \
  --space "$NMEM_SPACE" \
  --agent-id "$NMEM_AGENT_ID" \
  --unit-type learning \
  --label mmw-experience \
  --label "$MMW_EXPERIENCE_SCOPE" \
  --label "mmw-spec-$MMW_SPEC" \
  --label "mmw-ticket-$MMW_TICKET" \
  --title "<searchable title>"
```

stdin 只写五项：

```text
Applies when: <触发条件>
Finding: <已证实的非显然事实>
Action: <下一名 worker 应如何处理>
Evidence: <实际输出或 repository authority>
Observed in: <repo>#<ticket> @ <commit>
```

默认 unit type 是 `learning`；只有可以按固定步骤重复执行的做法使用 `procedure`。适合写的是工具行为、环境修法、测试的非显然前提和可复用操作顺序。普通实现细节、ticket 状态、未经验证的推测、用户决定、凭据和客户数据不写。spec、ticket 和 commit 只记录 provenance 与夜间列举条件，不决定 task 共享范围。

同一事实发生变化时不覆写历史：新 Memory 已证实旧 Memory 错误时使用 supersede；旧经验只是不再适用时使用 deprecate。普通 repository Memory 的写入与纠正不等待 owner 批准，因为等待会使并行 agent 继续重复遇到同一问题。

## 5. 并行 spec 的实际传播

以 map `#384` 下并行的 spec A、spec B 为例：

```text
spec A worker 启动
  → dispatch 注入 repository Space 中 label=mmw-map-384 的全部经验
  → worker 证实一个非显然工具行为
  → 立即写 Memory(labels: mmw-experience, mmw-map-384)

spec B worker 稍后启动
  → native parent 同样解析为 map #384
  → dispatch 直接注入新 Memory

spec B worker 已经在运行
  → 它遇到同一错误
  → 用错误、命令、组件搜索 mmw-map-384
  → 立即取回 spec A 的 Memory
```

另一个 map 即使在同一 repository 并行，也不会进入第一条精确列表。它只有在以后遇到相同具体问题、主动查历史经验时，才可能按 relevance 取回这条经验。

standalone spec 使用完全相同的传播路径，只是 scope 为 `mmw-spec-<n>`：该 spec 下先启动的 worker 写入后，后启动的 worker/reviewer 直接收到；其他 standalone spec 不进入它的精确列表。

## 6. tracker event 与 Memory 的边界

Memory 只承载“怎么做、踩过什么坑、什么非显然前提已被证实”。它不承载 ticket state、依赖、`## Owns`、acceptance 结果、spec 修订或必须马上执行的指令。

当 worker A 发现的信息必须立即改变 worker B 的行为时：

- contract 不适配：现有 `contract` child；
- pipeline 本身故障：现有 `fault` child；
- 需要 owner 选择：现有 `decision` child。

relay 继续只由 tracker event 唤醒 agent。Memory 不产生 wake，也不参与 gate。

## 7. reviewer 的读取与独立性

共享经验服务同一 task 的所有执行 agent，不只服务 worker。reviewer 因此接收当前 task root 的已验证操作经验，例如 runner 参数、测试前提、环境限制和已证实的工具行为；这能避免 reviewer 因同一基础问题重复失败。

reviewer 的独立性由内容边界保证，而不是通过拒绝所有 worker 经验保证：

- 不注入 worker 的完整 Thread、chain of thought、临时推测、自评或“实现正确”的结论；
- Memory 不能证明 acceptance criteria 已满足，不能替代 reviewer 自己运行检查，也不能免除任何 review axis；
- 一条 Memory 的 `Evidence` 只证明该操作经验本身，reviewer 仍以 ticket、repository authority 和本次实际结果判断产品正确性；
- review 中发现的可复用审查方法可以写 repository Memory；要成为每次 review 都执行的常驻要求，必须由 owner 批准后编译成 `mmw-reviewer` active Rule。

因此，同一 task 的 worker 与 reviewer 共享事实性操作经验，但不共享待审实现的论证和判决。

## 8. Thread、Working Memory 与跨夜路径

阶段二保留 Nowledge Mem 的原生跨夜链路：

```text
worker/reviewer session
  → connector 以 NMEM_SPACE 保存 Thread 到 repository Space
  → Nowledge 后台整理与异步蒸馏
  → repository Working Memory 在后续 session start 提供宽背景
  → 后续 agent 遇到具体问题时检索显式 Memory
```

这条链路负责“下一夜仍能找到”，不负责“同一夜立即广播”。同夜确定性由 worker 直接写显式 Memory、dispatch 在每次 start 精确列举、运行中 agent 按具体问题主动搜索共同保证。

完整 Thread 是事后证据，不直接塞给并行 agent。Working Memory 是整个 repository Space 的简报，可能同时包含多个 map 和 standalone spec；它只提供宽背景，不能作为 task root 检索结果。后台蒸馏即使较慢或没有发生，也不影响显式 Memory 的同夜传播。

后续 task 查历史经验时，先用具体问题在 repository Space 搜 `mmw-experience`。shared retrieval 会同时查 repository 与 `mmw-toolbox`；仍然不会查其他客户 repository 或 Default。阶段二不自建 Thread 摘要器、Working Memory patch、map Working Memory 或实时同步层。

## 9. 每夜 Memory 收口与 retro 的衔接

小写 `night` 是 `dispatch.sh` 对一份 spec 的一次运行，即使该 spec 属于更大的 map。Memory 收口因此按当前 spec 的 provenance label `mmw-spec-<n>` 列出这一夜写过的 Memory，而不是按 task root 一次处理整个 map。这样，并行 spec 可以分别收口；保留的 Memory 仍带 map scope，继续服务尚未完成的 sibling specs。

closing pass 对每条 Memory 只做两类事实处理：

1. **retain**：内容正确且仍适用，保留在 repository Space；
2. **supersede/deprecate**：有新证据替代，或适用条件已经结束。

是否应该变成长期规则不能只看单条 Memory，也不能只看本 spec。promotion proposal 移交给 `summary` 之后的 retro，由 retro 与 ticket event、review 结果、`git log` 和历史 occurrence 一起判断。

`dispatch.sh summary <spec>` 仍负责现有 task-state 闭合：未完成 closing pass 时拒绝，成功后写 `spec.closed` 并停止该 watch。它只增加本 spec Memory 的事实计数：

```text
Shared experience: 3 written, 2 retained, 1 superseded, 0 deprecated
```

同一个 main agent 随后立即执行 retro skill。retro 的失败不会撤销 `spec.closed`，但必须生成明确的 `Retro unavailable: <reason>`，不能无声跳过。正常结果写在同一 spec 的普通 comment 中，第一行固定为 `NIGHT RETRO <date>`；它不是 `<!-- mmw {...} -->` event，不参与 ticket state fold，也不唤醒 relay。

## 10. retro 的范围和证据输入

### 三个不同范围

| 范围 | 固定定义 | 作用 |
| --- | --- | --- |
| 本次证据范围 | 当前完成的 spec night | 决定这次新增哪些 occurrence；避免把 sibling spec 的结果重复记入 |
| 执行共享范围 | task root：`map if present, otherwise spec` | 决定阶段二运行中哪些 agent 立即共用 Memory |
| 历史比较范围 | 当前 repository | 发现跨 ticket、跨 spec、跨 map/standalone task 和跨 night 的重复问题；不读取其他客户 repository |

每份 spec 完成后各自运行一次 retro。map 内先完成的 spec 会立即留下 `NIGHT RETRO`；后完成的 sibling spec 把它作为历史输入。这样多 spec task 不必等到全部结束才学习，也不会为 map 再造第二套结束状态。

### evidence inventory

`retro.py collect <spec>` 必须一次读取下面的完整集合，并把存在、缺失和来源写进 evidence packet：

| 输入 | 当前来源 | retro 用途 |
| --- | --- | --- |
| 交付意图 | spec 的 `Problem Statement`、`User Stories`、`Out of Scope`、`Implementation Decisions`、`Testing Decisions` | 判断整批交付是否与已批准意图一致 |
| 本次 ticket 集合 | `tree.py <spec> --root spec` | 保证没有漏读任何 ticket 或 child |
| task-state 与失败 | 每张 ticket 的完整 event fold | 读取 bounce、return、lost、finding、route、check 和最终结果 |
| review 结果 | 最新 `reviewer.reported` comment 和 finding child body | 读取 axis、finding class、path、claim 与后续处置 |
| 实际落地 | 本批 ticket merge、closing-pass fix 和 base branch 的 `git log`/commit | 证明改了什么、action item 是否落地 |
| 共享经验 | repository Space 中带 `mmw-spec-<n>` 的显式 Memory | 读取本夜已证实的操作经验及其 retain/correct 结果 |
| 历史 occurrence | 当前 repository 所有较早的 `NIGHT RETRO` comment | 判断同一问题是第几次，不依赖日期或 Working Memory |
| 既有 proposal | 较早 retro 链接的 issue 及当前状态 | 先核上一次行动项，避免重复开 issue |
| session 过程 | repository Space 的 Thread，仅在现有证据无法解释过程时按需读取 | 补充“为什么走弯路”；第一版不依赖它完整存在 |

event、commit、review comment、spec section 和 Memory id 是证据；Working Memory、agent 自评、没有输出的推断和 retro 自己的猜测不是证据。Thread 缺失时只缩小 process-lesson 分析范围，不影响 event-backed 分析。任何输入读不全时，packet 必须写 `unreadable` 及原因，不能把“没有读到”表示成“没有发生”。

第一次运行阶段三时，repository 可能没有较早的 `NIGHT RETRO`。此时 `collect` 分页读取当前 repository 中全部带 `mmw:spec` 且已写 `spec.closed` 的旧 spec，从它们的 ticket event、review comment 与可定位 commit 建立一次 bootstrap occurrence baseline，并在首份 `NIGHT RETRO` 中逐条保留旧 spec source。后续 retro 直接读取这份 baseline 与后来报告，不再反复扫描全部旧 ticket。bootstrap 不读取或回填历史 transcript；旧证据不完整就标为 narrowed，不能猜原因。这样阶段三启用前已经发生过的问题仍能参与“第几次”的判断，又不增加数据库或迁移文件。

## 11. retro 的分析合同

### occurrence 的最小结构

retro 先从本次证据生成 occurrence，再与较早 `NIGHT RETRO` 的 occurrence 比较。每条 occurrence 固定包含：

```text
class: 稳定类别
cause: 证据支持的可预防原因
scope: repository | MMW | mmw-toolbox
source: ticket/event/review/commit/Memory 的可跳转引用
outcome: fixed | became-ticket | invalid | fixed-elsewhere | blocked | observed
```

`class` 不是自由发明的标签。review finding 沿用其 reviewer axis 内的稳定类型：`Spec` 使用 `missing`、`scope-creep`、`built-wrong`；`Tests` 使用六种 test smell；`Standards` 使用 documented-standard、Fowler smell、less-code 或 pass-through。运行故障沿用 event 名和已经记录的原因。retro 可以把不同来源归为同一个 cause，但必须逐条解释它们为什么是同一可预防问题；相同 path、相似标题或同一个大类本身不构成重复。

为使 review 结果可聚合，review comment 的 `In-ticket` 和 `Out-of-ticket` 每行增加一个稳定 `class` 字段，并由 `verify-ticket.py --review` 校验；固定行形为 `- <Axis> [<class>] <path>:<line> — <claim>`。为避免误学 false positive，`route ... stale` 变为 `<dispatch> route <ticket> <child> stale invalid|fixed-elsewhere`，reason 必填：

- `invalid`：finding 从一开始就不成立；
- `fixed-elsewhere`：finding 曾成立，但当前 `HEAD` 已由其他 ticket 或 closing-pass fix 修复。

这两个值是 `child.closed` 的补充字段，resolution 仍是 `stale`，所以现有 state fold、summary count 和 relay vocabulary 不变。

### 哪些内容形成 proposal

一个问题只有在以下任一条件成立时才形成 proposal：

1. 两次或以上独立 occurrence 指向同一个可预防 cause；它们可以跨 ticket、跨 spec 或跨 night；
2. 只有一次 occurrence，但它实际阻塞了 ticket 或 night，并有 `ticket.returned`、第二次 `ticket.bounced`、未解决的 `fault/contract` 或同等 event 证据。

同一批日志的重复行不是两次 occurrence；一个 finding 被 review、修复和 route 记录三次仍是一件事。一次非阻塞问题保留为 Memory 或 descriptive finding，不为显得完整而开 proposal。

每个 proposal candidate 必须同时回答：

- **当前情况如何处理**：已修复、已成为 ticket、仍阻塞、被证伪或没有找到处理证据；
- **怎样防止下一次**：改哪一个现有载体、让哪个确定行为改变、怎样观察改动有效。

### 先核上一次行动项

分析新问题之前，retro 先读取当前 repository 最近一份 `NIGHT RETRO` 链接的 proposal：

- issue 已通过正常 ticket 流程落地，并能引用 commit、Rule id、Memory id 或现行文件位置时，写 `已落地`；
- issue 仍在等待 owner、等待实现或只有关闭状态而没有落地证据时，按事实写当前状态；
- 找不到能证明落地的证据时，固定写 `没找到证据`，不把“issue 已关闭”推断为“预防措施已生效”。

若本次 occurrence 与一个仍有效的既有 proposal 同 cause、同目的地，向原 issue 追加新证据并在本次 retro 链接它，不另开重复 issue。

### 交付意图对照

retro 对整个 spec batch 做一次 descriptive reconciliation：

1. 从 `Problem Statement` 与 `User Stories` 列出用户预期能观察到的表面；
2. 从 landed commits、ticket closeout evidence、reverify 和实际运行结果列出已经观察到的表面；
3. 对照 `Out of Scope`，指出缺失、额外实现或证据空白。

这一部分只描述交付与批准意图是否一致，不自动开“补功能”proposal。产品范围仍由 owner 决定；若现有 acceptance 本身有洞，沿正常 finding/ticket 路径处理。

### 从 review 结果学习

- 同一路径、同一 finding class 且 `stale reason=invalid` 出现两次，形成“已知 false positive”review guideline candidate。它只能要求 reviewer 先检查反证或降低严重度，不能禁止报告该类问题。
- 同一真实缺陷以 `fixed`、`became-ticket` 或 `fixed-elsewhere` 在两次独立 occurrence 中成立，形成 repository anti-pattern、review guideline 或 automated check candidate。能机械判断时优先 automated check。
- `fixed-elsewhere` 证明 finding 曾经有效，不计入 false positive。
- reviewer 的 Memory 仍不能代替 acceptance evidence；retro 只改变下一次 reviewer 查什么、怎样验证，不把过去判决带入当前判决。

## 12. `NIGHT RETRO`、proposal 与 owner 决定

### spec comment

retro skill 把分析写成结构固定但人可读的 `NIGHT RETRO` comment：

```text
NIGHT RETRO 2026-09-14
Evidence: complete | narrowed: <missing source>
Previous actions: <issue> — 已落地 | 等待决定 | 没找到证据
Occurrences: <class/cause/source/outcome> ...
Repeated or blocking problems: <group and count> ...
Intent reconciliation: expected / observed / gap
Review learning: <candidate or none>
Proposals: <issue links or none>
Shared experience: <retained/superseded/deprecated Memory ids>
```

comment 只记录本次 spec 新增的 occurrence，同时引用用于比较的历史 occurrence。脚本在发布前验证：每条 finding 有 source；每个“重复”组至少两条独立 source；每个 proposal 同时有当前处理和预防措施；缺失输入被标明。未通过验证时不发布半份报告，而是把具体问题交给 main agent 修正后重试。

### proposal issue

需要 owner 决定的 candidate 使用现有 GitHub issue：

- 创建在实际应该承担改动的 repository；MMW 行为问题开在 multi-model-workflow，消费 repository 的本地问题开在该 repository；
- 加入已有 `ready-for-human` queue label，不加 `mmw:map/spec/ticket/child` layer label，因为批准前它还不是执行单元；
- body 固定包含 problem、独立 occurrence sources、current handling、proposed prevention、target surface、owner decision requested 和验证效果的方法；
- spec 的 `NIGHT RETRO` 链接 proposal，proposal 反向链接来源 spec；
- 未批准时不修改任何长期载体，不阻止 night 正常结束。

owner 的三个结果继续使用现有 tracker 操作，不增加 approval state machine：

| owner 结果 | 处理 |
| --- | --- |
| 批准 | 以 proposal 为 source 走正常 `to-spec`/`to-tickets` 流程，回写新 spec/ticket 链接后关闭 proposal；若只是一条 Memory copy 或 Rule 激活，也在 issue comment 留下实际 id 和证据后关闭 |
| 拒绝 | 说明原因，移除 `ready-for-human`，标 `wontfix` 并关闭；以后相同 occurrence 可以引用该决定，但不得自动重开同一 proposal |
| 暂不决定 | 保持 `ready-for-human`；下次 retro 只报告其状态，不另开副本 |

### 长期载体选择

| 问题性质 | owner 批准后的目的地 | 下一次如何生效 |
| --- | --- | --- |
| 可机械判断的 invariant | target、judge、lint、ticket `CHECK:` 或 script | 在运行或验收时直接阻止同类错误 |
| repository 通用、从代码无法推得的 authority/navigation | repository `AGENTS.md` 的现有适当 section | 后续 agent 启动时读取；不把 `AGENTS.md` 变成百科全书 |
| repository 的 domain term 或稳定设计决定 | 现有 `CONTEXT.md` 或 ADR | agent 按 repository navigation 读取，reviewer 可引用 authority |
| repository 特有的 review 规则 | 现有 coding standard/review guide；没有时由批准的 ticket 建立 | Standards reviewer 按 repository 规则读取 |
| 跨 repository 的 reviewer 方法 | `mmw-reviewer` active Rule | reviewer Context Bundle 常驻取得 |
| MMW pipeline 行为 | 对应 MMW skill、reference 或 script | 新版本安装后由以后运行使用；当前 frozen watch 永不切换 |
| 跨 repository 有用但不应强制的知识 | `mmw-toolbox` Memory copy | 使用 shared retrieval 的 repository 按需取得 |
| 尚不值得升级的经验 | 原 repository Memory | 继续按 task/history 搜索，不假装成 authority |

批准 `mmw-toolbox` 晋升时，在 `mmw-toolbox` 新建 copy，并保留原 Memory id/source；不把客户 repository 原件 move 出去。批准 Rule 时记录稳定 rule id、scope 和 status。批准 repository 文件或 MMW 改动时走正常 ticket、review、checks 和 commit，不由 retro 直接编辑。

### 回流到下一次阶段二

闭环完成不是 proposal 被创建，而是批准的预防措施在以后任务中实际生效：

```text
阶段二：agent 写/读 task Memory
  → spec summary 闭合 task state
  → 阶段三：retro 对照 repository 历史
  → owner 决定 proposal
  → 正常 ticket 落入长期载体
  → 下一次阶段二由 prompt、search、Rule、authority 或 check 使用
  → 后续 retro 验证是否仍重复
```

## 13. 必须补齐的现有结构契约

`to-spec/SKILL.md` 已规定一个 map 可以拆成多份 specs，并在 map 的 `## Specs` 写入顺序与链接；Task Board 和 `tree.py` 已假设这些 specs 是 map 的 native children。但 `to-spec/SKILL.md` 的发布步骤目前没有明确要求从 map 产生的 spec 使用 `--parent <map>`。

阶段二与阶段三必须同时补齐：

- 从 map 发布 spec 时，创建为该 map 的 native child；
- read-back 验证 spec 的 `parent.number` 等于 map number；
- 没有 map 的 spec 继续保持 standalone；
- reviewer finding 汇总行带稳定 class；
- `child.closed resolution=stale` 同时带 `reason=invalid|fixed-elsewhere`；
- `NIGHT RETRO` 是普通 spec comment，不加入 `events.py` 的 event vocabulary；
- proposal 复用 `ready-for-human`，不增加第四套 label 或私有审批表。

否则 map scope 无法机械取得、多 spec 共享无法成立，或 retro 会把不同 review 结果错误聚合。`## Sources`、map 的 `## Specs`、ticket title 和 `## Owns` 都是人可读记录或执行切片，不能替代 native parent 与 structured outcome。

## 14. 不可用时的行为

- native parent 查询成功且 `parent=null` 时才使用 standalone spec scope。查询失败时不伪装成 standalone spec，也不扩大到 repository scope：本次 session 不注入或写入 task-scoped Memory，只保留 ticket historical seed，并明确显示 `Task routing unavailable: <reason>`。
- Nowledge Mem 读不到时，session 继续启动，但首次 prompt 明确显示 `Shared experience unavailable: <reason>`。
- 查询成功但没有条目时，显示 `Shared experience: queried, 0 matches`；不能与“没有查询成功”写成同一个结果。
- Memory 写入失败不改变 ticket 的验收与落地；worker 报告 `Shared experience not saved: <reason>` 后继续。
- retro 的 event、review 或 git 输入读不全时，只报告已经实际读取的部分，并在 `Evidence:` 写明 narrowed scope；不能把 unreadable 计成 0 次。
- retro 无法完成时，main agent 尝试在 spec 留 `Retro unavailable: <reason>` 普通 comment；若 tracker 本身不可写，命令在 stderr 和 main agent 的用户报告中保留同一具体原因。night 已经关闭，不回滚 `spec.closed`，也不创建空 proposal。
- proposal issue 创建部分成功时，重跑 publish 先按 spec 反向链接和 occurrence sources 查重，补齐遗漏，不重复创建。

这些是可观察的 fail-open。它们不改变 ticket verdict，不增加 relay、数据库、定时轮询或新的人工队列。

## 15. 实施范围与顺序

阶段二与阶段三作为一个 spec 实施，分为同一依赖链上的四组改动。

### A. Space、Identity 与单一 adapter

1. `mmw-v2/install.sh`
   - 先 show、缺失时用 `nmem spaces create` 建立 `mmw-toolbox`；用 create-only 的 `agents enroll` 幂等建立 `mmw-worker` 和 `mmw-reviewer`；
   - `--check` 只读核对三者是否存在，不替 owner 改写已有 profile 或 Rule。
2. `mmw-v2/skills/dispatch/scripts/experience.py`
   - 作为唯一 Nowledge adapter，解析和校验 `nmem --json`；
   - 建立 repository Space，固定 `shared` 且只 `--share-with mmw-toolbox`；
   - 按 scope label 列举、按具体问题搜索、渲染首次 prompt、按 spec provenance 汇总 Memory；
   - 统一区分 unavailable、0 matches 和正常结果。

### B. 阶段二运行中读写

3. `mmw-v2/skills/dispatch/scripts/dispatch.sh` 与 `runners/{paseo,orca,herdr}.sh`
   - 从 native parent 解析 map/standalone scope；
   - `open` 向 main agent 列出当前 task Memory；`start` 向 worker/reviewer 注入当前 task Memory 与 ticket historical seed；
   - 向 agent 进程传递 Space、Identity、scope、spec 和 ticket；
   - `summary` 只加入本 spec Memory 的 written/retained/superseded/deprecated 事实计数。
4. `mmw-v2/upstream/skills/engineering/implement/SKILL.md` 与 `code-review`
   - agent 遇到具体非显然故障时主动搜索；证实可复用经验时立即写 Memory；
   - reviewer 可使用事实性操作经验，但仍重新运行 acceptance/review checks，不接收 worker Thread、推理或 correctness 结论。
5. `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`
   - 从 map 发布的 spec 以 map 为 native parent 并 read back；standalone spec 保持无 parent。

### C. 阶段三可聚合证据与 retro

6. `code-review/references/session.md`、三个 axis reference 与 `verify-ticket.py`
   - 为每条 review finding 写入并校验稳定 class，同时保留现有 axis、path、line 和 claim。
7. `events.py`、`dispatch.sh route`、`night.md` 与对应 contexts
   - `stale` 增加 `invalid|fixed-elsewhere` reason，不改变 resolution 和 summary slot；
   - night runbook 在成功 `summary` 后要求同一 main agent 执行 retro skill。
8. `mmw-v2/skills/retro/SKILL.md` 与 `scripts/retro.py`
   - `collect` 完整读取 spec tree、event folds、review、git、Memory、历史 `NIGHT RETRO` 和 proposal 状态，输出 evidence packet；
   - skill 只从 packet 形成 sourced occurrences、groups、intent reconciliation 和 proposal；
   - `publish` 校验证据合同，写普通 spec comment，在正确 repository 建立或更新 `ready-for-human` proposal issue；
   - 不读其他客户 Space，不写 event，不直接修改长期载体。

### D. 闭环回流与证明

9. owner 批准后的修改继续使用现有 `to-spec`、`to-tickets`、worker、review、closeout 和 landing 流程；`mmw-toolbox` copy 与 active Rule 也必须把结果 id 回写 proposal。
10. 更新 `CONTEXT-MAP.md` 后对应的 Tickets/Night/Memory context、dispatch 与 upstream merge-note；若消费 repository 的 `CHECK:`、screen contract 或 `.mmw/target.json` 失效，写 downstream-note。
11. 增加 install、dispatch、runner、implement、code-review、to-spec、retro 和跨 night 端到端测试。

实现顺序是 A → B → C → D。所有测试使用隔离的 `MMW_HOME`、假 tracker、临时 Git repository 和临时 Nowledge 对象。按照根 `AGENTS.md` 的 `Self-hosting boundary`，本次实现不能让正在运行的 frozen MMW runtime 消费任何新 skill、script、event field 或 runbook。

不新增数据库、map Space、Working Memory patch、实时消息、Memory lifecycle、retro event、approval state machine 或定时轮询。

## 16. 验收

阶段二与阶段三共同完成必须实际看到：

1. **task root**：一个 map 下两份 spec 的 tickets 都解析成同一 `MMW_EXPERIENCE_SCOPE`；没有 map parent 的 standalone spec 解析成自己的 scope，另一个 standalone spec 不共享该精确列表。
2. **Space isolation**：repository A 能搜自身与已批准的 `mmw-toolbox`；repository B、其他客户 repository 和 Default 内容都不出现。
3. **Identity routing**：worker/reviewer 的 Memory 与 connector Thread 都进入当前 repository Space，provenance 分别是 `mmw-worker`/`mmw-reviewer`，没有落入 Default。
4. **later start**：map 内 spec A worker 写入 sentinel Memory 后，稍后启动的 spec B worker 和 reviewer 首次 prompt 都包含它；另一个 map 的 agent 不包含它。standalone spec 内重复同一对照。
5. **already running**：已经运行的 agent 用实际错误、命令和组件搜索当前 task root 后，能取回刚写入的 Memory；没有相关故障时不会轮询。
6. **historical retrieval**：当前 task 没有答案时，按 `mmw-experience` 搜到 repository/toolbox 的相关历史经验，同时仍不越过 Space isolation。
7. **review independence**：reviewer 能使用 sentinel 操作经验解决环境问题，但首次 prompt 和检索结果不包含 worker Thread、推理、自评或 correctness 结论；reviewer 仍独立运行 acceptance/review checks。
8. **label semantics**：`memories list --label <task scope>` 只返回该 task 经验；重复 `--label` 继续按已实测的 OR 语义；按 `mmw-spec-<n>` 能单独列出当前 night 写入的 Memory。
9. **host parity**：Paseo、Orca、Herdr 启动的 agent 都读到正确的 Space、Identity、scope、spec 和 ticket；Claude、Codex、Cursor、Grok、Pi 都从统一首次 prompt 看到相同当前 task 经验。
10. **native parent**：从一个 map 发布两份 spec 后，两份 spec 的 `parent.number` 都是该 map；直接发布的 standalone spec 没有虚构 map parent。
11. **cross-night background**：支持 Thread capture 的 connector 把会话保存到 repository Space；下一次 Context Bundle 只含 repository Working Memory，不含 shared toolbox Working Memory；task Memory 送达不依赖 Working Memory 刷新。
12. **Memory closeout**：一份 spec night 的 summary 只列本 spec 的 written/retained/superseded/deprecated；同 map sibling 的 Memory 不被误算，也没有从 map scope 消失。
13. **complete evidence**：retro collector 读取本 spec 的全部 tickets、children、event folds、最新 review、相关 commits、spec sections 和 `mmw-spec-<n>` Memory；故意删掉一类输入后，报告为 narrowed/unreadable 而不是 0；repository 没有旧 `NIGHT RETRO` 时，从全部旧 `spec.closed` spec 建立一次 bootstrap baseline，下一次不再全量回扫。
14. **cross-spec repeat**：map 内 spec A 与 spec B 各留下一个同 cause occurrence；spec B retro 识别第二次并创建一个 proposal，引用两份 spec，不需要 map 结束 gate。
15. **cross-night repeat**：两个 standalone spec night 出现同 cause；第二夜在 repository 历史中识别重复，但另一个客户 repository 的 occurrence 不可见。
16. **one blocker**：只有一次但有实际阻塞 event 的问题可形成 proposal；一次非阻塞 observation 不开 proposal。
17. **dedupe**：已有同 cause、同目的地的开放 proposal 时，新的 occurrence 追加到原 issue；重跑 publish 不创建第二张 issue。
18. **previous action**：一个 proposal 仅关闭但无 commit/Rule/Memory 证据时显示“没找到证据”；真正落地时引用具体证据并显示“已落地”。
19. **intent reconciliation**：整批实现与 `Problem Statement`、`User Stories`、`Out of Scope` 的 expected/observed/gap 同时出现在 retro；缺少实际运行证据时明确说未验证。
20. **review learning**：两个 `stale reason=invalid` 的同类 finding 形成降噪 candidate；`fixed-elsewhere` 不计作 false positive；两个真实缺陷优先形成 automated check 或 repository guideline candidate。
21. **approval boundary**：proposal 使用 `ready-for-human` 且没有 MMW layer；未获 owner 批准不会改变 Rule、`AGENTS.md`、gate、script、skill 或 `mmw-toolbox`。
22. **correct destination**：MMW 通用问题的 proposal 在 multi-model-workflow；消费 repository 本地问题留在该 repository；批准后通过正常 ticket 流程落地。
23. **failure semantics**：Nowledge Mem 不可用、0 条、正常返回三种结果可区分；native parent 查询失败显示 degraded routing；retro 发布失败留下具体 `Retro unavailable`，以上均不改 ticket verdict。
24. **self-hosting**：隔离测试证明新闭环，但当前 frozen installed runtime 在 watch 结束、owner 接受和 `finish` 完成以前没有读取新版本。

## 17. 效果指标

阶段二衡量“经验有没有在需要时被采用”，阶段三衡量“重复问题有没有被变成有效预防”。两者都不以 Memory 或 proposal 数量越多越好。

| 指标 | 记录位置 | 期望方向 |
| --- | --- | --- |
| 每次 `open/start` 实际注入的 task Memory 数 | dispatch 输出与 `NIGHT SUMMARY` | 可核对，不设数量目标 |
| agent 主动搜索后引用并采用的 Memory id 数 | ticket closeout 与 `NIGHT RETRO` | 上升后稳定 |
| 同一已知问题在一个 task 被第二名 agent 独立修复的次数 | ticket closeout 与 occurrence | 下降至 0 |
| retro evidence 完整率 | `NIGHT RETRO Evidence` | 接近 100%；unreadable 单独计数 |
| repeat/blocker candidate 被 owner 批准的比例 | proposal issue | 用来判断 proposal 准确度，不作为产量目标 |
| 批准 proposal 的实际落地率 | 下一次 `Previous actions` | 上升；没有证据不计落地 |
| 预防措施落地后同 cause 再次发生的次数 | 后续 occurrence | 下降至 0；再次发生说明措施无效或覆盖不全 |
| invalid false positive 在 guideline 生效后的重复次数 | review occurrence | 下降，同时不得压低真实缺陷报告 |

不使用 ticket pass rate 证明闭环有效，因为 pass rate 同时受任务难度、实现质量和 acceptance criteria 影响，不能归因于 Memory 或 retro。

## 18. 明确不采纳

- 把阶段二做完后再单独等待阶段三；
- 每个 map/spec 建一个 Space；
- 用 ticket title、`## Owns`、整份 spec 摘要或 semantic similarity 推断 task 归属；
- 用 path 或标题相同直接认定是同一原因；
- 用 `--time today` 表示 night 或历史比较范围；
- 只读 Memory 做 retro，忽略 event、review、spec intent 和 `git log`；
- 第一版必须保存并分析全部 transcript；
- 把 Working Memory 改造成 task scratchpad、map bus、retro index 或实时广播；
- 在派发关键路径使用耗时明显更高的 `nmem ask`；
- 新建 Memory/retro tracker event、relay、数据库、状态机、迁移流程、轮询或审批队列；
- 自动把 Memory 或 retro proposal 晋升为 Rule、`AGENTS.md`、gate、script、skill 或 `mmw-toolbox`；
- 把一次普通问题包装成 proposal，或把同一事件的多条记录当作多次 occurrence；
- 用已知 false positive guideline 静默禁止 reviewer 报告；
- 把 worker Thread、推理、自评或 correctness 结论交给 reviewer；
- 让新版本 MMW 接管正在运行的 frozen watch。

## 是否需要讨论

没有需要 grill 的产品问题。owner 已明确阶段二与阶段三共同实施；task root、repository 历史范围、现有 `ready-for-human` 决策面、owner 批准边界和 frozen runtime 都有现成 authority。剩余内容是工程合同与验收设计。

## 可复查来源

- [《Project Context 调研与 MMW 方案》](https://claude.ai/code/artifact/b9520c08-eb0d-40f1-872e-228662445954?via=auto_preview)的第 5 节“实验结果”、第 6 节“阶段二”、第 7 节“阶段三”和第 9 节“决定”
- [BMAD-METHOD `bmad-retrospective`](https://github.com/bmad-code-org/BMAD-METHOD/tree/main/skills/bmad-retrospective) 的 `workflow.md`、`references/evidence-gathering.md`、`references/retro-document.md` 与 `scripts/git_evidence.py`
- [Devin Session Insights](https://docs.devin.ai/product-guides/session-insights)
- [Augment Review Guidelines](https://docs.augmentcode.com/codereview/review-guidelines)
- [OpenAI Harness engineering](https://openai.com/index/harness-engineering/)
- [OpenAI Introducing Codex](https://openai.com/index/introducing-codex/)
- [Nowledge Mem Background Intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)
- [Nowledge Mem Spaces](https://mem.nowledge.co/docs/spaces)
- [Nowledge Mem Context](https://mem.nowledge.co/docs/ai-context)
- [Nowledge Mem CLI](https://mem.nowledge.co/docs/cli)
- `docs/agents/issue-tracker.md` 的 `Reading a tree`、`Three label sets`、`Morning queries` 与 `Wayfinding operations`
- `docs/contexts/task-board/CONTEXT.md` 的 `The Night`
- `docs/contexts/tickets/CONTEXT.md` 的 `spec`、`ticket`、`sub-issue` 与 `map`
- `docs/contexts/night/CONTEXT.md` 的 `main agent`、`closing pass`、`route`、`summary` 与 `spec.closed`
- `mmw-v2/skills/dispatch/references/night.md` 的 `## 4. The closing pass` 与 `## 5. The night is over`
- `mmw-v2/skills/dispatch/scripts/dispatch.sh` 的 `summary_spec()` 与 `route_finding()`
- `mmw-v2/skills/dispatch/scripts/status.py` 的 `summary()`、`ROUTES` 与 `routed_counts()`
- `mmw-v2/skills/verify-ticket/scripts/events.py` 的 `EVENTS`、`CHILD_RESOLUTIONS` 与 `fold()`
- `mmw-v2/upstream/skills/engineering/code-review/references/session.md` 的 `## 4. Sort every review finding into in-ticket or out-of-ticket` 与 `## 5. Write one review comment on the ticket`
- `mmw-v2/upstream/skills/in-progress/retro/SKILL.md` 的 `## Steps` 与 `### Implementation vs Review`
- `mmw-v2/skills/verify-ticket/scripts/tree.py` 的 module docstring 和 `LAYERS`
- `mmw-v2/board/board_data.py` 的 `BoardStore._read_trees()` 与 `BoardStore._spec_trees()`
- `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md` 的 `Work through the map`
- `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md` 的 `Process`
- `mmw-v2/upstream/skills/engineering/implement/SKILL.md` 的 read-in 与 `While writing code`
- `mmw-v2/install.sh` 的八项 installed items 与 `--check`
- 本机 Nowledge Mem Codex connector `hooks/nmem-context.py` 的 `_load_startup_context()` 与 `main()`
