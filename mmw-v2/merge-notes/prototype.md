# prototype

源目录：`mmw-v2/upstream/skills/engineering/prototype/`

## 总原则

上游的 prototype 是**用完就扔**的：答完一个问题就推到一次性分支，main 只留决定。
我们的 prototype 是**仓库内长期保存、持续迭代的研究件**，正式代码写的时候拿它当参考。

所以上游的提交分两类，取舍相反：

- 改**怎么做**（演示页的版式、纯模块的形状、变体生成、切换条行为、子形态判断）→ **收上游**。
- 改**原型是什么、怎么处置**（throwaway、primary source、一次性分支、capture、dispose）→ **弃上游，保我们的**。

通用约束，任何一段都不让步：全英文；不写测试（测试是正式代码落地时的事）；改动只落在必要的句子上，不重写段落。

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter `description` | 三类触发：逻辑、UI、实现方式。上游改措辞可跟，但第三类不能丢。改它要重开会话 |
| 首句「A prototype is …」 | 去掉 throwaway；说明它留在仓库、持续迭代、正式代码以它为参考 |
| Pick a branch | 三枝，第三枝指向 `EXP.md`；兜底规则里库/算法/集成 → experiment |
| 标题「Rules that apply to …」、规则 2、规则 5 | 覆盖三枝（every branch；experiment 也一条命令起；experiment 每次跑都打印状态） |
| 规则 1 | 存放约定 `prototypes/<task>/<issue>/<UI\|LOGIC\|EXP>/` + 叶子 `README.md`；`<task>` 的来源顺序（wayfinder 地图标题 → 问用户 → 分支名，`/` 换 `-`）；main 上先停；UI 自建路由仍守项目路由约定 |
| 规则 4 | 保留「无测试」并写明测试归正式代码；「不抽象」放宽为「复用部分要有清楚边界」 |
| 规则 6 | 结论进叶子 README；决定并进正式代码并按正式标准重写；原型原地保留可再跑；有 ticket 就把目录链为 asset。**没有**一次性分支 |

### LOGIC.md

| 段落 | 我们的意图 |
| --- | --- |
| 第 1 步 | 问题同时写进叶子 README |
| 第 2 步「The page around it is …」 | 页面是壳，纯模块是正式代码的来源；去掉 throwaway 措辞 |
| 第 5 步 | 纯模块是正式模块的写作来源；HTML 壳留在叶子目录，下一轮还能跑 |
| 第 2–4 步其余内容、反模式 | 上游的，照收 |

### UI.md

| 段落 | 我们的意图 |
| --- | --- |
| 开头「throws the rest away」 | 输家留作参考 |
| 子形态 B 及第 16 行「throwaway route」 | 叫 prototype route；其余判断照收 |
| 第 3 步末尾新增段 | 变体组件住在叶子目录，路由只留挂载点；import 不过去就软链；迭代只改叶子目录 |
| 第 6 步 | 结论进叶子 README；赢家按正式标准重写进页面；挂载点/原型路由留着（有 production 门控）；全套变体留在叶子目录 |
| 第 1、2、4、5 步、反模式 | 上游的，照收 |

### EXP.md

整个文件是我们的，上游没有。上游若新增同名文件，按「怎么做」归类逐段比对后合并，结构以我们的五步为准。

### agents/openai.yaml

未改。
