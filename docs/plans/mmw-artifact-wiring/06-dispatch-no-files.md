---
ticket: 39
artifact_refs: []
---

# Plan: mmw dispatch 接口变更与角色报告不落盘

**Goal:** `mmw dispatch` 直接接收四栏 task 正文。各宿主 adapter 收到相同正文。角色报告只走标准输出。算得出日志落点时，失败只保留符合路径形状的派发进度日志。算不出时不写日志，派发照常进行。
**Source spec:** `docs/specs/mmw-artifact-wiring/spec.md`
**Source ticket:** `#39`

## Constraints

- 四栏 task 与角色报告不落盘。算得出日志落点时，派发失败保留派发进度日志。来源：spec 第 5、17 节、ADR `0004-no-dispatch-files.md:1-16`。
- 这是破坏性接口变更。删除 `--task <文件>`，不保留兼容入口。CLI、adapter、全部派发动作块和技能产物必须同批交付。来源：spec `Contract Boundaries` 与 `Release Risk`。
- 本 plan 只改 CLI 主入口中的 `dispatch` 用法和参数解析分区。不得重排其他子命令。来源：spec `Cross-Plan Contract Anchors`。
- 宿主 adapter 与派发护栏由本 plan 独占。技能源只允许改派发动作块。不得改落点字面值、取名规则或入口分支。来源：spec `Cross-Plan Contract Anchors`。
- 不改 wayfinder 技能源的交接表、ticket 模板、认领步骤或 map 正文标题。它们归 plan 08。来源：spec `Cross-Plan Contract Anchors`。
- 不改 `mmw/cli/lib/init.sh` 或 `mmw/cli/tests/test_init.sh`。初始化删除 `.dispatch/` 归 plan 09。本 plan 只消费该结果。
- ticket `#39` 被 `#37` 阻塞。plan 01 先提供 `mmw artifact path`，本 plan 才能实现和验收派发进度日志落点。来源：ticket `#39` 的 blocking edge、spec `Cross-Plan Contract Anchors`。
- ticket `#39` 被 `#40` 阻塞。plan 02 先提供工作名参数、继承规则和任务状态字段，本 plan 才能传递工作名并验收日志落点。来源：ticket `#39` 的 blocking edge、spec 第 5 节与 `Cross-Plan Contract Anchors`。
- ticket `#39` 被 `#42` 阻塞。plan 09 先交付初始化后的五项忽略清单，本 plan 才能执行对应验收。来源：ticket `#39` 的 blocking edge、spec `Cross-Plan Contract Anchors`。
- Codex App 后台 Worktree 任务没有可读父工作名。启动块必须把主 agent 当前工作的工作名写进 task，并让后台 agent 显式传给 `mmw task bind --name`。来源：spec 第 5 节；plan 02 `Task parameters` 与 `Inheritance`。
- 不改 `mmw/skill-rebuilds/candidate/`。候选区当前不参与物化或运行。来源：`mmw/skill-rebuilds/README.md:10-14,29-33`。
- 不为派发失败保留 task 文件。后台输出截断也不通过新文件兜底。来源：ADR `0004-no-dispatch-files.md:15-16`。

## Current State

