# improve-codebase-architecture

## 定稿（主 agent 复核）

**判断**：本仓写的文字都有依据（出图规则来自新 agent 实跑时暴露的缺口），上游的 YAGNI、deletion test、"ADR 不轻易推翻" 几段都是灵魂，保留。缺的是结尾：审问结束后产出是什么、交给谁。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` 末尾，新增一节 `### 4. Hand the decision on`（本仓加，merge-note 记一条） | This skill changes no code. What the grilling settles is a decision: the deepened module, its interface, where the seam sits, which tests move to it. When the user confirms it, hand that decision to the `to-spec` skill, which turns this conversation into a spec the landing pipeline can build and verify; refactoring here would skip the tickets and the acceptance checks that make the change safe to land. Take one candidate per session, and tell the user the report's path so the others can be picked up later. | 它加载的 `grilling` 最后一句是"用户确认后再动手"；没有这一节，agent 可能在同一会话里直接改代码，绕过 spec、切票、验收。**推断**：没找到这个技能的真实运行记录。 |

### 不采纳

- "候选少也是有效结果"那段：没有观察到凑数的情况，按上游技能"只接不改"的规则不加。

## 结论

体量：`SKILL.md` 900 词、`HTML-REPORT.md` 802 词，另有 `agents/openai.yaml` 5 行，没有脚本。上游原版分别是 899 词和 924 词（`git show 5b1a4c51:skills/engineering/improve-codebase-architecture/…` 取得），所以本仓改完后比上游还短约 120 词：本仓删掉了上游的 Tailwind/Mermaid 骨架（约 600 词），换成约 480 词的接线文字，把出图交给 `diagram-design`。本仓加的这部分每一段都有 merge-note 条目，且大部分来自 2026-09-18 两次"新 agent 照原文跑一遍"发现的真实缺口（提交 `b898a009`、`6702fd42` 的说明），不是凭空预想的防御；我没找到可以删的本仓文字（A 表只有一条，在 merge-note 里，不在技能正文里）。主要问题不是多，而是少了一句：技能在 grilling 结束后没有说产出是什么、交给谁，在 MMW 里 agent 可能在同一会话里直接动手重构，绕过 spec → ticket → 夜间 worker 这条落地流水线。灵魂部分（YAGNI 定范围、按摩擦感探索、deletion test、ADR 不翻案、先报告后提接口）来自上游，完整，全部应保留。

## A. 删除或改成脚本

技能正文（`SKILL.md`、`HTML-REPORT.md`、`agents/openai.yaml`）里本仓加的文字：没有可删的。逐段对照 merge-note `mmw-v2/merge-notes/improve-codebase-architecture.md` 与上游 diff 后，每一段改动都改变了 agent 的做法（出图来源、免掉 §3 确认、固定画法、颜色角色、读者定位），没有历史注记、没有 no-op、没有复述脚本。

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| A1 | `mmw-v2/merge-notes/improve-codebase-architecture.md` `### SKILL.md` 表第一行（「保留，与上游一致…另外六个保留这一行的是…」），同样的清单也在 `grill-me.md`、`grill-with-docs.md`、`handoff.md`、`teach.md` 各自的第一行 | 6 | 七个保留 `disable-model-invocation` 的技能清单写在 `mmw-v2/merge-notes/README.md` `## disable-model-invocation`，又在 5 份 merge-note 里各抄一遍"另外六个"；README 同一节明说"下面每份说明只写它那个 skill 站在哪一边，不复述这条规则"。这是维护者文档，不是 agent 加载的技能文本 | README 那一节保留唯一的清单；各 merge-note 只留本技能的理由（本条的理由是：与 `codebase-design` 抢同一请求、night 里无人回答）。剩余风险：无，清单增减只改一处 | 删掉各 merge-note 行里"另外六个保留这一行的是 …"那一句，保留理由与"规则见 README"链接 |

