---
ticket: 37
artifact_refs:
  - category: research
    name: mmw-artifact-wiring
    issue: 19
    sub: artifact-inventory
---

# Plan: 产物落点数据与 `mmw artifact path`

**Goal:** 一个 agent 给出产物类别和工作名后，可以用一条无副作用命令取得正确落点。
**Source spec:** `docs/specs/mmw-artifact-wiring/spec.md`
**Source ticket:** GitHub issue `#37`
**Research source:** `docs/research/mmw-artifact-wiring/issue-19/artifact-inventory/README.md`；精确文件是同目录的 `report.md`

## Constraints

- 路径形状固定为 `<类别根>/<名字段>/[<范围段>/]<类别内细分>`。来源：spec Implementation Decisions 第 1 节。
- 安全路径段首字符必须是字母或数字。其余字符只能是小写字母、数字、点、下划线和连字符。来源：spec 第 1 节。
- `mmw/cli/artifacts.json` 是产物落点数据的唯一事实来源。类别根和类别内细分不得在解析代码里再写一份。来源：spec 第 2 节和 Contract Boundaries。
- `context-map.root` 取空字符串。拼接时不产生类别根目录段。来源：spec 第 2 节。
- 10 号 plan 先登记七个缺少定义条目的 canonical 术语。01 使用登记后的字面，不在本 plan 定义术语。来源：产物落点 leaf 与 Cross-Plan Contract Anchors 的文件归属。
- 01 号 plan 交付时，带名字段的类别必须显式给 `--name`。02 号 plan 才增加从任务状态读取工作名的缺省行为。来源：Cross-Plan Contract Anchors。
- 查询只读文件并输出路径。查询不得建立目录或写文件。来源：ticket `#37` 和 spec 第 4 节。
- 默认输出仓库相对路径。只有 `--absolute` 输出绝对路径。来源：spec 第 4 节。
- CLI 主入口只增加 `artifact` 的加载、用法、动作分发和顶层分发。不得调整其他子命令。来源：Cross-Plan Contract Anchors。
- `cmd_artifact()` 必须匹配 `^cmd_(\w+)\(\) \{ … ^\}`。`path)` 分支必须匹配 `^    ([a-z-]+)\)`。来源：`test_skill_refs.sh:43-49`。
- 顶层 `artifact` 分发行必须匹配 `^  ([a-z-]+)\) shift; `。来源：`test_skill_refs.sh:43-49`。
- 测试入口只增加 `test_artifact.sh` 的一行。不得调整其他测试行。来源：Cross-Plan Contract Anchors。
- research 的范围快照是 commit `b3d924ce9db88a7380dbcc13ad615aaa014454f9`。本 plan 只把它用于 27 类产物的覆盖核对。
- research 对三类产物的“无消费方”结论没有完整结构候选。本 ticket 不依赖这些结论。来源：research 索引“没查清楚的部分”。
- spec 第 2 节称“九个 `active` 类别”，但表中列出十个。该节随后明确区分 `context-map` 与 `context`。数据和测试按表中十个标识符处理。
- 不修改 spec、ticket、领域文档、其他 plan、技能源、初始化实现或任务状态实现。

## Current State

- `mmw/cli/mmw:46-68` 的顶层用法没有 `artifact`。`mmw/cli/mmw:720-735` 的顶层分发也没有 `artifact`。
- `mmw/cli/lib/config.sh:9-15` 返回当前 checkout 的仓库根。`mmw/cli/lib/config.sh:88-90` 读取 `.mmw.json` 的 `paths` 键。
- `mmw/cli/lib/task.sh:13-32` 的任务状态输出还没有工作名。因此本 plan 不能实现 `--name` 缺省。
- `mmw/cli/tests/test_domain.sh:7-33` 展示了现有命令行测试形态。测试在一次性 Git 仓库里运行真实 `mmw` 命令。
- `mmw/cli/tests/test_skill_refs.sh:43-49` 从 `mmw/cli/mmw` 解析顶层命令和动作。`mmw/cli/tests/test_skill_refs.sh:94-105` 用解析结果检查技能源里的命令。
- `mmw/test.sh:24-29` 逐行登记 CLI 测试。产物落点测试还没有登记。
- `mmw/cli/artifacts.json`、`mmw/cli/lib/artifact.sh` 和 `mmw/cli/tests/test_artifact.sh` 都需要新建。

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `mmw/cli/artifacts.json` | Create | 保存全部产物类别、路径形状数据、状态和用法术语 |
| `mmw/cli/lib/artifact.sh` | Create | 提供 `artifact` 用法，校验参数，并解析路径 |
| `mmw/cli/mmw` | Modify | 加载产物落点实现，并增加 `artifact` 用法、动作分发和顶层分发 |
| `mmw/cli/tests/test_artifact.sh` | Create | 在一次性仓库上验证数据结构和命令行行为 |
| `mmw/test.sh` | Modify | 只增加运行 `test_artifact.sh` 的一行 |

