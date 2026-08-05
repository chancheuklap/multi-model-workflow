# Matt Pocock Skills 1.2.2 与 MMW 方法保真调查

## 结论

当前 MMW 已经充分吸收上游大部分工程主链。Bug 诊断、领域建模、codebase design、架构改进、research、spec 综合、tracer bullet 主体、TDD 主循环、triage 和双轴代码审查的核心方法均在。

这次上游更新仍暴露出八项需要修改的合同。其中四项会直接改变方法效果，应优先处理：

1. `/mmw-prototype` 的逻辑原型仍是 TUI。上游已改为单文件可分享 HTML，并要求 free-play、guided walkthrough 和可重复初态。MMW 把原型作为 `docs/prototypes/` 下的重要资产长期保存；这是 MMW 的正式产物流转合同，不改变 prototype 的探索方法，也不能被上游的 Git 分支约定覆盖。
2. `/mmw-wayfinder` 把“一次会话最多解决一张 decision ticket”放宽为同一 AFK 链连续处理多张 ticket。仓库没有解释这个偏离。它改变了 decision ticket 的上下文隔离和粒度。
3. `/mmw-to-tickets` 删除了发布前的用户批准。上游要求围绕粒度、blocking edge、合并和拆分持续迭代，直到用户批准；MMW 当前明确“亮完就往下走”。
4. MMW 仍保留旧版 `/writing-great-skills`。上游已将它改名并重构为 model-invoked 的 `/writing-for-agents`，范围扩展到 skills、`AGENTS.md`、`CLAUDE.md` 和被 context pointer 引用的 agent 文档，并加入 environment-as-source-of-truth 与 cache 方法。

另外四项应跟随修正：

5. `/mmw-start` 没有承接上游新增的 phase-boundary 决策树。MMW 也没有其他 active skill 说明 Continue、清空上下文、handoff、subagent 和 compact 的有序取舍，以及 primary source 变成 secondary source 的代价。
6. `/mmw-tdd` 没有承接“interface 形状本身未定时，读取 `/mmw-codebase-design` 作为词汇参考”的新条款。`worker` 合同也没有明确保留上游“定期 typecheck、定期运行当前测试文件、结束时运行完整测试套件”的频率。
7. `/mmw-release` 能在 final 终审后生成修复提交，但成功判据只检查出包 stage，没有要求新 HEAD 重走 final 终审。这会让交付 commit 不再是终审过的 commit。
8. `/mmw-integrate` 已按双方意图解冲突，但没有明文保留上游“不能发明新行为”。MMW 允许在用户取消或既有目标无法决定取舍时 abort，这部分有安全和责任边界依据，可以保留。

当前 `main` 已经完成 Grilling 的主要恢复：设计树、frontier、整轮提问、事实调查、动态重算、无固定轮数上限和共同理解确认都已进入技能源和物化产物。该部分无需推倒重做，只需补回少量解释性合同。

## 调查基线

- 当前 vendored 上游版本是 `1.2.2`，见 `vendor/mattpocock-skills/.claude-plugin/plugin.json:1-4`。
- 当前 vendored 上游提交是 `8b36d4fb`。subtree 合入提交是 `1dc804a2`，更新范围为 `0986ebaf..8b36d4fb`。
- 本轮方法正文的主要变化发生在更早一段 `2ab95809..0986ebaf`。最后一段 `0986ebaf..8b36d4fb` 只修正 `writing-for-agents` 的 Codex model invocation 元数据。
- 上游当前 manifest 发布 25 项技能，见 `vendor/mattpocock-skills/.claude-plugin/plugin.json:21-47`。
- 当前 `main` 已通过 `aad71d6f` 恢复 Grilling 与 Domain Modeling 合同，并通过 `0776cde6` 对齐相关领域术语。

## 必须修改的合同

