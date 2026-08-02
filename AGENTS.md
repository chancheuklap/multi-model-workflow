# AGENTS.md

## 仓库范围

本仓库是同一套多模型开发编排的四个单宿主实现：共享产品语义，接线、状态目录、派发后端各自独立；运行时不得互相探测或调用。

| 宿主 | 源码目录 | 发布入口 | 状态目录 | 任务 worktree | 角色执行后端 |
| --- | --- | --- | --- | --- | --- |
| Claude Code | `plugin/` | `plugin/.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` | `.claude/multi-model-workflow/` | `.claude/worktrees/` | Codex CLI 工人 + 宿主 sub-agent 审者 |
| Factory Droid | `droid-plugin/` | `droid-plugin/.factory-plugin/plugin.json`、`.factory-plugin/marketplace.json` | `.factory/multi-model-workflow/` | `.factory/worktrees/` | `droid exec` + Custom Droids |
| pi | `pi-plugin/` | `pi-plugin/package.json` | `.pi/multi-model-workflow/` | `.pi/worktrees/` | pi-subagents + 动态 workflows |
| Cursor | `cursor-plugin/` | `cursor-plugin/.cursor-plugin/plugin.json`、根 `.cursor-plugin/marketplace.json` | `.cursor/multi-model-workflow/` | `.cursor/worktrees/`（任务 wt 常 UI 悬空创建后 `mmw task adopt`） | Cursor Task + `~/.cursor/agents` |

`archive/plugin-v1/` 冻结归档：不参与行为判断、构建或测试；无明确指令不改。

`vendor/mattpocock-skills/` 是上游 `mattpocock/skills` 的完整副本，用 git subtree squash 拉入，供各 plugin 按名字引用其中的技能（如 `productivity/grilling`、`engineering/prototype`、`engineering/domain-modeling`）。不手改，改了下次拉取必冲突。更新：

```bash
git subtree pull --prefix vendor/mattpocock-skills https://github.com/mattpocock/skills main --squash
```

## 当前工作流

阶段、结论词、审闸、场景预设以各宿主 `state-schema/routes.json` 为准；统一入口 `scripts/mmw.sh`。

| 场景 | 阶段 |
| --- | --- |
| `small-change` | build → final review → closing |
| `bug` | investigate → build → final review → closing |
| `develop` | 可选 wayfind → investigate → propose → design → to-issue → plan → plan review → build → final review → package → closing |
| `merge` | 不建任务 worktree；单独处理意图与实现冲突 |

- 正式任务先跑该宿主 `bash <源码目录>/scripts/mmw.sh where`（Cursor 本机也可用引擎根下 `mmw.sh`），按 `load` / `do` / `then` 行动。
- 设计只认 `/approve-design`；口头同意不过门。计划审与终审是模型闸（终审分档见 routes / runtime-contract）。package 有目标安装包时，功能测试与安装后测试仍需负责人确认。
- 状态、接力单、brief、账本、进度板只认该宿主状态目录。

## 事实源

同一宿主内按序核对：manifest / package → `state-schema/*.json` → `scripts/`、`hooks/`（pi 另含 `extensions/`、`workflows/`）→ `scripts/tests/`、`build/tests/` → 运行时 Markdown。

四宿主不必逐字一致；共性行为变更要四个都查。宿主专属路径、工具名、生命周期、派发后端禁止抄成兼容分支。

根文档只保留 `AGENTS.md`、`CLAUDE.md`、`TESTING.md`。勿新增 README / 架构 / 设计 / 调查 / 计划 / 审查类仓库说明。长期规则写本文件；运行行为写对应宿主 runtime 与测试。

运行时 Markdown（宿主加载或 Cursor install 后生效，不是说明文档）在各宿主 `agents|droids|agents-roster`、`commands`、`skills`、`build/fragments/`（pi 另有 `prompts/`；Cursor 源码整树在 `cursor-plugin/`，本机生效面见下）。

## 修改规则

