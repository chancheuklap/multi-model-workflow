# 阶段二共享经验层

日期：2026-09-14

对象：[《Project Context 调研与 MMW 方案》](https://claude.ai/code/artifact/b9520c08-eb0d-40f1-872e-228662445954?via=auto_preview)第 6 节“阶段二 · 共享经验层 · NOWLEDGE MEM 自带机制优先”和第 9 节“决定”

性质：阶段二实施前的研究结论，不修改产品代码

## 结论

阶段二先解析 task root：spec 有 native map parent 时，map 是 task root；spec 没有 map parent 时，该 standalone spec 自己就是 task root。一个 map 可以拆成多份 spec 并行执行，这些 spec 下的 worker 和 reviewer 使用同一个 task scope；standalone spec 下的全部 ticket 使用该 spec 的 task scope。

阶段二使用三个互补读取通道：

1. `dispatch.sh open <spec>` 和 `dispatch.sh start <ticket> worker|reviewer` 根据 GitHub native parent 得到 task root，精确列出这个 task root 已有的 Memory，直接交给 main agent、worker 或 reviewer。
2. `dispatch.sh start <ticket> worker|reviewer` 另用当前 ticket 的执行合同主动检索 repository 与 `mmw-toolbox` 历史经验，解决新 task 还没有 scoped Memory 的冷启动。
3. agent 遇到具体的非显然故障时，以当时的错误、命令和组件主动做 semantic search。先搜当前 task root，仍没有答案时再搜当前 repository Space 和已批准的 `mmw-toolbox`。

worker 一旦证实一条同一 task 其他 ticket 可复用的经验，就立即写入 repository Space，并带当前 task root 的 scope label。后来启动的 worker 或 reviewer 会自动得到它；已经运行的 agent 在遇到相同问题时通过主动检索得到它。

不增加实时消息系统或 Memory relay。必须立即改变其他 ticket 行为的信息不是经验，继续使用现有 `contract`、`fault` 或 `decision` tracker event。

## 文档覆盖范围

本文件覆盖阶段二的完整设计，而不只覆盖当前任务的检索：

1. repository Space 与 `mmw-toolbox` 的布局；
2. worker、reviewer 的 Identity，以及 main agent 的读取边界；
3. task root 的解析：有 map 时使用 map，没有 map 时使用 spec；
4. worker 何时写 Memory、写什么和如何证明；
5. dispatch 如何主动把当前 task root 的经验交给 agent；
6. 已经运行的 agent 如何主动取得后来出现的经验；
7. Thread capture、Working Memory 和跨夜 retrieval；
8. reviewer 的独立性与 reviewer Rule；
9. 每夜收口、supersede/deprecate 和 owner 批准的晋升；
10. 不可用时的行为、实施范围、验收与效果指标。

## 已定决定与本次更新

### 保留的阶段二决定

- 经验不是 ticket state，不写成 tracker event；agent 直接写 Nowledge Mem。
- 能用 Nowledge Mem 的 Space、Identity、Memory、Thread、Working Memory、Rule、supersede 和 deprecate 完成的部分，不另造存储或生命周期。
- 每个客户 repository 有自己的 Space；不同客户 repository 互不可见。只有 `mmw-toolbox` 可以作为所有 repository 明确批准的共享来源。
- pipeline worker/reviewer 的 Memory 与自动采集 Thread 进入 repository Space，不进入个人 Default；owner 自己的普通会话保持现状。
- 普通经验无需 owner 逐条批准。把经验变成跨 repository 内容或常驻行为，只能形成提案，由 owner 批准后执行。
- 当前流水线没有独立 verifier；阶段二只设计 main agent、worker 和 reviewer。

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

## 9. 每夜收口与经验晋升

小写 `night` 是 `dispatch.sh` 对一份 spec 的一次运行，即使该 spec 属于更大的 map。收口因此按当前 spec 的 provenance label `mmw-spec-<n>` 列出这一夜写过的 Memory，而不是按 task root 一次处理整个 map。这样，并行 spec 可以分别收口；保留的 Memory 仍带 map scope，继续服务尚未完成的 sibling specs。

closing pass 对每条 Memory 只做三类处理：

1. **retain**：内容正确且仍适用，保留在 repository Space；
2. **supersede/deprecate**：有新证据替代，或适用条件已经结束；
3. **promotion proposal**：同一经验在多张 ticket 重复出现，或一次就阻塞了工作，建议转成更可靠的长期载体。

晋升目的地由经验性质决定：

| 经验性质 | 晋升目的地 | 原因 |
| --- | --- | --- |
| reviewer 每次都应执行的审查方法 | `mmw-reviewer` active Rule | 进入 reviewer Context Bundle，稳定约束该角色 |
| 当前 repository 所有 agent 必须遵守的约束 | repository `AGENTS.md` | 由 repository authority 明文规定 |
| 可以机械验证或执行的条件 | target、judge、ticket `CHECK:` 或 script | 把建议变成可运行的保证 |
| MMW pipeline 本身的通用操作 | 对应 MMW skill、reference 或 script | 在行为发生的位置修正工具 |
| 跨 repository 有用但不应强制的知识 | `mmw-toolbox` Memory | 保留按需检索，不升级为规则 |

closing pass 只形成带 Memory id、证据和建议目的地的提案。跨 repository 内容、active Rule 和永久行为都由 owner 批准后再执行；普通 repository Memory 的 retain、supersede 和 deprecate 仍是工程收口，不逐条请求批准。

owner 批准 reviewer Rule 后，使用稳定 rule id 和 Nowledge 原生接口写入 `--scope agent --agent mmw-reviewer --status active`；批准 `mmw-toolbox` 晋升后，在 `mmw-toolbox` 新建一条保留原 Memory id/source 的 Memory，而不是把 repository 原件 move 出去。前者让后续 reviewer 的 Context Bundle 自动取得规则，后者让所有明确共享该 toolbox 的 repository 可以按需检索，同时保留客户 repository 内的原始证据。

`dispatch.sh summary <spec>` 在既有夜间摘要中增加一行可核对结果：

```text
Shared experience: 3 written, 2 retained, 1 superseded, 1 promotion proposed
```

这不是新的 gate、ticket state 或审批队列。提案随夜间报告交给 owner；未批准时，原 Memory 留在 repository Space，流水线照常结束。

## 10. 必须补齐的现有结构契约

`to-spec/SKILL.md` 已规定一个 map 可以拆成多份 specs，并在 map 的 `## Specs` 写入顺序与链接；Task Board 和 `tree.py` 已假设这些 specs 是 map 的 native children。但 `to-spec/SKILL.md` 的发布步骤目前没有明确要求从 map 产生的 spec 使用 `--parent <map>`。

阶段二必须同时补齐这一点：

- 从 map 发布 spec 时，创建为该 map 的 native child；
- read-back 验证 spec 的 `parent.number` 等于 map number；
- 没有 map 的 spec 继续保持 standalone。

否则 map scope 无法机械取得，多 spec 共享也无法成立。`## Sources` 和 map 的 `## Specs` 是人可读记录，不能替代 native parent。

## 11. 不可用时的行为

- native parent 查询成功且 `parent=null` 时才使用 standalone spec scope。查询失败时不伪装成 standalone spec，也不扩大到 repository scope：本次 session 不注入或写入 task-scoped Memory，只保留 ticket historical seed，并明确显示 `Task routing unavailable: <reason>`。
- Nowledge Mem 读不到时，session 继续启动，但首次 prompt 明确显示 `Shared experience unavailable: <reason>`。
- 查询成功但没有条目时，显示 `Shared experience: queried, 0 matches`；不能与“没有查询成功”写成同一个结果。
- Memory 写入失败不改变 ticket 的验收与落地；worker 报告 `Shared experience not saved: <reason>` 后继续。

这些是可观察的 fail-open，不增加 ticket event、gate、重试状态机或新的人工队列。

## 12. 实施范围

阶段二只需要改以下现有路径：

1. `mmw-v2/install.sh`
   - 先 show、缺失时用 `nmem spaces create` 建立 `mmw-toolbox`；用 create-only 的 `agents enroll` 幂等建立 `mmw-worker` 和 `mmw-reviewer`；
   - `--check` 只读核对三者是否存在，不替 owner 改写已有 profile 或 Rule。
2. `mmw-v2/skills/dispatch/scripts/experience.py`（新增的单一 Nowledge adapter）
   - 解析和校验 `nmem --json` 输出；
   - 建立 repository Space，固定 `shared` 且只 `--share-with mmw-toolbox`；
   - 按一个 scope label 精确列举、渲染首次 prompt、按 spec provenance 汇总 closeout；
   - 统一区分 unavailable、0 matches 和正常结果，避免三份 runner adapter 分别实现 JSON 与错误语义。
3. `mmw-v2/skills/dispatch/scripts/dispatch.sh`
   - 从 native parent 解析 map/standalone scope；
   - `open` 向 main agent 打印当前 scope 经验；
   - `start` 向 worker/reviewer 首次 prompt 注入同一份 live 经验；
   - 把 Space、Identity、scope、spec number 和 ticket number 交给 agent 进程；
   - closing pass/`summary` 按 `mmw-spec-<n>` 列出当夜 Memory，报告 retain、supersede/deprecate 与 promotion proposal。
4. `mmw-v2/skills/dispatch/scripts/runners/{paseo,orca,herdr}.sh`
   - 传递上述环境变量，不改变 runner boundary 的其他行为。
5. `mmw-v2/upstream/skills/engineering/implement/SKILL.md`
   - 加入一个按具体故障主动搜索的时机；
   - 加入一条经验证、可复用经验的即时写入规则；
   - closeout 记录本票写入、supersede/deprecate 和建议晋升的 Memory id。
6. `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`
   - reviewer 按 task root 接收事实性操作经验并可按具体问题主动搜索；
   - 明确禁止把 Memory 当作 acceptance evidence 或 worker correctness 结论。
7. `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`
   - 从 map 发布的 spec 必须以 map 为 native parent，并 read back 验证。
8. `mmw-v2/skills/dispatch/references/night.md` 与对应 contexts
   - 在现有 closing pass 和 `summary` 中加入共享经验收口，不创造另一套夜间流程；
   - 若 fixed vocabulary 改变，同步 Tickets / Night context。
9. 对应的 install、dispatch、runner、implement、code-review、to-spec 测试和 upstream merge-note。

实现顺序只有一条依赖链：先建立 Space/Identity 与 `experience.py`，再接 `open/start` 和 runner 环境，随后接 worker/reviewer 规则与 nightly closeout，最后补 native map parent 合同与端到端验收。所有测试使用隔离的 `MMW_HOME`、假 tracker 和临时 Nowledge 对象；按照 `AGENTS.md` 的 `Self-hosting boundary`，本次实现不能接管正在运行的 frozen MMW runtime。

不新增数据库、map Space、Working Memory patch、实时消息、Memory lifecycle、经验审批队列或定时轮询。

## 13. 验收

阶段二完成必须实际看到：

1. **task root**：一个 map 下两份 spec 的 tickets 都解析成同一 `MMW_EXPERIENCE_SCOPE`；没有 map parent 的 standalone spec 解析成自己的 scope，另一个 standalone spec 不共享该精确列表。
2. **Space isolation**：repository A 能搜自身与已批准的 `mmw-toolbox`；repository B、其他客户 repository 和 Default 内容都不出现。
3. **Identity routing**：worker/reviewer 的 Memory 与 connector Thread 都进入当前 repository Space，provenance 分别是 `mmw-worker`/`mmw-reviewer`，没有落入 Default。
4. **later start**：map 内 spec A worker 写入 sentinel Memory 后，稍后启动的 spec B worker 和 reviewer 的首次 prompt 都包含它；另一个 map 的 agent 不包含它。standalone spec 内重复同一对照。
5. **already running**：已经运行的 agent 用实际错误、命令和组件搜索当前 task root 后，能取回刚写入的 Memory；没有相关故障时不会轮询。
6. **historical retrieval**：当前 task 没有答案时，按 `mmw-experience` 搜到 repository/toolbox 的相关历史经验，同时仍不越过 Space isolation。
7. **review independence**：reviewer 能使用 sentinel 操作经验解决环境问题，但首次 prompt 和检索结果不包含 worker Thread、推理、自评或 correctness 结论；reviewer仍独立运行 acceptance/review checks。
8. **label semantics**：`memories list --label <task scope>` 只返回该 task 经验；测试固定重复 `--label` 是 OR 的实测事实，避免实现误写成 AND。按 `mmw-spec-<n>` 能单独列出当前 night 写入的 Memory。
9. **host parity**：Paseo、Orca、Herdr 启动的 agent 都读到正确的 Space、Identity、scope、spec 和 ticket；Claude、Codex、Cursor、Grok、Pi 都从统一首次 prompt 看到相同当前 task 经验。
10. **native parent**：从一个 map 发布两份 spec 后，两份 spec 的 `parent.number` 都是该 map，`tree.py <map> --root map` 能一次读全；直接发布的 standalone spec 没有虚构 map parent。
11. **cross-night**：支持 Thread capture 的 connector 把会话保存到 repository Space；下一次 session 的 Context Bundle 只含 repository Working Memory，不含 shared toolbox Working Memory，task 经验的送达不依赖 Working Memory 刷新。
12. **closeout**：一份 spec night 的摘要能列出本 spec 的 retained、superseded/deprecated 和 promotion proposals；同 map 的 sibling spec Memory 不被误算进本次 closeout，也没有从 map scope 消失。
13. **approval boundary**：普通 repository Memory 可以即时写入和纠正；未获 owner 批准的 proposal 不会变成 active Rule、`mmw-toolbox` 内容、`AGENTS.md` 或可执行 gate。
14. **failure semantics**：Nowledge Mem 不可用、0 条、正常返回三种结果可区分；native parent 查询失败显示 degraded routing；以上结果都不改变 ticket state 或阻止 session 启动。

## 14. 效果指标

阶段二衡量的是“经验是否在下一名 agent 需要时被使用”，不是 Memory 总数。

| 指标 | 记录位置 | 期望方向 |
| --- | --- | --- |
| 每次 `open/start` 实际注入的 task experience 条目数 | dispatch 输出与 night summary | 可核对，不设越多越好的目标 |
| agent 主动搜索后引用并实际采用的 Memory id 数 | ticket closeout 的共享经验行 | 上升后稳定 |
| 同一已知环境/工具问题在同一 task 被第二次独立修复的次数 | night closing pass 对照 Memory evidence 与 ticket closeout | 下降至 0 |
| 写入后被 supersede/deprecate 的比例 | spec night summary | 用于发现经验质量问题，不作为绩效目标 |
| promotion proposal 被 owner 接受后，原问题再次发生的次数 | 后续 night summary | 下降 |

不使用 ticket pass rate 证明共享经验有效，因为 pass rate 同时受任务难度、实现质量和 acceptance criteria 影响，不能单独归因于 Memory。

## 15. 明确不采纳

- 每个 map/spec 建一个 Space；
- 用 ticket title、`## Owns`、整份 spec 摘要或 semantic similarity 推断 task 归属；
- 用 `--time today` 代表 night；
- 把 Working Memory 改造成 task scratchpad、map bus 或实时广播；
- 在派发关键路径使用耗时明显更高的 `nmem ask`；
- 新建 Memory tracker event、relay、数据库、状态机、迁移流程、轮询或审批队列；
- 自动把普通 Memory 晋升为 Rule、`AGENTS.md`、gate 或 `mmw-toolbox`；
- 把 worker Thread、推理、自评或 correctness 结论交给 reviewer。

## 是否需要讨论

没有需要 grill 的产品问题。task root 的产品语义已经明确：`map if present, otherwise spec`。Space/Identity 路由、dispatch 主动注入、agent 按具体问题主动搜索、reviewer 隔离和 Working Memory 不承担 task bus，都是完成该语义所需的工程选择。

## 可复查来源

- [《Project Context 调研与 MMW 方案》](https://claude.ai/code/artifact/b9520c08-eb0d-40f1-872e-228662445954?via=auto_preview)的第 5 节“实验结果”、第 6 节“阶段二”和第 9 节“决定”
- [Nowledge Mem Background Intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)
- [Nowledge Mem Spaces](https://mem.nowledge.co/docs/spaces)
- [Nowledge Mem Context](https://mem.nowledge.co/docs/ai-context)
- [Nowledge Mem CLI](https://mem.nowledge.co/docs/cli)
- `docs/agents/issue-tracker.md` 的 `Reading a tree`、`Three label sets` 与 `Wayfinding operations`
- `docs/contexts/task-board/CONTEXT.md` 的 `The Night`
- `docs/contexts/tickets/CONTEXT.md` 的 `spec`、`ticket`、`sub-issue` 与 `map`
- `mmw-v2/skills/verify-ticket/scripts/tree.py` 的 module docstring 和 `LAYERS`
- `mmw-v2/board/board_data.py` 的 `BoardStore._read_trees()` 与 `BoardStore._spec_trees()`
- `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md` 的 `Work through the map`
- `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md` 的 `Process`
- `mmw-v2/upstream/skills/engineering/implement/SKILL.md` 的 read-in 与 `While writing code`
- `mmw-v2/upstream/skills/engineering/code-review/SKILL.md` frontmatter `description` 中的三条 review axes，以及表格行 `The reviewer session`
- `mmw-v2/skills/dispatch/references/night.md` 的 `## 4. The closing pass` 与 `## 5. The night is over`
- `mmw-v2/install.sh` 的八项 installed items 与 `--check`
- 本机 Nowledge Mem Codex connector `hooks/nmem-context.py` 的 `_load_startup_context()` 与 `main()`
