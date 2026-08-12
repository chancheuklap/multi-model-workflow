---
ticket: 41
artifact_refs: []
---

# Plan: 元数据块与 `mmw artifact index`

**Goal:** 三类长期文档使用固定元数据块。`mmw artifact index adr|spec` 每次读取都计算并输出清单，同时维护可浏览的索引副本。
**Source spec:** `docs/specs/mmw-artifact-wiring/spec.md`
**Source ticket:** GitHub issue `#41`

## Constraints

- 03 依赖 01 提供产物落点数据、`mmw artifact` 动作分发和产物测试入口。03 不改 `mmw/cli/mmw` 或 `mmw/test.sh`。（spec:845；ticket `#41` 的 `Blocked by`）
- 03 独占现有 14 份 ADR 和两个索引副本。14 份 ADR 都迁移元数据块；`0014` 还补一条 Consequence，记录本 spec 对并发判据的修正。03 只改 `AGENTS.md` 的 ADR 读取句。（spec:557-583,833-857）
- 共享技能源只改元数据或只读合同分区。06 的派发块、07 的落点写法、08 的接线分区保持不动。（spec:836-837）
- `mmw artifact index` 只接受 `adr` 和 `spec`。plan、research 和 prototype 不建总索引。（spec:473-500）
- 命令输出是权威。两个 `README.md` 只是同次运行写下的副本。（spec:479-491；ADR `0010`）
- 副本内容按完整字节比较。内容相同时不得写文件。（spec:483-491）
- 修改技能源前，完整读取该技能和链接的 reference。写作遵守 `writing-for-agents`。（`AGENTS.md:64-71`）
- `ADR-FORMAT.md` 有上游对应项。先按 `upstream-skill-fidelity` 把新增 `date` 与 `amends` 元数据块归类为已批准的 MMW 接线。保留上游 `Status` frontmatter 选项、简短 ADR、可选章节和编号方法。（spec:434-443；`vendor/mattpocock-skills/skills/engineering/domain-modeling/ADR-FORMAT.md:18-24`）
- 技能源是流程判据。修改后必须物化三个宿主产物。（`AGENTS.md:46`；`mmw/cli/lib/materialize_skills.py:20-25,323-337`）
- 本 ticket 没有 prototype 资产，也没有 research。（ticket `#41`）

## Current State

- 当前 spec 已有六字段元数据块，可作为有效输入样本。（`docs/specs/mmw-artifact-wiring/mmw-artifact-wiring.md:1-20`）
- spec 模板和 plan 模板都从一级标题开始，没有文档元数据块。（`mmw/skills-src/mmw-to-spec/spec-template.md:7-10`；`mmw/skills-src/mmw-planner/references/plan-body.md:7-14`）
- ADR 模板从一级标题开始。它仍把 `Status` 当成可选 frontmatter。（`mmw/skills-src/mmw-domain-modeling/ADR-FORMAT.md:7-23`）
- 现有 14 份 ADR 都从一级标题开始。它们的 Git 首次登记日期都是 `2026-08-11`。
- 审查者目前禁止任何工作区改动。审查 task 的约束栏也只写“只读”。（`mmw/skills-src/mmw-reviewer/SKILL.md:30-36`；`mmw/skills-src/mmw-review/SKILL.md:79-86`）
- ADR 读取句同时存在于受管种子和根 `AGENTS.md`。（`mmw/cli/seeds/AGENTS-domain-context.md:1-18`；`AGENTS.md:98-116`）
- `mmw/test.sh` 逐项调用 Bash 行为测试。01 负责加入 `test_artifact.sh` 的入口。（`mmw/test.sh:15-45`；spec:833-834）
- Graphify 的两次查询都被工具取消。Serena 也无法从当前 Bash 语言配置提取符号。上面的结构关系改用当前源码逐行验证。

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `mmw/cli/lib/artifact.sh` | Modify，文件由 01 建立 | 只增加 `index` 动作分区。不得改 01 的 `path` 行为或 CLI 主入口。 |
| `mmw/cli/lib/artifact_index.py` | Create | 读取元数据块，计算 ADR 或 spec 清单，输出并维护副本。 |
| `mmw/cli/tests/test_artifact.sh` | Test，文件由 01 建立 | 增加 `index` 的命令行行为用例。不得改 01 的 `path` 用例。 |
| `mmw/skills-src/mmw-to-spec/SKILL.md` | Modify | 规定六字段取值，并在发布后回填 `spec_issue`。 |
| `mmw/skills-src/mmw-to-spec/spec-template.md` | Modify | 在模板文件头增加六字段 YAML 元数据块。 |
| `mmw/skills-src/mmw-to-plan/SKILL.md` | Modify | 验证每份 plan 带正确 `ticket` 和 `artifact_refs` 字段。 |
| `mmw/skills-src/mmw-planner/references/plan-body.md` | Modify | 在 plan 模板文件头增加两字段 YAML 元数据块。 |
| `mmw/skills-src/mmw-planner/references/self-check.md` | Modify | 把两字段元数据块加入 plan 就绪门。 |
| `mmw/skills-src/mmw-domain-modeling/ADR-FORMAT.md` | Modify | 在 ADR 模板文件头增加 `date` 与 `amends`，并保留上游 `Status` frontmatter 选项。 |
| `mmw/skills-src/mmw-reviewer/SKILL.md` | Modify | 在只读纪律中加入索引命令的唯一允许写副作用。 |
| `mmw/skills-src/mmw-review/SKILL.md` | Modify | 在只读审查 task 的约束栏传递同一例外。 |
| `mmw/skills-pi/` 中上述八个对应文件 | 生成产物 | 由 `mmw skills materialize --host all` 同步改动。 |
| `mmw/skills-claude-code/` 中上述八个对应文件 | 生成产物 | 由 `mmw skills materialize --host all` 同步改动。 |
| `mmw/skills-codex/` 中上述八个对应文件 | 生成产物 | 由 `mmw skills materialize --host all` 同步改动。 |
| `docs/adr/0001-*.md` 至 `docs/adr/0014-*.md` | Docs·迁移·修正 | 为现有 14 份 ADR 补两字段元数据块；另给 `0014` 补一条 Consequence，记录并发判据修正。 |
| `docs/adr/README.md` | Create·生成 | 保存 `mmw artifact index adr` 同次运行的副本。 |
| `docs/specs/README.md` | Create·生成 | 保存 `mmw artifact index spec` 同次运行的副本。 |
| `mmw/cli/seeds/AGENTS-domain-context.md` | Modify | 把受管 ADR 读取句改成先运行索引命令。 |
| `AGENTS.md` | Modify·物化 | 只同步 `MMW-DOMAIN-CONTEXT` 中的 ADR 读取句。 |

