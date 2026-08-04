# Design It Twice

用户想给选定的 deepening 候选探索几种不同的 interface 时，用这个并行派 subagent 的做法。出自 Ousterhout 的「Design It Twice」——你的第一个想法多半不是最好的那个。

用的是 [SKILL.md](SKILL.md) 那套词汇——**module**、**interface**、**seam**、**adapter**、**leverage**。

## 流程

### 1. 把问题空间讲清楚

派 subagent 之前，先给选定的候选写一段面向用户的问题空间说明：

- 任何一个新 interface 都得满足的约束
- 它要依赖什么，这些依赖落在哪一类（见 [DEEPENING.md](DEEPENING.md)）
- 一段粗略的示意代码，把约束落到实处——这不是提案，只是让约束看得见

给用户看完就直接进第 2 步。他在读、在想的时候，subagent 已经在并行干活了。

### 2. 派 subagent

一个约束一个 subagent，至少三个，并行。每个约束：四栏表（目标=该设计约束下的 interface；读=技术材料路径 + `SKILL.md` + 领域文档路径；约束=只读且与其它变体结构不同；验收=交回 interface/用法/取舍）。
启动：四栏表写入 task 文件后，Bash（`run_in_background: true`）执行 `mmw dispatch investigator --task <task 文件绝对路径>`；回执 `mode: host-tool` 时原样传入 `params` 调用对应工具（params 已含 task 正文）。
每个 subagent 须产出**截然不同**的 interface。

每份 task 点名同样的技术材料路径（相关文件、耦合点、[DEEPENING.md](DEEPENING.md)、seam 位置），只有设计约束那一栏不同。task 与第 1 步给用户看的问题空间说明是两回事。

- subagent 1：「把 interface 压到最小——最多一到三个入口。每个入口的 leverage 拉到最大。」
- subagent 2：「把灵活性拉到最大——支持多种用法和扩展。」
- subagent 3：「为最常见的调用方优化——让默认情形简单到不用想。」
- subagent 4（用得上的话）：「跨 seam 的依赖按 ports & adapters 来设计。」

task 同时点名 [SKILL.md](SKILL.md) 与领域文档路径（`mmw domain path`），让命名跟架构语言和领域语言一致。领域文档三种返回怎么读见 `/mmw-domain-modeling` 的「读领域文档」一节。

每个 subagent 交回：

1. interface（类型、方法、参数——外加不变量、顺序、错误模式）
2. 一段用法示例，展示调用方怎么用
3. implementation 在 seam 后面藏了什么
4. 依赖策略和 adapter（见 [DEEPENING.md](DEEPENING.md)）
5. 取舍——哪里 leverage 高，哪里薄

### 3. 拿给用户看之前先验证

subagent 交回的是证据，不是结论。每份设计在到用户手上之前按 `/mmw-verifying-agent-output` 验证：它说存在的那些调用点、它说能去掉的那些耦合、它给出的依赖分类。一份读起来站得住、实际建立在误读当前代码之上的设计，会把用户带上错路——而这一步正是他要选一个的时候。

两份设计换了名字其实是同一个形状，算一份。把重合的地方写成排除项，重派那个约束。

### 4. 展示与比较

一份一份地展示，让用户能逐个吸收，然后用散文比较它们。按 **depth**（interface 上的 leverage）、**locality**（改动集中在哪）和 **seam 位置**来对比。

比完给出你自己的推荐：你认为哪一份最强、为什么。不同设计里的元素能组合得更好，就提出一个混合方案。要有立场——用户要的是一个明确的判断，不是一份菜单。
