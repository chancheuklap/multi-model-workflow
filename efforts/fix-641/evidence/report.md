# #641 调查结论

2026-10-31。调查目标是改善任务板性能，并让 MMW 的 GitHub API 调用更合理。本轮只调查，没有修改产品、安装版本、模型配置或 GitHub 记录。

建议先删除能直接证明的重复读取，再验证按变化读取的方案。当前代码同时存在重复等待和数据新鲜度不一致，单纯缩短轮询间隔会增加请求，不能消除页面矛盾。

## 证据范围

工作区和安装 checkout 的 HEAD 都是 `9e2c0f3e2fe281f3587092cfce8249d129095b86`。任务板数据读取、页面轮询、状态计算、条件请求、汇总及 relay 的六个关键源文件逐字节相同。这是磁盘代码核对，不代表核验了每个运行中进程实际加载的版本。

本轮没有实时流量采样、延迟基准或 UI 缺陷重现。因此下文确认的是当前代码路径及 GitHub 的文档规则，不报告当前响应秒数、实际额度消耗或预计提速倍数。#641 的旧测量属于历史证据。

## 当前读取链

可见页面打开时读取任务板，之后每 60 秒触发一次。页面隐藏时跳过定时读取，切回可见状态没有立即读取。计时器不等待上一轮结束，也没有同页正在读取的检查。参见 [board-feed.mjs](/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/board/page/board-feed.mjs:1)。

每个 HTTP 请求都进入 `BoardStore.answer`。锁覆盖 GitHub 读取全过程。后来的请求等锁，再启动自己的读取，锁没有让请求共用结果。普通读取和手动刷新调用同一个方法。参见 [board_data.py](/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/board/board_data.py:261)。

一次读取按上次缓存决定哪些任务票还要读评论。通常每 600 秒重读结构，其中包括 issue 的开关状态、子 issue 和依赖。未完成任务票的评论逐张、逐页读取。结构事件可能触发额外结构读取。新发现的任务票再读评论。成功后提交整个本地结果，失败则保留上一份结果并标记读取失败。参见 [读取计划](/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/board/board_data.py:52) 和 [结构读取](/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/board/board_data.py:137)。

因此，本地一次提交是完整的，但其输入不一定同龄，也不是 GitHub 的原子快照。顶栏的 `read_at` 记录本轮开始时间，不能当作所有字段的实际读取时间。

## 可以直接确认的浪费

| 位置 | 当前行为 | 建议 |
| --- | --- | --- |
| 重叠的任务板刷新 | 每个请求排队后各读一轮评论 | 共用正在进行的一轮读取及结果，先避免同一标签页叠加刷新 |
| 夜的汇总 `print_summary` | 读完任务票后，`batch_children` 再读相同任务票 | 在同次命令内传递已经读取的任务票 |
| 任务板与 relay | 独立读取同一仓库评论，各自缓存 | 先保留职责边界。跨进程共用数据是否值得，需另有测量和完整性证据 |

`print_summary` 已把结构传给 `batch_children`，却没有传任务票。若一批有 N 张不同任务票、C 张不同的被读取子 issue，现有链会调用 `read_ticket` 共 `2N+C` 次。复用任务票后该链可减少 N 次 `gh issue view` 调用。这是由代码推导的调用次数，不是 HTTP 请求数或实测提速。参见 [batch_children 与 print_summary](/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/skills/dispatch/scripts/status.py:842)。

不能把同一轮内的第二次结构读取一律删掉。若两次读取之间真的出现了结构变化，第二次读取可能有用。应先查明变化是否已被第一轮读取覆盖，或由新的读取方案替代触发规则。

## #641 的核心问题仍可由当前代码解释

| 原问题 | 当前依据 | 结论边界 |
| --- | --- | --- |
| A，卡片已落地，线仍阻塞 | `Board.done` 可用 landed 事件判完成；连线的 `blocker_hold` 先检查 GitHub 开关状态 | 路径仍存在，未现场重现今天的延迟 |
| B，落地后的事件读不到 | `finished` 为 landed 或已放行时，任务票退出评论轮询 | 复跑、回归、恢复和收口仍可能被遗漏 |
| C，卡片与事件分块阶段不同 | 卡片计算当前阶段；事件分块查历史事件映射，且 claim 可并入前一块 | 详情头部与卡片共用当前阶段。不能把历史事件所属阶段直接等同于当前阶段 |
| D，切回或刷新仍旧 | 没有立即处理可见性变化；手动刷新不强制重读结构 | 缩短轮询间隔不能解决所有来源的新鲜度问题 |

