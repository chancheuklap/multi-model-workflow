# Plan: 恢复 Pi 与 Claude Code 技能物化基线

**Goal:** 让当前技能源对应的 Pi、Claude Code 与 Codex 三宿主物化检查全部通过，为后续领域上下文技能改动建立零漂移基线。
**Source spec:** `docs/specs/feat-context-doc-contracts/feat-context-doc-contracts.md`
**Source ticket:** GitHub issue `#15`
**Blocked by:** 无
**Architecture:** 继续以 `mmw/skills/` 为技能源唯一事实来源，使用现有物化器整目录生成宿主产物；本 plan 只恢复当前已漂移的 Pi 与 Claude Code 产物，Codex 产物保持不变，领域上下文新行为留给 Plan 03。
**Tech stack:** Python 3 技能物化器、Shell 命令行接口、Markdown 技能发布产物、Git 静态检查。

## Global Constraints

- `mmw/skills/` 保存流程判据，`mmw/skills-pi/`、`mmw/skills-claude-code/` 与 `mmw/skills-codex/` 保存宿主物化产物。
- 本 plan 不得修改 `mmw/skills/` 下的技能源，也不得加入领域上下文新行为。
- 本 plan 只拥有当前已漂移的 Pi 与 Claude Code 物化文件。Plan 03 在本 plan 集成后才拥有三宿主领域技能的最终物化产物。
- Pi 发布产物可写前必须确认任务 worktree 干净。
- 宿主动作块必须由物化器整块替换。不得手工改写宿主差异，也不得在技能源或产物正文加入宿主二选一逻辑。
- `archive/` 与 `vendor/` 是冻结内容，不参与本次物化或检查。
- 本仓库不新增自动化测试、测试夹具或测试套件。本 ticket 使用 spec 已确定的“技能与 Codex 物化检查” seam。
- 本 plan 不执行 `git push`、部署或正式发布。任何对外发布仍由用户单独批准。

## File / Responsibility Map

下表中的每一行包含两个 `Modify` 文件。物化器从同一个相对路径的 `mmw/skills/` 源文件生成这两个宿主产物。

| Pi 产物 | Claude Code 产物 | 责任 |
| --- | --- | --- |
| `mmw/skills-pi/mmw-codebase-design/DESIGN-IT-TWICE.md` | `mmw/skills-claude-code/mmw-codebase-design/DESIGN-IT-TWICE.md` | 同步两版设计方法中的 subagent 报告术语。 |
| `mmw/skills-pi/mmw-diagnosing-bugs/narrowing.md` | `mmw/skills-claude-code/mmw-diagnosing-bugs/narrowing.md` | 同步最小复现、竞争假设和验证方法。 |
| `mmw/skills-pi/mmw-implement/worker-brief.md` | `mmw/skills-claude-code/mmw-implement/worker-brief.md` | 同步 `worker` 的材料优先级与四档完成报告合同。 |
| `mmw/skills-pi/mmw-prototype/SKILL.md` | `mmw/skills-claude-code/mmw-prototype/SKILL.md` | 同步设计原型与证据原型的文件和走查边界。 |
| `mmw/skills-pi/mmw-release/SKILL.md` | `mmw/skills-claude-code/mmw-release/SKILL.md` | 同步有无 spec 时的出包后移交规则。 |
| `mmw/skills-pi/mmw-retrieval/SKILL.md` | `mmw/skills-claude-code/mmw-retrieval/SKILL.md` | 同步检索服务器说明的唯一事实来源表述。 |
| `mmw/skills-pi/mmw-reviewer/SKILL.md` | `mmw/skills-claude-code/mmw-reviewer/SKILL.md` | 同步审查方法论与被审材料的边界。 |
| `mmw/skills-pi/mmw-reviewer/references/final-fresh.md` | `mmw/skills-claude-code/mmw-reviewer/references/final-fresh.md` | 同步测试值唯一事实来源的审查要求。 |
| `mmw/skills-pi/mmw-reviewer/references/final-trace.md` | `mmw/skills-claude-code/mmw-reviewer/references/final-trace.md` | 同步原型作为视觉合同唯一事实来源的要求。 |
| `mmw/skills-pi/mmw-reviewer/references/plan-compliance.md` | `mmw/skills-claude-code/mmw-reviewer/references/plan-compliance.md` | 同步数据唯一事实来源的 plan 合规检查。 |
| `mmw/skills-pi/mmw-reviewer/references/spec-alignment.md` | `mmw/skills-claude-code/mmw-reviewer/references/spec-alignment.md` | 同步术语、数据与不变量的唯一事实来源表述。 |
| `mmw/skills-pi/mmw-start/SKILL.md` | `mmw/skills-claude-code/mmw-start/SKILL.md` | 同步 issue、agent brief、单 seam 与 spec 的路由判据。 |
| `mmw/skills-pi/mmw-tdd/SKILL.md` | `mmw/skills-claude-code/mmw-tdd/SKILL.md` | 同步测试值唯一事实来源与竖切原因。 |
| `mmw/skills-pi/mmw-tdd/quality-bar.md` | `mmw/skills-claude-code/mmw-tdd/quality-bar.md` | 同步测试准入中的唯一事实来源措辞。 |
| `mmw/skills-pi/mmw-to-tickets/SKILL.md` | `mmw/skills-claude-code/mmw-to-tickets/SKILL.md` | 同步 ticket 分层表的唯一事实来源术语。 |
| `mmw/skills-pi/mmw-triage/AGENT-BRIEF.md` | `mmw/skills-claude-code/mmw-triage/AGENT-BRIEF.md` | 同步 agent brief 的行为合同、范围和测试 seam 职责。 |
| `mmw/skills-pi/mmw-triage/OUT-OF-SCOPE.md` | `mmw/skills-claude-code/mmw-triage/OUT-OF-SCOPE.md` | 同步被否需求的组织记忆与去重职责。 |
| `mmw/skills-pi/mmw-triage/SKILL.md` | `mmw/skills-claude-code/mmw-triage/SKILL.md` | 同步分诊状态、agent brief 和出口判据。 |
| `mmw/skills-pi/mmw-triage/examples.md` | `mmw/skills-claude-code/mmw-triage/examples.md` | 同步 PR 分诊示例中的 agent brief 术语。 |
| `mmw/skills-pi/mmw-verifying-agent-output/SKILL.md` | `mmw/skills-claude-code/mmw-verifying-agent-output/SKILL.md` | 同步 subagent 报告验证与 `worker` 四档处理规则。 |
| `mmw/skills-pi/mmw-wayfinder/map-anatomy.md` | `mmw/skills-claude-code/mmw-wayfinder/map-anatomy.md` | 同步 map 作为 effort 唯一索引的定义。 |

