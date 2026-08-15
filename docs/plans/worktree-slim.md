# Plan: 拿掉 MMW 对 worktree 的认领、单独工作名，以及工人树上的同一套手续

**Goal:** 用户自己开任务工作树。agent 只在已有的树上创建任务分支。产物文件夹名等于这次交付的任务分支 slug。工人只要一棵从主 agent 当前树长出来的隔离树。MMW 不再感知、绑定、配置 worktree。

本文件是落地依据。没有另写 spec。下面「已谈定」即合同。

## 已谈定

1. 任务工作树由用户创建和管理。agent 不建任务树，不 `mmw task bind`，不往 git 配置写 `mmw.task.*`。
2. 用户开出来的树常常是 detached：有目录、有某次提交，没有分支。agent 第一步确认这次任务的分支名，在这棵树上 `git switch -c` 建分支。不要沿用宿主给目录起的临时名（例如 Cursor 的 `cursor/5bb9b42d`）。
3. 产物路径的名字段等于这次交付的任务分支 slug：分支名里若有 `/`，取最后一个 `/` 之后的部分。普通任务就是当前任务分支的 slug。Wayfinder 整项工作用 **map 那条分支** 的 slug；decision ticket 自己的分支只承载那次会话的 git 改动。
4. 不再存在独立的「工作名」。废除 git worktree 配置里的 `mmw.task.work-name` / `branch` / `note`，废除为记用户原话而打的空提交。
5. 工人需要隔离工作树。这棵树必须从 **主 agent 当前工作树的当前提交** 长出，不从仓库默认分支长出。各宿主用各自的建树方式。工人进树之后直接干活、提交到结果分支，再合回当前任务分支。不再 bind，不再继承工作名。
6. 历史产物不迁移。新任务走新规则。

## 新行为

### 任务开始

用户已经用宿主工具开好一棵工作树，并在这棵树里开会话。

| 当前 HEAD | agent 做什么 |
| --- | --- |
| 没有分支（detached） | 按 `mmw-start` 现有规则取 slug（`feat-…` / `fix-…` 等）。需要宿主前缀时加在 slug 前面。`git switch -c <完整分支名>`。不打空提交。 |
| 已经挂在这次任务的分支上 | 用这条分支。不要再建一条。 |
| 在仓库主检出里 | 停下，请用户开工作树再开会话。禁止 `git worktree add` 建任务树。禁止 `mmw task new`。 |

Wayfinder charting：这次创建的就是 map 分支。把完整分支名写入 map 正文 `## 分支`。删除 map 正文里的 `## 工作名` 一节。

Wayfinder walking：为这张 ticket 建一条从 map 分支长出的任务分支。写产物时名字段用 map 分支的 slug，不要用 ticket 分支名。取值：读 map 的 `## 分支`，按上面的规则去掉前缀。

### 产物路径

`mmw artifact path` / `list` 在没有 `--name` 时：取当前分支名，按「最后一个 `/` 之后」得到名字段。

当前在 Wayfinder ticket 分支上时，当前分支的 slug 不是名字段。调用方必须传 `--name <map 分支 slug>`。`mmw-wayfinder/walking.md` 写死这一句。charting 会话当时就在 map 分支上，可以不传 `--name`。

### 工人树

派 `worker` / `worker-high-risk` 之前记下当前任务分支的 `HEAD` 作为基点。

| 宿主 | 谁建树 | 从哪长 | 工人进树后 |
| --- | --- | --- | --- |
| Cursor | `mmw-cursor-agent --worktree <结果分支> --worktree-base <当前任务分支>` | 当前任务分支 | 直接实现并提交。不要 `task bind`。 |
| Codex | `create_thread`，`environment.type = worktree`，`branchName` 为当前任务分支 | 当前任务分支 | 直接实现并提交。不要 `task bind`。结果分支仍用宿主要求的名字形状。 |
| Grok | 原生 subagent 打开 worktree 隔离 | 当前任务工作树 | 直接实现并提交。不要 `task bind`。 |
| Pi、Claude Code | `mmw worktree add <结果分支>`（见下） | 当前 `HEAD` | cwd 设为命令输出的路径，然后派 subagent。 |

做完：`mmw result verify` 仍核结果分支、HEAD、基点，并给出树路径以便读 diff。`mmw result integrate` 仍合进当前任务分支。Pi / Claude Code 合入后用 `mmw worktree remove <结果分支>` 收回。Cursor / Codex / Grok 由宿主回收。

### CLI

删除整个 `mmw task` 子命令：`state`、`name`、`bind`、`new`、`cleanup`。

新增两条只服务 Pi / Claude Code 工人树的薄命令：

