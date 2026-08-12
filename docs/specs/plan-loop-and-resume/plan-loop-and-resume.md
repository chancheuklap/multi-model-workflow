# plan 批次循环与恢复原生产者 spec

> 本 spec 来自当前对话：对上游 superpowers plugin（obra/superpowers，2026-07-24 改版）与 mattpocock/skills（提交 `84fdeffd`）的调查，加上对 MMW 交付工作流下游技能与 CLI 的逐文件核对，谈定五项改动。无 prototype 资产。无 research 目录（调查结论已由主 agent 在当前源码与真实命令上验证，关键事实记入 Current State）。

## Problem Statement

用户的交付工作流在 spec 之后的落地阶段有五个缺陷：

1. plan 全部提前写完，排在后面的 plan 引用的 `文件:行号` 会被先落地的 ticket 改掉。`worker` 按纪律停下上报矛盾，工作流断点直接落到用户面前。
2. tracer bullet ticket 的验收标准没有写作判据。下游四道检查全部以验收标准为基准，验收含糊时每道检查都会形式上通过，质量下降不显形。
3. `planner` 的报告判词 `needs-repair` 只有名字没有定义。`planner` 不知道什么时候交它，`/mmw-to-plan` 却依赖它路由。
4. 没有任何环节系统扫描「spec 的每项决定都有 ticket 承接」。拆分漏项只能靠用户肉眼批清单兜住。
5. 审查之后的修复全部重派新 subagent，原生产者的上下文被丢弃。恢复原生产者本是 MMW 的理念，在历次改造中丢失：Claude Code 宿主两条派发通道都没有留下恢复句柄，技能正文的返工规则全部写成新派发。

## Solution

五项改动，全部落在技能源、CLI 与物化层，不改变六道审的结构：

1. **plan 批次循环**：plan 的撰写按 ticket 的阻塞关系分批推进。先为当前 frontier 上的 ticket 写 plan 并落地，落地过审关票后 frontier 解锁下一批，再为下一批写 plan。每个 `planner` 面对的代码里，阻塞它的 ticket 已经全部落地。
2. **验收标准写作判据**：`/mmw-to-tickets` 起草验收标准时有明确判据，用户批准清单时能看到每张 ticket 的验收标准。
3. **`needs-repair` 定义**：`planner` 知道上游材料本身有错时交 `needs-repair`，与 `needs-context`（材料缺失）、`needs-redirection`（方向不成立）三分。
4. **覆盖扫描**：② plan 审的覆盖质量审在首个批次沿 spec 逐条走，指认每项决定的承接 ticket。
5. **恢复原生产者**：派发时留下恢复句柄；审查之后的修复默认发回原生产者续跑，宿主或时机不支持时退回现行的重派做法；改动小到主 agent 验证成本低于一次派发时由主 agent 直接落地。

## Current State

以下事实支撑本次决定，均已在当前源码或真实命令上验证：

- `/mmw-to-plan` 现行流程是批量前置：一次写完全部 plan、统一发起一次 ② plan 审、给全部 ticket 打 `ready-for-agent`，然后才移交 `/mmw-implement`。`/mmw-to-tickets` 正文已承认 plan 会过期（「plan 只是过期得慢一些」），但没有环节处理。
- `worker` 纪律规定「ticket、plan、spec 或代码互相矛盾时，报告冲突位置」并停下；`/mmw-implement` 规定该矛盾停下交给用户。
- Claude Code 宿主 adapter 的 gpt 族派发是一次性 `codex exec` 进程：提示词走 stdin、报告走 `-o` 文件、进度走 stderr 日志。该用法符合 Codex 非交互模式文档；缺失的是会话句柄——没有 `--json`，`thread_id` 从未被记录。claude 族派发走 Agent 工具，params 没有 `name` 字段，没有可寻址的恢复地址。
- 本机 codex-cli 0.147.0 实测：`codex exec --json` 的第一个事件是 `thread.started`，携带 `thread_id`，同时 `-o` 照常写出最终报告；`codex exec resume <thread_id> <提示>` 续跑同一线程且上下文完整（44k 输入中 28k 命中缓存，能答出上一轮内容）。三个用法约束：选项必须放在 SESSION_ID 之前；`resume` 子命令没有 `--color`、`-C`、`--sandbox` 三个参数；resume 的会话清单默认按 cwd 过滤。
- Claude Code 宿主对已完成的 subagent 支持按名字用 SendMessage 续跑，上下文完整。Agent 工具接受 `name` 参数。
- Codex App 的后台 Worktree 任务由 `create_thread` 创建并返回 `threadId`，`wait_threads` 等待；`threadId` 即句柄。向已有 thread 发后续消息的工具名尚未在 App 宿主实测。
- 上游 superpowers 的修复循环：前三轮恢复原实现者（上下文完整、成本低），四五轮换全新实现者加更强模型，第五轮由编排者裁决且禁止静默丢弃；宿主不能续跑时的退路是重派新实例并带上原 task、原报告和 findings。MMW 现行返工升级策略正是这条退路。
- `bash mmw/test.sh` 是本仓库唯一的行为测试入口；dispatch 装配测试在 `CLI 护栏` 子套件，物化展开测试在 `技能与角色物化` 子套件，技能引用完整性在 `技能之间的引用指得到东西` 子套件。

