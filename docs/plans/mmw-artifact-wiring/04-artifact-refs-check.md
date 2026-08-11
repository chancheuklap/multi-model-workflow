---
ticket: 43
artifact_refs: []
---

# Plan: 产物引用声明与 `mmw artifact check`

**Goal:** 固定结构承载产物引用。`/mmw-to-spec` 发布三个固定节。它把带 agent brief 的原 issue 挂到 spec issue，并在成功后关闭。`mmw artifact check` 能检查全部 spec 与 plan，并在生产方完成文件后运行。
**Source spec:** `docs/specs/mmw-artifact-wiring/mmw-artifact-wiring.md`
**Source ticket:** GitHub issue `#43`

## Constraints

- 产物引用只含 `category`、`name`、可选 `issue` 和可选 `sub`。这些键对应 `mmw artifact path` 参数。（spec 第 6、7 节）
- 持久化声明必须写 `name`。命令不得用当前任务工作树的工作名补它。（spec 第 7、10 节）
- YAML 的「无」是 `artifact_refs: []`。Markdown 的「无」是产物引用块中的单独一行 `无`。（spec 第 6 节）
- `mmw artifact check` 只校声明层。它不检查解析后的路径是否存在，也不做反向校验。（spec 第 10 节、Testing Decisions）
- 缺元数据块或缺 `artifact_refs` 的文件是历史文件。命令逐文件报告，但退出码不因此失败。（spec 第 10 节）
- 01 拥有 CLI 主入口中的 `artifact` 分发行、用法段和测试入口行。本 plan 不改 `mmw/cli/mmw` 或 `mmw/test.sh`。（Cross-Plan Contract Anchors）
- 03 拥有 spec、plan 和 ADR 元数据块的字段与解析形状。本 plan 只消费 `artifact_refs`，不另建第二套元数据块解析合同。（Cross-Plan Contract Anchors）
- 05 拥有 `mmw issue set-parent` 的 CLI 实现和测试。本 plan 只在 `/mmw-to-spec` 的发布步骤调用该命令。（spec 第 13 节、Cross-Plan Contract Anchors）
- 07 在同一批技能源中改落点字面值。本 plan 只新增产物引用块和校验调用。它不重写 07 拥有的原路径行。（用户给定约束、Cross-Plan Contract Anchors）
- 技能源是流程语义的权威。修改后必须物化 Pi、Claude Code 和 Codex 的技能产物。（`AGENTS.md` 宿主边界）

## Current State