**Test:** 不创建测试文件。公开物化检查命令直接验证这些发布产物的完整文件集合和字节内容。

## 小块清单

### 01.1 恢复三宿主零漂移基线

- **要做什么：** 用现有物化器重新生成 Pi 与 Claude Code 发布目录，保留 Codex 当前成功状态。
- **验收：** 全宿主技能物化检查和 Codex 运行时物化检查均返回成功；实现 diff 只含下方任务包拥有的四十二个发布产物；技能源没有变化。
- **被谁阻塞：** 无。Plan 03 必须等待本 plan 集成后再修改技能源和重新物化。
- **执行方式：** AFK。

## Dependency Graph

本 plan 只有任务包 01.1，没有包内依赖。任务包把 red 检查、两宿主恢复和全宿主 green 检查放在同一个可独立审查的交付物中。

## 发布风险与人工审批关卡

| 风险面 | 任务包 | Risk flag | 要不要提前发起审查 | 人工审批关卡由谁批准 |
| --- | --- | --- | --- | --- |
| 已跟踪的两套技能发布产物被整目录重新生成 | 01.1 | `generated-release-artifacts`、`cross-host` | 要。本 plan 必须先审查并集成，Plan 03 才能开始最终物化。 | 无。本 plan 不对外发布；后续正式发布由用户批准。 |
| 误把领域上下文新行为或技能源改动带入基线 | 01.1 | `cross-plan-scope` | 要。审查时验证技能源和 Codex 产物无 diff。 | 主 agent 依据 spec 合同边界验证，不需要用户作实现选择。 |

### Task Pack 01.1: 恢复三宿主零漂移基线

**Ticket:** GitHub issue `#15`
**Goal behavior:** 从当前 `mmw/skills/` 生成 Pi 与 Claude Code 发布产物后，三宿主物化检查返回成功，Codex 运行时物化检查继续返回成功。
**Why this matters:** Plan 03 需要从可验证的零漂移发布状态增加领域上下文消费入口。先恢复基线可以把既有漂移与新功能 diff 分开审查。
**Owned files:** `Modify` 下表四十二个文件。行号指向 2026-08-05 验证到的第一个现有漂移位置；物化器拥有每个文件的完整字节内容，禁止按行手改。