## User Stories

1. 作为主 agent，我希望每个 `planner` 探到的代码就是它的 ticket 开工时的代码，以便 plan 里的 `文件:行号` 在 `worker` 开工时仍然成立。
2. 作为 `planner`，我希望阻塞本 ticket 的实现已经真实落地，以便跨 plan 接口可以直接对源码验证，而不是对着纸面骨架猜。
3. 作为 `worker`，我希望拿到的 plan 与当前代码一致，以便不把结构性时差当成矛盾上报。
4. 作为用户，我希望 plan 与代码的时效断层在工作流内部消化，以便不再收到本可避免的断点上报。
5. 作为用户，我希望批准 ticket 清单时看到每张的验收标准，以便在拆分关卡就拦住含糊的验收。
6. 作为主 agent，我希望验收标准可观察、含精确值、可独立判定，以便 ③ 逐份验收和 ② plan 审有真实的判断基准。
7. 作为 `planner`，我希望知道什么情况交 `needs-repair`，以便上游材料有错时打回材料层，而不是硬写占位证明。
8. 作为主 agent，我希望 ② plan 审在首个批次确认 spec 每项决定都有 ticket 承接，以便拆分漏项在写 plan 阶段就暴露。
9. 作为主 agent，我希望派发之后手上有恢复句柄，以便修复轮把 findings 发回原生产者续跑。
10. 作为用户，我希望修复轮复用原生产者的上下文，以便修复成本下降、修复质量不因上下文丢失而变差。
11. 作为主 agent，我希望句柄缺失或宿主不支持续跑时派发当场退回重派做法，以便修复轮永远走得通。
12. 作为用户，我希望微小的采信 finding 由主 agent 直接落地并验证，以便不为一行改动支付一次完整派发。
13. 作为维护者，我希望上述行为变化中机器可判定的部分都有 `bash mmw/test.sh` 的断言，以便回归时当场变红。

## Implementation Decisions

### 决定一：plan 批次循环

**批次**的定义：某一时刻，阻塞已全部关闭、还没有 `ready-for-agent` 标签的全部 open tracer bullet ticket。成员资格只看标签这一个状态判据：plan 文件是否已经写出不参与判定。中断后重入时，已有 plan 文件但没有标签的 ticket 重新走验证、② plan 审和打标签，`ready-for-agent` 的幂等添加保证重入收敛。

