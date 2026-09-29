# R11 归置：principles（MMW 的原则层）

本文按 `docs/research/workflow-compare/reports/R4-mmw-architecture-form.md`（下称 R4）第 7 节 Q4 与第 13 节归置判据，定出 MMW 原则层的清单：哪些规则做成 `mmw-v2/skills/mmw/principles/<slug>.md`，调用方怎样引用，哪些看起来像原则但留在原处，pstack 的 23 条原则各自是否引入。准绳是 `docs/research/workflow-compare/reports/L7-pstack-component-contract.md`（下称 L7）第 A.4、C 节。`mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（下称 SSR）是被审视的对象。

标注：「已核实」＝本轮回到原文或跑命令看到；「推断」＝由原文推出；做不出判断的放第 8 节。

---

## 0. 结论

1. **原则清单维持 R4 的三条，不增不减：** `silence-is-never-a-pass`、`the-tracker-is-the-state`、`rerun-dont-reroute`。三条逐条过了 R4 D4.3 的七道门槛（第 3.1 节）。
2. **三条的主要收益：**
   - 它们给「跨任务的理由」一个运行时读得到的家。今天这些理由只在 ADR 0008、0010、0018 里，而消费仓库里的 agent 读不到本仓的 `docs/adr/`（ADR 0012 `## Considered Options` 第 2 条，已核实）。
   - 每条被三到四个不同机制的调用方复用。
   - `rerun-dont-reroute` 还消除一处已核实的冲突：`shared.md` 规则 11「redo it yourself」与流水线「报 blocked 并停下」方向相反。
   - 它们也是以后判断外来原则（例如 pstack 的）的参照。
   - **三条都不减少行数。** 调用方保留各自的具体规则和本处的理由，净增约 70 行。
3. **R4 对 PC8、PC11、PC12 的排除理由有事实错误，但排除结论成立。**
   - R4 第 15 节的理由是「完整理由已经在唯一的主要读者（worker）的文本里」。grep 核实：这三条各有三到五个不同读者，不是只有 worker（第 3.3 节）。
   - 改用成立的理由：
     - PC8（基线即合同）：每个读者的写法都绑定具体机制，并各带理由，找不到原则会改变决定的情形（L7 C.2、C.6 信号 2）。
     - PC11（线索不是证据）：通用形式的家是 `shared.md` 规则 4、12（门槛 7）。
     - PC12（一个文件一个写者）：可以由 `verify-ticket.py --lint` 机械检查，应该做成检查而不是原则（L7 C.1 第 2 问、C.6 信号 4）。这是一个 lint 候选，推断，见第 8 节。
4. **pstack 的 23 条原则一条都不原样引入**（第 3.4 节逐条）。
   - 16 条在 MMW 已有位置得当的家（`shared.md`、SSR、`CODING_STANDARDS.md`、`TESTING.md`、`to-tickets`、`diagnosing-bugs` 等）。
   - 7 条在 MMW 里没有运行时调用方：或只针对代码与类型设计（这类规则由消费仓库自己的规范管），或读者是设计 MMW 的维护者。
   - 唯一真正的空缺是 `principle-make-operations-idempotent` 覆盖的规则：写脚本时要保证被打断后可以原样重跑。它的读者是写脚本的人，不是运行时 agent，所以不做成原则，改为给 `CODING_STANDARDS.md` `## Skills and scripts` 加一条（第 1 节第 E2 行）。