## Contracts and Seams

- **Test seam:** 使用 spec 已确认的 `mmw` CLI 命令行接口。测试在一次性仓库中运行真命令。它验证当场计算、标准输出、字节比较、条件写入和不可写降级。（spec:762-780）
- **Consumes from 01:** 01 提供 `mmw/cli/artifacts.json`。03 读取 `adr` 与 `spec` 记录的 `root`、`root_kind` 和 `status`。两项必须是 `root_kind=fixed`、`status=active`。01 还提供 `mmw artifact` 动作分发和 `test_artifact.sh`。（spec:813,845）
- **Produces for 04:** 字段名固定为 `artifact_refs`。它始终存在，值是 YAML 映射列表；明确没有产物引用时写 `artifact_refs: []`。
- **Produces for 04:** 生产方按 `category`、`name`、`issue`、`sub` 的顺序书写。04 按键解析，不得依赖键顺序。`category` 和 `name` 必填。`issue` 与 `sub` 只在类别需要时出现。`name` 在持久化声明中不得缺省。`issue` 是整数，其余值是字符串。（spec:379-397,426-441）
- **Produces for 04:** `category` 对应类别参数，`name` 对应 `--name`，`issue` 对应 `--issue`，`sub` 对应 `--sub`。04 按此形状实现 `mmw artifact check`，不得改字段名或改成路径字符串。

```yaml
artifact_refs:
  - category: research
    name: mmw-artifact-wiring
    issue: 20
    sub: aidlc-v2-artifact-wiring
```

没有产物引用时，完整形状是：

```yaml
artifact_refs: []
```

- **Metadata:** spec 固定六个字段：`slug`、`summary`、`date`、`branch`、`spec_issue`、`artifact_refs`。plan 固定两个字段：`ticket`、`artifact_refs`。ADR 索引固定读取 `date` 与 `amends`；模板继续提供上游 `Status` frontmatter 选项。（spec:411-445；`mmw/skills-src/mmw-domain-modeling/ADR-FORMAT.md:18-23`）
- **ADR migration:** 14 份 ADR 的 `date` 都写 `2026-08-11`。`0007` 的 `amends` 是 `[1]`；`0008` 是 `[3]`；`0010` 是 `[1, 7]`；其余是 `[]`。（spec:731-739）
- **ADR correction:** `0014` 的 Consequences 增加一条修正记录。成功判据必须同时检查 V1 的全部行和本次新增行都存在于 V3；任一检查失败都重做。（spec:563-583）
- **Registry:** ADR 行从文件名取编号，从一级标题取标题，从元数据块取日期与 `amends`。`被哪几份改写` 由全部 `amends` 反向计算。它不写回 ADR。（spec:428-437,483-490）
- **Registry:** spec 行取 `slug`、`summary`、`date`、`branch` 和 `spec_issue`。扫描类别根下全部 spec 文档，排除索引副本。（spec:483-490）