## Contracts and Seams

- **Test seam:** 使用 `mmw` 命令行接口。测试在一次性仓库里运行真实命令，并验证标准输出、标准错误、退出码和文件系统副作用。
- **Data seam:** `mmw/cli/artifacts.json` 的顶层是按类别名取值的对象。类别名本身不在记录内重复。
- **Record fields:** 每条记录都有 `term`、`root`、`root_kind`、`has_name`、`allows_scope`、`sub_naming`、`sub_fixed`、`sub_pattern`、`status` 和 `answered_by`。
- **Display term:** `term` 保存领域文档的 canonical 术语。`mmw artifact` 的两列表从类别键和该字段生成。
- **Active records:** `root_kind` 取 `fixed` 或 `workdir`。`root` 分别保存仓库相对类别根，或 `.mmw.json.paths` 的键名。
- **Repository-root record:** `context-map.root` 是空字符串。拼接时跳过这个空段。相对路径必须是 `CONTEXT-MAP.md`，不带前导斜杠，也不带 `./`。
- **Inactive records:** `root`、`root_kind` 和 `sub_naming` 是 `null`。`has_name` 与 `allows_scope` 是 `false`。`sub_fixed` 是空数组。`sub_pattern` 是 `null`。
- **Status values:** `status` 只取 `active`、`no-file`、`not-shaped`、`external` 或 `tracker`。
- **Command owner:** `not-shaped` 记录的 `answered_by` 保存 `mmw release`、`mmw graph` 或 `mmw task`。其他记录的值是 `null`。
- **Category set:** `active` 包含 `spec`、`plan`、`prototype`、`research`、`adr`、`context`、`context-map`、`out-of-scope`、`scratch` 和 `review`。
- **Category set:** `no-file` 包含 `task` 和 `agent-report`。
- **Category set:** `not-shaped` 包含 `release-state`、`release-artifact`、`delivery-record`、`graph` 和 `worktree`。
- **Category set:** `external` 包含 `handoff` 和 `explanation`。
- **Category set:** `tracker` 包含 `map`、`decision-ticket`、`conclusion-comment`、`handback-comment`、`spec-issue`、`tracer-ticket` 和 `agent-brief`。
- **Usage terms:** `term` 使用下表字面。英文 product terms 保持领域文档原形，不另造中文名称。

| 类别名 | `term` | 类别名 | `term` |
| --- | --- | --- | --- |
| `spec` | spec | `plan` | plan |
| `prototype` | prototype 资产 | `research` | research |
| `adr` | ADR | `context` | leaf |
| `context-map` | Context Map | `out-of-scope` | 否决记录 |
| `scratch` | scratch | `review` | 审查记录 |
| `task` | task | `agent-report` | 报告 |
| `release-state` | 出包状态 | `release-artifact` | 出包阶段产物 |
| `delivery-record` | 交付记录 | `graph` | 结构图谱 |
| `worktree` | 任务 worktree | `handoff` | handoff |
| `explanation` | 解释 HTML | `map` | map |
| `decision-ticket` | decision ticket | `conclusion-comment` | 结论评论 |
| `handback-comment` | 交回评论 | `spec-issue` | spec issue |
| `tracer-ticket` | tracer bullet ticket | `agent-brief` | agent brief |

