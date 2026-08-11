---
ticket: 47
artifact_refs:
  - category: research
    name: mmw-artifact-wiring
    issue: 20
    sub: aidlc-v2-artifact-wiring
---

# Plan: 落点字面值的机械校验

**Goal:** 技能源重新写入受禁的落点字面值时，独立测试失败并报告文件与行号；类别名参数也必须来自产物落点数据。
**Source spec:** `docs/specs/mmw-artifact-wiring/mmw-artifact-wiring.md`
**Source ticket:** GitHub issue `#47`
**Research source:** `docs/research/mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/README.md`；精确文件是同目录 `report.md` 第 11 节

## Constraints

- 本 ticket 只校技能源 Markdown 文本。第一条规则匹配固定类别根后紧跟一个 `<…>` 占位符段。第二条规则匹配工作目录根的默认取值，不要求后面有占位符。来源：spec Testing Decisions、ADR `0009`。
- 固定类别根不带占位符地单独出现时必须通过。这是有意保留的洞。不得用豁免清单改造成零例外。来源：ticket `#47`、spec Testing Decisions、ADR `0009`。
- 固定类别根清单从 `mmw/cli/artifacts.json` 的 `active`、`fixed` 记录解析。工作目录根默认值从 `active`、`workdir` 记录的 `root` 键映射到 `mmw/cli/mmw.default.json.paths`。测试不得手抄第二份清单。来源：spec 第 2 节、Testing Decisions、Contract Boundaries。
- `context-map` 记录的 `root` 固定取空字符串 `""`。解析固定类别根时必须跳过空 `root`。仓库根不形成可扫描的目录前缀。来源：spec 第 2 节的 `context-map` 记录。
- 扫描范围是 `mmw/skills-src/**/*.md`。排除 `mmw/skills-src/mmw-setup/` 与 `mmw/skills-src/mmw-triage/examples.md`。前者是旧背景材料，后者是上游材料。两处都不由 MMW 的产物落点合同拥有。来源：spec Testing Decisions、Out of Scope。
- 两处扫描范围排除必须写死在 `test_skill_paths.sh`。它们不接受配置项，也不随命中数量增删。该边界按文件来源确定，不是按命中内容建立豁免。来源：spec Testing Decisions。
- 新校验必须独立放在 `test_skill_paths.sh`。不得并入 `test_skill_refs.sh`。前者守住落点命令边界，后者守住引用完整性。来源：spec Testing Decisions、ADR `0009`。
- 类别名参数校验只延伸 `test_skill_refs.sh` 的命令引用检查。类别名集合读取 `artifacts.json` 顶层键。来源：ticket `#47`、spec Testing Decisions。
- 不校产物质量、方法选择、完成度、字面值数量、目标仓库的实际产物，或反向相关性。除两处文件来源边界外，不得增加计数阈值或按命中内容建立豁免清单。来源：spec Testing Decisions、ADR `0009`。
- 01 提供 `artifacts.json`。07 与 08 提供改写后的技能源。本 plan 在这三项进入任务分支后实施。两条路径规则必须在 07 与 08 的最终技能源上通过。来源：spec Cross-Plan Contract Anchors、ticket `#47`。
- 本 plan 独占 `test_skill_refs.sh`。`mmw/test.sh` 只增加落点字面值测试的一行。不得改动其他 plan 拥有的测试入口行。来源：spec Cross-Plan Contract Anchors。
- research 范围是 `awslabs/aidlc-workflows` 的 `v2` 分支，访问日期是 2026-08-11。范围快照只有短 SHA `2ce654d` 和 README 版本 `2.5.62`。完整 SHA 未固定。
- research 第 11 节的五项只用于边界对照。本 ticket 对应其源文本正则校验形态，但校验内容不同。引用完整性留在 `test_skill_refs.sh`。sensor、完成度和全局运行时落点门禁不进入本 ticket。

## Current State

