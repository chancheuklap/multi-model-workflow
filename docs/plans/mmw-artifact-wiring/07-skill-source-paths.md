---
ticket: 44
artifact_refs: []
---

# Plan: 技能源落点改写与撞名查重

**Goal:** 活跃技能源只通过工作名和 `mmw artifact path` 取得产物落点。两个当场取名位置在首次写文件前处理撞名。三个宿主的技能产物与技能源同步。
**Source spec:** `docs/specs/mmw-artifact-wiring/mmw-artifact-wiring.md`。本 ticket 实施时改名为 `docs/specs/mmw-artifact-wiring/spec.md`。
**Source ticket:** GitHub issue `#44`

## Constraints

- 本 plan 在 01 和 02 之后实施。01 提供 `mmw artifact path`。02 提供任务状态中的工作名。（ticket `#44` 的 `Blocked by`）
- 技能源不再自行拼接路径形状。每个需要落点的位置写出完整的 `mmw artifact path` 命令行。（spec 第 19 节）
- 固定类别根不带占位符时保持原文。`docs/adr/`、`docs/context/` 和 `.out-of-scope/` 的目录级读取属于允许形态。（spec 第 19 节与 Testing Decisions）
- scratch 根和 reviews 根来自目标仓库配置。技能源不得出现 `.scratch/` 或 `.reviews/` 默认值。（spec 第 19 节）
- 工作名只从 `mmw task state` 的 `bound` 输出第四字段读取。不得从任务分支名、worktree 物理目录名或入口类型推导。（spec 第 5、19 节；plan 02）
- 任务分支名与工作名是两个值。`mmw-start` 的类型前缀表只继续约束任务分支名。（spec 第 5、19 节）
- research 主题和 prototype 变体组是两个查重位置。其他类别不增加查重步骤。（spec 第 16 节；ADR `0011`）
- 查重不询问用户，也不写进交回内容。重新取名失败时从 `-02` 开始使用两位序号。（spec 第 16 节）
- `mmw/skills-src/mmw-setup/` 是旧背景材料。扫描和改写都排除它。（`AGENTS.md` 修改规则）
- `mmw/skills-src/mmw-triage/examples.md` 是上游材料。它的路径写法保持不变。（spec Out of Scope）
- handoff 的仓库外落点保持不变。本 ticket 不修改 `mmw/skills-src/handoff/`。（spec Out of Scope）
- wayfinder 的交接表、ticket 正文模板、认领步骤和 map 正文小节标题归 08。07 不修改这些分区。（spec `Cross-Plan Contract Anchors`）
- wayfinder 和其他技能中的派发动作块归 06。07 不修改 `[[mmw-launch:…]]` 或 `[[mmw-launch-group:…]]`。（spec `Cross-Plan Contract Anchors`）
- 07 只处理其余位置的落点字面值、取名规则和入口分支判断。08 另行修改对谈技能的取得事实分区和 research 索引分区。（spec `Cross-Plan Contract Anchors`）
- 09 负责 Wiki 退役、界面 evidence 类别退役和收尾语义删除。07 在共享句子中只替换落点表达，不提前删除 09 的行为。（ticket `#42`；spec 第 17、19 节）
- 11 独占 `test_skill_paths.sh`、`test_skill_refs.sh` 和测试入口。07 不新增机械校验。（spec `Cross-Plan Contract Anchors`）
- 技能源修改后必须物化。不得手工修改宿主技能产物。（`AGENTS.md` 唯一事实来源）
- 本 ticket 没有 prototype 资产，也没有 research。（ticket `#44`）

## Current State

- spec 处数表的数值来自包含 `mmw-setup/` 的扫描，但表前文字要求排除它。按仓库规则排除该目录后，活跃技能源里的处数是下表数值。

