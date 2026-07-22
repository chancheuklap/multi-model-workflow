# wayfind 探路前缀阶段 + 颗粒化取证 · 设计(简版)

> 方向已经用户批准(2026-07-22,见同文件夹 direction.md);用户指示流程从简,不走整套编排。本文记机制设计决定与文件清单,供落地与回溯。

## 范围

- **做**:①develop 可选前缀阶段 `wayfind`(借 wayfinder 决策地图机制,自建工件);②颗粒化取证(design 取证战役只冻结依赖分支)。
- **不做**:外部知识问卷(已否决);任何引擎新状态机;worker 派发链路改动。

## 机制设计(基于 investigating.md 的取证)

1. **wayfind 进 phases 的方式**:`prepare.sh cmd_new` 加 `--with-wayfind`(仅 develop,其他 scenario 拒),置位时 `phases='["wayfind"]+presets.develop'`。routes.json `phase_bindings` 加一条 wayfind(load/do/produced),`presets` 不动。
2. **下游零改动**:investigate 无 reads 键,prev_outputs 默认取上一阶段产出(flow.sh:497-505),wayfind→investigate 天然衔接;pin 通用存在性检查放行目录(flow.sh:380);提交白名单靠 docs/.gitignore 只排 reviews/终审,wayfind/ 自动入 git;escalate 走 presets.develop 天然不带 wayfind;develop 起步 attended,wayfind 天然讨论态。
3. **wayfind 工件**:`docs/design/<slug>/wayfind/map.md`(只索引:目的地/已决 gist+链接/frontier/Not yet specified)+ `d-<NN>-<名字>.md`(一决策一文件)。收口双条件:frontier 清空 + 剩余雾区用户确认不挡路 → map 顶部写「路径」节 → handoff pass(produced=wayfind/ 目录)→ investigate 拿「路径」节投查。
4. **触发判据(语义判断,不脚本化)**:双条件同时成立——终点大致明确 + 决策空间在雾里(连要决定什么都没理清、单会话装不下)。写在 orchestrate SKILL 路由表与 scenario/develop.md。
5. **颗粒化取证**:discussion.md「按需补充上下文」节改分流表(小缺口四步不变、走原锚点区;成规模→取证战役,开打前把「在途取证+冻结面」登记进 Open Decisions,只暂停依赖分支);evidence-campaign.md 纪律节加对应一条。
6. **红线**:wayfind 只产决策不动手(能动手=收口信号);map 只索引不复述;决策未经用户确认不标已决。

## 文件清单(三镜像同改,host 词各自适配)

| 文件 | 改动 |
|---|---|
| `<镜像>/state-schema/routes.json` | phase_bindings 加 wayfind 一条 |
| `<镜像>/scripts/prepare.sh` | cmd_new 加 `--with-wayfind`(仅 develop) |
| `<镜像>/scripts/flow.sh` | 冷启动 task new 命令提示加 `[--with-wayfind]` |
| `<镜像>/skills/orchestrate/references/wayfind.md` | 新建(同文,investigate 调用按宿主写) |
| `<镜像>/skills/orchestrate/SKILL.md` | Step 1 路由表加 wayfind 行 |
| `<镜像>/skills/orchestrate/references/scenario/develop.md` | 记 --with-wayfind 与双条件判据 |
| `<镜像>/skills/orchestrate/references/design/discussion.md` | 「按需补充上下文」改分流表(锚点区不动) |
| `<镜像>/skills/orchestrate/references/design/evidence-campaign.md` | 纪律节加「开打先登记冻结面」 |
| `<镜像>/scripts/tests/test_flow.sh` | 加 wayfind 用例(见测试计划) |

## 测试计划

- `task new --scenario develop --with-wayfind`:manifest.phases[0]=wayfind;`where` 报 load=references/wayfind.md;handoff pass(produced=wayfind 目录)→ advance 到 investigate 且 prev_outputs 含 wayfind 目录。
- `--with-wayfind` 配 bug/small-change → 报错拒。
- 普通 develop(不带 flag)→ phases 不变(回归)。
- 三镜像 `build --check` + 全量测试套件;版本 bump(plugin/pi/droid 各 +0.0.1,marketplace 同步,test_pi_native 断言同步)。

## 验证方式

落地后按上表跑三镜像全量测试;主线程亲验 `mmw where`/`handoff` 真机行为(不作弊)。
