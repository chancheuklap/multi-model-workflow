# map 收尾

本文件只处理 MMW 中已经没有 open decision ticket 的 map 生命周期，由 [walking.md](walking.md) 移交。

本文件只在拥有 map 分支的任务中执行。运行 `mmw task state`，确认当前 checkout 已绑定 map 分支；确认所有包含仓库改动的 decision ticket 结果已经通过 `mmw result verify` 和 `mmw result integrate`；再运行 `mmw issue children <map 编号>`，确认不存在带 `wayfinder:` 标签的 open decision ticket。仍有这类 ticket 时停止，不执行收尾。

如果本次由 `/mmw-to-spec` 交回，而且它已经指出某张现有 spec issue 仍缺少一个能够精确表述、必须通过 decision ticket 解决的决定或事实，按以下顺序处理：

1. 运行 `gh issue reopen <map 编号>`，重新打开 map issue。
2. 按 [SKILL.md](SKILL.md) 的“Ticket 类型”一节选择 `wayfinder:<type>`。把 `/mmw-to-spec` 交回的完整问题写入 `Question`，原样继承 map 的 `产物目录`，使用 `mmw issue create --title "<ticket 名称>" --body-file <正文文件> --parent <map 编号> --label wayfinder:<type>` 创建 decision ticket。
3. 取得新 ticket 编号后，把正文中的 `issue 子目录` 回填为 `issue-<编号>`，再运行 `gh issue edit <ticket 编号> --body-file <更新后的正文文件>`。
4. 运行 `mmw issue frontier <map 编号> --label-prefix wayfinder:`，报告新 ticket 和当前 frontier，然后停止。

完成这四项后，不执行第 1、2、3 步，也不在 Wayfinder 中替 spec 作出决定。

## 1. 判断路线是否真的清楚

读取 Not yet specified 中的剩余内容，逐项应用 [SKILL.md](SKILL.md) 的“Fog of war”一节判据：

- 已经能够精确表述，而且仍位于通往 destination 的路线中：按 [SKILL.md](SKILL.md) 的“Ticket 类型”一节选择 `wayfinder:<type>`，建立新的 decision ticket，原样继承 map 的 `产物目录`，回填 `issue-<编号>`，再 wire blocking edge。
- 已经确定越过 destination：移入 Out of scope。存在对应 ticket 时，按 [SKILL.md](SKILL.md) 的“Out of scope”一节关闭并链接它；明确否决的 enhancement 同时按 tracker 合同把理由保存到 `.out-of-scope/`。
- 仍然是通往 destination 的 fog：记录这块 fog 为什么仍无法形成 ticket。只有 destination 或范围本身需要用户决定时才询问用户。

完成全部分类后，按下表处理：

| 分类结果 | 处理 |
| --- | --- |
| 建立了新的 decision ticket，或者仍有通往 destination 的 fog | 报告全部新 ticket、当前 frontier 和仍无法形成 ticket 的 fog，然后停止；map 保持 open，不执行第 2、3 步 |
| 通往 destination 的路线已经清楚，而且没有 decision ticket 留下 | 继续第 2 步 |

## 2. 按 destination 移交

destination 决定 map 的下游，不默认生成 spec：

| destination | 处理 |
| --- | --- |
| 一份或多份 spec | 按已经形成的决定组合出对应的 spec issue。每张 spec issue 挂在 map 下，不带 `wayfinder:` 标签；正文写明要综合的决定、原样继承的 `产物目录`，以及确实需要的 prototype、research 或 evidence 精确路径。首次抵达时，使用 `mmw issue create --title "<spec 名称>" --body-file <正文文件> --parent <map 编号>` 创建。此次收尾由现有 spec issue 交回时，把新形成的决定和精确资产路径更新到原 spec issue，不创建第二张 issue。完成后继续第 3 步 |
| 开始规划前必须锁定的决定 | 确定 Destination 或 Notes 点名的下游，并准备 resolution comment 和 Decisions so far 中已经形成的决定，然后继续第 3 步 |
| 一次就地完成的改动 | Notes 已经覆盖“规划，不执行”时，确认改动已经由对应 decision ticket 完成；没有覆盖时，确定 Destination 或 Notes 点名的下游并准备已经形成的决定。完成后继续第 3 步 |

Destination 和 Notes 没有点名非 spec destination 的下游，而且当前证据无法确定时，停止第 2 步并询问用户，不执行第 3 步。用户明确指定下游后，从第 2 步继续。

prototype、research、evidence、ADR 和领域 leaf 在产生时由对应 ticket 或下游技能完成持久化。收尾只使用这些现有出处。`.out-of-scope/` 只处理第 1 步刚刚判出范围的 enhancement。

## 3. 关闭 map

第 1 步完成，而且第 2 步已经建立所需的下游入口后，先提交收尾阶段实际形成的仓库改动；没有仓库改动时不制造空提交。仓库改动提交完成后关闭 map issue。

此次收尾由现有 spec issue 交回时，关闭 map 后调用 `/mmw-integrate`，让该 spec 的任务分支 rebase 到更新后的 map 分支。Rebase 完成后再把原 spec issue 交回 `/mmw-to-spec`。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| destination 是一份或多份 spec，spec issue 已建立，map 已关闭 | **移交**：每份 spec 分别进入 `/mmw-to-spec` |
| 非 spec destination 已建立明确下游，map 已关闭 | **移交**：进入 Destination 或 Notes 点名的下游 |
