---
ticket: 42
artifact_refs: []
---

# Plan: Wiki 退役、`.mmw.json` 收窄与 `mmw doctor` 报告

**Goal:** spec 与 plan 长期留在仓库。Wiki 命令和归档流程消失。`mmw init` 收窄目标仓库配置。`mmw doctor` 只读报告遗留配置与历史产物。
**Source spec:** `docs/specs/mmw-artifact-wiring/mmw-artifact-wiring.md`
**Source ticket:** GitHub issue `#42`

## Constraints

- 删除 `mmw/cli/lib/wiki.sh` 与 `mmw/cli/tests/test_wiki.sh`。不得保留停用文件或兼容分支。来源：spec 第 17 节、`Release Risk`、ADR `0001-spec-plan-stay-in-repo.md:11-20`。
- 用户已经批准这两份文件的删除。MMW 自身 Wiki 没有内容会丢失。来源：spec `Release Risk`、ticket `#42`。
- spec 与 plan 继续留在仓库。`/mmw-closing` 不再删除它们，也不再执行对外发布。来源：spec 第 17 节、ADR `0001-spec-plan-stay-in-repo.md:1-20`。
- `mmw doctor` 的两组报告只读。任何报告都不得改变诊断命令原有退出码。来源：spec 第 18 节、ADR `0008-no-migration-command.md:13-21`。
- 历史产物不自动移动或删除。机器只报告三类可直接判定的旧路径。来源：spec 第 18 节、ADR `0008-no-migration-command.md:15-21`。
- `.mmw.json.paths` 只保留 `scratch`、`reviews`、`release`、`worktrees`。迁移必须保留这四个键的现有取值。来源：spec 第 17 节、`Contract Boundaries`。
- 初始化实现由本 plan 独占。plan 06 只消费初始化不再写 `.dispatch/` 的结果。来源：spec `Cross-Plan Contract Anchors`。
- `mmw/cli/mmw` 的共享用法与顶层分发分区只删除 `wiki`。不得重排或改写其他 plan 拥有的子命令行。`cmd_doctor` 的报告逻辑属于本 ticket。
- 保留 `cmd_doctor` 的 GitHub HTTPS 推送鉴权检查与原有失败退出行为。只删除失败提示里的「（推 Wiki 要它）」。来源：`mmw/cli/mmw:594-604`、spec 第 18 节、ticket `#42`。
- `mmw/test.sh` 只删除 Wiki 测试入口。plan 01 与 plan 11 各自增加自己的测试入口。来源：spec `Cross-Plan Contract Anchors`。
- 当前 `AGENTS.md` 的提交检查段没有 Wiki 文案。本 plan 不修改该文件。若集成前该分区出现 Wiki 文案，只能删除该分区内的 Wiki 内容。
- 领域文档 leaf 与 `CONTEXT-MAP.md` 归 plan 10。本 plan 不删除「Wiki 页面」术语。来源：spec `Cross-Plan Contract Anchors`。
- `mmw-closing/SKILL.md` 与 `mmw-start/resuming.md` 整份归本 plan。plan 07 不碰这两份文件。完整重写时，每个 spec、plan、scratch 与审查记录落点都直接使用完整的 `mmw artifact path …` 命令，不保留旧路径字面值。来源：spec `Cross-Plan Contract Anchors`。
- `mmw-implement/SKILL.md:135` 的 Wiki 归档和删除本地 spec 与 plan 语义归本 plan。该行的落点字面值仍归 plan 07。`mmw-start/SKILL.md:92` 的「Wiki 写一次」语义归本 plan。只改这两个语义分区。来源：spec `Cross-Plan Contract Anchors`、ADR `0001-spec-plan-stay-in-repo.md:1-20`。
- 删除 `mmw/cli/mmw.default.json` 顶层 `wiki` 配置块。`mmw init` 还要从已有 `.mmw.json` 删除顶层 `wiki`，并让 `mmw doctor` 把该键作为遗留配置报告。报告不得改变退出码。来源：`mmw/cli/mmw.default.json:93-95`、`mmw/cli/lib/init.sh:29-80`、ADR `0001-spec-plan-stay-in-repo.md:1-20`、`AGENTS.md` 的修改规则。
- 修改技能源前，完整读取对应 `SKILL.md` 与链接的 reference。只改 `mmw/skills-src/`，再物化全部宿主产物。来源：`AGENTS.md:44-46,64-72`。
- 本 ticket 没有 prototype 资产，也没有 research。来源：ticket `#42`。

