# #641 受影响的已有功能

本结果来自 maintain-verification-skill 的 Find affected features 定向查找。读取了 verify-task-board 的完整 SKILL.md、五个 feature 文件的前三行，以及以下四个受影响文件的全文。没有运行 whole-product maintenance，没有宣称新增验收已存在。

| feature map 名称 | 来源 | 变化与保留 |
| --- | --- | --- |
| 任务列表 | .agents/skills/verify-task-board/features/tasks.md | 变化：默认选择活跃夜及所选已完成夜的恢复。保留：按地图和 spec 展示、用户手动切换 |
| 画布 | .agents/skills/verify-task-board/features/canvas.md | 变化：卡片阶段时间、与连线一致的事实解释、合入后状态。保留：依赖布局、缩放、点击打开详情 |
| 详情 | .agents/skills/verify-task-board/features/detail.md | 变化：按阶段的时间线、当前空阶段、收口复跑回归恢复与夜进度。保留：票的信息、子 issue 和 GitHub 链接 |
| 顶栏 | .agents/skills/verify-task-board/features/topbar.md | 变化：本轮数据读取状态与手动刷新语义。保留：仓库身份、四类计数、跳转需要主人处理的票、配置入口 |

任务列表、画布和详情的 feature 文件当前均标记 Tests: none，并未逐项登记行为。顶栏列出 smoke.e2e.ts，其中现有 Proof 是仓库名可见和配置入口可打开，不能当作 #641 的刷新或状态一致性证明。

本机配置不在 #641 的产品修改目标中。它作为既有入口及环境隔离要求保留，当前不触发其全面维护。

新增 UI 冻结后更新本次实际改到的 feature，按 prepare-ui-acceptance 准备对应验收。后端读取和 MMW 命令有各自的边界证明，不用页面测试重复覆盖其内部调用形状。
