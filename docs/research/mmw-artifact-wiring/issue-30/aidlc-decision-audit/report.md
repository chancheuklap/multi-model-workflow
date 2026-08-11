# 九个决定与 aidlc-workflows v2 的逐节对照

对照的两侧：

- **aidlc 一侧**：`docs/research/mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/report.md`，十二节。
- **MMW 一侧**：`docs/adr/0001` 到 `0009` 九份 ADR，以及各自 decision ticket 的结论评论。

对照日期 2026-08-11。九份 ADR 全文读取，aidlc 报告全文读取。

## 1. 先修正一处检索错误

本次对照的起因是一项统计：九张已解决 decision ticket 的**结论评论**里，提到 aidlc 的只有三张。该统计的检索范围只有 issue 评论，不含 ADR 正文，因此不足以支持「某张 ticket 没有对照过 aidlc」这个结论。

补查 ADR 正文之后：

| ADR | 提及 aidlc 的处数 |
| --- | --- |
| `0003-artifact-path-formula.md` | 1 |
| `0007-artifact-reference.md` | 3 |
| 其余七份 | 0 |

`0003` 那一处是完整的对照：它把「照搬 aidlc 的做法」列为 Considered Option，写出否决理由，并指明哪一条被采纳。原文在 `docs/adr/0003-artifact-path-formula.md:8`。

因此「本 effort 的骨架决定没有参考 aidlc」这个判断不成立。骨架决定参考了，对照结果写在 ADR 而不是 issue 评论里。

## 2. 逐节对照

| aidlc 报告的节 | 它规定什么 | MMW 的对应决定 | 判断 |
| --- | --- | --- | --- |
| 1 canonical name 推导落点 | 产物身份是名字不是路径 | `0003`、`0007` | 对照过，取舍有理由 |
| 2 唯一生产者，名称全局唯一 | 两个阶段不得声明同一个名字 | 无 | **缺口** |
| 3 产物在生产它的阶段目录下 | 落点锚定生产者 | `0003` 锚定工作名 | 分歧未记理由 |
| 4 路径形状 | 三种固定形状 | `0003` | 对照过 |
| 5 三步声明加一次解析 | 上游声明、下游声明、引擎解析 | `0007` | 对照过 |
| 6 阶段正文里的路径不是合同 | frontmatter 权威，正文写死根路径是文档错误 | `0006` 做同一件事 | 殊途同归，未留痕迹 |
| 7 conductor 不拥有产物位置 | 解析在上游，执行方只是传递者 | `0007` 让下游自己解析 | 分歧未记理由 |
| 8 registry is computed, not written | 不写索引文件 | `0001`、`0007` 都决定写索引文件 | **实质分歧** |
| 9 上游产物不存在时的行为 | 区分预期缺失与异常缺失 | `0007` 只对上「不许编造」 | 部分对照 |
| 10 工具的职责边界 | 没有公开的路径查询命令 | `0007` 指出了这一点 | 已补 |
| 11 机械校验校声明层 | 五项检查 | `0007` 对上一项，`0009` 零对照 | **缺口** |
| 12 CI 与测试覆盖 | 它自己承认三类事件未覆盖 | `0009` 的测试归位表 | 未对照，份量低 |

## 3. 用 research #20 自己的「下游怎么用」核对

`docs/research/mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/README.md` 的「下游怎么用」一节给四张 decision ticket 各点名了该读哪几节。逐条核对是否用到：

| ticket | README 点名的节 | 实际用了吗 |
| --- | --- | --- |
| #21 每类 MMW 产物的落点与路径形状 | 1、2、3、4 | 用了 1、3、4。**第 2 节的 Collision policy 没用** |
| #23 读取产物的技能怎么找到它需要的产物 | 4、7 | 用了，并另外用了 5、6、8、9、11 |
| #24 落点合同存放在哪里 | 5、6、10 | 做的事与第 6 节一致，但 ADR 正文没有对照记录 |
| #26 新归纳合同下机械校验能判定什么 | 11、12 | **零对照** |

README 在 #21 那一行写得很具体：「第 2 节的 Collision policy 直接对应 MMW 当前 `docs/evidence/` 由两个技能写入、没有唯一生产者规则的情况」。

`0003` 处理 `docs/evidence/` 的方式是取消这个类别根（`docs/adr/0003-artifact-path-formula.md:14`）。取消解决了这一个位置的双写，没有建立一般规则。

## 4. 三处发现

### 第一处：索引文件写成文件还是当场算出

aidlc 的原文（报告第 8 节，主 agent 亲自抓取核对）：

> "The registry is computed, not written."

它的名称注册表从全部阶段的 `produces[]` 与 `optional_produces[]` 计算得出，由 `aidlc graph artifacts` 输出到标准输出。它不登记每次运行的实际路径，也不落成仓库文件。

MMW 两处反向决定：

- `docs/adr/0001-spec-plan-stay-in-repo.md:17`：仓库里有一份自动生成的 spec 索引，由一条 CLI 命令全量重建。
- `docs/adr/0007-artifact-reference.md`：ADR 加元数据块，仓库里一份自动生成的 `docs/adr/README.md`。

