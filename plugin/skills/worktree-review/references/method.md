# 共享审查纪律(开工读一次,全 stage 通用)

各 stage 的审查角度在对应 `references/<stage>.md`;本文件是所有审查共用的纪律。本文件 + 你 stage 的 angle = 你的完整简报。

## 只读 + 边界
只读,不碰 working tree / index / HEAD / 分支,不创建临时 worktree;看别的版本用 `git show <rev>:<path>`、`git diff <range>`、`git grep <pattern> <rev>`。别读被审仓库里给其他 agent 的私有定义。代码 diff 用 `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---` 包裹。

## 一次审透(本轮完整覆盖)
你只有这一次独立审查机会(复审是全新审者,不继承你的对话)。本轮职责:
- **穷尽你负责视角内的真问题**:正确性 / 安全 / 数据与权限 / 合同与不变量 / 回归 / 测试质量 / 方向与方法级问题——能发现的现在全报,不许"小问题留到下一轮再说"。
- **知道却没报 = 审查失败**,不是谨慎。
- 按 angle 清单逐项过完再写 Return Contract;Evidence 表要能看出你覆盖了哪些面,不是只抽了几处。
- 不确定但是承重的:标 confidence 中/低 + 写清"怎样才能坐实",仍报在本轮,别吞。

## 报全 ≠ 报噪
穷尽的是**真缺陷与承重风险**,不是品味清单。
- **报**:会坏功能 / 丢数据 / 破安全或权限 / 破合同或不变量 / 漏核心意图 / 测不到承重行为 / 明显过度设计且已造成真实成本。
- **可报但必须标 non-blocking(进低置信观察或 Nit)**:命名偏好、纯风格、"可以更优雅"、无当前用户路径的抽象建议、教育性点评。
- **不报**:纯偏好、与 style guide / 项目规则无冲突的口味、对未改代码的顺便吐槽、无 locator 的感想。
- 自检句:**一个正常负责人看到这条,会不会真心想在本轮修掉?** 答"不会"→ 降为 Nit 或低置信观察,不进 Critical/Important。

## 放行标准(写给审者的校准,最终放行权在主线程)
目标不是完美产物,是**整体代码健康 / 设计健康在变好**。
- 无 Critical、无未说明的承重 Important → Verdict 倾向 `pass`;Nit 与低置信观察不阻止 `pass`。
- 不要为了显得严格而把 Important 堆满;严重度通胀 = 噪音。
- 源产物 / 注释里的"按 YAGNI 留的""故意从简"是作者自评,不因此降严重度 / 放过真偏差,仍按产物本身判。

## 先挑方向,再挑地基,最后过闸
过闸前先退两步:**先质疑方向(源意图本身),再质疑方法(实现手法)**,最后才验实现对不对。下面五问必须先答,找不到问题就明说"方向 + 方法都合理"再过闸:

**方向级（源意图不是标尺,是也要被审的对象——最易漏,因为源产物把它当前提）：**
- **解错问题 / 源意图本身可疑?** 别默认源意图(issue / 讨论结论 / 目标)对就只查产物对不对得上它。退一步问:这是**真问题**吗、换框架会不会让它**整个消失**、**什么都不做**的代价、**现有代码已解了多少**(优先复用)。源意图选错方向 = 一等 finding(Important;撼动账务 / 数据 / 大量工作量升 Critical),哪怕产物完美对齐一个错方向也要报。

**方法级（实现手法）：**
- **重造轮子?** 通用问题(解析结构化文档 / 数据清洗 / ETL / 状态机 / 调度 / 序列化 / 缓存 / 解析器)先问有没有**成熟库 / 标准做法 / 平台现成能力**;手搓通用能力 = Important,点名该用的成熟方案,别只夸它实现得对。蓝图若写"采用不重造 / 站在肩膀上",违它升级。
- **地基 vs 样本?** "在现有样本上恰好跑通"≠ 对;要 **by-构造 / 对抗输入**证明,不认"跑了 N 个样本全绿"。靠输入格式的偶然规律成立的 = Important。
- **这层该不该存在?** 反向 YAGNI:不是删多余代码,是问这**整块抽象是不是选错了**、有没有更上游的解法让它整个消失。**仅当这层已造成真实成本**(挡验收 / 放大面 / 明显拖慢或易错)才升 Important;仅"可以更干净"→ Nit/观察。
- **越改越对 ≠ 方法对**:把"在精雕一个本不该存在的东西"当 finding。