## Current State

- CLI 会载入 `lib/wiki.sh`。顶层用法、`usage_wiki`、`cmd_wiki` 和顶层分发公开 `ensure`、`nav`、`verify`。出处：`mmw/cli/mmw:32-33,46-68,168-177,455-464,720-735`。
- Wiki 实现维护工作副本、导航与删前验证。对应测试在本地 Git 仓库中覆盖导航和验证。出处：`mmw/cli/lib/wiki.sh:1-156`、`mmw/cli/tests/test_wiki.sh:1-112`。
- 完整测试入口仍运行 Wiki 测试。出处：`mmw/test.sh:24-29`。
- `mmw-closing` 仍把 Wiki 设为唯一事实来源。它前六步写 Wiki并删除仓库里的 spec 与 plan。第七步还含界面证据和派发目录的补偿清理。出处：`mmw/skills-src/mmw-closing/SKILL.md:8-108`。
- 恢复流程仍通过 Wiki 页面判断归档。出处：`mmw/skills-src/mmw-start/resuming.md:15-31`。
- `mmw-implement` 的下一步表仍要求 `/mmw-closing` 把 spec 与 plan 归档到 Wiki，再删除本地长期产物。`mmw-start` 仍把一次交付概括为「Wiki 写一次」。出处：`mmw/skills-src/mmw-implement/SKILL.md:135`、`mmw/skills-src/mmw-start/SKILL.md:92`、ADR `0001-spec-plan-stay-in-repo.md:1-20`。
- `test_skill_refs.sh` 会校验反引号中的 `mmw <命令>`，不会校验这两处散文的 Wiki 语义。出处：`mmw/cli/tests/test_skill_refs.sh:1-20,60-61,85-105`。
- 默认配置的 `paths` 已只含四个工作目录根键，但顶层仍有 `wiki` 配置块。新配置只执行 `del(.models)`，因此会复制该块；已有配置的快速返回条件与迁移删除列表也不处理顶层 `wiki`。出处：`mmw/cli/mmw.default.json:81-95`、`mmw/cli/lib/init.sh:29-80`。
- 初始化仍把 `.dispatch/` 写入 `.gitignore`。它的真实 worktree 用例也依赖该目录被忽略。出处：`mmw/cli/lib/init.sh:174-201,238-242`、`mmw/cli/tests/test_init.sh:76-88,110-128`。
- `cmd_doctor` 用局部 `status` 累积诊断结果。它没有历史产物或遗留配置报告。GitHub HTTPS 推送鉴权失败时，它仍把 `status` 设为 1；只有失败提示末尾的括号把该检查说成 Wiki 专用。出处：`mmw/cli/mmw:552-604,716`。
- `test_init.sh` 当前没有运行 `mmw doctor`。spec 也把两组新报告的测试归到这份文件。出处：`mmw/cli/tests/test_init.sh:1-214`、spec `Testing Decisions`。
- 技能物化器从 `mmw/skills-src/` 生成 Pi、Claude Code 和 Codex 产物。Pi 的用户入口另生成到 `mmw/prompts-pi/`。出处：`mmw/cli/lib/materialize_skills.py:20-27,311-392`。

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `mmw/cli/lib/wiki.sh` | Delete | 删除 Wiki 工作副本、导航和验证实现 |
| `mmw/cli/tests/test_wiki.sh` | Delete | 删除三个退役子命令的专用测试 |
| `mmw/cli/mmw` | Modify | 删除 Wiki 载入、用法、命令函数和顶层分发；保留 GitHub HTTPS 推送鉴权诊断，只删提示中的 Wiki 限定语；增加两组只读报告 |
| `mmw/cli/mmw.default.json` | Modify | 删除已退役功能的顶层 `wiki` 配置块 |
| `mmw/test.sh` | Modify | 只删除运行 `test_wiki.sh` 的一行 |
| `mmw/cli/lib/init.sh` | Modify | 保持四键配置迁移；从已有配置删除顶层 `wiki`；删除 `.dispatch/` 忽略项；更新同段注释和初始化报告 |
| `mmw/cli/tests/test_init.sh` | Test | 锁定四键迁移、顶层 `wiki` 清理、五项忽略清单、两组诊断报告、推送鉴权、排除项和退出码 |
| `mmw/skills-src/mmw-closing/SKILL.md` | Modify | 完整重写流程；全部落点通过 `mmw artifact path …` 解析；只保留当前任务过程材料清理和交回判定 |
| `mmw/skills-src/mmw-start/resuming.md` | Modify | 完整重写恢复检查；全部落点通过 `mmw artifact path …` 解析；从仓库判断 spec 与 plan 状态 |
| `mmw/skills-src/mmw-implement/SKILL.md` | Modify | 只把下一步表中的 Wiki 归档和删除长期产物改为仓库保留语义；落点字面值留给 plan 07 |
| `mmw/skills-src/mmw-start/SKILL.md` | Modify | 只把「Wiki 写一次」改为一次收尾；其他落点与入口分区留给 plan 07 |
| `mmw/skills-pi/mmw-closing/SKILL.md` | Modify·物化 | 同步新的收尾流程 |
| `mmw/skills-claude-code/mmw-closing/SKILL.md`、`mmw/skills-codex/mmw-closing/SKILL.md` | Modify·物化 | 同步新的收尾流程 |
| `mmw/skills-claude-code/mmw-start/resuming.md`、`mmw/skills-codex/mmw-start/resuming.md` | Modify·物化 | 同步新的恢复检查 |
| `mmw/skills-pi/mmw-implement/SKILL.md`、`mmw/skills-claude-code/mmw-implement/SKILL.md`、`mmw/skills-codex/mmw-implement/SKILL.md` | Modify·物化 | 同步 `mmw-implement` 的仓库保留语义 |
| `mmw/skills-claude-code/mmw-start/SKILL.md`、`mmw/skills-codex/mmw-start/SKILL.md`、`mmw/prompts-pi/mmw-start.md` | Modify·物化 | 同步 `mmw-start` 的一次收尾语义与内联恢复检查 |