两处都是提交进 Git 的文件。两处的 ADR 都没有提到 aidlc 在这件事上的相反做法。

差别在失效方式：写成文件时，生产者忘记重建索引，索引就与实际不一致，而且没有机械校验会发现（`0009` 明确不校验产物存在性）。当场算出时不存在这种不一致。

MMW 侧有一条 aidlc 没有的约束：`AGENTS.md` 要求 agent 读取与本次范围相关的 ADR，而零上下文的 agent 打开 `docs/adr/` 只看得到文件名。这是 `0007` 决定做索引的理由。这条理由本身成立，但它没有排除「用一条命令当场输出清单」这个选项。

### 第二处：产物引用没有防撞名规则

aidlc 的原文（报告第 2 节，主 agent 亲自抓取核对）：

> "Two stages **must not** declare the same canonical name in their"

它的注册表是集合，名称全局唯一。两个阶段的产物概念上重叠时，拆成两个不同的 canonical name；磁盘文件名允许相同。

MMW 的产物引用由四项构成（`docs/context/artifact-location.md` 的「产物引用」）：类别、工作名、范围段、类别内细分。

类别内细分由生产它的技能当场取名。`0007` 自己写明了这一点：research 主题名由 `/mmw-research` 当场取，prototype 变体目录名由 `/mmw-prototype` 当场取。

后果：同一次交付里两次 research 各自当场取名，取到同一个名字时，四项全部相同，解析出同一条路径，后写的覆盖先写的。九个决定里没有一条规定这种情况。

`0009` 也不会发现它：产物存在性与类别内细分的命名恰当性都在「明确不校验」清单里。

### 第三处：机械校验只对上 aidlc 五项中的一项

报告第 11 节列出 aidlc 的五项：

1. 阶段定义的引用校验（`Graph references`）。
2. sensor 对给定 target 的存在性与形状校验。
3. 上游存在性读取，只用于过滤。
4. per-unit 阶段的完成度检查。
5. 阶段源文件的 `Outputs:` 文本校验。

`0007` 对上了第 1 项，原文在 `docs/adr/0007-artifact-reference.md:18`。`0009` 定整套清单时零对照。

第 3 项与 MMW 直接相关。aidlc 按生产方目录查找上游产物，只把磁盘上存在的传给检查，原文是 `"filtered to artifacts that exist on disk"`。它的理由是：被 scope 跳过的阶段本来就没有产物，不过滤就会产生必然失败的检查。

MMW 有同一种情况——某个技能这一轮没有运行，它的产物就不存在。`0009` 定校验清单时没有对照这一项。

## 5. 结论

| 处 | 处置 | 理由 |
| --- | --- | --- |
| 第一处 索引文件 | 重开，建新 decision ticket | 它改变 spec 的形状。索引写成文件还是当场算出，决定了 spec 里要不要有「重建索引」这条命令，以及 ADR 与 spec 的元数据块要不要存在 |
| 第二处 撞名 | 重开，建新 decision ticket | 同上。防撞名规则会改变产物引用的定义，而产物引用是 `0007` 的核心 |
| 第三处 机械校验 | 不重开，写成交给 spec 阶段的一条要求 | `0009` 已经把校验命令的名字与挂载位置留给 spec 阶段。aidlc 五项逐条过一遍放在同一处做 |

不重开的七个决定，对照结果见本文第 2 节。其中两项分歧没有记录理由，列在这里供 spec 阶段引用：

- **第 3 节，落点锚定谁。** aidlc 把产物放在生产它的阶段目录下，MMW 放在工作名目录下。MMW 这样做的实际原因是一次交付有多条任务分支，按生产者归类会把同一次交付的产物散开（这条理由写在 `docs/adr/0005-work-name-vs-branch-name.md:3`，但那份 ADR 讲的是工作名与分支名的关系，没有把它写成与 aidlc 的对照）。
- **第 7 节，谁来解析。** aidlc 由引擎在上游解析好，把路径放进 directive 交给执行方。MMW 由下游自己跑 `mmw artifact path` 解析。MMW 没有引擎这一层，这是 `0003` 与 `0007` 共同的否决理由。后果是下游必须能运行这条命令。

## 6. 没查清楚的部分

- 本次对照全部基于 research #20 的报告，没有重新访问 `awslabs/aidlc-workflows`。该报告自己标注的未查清项一并继承：无法固定完整 commit SHA；`resolveArtifactPath()` 逐字源码未取得；「没有全局产物落点门禁」是「已查范围内未找到」不是完整否定；`core/tools/data/scaffold/` 的 404 未经主 agent 复核；测试覆盖表未逐条核对。
- aidlc 的 `optional_produces[]` 与 `required: true` 语义（报告第 9 节）本次只对照了「不许编造缺失产物的内容」一句。「预期缺失与异常缺失怎么区分」这一项对 MMW 是否有用，本次没有判断。
