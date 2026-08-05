# Matt Pocock Skills 1.2.2 方法保真升级 spec

> 本 spec 来自用户确认的《Matt Pocock Skills 1.2.2 与 MMW 方法保真调查》。术语以 `CONTEXT-MAP.md` 登记的 `docs/context/delivery-workflow.md`、`docs/context/tracker.md`、`docs/context/wayfinding.md`、`docs/context/agent-coordination.md`、`docs/context/review.md`、`docs/context/release-and-closure.md`、`docs/context/host-runtime.md` 和 `docs/context/project-context.md` 为准。

## Problem Statement

MMW 基于 Matt Pocock Skills 改造。上游升级到 1.2.2 后，MMW 的大部分工程主链仍然保真，但 prototype、Wayfinder、ticket 拆分和 agent 文档写作已经偏离上游当前合同。阶段边界、TDD、`/mmw-implement`、`/mmw-release` 和 `/mmw-integrate` 也遗漏了新的步骤或完成判据。继续保留这些偏离会改变上游方法的执行效果，并在 MMW 的 worktree、tracker、审查和发布流程之间形成断点。

上游还新增了若干正式技能。MMW 需要吸收与工程交付直接相连的 `writing-for-agents`、`wizard`、`to-questionnaire` 和 `wait-what`，并明确拒绝不属于仓库交付范围或绑定单一宿主的技能。所有修改必须保留 MMW 已有的报告验证、plan 层、六道审、领域文档、宿主 worktree 和 release 状态机。

## Solution

MMW 按上游 1.2.2 恢复八项方法合同：prototype、Wayfinder、ticket 拆分、agent 文档写作、阶段边界、TDD 与 `/mmw-implement`、`/mmw-release`、`/mmw-integrate`。MMW 同时补齐三处 Grilling 解释性细节。每项改动只做 MMW 工作流所需的宿主、tracker、worktree、领域文档和人工审批关卡适配，不另造方法。

正式实现从 prototype 资产吸收已验证的决定；逻辑 branch 还会把确认过的纯逻辑模块移入正式路径。完整 prototype 继续保存在任务分支的 `docs/prototypes/`。Wayfinder 恢复一会话一张 decision ticket。Ticket 写入 tracker 前增加明确的用户批准。Agent 文档写作迁移到上游当前的 `writing-for-agents`。阶段边界按上游的五步有序决策树执行，并为 Codex、Claude Code 和 Pi 物化真实可用的动作。TDD、`/mmw-implement`、`/mmw-release` 和 `/mmw-integrate` 恢复遗漏的引用、频率、重审和意图边界。

MMW 新增三个辅助技能。`wizard` 处理必须由用户完成的第三方配置和 cutover。`to-questionnaire` 把当前用户无法回答的知识缺口交给真正掌握信息的人。`wait-what` 提供即时的表达纠错入口。这三个技能不进入 `mmw-start` 的工程路由。

## Current State

