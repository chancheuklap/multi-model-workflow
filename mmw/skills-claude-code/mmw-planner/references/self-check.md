# Plan 交付前自检

按整份 plan 检查：

- 元数据块的 `ticket` 等于当前 tracer bullet ticket 的 GitHub issue 编号，且 `artifact_refs` 键存在。
- ticket 有 `## 产物引用` 固定节。plan 的 `artifact_refs` 逐条传递 ticket 的条目。每条都有显式 `name`。没有条目时两处分别写 `无` 和 `[]`。
- ticket 的每条验收都能在 `## Acceptance` 找到证明方式。
- 实施步骤覆盖完整路线，顺序成立，`worker` 不需要猜目标或未决业务决定。
- 既有路径、符号和当前行为已经回到源码验证；新文件标明 `Create`。
- `## Change Map` 覆盖本 ticket 会修改的文件，没有认领别份 plan 拥有的共享文件。
- 跨 plan 接口引用 spec `## Cross-Plan Contract Anchors` 的条目名，没有重复字段全文；没有跨 plan 接口时没有虚构接口。
- prototype 存在时，只使用用户选中版本和已确认决定，并写出资产出处。
- research 存在时，只使用当前 ticket 引用的索引和精确文件，并保留范围快照与未查清项。
- 测试落在 spec 已确认的 seam，命令来自目标仓库现有入口。
- 界面 ticket 写了独立的浏览器审批；高风险 ticket 写了回滚或人工审批关卡。
- plan 没有复制 spec、测试方法论或大段实现代码，也没有为了格式填充无关小节。

这些条件全部成立才交 `pass`。缺少会改变目标、合同或验收的上下文时交 `needs-context`；材料在手上但本身有错（验收无法映射为证明方式、ticket 与 spec 矛盾、合同锚点与阻塞关系对不上）时交 `needs-repair`；源码证明方向不成立时交 `needs-redirection`。