上游原文里有几处冗余，按任务书不报删：`SKILL.md` `### 2.` 的卡片字段列表（第 43–50 行）与 `HTML-REPORT.md` `## Candidate card` 重复且略有出入（前者叫 `Benefits`、要求讲 locality/leverage 与测试，后者叫 `Wins`、每条 ≤6 词）；词汇规则在 `SKILL.md` 第 13 行、第 54 行、`HTML-REPORT.md` `## Tone` 与 `codebase-design` 的 `## Glossary` 共出现四次；第 39 行的临时目录与 `open`/`xdg-open`/`start` 命令是 agent 默认就会的事。这些都不会让 agent 在 MMW 里做错（`HTML-REPORT.md` 更具体，agent 会以它为准），所以不提。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 第 9 行（`Surface architectural friction … The aim is testability and AI-navigability.`）：说明这次调查为谁服务，候选的好坏以"测试更容易、agent 更好找路"来衡量，而不是"代码更干净"。
- `SKILL.md` `### 1. Explore` 的 `**Scope before you scan: YAGNI.** Deepening a module pays off by making future changes to it easier…`：这是整个技能的判断核心，告诉 agent 重构的回报只在还会改的代码上兑现，所以先看提交历史定热点，而不是平铺扫全仓。
- `SKILL.md` 第 27 行 `Don't follow rigid heuristics; explore organically and note where you experience friction` 及其下五个问题：把"找什么"交给 agent 的切身摩擦感，问题只是提示方向；这正是任务书要的"信任 agent 判断"。
- `SKILL.md` 第 35 行 deletion test（`A "yes, concentrates" is the signal you want.`）：唯一的入选标准，挡住泛泛的"整理建议"。
- `SKILL.md` 第 56 行 `**ADR conflicts**: … only surface it when the friction is real enough … Don't list every theoretical refactor an ADR forbids.`：告诉 agent 已记录的决定有分量，翻案要有真实摩擦作代价。
- `SKILL.md` 第 60 行 `Do NOT propose interfaces yet.`：保住"先让用户挑，再深入"的顺序，防止 agent 抢先替用户选定方案。上游说明页记录过真实投诉（弱模型跳过报告直接对第一个想法追问），这一句是防线。
- `SKILL.md` 第 70 行 ADR 提议的限定（`Only offer when the reason would actually be needed by a future explorer … skip ephemeral reasons`）：给出"什么值得记下来"的判断标准，而不是见拒就记。
- `SKILL.md` 第 41 行（本仓加的）`the report is where the user reviews the diagrams, so draw every candidate's straight away`：理由句本身让 agent 明白为什么这里不照 `diagram-design` §3 停下来确认；删掉理由只留规则，agent 遇到类似的图多页面就无从类推。
- `HTML-REPORT.md` `## Candidate card` 末段 `The reader knows nothing about this topic. …`（本仓加的）：定义读者和图、字分工，决定了整份报告写给谁看。与 `wait-what/VISUAL.md`、`teach/SKILL.md` 三处逐字相同，见下文交接一节。
- `HTML-REPORT.md` `## Diagrams` 的 `Module, seam, leakage and deep module keep one look … so the reader learns the notation once` 与之后的强调色规则（本仓加的）：看起来像过度规定，但提交 `b898a009` 记录了新 agent 照旧文跑时各图各画、与图型自身规则相撞（Dependency graph 把强调色留给环、Sequence 返回线必须虚线）；有触发证据，不是过度防御。
- `HTML-REPORT.md` `## Tone` 的 `Concision is not an excuse to drift.` 与 `Wins bullets … Don't write "easier to maintain" or "cleaner code", because those terms aren't in the glossary and don't earn their place.`（上游）：给出词汇纪律的理由。

### 缺口与补充草稿

- `SKILL.md` `### 3. Grilling loop` 之后（文件末尾，第 71 行后）：**缺"这一轮产出什么、交给谁"。** 技能在 side-effect 列表处结束，没说 grilling 结束以后做什么。它加载的 `grilling` 技能末句是 `Do not act on it until the user confirms you have reached a shared understanding.`，字面上反而暗示"确认后就动手"。在 MMW 里，改代码要经过 spec → ticket → 夜间 worker → 验收关票（根 `AGENTS.md` 第一段），所以一个在本会话里直接重构的 agent 会绕过 `to-spec`、`to-tickets`、`verify-ticket` 的全部验收。上游说明页 `mmw-v2/upstream/docs/engineering/improve-codebase-architecture.md` `## What happens after you pick one` 与 `## Common questions` 写明了"产出是决定不是 diff、一次一个候选、交给 `to-spec`"，但这页 agent 不加载。这一条是推断（没有真实运行记录，见"没查到的"），但它属于"把上游技能接进工作流"，正是本仓负责的部分。按 `SKILL-SET-REVIEW.md` `### Upstream skills` "Connect outside the upstream text first"，可先考虑放在调用方；但这个时刻只有本技能在场，调用方（用户点名）没有文字可放，所以只能作为本仓在文件末尾加的一段，并在 merge-note 加一行。
  > ### 4. Hand the decision on
  >
  > This skill changes no code. What the grilling settles is a decision: the deepened module, its interface, where the seam sits, which tests move to it. When the user confirms it, hand that decision to the `to-spec` skill, which turns this conversation into a spec the landing pipeline can build and verify; refactoring here would skip the tickets and the acceptance checks that make the change safe to land. Take one candidate per session, and tell the user the report's path so the others can be picked up later.

- `SKILL.md` `### 2.` 第 60 行 `Do NOT propose interfaces yet.` 之前（可选，优先级低）：**缺"候选少也是结果"。** 上游说明页 `## Common questions` 的 `Will it ever tell me the codebase is fine?` 记录了真实用户反映：技能的框架推着 agent 产出候选，很少承认没问题。agent 因此会用 `Speculative` 候选填满报告，占用用户挑选时的注意力。这不是 MMW 特有的问题，按 `SKILL-SET-REVIEW.md` `### Upstream skills` 末句（加进上游技能的文字要以"工作流需要而上游没有的判断"换取篇幅）它不够资格；按本任务书对"灵魂"的要求它够。两者冲突，交给汇总的人裁定。
  > A short report is a valid result. If no candidate passes the deletion test clearly, say so in the Top recommendation and badge what remains `Speculative`; a report padded with weak candidates spends the user's attention on refactors that will never pay back.

