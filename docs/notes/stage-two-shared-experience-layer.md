# 阶段二与阶段三：共享经验与跨夜学习闭环

日期：2026-09-15

对象：[《Project Context 调研与 MMW 方案》](https://claude.ai/code/artifact/b9520c08-eb0d-40f1-872e-228662445954?via=auto_preview)第 6 节“阶段二 · 共享经验层 · NOWLEDGE MEM 自带机制优先”、第 7 节“阶段三 · 跨夜学习”和第 9 节“决定”

性质：阶段二与阶段三共同实施前的研究结论，不修改产品代码

## 方案总览

阶段二与阶段三作为一条反馈闭环共同实施：阶段二让 worker 在同一 task 内直接写入和取得已证实的经验，并在新 task 开工前主动取得相关历史 Memory；阶段三在每份 spec 的 `summary` 之后复盘 ticket event 与 `git log`，并在当前 repository Space 的 Retro Memory 中寻找较早的同因问题。达到门槛时，retro 创建一张 `needs-triage` proposal；owner 批准后，知识继续作为 Memory，或者通过正常 spec/ticket 流程实现为 check、reviewer active Rule、repository `AGENTS.md`、repository script、repository-local skill 或 MMW skill。

task root 按以下规则解析：spec 有 native map parent 时，map 是 task root；spec 没有 map parent 时，该 standalone spec 自己就是 task root。一个 map 可以拆成多份 spec 并行执行，这些 spec 下的 worker 使用同一个 task scope；standalone spec 下的全部 ticket 使用该 spec 的 task scope。reviewer 与 worker 使用同一个 repository Space，但不读取 task Memory。task root 决定哪些 worker 共享经验，不限制阶段三在 repository 内识别跨 task、跨 night 的重复问题。

阶段二的 worker 首次 prompt 有两个 Memory 区块，运行中另有一条按需检索路径：

1. `dispatch.sh start <ticket> worker` 根据 GitHub native parent 得到 task root，按 task scope label 精确列出当前 task 已写入的 Memory。这只负责同一轮 map 或 standalone spec 内的并行共享。
2. 同一次 start 以 task root 的已定内容执行一次 semantic search，从当前 repository 和已批准的 `mmw-toolbox` 取回与这项新任务相关的历史 Memory。map 下所有 specs 使用同一份 map 检索输入；standalone spec 使用自身检索输入。
3. worker 遇到具体的非显然故障时，以实际错误、命令和组件主动搜索；先搜当前 task，仍没有答案时再搜 repository 与 `mmw-toolbox`。

worker 一旦证实一条同一 task 其他 ticket 可复用的经验，就立即写入 repository Space，并带当前 task root 的 scope label。后来启动的 worker 会自动得到它；已经运行的 worker 在遇到相同问题时通过主动检索得到它。

reviewer 的首次 prompt 不放 Memory 检索结果；`dispatch.sh start <ticket> reviewer` 从 `mmw-reviewer` Context Bundle 中只取 active `rule_stack`，作为唯一由 MMW 加入 review 的经验。reviewer 独立读取 ticket、repository authority 和运行检查。这符合 Artifact 对 reviewer 干净上下文的设计，也不依赖各 host 是否能把 startup hook 输出送进模型。

不增加实时消息系统、Memory relay、retro 数据库或新的审批队列。必须立即改变其他 ticket 行为的信息继续使用现有 `contract`、`fault` 或 `decision` tracker event。完整 retro 写入 repository Space 的 Retro Memory；spec comment 只留下 script-written `spec.retroed` 回执。proposal 只指进入现有 `needs-triage` queue 的普通 issue。MMW 的 `finding` 仍只指 reviewer 创建的 `child.opened kind=finding`；`propose` 只是一条 worker Memory 在 closing pass 中的决定值。

**依据**：Artifact 第 6 节“阶段二”、第 7 节“阶段三”和第 9 节“决定”；task root 的范围来自 owner 对 map 与 standalone spec 的确认。

## 一、共享边界

### 1. task root、Space 与 Identity

#### MMW 已有的任务归属

- `tree.py`、Task Board 和 tracker 文档共同定义四层 native parent graph：`map → specs → tickets → children`。
- Task Board 的 `The Night` 是一个顶层 map 及其全部 specs/tickets；没有 open map parent 的 spec 自己成为一项 task。小写 `night` 仍是 `dispatch.sh` 对一份 spec 的一次运行。
- 真实 tracker 已验证 `#384 map → #374 spec → #375 ticket`；同一个 `tree.py 384 --root map` 调用读出了 #374 下的七张 tickets。
- `dispatch.sh read_ticket()` 已经从 ticket native parent 取得 spec。`## Parent` 是给 agent 读的 spec section 指针，不是机器归属关系。

一条经验的完整地址由两部分组成：

| 部分 | 值 | 作用 |
| --- | --- | --- |
| storage boundary | repository Space `owner__name` | 隔离不同客户仓库；该 Space 使用 shared retrieval，只共享读取 `mmw-toolbox` |
| task scope | `mmw-map-<map number>` | 把同一 map 下的全部 spec 放进同一个当前任务经验域 |

没有 map parent 的 standalone spec 使用 `mmw-spec-<spec number>`。

#### Space

| Space | 内容 | Retrieval mode | 可以读取 |
| --- | --- | --- | --- |
| repository Space `owner__name` | 该 repository 的 Memory、worker/reviewer Thread 和 Working Memory | `shared` | 自身与 `mmw-toolbox` |
| `mmw-toolbox` | owner 已批准、可以跨 repository 使用的 MMW 工具经验 | `strict` | 仅自身 |
| Default | owner 的普通跨工具会话与个人背景 | 保持现状 | 不进入 pipeline retrieval |

repository Space 的 `sharedSpaceIds` 只包含 `mmw-toolbox`。不同客户 repository 不互相链接；阶段二也不迁移 Default 的历史内容。`mmw-toolbox` 不是所有 Memory 的公共池，只接收 owner 明确批准晋升的通用经验。

不为每个 map 或 standalone spec 建 Space。那会把同一 repository 的跨任务历史切碎，要求在任务结束时搬运 Memory，并产生大量短命 Working Memory。task root 是 repository Space 内的 scope label，不是新的存储边界。

#### Identity

| Identity | 使用者 | 默认 Space | 作用 |
| --- | --- | --- | --- |
| `mmw-worker` | ticket worker | Default；dispatch 每次覆盖为当前 repository Space | 记录 provenance，接收 worker active Rules |
| `mmw-reviewer` | ticket reviewer | Default；dispatch 每次覆盖为当前 repository Space | 记录 provenance，接收 owner 批准的 reviewer active Rules |
| `default` | owner 的普通会话与非 pipeline 工作 | Default | 保持个人上下文，不由 dispatch 改写 |

Identity 不承担授权：Memory 是否可见由 active Space、retrieval mode 和 shared Spaces 决定。Identity 只回答“谁产生了这条记录”和“哪个角色的 active Rules 应进入 Context Bundle”。`agents enroll` 未指定 `--default-space` 时落到 Default；固定 Identity 也不能把 default Space 设成“当前 repository”，所以 pipeline 必须每次显式传 `NMEM_SPACE`。

main agent 不使用独立的 `mmw-main` Identity，也不在 `open` 时接收 task Memory 注入。它在 closing pass 由 `dispatch.sh` 按本 spec label 读取 Memory；owner 会话的完整 Thread 不会被自动搬进客户 repository Space。

#### Working Memory

Nowledge Mem Working Memory 是每个 Space 一份、由 AI 维护的每日简报，内容是当前 focus areas、open questions 和 recent activity。

- 每天早晨生成并归档上一份；新 Memory 写入后也会异步刷新，但延迟比其他后台任务更长。
- 支持的 connector 在 session start 时通过 Context Bundle 注入它；正在运行的 session 不会收到后来刷新出的内容。
- Context Bundle 还包含 Identity、active Space 和 active Rules，但不包含“按当前 task root 搜出的 Memory”。
- shared retrieval 只扩大 Memory search 的读取范围，不合并 Working Memory。repository Space 共享 `mmw-toolbox` 后，Context Bundle 仍只带 repository Space 自己的一份 Working Memory。
- 一个 repository Space 同时运行多个 map 时，它只有一份 Working Memory，不能按 map 过滤。

因此 Working Memory 是 repository 的宽背景，不是 map 级共享经验，不是实时 scratchpad，也不是确定性的任务输入。阶段二不写它、不 patch 它，也不为每个 map 新建 Space。

这一区分由本机 `nmem 0.10.78` 的 CLI、Context Bundle、Working Memory API 和 Codex connector 源码验证。Codex connector 的 `SessionStart` 读取 Context Bundle；`UserPromptSubmit` 只注入“需要时主动搜索”的提示，不重新注入 Working Memory。

#### 建立和解析

- `install.sh` 幂等建立全局的 `mmw-toolbox`、`mmw-worker` 与 `mmw-reviewer`；`install.sh --check` 只报告缺失或形状不一致。
- `dispatch.sh open <spec>` 幂等建立当前 repository Space；已有正确 Space 时不重建。Memory 只在每名 worker 真正启动时进入它的首次 prompt，不在 `open` 时交给 main agent，也不另存一份 task 检索包。
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

`agents enroll` 已有 create-only/no-op 语义；`spaces create` 没有同样承诺，所以 `dispatch.sh` 先 `spaces show <id>`，缺失才 create。MMW 命名空间下的 repository Space 已存在但 retrieval shape 不一致时，用 `spaces update <id> --retrieval-mode shared --share-with mmw-toolbox` 恢复固定形状；不会触碰 Default 或其他 Space。

正常路由只读 tracker graph：

```text
ticket --native parent--> spec --native parent--> map
```

`read_ticket()` 已经从 ticket 的 native parent 得到 spec。`dispatch.sh` 再读取 spec 的 native parent；parent 带 `mmw:map` 时使用 map scope，没有 parent 时使用 standalone spec scope。

不使用以下内容决定共享范围：

- ticket title：只是一个工作切片的名称；
- `## Owns`：只是可写路径和并行冲突边界；
- Parent spec 正文：只描述一个 seam，不能代表同一 map 下其他并行 spec；
- semantic similarity：只能判断内容相似，不能证明两个 agent 属于同一项任务。

**依据**：Artifact 2.1、第 6 节“布局”和第 9 节“Nowledge Mem 布局”；`docs/contexts/tickets/CONTEXT.md` 的 `map`、`spec` 与 `sub-issue`；`mmw-v2/skills/verify-ticket/scripts/tree.py` 的 native parent graph；Nowledge Mem `Spaces`、`Agent identity`、`Background Intelligence` 与 `Context`。

### 2. Nowledge Mem 的能力约束

| 能力 | 已确认行为 | 阶段二用途 |
| --- | --- | --- |
| `memories add` | 可指定 Space、Identity、unit type、labels；写入后即可检索 | worker 即时保存显式经验 |
| `memories list` | 可按一个 label 精确列出；只列 active Space 自身，不扩到 shared Space；本机重复 `--label` 实测为 OR；达到 `--limit` 仍 exit 0，须比较 `total` 与 `returned` | 列出当前 task root 或当前 spec night 产生的经验 |
| `memories search` | semantic + text search，约 0.5 秒；可按 label、unit type、时间和 metadata 过滤；active Space 为 `shared` 时扩到显式 shared Spaces | worker start 按 task root 取历史 Memory；agent 按真实问题精确找经验 |
| `ask` | 本机一次约 130 秒 | 不进入派发路径 |
| Space | `strict` 只读当前 Space；`shared` 读取当前 Space 和显式 shared Spaces | repository 隔离并只共享 `mmw-toolbox` |
| Identity | provenance、默认 Space 与 agent Rule 的选择，不是授权，也不是 Memory 可见性过滤器 | 区分 worker/reviewer 来源与常驻 Rule |
| Thread capture | connector 在 session 结束/compact 时保存完整会话；后台可能蒸馏成 Memory | 跨夜证据与宽背景，不承担同夜保证 |
| Working Memory | 每个 Space 一份简报，早晨生成，新 Memory 后异步刷新 | session start 的宽背景 |
| Context Bundle | Identity、active Space、active Rules、Working Memory | startup 背景；不含 task retrieval |
| supersede/deprecate | supersede 保留旧条目并建立 replacement；deprecate 使其退出普通 recall | 纠正或结束经验 |
| active Rules | 编译进 Context Bundle；普通 Memory 不会自动变 Rule | owner 批准后的 reviewer/Space 常驻行为 |
| Space 间迁移 | `memories move` 保留 Memory id、source 与 labels，但原 Space 不再持有该 Memory；同一套个人 Space 没有 copy 命令 | 不用来晋升 `mmw-toolbox`；晋升时新建泛化后的 Memory，原 repository Memory 保持不变 |

**依据**：本机 `nmem 0.10.78` CLI、Context Bundle、Working Memory API 与 Codex connector 的实际行为；隔离实验验证 `list` 不扩到 shared Space、`search` 会扩展、`move` 会从原 Space 移除记录。

## 二、阶段二：task 内共享经验

### 3. worker 启动时主动注入

#### `dispatch.sh start <ticket> worker`

`start` 在调用 runner adapter 前组装一次开场经验包：

1. 从 ticket 的 native parent 得到 spec，再从 spec 的 native parent 得到 `map:<n>` 或 standalone `spec:<n>`；
2. 得到当前 repository Space；
3. 用唯一 task scope label 列出当前 task 已写入的显式 Memory；
4. 用 task root 的已定内容做一次历史 semantic search；
5. 按 Memory id 去重后，把两组结果放进 worker 的首次 prompt。

```sh
nmem --json memories list \
  --space "$NMEM_SPACE" \
  --label "$MMW_TASK_SCOPE" \
  --limit 1000
```

`dispatch.sh` 比较返回值的 `total` 与 `returned`。相等才算完整读取；`total > returned` 时仍启动 worker，但首次 prompt 明确写出“当前 task Memory 已截断”，不能把前 1000 条伪装成完整结果。本机 CLI 没有 `offset`，因此不另造分页层；一个 task 达到这个上限时应治理其 Memory，而不是继续扩大启动 prompt。

这里只使用一个 scope label。本机实测 `memories list` 的重复 `--label` 是 OR，不是 AND；因此所有带 task scope label 的 Memory 都必须是共享经验。

历史检索不使用 scope label，因为下一夜启动的是新的 map 或 standalone spec，先前 repository 经验带的是旧 task label。它使用同一个 task root 的已定内容，让同一 map 下所有 specs 得到相同的历史检索结果：

| task root | semantic search 输入 | 原因 |
| --- | --- | --- |
| map | `Destination`、`Notes`、`Decisions so far` | map 是同一项任务的共同低分辨率索引；这些段落说明目标、领域与已定路线，不读取某一份 child spec 来代替整个 map |
| standalone spec | `Problem Statement`、`Solution`、`Implementation Decisions`、`Testing Decisions` | 没有 map 时，spec 本身就是完整 task root |

map 的 `Decisions so far` 已经给每项决定一行 gist 与 resolution link；检索只需要这份共同索引，不在每次 worker start 重新读取所有 resolution comment。`Out of scope` 不进入 query，避免把明确不做的内容召回成工作经验。检索命令固定为：

```sh
nmem --json memories search "$MMW_TASK_QUERY" \
  --space "$NMEM_SPACE" \
  --label mmw-experience \
  --limit 10
```

repository Space 的 shared retrieval 使结果只来自当前 repository 和已批准的 `mmw-toolbox`。当前 task Memory 如果同时被 semantic search 命中，按 Memory id 去重，精确 `list` 的版本保留。检索包不写回 tracker、文件或 Mem；每次 worker start 直接重做两次廉价读取，所以没有缓存失效或另一份 task 状态。

首次 prompt 的固定部分只包含：

```text
MMW task root: map #384
MMW task scope: mmw-map-384
Current task shared experience:
- <memory id> — <title>
  <content>
  Source: <source>

Historical experience relevant to this task:
- <memory id> — <title>
  <content>
  Source: <source>

When an unexplained failure is not covered above, search with the exact error,
command and component. Verify every Memory against current repository evidence.
```

task scope 仍只由 native parent 决定；semantic query 只判断历史相关性，不能改变归属。ticket title、`## Owns` 与 `--time today` 既不定 scope，也不组成开场 query。若 task-scoped `list` 为 0，新 task 仍可通过历史 semantic search 得到旧经验；若 semantic search 为 0，则明确写 0，不用 Working Memory 冒充检索结果。

#### `dispatch.sh start <ticket> reviewer`

reviewer 不执行上述 Memory 读取，首次 prompt 不放其结果。`dispatch.sh` 另读一次不带 Working Memory 的 Context Bundle：

```sh
nmem --json context read \
  --space "$NMEM_SPACE" \
  --agent-id mmw-reviewer \
  --no-working-memory
```

它只把返回值 `rule_stack.global`、`rule_stack.owner`、`rule_stack.space` 与 `rule_stack.agent` 中的 active Rules 加入 reviewer 首次 prompt；owner profile、Working Memory、Memory search result 和 Thread 都不进入这个 review packet。这样，能接收 startup Context Bundle 的 host 即使重复看到同一条 Rule，也不改变行为；不能接收 startup hook 输出的 host 仍会在 review 开始前得到同一组 Rules。

两种角色都由 runner adapter 设置：

- `NMEM_SPACE=<repository Space>`
- `NMEM_AGENT_ID=mmw-worker|mmw-reviewer`

worker 另收到 `MMW_TASK_SCOPE`、`MMW_SPEC` 与 `MMW_TICKET`，供主动搜索和写入使用。runner 的 `start` 合同增加可重复的 `--env KEY=VALUE`：Paseo 转发给现有 `paseo run --env`，Herdr 转发给现有 `herdr tab create --env`，Orca 把同一组值放进新 terminal 的 host launch environment。Space、Identity 和 task scope 仍由 `dispatch.sh` 解析，adapter 只传值。

**依据**：Artifact 2.2“当夜由派发脚本查一次”；monomind project-context `context_packet.py` 的开工前相关上下文取回；现有 `dispatch.sh read_ticket()` 与 runner adapters；`wayfinder/SKILL.md` 的 map body 与 `to-spec/SKILL.md` 的 spec template。

### 4. worker 遇到问题时主动搜索

worker 只在一个明确时刻主动检索：命令或工具出现 ticket、repository 文档和当前 task 经验都没有解释的行为，在尝试 workaround 之前。

先查当前 task：

```sh
nmem --json memories search \
  "<exact error + command + component>" \
  --space "$NMEM_SPACE" \
  --label "$MMW_TASK_SCOPE" \
  --limit 10
```

没有答案时，再查 repository 与 toolbox 历史：

```sh
nmem --json memories search \
  "<exact error + command + component>" \
  --space "$NMEM_SPACE" \
  --label mmw-experience \
  --limit 10
```

repository Space 的 shared retrieval 让第二次搜索同时覆盖当前 repository 与 `mmw-toolbox`，但不读取其他客户 repository 或个人 Default。行为写进 `implement/SKILL.md`；没有相关问题时不轮询。Memory 是资料，不是 authority，worker 必须用当前命令输出或 repository authority 核对后才采用。

**依据**：Artifact 2.2“worker 也可以按技能文本自己搜”；Nowledge Mem `memories search`。

### 5. worker 当场写入可复用经验

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
  --label "$MMW_TASK_SCOPE" \
  --label "mmw-spec-$MMW_SPEC" \
  --label "mmw-ticket-$MMW_TICKET" \
  --title "<searchable title>"
```

Memory 正文固定使用 Artifact 2.1 的五项内容；字段名避免与 MMW `finding` 混名：

```text
适用条件：<环境、版本或前提>
问题：<已证实的非显然行为>
有效做法：<下一名 worker 可以直接执行的操作>
证据：<命令与输出首行，或 path:line>
发生位置：<repository、spec #n、ticket #n、日期>
```

“适用条件”防止旧环境经验被无条件套用，“有效做法”让下一名 worker 可以直接行动，“发生位置”保留来源与时间；不另造 provenance schema。默认 unit type 是 `learning`；固定操作步骤使用 `procedure`。适合写的是不稳定测试、工具的非显然行为、环境修法和测试前提。普通实现细节、ticket 状态、未经验证的推测、用户决定、凭据和客户数据不写。Space、Identity、task/spec/ticket labels 已提供 repository、角色和工作来源。

同一事实发生变化时不覆写历史：新 Memory 已证实旧 Memory 错误时使用 supersede；旧经验只是不再适用时使用 deprecate。普通 repository Memory 的写入与纠正不等待 owner 批准，因为等待会使并行 agent 继续重复遇到同一问题。

**依据**：Artifact 2.1；monomind project-context `context_capture.py` 的当场 capture 与 provenance；Augment Expert Memory 的“只保存会改变未来判断的信息”和 narrowest stable scope。

### 6. map 下并行 spec 的传播

以 map `#384` 下并行的 spec A、spec B 为例：

```text
spec A worker 启动
  → dispatch 用 map 的共同 query 注入相关历史 Memory
  → 再注入 label=mmw-map-384 的当前 task Memory
  → worker 证实一个非显然工具行为
  → 立即写 Memory(labels: mmw-experience, mmw-map-384)

spec B worker 稍后启动
  → native parent 同样解析为 map #384
  → 使用与 spec A 相同的 map query 取得相关历史 Memory
  → task-scoped list 直接取得 spec A 的新 Memory

spec B worker 已经在运行
  → 遇到同一错误
  → 用错误、命令、组件搜索 mmw-map-384
  → 取回 spec A 的 Memory
```

下一夜的新 map 不进入旧 map 的 task-scoped 列表；它会在 worker start 以自己的 task root query 搜索 repository 历史，因此相关旧 Memory 可以在开工前按 relevance 取回。没有命中但后来出现具体相同问题时，worker 仍用错误、命令和组件精确搜索。standalone spec 使用相同路径，scope 改为 `mmw-spec-<n>`，历史 query 改用自身的四个已定 section。reviewer 不在这条 Memory 传播路径中。

**依据**：task root 的 native parent graph，以及前述 worker 注入、搜索和写入路径。

### 7. Memory 与 tracker event 的分工

Memory 只承载“怎么做、踩过什么坑、什么非显然前提已被证实”。它不承载 ticket state、依赖、`## Owns`、acceptance 结果、spec 修订或必须马上执行的指令。

Memory 与行为机制也不是同一类东西。Memory 通过 list/search 按相关性取得，使用前必须核对；check、script、repository `AGENTS.md`、repository-local skill、reviewer active Rule 和 MMW skill 会直接检查、注入或规定后续行为。一个经验可以长期留在 Memory 而不改变任何 agent 行为；只有 owner 批准并完成对应改变后，它才进入行为机制。

当 worker A 发现的信息必须立即改变 worker B 的行为时：

- contract 不适配：现有 `contract` child；
- pipeline 本身故障：现有 `fault` child；
- 需要 owner 选择：现有 `decision` child。

relay 继续只由 tracker event 唤醒 agent。Memory 不产生 wake，也不参与 gate。

**依据**：Artifact 2.1 与第 9 节“经验不经票事件”；`mmw-v2/skills/verify-ticket/scripts/events.py` 的 event fold。

### 8. reviewer 的独立性

reviewer 的开场 prompt 不放 worker 或 repository Memory 的检索结果，`code-review` 也不要求 reviewer 主动搜索普通 Memory。需要常驻的 review 经验只以 owner 已批准并编译进 `mmw-reviewer` Context Bundle 的 active Rules 提供；`dispatch.sh` 从 `rule_stack` 取出这些 Rules，保证所有 runner/host 得到相同 review packet。

reviewer 仍独立读取 ticket、spec、repository authority 与 diff，并重新运行它负责的检查。worker Thread、推理、自评和“实现正确”的结论都不进入 reviewer。connector 自动提供的 repository Working Memory 只作宽背景，不能作为 finding 或 verdict 的证据；MMW 自己组装的 review packet 不包含它。需要让以后每次 review 都执行的稳定方法，先由 retro 提议，owner 批准后再成为 active Rule。

这保留了 Artifact 2.2 的角色边界：reviewer 使用稳定规则与当前 repository 证据，不继承 worker 的检索结果或结论。

**依据**：Artifact 2.2“角色”；`research-4-theory.md` 的 `A14. 验证者用干净上下文`；Augment Review Guidelines。

### 9. Thread、Working Memory 与跨夜检索

下一夜会启动新的 map 或 standalone spec，不会靠旧 task label 继续上一夜。跨夜经验通过以下路径进入新 agent。

#### connector 自动注入的真实内容

支持 session-start 注入的 Nowledge connector 会使用 runner 提供的 `NMEM_SPACE` 和 `NMEM_AGENT_ID` 读取 Context Bundle。自动注入的是实际文本，而不只是提示：owner/agent Identity 摘要、active Space、适用的 active Rules，以及该 repository Space 当前的一份 Working Memory。Working Memory 本身可以包含 Nowledge 后台从较早 Memory 与活动整理出的内容和 Memory 链接，所以它能给 agent 一份真实的 repository 宽背景。

它**不会**自动执行与当前 map/spec 有关的 `memories search`，不会自动注入命中的 Memory records，也不会把上一夜的完整 Thread 直接放进新会话。Working Memory 是整个 repository 的异步简报，可能同时包含多个 task，不能按当前 task root 过滤；其刷新也没有派发时限。因此它可用于方向与未决事项，不能承担“这项新任务的相关历史已经送达”。

Claude Code、Codex、Cursor 与 Pi 的 connector 可以在 session start 提供 Context Bundle，但各自有 fallback 差异；Grok 的 passive `SessionStart` 不把正文交给模型。MMW 不把关键路径建立在这种 host 差异上。

#### MMW 在新 task 开工前主动送达

每名 worker 启动时，`dispatch.sh` 都做两次读取，并把结果直接写进首次 prompt：

1. `memories list --label <current task scope>`：取得同一轮 task 内较早 worker 刚写的经验；新 task 开始时通常为 0。
2. `memories search <task root query> --label mmw-experience`：取得较早 task 留在当前 repository 和 `mmw-toolbox` 的相关历史；这才是下一夜新 map/spec 的主动跨夜路径。

map 的所有 worker 使用 `Destination + Notes + Decisions so far` 这一份共同 query；standalone spec 使用自己的 `Problem Statement + Solution + Implementation Decisions + Testing Decisions`。结果不另存一份，worker 每次 start 直接搜索，所以 task root 内容变化会在下一次启动自然生效。

#### worker 运行中的精确检索

开场 semantic search 只能按任务语义取回最相关的一小组历史，不能预知后面出现的具体故障。worker 真正遇到未解释的行为时，仍以实际错误、命令和组件搜索 current task，再搜索 repository 与 `mmw-toolbox`。这条路径补充开场包，不替代它。

#### Thread 的位置

session 结束或 compact 时，已启用的 connector 可以把会话保存为 repository Thread。Thread 是可审计的会话记录；Nowledge 后台以后可能从中蒸馏 Memory 并刷新 Working Memory，但这个过程异步且不保证完成。Thread 本身不自动注入下一名 agent，也不承担确定送达。

因此，Mem 的自动能力负责宽背景与 Thread capture；MMW 的 worker-start 检索负责主动送达新 task 的相关历史和同一 task 的即时共享；worker 的精确 search 负责开场时无法预知的问题。reviewer 所需的 active Rules 仍由 `dispatch.sh` 读取 `context read --no-working-memory` 后明确放进 review packet，普通 Memory 不进入 reviewer。

**依据**：Artifact 2.1、2.2；Nowledge Mem `Background Intelligence` 与 `Context`。

## 三、阶段二收口与阶段三 retro

### 10. closing pass 到 retro 只有一条顺序

`mmw-v2/skills/dispatch/references/night.md` 的 `## 4. The closing pass` 先按现有流程读取本 spec 的每张 ticket，并把每个 reviewer `finding` 路由为 `fixed`、`stale` 或 `became-ticket`。没有未路由 finding 后，main agent 按 `mmw-spec-<n>` 列出本 spec night 写入的 worker Memory，逐条选择：

1. **`retain`**：仍正确、仍适用，Memory 不改；
2. **`propose`**：这条 Memory 应交给 retro 判断是否需要 owner 批准的行为改变或 `mmw-toolbox` copy；这是决定值，不是新对象；
3. **`deprecate`**：证据表明不再适用；
4. **`supersede`**：另一条新 Memory 已经明确替代它。

`propose` 的门槛沿用 Artifact 2.3：同因独立出现至少两次，或一次就有实际阻塞 ticket 的 event/commit 证据。main agent 把 `memory_id`、决定、理由和必要证据交给 `dispatch.sh summary <spec> --memory-decisions <file>`；`supersede` 另带 `replacement_id`，`propose` 另带达到门槛的 event/commit URL。`summary` 重新列举同一组 ids 后才执行 Memory lifecycle 操作。

`spec.closed` 的 `NIGHT SUMMARY` 记录逐项决定、计数与 `propose` 的 Memory ids，作为 closing pass 到 retro 的确定性交接。Memory 服务不可用、JSON 不可读或读取截断时仍允许 night 结束，但明确写 `Memory closing: unchecked (<reason>)`，不能写成 0。

`summary` 成功后，同一 main agent 立即运行 retro。retro 完成证据分析后，达到门槛时先创建或复用 proposal，再用固定 id 写完整 Retro Memory，最后写 `spec.retroed` 回执。它不改变 `spec.closed`，不持有 agent，也不触发 relay。

**依据**：Artifact 2.3、3.1；`mmw-v2/skills/dispatch/references/night.md` 的 `## 4. The closing pass` 与 `## 5. The night is over`；现有 `summary` 与 `spec.closed`。

### 11. retro 的范围与证据

#### 三个范围

| 范围 | 固定定义 | 作用 |
| --- | --- | --- |
| 本次复盘 | 当前刚完成的 spec night | 形成本次 Retro Memory |
| 阶段二共享 | task root：`map if present, otherwise spec` | 决定哪些 worker 立即共用 `mmw-experience` Memory |
| 历史比较 | 当前 repository Space 中较早的 `mmw-retro` Memory | 识别跨 ticket、spec、task 和 night 的同因问题 |

每份 spec 各自运行一次 retro，不等待同一 map 的其他 specs；后完成的 sibling spec 可以搜索到先完成 spec 的 Retro Memory。没有 map-level retro，也没有“下一夜继续同一 map/spec”的假设。

#### 本次事实来源

| 输入 | 来源 | 能证明什么 |
| --- | --- | --- |
| 本次完整 ticket 集合 | spec 的 native children | 哪些 ticket 与 child 必须读取 |
| 执行与最终结果 | 每张 ticket 的完整 event fold 与承载 event 的 comment | bounce、return、lost、HANDOFF、finding、route、check 与最终结果 |
| 实际落地 | 本批 merge、closing-pass fix 与 base branch `git log` | 哪些改变进入 repository |
| closing pass 的 `propose` 决定 | 当前 `spec.closed` | 哪些 worker Memory 需要 owner 判断；不能证明运行事实 |
| 交付意图 | 当前 spec 的 `Problem Statement`、`User Stories`、`Out of Scope` | expected surface；不能证明实现发生了什么 |

运行事实只接受 event 或 commit。reviewer finding 的 path、claim 与 category 从承载 `reviewer.reported` 的 comment 取得。Memory、Thread、Working Memory、agent 自评和无输出推断不能补成运行证据。

阶段三不回填启用以前的 closed specs，也不建立 bootstrap baseline。历史从第一条 Retro Memory 开始。某项来源读不到时写“未检查”及来源，不能写成“没有发生”。

**依据**：Artifact 3.1；BMAD-METHOD `bmad-retrospective/workflow.md` 与 `evidence-gathering.md`；MMW `events.py` 与 `git log`。

### 12. retro 的处理顺序

1. **核对最近一次 proposal。** 用 `memories list --label mmw-retro --limit 1` 取得当前 repository Space 最近一条 Retro Memory，读取其中的 proposal 链接。只有找到实际 commit、active Rule id、Memory id 或现行文件位置，才写“已落地”；issue 关闭本身不算。
2. **从本次 event/commit 形成问题描述。** 同一事实同时出现在 reviewer comment、child 与 route 中只算一次。每个问题写明 category、cause、当前处理、预防方向和 evidence URL。
3. **搜索较早同因问题。** 对每个当前问题，用 `category + cause` 搜索带 `mmw-retro` label 的 Memory；相同 path、相似标题或宽 category 不能单独算同因。
4. **核对历史命中。** 读取命中 Memory 中的原 ticket event/commit URL。只有原始证据能够打开、确实是同一原因、且来自不同 ticket/spec/night 时，才计为独立出现。
5. **完成 intent reconciliation。** 从 spec 取得 expected surface，从 checks/event 取得 observed surface，并与 `Out of Scope` 对照；只报告一致、偏离或未验证。
6. **完成 review learning。** 区分 reviewer false positive 与被其他 ticket 修掉的有效 finding。
7. **决定是否创建或复用 proposal。** 满足第 13 节门槛才创建；retro 本身不修改行为。
8. **写入产物。** 先写完整 Retro Memory，再在 spec issue 留 `spec.retroed` 回执。

这条路径让 Mem 负责发现相关历史，让 ticket event 与 commit 负责核实。下一次 retro 不遍历旧 spec comments，也不需要 occurrence 表、retro 数据库或检索缓存。

**依据**：Artifact 3.1；BMAD `retro-document.md` 的 previous-action verification；Artifact 第 5 节“经验直接写 Mem”与 MMW tracker authority。

### 13. retro 的产物与后续去向

每次 retro 有两个固定产物：完整 Retro Memory 和 `spec.retroed` 回执；达到门槛时另有一张 `needs-triage` proposal。

#### 完整 Retro Memory

每份成功的 retro 在当前 repository Space 写一条 `unit-type=event` 的 Memory：

```sh
nmem --json memories add --stdin \
  --id "mmw-retro-<repository-space-id>-spec-<spec-number>" \
  --space "$NMEM_SPACE" \
  --source mmw-retro \
  --unit-type event \
  --label mmw-retro \
  --title "Retro: <repository>#<spec-number> — <spec title>"
```

固定 id 使同一 spec 的重试写回同一条记录。Retro Memory 只带 `mmw-retro`，不带 `mmw-experience`、`mmw-spec-*` 或 task scope label；因此 worker 的开场读取和 closing pass 都不会把它当成 worker experience。`mmw-toolbox` 也只接收 `mmw-experience`，不接收 `mmw-retro`，所以 repository Space 的 shared retrieval 不会把其他来源混进 retro 历史。只有 retro script 读取 Retro Memory。

正文固定为：

```text
Spec: <repository>#<spec-number>
Task root: map #n | standalone spec #n
Evidence checked: <tickets、event comments、commit range；未检查项>

## Previous proposals
- <proposal> — 已落地：<commit / Rule / Memory / file> | 没找到证据

## Problems observed
### <category>: <cause>
Evidence: <ticket event or commit URL>
Handled here: <本次怎样处理>
Prevention: <怎样防下一次>
Earlier occurrences: <Retro Memory ids + source evidence，或 none>
Proposal: <issue URL，或 none>

## Intent reconciliation
Expected: <spec surface>
Observed: <checks/event surface>
Gap: <一致、偏离或未验证>

## Review learning
<有效 finding、invalid、fixed-elsewhere 与 proposal，或 none>

Observed: <retro 时间与 base commit>
```

这里的“problem”是 Retro Memory 的普通正文，不是新的 tracker object。MMW 的 `finding` 只在引用 reviewer finding 时使用。完整 Retro Memory 是经验记录，不是行为机制；普通 worker/reviewer 不读取它。

#### `spec.retroed` 回执

retro script 成功写入 Retro Memory 后，在当前 spec 留一条简短 comment：

```text
NIGHT RETRO
Result: recorded
Retro Memory: nowledgemem://memory/<id>
Problems: <count>
Proposals: <issue links or none>
Evidence: complete | partial (<unreadable sources>)

<!-- mmw {"v":1,"event":"spec.retroed","stage":"night","actor":"main",
"result":"recorded","retro_memory":"<id>",
"problem_count":<n>,"proposals":[...]} -->
```

`spec.retroed` 只做三件事：

1. 证明脚本为这份 spec 完成了 retro；
2. 从 tracker 指向完整 Retro Memory 与 proposal；
3. 让同一 spec 的 retro 重跑判断“已经完成”，保持幂等。

它不用于发现历史，后续 retro 也不需要读取较早的 `spec.retroed`。下一次 retro 直接在 Mem 搜 `mmw-retro`，再核对命中记录引用的原 ticket event/commit。这符合 Artifact 第 5 节“经验不在票上留第二份”，也保留 Artifact 3.1 要求的 script-written event。

Retro Memory 写入失败时，脚本写 `result=unrecorded` 与具体原因。已经用 event/commit 证据创建的 proposal 保留；再次运行以 proposal 正文中的 source spec URL 和 evidence URL 复用该 issue，以同一固定 Memory id 完成 upsert，再追加 `result=recorded` 回执。`events.py` 以最新一条为准。retro 失败不回滚已经完成的 `spec.closed`，但报告不能伪装成成功或 0 个问题。

#### `needs-triage` proposal

proposal 只有一个含义：一张请求 owner 批准预防改变的普通 GitHub issue。retro 只在以下任一条件成立时创建：

1. 本次执行问题与较早 Retro Memory 是同因，并有两个独立 event/commit 来源；Artifact 首批范围是相同 bounce 原因、相同 `HANDOFF REQUIRED` 原因、相同 reviewer finding category、相同环境问题被重复修复。
2. closing pass 已把一条 worker Memory 决定为 `propose`，并有“两次独立出现”或“一次实际阻塞 ticket”的 event/commit 证据。

一次普通执行问题不因为严重就自动提案；它仍走现有 `fault`、`contract`、`finding` 或 ticket 路径。

proposal 创建在负责改变的 repository：MMW/toolbox 行为开在 multi-model-workflow；consumer-local 问题留在该 consumer repository。它只带现有 `needs-triage` queue label，不带 `mmw:map/spec/ticket/child` layer label。正文只含问题、来源、本例处理、预防方式、建议目的地、source spec 与 Retro Memory id。

创建前按正文中的 source spec URL 和 evidence URL 搜索已有 proposal；命中则复用 URL。同一 spec 的重试由固定 Retro Memory id 与最新 `spec.retroed` 回执保持幂等。

#### intent reconciliation 与 review learning

intent reconciliation 从 `Problem Statement`、`User Stories` 取得 expected surface，从 ticket checks 与 event 取得 observed surface，再与 `Out of Scope` 对照。它只描述一致、偏离或未验证，不增加功能，不改 spec。

reviewer 汇总中的每条 `finding` 增加稳定 category，同时保留现有 axis、path、line 与 claim。`route … stale` 记录：

- `reason=invalid`：finding 从一开始就不成立；
- `reason=fixed-elsewhere`：finding 曾成立，但已由其他 ticket 或 closing-pass fix 修复。

同一 category 的 `invalid` 两次，可以提出 reviewer 行为改变；同类真实缺陷两次，可以提出 anti-pattern、check 或 lint。repository-specific 的 review 经验进入该 repository 的 `AGENTS.md` 或 check；只有跨 repository 都成立的稳定 review 方法才进入 `mmw-reviewer` active Rule，因为这个 Identity 是全局共用的。`fixed-elsewhere` 不算 reviewer false positive。category 只是检索入口，是否同因仍由 cause 与独立 evidence 决定。

#### owner 批准后：Memory 与行为机制分开

Memory 可以长期存在，但仍只是按相关性检索、使用前核对的经验。check、script、repository `AGENTS.md`、repository-local skill、reviewer active Rule 和 MMW skill 会直接检查、注入或规定后续行为。文档以“Memory”和“行为机制”分别指这两类结果；区别是“是否改变后续执行”，不是“保存多久”。Augment Code Review Memory 也明确区分这两者：Memory 是随证据演进的上下文，skill 是可重复执行的明确方法。

| 问题性质 | 目的地 | 后续怎样生效 |
| --- | --- | --- |
| 可机械判断 | `.mmw/target.json`、judge、lint、ticket `CHECK:` 或 repository script | 运行或验收时直接检查 |
| repository 通用且代码无法推出 | repository `AGENTS.md` 的 Gotchas | 后续 agent 读取 repository authority |
| repository 特有、重复出现、需要多步操作 | repository-local skill | description 负责发现；任务匹配时加载 `SKILL.md` 与必要的 scripts/references/assets |
| 跨 repository 成立的 reviewer 稳定方法 | `mmw-reviewer` active Rule | reviewer start 从 Context Bundle 的 active `rule_stack` 注入 |
| MMW pipeline 行为 | 对应 MMW skill、reference 或 script | 新版本安装后的 night 使用 |
| 跨 repository 有用但不应强制 | `mmw-toolbox` 中一条泛化后的 Memory | repository shared search 按需取得；原 repository Memory 不移动 |
| 不够稳定或不够通用 | 原 repository Memory | 保持可搜索，不改变行为 |

能机械执行的内容优先进入 check/script；`AGENTS.md` 只放无法从代码推出且几乎每项任务都适用的短规则。repository-local skill 只用于当前 repository 后续会重复执行的多步方法，并且能够写清触发条件、输入、输出与 `Done when`；偶尔有用的事实继续留在 Memory，单步命令不包装成 skill，MMW 自身流程才进入 MMW skill。owner 批准后仍走正常 `to-spec`、`to-tickets`、worker、review、closeout 和 landing，retro 不直接写这些行为机制。

reviewer active Rule 与 toolbox Memory 都使用 Nowledge Mem 的现有接口：

```sh
nmem --json rules upsert <rule-id> \
  --scope agent --agent mmw-reviewer --status active \
  --title "<owner 批准的标题>" --body "<owner 批准的规则>"

nmem --json memories add --stdin \
  --id "mmw-toolbox-<source-memory-id>" \
  --space mmw-toolbox --source mmw-promotion \
  --unit-type learning --label mmw-experience \
  --label mmw-toolbox-approved \
  --title "<owner 批准的通用标题>"
```

toolbox Memory 的正文使用 owner 批准的通用表述，并保留原 Memory id、source proposal URL 与来源 repository。固定目标 id 使重试更新同一条 copy；不使用 `memories move`，因为实测 move 会使原 repository 不再持有该 Memory。

#### 回流路径

```text
worker 写/读 mmw-experience
  → closing pass：retain / propose / deprecate / supersede
  → spec.closed
  → retro：本次 event/commit + 较早 mmw-retro
  → 达到门槛时创建或复用 needs-triage proposal
  → 完整 Retro Memory（含 proposal URL 或 none）
  → spec.retroed 回执
  → owner 批准
      ├─ 知识：repository Memory / mmw-toolbox Memory
      └─ 行为：check / script / AGENTS.md / repository-local skill /
               reviewer active Rule / MMW skill
  → 后续 worker、reviewer、check 与 retro 从各自入口使用
```

**依据**：Artifact 第 5 节“Memory 是经验库”、2.3、3.1 与第 9 节；MMW tracker authority、`needs-triage` 与现有发布流程；BMAD previous-action verification；OpenAI Harness Engineering；Augment Code Review Memory；Agent Skills specification。

## 四、实施与证明

### 14. 实施起点

- 本机 CLI/server 是 `0.10.78`；本文只使用这个本机版本已实测的接口。
- Spaces 功能已经启用，目前只有 Default；repository Spaces、`mmw-toolbox` 和 MMW Identities 尚未建立。
- 当前只有 `default` Identity；active Rules 为 0，已有 Rule 全部是 draft。
- MMW 目前只由 `install.sh` 配置 Cursor 的 Nowledge MCP；dispatch、implement 和 runner adapter 里还没有阶段二路由。
- `to-spec` 已允许一个 map 拆成多份 specs，但发布步骤尚未明确保证这些 specs 是 map 的 native children。

**依据**：本机 `nmem 0.10.78` 实测；现有 `install.sh`、`dispatch.sh`、runner adapters 与 `to-spec/SKILL.md`。

### 15. 阶段三必须补齐的结构化接口

阶段二沿用 Nowledge Mem 的 Space、Identity、Memory、Context Bundle 与 Rules 接口；阶段三只补齐以下 MMW 与 Mem 连接：

1. 从 map 发布 spec 时，把 spec 创建为该 map 的 native child，并在 read-back 验证 `parent.number`；standalone spec 保持无 map parent。
2. review finding 汇总行增加稳定 category，同时保留现有 axis、path、line 和 claim。
3. `child.closed resolution=stale` 增加 `reason=invalid|fixed-elsewhere`，resolution 本身不变。
4. retro 用固定 id 在 repository Space 写完整 `mmw-retro` Memory。
5. `events.py` 增加 `spec.retroed result=recorded|unrecorded`；recorded 回执带 `retro_memory` 与 proposal numbers，不进入 hold、relay 或 ticket verdict。
6. retro proposal 使用现有 `needs-triage` queue 和现有 issue tracker，不增加 layer、queue 或私有审批表。

`## Sources`、map 的 `## Specs`、ticket title 和 `## Owns` 都是人可读记录或执行切片，不能替代 native parent 与 structured outcome。

**依据**：现有 `to-spec`、review comment、`route`、`events.py` 与 issue tracker 合同。

### 16. 实施顺序

阶段二与阶段三作为一个 spec，按同一依赖链实施。

#### A. Space、Identity 与现有 dispatch

1. `mmw-v2/install.sh` 幂等建立 `mmw-toolbox`、`mmw-worker` 与 `mmw-reviewer`，`--check` 只读核对。
2. 在现有 `dispatch.sh` 内增加 Nowledge helper：建立或读取 repository Space、解析 `nmem --json`、按 task/spec label 列举、从 task root 生成历史 semantic query、读取 reviewer active `rule_stack`，并区分 unavailable、0 results 与截断。worker 仍直接使用 Nowledge CLI 做运行中的精确搜索并写 Memory，不增加中间服务、检索缓存或新 adapter module。

#### B. 阶段二读写

3. `dispatch.sh` 解析 native parent，并通过 runner `start --env` 设置 Space/Identity；三个 runner adapter 只把值送入实际 agent process。worker start 精确列出当前 task Memory，并按 map 或 standalone spec query 搜索历史后去重；reviewer start 只读取 active `rule_stack`；`summary --memory-decisions` 校验逐项 manifest，并把完整决定写入 `spec.closed`。
4. `implement/SKILL.md` 增加 Artifact 2.1 的五字段写入条件与 2.2 的主动搜索时点；`code-review` 不增加 Memory retrieval，只使用 prompt 中的 active Rules。
5. `to-spec/SKILL.md` 在 map 来源时创建 native child 并 read back；standalone spec 不虚构 parent。

#### C. 阶段三 retro

6. `code-review` 的汇总合同增加 category；`route … stale` 增加 `invalid|fixed-elsewhere` reason。
7. `events.py` 增加一个无 hold、无 wake 的 `spec.retroed` 回执 event；night runbook 在成功 `summary` 后执行 retro。
8. 新增 `mmw-v2/skills/retro/SKILL.md` 与一个脚本入口。脚本读取当前 spec tree、ticket event、相关 `git log` 与 `spec.closed` 的 proposed Memory ids；用 `mmw-retro` list/search 取得较早记录，命中后核对其原 event/commit；达到门槛时先创建或复用 `needs-triage` proposal，再写完整 Retro Memory 和当前 spec 回执。普通 worker/reviewer 不读 Retro Memory；retro 不把 Memory、Thread 或 Working Memory 当作运行事实。

#### D. owner approval 与证明

9. 批准后的改变继续走现有 triage、`to-spec`、`to-tickets`、worker、review、closeout 和 landing；生成 repository-local skill 时验证触发、完整流程与当晚 host 的发现结果，新建 toolbox Memory 或激活 Rule 时在 proposal 留下实际 id。
10. 按 repository 规则更新 Tickets/Night/Memory contexts、dispatch reference、upstream merge-note 和必要的 downstream-note。
11. 测试覆盖 install、dispatch、runner、map/standalone scope、当前 task list、新 task historical search、review category、stale reason、retro event、proposal repository/label 和跨 night 重复。

实现顺序是 A → B → C → D。所有验证使用隔离 `MMW_HOME`、假 tracker、临时 Git repository 和临时 Nowledge objects；当前 frozen runtime 不读取新版本。

**依据**：Artifact 3.1；`mmw-v2/upstream/skills/in-progress/retro/SKILL.md`；根 `AGENTS.md` 的 `Self-hosting boundary`。

### 17. 不可用时的行为

- Nowledge Mem 读取或写入失败时，worker 照常执行 ticket，输出具体失败原因；Memory 从不改变 acceptance、review 或 landing verdict。
- native parent 读不到时，不猜成 standalone spec，也不扩大到 repository scope；本次 worker 不注入或写 task-scoped Memory，并报告 routing 未完成。
- retro 的某项 event/git source 读不到时，Retro Memory 明确写“未检查”；不能把 unreadable 当 0，也不能用该来源形成 proposal。Retro Memory 写入失败时，spec 写 `spec.retroed result=unrecorded` 回执；已由可读 event/commit 支撑的 proposal 保留并由重试复用。

这些行为只让“查询失败”和“查到 0 条”可区分，不增加 retry state、补偿事务或新的 gate。

**依据**：Artifact 2.1 的 fail-open；MMW ADR 0008 的 refusal 语义。

### 18. 验收

1. 一个 map 下两份 specs 的 workers 解析成同一 task scope；standalone spec 使用自己的 scope。
2. repository A 只能搜索自身与 `mmw-toolbox`，看不到 repository B 或 Default。
3. runner 实际启动的 agent process 收到 `NMEM_SPACE` 与对应 `NMEM_AGENT_ID`；显式 worker Memory 进入当前 repository Space，已启用 connector 时 worker/reviewer Thread 也进入该 Space。
4. spec A worker 写入 task Memory 后，同一 map 中稍后启动的 spec B worker 通过 task-scoped `list` 得到它；reviewer prompt 不包含它。
5. 下一夜的新 map worker 以该 map 的 `Destination + Notes + Decisions so far`，新 standalone spec worker 以自身四个已定 section，在首次 prompt 中得到 repository/toolbox 的相关历史 Memory；两种 task 的结果都不含其他客户 repository 或 Default。
6. 已运行 worker 用实际错误、命令和组件取回当前 task 或 repository/toolbox 历史 Memory；没有具体问题时不做运行中搜索。
7. MMW 组装的 reviewer packet 只包含 active Rules，不包含普通 Memory、Thread 或 Working Memory；reviewer 独立运行 acceptance/review checks。
8. 一份 spec 的 closing pass 只处理带该 spec label 的 current Memory；完整读取时 `total == returned` 且每条都有唯一的 retain/propose/deprecate/supersede 决定，`spec.closed` 保存逐项决定、计数与 proposed ids；读取失败或截断明确写 `unchecked`，proposal issue 只由随后的 retro 创建。
9. `summary` 后的 retro 达到门槛时先创建或复用 proposal，再写固定 id 的完整 Retro Memory，最后在当前 spec 写 `spec.retroed result=recorded` 回执；回执只含 Memory id、计数与 proposal links，不重复完整正文。
10. 下一份 spec 的 retro 通过 `mmw-retro` semantic search 取回较早同因问题，再核对其中引用的原 event/commit；两个 specs/nights 的同因 event 在第二次形成一个 proposal，同一事件的多条记录不重复计数。
11. 上一轮 proposal 只有在找到实际落地证据时显示“已落地”，否则显示“没找到证据”。
12. intent reconciliation 同时显示 spec expected surface、实际 observed surface 与 gap/未验证。
13. 两个 `stale reason=invalid` 的同类 finding 形成 reviewer 行为 proposal：repository-specific 内容进入该 repository 的 `AGENTS.md` 或 check，跨 repository 成立的方法才进入 `mmw-reviewer` active Rule；`fixed-elsewhere` 不算 false positive。
14. proposal 在正确 repository 创建，初始 label 为 `needs-triage`；未获 owner 批准不改变 Memory 之外的任何行为机制，retro 重试按 proposal 正文中的 source spec URL 和 evidence URL 复用已有 issue。
15. owner 批准 toolbox 晋升后，原 repository Memory 保留，固定 id `mmw-toolbox-<source-memory-id>` 在所有 shared repository 可搜索；重复执行仍只有一条。
16. owner 批准 repository-local skill 后，代表性任务能从 description 发现并执行完整流程，不相关任务只看到 description；该 skill 不被安装到其他 repository。
17. 隔离测试证明新闭环，而正在运行的 frozen MMW watch 从未读取新版本。

**依据**：本文“共享边界”“阶段二：task 内共享经验”“阶段二收口与阶段三 retro”中的可观察结果。

### 19. 效果指标

| 指标 | 记录位置 | 期望方向 |
| --- | --- | --- |
| worker start 实际注入的当前 task / 历史 Memory 数 | dispatch 输出与 `NIGHT SUMMARY` | 两组分开记录，可核对，不设数量目标 |
| 同一已知问题在一个 task 被第二名 worker 重复修复的次数 | ticket event 与 retro | 下降 |
| retro proposal 的实际落地率 | 下一条 Retro Memory 的 `Previous proposals` | 上升；无证据不计落地 |
| 预防措施落地后同因问题再次出现的次数 | 后续 Retro Memory 及其 source event | 下降至 0 |

不使用 ticket pass rate 证明闭环有效，因为它不能归因于 Memory 或 retro。

**依据**：Artifact 2.3 的 `NIGHT SUMMARY` 计数、Artifact 3.1 的 proposal 落地率，以及 OpenAI/Augment 的重复错误反馈原则。

### 20. 设计边界

以下机制不属于本方案：

- 阶段二、阶段三分别等待两次实施；
- 每个 map/spec 建 Space，或把 Working Memory 改成 task bus；
- 用 ticket title、`## Owns`、整份 spec 或 `--time today` 决定 task scope；
- `dispatch.sh open` 注入、历史检索结果缓存或 reviewer Memory 注入；
- 用 Memory、Thread 或 Working Memory 补 retro 的运行证据；
- 把完整 retro 同时写进 spec comment 与 Mem，或扫描所有旧 spec comments 发现历史问题；
- bootstrap 全量扫描、`occurrence` 数据层、evidence packet、proposal 去重状态机；
- 新建 retro 数据库、relay、轮询、queue 或 approval state machine；
- 自动把 Memory 或 proposal 晋升为 Rule、`AGENTS.md`、check、script、skill 或 `mmw-toolbox`；
- 把一次阶段三问题当作重复问题提案；
- 用 known false positive guideline 静默禁止 reviewer 报告；
- 让新版本 MMW 接管正在运行的 frozen watch。

**依据**：Artifact 的既定机制、Nowledge Mem 的实测能力边界、task root 的 native parent graph，以及根 `AGENTS.md` 的 `Self-hosting boundary`。

## 五、研究依据与采用范围

正文每个设计段落就地标明依据；本节给出可复查的原始实现和 MMW authority。

### Artifact

- [《Project Context 调研与 MMW 方案》](https://claude.ai/code/artifact/b9520c08-eb0d-40f1-872e-228662445954?via=auto_preview)第 5 节“实验结果”、第 6 节“阶段二”、第 7 节“阶段三”和第 9 节“决定”：方案主体，包括当场 capture、worker 派发时检索一次、reviewer 使用 active Rules、Memory closing pass、retro、`needs-triage` 与 owner approval。

### 参考项目

- [monomind project-context `context_capture.py`](https://github.com/monomind-ai-lab/project-context/blob/72a0a22640f4577eddd615c6bd3a4dad2a6473b9/skills/project-context/scripts/context_capture.py) 与 [`context_packet.py`](https://github.com/monomind-ai-lab/project-context/blob/72a0a22640f4577eddd615c6bd3a4dad2a6473b9/skills/project-context/scripts/context_packet.py)：采用当场 capture、provenance 和按相关上下文取回；不用 capsule inbox、approval state、`path@commit` doctor 或文件存储层。
- BMAD-METHOD `bmad-retrospective` @94b6727b：采用 [`workflow.md`](https://github.com/bmad-code-org/BMAD-METHOD/blob/94b6727b00c8316557828c8a8ff2a48ff60d60cc/skills/bmad-retrospective/workflow.md) 与 [`evidence-gathering.md`](https://github.com/bmad-code-org/BMAD-METHOD/blob/94b6727b00c8316557828c8a8ff2a48ff60d60cc/skills/bmad-retrospective/references/evidence-gathering.md) 的 evidence inventory 和来源规则、[`acceptance-verdict.md`](https://github.com/bmad-code-org/BMAD-METHOD/blob/94b6727b00c8316557828c8a8ff2a48ff60d60cc/skills/bmad-retrospective/references/acceptance-verdict.md) 的 dual disposition、[`retro-document.md`](https://github.com/bmad-code-org/BMAD-METHOD/blob/94b6727b00c8316557828c8a8ff2a48ff60d60cc/skills/bmad-retrospective/references/retro-document.md) 的 previous-action verification；不用 sprint-status、独立文档树或团队仪式。
- [Augment Expert Memory](https://docs.augmentcode.com/cosmos/experts-memory)、[Code Review Memory](https://docs.augmentcode.com/cosmos/experts-code-review-memory) 与 [Review Guidelines](https://docs.augmentcode.com/codereview/review-guidelines)：采用强弱信号、review 结果学习、明确 scope，以及把可检索经验与 reviewer 行为规则分开；不用 VFS 或专有 guideline 格式。
- [Devin Session Insights](https://docs.devin.ai/product-guides/session-insights)：支持“工作完成后从真实运行记录提出改进”；MMW 使用 tracker event，不复制 transcript 分析系统。
- [OpenAI Harness Engineering](https://openai.com/index/harness-engineering/) 与 [Codex Best Practices](https://learn.chatgpt.com/guides/best-practices)：采用“同类错误第二次进入长期预防”、把可执行 rule 进入 code/check，以及把稳定的重复流程写成 skill；不用后台 agent 或 quality-score 系统。
- [Agent Skills specification](https://agentskills.io/specification)：采用 `SKILL.md`、按需加载的 progressive disclosure，以及可选的 `scripts/`、`references/`、`assets/` 结构；只用于确实需要重复流程的 repository-local skill。
- [Anthropic AI-native SDLC](https://claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle)：采用“bug class 回到长期指导”的反馈原则；不增加 reviewer 或 shadow mode。
- `mmw-v2/upstream/skills/in-progress/retro/SKILL.md` 的 `## Steps` 与 `### Implementation vs Review`：只复用 Navigation、Automated checks、Coding standards、Global `AGENTS.md`、Tool economy、No-ops 和 Information access 这些改进目的地；分析范围改为一份 spec night 的完整 tracker evidence。

这些参考项目都不包含 MMW 的 GitHub native parent、event fold、`route` 和 frozen runtime，所以本方案扩展现有 MMW 与 Nowledge Mem，不引入另一套工作流。

### MMW 与 Nowledge Mem authority

- [Nowledge Mem Background Intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)、[Spaces](https://mem.nowledge.co/docs/spaces)、[Context](https://mem.nowledge.co/docs/ai-context)、[Customize Integration Behavior](https://mem.nowledge.co/docs/integrations/customize-behavior) 与 [CLI](https://mem.nowledge.co/docs/cli)：Space、Identity、Memory、Thread、Working Memory、Context Bundle、multi-agent 环境路由、shared retrieval 与 CLI 行为。
- `docs/contexts/tickets/CONTEXT.md` 的 `spec`、`ticket`、`sub-issue` 与 `map`，以及 `mmw-v2/skills/verify-ticket/scripts/tree.py` 的 module docstring 和 `LAYERS`：native parent graph 与 task root。
- `docs/contexts/task-board/CONTEXT.md` 的 `The Night`；`docs/contexts/night/CONTEXT.md` 的 `main agent`、`closing pass`、`route`、`summary` 与 `spec.closed`：map 级任务与 spec night 的不同范围。
- `mmw-v2/skills/dispatch/references/night.md` 的 `## 4. The closing pass` 与 `## 5. The night is over`；`mmw-v2/skills/dispatch/scripts/dispatch.sh` 的 `summary_spec()` 与 `route_finding()`；`mmw-v2/skills/dispatch/scripts/status.py` 的 `summary()`、`ROUTES` 与 `routed_counts()`：现有收口流程。
- `mmw-v2/skills/verify-ticket/scripts/events.py` 的 `EVENTS`、`CHILD_RESOLUTIONS` 与 `fold()`；`mmw-v2/upstream/skills/engineering/code-review/references/session.md` 的第 4、5 步：event 与 review finding 合同。
- `docs/agents/issue-tracker.md` 的 `Reading a tree`、`Three label sets`、`Morning queries` 与 `Wayfinding operations`：proposal 的 repository、queue 与发布路径。
- `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md` 的 `Work through the map`、`to-spec/SKILL.md` 的 `Process`、`implement/SKILL.md` 的 read-in 与 `While writing code`：map、spec 与 worker 的现有流程。
- 根 `AGENTS.md` 的 `Self-hosting boundary`：新版本只能在隔离环境验证，不能接管当前 watch。
- 本机 Nowledge Mem Codex connector `hooks/nmem-context.py` 的 `_load_startup_context()` 与 `main()`、Claude/Grok connector 的 `scripts/nmem-hook-read.sh`、Cursor connector 的 `hooks/nmem-runtime.mjs`、Pi connector 的 `extensions/nowledge-mem.ts`：各 connector 消费 `NMEM_SPACE` / `NMEM_AGENT_ID` 的实际路径，以及 Grok startup hook 不注入正文的限制。
