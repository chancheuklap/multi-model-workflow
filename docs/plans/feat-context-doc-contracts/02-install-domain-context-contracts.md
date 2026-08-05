# Plan: 安装并检查领域上下文仓库合同

**Goal:** 让仓库维护者通过 MMW 幂等安装领域上下文消费规则，并让 `doctor` 在 `none`、`single`、`map` 三种领域形态下准确诊断合同。
**Source spec:** `docs/specs/feat-context-doc-contracts/feat-context-doc-contracts.md`
**Source ticket:** GitHub issue `#16`
**Blocked by:** Plan 01，GitHub issue `#15`
**Architecture:** 以两份 Markdown 种子作为受管正文的唯一事实来源；领域合同模块负责受管区块同步和结构检查；`mmw init` 只把安全且实际变化的目标登记进现有提交机制；`mmw domain` 暴露可重复验证的同步与检查命令；`mmw doctor` 消费同一检查结果。
**Tech stack:** Python 3 标准库、Bash、Git、GitHub 风格 Markdown、ShellCheck、临时 Git 仓库 fixture。

## Global Constraints

- `.mmw.json` 保存目标仓库的 `domain.map`、`domain.fallback`、`domain.context_dir` 和 `domain.adr_dir`；技能和 CLI 不写死目标仓库路径。
- `AGENTS.md` 规则覆盖主 agent 与 subagent。subagent task 不注入 leaf 路径。
- MMW 只管理 `AGENTS.md` 的领域上下文区块和 Map 的使用规则区块。`Contexts`、`Relationships` 与 leaf 内容归目标仓库所有。
- `none`、`single`、`map` 都是合法领域形态。`none` 不创建领域文档，`single` 不创建 Map，`map` 只更新已经存在的 Map。
- 修改既有 `AGENTS.md`、`CLAUDE.md` 或 Map 前，目标必须已被 Git 跟踪，且暂存区和工作区都干净。文件不存在时可以创建。
- 标记缺失一端、重复或次序错误时，命令必须非零退出。失败不得改写目标文件。
- 相同输入不得重写文件，也不得登记进初始化提交。
- 本仓库不保留自动化测试、测试夹具或测试套件。行为检查使用运行后删除的临时 Git 仓库。
- `archive/` 与 `vendor/` 是冻结内容，不参与本 plan。
- 本 plan 不修改技能源、三套技能物化目录、`mmw-skill-map.html`、发布 manifest 或版本字段。这些文件归 Plan 03。
- 本 plan 不执行 `git push`、远端合并、部署或正式发布。

## File / Responsibility Map

| 类型 | 文件 | 责任 |
| --- | --- | --- |
| Create | `mmw/cli/seeds/AGENTS-domain-context.md` | 保存 spec 已批准的完整 `AGENTS.md` 受管区块。 |
| Create | `mmw/cli/seeds/CONTEXT-MAP-rules.md` | 保存 spec 已批准的完整 Map 使用规则受管区块。 |
| Create | `mmw/cli/lib/context_docs.py` | 同步受管区块和 Claude bridge；保护既有目标的 Git 状态；检查三种领域形态、Map、leaf 与权威引用；输出稳定的 TSV 结果。 |
| Modify | `mmw/cli/lib/domain.sh` | 调用领域合同模块；更新 `map` 形态提示；保留现有 `path`、`dirs` 与 `adr-next` 合同。 |
| Modify | `mmw/cli/lib/init.sh` | 在初始化流程中消费安全同步结果，并登记实际变化路径。 |
| Modify | `mmw/cli/mmw` | 登记 `mmw domain sync`、`mmw domain check`，并把领域检查接入 `mmw doctor`。 |
| Modify | `AGENTS.md` | 通过新同步命令安装本 MMW 仓库的领域上下文受管区块。 |
| Test | 不创建测试文件 | 按 spec 的公开 seam 在临时 Git 仓库执行 fixture 矩阵。 |

## 小块清单

### 02.1 受管区块同步核心

- **要做什么：** 建立两份种子和 `mmw domain sync`，覆盖 AGENTS、已有 Map、Claude bridge、幂等、Git 状态保护与损坏标记失败。
- **验收：** `AGENTS.md` 与已有 Map 只改变受管区块；Map 不存在时不创建；Claude bridge 符合宿主规则；不安全或损坏输入保留整轮目标字节；本 MMW 仓库根 `AGENTS.md` 通过新命令安装受管区块，根 `CLAUDE.md` 保持 current。
- **被谁阻塞：** Plan 01。
- **执行方式：** AFK。

### 02.2 init 消费与变化登记

- **要做什么：** 让 `mmw init` 消费 02.1 已完成 Git 保护和 Claude bridge 处理的安全同步结果，并只登记实际变化。
- **验收：** 新文件可创建；同步失败不登记领域路径；同步成功只登记实际变化；current 结果不产生 diff 或空提交；九个脏目标经 `mmw init` 入口仍然非零且不夹带用户改动。
- **被谁阻塞：** 02.1。
- **执行方式：** AFK。

### 02.3 doctor 与三形态 fixture 验证

- **要做什么：** 建立 `mmw domain check`，更新 `mmw domain path` 的 Map 提示，并把检查结果接入 `mmw doctor`。
- **验收：** 三种合法形态返回成功；Claude Code 缺根 AGENTS 导入时返回失败；Pi/Codex 不要求该桥；损坏标记、Map 结构错误、越界或失效 leaf、失效权威引用返回失败。
- **被谁阻塞：** 02.2。
- **执行方式：** AFK。

