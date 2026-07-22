# Direction · wayfind 前缀阶段 + 颗粒化取证(2026-07-22-wayfind-phase)

## 选定方向

1. **wayfind 探路阶段**:借 mattpocock wayfinder 的决策地图机制,作为 develop 的**可选前缀阶段**接入三镜像(`task new --with-wayfind` 时 phases 前缀 `wayfind`)。工件自建、落 `docs/design/<slug>/wayfind/` 随设计入 git:map.md 只做索引、决策卡 d-NN 一决策一文件;frontier 循环 + grilling 逐个拍板;只产决策不动手;frontier 清空且剩余雾区经用户确认不挡路 → handoff 进 investigate。
2. **颗粒化取证**:design 讨论中成规模取证(取证战役)开打前登记"在途取证 + 冻结面"进 Open Decisions,只暂停依赖分支、无关分支照常;打完落盘解锁回灌。落点:discussion.md「按需补充上下文」节改分流表 + evidence-campaign.md 纪律加一条。
3. **明确不做**:外部知识问卷(用户已否决)。

## 为什么

- 补真实能力空档:investigate 回答已知问题,wayfind 管"问题本身还在雾里"的事;今天这类事硬塞 develop 等于假装知道该查什么。
- 引擎零新状态机:presets 单源(prepare.sh:80)、prev_outputs 默认取上一阶段(flow.sh:497-505)、pin 通用存在性检查(flow.sh:380)全部复用,改动面 = 1 条 phase_binding + 1 个 prepare flag + 1 份新 reference + 路由判据 + discussion/evidence 改写 + flow 测试。
- 颗粒化取证纯 reference 改写,消灭一次取证冻结整场 design 的阻塞。

## 最强对照(为什么不直接引用上游 wayfinder skill)

运行时调外部技能 = 把外部 issue tracker 变成第二套编排权威(地图与 ticket 住在 tracker 上),与 mmw 状态平面单权威冲突,且要求用户先跑 setup 配置 tracker;借机制自建工件,权威唯一、零配置。