- `/mmw-to-tickets` 不变：一次性发布全部 ticket 和 blocking edge。
- `/mmw-to-plan` 首次进入时做两件一次性的事：把 `## Cross-Plan Contract Anchors` 骨架写进 spec（它只依赖 spec 与 ticket 的阻塞关系，首日信息完整）；按上面的定义取第一个批次。
- 批次内流程保持现行：派 `planner`（批内互不依赖时并行）、验证返回、回填本批次 plan 的精确字段、发起一次 ② plan 审、提交、给本批次 ticket 打 `ready-for-agent`。
- **② plan 审的材料与判据按批次重定义**：覆盖质量审与合规交叉审的被审对象从「全部 plan」改为「本批次 plan」；spec 与全部 ticket 仍然全量进入材料。覆盖质量审的「每张 ticket 都有 plan」改为「本批次每张 ticket 都有 plan」。`/mmw-review` 的 ② 行文与材料表、`/mmw-reviewer` 的覆盖质量审判据同步修改。
- **落地后的移交判据**：`/mmw-implement` 关掉一张 ticket 后读取全部 open ticket。存在符合批次定义的 ticket（阻塞已全关、无 `ready-for-agent`）时，移交回 `/mmw-to-plan` 做下一批次。frontier 上还有带标签的 ticket 时继续取下一张。两者都没有、但仍有 open ticket 时（都被认领或仍被阻塞），报告各张的状态并停下等待，不空转移交。
- `/mmw-implement` 的前置检查从「任何 open ticket 缺 `ready-for-agent` 就回 `/mmw-to-plan`」改为按上一条判据处理。`/mmw-start` 恢复路线里「有 open tracer bullet ticket 缺少 `ready-for-agent` 时，回 `/mmw-to-plan`」一句按同一判据同步修改。
- 派 `worker` 之前，主 agent 把该 plan 引用的关键路径对当前任务分支抽验一遍；失效就先按修复路由让 `planner` 刷新那份 plan。抽验降低批次内部漂移进入 `worker` task 的概率；没被抽到的残余漂移仍由 `worker` 的矛盾上报兜底——批次化之后这条上报是低频兜底路径，不再是结构性常态。
- `planner` 的 plan 正文规则不变：`## Current State` 继续钉 `文件:行号`——批次化之后这条指令对每张 ticket 都成立。
- 本决定改变 `mmw-skill-map.html` 里「全部 plan 通过 ② plan 审并提交后，为全部 ticket 添加 ready-for-agent」的架构描述，落地时同步更新；「批次」是新的长期术语，按 `/mmw-domain-modeling` 写进拥有 plan 概念的领域 leaf。
- 已知代价：② plan 审从一次变为每批次一次，单轮范围更小，总审查轮数增加。接受。

### 决定二：验收标准写作判据

`/mmw-to-tickets` 起草垂直切片时，验收标准按四条判据写：

1. 每条写可观察的外部行为，从 spec 已确认的 seam 或用户可见界面观察，不写内部实现。
2. 精确值（数字、文案、状态名、字段名）从 spec 或 prototype 选中产物逐字照抄。禁止「合适的」「正确的」「符合预期」这类需要再解释的说法。
3. 一条验收只判定一个行为，能独立判定真假；复合的拆开。
4. 每条验收写得出验证落点：spec 已确认 seam 上的测试，或人工浏览器审批项。写不出落点说明 spec 缺一项决定，停下回 `/mmw-to-spec`，不硬写。

用户批准清单的关卡从每张三样改为四样：Title、Blocked by、What it delivers、Acceptance criteria。

### 决定三：`needs-repair` 定义

在 `/mmw-planner` 正文补触发条件：

- 交 `needs-repair`：派给你的材料本身有错，而不是缺失。包括：ticket 的某条验收无法映射为任何证明方式；ticket 与 spec 互相矛盾；`## Cross-Plan Contract Anchors` 与 ticket 的阻塞关系对不上。写清是哪份材料、哪个位置、错在哪。修的动作在派发方，不在 `planner`。
- `/mmw-to-plan` 的对应行改为两分支：`needs-context` 补材料重派；`needs-repair` 按下一条处理后重派。
- **`needs-repair` 的修复不绕人工审批关卡**：spec 定稿与 ticket 清单都经过用户明确批准。要改的内容会变更用户已批准的验收标准、spec 决定或 blocking edge 时，`/mmw-to-plan` 停下，把 `planner` 交回的证据交给用户，取得批准后再修对应材料；只有不改变已批准语义的笔误级修正可以直接修。
- `planner` 交付前自检的判词从三档补成四档，与报告一节一致。

### 决定四：覆盖扫描

