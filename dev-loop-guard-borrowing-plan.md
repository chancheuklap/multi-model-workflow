# 开发主循环守卫补强方案（graph/loop 借鉴收敛稿）

> 状态：动作三待用户拍板（做实 / 删字段），其余可落地。
> 范围：三镜像（`plugin/` `droid-plugin/` `pi-plugin/`）同步。
> 来源：2026-07-20 双模型独立分析 + 三轮交叉审查收敛；文内所有行号已按镜像分别亲验。

## 背景与判据

loop engineering / graph 架构的核心课（验证器即工程、显式状态机、新鲜上下文 + 文件状态、类型化回边）mmw 主流程已具备。真正缺口：仓库内 `release-flow`（打包发布）已有全套自治守卫，而天天用的开发主循环（写码→审查→返工）在同一位置 fail-open——收敛只靠文档提醒文字，无引擎强制。这违背本项目「不静默兜底、fail-closed、行为分叉落 manifest 由脚本强制」（v6.5.0 决策）的既定原则。

借件判据：复用自己仓库已验证的模式，不引入外部框架，不过度设计。

## 动作清单

| # | 动作 | 定性 | 优先级 |
|---|---|---|---|
| 1 | 开发循环同根因打转强制上报 | 技术实现（需设计新分类器） | 最高 |
| 2 | unattended 墙钟 / 轮次软预算 | 纯技术实现 | 高 |
| 3 | `gate_fingerprints` 做实或删字段 | **唯一待拍板** | 中 |
| 4 | reward-hacking diff 预检 | 纯技术，backlog | 低 |
| 5 | progress 路线图可视化 | 纯展示层 | 最低（前四件完成后） |

## 动作一：开发循环同根因打转强制上报

### 现状（证据）

- 主循环返工 / 掉头只打 WARN 文字，无引擎动作：「已返工 N 轮……持续打转要主动交人」（`flow.sh`：plugin:190 / droid:192 / pi:200，三镜像同文）。
- 对照组 release-flow 四件套齐全：同根因熔断（`release-flow.sh:88` CIRCUIT-BREAK）、轮次 / 墙钟预算（:98/:110）、轮次到顶自动 surface 交人（:1202 ROUND-CAP）、逐动作 attempt_ledger。
- release-flow 的指纹来自其 diagnose 分类管线（把构建日志翻译成带 tier + fingerprint 的失败，`release-flow.sh:1012` 注释 + `release_contracts.py classify-findings`）；开发循环无此管线，**不能照抄**，同根因判定需重新设计。

### 目标形态

- **打转判定**：计数对象是「同一 finding 的重现」，不是返工轮数（三轮修三个不同缺陷是健康迭代，同一缺陷反复修不掉才是打转）。
  - 数据源：审查留痕 `docs/reviews/<slug>-<stage>.md` 的 accepted findings 集合。
  - 指纹：文件 + 归一化缺陷签名（标题 / 类型级）；**行号只作弱信号**——返工改代码会挪行号，锚 `file:line` 会把同一缺陷误判成新缺陷而放过真打转。
  - 判据：连续两轮审出实质重合的 accepted findings = 打转。规模为几十行归一化比对，不碰 release-flow 的构建日志管线。
- **阈值字段**：落 `routes.json`，与 `review_gates` 同级（判断落 manifest、脚本强制）。
- **触发动作分 attendance**：
  - attended / afk → 引擎置 `waiting-user` + `mmw where` 置顶；**不锁死**，人来想继续就继续（保留 `routes.json` description 的既定决策：流水线态回上游「向用户汇报但不锁死」）。
  - unattended → 硬停写板，不问人（套用 `steer.sh:77` 默认策略 `review_fail=rework_then_hard_stop` 先例，`references/control/attendance.md:50`）。

## 动作二：unattended 墙钟 / 轮次软预算

- 严格限定 unattended（attended 时人就是预算，不需要）。
- 一份 plan 反复 resume 可在无人值守下长时间烧 token；给墙钟或总轮次软预算，超了 surface 写板，**不硬杀**。

## 动作三：`gate_fingerprints`（待拍板：做实 / 删字段）

### 缺口（已亲验）

- schema 声明了一整套行为：「gated 阶段过闸时记产物内容指纹（phase→hash），`mmw where` 再算比对，不同 = 过闸后被改 → 提示回该阶段重审」（pi `task-manifest.schema.json:119-124`，标「可选」）。
- 全仓脚本与文档**零引用**该字段——声明的守卫不存在，零上下文 agent 读 schema 会误判有保护。

### 仓库内已有两套可抄的指纹模式

1. approval 文档指纹：`flow.sh:53-59` 实现比对，算法单源在 `note.sh fingerprint`，`approval_stale` 硬停输出于 `flow.sh:517`。
2. 审查窗口工作树基线：`review.sh:30-51`（`review_worktree_fingerprint` / `clean_check`），`flow.sh:145-150` 调用——审前录基线、审后核工作树未被改。

### 选项

- **做实**（两模型均推荐）：复制 approval 模式到 plan / final 过闸产物；「过闸产物被偷改 → 提示重审」正是 fail-closed。注意 `where` 是热路径——只在闸点算指纹，不在每次 `where` 全量算。
- **删字段**：去掉空头承诺止血，不留「声明了行为却零实现」的字段误导后来人。

## 动作四：reward-hacking diff 预检（backlog）

- 落地 diff 自动扫：测试文件净删除行 / 断言计数下降 / 新增 `skip`·`xfail`·`only`。
- 只作验收回执里的注意力提示塞给验收人，**绝不做成闸**（已有跨模型全新审者重审兜底，硬闸即过度）。

## 动作五：progress 路线图可视化（最低优先）

- progress 板按 preset 阶段序列（`routes.json` `presets`）拼一小段路线链，标当前节点 + 各回边 repair 计数。
- 纯展示层零风险；数据全现成（presets + `task.json` `repair_count`）。

## 明确不借（过度设计红线）

- LangGraph 式图 DSL / 重写编排引擎（`routes.json` + `conclusions` 已是够用的状态机）。
- checkpoint 时间旅行 / 回放（git 已给）。
- typed state schema / reducer 注册表。
- 单 loop 内 context 压缩框架（subagent 隔离 + 落盘已解决 context rot；review 刻意「原样落盘不摘要」，摘要会丢审计证据）。
- 逐 tool-call 细粒度 trace、AutoGen 式多 agent 自由辩论（前者观测性过度，后者破坏可审计流水线）。

## 落地范围与纪律

- 三镜像同步：共用文字走 `build/fragments` + `build.sh --apply` 单源注入；各镜像脚本行号落地时各自重核（三镜像存在行号漂移，例：WARN 行 pi:200 / droid:192 / plugin:190），禁照抄。
- 验证：动作一 / 二改 `flow.sh` 引擎，补 `scripts/tests/test_flow.sh` 用例（同根因打转判定 × attendance 分支）；三镜像全量测试全绿 + `build.sh --check` 无 DRIFT。
- 责任：Coordinator（主线程）落地；Worker 不碰本文档与 `docs/`。