## Implementation

1. **01 的扩展接缝可用**
   - Change: 等 01 落地后，确认 `artifact` 动作分发、产物落点数据和统一测试文件存在。03 只登记 `index` 动作。
   - Files: `mmw/cli/lib/artifact.sh`、`mmw/cli/artifacts.json`、`mmw/cli/tests/test_artifact.sh`。
   - Verify: `mmw/cli/mmw artifact path spec --name probe` → 只输出 `docs/specs/probe/spec.md`。

2. **三类生产方写出固定元数据块**
   - Change: 更新 spec、plan 和 ADR 模板。生产方必须写完整字段。没有产物引用时仍写空列表。
   - Change: 在 `ADR-FORMAT.md` 的模板文件头增加 spec 已批准的 `date` 与 `amends`。保留上游 `Status` frontmatter 选项和其余正文方法。
   - Change: `/mmw-to-spec` 保留人工审批与发布顺序。issue 建立后回填 `spec_issue`，并在移交前提交这次回填。最终文件不得保留占位编号。
   - Change: `/mmw-to-plan` 验证 `ticket` 等于当前 issue 编号，并验证 `artifact_refs` 键存在。引用内容的解析归 04。
   - Files: `mmw/skills-src/mmw-to-spec/`、`mmw/skills-src/mmw-to-plan/SKILL.md`、`mmw/skills-src/mmw-planner/references/`、`mmw/skills-src/mmw-domain-modeling/ADR-FORMAT.md`。
   - Verify: `rg -n "^(slug|summary|date|branch|spec_issue|ticket|artifact_refs|amends):" mmw/skills-src/mmw-to-spec mmw/skills-src/mmw-to-plan mmw/skills-src/mmw-planner mmw/skills-src/mmw-domain-modeling/ADR-FORMAT.md` → 三类模板显示各自的完整字段。
   - Verify: `rg -n "\*\*Status\*\* frontmatter" mmw/skills-src/mmw-domain-modeling/ADR-FORMAT.md` → 上游 `Status` frontmatter 选项仍存在。

3. **现有 ADR 完成元数据迁移与 `0014` 判据修正**
   - Change: 在 14 份 ADR 的一级标题前增加元数据块。编号与标题继续只存在于文件名和一级标题。
   - Change: 给 `docs/adr/0014-map-append-command.md` 的 Consequences 补一条修正记录。原来的二选一描述改为两个同时成立的判据：V1 的全部行都在 V3，并且本次新增行也在 V3；任一项不成立都重做。
   - Files: `docs/adr/0001-*.md` 至 `docs/adr/0014-*.md`。
   - Verify: `mmw/cli/mmw artifact index adr` → 输出 14 行 ADR，并显示 `0001` 被 `0007`、`0010` 改写，`0003` 被 `0008` 改写，`0007` 被 `0010` 改写。
   - Verify: `rg -n "V1|V3|新增行|两项" docs/adr/0014-map-append-command.md` → 一条 Consequence 明确记录两项判据和本 spec 的修正。

4. **索引命令从元数据当场计算清单**
   - Change: 先在 01 的 `test_artifact.sh` 增加失败用例，再实现 `index adr` 与 `index spec`。
   - Change: 输出与副本使用同一份完整 Markdown 字节串。ADR 按编号排序。spec 按工作名排序。
   - Change: 副本缺失或内容不同才原子写入。内容相同时不打开文件写入。
   - Change: 副本不可写时保留旧文件。命令仍输出完整清单，并向标准错误写一行说明，退出码为 0。
   - Change: 元数据块缺失、格式错误或必填字段缺失时，列出文件和字段并非零退出。不要静默漏掉清单行。
   - Files: `mmw/cli/lib/artifact.sh` 的 `index` 分区、`mmw/cli/lib/artifact_index.py`、`mmw/cli/tests/test_artifact.sh` 的 `index` 分区。
   - Verify: `bash mmw/cli/tests/test_artifact.sh` → 01 的 `path` 用例和 03 的 `index` 用例全部通过。

