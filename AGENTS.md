# AGENTS.md — multi-model-workflow 维护协议

本仓库是 Codex 多代理工作流的源码和同步仓库。它的目标不是展示方法论，而是让 Codex 在真实项目里自动完成：

1. 新功能、系统性 bug、系统性改造讨论中的 context capture。
2. 设计文档 review。
3. 计划文档 review。
4. Task Pack 切分、派发和执行。
5. 代码 review 与修复循环。
6. 未知根因调查。
7. 最终意图验证和生产风险 review。
8. 面向项目负责人的业务语言汇报。

后续 agent 进入本仓库时，先按这个目的判断工作是否有效。不要把“文件存在、脚本能跑、安装成功”当成系统已经完整。

## 1. Source / Runtime

本仓库只是源码和储存层。Codex 实际使用的是安装后的 skill 和 agent 配置。

| 层级 | 路径 | 作用 |
| --- | --- | --- |
| Codex skill source | `.agents/skills/orchestrate-discovery/`、`.agents/skills/orchestrate-workflow/`、`.agents/skills/orchestrate-plan-writing/` | Codex workflow skills 的源码真相 |
| Codex agent source | `codex/agents/*.toml` | 自定义 `agent_type` 指令模板 |
| Codex skill runtime | `/Users/cheuklapchan/.agents/skills/orchestrate-discovery`、`/Users/cheuklapchan/.agents/skills/orchestrate-workflow`、`/Users/cheuklapchan/.agents/skills/orchestrate-plan-writing` | Codex 实际可加载的 user-level skills |
| Codex agent runtime | `/Users/cheuklapchan/.codex/agents/*.toml` | Codex 实际可调用的 custom sub-agent |
| Codex hook source | `codex/hooks/*.sh`、`codex/hooks/hooks.json` | user-level hook 的源码真相 |
| Codex hook runtime | `/Users/cheuklapchan/.codex/hooks/multi-model-workflow/`、`/Users/cheuklapchan/.codex/hooks.json` | Codex 实际执行的 user-level hooks |
| Claude plugin source | `plugin/` | Claude Code 兼容源；不作为 Codex 当前设计权威 |

改 Codex 运行行为时，先改 source，再同步 runtime。不要只改 `/Users/cheuklapchan/.agents` 或 `/Users/cheuklapchan/.codex/agents`，也不要只改仓库 source 后忘记同步。

同步命令：

```bash
bash codex/skills/install-orchestrate-workflow.sh --user --apply
bash codex/agents/sync-agents.sh --apply
bash codex/hooks/install-hooks.sh --apply
diff -qr .agents/skills/orchestrate-workflow /Users/cheuklapchan/.agents/skills/orchestrate-workflow
diff -qr .agents/skills/orchestrate-discovery /Users/cheuklapchan/.agents/skills/orchestrate-discovery
diff -qr .agents/skills/orchestrate-plan-writing /Users/cheuklapchan/.agents/skills/orchestrate-plan-writing
for f in code-explorer code-reviewer coding-worker complex-code-explorer complex-coding-worker docs-worker release-reviewer; do
  diff -q "codex/agents/$f.toml" "/Users/cheuklapchan/.codex/agents/$f.toml"
done
diff -q codex/hooks/session-start.sh /Users/cheuklapchan/.codex/hooks/multi-model-workflow/session-start.sh
diff -q codex/hooks/guard-premature-push.sh /Users/cheuklapchan/.codex/hooks/multi-model-workflow/guard-premature-push.sh
```

## 2. Runtime Files

这些文件会直接影响 Codex 行为，按执行文件维护：

- `.agents/skills/orchestrate-workflow/SKILL.md`
- `.agents/skills/orchestrate-workflow/references/*.md`
- `.agents/skills/orchestrate-discovery/SKILL.md`
- `.agents/skills/orchestrate-discovery/references/*.md`
- `.agents/skills/orchestrate-plan-writing/SKILL.md`
- `.agents/skills/orchestrate-plan-writing/references/*.md`
- `codex/agents/*.toml`
- `codex/hooks/*.sh`
- `codex/hooks/hooks.json`

runtime 文件只写会改变 agent 下一步行为的指令：

- trigger / entry router；
- phase 顺序；
- 必读 reference；
- agent routing；
- dispatch contract；
- review / worker contract；
- stop condition；
- finding severity；
- verification gate；
- sync command。

不要写：