- Vendored 上游版本是 1.2.2，正式 manifest 发布 25 项技能。调查逐项检查了 25 项正式技能和 10 项未发布或 misc 技能（`docs/research/matt-upstream-1.2.2-mmw-fidelity-audit.md:23-29`、`docs/research/matt-upstream-1.2.2-mmw-fidelity-audit.md:183-188`）。
- Bug 诊断、Research、Domain Modeling、Codebase Design、架构改进、Spec、TDD 主循环、Triage 和双轴 Code Review 的核心方法已经保留，不需要因本轮更新重写（`docs/research/matt-upstream-1.2.2-mmw-fidelity-audit.md:99-108`）。
- Grilling 已恢复设计树、frontier、整轮提问、事实调查、动态重算和共同理解确认，只缺三处用户参与与调查并行的解释性合同（`docs/research/matt-upstream-1.2.2-mmw-fidelity-audit.md:46-56`）。
- 逻辑 prototype 当前固定为 TUI。设计 prototype 会保存在任务分支的 `docs/prototypes/` 并随设计提交。上游当前要求单文件 HTML、free-play、guided walkthrough 和已知初态；上游的分支承载方式不覆盖 MMW 已有的资产流转合同（`mmw/skills/mmw-prototype/SKILL.md:8-10`、`mmw/skills/mmw-prototype/SKILL.md:20-31`、`mmw/skills/mmw-prototype/LOGIC.md:41-61`、`vendor/mattpocock-skills/skills/engineering/prototype/LOGIC.md:35-58`）。
- Wayfinder 当前把 effort 限定为需要多份 spec，并允许一个会话沿 AFK 链连续解决多张 decision ticket。上游入口是超出一次 agent session 且路线不清，一次会话只解决一张 decision ticket，建图时并行 Research 是唯一例外（`mmw/skills/mmw-wayfinder/SKILL.md:3-9`、`mmw/skills/mmw-wayfinder/SKILL.md:35-37`、`mmw/skills/mmw-wayfinder/walking.md:1-3`、`vendor/mattpocock-skills/skills/engineering/wayfinder/SKILL.md:3-13`、`vendor/mattpocock-skills/skills/engineering/wayfinder/SKILL.md:105-116`）。
- Ticket 拆分已经保留 tracer bullet、垂直路径、独立验证、prefactor、blocking edge、frontier 和 expand-contract 例外，但清单展示后会直接写入 tracker。上游要求围绕粒度、blocking edge、合并与拆分迭代到用户批准（`docs/research/matt-upstream-1.2.2-mmw-fidelity-audit.md:80-86`）。
- `writing-great-skills` 仍是旧名称和旧范围。上游 `writing-for-agents` 已扩展到 skill、`AGENTS.md`、`CLAUDE.md` 和 context pointer 文档，并把 skill mechanics 单独披露（`docs/research/matt-upstream-1.2.2-mmw-fidelity-audit.md:110-139`）。
- `mmw-start` 没有阶段边界决策树。上游依次判断 Continue、上下文是否无关、是否需要 portability、是否可 AFK，最后才 compact，并明确说明离开当前会话会把 primary source 降为 secondary source（`docs/research/matt-upstream-1.2.2-mmw-fidelity-audit.md:14-19`、`vendor/mattpocock-skills/skills/engineering/ask-matt/PHASE-BOUNDARIES.md:1-49`）。
- `mmw-tdd` 缺少 interface 未定时读取 Codebase Design 的条款。`mmw-implement` 缺少定期 typecheck、定期运行当前测试、结束运行完整测试套件的频率合同（`docs/research/matt-upstream-1.2.2-mmw-fidelity-audit.md:88-97`）。
- `/mmw-release` 可以在 final 终审后生成修复提交，但当前前置条件只证明曾经终审，没有证明当前 HEAD 就是终审通过的提交（`mmw/skills/mmw-release/SKILL.md:10-19`、`mmw/skills/mmw-release/SKILL.md:53-68`）。
- `/mmw-integrate` 已按双方意图处理冲突，并保留目标不足时停下交用户决定的安全边界，但没有明说不能发明新行为（`mmw/skills/mmw-integrate/SKILL.md:52-60`、`mmw/skills/mmw-integrate/SKILL.md:72-83`）。
- MMW 当前有 23 个工作流技能，以及 `handoff` 和 `writing-great-skills` 两个辅助技能。Claude Code manifest 显式列出每个技能；Pi 与 Codex 使用目录入口（`README.md:54-69`、`mmw/.claude-plugin/plugin.json:7-44`、`mmw/package.json:8-16`、`mmw/.codex-plugin/plugin.json:19-20`）。
- 共享技能源会物化到 Pi、Claude Code 和 Codex。物化器可以把完整的宿主动作块展开为不同宿主的真实动作（`mmw/cli/lib/materialize_skills.py:247-332`）。
- 产品版本当前为 0.9.0。版本分布在 Codex manifest、Claude Code manifest、根 Claude marketplace 和 Pi package（`mmw/.codex-plugin/plugin.json:1-4`、`mmw/.claude-plugin/plugin.json:1-5`、`.claude-plugin/marketplace.json:9-31`、`mmw/package.json:1-4`）。
- 根架构图仍展示旧辅助技能和 Wayfinder 链。Wayfinder SVG 也展示旧链式调度（`mmw-skill-map.html:470`、`mmw-skill-map.html:747`、`README.md:225`）。

复用现有技能源、宿主动作物化器、tracker 命令、结果分支验证、报告验证、六道审、prototype 资产目录和 release 状态机。新增阶段边界宿主动作，因为现有机械层没有对应的完整行为。

## User Stories