| 字面值 | 活跃技能源行数 |
| --- | ---: |
| `.out-of-scope/` | 28 |
| `.scratch/` | 28 |
| `docs/specs/` | 14 |
| `docs/adr/` | 10 |
| `docs/plans/` | 10 |
| `docs/context/` | 11 |
| `.reviews/` | 10 |
| `docs/prototypes/` | 4 |
| `docs/research/` | 6 |
| `docs/evidence/` | 3 |
| `.dispatch/` | 2 |
| `<产物目录>` | 27 |

- 上述字面值分布在 20 个技能中。部分技能只有允许保留的固定类别根。
- `mmw/cli/lib/materialize_skills.py:20-25` 指定技能源和三个宿主输出目录。该文件第 323 至 337 行读取并展开技能源。第 339 至 362 行执行一致性检查或写出产物。
- `mmw/cli/mmw:354-383` 提供 `mmw skills materialize --host all [--check]`。`mmw/test.sh:42-43` 运行现有物化测试。
- Graphify 查询被工具取消。Serena 当前只启用 Bash，不能解析物化器的 Python 符号。物化关系改用上述当前源码逐行核对。
- 当前 spec 文件仍使用旧文件名。旧路径是 `docs/specs/mmw-artifact-wiring/mmw-artifact-wiring.md`。

### 20 个技能的核对清单

