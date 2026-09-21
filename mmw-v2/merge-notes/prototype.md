# prototype

源目录：`mmw-v2/upstream/skills/engineering/prototype/`

## 总原则

上游的 prototype 是**用完就扔**的：答完一个问题就推到 throwaway branch，main 只留决定。
我们的 prototype **长期留在仓库里、持续迭代**，正式代码写的时候拿它当参考。

所以上游的提交分两类，取舍相反：

- 改**怎么做**（演示页的版式、纯模块的形状、variant 生成、切换条行为、子形态判断）→ **收上游**。
- 改**prototype 是什么、怎么处置**（throwaway、primary source、throwaway branch、capture、dispose）→ **弃上游，保我们的**。

一个例外：上游第 6 步「删掉 prototype 代码」这个动作我们**收**，只是时机与范围不同——上游在第 6 步删住在 `src/` 里的 variant 本体（所以它需要 throwaway branch 接住），我们在第 7 步、第一次 pull 之后才删 mount point 那几行（variant 本来就在 leaf directory，不用接）。上游改这个动作的措辞可跟，收到第 7 步。

通用约束，任何一段都不让步：全英文；不写测试（测试是正式代码落地时的事）；改动只落在必要的句子上，不重写段落。

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter `description` | 三类触发：逻辑、UI、实现方式。上游改措辞可跟，但第三类不能丢。改它要重开会话 |
| 首句「A prototype is …」 | 不用 throwaway 的说法；写明它留在仓库、持续迭代，正式代码以它为参考 |
| Pick a branch | 三枝，第三枝指向 `EXP.md`；兜底规则里库/算法/集成 → experiment |
| 标题「Rules that apply to …」、规则 2、规则 5 | 覆盖三枝（every branch；experiment 也一条命令起；experiment 每次跑写 evidence page） |
| 规则 2「A logic demo is …」 | host 能发布就是在线页，否则双击 |
| 规则 1 | 存放约定：leaf directory `prototypes/<task>/<issue>/<UI\|LOGIC\|EXP>/` + leaf `README.md`，`<issue>` 是 ticket number；`<task>` 是这次工作的目录名（小写 ASCII 单词用 `-` 连），来源分级按「有没有 wayfinder map」判，不按「有没有 ticket」（map 的 `## Notes` 写的那个 → 问 user → 分支名，`/` 换 `-`）；main 上先停；UI 自建路由仍守项目路由约定 |
| 规则 4 | 保留「无测试」并写明测试归正式代码；「不抽象」放宽为「复用部分要有清楚边界」 |
| 规则 6 | 结论进 leaf `README.md`；决定并进正式代码并按正式标准重写；落地后 leaf directory 是 prototype 唯一的家；有 ticket 就把 leaf directory 链为 asset。**没有** throwaway branch |

### LOGIC.md

| 段落 | 我们的意图 |
| --- | --- |
| 第 1 步 | 问题同时写进 leaf `README.md` |
| 第 3 步第二段（新增）、第 4 步首句 | 文件写进 leaf directory 是源头；host 能把文件发布成在线交互页就发布交链接，否则交文件。按能力措辞，不写 host 名 |
| 第 2 步「The page around it is …」 | 页面是壳，纯模块是正式代码的来源；不用 throwaway 措辞 |
| 第 3 步「Write it for a non-developer」之后新增段（`The reader knows nothing about this topic.` 起） | 我们加的整段。上游只说用 domain language、用平白的话解释，没定图和字的分工；这段定：图管是什么与怎么连，字只做图做不到的三件事（图答的是哪个问题、重点在哪、由此得出什么），字重复图就删字，图要一段话才看得懂就重画。四个用 HTML 做解释的技能放的是同一段。上游改「Write it for a non-developer」那段 → 收上游，这一段原样接在后面 |
| 第 5 步 | 纯模块是正式模块的写作来源；HTML 壳留在 leaf directory，下一轮还能跑 |
| 第 2–4 步其余内容、反模式 | 上游的，照收 |

### UI.md