| 优先级 | 范围 | 当前问题 | 应恢复的上游合同 | MMW 适配边界 |
| --- | --- | --- | --- | --- |
| P0 | Prototype | 逻辑原型固定为 TUI；缺少 guided walkthrough | 单文件 HTML；非开发者双击运行；free-play；按 tab 的场景；每个场景重置已知初态；纯逻辑模块可移入正式代码；HTML 外壳不进入生产代码 | 保留 MMW 的一轮一问题、用户走查、逐轮证据、结论回填和 `docs/prototypes/` 长期资产合同；后续 ticket 把已确认的纯逻辑模块移入正式路径并补 TDD，不新增 prototype 分支 |
| P0 | Wayfinder | 一次会话可沿 AFK 链连续解决多张 decision ticket | 一次会话只解决一张 decision ticket；建图时并行 research ticket 是唯一例外 | 保留 claim、frontier、worktree、报告验证和 map 集成；删除“链可连续燃尽多张 AFK ticket”的调度扩展 |
| P0 | Ticket 拆分 | 清单展示后直接发布 | 询问粒度、blocking edge、是否合并或拆分；迭代到用户批准后才发布 | MMW 可把它定义为 ticket 拆分人工审批关卡，或至少恢复明确的发布前确认；不能继续采用静默默认发布 |
| P0 | Agent 文档写作 | 旧名、旧范围、旧结构、user-invoked | 改为 `writing-for-agents`；model-invoked；覆盖所有 agent 消费文档；将 skill mechanics 单独披露；加入 cache | 保留 MMW 宿主物化规则与项目写作规范；更新 manifest、技能引用和三套物化产物 |
| P1 | Phase boundary | 主流程只路由任务，不判断上下文应继续、清空、移交、派发还是压缩 | 只在 phase boundary 判断；先判断 Continue，再判断上下文是否无关、是否需要 portability、是否 AFK，最后才 compact | 不伪造宿主不存在的 `/clear` 或 `/compact`。把五个语义映射成宿主动作；Codex、Claude Code、Pi 分别物化 |
| P1 | TDD 与 implement | 缺少 interface 未定时的 codebase-design reference；缺少测试频率 | interface 形状未定时读取 codebase-design；定期 typecheck、定期跑当前测试、结束跑完整套件 | `TESTING.md` 继续决定命令和仓库事实；共享技能决定执行频率和完成判据 |
| P1 | Release | final 终审后可能产生新提交，最终 HEAD 未重审 | 交付前代码必须经过实现后的 review | 任一 P1 自动修复或主 agent 修复改变 HEAD 后，重新进入 final 终审；只重新跑 stage 不够 |
| P2 | Integrate | 缺少“不发明新行为”的显式边界 | 只从双方 primary source 和既定集成目标解析意图 | 保留 MMW 的安全 abort：用户取消或既有目标不足以决定时停止，不强行解决 |

## 关键方法对照

### Grilling

上游当前要求设计树、frontier、整轮编号提问、整轮后重算，以及只暂停依赖正在调查事实的下游问题。MMW 已在 `mmw/skills/mmw-grilling/SKILL.md:32-81` 保留这些核心合同。

还应补三处解释性细节：

- 明说用户可以按编号回答整轮。
- 明说“不知道”、指出范围漂移和推回不合适的问题都是有效回答。
- 开问前启动的现状调查也只暂停依赖该事实的问题；其余 frontier 可以继续。

这些细节不会改变 MMW 的领域文档、调查验证和共同理解人工审批关卡。

### Wayfinding

MMW 已保留 destination、map、decision ticket、native blocking、frontier、fog of war、`Not yet specified`、`Out of scope`、claim、resolution comment，以及 Grilling、Prototype、Research、Task 四类 ticket。出处集中在 `mmw/skills/mmw-wayfinder/map-anatomy.md`。

MMW 的两项扩展有充分工作流依据，可以保留：

- Research 报告由主 agent 验证后写入 ticket 评论，再关闭 ticket。该行为对应 MMW 的报告验证责任。
- map 可以提前切出一份不再受剩余 fog 影响的 spec。该行为服务 MMW 的多 spec effort 和并行交付。

需要修正两处：

