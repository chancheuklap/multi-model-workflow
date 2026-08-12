# aidlc-workflows v2 的产物落点与阶段间传递

范围快照：`awslabs/aidlc-workflows` 分支 `v2`，访问日期 2026-08-11。GitHub 当时显示头提交短 SHA `2ce654d`，README 标注版本 `2.5.62`。无法固定完整 commit SHA：`api.github.com/repos/.../commits/v2` 被宿主拒绝，GitHub commits 页面返回 `429`，本机 `git ls-remote` 无法解析 `github.com`。

英文原文按原样抄写。每条注明主 agent 是否亲自核对。

## 1. 产物有 canonical name，落点从 name 推导

产物的身份不是路径，是一个 **canonical name**。

> "Artifacts live on disk at paths that are derivable from `(canonical name) + (producing stage) + (per-unit flag)`."
> —— `docs/reference/16-artifact-vocabulary.md`（主 agent 亲自抓取核对）

canonical name 的定义：短 kebab-case 字符串，无扩展名、无目录前缀、无斜杠，由**恰好一个**生产阶段在自己的 YAML frontmatter 里声明。

> "An artifact is a **canonical identifier** declared by exactly one"
> —— 同上（主 agent 亲自抓取核对）

## 2. 唯一生产者，且名称全局唯一

**Collision policy**：两个阶段不得声明同一个 canonical name。registry 是一个集合，名称全局唯一。两个阶段的产物概念上重叠时，拆成两个不同的 canonical name。

> "Two stages **must not** declare the same canonical name in their"
> —— `docs/reference/16-artifact-vocabulary.md`（主 agent 亲自抓取核对）

实例：`build-and-test` 阶段与 `performance-validation` 阶段的磁盘文件名都可能是 `test-results.md`，但 canonical name 分别是 `build-test-results` 和 `load-test-results`。

> "On-disk filenames don't have to match."
> —— 同上（主 agent 亲自抓取核对）

## 3. 消费者不拥有路径，产物位于生产它的阶段目录下

`resolveArtifactPath()` 的注释里有这个短语：

> "UNDER THE STAGE THAT OWNS THE FILE"
> —— `core/tools/aidlc-orchestrate.ts`，`resolveArtifactPath` 上方注释（主 agent 亲自抓取核对）

`investigator` 另抄回同一注释块的一句：`"A consumed artifact lives under the stage that PRODUCES it"`。主 agent 未取得这一句的逐字原文；两次独立取证的语义一致，事实采信，逐字原文只以上面那个短语为准。

函数行为（主 agent 通过两次独立取证确认语义，未取得逐字源码）：

- 遵循 1:1 producer 规则。消费方请求某个 canonical name 时，路径锚定在生产它的阶段目录，不是消费方目录。
- `codekb` 类产物走特例，解析到 space 级共享目录，按仓库分键。
- per-unit 阶段（Construction 阶段按 Unit of Work 重复）插入一段 `<unit-name>`。
- 其余阶段用生产阶段的 phase 与 slug 拼路径。

## 4. 路径形状

```text
普通阶段      <record>/<phase>/<producer-stage>/<canonical-name>.md
per-unit 阶段  <record>/construction/<unit-name>/<producer-stage>/<canonical-name>.md
codekb 例外    aidlc/spaces/<space>/codekb/<repo>/<canonical-name>.md
```

`<record>` 是当前活跃 intent 的记录目录：

```text
aidlc/spaces/<space>/intents/<YYMMDD>-<label>/
```

> "State, audit, and artifacts live under the active intent record dir"
> —— `docs/reference/06-hooks-and-tools.md`（`investigator` 抄回，主 agent 未逐字核对）

## 5. 阶段间传递：三步声明加一次解析

1. 上游在 YAML `produces[]` 声明 canonical name。
2. 下游在 YAML `consumes[]` 声明**同一个 name**。
3. 引擎发 `run-stage` directive 时把已存在的输入解析成实际路径，放进 `directive.consumes`。

> "Other stages reference the same identifier in `consumes[]` to declare a read dependency."
> —— `docs/reference/16-artifact-vocabulary.md`（主 agent 亲自抓取核对）

> "the directive's `consumes` lists only resolved paths that exist on disk"
> —— `core/aidlc-common/protocols/stage-definition.md`（主 agent 亲自抓取核对）

下游阶段**不在正文里抄写上游路径**。

## 6. 阶段正文里的路径不是合同

这是 aidlc 与 MMW 现状差别最大的一条。

> "YAML frontmatter at the top of every stage `.md` is authoritative."
> —— `core/aidlc-common/protocols/stage-definition.md`（主 agent 亲自抓取核对）

> "the engine NEVER reads `outputs:` for path resolution; it resolves the node's `produces[]` artifact NAMES against the **active intent's record dir**"
> —— 同上（主 agent 亲自抓取核对）

frontmatter 的 `outputs:` 字段被标为：

