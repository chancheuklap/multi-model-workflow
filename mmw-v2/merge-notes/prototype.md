# prototype

源目录：`mmw-v2/upstream/skills/engineering/prototype/`

## 总原则

上游的 prototype 是**用完就扔**的：答完一个问题就推到 throwaway branch，main 只留决定。
我们的 prototype **长期留在仓库里、持续迭代**，正式代码写的时候拿它当参考。

所以上游的提交分两类，取舍相反：

- 改**怎么做**（演示页的版式、纯模块的形状、variant 生成、切换条行为、子形态判断）→ **收上游**。
- 改**prototype 是什么、怎么处置**（throwaway、primary source、throwaway branch、capture、dispose）→ **弃上游，保我们的**。

一个例外：上游第 6 步「删掉 prototype 代码」这个动作我们**收**，只是时机、范围与位置不同——上游在第 6 步删住在 `src/` 里的 variant 本体（所以它需要 throwaway branch 接住），我们在第一次 pull 之后才删 mount point 那几行（variant 本来就在 leaf directory，不用接），这一步写在 `design-pages` 技能 `references/pull.md` 的 **After the first pull**，不在 `UI.md` 里。上游改这个动作的措辞可跟，收到那一节。

通用约束，任何一段都不让步：全英文；不写测试（测试是正式代码落地时的事）；改动只落在必要的句子上，不重写段落。

原型做完之后交给哪个技能或 playbook、结论怎样进正式代码，不写在这个技能里：写在 `mmw` 技能的 playbook **Prototype**（`mmw-v2/skills/mmw/playbooks/prototype.md` 的 **Hand the answer on**）与 **Design a UI**。所以 `UI.md` 不设 `## Next`，第 3 步也不点名 `design-pages` 技能；`SKILL.md` 规则 6 只写结论记在哪、原型留在哪，原型会话不改正式代码。

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter `description` | 三类触发：逻辑、UI、实现方式。上游改措辞可跟，但第三类不能丢。改它要重开会话 |
| 首句「A prototype is …」 | 不用 throwaway 的说法；写明它留在仓库、持续迭代，正式代码以它为参考 |
| Pick a branch | 三枝，第三枝指向 `EXP.md`；兜底规则里库/算法/集成 → experiment |
| 标题「Rules that apply to …」、规则 2（**Trivial to run.**）、规则 5（**Surface the state.**） | 覆盖三枝（every branch；experiment 也一条命令起；experiment 每次跑写 evidence page） |
| 规则 2「A logic demo is …」 | host 能发布就是在线页，否则双击 |
| 规则 1 | 存放约定：leaf directory `prototypes/<effort>/<issue>/<UI\|LOGIC\|EXP>/` + leaf `README.md`，`<issue>` 是 ticket number；`<effort>` 是这次工作的目录名，`prototypes/` 与 `docs/specs/` 下同名（小写 ASCII 单词用 `-` 连；`design-pages` 的 existing product 一步指回这一条，`write-screen-contract` 与 `design-pages` 的 pull 从已存在的 `prototypes/<effort>/` 目录读出它，都不另写推导），来源分级按「有没有 wayfinder map」判，不按「有没有 ticket」（map 的 `## Notes` 写的那个 → 问 user → 分支名，`/` 换 `-`）；UI 自建路由仍守项目路由约定 |
| 规则 4（**Skip the polish.**） | 保留「无测试」并写明测试归正式代码；「不抽象」放宽为「复用部分要有清楚边界」 |
| 规则 6（**Record the answer, keep the prototype**） | 结论进 leaf `README.md`；leaf directory 是 prototype 的家，下一轮同一个问题在它上面迭代；有 ticket 就把 leaf directory 链为 asset。**没有** throwaway branch。上游这一条的「Fold any validated decision into the real code」不收：原型会话不改正式代码，LOGIC、EXP 的结论进 spec 或小改动、UI 的 winner 进 Claude Design，都由 playbook **Prototype** 的 **Hand the answer on** 交出。leaf `README.md` 的下游读者句（`to-spec` 引用它、`to-tickets` 从它复制精确值、worker 夜里照它的结论施工）也加在这里：技能只说"write the verdict"，没说给谁看、按什么用，实际用例（`prototypes/task-board/546` 到 `551` 那几份）只写了指向 tracker 评论的指针，读不到决定本身 |

### LOGIC.md

