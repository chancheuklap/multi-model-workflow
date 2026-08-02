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
- **mmw-v2 的每份技能以一节「下一步」收尾**，形式固定成两列表（情况、下一步），动词只用「自己继续」「移交」「停」三个。只有两种情况允许停：agent 开不了新会话，或者事情要人拍板；其余一律自己接着做。
- **审查方法论只有一份**，在 `mmw-reviewer`，审者读它，主线程不读也不转述。改审查判据只改那里；`mmw-review` 只管编排（哪一道、几路、谁去审、备什么材料）。审者靠装载读到它（软链进无头那一家自己的技能目录），不靠把方法论粘进提示词。
- **技能里提到另一个技能一律写 `` `/技能名` ``**，跟上游合集一致，不分调起还是引用方法。同名的分支、`wayfinder:` 标签值、文件路径不加斜杠。

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
| 0 · 配置 | 七份种子随插件分发，在 `mmw-v2/skills/mmw-setup/`；`/mmw-setup` 把前六份铺进目标仓库的 `docs/agents/`，第七份 `testing.md` 铺成仓库根的 `TESTING.md` 骨架。我们的选择全固定，所以 setup 不问问题（这是比 Matt 更简的形态：他要问，因为他的用户各不相同）。技能一律读目标仓库的 `docs/agents/*.md`，不读插件内路径——避免旧 plugin 那套「先定位插件根」的烂摊子 |
| 1 · 纪律 | Matt 的 model-invoked 技能：tdd、diagnosing-bugs、codebase-design、domain-modeling、grilling、prototype、research（原本还有 resolving-merge-conflicts，已吸收进 `mmw-review` 的 ⑥ 并删除） |
| 2 · 自有能力 | 跨模型派发、亲验裁判、任务隔离。这三块 Matt 完全没有，是仓库存在的理由 |
| 3 · 编排 | 改造 Matt 的 user-invoked 技能，把第 2 层注入进去 |

### 搬迁批次

搬迁已完成：Matt 那边 18 个技能搬进 `mmw-v2/skills/`，除自写的 `mmw-setup` 外一律原样复制自 vendor。加上自写的 `mmw-dispatching-agents`、`mmw-verifying-agent-output`、`mmw-start`、`mmw-to-plan`、`mmw-planner`，还有顺手补搬的 11 个上游技能，manifest 现在登记 32 个。

**触发方式**：Matt 大部分技能是人打名字才走（`disable-model-invocation: true`）。我们的入口是 `mmw-start`，它要能把活直接交给下游技能，所以链路上的技能一律改成模型可触发，description 按 `writing-great-skills` 的写法改成触发式。已经改过的技能正文一并译成中文，合集通用术语（spec、ticket、seam、frontier、worktree、tight、red、fog of war、destination、map、HITL / AFK、ready-for-agent）保持英文。

**`mmw-` 前缀标记所有权。** 正文真正被我们改造过的技能，目录名和 `name` 一律加 `mmw-` 前缀，跟原样搬进来的上游技能区分开。现在有 19 个：`mmw-start`、`mmw-setup`、`mmw-dispatching-agents`、`mmw-verifying-agent-output`、`mmw-grilling`、`mmw-triage`、`mmw-wayfinder`、`mmw-to-spec`、`mmw-to-tickets`、`mmw-to-plan`、`mmw-planner`、`mmw-implement`、`mmw-tdd`、`mmw-review`、`mmw-reviewer`、`mmw-diagnosing-bugs`、`mmw-prototype`、`mmw-closing`、`mmw-research`。

**不留只做跳转的空壳。** 一个技能正文只是「去跑另外那个技能」，就把它的内容并进被它调的那个，然后删掉它。已删四个：`grill-with-docs`（并进 `mmw-grilling`）、`ask-matt`（路由判据并进 `mmw-start`）、`batch-grill-me`、`claude-handoff`。