- 上游的入口判据是“超出单次 agent session，且路线仍看不清”。MMW 当前把 effort 限定为“必须拆成多份 spec”，却又保留“一个决定或一次就地改动也可成为 destination”的上游例子。应统一入口定义，避免同一技能内部自相矛盾。
- `docs/context/wayfinding.md:23-25` 把链定义为一次会话连续处理的对象。上游当前以单张 decision ticket 为会话单位。领域定义和 walking 流程应一并调整。

### Prototype

MMW 保留了一轮一个可回答问题、最小可运行、默认内存状态、少打磨、状态可见、用户走查和回填。这些都是有效增强。

MMW 当前 `mmw/skills/mmw-prototype/LOGIC.md:41-61` 指定 TUI。上游 `vendor/mattpocock-skills/skills/engineering/prototype/LOGIC.md:35-58` 指定单文件 HTML、free-play 和 guided walkthrough。这里不能按“宿主适配”解释，因为产物面向用户，选择 TUI 会直接降低非开发者的可运行性和场景可重复性。

MMW 当前 `mmw/skills/mmw-prototype/SKILL.md:8-10,51-71` 把原型定义为 `docs/prototypes/` 下的重要资产。上游 `vendor/mattpocock-skills/skills/engineering/prototype/SKILL.md:19-26` 要求 prototype 按 throwaway 约束编写，并保留为可追溯 primary source。两边对保留 primary source 的意图一致，只是 Git 承载位置不同。逻辑 branch 还有一项更强合同：HTML 外壳可丢弃，纯逻辑模块必须保持可移植，并在正式实现时移入真实 module。MMW 的目录、spec、ticket、plan 和 closing 已经围绕仓库内路径形成完整消费链，因此保留当前承载位置，并让后续 ticket 完成模块移入和 TDD。需要纠正的是产物形态和生产吸收边界，不是资产位置。

### Spec、ticket、plan

`/mmw-to-spec` 已保留“不重新采访，只综合”、代码库调查、Testing Decisions、用户确认 seam 和 spec 定稿人工审批关卡。

`/mmw-to-tickets` 已保留 tracer bullet、完整垂直路径、独立可验证、prefactor、blocking edge、frontier 和大范围重构的 expand-contract 例外。关键缺口只有发布前确认。上游证据在 `vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md:42-60`；MMW 的相反行为在 `mmw/skills/mmw-to-tickets/SKILL.md:53-63`。

`/mmw-to-plan` 与 `/mmw-planner` 是 MMW 为多 agent 交付增加的层。任务包仍受一张 tracer bullet ticket 的行为边界约束，并要求独立实现、独立验证。当前没有证据表明该层改写了上游 ticket 方法。

### Implement、TDD 与 review

MMW 已保留预先确定的 spec/ticket 输入、预先确认的 seam、公开接口行为测试、只 mock 系统边界、red before green、一次一个 vertical slice、最小实现和 fresh-context review。

两项遗漏需要补回：

- 上游新增 `vendor/mattpocock-skills/skills/engineering/tdd/SKILL.md:26`：interface 的 depth、seam 或暴露面尚未确定时，读取 codebase-design 词汇，不在 TDD 中自己设计。
- 上游 `vendor/mattpocock-skills/skills/engineering/implement/SKILL.md:9-13` 明确测试频率。MMW 当前只要求读取目标仓库 `TESTING.md` 和“测试通过”。`TESTING.md` 应决定运行什么，不能替代何时运行。

MMW 的六道审扩展与上游双轴 `code-review` 相容。final 终审仍覆盖 Standards 与 Spec 两轴，并增加 spec 审、plan 审、逐份验收、合同门和合并集成审。

### Bug 诊断、research、领域建模和架构

以下方法已充分保留，无需因本轮更新改动：

- `/mmw-diagnosing-bugs`：tight red loop、实际运行、无 loop 不建理论、3 到 5 条可证伪假设、预测、正确 seam 上的 regression test、重跑原始 loop。
- `/mmw-research`：background subagent、一手来源、逐条出处。MMW 将内部调查细化为 `文件:行号`，并增加主 agent 验证；这是增强。
- `/mmw-domain-modeling`：ubiquitous language、边界场景、glossary/leaf、`_Avoid_`、Context Map、术语所有权和三条件 ADR。
- `/mmw-codebase-design`：module、interface、depth、seam、adapter、leverage、locality、deletion test、两 adapter 才构成真实 seam、Design It Twice。
- `/mmw-improve-codebase-architecture`：最近活跃区的 YAGNI 过滤、五种摩擦、有机探索、deletion test、HTML 候选报告和用户选择关卡。
- `/mmw-triage`：类别和状态角色、agent brief、已有实现、既有否决、bug 复现、PR diff 验证、`needs-info` 和 `.out-of-scope/`。

