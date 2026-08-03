# Build · 写码工人派发落地(develop)

> 落地 = **写码工人改代码 + 主线程按计划验收**。把 ②计划审过的 plan 完整落地、不偏离设计,各 plan 一 worktree、可并行。
> 红线:验收吃**跑测试 / 读 diff 的 ground truth**,不吃自述;afk 只放权自主跑(`attended` 才停问),真缺输入 / 方向疑 / 合并红线才停;push/deploy 要人批(收尾阶段;本地 merge 不拦)。
> - 工人 **只改源码、禁碰 `docs/`**:工人回执后 `mmw worker verify` fail-closed 核边界。碰了 docs → 修复指令 resume 打回;每 Pack 一提交带 `Pack N.M`。
> - **工人返回的事实是劳动力不是信源**——你 verify 时自己 grep / 读 / 跑坐实。

## 断点恢复(context 断了 / 中途回来,先跑这个)

`mmw where` 报 `inner_loop=execution` = 落地账本没走完。读 `loop-state.json` 的 `steps`,**认步账不认记忆**——哪步派了、派到哪全在里面:

| step 状态 | 含义 | 接着做 |
|---|---|---|
| `done` | 该 plan 已验收提交 | 跳过 |
| `pending` + 有 `worktree` + 派发账本 `status=dispatched` | 后台 run 可能在飞 | **别重派**:拿账本 run_id 去 Cursor 后台 Task 列表核对该 run 是否还在飞;确认已结束再 verify 或 resume |
| `pending` + 有 `worktree` + `status=completed` | 工人已返回 | 跑 `status` 触发边界门并读最后回执,再走 B3 |
| `pending` + 有 `worktree` + `status=failed` | 派发失败或异常退出 | 读账本 `log_file`;可修环境后重新 dispatch,已有成功 session 才允许 resume |
| `pending` + 无 `worktree` | 还没轮到 | 正常 B1→B2 派 |

## B0. 返修入口(④终审 / ③合同门判 needs-repair 回来才走;首次落地跳过,直接 B1)

`mmw where` 报 phase=build 且 `repair_count>0` = 从 ④终审(或 ③合同门)带 accepted 缺陷回来**定点修**,**不重走 B1–B6 全量派发**。子 worktree 已在 B4 清掉,代码都在**任务分支**上;不复活原会话、不找原 builder、不重开子 worktree。

1. **读 accepted 缺陷**:④ 读终审报告 `docs/<slug>-final-review.md` 的 findings 段(每条带 `file:line`+remediation);③ 读合同门未兑现项。
2. **判规模,定谁修**:
 - 一两处、确定性的小修 → 主线程**直接改** + 自己验(随后全新审者重审仍保证写者≠验者)。
 - 成规模 / 多文件 / 涉合同 → 汇一份返修指令(fix-spec:改哪个 `file:line`、为什么、验收命令),**落状态平面**(gitignored,免未提交的 docs/ 触发 worker 边界误报),派**一个全新写码工人进任务 worktree** 定点 TDD 修:
 ```bash
 mmw worker dispatch --plan <fix-spec 绝对路径> --worktree "$(git rev-parse --show-toplevel)" \
   --design <设计文档绝对路径> --issue <相关 issue 绝对路径>
 ```
 (任务 worktree 已存在,脚本不重开;工人只改源码、禁碰 `docs/`,与 B2 同 fail-closed;全新 context = 写者≠原验者。)
3. **验收**(B3 同法):跑测试 / 读 diff 亲验,测试质量对标下面权威,不吃自述。
4. **回 ④重审**:若返修触碰跨 plan 合同,先重跑 B5 ③;否则直接 `mmw handoff --conclusion pass --produced "<base..HEAD>"` → 引擎重进 ④终审闸,**全新审者重审**。返修从第 3 轮起,每轮先向用户汇报卡点/根因/下一步再继续;持续不收敛 → `blocked` 交人,别硬磨。

## B1. 进 + 起执行账本

`mmw where` → `prev_outputs` = plan 阶段钉的 plan 目录。读该目录拿 Task Pack 清单、acceptance、plan 间依赖。起账本、把 plan 展开成步账(**一份 plan 一步**,派前把 plan 路径 + 分配的子 worktree 记进步账——断点恢复靠它认"哪步=哪 plan=派到哪"):

```bash
mmw loop init   # 执行账本(值守档自动从 task.json 读入;过门后已是 afk)
mmw loop step add --id <plan-id> --desc "<标题>" --plan <plan 绝对路径> --worktree <该 plan 的子 worktree 绝对路径> # 逐项
```

判哪些 plan 互不依赖 → 并行;有 blocked_by 链 → 按序。

## B2. 派写码工人落地(一条命令准备 + 宿主派发)

每份 plan 派一个写码工人(`mmw worker dispatch` 准备 worktree、prompt 和账本,再照它打印的指令派 Task):