## Dependency Graph

```mermaid
flowchart LR
  A[02.1 受管区块同步核心] --> B[02.2 init 消费与变化登记]
  B --> C[02.3 doctor 与三形态检查]
```

02.2 消费 02.1 的同步结果来登记初始化提交。02.3 使用 02.2 产生的真实仓库状态验证 `doctor`，因此按顺序实施。

## Cross-Plan CLI Contract

Plan 03 只消费下表中的公开合同，不修改本 plan 拥有的种子、模块或 CLI 接入。

| 命令 | 成功退出码 | 失败退出码 | stdout 形状 |
| --- | ---: | ---: | --- |
| `mmw domain sync` | `0` | `1` | 每个目标一行：`sync<TAB><agents\|map\|claude><TAB><仓库相对路径><TAB><created\|inserted\|updated\|appended\|current\|not-present\|not-required>`。 |
| `mmw domain check` | `0` | `1` | 成功时一行：`check<TAB><none\|single\|map><TAB><仓库相对路径或 -><TAB>valid`。失败时 stdout 为空，诊断写 stderr。 |
| `mmw domain path` | `0` | `1` | 保持三列 TSV：`<none\|single\|map><TAB><绝对路径或空><TAB><操作提示>`。`map` 的第三列固定为 `这是索引：读它，再读取它列出的本次相关全部 leaf`。 |
| `mmw domain dirs` | `0` | `1` | 固定四行 TSV，顺序为 `single`、`map`、`context`、`adr`；每行是 `<类型><TAB><配置验证后的绝对路径>`。 |
| `mmw doctor` | 所有检查通过时 `0` | 任一检查失败时 `1` | 领域成功行：`领域合同 : valid shape=<none\|single\|map> path=<仓库相对路径或 ->`；领域失败行：`领域合同 : invalid`，后接缩进诊断。 |

同步与检查失败的 stderr 每行固定为 `error<TAB><仓库相对路径><TAB><错误码><TAB><中文说明>`。本 ticket 使用 `invalid-markers`、`dirty-target`、`managed-drift`、`missing-claude-import`、`unreadable-single`、`missing-section`、`invalid-context-table`、`invalid-leaf`、`invalid-relationships`、`invalid-authoritative`、`invalid-config` 与 `io-error`。

两个受管区块使用以下 marker 字面量：

- `AGENTS.md`：`<!-- MMW-DOMAIN-CONTEXT-START -->` 与 `<!-- MMW-DOMAIN-CONTEXT-END -->`。
- Map：`<!-- MMW-CONTEXT-MAP-RULES-START -->` 与 `<!-- MMW-CONTEXT-MAP-RULES-END -->`。

## 发布风险与人工审批关卡

| 风险面 | 任务包 | Risk flag | 要不要提前发起审查 | 人工审批关卡由谁批准 |
| --- | --- | --- | --- | --- |
| 受管区块错误覆盖项目正文 | 02.1 | `managed-content`、`filesystem-write` | 要。审查同步 fixture 和失败前后字节摘要。 | 无。受管正文已由 spec 批准。 |
| 同步命令覆盖已有用户改动 | 02.1 | `git-state`、`managed-content` | 要。审查暂存、工作区与未跟踪三类 fixture。 | 无。失败策略已由 spec 批准。 |
| 初始化登记错误路径 | 02.2 | `automatic-commit` | 要。审查安全同步结果和初始化提交路径。 | 无。登记规则已由 spec 批准。 |
| doctor 漏报失效领域合同 | 02.3 | `contract-validation` | 要。审查合法与非法 fixture 矩阵。 | 无。检查合同已由 spec 批准。 |

### Task Pack 02.1: 受管区块同步核心

**Ticket:** GitHub issue `#16`
**Goal behavior:** `mmw domain sync` 从两份种子安全创建或更新 `AGENTS.md`、已有 Map 和 Claude bridge，只替换 MMW 拥有的内容，保护既有 Git 改动，并在输入无变化时保持目标文件不变。
**Why this matters:** 仓库维护者需要一个可升级的共同规则入口，同时继续拥有 Map 路由、关系和 leaf 内容。
**Owned files:** Create `mmw/cli/seeds/AGENTS-domain-context.md` / Create `mmw/cli/seeds/CONTEXT-MAP-rules.md` / Create `mmw/cli/lib/context_docs.py` / Modify `mmw/cli/lib/domain.sh:12` / Modify `mmw/cli/mmw:151` / Modify `mmw/cli/mmw:519` / Modify `AGENTS.md:1`

**Verified current state:** 2026-08-05 验证到 `mmw domain path` 只提供 `map`、`single`、`none` 三形态，并在 `map` 提示中假定 leaf 名为 `CONTEXT.md`（`mmw/cli/lib/domain.sh:12`）。`usage_domain` 和 `cmd_domain` 没有同步或检查子命令（`mmw/cli/mmw:151`、`mmw/cli/mmw:519`）。种子目录目前只有 `TESTING.md`（`mmw/cli/seeds/TESTING.md:1`）。本 MMW 仓库根 `AGENTS.md` 尚无 `MMW-DOMAIN-CONTEXT` marker（`AGENTS.md:1`）。