1. 作为 MMW 用户，我要用双击可运行的 HTML 走查状态模型，以便非开发者也能重复执行 free-play 和 guided walkthrough。
2. 作为 MMW 用户，我要让已经走查的 prototype 作为重要资产进入任务历史，以便 spec、ticket、plan、审查和实现都能读取同一份出处。
3. 作为 Wayfinder 用户，我要让一个会话只解决一张 decision ticket，以便每项决定保持清楚的上下文边界和粒度。
4. 作为 Wayfinder 用户，我要在一项工作超出一次 agent session 且路线不清时进入 map，以便单一 spec 数量不会错误限制入口。
5. 作为 spec 负责人，我要在 tracer bullet ticket 写入 tracker 前检查粒度、blocking edge、合并和拆分，以便 tracker 不会固化错误切片。
6. 作为 MMW 维护者，我要使用上游当前的 Agent 文档写作方法，以便 skill、规则文件和 context pointer 文档遵守同一套信息层级和 cache 原则。
7. 作为主 agent，我要只在阶段边界按固定顺序决定继续、丢弃上下文、handoff、派 subagent 或 compact，以便保留 primary source 并减少无谓上下文切换。
8. 作为 `worker`，我要在 interface 尚未定形时读取 `/mmw-codebase-design`，并在实现过程中定期运行类型检查和当前测试、结束时运行完整测试套件，以便 TDD 不替代接口设计且错误能尽早暴露。
9. 作为发布负责人，我要确保交付包对应的 HEAD 经过 final 终审，以便 release 自愈提交不能绕过审查。
10. 作为集成负责人，我要只根据双方 primary source 和既定目标解冲突，以便合并过程不会发明新行为。
11. 作为需要用户完成第三方设置的 agent，我要使用 `wizard` 生成带确认、秘密输入和持久化落点的脚本，以便用户能安全重复执行人工步骤。
12. 作为缺少他人专业知识的用户，我要使用 `to-questionnaire` 生成一份针对知识持有者的问卷，以便异步补齐决定所需事实。
13. 作为没有听懂上一条回复的用户，我要让 agent 用简化技术英语和 canonical 术语重新说明，以便讨论能回到共同语言。
14. 作为三个宿主的用户，我要获得语义一致的技能和真实可用的宿主动作，以便任何宿主都不会出现流程断点。

## Implementation Decisions