| Pi 产物 | Claude Code 产物 |
| --- | --- |
| `mmw/skills-pi/mmw-codebase-design/DESIGN-IT-TWICE.md:45` | `mmw/skills-claude-code/mmw-codebase-design/DESIGN-IT-TWICE.md:45` |
| `mmw/skills-pi/mmw-diagnosing-bugs/narrowing.md:18` | `mmw/skills-claude-code/mmw-diagnosing-bugs/narrowing.md:18` |
| `mmw/skills-pi/mmw-implement/worker-brief.md:5` | `mmw/skills-claude-code/mmw-implement/worker-brief.md:5` |
| `mmw/skills-pi/mmw-prototype/SKILL.md:41` | `mmw/skills-claude-code/mmw-prototype/SKILL.md:41` |
| `mmw/skills-pi/mmw-release/SKILL.md:21` | `mmw/skills-claude-code/mmw-release/SKILL.md:21` |
| `mmw/skills-pi/mmw-retrieval/SKILL.md:6` | `mmw/skills-claude-code/mmw-retrieval/SKILL.md:6` |
| `mmw/skills-pi/mmw-reviewer/SKILL.md:9` | `mmw/skills-claude-code/mmw-reviewer/SKILL.md:9` |
| `mmw/skills-pi/mmw-reviewer/references/final-fresh.md:14` | `mmw/skills-claude-code/mmw-reviewer/references/final-fresh.md:14` |
| `mmw/skills-pi/mmw-reviewer/references/final-trace.md:11` | `mmw/skills-claude-code/mmw-reviewer/references/final-trace.md:11` |
| `mmw/skills-pi/mmw-reviewer/references/plan-compliance.md:10` | `mmw/skills-claude-code/mmw-reviewer/references/plan-compliance.md:10` |
| `mmw/skills-pi/mmw-reviewer/references/spec-alignment.md:9` | `mmw/skills-claude-code/mmw-reviewer/references/spec-alignment.md:9` |
| `mmw/skills-pi/mmw-start/SKILL.md:25` | `mmw/skills-claude-code/mmw-start/SKILL.md:25` |
| `mmw/skills-pi/mmw-tdd/SKILL.md:18` | `mmw/skills-claude-code/mmw-tdd/SKILL.md:18` |
| `mmw/skills-pi/mmw-tdd/quality-bar.md:13` | `mmw/skills-claude-code/mmw-tdd/quality-bar.md:13` |
| `mmw/skills-pi/mmw-to-tickets/SKILL.md:12` | `mmw/skills-claude-code/mmw-to-tickets/SKILL.md:12` |
| `mmw/skills-pi/mmw-triage/AGENT-BRIEF.md:3` | `mmw/skills-claude-code/mmw-triage/AGENT-BRIEF.md:3` |
| `mmw/skills-pi/mmw-triage/OUT-OF-SCOPE.md:3` | `mmw/skills-claude-code/mmw-triage/OUT-OF-SCOPE.md:3` |
| `mmw/skills-pi/mmw-triage/SKILL.md:27` | `mmw/skills-claude-code/mmw-triage/SKILL.md:27` |
| `mmw/skills-pi/mmw-triage/examples.md:85` | `mmw/skills-claude-code/mmw-triage/examples.md:85` |
| `mmw/skills-pi/mmw-verifying-agent-output/SKILL.md:6` | `mmw/skills-claude-code/mmw-verifying-agent-output/SKILL.md:6` |
| `mmw/skills-pi/mmw-wayfinder/map-anatomy.md:9` | `mmw/skills-claude-code/mmw-wayfinder/map-anatomy.md:9` |

**Verified current state:** 2026-08-05 在当前任务 worktree 验证到以下结果。公开命令由 `mmw/cli/mmw:388` 定义。物化器把源目录映射到三个宿主目录（`mmw/cli/lib/materialize_skills.py:20`、`mmw/cli/lib/materialize_skills.py:22`），逐文件生成并按字节检查差异（`mmw/cli/lib/materialize_skills.py:344`）。Codex 运行时单独调用同一物化器检查 Codex 产物（`mmw/codex/runtime.py:139`）。

| 宿主 | 公开检查结果 | 漂移文件数 | 缺口 |
| --- | --- | ---: | --- |
| Pi | `mmw/cli/mmw skills materialize --host pi --check` 返回 `1` | 21 | 上表 Pi 产物没有跟上当前技能源。 |
| Claude Code | `mmw/cli/mmw skills materialize --host claude-code --check` 返回 `1` | 21 | 上表 Claude Code 产物没有跟上当前技能源。 |
| Codex | `mmw/cli/mmw skills materialize --host codex --check` 返回 `0` | 0 | 无缺口，必须保持无 diff。 |

