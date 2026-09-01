# prototype

源目录：`mmw-v2/upstream/skills/engineering/prototype/`

## 总原则

上游的 prototype 是**用完就扔**的：答完一个问题就推到 throwaway branch，main 只留决定。
我们的 prototype **长期留在仓库里、持续迭代**，正式代码写的时候拿它当参考。

所以上游的提交分两类，取舍相反：

- 改**怎么做**（演示页的版式、纯模块的形状、variant 生成、切换条行为、子形态判断）→ **收上游**。
- 改**prototype 是什么、怎么处置**（throwaway、primary source、throwaway branch、capture、dispose）→ **弃上游，保我们的**。

一个例外：上游第 6 步「删掉 prototype 代码」这个动作我们**收**，只是范围不同——上游删的是住在 `src/` 里的 variant 本体（所以它需要 throwaway branch 接住），我们删的只是 mount point 那几行（variant 本来就在 leaf directory，不用接）。上游改这个动作的措辞可跟。

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
| 规则 1 | 存放约定：leaf directory `prototypes/<task>/<issue>/<UI\|LOGIC\|EXP>/` + leaf `README.md`，`<issue>` 是 ticket number；`<task>` 的来源分级按「有没有 wayfinder map」判，不按「有没有 ticket」（map 标题 → 问 user → 分支名，`/` 换 `-`）；main 上先停；UI 自建路由仍守项目路由约定 |
| 规则 4 | 保留「无测试」并写明测试归正式代码；「不抽象」放宽为「复用部分要有清楚边界」 |
| 规则 6 | 结论进 leaf `README.md`；决定并进正式代码并按正式标准重写；落地后 leaf directory 是 prototype 唯一的家；有 ticket 就把 leaf directory 链为 asset。**没有** throwaway branch |

### LOGIC.md

| 段落 | 我们的意图 |
| --- | --- |
| 第 1 步 | 问题同时写进 leaf `README.md` |
| 第 3 步第二段（新增）、第 4 步首句 | 文件写进 leaf directory 是源头；host 能把文件发布成在线交互页就发布交链接，否则交文件。按能力措辞，不写 host 名 |
| 第 2 步「The page around it is …」 | 页面是壳，纯模块是正式代码的来源；不用 throwaway 措辞 |
| 第 5 步 | 纯模块是正式模块的写作来源；HTML 壳留在 leaf directory，下一轮还能跑 |
| 第 2–4 步其余内容、反模式 | 上游的，照收 |

### UI.md

| 段落 | 我们的意图 |
| --- | --- |
| 开头「throws the rest away」 | 没赢的 variant 留作参考 |
| 子形态 B 及第 16 行「throwaway route」 | 叫 prototype route；其余判断照收 |
| 第 3 步 sub-shape B 那句 | 删掉 `/prototype/<name>` 这个路径，只留「B 也挂同一个切换条」。路径规则的唯一出处是子形态 B 那节（跟项目现有约定走，别造新顶层）；写在这里会和它冲突——B 的前提就是项目里还没有这类页面，`/prototype/` 必然是新顶层。上游若改这句措辞，仍然只收挂载语义，不收路径 |
| 第 3 步末尾新增段 | variant 组件住在 leaf directory，路由只留 mount point；mount point 连同 symlink 定性为 scaffolding，第 6 步拆掉；import 不过去就 symlink；迭代只改 leaf directory |
| 第 6 步首段新增句 | winning variant 要移植进 Claude Design 时，先跑 `claude-design-blocks` 再拆 scaffolding：那个技能靠 `?variant=<winner>` 打开真实页面取 CSS 和 DOM，mount point 拆早了取回来的就是重写后的正式实现。上游没有这一句 |
| 第 6 步 | 结论进 leaf `README.md`；winning variant 按正式标准重写进页面；拆掉 mount point、切换条、symlink、prototype route，完成条件是 leaf directory 外无人 import 且 leaf directory 随时可删；全套 variant 留在 leaf directory |
| 第 1、2、4、5 步、反模式 | 上游的，照收 |

### EXP.md、evidence-page.md

两个文件整个是我们的，上游没有。上游若新增同名文件，按「怎么做」归类逐段比对后合并，结构以我们的五步为准。

### agents/openai.yaml

未改。
