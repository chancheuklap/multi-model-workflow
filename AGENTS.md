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
| 0 · 配置 | 六份种子随插件分发，在 `mmw-v2/skills/setup/`；`/setup` 铺进目标仓库的 `docs/agents/`。我们的选择全固定，所以 setup 不问问题（这是比 Matt 更简的形态：他要问，因为他的用户各不相同）。技能一律读目标仓库的 `docs/agents/*.md`，不读插件内路径——避免旧 plugin 那套「先定位插件根」的烂摊子 |
| 1 · 纪律 | Matt 的 model-invoked 技能原样搬：tdd、diagnosing-bugs、codebase-design、domain-modeling、grilling、prototype、resolving-merge-conflicts、research |
| 2 · 自有能力 | 跨模型派发、亲验裁判、任务隔离。这三块 Matt 完全没有，是仓库存在的理由 |
| 3 · 编排 | 改造 Matt 的 user-invoked 技能，把第 2 层注入进去 |

### 搬迁批次

搬迁已完成：Matt 那边 18 个技能全在 `mmw-v2/skills/`，搬进来时除自写的 `setup` 外一律原样复制自 vendor，未改一字。加上自写的 `dispatching-agents`、`judging-agent-output`、`mmw-start`，以及顺手补搬的 11 个上游技能，manifest 现在登记 33 个。

**触发方式**：Matt 大部分技能是人打名字才走（`disable-model-invocation: true`）。我们的入口是 `mmw-start`，它要能把活直接交给下游技能，所以链路上的技能一律改成模型可触发，description 按 `writing-great-skills` 的写法改成触发式。已经改过的技能正文一并译成中文，合集通用术语（spec、ticket、seam、frontier、worktree、tight、red、fog of war、destination、map、HITL / AFK、ready-for-agent）保持英文。

改造按 Matt 主干顺序推进，一个跑通再动下一个。先做了链条末端的两个，因为跨模型派发和亲验裁判在那里第一次落地，前面几个技能要复用同一套底子：

| 顺序 | 技能 | 要加什么 | 状态 |
| --- | --- | --- | --- |
| 0 | `mmw-start` | 我们自己的入口：认路、起 slug、建树进树、记原话、交棒 | 已落地 |
| 1 | `grill-with-docs` | 开问前先查仓库现状；摆路线让用户选；出口交给 `to-spec` | 待做（已转模型可触发） |
| 2 | `to-spec` | 测试接缝判据（用旧 plugin 那套测试规矩）、`/approve-design` 人闸、派 Codex 审这份设计 | 待做 |
| 3 | `to-tickets` | 实施计划塞在哪：切片 issue 正文还是单独文档 | 待做 |
| 4 | `implement` | 换成 worktree + 派 Codex 无头写码 | 已落地 |
| 5 | `code-review` | 接亲验裁判，把 Matt 明确不做的判断补上 | 已落地 |

`ask-matt` 是 Matt 的路由器，路由判据已经被 `mmw-start` 吸收，本身不再有用途，等确认后删掉。它还留着三处指向不存在技能的悬空引用（`/grill-me`、`/teach`、`/writing-great-skills`）。

### 已落地

第 2 层三块自有能力里的两块，加上末端两个编排技能，都已写成技能并各自实跑验过一轮。设计结论住在技能自己那几份文件里，本文件不复述。

| 落点 | 内容 | 怎么验的 |
| --- | --- | --- |
| `skills/dispatching-agents` | 两个后端（Claude sub-agent、Codex 无头）、模型档一律从 `docs/agents/models.md` 取、简报自包含 | 实跑派出过审者和写码工人各一轮 |
| `skills/judging-agent-output` | 采信段（每条承重断言要有主线程能自己复核的锚）加处置段（五个英文处置词） | 实跑八条 findings 逐条坐实，其中一条审者报的行号真的差了一行 |
| `skills/code-review` | Matt 两轴之外补第三轴 Correctness，跨家派发，findings 原样落盘再裁判 | 实跑一轮真 diff，Claude 和 Codex 各自捞到对方没看见的一条 |
| `skills/implement` | 主线程不写码，一张 ticket 派一个 Codex 无头工人；主线程只做备料、派发、验收、起审 | 实跑一个真工人在 throwaway 仓库里做完一张 ticket，测试全绿 |
| `skills/tdd` | 接缝改成由 spec 钉死（无头工人问不到人），另加 `quality-bar.md` 收下旧 plugin 那套测试规矩 | 随 `implement` 一起跑过 |
| `skills/mmw-start` | 六条路由判据；worktree 建错了重建，所以报一句就走不等确认；`resuming.md` 靠查产物报进度，不设状态文件 | 未实跑 |
| `skills/triage` | 新增「出口」一节：只碰一处且 brief 写明 seam 直走 `implement`，碰多处走 `to-spec`；agent brief 模板加 `Test seam` 栏 | 未实跑 |
| `skills/diagnosing-bugs` | 前四个 Phase 主线程做，Phase 5 的修派 Codex 工人；派发前先删 `[DEBUG-]` 埋点保证树干净 | 未实跑 |

断点续传不用状态文件：每一步都有一件落在 git 或 GitHub 上的产物对应它（分支上第一个空提交记用户原话、`docs/specs/<slug>/`、子 issue 的开关与 assignee、`.reviews/`、Wiki 页），查产物就知道走到哪。旧 plugin 需要状态文件是因为它有阶段引擎要记 phase 变量，新架构没有引擎。唯一查不出来的是 seam 那道人闸过没过。

派可写沙箱时踩到的坑已记进 `dispatching-agents`：`--sandbox workspace-write` 默认把 `.git` 锁成只读，工人提交会卡死，要把 worktree 的 `.git` 加进 `writable_roots`。

### 待定事项

| 要定什么 | 当时的背景与张力 | 旧实现位置（背景线索） |
| --- | --- | --- |
| `/setup` 要不要自动跑 | 现在得手敲，用户忘了跑配置就全空、技能读不到任何仓库事实。想用 SessionStart 钩子自动铺，但那要接 `hooks/hooks.json`，属于插件机械层，等第 2 层能力定形后一起做 | `plugin/hooks/` |
| 纪律层剩下六个技能的适配 | 八个里 `tdd` 和 `diagnosing-bugs` 已经改完，其余六个还是原样搬进来的，一个字没改。每个都有旧 plugin 里的自有加法要合（见右栏） | `research` ← `investigate-internal` / `investigate-external`；`prototype` ← `scripts/prototype.sh`、`design/prototype-mockup.md`；`resolving-merge-conflicts` ← `scenario/merge.md`；`domain-modeling` ← 核 ADR 编号约定；`grilling` ← `design/discussion.md` |
| 任务隔离要不要脚本 | 建树、进树、打空提交这三步已经写进 `mmw-start` 的正文，主线程直接跑命令就够，暂时不做脚本。清理那一步要用户点头，本来也不适合脚本化 | `plugin/scripts/prepare.sh` 的 task new / cleanup |
| `/approve-design` 人闸和无人值守档 | 新架构没有阶段引擎，「设计过门」这个动作靠什么承载还没答案（issue 标签？提交？）。人闸只有这一道，口头同意不算 | `plugin/commands/approve-design.md`、`plugin/skills/orchestrate/references/control/attendance.md` |
| 本地文档转 Wiki 的脚本 | 约定全定完了，在 `mmw-v2/skills/setup/wiki.md`（命名、页面结构、导航生成、写入顺序、三条核验）。只剩生成 `Home.md` / `_Sidebar.md` 那段薄脚本怎么写，以及挂在收尾技能的哪一步 | 无（新能力） |