> "**Non-load-bearing at runtime**"
> —— 同上（主 agent 亲自抓取核对）

阶段 `.md` 文件本身**不硬编码任何工作区根路径**。`produces[]` 里只有相对的 kebab-case 产物名。实际磁盘路径由引擎在发 directive 时计算，由 `aidlc-orchestrate.ts` 的 `resolveArtifactPath()` 与 `memoryPathFor()` 完成，配合 `aidlc-lib.ts` 的 `relativeRecordDir()` 提供当前活跃 intent 的相对记录目录。

**阶段文件里出现写死的根路径，被这份协议定性为文档错误，不是行为约定。**（主 agent 亲自抓取核对该文件时得到此项说明）

## 7. conductor 不拥有产物位置

conductor 执行引擎给出的一个 directive：读取已解析的输入路径、执行阶段、报告结果。它不自行计算下一阶段，也不自行拼接或登记产物位置。

> "The engine decides which stage is next; you own the quality of execution inside the move it named."
> —— `core/aidlc-common/conductor.md`（`investigator` 抄回，主 agent 未逐字核对）

> "Read resolved inputs. The conductor reads the existing artifacts in `directive.consumes`."
> —— `docs/reference/03-orchestrator.md`（`investigator` 抄回，主 agent 未逐字核对）

多 agent 阶段中，conductor 把**已经给出的路径**放进任务上下文。它是传递者，不是权威来源。

## 8. 没有中心产物索引，只有派生的名称注册表

**没有一处登记全部实际文件位置的索引。**

有一个 canonical name 注册表：从全部阶段的 `produces[]` 与 `optional_produces[]` 计算得出，只登记 name，不登记每次运行的实际路径，由 `aidlc graph artifacts` 输出到标准输出。

> "The registry is computed, not written."
> —— `docs/reference/16-artifact-vocabulary.md`（主 agent 亲自抓取核对）

`aidlc graph producers <artifact>` 与 `aidlc graph consumers <artifact>` 回答生产方与消费方关系。它们回答的是**阶段定义里的 artifact**，不扫描磁盘列出现有文件。

**没有独立的公开 `artifact-path` 命令。** 实际路径由 `aidlc-orchestrate` 内部的 `resolveArtifactPath()` 计算后放进 directive，不作为一条可单独调用的查询命令暴露。

恢复时，系统先读实际 artifact tree，再读 `memory.md`、audit、state 和 `runtime-graph.json`；`runtime-graph.json` 是跨阶段摘要，不是全部文件位置索引。

## 9. 上游产物不存在时的行为

先区分「预期不存在」与「异常缺失」。

`required: true` 不等于全局必须存在：

> "`required: true` means 'if the producing stage runs, this consume must be satisfied.'"
> —— `docs/reference/15-stage-definition.md`（`investigator` 抄回，主 agent 未逐字核对）

- 生产阶段被 scope 跳过：输入按设计缺失。下游执行阶段正文定义的 fallback，或由用户手工提供文件。
- 生产阶段本应运行但文件不在磁盘上：阶段未完成就正常运行它；状态已记录为完成就告诉用户文件缺失，并给两个选项。

> "Do not invent the missing artifact's content and do not treat the gap as a failure."
> —— `core/aidlc-common/protocols/stage-protocol-recovery.md`（`investigator` 抄回，主 agent 未逐字核对）

> "Offer two options: re-run the stage, or provide the artifacts manually."
> —— 同上（`investigator` 抄回，主 agent 未逐字核对）

反方向有强制失败：阶段批准时，若它声明的 `produces[]` 文件缺失，引擎拒绝把该阶段标记为完成（出处 `docs/reference/03-orchestrator.md`，`investigator` 抄回，主 agent 未逐字核对）。

## 10. 工具的职责边界

`core/tools/` 下有 37 个 `aidlc-*.ts` 文件（含分发器 `aidlc.ts`），其中 `aidlc.ts` 的 `TOOLS` 表登记 20 个可调用工具，其余 17 个是分发器、路径库、schema、诊断和工作区支持文件。文件计数由主 agent 通过 GitHub API 列目录亲自核对：36 个 `aidlc-*.ts` 加 `aidlc.ts`，共 37 个。

阶段产物的正文主要由 harness 的 `Write` / `Edit` 写入。工具负责提供路径、状态、审计、验证和生成结构，不代替阶段写文档。

与产物落点直接相关的工具：

| 工具 | 与落点的关系 |
| --- | --- |
| `aidlc-graph` | 编译阶段定义；查询 artifact、producer、consumer、拓扑与 scope；写编译后的 `stage-graph.json`；`artifacts` 输出注册表到标准输出 |
| `aidlc-orchestrate` | 按 graph 与 state 决定下一步，生成 directive；**计算**阶段产物路径，但不写产物正文 |
| `aidlc-sensor` | 接收调用方传入的 `--output-path`，检查该 target 是否存在并匹配 sensor manifest 的 `matches` 规则；不负责选择 canonical 路径 |
| `aidlc-validate` | 校验仓库中阶段源文件的 `Outputs:` 声明是否在阶段步骤正文里被引用；不读取任何项目的实际产物 |
| `aidlc-utility` | `doctor` 等通用动作，含下一节的引用校验 |