- `mmw worktree add <结果分支>`：在 `paths.worktrees/<结果分支>` 上 `git worktree add -b`，基点是当前 HEAD。不写 git 配置，不打空提交，不接收 `--name`。
- `mmw worktree remove <结果分支>`：树必须已合进当前分支，且工作区干净。否则非零退出。禁止在这棵树内部删自己。

Cursor / Codex / Grok 上这两条命令失败并说明树由宿主创建和回收。

`mmw result verify` / `integrate` 保留。

### 技能正文

删除 `[[mmw-bind-task]]`。`materialize_skills.py` 同时删除 `[[mmw-bind-task]]` 和未再被调用的 `[[mmw-enter-worktree]]` 展开。

所有「先跑 `mmw task state`，按第一个词选行」换成上面「任务开始」那张三行表，或在已经确定有任务分支的技能里直接开始做事。`walking.md` 里写死的认领表一并换掉。

所有「必须 `bound` 才能继续」改成：当前在一条任务分支上（有 symbolic ref）。没有分支就停。

工人 launch 文案里删掉 `task state` / `task name` / `task bind` / `task new --name`。按上表写宿主自己的建树方式。

`mmw-start/resuming.md`：用 `git worktree list` 找还在的任务树；用当前分支 slug 解析产物。不要读空提交正文当「当初用户要什么」——改读 tracker 和产物。

map 模板与 wayfinding 领域文档：删除「工作名」字段；名字段规则写进 `artifact-location.md`。

## 明确不改

- 工人仍然在隔离树里提交，结果仍然合回任务分支。只删认领手续。
- 四栏 task、`mmw result verify` / `integrate`、六道审、tracker 认领 issue，都不在本范围。
- `paths.worktrees` 和 gitignore / `.graphifyignore` 里对它的排除仍留给 Pi / Claude Code 的工人树。
- `mmw/skill-rebuilds/candidate/` 不改。现役改完后再说。
- `mmw/skills-src/mmw-setup/` 仍是旧背景材料，不参与行为。最多加一句「已被本计划取代」，不重建它。
- 历史 `docs/specs/<旧工作名>/` 等目录不搬家。

## Current State

