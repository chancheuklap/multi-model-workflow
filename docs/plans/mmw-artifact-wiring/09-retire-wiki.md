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
- `mmw/test.sh` 只删除 Wiki 测试入口。plan 01 与 plan 11 各自增加自己的测试入口。来源：spec `Cross-Plan Contract Anchors`。
- 当前 `AGENTS.md` 的提交检查段没有 Wiki 文案。本 plan 不修改该文件。若集成前该分区出现 Wiki 文案，只能删除该分区内的 Wiki 内容。
- 领域文档 leaf 与 `CONTEXT-MAP.md` 归 plan 10。本 plan 不删除「Wiki 页面」术语。来源：spec `Cross-Plan Contract Anchors`。
- 技能源中，本 plan 只改 `mmw-closing` 的退役流程，以及 `mmw-start/resuming.md` 的归档检查行。其他落点、工作名和入口分支改写归 plan 07。
- 修改技能源前，完整读取对应 `SKILL.md` 与链接的 reference。只改 `mmw/skills-src/`，再物化全部宿主产物。来源：`AGENTS.md:44-46,64-72`。
- 本 ticket 没有 prototype 资产，也没有 research。来源：ticket `#42`。

## Current State

- CLI 会载入 `lib/wiki.sh`。顶层用法、`usage_wiki`、`cmd_wiki` 和顶层分发公开 `ensure`、`nav`、`verify`。出处：`mmw/cli/mmw:32-33,46-68,168-177,455-464,720-735`。
- Wiki 实现维护工作副本、导航与删前验证。对应测试在本地 Git 仓库中覆盖导航和验证。出处：`mmw/cli/lib/wiki.sh:1-156`、`mmw/cli/tests/test_wiki.sh:1-112`。
- 完整测试入口仍运行 Wiki 测试。出处：`mmw/test.sh:24-29`。
- `mmw-closing` 仍把 Wiki 设为唯一事实来源。它前六步写 Wiki并删除仓库里的 spec 与 plan。第七步还含界面证据和派发目录的补偿清理。出处：`mmw/skills-src/mmw-closing/SKILL.md:8-108`。
- 恢复流程仍通过 Wiki 页面判断归档。出处：`mmw/skills-src/mmw-start/resuming.md:15-31`。
- 默认配置已经只含四个工作目录根键。初始化也已补齐四键，并删除五个旧路径键。现有测试没有锁定迁移后的精确键集合。出处：`mmw/cli/mmw.default.json:81-95`、`mmw/cli/lib/init.sh:22-81`、`mmw/cli/tests/test_init.sh:65-88`。
- 初始化仍把 `.dispatch/` 写入 `.gitignore`。它的真实 worktree 用例也依赖该目录被忽略。出处：`mmw/cli/lib/init.sh:174-201,238-242`、`mmw/cli/tests/test_init.sh:76-88,110-128`。
- `cmd_doctor` 用局部 `status` 累积诊断结果。它没有历史产物或遗留配置报告。它仍用 Wiki 推送凭据检查改变退出码。出处：`mmw/cli/mmw:552-604,716`。
- `test_init.sh` 当前没有运行 `mmw doctor`。spec 也把两组新报告的测试归到这份文件。出处：`mmw/cli/tests/test_init.sh:1-214`、spec `Testing Decisions`。
- 技能物化器从 `mmw/skills-src/` 生成 Pi、Claude Code 和 Codex 产物。Pi 的用户入口另生成到 `mmw/prompts-pi/`。出处：`mmw/cli/lib/materialize_skills.py:20-27,311-392`。

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `mmw/cli/lib/wiki.sh` | Delete | 删除 Wiki 工作副本、导航和验证实现 |
| `mmw/cli/tests/test_wiki.sh` | Delete | 删除三个退役子命令的专用测试 |
| `mmw/cli/mmw` | Modify | 删除 Wiki 载入、用法、命令函数和顶层分发；删除 Wiki 推送鉴权诊断；增加两组只读报告 |
| `mmw/test.sh` | Modify | 只删除运行 `test_wiki.sh` 的一行 |
| `mmw/cli/lib/init.sh` | Modify | 保持四键配置迁移；删除 `.dispatch/` 忽略项；更新同段注释和初始化报告 |
| `mmw/cli/tests/test_init.sh` | Test | 锁定四键迁移、五项忽略清单、两组诊断报告、排除项和退出码 |
| `mmw/skills-src/mmw-closing/SKILL.md` | Modify | 删除 Wiki 与本地文档删除流程；只保留当前任务过程材料清理和交回判定 |
| `mmw/skills-src/mmw-start/resuming.md` | Modify | 把归档检查改为检查仓库中的 spec 路径 |
| `mmw/skills-pi/mmw-closing/SKILL.md` | Modify·物化 | 同步新的收尾流程 |
| `mmw/skills-claude-code/mmw-closing/SKILL.md`、`mmw/skills-codex/mmw-closing/SKILL.md` | Modify·物化 | 同步新的收尾流程 |
| `mmw/skills-claude-code/mmw-start/resuming.md`、`mmw/skills-codex/mmw-start/resuming.md` | Modify·物化 | 同步新的恢复检查 |
| `mmw/prompts-pi/mmw-start.md` | Modify·物化 | 同步内联后的 Pi 恢复检查 |