## Contracts and Seams

- **Test seam:** 使用真实 `mmw` 命令行接口。测试在一次性仓库中验证输出、退出码和文件副作用。来源：spec `Testing Decisions`。
- **Produces for plan 01:** `.mmw.json.paths` 的完整键集合固定为 `scratch`、`reviews`、`release`、`worktrees`。四个值由目标仓库配置。初始化迁移不得覆盖已有值。
- **Consumes from plan 01:** 恢复检查用 `mmw artifact path spec --name <工作名>` 取得仓库中的 spec 文件。收尾清理用 `mmw artifact path` 取得当前工作名下的 scratch 与审查记录位置。
- **Produces for plan 06:** `mmw init` 不再把 `.dispatch/` 加入 `.gitignore`。初始化测试证明忽略清单只含四个工作目录根和 `graphify-out/`。
- **Doctor report — historical paths:** 报告 `docs/evidence/`、`.dispatch/` 和 `docs/specs/<X>/<X>.md`。每行点名实际路径，并说明它已退役。
- **Doctor report — legacy config:** `.mmw.json.paths` 中的 `specs`、`plans`、`prototypes`、`research`、`evidence` 每出现一个就报告一行。顶层 `wiki` 出现时另报一行。每行点名键名，并说明它已退役。
- **Doctor exclusions:** 不报告 `docs/plans/` 或 `docs/research/` 的名字段取值。也不报告 scratch 根与 reviews 根内部的细分差异。
- **Exit-status seam:** 在其他诊断全部通过的受控仓库中，两组报告出现前后都返回 0。报告逻辑不得给 `status` 赋失败值。
- **Read-only seam:** `mmw doctor` 不修改 `.mmw.json`，也不移动、删除或创建历史产物。
- **Push-auth seam:** GitHub HTTPS 推送鉴权检查的命令、成功输出、`status=1` 失败行为和修复命令保持不变。失败提示只删除「（推 Wiki 要它）」。
- **Shared-skill seam:** plan 09 独占 `mmw-closing/SKILL.md` 与 `mmw-start/resuming.md`。plan 09 在 `mmw-implement/SKILL.md:135` 和 `mmw-start/SKILL.md:92` 只改 Wiki 语义；plan 07 继续拥有同文件中的落点字面值与入口分区。
- **Migration:** `mmw init` 删除五个旧路径键和顶层 `wiki`。历史产物只由用户人工处理，不提供迁移命令。

