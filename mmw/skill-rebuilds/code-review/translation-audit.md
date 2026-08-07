# `code-review` 1.2.2 翻译审查

## 本技能术语应用

共享术语只由 [上游技能翻译共享术语](../translation-terms.md) 定义。下表记录本技能的术语应用和独有术语，不建立第二份定义。

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| Standards、Spec | `Standards`、`Spec` | 两条审查轴的固定名称 |
| fixed point | 基准点 | 符合代码审查语境，并与 merge-base 保持区分 |
| sub-agent | `subagent` | 与仓库跨技能术语一致 |
| prompt、brief | `prompt`、`brief` | 两者指向不同层次的派发内容，不改写成 MMW `task` |
| finding | `finding` | 审查产出的固定对象 |
| smell baseline | 代码异味基线 | 有标准中文译名 |
| hunk | diff 区块 | 明确指向 diff 中的区块 |
| judgement call | 需要判断的事项 | 直接表达必须由审查者判断，不自造名词 |
| scope creep | `scope creep` | 保留上游方法词 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。下表逐一登记其他每一行。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | `name: code-review` 字面量已保留 |
| `SKILL.md:3` | 基准点的四种形态、Standards 与 Spec 两条轴、各自问题、并行 subagent、并列报告和四类使用场景均已保留 |
| `SKILL.md:4` | YAML 结束分隔符已保留 |
| `SKILL.md:6` | `HEAD`、用户提供的基准点和双轴 diff 审查均已保留 |
| `SKILL.md:8` | Standards 轴和仓库记录的编码标准已保留 |
| `SKILL.md:9` | Spec 轴和忠实实现来源 issue 或 spec 已保留 |
| `SKILL.md:11` | 两轴并行、避免上下文相互污染和随后汇总 findings 均已保留 |
| `SKILL.md:13` | issue tracker、缺失文件判据和 setup fallback 均已保留 |
| `SKILL.md:15` | `Process` 译为“流程” |
| `SKILL.md:17` | 第 1 步和锁定基准点的动作已保留 |
| `SKILL.md:19` | 用户说法决定基准点、六类示例和未指定时询问用户均已保留 |
| `SKILL.md:21` | 三点 diff、merge-base 原因和提交清单命令均已保留 |
| `SKILL.md:23` | rev-parse、非空 diff、错误 ref 与空 diff 必须在派发前失败均已保留 |
| `SKILL.md:25` | 第 2 步和找出 spec 来源已保留 |
| `SKILL.md:27` | 按顺序寻找的要求已保留 |
| `SKILL.md:29` | 提交信息中三类 issue 引用和按 tracker 文档取得内容已保留 |
| `SKILL.md:30` | 用户传入的路径已保留 |
| `SKILL.md:31` | 三个目录和分支名称或功能匹配条件均已保留 |
| `SKILL.md:32` | 没找到时询问、用户确认无 spec、跳过 Spec subagent 和固定报告文字均已保留 |
| `SKILL.md:34` | 第 3 步和找出标准来源已保留 |
| `SKILL.md:36` | 仓库内代码写法文档的定义和两个示例均已保留 |
| `SKILL.md:38` | 仓库标准之外始终携带、Fowler 出处、固定集合和无仓库文档时仍适用均已保留 |
| `SKILL.md:40` | 仓库规则优先、冲突时仓库获胜和抑制代码异味均已保留 |
| `SKILL.md:41` | 启发法标签、非硬性违规、Feature Envy 示例和跳过工具强制项均已保留 |
| `SKILL.md:43` | 每项异味的定义到修法顺序和对照 diff 的动作均已保留 |
| `SKILL.md:45` | Mysterious Name 的定义、重命名修法和无法诚实名命时的含义均已保留 |
| `SKILL.md:46` | Duplicated Code 的跨区块或文件定义与提取共享形状修法均已保留 |
| `SKILL.md:47` | Feature Envy 的定义与移动方法修法均已保留 |
| `SKILL.md:48` | Data Clumps 的字段参数同行定义、类型暗示和组合类型修法均已保留 |
| `SKILL.md:49` | Primitive Obsession 的定义和建立小型领域类型修法均已保留 |
| `SKILL.md:50` | Repeated Switches 的 switch、if 级联定义和多态或共享映射修法均已保留 |
| `SKILL.md:51` | Shotgun Surgery 的分散改动定义和集中 module 修法均已保留 |
| `SKILL.md:52` | Divergent Change 的多种无关原因定义和按原因拆 module 修法均已保留 |
| `SKILL.md:53` | Speculative Generality 的超出 spec 定义和删除、重新内联修法均已保留 |
| `SKILL.md:54` | Message Chains 的链式示例、调用方依赖问题和首对象封装修法均已保留 |
| `SKILL.md:55` | Middle Man 的委托定义和直接调用真实目标修法均已保留 |
| `SKILL.md:56` | Refused Bequest 的继承忽略定义和组合修法均已保留 |
| `SKILL.md:58` | 第 4 步、两个 subagent 和并行要求均已保留 |
| `SKILL.md:60` | 一条消息、两次 Agent 调用和两者都用 general-purpose 均已保留 |
| `SKILL.md:62` | Standards subagent prompt 及其包含项引导已保留 |
| `SKILL.md:64` | 完整 diff 命令和提交清单已保留 |
| `SKILL.md:65` | 标准来源、完整粘贴异味基线和 subagent 无其他访问方式均已保留 |
| `SKILL.md:66` | 两类报告、文件或区块定位、标准引用、异味命名与引用、硬性违规和需要判断事项的区分、仓库优先、跳过工具项和 400 词限制均已保留 |
| `SKILL.md:68` | Spec subagent prompt 及其包含项引导已保留 |
| `SKILL.md:70` | diff 命令和提交清单已保留 |
| `SKILL.md:71` | spec 路径或取得的正文已保留 |
| `SKILL.md:72` | 缺失或部分需求、scope creep、错误实现、每项引用 spec 行和 400 词限制均已保留 |
| `SKILL.md:74` | 无 spec 时跳过 Spec subagent 并在最终报告注明已保留 |
| `SKILL.md:76` | 第 5 步和汇总已保留 |
| `SKILL.md:78` | 两个固定标题、原样或轻微整理、禁止合并和重新排序以及两轴有意分开均已保留 |
| `SKILL.md:80` | 一行总结、每轴总数、每轴内部最严重问题和禁止跨轴选唯一问题均已保留 |
| `SKILL.md:82` | “为何使用两条轴”标题已保留 |
| `SKILL.md:84` | 一条轴通过而另一条失败的可能性已保留 |
| `SKILL.md:86` | Standards 通过而 Spec 失败的例子已保留 |
| `SKILL.md:87` | Spec 通过而 Standards 失败的例子已保留 |
| `SKILL.md:89` | 分开报告防止彼此掩盖已保留 |
| `agents/openai.yaml:1` | `interface` 字段已保留 |
| `agents/openai.yaml:2` | `display_name: "Code Review"` 已保留 |
| `agents/openai.yaml:3` | 短描述中的 diff、Standards 和 Spec 两条轴均已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的每个非空行都有对应译文和独立检查记录 |
| 增写 | 无。没有加入 MMW 六道审查、MMW 角色、报告验证或人工审批关卡 |
| 曲解 | 无。两条审查轴保持隔离，汇总阶段没有合并 findings 或跨轴重新排序 |
| 术语漂移 | 无。Standards、Spec、基准点、subagent、finding 和代码异味基线使用一致 |
