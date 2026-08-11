---
ticket: 45
artifact_refs:
  - category: research
    name: mmw-artifact-wiring
    issue: 20
    sub: aidlc-v2-artifact-wiring
---

# Plan: wayfinder 接线与 `mmw artifact list`

**Goal:** decision ticket 在开工前声明并补全必读材料。四类 decision ticket 都把材料交给下游。`mmw artifact list` 提供候选清单。
**Source spec:** `docs/specs/mmw-artifact-wiring/mmw-artifact-wiring.md`
**Source ticket:** GitHub issue `#45`
**Research source:** `docs/research/mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/README.md`；精确文件是同目录的 `report.md`

## Constraints

- 本 plan 在 01、02 和 05 之后实施。01 建立 `artifact` 命令。02 提供缺省工作名。05 提供追加动作。来源：ticket `#45` 的 `Blocked by`。
- decision ticket 正文固定包含 `## Question` 和 `## 必读材料声明`。来源：spec Implementation Decisions 第 8、14 节。
- 必读材料声明使用两类条目。仓库产物写产物引用。结论评论写 issue 编号。来源：spec 第 6、14 节。
- 仓库产物条目照搬 research 报告第 5 节的下游声明步骤。ticket 声明与上游相同的产物身份，不抄写路径。路径由下游解析。
- `mmw artifact list` 只给候选。是否选入必读材料声明，由认领者判断。来源：spec 第 11 节。
- 结论评论固定使用 `<!-- mmw:conclusion -->`。它包含 `## 答案`、`## 资产精确路径` 和 `## 材料使用记录`。来源：spec 第 8、14 节。
- 交回评论固定使用 `<!-- mmw:handback -->` 和 `## 交回`。读取方按标识定位，不再取最后一条评论。来源：spec 第 8 节。
- map 的决定索引必须调用 05 提供的追加动作。agent 不再拼整份 map 正文。来源：spec 第 12、19 节。
- wayfinder 四份技能源中，本 plan 只拥有交接表、ticket 正文模板、认领步骤和 map 正文小节标题。来源：spec `Cross-Plan Contract Anchors`。
- 07 拥有上述四份文件中其余位置的落点字面值。07 也拥有其他技能源中的取名规则和入口分支。来源：spec `Cross-Plan Contract Anchors`。
- 06 拥有派发动作块。本 plan 不改任何 `[[mmw-launch:…]]` 或 `[[mmw-launch-group:…]]` 块。来源：spec `Cross-Plan Contract Anchors`。
- `mmw-grilling` 的范围段自定规则由 07 删除。本 plan 只让 wayfinder 调用方传入范围段，并在集成验收中消费 07 的结果。
- 修改 `mmw-grilling` 前，worker 必须完整读取 `.agents/skills/upstream-skill-fidelity/SKILL.md` 及其要求的材料。新增步骤归该技能第 4 节第 3 类“MMW 接线”。它不是翻译、精简或语义漂移。
- `mmw-research` 只把 research 索引中的“下游怎么用”改为“章节指引”。prototype 索引保持现状。来源：spec 第 15 节。
- 材料缺失照搬 research 报告第 9 节的分类。预期缺失继续。异常缺失必须停下问用户。两类都不得编造内容。
- research 范围快照是 `awslabs/aidlc-workflows` 的 `v2` 分支、短 SHA `2ce654d`、README 版本 `2.5.62`，访问日期是 2026-08-11。完整 SHA 与 `resolveArtifactPath()` 逐字源码仍未取得。
- 本 ticket 没有 prototype 资产。不修改 spec、ticket、research、领域文档、ADR、其他 plan 或产品版本。

## Current State