1. 以 vendored 1.2.2 的对应技能为方法论唯一上游。实现只允许调整 MMW 的 worktree、tracker、报告验证、领域文档、人工审批关卡和宿主动作。每项删改都要能指向已确认的 MMW 合同。原型免除：该决定可由上游文档和当前仓库规则判定，不需要用户判断。
2. 逻辑 prototype 改成一个自包含 HTML 文件。文件使用内联 HTML、CSS 和 JavaScript，无框架、bundler 或服务器。页面同时提供 free-play、按 tab 分组的 guided walkthrough、每个场景的自然语言说明、真实动作按钮和启动场景时的已知初态重置。逻辑仍隔离为纯 reducer、状态机、函数集或持有状态的模块。原型免除：产物形态由上游文档明确规定，不需要用户判断。
3. 设计 prototype 保留“一轮一个可回答问题”、最小可运行、默认内存状态、少打磨、完整状态可见、真实边界、用户走查、逐轮证据和结论回填。最小脚本和外部系统 Evidence 分支保持现有职责。原型免除：该决定照搬现有 MMW 合同。
4. 每项设计 prototype 继续保存在任务分支的 `docs/prototypes/<slug>/`。目录保存全部源码、变体、运行说明、逐轮记录和证据，并随本轮结果提交。`/mmw-to-spec`、`/mmw-to-tickets`、`/mmw-to-plan`、审查和 `worker` 继续通过仓库路径消费同一资产。结果分支只提供 worktree 隔离和验证，验收通过后仍按现有合同集成回任务分支。原型免除：该决定来自 MMW 已形成闭环的资产流转合同。
5. Wayfinder prototype 的结案评论指向任务分支内的 prototype 资产路径。Grilling 或直接调用在 spec 产生前完成 prototype 时，资产和逐轮结论已经存在于 `docs/prototypes/<slug>/README.md`；`/mmw-to-spec` 直接读取并吸收。`/mmw-to-tickets` 把相关资产路径和决定含量传给消费该决定的 tracer bullet ticket。主分支长期保留 prototype、verdict、验收标准和视觉合同。原型免除：该决定来自 MMW 的 tracker 与资产消费链。
6. Prototype 阶段只形成并提交资产、走查证据和已验证决定，不提前完成正式集成。实现阶段把已确认的纯逻辑模块移入正式 module，并由同一 ticket 的 TDD 证明行为。HTML shell 不进入生产模块。UI 按仓库规范重写；prototype route、变体和切换器在回填时归档到 `docs/prototypes/<slug>/`，不留在正式路由。原型免除：该决定同时保留上游“纯逻辑模块可移入、HTML 外壳可丢弃”的合同和 MMW 的 spec-to-ticket 实现顺序。
7. Wayfinder 的 effort 统一定义为“超出一次 agent session，且从当前状态到 destination 的路线仍不清楚”。是否最终形成一份或多份 spec 不再作为入口条件。保留 destination、map、decision ticket、frontier、fog of war 和提前提取独立 spec。原型免除：该决定由上游文档和现有 MMW map 合同判定，不需要用户判断。
8. Wayfinder 的工作单位改成“一会话一张 decision ticket”。建图会话不手工解决 ticket。解决任一非 `wayfinder:research` ticket 后，本会话完成回填并停止，不沿新 frontier 继续。建图时可并行派发多张 `wayfinder:research` ticket；每个调查者仍只负责一张 ticket，主 agent 在同一建图会话验证报告并写入各自评论。删除“链”这一调度概念及其领域定义。原型免除：该决定由上游完成判据明确规定，不需要用户判断。
9. `/mmw-to-tickets` 在写入 tracker 前展示 ticket、blocking edge 和执行顺序。用户可以按粒度、blocking edge、合并和拆分提出修改。只有用户明确批准后才创建 ticket。该确认是 ticket 拆分人工审批关卡，不替代共同理解或 spec 定稿的人工审批关卡。原型免除：该决定由上游 tracker 流程明确规定，不需要用户判断。
10. `writing-great-skills` 由 model-invoked 的 `writing-for-agents` 取代，不保留 alias。新正文覆盖所有 agent 消费文档，保留 context pointer、context load、cognitive load、information hierarchy、completion criterion、leading word、environment source of truth、cache、pruning 和 no-op。Skill 专有的 frontmatter、invocation、按 invocation 拆分和 router skill 进入单独的 `SKILL-MECHANICS.md`。MMW 只增加现有项目写作规范和物化边界，不另写第二套方法。原型免除：该决定采用上游当前参考，不需要用户判断。
11. 阶段边界规则作为 `mmw-start` 的披露 reference 保存。所有工作流技能在执行 `## 下一步` 的 phase transfer 前读取同一 reference，不复制五步方法。规则只在阶段边界应用；阶段中继续当前步骤，或把剩余 AFK 工作派给 subagent。原型免除：该决定可由上游文档和当前技能结构判定，不需要用户判断。
12. 阶段边界按固定顺序判断：先判断当前会话能否继续；再判断现有上下文是否与下一阶段无关；再判断是否需要跨 harness、目录、同事或中途支线的 portability；再判断下一阶段是否可 AFK；最后才 compact。每一步都说明 primary source 转成 secondary source 的信息损失。原型免除：该顺序由上游决策树明确规定，不需要用户判断。
13. 阶段边界的共享正文使用完整宿主动作块物化。Continue 继续当前任务。Portability 调用 `handoff`。AFK 使用宿主已有的 subagent 或后台 Worktree 任务。清空或 compact 能由 agent 执行时直接执行；只能由用户触发时，停在边界并给出一条精确宿主操作，等用户完成后恢复；agent 与用户都无法触发时，不执行 phase transfer。此时 Continue 仍安全就继续，否则停下并报告宿主能力 blocker。MMW 不声称已经清空或压缩，也不静默用 handoff 替代。原型免除：该决定可由宿主能力和 MMW 物化规则判定，不需要用户判断。
14. TDD 在测试 seam、module depth 或 interface 暴露面尚未确定时读取 `/mmw-codebase-design`，只使用其 module、interface、seam、adapter 和 depth 词汇帮助澄清边界；已由 spec 决定的 seam 不重新设计。原型免除：该决定由上游文档和现有 spec 责任边界判定，不需要用户判断。
15. `/mmw-implement` 继续让目标仓库的 `TESTING.md` 决定命令和测试层次，并恢复上游原文的执行频率：实现过程中定期运行类型检查和当前测试文件，全部实现完成后运行一次完整测试套件。“定期”表示这些命令与实现循环交错，不能全部推迟到结束；不把上游的判断改成固定时间或固定次数。`worker` 报告按发生顺序列出命令与结果。仓库没有对应命令时明确报告不适用，不编造命令。原型免除：该决定由上游文档和仓库测试入口判定，不需要用户判断。
16. 每轮 final 终审记录固定点和被审 HEAD；只有没有 `accepted` 的通过轮次才登记终审提交。固定点限定 diff 范围；终审提交是该轮实际审查并通过的被审 HEAD。`/mmw-release` 在开始时读取终审提交。任何 release 自愈、人工修复或重新出包过程只要改变 HEAD，就立即使该凭据失效，并移交 final 终审。新 HEAD 终审通过后从 `/mmw-release` 前置检查重新开始。包的 `source_commit` 一致仍是必要条件，但不能替代终审。原型免除：该决定可由 review 记录、Git 和 release 状态判定，不需要用户判断。
17. `/mmw-integrate` 解每个冲突时只使用双方提交、issue、spec 和既定集成目标中的行为。兼容行为都保留；不兼容行为按既定目标取舍；任何合成都不得发明新行为。用户取消或现有目标不足以决定取舍时，保留 MMW 的安全 abort 和停止出口。原型免除：该决定由上游文档和现有安全边界判定，不需要用户判断。
18. Grilling 补充三项解释性合同：用户可以按编号回答整轮；“不知道”、指出范围漂移和推回不合适的问题都是有效回答；开问前的事实调查只暂停依赖该事实的 frontier，其余问题继续。设计树、动态重算和共同理解人工审批关卡不变。原型免除：该决定由上游文档和当前技能正文判定，不需要用户判断。
19. 新增 model-invoked 的 `wizard`。它只处理 agent 无法代办的人工作业。生成前读取仓库并向用户展示步骤、值来源、写入位置和 secret 属性，取得确认后才生成。脚本实现继续使用上游模板的 `stage` 函数，不把该代码标识符定义成 MMW 领域术语。模板提供进度、URL 打开、秘密输入、幂等环境变量写入、CI secret、不可逆动作确认和总结。脚本默认临时，用户要求可重复路径时才进入仓库。原型免除：该决定采用上游已有模板和步骤，不需要用户判断。
20. 新增 user-invoked 的 `to-questionnaire`。它只采访“发给谁”和“需要拿回什么”，再生成按重要性排序、每题一个意图、有回答占位的 discovery questionnaire。它可以作为 Grilling 因当前用户不掌握事实而阻塞时的出口；答案回来后仍回 Grilling 建立共同理解。原型免除：该决定采用上游现有文档合同，不需要用户判断。
21. 新增 user-invoked 的 `wait-what`。它要求 agent 补充必要上下文，使用简化技术英语，并遵守目标仓库 `AGENTS.md` 指向的 canonical 术语。它不写文件，不进入工程交付路由。原型免除：该决定采用上游当前正文并按现有领域规则定位术语，不需要用户判断。
22. 不吸收 `teach`、`grill-me`、`claude-handoff`、`loop-me`、`setup-ts-deep-modules`、文章写作技能和 misc 专项工具。它们分别超出仓库工程交付范围、重复 repo 内主流程、绑定单一宿主或属于一次性专项能力。原型免除：该决定来自逐项范围调查，不需要用户判断。
23. 所有改动从共享技能源生成 Pi、Claude Code 和 Codex 产物。Claude Code 显式 manifest 加入新技能并移除旧技能。README 同步工作流与辅助技能说明。根架构图和 Wayfinder SVG 同步 prototype 资产合同、阶段边界、ticket 拆分人工审批关卡、一会话一 ticket 和新增辅助技能。原型免除：该决定照搬现有发布合同。
24. 领域文档与流程同时更新。交付工作流登记共同理解、spec 定稿和 ticket 拆分三个不同的人工审批关卡，并明确 prototype 资产归属。Wayfinding 把 effort 改为“超出一次 agent session 且路线不清”，删除“链”及其所有权。审查登记与固定点不同的终审提交。Context Map 的 Owns 列同步上述所有权。每个概念只在 owning leaf 定义，其余 leaf 使用权威引用。原型免除：该决定照搬现有领域文档合同。
25. 发布版本统一提升为 0.10.0。该版本表示方法合同、辅助技能集合和宿主物化都发生兼容性可见变化。Codex manifest、Claude Code manifest、根 Claude marketplace 的插件版本和顶层版本，以及 Pi package 同步更新。原型免除：该决定可由现有版本合同判定，不需要用户判断。
26. 实施按四个原子主题提交：核心 P0 保真修复；阶段边界与 P1/P2 闭环；新增辅助技能；宿主物化、文档、架构图和版本。每个主题完成后检查共享源与三宿主产物。原型免除：该决定只改变内部提交结构，不改变用户可见行为。

