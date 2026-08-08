# Research 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Research。当前发布技能仍位于 `mmw/skills/mmw-research/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐段中文翻译。第二阶段已经建立精简稿；精简稿只移除翻译基线中的出处标注，不删改上游方法内容。第三阶段从精简稿建立按 agent 身份渐进加载的接线候选；候选材料仍不参与 Plugin 运行。

`../candidate/skills/mmw-research/SKILL.md` 直接按身份路由到 `MAIN.md`、`INTERNAL.md` 或 `EXTERNAL.md`，不再经过一层只做方向判断的中转文件。

保存不是无条件询问：来自 `wayfinder:research` ticket 的 research 直接保存，因为那张 ticket 本身就是用户对这次调查的批准，而且它是 AFK，并行派出的多张 research ticket 不能各自停下来等人回答。其余情况仍要问过用户再落盘。

实测取证（`EVIDENCE.md`）从 `/mmw-prototype` 移到这里。理由是它验的对象跟 research 一样，是外部世界既有的事实，不是我们自己要写的东西；prototype 验的是我们自己那套东西成不成立，靠的是用户走查，两者的判据完全不同。移过来之后：

- 入口在 `MAIN.md` 第 1 节的问题分类表，只有"必须把外部系统真跑起来、而且有一项决定被卡住"才转进去。
- 台账和测试计划写在 `mmw path research` 底下，不再单开 `mmw path evidence`。
- `EXTERNAL.md` 的边界改写成**只读**：`investigator` 可以跑只读命令，但要动真实凭证、生产环境、费用、写入外部系统、施加负载或多轮测量时一律停下来交回主 agent。
- 要动真实凭证、连生产、上真机、产生费用或写入外部系统数据时，必须停下来等用户点头。`wayfinder:research` 的 AFK 免掉的是"要不要保存"这种问题，免不掉这一关。

## 接手与移交的复查

把 `EVIDENCE.md` 接进来之后，对着全部调用方复查了一遍 `MAIN.md` 第 1 节的路由，改了这几处：

- 补一行移交 `/mmw-diagnosing-bugs`。原来"查一个东西为什么坏"没有任何出口，research 会把它接下来当普通调查做。
- 补一行兜底。原来最后一行是正面清单（多角度、多份一手资料），只有一个角度的调查会落空，agent 有可能退回调用方。
- "一条命令就能答"那一行加了例外：问题来自 `wayfinder:research` ticket 时，拿到事实之后仍然要保存并交回。Wayfinder 的 charting 和 walking 都要往 ticket 评论里写 research 的 `README.md` 路径，原来这条路径会不存在。
- 移交 `/mmw-prototype` 那一行补上要把 `产物目录` 一起交过去，否则 prototype 会重新去找位置。
- 第 4 节原来写死"完成验证和综合后"，而 `EVIDENCE.md` 要在立计划之前就拿到路径，改成不绑时机。
- 第 6 节和「下一步」补上用户直接调用时领域术语的出口。原来只写了"交给调用方"，没有调用方时这句话悬空。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐段中文翻译基线 |
| `translation-audit.md` | 术语选择、逐段完整性与无新增语义检查 |
| `simplified.zh-CN.md` | 移除出处标注、尚未加入 MMW 接线的精简稿 |
| `../candidate/skills/mmw-research/SKILL.md` | 识别当前 agent 是主 agent 还是 `investigator`，只加载对应入口 |
| `../candidate/skills/mmw-research/MAIN.md` | 主 agent 使用的派发、验证、综合、保存和交回流程 |
| `../candidate/skills/mmw-research/EVIDENCE.md` | 主 agent 使用的实测取证流程：立计划、用户批准、真实跑、记台账 |
| `../candidate/skills/mmw-research/INTERNAL.md` | 内部 research 角度特有的源码出处要求，只供 `investigator` 读取 |
| `../candidate/skills/mmw-research/EXTERNAL.md` | 外部 research 角度特有的一手来源要求，只供 `investigator` 读取 |