**不按上下文容量做判断。** 我们不会因为窗口满了就重开会话，所以「一个会话装不装得下」不是任何判据。活的大小按**要拆成几份 spec** 衡量：一份 spec 说得清走 `mmw-grilling` → `mmw-to-spec`；哪几份 spec、按什么顺序都还没数才走 `mmw-wayfinder`。`handoff` 单独保留，供用户自己手动交接用。

改造按 Matt 主干顺序推进，一个跑通再动下一个。先做了链条末端的两个，因为跨模型派发和亲验裁判在那里第一次落地，前面几个技能要复用同一套底子：

| 顺序 | 技能 | 要加什么 | 状态 |
| --- | --- | --- | --- |
| 0 | `mmw-start` | 我们自己的入口：判定路线、定 slug、建树进树、记原话、移交 | 已落地 |
| 1 | `mmw-grilling` | 开问前先查仓库现状；领域词与 ADR 随谈随落；出口交给 `mmw-to-spec` | 已落地 |
| 2 | `mmw-to-spec` | 测试 seam 判据（用旧 plugin 那套测试规矩）、`/approve-design` 人闸、派 Codex 审这份设计 | 已落地 |
| 3 | `mmw-to-tickets` | 接进我们的 tracker 约定：正文按三层结构写、`## Plan` 一节先占住 plan 路径、编号即 plan 编号；亮清单不等确认，因为人闸在 spec 那一步 | 已落地 |
| 3.5 | `mmw-to-plan` 与 `mmw-planner` | 补上旧 plugin 的二层拆解：一张 ticket 一份 plan 一个工人，编排与写作方法论分开 | 已落地 |
| 4 | `mmw-implement` | 换成 worktree + 派 Codex 无头写码 | 已落地 |
| 5 | `mmw-review` 与 `mmw-reviewer` | 审查抽成一层：编排与纪律分开，八路视角，方法论装给审者不粘提示词 | 已落地 |

### 已落地

第 2 层三块自有能力里的两块，加上末端两个编排技能，都已写成技能并各自实跑验过一轮。设计结论住在技能自己那几份文件里，本文件不复述。

