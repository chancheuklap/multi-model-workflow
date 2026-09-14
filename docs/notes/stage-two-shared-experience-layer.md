# 阶段二与阶段三：共享经验和跨夜学习闭环

日期：2026-09-14

对象：[《Project Context 调研与 MMW 方案》](https://claude.ai/code/artifact/b9520c08-eb0d-40f1-872e-228662445954?via=auto_preview)第 6 节“阶段二 · 共享经验层 · NOWLEDGE MEM 自带机制优先”、第 7 节“阶段三 · 跨夜学习”和第 9 节“决定”

性质：阶段二与阶段三共同实施前的研究结论，不修改产品代码

## 方案总览

阶段二与阶段三作为一条反馈闭环共同实施：阶段二让 worker 在同一 task 内直接写入和取得已证实的经验；阶段三在每份 spec 的 `summary` 之后复盘 ticket event 与 `git log`，把跨 ticket 或跨 night 第二次出现的问题，以及一次就实际阻塞工作的 Memory proposal candidate，提议为自动检查、reviewer Rule、repository `AGENTS.md` Gotchas、repository script、repository-local skill、MMW skill 或 `mmw-toolbox` Memory。owner 批准后的结果在后续 worker、reviewer 或检查中生效。

task root 按以下规则解析：spec 有 native map parent 时，map 是 task root；spec 没有 map parent 时，该 standalone spec 自己就是 task root。一个 map 可以拆成多份 spec 并行执行，这些 spec 下的 worker 和 reviewer 使用同一个 task scope；standalone spec 下的全部 ticket 使用该 spec 的 task scope。task root 决定执行时谁共享经验，不限制阶段三在 repository 内识别跨 task、跨 night 的重复问题。

阶段二只有两条读取路径：

1. `dispatch.sh start <ticket> worker` 根据 GitHub native parent 得到 task root，按 task scope label 读取一次当前 task 已有的 Memory，放进 worker 的首次 prompt。
2. worker 遇到具体的非显然故障时，以实际错误、命令和组件主动做 semantic search；先搜当前 task，仍没有答案时再搜当前 repository Space 和已批准的 `mmw-toolbox`。

worker 一旦证实一条同一 task 其他 ticket 可复用的经验，就立即写入 repository Space，并带当前 task root 的 scope label。后来启动的 worker 会自动得到它；已经运行的 worker 在遇到相同问题时通过主动检索得到它。

reviewer 的首次 prompt 不放 Memory 检索结果；`dispatch.sh start <ticket> reviewer` 从 `mmw-reviewer` Context Bundle 中只取 active `rule_stack`，作为唯一由 MMW 加入 review 的经验。reviewer 独立读取 ticket、repository authority 和运行检查。这符合 Artifact 对 reviewer 干净上下文的设计，也不依赖各 host 是否能把 startup hook 输出送进模型。

不增加实时消息系统、Memory relay、retro 数据库或新的审批队列。必须立即改变其他 ticket 行为的信息继续使用现有 `contract`、`fault` 或 `decision` tracker event。retro 使用一个 script-written `spec.retroed` event 留在 spec comment 中；proposal 先进入现有 `needs-triage` 队列，owner 决定是否落入长期载体。

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
- `dispatch.sh open <spec>` 幂等建立当前 repository Space；已有正确 Space 时不重建，但不把 Memory 注入 main prompt。
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
| `memories search` | semantic + text search，约 0.5 秒；可按 label、unit type、时间和 metadata 过滤；active Space 为 `shared` 时扩到显式 shared Spaces | agent 按真实问题主动找经验 |
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

`start` 在调用 runner adapter 前完成一次当前 task 读取：

1. 从 ticket 的 native parent 得到 spec，再从 spec 的 native parent 得到 `map:<n>` 或 standalone `spec:<n>`；
2. 得到当前 repository Space；
3. 用唯一 task scope label 列出当前 task 已写入的显式 Memory；
4. 把结果放进 worker 的首次 prompt。

```sh
nmem --json memories list \
  --space "$NMEM_SPACE" \
  --label "$MMW_EXPERIENCE_SCOPE" \
  --limit 1000
```

`dispatch.sh` 比较返回值的 `total` 与 `returned`。相等才算完整读取；`total > returned` 时仍启动 worker，但首次 prompt 明确写出“当前 task Memory 已截断”，不能把前 1000 条伪装成完整结果。本机 CLI 没有 `offset`，因此不另造分页层；一个 task 达到这个上限时应治理其 Memory，而不是继续扩大启动 prompt。

这里只使用一个 scope label。本机实测 `memories list` 的重复 `--label` 是 OR，不是 AND；因此所有带 task scope label 的 Memory 都必须是共享经验，`mmw-experience` 只用于 worker 按具体问题搜索历史。

首次 prompt 的固定部分只包含：

```text
MMW task root: map #384
MMW task scope: mmw-map-384
Current task shared experience:
- <memory id> — <title>
  <content>
  Source: <source>

When an unexplained failure is not covered above, search with the exact error,
command and component. Verify every Memory against current repository evidence.
```

这一步不用 ticket title、`## Owns`、`--time today` 或整份 spec 作为检索输入，也不增加第二次 historical seed。新 task 没有 scoped Memory 时结果就是 0；真正遇到问题后再按“worker 遇到问题时主动搜索”处理，避免把仅仅“可能相关”的内容预先塞给 worker。

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

worker 另收到 `MMW_EXPERIENCE_SCOPE`、`MMW_SPEC` 与 `MMW_TICKET`，供主动搜索和写入使用。runner 的 `start` 合同增加可重复的 `--env KEY=VALUE`：Paseo 转发给现有 `paseo run --env`，Herdr 转发给现有 `herdr tab create --env`，Orca 把同一组值放进新 terminal 的 host launch environment。Space、Identity 和 scope 仍由 `dispatch.sh` 解析，adapter 只传值。

**依据**：Artifact 2.2“当夜由派发脚本查一次”；现有 `dispatch.sh read_ticket()` 与 runner adapters；task root 解析沿用上一节的 native parent graph。

### 4. worker 遇到问题时主动搜索

worker 只在一个明确时刻主动检索：命令或工具出现 ticket、repository 文档和当前 task 经验都没有解释的行为，在尝试 workaround 之前。

先查当前 task：

```sh
nmem --json memories search \
  "<exact error + command + component>" \
  --space "$NMEM_SPACE" \
  --label "$MMW_EXPERIENCE_SCOPE" \
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
  --label "$MMW_EXPERIENCE_SCOPE" \
  --label "mmw-spec-$MMW_SPEC" \
  --label "mmw-ticket-$MMW_TICKET" \
  --title "<searchable title>"
```

stdin 使用 Artifact 2.1 的五个字段：

```text
Applies: <适用的环境、版本或前提>
Finding: <已证实的非显然事实>
Action: <下一名 worker 应采取的操作>
Evidence: <命令与输出首行，或 path:line>
Observed: <YYYY-MM-DD>
```

`Applies` 防止旧环境经验被无条件套用，`Action` 让下一名 worker 可以直接行动，`Observed` 保留时间判断；不另造 provenance schema。默认 unit type 是 `learning`；固定操作步骤使用 `procedure`。适合写的是不稳定测试、工具的非显然行为、环境修法和测试前提。普通实现细节、ticket 状态、未经验证的推测、用户决定、凭据和客户数据不写。Space、Identity、task/spec/ticket labels 已提供 repository、角色和工作来源。

同一事实发生变化时不覆写历史：新 Memory 已证实旧 Memory 错误时使用 supersede；旧经验只是不再适用时使用 deprecate。普通 repository Memory 的写入与纠正不等待 owner 批准，因为等待会使并行 agent 继续重复遇到同一问题。

**依据**：Artifact 2.1；monomind project-context `context_capture.py` 的当场 capture 与 provenance；Augment Expert Memory 的 evidence log 与“代码可推得则不存”。

### 6. map 下并行 spec 的传播

以 map `#384` 下并行的 spec A、spec B 为例：

```text
spec A worker 启动
  → dispatch 注入 label=mmw-map-384 的当前 task Memory
  → worker 证实一个非显然工具行为
  → 立即写 Memory(labels: mmw-experience, mmw-map-384)

spec B worker 稍后启动
  → native parent 同样解析为 map #384
  → dispatch 的一次 task 读取直接取得新 Memory

spec B worker 已经在运行
  → 遇到同一错误
  → 用错误、命令、组件搜索 mmw-map-384
  → 取回 spec A 的 Memory
```

另一个 map 不进入 task-scoped 列表；以后只有在 worker 遇到具体相同问题并主动查 repository 历史时，才可能按 relevance 取回这条经验。standalone spec 使用相同路径，scope 改为 `mmw-spec-<n>`。reviewer 不在这条 Memory 传播路径中。

**依据**：task root 的 native parent graph，以及前述 worker 注入、搜索和写入路径。

### 7. Memory 与 tracker event 的分工

Memory 只承载“怎么做、踩过什么坑、什么非显然前提已被证实”。它不承载 ticket state、依赖、`## Owns`、acceptance 结果、spec 修订或必须马上执行的指令。

当 worker A 发现的信息必须立即改变 worker B 的行为时：

- contract 不适配：现有 `contract` child；
- pipeline 本身故障：现有 `fault` child；
- 需要 owner 选择：现有 `decision` child。

relay 继续只由 tracker event 唤醒 agent。Memory 不产生 wake，也不参与 gate。

**依据**：Artifact 2.1 与第 9 节“经验不经票事件”；`mmw-v2/skills/verify-ticket/scripts/events.py` 的 event fold。

### 8. reviewer 的独立性

reviewer 的开场 prompt 不放 worker 或 repository Memory 的检索结果，`code-review` 也不要求 reviewer 主动搜索普通 Memory。需要常驻的 review 经验只以 owner 已批准并编译进 `mmw-reviewer` Context Bundle 的 active Rules 提供；`dispatch.sh` 从 `rule_stack` 取出这些 Rules，保证所有 runner/host 得到相同 review packet。

reviewer 仍独立读取 ticket、spec、repository authority 与 diff，并重新运行它负责的检查。worker Thread、推理、自评和“实现正确”的结论都不进入 reviewer。connector 自动提供的 repository Working Memory 只作宽背景，不能作为 finding 或 verdict 的证据；MMW 自己组装的 review packet 不包含它。需要让以后每次 review 都执行的稳定方法，先由 retro 提议，owner 批准后再成为 active Rule。

这保留了 Artifact 2.2 的角色边界，也与 Cognition、LangChain 的 clean verifier context 一致。

**依据**：Artifact 2.2“角色”；`research-4-theory.md` 的 `A14. 验证者用干净上下文`；Augment Review Guidelines。

### 9. Thread、Working Memory 与跨夜检索

跨夜信息通过三条彼此独立的路径进入 agent；只有第一条和第二条是阶段二的确定路径。

#### 同一 task 的显式送达

Memory 写入 repository Space 后会一直保留，不因 night 结束而消失。下一夜如果启动的 worker 仍属于同一 task root，`dispatch.sh start <ticket> worker` 会按 `mmw-map-<n>` 或 `mmw-spec-<n>` 执行 `memories list`，把完整结果直接写进首次 prompt。这是“跨夜记忆给到 agent”的主要路径，也是唯一不要求 agent 先意识到问题的历史 Memory 路径。

#### 不同 task 的按需检索

新 task 不自动继承旧 task 的 Memory。worker 真正遇到未解释的错误后，以错误、命令和组件执行 `memories search --space <repository> --label mmw-experience`；repository Space 的 shared retrieval 同时搜索本 repository 与 `mmw-toolbox`，但不搜索其他客户 repository 或 Default。命中的旧 Memory 被当前证据核实后使用。这条路径跨 task、跨 map、跨 night，但不会把大量“可能相关”的历史预先注入 prompt。

#### connector 的自动 Context Bundle

支持 session-start 注入的 Nowledge connector 会使用 runner 提供的 `NMEM_SPACE` 和 `NMEM_AGENT_ID` 读取 Context Bundle。自动注入的是：owner/agent Identity 摘要、active Space、适用的 active Rules，以及该 repository Space 当前的一份 Working Memory。它**不会**自动注入任意历史 Memory 的检索结果，也不会把上一夜的完整 Thread 直接放进新会话。

Working Memory 是整个 repository 的异步简报，可能同时包含多个 map 和 standalone spec，不能按 task root 过滤。Claude Code、Codex、Cursor 与 Pi 的 connector 可以在 session start 提供 Context Bundle，但各自有 fallback 差异；Grok 的 passive `SessionStart` 不把正文交给模型。因此本方案只把它当作可选的跨夜宽背景，不用它证明 task Memory 已送达。reviewer 所需的 active Rules 仍由 `dispatch.sh` 读取 `context read --no-working-memory` 后明确放进 review packet，避免 host 差异。

session 结束或 compact 时，已启用的 connector 可以把会话保存为 repository Thread。Thread 是可审计的会话记录；Nowledge 后台以后可能从中蒸馏 Memory 并刷新 Working Memory，但这个过程异步且不保证完成。Thread 本身不自动注入下一名 agent，也不承担同夜或跨夜的确定送达。

所以本方案对 Mem 自动能力的利用只有两项：用 Context Bundle 提供非关键的 repository 宽背景；用 connector capture 保留可供后台整理的 Thread。真正影响工作行为的经验仍走 `dispatch.sh` 的 task Memory 注入、worker 的按需 search 和 reviewer 的 active Rules 注入。阶段二不自建 Thread 摘要器、Working Memory patch、map Working Memory或实时同步层。

**依据**：Artifact 2.1、2.2；Nowledge Mem `Background Intelligence` 与 `Context`。

## 三、阶段二收口与阶段三 retro

### 10. 从 closing pass 到 retro

#### 现有起点

- `mmw-v2/skills/dispatch/references/night.md` 的 `## 4. The closing pass` 要求 main agent 读取本 spec 的每张 ticket，把每个 `finding` 以 `fixed`、`stale` 或 `became-ticket` 路由；`dispatch.sh summary <spec>` 在仍有未路由 finding 时拒绝关闭 night。
- `dispatch.sh summary <spec>` 当前只生成 `NIGHT SUMMARY`、写入 `spec.closed` 并停止该 spec 的 relay。它没有 retro，也不会比较更早的 spec 或 night。
- 每个 ticket 的 comment 中已经有完整的 script-written event fold；`ticket.bounced`、`ticket.returned`、`worker.lost`、`reviewer.reported`、`child.opened`、`child.closed` 和 `ticket.checked` 足以作为第一版 process evidence，不需要先保存全部 agent transcript。
- reviewer comment 已固定分成 `Standards`、`Spec`、`Tests` 三个 axis，并将 finding 分成 `In-ticket` 与 `Out-of-ticket`。但每条汇总行只有 axis、path、line 与自由文本 claim，缺少可稳定聚合的 finding category。
- 当前 `route ... stale` 只说明 finding 在 `HEAD` 已不成立，没有区分“原 finding 本来就是误报”和“finding 曾经成立但被其他 ticket 修复”。阶段三不能把两者混成 reviewer false positive。
- `git log` 能给 closing pass 自行修复、ticket merge、proposal 后续落地和当前 base revision 提供独立证据；它不能单独说明 agent 为什么失败，所以原因仍以 event、finding body 和 review comment 为准。

#### 收口顺序

小写 `night` 是 `dispatch.sh` 对一份 spec 的一次运行。closing pass 按 `mmw-spec-<n>` 列出本 spec night 写入的 Memory，逐条执行 Artifact 2.3 的三选一：

1. **retain**：仍正确、仍适用，原 Memory 保持不变；
2. **propose**：同类经验已独立出现两次以上，或一次就实际阻塞 ticket，标成长期载体 proposal candidate；
3. **deprecate**：已有证据说明不再适用，用 Nowledge Mem deprecate 并写原因；若新事实替代旧事实，使用 supersede。

这一步只处理经验本身，不把 Memory 当作阶段三的运行证据。main agent 把逐条决定写入临时 JSON manifest，并调用 `dispatch.sh summary <spec> --memory-decisions <file>`；每项只有 `memory_id`、`decision=retain|propose|deprecate|supersede` 与 `reason`，`supersede` 另带 `replacement_id`，`propose` 另带证明“重复出现”或“实际阻塞”的 event/commit URL。`summary` 自己重新列出 `mmw-spec-<n>`，完整读取时要求 manifest ids 与 current Memory ids 完全一致，再执行 lifecycle 操作。

`spec.closed` 的 `NIGHT SUMMARY` 保存逐条 decision manifest，并给出 `written / retained / proposed / deprecated / superseded` 计数及 proposed Memory ids；它是 closing pass 与 retro 的机器交接记录。`retain` 不调用 Mem 写接口，其他决定只有对应接口成功后才计数。Nowledge unavailable、JSON 不可读或 `total > returned` 时按既定 fail-open 关闭 night，但 `spec.closed` 必须写 `Memory closing: unchecked (<reason>)`，不能写成 0 或完整盘点。

`summary` 成功写入 `spec.closed` 后，同一 main agent 立即运行 retro。retro 是 proposal issue 的唯一创建点：它接收 closing pass 的 proposed Memory ids，并与本次 event/commit finding 合并；同一原因只创建一个 issue。Memory candidate 可以按 Artifact 2.3 的“一次实际阻塞”成立，阶段三 finding 仍必须满足“两次独立出现”。retro 以一个 script-written `spec.retroed` event 写在该 spec comment 中。它不改变 `spec.closed`，不持有任何 agent，也不触发 relay。

**依据**：Artifact 2.3、3.1；`mmw-v2/skills/dispatch/references/night.md` 的 `## 4. The closing pass` 与 `## 5. The night is over`；现有 `dispatch.sh summary <spec>`。

### 11. retro 的范围与证据

#### 三个范围

| 范围 | 固定定义 | 作用 |
| --- | --- | --- |
| 本次复盘 | 当前刚完成的 spec night | 决定本次新增哪些 finding |
| 阶段二共享 | task root：`map if present, otherwise spec` | 决定哪些 worker 立即共用 Memory |
| 历史比较 | 当前 repository 的较早 `spec.retroed` events | 发现跨 ticket、跨 spec、跨 task 和跨 night 的重复问题 |

每份 spec 完成后各自运行一次 retro。map 内先完成的 spec 立即留下 `spec.retroed`；后完成的 sibling spec 可以把它作为 repository 历史。没有 map-level retro 或等待全部 sibling 的 gate。

#### 输入及其用途

| 输入 | 来源 | 能证明什么 |
| --- | --- | --- |
| 本次完整 ticket 集合 | `tree.py <spec> --root spec` | 哪些 ticket 与 child 必须读取 |
| process 与最终结果 | 每张 ticket 的完整 event fold及其 script-written comment | bounce、return、lost、HANDOFF、finding、route、check 与最终结果 |
| 实际落地 | 本批 merge、closing-pass fix 与 base branch `git log` | 哪些改变确实进入 repository |
| 历史重复与上一轮行动 | 较早的 `spec.retroed` event 及其链接的 issue，再用 commit、Rule、Memory 或现行文件复核 | 同类问题是否已出现、已提议的预防是否真正落地 |
| Memory promotion candidate | 当前 `NIGHT SUMMARY` 的 proposed Memory ids | 只决定是否提出长期载体，不证明运行中发生了什么 |
| 交付意图 | 当前 spec 的 `Problem Statement`、`User Stories`、`Out of Scope` | 仅用于 expected surface，不证明实现发生了什么 |

retro 的运行事实只接受 event 或 commit source。review finding 的 path、claim 与 category 来自承载 `reviewer.reported` event 的 comment；spec 只定义批准的意图。Memory、Thread、Working Memory、agent 自评和无输出推断都不能补成运行证据。

第一版不扫描阶段三启用以前的全部 closed specs，也不建立 bootstrap baseline。跨 night 计数从 `spec.retroed` 开始，避免为了追溯旧夜再造迁移、索引或缓存。读取失败的来源明确写“未检查”，不能写成“没有发生”。

**依据**：Artifact 3.1；BMAD-METHOD `bmad-retrospective/workflow.md` 与 `evidence-gathering.md` 的来源规则。

### 12. retro 怎样形成 finding 和 proposal

#### 从证据到 finding

retro 不建立独立 `occurrence` 数据层。每条 finding 直接写在 `spec.retroed` 的人可读正文中，包含：

- 支持它的 ticket event 或 commit 链接；
- 本例已经怎样处理；
- 怎样防止下一次，以及应落入哪个现有载体。

同一事件同时出现在 review comment、child 与 route 中仍只算一次。相同 path、相似标题或同一个宽类别都不能单独证明是同一原因。

#### 形成 proposal 的条件

阶段三只把跨 ticket 或跨 night 独立出现两次以上的同类问题列为 proposal，范围限于 Artifact 3.1 明列的四类：

- 相同 `ticket.bounced` 原因；
- 相同 `HANDOFF REQUIRED` 原因；
- 相同 review finding category；
- 相同环境问题被重复修复。

proposal 必须引用两次独立的 event/commit source。一次问题即使严重，也不由 retro 推成阶段三 proposal；它按现有 fault、contract、finding 或 ticket 路径处理。Artifact 2.3 的“单次实际阻塞也可 propose”只适用于“从 closing pass 到 retro”中的 Memory promotion。

#### 上一次行动项

retro 先核最近一份 `spec.retroed` 中的 proposal。能指出实际 commit、active Rule、Memory id 或现行文件位置才写“已落地”；找不到这种证据就写“没找到证据”。issue 关闭本身不等于预防措施已生效。

#### intent reconciliation

只做描述性对照：从 `Problem Statement` 与 `User Stories` 取得 expected surface，从 ticket checks 与实际运行证据取得 observed surface，再与 `Out of Scope` 对照。它报告一致、偏离或未验证，不自行增加功能，也不自动改 spec。

#### review learning

review finding 增加一个稳定 category。`route … stale` 同时记录：

- `invalid`：finding 从一开始就不成立；
- `fixed-elsewhere`：finding 曾成立，但当前 `HEAD` 已由其他 ticket 或 closing-pass fix 修复。

同一 category 的 `invalid` 两次，提议一条 reviewer Rule；同类真实缺陷两次，提议 anti-pattern 或自动检查。`fixed-elsewhere` 不计作 false positive。category 只用于聚合，具体 proposal 仍需引用 finding 的 path、claim 与处置证据。

**依据**：Artifact 3.1；BMAD `acceptance-verdict.md` 的 dual disposition 与 `retro-document.md` 的 previous-action verification；OpenAI Codex Best Practices 的“同类错误第二次进入长期预防”；Augment Code Review Memory。

### 13. `spec.retroed`、owner 决定与长期载体

#### `spec.retroed` event

retro script 在 spec 上写一条现有 event 格式的 comment：

```text
NIGHT RETRO
Evidence checked: <ticket events and commit range>
Previous actions: <已落地 | 没找到证据>
Repeated problems: <two or more sourced findings, or none>
Intent reconciliation: <expected / observed / gap>
Review learning: <proposal or none>
Proposals: <issue links or none>

<!-- mmw {"v":1,"event":"spec.retroed","stage":"night","actor":"main",...} -->
```

每条 finding 的正文带 source；无 event/commit source 的内容不写。`spec.retroed` 是 repository 内可折叠、可读取的 event，不增加 status、hold、wake 或 gate。

#### proposal issue

proposal 创建在应承担改变的 repository：MMW 或 toolbox 行为开在 multi-model-workflow，consumer-local 问题留在该 consumer repository。新 issue 加现有 `needs-triage` queue label，不加 `mmw:map/spec/ticket/child` layer label；spec event 链接 proposal，proposal 回链来源 spec 和两次独立证据。

proposal body 带稳定的 source spec 与 evidence marker。retro 创建前用这两个 marker 查询已有 open/closed proposal；命中时复用其链接，不再创建。这样即使 issue 已创建而 `spec.retroed` 尚未写入，重跑也不会重复开票，不需要 proposal 数据库或新状态机。`spec.retroed` 已存在时再次运行是 no-op。

proposal 只写 Artifact 要求的内容：本例如何处理、怎样防下一次、目标载体、来源。它不直接修改长期载体，也不阻止 night 结束。owner 批准后，需实现的改变走现有 `to-spec`、`to-tickets`、worker、review 和 landing 流程；owner 拒绝则按现有 triage 结果处理，不建立新的审批状态。

#### owner 批准后的长期载体

| 问题性质 | 目的地 | 后续怎样生效 |
| --- | --- | --- |
| 可机械判断 | `.mmw/target.json`、judge、lint、ticket `CHECK:` 或 repository script | 运行或验收时直接检查 |
| repository 通用且代码无法推出 | repository `AGENTS.md` 的 Gotchas | 后续 agent 读 repository authority |
| repository 特有的重复工作方法 | repository-local skill：`SKILL.md`，按需附带 `scripts/`、`references/` 或 `assets/` | description 负责发现；只有任务匹配时才加载并执行完整流程 |
| reviewer 的稳定方法 | `mmw-reviewer` active Rule | `dispatch.sh start <ticket> reviewer` 从 Context Bundle 的 active `rule_stack` 注入 |
| MMW pipeline 行为 | 对应 MMW skill、reference 或 script | 新版本安装后的 night 使用 |
| 跨 repository 有用但不应强制 | 在 `mmw-toolbox` 新建一条泛化后的 Memory，正文回链原 Memory id | repository shared retrieval 按需取得；原 repository Memory 不移动 |
| 不够稳定或不够通用 | 原 repository Memory | 保持可搜索，不升格 |

能机械执行的内容优先进入 check 或 script；只有无法从代码推得且几乎每项任务都适用的短规则才进入 `AGENTS.md`。repository-local skill 用于另一类内容：方法只属于当前 repository，会在多张 ticket 中重复，并且需要多个有顺序的步骤、工具调用、模板或可执行辅助文件；它不该让每个 agent 永久背在 prompt 中，也不值得进入所有 repository 共用的 MMW skill。若内容只是一个事实或偶尔有用的提示，继续留在 repository Memory；若能直接判定对错，写 check/script，不为它包一层 skill。

repository-local skill 只有在 proposal 证明该流程已独立出现两次，或一次就实际阻塞工作且同一 repository 后续还会复用，并能写出明确触发条件、输入、输出和 `Done when` 时才生成。owner 批准后仍走正常 ticket 实现和 review；retro 本身不自动生成 `SKILL.md`。文件放进 consuming repository 已采用的 skill root；没有既有 root 时，实现 ticket 按 Agent Skills 的 `SKILL.md` 标准建立 repository-local skill，并验证当晚选定的 host 能发现它。MMW pipeline 自身的操作才进入 MMW repository 的 skill、reference 或 script。

这些选择来自 Agent Skills 的 progressive disclosure、OpenAI Harness Engineering 与 Augment 的 AGENTS.md/Review Guidelines，不扩展为新的 `CONTEXT.md`、ADR、coding-standard 层或治理系统。

Rule 与 toolbox Memory 直接使用现有 Nowledge 接口：

```sh
nmem --json rules upsert <rule-id> \
  --scope agent --agent mmw-reviewer --status active \
  --title "<title>" --body "<approved body>"

nmem --json memories add --stdin \
  --id "mmw-toolbox-<source-memory-id>" \
  --space mmw-toolbox --source mmw-promotion \
  --unit-type learning --label mmw-experience \
  --label mmw-toolbox-approved \
  --title "<approved generalized title>"
```

toolbox Memory 的正文保留 `Source Memory: <id>`、source proposal URL 与原 repository slug，但只写 owner 批准的通用表述。固定目标 id 让同一 source Memory 的重试更新原目标，而不是生成重复项。`memories move` 不用于这里：实测它会让原 repository 不再持有该 Memory；新建记录既保留 task 内原始证据，又避免把 repository-specific 正文原样暴露给其他 repository。

#### 回流到下一次阶段二

```text
worker 写/读 task Memory
  → closing pass：retain / propose / deprecate
  → summary 写 spec.closed
  → retro 写 spec.retroed，并对重复问题开 needs-triage proposal
  → owner 批准后由现有 ticket 流程落入长期载体
  → 后续 worker、reviewer 或 check 使用
  → 后续 retro 以证据判断是否仍重复
```

**依据**：Artifact 2.3、3.1 与第 9 节“决定”；`docs/agents/issue-tracker.md` 的 `Three label sets`、`Morning queries` 与现有发布流程；OpenAI Harness Engineering；Augment AGENTS.md/Review Guidelines。

## 四、实施与证明

### 14. 当前缺口

- 本机 CLI/server 是 `0.10.78`；本文只使用这个本机版本已实测的接口。
- Spaces 功能已经启用，目前只有 Default；repository Spaces、`mmw-toolbox` 和 MMW Identities 尚未建立。
- 当前只有 `default` Identity；active Rules 为 0，已有 Rule 全部是 draft。
- MMW 目前只由 `install.sh` 配置 Cursor 的 Nowledge MCP；dispatch、implement 和 runner adapter 里还没有阶段二路由。
- `to-spec` 已允许一个 map 拆成多份 specs，但发布步骤尚未明确保证这些 specs 是 map 的 native children。

**依据**：本机 `nmem 0.10.78` 实测；现有 `install.sh`、`dispatch.sh`、runner adapters 与 `to-spec/SKILL.md`。

### 15. 阶段三必须补齐的五个结构化接口

阶段二沿用 Nowledge Mem 的 Space、Identity、Memory、Context Bundle 与 Rules 接口；阶段三只补齐以下五个 MMW 结构化接口：

1. 从 map 发布 spec 时，把 spec 创建为该 map 的 native child，并在 read-back 验证 `parent.number`；standalone spec 保持无 map parent。
2. review finding 汇总行增加稳定 category，同时保留现有 axis、path、line 和 claim。
3. `child.closed resolution=stale` 增加 `reason=invalid|fixed-elsewhere`，resolution 本身不变。
4. `events.py` 增加 `spec.retroed`；它不进入 hold、relay 或 ticket verdict。
5. retro proposal 使用现有 `needs-triage` queue 和现有 issue tracker，不增加 layer、queue 或私有审批表。

`## Sources`、map 的 `## Specs`、ticket title 和 `## Owns` 都是人可读记录或执行切片，不能替代 native parent 与 structured outcome。

**依据**：现有 `to-spec`、review comment、`route`、`events.py` 与 issue tracker 合同。

### 16. 实施顺序

阶段二与阶段三作为一个 spec，按同一依赖链实施。

#### A. Space、Identity 与现有 dispatch

1. `mmw-v2/install.sh` 幂等建立 `mmw-toolbox`、`mmw-worker` 与 `mmw-reviewer`，`--check` 只读核对。
2. 在现有 `dispatch.sh` 内增加 Nowledge helper：建立或读取 repository Space、解析 `nmem --json`、按 task/spec label 列举、读取 reviewer active `rule_stack`，并区分 unavailable 与 0 results。worker 仍直接使用 Nowledge CLI 搜索与写 Memory，不增加中间服务或新 adapter module。

#### B. 阶段二读写

3. `dispatch.sh` 解析 native parent，并通过 runner `start --env` 设置 Space/Identity；三个 runner adapter 只把值送入实际 agent process。worker start 读取一次 task Memory 并核对 `total == returned`；reviewer start 只读取 active `rule_stack`；`summary --memory-decisions` 校验逐项 manifest，并把完整决定写入 `spec.closed`。
4. `implement/SKILL.md` 增加 Artifact 2.1 的五字段写入条件与 2.2 的主动搜索时点；`code-review` 不增加 Memory retrieval，只使用 prompt 中的 active Rules。
5. `to-spec/SKILL.md` 在 map 来源时创建 native child 并 read back；standalone spec 不虚构 parent。

#### C. 阶段三 retro

6. `code-review` 的汇总合同增加 category；`route … stale` 增加 `invalid|fixed-elsewhere` reason。
7. `events.py` 增加一个无 hold、无 wake 的 `spec.retroed` event；night runbook 在成功 `summary` 后执行 retro。
8. 新增 `mmw-v2/skills/retro/SKILL.md` 与一个脚本入口。脚本读取当前 spec tree、ticket event、相关 `git log`、较早 `spec.retroed` 和 `spec.closed` 的 proposed Memory ids，按 source spec/evidence marker 复用已有 proposal，写本次 event，并作为唯一入口创建 `needs-triage` proposal。它不把 Memory、Thread 或 Working Memory 当作运行证据，也不写长期载体。

#### D. owner approval 与证明

9. 批准后的改变继续走现有 triage、`to-spec`、`to-tickets`、worker、review、closeout 和 landing；生成 repository-local skill 时验证触发、完整流程与当晚 host 的发现结果，新建 toolbox Memory 或激活 Rule 时在 proposal 留下实际 id。
10. 按 repository 规则更新 Tickets/Night/Memory contexts、dispatch reference、upstream merge-note 和必要的 downstream-note。
11. 测试覆盖 install、dispatch、runner、map/standalone scope、review category、stale reason、retro event、proposal repository/label 和跨 night 重复。

实现顺序是 A → B → C → D。所有验证使用隔离 `MMW_HOME`、假 tracker、临时 Git repository 和临时 Nowledge objects；当前 frozen runtime 不读取新版本。

**依据**：Artifact 3.1；`mmw-v2/upstream/skills/in-progress/retro/SKILL.md`；根 `AGENTS.md` 的 `Self-hosting boundary`。

### 17. 不可用时的行为

- Nowledge Mem 读取或写入失败时，worker 照常执行 ticket，输出具体失败原因；Memory 从不改变 acceptance、review 或 landing verdict。
- native parent 读不到时，不猜成 standalone spec，也不扩大到 repository scope；本次 worker 不注入或写 task-scoped Memory，并报告 routing 未完成。
- retro 的某项 event/git source 读不到时，`spec.retroed` 明确写“未检查”；不能把 unreadable 当 0，也不能用该来源形成 proposal。

这些行为只让“查询失败”和“查到 0 条”可区分，不增加 retry state、补偿事务或新的 gate。

**依据**：Artifact 2.1 的 fail-open；MMW ADR 0008 的 refusal 语义。

### 18. 验收

1. 一个 map 下两份 specs 的 workers 解析成同一 task scope；standalone spec 使用自己的 scope。
2. repository A 只能搜索自身与 `mmw-toolbox`，看不到 repository B 或 Default。
3. runner 实际启动的 agent process 收到 `NMEM_SPACE` 与对应 `NMEM_AGENT_ID`；显式 worker Memory 进入当前 repository Space，已启用 connector 时 worker/reviewer Thread 也进入该 Space。
4. spec A worker 写入 task Memory 后，稍后启动的 spec B worker 在一次 task 读取中得到它；reviewer prompt 不包含它。
5. 已运行 worker 用实际错误、命令和组件取回 current-task 或 repository/toolbox 历史 Memory；没有具体问题时不搜索。
6. MMW 组装的 reviewer packet 只包含 active Rules，不包含普通 Memory、Thread 或 Working Memory；reviewer 独立运行 acceptance/review checks。
7. 一份 spec 的 closing pass 只处理带该 spec label 的 current Memory；完整读取时 `total == returned` 且每条都有唯一的 retain/propose/deprecate/supersede 决定，`spec.closed` 保存逐项决定、计数与 proposed ids；读取失败或截断明确写 `unchecked`，proposal issue 只由随后的 retro 创建。
8. `summary` 后写出一个 `spec.retroed` event；每条运行 finding 都能跳到 ticket event 或 commit。
9. 两个 specs/nights 的同因 event 在第二次形成一个 proposal；同一事件的多条记录不重复计数。
10. 上一轮 proposal 只有在找到实际落地证据时显示“已落地”，否则显示“没找到证据”。
11. intent reconciliation 同时显示 spec expected surface、实际 observed surface 与 gap/未验证。
12. 两个 `stale reason=invalid` 的同类 finding 形成 reviewer Rule proposal；`fixed-elsewhere` 不算 false positive。
13. proposal 在正确 repository 创建，初始 label 为 `needs-triage`，未获 owner 批准不改变任何长期载体；retro 重试按 source spec/evidence marker 复用已有 proposal。
14. owner 批准 toolbox 晋升后，原 repository Memory 保留，固定 id `mmw-toolbox-<source-memory-id>` 在所有 shared repository 可搜索；重复执行仍只有一条。
15. owner 批准 repository-local skill 后，代表性任务能从 description 发现并执行完整流程，不相关任务只看到 description；该 skill 不被安装到其他 repository。
16. 隔离测试证明新闭环，而正在运行的 frozen MMW watch 从未读取新版本。

**依据**：本文“共享边界”“阶段二：task 内共享经验”“阶段二收口与阶段三 retro”中的可观察结果。

### 19. 效果指标

| 指标 | 记录位置 | 期望方向 |
| --- | --- | --- |
| worker start 实际注入的 task Memory 数 | dispatch 输出与 `NIGHT SUMMARY` | 可核对，不设数量目标 |
| 同一已知问题在一个 task 被第二名 worker 重复修复的次数 | ticket event 与 retro | 下降 |
| retro proposal 的实际落地率 | 下一次 `Previous actions` | 上升；无证据不计落地 |
| 预防措施落地后同因问题再次出现的次数 | 后续 `spec.retroed` | 下降至 0 |

不使用 ticket pass rate 证明闭环有效，因为它不能归因于 Memory 或 retro。

**依据**：Artifact 2.3 的 `NIGHT SUMMARY` 计数、Artifact 3.1 的 proposal 落地率，以及 OpenAI/Augment 的重复错误反馈原则。

### 20. 设计边界

以下机制不属于本方案：

- 阶段二、阶段三分别等待两次实施；
- 每个 map/spec 建 Space，或把 Working Memory 改成 task bus；
- 用 ticket title、`## Owns`、整份 spec 或 `--time today` 决定 task scope；
- `dispatch.sh open` 注入、worker start 的第二次 historical seed、reviewer Memory 注入；
- 用 Memory、Thread 或 Working Memory 补 retro 的运行证据；
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
- [BMAD-METHOD `bmad-retrospective` @94b6727b](https://github.com/bmad-code-org/BMAD-METHOD/tree/94b6727b00c8316557828c8a8ff2a48ff60d60cc/skills/bmad-retrospective)：采用 `workflow.md` 与 `evidence-gathering.md` 的 evidence inventory 和来源规则、`acceptance-verdict.md` 的 dual disposition、`retro-document.md` 的 previous-action verification；不用 sprint-status、独立文档树或团队仪式。
- [Augment Expert Memory](https://docs.augmentcode.com/cosmos/experts-memory)、[Code Review Memory](https://docs.augmentcode.com/cosmos/experts-code-review-memory) 与 [Review Guidelines](https://docs.augmentcode.com/codereview/review-guidelines)：采用强弱信号、review 结果学习、明确 scope 和稳定长期载体；不用 VFS 或专有 guideline 格式。
- [Devin Session Insights](https://docs.devin.ai/product-guides/session-insights)：支持“工作完成后从真实运行记录提出改进”；MMW 使用 tracker event，不复制 transcript 分析系统。
- [OpenAI Harness Engineering](https://openai.com/index/harness-engineering/) 与 [Codex Best Practices](https://developers.openai.com/codex/learn/best-practices)：采用“同类错误第二次进入长期预防”和“可执行 rule 进入 code/check”；不用后台 agent 或 quality-score 系统。
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
