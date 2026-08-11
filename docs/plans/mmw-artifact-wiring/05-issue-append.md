---
ticket: 38
artifact_refs: []
---

# Plan: mmw issue append 与 mmw issue set-parent

**Goal:** 两个并发追加调用保住各自的新行。已有 issue 也能通过同一套父子关系端点设置父 issue。`mmw issue` 用法把追加一行导向 `mmw issue append`。
**Source spec:** `docs/specs/mmw-artifact-wiring/mmw-artifact-wiring.md`
**Source ticket:** GitHub issue #38

## Constraints

- `mmw issue append` 必须执行完整五步。顺序是读、插入、写、等 2 秒、重读。来源：spec 第 12 节。
- 重读后必须同时检查两项。V1 的全部行必须仍在，新增行也必须仍在。来源：spec 第 12 节与 ticket #38。
- 任一检查失败后最多重做 3 次。用尽后必须非零退出，并输出缺失行原文。来源：spec 第 12 节与 Failure Paths。
- `--section` 只精确匹配 Markdown 二级标题。找不到时必须列出现有二级标题，且不得创建小节。来源：spec 第 12 节与 Failure Paths。
- 不使用条件请求或乐观锁。该方案已经实测不可用。来源：spec 第 12 节与 ticket #38。
- `set-parent` 必须复用 `create --parent` 的 sub-issues 端点。端点失败时不得退回正文约定。来源：spec 第 13 节。
- issue 实现和 `test_issue.sh` 归本 plan 独占。CLI 主入口只改 issue 分区：增加两个动作的用法与分发行，修正动作总数和正文编辑说明，不重排其他行。来源：Cross-Plan Contract Anchors。
- `usage_issue` 必须把内置 tracker 动作总数从五条改为七条。追加一行必须指向 `mmw issue append`。`gh issue edit --body-file` 只用于有意替换整份正文，例如修改 `Destination` 小节。来源：`mmw/cli/mmw:159-162` 与 ADR `0014-map-append-command.md:1-3`。
- 不修改 ADR `0014`。14 份 ADR 与索引副本归 plan 03。来源：Cross-Plan Contract Anchors。
- 本 ticket 没有 prototype 资产，也没有 research。来源：ticket #38。

## Current State

- `mmw/cli/lib/issue.sh:21-32` 已有仓库解析和 issue database id 查询函数。
- `mmw/cli/lib/issue.sh:118-145` 的 `mmw_issue_create` 已实现 `--parent`。它向父 issue 的 `sub_issues` 端点提交子 issue database id。
- `mmw/cli/mmw:30-31` 加载 issue 实现。`mmw/cli/mmw:414-453` 的 `cmd_issue` 负责动作分发。
- `mmw/cli/mmw:132-164` 的 issue 用法目前只列五个动作。`mmw/cli/mmw:159` 仍写“以上五条”。`mmw/cli/mmw:162` 仍把普通“改正文”直接指向 `gh issue edit --body-file`。ADR `0014-map-append-command.md:1-3` 把 agent 拼整份正文写回认定为 map 正文丢行的成因。
- `mmw/cli/tests/test_issue.sh:58-103` 已用可记录请求的 `gh` stub 隔离真实仓库。`mmw/cli/tests/test_issue.sh:133-182` 已验证写请求顺序和 database id。
- `mmw/test.sh:25` 已执行 `test_issue.sh`。本 plan 不修改测试入口。
- 规划时，Serena 返回了 `issue.sh` 的函数候选。Graphify 连续两次被工具端取消。上述模块关系改用当前源码逐行确认。

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `mmw/cli/lib/issue.sh` | Modify | 实现 append 的五步并发保护、失败输出和 set-parent 端点调用。 |
| `mmw/cli/mmw` | Modify | 增加 append 与 set-parent 的用法段和对应分发行。把 tracker 动作总数改为七条。正文编辑说明把追加一行导向 append，并把 `gh issue edit` 限定为有意替换整份正文。 |
| `mmw/cli/tests/test_issue.sh` | Test | 扩展 stateful `gh` stub，并覆盖参数、时序、两项检查、重做、并发、父子端点失败和 issue 用法文本。 |

## Contracts and Seams