**先读：** spec 的 `Implementation Decisions` 第 1 至 4、6 项、两段受管正文、`Failure Paths`、`Testing Decisions`；`AGENTS.md:38` 的唯一事实来源和 `AGENTS.md:66` 的脚本失败规则；`TESTING.md:3` 与 `TESTING.md:5`。

**Interfaces:**

- **Consumes:** `.mmw.json` 的 `domain.map`、`domain.fallback` 与 `domain.context_dir`；两份种子文件的完整 UTF-8 字节。
- **Produces:** `mmw domain sync`。成功输出遵守 `Cross-Plan CLI Contract` 的四列 TSV；失败输出 `error` 四列 TSV 并返回 `1`。

**Contract anchors:** 归属方是 Plan 02。提供方是两份种子和目标仓库 `.mmw.json`。消费方是 `mmw init`、Plan 03 的架构图和后续 AgentFlow 迁移。同步器不修改 `Contexts`、`Relationships` 或 leaf。

**Schema / API shapes:** `agents` 永远是同步目标；`map` 只在配置的 Map 已存在时是同步目标。Claude Code 下，缺少 `CLAUDE.md` 时创建精确内容 `@AGENTS.md\n`；已有文件缺少独立一行 `@AGENTS.md` 时追加该行；已有该行时返回 `current`。Pi 与 Codex 返回 `claude not-required`。无 marker 时，`AGENTS.md` 在文件末尾插入种子，Map 在第一个 `## Contexts` 前插入种子；完整唯一 marker 对原位替换；单边、重复或逆序 marker 返回 `invalid-markers`。同步器先计算整轮目标与候选内容，再检查每个待修改的既有目标：该文件必须已被 Git 跟踪，且 `git diff --quiet -- <path>` 与 `git diff --cached --quiet -- <path>` 都成功；任一目标不安全时返回 `dirty-target`，整轮不写文件。每个安全目标在同目录写临时文件，再用原子替换写回。现有文件权限保持不变。

**Mockup specs:** 不适用。本 ticket 没有界面或原型。

**Do Not Touch:** 不修改 `mmw/skills/`、`mmw/skills-pi/`、`mmw/skills-claude-code/`、`mmw/skills-codex/`、`mmw-skill-map.html`、manifest、版本字段、Plan 01 或 spec。

**Fixture bootstrap:** 在源仓库执行 `source_root="$(git rev-parse --show-toplevel)"` 和 `fixture_root="$(mktemp -d)"`。每个 fixture 在 `${fixture_root}` 下使用独立目录，并配置仓库级 Git 用户。只清理本包创建的 `${fixture_root}`。

**Acceptance criteria:**

1. [ ] 缺少 `AGENTS.md` 时创建文件，文件字节等于 AGENTS 种子。
2. [ ] 无 marker 的 `AGENTS.md` 保留原正文，并在末尾插入一个受管区块。
3. [ ] 已有完整 marker 的 `AGENTS.md` 或 Map 只替换 marker 之间的正文。
4. [ ] 已有 Map 的 `Contexts`、`Relationships` 与其他项目正文在同步前后逐字节一致；缺少 Map 时不创建 Map。
5. [ ] 单边、重复或逆序 marker 让命令返回 `1`；目标文件 SHA-256 不变；同目录不残留临时文件。
6. [ ] 连续第二次对已同步输入运行命令时，各目标状态为 `current`、`not-present` 或 `not-required`；目标 mtime 与 Git diff 不变。
7. [ ] Claude Code 新仓库创建单行 `CLAUDE.md`；已有干净文件追加精确导入；已有导入返回 `current`；Pi 与 Codex 返回 `not-required`。
8. [ ] 待修改的既有 AGENTS、CLAUDE 或 Map 处于未跟踪、已暂存或工作区修改状态时，直接运行 `mmw domain sync` 返回 `1` 和 `dirty-target`；整轮所有目标的 SHA-256 与暂存区不变。
9. [ ] 在本 MMW 仓库运行新同步命令后，根 `AGENTS.md` 包含与种子逐字一致的唯一受管区块并进入 02.1 提交；根 `CLAUDE.md` 返回 `current` 且无 diff。

**Verification commands:**

- `MMW_HOST=codex "${source_root}/mmw/cli/mmw" domain sync` → Expected: 在临时 `none` 仓库输出 `agents created`、`map not-present`、`claude not-required` 四列 TSV，退出码 `0`。
- 对已提交的无 marker 文件、旧完整区块、已有 Map 分别运行同一命令 → Expected: 状态依次覆盖 `inserted` 与 `updated`；非受管正文的 SHA-256 分片不变。
- 对单边、重复和逆序 marker fixture 运行同一命令 → Expected: 三次均退出 `1`，stderr 错误码为 `invalid-markers`，完整目标 SHA-256 不变。
- 使用 `MMW_HOST=claude-code` 对缺少 CLAUDE、已有其他正文、已有 `@AGENTS.md` 三个 fixture 运行同一命令 → Expected: `claude` 状态依次为 `created`、`appended`、`current`。
- 对 AGENTS、CLAUDE 和 Map 分别建立未跟踪、已暂存、工作区修改三个待更新 fixture，直接运行同一命令 → Expected: 九个 fixture 都退出 `1` 并报告 `dirty-target`；整轮目标摘要和用户暂存区不变。
- 对已经同步并提交的 fixture 连续运行两次同一命令 → Expected: 第二次目标状态为 `current`，`git diff --exit-code` 返回 `0`，mtime 不变。
- 在本 MMW 仓库先运行 `MMW_HOST=codex "${source_root}/mmw/cli/mmw" domain sync`，再运行 `MMW_HOST=claude-code "${source_root}/mmw/cli/mmw" domain sync` → Expected: 第一次 `agents` 为 `inserted`；第二次 AGENTS 与 CLAUDE 都为 `current`；根 `CLAUDE.md` 无 diff。