## Implementation

1. **先把配置与诊断合同写成失败测试**
   - Change: 为新仓库断言 `paths` 的精确四键集合，并断言顶层没有 `wiki`。为旧配置加入五个旧路径键与顶层 `wiki`，并给四个保留键设置非默认值。
   - Change: 运行 `mmw init` 后，断言六个遗留键消失，四个自定义值保持不变。
   - Change: 建立一个其他诊断全部通过的 `mmw doctor` 仓库。分别加入三类历史路径、五个旧路径配置键和顶层 `wiki`。
   - Change: 逐行断言报告。比较加入遗留项前后的退出码。加入不应报告的名字段与内部细分作为反例。
   - Change: 另建缺少 GitHub HTTPS 凭据的诊断状态。断言原有推送鉴权检查仍失败，只是提示不再含「推 Wiki 要它」。
   - Files: `mmw/cli/tests/test_init.sh`。
   - Verify: `bash mmw/cli/tests/test_init.sh` → 新增用例在当前实现上失败，既有初始化用例继续运行。

2. **收窄初始化输出与忽略清单**
   - Change: 从默认配置删除顶层 `wiki`。保持现有四键补齐和五个旧路径键删除逻辑。
   - Change: 把顶层 `wiki` 加入已有配置的迁移判据与删除集合。补齐测试暴露的精确集合或保值缺口。
   - Change: 从初始化忽略清单删除 `.dispatch/`。把真实 worktree 用例改为四个工作目录根中的过程材料。
   - Change: 不删除目标仓库中已经存在的 `.dispatch/`。它只由 `mmw doctor` 报告。
   - Files: `mmw/cli/mmw.default.json`、`mmw/cli/lib/init.sh`、`mmw/cli/tests/test_init.sh`。
   - Verify: `bash mmw/cli/tests/test_init.sh` → 新配置与迁移配置都只含四个 `paths` 键且没有顶层 `wiki`；忽略清单没有 `.dispatch/`。

3. **增加不改变退出码的两组只读报告**
   - Change: 在仓库和配置可读时执行两组检查。把报告与现有安装故障分开输出。
   - Change: 历史路径只检查三条已批准规则。旧 spec 只匹配父目录名与文件名相同的形状。
   - Change: 遗留配置逐键报告五个旧路径键和顶层 `wiki`。不要把报告结果写进 `status`。
   - Change: 保留 GitHub HTTPS 推送鉴权检查及其 `status=1` 行。只从失败提示删除「（推 Wiki 要它）」。
   - Files: `mmw/cli/mmw`、`mmw/cli/tests/test_init.sh`。
   - Verify: `bash mmw/cli/tests/test_init.sh` → 九项逐行出现；反例不出现；两组报告存在时退出码仍为 0；文件树不变；缺少推送凭据时仍非零退出。