- `mmw/cli/lib/task.sh` 实现 state / name / bind / new / cleanup，并把工作名写入 `git config --worktree mmw.task.work-name`。bind 还会 `git switch -c` 并打空提交。
- `mmw artifact path` 没给 `--name` 时调用 `mmw_task_state`，要求 `bound` 且带工作名（`mmw/cli/lib/artifact.sh`）。
- `materialize_skills.py` 把 `[[mmw-bind-task]]` 展开成四档表；也实现了 `[[mmw-enter-worktree]]`，但现役技能源没有调用这个占位符。`walking.md` 把认领表直接写在正文里。工人 launch 在 Cursor / Codex / Grok 上要求先 state 再 bind，在 Pi / Claude Code 上要求 `mmw task new --name --from`。
- 十一份技能源调用 `[[mmw-bind-task]]`。另有一批技能要求 `bound` 才继续：`mmw-implement`、`mmw-to-plan`、`mmw-to-tickets`、`mmw-integrate`、`mmw-release`、`mmw-closing`，以及 `mmw-start` / `resuming.md`。
- ADR 0005 规定工作名与任务分支名是两个值，并且不在任务树里就无处存放工作名。本计划改写这条。
- `docs/plans/mmw-artifact-wiring/02-work-name-in-task.md` 是把工作名写进任务树的那次落地。本计划把它收回。

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `mmw/cli/lib/task.sh` | Modify 或拆分 | 删认领。留下（或改名为 worktree.sh）Pi/Claude 的 add/remove |
| `mmw/cli/mmw` | Modify | 删 `task` 子命令。加 `worktree add/remove`。改 usage |
| `mmw/cli/lib/artifact.sh` | Modify | `--name` 缺省时从当前分支算 slug，不再读 `mmw_task_state` |
| `mmw/cli/lib/materialize_skills.py` | Modify | 删 bind-task / enter-worktree。改各宿主 `cwd_mode=worktree` 的 launch 文案 |
| `mmw/cli/tests/test_materialize_skills.py` | Modify | 删 bind/enter 展开测试。改 launch 文案断言 |
| `mmw/cli/tests/guardrails.sh` | Modify | 删 task state/name/bind/new/cleanup 段。加 worktree add/remove 与 artifact 默认名字段 |
| `mmw/cli/adapters/cursor.sh` | Modify | 注释与报错不再提 task bind |
| `mmw/install.sh` | Modify | Cursor 安装注释不再写「主 agent 用 task bind」 |
| `mmw/skills-src/mmw-start/SKILL.md` | Modify | 第 2、3 步：只建分支，不 bind、不请 MMW 建树 |
| `mmw/skills-src/mmw-start/resuming.md` | Modify | 按分支 slug 恢复，不读空提交 |
| `mmw/skills-src/mmw-wayfinder/SKILL.md` | Modify | map 模板删 `## 工作名`；并发会话那条改成「ticket 分支只管 git，产物名字段用 map 分支 slug」 |
| `mmw/skills-src/mmw-wayfinder/charting.md` | Modify | 建 map 分支；写入 `## 分支`；不写工作名 |
| `mmw/skills-src/mmw-wayfinder/walking.md` | Modify | 删正文里的 `mmw task state` 认领表。写产物带 `--name <map slug>` |
| `mmw/skills-src/mmw-implement/SKILL.md` | Modify | 前置条件与工人派发、cleanup 按新 CLI |
| `mmw/skills-src/mmw-implement/worker-brief.md` | Modify | 去掉对工作名 / bind 的依赖 |
| `mmw/skills-src/mmw-integrate/SKILL.md` | Modify | 前置不再要求 bound；cleanup 改 worktree remove |
| `mmw/skills-src/mmw-closing/SKILL.md` | Modify | 同上 |
| `mmw/skills-src/mmw-to-plan/SKILL.md` | Modify | 前置改为「在任务分支上」 |
| `mmw/skills-src/mmw-to-tickets/SKILL.md` | Modify | 用当前分支 slug，不再 `task name` |
| `mmw/skills-src/mmw-to-spec/SKILL.md` | Modify | 删 bind-task；slug 元数据用当前分支 slug |
| `mmw/skills-src/mmw-grilling/SKILL.md` | Modify | 删 bind-task |
| `mmw/skills-src/mmw-research/MAIN.md` | Modify | 删 bind-task |
| `mmw/skills-src/mmw-prototype/SKILL.md` | Modify | 删 bind-task |
| `mmw/skills-src/mmw-diagnosing-bugs/SKILL.md` | Modify | 删 bind-task |
| `mmw/skills-src/mmw-domain-modeling/SKILL.md` | Modify | 删 bind-task |
| `mmw/skills-src/mmw-improve-codebase-architecture/SKILL.md` | Modify | 删 bind-task |
| `mmw/skills-src/wizard/SKILL.md` | Modify | 删 bind-task |
| `mmw/skills-src/to-questionnaire/SKILL.md` | Modify | 删 bind-task |
| `mmw/skills-src/mmw-release/SKILL.md` | Modify | 前置改为在任务分支上 |
| `docs/context/artifact-location.md` | Modify | 名字段 = 任务分支 slug；Wayfinder 用 map 分支 slug。删除独立「工作名」词条或改成指向名字段 |
| `docs/context/host-runtime.md` | Modify | Cursor 条目：用户开树，agent 建分支；不要写 task bind |
| `docs/context/agent-coordination.md` | Modify | 任务 worktree 定义改为用户开的树 + 任务分支 |
| `docs/context/wayfinding.md` | Modify | map 不再记录工作名；记录分支；ticket 继承 map 的名字段 |
| `docs/context/delivery-workflow.md` | Modify | 凡写工作名的地方改成名字段规则 |
| `docs/adr/0005-work-name-vs-branch-name.md` | 由新 ADR 改写 | 新 ADR 写明：名字段复用任务分支 slug（Wayfinder 复用 map 分支 slug） |
| `AGENTS.md` | Modify | 宿主边界里不要再写死 `mmw task new` 与 Cursor bind 的对立，改成「任务树由用户开」 |
| `mmw-skill-map.html` | Modify | 若图上画了 task bind / 工作名，一并改 |

工人 launch 还出现在 `mmw-diagnosing-bugs/fixing.md` 的物化产物里。源若有 `[[mmw-launch:worker:worktree]]`，改 `materialize_skills.py` 即可覆盖产物。落地后必须跑 `mmw skills materialize`（及 Codex `runtime.py materialize`）。

## Contracts and Seams

- **Test seam:** `mmw/cli/tests/guardrails.sh` 与 `test_materialize_skills.py`。验证：artifact 默认名字段来自分支；task 子命令不存在；worktree add 不写 git 配置、不打空提交；Cursor 宿主上 worktree add 失败；launch 文案不含 bind/state/name。
- **Consumes / Produces:** 技能正文不再消费 `mmw task *`。消费 `git switch -c`、`mmw artifact path`（默认名字段或 `--name`）、宿主建树、以及 Pi/Claude 的 `mmw worktree add/remove`。
- 新 ADR 改写 0005。0003 里「一次交付有多条任务分支所以名字段不能等于生产者」仍成立：名字段等于 **map 或本次交付的那一条任务分支**，不等于每张 ticket 的分支。

## Implementation