- `usage_dispatch` 只公开 `--task <文件>`。`cmd_dispatch` 要求文件存在，并把绝对路径导出为 `MMW_D_TASK`。随后它加载宿主 adapter。出处：`mmw/cli/mmw:71-89,250-272,286-311`。
- Claude Code 的 claude 路径用 `jq --rawfile` 读取 task。gpt 路径把同一文件路径交给后台命令。出处：`mmw/cli/adapters/claude-code.sh:60-82`。
- Claude Code 的 gpt 执行路径创建 `.dispatch/`。报告和日志名称都取自 task 文件基名。`codex exec -o` 额外写角色报告。出处：`mmw/cli/adapters/claude-code.sh:85-97,129-161`。
- Claude Code 的 gpt 执行路径在读不到 scratch 根时回退到 `.scratch`。这会在主检出没有工作名时猜一个日志落点。出处：`mmw/cli/adapters/claude-code.sh:85-94`；spec 第 5 节。
- Pi adapter 也用 `jq --rawfile` 读取 task 文件。出处：`mmw/cli/adapters/pi.sh:22-35`。
- 技能物化器让 Claude Code 先写 task 文件，再调用 `mmw dispatch --task`。单角色与审查启动组都复用这段展开。出处：`mmw/cli/lib/materialize_skills.py:76-90,128-184`。
- 技能物化器生成的 Codex App 后台启动块只把结果分支名、目标原文和基点 SHA 交给 `mmw task bind`。命令没有 `--name`。出处：`mmw/cli/lib/materialize_skills.py:108-125`。
- `mmw dispatch` 没有收到 `--cwd` 时使用当前检出。六处 `none` 动作块会这样派只读角色；主检出的任务状态是 `local`，无法解析日志落点。出处：`mmw/cli/mmw:275-284`；spec 第 5 节。
- 物化器从全部技能源展开动作块，并逐文件比较技能产物。出处：`mmw/cli/lib/materialize_skills.py:311-364`。
- 当前派发护栏以 task 文件调用 CLI。它覆盖缺少 `--cwd`、非 Git 工作树、主检出和脏任务 worktree。出处：`mmw/cli/tests/guardrails.sh:304-330`。
- 初始化仍把 `.dispatch/` 写入忽略清单。该分区归 plan 09。出处：`mmw/cli/lib/init.sh:174-188`、`mmw/cli/tests/test_init.sh:76-88`。

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `mmw/cli/mmw` | Modify | 只改 `dispatch` 用法和参数解析。接收标准输入或 `--task-text`，并把正文交给 adapter。 |
| `mmw/cli/adapters/claude-code.sh` | Modify | 让两条模型路径消费正文。删除角色报告文件。按路径命令结果决定是否写派发进度日志，并删除 `.scratch` 回退。 |
| `mmw/cli/adapters/pi.sh` | Modify | 用正文构造原生 `subagent` 参数，不再读取 task 文件。 |
| `mmw/cli/lib/materialize_skills.py` | Modify | 改 Claude Code 派发动作块。修 Codex App 后台启动块的工作名传递与显式绑定。 |
| `mmw/cli/tests/guardrails.sh` | Test | 覆盖两种正文入口、逐字传递、报告标准输出、日志落点成功与失败、既有拒绝语义。 |
| `mmw/cli/tests/test_materialize_skills.py` | Test | 覆盖各工作目录模式、审查启动组和三个 Codex App 后台角色的工作名传递。 |
| `mmw/skills-claude-code/` | Modify（物化） | 保存从技能源重新物化的 Claude Code 派发动作块。 |
| `mmw/skills-codex/` | Modify（物化） | 保存 Codex App 后台启动块的新工作名传递与显式绑定命令。 |
| `mmw/skills-pi/`、`mmw/prompts-pi/` | Test（物化检查） | 确认同次全宿主物化没有漂移或遗留标记。 |

## Contracts and Seams