4. **删除 Wiki 命令和专用测试**
   - Change: 删除 Wiki 实现与测试文件。删除 CLI 的 source 行、顶层用法行、`usage_wiki`、`cmd_wiki` 和顶层分发行。
   - Change: 测试入口只删除 Wiki 测试行。不要改 plan 01 或 plan 11 的入口行。
   - Files: `mmw/cli/lib/wiki.sh`、`mmw/cli/tests/test_wiki.sh`、`mmw/cli/mmw`、`mmw/test.sh`。
   - Verify: `bash -n mmw/cli/mmw && test ! -e mmw/cli/lib/wiki.sh && test ! -e mmw/cli/tests/test_wiki.sh` → CLI 语法通过，两份文件不存在。
   - Verify: `mmw/cli/mmw wiki >/dev/null 2>&1; test $? -ne 0` → 退役命令不再分发。

5. **把收尾与恢复流程切到仓库长期保存合同**
   - Change: 完整重写 `mmw-closing` 的目标、前置条件、流程和下一步表。删除 Wiki 初始化、写页、导航、人工推送、验证和删除本地文档六步。
   - Change: 唯一步骤清理当前工作名下的 scratch 与审查记录。每个目标都用 `mmw artifact path scratch --name <工作名> --sub <类别内细分>` 或 `mmw artifact path review --name <工作名> --sub <审查记录>` 解析。先列出目标并核实归属。不得删除别的任务内容。
   - Change: 删除界面验收证据的额外补偿路径。删除 `.dispatch/` 的额外清理分支。界面验收证据随当前任务 scratch 一起清理。
   - Change: 保留“这条分支就绪待集成”的判定点。用 `mmw artifact path spec --name <工作名>` 与逐份 `mmw artifact path plan --name <工作名> --sub <计划文件>` 取得长期产物位置，交回时明确它们仍在仓库。
   - Change: 完整重写恢复文件。spec、plan、scratch 与审查记录的每个检查都运行对应的完整 `mmw artifact path …` 命令，不保留旧路径字面值。
   - Change: 在 `mmw-implement/SKILL.md:135` 只把「归档到 Wiki、删除本地 spec 与 plan」改为「长期产物留在仓库、收尾只清理过程材料」。保留该行的落点字面值，交给 plan 07 改写。
   - Change: 在 `mmw-start/SKILL.md:92` 只把「Wiki 写一次」改为一次收尾。不要改该文件其他落点与入口分区。
   - Files: `mmw/skills-src/mmw-closing/SKILL.md`、`mmw/skills-src/mmw-start/resuming.md`、`mmw/skills-src/mmw-implement/SKILL.md`、`mmw/skills-src/mmw-start/SKILL.md`。
   - Verify: `bash mmw/cli/tests/test_skill_refs.sh` → 技能源不再引用已删除的 `mmw wiki` 命令，其他引用仍有效。
   - Verify: `! rg -n '归档到 Wiki|删掉本地的 .*docs/specs|Wiki 写一次' mmw/skills-src/mmw-implement/SKILL.md mmw/skills-src/mmw-start/SKILL.md` → 两处散文不再指示 Wiki 归档或删除长期产物。
   - Verify: `! rg -n 'docs/(specs|plans)/<|\.scratch/|\.reviews/' mmw/skills-src/mmw-closing/SKILL.md mmw/skills-src/mmw-start/resuming.md` → 两份整文件没有旧落点字面值。

6. **物化技能并执行完整交付关卡**
   - Change: 运行全宿主物化。只提交由四份技能源产生的对应差异，不手改技能产物。
   - Change: 检查共享文件分区。不得包含 plan 01、03、05、06、10 或 11 的改动。
   - Files: Change Map 中的技能产物、CLI、初始化和测试文件。
   - Verify: `mmw/cli/mmw skills materialize --host all --check` → Pi、Claude Code 与 Codex 技能产物无漂移。
   - Verify: `git diff --check` → 没有空白错误。
   - Verify: `bash mmw/test.sh` → 全部测试通过并退出 0。