1. **CLI 先红：默认名字段来自当前分支**
   - Change: `mmw artifact path` 未给 `--name` 时，读 `git symbolic-ref --short HEAD`，取最后一个 `/` 之后作为名字段。没有分支则非零退出，说明要先建任务分支。不再调用 `mmw_task_state`。
   - Files: `mmw/cli/lib/artifact.sh`；`guardrails.sh` 增加用例（`feat-x` 与 `cursor/feat-x` 都得到 `feat-x`）。
   - Verify: `bash mmw/cli/tests/guardrails.sh` 中 artifact 段失败（红）再改到绿。

2. **删 `mmw task`，加 `mmw worktree add/remove`**
   - Change: 删除 state/name/bind/new/cleanup 对外入口。Pi/Claude 的 add：`git worktree add -b` 到 `paths.worktrees/<分支>`，基点当前 HEAD。remove：已合并且干净才删。Cursor/Codex/Grok 上 add/remove 非零退出。
   - Files: `task.sh`（或改名为 `worktree.sh` 并改 `mmw` 的 source）、`mmw/cli/mmw`、`guardrails.sh` 原 task 段改写。
   - Verify: 旧 `mmw task state` 用法失败；`MMW_HOST=pi` 下 add 出树且 `git config --worktree --get mmw.task.work-name` 为空；`MMW_HOST=cursor` 下 add 失败。

3. **物化：删占位符，改工人 launch**
   - Change: 删除 `BIND_TASK_RE` / `ENTER_WORKTREE_RE` 及展开函数。各宿主 `expand_*` 的 `cwd_mode == worktree` 按「新行为 / 工人树」表重写。`cwd_mode == current` 的句子改为「使用当前工作树，不另开结果树」，不要 `task state`。
   - Files: `materialize_skills.py`、`test_materialize_skills.py`。
   - Verify: `python3 mmw/cli/tests/test_materialize_skills.py`。产物正文不得出现 `mmw task`、`[[mmw-bind-task]]`、`[[mmw-enter-worktree]]`。

4. **技能源：入口与前置**
   - Change: 十一处 `[[mmw-bind-task]]` 换成「任务开始」三行表或删掉（已在任务分支上的技能）。`walking.md` 写 `--name` 取自 map `## 分支`。`mmw-start` 第 3 步只 `git switch -c`。要求 `bound` 的技能改成要求当前有任务分支。
   - Files: Change Map 中全部 `mmw/skills-src/**`。
   - Verify: `rg 'mmw task |mmw-bind-task|mmw-enter-worktree|mmw.task.work-name' mmw/skills-src` 仅允许在本计划或注释「已废除」里出现。

5. **领域文档与 ADR**
   - Change: 新 ADR 改写 0005。leaf 按 Change Map 改术语。map 定义改为记录分支、不记录工作名。
   - Files: `docs/adr/` 新文件、`docs/context/*.md`、`AGENTS.md`。
   - Verify: `CONTEXT-MAP.md` 与各 leaf 不再把工作名定义为独立于分支的值。

6. **物化到各宿主并跑全套检查**
   - Change: `mmw skills materialize`（各宿主）、`python3 mmw/codex/runtime.py materialize`。更新 `mmw-skill-map.html` 若涉及。
   - Files: 生成的 `skills-pi` / `skills-cursor` / `skills-codex` / `skills-claude-code` / `skills-grok`（只通过物化产生，不手改）。
   - Verify: `bash mmw/test.sh` 退出码 0。

## Acceptance

| 验收 | 证明方式 | 命令或结果 |
| --- | --- | --- |
| 没有 `mmw task` 子命令 | CLI | `mmw task state` 非零，usage 不再列出 task |
| 产物名字段来自分支 slug | 测试 | 分支 `cursor/feat-login` 上 `mmw artifact path spec` 的路径含 `feat-login`，不含 `cursor` |
| 不写 worktree git 配置 | 测试 | `mmw worktree add` 之后 `git config --worktree --get-regexp mmw.task` 为空 |
| 技能源不再认领 | 检索 | skills-src 无 `[[mmw-bind-task]]`、无 `mmw task state` |
| 工人 launch 不再 bind | 物化测试 | Cursor/Codex/Grok/Pi 展开文案无 `task bind` / `task new --name` |
| Cursor/Codex/Grok 不在仓库 `.worktrees` 建任务树 | CLI | 这些宿主上 `mmw worktree add` 失败；技能也不叫它建**任务**树 |
| Wayfinder 名字段规则写在技能里 | 阅读 | walking.md 写明 `--name` 来自 map `## 分支` 的 slug |
| 全套检查通过 | `bash mmw/test.sh` | 退出码 0 |

## Browser Acceptance

不适用。

## Rollback and Gates

改的是 MMW 自己的技能和 CLI，不是用户数据。合回主分支前跑通 `bash mmw/test.sh`。不 push、不发布，除非用户明确说发布。

落地时用户确认本计划即可开始，不必再开一道「工作名是否独立」的讨论。
