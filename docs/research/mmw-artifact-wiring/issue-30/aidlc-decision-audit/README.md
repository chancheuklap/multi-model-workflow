# research：九个决定与 aidlc-workflows v2 的对照复核

## 这次要回答的问题

map #18「MMW 产物归纳与接线合同」已经形成九个决定。哪几处 aidlc-workflows v2 有对应做法而本次没有对照过？看过之后哪几处要重开？

来源：Wayfinder decision ticket #30，map 是 #18。

## 查证范围

- `docs/research/mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/report.md` 全文，十二节。
- `docs/adr/0001` 到 `0009` 九份 ADR 全文。
- decision ticket #21 到 #29 的结论评论。

本次没有重新访问 `awslabs/aidlc-workflows`。aidlc 一侧的全部事实来自 research #20，它标注的未查清项本文继承。

## 结论摘要

1. **起因那项统计不完整。** 「九张 ticket 里只有三张提到 aidlc」的检索范围只有 issue 评论，不含 ADR 正文。补查后，`0003` 与 `0007` 两份 ADR 有对照记录，其余七份没有。
2. **骨架决定对照过 aidlc。** `docs/adr/0003-artifact-path-formula.md:8` 把「照搬 aidlc 的做法」列为 Considered Option，写出否决理由（MMW 没有引擎那一层），并指明「技能正文里的路径不该各写各的」这一条被采纳。
3. **三处实质问题。** 索引文件写成文件还是当场算出；产物引用没有防撞名规则；机械校验只对上 aidlc 五项中的一项。
4. **两处重开，一处交给 spec 阶段。** 前两处改变 spec 的形状，各建一张新 decision ticket。第三处并进 `0009` 已经留给 spec 阶段的那一批。
5. **七个不重开的决定，对照结果逐条记在 `report.md` 第 2 节。** 其中两项分歧没有记录理由，`report.md` 第 5 节补上：落点锚定工作名而非生产者；解析在下游而非上游。

## 本目录的文件

| 文件 | 内容 |
| --- | --- |
| `README.md` | 本文件，research 索引 |
| `report.md` | 完整对照，六节。十二节逐节对照矩阵、research #20「下游怎么用」的核对、三处发现的原文与出处、处置结论 |

## 下游怎么用

- 新建的两张 decision ticket 各自解决第一处与第二处，`report.md` 第 4 节是它们的输入。
- 写 spec 时：`report.md` 第 4 节第三处列出 aidlc 机械校验的五项，`0009` 留给 spec 阶段的那一批要逐条对照它。
- 写 spec 时：`report.md` 第 5 节末尾两条分歧理由，是「aidlc 的哪一项我们看过、为什么这样定」的记录，可直接引用。

## 没查清楚的部分

- 继承 research #20 的全部未查清项，逐条列在 `report.md` 第 6 节。
- aidlc 的 `required: true` 语义与「预期缺失、异常缺失」的区分（research #20 报告第 9 节），本次只对照了其中一句，没有判断这个区分对 MMW 是否有用。