- 当前 CLI 主入口显式加载若干 `mmw/cli/lib/` shell 文件。它在末尾分发一级命令。当前分发表没有 `artifact`。（`mmw/cli/mmw:21-41,720-735`）
- `/mmw-to-spec` 在第 3 步写 spec，并在第 4 步开始审查。两步之间只有人工自检，没有声明校验命令。（`mmw/skills-src/mmw-to-spec/SKILL.md:55-73`）
- `/mmw-to-spec` 发布 spec issue 时只要求摘要、spec 路径和输入出处。它没有固定的 `## 工作名`、`## 输入出处` 和 `## 产物引用` 三节。（`mmw/skills-src/mmw-to-spec/SKILL.md:79-89`；spec 第 8 节）
- `/mmw-to-spec` 从已分诊 issue 进入时会读取 agent brief。它的发布步骤只创建 spec issue，没有设置父 issue 或关闭带 agent brief 的原 issue。（`mmw/skills-src/mmw-to-spec/SKILL.md:21,79-89`；spec 第 13 节）
- `/mmw-to-tickets` 从 spec issue 的输入出处读取精确路径。它的 ticket 模板没有 `## 产物引用` 节。（`mmw/skills-src/mmw-to-tickets/SKILL.md:17-25,103-141`）
- `/mmw-to-plan` 向 `planner` 传精确路径。它验证 plan 文件和 Acceptance，但不运行声明校验。（`mmw/skills-src/mmw-to-plan/SKILL.md:24-47,66-88`）
- `planner` 当前只把 prototype 与 research 的精确路径写进 plan。03 将在它的模板中提供 plan 元数据块。（`mmw/skills-src/mmw-planner/SKILL.md:15-30`; `mmw/skills-src/mmw-planner/references/plan-body.md:1-47`）
- `/mmw-implement` 仍把 prototype 与 research 的精确路径写入 `worker` 四栏 task。（`mmw/skills-src/mmw-implement/SKILL.md:47-70`）
- `bash mmw/test.sh` 通过 `run` 汇总各测试入口。01 负责加入 `test_artifact.sh` 的入口行。当前“技能物化”测试使用假源与临时产物目录，不比较当前技能源和当前技能产物。（`mmw/test.sh:15-43`；`mmw/cli/tests/test_materialize_skills.py:1-10,44-58,252-289`；Cross-Plan Contract Anchors）
- 技能物化器从 `mmw/skills-src/` 生成三个宿主目录。它在检查模式下逐文件比较产物。（`mmw/cli/lib/materialize_skills.py:20-26,311-392`）

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `mmw/cli/lib/artifact.sh` | Modify（由 01 Create） | 在 01 的 `artifact` 动作分发内增加 `check`。保留 01 的 `path` 行为和 CLI 主入口分区。 |
| `mmw/cli/lib/artifact_check.py` | Create | 扫描 spec 与 plan 元数据块，汇总历史文件与解析错误，不读取目标路径。 |
| `mmw/cli/tests/test_artifact.sh` | Test（由 01 Create） | 只增加产物引用形状、历史文件分流和 `check` 行为用例。不改 01、03 拥有的测试段。 |
| `mmw/skills-src/mmw-to-spec/SKILL.md` | Modify | 写 spec 元数据块。发布 spec issue 正文的三个固定节。把带 agent brief 的原 issue 挂到 spec issue 并关闭。运行声明校验。 |
| `mmw/skills-src/mmw-to-tickets/SKILL.md` | Modify | 从上游声明选择本 ticket 需要的产物引用。每张 ticket 固定写 `## 产物引用`。 |
| `mmw/skills-src/mmw-to-plan/SKILL.md` | Modify | 把 ticket 的产物引用交给 `planner`，并在每份 plan 写完后运行校验命令。 |
| `mmw/skills-src/mmw-planner/SKILL.md` | Modify | 解析 ticket 的产物引用，并按 03 的元数据块合同写入 plan。缺固定节时停止报缺。 |
| `mmw/skills-src/mmw-planner/references/self-check.md` | Modify | 自检 plan 的产物引用声明、显式工作名和上游传递完整性。 |
| `mmw/skills-src/mmw-implement/SKILL.md` | Modify | 从 plan 元数据块取得产物引用，并把它们写进 `worker` task 的「读」栏。 |
| `mmw/skills-src/mmw-implement/worker-brief.md` | Modify | 要求 `worker` 逐条解析产物引用。缺声明或异常缺失时停止，不猜路径。 |
| `mmw/skills-pi/` | Modify（由命令生成） | 生成上述技能源的 Pi 技能产物。 |
| `mmw/skills-claude-code/` | Modify（由命令生成） | 生成上述技能源的 Claude Code 技能产物。 |
| `mmw/skills-codex/` | Modify（由命令生成） | 生成上述技能源的 Codex 技能产物。 |

## Contracts and Seams

- **Test seam:** 使用 spec 已确认的 `mmw` CLI 命令行接口。测试在一次性仓库中运行 `mmw artifact check`，观察标准输出、标准错误、退出码和文件系统状态。
- **Test seam:** 使用 spec 已确认的技能源 Markdown 文本 seam。测试固定标题、键名顺序和「无」的写法；物化检查证明三个宿主产物与技能源一致。
- **Consumes — 01 → 04:** 01 提供 `mmw artifact path <category> --name <name> [--issue <issue>] [--sub <sub>]`。04 期望它校验类别、范围段许可、安全路径段和类别内细分规则。04 每次显式传 `--name`，并复用同一解析结果和失败原因。该接口不得检查目标路径是否存在。
- **Consumes — 01 → 04:** 01 的 `mmw/cli/artifacts.json` 提供 `root`、`root_kind`、`status`、`sub_fixed` 和 `sub_pattern`。04 用 `spec` 与 `plan` 记录确定扫描范围，不把 spec 索引副本当成 spec。
- **Consumes — 03 → 04:** 03 提供文件头 YAML 元数据块合同。字段名是 `artifact_refs`。04 期望读取结果能区分「没有元数据块」「没有该键」和「该键是空列表」。非空值是映射列表。
- **Consumes — 03 → 04:** 每项按 `category`、`name`、`issue`、`sub` 排列。`category` 与 `name` 必填。`issue` 是整数。其余值是字符串。`issue` 与 `sub` 只在类别需要时出现。
- **Consumes — 05 → 04:** 05 提供 `mmw issue set-parent <子 issue 编号> --parent <父 issue 编号>`。04 把带 agent brief 的原 issue 作为子 issue，把新建的 spec issue 作为父 issue。命令失败时停止，不退回正文约定。
- **Ownership:** 01 保留 `mmw/cli/mmw` 的 `artifact` 分发行、用法段和 `mmw/test.sh` 的测试入口行。04 只增加 `check` 动作与对应测试段。
- **Ownership:** 03 保留 `mmw-to-spec/spec-template.md` 与 `mmw-planner/references/plan-body.md` 中的元数据块形状。04 只补生产、传递、消费和校验行为。
- **Ownership:** 05 保留 `mmw issue set-parent` 的 CLI 实现与测试。04 只增加 `/mmw-to-spec` 的调用行和失败处置。
- **Ownership:** 07 在上述技能源内只改落点字面值、工作名取得和取名规则。04 的新增固定节、产物引用块和校验命令行不与这些行重叠。