| 段落 | 我们的意图 |
| --- | --- |
| 第 1 步（`### 1. State the question`） | 问题同时写进 leaf `README.md` |
| 第 3 步（`### 3. Build the shareable HTML file`）第二段（新增）、第 4 步（`### 4. Hand it over`）首句 | 文件写进 leaf directory 是源头；host 能把文件发布成在线交互页就发布交链接，否则交文件。按能力措辞，不写 host 名 |
| 第 2 步（`### 2. Isolate the logic in a portable module`）「The page around it is …」 | 页面是壳，纯模块是正式代码的来源；不用 throwaway 措辞 |
| 第 5 步（`### 5. Capture the answer and the prototype`） | 纯模块是正式模块的写作来源；HTML 壳留在 leaf directory，下一轮还能跑 |
| 第 2–4 步其余内容、反模式 | 上游的，照收 |

### UI.md

| 段落 | 我们的意图 |
| --- | --- |
| 开头（`# UI Prototype`）「throws the rest away」 | 没赢的 variant 留作参考 |
| 子形态 B（`### Sub-shape B: a new page (last resort)`）及 `## Two sub-shapes: strongly prefer sub-shape A` 里的「throwaway route」 | 叫 prototype route；其余判断照收 |
| 第 3 步（`### 3. Wire them together`）sub-shape B 那句 | 删掉 `/prototype/<name>` 这个路径，只留「B 也挂同一个切换条」。路径规则的唯一出处是子形态 B 那节（跟项目现有约定走，别造新顶层）；写在这里会和它冲突——B 的前提就是项目里还没有这类页面，`/prototype/` 必然是新顶层。上游若改这句措辞，仍然只收挂载语义，不收路径 |
| 第 2 步（`### 2. Generate radically different variants`）末句 | 样式用变量，界面按可复用组件拆，需要时可以从它建 design system。上游没有这一句 |
| `## Two sub-shapes` 之下的 `### When there is no app yet` | 我们加的：全新产品还没有 app——子形态 A 要一个已有路由，B 要「the project's routing convention」，两个都假定 app 已存在。这时 variant 是 leaf directory `prototypes/<effort>/<issue>/UI/` 里的独立页面，用这次工作已定的技术栈写，共用一个切换条；leaf directory 之外没有东西挂它们（拆 scaffolding 的时机只写在 `design-pages` 的 `pull.md`，这里不重复）。理由：按「从零做一个新产品」走一遍真实流程时，agent 在这里只能自造一个路由结构，而子形态 B 明写不许造新顶层。上游改子形态一节 → 收上游措辞，这一小节接在后面 |
| 第 3 步末尾新增段 | variant 组件住在 leaf directory，路由只留 mount point；mount point 连同 symlink 定性为 scaffolding；import 不过去就 symlink；迭代只改 leaf directory。这一段不写 scaffolding 什么时候拆：第 6 步第二段说它留到第一次 pull，拆的做法在 `design-pages` 技能 `references/pull.md` 的 **After the first pull** |
| 第 6 步第二段 | winning variant 一律进 Claude Design，所以 scaffolding 保留到第一次 pull：跑着的 winner 是画页面时的参照，从它建 design system 时读它的样式与组件。上游没有这一段 |
| 第 6 步（`### 6. Capture the answer`） | 结论进 leaf `README.md`。上游仍在这一步把 winner 折进真实代码并拆 scaffolding → 不收那一半，拆 scaffolding 收到 `design-pages` 的 `references/pull.md` **After the first pull** |
| 拆 scaffolding（上游第 6 步后半段） | `UI.md` 里没有这一步：它写在 `design-pages` 技能 `references/pull.md` 的 **After the first pull**，由第一次 pull 之后拉回设计的 agent 执行。UI prototype 的 agent 从不执行它，写在 `UI.md` 里只会让每次拉回为这几行多读一整份别的技能的文件。删 mount point 或 prototype 路由、切换条、leaf directory 的 import 与路由旁的 symlink；完成条件是 leaf directory 外无人 import。上游改原第 6 步后半段措辞 → 收到那一节 |
| 第 1、4、5 步、反模式 | 上游的，照收 |

### EXP.md、evidence-page.md

两个文件整个是我们的，上游没有。`EXP.md` 的反模式不列「不加测试」与「别把结果只留在脑子里」：前者是 `SKILL.md` 规则 4，后者是第 4 步的 `Done when`「每行都有观察」与第 5 步重写 **Conclusion**，再列一遍只是多一份要同步的副本。五步各以一行 `Done when` 收尾，是本仓库自己文字的写法。上游若新增同名文件，按「怎么做」归类逐段比对后合并，结构以我们的五步为准。

### agents/openai.yaml

未改。