- **Test seam:** 使用 `mmw` 命令行接口。测试在一次性仓库里运行真 CLI，并把 `gh` 和等待动作换成可控 stub。它验证 agent 实际调用的外部行为。
- **Produces for plan 08:** 归属方和提供方是 plan 05。消费方是 plan 08 的 Wayfinder 改写。
- **Append call:** `mmw issue append <issue 编号> --section "<小节标题>" --line "<要追加的一行>"`。
- **Append fields:** 第一个位置参数是目标 issue 编号。`--section` 是二级标题的标题文字。Wayfinder 使用 `--section "Decisions so far"`，对应正文行 `## Decisions so far`。`--line` 是本次追加的一行。
- **Append result:** 命令只在 V1 全部行和新增行都存在时成功。任一检查失败就重做。重做用尽后非零退出，并在标准错误输出缺失行原文。
- **Set-parent call:** `mmw issue set-parent <子 issue 编号> --parent <父 issue 编号>`。
- **Set-parent endpoint:** 调用 `POST repos/<仓库>/issues/<父编号>/sub_issues`。字段是 `sub_issue_id=<子 issue database id>`。

## Implementation

1. **先把两个新动作的外部合同写成失败测试**
   - Change: 扩展 `gh` stub，使它保存 issue 正文，并能按屏障控制读写顺序。增加等待 stub，记录 `sleep 2`，但不真实等待。
   - Change: 增加 append 参数、小节插入、缺失小节、五步顺序、重做上限和缺失行输出测试。
   - Change: 为两项检查各写一条独立失效时序。第一条让重读结果保留 V1，却删掉新增行。第二条让重读结果保留新增行，却删掉 V1 中的一行。两条都必须触发重做并恢复缺失内容。
   - Change: 用屏障让两个后台调用都从同一个正文 S 开始。强制写入顺序为 `S+a` 后 `S+b`，再断言最终正文同时包含 a 和 b。
   - Change: 增加 set-parent 的请求形状和端点失败测试。端点失败必须直接传出非零状态，且不能发生正文降级写入。
   - Change: 增加 `usage_issue` 回归测试。断言用法列出 append 与 set-parent，tracker 动作总数是七条，并且不再把普通“改正文”直接指向 `gh issue edit`。
   - Change: 用法测试还要断言两条边界。追加一行使用 `mmw issue append`。只有有意替换整份正文时才使用 `gh issue edit --body-file`，示例是修改 `Destination` 小节。
   - Files: `mmw/cli/tests/test_issue.sh`。
   - Verify: `bash mmw/cli/tests/test_issue.sh` → 新增用例先失败，旧有 20 项仍通过。

2. **实现 append 的五步循环和两项独立检查**
   - Change: 解析 issue 编号、`--section` 和 `--line`。缺参数或未知参数时非零退出，且不写正文。
   - Change: 每次尝试先读最新正文 V1。精确找到 `## <小节标题>`，并在下一个二级标题之前插入新行。
   - Change: 插入位置是目标小节最后一个非空行之后。空小节则在标题之后插入。
   - Change: 写回 V2 后等待 2 秒，再读 V3。分别计算 V1 缺失行和新增行是否缺失。
   - Change: 任一结果失败就重做。下一轮不能忘掉上一轮已经发现的缺失行，否则 V1 检查无法修复它发现的丢行。局部合并方式由 worker 决定。
   - Change: 初次尝试后最多重做 3 次。仍失败时输出当前缺失行原文并返回非零状态。
   - Change: 小节不存在时，从正文收集实际二级标题并报错。此路径不能执行正文写入。
   - Files: `mmw/cli/lib/issue.sh`。
   - Verify: `bash mmw/cli/tests/test_issue.sh` → 两条单项失效时序、并发调用和失败路径全部通过。

