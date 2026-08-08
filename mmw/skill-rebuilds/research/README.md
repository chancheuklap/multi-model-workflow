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