`mmw/cli/mmw skills materialize --host all --check` 当前返回 `1`，合计报告四十二个 `异`。`python3 mmw/codex/runtime.py materialize --check` 当前返回 `0`。

**先读：**

- `docs/specs/feat-context-doc-contracts/feat-context-doc-contracts.md` 的 `Implementation Decisions`、`Testing Decisions`、`Contract Boundaries`、`Cross-Plan Contract Anchors` 与 `Release Risk`。
- GitHub issue `#15` 的三条验收标准。
- `AGENTS.md:30` 的发布目录职责、`AGENTS.md:38` 的技能源规则、`AGENTS.md:46` 的宿主边界、`AGENTS.md:105` 的提交检查。
- `TESTING.md:3` 的无测试套件约束、`TESTING.md:5` 的静态检查与 `TESTING.md:22` 的真实宿主验证边界。
- `mmw/cli/lib/materialize_skills.py:333` 的源文件枚举与 `mmw/cli/lib/materialize_skills.py:344` 的生成、检查和整目录替换行为。
- 开工时运行 `mmw domain path`，按当前任务 worktree 返回的领域文档形态读取本次范围。

**Interfaces:**

- **Consumes:** `mmw skills materialize --host <pi|claude-code|codex|all> [--check] [--out <目录>]`；`iter_skill_files() -> list[Path]` 提供当前 `mmw/skills/` 文件集合；`materialize_host(host: str, out_root: Path, role_agents: dict[str, str], codex_profiles: dict, *, check: bool) -> int` 生成或检查一个宿主目录。
- **Produces:** Pi 与 Claude Code 各二十一个当前源对应的 Markdown 发布产物；`mmw skills materialize --host all --check` 返回 `0` 的三宿主零漂移基线。没有新增函数、参数、字段或命令。

**Contract anchors:**

- **归属方：** Plan 01 只拥有上表四十二个 Pi 与 Claude Code 发布产物。
- **提供方：** `mmw/skills/` 和 `mmw/cli/lib/materialize_skills.py` 提供当前源及宿主展开规则；本任务只消费，不修改。
- **消费方：** Plan 03 在 Plan 01 集成后修改领域技能源，并基于这份零漂移基线重新物化三宿主最终产物。
- **数据结构：** 每个源文件的相对路径原样映射到宿主目录。Markdown 只经过 `expand_text(...)` 的宿主块展开；物化检查比较完整文件集合和字节内容。
- **登记与迁移：** 不新增登记。迁移动作只运行 Pi 与 Claude Code 的现有物化命令。
- **验证：** 全宿主物化检查返回 `0`；Codex 运行时物化检查返回 `0`；技能源和 Codex 产物没有 diff。

**Schema / API shapes:** 不适用。本任务不新增数据结构或公开接口。

**Mockup specs:** 不适用。本需求没有界面或原型。

**Do Not Touch:**

- 不修改 `mmw/skills/` 下的任何技能源。
- 不修改 `mmw/skills-codex/` 下的 Codex 产物。
- 不修改 `mmw/cli/lib/materialize_skills.py`、`mmw/cli/mmw` 或 `mmw/codex/runtime.py`。
- 不认领 Plan 02 的领域规则种子、同步与检查模块、init、domain 或 doctor 接入。
- 不认领 Plan 03 的领域技能源、三宿主最终领域物化产物、`mmw-skill-map.html` 或发布版本字段。
- 不修改 `archive/`、`vendor/` 或 AgentFlow 仓库。

**Root cause:** 当前两个宿主目录的已跟踪字节不等于物化器从现行技能源生成的字节。检查结果只能证明产物未同步，不能证明是哪一次历史操作遗漏了重新物化。因此修复动作只运行现有生成器，不改技能源或物化器。

**Acceptance criteria:**

1. [ ] `mmw/cli/mmw skills materialize --host all --check` 返回 `0`，不报告 `缺`、`多` 或 `异`。
2. [ ] `python3 mmw/codex/runtime.py materialize --check` 返回 `0`，Codex 当前成功状态没有回退。
3. [ ] 实现 diff 在 `mmw/` 下只包含上表四十二个文件：Pi 二十一个，Claude Code 二十一个；`mmw/skills/`、`mmw/skills-codex/`、`mmw/cli/` 与 `mmw/codex/` 没有 diff。
4. [ ] 四十二个产物均由现有物化器生成，并与当前技能源逐字节一致；没有手工编辑，也没有加入领域上下文新行为。
5. [ ] `git diff --check` 返回 `0`。