## Failure Paths

| 失败 | 什么触发 | 谁捕获 | 用户看到什么 | 系统做什么 | 对应哪条验收 |
| --- | --- | --- | --- | --- | --- |
| prototype 资产没有进入任务分支 | 走查后只留下会话记录或结果分支 | 主 agent、`/mmw-to-spec`、final 终审 | 点名缺少的资产与证据 | 不结束回填，不删除结果 worktree | `docs/prototypes/<slug>/` 可从任务分支读取 |
| prototype 资产路径失效 | spec、ticket、plan 或 task 指向不存在的产物 | `/mmw-to-spec`、`/mmw-to-tickets`、审查者、`worker` | 点名失效路径 | 停止消费该决定，不猜选中版本 | 每个引用可在当前任务提交读取 |
| prototype 结果未经验证 | `prototype-worker` 报告与分支、HEAD 或基点不符 | 主 agent | 显示报告值与实际值 | 不集成结果分支 | 结果验证先于资产进入任务分支 |
| prototype 临时代码残留正式路由 | 回填后应用仍包含切换器、落选变体或 prototype route | 主 agent、final 终审 | 点名残留路径 | 完成归档和清理后再推进 | 正式路由不含 prototype 壳，资产目录内容完整 |
| Wayfinder 会话继续第二张非 `wayfinder:research` ticket | 一张 ticket 已完成并解锁下一张 | `/mmw-wayfinder` | 报告本会话已完成的 ticket 和新 frontier | 停止本会话，等待另一个会话认领 | 每个非 `wayfinder:research` 会话只关闭一张 ticket |
| Ticket 未经批准写入 | 用户尚未明确同意清单 | `/mmw-to-tickets` | 显示待确认清单 | 不调用 tracker 创建命令 | Ticket 创建记录晚于批准消息 |
| 宿主动作被伪造 | 物化正文声称执行宿主不存在的 clear 或 compact | 物化检查、项目一致性审 | 点名宿主和虚假动作 | 物化失败或修正文案 | 三宿主正文只包含真实能力 |
| 阶段边界动作不可用 | 决策树选中的 clear 或 compact 既不能由 agent 执行，也不能由用户触发 | 阶段边界宿主动作 | 显示缺失能力和未执行的 phase transfer | Continue 安全时继续，否则停在边界 | 不产生虚假 handoff、clear 或 compact 状态 |
| 实现阶段缺少测试入口 | 目标仓库没有类型检查、当前测试或完整套件命令 | `worker`、主 agent | 分项报告不适用及仓库证据 | 运行存在的层次，不编造命令 | 报告列出每层实际命令或不适用原因 |
| `/mmw-release` 后 HEAD 未重审 | 出包期间生成新提交 | `/mmw-release` 状态机、主 agent | 显示旧终审提交与新 HEAD | 停止交付并移交 final 终审 | 交付 HEAD 等于终审提交 |
| 冲突需要新行为才能解决 | 双方意图和既定目标都没有答案 | 主 agent | 显示冲突位置和两边意图 | 安全 abort 或停止让用户决定 | 集成记录不含新发明行为 |
| 新技能缺少配套资产 | `wizard` 缺模板，`writing-for-agents` 缺 `SKILL-MECHANICS.md` | 物化检查、manifest 检查 | 点名缺失文件 | 发布失败 | 每个新增技能目录完整物化 |
| 宿主产物漂移 | 共享源与任一物化目录不一致 | 技能物化检查、Codex runtime 检查 | 显示具体宿主和文件 | 不提交发布版本 | 全宿主物化检查通过 |
| 版本入口不一致 | 任一 manifest 或 package 保留旧版本 | JSON 检查、人工 diff 检查 | 显示不一致字段 | 不发布 | 五个版本字段均为 0.10.0 |

