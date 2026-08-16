# Research 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Research。当前发布技能仍位于 `mmw/skills-src/mmw-research/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（一份 `SKILL.md`，12 行）。候选是 **1 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)，按将来位于 `mmw/skills-src/mmw-research/SKILL.md` 书写。现役五文件技能源未改。

上游三步原文留下。第 1 步末尾加「Source code includes this repo.」第 3 步的约定：每个 Explore 写 `--sub <topic>/<slug>.md`；主 agent 写 `--sub <topic>/README.md`。

主 agent 的步骤按 1–6 写。`README.md` 是 research 目录的索引（问题 + 文件清单），由主 agent 写。每个 Explore 各写一份 findings 文件。两者不是同一份文档。开篇写清这一点。

已叠进候选的接线：

- 后台是一组 **Explore**，点名即可。不是 `investigator`，也不用 `[[mmw-launch:investigator:…]]`。Explore 是各宿主内置角色，不进 `roles.json`。
- 派发是一组，不是单独一个。互不依赖的问题：一个 Explore 一个，同一组、同一轮。只传问题和该 agent 的 findings 路径，不传文件清单，不传 README 路径。
- 调查结果由 Explore 写盘。主 agent 不重写 findings，不把 findings 抄进 README。
- 主 agent 写 `README.md`：只作索引。下游点名 README，再读它列出的文件。
- `wayfinder:research` 直接保存。其余先问再落盘。
- 动真实凭证、生产、花钱、写仓库外数据：先问用户，再派。
- 无 `report.md`、无章节指引、无 `MAIN.md` / `INTERNAL.md` / `EXTERNAL.md` / `EVIDENCE.md`。索引是 `README.md`；findings 是每个 Explore 各自那一份 Markdown。
- 首次写入前 `[[mmw-require-task-branch]]`。
- 交回 README 路径。没保存就报告没保存。

未叠：

- 五文件身份路由、入口合同表、主 agent 预填阅读清单。
- 从 research 转到 `/mmw-diagnosing-bugs` 或 `/mmw-prototype`。
- `EVIDENCE.md` 整条实测平行流程。
- 「一条命令就能答就不要派」和 wayfinder ticket 例外互相打架的那一套。
- 四栏 task、综合四步、撞名 `-02`、scratch 清理讲义。
- `[[mmw-launch-group:explore:…]]`。`mmw-launch-group` 目前只认 `reviewers`。点名 Explore 不走占位块。

同轮改了 wayfinder 候选 leaf 一句：`each investigator` → `each research invocation`。grilling 候选未改。

本 worktree 跑过：`bash mmw/cli/mmw artifact path research --name probe --issue 19 --sub topic/README.md` → `docs/research/probe/issue-19/topic/README.md`。

### 发布时的 leaf 与级联（未改现役）

- `docs/context/delivery-workflow.md`：更新 `research` / `research 索引` / `research 目录`；删 `research 报告`、`research 配套文件`、`章节指引`。草稿见 [`candidate/leaf-terms.md`](candidate/leaf-terms.md)。`evidence` 仍写 research 目录下的 `raw/`，留给实测那一轮。
- `docs/context/wayfinding.md`：每一次 research 仍只解决一张 ticket。现役 leaf 已改。
- `docs/context/agent-coordination.md` 的角色例子不再列 `investigator`。
- `investigator` 与 `prototype-worker` 已从 `roles.json`、Codex profile、模型档和 `runtime.py` 删除。research 与 architecture 现役技能改派 Explore。
- `mmw/cli/lib/install-agent-skills.sh` 不再为 research 装 `mmw-research`；Explore 不靠这份清单加载技能。
- `mmw artifact path --help` 例子仍写 `--sub report`。CLI 那一轮改。
- 现役 to-tickets / to-plan / review 若仍点名 `report.md` 或章节指引，各自那一轮改。下游继续可以点名 `README.md`。

本轮不派冷读 subagent。

## 先前阶段（中文重建）

第一阶段：上游逐段中文翻译。第二阶段精简稿只去掉出处标注。第三阶段在 `../candidate/skills/mmw-research/` 做成五文件身份路由，并接入 `EVIDENCE.md`。那些候选不是本轮英文底稿。

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐段中文翻译基线 |
| `translation-audit.md` | 术语选择、逐段完整性与无新增语义检查 |
| `simplified.zh-CN.md` | 移除出处标注、尚未加入 MMW 接线的精简稿 |
| `../candidate/skills/mmw-research/` | 中文五文件候选（`SKILL.md` + `MAIN.md` + `INTERNAL.md` + `EXTERNAL.md` + `EVIDENCE.md`）。不是本轮英文底稿。 |

下面是中文重建台账原文，供对照。英文逆向不再沿用其中的五文件路由、入口合同表和实测平行流程。