**Browser acceptance:** 不适用。本任务包没有界面行为。

**Testing pyramid:**

| 层 | 测什么 | 数量 |
| --- | --- | ---: |
| 临时 Git 仓库行为检查 | 创建、插入、升级、Map 保留、缺失 Map、Claude 三种状态、六个损坏 marker、九个 Git 状态错误、幂等、原子失败。 | 25 个 fixture |
| 提交前静态检查 | ShellCheck、Python 语法、空白错误。 | 3 条命令 |
| 真实宿主验证 | 本包不改变宿主运行面。 | 0 |

**Rollback:** 回滚本任务包提交会删除新命令和种子。已经写入目标仓库的受管区块属于另一个仓库的已提交内容，需要在该仓库单独回滚。

**Complexity:** standard。
**Commit boundary:** 同步 fixture 全部通过后，用新命令更新根 `AGENTS.md` 并验证根 `CLAUDE.md` 为 current，再把两份种子、领域合同模块、`domain sync` 接入和根 `AGENTS.md` 受管区块放进同一个提交。根 `CLAUDE.md` 不进入该提交。建议提交信息：`feat: add domain context rule sync (#16)`。
**Risk flags:** `managed-content`、`filesystem-write`、`atomic-replace`、`git-state`。
**发布风险:** 命令会写目标仓库的 Markdown。损坏 marker 必须先于任何写入被发现。
**HITL 还是 AFK:** AFK。正文和失败策略已由 spec 定死。
**Dependencies:** Plan 01 已集成。
**Out of scope:** init 登记、doctor、技能、物化产物、架构图、版本与 AgentFlow 迁移。

#### Implementation tasks

- [ ] Step 1: 建立同步 red fixture。创建临时 Git 仓库，复制 `mmw/cli/mmw.default.json` 为 `.mmw.json`，运行 `MMW_HOST=codex "${source_root}/mmw/cli/mmw" domain sync`。预期当前命令进入 `usage_domain` 并返回 `2`。
- [ ] Step 2: 创建两份种子和同步模块。种子逐字复制 spec 已批准的两个代码块；同步模块实现唯一 marker 对解析、AGENTS 与 Map 更新、Claude bridge、幂等判断、同目录临时文件与原子替换。
- [ ] Step 3: 在 `domain.sh` 和 `mmw` 暴露 `mmw domain sync`，输出 `Cross-Plan CLI Contract` 的四列 TSV。运行缺文件、无 marker、旧区块、已有 Map 和 Claude 三种状态 fixture，预期退出 `0` 且状态分别准确。
- [ ] Step 4: 建立失败 red fixture。为 AGENTS 与 Map 分别构造单边、重复、逆序 marker；为 AGENTS、CLAUDE 与 Map 分别构造未跟踪、已暂存、工作区修改状态；保存整轮目标 SHA-256 和暂存区 diff 后运行同步。若任一命令返回 `0` 或任一证据改变，则该步失败。
- [ ] Step 5: 让失败路径变绿。同步器在生成任何临时文件前完成整轮 marker 和 Git 状态预检；六个 marker fixture 返回 `invalid-markers`，九个 Git fixture 返回 `dirty-target`，所有文件摘要和暂存区不变。
- [ ] Step 6: 验证幂等、Map 所有权和当前仓库安装。对已同步并提交的 Map 再运行两次，确认项目正文、Git diff 与 mtime 不变；随后在本 MMW 仓库先以 Codex 宿主同步，再以 Claude Code 宿主同步，确认根 `AGENTS.md` 从 `inserted` 变为 `current`，根 `CLAUDE.md` 始终是 `current` 且无 diff。
- [ ] Step 7: 运行 `python3 -m py_compile mmw/cli/lib/context_docs.py`、`shellcheck --severity=warning mmw/cli/mmw mmw/cli/lib/domain.sh` 与 `git diff --check`。确认根 `AGENTS.md` 在 diff 中且根 `CLAUDE.md` 不在 diff 中；全部返回 `0` 后按 Commit boundary 提交。

### Task Pack 02.2: init 消费与变化登记

**Ticket:** GitHub issue `#16`
**Goal behavior:** `mmw init` 在三种领域形态下消费 02.1 已完成 Git 保护和 Claude bridge 处理的安全同步结果，初始化提交只登记本轮实际改变的目标。
**Why this matters:** 仓库维护者需要用既有入口安装合同，并让现有提交机制准确区分 changed 与 current 结果。
**Owned files:** Modify `mmw/cli/lib/init.sh:16` / Modify `mmw/cli/lib/init.sh:186` / Modify `mmw/cli/lib/init.sh:233`