- `mmw/cli/lib/artifact.sh` 和 `mmw/cli/tests/test_artifact.sh` 当前不存在。01 将创建两份文件，02 将扩展缺省工作名。来源：`docs/plans/mmw-artifact-wiring/01-artifact-path-command.md` 与 `02-work-name-in-task.md`。
- `mmw/cli/lib/issue.sh:39-56` 的 `mmw_issue_children_raw` 已按编号返回 map 的子 issue JSON。它可以提供状态、标题和标签候选。
- `mmw/skills-src/mmw-wayfinder/SKILL.md:36-38` 仍使用 `## 产物目录`。同文件第 67-73 行规定 ticket 正文只有 `Question`。
- `mmw/skills-src/mmw-wayfinder/SKILL.md:89` 仍要求 agent 读取、改写和复读整份 map 正文。
- `mmw/skills-src/mmw-wayfinder/charting.md:35-42` 建 ticket 时只写 `Question`。第 52-56 行 claim research 后只传三项。
- `mmw/skills-src/mmw-wayfinder/charting.md:62-64` 的结论评论没有固定标识和固定小节。map 更新仍由 agent 拼正文。
- `mmw/skills-src/mmw-wayfinder/walking.md:18-34` claim 后直接开工。它没有补全必读材料声明。
- `mmw/skills-src/mmw-wayfinder/walking.md:46-51` 的四行交接不一致。grilling 行只写调用。其余三行各传三项。
- `mmw/skills-src/mmw-wayfinder/walking.md:65-69` 的结论评论没有材料使用记录。map 更新仍由 agent 拼正文。
- `mmw/skills-src/mmw-wayfinder/walking.md:86-94` 的交回评论没有固定标识。读取方取最后一条评论。
- `mmw/skills-src/mmw-wayfinder/closing.md:9` 也从最后一条评论取得交回值。
- `mmw/skills-src/mmw-grilling/SKILL.md:22-32` 的“取得事实”没有先读被点名材料的步骤。上游 `vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md:20` 已要求 agent 自己查可查事实。
- `mmw/skills-src/mmw-research/MAIN.md:104-110` 仍要求 research 索引写“下游怎么用”。
- Graphify 在规划时连续两次由工具端取消。Serena 只为 `issue.sh` 返回了 Bash 符号候选。上述 Markdown 事实均已回到当前技能源逐行确认。

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `mmw/cli/lib/artifact.sh` | Modify（由 01 创建，02 扩展） | 增加 `list` 动作，并生成仓库产物与结论评论候选 |
| `mmw/cli/tests/test_artifact.sh` | Test（由 01 创建，02 扩展） | 在一次性仓库和 GitHub stub 上验证 `artifact list` |
| `mmw/skills-src/mmw-wayfinder/SKILL.md` | Modify | 更新 map 小节标题、ticket 模板和 map 追加规则 |
| `mmw/skills-src/mmw-wayfinder/charting.md` | Modify | 更新建 ticket、claim、research 交接、结论评论和 map 追加 |
| `mmw/skills-src/mmw-wayfinder/walking.md` | Modify | 补全必读材料声明，统一四行交接，并更新两类评论和 map 追加 |
| `mmw/skills-src/mmw-wayfinder/closing.md` | Modify | 按固定标识读取交回评论，并读取 `## 工作名` |
| `mmw/skills-src/mmw-grilling/SKILL.md` | Modify | 在“取得事实”中先检查被点名材料 |
| `mmw/skills-src/mmw-research/MAIN.md` | Modify | 把 research 索引要求改成章节指引 |
| `mmw/skills-pi/`、`mmw/skills-claude-code/`、`mmw/skills-codex/` | Modify（物化） | 保存上述三类技能源的宿主产物 |

## Contracts and Seams