依据：[finished](/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/board/board_data.py:41)、[当前阶段与完成判定](/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/board/page/board-logic.mjs:57)、[连线判定](/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/board/page/board-logic.mjs:178)、[事件分块映射](/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/board/page/board-logic.mjs:392)、[依赖放行语义](/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/skills/verify-ticket/scripts/events.py:834)。

同一张任务票可以同时具有不同的业务事实，例如 GitHub 已关闭但尚未合入。统一状态来源不等于把这些事实压成一个“完成”。需要让页面共同使用同一份已解释的事实，并保留关闭、通过、合入和回归的区别。

## GitHub API 调用应该怎样更合理

现有 `ConditionalListReader` 已经保存每页内容、ETag 和后续页地址，任务板和 relay 都在使用。它还处理了恰好满页时追加新页的情况，不能用“首页没变”替代整份分页读取。参见 [ghlist.py](/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/skills/dispatch/scripts/ghlist.py:87)。

GitHub 文档明确规定，正确认证的条件请求若返回 304，不计入主要额度。304 仍然是网络请求，MMW 也仍启动了 `gh`。因此，减少 HTTP 请求、减少子进程、减少主要额度消耗和减少等待时间，是不同目标。[GitHub 条件请求规则](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api#use-conditional-requests)

GitHub 建议避免并发请求，并要求限流后遵守 `Retry-After` 或额度重置时间。当前 `ghlist` 把非 200、304 响应变成错误，没有把这些时间交给调用方；relay 的外层循环继续按固定间隔再读。本轮没有核查 `gh` 内部的重试实现，不能据此声称完全没有重试保护。建议先在已有读取层保留并遵守服务器的暂停信息，而非增加并发或新增全局调度服务。[GitHub 并发与限流建议](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api#handle-rate-limit-errors-appropriately)

relay 已按评论更新时间减去两分钟重叠区间增量读取，重启后先完整读取。它读到的后续结果是增量，不是任务票全部历史，不能直接当作任务板的完整事件记录。它还会为每个 spec watch 读取子 issue，再对不同任务票读评论。参见 [relay 的评论读取](/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/skills/dispatch/scripts/relay.py:479) 和 [poll](/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/skills/dispatch/scripts/relay.py:950)。

按仓库读取变化，再更新受影响任务票，是值得验证的候选方案。issue 列表可提供开关状态等字段，评论列表支持按更新时间读取。但官方文档没有承诺父 issue 的 `updated_at` 会反映每次评论编辑或删除；增量列表也不是删除日志。按更新时间排序时，数据变化还会移动分页位置。不能以一页列表、一个时间戳或一次 304 保证整仓库完整。[issue 列表参数](https://docs.github.com/en/rest/issues/issues#list-repository-issues)、[评论列表参数](https://docs.github.com/en/rest/issues/comments#list-issue-comments)、[分页与缓存限制](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api#make-requests-that-can-be-cached)

## 推荐顺序与下一步证据

1. 删除重复工作。合并重叠的任务板读取；同次汇总复用任务票；在现有读取层遵守限流暂停。这些改变不需要重设计任务板外观。
2. 用隔离实验比较现有逐票读取与仓库级变化读取。覆盖新增、编辑、删除、重开、落地后回归、分页边界和重启。检查事件完整性、状态年龄、请求数、200 与 304、子进程数及页面等待时间。旧方案和候选方案必须使用同一份事件序列和相同网络条件。未通过完整性验证前，不以“更省”作为采用理由。
3. 依据验证结果修正读取计划和状态解释。新加当前阶段时间、夜的收口状态等显示，沿用 #641 已记录的设计验收要求，另做产品设计，不把调查页当作 UI 设计签收。

没有建议新增一套 ticket 状态存储、全局缓存服务或跨仓库限流协调器。当前证据先支持删除本地重复工作，再判断是否需要更大的改造。

## 原始研究

- [任务板读取链](board.md)
- [MMW 其他 GitHub 调用](runtime.md)
- [GitHub 官方规则](github-rules.md)

原始研究报告已保存在本目录，研究批次关闭后仍可读取。

[read-paths.py](read-paths.py) 只用 Python 标准库解析源文件，提取读取计划和调用位置，不运行产品代码或连接 GitHub。[本轮提取结果](read-paths.json) 与报告引用的调用位置一致。可在以后检查修改是否消除了重复调用；该脚本不是性能基准，也不证明运行行为。