## Testing Decisions

| Seam | 验证什么行为 | 为什么是这一层 |
| --- | --- | --- |
| 共享技能与对应上游 reference 的语义对照 | 八项合同、三项 Grilling 细节和四项新增技能逐条保留上游步骤、解释和完成判据 | 方法保真无法由机械文本 diff 判断，必须在源级审查语义 |
| 临时 Git 仓库中的 prototype 资产流程 | 结果验证、任务分支集成、逐轮证据、资产路径传递、临时代码归档和正式实现延后 | 这是 prototype 与 MMW worktree、spec、tracker 和 Git 的真实交界 |
| 临时 tracker 或测试 issue 上的 Wayfinder 流程 | effort 入口、建图不解票、一会话一 ticket、并行 `wayfinder:research` 例外、回填后停止、frontier 保留 | 这是 Wayfinder 调度方法的最高稳定边界 |
| 临时 tracker 或 dry-run 上的 ticket 拆分 | 写入前可修改粒度、blocking edge、合并与拆分，未批准零写入，批准后才创建 | 这是新增人工审批关卡的 tracker 写入边界 |
| 三宿主阶段边界物化正文 | 五步顺序一致，Continue 优先，handoff 与 AFK 可执行，clear 和 compact 不虚构；能力缺失时出口确定 | 宿主差异只应存在于完整动作块的生成结果 |
| `worker` task 和结果报告 | `/mmw-codebase-design` 条件引用；类型检查与当前测试在实现过程中交错出现；结束运行完整套件 | 这是 `/mmw-implement` 与 TDD 执行合同的消费边界 |
| `/mmw-release` 的终审提交与最终 HEAD | 无新提交时继续出包；任何新提交使审查失效；重审后恢复；交付记录对应同一终审提交 | 这是 final 终审与 release 状态机之间的断点 |
| 冲突 fixture 与集成记录 | 兼容意图合并、不兼容意图按目标取舍、无依据时停止、从不发明新行为 | 这是 `/mmw-integrate` 的行为边界 |
| 新增辅助技能目录与 invocation 元数据 | `writing-for-agents` 和 `wizard` 可由模型触发；`to-questionnaire` 和 `wait-what` 只能由用户触发；配套 reference 和模板齐全 | invocation 是技能是否按上游方式工作的公开合同 |
| `wizard` 临时脚本静态走查 | `bash -n`、ShellCheck、所有值的来源和落点、secret 输入、幂等写入、CI 名称、不可逆动作确认 | 上游明确禁止 agent 端到端代用户运行，静态走查是最高安全 seam |
| `to-questionnaire` 临时产物走查 | 收件人和信息缺口全部进入目的、上下文和单意图问题；问题按重要性排序并有回答占位 | 这是用户实际交给知识持有者的公开文档边界 |
| `wait-what` 三宿主 smoke | 对一条缺上下文且术语混乱的回复重新说明，并使用目标仓库 canonical 术语 | 这是该短技能唯一的用户可见行为 |
| 技能物化和 Codex runtime 检查 | Pi、Claude Code、Codex 产物与共享源一致，宿主动作全部展开 | 这是三宿主发布的现有稳定 seam |
| Manifest、README、领域文档和架构图静态检查 | 技能集合、数量、名称、五个版本字段、canonical 术语、流程图与运行行为一致 | 这些是用户、agent 和宿主发现合同的发布入口 |