```bash
mmw worker dispatch --plan <plan 绝对路径> --worktree <该 plan 的 worktree 绝对路径> \
 --design <设计文档绝对路径> --issue <该 plan 对应 issue 绝对路径>
```

- **子 worktree 落点定死**:`<主仓库>/.cursor/worktrees/<slug>-plan-<NNN>`(与任务 worktree 同层,别散落);脚本挂 `worker/<目录名>` 分支,从 `--base`(默认 HEAD)分叉。
- **三文档都传**:pack-executor 开工要读设计(意图 / 合同)+ 它的 issue(边界)+ 它的计划(实施权威),不能只给计划。
- **模型档脚本按 plan 的 `Complexity` 自动切,你不手传**:高风险 plan(标 `Complexity: capable`——计费 / 权限 / migration / 跨服务)脚本自动切 `pack-executor-capable` 角色。
- **一律后台跑**:`worker.sh` 创建 Git worktree 并组好 prompt，协调者照打印的 DISPATCH 派 `Task({subagent_type:"pack-executor", prompt:PROMPT_FILE 全文, run_in_background:true})`，并把返回的 run id 用 `mmw worker note-run-id` 落账；返修从派发账本找到原 run id 与 worktree。工人回执在会话内直接回来，回执后跑 `mmw worker verify --worktree <wt>` 过边界门。
- 并行:互不依赖的 plan,各自一个 worktree,同时发多条后台 dispatch。
- **铁律在 `worktree-build` skill**:prompt 只给角色 + worktree + 三文档 + skill 指针。
- 工人在自己 worktree 提交;进度靠你 verify 后 `mmw loop step done`。
- **docs 红线 fail-closed**:`mmw worker verify` 核 docs 边界;非零 / `DOCS_VIOLATION` 禁止 `loop step done`,写修复指令 resume。

## B3. 验收(命门:你按计划验,不信工人自述)

工人回执完成且 `mmw worker verify` 边界门通过后,再由主线程亲验:

- **完整性**:plan 的每条 acceptance 真达成?跑验收命令、读 diff,不认"我做完了"。
- **测试质量(防工人写垃圾测试自己绿)**:pack-executor 写的测试它自己说了不算,你按下面完整权威逐条核(与工人写测试前读的是同一份,单源注入)，同时按目标仓库项目指令链公开的测试规则核分层落点、外部接缝、权威源和门控。测试不达标 = 缺陷,打回重写,别将就。

<!-- BEGIN: test-quality -->
**测试写作权威(plugin 随身携带,任何仓库生效;仓库薄层 TESTING.md 只补本仓库事实——目录分层/外部接缝清单/权威源指针/套件门控——不覆盖本节):**

- 测试名 = 一句业务行为陈述(如「激活码重放被拒绝」),不复述函数名。
- 每测试一个逻辑断言(一个行为事实,可含多行字段核对)。
- 断言对象 = 外部可观察事实:优先系统读接口,其次 HTTP 响应 / 文件产物 / 账本行 / CLI stdout;禁断言内部调用序列、私有函数、源码文本。
- mock 只在外部供应商接缝(网络 / 时钟 / 三方服务;本仓库哪些边界算外部看薄层);自家模块 / 服务之间禁 mock——桩和真实现会漂移,绿测试掩盖真断裂。
- 每个行为在拥有它的权威层测一次,禁跨层重复断言,不为凑覆盖率加脆弱测试。
- 测试数据经真实 producer 路径构造(共享 builder),禁手搓 producer 形状的第二份拷贝。
- 修 bug 的回归测试写进对应业务域文件,禁新建 fix_xxx 文件。
- 价格 / 文案 / 枚举不硬编码进断言,从权威源读取后对比(权威源指针看薄层)。
- 行为退役时测试同提交删;skip 存活超过一个迭代 = 删。
- 生产代码禁为测试留 seam(`_for_test` 类后门);可测试性靠依赖注入与返回结果式接口。
- 跑通仓库自己的 test guards / lint / 类型检查——它们绿是机器底线,但绿 ≠ 测得对。

**禁止形态(写了就是缺陷,验收/审查一律打回):**

