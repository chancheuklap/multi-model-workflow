# #641 当前产品复现与读取基线

2026-10-31，产品基线为 `9e2c0f3e2fe281f3587092cfce8249d129095b86`。后续提交仅有本轮准备材料，未修改产品。

## 运行方式与证据边界

从仓库根目录运行：

```bash
python3 efforts/fix-641/diagnose.py reproduce
python3 efforts/fix-641/diagnose.py browser
python3 efforts/fix-641/diagnose.py benchmark
```

前两条在原产品上退出 1，表示预期的行为缺陷。不是测试已通过。browser 使用项目 e2e 包已安装的 Chromium 依赖，需要先运行 `npm ci --prefix tests/e2e/task-board --silent`。页面截图与每次运行的原始结果默认保存在 `.scratch/fix-641/diagnosis/`。

后端是本 checkout 的 server.py，前端是原 page 模块。复用现有 RunningBoard 与 fake gh，在 GitHub I/O 边界提供固定回答，每个实例有独立的 MMW_HOME 和临时目录。不拦截或替换任务板自己的计算。浏览器实际点现有刷新按钮及 ticket 卡片。退出时关闭浏览器、服务器和临时目录。

真实仓库的开放 map 与 spec 列表当前均为空，因此本轮没有活夜的线上延迟或 API 额度测量。隔离证明支持当前代码对这些输入的行为，不证明 GitHub 服务的实际延迟或原子一致性。

## 三项缺陷均已触发

1. 首次读取 open 票与 working 事件。只改变 GitHub 回答，使该票 closed 且新增 passed、landed。点击原刷新按钮后，后端仍回答 state=open、blocker_hold=open，却已读到 landed。页面 pill 为 landed，出边仍有 1 条 blocked。截图为 `landed-edge.png`。
2. 在上一场景继续加入 ticket.regressed、重开该票，再手动刷新。评论读取为 0 次，返回事件只到 landed。说明是读取计划跳过了该票，不是 GitHub 替身漏发新事件。
3. 让 GitHub 返回 worker.started、claimed、reviewer.started、reviewer.reported、再次 claimed。打开原卡片，卡片和详情头部为 working，Events 最新块仍为 review。截图为 `review-return.png`。

两项页面检查均无 pageerror。后端循环和页面循环重复执行后结果相同。持久结果在 [baseline](baseline/)；[landed 红线截图](baseline/landed-edge.png) 和 [review 返回截图](baseline/review-return.png) 均已实际查看。

## 假设与判别

| 排名 | 预测 | 结果 |
| --- | --- | --- |
| 1，不同来源的更新周期不一致 | GitHub 同时给出 closed 和 landed，手动刷新仍只更新后者 | 符合，直接 HTTP 回答和页面都矛盾，排除仅由渲染延迟造成 |
| 2，finished 把 landed 当作没有后续事件 | landed 后改变评论，后续请求根本不读该票 | 符合，fake gh 记录为 0 次 |
| 3，事件分块另有阶段解释 | 同一份后端数据的头部与 Events 给出不同阶段 | 符合，原页面同次呈现 working 与 review |

已读完整 board_data.py，以及页面的阶段解释、事件分块和读取循环。运行观察分别落在 plan_read 的 600 秒结构节奏、finished 停读条件和 PHASE_OF_EVENT 加 sticky claim 的路径。

## 重复读取的受控基线

固定 12 张票，各 1 页评论，先完整读取，再交替运行单请求与两个同时请求，每种 5 轮。fake gh 每次人为增加 50 ms 等待，两侧使用相同版本、环境、数据、条件缓存和延迟。

| 工作量 | 完成整组请求的中位数 | 范围 | 每轮 gh 命令 | 错误 |
| --- | --- | --- | --- | --- |
| 1 个 GET | 1.240 秒 | 1.225–1.270 秒 | 12 | 0 |
| 2 个同时 GET | 2.482 秒 | 2.460–2.524 秒 | 24 | 0 |

[原始轮次](baseline/baseline.json) 与 [GitHub 边界耗时记录](baseline/gh-spans.jsonl) 已保留。每个回答都检查票数完整且没有 read_failed，两个请求均等待实际响应，未把拒绝、异常或后台未结束的工作计成提速。

这是单客户端与双客户端的当前行为对照，没有候选实现，更没有“已经提速一倍”的结论。人为延迟和进程启动均计入端到端时间，不是生产 GitHub 耗时。边界记录也在测量期间写盘，数字包含该工具开销。

可确认的机制是两个请求串行各做了 12 次条件评论读取，而不是共用一次结果。这里逐票 gh 等待主导耗时是实验构造与运行记录共同支持的结论，不是对生产环境 CPU 或网络瓶颈的测量。运行前机器为 18 逻辑核、load average 2.54/2.55/2.57。没有新增并发 GitHub 读取。

## 实施后必须怎样比较

沿用同一 workload，分别证明新鲜结果的重复 GET 不再新增 GitHub 读取，以及过期或手动刷新确实重新读到修改后的数据。不能只把全部请求缓存后宣称提速。补上原页面的固定产品验收与既有操作的保留证明，再交替复测五轮。

冷启动、真正刷新一轮、warm GET 的等待及 GitHub 调用分别报告。当前循环未覆盖真实限流、分页移动或 relay 唤醒，这些边界交由对应读取工具和 relay 的针对性隔离验证。