覆盖质量审的判据增加一条：沿 spec 的 `## Implementation Decisions` 与 `## User Stories` 逐条走，指认承接它的 ticket；指认不出的报 finding。该扫描只在首个批次的 ② plan 审执行——ticket 集合在 `/mmw-to-tickets` 时已固定，后续批次重扫是重复劳动。由 `/mmw-to-plan` 在首批次发起审查时写进审查材料。

### 决定五：恢复原生产者

分三层落地。机械动作在 CLI 与 adapter，宿主差异在物化层，技能正文只写角色语义。

**CLI 与 adapter 层（Claude Code 宿主）**：

- **句柄的形态**：gpt 族句柄是 `codex exec` 的 `thread_id` 原文；claude 族句柄是确定性生成的名字 `<角色>-<task 正文的 sha256 前 12 位>`。task 不落盘，没有文件名可借，正文摘要同样确定性：同一份 task 永远算出同一个名字，上下文压缩后只要还有那份正文就能重建。`--resume` 只接受句柄原文，不接受文件路径。
- gpt 族派发加 `--json`，从事件流的 `thread.started` 事件取 `thread_id`，写入句柄文件 `<角色>-<正文摘要>.session`，内容是单行句柄原文。落点是派发进度目录，由 `mmw artifact path scratch --sub dispatch` 回答，与派发进度日志同一处；算不出落点时不存盘，只在输出里给一次。报告仍然走标准输出——标准输出这条通道被 `--json` 的事件流占了，所以报告改用 `-o` 写进系统临时文件，读出来原样打到标准输出，用完就删。对调用方来说报告的合同没有变。`mode: executed` 输出增加 `session: <句柄原文>` 一行。
- claude 族派发的 params 增加 `name` 字段，值即句柄；输出增加 `handle: <句柄原文>` 一行。名字确定性生成意味着上下文压缩后可重建，不需要存盘。
- `mmw dispatch` 新增 `--resume <句柄>`，并把该参数登记进 `usage_dispatch` 的用法文本。gpt 族展开为后台 Bash：先 `cd` 进结果 worktree，再 `codex exec resume <选项> <thread_id> -`，修复 task 从 stdin 进，`-o` 收报告；选项排在 SESSION_ID 之前；不传 `--color`；sandbox 用 `-c` 配置覆盖按原派发同档传入。claude 族输出 `mode: host-tool`、`tool: SendMessage`、params 为收件名与修复 task 正文。
- resume 不换模型。换模型的轮次走全新派发。
- `--resume` 找不到句柄文件、句柄为空或宿主无对应通道时，当场以非零退出并说明缺什么，不静默降级成全新派发。
- 可写角色的 resume 必须能取得与原派发同档的写权限。落地时用测试确认 `-c sandbox_mode` 覆盖在 `codex exec resume` 上生效；确认不了则 gpt 族可写角色的 resume 通道不启用，走重派退路。

**物化层**：

- 新增 `[[mmw-resume:<角色>:<cwd 模式>]]` 动作块，与 `[[mmw-launch:…]]` 同构（cwd 模式同样是 `worktree`、`current`、`none` 三个取值），由 `mmw skills materialize` 按宿主整块展开。
- Claude Code 展开为 `mmw dispatch --resume` 指令；Codex App 的后台 Worktree 任务（`worker`、`worker-high-risk`、`prototype-worker`）展开为「向原 `threadId` 发送修复 task，`wait_threads` 等待」，工具名以落地时在 App 宿主实测到的为准，实测取不到就把该宿主的这一块物化为重派退路文案；Pi 与 Codex 原生 subagent（Codex App 上的 `planner`、`investigator`、`designer`、审查角色都属于原生 subagent）在续跑能力确认之前物化为重派退路文案。也就是说，Codex App 宿主本次最多只有 `worker` 族获得续跑，plan 修复在该宿主上走重派退路；这个覆盖差距记入 Out of Scope。
- 重派退路文案与现行返工做法一致：重派新实例，task 带原路径、原报告和本轮修复指令。

**技能层的修复路由**：审查之后的修复默认发回原生产者。总规则与例外写进 `/mmw-review`；各关卡的路由如下。