**Verified current state:** 2026-08-05 验证到 `MMW_INIT_TOUCHED` 记录本轮路径（`mmw/cli/lib/init.sh:16`），`mmw_init_commit` 对每个登记路径执行 `git add` 并按路径提交（`mmw/cli/lib/init.sh:186`），但 `mmw_init` 没有领域同步步骤（`mmw/cli/lib/init.sh:233`）。根 `CLAUDE.md` 当前使用单行 `@AGENTS.md`（`CLAUDE.md:1`），可作为桥接合同样例。

**先读：** spec 的 `Implementation Decisions` 第 4 至 7 项、`Failure Paths` 的目标文件已有改动与同步无变化两行、`Testing Decisions` 的 `mmw init` seam；`AGENTS.md:46` 的宿主边界；`TESTING.md:3` 与 `TESTING.md:5`。

**Interfaces:**

- **Consumes:** 02.1 的 `mmw domain sync` 四列 TSV；现有 `mmw_init_touch <仓库相对路径>` 与 `mmw_init_commit()`；`mmw_host()` 返回的 `claude-code`、`pi` 或 `codex`。
- **Produces:** `mmw init` 的 `领域规则 : agents=<状态> map=<状态> claude=<状态>` 日志行，以及与 changed 状态一致的 `MMW_INIT_TOUCHED` 路径集合。

**Contract anchors:** `AGENTS.md` 与 Map 受管正文由 02.1 提供。根 `CLAUDE.md` 由目标仓库提供并由 Claude Code 消费。`MMW_INIT_TOUCHED` 只登记状态为 `created`、`inserted`、`updated` 或 `appended` 的仓库相对路径。

**Schema / API shapes:** `mmw init` 不重复实现同步、Claude bridge 或 Git 状态预检，只解析 02.1 的安全同步结果。`created`、`inserted`、`updated`、`appended` 进入 `MMW_INIT_TOUCHED`；`current`、`not-present`、`not-required` 不登记。同步命令返回 `1` 时，init 记录 stderr、最终返回非零，并且不登记任何领域路径。

**Mockup specs:** 不适用。本任务包没有界面或原型。

**Do Not Touch:** 不改 `mmw_init_commit` 的按路径提交语义，不把用户已有暂存内容清空或提交；不修改全局宿主配置、技能、物化产物、架构图、版本或 AgentFlow。

**Fixture bootstrap:** 在源仓库执行 `source_root="$(git rev-parse --show-toplevel)"`、`fixture_root="$(mktemp -d)"`、`fixture_codex="${fixture_root}/codex-home"` 与 `fixture_bin="${fixture_root}/bin"`。每个 fixture 在 `${fixture_root}` 下使用独立目录，并配置仓库级 Git 用户。只清理本包创建的 `${fixture_root}`。

**Acceptance criteria:**

1. [ ] `none` 与 `single` 的 `mmw init` 只同步 `AGENTS.md`；`map` 同步 `AGENTS.md` 与已有 Map；三种形态都不创建新的领域文档。
2. [ ] Claude Code 新仓库创建单行 `CLAUDE.md`；已有干净文件追加精确导入；已有导入不改；Pi 与 Codex 不改 `CLAUDE.md`。
3. [ ] 安全同步后，只有实际改变的 AGENTS、CLAUDE 或 Map 进入 `MMW_INIT_TOUCHED` 和初始化提交；状态为 `current`、`not-present` 或 `not-required` 的路径不登记。
4. [ ] 连续第二次运行 `mmw init` 不产生领域文件 diff，也不产生只包含领域文件的空提交。
5. [ ] `mmw init` 消费 AGENTS 与 CLAUDE 均为 `current` 的安全结果时，不登记这两个路径，也不产生领域文件 diff。
6. [ ] AGENTS、CLAUDE、Map 分别处于未跟踪、已暂存或工作区修改状态且需要更新时，经 `mmw init` 运行的九个 fixture 都返回非零；日志包含 `dirty-target` 和未完成提示；目标 SHA-256、暂存区 diff 与用户改动保持不变；初始化提交不包含对应脏目标。

**Verification commands:**

- 在临时仓库中运行 `MMW_HOST=codex CODEX_HOME="${fixture_codex}" MMW_CODEX_BIN_DIR="${fixture_bin}" MMW_CODEX_PLUGIN_ROOT="${source_root}/mmw" "${source_root}/mmw/cli/mmw" init` → Expected: `none` 仓库提交新 `AGENTS.md`，不创建 Map 或 `CLAUDE.md`。
- 使用 `MMW_HOST=claude-code` 在根 `CLAUDE.md` 已存在与不存在的两个隔离 fixture 运行 `mmw init` → Expected: 分别追加或创建一行 `@AGENTS.md`，第二次运行不改文件。
- `git show --name-only --format= HEAD` → Expected: 现有初始化路径可以出现；领域路径只包含本轮状态为 `created`、`inserted`、`updated` 或 `appended` 的 AGENTS、CLAUDE 或 Map，不能出现脏目标。
- 在 AGENTS 与 CLAUDE 已是 current 的临时仓库再次运行 `mmw init` → Expected: 初始化日志显示两个 `current`；提交路径不含 AGENTS 或 CLAUDE；领域文件无 diff。
- 对 AGENTS、CLAUDE、Map 分别建立未跟踪、已暂存、工作区修改三个待更新 fixture，经对应宿主运行 `mmw init` → Expected: 九次均返回非零；stdout 或 stderr 保留 `dirty-target` 和 init 未完成信息；运行前后的目标 SHA-256、`git diff --cached --binary` 与用户工作区 diff 相同；若 init 提交了其他新配置，`git show --name-only --format= HEAD` 不含脏目标。