## Contracts and Seams

- **Test seam:** 使用真实 `mmw` 命令行接口。测试在一次性仓库中验证输出、退出码和文件副作用。来源：spec `Testing Decisions`。
- **Produces for plan 01:** `.mmw.json.paths` 的完整键集合固定为 `scratch`、`reviews`、`release`、`worktrees`。四个值由目标仓库配置。初始化迁移不得覆盖已有值。
- **Consumes from plan 01:** 恢复检查用 `mmw artifact path spec --name <工作名>` 取得仓库中的 spec 文件。收尾清理用 `mmw artifact path` 取得当前工作名下的 scratch 与审查记录位置。
- **Produces for plan 06:** `mmw init` 不再把 `.dispatch/` 加入 `.gitignore`。初始化测试证明忽略清单只含四个工作目录根和 `graphify-out/`。
- **Doctor report — historical paths:** 报告 `docs/evidence/`、`.dispatch/` 和 `docs/specs/<X>/<X>.md`。每行点名实际路径，并说明它已退役。
- **Doctor report — legacy config:** `.mmw.json.paths` 中的 `specs`、`plans`、`prototypes`、`research`、`evidence` 每出现一个就报告一行。每行点名键名，并说明它已退役。
- **Doctor exclusions:** 不报告 `docs/plans/` 或 `docs/research/` 的名字段取值。也不报告 scratch 根与 reviews 根内部的细分差异。
- **Exit-status seam:** 在其他诊断全部通过的受控仓库中，两组报告出现前后都返回 0。报告逻辑不得给 `status` 赋失败值。
- **Read-only seam:** `mmw doctor` 不修改 `.mmw.json`，也不移动、删除或创建历史产物。
- **Migration:** `mmw init` 删除五个旧路径键。历史产物只由用户人工处理，不提供迁移命令。

## Implementation

1. **先把配置与诊断合同写成失败测试**
   - Change: 为新仓库断言 `paths` 的精确四键集合。为旧配置加入五个旧键，并给四个保留键设置非默认值。
   - Change: 运行 `mmw init` 后，断言旧键消失，四个自定义值保持不变。
   - Change: 建立一个其他诊断全部通过的 `mmw doctor` 仓库。分别加入三类历史路径和五个旧配置键。
   - Change: 逐行断言报告。比较加入遗留项前后的退出码。加入不应报告的名字段与内部细分作为反例。
   - Files: `mmw/cli/tests/test_init.sh`。
   - Verify: `bash mmw/cli/tests/test_init.sh` → 新增用例在当前实现上失败，既有初始化用例继续运行。

2. **收窄初始化输出与忽略清单**
   - Change: 保持现有四键补齐和五键删除逻辑。补齐测试暴露的精确集合或保值缺口。
   - Change: 从初始化忽略清单删除 `.dispatch/`。把真实 worktree 用例改为四个工作目录根中的过程材料。
   - Change: 不删除目标仓库中已经存在的 `.dispatch/`。它只由 `mmw doctor` 报告。
   - Files: `mmw/cli/lib/init.sh`、`mmw/cli/tests/test_init.sh`。
   - Verify: `bash mmw/cli/tests/test_init.sh` → 新配置与迁移配置都只含四键；忽略清单没有 `.dispatch/`。

3. **增加不改变退出码的两组只读报告**
   - Change: 在仓库和配置可读时执行两组检查。把报告与现有安装故障分开输出。
   - Change: 历史路径只检查三条已批准规则。旧 spec 只匹配父目录名与文件名相同的形状。
   - Change: 遗留配置逐键报告五项。不要把报告结果写进 `status`。
   - Change: 删除只为 Wiki 推送服务的 GitHub HTTPS 凭据检查。
   - Files: `mmw/cli/mmw`、`mmw/cli/tests/test_init.sh`。
   - Verify: `bash mmw/cli/tests/test_init.sh` → 八项逐行出现；反例不出现；两组报告存在时退出码仍为 0；文件树不变。

