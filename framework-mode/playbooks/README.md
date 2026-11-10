# 编写 framework-mode 的 playbook

要沿用 mode 的统一约定，增加一条处理特定任务的流程，就写 playbook。要让一种方法有自己的调用入口、所需材料和返回结果，供用户或不同流程单独使用，就写 skill。先写一句用户请求，再写一句完成条件，确定你正在增加哪一种东西。

```text
用户请求 → mode 选 playbook → 主对话执行步骤 → 验证交付物并报告
                                  │
                                  └─ 某一步需要专门方法
                                     读 skill，按其步骤完成 → 继续原流程
```

## 判断一段内容放在哪里

同样是“启动很慢”，用户给了一份 CPU profile，只问时间花在哪里，`Trace forensics` 就以这份采样为依据，交回能定位到源码的诊断。用户要求修好已经测出的慢启动，`Perf issue` 则必须取得基线、实施修复并重新测量。**改变用户要的结果，主对话要执行的流程就变了。** [Trace forensics](../../upstream/pstack/skills/poteto-mode/playbooks/trace-forensics.md) · [Perf issue](../../upstream/pstack/skills/poteto-mode/playbooks/perf-issue.md)

在 `Perf issue` 里还有一个独立问题：“这个数字值得信吗？”playbook 决定**何时**需要这个判断，以及测量不可信时能否宣称修复有效。`benchmark-checklist` 教 agent **如何**得出判断，包括检查错误数、确认计时区间里真的完成了工作。换到 `Hillclimb`，同一方法用于检验即将固定下来的测量工具。方法可以单独改进，两份 playbook 各自保留自己的停止条件。[benchmark-checklist](../../upstream/pstack/skills/benchmark-checklist/SKILL.md) · [Hillclimb](../../upstream/pstack/skills/poteto-mode/playbooks/hillclimb.md)

复用次数和步骤多少都分不出两者。`Opening a PR` 被多个 playbook 调用，集中规定这个 mode 怎样使用 worktree、整理提交和打开 PR。它把这些流程接到同一种交付方式上。通常交回已打开的 PR 链接就结束，跟进 PR 状态另有 `Babysit`。`arena` 有六个阶段，也能独立运行。调用者给它一道题，就能拿回经比较、综合和验证的结果。候选方案怎样生成和评判，都由这个 skill 负责。[Opening a PR](../../upstream/pstack/skills/poteto-mode/playbooks/opening-a-pr.md) · [arena](../../upstream/pstack/skills/arena/SKILL.md)

在 pstack 里，mode 的路由索引和其他 playbook 的步骤都可以指向一份 playbook。读到它时，主对话已经有 mode 规定的原则、授权和委派方式，所以 playbook 只需补上这类任务的具体步骤。skill 有自己的 `name` 和 `description`，提供单独的调用入口，并写清自己需要的材料和返回的结果。skill 也可以调用别的 skill。这样的组织让各条流程按需读取方法，修改一个方法时也有明确的归属。[mode 的读取规则](../../upstream/pstack/skills/poteto-mode/SKILL.md#playbooks) · [arena 的入口与输出](../../upstream/pstack/skills/arena/SKILL.md)

`figure-it-out` 更能说明这个边界。它会为眼前的任务设计一份 playbook，然后执行并验证。作为 skill，它保存的是“怎样针对一个陌生任务制定并运行合适流程”的方法。每次产生的阶段和停止条件属于那次任务。这是从它的输入、步骤和输出得出的区分。[figure-it-out](../../upstream/pstack/skills/figure-it-out/SKILL.md)

## 写一份可以直接执行的 playbook

1. **先写入口和终点。** 在 mode 的 Playbooks 索引加一行，用用户给得出的条件区分相邻流程。例如“已有采样文件，希望取得诊断”就足以选中 `Trace forensics`。正文放在 `playbooks/<title>.md`，文件名采用小写和连字符，另取文件名时在索引注明。主对话选中以后才读全文。[mode 的 Playbooks 索引](../SKILL.md#playbooks)
2. **从终点倒推步骤。** 写出哪些证据必须先取得，哪些动作依赖它，什么结果会让主对话停止或改走另一条路。用主对话可以原样抄进待办的动作句。按依赖顺序排列，运行时跳过某步仍保留该项并写明原因。[pstack 路由指南](../../upstream/pstack/docs/guide/02-poteto-mode.md)
3. **在用得上的那一步调用 skill。** 写清交给它什么、需要拿回什么、结果怎样影响下一步。一两句能交代完的局部动作就写在步骤里。值得单独调用或维护的方法再抽为 skill。若一段内容同时规定整项任务的下一步和某种方法的内部做法，就在方法产生结果的位置分开写。
4. **写出交回什么就停。** 在 `Reply` 中列这条流程特有的产物、证据和未决项。需要另一个流程接手时，写清交接条件。例如 `Multi-phase plan` 交回计划路径和检查结果，点名之后执行计划的 playbook，等用户明确要求执行才开始实施。[Multi-phase plan](../../upstream/pstack/skills/poteto-mode/playbooks/multi-phase-plan.md)

步骤需要子代理时，补上分给它的范围、完成条件和返回材料。主对话收到结果后要做的检查也写在这一步。子代理如何读 mode、何时新建、按什么配置选模型，沿用 mode 的 Subagents 指令。调用 `interrogate` 这类自行组织子代理的 skill 时，沿用该 skill 的分工。[两种委派的完整例子](../README.md#同一份-feature-playbook-里的两种委派)

常见的正文可以这样起笔。需要几步就写几步，已有 playbook 能承担一段完整流程时可以直接引用。

```markdown
### ⟦Playbook 名称⟧

**你负责交付⟦结果⟧。** ⟦足以区分相邻流程的输入或范围⟧。

1. ⟦取得后续判断所需的证据⟧。
2. ⟦根据证据采取行动。需要专门方法时，写明调用的 skill 和所需结果⟧。
3. ⟦验证交付物。说明什么结果须停止或交回⟧。

**Reply:** ⟦本流程的结果、证据位置及仍待确认的事实⟧。
```

## 决定写多细

拿 `Trace forensics` 的收尾步骤试写。“分析完就给结论”太粗，agent 可能把最热的函数直接报成根因。写到“把热点映射到源文件、符号和行号。有前后两份采样就比较，只有一份就标为该采样支持的最强假设”，agent 已经知道怎样取证、能下多强的结论、何时交回。原文保留了这些要求，具体解析器则留给采样格式决定。[Trace forensics 的取证与交付](../../upstream/pstack/skills/poteto-mode/playbooks/trace-forensics.md)

最后逐句试删。删后会让 agent 走错分支、漏取证据、越过授权或提前宣布完成，这句话就留在 playbook。若删掉的只是被调用 skill 里已经写明的做法，保留调用处即可。具体文件、符号、命令和预期值，放进当次计划或任务说明。跨任务必须一致的命令或格式仍可写在 playbook，像 `Multi-phase plan` 中由检查脚本验证的计划结构。有时两条流程只差一个终点，篇幅就该很短。`Autopilot-stack` 直接沿用 `Autopilot-full`，只写哪些 PR 可以堆叠，以及在哪个已验证状态交给用户合并。[Autopilot-stack](../../upstream/pstack/skills/poteto-mode/playbooks/autopilot-stack.md)