仓库不保留自动化测试套件。实现时使用临时仓库和测试 issue 验证行为，并按根 `TESTING.md` 运行 ShellCheck、JSON 格式检查、`git diff --check`、全宿主技能物化检查和 Codex runtime 物化检查。真实 tracker 写入只使用测试 issue 或 dry-run；不得污染正式 issue。

## Contract Boundaries

| 边界 | 归属方 | 提供方 | 消费方 | 合同 | 登记与验证 |
| --- | --- | --- | --- | --- | --- |
| 上游方法 | Matt Pocock Skills | Vendored 1.2.2 技能与 reference | MMW 共享技能源 | 方法论、步骤、解释和完成判据 | 源级语义对照与两道 spec 审查 |
| MMW 工作流适配 | MMW | worktree、tracker、报告验证、领域文档、人工审批关卡 | 共享流程技能 | 不改变上游意图的承载与关卡 | 项目一致性审与真实流程验证 |
| prototype 资产 | 当前任务分支 | `docs/prototypes/<slug>/` 下的源码、证据、问题和 verdict | spec、ticket、plan、审查者、`worker` | 当前任务提交可读取；完整资产长期保留；正式实现吸收已验证决定，逻辑 branch 的纯模块移入正式代码 | 结果验证、仓库路径解析和 final 终审 |
| 阶段边界语义 | `mmw-start` | 单一披露 reference | 所有流程技能 | 五步有序决策树 | 每个 phase transfer 的 pointer 与源级审查 |
| 阶段边界宿主动作 | MMW 物化器 | Codex、Claude Code、Pi 的完整动作块 | 对应宿主技能 | 只描述宿主真实能力 | 三宿主物化正文检查 |
| Ticket 创建 | `/mmw-to-tickets` | 用户批准和 ticket 清单 | issue tracker | 批准前零写入，批准后按 blocking edge 创建 | 测试 issue 或 dry-run |
| 终审提交 | final 终审 | 该轮实际审查并通过的被审分支 HEAD | `/mmw-release` | 最终交付 HEAD 必须等于有效终审提交；与限定 diff 范围的固定点分开登记 | 审查记录、release 前置检查和交付记录 |
| Canonical 领域术语 | 交付工作流、Wayfinding、审查 owning leaf | 人工审批关卡、prototype 资产、effort、终审提交 | 全部流程技能和角色 | 一个概念只在 owning leaf 定义；Context Map 登记所有权 | `mmw domain check`、项目一致性审和静态 diff |
| 新增技能 invocation | 各技能 frontmatter | manifest 与宿主 skill loader | 用户与模型 | model-invoked 或 user-invoked 与上游一致 | 目录、manifest 和物化检查 |
| 产品版本 | MMW 发布入口 | 五个版本字段 | Codex、Claude Code、Pi 用户 | Codex manifest、Claude Code manifest、Claude marketplace 插件版本、Claude marketplace 顶层版本和 Pi package 全部为 0.10.0 | JSON 检查和静态 diff |