**Verification commands:**

- `mmw/cli/mmw skills materialize --host all --check` → Expected: 退出码 `0`，无漂移输出。
- `python3 mmw/codex/runtime.py materialize --check` → Expected: 退出码 `0`，无差异输出。
- `git diff --name-only -- mmw/skills-pi mmw/skills-claude-code` → Expected: 只列出 Owned files 表中的四十二个路径。
- `git diff --name-only -- mmw/skills-pi | wc -l` → Expected: `21`。
- `git diff --name-only -- mmw/skills-claude-code | wc -l` → Expected: `21`。
- `git diff --exit-code -- mmw/skills mmw/skills-codex mmw/cli mmw/codex` → Expected: 退出码 `0`，无 diff。
- `git diff --check` → Expected: 退出码 `0`，无输出。

**Browser acceptance:** 不适用。本任务没有界面行为。

**Testing pyramid:**

| 层 | 测什么 | 数量 |
| --- | --- | ---: |
| 提交前静态检查 | 全宿主技能产物与当前技能源逐字节一致；Codex agent、plugin 与技能物化输入保持一致；diff 没有空白错误。 | 3 条命令 |
| 真实宿主验证 | 本任务不改变宿主行为，不声明 Pi、Claude Code 或 Codex App 的真实运行路径已经通过。 | 0 |

**Rollback:** 集成后如需撤回，回滚本任务的单一实现提交。该动作恢复 ticket 前的发布产物字节，也会重新引入已知漂移；不得用修改技能源的方式掩盖漂移。

**Complexity:** standard。改动跨两套宿主发布目录和四十二个文件，但生成、检查与回滚均由现有确定性命令完成。

**Commit boundary:** 全部 green 检查通过后，把四十二个生成产物放进一个提交。建议提交信息：`chore: restore skill materialization baseline (#15)`。

**Risk flags:** `generated-release-artifacts`、`cross-host`、`cross-plan-ordering`。

**发布风险:** 本任务只恢复 Markdown 发布产物，不迁移数据，不改命令合同，也不执行正式发布。主要风险是生成时夹带源改动或越过 Plan 03 边界；文件范围和物化检查共同拦截该风险。

**HITL 还是 AFK:** AFK。所有结果都有确定性命令和文件范围判据，不需要用户作产品或架构决定。

**Dependencies:** 包内无依赖。Plan 03 依赖本任务包完成、审查并集成。

**Out of scope:** 领域规则同步器、doctor 检查、领域技能提醒、架构可视化、版本发布、AgentFlow 迁移、真实宿主运行验证。

#### Implementation tasks

- [ ] Step 1: 确认开工条件。运行 `git status --short`，预期没有输出；运行 `mmw domain path`，按返回形态读取本次范围。任务 worktree 不干净时停止，不要运行写入模式的 Pi 物化。
- [ ] Step 2: 在公开物化 seam 建立 red 证据。运行 `mmw/cli/mmw skills materialize --host all --check`，预期退出码为 `1`，只报告 Pi 二十一个和 Claude Code 二十一个 `异`，不报告 Codex 漂移。
- [ ] Step 3: 生成 Pi 的最小修复。运行 `mmw/cli/mmw skills materialize --host pi`，让物化器从当前 `mmw/skills/` 整目录重建 `mmw/skills-pi/`；不要手工编辑任何生成文件。
- [ ] Step 4: 确认 Pi 这一片变绿。运行 `mmw/cli/mmw skills materialize --host pi --check`，预期退出码为 `0` 且没有漂移输出。
- [ ] Step 5: 生成 Claude Code 的最小修复。运行 `mmw/cli/mmw skills materialize --host claude-code`，让物化器从当前 `mmw/skills/` 整目录重建 `mmw/skills-claude-code/`；不要手工编辑任何生成文件。
- [ ] Step 6: 确认完整公开 seam 变绿。运行 `mmw/cli/mmw skills materialize --host all --check`，预期退出码为 `0` 且没有 `缺`、`多` 或 `异`。
- [ ] Step 7: 保持 Codex 运行时 green。运行 `python3 mmw/codex/runtime.py materialize --check`，预期退出码为 `0` 且没有差异输出。
- [ ] Step 8: 验证提交范围。Pi 与 Claude Code 的 `git diff --name-only` 数量分别为二十一个；`git diff --exit-code -- mmw/skills mmw/skills-codex mmw/cli mmw/codex` 返回 `0`；`git diff --check` 返回 `0`。全部通过后按本任务包的 Commit boundary 提交。