- **Consumes from 10:** 10 号 plan 登记七个缺少定义条目的术语。它们是出包状态、出包阶段产物、解释 HTML、handoff、任务 worktree、否决记录和 spec issue。01 只使用 10 登记后的字面。01 不在 `artifacts.json` 或本 plan 定义术语。
- **Research reconciliation:** 用 research 报告第 1 节的 27 行逐行核对上述集合。一个数据类别可以覆盖多行过程材料。一个 research 行也可以拆成多个数据类别。
- **Removed research item:** research 中的 Wiki 页面由 spec 第 17 节废除。09 号 plan 负责删除实现。它不进入新的产物落点数据。
- **Fixed values:** `sub_fixed` 与 `sub_pattern` 使用 spec 第 2 节的完整取值。只有一个固定值时，调用方可以省略 `--sub`。
- **Fixed exception:** `context-map` 的固定值是 `CONTEXT-MAP.md`。它来自数据，不按用户输入的全小写规则再次拒绝。
- **User input validation:** 将 `--sub` 按斜杠拆成多段。拒绝空段、`.`、`..`、大写字母、非法首字符和其他非法字符。
- **Category validation:** 多个 `sub_fixed` 只约束第一段。其余段仍按安全路径段规则校验。`sub_pattern` 按完整类别内细分匹配。
- **Default sub:** 只有一个 `sub_fixed` 值时可以缺省 `--sub`。其他需要类别内细分的类别必须显式给值。
- **Scope:** `--issue` 只接收纯编号。命令把它转换成 `issue-<编号>`。`allows_scope` 为假时必须拒绝该参数。
- **Reusable resolver:** `mmw artifact path <类别> [--name ...] [--issue ...] [--sub ...] [--absolute]` 是公开解析接口。04 号 plan 复用该接口，不复制校验规则。
- **Command discovery:** `cmd_artifact() {` 与结尾 `}` 都从行首开始。`path)` 分支使用四空格缩进。顶层分发行写成 `  artifact) shift; cmd_artifact "$@" ;;`。这些形状让 `test_skill_refs.sh` 取得 `artifact` 和 `path`。
- **Standard streams:** 成功路径只写标准输出。错误和当场取名提醒只写标准错误。
- **Ad-hoc reminder:** `sub_naming` 是 `ad-hoc` 时，成功路径后输出查重提醒。提醒不得混入路径变量。
- **Consumes from 09:** `scratch.root` 取 `scratch`。`review.root` 取 `reviews`。解析时通过 `.mmw.json.paths` 读取实际工作目录根。
- **Consumes from 02:** 本 plan 预留缺省工作名接点，但不读取当前任务状态。02 号 plan 提供任务状态的工作名后，再让缺省 `--name` 使用它。
- **Produces for 02、03、04、07、09、11:** 上述记录字段、类别集合和 `mmw artifact path` 调用形态是这些 plan 消费的接口。

## Implementation

1. **产物落点数据覆盖完整集合**
   - Change: 先在 `test_artifact.sh` 固定 spec 第 2 节的类别集合和记录结构。再建立 `artifacts.json`。
   - Change: 逐行对照 research 报告第 1 节。记录每一行对应的数据类别或 spec 废除项。
   - Change: 填入全部固定类别根、工作目录根键、类别内细分取值、正则和状态。
   - Change: 把 `context-map.root` 写成空字符串。不要写 `/`、`.` 或 `./`。
   - Change: 七个缺少定义条目的 `term` 只使用 10 号 plan 登记后的字面。
   - Files: `mmw/cli/artifacts.json`、`mmw/cli/tests/test_artifact.sh`。
   - Verify: `bash mmw/cli/tests/test_artifact.sh` → JSON 可解析，类别集合完整，每条记录字段完整。

2. **路径解析通过真实命令行验证**
   - Change: 在 `artifact.sh` 实现详细用法和 `path` 动作。所有路径数据都从 `artifacts.json` 读取。
   - Change: 覆盖固定类别根、工作目录根、名字段、范围段和类别内细分。
   - Change: 为四种非 `active` 状态输出 spec 规定的说明。所有这些查询都非零退出。
   - Change: 为认不出的类别列出全部合法类别名。不得返回猜测路径。
   - Change: 校验固定值、正则、安全路径段、范围段和必需参数。
   - Change: 拼接时跳过空的 `root`。`context-map` 的相对路径只输出 `CONTEXT-MAP.md`。
   - Change: 分离标准输出、标准错误和当场取名提醒。
   - Files: `mmw/cli/lib/artifact.sh`、`mmw/cli/tests/test_artifact.sh`。
   - Verify: `bash mmw/cli/tests/test_artifact.sh` → 路径、失败、退出码、输出通道和无副作用断言全部通过。