- 迁移背景说明；
- “这是从旧 plugin / 某 GitHub skill 吸收来的”这类来源说明；
- “不是某某、不是某某”的大段定位解释；
- 方法名清单；
- 给人看的项目复盘；
- 安装说明、市场说明、README 式介绍；
- 为了证明自己理解而写的概念性段落。

优化 runtime 文件时做信息密度提升，不做能力清空：

- `SKILL.md` 前部优先保留 coordinator loop、硬优先级、phase routing。
- `references/` 保留深水区细节，但入口处压成可执行习惯或检查项。
- `codex/agents/*.toml` 先写角色纪律，再写 role-specific 方法。
- 删除解释性背景，不删除 contract、mockup、verification、risk、routing、feedback loop、TDD、final intent 这些能力。

## 3. 系统完整性

评估这套系统是否“完成”，不能只看安装。必须判断它是否能端到端承接真实项目工作流。

合格标准：

- `orchestrate-workflow` 能从 discovery capture、design、plan、bug feedback、UI/UX feedback 或 existing diff 接管正确入口。
- `orchestrate-discovery` 能把新功能、issue、backlog、现有 PRD、系统性 bug、wrong state、UI/UX 反馈和产品讨论转成可进入 Phase 0a 的 design document；domain ambiguity 必须通过 `grill-with-docs` 对齐项目文档并写回。
- Phase 0a 能审设计文档的完整性、项目一致性、场景边界、合同边界和 UI/mockup 承接关系。
- `orchestrate-plan-writing` 能把已 review 的 design / SPEC / PRD 与 `to-issues` 产出的 vertical large issues / vertical small issues 生成 issue-backed implementation plan；大 issue 对应 plan 一级章节，小 issue 对应 Task Pack。缺 issue 层级时必须回到 `to-issues`，不能自行把候选拆分当正式 pack。
- Phase 0b 能审计划文档的覆盖率、真实路径、可执行性、验收标准、issue -> Task Pack 映射和风险任务。
- Phase A 能把 Task Pack 派给正确 custom agent，实现后做 spec compliance 和 code quality review。
- Phase B 能把所有 pack 合起来审最终 intent，而不是只相信每个 pack 自报完成。
- 生产风险必须追加 `release_reviewer`，但不能替代 baseline `code_reviewer`。
- 未知根因必须先建立 feedback loop，再提出可证伪 hypotheses，再修复。
- worker 必须按 public behavior 做 vertical TDD，不做 horizontal slicing。
- API、Pydantic、DB、JSON、sync、billing、permission、runtime、UI action 和 helper placement 必须走正式 contract boundary。
- 最终汇报必须面向项目负责人说明产品能力、验证证据、残余风险和需要业务决策的事项。

不合格信号：

- 只说“已经安装 / 已经复制”。
- 只在 README 里提到旧 plugin 或 upstream skills，却没有转成具体 runtime 规则。
- skill 里出现长篇解释、历史背景、方法论摘要。
- custom agent TOML 只有泛泛角色描述，没有 review / implementation / diagnosis 的具体 contract。
- review 只审代码，不审 design、plan 和 final intent。
- release-risk review 覆盖掉 baseline review。
- Task Pack 按文件类型横切，而不是按可验证行为纵切。

## 4. 运行主体边界

先判断哪个运行主体会读到哪份文件，再写规则。不要让 custom agent 依赖它看不见的 `SKILL.md`、reference 或历史 plugin 语境。

| 文件 | 读者 | 负责什么 | 禁止什么 |
| --- | --- | --- | --- |
| `.agents/skills/orchestrate-workflow/SKILL.md` | 主线程 coordinator | 入口路由、phase、escalation gate、dispatch、review reception、standard return contract | 假设 custom agent 自动知道本文件 |
| `.agents/skills/orchestrate-workflow/references/*.md` | 主线程 coordinator | phase-specific 检查项、payload 模板、finding 分类、pack / review 规则 | 写成 sub-agent 自动读取的 contract source |
| `.agents/skills/orchestrate-discovery/SKILL.md` | 主线程 discovery owner | 缺 design document 输入的分类、domain alignment、design document 生成或修订 | 生成 plan、拆 Task Pack、派 worker |
| `.agents/skills/orchestrate-discovery/references/*.md` | 主线程 discovery owner | conversation / bug / issue / feedback 输入处理、domain alignment、design contract、自检 | 写成 Phase A execution contract |
| `.agents/skills/orchestrate-plan-writing/SKILL.md` | 主线程 planner | issue-backed plan 生成流程、输入要求、plan 结构、Task Pack 写作规则 | 重新定义 Orchestrate Phase A/B；提供非 Orchestrate execution owner |
| `.agents/skills/orchestrate-plan-writing/references/*.md` | 主线程 planner | issue -> pack 映射、plan 文档合同、自检清单 | 让 worker 直接依赖这些 references |
| `codex/agents/*.toml` | custom agent 自己 | 角色边界、默认方法、项目 overlay、可执行 / 只读纪律、本地 return contract | 引用模糊的 `SKILL.md`；重新定义 Orchestrate phase |
| parent dispatch prompt | 主线程发给 custom agent | 本次 phase、source docs、anchors、risk、verification、return contract | 只发“按 Orchestrate 做”这类隐式要求 |