**Browser acceptance:** 不适用。本任务包没有界面行为。

**Testing pyramid:**

| 层 | 测什么 | 数量 |
| --- | --- | ---: |
| 临时 Git 仓库行为检查 | 三形态路由、Claude 新建与追加、已有导入、九个脏目标的失败传播、实际变化登记、第二轮幂等。 | 17 个 fixture |
| 提交前静态检查 | ShellCheck、空白错误。 | 2 条命令 |
| 真实宿主验证 | fixture 通过 `MMW_HOST` 和隔离的 Codex 路径运行；不声明真实宿主已验证。 | 0 |

**Rollback:** 回滚本任务包提交会移除初始化接入。目标仓库中已经提交的规则文件需要在目标仓库单独回滚。

**Complexity:** standard。
**Commit boundary:** 十七个 init fixture 全部通过后，只提交 `init.sh` 的安全结果消费、失败传播和变化登记接入。根 `CLAUDE.md` 不进入提交。建议提交信息：`feat: install domain context contracts in init (#16)`。
**Risk flags:** `automatic-commit`、`cross-host`。
**发布风险:** 错误的路径登记可能夹带用户改动。验收必须同时检查提交内容和保留的暂存区。
**HITL 还是 AFK:** AFK。宿主差异和提交边界已由 spec 定死。
**Dependencies:** 02.1 已完成。
**Out of scope:** doctor、Map 语义推断、技能、物化产物、架构图、版本与 AgentFlow 迁移。

#### Implementation tasks

- [ ] Step 1: 建立 init red fixture。用 `none`、`single`、`map` 和 Claude Code 三类临时仓库运行 `mmw init`，记录提交路径与领域日志。预期当前实现不安装或登记领域目标。
- [ ] Step 2: 在 `init.sh` 调用 02.1 的同步入口。成功时解析四列 TSV，只把 changed 状态路径传给 `mmw_init_touch`；失败时记录结构化诊断、最终返回非零并且不登记领域路径。
- [ ] Step 3: 经 `mmw init` 运行 AGENTS、CLAUDE、Map 各三种 Git 状态 fixture。预期九次都非零并保留 `dirty-target`；比较运行前后的文件摘要、暂存区二进制 diff、工作区 diff 和最新提交路径，确认失败未被吞掉且没有初始化提交夹带脏目标。
- [ ] Step 4: 重跑 `none`、`single`、`map` 三个合法 fixture。预期 AGENTS 总是安装，只有已有 Map 被更新，fallback 和 leaf 都不创建或改写；提交路径与 changed 状态一致。
- [ ] Step 5: 重跑 Claude Code 的创建、追加与 current 三个合法 fixture。预期 CLAUDE 的 changed 状态被登记，current 状态不登记；`init.sh` 没有第二套 bridge 或 Git 预检逻辑。
- [ ] Step 6: 连续运行两次 `mmw init`，比较第二次前后的 HEAD、目标 mtime 与 `git status --short`。预期第二次日志全部是 current、not-present 或 not-required，不产生领域文件变化或空提交。
- [ ] Step 7: 运行 `shellcheck --severity=warning mmw/cli/lib/init.sh` 与 `git diff --check`。确认本包 diff 只有 `init.sh` 后按 Commit boundary 提交。

### Task Pack 02.3: doctor 与三形态 fixture 验证

**Ticket:** GitHub issue `#16`
**Goal behavior:** `mmw domain check` 和 `mmw doctor` 接受合法的 `none`、`single`、`map`，并用可定位诊断拒绝损坏规则、Map、leaf 或权威引用；`mmw domain dirs` 返回领域建模所需的四个配置落点。
**Why this matters:** agent 开工前需要发现领域消费合同漂移，避免使用错误术语或遗漏相关 leaf。
**Owned files:** Modify `mmw/cli/lib/context_docs.py` / Modify `mmw/cli/lib/domain.sh:12` / Modify `mmw/cli/mmw:151` / Modify `mmw/cli/mmw:519` / Modify `mmw/cli/mmw:571`

**Verified current state:** 2026-08-05 验证到 `mmw doctor` 检查仓库、配置、依赖、宿主产物与 MCP，但没有领域合同检查（`mmw/cli/mmw:571`）。`mmw domain path` 的 `map` 输出仍写死 `CONTEXT.md`（`mmw/cli/lib/domain.sh:25`）。`domain.context_dir` 当前默认是 `docs/context`（`mmw/cli/mmw.default.json:119`）。

**先读：** spec 的 `Implementation Decisions` 第 6、8 至 12 项、`Failure Paths`、`Testing Decisions`、`Contract Boundaries`；`AGENTS.md:38` 的 `.mmw.json` 路径规则与 `AGENTS.md:78` 的领域文档位置规则；`TESTING.md:3`、`TESTING.md:5` 与 `TESTING.md:22`。

**Interfaces:**

- **Consumes:** 02.1 的两份种子与 marker；02.2 完成后的仓库文件；`.mmw.json` 的 map、fallback、context 与 ADR 路径。
- **Produces:** `mmw domain check`、更新后的 `mmw domain path`、四行 `mmw domain dirs` 和 `mmw doctor` 领域状态行。退出码和 stdout 遵守 `Cross-Plan CLI Contract`。