5. **对 R4 D4.1、D4.4 的三处细化**（都是工程决定，理由在第 1 节）：
   - 跨技能的括注写成「(the `mmw` skill's `principles/<slug>.md`)」，不写「principle `<slug>`」。依据：SSR `### Hand-offs`「A file in another skill is named by skill and file」；worker 从不加载 `mmw`，只凭 slug 不知道该打开哪个文件。
   - 原则文件的 `**Why:**` 用文字写出观察到的故障和用户的决定，不写 ADR 编号、日期和 issue 号。依据：SSR `### Redundancy and bloat` 的沉积表；ADR 0012。slug 与 ADR 的对应只记在新 ADR 里。
   - `the-tracker-is-the-state` 在夜间的括注放在 `dispatch/SKILL.md` 第 8 行，不放在 `night.md`：`night.md` 第 5、11 行已带理由，第 8 行是唯一有规则、没理由、而且所有流水线角色都读的那一句。
6. **新增一个写作规则的家：SSR `### Principles`**，约 8 行。它写原则文件的格式、七道门槛、两种括注写法，以及一句划界：「步骤的具体规则与它括注的原则不算重复」。原则文件是给运行时 agent 读的，写原则的规矩要放在写技能的人读的文件里。放进 `mmw/SKILL.md` 会让每个人启动的会话都付这笔阅读成本（ADR 0008 `## Considered Options` 第 1 条的同一理由）。

---

## 1. 归置表

来源、行号都是本轮回到原文核对过的。表中「收益」只取用户要求 2 列的六种：去重复、给家、上游回原文、被两个以上调用方复用、以后加外来技能不必改现有文字、消除断点或冲突。

### A. 新建的原则文件（批 3，与 `mmw` 同一次提交）

| # | 现在位置 → 新位置与层 | 动作 | 具体内容 | 收益（证据） | 体量 | 被取代的旧规则与原意 |
|---|---|---|---|---|---|---|
| A1 | ADR 0008 全文（理由）＋各处本地句 → `mmw-v2/skills/mmw/principles/silence-is-never-a-pass.md`，原则层 | 新建 | 规则、Why、Applies when、Boundaries、Not，见第 3.1 节 | 给家：跨任务的理由今天只在 ADR 0008，消费仓库读不到（ADR 0012 选项 2）。复用：4 个不同机制的调用方括注它（第 3.1 节）。以后加外来技能不必改现有文字：pstack `prove-it-works`、`test-behavior-not-implementation` 引入时拿它比对（第 3.4 节） | +15 至 20 行 | Memory `415f96d0`「理由只放 ADR」：对跨任务理由改为放原则文件；原意（技能正文短）保住，因为原则按需读、不常驻。ADR 0008 选项 1「别写进 `verify-ticket/SKILL.md`，每个 worker 每次开工都要读」：原则文件不在每次运行时读，不违背 |
| A2 | ADR 0010、0019、0020 ＋ `dispatch/SKILL.md` 第 8 行 → `mmw/principles/the-tracker-is-the-state.md` | 新建 | 同上 | 给家：理由（宿主的 shell 工具会截断等待中的命令；定时查表只是把轮询搬家，这是用户 2026-09-06 的原话）只在 ADR 0010。复用：`mmw` 与夜间的 `dispatch` 两类读者都需要这同一条理由，写两份就是重复，放原则文件只写一处（Memory `8ec53374`「每条只写一处」） | +12 至 16 行 | SSR 事实 1「理由贴在规则旁」：本地理由照留，原则只承载跨任务的那一份 |
| A3 | ADR 0010 第 35 行、0017、0018 第 18–19 行 ＋ `ui-acceptance/SKILL.md` 第 35–36 行 → `mmw/principles/rerun-dont-reroute.md` | 新建 | 同上，含 `**Boundaries:**` 三条 | 消除冲突：`shared.md` 规则 11 与 `ui-acceptance` 规则 4、5 及 `implement` 第 18 行方向相反（N9 §9.3 第 1 条，已核实原文）。另有两处容易被误读成违规的合法重试，在 Boundaries 里说清：`night.md` 第 131 行 fast-forward push 被拒后重试；`implement` 第 84 行 `start` exit 2 时照 stderr「run it once more」。复用：3 个调用方 | +15 至 20 行 | 不改 `shared.md`（R4 D2.4）；把规则 11 经它自己的无人会话前言读成「重跑被打断的那一步；流水线的拒绝经技能给的路由上报」，见第 3.1 节 |

### B. `mmw` 里的原则索引（在 `mmw` 单元的文件里，内容由本单元给）

| # | 位置 | 动作 | 内容 | 收益 | 体量 | 旧规则 |
|---|---|---|---|---|---|---|
| B1 | `mmw/SKILL.md` `## Principles` | 新建 | 三行，格式照 R4 D2.2：`**Silence Is Never a Pass** (\`silence-is-never-a-pass\`). When you write a check or report a result that rests on one. A check that did nothing must not read like a pass.`，另两行同形。末句：「应用某条原则时读 `principles/<slug>.md` 全文」 | 给家：人启动的会话在任务开头看到原则名（pstack mode `## Principles` 的做法，L7 A.4） | +4 行 | — |

### C. 调用方括注（批 3，前提是调用方已是自有技能）

每处只在句末加一个括注，句子本身一字不动。选点的规则是每个调用方文件只加一处，（R12 K-9 改定：实际执行的规则是每个调用方文件对每条原则只加一处。）落在「本地规则没写理由」或「读者最可能遇到规则没覆盖的情形」的那一句上。上游文本不加括注，否则就是往上游加 MMW 改动，与「上游回到原文」相反。`implement`、`to-tickets` 在批 2 分叉成自有技能之后才加。

| # | 调用方与锚点（原文） | 括注写法 | 收益 | 为什么是这一句 |
|---|---|---|---|---|
| C1 | `mmw/playbooks/idea-to-tickets.md` **Tickets**（R4 D3.3） | `(principle \`silence-is-never-a-pass\`)` | 复用 | R4 已定 |
| C2（已被 R12 K-9 改定） | `to-tickets/SKILL.md` 第 84 行 `EXPECT:` 的 **success-only marker** 一条 | `(the \`mmw\` skill's \`principles/silence-is-never-a-pass.md\`)` | 复用 | 写判据的人会遇到先例没有计数行、或要用新 oracle 的情形，这时规则覆盖不到 |
| C3 | `implement/SKILL.md` 第 96 行（第 7 步）「each criterion under `Green before work:` with the landed ticket …」 | 同 C2 | 复用 | 这一句只给做法，没给理由：一条开工前就绿的判据证明不了这张票 |
| C4 | `dispatch/references/night.md` 第 127 行（`## 4` 第 2 步）「… and it asks for a negative control」 | 同 C2 | 复用 | 同上，只有做法、没有理由 |
| C5（已被 R12 K-41 改定） | `mmw/SKILL.md` `## Where you are`（R4 D2.2） | `(principle \`the-tracker-is-the-state\`)` | 复用 | R4 已定 |
| C6（已被 R12 K-41 改定） | `idea-to-tickets.md` `## Where you are` | 同 C5 | 复用 | R4 已定；白天没有脚本替它算位置 |
| C7（已被 R12 K-41 改定） | `dispatch/SKILL.md` 第 8 行「Where you are is what the ticket's events say, not what this session remembers.」 | `(the \`mmw\` skill's \`principles/the-tracker-is-the-state.md\`)` | 复用；给家（这一句今天没有理由） | 所有流水线角色（orchestrator、单票 orchestrator、自己接手的 worker）进入时都读这一句；取代 R4 列的 `night.md` |
| C8（已被 R12 K-41 改定） | `implement/SKILL.md` 第 74 行「A ticket you are prompted back into: … carry on at the step its `RESUME:` line names.」 | 同 C7 | 复用 | worker 被唤醒时读的就是这一段，而这一段没写理由 |
| C9（已被 R12 K-9 改定） | `dispatch/SKILL.md` 第 25 行 `## On waking` 第 1 步「Run that command again first.」 | `(the \`mmw\` skill's \`principles/rerun-dont-reroute.md\`)` | 复用 | 三个角色被唤醒时都读 |
| C10 | `night.md` 第 82 行 `child.opened` of kind `fault` 一行「… you do not patch while they run the night」 | 同 C9 | 复用 | R4 已定 |
| C11 | `implement/SKILL.md` 第 18 行「… `--sub-issue fault <file>` … then stop.」 | 同 C9 | 复用；消除冲突（worker 读到 `shared.md` 规则 11 与本句方向相反，今天没有调和句） | 本句只有做法、没有理由 |

C 组合计：11 处，每处增加约 8 个英文词，不增加行数。

### D. SSR（写技能的人读的规则）

| # | 现在位置 | 动作 | 具体内容 | 收益 | 体量 | 旧规则与原意 |
|---|---|---|---|---|---|---|
| D1 | 无 → SSR 新增 `### Principles`，放在 `### Hand-offs` 之后 | 新建 | 1）原则文件的格式（R4 D4.1，按第 0 节第 5 条细化）；2）R4 D4.3 的七道门槛；3）两种括注写法，括注只加在自有文本上；4）步骤保留本处的具体规则与理由，原则文件不列调用方、不复述任何调用方的规则，两者不算 **Duplication**；5）新原则的来源是 `retro` 的 `mmw-skill` 提案或用户的决定（SSR `## Editing` 第 1 条） | 给家：写原则的规矩今天无处可放（R4 只定了形式，没定住在哪）；消除冲突：没有第 4 条，SSR `### Redundancy and bloat` 的 Duplication 条（「one meaning stated in two places … delete the others」）会把原则与调用方判成重复 | +8 行 | SSR Duplication 保留；原意（两份副本会漂移）保住的方式：原则文件只写跨任务的形式，调用方只写本处的形式，二者一致与否由接线 lint 第 4 类核对存在性（R4 D3.6） |
| D2 | SSR 第 62 行「A check or completion criterion that cannot fail proves nothing」 | 不动 | — | 读者是写技能的人，这里就是他们的家（门槛 7） | 0 | — |
| D3 | SSR 第 32 行「A rule sits in the text of the agent that must follow it」 | 不动 | 成为原则层的边界：具体规则留在调用方（R4 D4.2） | — | 0 | — |
| D4 | SSR 事实 1「理由贴在规则旁」 | 不动 | 本地理由照留；原则承载跨任务理由 | — | 0 | — |

### E. `CODING_STANDARDS.md`、`TESTING.md`、`shared.md`

| # | 现在位置 | 动作 | 内容 | 收益 | 体量 | 旧规则与原意 |
|---|---|---|---|---|---|---|
| E1 | `CODING_STANDARDS.md` 第 10 行（拒绝三段；「A check that could verify nothing says so instead of reading like a pass (ADR 0008)」） | 不动 | 写脚本的人读这一条；原则文件是运行时 agent 读的，两者读者不同 | — | 0 | — |
| E2 | ADR 0010 第 35 行（「`advance` 本来就写成可以随时重跑」）、ADR 0025 第 15 行（`spec.merged` 是重跑边界）、提交 `0855d553`「fix(#414,#440): make closeout retry safe」→ `CODING_STANDARDS.md` `## Skills and scripts` 新增一条 | 新建（一条） | 草稿：「A command with side effects converges when run again after being cut off at any point: it skips what it already did and repeats no event, merge or message.」 | 给家：`rerun-dont-reroute` 的「原样重跑」以脚本可重跑为前提，而这条写脚本的规则今天只在 ADR 的 Consequences 与一次修复提交里，`CODING_STANDARDS.md` 与 `TESTING.md` grep「rerun、re-run、idempot、run again、twice」为 0，Standards axis 审新脚本时无据可依 | +1 行 | pstack `principle-make-operations-idempotent` 的内容以 MMW 自己的措辞落到这里，不引入原则文件（第 3.4 节第 11 行） |
| E3 | `CODING_STANDARDS.md` 其余 8 条、`TESTING.md` 全文 | 不动 | — | 各被一个 review axis 整份读（N9 §8） | 0 | — |
| E4 | `mmw-v2/prompt/shared.md` 全部 15 条 | 不动 | PC9、PC10、PC13、PC14 的家；`rerun-dont-reroute` 的 Boundaries 只是读法，不改原文 | — | 0 | ADR 0014 两条理由保留 |

### F. ADR 与词表

| # | 现在位置 | 动作 | 内容 | 收益 | 体量 | 旧规则与原意 |
|---|---|---|---|---|---|---|
| F1 | ADR 0008、0010、0017、0018、0019、0020 正文 | 不动 | 仍是原则 `**Why:**` 的维护者依据 | — | 0 | ADR 只记决定（`shared.md` 规则 13 的例外） |
| F2 | R4 第 9 节的新 ADR | 该 ADR 加一节 | 三个 slug 各自的依据 ADR 与记录在案的运行：`silence-is-never-a-pass` ← 0008、0018 第 19 行、0020 第 20 行；`the-tracker-is-the-state` ← 0010、0017、0019、0020；`rerun-dont-reroute` ← 0010 第 35 行、0017、0018 第 18–19 行、提交 `0855d553` | 给家：原则文件不写 ADR 编号（第 0 节第 5 条），维护者要从 slug 找到依据，只能靠这里 | +6 行 | — |
| F3 | `docs/contexts/toolbox/CONTEXT.md` | 新增 **principle** 词条（R4 已列四个词条之一） | 定义、`_Home_` 指 SSR `### Principles`；一句 `Distinct from`：上游 `codebase-design/SKILL.md` 第 62 行与 `triage/AGENT-BRIEF.md` 第 9 行的 `## Principles` 是普通意义上的原则，不是这个组件 | 消除冲突：同一个词在本合集里已有上游的另一种用法（grep 已核实），SSR `### Vocabulary` 第 1 条要求一词一义 | +3 行 | — |

### G. N9 的 18 条原则候选：逐条去处

「在哪」列的行号是本轮 grep 的结果。N9 的行号有两处漂移：`dispatch/SKILL.md` 第 7 行现在是第 8 行；`night.md` 第 92 行现在是 watchdog 一行，基线相关的是第 96、98 行。

| PC | 去处 | 理由 |
|---|---|---|
| PC1 假通过比诚实失败更坏 | 并入 `silence-is-never-a-pass` | 第 3.1 节 |
| PC2 检查要能失败 | 并入 `silence-is-never-a-pass` | 同一条 ADR（0008 `## Consequences`「把失败路径跑一遍」）的设计时形式；分成两条只会多一个名字 |
| PC3 拒绝三段 | 留在原处：`CODING_STANDARDS.md` 第 10 行、`ui-acceptance/scripts/refusal.py`、SSR 第 134–136 行 | 读者是写脚本的人，已有家（门槛 7）；由 `refusal.py` 机械生成（C.6 信号 4） |
| PC4 不轮询、由事件叫醒 | 并入 `the-tracker-is-the-state` | 与 PC5 同源（ADR 0019、0020） |
| PC5 进度读自持久记录 | 并入 `the-tracker-is-the-state` | 同上；但 `exe-release/references/driving.md` 第 5 行不括注（第 5 节） |
| PC6 协议状态只由脚本写 | 留在原处 | `tool-guard.py` `leaves_the_agent_lane` 已机械拦截（C.6 信号 4）；文字只留在 `implement` 第 99 行执行的那一步 |
| PC7 确定性交给脚本 | 留在原处：SSR 事实 2 | 读者是写技能的人（门槛 7） |
| PC8 基线即合同 | 留在原处，见第 3.3 节 | R4 的排除理由不对，结论成立 |
| PC9 用户只决定产品事项 | 留在原处：`shared.md` 规则 1、2，`AUTONOMOUS` | 门槛 7 |
| PC10 写给冷读的读者 | 留在原处：`shared.md` 规则 2、10 | 门槛 7 |
| PC11 线索不是证据 | 留在原处，见第 3.3 节 | 同 PC8 |
| PC12 一个文件一个写者 | 留在原处，并提 lint 候选，见第 3.3 节 | 同 PC8 |
| PC13 文件只写现状 | 留在原处：`shared.md` 规则 13、SSR 第 145 行 | 门槛 7 |
| PC14 最小测试集 | 留在原处：`shared.md` 规则 15、`TESTING.md` | 门槛 7 |
| PC15 只读靠文字 | 留在原处：`advisor`、`code-review` 的四个 axis 文件 | 只有两个技能，是同一个宿主限制的两个实例（L7 C.2「只有一个调用方」的变体） |
| PC16 一个家 | 留在原处：SSR 事实 7 | 门槛 7 |
| PC17 被打断后原样重跑 | 运行时部分并入 `rerun-dont-reroute`；写脚本的部分进 E2 | 读者分成两群 |
| PC18 拒绝要响、不静默替代 | 并入 `rerun-dont-reroute` | ADR 0018 第 19 行把它与 0008 连起来，所以原则里写 `**Not:**` 与 `silence-is-never-a-pass` 划界 |

---

## 2. playbook 草图

本单元不产生 playbook，也不新增任何 playbook 步骤。它只参与两件事：R4 D3.3 `idea-to-tickets` 的 **Tickets** 步骤和 `## Where you are` 各带一个括注（第 1 节 C1、C6）；R4 D4.2 的括注写法规定原则名只出现在句末括注里。原则不被「调用」，所以任何 playbook 都没有一步叫「读原则」。

---

## 3. 原则

### 3.1 三条原则的全部字段

门槛编号指 R4 D4.3 的七道门槛：1 短名；2 可观察的触发；3 改变具体决定；4 跨任务；5 至少两处引用、机制不同；6 理由有依据；7 读者群没有现成的家。

#### `silence-is-never-a-pass`

- **规则一句（文件正文草稿，英文，写成事实，照 Memory `ec59cec8`）：** A check that did nothing and a deliverable that did nothing read exactly like ones that passed; so a check you write must be able to fail, and a result that rests on a check nobody could run says "could not check", not "met".
- **Why（依据，均已核实原文）：**
  - ADR 0008 `## 这条规则是从哪一批故障里得出的`：一夜里五道闸口都处在「既没干活也没出声」的状态，其中 `advance` 一张没派，却打印了与「本来就没事可做」相同的总结行。
  - ADR 0018 第 19 行：「拒绝要响，替换是静默的」。
  - ADR 0020 第 20 行：没有中继时照起、只打警告，被否决，理由是这是一道「靠什么都不做通过的闸口」。
  - 本地的代价句：`implement` 第 22 行「a false `ALL MET` lands broken behaviour under a green mark, and every ticket built on this one inherits it」。
  - 按第 0 节第 5 条，原则文件只用文字写这些故障，不写编号和日期。
- **Applies when：** 你写或配置一道检查（`CHECK:`/`EXPECT:`、oracle、checker、hook、harness），或者报告一个建立在检查上的结果（closing comment、`NIGHT SUMMARY`、retro 的问题）。
- **会改变的决定：**
  1. worker 遇到开工前就绿的判据时，写出做了这项工作的已落地票，或者开 `contract` 子票，而不是直接勾上。
  2. 写判据的人遇到先例没有计数行时，换一个会失败的标记，或者把这条交给 `contract` 或 `none`，而不是抄 `ok`。
  3. orchestrator 为一条「已绿却坏了」的 finding 开票时，知道为什么要附 negative control。
  4. 在消费仓库里新加检查的 agent（例如一个 git hook、一个 harness 守卫）会先把失败路径跑一遍。这类情形没有任何本地规则覆盖，是这条原则独有的价值。
- **Boundaries（草稿）：** 调用方自己的形式优先于本原则，包括 success-only marker、negative control、probe、`unverified:`、`no-evidence-found`；本原则只管这些形式没点名的情形。
- **Not：** 与 `rerun-dont-reroute` 不同，后者管被拒绝之后做什么，本原则管结果怎样读。
- **现在出现的全部位置（grep 核实，102 个已安装技能 `.md` 文件）：**
  - `implement/SKILL.md` 第 22、30 行；
  - `to-tickets/SKILL.md` 第 84、86 行，`references/cutting-interface-tickets.md` 第 43–46 行；
  - `dispatch/references/night.md` 第 7、127 行；
  - `ui-acceptance/SKILL.md` 第 34 行，`references/journey.md` 第 42–53 行，`story-parity.md` 第 114–117 行，`harness-guard.md` 第 10–11 行；
  - `code-checkers/SKILL.md` 第 57–58 行，`references/git-hooks.md` 第 42、72 行；
  - `retro/SKILL.md` 第 47–48、58 行；
  - `code-review/references/session.md` 第 89 行（`unverified:`）；
  - 维护者的家：SSR 第 62、89 行，`CODING_STANDARDS.md` 第 10 行。
  - N9 列的 `to-spec/SKILL.md` 第 95 行讲的是产品的「silent break」要写旅程，只是近义，不括注。
  - ADR 0008 说有一条 `**silence is never a pass**` 词条，`docs/contexts/` grep 为 0，这个词条已经不在了。
- **归并后调用方的写法：** 上面每一处的句子一字不动。只在 C1–C4 四处加括注，其余各处已自带理由、写法完整，不加括注（SSR 事实 3）。
- **门槛：**
  - 1、2 通过。
  - 3 通过：见决定第 4 条。
  - 4、5 通过：头部 playbook、切票能力、worker 角色、orchestrator 角色，四种机制。
  - 6 通过：ADR 0008 的事故记录。
  - 7 通过：运行时 agent 没有通用形式的家，`CODING_STANDARDS.md` 与 SSR 的读者是维护者。

#### `the-tracker-is-the-state`

- **规则一句：** What has happened in a ticket's or a spec's work is what its events on the tracker say; a session's memory of it is a copy that compression and a new session lose, and waiting on another agent is an ended turn that an event wakes, not a loop that asks.
- **Why：**
  - ADR 0010 `## Considered Options` 第 1 条：宿主会截断超过 shell 工具时限的命令，转入后台且不交回退出码，所以 `wait` 循环拿不到结果。
  - 同节第 2 条，用户 2026-09-06 的原话：「本质上是把 worker 的轮询成本转嫁到 main 上面来，一点都不解决根本问题」。
  - ADR 0019：每个事件由脚本贴，票上的记录是完整的。
  - 本地理由：`night.md` 第 5 行「A reason that lives only in this session is lost when it ends」。
- **Applies when：**
  - 被唤醒、被压缩或在新会话里接手一件事；
  - 要等另一个 agent；
  - 某一步要判断「这件事做完了没有」。
- **会改变的决定：**
  1. 被压缩的会话读事件或 `RESUME:`，不读摘要。
  2. 等 reviewer 或槽位时结束回合，不写 `sleep` 加查询的循环。
  3. 白天被压缩的头部会话从已发布的 spec、票和仓库文件判断走到哪，不凭记忆。
  4. 引入带 `/loop`、transcript 续跑的外来 playbook 时，知道该换成什么（R4 D7.5）。
- **Boundaries（草稿）：** 还没有事件的白天会话，以已发布的 spec、票和仓库文件为记录。
- **现在出现的全部位置：**
  - `dispatch/SKILL.md` 第 8 行；
  - `dispatch/references/night.md` 第 5、11、66、76、93、110、165、206 行；
  - `one-ticket.md` 第 8 行；
  - `inside-a-ticket.md` 第 5 行；
  - `implement/SKILL.md` 第 22、74、78、84、86 行；
  - `ui-acceptance/SKILL.md` 第 38 行；
  - `verify-ticket/references/sub-issues.md` 第 11 行；
  - `exe-release/references/driving.md` 第 5 行（release engine 的状态，不是 tracker）；
  - 维护者的家：SSR 第 90 行，`CODING_STANDARDS.md` 第 16 行。
- **归并后调用方的写法：** C5–C8 四处加括注。R4 列的 `night.md` 改为 `dispatch/SKILL.md` 第 8 行（第 0 节第 5 条）。其余不动。
- **门槛：** 1–7 都通过。
- **诚实的评估：** 这是三条里最弱的一条。
  - 批 1 之后，worker 与 orchestrator 的位置都由脚本的 `RESUME:` 算出，按 C.6 信号 4，夜里这一半已由机制保证。
  - 它剩下的独有用途是：白天的读者、`dispatch/SKILL.md` 第 8 行缺的那句理由、引入外来组件时的判据。
  - 退路：如果 T13 走查显示没有 agent 打开它、也没有做出不同选择，就把 `**Why:**` 并进 `dispatch/SKILL.md` 第 8 行成为一个从句，并删掉这个文件与四个括注。可以撤销，代价是 5 处小改。

#### `rerun-dont-reroute`

- **规则一句：** A command cut short by a wake is run again as it was, because the pipeline's commands repeat no completed step; a command that refuses, a product that cannot be reached, or a fault in the pipeline's own scripts is reported where the pipeline routes it and not worked around, because a retry loop, another host or runner, a changed environment or a patched script hides the failure from every ticket after yours.
- **Why：**
  - ADR 0010 第 35 行：唤醒会打断正在跑的命令；`advance` 写成可以随时重跑。
  - ADR 0018 第 18 行：用户 2026-09-10 否决「退避重试五次再换 fallback host」，理由是那一夜被悄悄顶替，第二天早上才看得见。
  - `ui-acceptance/SKILL.md` 第 36 行本地理由：「A workaround built instead hides it from every ticket after yours」。
  - `refusal.py` 头注释：三个 worker 对同一条拒绝各自发明了等待、重试循环和杀进程（N9 §6 引，本轮未重读 `refusal.py`）。
- **Applies when：**
  - 一次唤醒打断了你；
  - 一条命令以拒绝退出；
  - 产品或流水线脚本出错。
- **会改变的决定：**
  1. 被唤醒时先原样重跑被打断的命令。
  2. `advance` exit 4 时修拒绝点名的事，不换 host。
  3. 产品连不上时开 `fault` 子票并停下，不写重试循环、不改环境。
  4. orchestrator 不在夜里修补流水线脚本。
  5. 有人值守的白天会话照 `shared.md` 规则 11 自己重做被打断的一步，但不绕过流水线的拒绝。
- **Boundaries（草稿，三条）：**
  1. 「redo it yourself before replying」（owner 的常驻规则）适用于你自己被打断的一步。对脚本启动、屏幕前没人的会话，它经那份提示词自己的前言生效（「what it reports goes in the formats its skills give」）：流水线自身的故障，按技能给的路由上报，形式就是 `fault` 子票。
  2. 一条拒绝或退出码自己写着「再跑一次」的，照写的做一次，这不算重试循环。例如 `route` exit 1「run the same command again」、`summary` 拒绝后重跑、`start` exit 2 时 stderr 说再起、fast-forward push 被拒后先 fetch 再 merge 再推（`night.md` 第 131 行）。
  3. 由脚本拥有的重试归脚本，agent 不在上面再加一层。例如 `exe-release/references/key.md` 第 201 行的 `transient:` 指纹由 release engine 重试；relay 在收到 ack 前会重发唤醒。
- **Not：** 与 `silence-is-never-a-pass` 不同，后者管结果怎样读；本原则管拒绝之后做什么。本原则的 Why 按名点那一条（原则指向原则，L7 A.4）。
- **现在出现的全部位置：**
  - `dispatch/SKILL.md` 第 25 行；
  - `dispatch/references/night.md` 第 52、66、82、120、131、180 行；
  - `implement/SKILL.md` 第 18、76、84 行；
  - `ui-acceptance/SKILL.md` 第 35–36 行；
  - `verify-ticket/references/sub-issues.md` 第 19 行；
  - 脚本：`tool-guard.py` 头注释第 18–20 行；
  - 维护者的家：SSR 第 136 行。
- **归并后调用方的写法：** C9–C11 三处加括注，其余不动。`night.md` 第 66 行「none is retried」与第 82 行在同一个文件，只括注第 82 行（R4 已定）。
- **门槛：**
  - 1–7 通过。
  - 3 的证据最强：它消除了一处已核实的冲突，也就是 worker 同时读到 `shared.md` 规则 11 与 `implement` 第 18 行。

### 3.2 三条原则的共同写法（进 SSR `### Principles`，第 1 节 D1）

- 文件：`# <Title>`；一到三句规则，写成事实；`**Why:**` 写观察到的故障与用户的决定，不写 ADR 编号、日期、issue 号；`**Applies when:**`；可选 `**Boundaries:**`、`**Not:**`。没有 frontmatter，不列调用方。
- 括注：`mmw` 目录内写 `(principle \`<slug>\`)`；其他自有技能写 `(the \`mmw\` skill's \`principles/<slug>.md\`)`；上游文本不写。
- 调用方的句子不因加括注而改写；原则文件不复述任何调用方的具体规则。

### 3.3 看起来像原则、但留在原处的规则

| 规则 | 出现位置（grep 核实） | 留下的理由 |
|---|---|---|
| PC8 基线即合同（照抄已定的结论；不成立就开 `contract` 子票） | `implement` 第 16、22、23、27、90–92 行，`references/writing-interface-code.md` 第 3 行；`code-review/references/spec-reviewer.md` 第 14、16、45、58 行；`dispatch/references/night.md` 第 96、98–100 行；`design-pages/SKILL.md` 第 10 行，`references/pull.md` 第 5 行；`triage/references/pipeline-issues.md` 第 5 行；`write-screen-contract/SKILL.md` 第 18 行；`to-spec/SKILL.md` 第 22、113–114 行 | 读者至少五类：worker、reviewer、orchestrator、做设计拉取的会话、triage。所以 R4 第 15 节「唯一读者」的说法不对。留下的理由是：每类读者的形式都绑定具体机制，即 `contract` 子票、authority order、Spec axis 的 `Missing`/`Built wrong`、story oracle、只由 pull 写入的设计包（L7 C.2 第一行）。每处又各带理由（`implement` 第 22 行、`spec-reviewer.md` 第 16 行、`design-pages/SKILL.md` 第 10 行）。本轮找不到哪个情形里，没有原则的 agent 会做出不同的事（C.6 信号 2） |
| PC11 线索不是证据 | `implement` 第 47–49 行（Memory）；`code-review/references/session.md` 第 101 行（Rules）；`spec-reviewer.md` 第 22 行（`integrated` 的结论）；`retro/SKILL.md` 第 63–64 行；`advisor/references/advising.md` 第 15 行 | 五个技能，所以同样不是「唯一读者」。通用形式的家是 `shared.md` 规则 4「A cause is something you found, not something you guessed」与规则 12（门槛 7）。各处的形式按线索的种类写，已经完整。Cursor 读不到 `shared.md`（ADR 0007），但各技能里的具体规则照样到达 |
| PC12 一个文件一个写者 | `to-tickets/SKILL.md` 第 96、98、102–109 行；`implement/SKILL.md` 第 28、78 行；`night.md` 第 126、139 行 | 读者有三类：切票的人、worker、orchestrator。「能并行的两张票不写同一个文件」可以由 `verify-ticket.py <spec> --lint` 按整批的 `## Owns` 与阻塞边机械检查。本轮 grep `verify-ticket.py`、`dispatch.sh`，都没有这项检查，只有事后记录的 `Outside Owns:`。SSR 第 61 行「A rule a script could check exactly becomes a check」与 C.6 信号 4 都指向做成检查。`to-tickets` 第 103 行的 prefactor 与按票拆文件，正是 pstack `separate-before-serializing-shared-state` 的第 2 步，已在唯一的写票处 |
| PC6 协议状态只由脚本写 | `implement` 第 99 行；`night.md` 第 112 行 | 由 hook 强制 |
| `ui-acceptance` 规则 1「Never end a process you did not start」 | `ui-acceptance/SKILL.md` 第 32 行；`sub-issues.md` 第 19 行 | 由 hook 强制（`tool-guard.py` `ends_a_process`）；绑定 lease 机制，只在一个领域 |
| `exe-release/references/driving.md` 第 5 行「Do not resume from session memory」 | 同左 | 状态在 release engine，不在 tracker。硬套 `the-tracker-is-the-state` 是误用；这一句的读者只有一个，规则完整 |
| N9 §9.4 全表（0012 四步门槛、0027 第二次 bounce、0031 查询写法、0026 final run 等） | 各自唯一的调用方 | 单一调用方或绑定机制（L7 C.2、C.4）；本轮未发现与 N9 不同的事实 |
| `ask-matt/PHASE-BOUNDARIES.md` | 残留目录 | R4 D4.5 定为 `mmw/references/phase-boundaries.md`，是 reference，不是原则（形态是有序判断树，只在一个分支读） |

### 3.4 pstack 的 23 条原则：逐条判断

原文逐条读过：`docs/research/code-landing-refs/pstack/skills/principle-*/SKILL.md`，共 513 行。R4 D7.4 定下的引入条件是：过 D4.3 的七道门槛，其中门槛 6 要求 MMW 自己的依据，pstack 的 `**Why:**` 不算 MMW 的运行记录（SSR `## Editing` 第 1 条）。

| # | pstack 原则 | MMW 已有的家或缺口 | 判断 |
|---|---|---|---|
| 1 | `attack-the-premise` | 无对应；它的 Pattern（按参与者统计不平衡、轮换角色）针对负载分配一类问题 | 不引入：MMW 没有调用方，也没有记录在案的「同一前提下两次修复都失败」的运行（门槛 5、6） |
| 2 | `boundary-discipline` | 代码设计规则，属于消费仓库自己的规范与 `codebase-design` | 不引入：MMW 不规定产品代码写法 |
| 3 | `build-the-lever` | SSR 事实 2；`night.md` 第 128 行「`grep` proves you got them all」 | 不引入：已有家 |
| 4 | `encode-lessons-in-structure` | SSR 事实 2 与 `### Scripts and judgement` 第 61 行；`retro/SKILL.md` `## Prevention destinations`（按读者选 `check`、`script`、`reviewer-rule` 等，就是「Route to the right layer」） | 不引入：已有家。新原则经 `retro` 的 `mmw-skill` 去处提出，原则文件在 `mmw` 技能里，现有去处已覆盖，不必加新的 `destination` 值 |
| 5 | `exhaust-the-design-space` | `prototype` 技能（上游）的 UI 分支做多个变体 | 不引入：已有家 |
| 6 | `experience-first` | 「少做功能、做精」属于范围与顾客所见，按 `shared.md` 规则 1 是 owner 的决定 | 不引入：与 `shared.md` 规则 1 冲突 |
| 7 | `fix-root-causes` | `diagnosing-bugs`（上游）的复现、诊断循环；`shared.md` 规则 4 | 不引入：已有家 |
| 8 | `foundational-thinking` | 代码与数据结构设计 | 不引入：没有 MMW 调用方 |
| 9 | `guard-the-context-window` | SSR 事实 3、5；`code-review` 按 axis 分给子代理；`mmw/references/phase-boundaries.md` | 不引入：已有家 |
| 10 | `laziness-protocol` | `implement` 第 24 行（被取代的分支同一次提交删掉）；SSR `## Editing` 第 1 条；`code-review` 的 `less-code` | 不引入：已有家 |
| 11 | `make-operations-idempotent` | **空缺**：写脚本时保证可重跑，这条规则只在 ADR 0010、0025 与提交 `0855d553` | 不作为原则引入：读者是写脚本的人，家是 `CODING_STANDARDS.md`，改为第 1 节 E2 的一条 |
| 12 | `migrate-callers-then-delete-legacy-apis` | `implement` 第 24 行；SSR `## Editing` 第 4 条（改名同一次改全） | 不引入：已有家 |
| 13 | `minimize-reader-load` | 代码可读性；技能文本侧是 SSR 事实 3 | 不引入 |
| 14 | `model-the-domain` | 代码结构；`domain-modeling` 管的是词汇，不是同一件事 | 不引入：没有调用方 |
| 15 | `never-block-on-the-human` | `shared.md` 规则 1、2；`AUTONOMOUS`；`implement` 第 23 行 | 不引入：已有家；pstack 自己的 mode 也放宽了它（L7 C.2） |
| 16 | `outcome-oriented-execution` | 无对应任务类型 | 不引入：没有调用方 |
| 17 | `prove-it-works` | `shared.md` 规则 4（「"it compiles" and "it deploys" are not "it works"」几乎同义） | 不引入；在 `silence-is-never-a-pass` 的 `**Not:**` 里不点它，因为它在 MMW 不存在 |
| 18 | `redesign-from-first-principles` | 用户 2026-09-06 判据「不要修修补补，要最根本的最优解」（`docs/research/mmw-structure/2026-09-06-handoff.md` `## 五` 第 4 条）意思相近，但读者是设计 MMW 的维护者 | 不引入：见第 8 节 |
| 19 | `separate-before-serializing-shared-state` | `to-tickets` 第 98–107 行（先按票拆文件、prefactor，再用 `Blocked by` 串行），就是它的第 2、3 步 | 不引入：已有家；另见 PC12 的 lint 候选 |
| 20 | `sequence-verifiable-units` | `tdd`、`to-tickets` 的 tracer bullet、`verify-ticket` 逐条判据 | 不引入：已有家 |
| 21 | `subtract-before-you-add` | SSR `## Editing` 第 1 条「A fix removes, merges, moves or simplifies before it adds」 | 不引入：已有家 |
| 22 | `test-behavior-not-implementation` | `TESTING.md` `## What a test proves`（「Pinning the wording … the passing test still proves nothing」，与 pstack 的「constant pin」同义）；消费仓库侧是 `tdd` 与 Tests axis | 不引入：已有家 |
| 23 | `type-system-discipline` | 语言层面的规则 | 不引入：没有调用方 |

合计：原样引入 0 条。16 条已有家（第 3、4、5、6、7、9、10、12、13、15、17、19、20、21、22 条，以及第 11 条的内容进 `CODING_STANDARDS.md`）；7 条没有 MMW 运行时调用方（第 1、2、8、14、16、18、23 条）。

---

## 4. 连线

```edges
mmw -> mmw/principles/silence-is-never-a-pass.md : cites-principle
mmw -> mmw/principles/the-tracker-is-the-state.md : cites-principle
mmw -> mmw/principles/rerun-dont-reroute.md : cites-principle
mmw/playbooks/idea-to-tickets.md -> mmw/principles/silence-is-never-a-pass.md : cites-principle
mmw/playbooks/idea-to-tickets.md -> mmw/principles/the-tracker-is-the-state.md : cites-principle
to-tickets -> mmw/principles/silence-is-never-a-pass.md : cites-principle
implement -> mmw/principles/silence-is-never-a-pass.md : cites-principle
implement -> mmw/principles/the-tracker-is-the-state.md : cites-principle
implement -> mmw/principles/rerun-dont-reroute.md : cites-principle
dispatch/references/night.md -> mmw/principles/silence-is-never-a-pass.md : cites-principle
dispatch/references/night.md -> mmw/principles/rerun-dont-reroute.md : cites-principle
dispatch -> mmw/principles/the-tracker-is-the-state.md : cites-principle
dispatch -> mmw/principles/rerun-dont-reroute.md : cites-principle
mmw/principles/rerun-dont-reroute.md -> mmw/principles/silence-is-never-a-pass.md : cites-principle
mmw/principles/rerun-dont-reroute.md -> shared.md : reads-reference
mmw-v2/tests/lib/check_wiring.py -> mmw : reads-reference
mmw-v2/tests/lib/check_wiring.py -> mmw/principles/silence-is-never-a-pass.md : reads-reference
mmw-v2/tests/lib/check_wiring.py -> mmw/principles/the-tracker-is-the-state.md : reads-reference
mmw-v2/tests/lib/check_wiring.py -> mmw/principles/rerun-dont-reroute.md : reads-reference
writing-for-agents -> writing-for-agents/SKILL-SET-RULES.md#Principles : reads-reference
retro -> mmw : hands-off-to
code-review/references/standards-reviewer.md -> CODING_STANDARDS.md : reads-reference
```

说明：

- `rerun-dont-reroute -> shared.md` 表示 Boundaries 第 1 条引用 owner 常驻规则的原文。这是按字面引用，不按编号引用，因为 Cursor 读不到 `shared.md`，引用写成「the owner's standing rule "redo it yourself before replying"」。
- `retro -> mmw : hands-off-to` 表示：新原则的来源是 retro 在 `mmw-skill` 去处上提出的提案，经人确认后落进 `mmw/principles/`。retro 自己不写原则文件（`retro/SKILL.md` `## Prevention destinations`）。
- lint 读的是 `mmw` `## Principles` 索引与三份文件，核对 R4 D3.6 第 4 类：每个文件有索引行，每个括注的 slug 有文件。

---

## 5. 不动清单

| 部件 | 理由 |
|---|---|
| 各调用方已自带理由的本地句：`implement` 第 22、30 行，`to-tickets` 第 86 行，`night.md` 第 5、7、11、66 行，`ui-acceptance` Five rules，`code-checkers` 第 57–58 行，`retro` 第 47–48、58 行，`code-review` `session.md` 第 89 行，`sub-issues.md` 第 11、19 行 | 规则绑定本处的机制，而且已带本处的理由（L7 C.2）；加括注不会改变任何决定，只多出文字（C.6 信号 2，SSR 事实 3） |
| `exe-release/references/driving.md` 第 5 行 | 状态在 release engine；单一读者；规则完整 |
| `ui-acceptance/scripts/refusal.py`、`tool-guard.py`、`turn-guard.py` 的消息与头注释 | 脚本给维护者看的理由；机制本身已强制 |
| `CODING_STANDARDS.md` 除 E2 以外全部，`TESTING.md` 全部 | 各有其读者（Standards axis、Tests axis），而且是那类读者的家 |
| `shared.md` 全部 | owner 的全局规则；MMW 不复述也不写入（R4 D2.4、ADR 0014） |
| ADR 全部正文 | ADR 记决定；新理由写进新 ADR（F2） |
| SSR 事实 1、2、7，`### Load and disclosure`，`### Redundancy and bloat` 的 Duplication 条，第 62 行 | 原意都保住；与原则层的关系统一写在新增的 `### Principles` 里，不去改这几条的字面 |
| `retro/SKILL.md` `## Prevention destinations` 与 `retro.py` 的 `DESTINATIONS` | `mmw-skill` 去处已经覆盖「改 MMW 的某个技能文件」，原则文件就在 `mmw` 技能里；加一个 `principle` 值要改脚本，拿不到任何一种所列收益 |
| 上游技能文本（`to-spec`、`tdd`、`diagnosing-bugs` 等）里与原则同义的句子 | 不往上游加括注；上游回到原文 |
| N9 PC3、PC6、PC7、PC8、PC9、PC10、PC11、PC12、PC13、PC14、PC15、PC16 | 见第 1 节 G 表、第 3.3 节 |

---

## 6. 形式拆散自查（L7 C.6 十一个信号）

1. **没有先确认已有组件不是合适的归宿：** 未触发。
   - 每条都先排除了 `shared.md`、`CODING_STANDARDS.md`、SSR、`TESTING.md`。
   - PC11、PC9、PC10、PC13、PC14、PC16 正是因此不做成原则。
   - `the-tracker-is-the-state` 与 `dispatch/SKILL.md` 第 8 行的重叠已写明：第 8 行的读者只有流水线角色，原则还服务白天的读者，并提供第 8 行缺的理由。
2. **新增内容不改变决定：** 部分未定。
   - 每条都写了会改变的决定（第 3.1 节）。
   - 但这些是推断，要到 T13 走查才能确认；`the-tracker-is-the-state` 最弱，已给退路。
   - 括注只加在「规则没写理由」的句子上，不加在已完整的句子上。
3. **重复已有的、位置得当的指引：** 触发了一处，已按 L7 C.5 处理。
   - `dispatch/SKILL.md` 第 8 行与 `the-tracker-is-the-state` 的规则句同义。
   - 按 C.5「点名持有者，同时保留关键一句」的写法：第 8 行保留原句，加括注指向持有者。原则文件不复述调用方。
   - 这一处写进 SSR `### Principles` 第 4 条，不再判为 Duplication。
4. **本可由机制强制的规则写成了文字：** 未触发，反向处理了一处。
   - PC12 可以机械检查，所以不做原则，提 lint 候选。
   - PC6 已由 hook 强制。
   - 原则的存在性与索引由接线 lint 第 4 类核对。
5. **playbook 只调一个技能：** 不适用，本单元不建 playbook。
6. **reference 每次都读、单一调用方：** 不适用，本单元不建 reference。
7. **原则说不出改变哪个决定，或只适用一步：** 未触发。三条各有三到四个不同机制的调用方，并写明会改变的决定。
8. **拆完需要按步骤编号引用：** 未触发。括注按 slug 与文件名；原则里提到 owner 的规则时按原文引，不按「规则 11」的编号。
9. **拆出的内容没有第二个调用方、也不减少重复：** 未触发。三条各有三到四个调用方。
   - 减少重复这一项较弱，只体现在跨任务理由只写一处（Memory `8ec53374`）。
   - 本地句不删，第 0 节第 2 条已如实说明。
10. **把单入口固定流程拆成三层：** 未触发，没有拆任何流程。
11. **把只在流程之间复用的内容做成能力技能：** 未触发。原则是文件，不是技能。

---

## 7. 待用户决定

只列 owner 层面的决定。其余都是工程决定，本文已定。

| # | 决定 | 建议 |
|---|---|---|
| 1 | 是否从 pstack 引入任何原则（即 R4 U1 中原则那一半） | 本轮逐条判断后建议零条：16 条在 MMW 已有位置得当的家，7 条没有运行时调用方。以后要引入，走 R4 D7.4 与 SSR `### Principles` 的门槛 |
| 2 | `rerun-dont-reroute` 的 `**Boundaries:**` 第 1 条怎样读 owner 自己的规则 11（「When a step fails or is interrupted, redo it yourself before replying」）：对屏幕前没人的流水线会话，它经提示词前言「what it reports goes in the formats its skills give」生效，流水线自身的故障以 `fault` 子票上报、停下，而不是自己修好再继续 | 按这个读法写。它与 ADR 0018 里 owner 2026-09-10 的决定一致，不改 `shared.md`。如果 owner 希望规则 11 自己写明这一例外，那是改 owner 的全局提示词，由 owner 决定 |

---

## 8. 未确定

| # | 问题 | 需要什么才能定 |
|---|---|---|
| 1 | 三条原则是否真的改变 agent 的决定（R4 K8、T13） | 批 3 之后按 SSR `## Verifying` 走查：给全新 worker 一张开工前就绿的判据的票，给全新 orchestrator 一条 `advance` exit 4。记录它是否打开原则文件，以及打开前后的选择。`the-tracker-is-the-state` 未通过时按第 3.1 节的退路处理 |
| 2 | 一个会话从没加载过 `mmw` 技能时，能否按「the `mmw` skill's `principles/<slug>.md`」在五个宿主上打开这份文件 | 同类写法今天已有（`implement` 第 12 行点名 `dispatch` 的 `references/inside-a-ticket.md`），但本轮没有看到各宿主的会话记录。列入 R4 T4 一起测 |
| 3 | PC12「能并行的两张票不写同一个文件」能否由 `verify-ticket.py <spec> --lint` 检查（推断能：它已读整批，并报 `[parent-unreadable]`、`[sub-issues-unreadable]`） | 读 `verify-ticket.py` 的 `--lint` 实现，确认它拿得到整批的 `## Owns` glob 与阻塞边；glob 与 `(new)` 路径的重叠判定能否写成精确检查。能的话开一张普通票 |
| 4 | 用户 2026-09-06 判据「不要修修补补，要最根本的最优解」在现行规则里没有对应句（N9 §7 已记，本轮核实 `docs/research/mmw-structure/2026-09-06-handoff.md` `## 五` 第 4 条原文） | 它的读者是设计 MMW 改动的维护者，不是运行时 agent，所以不属于原则层。候选的家是 SSR `## Editing`。归哪里需要问 owner 这条判据是否仍然有效，本轮不决定 |
| 5 | 词表里 400 余条词条是否还嵌着只在词表里有的行为规则（N9 §11） | 逐条核对，不在本单元范围 |
| 6 | `refusal.py` 头注释「三个 worker 各自发明等待、重试、杀进程」的原文 | 本轮没有重读，只取 N9 §6 的已核实记录；写 `rerun-dont-reroute` 的 Why 前回到原文 |

---

## 本轮读了什么

- 通读：
  - R4 全文（任务附带）；
  - L7 第 0、A.4、A.5、C 节；
  - N9 全文，N11 全文；
  - pstack 23 份 `principle-*/SKILL.md`；
  - `mmw-v2/prompt/shared.md`（用 `diff` 确认与 `~/.claude/CLAUDE.md` 相同）、`CODING_STANDARDS.md`、`TESTING.md` 前 16 行、SSR 全文；
  - `implement/SKILL.md` 全文，`dispatch/SKILL.md` 全文，`night.md` 全文，`one-ticket.md`、`inside-a-ticket.md` 全文；
  - `tool-guard.py` 第 1–91、195–216 行，`turn-guard.py` 第 1–40 行；
  - ADR 0008 全文、0010 第 1–40 行、0012 `## Considered Options`、0017 第 1–12 行、0018 第 8、18、19、23 行、0019 第 8–16 行、0020 第 16、20 行、0025 第 15 行；
  - `retro/SKILL.md` 第 44–70、186–215 行；
  - R3 第 7.3–7.4 节，R2 第 6 节相关行；
  - Memory `8ec53374`、`ec59cec8`、`756fc056`、`ce037679`（`nmem` 读到原文）。
- grep 范围：`mmw-v2/skills.txt` 列出的已安装技能的 102 个 `.md` 文件（不含 `diagram-design`），与 N9 同口径。
- 没有读：`refusal.py`、`verify-ticket.py` 的 `--lint` 实现、`status.py`、各 runner 适配器。依赖它们的结论已标为推断或列在第 8 节。