| 技能 | 当前源码位置 | 07 的处置 |
| --- | --- | --- |
| `mmw-closing` | `SKILL.md:10,21,45-46,88,96-106` | 把仍需表达的 spec、plan、scratch 和 review 落点改为命令。工作名读任务状态第四字段。Wiki、evidence 和 dispatch 的删除语义留给 09。 |
| `mmw-diagnosing-bugs` | `SKILL.md:21-30` | 删除普通任务与 Wayfinder 的落点推导表。使用 `mmw artifact path scratch [--issue <编号>] --sub diagnosis/<短名>`。 |
| `mmw-domain-modeling` | `ADR-FORMAT.md:3`、`CONTEXT-FORMAT.md:38-61`、`SKILL.md:26-74` | 不改。这里是固定类别根、具体示例或目录级读取。 |
| `mmw-grilling` | `SKILL.md:62` | 把共同理解记录改为 `mmw artifact path scratch [--issue <编号>] --sub understanding.md`。删除自定工作名。范围段自定规则的删除归 08。 |
| `mmw-implement` | `SKILL.md:16,99,135`；`worker-brief.md:18` | spec 与界面 evidence 的落点改为命令。固定的领域文档和 ADR 目录级读取保持不变。09 负责删除 Wiki 和长期 evidence 语义。 |
| `mmw-improve-codebase-architecture` | `SKILL.md:32,94-102` | `docs/adr/` 保持不变。建立或绑定任务时传工作名。不得把任务分支 slug 当工作名。 |
| `mmw-integrate` | `SKILL.md:79` | 集成记录改为 `mmw artifact path review --sub integration-<日期>.md`。同日序号规则保持。 |
| `mmw-prototype` | `SKILL.md:21,26-47`；`UI.md:36` | 删除产物目录取名表。读取工作名，并用 prototype 与 scratch 类别命令。`UI.md` 在问题 slug 取名后加入查重步骤。 |
| `mmw-release` | `SKILL.md:16-17` | 终审记录改为 `mmw artifact path review --sub final.md`。 |
| `mmw-research` | `MAIN.md:14-16,31,78-88,114-120` | 删除入口决定产物目录的三行。工作名读任务状态。research 用主题作为 `--sub`。scratch 用对应类别命令。主题取名后加入查重步骤。 |
| `mmw-review` | `SKILL.md:30,32,58,73,77,88` | understanding、spec、plan、evidence 和四类审查记录都改为命令或上游点名的产物引用。06 负责不落盘的 task 动作。 |
| `mmw-reviewer` | `references/spec-alignment.md:9` | 不改。`docs/context/` 和 `docs/adr/` 都是不带占位符的目录级读取。 |
| `mmw-start` | `SKILL.md:51-69,82-96`；`resuming.md:13,21-29` | 类型前缀只用于任务分支名。建树时另传工作名。恢复时用 spec、plan 和 review 的命令，不从分支名推导工作名。09 负责归档检查语义。 |
| `mmw-to-plan` | `SKILL.md:19,45,72,107` | spec 与每份 plan 的落点改为命令。批量审查传逐份 plan 路径，不传手拼目录。 |
| `mmw-to-spec` | `SKILL.md:26-40,55,81-84,95` | 删除五行入口取名表。读取工作名。spec 与 spec issue 正文的 scratch 文件都改为命令。固定 `docs/adr/` 读取保持不变。 |
| `mmw-to-tickets` | `SKILL.md:14,24,80-84,107-115` | 工作名由任务状态取得。prototype 和 research 只使用产物引用。ticket 正文 scratch 路径与 plan 文件路径改为命令。 |
| `mmw-triage` | `SKILL.md:23,87-110`、`OUT-OF-SCOPE.md:3-103`、`examples.md:46-80` | `SKILL.md` 与 `OUT-OF-SCOPE.md` 的固定类别根保持不变。`examples.md` 是上游材料，整份保持不变。 |
| `mmw-wayfinder` | `SKILL.md:31-73`、`charting.md:5-62`、`walking.md:7-67`、`closing.md:41-53` | 07 只改 `charting.md` 的非 ticket 模板落点和 `walking.md` 的路径表、答案临时文件。`SKILL.md` 的 map 与 ticket 模板、`charting.md` 的 ticket 模板、`walking.md` 的认领和交接表、`closing.md` 的移交归 08。 |
| `to-questionnaire` | `SKILL.md:24-33` | 删除入口推导表。使用 `mmw artifact path scratch [--issue <编号>] --sub questionnaire/<主题>.md`。 |
| `wizard` | `SKILL.md:46-57` | 删除入口推导表。使用 `mmw artifact path scratch [--issue <编号>] --sub wizard/<流程>.sh`。 |

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `docs/specs/mmw-artifact-wiring/mmw-artifact-wiring.md` → `docs/specs/mmw-artifact-wiring/spec.md` | Docs·Rename | 让本 effort 的 spec 使用固定文件名 `spec.md`。内容和元数据保持不变。 |
| `mmw/skills-src/mmw-closing/SKILL.md` | Modify | 只改 07 拥有的工作名和落点表达。保留 09 的删除语义。 |
| `mmw/skills-src/mmw-diagnosing-bugs/SKILL.md` | Modify | 用工作名和 scratch 命令替换入口推导。 |
| `mmw/skills-src/mmw-grilling/SKILL.md` | Modify | 改共同理解记录的落点和工作名。 |
| `mmw/skills-src/mmw-implement/SKILL.md` | Modify | 改 spec 与界面 evidence 的落点表达。 |
| `mmw/skills-src/mmw-improve-codebase-architecture/SKILL.md` | Modify | 建立或绑定任务时传工作名。 |
| `mmw/skills-src/mmw-integrate/SKILL.md` | Modify | 改集成记录落点。 |
| `mmw/skills-src/mmw-prototype/SKILL.md` | Modify | 删除产物目录取名和入口分支。用工作名与路径命令。 |
| `mmw/skills-src/mmw-prototype/UI.md` | Modify | 给问题 slug 加入撞名处理。 |
| `mmw/skills-src/mmw-release/SKILL.md` | Modify | 改 final 审查记录落点。 |
| `mmw/skills-src/mmw-research/MAIN.md` | Modify | 删除产物目录取名。改 research 与 scratch 落点。加入主题撞名处理。 |
| `mmw/skills-src/mmw-review/SKILL.md` | Modify | 改审查输入、界面 evidence 和审查记录落点。 |
| `mmw/skills-src/mmw-start/SKILL.md` | Modify | 分离任务分支名和工作名。建立任务时传工作名。 |
| `mmw/skills-src/mmw-start/resuming.md` | Modify | 用工作名和路径命令恢复 spec、plan 与审查记录。 |
| `mmw/skills-src/mmw-to-plan/SKILL.md` | Modify | 用命令取得 spec 与每份 plan。 |
| `mmw/skills-src/mmw-to-spec/SKILL.md` | Modify | 删除入口取名表。用工作名、spec 命令和 scratch 命令。 |
| `mmw/skills-src/mmw-to-tickets/SKILL.md` | Modify | 用产物引用和命令取得输入、ticket 正文与 plan 路径。 |
| `mmw/skills-src/mmw-wayfinder/charting.md` | Modify | 只改 07 分区内的工作名和落点字面值。 |
| `mmw/skills-src/mmw-wayfinder/walking.md` | Modify | 只改 07 分区内的路径表和答案临时文件落点。 |
| `mmw/skills-src/to-questionnaire/SKILL.md` | Modify | 用工作名与 questionnaire 的 scratch 命令。 |
| `mmw/skills-src/wizard/SKILL.md` | Modify | 用工作名与 wizard 的 scratch 命令。 |
| `mmw/skills-pi/` 中上述对应文件 | 生成产物 | 由全宿主物化同步。 |
| `mmw/skills-claude-code/` 中上述对应文件 | 生成产物 | 由全宿主物化同步。 |
| `mmw/skills-codex/` 中上述对应文件 | 生成产物 | 由全宿主物化同步。 |