3. **复用父子端点，并公开两个 CLI 动作**
   - Change: 实现 set-parent。它解析子 issue 编号和 `--parent`，查询子 issue database id，再复用 create 的 sub-issues 请求形状。
   - Change: 让端点错误直接成为命令错误。不写父子关系文本，也不调用 `gh issue edit` 降级。
   - Change: 在 `usage_issue` 加入 append 与 set-parent 两段。在 `cmd_issue` 只加入对应分发行。
   - Change: 把 `usage_issue` 的“以上五条”改成“以上七条”。不改其他命令的排列。
   - Change: 删除“改正文”直接使用 `gh issue edit --body-file` 的通用提示。明确说明向现有小节追加一行必须使用 `mmw issue append`，不要拼整份正文写回。
   - Change: 保留整份正文替换入口。把 `gh issue edit --body-file` 限定为有意替换整份正文，例如修改 `Destination` 小节；替换前先读取最新正文。
   - Files: `mmw/cli/lib/issue.sh`、`mmw/cli/mmw`。
   - Verify: `bash mmw/cli/tests/test_issue.sh` → set-parent 成功请求和端点失败用例通过；两个动作的无参或缺参调用返回更新后的 issue 用法和非零状态；用法回归断言通过。

4. **运行完整机械验证并检查施工边界**
   - Change: 不改 `mmw/test.sh`、ADR、技能源或其他 plan 文件。检查 diff 只包含 Change Map 的三个文件和本 plan。
   - Files: 本 plan 的全部改动。
   - Verify: `bash mmw/test.sh` → 全部测试通过，退出码为 0。
   - Verify: `git diff --check` → 没有空白错误。
   - Verify: `git diff --name-only` → 实现 diff 只包含 Change Map 的三个实现文件；plan 文件由规划阶段单独存在。

## Acceptance

| Ticket 验收 | 证明方式 | 命令或人工结果 |
| --- | --- | --- |
| append 接收 issue 编号、小节标题和单行内容 | CLI 参数成功与缺参测试 | `bash mmw/cli/tests/test_issue.sh` → 三个字段均被验证，缺任一字段时非零且不写正文。 |
| 一次调用执行读、插入、写、等待、重读 | stub 事件日志断言完整顺序和 `sleep 2` | `bash mmw/cli/tests/test_issue.sh` → 五步顺序测试通过。 |
| V1 全部行和新增行必须同时存在 | 两条互补的强制失效时序 | `bash mmw/cli/tests/test_issue.sh` → 删除任一检查都会有对应测试失败。 |
| 重做有上限，耗尽后报告缺失行 | 持续注入覆盖，断言尝试数、退出码和原文 | `bash mmw/cli/tests/test_issue.sh` → 初次尝试加最多 3 次重做后失败，并逐行输出缺失原文。 |
| 小节不存在时只报错，不创建 | 正文包含多个实际二级标题，目标标题缺失 | `bash mmw/cli/tests/test_issue.sh` → 非零退出，错误列出现有标题，正文逐字不变。 |
| 两个并发追加最终都保留 | 两个后台 CLI 调用共享一个受屏障控制的正文 | `bash mmw/cli/tests/test_issue.sh` → 最终目标小节同时包含 a 和 b。 |
| 已存在 issue 可设置父 issue，且没有文本降级 | 请求日志断言与端点失败注入 | `bash mmw/cli/tests/test_issue.sh` → 请求复用 create 的 endpoint 和 database id；失败时无正文写入。 |
| issue 用法在增加两个动作后按七条说明 | 捕获无参或未知动作输出，断言动作段和汇总句 | `bash mmw/cli/tests/test_issue.sh` → append 与 set-parent 均出现，“以上七条”出现，“以上五条”不再出现。 |
| issue 用法不会再把追加一行导向整份正文覆盖 | 用法文本回归断言 | `bash mmw/cli/tests/test_issue.sh` → 追加一行明确使用 `mmw issue append`；普通“改正文”快捷项消失；`gh issue edit --body-file` 只随整份替换说明出现，并列出修改 `Destination` 小节的示例。 |
| 新行为有回归测试，完整测试入口通过 | 局部测试后运行完整测试 | `bash mmw/test.sh` → 全部通过并以 0 退出。 |

## Browser Acceptance

不适用。此 ticket 没有界面。

## Rollback and Gates

- 自动测试只能使用 `gh` stub。不要用真实 issue 验证失败时序。
- 实现没有数据迁移。代码回滚使用 Git revert。
- 已经由用户运行过的 tracker 写入不会随代码回滚自动撤销。本 ticket 的实现阶段不执行这类真实写入。