**Contract anchors:** Plan 02 拥有检查器和 CLI 输出。Plan 03 消费命令名、退出码、stdout 形状和 marker 字面量；Plan 03 不复制检查逻辑。Map 的 `Contexts` 与 `Relationships` 由目标仓库提供，doctor 只验证结构和路径，不解释关系语义。

**Schema / API shapes:** 三种领域形态先检查 AGENTS 受管区块。`MMW_HOST=claude-code` 时还要求根 `CLAUDE.md` 含独立一行 `@AGENTS.md`；文件缺失或缺少该行时返回 `missing-claude-import`。Pi 与 Codex 不检查 Claude bridge。`single` 另读取 fallback；`map` 另检查 Map 规则、唯一的 `## Contexts`、唯一的 `## Relationships`、精确三列表头 `Context`、`Leaf`、`Owns`、至少一条关系以及每一行 leaf。`Context` 非空且唯一；`Leaf` 整格只能是一个 Markdown 链接，按 Map 位置解析后必须位于 `mmw domain dirs` 返回的 `context` 目录内、以 `.md` 结尾且可读；`Owns` 非空。每个已登记 leaf 中出现的 `authoritative:` 都必须符合 `(authoritative: [显示文本](相对路径))`，并解析为 context 目录内且已登记的 leaf。`mmw domain dirs` 使用同一配置验证结果，按 `single`、`map`、`context`、`adr` 顺序输出四个绝对路径；即使当前形态为 `none`，前两行仍提供按需创建首份 fallback 或 Map 的落点。

**Mockup specs:** 不适用。本任务包没有界面或原型。

**Do Not Touch:** 不把关系端点或 `Owns` 自然语言变成机器语法；不猜 bounded context；不修改领域文档；不修改技能、物化产物、架构图、版本或 AgentFlow。

**Fixture bootstrap:** 在源仓库执行 `source_root="$(git rev-parse --show-toplevel)"` 和 `fixture_root="$(mktemp -d)"`。每个 fixture 在 `${fixture_root}` 下使用独立目录，并配置仓库级 Git 用户。只清理本包创建的 `${fixture_root}`。

**Acceptance criteria:**

1. [ ] 合法 `none` 输出 `check<TAB>none<TAB>-<TAB>valid` 并返回 `0`。
2. [ ] 合法 `single` 输出 fallback 相对路径和 `valid` 并返回 `0`；fallback 不可读时返回 `unreadable-single`。
3. [ ] 合法 `map` 输出 Map 相对路径和 `valid` 并返回 `0`；命名 leaf 和 context 子目录中的 leaf 都被接受。
4. [ ] AGENTS 或 Map 受管区块缺失、漂移或 marker 损坏时返回 `1`，并点名文件。
5. [ ] 缺失固定节、错误表头、空或重复 Context、非单链接 Leaf、空 Owns、空 Relationships 分别返回结构化错误。
6. [ ] 绝对路径、越出 context 目录、非 Markdown、失效或不可读 Leaf 返回 `invalid-leaf`。
7. [ ] 格式错误、越界、未登记或失效的权威引用返回 `invalid-authoritative`，并点名来源 leaf 与目标。
8. [ ] `mmw doctor` 复用同一检查结果；领域失败把 doctor 最终退出码置为 `1`。
9. [ ] `mmw domain path` 的 `map` 第三列使用 Cross-Plan CLI Contract 的固定提示，不再出现 leaf 文件名假设。
10. [ ] 本 MMW 仓库的 `mmw domain check` 输出 `check<TAB>none<TAB>-<TAB>valid`；`mmw doctor` 输出 `领域合同 : valid shape=none path=-`，领域检查本身不再判红。
11. [ ] 同一个合法领域 fixture 在 Claude Code 宿主下，根 `CLAUDE.md` 含独立一行 `@AGENTS.md` 时 `domain check` 和 doctor 的领域检查均为 valid；缺少文件或缺少该行时均返回 `missing-claude-import`，`domain check` 返回 `1` 且 doctor 最终返回 `1`。同一 fixture 在 Pi 与 Codex 宿主下不因缺少 `CLAUDE.md` 判红。
12. [ ] 自定义 map、fallback、context 和 ADR 路径时，`mmw domain dirs` 按固定顺序返回四个准确绝对路径；任一字段越出仓库时返回 `invalid-config`。

**Verification commands:**