- **Test seam:** 使用真实 `mmw` 命令行。测试在一次性仓库中运行，并用 GitHub stub 提供 map 子 issue。来源：spec `Testing Decisions`。
- **Consumes from 01:** `mmw/cli/artifacts.json` 提供 `research` 与 `prototype` 的类别根。`mmw artifact path` 保留产物引用四项的解析规则。
- **Consumes from 02:** `--name` 缺省时读取 `mmw task state` 的 `bound` 行第四字段。显式 `--name` 不读取当前任务状态。
- **Consumes from 05:** 调用形态固定为 `mmw issue append <map 编号> --section "Decisions so far" --line "<一行概要>"`。成功表示旧行与新增行都保留。
- **Consumes from 07:** 07 删除 `mmw-grilling` 自定范围段的规则。08 给四类下游调用显式传工作名和范围段。两边集成后只有调用方决定范围段。
- **Produces for 11:** 08 改完的技能源供 11 执行落点字面值校验。本 plan 不修改 11 的测试。
- **List call:** `mmw artifact list [--name <工作名>] [--map <map 编号>]`。
- **Repository candidates:** 只列 `<类别根>/<工作名>/` 下已经保存的 research 和 prototype。每项输出 spec 第 6 节的一行键值形态。范围段存在时输出纯 issue 编号。
- **Saved boundary:** research 或 prototype 的索引 `README.md` 存在时，该目录才算已保存。空目录和过程目录不进入候选。
- **Tracker candidates:** 给出 `--map` 时，只列该 map 下状态为 closed、标签以 `wayfinder:` 开头的子 issue。每项带 issue 编号、`结论评论` 字样和 ticket 标题。
- **No-map behavior:** 没有 `--map` 时不调用 GitHub。命令只列仓库候选，并以成功状态结束。
- **List scope:** 命令不判断候选与当前 ticket 是否相关。它不改 decision ticket 正文。
- **Ticket declaration:** 建 ticket 时写当时已知的条目。claim 后运行 `artifact list`，再把后来产生且相关的条目补入原节。既有条目必须保留。
- **Five handoff values:** 四类下游都收到 `Question`、全部仓库产物引用、全部结论评论 issue 编号、工作名和范围段。
- **Missing material:** 生产 ticket 按设计未运行，或用户选择不保存 research，属于预期缺失。生产方已经运行且声明内容应存在，但内容找不到，属于异常缺失。
- **Conclusion comment:** 第一行是 `<!-- mmw:conclusion -->`。材料使用记录逐条覆盖必读材料声明中的每个条目。
- **Handback comment:** 第一行是 `<!-- mmw:handback -->`。`## 交回` 中分别写任务分支名、HEAD SHA 和基点 SHA。
- **Migration:** 不改历史 ticket 或历史 research 索引。新技能行为只约束后续运行。

## Implementation

1. **依赖合同已经可执行**
   - Change: 确认 01、02 和 05 已集成。打开它们的最终实现和测试，核对本 plan 消费的字段与调用形态。
   - Change: 确认 `artifact.sh` 与 `test_artifact.sh` 已存在。确认 `artifact path` 可以缺省读取工作名。
   - Change: 运行 05 的 issue 测试。确认追加动作的参数和成功条件没有漂移。
   - Files: 只读 `mmw/cli/lib/artifact.sh`、`mmw/cli/tests/test_artifact.sh`、`mmw/cli/lib/issue.sh`、`mmw/cli/tests/test_issue.sh`。
   - Verify: `bash mmw/cli/tests/test_artifact.sh` → 01、02 的既有用例通过。
   - Verify: `bash mmw/cli/tests/test_issue.sh` → 05 的追加与父 issue 用例通过。

2. **`mmw artifact list` 给出完整候选**
   - Change: 先为显式工作名、缺省工作名、无 map、有 map 和空清单写失败测试。
   - Change: fixture 同时放入 scoped 与 unscoped 的 research 和 prototype。只给已保存的产物写 `README.md`。
   - Change: GitHub stub 同时返回 open ticket、closed decision ticket 和 closed 非 wayfinder 子 issue。只有 closed decision ticket 进入输出。
   - Change: 实现 `list` 动作。类别根只读产物落点数据。工作名缺省规则复用 02 的现有解析。
   - Change: 复用 `mmw_issue_children_raw` 取得 map 子 issue。不要复制 sub-issues 分页与补齐逻辑。
   - Change: 输出稳定排序。仓库项使用固定键值形态。tracker 项保留 issue 编号和完整标题。
   - Change: 没有 `--map` 时禁止调用 GitHub。不存在对应类别根时返回空清单，不建立目录。
   - Files: `mmw/cli/lib/artifact.sh`、`mmw/cli/tests/test_artifact.sh`。
   - Verify: `bash mmw/cli/tests/test_artifact.sh` → 仓库、tracker、缺省工作名、过滤、空清单和无副作用用例通过。