## 上游正式技能逐项状态

| 上游技能 | MMW 状态 | 本轮结论 |
| --- | --- | --- |
| `ask-matt` | `/mmw-start` 间接覆盖 | 主路由充分；缺 phase-boundary tree；Wayfinder 入口需放宽为“超出一会话且路线不清” |
| `code-review` | `/mmw-review`、`/mmw-reviewer` | 核心相容；六道审为 MMW 扩展 |
| `codebase-design` | `/mmw-codebase-design` | 充分保留 |
| `diagnosing-bugs` | `/mmw-diagnosing-bugs` | 充分保留 |
| `domain-modeling` | `/mmw-domain-modeling` | 充分保留；Context Map/leaf 为合理适配 |
| `grill-with-docs` | `/mmw-grilling` 加 `/mmw-domain-modeling` | 充分覆盖 |
| `implement` | `/mmw-implement` | 核心保留；补测试频率 |
| `improve-codebase-architecture` | `/mmw-improve-codebase-architecture` | 已吸收本轮 YAGNI 更新 |
| `prototype` | `/mmw-prototype` | 需要按上游重做逻辑产物；保留 MMW 的 primary-source 承载 |
| `research` | `/mmw-research` | 核心保留；验证与按调用方落点为合理适配 |
| `resolving-merge-conflicts` | `/mmw-integrate` | 核心覆盖；补“不发明行为”；安全 abort 保留 |
| `setup-matt-pocock-skills` | `mmw init` 和项目配置间接覆盖 | 不新增同名 skill；初始化已由确定 CLI 与 `.mmw.json` 承担 |
| `tdd` | `/mmw-tdd` | 主循环保留；补 codebase-design reference |
| `to-spec` | `/mmw-to-spec` | 充分保留 |
| `to-tickets` | `/mmw-to-tickets` | 主体保留；恢复发布前用户批准 |
| `triage` | `/mmw-triage` | 充分保留；Grilling 已按轮运行 |
| `wayfinder` | `/mmw-wayfinder` | map 主体保留；恢复一会话一 ticket，统一 effort 入口 |
| `wizard` | 无核心覆盖 | 建议新增，见“新增技能取舍” |
| `grill-me` | `/mmw-grilling` 部分覆盖 | MMW 是 repo 工作流，不新增无状态入口 |
| `grilling` | `/mmw-grilling` | 主要恢复已完成；补少量用户参与说明 |
| `handoff` | `/handoff` | 技能正文仍与上游 byte-identical；把 portability 选择放入 phase-boundary 规则 |
| `teach` | 无核心覆盖 | 不属于 MMW 工程交付范围，不吸收 |
| `to-questionnaire` | 无核心覆盖 | 建议新增，见“新增技能取舍” |
| `wait-what` | 无核心覆盖 | 建议作为极小辅助技能吸收 |
| `writing-for-agents` | 旧 `/writing-great-skills` 部分覆盖 | 必须迁移到当前上游结构和名称 |

## 新增技能取舍