| 禁止 | 为什么 | 替代 |
| --- | --- | --- |
| 源码文本 grep 断言(读源码/文档找字面量、私有符号子串) | 改名即误红、绕开字面量即漏判,双向失效;锁的是实现不是行为 | 调真函数/真命令断外部可观察结果;结构需要断言用 AST/结构化解析 |
| 逐字锁 UI 文案 / 文档 prose | 润色即假红;prose 不是合同 | 断语义键 / 状态枚举;文案从单源读取后比对 |
| 字段全集 / 默认值 / 枚举镜像断言 | 把合同 schema 抄成第二份,改一处要改两处 | 走正式契约类型 + producer→consumer 真链路 |
| 文档计数断言(某 .md 含 N 个词 / 清单 M 条) | 文档润色即假红 | 不断文档;事实从代码权威源读 |
| 墓碑路径清单(retired 文件逐一 not-exists / archive 逐一 exists) | 清单静默腐烂,整理即红 | 只断顶级目录该在 / 不该在;import 回流交行为测试天然报错 |
| 「测试测测试」meta-gate(断某 suite 清单含某测试文件名) | 套件成员从目录推导,登记表无存在理由 | 删 |
| per-file allowlist(硬编码生产文件路径清单做豁免 / 必备) | 与布局强耦合,条目静默失效 | 结构化遍历 + 结构化例外条件 |
| mock 自家服务 / 自家接缝打桩 | 桩与真实现漂移,绿测试掩盖真断裂 | 自家接缝走真代码,mock 只在外部供应商接缝 |

**准入问题(每个新测试进仓前必答):这个测试守的是哪个用户旅程 / 哪笔钱 / 哪份数据?坏了哪个用户当天受伤?答不出 = 没资格进仓。**
<!-- END: test-quality -->

- **设计一致性**:落地有没有偏离设计 / 计划的意图、合同、边界?
- 过了这三关 → `mmw loop step done --id <plan-或-pack-id>`。测试不达标也算"有缺陷":写修复指令 resume 打回**重写测试**,别将就。
- 有缺陷 / 没达成 → 写修复指令,**发回原对话**(keep context):
 ```bash
 mmw worker resume --worktree <wt> --instructions <fix.md>
 ```
 verify ↔ resume 直至这份 plan 验收通过。

**pack-executor 停下说"缺输入 / 计划与现实冲突"**:你判。afk 拍板前可 Task(subagent_type="advisor") + handoff pack(含失败日志与冲突现场)。

小问题有合理默认 → afk 直接给指令 resume(留痕);真缺输入 / 怀疑方向错 → 停下抛用户(`mmw handoff --conclusion needs-context` / `needs-redirection`),别替用户拍方向。顾问建议换路不自动 handoff。

## B4. 全 plan 验完 + 合并

每份 plan 验过(B3)→ `mmw loop step done`。所有 plan 都 done(`mmw loop status` 报 remaining=none;账本只报不拦,别拿它当验收——验收在 B3 亲验)。并行 plan 各在自己 worktree → 合并回任务分支(解 git 冲突 + 业务 / 功能冲突;本地 merge 不经红线,红线只拦 push / gh pr merge / 部署)。**每合完一个 plan 就清它的子 worktree**(不留孤儿):先删实际 worktree 根下的 `.mmw-keep-worktree`,再 `git worktree remove <实际子 worktree>` + `git branch -d worker/<目录名>`。

## B5. ③ 合同门(一次,全 plan 合并后)

全 plan 合并后跑**一次** ③(不 per-plan),只核**跨 plan 合同兑现**:

```bash
mmw review start --stage plan-impl --source "<设计文档 ## Cross-Plan Contract Anchors>"
```

照它打印的回执走——anchors 节为空脚本直接放行;有实体合同 → **核什么、三个出口全在 `references/review/plan-impl.md`**(到这步才读那一份,方法论只此一源),核对过程与逐条兑现证据写进留痕文件。**不派写码工人、不列 pack**。

## B6. 钉产出 → handoff(引擎随即强制 ④终审闸)

**先自检:动了打包面就更新出包钥匙(提示级,非硬闸)**。若本项目有 release adapter(出包钥匙、后面 package 阶段会驱动 `mmw release`),且本次落地动了**打包面**——依赖增删 / 原生扩展 / 打进包的资产 / 入口模块 / 运行时车道——就在 handoff 前按**项目自己的配钥匙规范**更新那把钥匙,让 ④终审看到的是更新后的钥匙、package 阶段的出包前 `verify_key` 不会因钥匙过时硬停。**plugin 只提示"该更钥匙了",怎么配是项目知识**(找项目的 key-config 文档 / `*.release-adapter.json` 约定位置);普通逻辑改动不碰钥匙。**能派生的自动更、结构性的补齐后再 handoff**;不确定动没动打包面,按 diff 是否触及 pyproject / package.json / 依赖清单 / 资产目录 / 原生扩展判断。

```bash
mmw handoff --conclusion pass --produced "<分支提交范围,如 base..HEAD>"
```

→ build 产物通过,**引擎强制进 ④终审闸**(build ∈ `review_gates`,phase 冻住;`mmw where` 吐 `review_start=mmw review start --stage final`,照跑;审过再 handoff pass 才到 closing)。落地撞破设计 / 计划(根因在上游)→ `needs-redirection --to-phase plan`(或 `--to-phase design`)回上游改;卡死或超轮 → `blocked`。(`needs-repair` 只原地返工 build,回不到上游。)