return contract 只有一套，但必须自足地出现在 custom agent TOML 或 parent dispatch prompt 里。禁止在 agent TOML 写 `Fill the SKILL.md universal return envelope`、`use Orchestrate Workflow SKILL.md envelope` 这类 custom agent 无法定位的句子。

## 5. 当前 Codex 权威

Codex runtime 优先使用真实 `agent_type`，不要把旧 Claude plugin 的 agent 名当成当前系统概念。

| 当前能力 | agent_type / owner |
| --- | --- |
| issue-backed implementation plan generation | `orchestrate-plan-writing` |
| baseline design / plan / pack / final review | `code_reviewer` |
| production-risk supplement | `release_reviewer` |
| ordinary Task Pack / clear implementation finding | `coding_worker` |
| high-risk Task Pack / high-risk repair | `complex_coding_worker` |
| unknown root cause / multi-module investigation | `complex_code_explorer` |
| narrow code location / call-chain question | `code_explorer` |
| low-risk docs cleanup / design / issue draft | `docs_worker` |
| domain / UX / terminology / ownership ambiguity | `orchestrate-discovery` uses `grill-with-docs` |
| bug / error / wrong state | parent uses `diagnose` before patching |
| state machine / interface shape / UI direction | parent uses `prototype` |
| bad test seam / architecture friction / repeated repair | parent uses `improve-codebase-architecture` |

`plugin/` 只作为 Claude Code 兼容源存在。除非用户明确要求维护 Claude plugin，否则不要再从旧 plugin 推导 Codex 行为；更不要把 `workflow-auditor`、`pack-executor`、`root-cause-analyst`、`SendMessage`、`Agent tool`、`codex-rescue` 写进 Codex runtime source。

## 6. Upstream Skills

`orchestrate-discovery` 和 `mattpocock/skills` 是当前 Codex workflow 的前置方法和升级路径，不是附录，也不是历史来源说明。

必须保留的行为：

- 新功能、issue、backlog、现有 PRD、系统性 bug、wrong state、performance regression、UI / UX 反馈、截图反馈、测试反馈、系统性改造或产品讨论：先由 `orchestrate-discovery` 生成或修订 design document，再进入 Phase 0a。
- design 通过 review 后，先由 `to-issues` 形成 vertical large issues 和 vertical small issues，再由 `orchestrate-plan-writing` 生成 issue-backed plan，最后由 `orchestrate-workflow` 接管 Phase 0b、Task Pack、Phase A、Phase B、Phase C。
- `grill-with-docs` 是 Discovery 全程 domain alignment 机制；术语、对象 owner、状态、边界、合同、现有文档不清时高频触发，结论写回 `CONTEXT.md` / domain docs 和 design document。
- bug / error / wrong state / performance regression：在 `orchestrate-discovery` 或 repair flow 内先 `diagnose` 建 feedback loop、症状、hypotheses、regression target，再判断是 design repair 还是 Phase A repair。
- implementation work：`tdd` 转成 public-behavior vertical TDD，禁止 horizontal slicing。
- UI / state machine / interface shape 不确定：`prototype` 只回答决策问题，结论回写 design / plan。
- bad seam、repeated repair、single-adapter、测试面错误：`improve-codebase-architecture` 产生 architecture finding，再回到 Orchestrate gate。
- durable backlog 或跨会话交接：`orchestrate-discovery` 先生成 design document；Phase 0a 通过后由 `to-issues` 生成 issue hierarchy；进入执行前必须由 `orchestrate-plan-writing` 固化成 plan / Task Pack。
- completion proof：最终 gate 必须保留完成前证据纪律，没有验证证据不得声称完成。

禁止做法：

- 在 runtime 文件里列“吸收了哪些 skill”。
- 把外部 skill 整套复制进来。
- 用外部方法替代本系统的 Phase 0 / Phase A / Phase B 主流程。
- 让 worker 遇到 context ambiguity 时直接 patch。