5. **写出两个索引副本**
   - Change: 分别运行 ADR 与 spec 索引命令。不要手写副本。
   - Files: `docs/adr/README.md`、`docs/specs/README.md`。
   - Verify: `cmp <(mmw/cli/mmw artifact index adr) docs/adr/README.md && cmp <(mmw/cli/mmw artifact index spec) docs/specs/README.md` → 两份副本逐字节等于命令输出。

6. **只读合同与 ADR 读取入口一致**
   - Change: 更新受管种子，再运行 `mmw domain sync`。根 `AGENTS.md` 只改变 ADR 读取句。
   - Change: 审查者和审查 task 都说明：运行 `mmw artifact index` 是允许动作。它可能更新索引副本，但不算修改被审产物。
   - Files: `mmw/cli/seeds/AGENTS-domain-context.md`、`AGENTS.md`、`mmw/skills-src/mmw-reviewer/SKILL.md`、`mmw/skills-src/mmw-review/SKILL.md`。
   - Verify: `mmw/cli/mmw domain check` → 受管领域上下文有效。

7. **物化并完成全仓库验证**
   - Change: 物化 Pi、Claude Code 和 Codex 三套技能产物。只保留由本次技能源差异产生的文件变更。
   - Files: `mmw/skills-pi/`、`mmw/skills-claude-code/`、`mmw/skills-codex/` 中对应技能。
   - Verify: `mmw/cli/mmw skills materialize --host all --check` → 三个宿主产物与技能源一致。
   - Verify: `bash mmw/test.sh` → 全部测试通过，退出码为 0。
   - Verify: `git diff --check` → 没有空白错误。

## Acceptance

| Ticket 验收 | 证明方式 | 命令或人工结果 |
| --- | --- | --- |
| 三类元数据块格式落地 | 检查三份生产模板、生产流程和物化产物 | `rg -n "^(slug|summary|date|branch|spec_issue|ticket|artifact_refs|amends):" mmw/skills-src mmw/skills-pi mmw/skills-claude-code mmw/skills-codex` → spec 六字段、plan 两字段、ADR 两字段均存在 |
| ADR 模板保留上游 `Status` 选项 | 同时核对 MMW 模板和上游模板的可选章节 | `rg -n "\*\*Status\*\* frontmatter" mmw/skills-src/mmw-domain-modeling/ADR-FORMAT.md vendor/mattpocock-skills/skills/engineering/domain-modeling/ADR-FORMAT.md` → 两份模板都保留 `Status` 选项 |
| ADR 与 spec 都能当场输出清单 | 在一次性仓库用真实 CLI 建两类样本 | `bash mmw/cli/tests/test_artifact.sh` → 两类输出用例通过 |
| 副本一致时不写 | 测试记录纳秒修改时间和 inode，再重复运行 | `bash mmw/cli/tests/test_artifact.sh` → 一致副本的修改时间和 inode 不变 |
| 副本不同时写入 | 先写入过期正文，再运行命令 | `bash mmw/cli/tests/test_artifact.sh` → 副本逐字节等于新输出 |
| 副本不可写时降级 | 在一次性仓库让副本目录不可写 | `bash mmw/cli/tests/test_artifact.sh` → stdout 完整，stderr 一行说明，退出码 0，旧副本不变 |
| 反向改写关系由命令计算 | fixture 只写 `amends`，不写反向字段 | `bash mmw/cli/tests/test_artifact.sh` → 被改写列按反向关系生成 |
| 14 份 ADR 都有正确元数据 | 运行真实 ADR 索引并核对行数和三组关系 | `mmw/cli/mmw artifact index adr` → 14 行，日期全为 `2026-08-11`，改写关系与 spec 第 20 节一致 |
| ADR `0014` 记录并发判据修正 | 检查 Consequences 中新增的修正记录 | `rg -n "V1|V3|新增行|两项" docs/adr/0014-map-append-command.md` → 同时检查 V1 全部行与本次新增行；任一项不成立都重做 |
| `AGENTS.md` 先取索引再读 ADR | 同步受管种子并检查受管合同 | `mmw/cli/mmw domain check` → 有效；根文件只改指定句 |
| 只读审查允许索引命令 | 检查审查者纪律、task 约束和三个宿主产物 | `mmw/cli/mmw skills materialize --host all --check` → 对应文本全部一致 |
| 新测试进入完整测试入口并全部通过 | 01 已登记统一产物测试；03 扩展同一文件 | `bash mmw/test.sh` → 退出码为 0 |

## Browser Acceptance

不适用。