- 改宿主前读该宿主 `skills/orchestrate/SKILL.md`、完整 reference、脚本与测试。测前读根 `TESTING.md`。
- 共用片段只改 `build/fragments/*.md`，再对该宿主 `build/build.sh --apply` 与 `--check`；锚点生成区禁手改。两份 `task-pack.md` 必须一致（`test_shared_refs_sync.sh`）。
- pi：GPT 公共提示词改 `agents-roster/_fragments/` 后跑 `render_agent_prompts.py`；workflow 改 `workflows/*.workflow.js` 后跑 `install-workflows.sh`（含 `--check`）。
- 版本：Claude 同步 plugin manifest + marketplace（含根版本）；Droid 同步 plugin + marketplace；pi 以 `package.json` 为准；Cursor 同步 `cursor-plugin/.cursor-plugin/plugin.json` 与根 `.cursor-plugin/marketplace.json`。
- **Cursor**：源码只改 `cursor-plugin/`。本机跑 `bash cursor-plugin/scripts/install-local-surface.sh` 复制到 `~/.cursor/{agents,skills,commands,rules,hooks}`，合并 `hooks.json` / `mcp.json`，引擎树落到 `~/.cursor/multi-model-workflow-engine/`（可用 `MMW_ENGINE_ROOT`）。花名册 frontmatter（`model` 含 `id[effort=…]`、`is_background`）生效；Task 只传 `subagent_type`（+prompt/background）。细合同见 `cursor-plugin/skills/orchestrate/references/control/runtime-contract.md`。改完须再 install + Reload；运行时不以 `plugins/local` 为发现面。
- 不用旧残留、兼容目录或静默默认值掩盖错误；脚本异常须非零退出或结构化告警。

## Git 与安全

- 正式改动在独立 worktree；合回主分支用 `git merge --no-ff`，禁止 squash。
- 写码工人禁改 `docs/`；计划工人只改自己的 plan 与对应 issue（`worker verify` / `plan-check`）。
- 本地 commit / merge 可自主；`git push`、远端合并、部署须用户批准。
- 子代理输出不是事实源；承重定位与测试结论写入前由主线程复核。

## 构建与测试

```bash
for host in plugin droid-plugin pi-plugin cursor-plugin; do
  bash "$host/build/build.sh" --check || exit 1
  bash "$host/build/tests/test_build.sh" || exit 1
  for test_file in "$host"/scripts/tests/test_*.sh; do
    bash "$test_file" || exit 1
  done
done

for host in plugin droid-plugin pi-plugin cursor-plugin; do
  uv run --with pytest --with pydantic pytest \
    "$host/scripts/tests/test_release_contracts.py" \
    "$host/scripts/tests/test_release_script_assembler.py" || exit 1
done

python3 pi-plugin/scripts/render_agent_prompts.py --check
bash pi-plugin/workflows/install-workflows.sh --check
```

提交前：`git diff --check`；本次改动的 JSON 用 `python3 -m json.tool` 校验。

## mmw-v2 重建（进行中，完成后本节删除）

新 plugin 在 Matt 的技能上长出我们自己的骨架，不再把流程实现成引擎。上游副本在 `vendor/mattpocock-skills/`，旧实现在 `plugin/`（只作背景线索，不搬重流程）。落点暂名 `mmw-v2/`（仓库里已有上次失败的 `mmw/`，别混），全部弄好再改名。只做 Claude Code 一个宿主。

### 地基四层

| 层 | 内容 |
| --- | --- |
| 0 · 配置 | 五份种子随插件分发，在 `mmw-v2/skills/setup/`；`/setup` 铺进目标仓库的 `docs/agents/`。我们的选择全固定，所以 setup 不问问题（这是比 Matt 更简的形态：他要问，因为他的用户各不相同）。技能一律读目标仓库的 `docs/agents/*.md`，不读插件内路径——避免旧 plugin 那套「先定位插件根」的烂摊子 |
| 1 · 纪律 | Matt 的 model-invoked 技能原样搬：tdd、diagnosing-bugs、codebase-design、domain-modeling、grilling、prototype、resolving-merge-conflicts、research |
| 2 · 自有能力 | 跨模型派发、亲验裁判、任务隔离。这三块 Matt 完全没有，是仓库存在的理由 |
| 3 · 编排 | 改造 Matt 的 user-invoked 技能，把第 2 层注入进去 |

