# #1480 执行器复验

候选提交 c2c6afc55d92158597697abcdf6ffb3d5974e262；运行控制版本保持 installed runtime 9e2c0f3e 不变。

## 原缺陷的产品复验

在候选 checkout 运行 `python3 efforts/fix-641/diagnose.py browser --output .scratch/fix-641/executor-ui`，输出 BOARD_UI_REPLAY_MET，退出 0。原刷新按钮读到关闭和合入后，卡片为 landed、blocked 线为 0；review 结束后再次认领，详情当前阶段及最新事件块均为 working。两项场景均没有 pageerror。执行器实际查看了 [合入后的页面](landed-edge.png) 和 [review 返回后的页面](review-return.png)。

使用原前后端和真实 Chromium，仅在既有 GitHub I/O 边界隔离外部回答。没有把静态页面或替代 `/api/board` 的答案当成后端修复。现场 GitHub 仓库没有开放 map/spec，不能声称这证明了正在跑一夜的所有状态。

## 有效缓存内的重复读取

交替执行旧版和候选版各五轮，每轮用同一 diagnose.py benchmark workload：12 张票，每张一页评论，每次 fake gh 注入 50 ms 等待，先完整读取成功再做单 GET 和双 GET。旧版产品在 b967d973b 的准备分支，候选为 c2c6afc55。独立临时 MMW_HOME，不运行真实 tracker 写入。

| 完整 HTTP 请求组 | 旧版新增 gh 命令 | 候选新增 gh 命令 | 每版轮数 | 错误 |
| --- | --- | --- | --- | --- |
| 单 GET | 每轮 12 | 每轮 0 | 5 | 0 |
| 两个同时 GET | 每轮 24 | 每轮 0 | 5 | 0 |

两版均返回完整 12 票。候选复用的是 60 秒内已经完整核对成功的结果；过期、手动刷新、失败和限流恢复另由同一候选的判据及完整检查覆盖。这里的 0 不表示冷启动或真正刷新也不访问 GitHub。

[逐轮原始数据](comparison.json) 保存 HTTP 完成时间、中位数、范围和调用计数。测量前为 18 逻辑核，load average 3.42/3.24/3.16。两个版本交替，避免时间漂移偏向一侧。旧版重复耗时主要是顺序等待 gh，候选用已发布结果消除该 I/O。两侧包括相同诊断日志开销。

这是受控缓存命中场景，不是实际 GitHub 网络、服务器额度或整个 MMW 的提速倍数。交付的主要数字采用外部读取计数，未将 304、gh 子进程和 GraphQL 点数混为一谈。

## 评审和证据范围

独立评审已在票据记录。评审指出的限流恢复、轮询边界、分页及重叠测试问题有对应修复提交，候选的 11 项判据已由 frozen verifier 复跑通过。正常 status 输出契约保留，工作流文本和 agent 命令协议未改。这次没有把候选控制脚本用于控制当前 watch。

## 全库检查尚未通过

在候选 c2c6afc55 运行 `scripts/check --all`，日志为候选 checkout 的 `.scratch/check/20261031-180053/`。board 和全套任务板 e2e 的 9 项测试通过。完整结果为 `CHECK FAIL all: 4 of 20 steps red (dispatch, liveness, relay, verify-ticket) in 660s`，退出 1。

dispatch 的 landstopfailure、open 和 openticket 场景失败。子 issue 读取已迁移到带 HTTP 响应头的条件读取，`mmw-v4/tests/dispatch/test_dispatch.sh` 的 GitHub 替身仍输出旧的裸 JSON，并保留旧 `--paginate --slurp` 参数断言。失败包含 `the response had no HTTP headers`。原始失败保留，不以票内 11 项通过替代全库检查，不合入当前候选。

relay 的 readonly 场景同样没有完成读取。`mmw-v4/tests/relay/test_relay.sh` 的 sub_issues 替身仍输出旧 slurp 包装，缺少条件读取需要的 HTTP 响应头。

liveness 发现实际产品回归。relay.py 移除了 GH_TIMEOUT 导出，watchdog.py 的 MARGIN 仍读取 relay_mod.GH_TIMEOUT，导致候选 watchdog 导入失败，turn-guard 端到端用例也失败。修复需要恢复生产调用链的契约，不能只修改替身。

[执行器失败记录](https://github.com/chancheuklap/multi-model-workflow/issues/1480#issuecomment-6542073733) 已写入原实现票据。Owns 仅补两个既有 CLI 测试文件，AC 与冻结产品验收不变。

第四组 verify-ticket 的单个失败来自环境隔离。`test_refused_ends_hold.TestTheRefusalNamesItsSession.test_own_session_is_what_the_dispatch_skill_reads_from_this_process` 期望无 runner，测试环境却保留了 Codex App 的 CODEX_THREAD_ID。基线 b967d973b 与候选 c2c6afc55 的相关代码相同，两侧在原环境均失败。只对子进程移除 CODEX_THREAD_ID 后，两侧同一用例均通过，保留其中 Paseo 身份识别和无 runner 两个断言。没有修改测试、跳过断言或隐藏原失败。后续全库复验沿用这个隔离环境，生产 dispatch 仍保留实际会话身份。


## 修复后的执行器验收

最终候选为 b562324d58e1c53e25100f6437e79323d5c6d7f8，最新 [票内验收](https://github.com/chancheuklap/multi-model-workflow/issues/1480#issuecomment-6542195070) 为 11 met、0 unmet、0 abandoned。原始失败记录保留。

执行器检查了本轮修复。relay 恢复 watchdog 所用的 GH_TIMEOUT 导出。结构与评论分别复用已有 ghlist 副本，共享限流暂停，并保留原心跳中评论计数的含义。CLI 和 liveness 的 GitHub 替身按真实 HTTP 回答迁移，原有 watch、只读、唤醒和心跳断言保留。范围外的 liveness 测试适配已披露并由新一轮评审判为必要。评审发现其他会话拒绝接手会覆盖活跃阶段，worker 已修复并增加回归。

执行器再次运行原浏览器反馈环，命令为 `python3 efforts/fix-641/diagnose.py browser --output .scratch/fix-641/executor-ui-repair`。输出 BOARD_UI_REPLAY_MET，退出 0。已关闭并合入的上游不再留下 blocked 线，review 后再认领时当前阶段与最新事件块均为 working。两项场景均无 pageerror。两张 [当前红线场景截图](repair/landed-edge.png) 和 [当前阶段场景截图](repair/review-return.png) 已实际查看。

读取代码与 c2c6afc55 的五轮交替测量版本逐字节相同，见 [读取路径校验](repair/unchanged-read-paths.json)。所以五轮调用计数仍适用；没有重新包装为最终版本的实时 GitHub 延迟测量。

在候选 checkout 使用 `env -u CODEX_THREAD_ID scripts/check --all`。只对子进程移除宿主会话身份，不改变生产 dispatch 环境。完整检查退出 0：

```text
PASS e2e-task-board 10s
CHECK PASS all: 20 steps in 677s
```

全套任务板页面测试为 9 passed。此前失败的 dispatch、liveness、relay、verify-ticket 均通过。完整输出见 [全库结果](repair/check-all.log)，相关套件原始日志在同目录。运行期间候选 HEAD 始终为 b562324d5，未修改输入。

未运行的 Windows PowerShell 安装检查需要 Windows 构建机。它们不在本机这 20 项检查的范围内。真实 GitHub 配额收费、实际限流和活跃批次整页延迟的证据边界不变。