3. **ticket 声明在建图和认领两处闭合**
   - Change: 编辑前完整读取 wayfinder 的 `SKILL.md`、`charting.md`、`walking.md` 和 `closing.md`。
   - Change: 把 `SKILL.md` 的 ticket 模板改成 `Question` 与必读材料声明两节。没有材料时写 `无`。
   - Change: `charting.md` 建 ticket 时写当时已知的全部条目。`walking.md` 后续建 ticket 时使用同一模板。
   - Change: 在 `charting.md` 与 `walking.md` 的 claim 成功之后运行 `mmw artifact list --name <工作名> --map <map 编号>`。
   - Change: 从候选中选择与当前 `Question` 相关的材料。把新条目补入自己的 ticket 正文，并保留已有条目。
   - Change: 开工前读取声明中的全部条目。按预期缺失与异常缺失两类处理。
   - Change: 只把 map 正文标题改成 `## 工作名`。同文件其他落点字面值留给 07。
   - Files: `mmw/skills-src/mmw-wayfinder/SKILL.md`、`charting.md`、`walking.md`、`closing.md`。
   - Verify: 逐行读取四份技能源 → template、建 ticket、两处 claim 和全部 `## 工作名` 读写使用同一合同。

4. **四类交接和两类评论保留完整材料痕迹**
   - Change: 重写 `walking.md` 的四行交接。每行都传五项。两类必读材料均不得丢失。
   - Change: `charting.md` 直接启动 research 时也传同样五项。
   - Change: 结论评论增加固定标识和三个固定小节。材料使用记录逐项写“用上”或“未用”，并写明理由。
   - Change: 交回评论增加固定标识与 `## 交回`。`walking.md` 和 `closing.md` 按标识定位，不再读取最后一条评论。
   - Change: 把 `SKILL.md`、`charting.md` 和 `walking.md` 的手工 map 改写说明换成 05 的追加命令。
   - Files: `mmw/skills-src/mmw-wayfinder/SKILL.md`、`charting.md`、`walking.md`、`closing.md`。
   - Verify: 逐行读取四份技能源 → 四行交接、charting research 交接、两类评论和三处 map 更新符合固定合同。

5. **对谈先读材料，research 索引只负责指路**
   - Change: 编辑 `mmw-grilling` 前完整读取 `upstream-skill-fidelity`、`writing-for-agents`、`SKILL-MECHANICS.md` 和上游 grilling `SKILL.md`。
   - Change: 编辑 `mmw-research` 前完整读取其 `SKILL.md`、`MAIN.md`、`INTERNAL.md`、`EXTERNAL.md` 和 `EVIDENCE.md`。
   - Change: 把本次差异登记为第 3 类“MMW 接线”。保留上游步骤顺序与现有中文正文。
   - Change: 在“取得事实”中增加第一步。提出问题前，先检查被点名材料是否已经回答该问题。
   - Change: 不删除范围段自定规则。该行归 07。本步骤只验证 07 集成后该规则消失。
   - Change: 把 `mmw-research/MAIN.md` 的索引要求改成 `## 章节指引`。它使用两列表逐节说明内容，不写 ticket 编号，也不限定读取章节。
   - Change: 不修改 `mmw-prototype` 或历史 research 索引。
   - Files: `mmw/skills-src/mmw-grilling/SKILL.md`、`mmw/skills-src/mmw-research/MAIN.md`。
   - Verify: 逐行对照上游与当前 grilling → 新增内容只承载现有查事实方法，分类为 MMW 接线。
   - Verify: 逐行读取 research 与 prototype 技能源 → 章节指引只进入 research 索引合同。

6. **物化全部宿主并完成整仓回归**
   - Change: 运行全宿主物化。只让命令更新技能产物，不手改生成文件。
   - Change: 运行物化检查，确认三类宿主产物与技能源一致。
   - Change: 运行局部 CLI 测试和完整测试入口。
   - Files: `mmw/skills-pi/`、`mmw/skills-claude-code/`、`mmw/skills-codex/` 中受影响的 wayfinder、grilling 和 research 文件。
   - Verify: `mmw/cli/mmw skills materialize --host all` → 三个宿主的技能产物完成更新。
   - Verify: `mmw/cli/mmw skills materialize --host all --check` → 没有物化漂移。
   - Verify: `bash mmw/cli/tests/test_artifact.sh` → `artifact list` 全部用例通过。
   - Verify: `bash mmw/test.sh` → 全部测试通过，退出码为 0。
   - Verify: `git diff --check` → 没有空白错误。

## Acceptance