## Acceptance

| Ticket 验收 | 证明方式 | 命令或人工结果 |
| --- | --- | --- |
| Wiki 命令面完整退役 | 两份文件不存在；CLI 不再载入、说明或分发 Wiki；旧命令失败 | `bash -n mmw/cli/mmw` 与文件存在性检查通过；`mmw/cli/mmw wiki` 非零退出 |
| 收尾只负责过程材料清理 | 完整读取技能源和三份物化产物；确认流程只有清理与交回；每个落点都由 `mmw artifact path …` 解析 | 技能源没有 Wiki、远端推送、删除 spec 与 plan 的步骤或旧落点字面值；物化检查通过 |
| 恢复流程从仓库读取长期文档 | 整份恢复文件通过 `mmw artifact path …` 检查 spec、plan、scratch 与审查记录 | `bash mmw/cli/tests/test_skill_refs.sh`、旧落点字面值反向检索与物化检查通过 |
| `mmw-implement` 与 `mmw-start` 不再留下 Wiki 语义 | 只核对两处分区；确认下一步不再删除长期产物，一次交付不再要求 Wiki 写入 | 两个精确散文片段的 `rg` 反向检查零命中；对应物化产物同步 |
| 目标仓库只配置四个工作目录根 | 首次初始化和旧配置迁移都断言精确键集合，并验证自定义值保留；默认配置与生成配置没有顶层 `wiki` | `bash mmw/cli/tests/test_init.sh` → 四键集合、顶层 `wiki` 删除与保值用例通过 |
| 界面验收证据不再有长期类别根补偿 | 完整读取收尾技能源；确认界面证据只随当前任务 scratch 清理 | 技能源和物化产物没有 `docs/evidence/` 补偿分支 |
| 三类历史路径都会被看见 | 一次性仓库分别建立旧证据目录、旧派发目录和旧 spec 文件 | `bash mmw/cli/tests/test_init.sh` → 三类报告逐项通过 |
| 五个旧路径配置分别提示 | 一次性配置同时放入五键，逐键断言报告 | `bash mmw/cli/tests/test_init.sh` → 五行报告都点名正确键 |
| 已有 `.mmw.json` 的顶层 `wiki` 不会成为残留 | 独立仓库验证 `mmw doctor` 先只读报告；再运行 `mmw init` 验证该键被删除 | `bash mmw/cli/tests/test_init.sh` → 报告点名 `wiki`，退出码不因报告改变，初始化后该键不存在 |
| 报告不把正常诊断变成失败 | 受控仓库先取得通过结果，再加入两组遗留项并比较退出码 | `bash mmw/cli/tests/test_init.sh` → 两次都退出 0，且文件树不变 |
| 推送鉴权仍是失败型诊断 | 在没有 GitHub HTTPS 凭据的受控环境运行 `mmw doctor`；比较输出与退出码 | `bash mmw/cli/tests/test_init.sh` → 仍非零退出，修复命令保留，提示不含「推 Wiki 要它」 |
| 报告边界没有扩大 | 放入旧 plan 与 research 名字段，以及 scratch 与 reviews 内部差异 | `bash mmw/cli/tests/test_init.sh` → 这些反例没有产生遗留报告 |
| Wiki 测试入口消失且完整回归通过 | 测试入口只少 Wiki 行；聚焦测试与完整测试都通过 | `bash mmw/cli/tests/test_init.sh && bash mmw/test.sh` → 退出码 0 |

## Browser Acceptance

不适用。

## Rollback and Gates

- Wiki 实现与测试的删除已经取得用户授权。实施时不再请求第二次确认。
- 删除内容和配置迁移都在 Git 中。回滚使用 revert，不恢复兼容入口。
- `mmw doctor` 不处理历史产物。用户根据报告决定是否移动或删除实际文件。
- `mmw init` 只迁移 `.mmw.json` 与初始化管理的忽略项。它不得顺带清理历史目录。
- 不执行 `git push`、远端合并、部署或正式发布。