## Implementation

1. **声明合同先由行为测试固定**
   - Change: 在一次性仓库中建立 spec 与 plan 测试输入。覆盖有效映射、空列表、历史文件、缺 `name`、非法类别、非法范围段和非法类别内细分。
   - Change: 同一次运行放入多条错误声明。断言命令逐条报告，而不是遇到第一条就退出。
   - Change: 放入可解析但目标路径不存在的产物引用。断言命令成功，且没有创建目录或文件。
   - Change: 对技能源固定结构增加文本断言。YAML 使用映射列表或空列表；Markdown 使用一条一行的键值形态或单独一行 `无`。
   - Files: `mmw/cli/tests/test_artifact.sh`。
   - Verify: `bash mmw/cli/tests/test_artifact.sh` → 新用例先因 `check` 与生产方声明尚未完成而失败。

2. **实现仓库级声明解析校验**
   - Change: 让 `mmw artifact check` 按 01 的类别根和文件形状扫描全部 spec 与 plan。排除 spec 索引副本。读取 03 的元数据块结果，并保留键是否存在的信息。
   - Change: 对每个非空条目要求显式 `category` 与 `name`。把可选 `issue` 和 `sub` 转成 01 的 `path` 参数。
   - Change: 用 01 的解析规则校每一条声明。成功时丢弃路径输出；失败时保留文件、条目和原因，最后统一返回非零。
   - Change: 对没有元数据块或缺 `artifact_refs` 的历史文件各报告一行。空列表直接通过。两类都不增加失败数。
   - Change: 不读取解析所得路径。不得执行文件存在性检查，也不得从磁盘反推漏写的产物引用。
   - Files: `mmw/cli/lib/artifact.sh`、`mmw/cli/lib/artifact_check.py`、`mmw/cli/tests/test_artifact.sh`。
   - Verify: `bash mmw/cli/tests/test_artifact.sh` → 全部 `check`、历史分流和无副作用用例通过。

3. **把产物引用传过五个固定位置**
   - Change: 五个固定位置是 spec 元数据块、spec issue 正文、tracer bullet ticket 正文、plan 元数据块和 `worker` task 的「读」栏。七份技能源必须共同覆盖这五处。
   - Change: `/mmw-to-spec` 从本次实际使用的 prototype 资产和 research 形成产物引用。spec 元数据块使用 03 的 YAML 形状。
   - Change: `/mmw-to-spec` 发布 spec issue 时固定写 `## 工作名`、`## 输入出处` 和 `## 产物引用`。工作名使用当前值，输入出处列出实际输入。没有产物引用时写 `无`。
   - Change: `/mmw-to-tickets` 读取上游固定声明。它只把当前 ticket 需要的条目写进 ticket 的 `## 产物引用`。没有条目时仍写该节和 `无`。
   - Change: `/mmw-to-plan` 把 ticket 的产物引用写入 `planner` task 的「读」栏。`planner` 逐条运行 `mmw artifact path`，并把条目写入 03 提供的 plan 元数据块。
   - Change: `/mmw-implement` 从 plan 元数据块取产物引用。它在 `worker` task 的「读」栏保留同一行键值形态。`worker` 自己解析路径，再读取索引列出的文件。
   - Change: 从已分诊 issue 进入时，`/mmw-to-spec` 先取得新 spec issue 编号。随后运行 `mmw issue set-parent <原 issue 编号> --parent <spec issue 编号>`。命令成功后才运行 `gh issue close <原 issue 编号>`。
   - Change: `mmw issue set-parent` 失败时停止。保留带 agent brief 的原 issue 为 open，不改用正文约定。没有原 issue 时跳过设置父 issue 和关闭步骤。
   - Change: 任一生产方都必须写固定声明。任一下游读不到声明时停止，说明缺失位置和上游，不猜路径。
   - Change: 只新增上述声明和消费规则。原有路径字面值的删除与改写留给 07。
   - Files: `mmw/skills-src/mmw-to-spec/SKILL.md`、`mmw/skills-src/mmw-to-tickets/SKILL.md`、`mmw/skills-src/mmw-to-plan/SKILL.md`、`mmw/skills-src/mmw-planner/SKILL.md`、`mmw/skills-src/mmw-planner/references/self-check.md`、`mmw/skills-src/mmw-implement/SKILL.md`、`mmw/skills-src/mmw-implement/worker-brief.md`。
   - Verify: `bash mmw/cli/tests/test_artifact.sh` → 两种书写形态、显式 `name` 和「无」用例通过。