| 落点 | 内容 | 怎么验的 |
| --- | --- | --- |
| `skills/mmw-dispatching-agents` | 两个后端（Claude sub-agent、Codex 无头）、模型档一律从 `docs/agents/models.md` 取、简报自包含 | 实跑派出过审者和写码工人各一轮 |
| `skills/mmw-verifying-agent-output` | 只管采信：每条承重断言要有主线程能自己复核的锚，加工人交回的四档怎么读。findings 怎么处置归 `mmw-review` | 实跑八条 findings 逐条复核，其中一条审者报的行号真的差了一行 |
| `skills/mmw-review` | 主线程侧的编排：六道审各在哪、几路、谁配谁、每一路备齐什么材料、落盘命名、复审。③ 逐份验收与 ④ 合同门不派审者，判据也写在这里 | 未实跑 |
| `skills/mmw-reviewer` | 审者侧的方法论单源：共享纪律加八路视角。标准原样搬旧 plugin，只补 Matt 那一路编码规范审。砍掉严重度与置信度，保留 `needs-redirection`、`needs-context` 两个出口 | 未实跑；装载脚本四种情形实测通过 |
| `skills/mmw-dispatching-agents/install-agent-skills.sh` | 装载脚本，软链三份方法论进无头那一家自己的技能目录：审查、写计划、测试。从起审技能旁边挪到派发技能旁边，因为它不再只服务审者 | 三份装、幂等重跑、`--check` 实测通过 |
| `skills/mmw-implement` | 主线程不写码，一张 ticket 派一个 Codex 无头工人；主线程只做准备简报、派发、验收、起审 | 实跑一个真工人在 throwaway 仓库里做完一张 ticket，测试全绿 |
| `skills/mmw-tdd` | 测试要求分三层：怎么写（本技能加 `tests.md`、`mocking.md`）、够不够格进仓库（`quality-bar.md`）、这个仓库的事实（目标仓库根 `TESTING.md`，由 `mmw-setup` 铺骨架）。seam 由 spec 钉死，因为无头工人问不到人 | 随 `mmw-implement` 一起跑过 |
| `skills/mmw-start` | 七条路由判据（含「报了一张 map 的编号」）；worktree 建错了重建，所以报一句就走不等确认；`resuming.md` 靠查产物报进度，不设状态文件 | 未实跑 |
| `skills/mmw-wayfinder` | 按会话拆成三条 branch：`drawing.md` 建 map、`walking.md` 认领一条链、`closing.md` 收口，三条共用 `map-anatomy.md`。SKILL.md 只留入口判定和几个会话同时跑的四条硬约束 | 未实跑 |
| `skills/mmw-triage` | 新增「出口」一节：只碰一处且 brief 写明 seam 直走 `mmw-implement`，碰多处走 `mmw-to-spec`；agent brief 模板加 `Test seam` 栏 | 未实跑 |
| `skills/mmw-diagnosing-bugs` | 按 Phase 拆三份：SKILL.md 只留 Phase 1 造 loop，`narrowing.md` 收窄，`fixing.md` 派工人修。拆的理由是知道后面还有五个 Phase 会让人草率对待 Phase 1 | 未实跑 |
| `skills/mmw-grilling` | 吸收 `grill-with-docs`：开问前先查现状，谈的过程里按 `domain-modeling` 落术语与 ADR，主线出口交 `mmw-to-spec`。四个技能共用它，所以它单独存在，不并进任何一个 | 未实跑 |
| `skills/mmw-prototype` | Matt 那份是一次性探路、做完扔废弃分支，旧 plugin 那份是设计内层循环、产物是正式资产。取旧的地位加 Matt 的手法：产物落 `docs/prototypes/<slug>/` 且不随 spec 转 Wiki 删除，一轮只验一个能判真假的问题，走查是人闸，界面变体一个变体派一个劳动力防趋同，`capture.md` 单独收回灌 | 未实跑 |
| `skills/mmw-to-tickets` | 上游那份接进我们的 tracker 约定：正文只留摘要、`## Plan` 一节先把 plan 路径占住、编号即 plan 编号；发布沿 frontier 走，`ready-for-agent` 打在 ticket 上是「可开工」，跟 spec issue 上那个人闸凭据分开。切分清单亮给用户就往下走，不等确认——粒度由 ② plan 审兜住。tracer bullet、expand–contract 那几段判据原样译出 | 未实跑 |
| `skills/mmw-to-plan` | 主线程侧的编排，原样搬旧 plugin 那五步：定 plan 清单、派工人之前把合同落到 plan 头上（spec 新增 `## Cross-Plan Contract Anchors` 一节，不动人闸过的 `## Contract Boundaries`）、扇出派工人、亲验返回、回填精确字段并核越界。收尾起一次 ② plan 审 | 未实跑 |
| `skills/mmw-planner` | 写计划工人侧的方法论单源，原样搬旧 plugin `worktree-plan` 那三份。砍掉跨 plan 合同锚点的自行发明（改由主线程划）、砍掉再切一层 slice（ticket 已经是 tracer bullet，工人只拆它内部的实施步骤）。测试规划这一层留着，测试怎么写引 `mmw-tdd` | 未实跑 |
| `skills/mmw-research` | 上游那 12 行只剩一条有用：一手来源。改造的要点是**判据下发到采集那一侧**——一手来源和事实写法两段原样写进简报，不是收回来才挑剔。派发与复核各引对应技能，不复述 | 未实跑 |
| `skills/mmw-closing` | 一次任务的收尾：把 spec 与 plan 转成 Wiki 的一页、重生成两个导航文件、推送前给用户看、三条核验全过才删本地那两个目录。归档约定不复述，指 `docs/agents/wiki.md`。原型产物不删 | 未实跑 |
| `skills/mmw-to-spec` | 六条入口路径各自要取齐哪些上游产物写成一张表；seam 一节的形状定死成清单，因为下游直接读它；模板吸收旧 plugin 的现状引用、失败路径、视觉契约、还没拍板的事；派一个 Codex 审这份 spec；用户点头之后才发布 issue 并打 `ready-for-agent`，这个动作就是人闸的凭据 | 未实跑 |