- **Test seam:** 使用真实 `mmw` CLI。验证 task 正文完整传递、既有护栏、标准输出和文件副作用。技能动作用物化后的 Markdown 文本验证。来源：spec `Testing Decisions`。
- **Produces — task 接口:** 支持标准输入与 `--task-text <正文>` 两种入口。一次调用只能选一种。旧 `--task <文件>` 必须当场拒绝。
- **Produces — adapter 输入:** CLI 向 adapter 传一个正文值，不再传路径。正文必须保留换行、空行、引号、反斜线、反引号和结尾换行。
- **Produces — scope 输入:** `mmw dispatch` 使用可选的 `--issue <编号>` 承载范围段。它只用于派发进度日志。动作块在 decision ticket 范围内传入该编号。
- **Produces — adapter 输出:** `mode`、`tool` 和 `params` 的宿主工具合同保留。删除 `task-file` 与 `report` 路径。gpt 角色的报告正文继续走标准输出。
- **Produces — Codex App 工作名传递:** 主 agent 在当前任务 worktree 运行 `mmw task state`，取 `bound` 行第四字段。主 agent 把该工作名连同四栏 task、完整结果分支名和基点 SHA 交给 Codex App 后台 Worktree 任务。后台 agent 先运行 `mmw task bind <完整结果分支名> <目标栏原文> --name <工作名> --from <基点 SHA>`。
- **Consumes — plan 01:** 使用 `mmw artifact path scratch [--name <工作名>] [--issue <编号>] --sub dispatch --absolute` 取得日志目录。不得在 adapter 内重写路径形状或回退到 `.scratch`。
- **Consumes — plan 02:** `mmw task state` 的 `bound` 行第四字段是工作名。adapter 在 `MMW_D_CWD` 对应的 worktree 中解析日志路径。Codex App 后台 Worktree 任务没有可读父工作名，因此启动块必须显式传 `--name`。
- **日志落点失败:** `mmw artifact path` 算不出日志落点时，adapter 不写日志，也不猜路径。它在标准错误写“派发进度日志算不出落点时不写日志，派发照常进行”。来源：spec 第 5 节。
- **Consumes — plan 09:** `mmw init` 不再写入 `.dispatch/`。`test_init.sh` 证明忽略清单只保留五项。plan 06 不修改这两个文件。
- **Migration:** 不提供双接口或迁移命令。CLI、动作块与技能产物在一个结果分支中一次切换。

## Implementation

1. **把新接口写成失败的外部行为测试**
   - Change: 改写五处文件式派发用例。增加标准输入和 `--task-text` 用例。加入含特殊字符与结尾换行的多行正文。
   - Change: 使用测试用宿主输出或假 `codex` 进程检查 `params`、标准输出和磁盘副作用。不要调用 adapter 私有函数。
   - Change: 从主检出派一个不带 `--cwd` 的只读角色。让日志路径解析失败，断言标准错误有明确说明、派发仍执行并且没有回退日志目录。
   - Files: `mmw/cli/tests/guardrails.sh`。
   - Verify: `bash mmw/cli/tests/guardrails.sh` → 新接口用例在旧实现上失败；既有拒绝用例继续运行。

2. **一次切换 CLI 与全部宿主 adapter**
   - Change: 删除 task 文件检查和路径规范化。读取唯一正文来源，并通过明确的正文变量交给 adapter。
   - Change: Claude Code 的 claude 路径改用 `jq --arg`。gpt 的后台命令安全携带多行正文和可选 issue 编号。
   - Change: gpt 执行路径删除 `.dispatch/`、`-o` 和 `report:`。算得出落点时，`codex` 进度的标准错误仍只进入派发进度日志。
   - Change: 日志目录通过 `mmw artifact path` 取得。文件名改为 `<角色>-<时间戳>.log`。成功时删除日志，派发失败时保留并输出路径。
   - Change: 删除 `.scratch` 回退。路径命令失败时写 spec 规定的标准错误说明，不建日志目录，继续执行派发。
   - Change: Pi adapter 改用正文值生成 `params.task`。
   - Files: `mmw/cli/mmw`、`mmw/cli/adapters/claude-code.sh`、`mmw/cli/adapters/pi.sh`。
   - Verify: `bash mmw/cli/tests/guardrails.sh` → 两种正文入口通过；多行正文一致；既有护栏仍拒绝；没有 task 或角色报告文件。

3. **同步全部派发动作块和技能产物**
   - Change: 改单角色与审查启动组的 Claude Code 展开。动作块直接把四栏 task 正文交给新接口。
   - Change: 改 Codex App 的 `worktree` 启动块。主 agent 先读取当前工作名，再把它放入后台 task；后台绑定命令显式传 `--name <工作名>`。
   - Change: 扩展物化测试，覆盖 `worktree`、`current`、`none` 和审查启动组。三个后台角色都必须生成工作名传递和显式绑定命令。Claude Code 产物不再要求 task 文件，也不再出现旧参数。
   - Change: 运行全宿主物化。不要手改 `mmw/skills-claude-code/` 或其他技能产物。
   - Files: `mmw/cli/lib/materialize_skills.py`、`mmw/cli/tests/test_materialize_skills.py`、全部技能产物目录。
   - Verify: `uv run --quiet --with pytest python -m pytest mmw/cli/tests/test_materialize_skills.py -q` → 全部物化行为通过。
   - Verify: `mmw/cli/mmw skills materialize --host all --check` → 三个宿主与 Pi 用户命令均无漂移。