## Contracts and Seams

- **Test seam:** 使用技能源 Markdown 文本。11 的两条正则验证类别根加占位符和工作目录根默认值。07 先用同范围的只读检索做交付前审计。（spec Testing Decisions）
- **Consumes from 01:** 公开接口是 `mmw artifact path <类别> [--name <工作名>] [--issue <编号>] [--sub <类别内细分>] [--absolute]`。成功路径只从标准输出读取。提醒位于标准错误。（plan 01）
- **Consumes from 02:** `mmw task state` 的已绑定输出是 `bound <任务分支> <HEAD> <工作名>`。07 只取第四字段作为当前工作名。（plan 02）
- **Task creation:** `mmw task new` 与 `mmw task bind` 继续接收任务分支名。调用方另用 `--name <工作名>` 传工作名。已有父任务时按 02 的继承合同处理。
- **Command selection:** 每一处按下表选命令。命令参数必须写到能返回目标文件或目标目录的完整程度。

| 目标 | 命令形态 |
| --- | --- |
| 当前 spec | `mmw artifact path spec` |
| 一份 plan | `mmw artifact path plan --sub <两位编号>-<ticket短名>.md` |
| research | `mmw artifact path research [--issue <编号>] --sub <主题>` |
| prototype 内的目标细分 | `mmw artifact path prototype [--issue <编号>] --sub <类别内细分>` |
| 共同理解记录 | `mmw artifact path scratch [--issue <编号>] --sub understanding.md` |
| 界面 evidence | `mmw artifact path scratch [--issue <编号>] --sub evidence` |
| bug 诊断材料 | `mmw artifact path scratch [--issue <编号>] --sub diagnosis/<短名>` |
| questionnaire | `mmw artifact path scratch [--issue <编号>] --sub questionnaire/<主题>.md` |
| wizard | `mmw artifact path scratch [--issue <编号>] --sub wizard/<流程>.sh` |
| 审查记录 | 按关卡运行 `mmw artifact path review --sub understanding.md`、`spec.md`、`plan.md` 或 `final.md` |
| 集成记录 | `mmw artifact path review --sub integration-<日期>[-<序号>].md` |
| 否决记录文件 | `mmw artifact path out-of-scope --sub <概念>.md`。只有需要具体文件时使用。 |