十九个 `mmw-` 技能里，十七个有 `## 下一步` 表（`mmw-reviewer` 和 `mmw-planner` 没有——它们是派出去的劳动力读的方法论，不是流程技能），形式一致：两列（情况、下一步），动词只有「自己继续」「移交」「停」。`mmw-tdd` 及各技能下的 reference 全部补译成中文（派给审者和工人的提示词也是中文，模板里的结构字段名保持英文），全仓用词已对齐（决策改为决定，坐实改为复核，雾改为 fog of war，map 与 spec 的模板节名一律用英文原文）。上游原样搬进来的技能不加这一节——`domain-modeling`、`codebase-design` 做完就是做完，没有会带跑我们流程的出口。

断点续传不用状态文件：每一步都有一件落在 git 或 GitHub 上的产物对应它（分支上第一个空提交记用户原话、`docs/specs/<slug>/`、子 issue 的开关与 assignee、`.reviews/`、Wiki 页），查产物就知道走到哪。旧 plugin 需要状态文件是因为它有阶段引擎要记 phase 变量，新架构没有引擎。全流程唯一那道人闸也有产物：`mmw-to-spec` 只在用户点头之后才发布 spec issue 并打 `ready-for-agent`，issue 在且带这个标签就是过门的凭据。

派可写沙箱时踩到的坑已记进 `mmw-dispatching-agents`：`--sandbox workspace-write` 默认把 `.git` 锁成只读，工人提交会卡死，要把 worktree 的 `.git` 加进 `writable_roots`。

### 待定事项

| 要定什么 | 当时的背景与张力 | 旧实现位置（背景线索） |
| --- | --- | --- |
| `/mmw-setup` 要不要自动跑 | 现在得手敲，用户忘了跑配置就全空、技能读不到任何仓库事实。想用 SessionStart 钩子自动铺，但那要接 `hooks/hooks.json`，属于插件机械层，等第 2 层能力定形后一起做 | `plugin/hooks/` |
| 纪律层剩下两个技能的适配 | 八个里 `mmw-tdd`、`mmw-diagnosing-bugs`、`mmw-grilling`、`mmw-prototype`、`mmw-research` 已经改完，`resolving-merge-conflicts` 已吸收进 `mmw-review` 的 ⑥ 并删除，其余两个还是原样搬进来的，一个字没改 | `domain-modeling` ← 核 ADR 编号约定；`codebase-design` ← 无 |
| 补搬那 11 个上游技能留不留 | `qa`、`wizard`、`to-questionnaire`、`request-refactor-plan`、`design-an-interface`、`setup-ts-deep-modules`、`git-guardrails-claude-code`、`setup-pre-commit` 等来自上游 `deprecated/`、`in-progress/`、`misc/`，不在我们的主干上，但也不是空壳。留着占 description 的常驻成本，删了以后要用再搬回来 | 无 |
| 任务隔离要不要脚本 | 建树、进树、打空提交这三步已经写进 `mmw-start` 的正文，主线程直接跑命令就够，暂时不做脚本。清理那一步要用户点头，本来也不适合脚本化 | `plugin/scripts/prepare.sh` 的 task new / cleanup |
| 无人值守档 | 人闸已经有落点（`mmw-to-spec` 第 7 步用户点头，第 8 步发布 issue 打 `ready-for-agent` 即凭据）。旧 plugin 另有三档值守曲线，过门之后自动放权自主跑；新架构还没有对应的东西，也还不知道要不要 | `plugin/skills/orchestrate/references/control/attendance.md` |