- 在合法 `none`、`single`、`map` 临时仓库分别运行 `MMW_HOST=codex "${source_root}/mmw/cli/mmw" domain check` → Expected: 三次退出 `0`，stdout 分别匹配三种 `check` 四列 TSV。
- 在损坏 marker、缺节、错表头、空关系、越界 leaf、失效 leaf、非 Markdown leaf、未登记权威引用和失效权威引用 fixture 运行同一命令 → Expected: 全部退出 `1`，stdout 为空，stderr 点名来源路径和对应错误码。
- 对同一个合法 `none` fixture 分别运行：Claude Code 且有 `@AGENTS.md`、Claude Code 且缺 `CLAUDE.md`、Claude Code 且文件中缺该行、Codex/Pi 且无 `CLAUDE.md` → Expected: 第一种 `domain check` 返回 `0`；中间两种返回 `1` 和 `missing-claude-import`，doctor 领域行是 invalid 且最终返回 `1`；最后一种在 Codex 与 Pi 下均保持 valid。
- `MMW_HOST=codex "${source_root}/mmw/cli/mmw" domain path` → Expected: `map` fixture 第三列精确等于 `这是索引：读它，再读取它列出的本次相关全部 leaf`。
- 在四个领域路径均使用自定义相对路径的 `none` fixture 运行 `MMW_HOST=codex "${source_root}/mmw/cli/mmw" domain dirs` → Expected: 依次输出 `single`、`map`、`context`、`adr` 及对应绝对路径；把 `adr_dir` 改为 `../outside` 后返回 `1` 和 `invalid-config`。
- `MMW_HOST=codex "${source_root}/mmw/cli/mmw" doctor` → Expected: 合法 fixture 包含 `领域合同 : valid shape=...`；非法 fixture 包含 `领域合同 : invalid`，且最终退出码为 `1`。doctor 的其他本机检查结果不替代领域行断言。
- 在本 MMW 仓库运行 `MMW_HOST=codex "${source_root}/mmw/cli/mmw" domain check` 和 `MMW_HOST=codex "${source_root}/mmw/cli/mmw" doctor` → Expected: 前者返回 `check<TAB>none<TAB>-<TAB>valid`；后者包含 `领域合同 : valid shape=none path=-`。doctor 的总退出码仍由其他本机检查共同决定。

**Browser acceptance:** 不适用。本任务包没有界面行为。

**Testing pyramid:**

| 层 | 测什么 | 数量 |
| --- | --- | ---: |
| 临时 Git 仓库行为检查 | 三种合法形态、四个宿主 bridge fixture、六类受管规则错误、八类 Map 结构错误、五类 leaf 错误、四类权威引用错误，以及自定义四路径与越界路径；doctor、domain path 与 domain dirs 复用这些仓库。 | 32 个 fixture |
| 提交前静态检查 | ShellCheck、Python 语法、完整仓库检查。 | 4 条命令 |
| 真实宿主验证 | CLI 文件行为不声明五个真实宿主已经通过。 | 0 |

**Rollback:** 回滚本任务包提交会移除 checker、doctor 接入和 Map 提示更新；不会改动目标仓库领域文档。

**Complexity:** standard。
**Commit boundary:** 三种合法形态和全部错误 fixture 通过后提交 checker、doctor 与 domain path 更新。建议提交信息：`feat: check domain context contracts (#16)`。
**Risk flags:** `contract-validation`、`path-containment`、`cross-host-cli`。
**发布风险:** 漏报会让 agent 消费错误合同，误报会阻止开工。路径检查必须使用解析后的真实路径做 context 目录包含关系判断。
**HITL 还是 AFK:** AFK。合法结构和失败条件已由 spec 定死。
**Dependencies:** 02.2 已完成。
**Out of scope:** 关系语义解析、领域文档自动修复、技能、物化产物、架构图、版本、AgentFlow 迁移和真实宿主验收。

#### Implementation tasks

- [ ] Step 1: 建立检查 red fixture。对 02.2 产出的合法 `none`、`single`、`map` 仓库，以及 Claude bridge valid、缺文件、缺导入行仓库运行 `mmw domain check`。预期当前命令进入 `usage_domain` 并返回 `2`。
- [ ] Step 2: 在领域合同模块实现三形态和宿主 bridge 检查，并在 `domain.sh` 和 `mmw` 暴露 `mmw domain check`。按 `Schema / API shapes` 读取真实文件，不扫描源码文本，不修改 fixture。
- [ ] Step 3: 运行三种合法形态、Claude Code bridge valid/缺文件/缺导入行、Pi/Codex 无 CLAUDE、自定义四路径、越界路径和其他错误矩阵。预期合法 fixture 返回四列 `valid`；`domain dirs` 返回固定顺序的四个绝对路径；Claude 两种缺失都返回 `missing-claude-import`；Pi/Codex 不因缺桥判红；其他非法 fixture stdout 为空、stderr 返回精确错误码和路径。
- [ ] Step 4: 建立 CLI 集成 red 证据。对 `map` fixture 断言 `mmw domain path` 第三列的固定提示；对一般合法/非法 fixture 和 Claude bridge valid/missing fixture 断言 `mmw doctor` 领域行和最终退出码。预期当前提示或领域行至少一项不符合合同。
- [ ] Step 5: 更新 `mmw domain path` 的 Map 提示，并在 `cmd_doctor` 检查到仓库与配置后调用同一个领域检查入口。成功时打印 `valid` 行；失败时打印 `invalid`、缩进诊断并把最终状态置为 `1`。
- [ ] Step 6: 重跑 `domain path`、`domain dirs`、`domain check` 与 doctor fixture，再在本 MMW 仓库运行 `domain check` 和 doctor。预期 fixture 的命令名、退出码和 stdout 逐字符合 `Cross-Plan CLI Contract`；当前仓库领域形态为 `none`，两条检查命令的领域合同均为 valid。
- [ ] Step 7: 运行 `python3 -m py_compile mmw/cli/lib/context_docs.py`、`shellcheck --severity=warning mmw/cli/mmw mmw/cli/lib/domain.sh mmw/cli/lib/init.sh`、`git diff --check` 和根 `TESTING.md` 的全部静态检查。确认 diff 不含技能、物化目录、架构图、manifest 或版本字段后，按 Commit boundary 提交。