## 7. 修改流程

当用户要求“检查这套系统是否完善”时，先做概念和行为审计：

1. 读 `.agents/skills/orchestrate-workflow/SKILL.md`。
2. 读 `.agents/skills/orchestrate-discovery/SKILL.md`。
3. 读 `.agents/skills/orchestrate-plan-writing/SKILL.md`。
4. 读相关 `references/*.md`。
5. 读 `codex/agents/*.toml`。
6. 对照当前 Codex runtime、Orchestrate 工作流和 upstream engineering skills。
7. 判断每个能力是否已经变成可执行指令。
8. 检查每条指令的 reader 是否正确：parent、discovery、planner、reference、custom agent、runtime script 不能混。
9. 只在发现明确缺口时改 source。
10. 改完同步 runtime 并验证 diff。

不要再把旧 Claude plugin source 当作 Codex 设计依据。只有在维护 `plugin/` 兼容包，或用户明确要求核旧包是否还有未迁移能力时，才读取旧 plugin source；读取后也必须以当前 Codex runtime 为准。

不要一上来检查有没有安装。安装状态只能证明文件复制成功，不能证明系统设计成立。

当用户要求“清理垃圾解释性文字”时，直接扫描 runtime source 和 agent source：

```bash
rg -n "workflow-auditor|pack-executor|root-cause-analyst|codex-rescue|SendMessage|Agent tool|Fill the .*SKILL.md|SKILL.md universal|装饰文档|不纳入 Runtime|来自外部|只写成方法名|不是方法名称|不安装整套" .agents/skills codex/agents
```

发现解释性文字后，优先删除；如果其中含有必要行为，只改写成直接指令。

## 8. 子代理使用

本仓库的工作经常是 prompt / instruction 维护。不要把简单清理委派出去。

可以委派的情况：

- 一个 agent 审 `orchestrate-workflow` skill。
- 一个 agent 审 `orchestrate-plan-writing` skill。
- 一个 agent 审 `codex/agents/*.toml`。
- 一个 agent 对照当前 Codex runtime 找 source / runtime 漂移。

不要委派的情况：

- 只需要删几段解释性文字。
- 用户正在纠正方向，主线程需要直接承担判断。
- 下一步是关键路径，主线程等一个子代理才能继续。
- 问题本质是运行主体边界、source/runtime 权威、或用户指出主线程理解错了系统。

委派时必须明确：

- 不写长篇说明。
- 不改 runtime 以外的文档来假装完成。
- 输出具体缺口和建议 patch。
- 禁止把安装成功当成能力完整。

## 9. 用户沟通

用户不是要看方法论汇报，而是要这套系统真的可用。沟通时：

- 先给结论，再给证据。
- 少讲“我理解了什么”，多讲“我检查了什么、改了什么、同步到了哪里”。
- 用户问概念判断时，不要用文件存在、安装成功或脚本输出回避设计判断。
- 用户要求执行时，直接执行，不停在方案。
- 承认方向错了以后立刻修，不要用新增文档掩盖 runtime 缺口。
- 不要把 README、审计报告、设计文档当成 runtime 能力。
- 用户指出“你没有理解系统”时，先停手读 source、runtime、config 和当前规则；不要马上 patch。
- 回答为什么读某个旧来源时，如果它不是当前权威，必须说明它只是兼容 / 漂移检查，不再用来推导 Codex 设计。

## 10. 同步清单

如果改了 user-level runtime：

```bash
bash codex/skills/install-orchestrate-workflow.sh --user --apply
bash codex/agents/sync-agents.sh --apply
bash codex/hooks/install-hooks.sh --apply
diff -qr .agents/skills/orchestrate-workflow /Users/cheuklapchan/.agents/skills/orchestrate-workflow
diff -qr .agents/skills/orchestrate-discovery /Users/cheuklapchan/.agents/skills/orchestrate-discovery
diff -qr .agents/skills/orchestrate-plan-writing /Users/cheuklapchan/.agents/skills/orchestrate-plan-writing
diff -q codex/hooks/session-start.sh /Users/cheuklapchan/.codex/hooks/multi-model-workflow/session-start.sh
diff -q codex/hooks/guard-premature-push.sh /Users/cheuklapchan/.codex/hooks/multi-model-workflow/guard-premature-push.sh
```

如果改了 agent TOML，还要逐个对比 `/Users/cheuklapchan/.codex/agents/*.toml`。

收尾时报告真实同步结果；不要把脚本输出包装成系统设计已经成立。