- **Directory reads:** 需要一批 plan 时，先从 ticket 取得每份 `--sub` 值，再逐份解析。不得用 `docs/plans/<工作名>/` 代替文件清单。
- **Artifact references:** 消费已有 prototype 或 research 时，先读上游点名的产物引用。不得从旧路径示例反推工作名、范围段或类别内细分。
- **Fixed roots:** 目录级读取 `docs/adr/`、`docs/context/` 和 `.out-of-scope/` 可以保留。具体文件带占位符时必须改用命令。
- **Collision:** research 在 `MAIN.md` 第 4 节的主题名确定后查重。prototype 在 `UI.md` 第 3 节的问题 slug 确定后查重。
- **Collision algorithm:** 写第一个文件前列目标路径的父目录。目标存在时先读已有索引。没有索引时读全部文件名和一级标题。确认是不同问题后重新取名。仍取不出时从 `-02` 开始加两位序号。
- **Produces for 11:** `mmw/skills-src/` 中 07 拥有的分区不再出现“类别根加占位符”。这些分区也不再出现工作目录根默认值。命令里的类别参数值必须来自 01 的类别集合。
- **Shared ownership with 06:** 07 不修改派发动作块。06 物化新 task 接口时保留 07 改写后的周围正文。
- **Shared ownership with 08:** 08 修改 wayfinder 受保护分区。08 还删除 grilling 的范围段自定规则，并修改 research 的章节指引。07 只改这些位置之外的落点表达。
- **Generated outputs:** 技能源是提供方。三个宿主技能目录是消费方。物化器整块替换宿主动作，不改变共享路径语义。
- **Migration:** spec 只改文件名。没有历史产物迁移命令。其他 spec 与 plan 文件不在本 ticket 改名。

## Implementation

1. **确认 01 与 02 的接口已经可用**
   - Change: 运行真实 CLI，确认显式工作名和当前任务工作名都能解析 spec 路径。
   - Change: 确认任务状态的第四字段是工作名。不要在技能源里复制解析规则。
   - Files: 只读 `mmw/cli/artifacts.json`、`mmw/cli/lib/artifact.sh`、`mmw/cli/lib/task.sh`。
   - Verify: `mmw/cli/mmw artifact path spec --name mmw-artifact-wiring` → 输出 `docs/specs/mmw-artifact-wiring/spec.md`。
   - Verify: `mmw/cli/mmw task state` → 已绑定状态输出四个字段，第四字段是 `mmw-artifact-wiring`。

2. **把工作名读取收口到任务状态**
   - Change: 按 20 技能清单修改 `mmw-start`、`mmw-improve-codebase-architecture`、`mmw-prototype`、`mmw-research`、`mmw-to-spec`、`mmw-diagnosing-bugs`、`to-questionnaire`、`wizard` 和 07 拥有的 wayfinder 分区。
   - Change: 删除各技能自己的产物目录取名、入口分类和任务分支反推。
   - Change: 保留任务分支的 slug 规则。建立或绑定任务时通过 `--name` 另传工作名。
   - Change: 不修改 `walking.md` 的认领步骤。该分区归 08。
   - Files: 上述技能在 `Change Map` 中列出的源文件。
   - Verify: `rg -n --glob '!**/mmw-setup/**' '<产物目录>|## 产物目录|普通任务用当前任务 slug|任务分支名.*工作名' mmw/skills-src` → 只剩 08 拥有的 map、ticket、认领和交接分区，以及明确讨论任务分支名的句子。

3. **改写长期产物的落点**
   - Change: 把 spec、plan、prototype、research 和具体否决记录的路径拼接改成完整命令。
   - Change: 消费已有 prototype 或 research 时改读产物引用。不要从 README 路径反推类别参数。
   - Change: 需要一批 plan 时逐份解析，不保留 plan 目录字面值。
   - Change: 固定类别根的目录级读取保持不变。
   - Files: `mmw-implement`、`mmw-review`、`mmw-start`、`mmw-to-plan`、`mmw-to-spec`、`mmw-to-tickets`、`mmw-prototype`、`mmw-research` 和 07 的 wayfinder 分区。
   - Verify: `rg -n --pcre2 --glob '*.md' --glob '!**/mmw-setup/**' --glob '!**/mmw-triage/examples.md' '(?:\.out-of-scope/|docs/specs/|docs/adr/|docs/plans/|docs/context/|docs/prototypes/|docs/research/|docs/evidence/)[^`[:space:]]*<[^>]+>' mmw/skills-src` → 07 拥有的分区零命中。08 拥有的分区单独登记，不由 07 修改。

