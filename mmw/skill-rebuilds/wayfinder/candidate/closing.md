# map 收尾

本文件只处理 MMW 中已经没有 open decision ticket 的 map 生命周期，由 [walking.md](walking.md) 移交。

重新读取 map 正文，再运行 `mmw issue children <map 编号>`。仍有带 `wayfinder:` 标签的 open decision ticket 时停止；map 保持 open，不执行收尾。

## 1. 判断路线是否真的清楚

读取 Not yet specified 中的剩余内容，逐项应用 [SKILL.md](SKILL.md) 的“Fog of war”一节判据：

- 已经能够精确表述，而且仍位于通往 destination 的路线中：按 [charting.md](charting.md) 第 4 步执行 create-then-wire，建立新的 decision ticket。
- 已经确定越过 destination：移入 Out of scope。存在对应 ticket 时，按 [SKILL.md](SKILL.md) 的“Out of scope”一节关闭并链接它。
- 仍然是通往 destination 的 fog：map 尚未完成。按照 [charting.md](charting.md) 第 2 步的广度优先方式，再次对剩余 fog 进行 grilling。能够精确表述的问题按第一项建立 decision ticket；确定越过 destination 的内容按第二项移入 Out of scope。grilling 后仍无法精确表述的内容继续保留在 Not yet specified，报告这块 fog 和当前缺少的信息，然后停止。

完成全部分类后，按下表处理：

| 分类结果 | 处理 |
| --- | --- |
| 建立了新的 decision ticket | 运行 `mmw issue frontier <map 编号> --label-prefix wayfinder:`，报告新 ticket 和当前 frontier，然后停止；map 保持 open，不执行第 2、3 步 |
| 仍有通往 destination 的 fog | 报告仍无法形成 ticket 的 fog，然后停止；map 保持 open，不执行第 2、3 步 |
| 通往 destination 的路线已经清楚，而且没有尚待解决的 decision ticket | 继续第 2 步 |

## 2. 关闭 map

通往 destination 的路线已经清楚，而且没有尚待解决的 decision ticket 时，关闭 map issue：

```bash
gh issue close <map 编号>
```

## 3. 按 destination 移交

destination 决定 Wayfinder 怎样结束。Wayfinder 只交出 map，不替后续技能建立输入产物：

| destination | 处理 |
| --- | --- |
| destination 是一份 spec | 把 map 名称及其 URL 或编号交给 `/mmw-to-spec`。`/mmw-to-spec` 从 map 的 Decisions so far 进入相关 decision ticket，再按 ticket 中的精确链接读取需要的 prototype、research 或 evidence。Wayfinder 不预建 spec issue，不把 map 拆成多份 spec，也不复制这些输入 |
| destination 是开始规划前必须锁定的决定 | 报告已经锁定的决定，并提供 map 名称及其 URL 或编号 |
| destination 是一次就地完成的改动，而且 Notes 已经覆盖“规划，不执行” | 报告 map 已完成；不再建立下游入口 |
| destination 是一次就地完成的改动，而且 Notes 没有覆盖“规划，不执行” | 报告路线已经清楚、改动尚未执行，并提供 map 名称及其 URL 或编号 |

非 spec destination 到这里完成 Wayfinding：交出已经形成的决定，不继续执行 destination。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| destination 是一份 spec，map 已关闭 | **移交**：把 map 名称及其 URL 或编号交给 `/mmw-to-spec` |
| destination 是已经锁定的决定，map 已关闭 | **停**：报告决定和 map 名称及其 URL 或编号 |
| destination 是已经完成的就地改动，map 已关闭 | **停**：报告 map 已完成 |
| destination 是尚未执行的就地改动，map 已关闭 | **停**：报告路线已经清楚、改动尚未执行，以及 map 名称及其 URL 或编号 |