接线候选由五份技能文件组成。主 agent 读取 `SKILL.md` 和 `MAIN.md`，只有转进实测时才加读 `EVIDENCE.md`。`investigator` 只读取 `SKILL.md` 和 task 指定的 `INTERNAL.md` 或 `EXTERNAL.md`；原来那份只做方向判断的 `INVESTIGATOR.md` 已并入 `SKILL.md`。正式技能源保持不变，等待用户审查候选后再决定是否进入 Plugin 发布面。

Claude Code 派出的 headless Codex 也必须读取这五份文件。候选安装清单已加入 `mmw-research`，避免 `investigator` 只能收到 task，却找不到身份路由和方向 reference。

## 2026-08 复审确认的两处有意改写

1. **落点固定化**：上游要求单文件、落点匹配仓库既有笔记惯例；候选写死 `docs/research/<产物目录>/…` 多文件结构。理由：spec、plan、审查、实现都按精确路径消费 research，落点必须确定，这是 MMW 工作流对上游方法的取舍，用户已确认。
2. **INTERNAL 方向**：上游把 research 定位为查工作目录之外的事实；候选新增调查本仓库自身的内部方向。属范围扩张，用户已确认。

## 2026-08 路由重构（入口合同表）

用户审查发布面后确认：调用方差异散在 `MAIN.md` 第 1、4、5、6、7 节的例外分句里，没有一处告诉 agent 自己属于哪类调用方；第 1 节第 2 行把过滤、ticket 例外和理由嵌成一格，无法阅读。本轮在候选目录做了下列改动：

- `MAIN.md` 新增第 0 节入口合同表：五行入口（wayfinder ticket、带 `产物目录` 的技能调用、不带的技能调用、用户直接调用、兜底），四列合同（手上保证有的、research 路径的上一级、保存、交回）。第 1、4、5、7 节的来源分叉全部收进这张表，各节只引用列名。原第 4 节那张没有兜底行的三行取值表删除，其兜底由合同表兜底行承担。
- `MAIN.md` 第 1 节第 2 行拆开：取证方式（自己查、不派 `investigator`）与后续处置（ticket 入口走保存交回、其他入口直接交回）分成两句，理由上移到第 0 节表后那段「ticket 无条件进入」说明。原「其余情况拿到事实就结束」与第 7 节交回合同的矛盾随之消除：统一为按「交回」列交回。
- `MAIN.md` 开篇改为描述完整流程（认领入口、定问题、取证、验证、保存、交回），不再只写派发。原开篇把「启动后台 `investigator`」写成全文前提，与第 1 节四条不派发的分支冲突。
- `MAIN.md` 第 6 节 `README.md` 行补一句绑定：它就是各技能引用的 research 索引。此前该词只在 `mmw-to-tickets` 与领域文档 `delivery-workflow.md` 中定义，生产者自己未绑定。
- 术语「落点」全部改为领域文档 canonical 的「research 路径」（拥有方：`docs/context/delivery-workflow.md`）；「过程材料路径」统一为「scratch 路径」。
- `EVIDENCE.md` 第 1 节删除自带的 scratch 形状定义（`.scratch/<产物目录>/<子目录>`，「同两个值」）。它与 `MAIN.md` 第 6 节的规则冲突：非 wayfinder 入口下「同两个值」取不出值，也无视调用方传入的 scratch 路径。去向：scratch 路径的唯一定义保留在 `MAIN.md` 第 6 节，`EVIDENCE.md` 引用它。
- `EVIDENCE.md` 第 3 节占位符「这次战役的名字」改为「本轮实测的短名」，补取名规则（按被测对象或口径取，单个路径段，字符规则同 `MAIN.md` 第 4 节）。原词全仓库仅此一处，无定义。

消费者检查：原第 4 节取值表被删，它承担的取值问题全部由合同表接手，逐行核对无遗漏；charting 侧「明确写一句直接保存」的指示同轮删除（见 wayfinder 台账），其功能由合同表 ticket 行接手；`MAIN.md` 第 5 节「调用方明确传入直接保存」分支保留在合同表第二行，仍有消费者。

发布时同步：`docs/context/wayfinding.md` 的 `wayfinder:research` 定义仍写「需要当前工作目录之外的知识」，与本轮扩张后的判据不一致。候选进入发布面时按 `/mmw-domain-modeling` 更新该 leaf。