4. **改写 scratch 与 review 落点**
   - Change: 把所有 07 拥有的 `.scratch/` 和 `.reviews/` 写法改成 `scratch` 或 `review` 类别命令。
   - Change: 明确覆盖六个不带占位符的默认根。它们位于 diagnosing 第 30 行、wizard 第 55 行、questionnaire 第 31 行、closing 第 104 与 106 行、resuming 第 13 行。
   - Change: 界面 evidence 使用 scratch 类别。用户要求长期保存时只写“由用户指定位置”，不建立已退役的类别。
   - Change: 不删除 Wiki、dispatch 或收尾步骤。09 负责这些行为。
   - Files: `mmw-closing`、`mmw-diagnosing-bugs`、`mmw-grilling`、`mmw-implement`、`mmw-integrate`、`mmw-prototype`、`mmw-release`、`mmw-research`、`mmw-review`、`mmw-start/resuming.md`、`mmw-to-spec`、`mmw-to-tickets`、`to-questionnaire`、`wizard` 和 07 的 wayfinder 分区。
   - Verify: `rg -n -F --glob '!**/mmw-setup/**' -e '.scratch/' -e '.reviews/' mmw/skills-src` → 07 拥有的分区零命中。任何剩余命中都必须落在 08 的受保护分区。

5. **在 wayfinder 的分区边界内完成改写**
   - Change: `charting.md` 只改 map 正文临时文件、research 入口、答案临时文件和 07 拥有的工作名规则。
   - Change: `walking.md` 只改资产路径表和答案临时文件。
   - Change: 不改 `SKILL.md` 的 map 正文模板和 ticket 模板。
   - Change: 不改 `charting.md` 的 ticket 正文模板。
   - Change: 不改 `walking.md` 的认领步骤和四行交接表。
   - Change: 不改 `closing.md` 的移交分区。
   - Files: `mmw/skills-src/mmw-wayfinder/charting.md`、`mmw/skills-src/mmw-wayfinder/walking.md`。
   - Verify: `git diff -- mmw/skills-src/mmw-wayfinder/` → 差异只位于上述 07 分区。受保护分区逐字不变。

6. **给两个当场取名位置加查重**
   - Change: 在 research 主题名确定后加入完整查重动作。
   - Change: 在 prototype 问题 slug 确定后加入同一动作。
   - Change: 不按 `research` 和 `prototype` 枚举一般规则。正文只说明当前这个当场取名步骤必须查重。
   - Change: 保留后续轮次原地修改的规则。查重只发生在首次写文件前。
   - Files: `mmw/skills-src/mmw-research/MAIN.md`、`mmw/skills-src/mmw-prototype/UI.md`。
   - Verify: `rg -n '父目录|重新取名|-02|不问用户|不报告' mmw/skills-src/mmw-research/MAIN.md mmw/skills-src/mmw-prototype/UI.md` → 两处都写明完整处置。

7. **把本 effort 的 spec 改成固定文件名**
   - Change: 移动当前 spec 到 `docs/specs/mmw-artifact-wiring/spec.md`。
   - Change: 保留元数据块、正文和 Git 历史。不要复制成两份。
   - Change: 不修改其他 plan 文件。它们的 Source spec 路径由主 agent 在跨 plan 收口时统一处置。
   - Files: `docs/specs/mmw-artifact-wiring/mmw-artifact-wiring.md`、`docs/specs/mmw-artifact-wiring/spec.md`。
   - Verify: `test -f docs/specs/mmw-artifact-wiring/spec.md && test ! -e docs/specs/mmw-artifact-wiring/mmw-artifact-wiring.md` → 新文件存在，旧文件不存在。