`core/tools/data/scaffold/` 在当前 v2 分支**不存在**（GitHub tree 与 raw README 均返回 404）。实际存在的是 `core/tools/data/templates/`，当前只有 `.gitkeep`，没有阶段产物模板。产物结构来自 `produces[]` / `consumes[]`、生产阶段和 `resolveArtifactPath()`。主 agent 通过 GitHub API 确认 `core/tools/` 下存在 `data` 子目录，未逐层确认 `scaffold` 的 404。

## 11. 机械校验校的是声明层，不是运行时落点

这一节对 MMW 的机械校验边界最相关。

**有：阶段定义的引用校验。** `/aidlc --doctor` 跑一项 "Graph references" 检查（实现在 `aidlc-utility.ts`）：每个 `consumes[].artifact` 和每个 `requires_stage[]` slug 都必须解析到派生注册表里的真实对象；解析不到的报告为 "broken references"，即孤立消费者。

> "runs a "Graph references" check (`aidlc-utility.ts`) — every `consumes[].artifact`"
> —— `docs/reference/16-artifact-vocabulary.md`（主 agent 亲自抓取核对）

这校验的是**阶段定义之间的引用完整性**，不检查某一次运行的产物文件是否已经落到磁盘。

**有：sensor 对给定 target 的存在性与形状校验。** `aidlc-sensor fire` 要求 `--output-path`，路径不存在则命令失败，并检查该路径是否匹配 sensor manifest 的 `matches` 规则。它验证给定 target，不验证该 artifact 是否位于 resolver 应给出的 canonical 目录。

**有：上游存在性读取，但只用于过滤。** sensor 按生产方目录查找上游 `<name>.md`，只把磁盘上存在的上游产物传给 upstream-coverage sensor（`"filtered to artifacts that exist on disk"`）。缺失的上游被过滤掉，以免对被跳过的阶段产生必然失败的检查。它不是「所有上游必须存在否则阶段失败」的总门禁。

**有：per-unit 阶段的完成度检查。** `aidlc-orchestrate` 的 `unitCovered()` 用解析出的 canonical 路径检查每个适用 `produces[]` 文件是否是 regular file。它用于 unit coverage 与完成判断，不是独立的落点校验工具。

**有：阶段源文件的 `Outputs:` 文本校验。** `aidlc validate outputs` 检查每个声明的文件名是否在该阶段步骤正文中被引用。它读仓库里的阶段文件，不读任何项目的实际产物。

**没有找到：全局产物落点门禁。** 在已读取的公开工具分发器、路径 resolver、doctor、sensor、测试与 CI 中，没有一个通用动作同时做到遍历全部 `produces[]`、计算每个 canonical 路径、检查文件在该位置存在、并对任意错位或缺失统一失败。

这条否定断言的取证范围是：`core/tools/` 的公开工具、`tests/`、`.github/workflows/ci.yml`、`scripts/package.ts`，以及 `docs/reference/` 的相关文档。`investigator` 无法固定 commit SHA，也未阅读全部 37 个文件的完整源码。**它是「已查范围内未找到」，不是「不存在」的完整结论。**

## 12. CI 与测试覆盖

CI 跑打包一致性、TypeScript、lint、smoke 与 unit tests。`scripts/package.ts` 的 `--check` 检查生成的 `dist` 是否与提交内容逐字节一致。`.github/workflows/ci.yml` 没有对某个 intent record 的阶段产物执行扫描。

与产物落点和传递相关的测试（`investigator` 抄回，主 agent 未逐条核对）：

| 测试 | 覆盖 | 未覆盖 |
| --- | --- | --- |
| `t45-aidlc-validate` | `validate outputs` 读已发布阶段文件，检查 `Outputs:` 名称出现在步骤文本中 | 项目实际产物是否存在、路径是否正确 |
| `t63-aidlc-graph-artifacts` | `aidlc graph artifacts` 的注册表 | 不扫描 intent record 内的文件 |
| `t92-aidlc-sensor` | `sensor fire` 必须得到 `--output-path` 且该路径必须存在 | 不证明该路径等于 `resolveArtifactPath()` 的结果 |
| `t264-review-freeze` | READY receipt 之后阻止对 `produces[]` 路径的写入 | 不验证第一次写入时的落点 |
| `t12-aidlc-runtime` | runtime graph fragment 的 worktree fork / merge | 不验证阶段 Markdown 产物传递 |
| `t129-runner-gen` | graph 与生成 runner 的漂移检查 | 不验证实际运行的产物文件 |

`tests/.coverage-registry` 把 `ARTIFACT_CREATED`、`ARTIFACT_REUSED`、`ARTIFACT_UPDATED` 标为 `UNCOVERED`。