4. **删除 Wiki 命令和专用测试**
   - Change: 删除 Wiki 实现与测试文件。删除 CLI 的 source 行、顶层用法行、`usage_wiki`、`cmd_wiki` 和顶层分发行。
   - Change: 测试入口只删除 Wiki 测试行。不要改 plan 01 或 plan 11 的入口行。
   - Files: `mmw/cli/lib/wiki.sh`、`mmw/cli/tests/test_wiki.sh`、`mmw/cli/mmw`、`mmw/test.sh`。
   - Verify: `bash -n mmw/cli/mmw && test ! -e mmw/cli/lib/wiki.sh && test ! -e mmw/cli/tests/test_wiki.sh` → CLI 语法通过，两份文件不存在。
   - Verify: `mmw/cli/mmw wiki >/dev/null 2>&1; test $? -ne 0` → 退役命令不再分发。

5. **把收尾与恢复流程切到仓库长期保存合同**
   - Change: 完整重写 `mmw-closing` 的目标、前置条件、流程和下一步表。删除 Wiki 初始化、写页、导航、人工推送、验证和删除本地文档六步。
   - Change: 唯一步骤清理当前工作名下的 scratch 与审查记录。先列出目标并核实归属。不得删除别的任务内容。
   - Change: 删除界面验收证据的额外补偿路径。删除 `.dispatch/` 的额外清理分支。界面验收证据随当前任务 scratch 一起清理。
   - Change: 保留“这条分支就绪待集成”的判定点。交回信息改为仓库中的 spec 与 plan，不再报告 Wiki 页面。
   - Change: 把恢复表的归档检查改成解析并检查仓库中的 spec 文件。只改这一行，不改 plan 07 拥有的其他落点与工作名段落。
   - Files: `mmw/skills-src/mmw-closing/SKILL.md`、`mmw/skills-src/mmw-start/resuming.md`。
   - Verify: `bash mmw/cli/tests/test_skill_refs.sh` → 技能源不再引用已删除的 `mmw wiki` 命令，其他引用仍有效。

6. **物化技能并执行完整交付关卡**
   - Change: 运行全宿主物化。只提交由两份技能源产生的对应差异，不手改技能产物。
   - Change: 检查共享文件分区。不得包含 plan 01、03、05、06、10 或 11 的改动。
   - Files: Change Map 中的技能产物、CLI、初始化和测试文件。
   - Verify: `mmw/cli/mmw skills materialize --host all --check` → Pi、Claude Code 与 Codex 技能产物无漂移。
   - Verify: `git diff --check` → 没有空白错误。
   - Verify: `bash mmw/test.sh` → 全部测试通过并退出 0。

## Acceptance

| Ticket 验收 | 证明方式 | 命令或人工结果 |
| --- | --- | --- |
| Wiki 命令面完整退役 | 两份文件不存在；CLI 不再载入、说明或分发 Wiki；旧命令失败 | `bash -n mmw/cli/mmw` 与文件存在性检查通过；`mmw/cli/mmw wiki` 非零退出 |
| 收尾只负责过程材料清理 | 完整读取技能源和三份物化产物；确认流程只有清理与交回 | 技能源没有 Wiki、远端推送或删除 spec 与 plan 的步骤；物化检查通过 |
| 恢复流程从仓库读取长期文档 | 恢复表通过 `mmw artifact path spec` 检查当前工作名的 spec | `bash mmw/cli/tests/test_skill_refs.sh` 与物化检查通过 |
| 目标仓库只配置四个工作目录根 | 首次初始化和旧配置迁移都断言精确键集合，并验证自定义值保留 | `bash mmw/cli/tests/test_init.sh` → 四键集合与保值用例通过 |
| 界面验收证据不再有长期类别根补偿 | 完整读取收尾技能源；确认界面证据只随当前任务 scratch 清理 | 技能源和物化产物没有 `docs/evidence/` 补偿分支 |
| 三类历史路径都会被看见 | 一次性仓库分别建立旧证据目录、旧派发目录和旧 spec 文件 | `bash mmw/cli/tests/test_init.sh` → 三类报告逐项通过 |
| 五个旧路径配置分别提示 | 一次性配置同时放入五键，逐键断言报告 | `bash mmw/cli/tests/test_init.sh` → 五行报告都点名正确键 |
| 报告不把正常诊断变成失败 | 受控仓库先取得通过结果，再加入两组遗留项并比较退出码 | `bash mmw/cli/tests/test_init.sh` → 两次都退出 0，且文件树不变 |
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