8. **完成 20 技能审计并物化**
   - Change: 按 20 技能清单逐行核对。三个只需核对的技能和三类上游排除项不得产生 diff。
   - Change: 运行全宿主物化。只保留由本 ticket 技能源产生的对应技能产物差异。
   - Change: 再运行物化检查，确认三个宿主没有漂移。
   - Files: `mmw/skills-pi/`、`mmw/skills-claude-code/`、`mmw/skills-codex/` 中对应文件。
   - Verify: `mmw/cli/mmw skills materialize --host all` → 三个宿主完成物化。
   - Verify: `mmw/cli/mmw skills materialize --host all --check` → 退出 0。
   - Verify: `git diff --exit-code -- mmw/skills-src/mmw-setup mmw/skills-src/mmw-triage/examples.md mmw/skills-src/handoff` → 三类排除项没有改动。

9. **执行整仓交付关卡**
   - Change: 先运行 07 的文本审计。11 尚未实施时，不自行新建它的测试文件。
   - Change: 运行物化测试和完整测试入口。
   - Files: 无额外文件。
   - Verify: `uv run --quiet --with pytest python -m pytest mmw/cli/tests/test_materialize_skills.py -q` → 物化测试通过。
   - Verify: `bash mmw/test.sh` → 全部测试通过，退出码为 0。
   - Verify: `git diff --check` → 没有空白错误。

## Acceptance

| Ticket 验收 | 证明方式 | 命令或人工结果 |
| --- | --- | --- |
| 20 个技能里的占位符落点完成改写 | 按 20 技能清单逐项核对。固定类别根和排除项另行标明 | 第 3 步 PCRE 检索 → 07 分区零命中；08 分区单独登记 |
| 工作目录根默认值清零 | 全量检索 scratch 根和 reviews 根，并抽验六个不带占位符的位置 | 第 4 步固定字符串检索 → 07 分区零命中；六个位置全部改为术语或命令 |
| 工作名不再由占位符或分支名承担 | 检查任务状态第四字段的读取，以及 `--name` 传递 | 第 2 步检索 → 只剩 08 受保护分区和任务分支自身的 slug 规则 |
| 技能自己的取名规则删除 | 抽验 prototype、research、grilling 和 wayfinder charting 的旧规则 | `rg -n '给这项工作起一个名字当作|普通任务用当前任务 slug|产物目录.*短横线名字'` → 07 分区零命中 |
| 入口分支判断删除 | 抽验 to-spec、diagnosing、questionnaire 与 wizard | 四处都只读取工作名，并按是否有范围段传 `--issue` |
| spec 使用新文件名 | 检查新旧两个精确路径 | 第 7 步 `test` 命令 → 新文件存在，旧文件不存在 |
| 两个当场取名位置都查重 | 核对 research 主题和 prototype 问题 slug 的完整处置 | 第 6 步检索 → 两处都有父目录、索引、重新取名和 `-02` 兜底 |
| 上游材料路径不变 | 对排除目录和文件运行精确 diff | 第 8 步 `git diff --exit-code` → 退出 0 |
| 三个宿主技能产物同步 | 先物化，再用只读模式逐文件比较 | `mmw/cli/mmw skills materialize --host all --check` → 退出 0 |
| 完整回归通过 | 运行仓库唯一完整测试入口 | `bash mmw/test.sh` → 退出 0 |

## Browser Acceptance

不适用。

## Rollback and Gates

- 先完成技能源审计，再运行物化。不要在路径表达仍混杂时覆盖宿主技能产物。
- 技能源、spec 文件名和三个宿主技能产物作为一个结果回滚。只回滚其中一层会留下漂移。
- 本 ticket 不改数据库、外部服务或 issue tracker 状态。回滚不需要数据迁移或外部清理。