### 中文重建当时的阶段说明

`../candidate/skills/mmw-research/SKILL.md` 直接按身份路由到 `MAIN.md`、`INTERNAL.md` 或 `EXTERNAL.md`，不再经过一层只做方向判断的中转文件。

保存不是无条件询问：来自 `wayfinder:research` ticket 的 research 直接保存，因为那张 ticket 本身就是用户对这次调查的批准，而且它是 AFK，并行派出的多张 research ticket 不能各自停下来等人回答。其余情况仍要问过用户再落盘。

实测取证（`EVIDENCE.md`）从 `/mmw-prototype` 移到这里。理由是它验的对象跟 research 一样，是外部世界既有的事实，不是我们自己要写的东西；prototype 验的是我们自己那套东西成不成立，靠的是用户走查，两者的判据完全不同。移过来之后：

- 入口在 `MAIN.md` 第 1 节的问题分类表，只有"必须把外部系统真跑起来、而且有一项决定被卡住"才转进去。
- 台账和测试计划写在 `mmw path research` 底下，不再单开 `mmw path evidence`。
- `EXTERNAL.md` 的边界改写成**只读**：`investigator` 可以跑只读命令，但要动真实凭证、生产环境、费用、写入外部系统、施加负载或多轮测量时一律停下来交回主 agent。
- 要动真实凭证、连生产、上真机、产生费用或写入外部系统数据时，必须停下来等用户点头。`wayfinder:research` 的 AFK 免掉的是"要不要保存"这种问题，免不掉这一关。

### 接手与移交的复查

把 `EVIDENCE.md` 接进来之后，对着全部调用方复查了一遍 `MAIN.md` 第 1 节的路由，改了这几处：

- 补一行移交 `/mmw-diagnosing-bugs`。原来"查一个东西为什么坏"没有任何出口，research 会把它接下来当普通调查做。
- 补一行兜底。原来最后一行是正面清单（多角度、多份一手资料），只有一个角度的调查会落空，agent 有可能退回调用方。
- "一条命令就能答"那一行加了例外：问题来自 `wayfinder:research` ticket 时，拿到事实之后仍然要保存并交回。Wayfinder 的 charting 和 walking 都要往 ticket 评论里写 research 的 `README.md` 路径，原来这条路径会不存在。
- 移交 `/mmw-prototype` 那一行补上要把 `产物目录` 一起交过去，否则 prototype 会重新去找位置。
- 第 4 节原来写死"完成验证和综合后"，而 `EVIDENCE.md` 要在立计划之前就拿到路径，改成不绑时机。
- 第 6 节和「下一步」补上用户直接调用时领域术语的出口。原来只写了"交给调用方"，没有调用方时这句话悬空。

接线候选由五份技能文件组成。主 agent 读取 `SKILL.md` 和 `MAIN.md`，只有转进实测时才加读 `EVIDENCE.md`。`investigator` 只读取 `SKILL.md` 和 task 指定的 `INTERNAL.md` 或 `EXTERNAL.md`；原来那份只做方向判断的 `INVESTIGATOR.md` 已并入 `SKILL.md`。正式技能源保持不变，等待用户审查候选后再决定是否进入 Plugin 发布面。

Claude Code 派出的 headless Codex 也必须读取这五份文件。候选安装清单已加入 `mmw-research`，避免 `investigator` 只能收到 task，却找不到身份路由和方向 reference。

### 2026-08 复审确认的两处有意改写

1. **落点固定化**：上游要求单文件、落点匹配仓库既有笔记惯例；候选写死 `docs/research/<产物目录>/…` 多文件结构。理由：spec、plan、审查、实现都按精确路径消费 research，落点必须确定，这是 MMW 工作流对上游方法的取舍，用户已确认。
2. **INTERNAL 方向**：上游把 research 定位为查工作目录之外的事实；候选新增调查本仓库自身的内部方向。属范围扩张，用户已确认。

### 2026-08 路由重构（入口合同表）

用户审查发布面后确认：调用方差异散在 `MAIN.md` 第 1、4、5、6、7 节的例外分句里，没有一处告诉 agent 自己属于哪类调用方；第 1 节第 2 行把过滤、ticket 例外和理由嵌成一格，无法阅读。那一轮在中文候选目录做了入口合同表、拆开第 1 节第 2 行、改开篇、绑定 `README.md` 为 research 索引、把「落点」改成 `research 路径`，并修了 `EVIDENCE.md` 的 scratch 形状与占位符。

发布时同步：`docs/context/wayfinding.md` 的 `wayfinder:research` 定义仍写「需要当前工作目录之外的知识」，与 INTERNAL 扩张后的判据不一致。英文 wayfinder 候选已经改成「事实可以来自本仓库源码」。