4. **执行跨 plan 与整仓交付关卡**
   - Change: 不修改 plan 09 的文件。确认集成结果已删除初始化中的 `.dispatch/` 条目。
   - Files: 只读 `mmw/cli/lib/init.sh`、`mmw/cli/tests/test_init.sh`。
   - Verify: `bash mmw/cli/tests/test_init.sh` → 新仓库的忽略清单不含 `.dispatch/`，其余初始化行为通过。
   - Verify: `git diff --check` → 没有空白错误。
   - Verify: `bash mmw/test.sh` → 全部测试通过。

## Acceptance

| Ticket 验收 | 证明方式 | 命令或人工结果 |
| --- | --- | --- |
| CLI 直接接收四栏 task 正文 | CLI 行为测试分别走标准输入与 `--task-text`，并拒绝旧文件参数 | `bash mmw/cli/tests/guardrails.sh` → 两种入口通过，`--task` 拒绝 |
| adapter 不改变多行正文 | 从宿主工具 `params` 或假 `codex` 的标准输入取回正文，逐字比较 | `bash mmw/cli/tests/guardrails.sh` → 特殊字符、空行与结尾换行一致 |
| 角色报告只走标准输出 | 假 `codex` 输出已知报告，检查命令输出和磁盘 | `bash mmw/cli/tests/guardrails.sh` → stdout 含报告，`.dispatch/` 与报告文件都不存在 |
| 派发进度日志使用新名称和路径形状 | 在已绑定任务 worktree 让假 `codex` 失败，检查保留日志的绝对路径和文件名 | `bash mmw/cli/tests/guardrails.sh` → 路径含工作名及可选范围段，文件名为角色加时间戳 |
| 算不出派发进度日志落点时不阻断只读派发 | 从主检出派不带 `--cwd` 的只读角色，检查标准错误、派发结果和磁盘 | `bash mmw/cli/tests/guardrails.sh` → 标准错误含 spec 原句，派发仍执行，没有 `.scratch` 回退或日志文件 |
| Codex App 后台 Worktree 任务显式绑定工作名 | 物化三个后台角色，检查主 agent 传值说明和后台绑定命令 | `uv run --quiet --with pytest python -m pytest mmw/cli/tests/test_materialize_skills.py -q` → `worker`、`worker-high-risk`、`prototype-worker` 都包含当前工作名和 `mmw task bind ... --name <工作名> --from <基点 SHA>` |
| 三项 blocking edge 满足后才执行完整验收 | 开工前确认 `#37`、`#40`、`#42` 已关闭，并确认对应结果已集成当前任务分支 | tracker 没有 open blocker；日志落点、工作名和初始化验收都能运行 |
| CLI 与全部派发动作块同批切换 | 物化测试覆盖所有动作模式，再比较全部技能产物 | `uv run --quiet --with pytest python -m pytest mmw/cli/tests/test_materialize_skills.py -q` 与 `mmw/cli/mmw skills materialize --host all --check` → 通过 |
| 既有派发护栏语义不变 | 在真实一次性仓库重跑缺 cwd、非 Git 工作树、主检出和脏 worktree | `bash mmw/cli/tests/guardrails.sh` → 四类继续拒绝 |
| 初始化不再忽略派发目录 | 消费 plan 09 的初始化结果，不在本 plan 改其文件 | `bash mmw/cli/tests/test_init.sh` → `.gitignore` 不含 `.dispatch/` |
| 整仓回归通过 | 运行统一提交检查 | `bash mmw/test.sh` → 退出码 0 |

## Browser Acceptance

不适用。