### 搬迁批次

搬迁已完成：19 个技能全在 `mmw-v2/skills/`，除自写的 `setup` 外一律原样复制自 vendor，未改一字。

改造按 Matt 主干顺序推进，一个跑通再动下一个：

| 顺序 | 技能 | 要加什么 |
| --- | --- | --- |
| 1 | `grill-with-docs` | 开问前先查仓库现状；摆路线让用户选；出口交给 `to-spec` |
| 2 | `to-spec` | 测试接缝判据（用旧 plugin 那套测试规矩）、`/approve-design` 人闸、派 Codex 审这份设计——跨模型派发在这里第一次落地 |
| 3 | `to-tickets` | 实施计划塞在哪：切片 issue 正文还是单独文档 |
| 4 | `implement` | 换成 worktree + 派 Codex 无头写码 |
| 5 | `code-review` | 接亲验裁判，把 Matt 明确不做的判断补上 |

`ask-matt` 是 Matt 的路由器，留着做底子，最终名字和内容都要换成我们自己的入口。

### 批 2 已落地

跨模型派发、亲验裁判、`code-review` 三轴改造已写成技能，实跑一轮验过（`mmw-v2/skills/dispatching-agents`、`judging-agent-output`、`code-review`）。设计结论住在那三份技能里，本文件不再复述。

改造顺序表里 `code-review` 那一行因此完成；下一个是 `implement`（worktree 加派 Codex 无头写码），它复用同一套派发与裁判。

### 待定事项

| 要定什么 | 当时的背景与张力 | 旧实现位置（背景线索） |
| --- | --- | --- |
| 派 Codex 无头写码 | 审那一侧的派发已落地，写那一侧还没：可写沙箱、首派前工作树要干净、交回的完工报告怎么验收。跟 `implement` 一起做 | `plugin/scripts/worker.sh` |
| `/setup` 要不要自动跑 | 现在得手敲，用户忘了跑配置就全空、技能读不到任何仓库事实。想用 SessionStart 钩子自动铺，但那要接 `hooks/hooks.json`，属于插件机械层，等第 2 层能力定形后一起做 | `plugin/hooks/` |
| 纪律层八技能的适配 | 原样搬进来了，一个字没改。每个技能都有旧 plugin 里的自有加法要合（见下表）。已看清的第一个真冲突：Matt 的 `tdd` 要求写测试前跟用户确认接缝，我们的写码工人是无人值守 Codex，问不到人，所以要改成「接缝由计划的 Task Pack 钉死」 | `tdd` ← `worktree-build/references/tests.md`、`discipline.md`；`research` ← `investigate-internal` / `investigate-external`；`prototype` ← `scripts/prototype.sh`、`design/prototype-mockup.md`；`resolving-merge-conflicts` ← `scenario/merge.md`；`diagnosing-bugs` ← 悬空引用 + `scenario/bug.md`；`domain-modeling` ← 核 ADR 编号约定；`grilling` ← `design/discussion.md` |
| 任务隔离脚本 | 建 / 进 / 清 worktree 加 docs 落点。约定全在 `mmw-v2/skills/setup/worktrees.md`，只剩薄脚本怎么写 | `plugin/scripts/prepare.sh` 的 task new / cleanup |
| `/approve-design` 人闸和无人值守档 | 新架构没有阶段引擎，「设计过门」这个动作靠什么承载还没答案（issue 标签？提交？）。人闸只有这一道，口头同意不算 | `plugin/commands/approve-design.md`、`plugin/skills/orchestrate/references/control/attendance.md` |
| 本地文档转 Wiki 的脚本 | 约定全定完了，在 `mmw-v2/skills/setup/wiki.md`（命名、页面结构、导航生成、写入顺序、三条核验）。只剩生成 `Home.md` / `_Sidebar.md` 那段薄脚本怎么写，以及挂在收尾技能的哪一步 | 无（新能力） |