| 关卡 | 生产者 | 修复路由 |
| --- | --- | --- |
| ⓪ 共同理解、① spec | 主 agent | 不变，主 agent 自己修 |
| `/mmw-to-plan` 验证失实、② plan 审采信项 | `planner` | 恢复原 `planner` 带修复说明续跑；三轮上限保留，第三轮不过停。跨批次不恢复——下一批次由新 `planner` 对新代码探 |
| ③ 逐份验收返工 | `worker` | 一到三轮恢复原 `worker`（此时结果尚未集成，worktree 与任务分支同步）；四五轮维持全新 `worker-high-risk`；第五轮判定不变 |
| ④ 合同门缺兑现 | 提供方 ticket 的 `worker` | 先按下面的同步前置恢复该提供方的原 `worker` 补齐；恢复不了就合成修复 ticket 派新 `worker`；再失败才停 |
| ⑤ final 终审采信项 | 多张 ticket 的多个 `worker` | findings 全部落在同一张 ticket 时按同步前置恢复那张的原 `worker`；跨 ticket 时维持现行「打包一张修复 ticket 派一个新 `worker`」 |

**④⑤ 恢复的同步前置**：集成只把结果分支合入任务分支，不推进结果分支——原结果 worktree 看不到后来集成的 ticket。④⑤ 恢复原 `worker` 之前，主 agent 先在该结果 worktree 把当前任务分支合入结果分支（`git merge --no-ff`）；合并有冲突，或 worktree 已收、句柄失效时，放弃恢复，退到修复 ticket 派新 `worker`。同步成功后才发修复 task。

**小改动例外**：同时满足四个条件时主 agent 直接落地——不碰跨 plan 合同、seam 和共享文件归属；不涉及计费、权限、数据迁移和不可逆操作（这些属于 `worker-high-risk` 的升档面，不因改动小而降档）；改动量一眼可验证（一处文案、一个数值、一行断言这个量级）；验证成本低于一次派发。落地后必须运行该处验收命令并记录。

## Failure Paths

| 失败情况 | 触发条件 | 负责处理的边界 | 用户观察到的结果 | 系统行为 |
| --- | --- | --- | --- | --- |
| resume 缺句柄 | `--resume` 找不到句柄文件或句柄为空 | `mmw dispatch` | 派发报错一次 | 非零退出并说明缺什么；主 agent 改走重派退路 |
| resume 通道在当前宿主不存在 | 宿主无续跑能力或能力未确认 | 物化层 | 无感知 | 该宿主的 `[[mmw-resume:…]]` 物化为重派退路文案 |
| 原 `worker` 的结果 worktree 已收、句柄失效，或同步前置合并冲突 | ④、⑤ 阶段修复 | 主 agent | 无感知 | 按路由表退到修复 ticket 派新 `worker` |
| 批次内 plan 漂移 | 派 `worker` 前抽验发现关键路径失效 | 主 agent | 无感知 | 先让原 `planner` 刷新该 plan，再派 `worker` |
| `planner` 交 `needs-repair` | 上游材料本身有错 | `/mmw-to-plan` | 改动触及已批准语义时停，收到证据等批准；笔误级无感知 | 按决定三：先过对应人工审批关卡再修，然后重派 |
| 批次循环中 `planner` 交 `needs-redirection` | 当前源码证明 spec 方向不可实现 | `/mmw-to-plan` | 停，收到证据与建议 | 已落地批次保留在任务分支，由用户定向 |
| 可写角色 resume 写权限确认失败 | `codex exec resume` 的 sandbox 覆盖不生效 | CLI 测试 | 无感知 | gpt 族可写角色 resume 不启用，走重派退路 |

## Testing Decisions

- 好测试只测外部行为：命令给定输入产出什么、护栏拒绝什么、拒绝之后破坏有没有发生。这是 `mmw/test.sh` 现行准则，本次沿用。
- 技能正文的流程语义变化（批次循环、验收判据、`needs-repair`、覆盖扫描、修复路由）不新增机械校验。按 AGENTS.md 的机械校验边界，产物质量与流程正确性由技能与主 agent 判断；机器只校验语法结构、引用完整性和物化一致性，现有子套件已覆盖。
- 测试先例：dispatch 装配断言在 `CLI 护栏` 子套件，物化展开断言在 `技能与角色物化` 子套件，引用完整性在 `技能之间的引用指得到东西` 子套件。