- `mmw/cli/tests/test_skill_refs.sh:31-41` 已取得技能源目录、CLI 目录和技能名集合。`mmw/cli/tests/test_skill_refs.sh:70-72` 已扫描 Markdown，并排除 `mmw-setup`。
- `mmw/cli/tests/test_skill_refs.sh:94-105` 只验证 `mmw` 顶层命令与子命令。它还不验证 `mmw artifact path` 后面的类别名参数。
- `mmw/cli/tests/test_skill_refs.sh:140-144` 已按文件与行号汇总失败，并用退出码表达结果。新增类别名错误沿用这条报告形态。
- `mmw/skills-src/mmw-triage/examples.md:54` 写着 `` `.out-of-scope/<概念>.md` ``。它会命中规则一。spec Out of Scope 与 plan 07 都要求保持这份上游材料不变；plan 07 的审计命令也精确排除该文件。
- `mmw/cli/mmw.default.json:81-85` 保存 `scratch`、`reviews`、`release` 和 `worktrees` 的默认值。路径校验只消费产物落点数据标成 `workdir` 的键。
- `mmw/test.sh:15-22` 用 `run` 汇总各份测试的退出码。`mmw/test.sh:24-33` 逐行登记现有测试，其中第 29 行登记查引用测试。
- 当前 checkout 的 `mmw/cli/artifacts.json` 还未建立。01 号 plan 负责建立该文件。`test_skill_paths.sh` 也需要由本 plan 新建。

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `mmw/cli/tests/test_skill_paths.sh` | Create | 从两份权威数据解析字面值，并执行两条技能源文本规则 |
| `mmw/cli/tests/test_skill_refs.sh` | Modify | 验证 `mmw artifact path` 的类别名参数存在于产物落点数据 |
| `mmw/test.sh` | Modify | 只增加运行 `test_skill_paths.sh` 的一行 |

## Contracts and Seams

- **Test seam:** 使用 spec 已确认的技能源 Markdown 文本 seam。测试观察每一行是否命中两条正则规则，并观察标准输出、标准错误和退出码。
- **Consumes — 01 → 11:** `mmw/cli/artifacts.json` 顶层是按类别名取值的对象。记录提供 `root`、`root_kind` 和 `status`。本 plan 只读取这些字段，不改变产物落点数据。
- **Consumes — model profile → 11:** `mmw/cli/mmw.default.json.paths` 提供工作目录根的默认取值。`artifacts.json` 的 `workdir` 记录决定实际读取哪些键。
- **Consumes — 07、08 → 11:** 两份 plan 交付改写后的 `mmw/skills-src/`。本 plan 在两处文件来源边界外扫描它们的合并结果。它不修改技能源，也不增加按命中内容建立的豁免。
- **Ownership:** 本 plan 独占 `test_skill_refs.sh` 的类别名参数检查。它新建 `test_skill_paths.sh`，并只占 `mmw/test.sh` 中新增落点字面值测试的一行。

## Implementation

1. **两条规则先在一次性测试目录中固定**
   - Change: 新建 `test_skill_paths.sh`。让内嵌检查逻辑接收技能源目录、产物落点数据和模型档。
   - Change: 从 `artifacts.json` 解析固定类别根。对目录根统一末尾斜杠，再安全转义成正则。固定类别根记录的 `root` 是空字符串时跳过该记录。
   - Change: 从 `workdir` 记录取得模型档键，再从 `mmw.default.json.paths` 解析默认取值。缺键、空值或数据形状错误必须非零退出。
   - Change: 建立一次性测试目录。证明固定类别根紧跟占位符会失败，并报告测试文件与行号。
   - Change: 证明工作目录根默认值单独出现和后接占位符都会失败。证明固定类别根单独出现会通过。
   - Change: 在一次性产物落点数据中加入 `context-map` 的空 `root`。证明它不会把任意占位符误判为规则一命中。
   - Change: 在一次性测试目录的 `mmw-setup` 与 `mmw-triage/examples.md` 放入同类错误。证明两处文件来源边界被排除。另在 `mmw-triage/SKILL.md` 放入错误，证明排除没有扩大到整个技能目录。
   - Change: 两处排除直接写在测试逻辑中。不要增加配置键，也不要根据命中内容改变扫描范围。
   - Files: `mmw/cli/tests/test_skill_paths.sh`。
   - Verify: `bash mmw/cli/tests/test_skill_paths.sh` → 内部正反例全部符合预期，随后当前技能源扫描通过。

2. **在 07 与 08 的最终技能源上执行真实扫描**
   - Change: 按文件名排序扫描 `mmw/skills-src/` 下全部 Markdown。按路径段排除 `mmw-setup`，并精确排除 `mmw-triage/examples.md`。
   - Change: 规则一只在固定类别根与占位符段直接相连时命中。固定类别根的其他单独出现保持通过。
   - Change: 规则二在工作目录根默认值完整出现时命中。它不查看后续字符是否为占位符。
   - Change: 汇总全部命中。每条输出仓库相对文件、行号和命中的规则。任意命中都非零退出。
   - Files: `mmw/cli/tests/test_skill_paths.sh`。
   - Verify: `bash mmw/cli/tests/test_skill_paths.sh` → 07 与 08 的最终技能源没有违规字面值，退出码为 0。