| Ticket 验收 | 证明方式 | 命令或人工结果 |
| --- | --- | --- |
| decision ticket 正文使用两节 | 逐行检查模板、charting 建 ticket 和 walking 新建 ticket 三处 | `git diff -- mmw/skills-src/mmw-wayfinder/` → 三处都写 `## Question` 与 `## 必读材料声明` |
| claim 后补全必读材料声明 | 检查 charting 与 walking 两处 claim；确认命令位于开工之前 | `git diff -- mmw/skills-src/mmw-wayfinder/charting.md mmw/skills-src/mmw-wayfinder/walking.md` → 两处都运行 `mmw artifact list` 并补入相关条目 |
| 清单覆盖仓库与 tracker 候选 | 一次性仓库和 GitHub stub 覆盖 scoped、unscoped、open、closed 和非 wayfinder 子 issue | `bash mmw/cli/tests/test_artifact.sh` → 只输出已保存 research、prototype 和 closed decision ticket |
| 不给 map 时只列仓库候选 | 让 GitHub stub 在被调用时失败 | `bash mmw/cli/tests/test_artifact.sh` → 命令成功，且 stub 没有调用记录 |
| 四行交接都传五项 | 人工逐行检查交接表；分别放入仓库条目与 tracker 条目 | `git diff -- mmw/skills-src/mmw-wayfinder/walking.md` → 四行都传 Question、两类材料、工作名和范围段 |
| 结论评论有材料使用记录 | 人工检查固定标识与三个固定小节 | `git diff -- mmw/skills-src/mmw-wayfinder/charting.md mmw/skills-src/mmw-wayfinder/walking.md` → 每项必读材料都有使用结果或未用理由 |
| 对谈先看被点名材料 | 对照上游第 20 行与新增步骤 | `git diff -- mmw/skills-src/mmw-grilling/SKILL.md` → 新增步骤位于“取得事实”，并记录为 MMW 接线 |
| 下游不再自定范围段 | 消费 07 的集成结果；08 只验证，不修改 07 分区 | `rg -n '解决 Wayfinder 的 decision ticket 时用' mmw/skills-src/mmw-grilling/SKILL.md` → 无命中；wayfinder 四行均传范围段 |
| research 索引改成章节指引 | 检查 `MAIN.md` 的 README 要求 | `git diff -- mmw/skills-src/mmw-research/MAIN.md` → 使用 `## 章节指引` 两列表，不写 ticket 编号或读取范围 |
| prototype 索引保持现状 | 确认实现 diff 没有 prototype 技能源 | `git diff --name-only` → 不含 `mmw/skills-src/mmw-prototype/` |
| 材料缺失分成两类 | 人工检查认领后的材料读取分支 | `git diff -- mmw/skills-src/mmw-wayfinder/` → 预期缺失继续，异常缺失停下问用户，两者都不编造内容 |
| map 决定索引消费 05 | 检查三处旧手工说明均已替换 | `rg -n '改 map 正文之前' mmw/skills-src/mmw-wayfinder/` → 无命中；`rg -n 'mmw issue append' mmw/skills-src/mmw-wayfinder/` → 三处调用 |
| 两类评论可稳定定位 | 检查写入端与读取端使用同一标识 | `git diff -- mmw/skills-src/mmw-wayfinder/` → 结论评论与交回评论分别使用固定 HTML 标识 |
| 技能源已物化并完成回归 | 比较全部宿主产物，再运行统一测试入口 | `mmw/cli/mmw skills materialize --host all --check` 与 `bash mmw/test.sh` → 都以 0 退出 |

## Browser Acceptance

不适用。此 ticket 没有界面。

## Rollback and Gates

- 依赖关卡是 01、02、05 已集成。任一接口缺失时停止实施，不在本 plan 重建它。
- 跨 plan 关卡是 07 已删除下游自定范围段。07 未集成时，08 的独占分区可以完成，但 ticket `#45` 的对应验收不能判定通过。
- `artifact list` 的 GitHub 测试只使用 stub。实现阶段不对真实 issue 执行追加、编辑、评论或关闭。
- 技能源和三类技能产物必须同一提交回滚。只回滚一侧会留下物化漂移。
- 本 ticket 没有数据迁移。代码回滚使用 Git revert。已经由用户运行过的 tracker 写入不会自动撤销。