用户已确认的 seam：

| Seam | 验证的外部行为 | 选择这一层的原因 |
| --- | --- | --- |
| `bash mmw/test.sh` | ① `mmw dispatch --resume` 两族的装配输出（gpt 族命令含 `codex exec resume`、选项在句柄前、不含 `--color`；claude 族输出 `SendMessage` 参数）；② 缺句柄时非零退出；③ gpt 族派发写出 `.session` 句柄文件且 `mode: executed` 含 `session:` 行、claude 族 params 含确定性 `name`；④ `[[mmw-resume:…]]` 在三个宿主产物中的展开与退路文案；⑤ `usage_dispatch` 帮助输出含 `--resume`；⑥ 技能引用完整性照常 | 本仓库唯一的行为测试入口，全部子套件挂在它底下；不新增 seam |

## Contract Boundaries

- **dispatch 输出合同**：`mode: executed` 的行集从「log、exit」扩展为「session、log、exit」，报告本身仍走标准输出；host-tool 输出增加 `handle:` 行。归属方是 Claude Code 宿主 adapter；消费方是技能产物里的派发指令和主 agent。句柄文件与派发进度日志同目录，生命周期不同：日志成功即删，句柄文件留到修复轮用完为止。
- **`[[mmw-resume:<角色>:<cwd 模式>]]` 物化合同**：技能源写动作块，物化层按宿主整块替换；技能正文不出现宿主名称分支。归属方是物化层；消费方是三个宿主的技能产物（Pi、Claude Code、Codex——Cursor 只有 agent 物化面，没有技能产物）。
- **报告判词合同**：`planner` 的四档判词 `pass`、`needs-repair`、`needs-redirection`、`needs-context` 在 `/mmw-planner` 报告节、自检节与 `/mmw-to-plan` 路由行三处语义一致。
- **`ready-for-agent` 语义不变**：仍表示「该 ticket 的 plan 已通过 ② plan 审」，只是打标签的时机从全量一次变为按批次。tracker leaf 的定义无需修改。

## Release Risk

- 本次不出包、不 push、不对外发布。改动合回主分支用 `git merge --no-ff`，由用户授权后执行远端动作。
- 技能源与 CLI 改动后必须重新物化三个宿主的技能产物并跑 `bash mmw/test.sh`；物化产物不同步时 `--check` 子套件当场变红，这是既有护栏。
- 修改 `mmw/cli/lib/materialize_skills.py` 与宿主 adapter 影响出包面；后续正式出包时按 AGENTS.md 的版本号五处同步规则处理，不在本次范围。

## Out of Scope

- ⑤ final 终审跨 ticket 修复维持现行单修复 ticket 做法，不做逐 finding 恢复多个 `worker`。
- `prototype-worker` 与审查角色的 resume。审查者一次性使用；修复验收由主 agent 做，不派审查者，无续跑需求。
- Pi、Cursor 与 Codex App 原生 subagent 续跑能力的探测与启用。本次 Pi 全部角色、Codex App 的 `planner` 等原生 subagent 物化为重派退路文案；Codex App 宿主本次最多只有后台 Worktree 任务的 `worker` 族获得续跑。
- `orchestrator` 模型档与各角色模型分配的调整。
- 上游 vendor 副本的更新（当前与上游同提交，无可更新内容）。

## Further Notes

- 上游对照结论：superpowers 的「前三轮恢复原实现者」与 MMW 的「一到三轮重派」差异是本次还原的对象；superpowers 的「第四五轮换更强模型」在 MMW 对应换 `worker-high-risk`，本来就成立，不改。上游禁止编排者亲手修 findings；本 spec 的小改动例外比上游宽，用四个条件和「落地后必须跑验收命令」把口子守住。
- 批次循环与恢复原生产者互相咬合：批次内的 plan 返修与 ③ 返工走 resume，批次边界是 `planner` 句柄的自然失效线。