3. **CLI 只接入 `artifact` 分区**
   - Change: 在 CLI 主入口加载 `artifact.sh`。
   - Change: 顶层用法增加 `artifact` 一行。
   - Change: 在 `mmw/cli/mmw` 定义 `cmd_artifact() { ... }`。函数边界从行首开始。用四空格缩进的 `path)` 分支调用路径解析实现。
   - Change: 顶层 `case` 增加 `  artifact) shift; cmd_artifact "$@" ;;`。
   - Change: 详细用法、两列表和 `path` 行为留在 `artifact.sh`。
   - Change: 在 `test_artifact.sh` 用 `test_skill_refs.sh` 的两条正则解析入口。断言顶层集合含 `artifact`，动作集合含 `path`。
   - Change: 不重排或改写其他子命令的顶层用法与分发行。
   - Files: `mmw/cli/mmw`、`mmw/cli/tests/test_artifact.sh`。
   - Verify: `bash mmw/cli/tests/test_artifact.sh` → 命令入口可执行，机械校验也能解析 `artifact path`。

4. **产物落点测试进入唯一测试入口**
   - Change: 在 `mmw/test.sh` 增加一行产物落点测试。保留其他测试行的顺序和正文。
   - Files: `mmw/test.sh`。
   - Verify: `bash mmw/test.sh` → 全部测试通过并退出 0。
   - Verify: `git diff --check` → 没有空白错误。

## Acceptance

| Ticket 验收 | 证明方式 | 命令或人工结果 |
| --- | --- | --- |
| 产物落点数据完整 | 测试精确比对类别集合、必填字段、枚举、固定取值和正则 | `bash mmw/cli/tests/test_artifact.sh` → 数据合同用例通过 |
| 非 `active` 类别没有遗漏 | 测试分别比对四组非 `active` 类别和状态 | `bash mmw/cli/tests/test_artifact.sh` → 状态覆盖用例通过 |
| spec 第 4 节的失败回应全部成立 | 每种输入分别断言非零退出、标准错误内容和无路径标准输出 | `bash mmw/cli/tests/test_artifact.sh` → 失败表用例通过 |
| 查询没有建立目录 | 在一次性仓库里比较命令前后的目录清单 | `bash mmw/cli/tests/test_artifact.sh` → 文件系统无副作用用例通过 |
| 相对路径与绝对路径正确 | 断言默认值和 `--absolute` 的完整输出 | `bash mmw/cli/tests/test_artifact.sh` → 两种路径输出用例通过 |
| `--sub` 逐段拒绝不安全输入 | 覆盖五类非法值，并断言标准错误指出具体规则 | `bash mmw/cli/tests/test_artifact.sh` → 安全路径段用例通过 |
| 无参用法是完整两列表 | 精确比对全部类别名和 canonical 术语 | `bash mmw/cli/tests/test_artifact.sh` → 用法输出用例通过 |
| `context-map` 的仓库根拼接正确 | 断言数据中的 `root` 是空字符串，并精确比对相对路径 | `bash mmw/cli/tests/test_artifact.sh` → 只输出 `CONTEXT-MAP.md`，不带 `/` 或 `./` |
| 当场取名提醒不污染路径 | 对 `ad-hoc` 类别分别捕获标准输出和标准错误 | `bash mmw/cli/tests/test_artifact.sh` → 标准错误出现提醒，标准输出只有路径 |
| 机械校验能识别 `artifact path` | 使用 `test_skill_refs.sh` 的顶层和动作正则解析 `mmw/cli/mmw` | `bash mmw/cli/tests/test_artifact.sh` → `artifact` 和 `path` 都在解析集合中 |
| 七个缺少定义条目的 `term` 由 10 号 plan 提供 | 合同门逐项比对 leaf 定义条目与 `artifacts.json.term` | 人工结果：七个字面一致，01 没有修改 leaf 或重复定义术语 |
| 新测试进入完整测试入口 | 运行仓库唯一测试入口 | `bash mmw/test.sh` → 全部测试通过并退出 0 |

## Browser Acceptance

不适用。

## Rollback and Gates

- 合同门先运行聚焦测试，再运行 `bash mmw/test.sh`。
- 产物落点数据和解析实现必须一起回滚。只回滚其中一项会留下不可解析的记录或缺失规则。
- 命令没有持久副作用。回滚不需要迁移文件或清理外部状态。
- 历史产物迁移不属于本 ticket。发现旧路径时只记录跨 plan 接触点。