| 新技能 | 是否吸收 | 理由与 MMW 接缝 |
| --- | --- | --- |
| `writing-for-agents` | 是，必需 | MMW 大量行为由技能、`AGENTS.md`、领域文档和 pointer 驱动。新范围直接覆盖 MMW 的核心维护对象。应替换旧技能，不保留无用 alias |
| `wizard` | 是，建议 | MMW 的 `wayfinder:task` 目前只能给人工清单。Wizard 把第三方配置、凭证、CI secret、一次性迁移和 cutover 变成可重复的交互式脚本。生成前展示 stage 与写入位置并取得确认；脚本由用户运行；涉及 `.env`、GitHub secret 和不可逆动作时继续遵守现有人工确认规则 |
| `to-questionnaire` | 是，建议 | `/mmw-grilling` 假设当前用户能作答。现实中知识可能在另一位产品负责人、客户或运维人员手中。该技能只 grill “发给谁、要拿回什么”，不会错误采访当前用户不掌握的 subject。可作为 Grilling 的阻塞出口，答案回来后再继续共同理解 |
| `wait-what` | 是，可低成本加入 | MMW 已有 ASD-STE100 和 canonical 术语规则，但缺少针对“上一条没听懂”的即时纠错入口。该技能极短，适合作为辅助 skill，不进入主流程 |
| `teach` | 否 | 多会话教学工作区不属于工程交付工作流 |
| `grill-me` | 否 | MMW 的任务、领域文档、worktree 和 tracker 都以 repo 为边界；无状态非 repo 讨论属于通用助手能力 |

## 未发布或 misc 技能取舍

| 技能 | 结论 |
| --- | --- |
| `claude-handoff` | 不吸收。仍是 beta 且绑定 Claude 后台命令，不符合 MMW 多宿主边界 |
| `loop-me` | 不吸收。生活循环与 workflow 文档不属于 MMW 工程交付范围 |
| `setup-ts-deep-modules` | 不吸收为共享 MMW skill。它是 TypeScript 与 dependency-cruiser 专项工具；需要时可作为目标项目技能使用 |
| `writing-beats`、`writing-fragments`、`writing-shape` | 不吸收。属于文章写作方法，不属于 MMW |
| `git-guardrails-claude-code` | 不吸收。宿主专用 hook 与 MMW 多宿主边界冲突；现有 Git 纪律和宿主护栏负责该层 |
| `migrate-to-shoehorn`、`scaffold-exercises`、`setup-pre-commit` | 不吸收。它们是专项工具，不是 MMW 共享工作流方法 |

## 可保留的 MMW 扩展

以下扩展有明确责任边界，没有发现它们曲解上游方法：

- 主 agent 验证 subagent 报告；取证可派，判定不可派。
- `planner` 与 plan 任务包层；每张 tracer bullet ticket 仍是一个 `worker` 的完整行为边界。
- 六道审；final 终审仍包含上游 Standards 与 Spec 两轴。
- Context Map、leaf、权威引用、结构图谱和结构候选。
- Codex App 后台 Worktree 任务、结果分支、基点验证和非 fast-forward 集成。
- `docs/prototypes/` 作为走查资产和视觉合同出处，随任务分支进入正式历史。
- `/mmw-retrieval`、`/mmw-closing` 和 release 状态机本身。
- Wayfinder research 报告先验证再写入 ticket 评论。该行为服务 MMW 的证据责任，可以替代未经验证的 raw report pointer。

`/mmw-release` 在 final 终审后改变 HEAD 是上述结论的唯一例外，必须补回重审闭环。

## 建议实施顺序

1. 先修 `/mmw-wayfinder`、`/mmw-prototype`、`/mmw-to-tickets` 和 `/writing-for-agents`。这四项直接影响最重、最频繁或最基础的方法。
2. 再补 phase-boundary、TDD/implement、release 重审和 integrate 意图边界。
3. 最后新增 `to-questionnaire`、`wizard` 和 `wait-what`。新增技能不要与方法保真修复放在同一提交。
4. 每一组技能源改动后同步 Pi、Claude Code、Codex 技能产物，并运行全部物化检查。

## 验证与过滤

- 调查覆盖全部 25 项上游正式技能，以及 10 项 `in-progress`/`misc` 技能。
- 关键差异已回到当前源码逐项读取；本报告没有依据文件名机械判断方法保真。
- 一条报告断言被丢弃：调查报告称 manifest 有 26 项正式技能。实际 `skills` 数组有 25 项。
- 没有其他因缺少出处而丢弃的断言。
- 本次只验证文本合同和 Git 基线，没有运行真实 Grilling、Wayfinder、Prototype、release 或宿主 materialization 流程。实施后仍需按目标技能的完成判据做运行验证。