## 复审轮规则(dispatch 标明本轮是 re-review 时强制)
- 先读上一轮留痕路径(dispatch 会给)。
- **只做两件事**:① 验证上轮 accepted 项是否真修好;② 本次修复 diff 引入的新回归 / 新承重缺陷。
- 已标 `rejected` / `waived` / `duplicate` 的项:**无新证据不得重提**(换表述重报 = 违规)。
- **不对未改动区域起新 Nit**;新 Important/Critical 必须落在修复触及的路径或与 accepted 修复直接相关的连锁面上,并写清与上轮的增量关系。
- 上轮 accepted 已修好且无新承重问题 → `pass`,不要为证明自己有产出而找茬。

## 结构候选先行
遇到谁调用/引用某符号、连接关系、依赖路径或影响面，先完整读取 [Retrieval Doctrine](../../orchestrate/references/retrieval-doctrine.md) 并按它取得候选。图/LSP 输出只用于扩大检查面；每条 finding 仍必须通过下面的验证门，引用目标 checkout 的 `file:line` + 原始行。

## 防幻觉四件套
1. 置信度:每条 finding 标 1-3 低 / 4-6 中 / 7-10 高。
2. 验证门:每条引用触发它的 `file:line` + 原始行("字段 X 不在 model Y"→引 class Y 定义体;"race"→引两处)。引不出 = 未验证,confidence 压到 4-5 移到低置信观察区。元编程(ORM 元类 / 装饰器 / 代码生成)引生成该符号的元构造。
3. 防自我合理化:"看着没问题"→引证据或标 unknown;"应该别处处理了"→读并引用;"大概测过"→给测试文件 + 方法名。
4. 证据表 + 偏见声明:`### Evidence` 列已读产物 / 已查代码路径 / 已跑命令 / 假设(影响 verdict 的前提)/ 未验证项;无对应写"不适用"不留空。另设**结构候选**必填行：图谱/LSP 存在且新鲜时，记录实际运行的候选查询、命令和关键输出；图缺失/过期、工具不可用或问题不适用时，记录具体退化原因。缺这行的回执不合格，与 `file:line` 验证门同级。结尾声明不熟的模块 / 栈 + 受影响的 finding。

## Finding 字段
severity(Critical/Important/Minor) · blocking(yes/no) · confidence(1-10) · locator(file:line) · evidence · impact · remediation · scope(in-scope|out-of-scope|unclear)

- `blocking=yes` 仅用于 Critical 与承重 Important(不修不能放行)。
- Minor 默认 `blocking=no`。
- `scope=out-of-scope` 的项写清"应 spinoff / 开 issue",不伪装成本轮必修。

## 分级
- Critical:bug / 安全 / 数据丢失 / 功能坏 / 违反不变量。
- Important:漏核心需求 / 脆弱或错误行为 / 可维护性损伤且已造成真实成本(逐字复制、吞错、空断言测试、绕正式合同)。
- Minor:覆盖可更广 / 风格 / 优化 / 文档 / "可以更优雅"。
措辞 / 命名偏好不是 finding(连 Minor 都不进,除非违反项目明文规则)。源产物明写要的缺陷(空断言测试 / 逐字复制)→ Important 标 `plan-mandated`,human decides。先肯定做对的,无严重缺口则 approve。

## Return Contract
```
### Verdict — pass / needs-repair / needs-redirection / blocked / needs-context
### Evidence — 证据表 + 偏见声明
### Result — 对应 angle 文件规定的结果字段
### Critical / Important / Minor(non-blocking) / 低置信度观察 — 每条按 Finding 字段
### Assessment — 1-2 句;复审时加一句"相对上轮增量"
```
结构性 finding（谁调用/引用、连接关系、依赖路径或影响面）必须标注候选来源，或在 `### Evidence` 的结构候选行中给出合法退化声明。
整体 `needs-context` = 没拿到审查上下文,在 Verdict 说明缺什么,别硬凑 finding。
`needs-redirection` = 方向/源意图本身存疑(方向级第一问命中),不是产物有缺陷(那才是 needs-repair);Verdict 一句话说清「源意图哪里可疑 + 建议重新框定」,交人决策。
`pass` 可与 Minor/Nit 并存;不要因为还有 Nit 就改成 needs-repair。

## 禁用捷径（普适红线）
普适原则(任何项目):跨边界用弱类型裸结构绕过正式**合同** / 新增可被外部引用之物不**登记** / 绕过项目的数据校验与迁移机制 / 把行为测在非**权威层**——命中即 finding;影响验收 / 数据 / 权限 / 账务 / runtime / 发布时升 Critical。按被审项目自身的合同 / 登记 / 迁移机制具体化,别套别的项目的清单。