## C. 死板的流程

没有需要放开的。

- `## Process` 的三步（探索 → 报告 → 用户挑选后 grilling）是真实的先后依赖：报告必须在用户挑选之前写完，接口必须在挑选之后才提，这个顺序就是第 60 行那条禁令要保护的东西。
- `HTML-REPORT.md` 的卡片字段、固定画法、约 560 宽的 `viewBox` 看起来是硬规定，但它们服务于读者（每次运行、每张图同一套记号，前后两图可以目测对比），并且后两者有新 agent 实跑发现的缺口作依据（提交 `6702fd42` 的说明：第二次冷启动试跑发现半栏宽下标签看不清、Sequence 的泄漏返回线与该图型规则冲突；merge-note `## Diagrams` 行记了具体数字：960 宽的预设放进半栏，12px 字缩到约 7px）。`## Diagrams` 的图型列表本身写的是 `Pick the diagram-design type that fits … Mix them.`，已经是交给判断的写法。
- 第 23 行的 hot spot 推断、第 29–33 行的五个问题都明写 `Don't follow rigid heuristics`，不是清单。

## 脚本

无。技能目录下没有脚本；出图后的检查（`diagram-design` 的 `self_check.py`、`verify-geometry.py`）属于 `diagram-design`，不在本报告范围。

## 与其他技能的重复或交接问题

- **"读者一无所知"段三处逐字相同**：`HTML-REPORT.md` `## Candidate card` 末段、`mmw-v2/upstream/skills/productivity/wait-what/VISUAL.md` `## Draw the page`、`mmw-v2/upstream/skills/productivity/teach/SKILL.md` `## Lessons`（`grep` 确认三份相同）。三个技能的 agent 各自只加载自己那份，每份都是"行动时加载的那一份"，按 `SKILL-SET-REVIEW.md` `### Redundancy and bloat` 的规则三份都该留。代价只是维护时"改一处三处一起改"，merge-note 已记。
- **交接目标不一致**：`mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md` 第 53 行说挑中候选后"take into the main flow at the `grill-with-docs` skill"；上游说明页说 `grill-with-docs` 或 `to-spec`。本技能自己的 grilling loop 已经跑过一轮审问，再进 `grill-with-docs` 会重复，所以 B 里的草稿写 `to-spec`。`ask-matt` 那句是上游原文，读它的是还没进本技能的 agent，不改。
- **子会话写法不一致（仅记录，不建议改）**：本仓把第 71 行 design-it-twice 那条改成 `asks your host for its own general-purpose subagents`（merge-note 理由：host 中立），但第 27 行 `Then spawn a sub-agent to walk the codebase.` 保持上游原文。在装了 `orchestration`、`orca-cli` 的机器上，"开子 agent"理论上可能被理解成开 Orca worker；没有见到实际发生，按"不制造发现"不提改动。
- **`codebase-design` 的 dependency category**：`HTML-REPORT.md` 的 badge row 要一个依赖类别标签（`in-process` 等），定义在 `codebase-design/DEEPENING.md`，而本技能只让读 `codebase-design` 的 `SKILL.md`。那份 `SKILL.md` 的 `## Going deeper` 指向 `DEEPENING.md`，agent 需要时会顺着找到，且是上游原文，不提。

## 没查到的

- **没有真实运行记录。** `$TMPDIR`、`/tmp`、`/private/var/folders` 下都没有 `architecture-review-*.html`；Nowledge Mem 里只有 2026-09-18 接入 `diagram-design` 的决定与两次冷启动试跑（由提交说明得知，试跑的报告文件已不在）。所以 B 的第一条缺口（agent 会在同一会话直接重构）是由 `grilling` 末句与 MMW 流水线规则推断的，不是观察到的。
- 没有渲染一份报告验证 `HTML-REPORT.md` 的画法在当前 `diagram-design` 版本下仍然成立。
- `diagram-design/SKILL.md`（5905 词）只读了 §0、§3 的 `### Confirm before drawing`、§7 `### Page layout`、§12 `## Output`，用于核对本技能引用的那几处存在且说法一致；其余部分未读。
- `codebase-design/DEEPENING.md` 未读；`DESIGN-IT-TWICE.md` 只读了前 40 行（确认与上游一致、已是 host 中立写法）。
- 上游当前 `main` 的 `SKILL.md` 与本仓最后一次 squash（`5b1a4c51`）逐字相同（`gh api` 取得后 `diff`），上游最近一次改这个技能是 2026-08-19 的去 em-dash 提交。