## Release Risk

prototype 继续作为任务分支中的重要资产。风险在于临时 route、切换器或 HTML 外壳被误当成正式实现。回填必须同时完成两件事：把完整产物归档到 `docs/prototypes/<slug>/`，并从正式应用路径撤掉 prototype 壳。正式实现只在后续 ticket 中进行；逻辑 branch 移入已确认的纯逻辑模块，UI branch 按视觉合同重写。

Ticket 拆分新增人工审批关卡，会让全自动交付在写入 tracker 前多一次停顿。这是恢复上游方法所需的有意变化。共同理解、spec 定稿和 ticket 拆分三个关卡分别批准不同产物，互不替代。

阶段边界涉及宿主能力差异。共享语义保持一致，宿主动作必须诚实。某个宿主只能由用户触发 clear 或 compact 时，流程停在边界等用户完成。Agent 与用户都无法触发时，MMW 不执行 phase transfer；Continue 安全时继续，否则报告 blocker。该限制不能绕过现有 task、handoff 或 subagent 合同。

辅助技能集合和名称发生变化。`writing-great-skills` 不保留 alias，因此明确调用旧名会失败。README 和架构图必须同步新名称。版本提升到 0.10.0。正式安装、推送和发布仍需用户另行授权。

## Out of Scope

- 不重写已经充分保真的 Bug 诊断、Research、Domain Modeling、Codebase Design、架构改进、Triage、Spec 和 Review 方法。
- 不删除 MMW 的报告验证、plan 层、六道审、Context Map/leaf、Worktree 结果验证、Retrieval、Closing 或 Release 状态机。
- 不迁移或删除历史 prototype 资产；历史产物与新产物都继续按 `docs/prototypes/` 资产合同解释。
- 不吸收 `teach`、`grill-me`、`claude-handoff`、`loop-me`、`setup-ts-deep-modules`、文章写作技能或 misc 专项工具。
- 不新增与 `mmw-start` 并列的工程路由入口。新增技能保持辅助技能身份。
- 不推送分支、不正式发布 plugin，也不安装 0.10.0 到用户运行时；这些动作需要后续明确授权。
