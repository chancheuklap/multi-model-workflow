# #641 受影响的已有功能

本轮保持现有 UI。复用 Find affected features 的定向查找，不启动 whole-product maintenance。

| feature map 名称 | 来源 | 本轮边界 |
| --- | --- | --- |
| 画布 | .agents/skills/verify-task-board/features/canvas.md | 修复卡片与依赖线的数据一致性；保留布局、缩放和点击打开详情，不新增时间或状态显示 |
| 详情 | .agents/skills/verify-task-board/features/detail.md | 修复现有状态、阶段、事件及子 issue 的陈旧或矛盾数据；保留字段、布局和交互，不新增阶段时间线或夜进度 |
| 顶栏 | .agents/skills/verify-task-board/features/topbar.md | 修复现有计数、读取状态与刷新承诺；保留仓库身份、计数、跳转和配置入口 |
| 任务列表 | .agents/skills/verify-task-board/features/tasks.md | 保留呈现、选择及切换行为，不改默认选择策略 |

画布、详情和顶栏已登记 `tests/e2e/task-board/issue-641.e2e.ts`。两项修复在原产品上因红线和 review 阶段的实际症状失败；原有选择、详情及配置操作的保留测试通过，破坏配置按钮后的反例失败，恢复后再次通过。任务列表没有改变选择策略，保留原有呈现。来源是实际产品和已复现需求，无需设计 winner。

本机配置及其他未改功能保持原状。后端读取与 MMW 命令在自己的 I/O 边界验证，不用页面测试重复检查内部调用形状。