4. **把校验放在两个生产检查点**
   - Change: `/mmw-to-spec` 每次写完或修完 spec 后，在自检和 ① spec 审之前运行 `mmw artifact check`。非零时先修声明，不进入审查。
   - Change: `/mmw-to-plan` 每次收到一份 plan 后，在接受 `planner` 的 `pass` 前运行 `mmw artifact check`。非零时把当前 plan 的错误交回该 `planner` 修复。
   - Change: 两处都调用仓库级命令，不另传单文件参数。这样当前文件和已有声明同时受检。
   - Files: `mmw/skills-src/mmw-to-spec/SKILL.md`、`mmw/skills-src/mmw-to-plan/SKILL.md`。
   - Verify: `rg -n "mmw artifact check" mmw/skills-src/mmw-to-spec/SKILL.md mmw/skills-src/mmw-to-plan/SKILL.md` → 两个生产检查点各有一次明确调用。

5. **物化并完成整仓验证**
   - Change: 从最新技能源物化三个宿主。不得直接修技能产物。
   - Files: `mmw/skills-pi/`、`mmw/skills-claude-code/`、`mmw/skills-codex/`。
   - Verify: `mmw/cli/mmw skills materialize --host all` → 三个宿主产物生成成功。
   - Verify: `mmw/cli/mmw skills materialize --host all --check` → 没有缺、异或多出的技能产物。
   - Verify: `bash mmw/test.sh` → 完整测试套件退出码为 0。

## Acceptance

| Ticket 验收 | 证明方式 | 命令或人工结果 |
| --- | --- | --- |
| YAML 与 Markdown 两种产物引用形态使用同一组键 | CLI fixture 与技能源固定结构测试覆盖 `category`、`name`、可选 `issue`、可选 `sub` | `bash mmw/cli/tests/test_artifact.sh` → 两种形态用例通过 |
| 两种形态都能明确表达没有产物引用 | 测试 `artifact_refs: []` 和产物引用块中的单独一行 `无` | `bash mmw/cli/tests/test_artifact.sh` → 两个「无」用例通过 |
| 持久声明不能缺工作名 | YAML 缺 `name` 时命令失败；issue 生产方模板要求每条显式 `name` | `bash mmw/cli/tests/test_artifact.sh` → 缺 `name` 用例非零，并报告对应条目 |
| 命令扫描全仓库 spec 与 plan，并汇总全部错误 | 一次性仓库同时放多文件和多条错误声明 | `bash mmw/cli/tests/test_artifact.sh` → 输出逐条包含文件与原因，退出码非零 |
| 历史文件只报告，不导致失败 | 分别覆盖没有元数据块和缺 `artifact_refs` 键 | `bash mmw/cli/tests/test_artifact.sh` → 每个历史文件一行，整体退出码为 0 |
| 显式空列表通过 | 新文件使用 `artifact_refs: []` | `bash mmw/cli/tests/test_artifact.sh` → 退出码为 0 |
| 校验不依赖目标文件落盘 | 有效引用指向尚不存在的位置，并比较运行前后文件树 | `bash mmw/cli/tests/test_artifact.sh` → 退出码为 0，文件树不变 |
| 五个固定位置都生产或传递产物引用 | 逐份读取七个技能源，核对 spec 元数据块、spec issue、tracer bullet ticket、plan 元数据块和 `worker` task | `git diff -- mmw/skills-src/mmw-to-spec/SKILL.md mmw/skills-src/mmw-to-tickets/SKILL.md mmw/skills-src/mmw-to-plan/SKILL.md mmw/skills-src/mmw-planner/SKILL.md mmw/skills-src/mmw-planner/references/self-check.md mmw/skills-src/mmw-implement/SKILL.md mmw/skills-src/mmw-implement/worker-brief.md` → 七份技能源共同覆盖五处，缺固定声明时停止 |
| spec issue 正文生产三个固定节 | 检查 `/mmw-to-spec` 的发布正文模板 | `rg -n '^## (工作名|输入出处|产物引用)$' mmw/skills-src/mmw-to-spec/SKILL.md` → 三个标题各出现一次 |
| 带 agent brief 的原 issue 成为 spec issue 的子 issue | 检查 `/mmw-to-spec` 发布步骤的命令顺序和失败处置 | `git diff -- mmw/skills-src/mmw-to-spec/SKILL.md` → 新 spec issue 建立后运行 `mmw issue set-parent`；成功后才关闭原 issue；失败时停止且不退回正文约定 |
| 三个宿主技能产物与技能源一致 | 用只读模式比较当前技能源和 Pi、Claude Code、Codex 技能产物 | `mmw/cli/mmw skills materialize --host all --check` → 退出码为 0 |
| 回归测试与完整套件通过 | 先跑 ticket 测试，再跑仓库统一入口 | `bash mmw/cli/tests/test_artifact.sh` 与 `bash mmw/test.sh` → 都退出 0 |

## Browser Acceptance

不适用。