3. **把类别名参数加入现有引用校验**
   - Change: 在 `test_skill_refs.sh` 读取 `artifacts.json` 顶层键，不建立类别名常量集合。
   - Change: 扫描技能源里的 `mmw artifact path <类别名>` 调用。每个字面类别名必须存在于数据顶层键。
   - Change: 未知类别沿用现有失败汇总，报告技能源文件、行号和错误类别名。通用占位符命令不当成字面类别名。
   - Files: `mmw/cli/tests/test_skill_refs.sh`。
   - Verify: `bash mmw/cli/tests/test_skill_refs.sh` → 技能、文件、步骤、命令、角色技能和类别名引用全部通过。

4. **新校验进入唯一测试入口**
   - Change: 在 `mmw/test.sh` 增加一行落点字面值测试。保留其他测试行的正文和顺序。
   - Files: `mmw/test.sh`。
   - Verify: `bash mmw/cli/tests/test_skill_paths.sh` → 独立校验退出码为 0。
   - Verify: `bash mmw/cli/tests/test_skill_refs.sh` → 延伸后的引用校验退出码为 0。
   - Verify: `bash mmw/test.sh` → 完整测试套件退出码为 0。
   - Verify: `git diff --check` → 没有空白错误。

## Acceptance

| Ticket 验收 | 证明方式 | 命令或人工结果 |
| --- | --- | --- |
| 落点字面值校验保持独立 | 新脚本承载两条路径规则；查引用测试只增加类别名检查 | `test -f mmw/cli/tests/test_skill_paths.sh && bash mmw/cli/tests/test_skill_paths.sh` → 文件存在且退出 0 |
| 固定类别根后紧跟占位符时失败，并指出位置 | 一次性测试目录放入一条违规行，断言非零退出和 `文件:行号` | `bash mmw/cli/tests/test_skill_paths.sh` → 规则一反例断言通过 |
| 工作目录根默认值出现即失败 | 分别覆盖默认值单独出现和后接占位符，断言两项都失败 | `bash mmw/cli/tests/test_skill_paths.sh` → 规则二两项反例断言通过 |
| 固定类别根单独出现时通过 | 一次性测试目录只放不带占位符的固定类别根 | `bash mmw/cli/tests/test_skill_paths.sh` → 已知洞正例断言通过 |
| 两份字面值清单没有手抄副本 | 测试从 `artifacts.json` 的记录映射到 `mmw.default.json.paths`，并用一次性数据验证解析结果 | `bash mmw/cli/tests/test_skill_paths.sh` → 数据驱动用例通过 |
| `context-map` 的空 `root` 不形成正则前缀 | 一次性数据包含 `root: ""`，并用任意占位符行证明它不会产生规则一命中 | `bash mmw/cli/tests/test_skill_paths.sh` → 空类别根用例通过，其他固定类别根反例仍失败 |
| 两处非 MMW 拥有的来源不进入扫描 | `mmw-setup` 与 `mmw-triage/examples.md` 下的违规文件不产生失败；`mmw-triage/SKILL.md` 的违规文件仍失败 | `bash mmw/cli/tests/test_skill_paths.sh` → 两处固定范围排除用例通过，排除未扩大 |
| 两处扫描范围排除不是可配置豁免 | 测试逻辑固定两条相对路径边界，不读取配置，也不根据命中内容增删 | `bash mmw/cli/tests/test_skill_paths.sh` → 固定扫描范围用例通过 |
| 技能源类别名参数都能在产物落点数据中找到 | 查引用测试从数据顶层键验证每个 `mmw artifact path` 类别名 | `bash mmw/cli/tests/test_skill_refs.sh` → 类别名检查通过 |
| 新校验进入完整测试入口，且 07 与 08 的技能源全绿 | 先跑两份聚焦测试，再跑仓库统一入口 | `bash mmw/cli/tests/test_skill_paths.sh && bash mmw/cli/tests/test_skill_refs.sh && bash mmw/test.sh` → 全部退出 0 |

## Browser Acceptance

不适用。