| 段落 | 我们的意图 |
| --- | --- |
| 开头「throws the rest away」 | 没赢的 variant 留作参考 |
| 子形态 B 及第 16 行「throwaway route」 | 叫 prototype route；其余判断照收 |
| 第 3 步 sub-shape B 那句 | 删掉 `/prototype/<name>` 这个路径，只留「B 也挂同一个切换条」。路径规则的唯一出处是子形态 B 那节（跟项目现有约定走，别造新顶层）；写在这里会和它冲突——B 的前提就是项目里还没有这类页面，`/prototype/` 必然是新顶层。上游若改这句措辞，仍然只收挂载语义，不收路径 |
| 第 2 步末句 | 样式用变量，界面按可复用组件拆，需要时可以从它建 design system。上游没有这一句 |
| `## Two sub-shapes` 之下的 `### When there is no app yet` | 我们加的：全新产品还没有 app——子形态 A 要一个已有路由，B 要「the project's routing convention」，两个都假定 app 已存在。这时 variant 是 leaf directory `prototypes/<task>/<issue>/UI/` 里的独立页面，用这次工作已定的技术栈写，共用一个切换条；leaf directory 之外没有东西挂它们，第 7 步没有 scaffolding 可拆。理由：按「从零做一个新产品」走一遍真实流程时，agent 在这里只能自造一个路由结构，而子形态 B 明写不许造新顶层。上游改子形态一节 → 收上游措辞，这一小节接在后面 |
| 第 3 步末尾新增段 | variant 组件住在 leaf directory，路由只留 mount point；mount point 连同 symlink 定性为 scaffolding，第 7 步拆掉；import 不过去就 symlink；迭代只改 leaf directory |
| `SKILL.md` 第 6 条 | UI prototype 的 winner 不在这里折进真实代码，而是交给 Claude Design、再从拿回来的 design page 写真实代码（指向 `UI.md` 第 6、7 步）。上游只写「折进真实代码」，对 LOGIC 与 EXP 仍然成立，所以收上游措辞、保留这一句 |
| 第 6 步第二段 | winning variant 进 Claude Design 时 scaffolding 保留到第 7 步：跑着的 winner 是画页面时的参照，从它建 design system 时读它的样式与组件。上游没有这一段 |
| 第 6 步 | 结论进 leaf `README.md`；`## State list`；点名 `design-pages`。上游仍在这一步把 winner 折进真实代码并拆 scaffolding → 不收那一半，收到第 7 步 |
| 第 6 步 `## State list` | README 在固定标题 `## State list` 下按区域列出 winning variant 的全部状态：每个区域一个三级标题（即之后 `Component · <区域>` 页名），每个状态一个列表项且以状态名开头。`scene` prop、pull report、会改变页面状态的 decision ticket 都按这些名字核对。一个界面只有一份 state list：有 wayfinder map 时写在 handoff ticket 的 leaf `README.md`，汇总 map 上每张 UI prototype 票的 winner；每张 prototype 票自己的 leaf `README.md` 留结论并写明定了哪些区域（任务板试点 #541：`design-pages` 与 pull 只认一份）。上游没有这一段 |
| 第 7 步「拆 scaffolding」 | 由原第 6 步后半段拆出。第一次 pull 之后才执行；`design-pages` 的 `pull.md` 指回这里，正文不写这一句（读到这一步的 agent 正是从那里来的）。挂在已有页面上的删挂载点、切换条与 import；单独路由的删 prototype 路由与切换条；完成条件是 leaf directory 外无人 import。上游把拆 scaffolding 写在第 6 步；我们改到第 7 步且改时机。上游改原第 6 步后半段措辞 → 收到第 7 步 |
| `## Next`（文末） | 我们加的整节：winner 要进 Claude Design 时，点名 `design-pages` 技能的 **edit pages** 入口（建用户在里面设计的项目；winner 留在 scaffolding 后面当参照只写在第 6 步第二段，这里不重复）、可选的 **design system** 入口（需要时由 Claude Design 里的 agent 从 winner 的代码建，ADR 0030）与 **pull** 入口（拉回并指回第 7 步）；UI 的 winner 一律进 Claude Design（与 `SKILL.md` 规则 6、ask-matt 一致），所以这一节没有“不进 Claude Design 的 winner”分支。理由：原来全文没有往下一步的出口，唯一的路藏在第 6 步讲 scaffolding 的从句里。design system 不是前置步骤：拉回、合同与验收都不读它，设计本身由用户在 Claude Design 里做（任务板试点 #541，2026-09-21）。上游给 `UI.md` 加收尾步 → 收上游措辞，这一节接在它后面 |
| 第 1、4、5 步、反模式 | 上游的，照收 |

### EXP.md、evidence-page.md

两个文件整个是我们的，上游没有。上游若新增同名文件，按「怎么做」归类逐段比对后合并，结构以我们的五步为准。

### agents/openai.yaml

未改。
