# Build · 写码工人派发落地(develop)

> 落地 = **写码工人改代码 + 主线程按计划验收**。把 ②计划审过的 plan 完整落地、不偏离设计,各 plan 一 worktree、可并行。
> 红线:验收吃**跑测试 / 读 diff 的 ground truth**,不吃自述;afk 只放权自主跑(`attended` 才停问),真缺输入 / 方向疑 / 合并红线才停;push/deploy 要人批(收尾阶段;本地 merge 不拦)。
> - 工人 **只改源码、禁碰 `docs/`**:`dispatch`/`resume` 末脚本自动 fail-closed。碰了 docs → 修复指令 resume 打回;每 Pack 一提交带 `Pack N.M`。
> - **工人返回的事实是劳动力不是信源**——你 verify 时自己 grep / 读 / 跑坐实。

## 断点恢复(context 断了 / 中途回来,先跑这个)

`mmw where` 报 `inner_loop=execution` = 落地 loop 没走完。读 `loop-state.json` 的 `steps`,**认步账不认记忆**——哪步派了、派到哪全在里面:

| step 状态 | 含义 | 接着做 |
|---|---|---|
| `done` | 该 plan 已验收提交 | 跳过 |
| `pending` + 有 `worktree` + 该 worktree 内有 `codex-session` | 已派写码工人(可能已在子 worktree 提交) | **别重派**:进那 worktree 读 codex 最后消息 → 走 B3 验收;要补改用 `mmw worker resume --worktree <wt> --instructions <f>` |
| `pending` + 有 `worktree` + 无 `codex-session` 但有 `codex-logs/run.log` | 派过但中途被杀(如超时),Codex 可能已提交部分 Pack | **别重派**:先核 worktree 已有提交,写续做指令走 `mmw worker resume`(session 由脚本自动从 run.log 捞回) |
| `pending` + 有 `worktree` + 无 `codex-session` 也无 `run.log` | 记了映射但没派成(dispatch 崩) | 重派:回 B2 `mmw worker dispatch` |
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
3. **验收**(B3 同法):跑测试 / 读 diff 亲验,测试质量对标仓库标准,不吃自述。
4. **回 ④重审**:若返修触碰跨 plan 合同,先重跑 B5 ③;否则直接 `mmw handoff --conclusion pass --produced "<base..HEAD>"` → 引擎重进 ④终审闸,**全新审者重审**(改动过闸后 source-stability 指纹也会要求重审)。返修满 `max_repair` 仍不过 → 引擎自动 `blocked` 上报。

## B1. 进 + 起落地 loop

`mmw where` → `prev_outputs` = plan 阶段钉的 plan 目录。读该目录拿 Task Pack 清单、acceptance、plan 间依赖。起 loop、把 plan 展开成步账(**一份 plan 一步**,派前把 plan 路径 + 分配的子 worktree 记进步账——断点恢复靠它认"哪步=哪 plan=派到哪"):

```bash
mmw loop init --kind execution
mmw loop attendance --mode afk # 放权自主跑;盯着调试设 attended
mmw loop step add --id <plan-id> --desc "<标题>" --plan <plan 绝对路径> --worktree <该 plan 的子 worktree 绝对路径> # 逐项
```

判哪些 plan 互不依赖 → 并行;有 blocked_by 链 → 按序。

## B2. 派写码工人落地

每份 plan 派一个 Codex 写码工人(`mmw worker dispatch` 代劳 worktree + prompt):

```bash
mmw worker dispatch --plan <plan 绝对路径> --worktree <该 plan 的 worktree 绝对路径> \
 --design <设计文档绝对路径> --issue <该 plan 对应 issue 绝对路径>
```

- **子 worktree 落点定死**:`<主仓库>/.claude/worktrees/<slug>-plan-<NNN>`(与任务 worktree 同层,别散落);脚本挂 `codex/<目录名>` 分支,从 `--base`(默认 HEAD)分叉。

- **三文档都传**:Codex 开工要读设计(意图 / 合同)+ 它的 issue(边界)+ 它的计划(实施权威),不能只给计划。
- **模型档脚本按 plan 的 `Complexity` 自动切,你不手传**:高风险 plan(标 `Complexity: capable`——计费 / 权限 / migration / 跨服务)脚本自动切高档。`--model`/`--effort` 仅在你要临时覆盖时才传。
- **一律后台跑**:dispatch / resume 都用 Bash 后台启动 `codex exec`。完成读 `CODEX_EXIT`/`SESSION`/`.claude/multi-model-workflow/codex-logs/last.md`。
- 并行:互不依赖的 plan,各自一个 worktree,同时发多条后台 dispatch。
- **铁律在 `worktree-build` skill**:prompt 只给角色 + worktree + 三文档 + skill 指针。
- 工人在自己 worktree 提交;进度靠你 verify 后 `mmw loop step done`。
- **docs 红线 fail-closed**:`dispatch`/`resume` 末脚本自动 `check_docs_boundary`;非零 / `DOCS_VIOLATION` 禁止 `loop step done`,写修复指令 resume。

## B3. 验收(命门:你按计划验,不信工人自述)

Codex 返回后,读它最后消息(dispatch 回执里打印;原文在 `<该 plan 的 worktree>/状态平面/codex-logs/last.md`)+ **自己核**(亲验):

- **完整性**:plan 的每条 acceptance 真达成?跑验收命令、读 diff,不认"我做完了"。
- **测试质量(对标仓库标准,防 Codex 写垃圾测试自己绿)**:Codex 写的测试它自己说了不算,你审。先**定位并读仓库测试治理文档**(常见:仓库根或 tests/ 下 TESTING.md、AGENTS.md / CLAUDE.md 测试节、tests 目录 README);**定位不到必须在 B3 验收回执里标 `no-test-standard waiver`,不准默默跳过**。审 Codex 这份 plan 新增 / 改动的测试,达不达标:
 - 测**公开可观察行为**(系统读接口 / HTTP 响应 / 文件产物 / 账本行),不断言私有函数 / 内部调用顺序 / 源码文本;
 - mock **只在外部供应商边界**(网络 / 时钟 / 三方),**不 mock 仓库内部自家接缝**;
 - 每个行为在**拥有它的权威层测一次**,不跨层重复断言、不凑覆盖率;
 - 断言**非空、非纯存在性**(`assert True` / 只断"对象存在" = 垃圾);无整段逻辑逐字复制粘贴;
 - 跨模块边界用**正式契约类型**,不裸 dict;违反**仓库声明的禁形态**(若有)即缺陷;
 - 跑通**仓库自己的 test guards / lint / 类型检查**(它们绿是机器底线,但绿 ≠ 测得对)。
- **设计一致性**:落地有没有偏离设计 / 计划的意图、合同、边界?
- 过了这三关 → `mmw loop step done --id <plan-或-pack-id>`。测试不达标也算"有缺陷":写修复指令 resume 打回**重写测试**,别将就。
- 有缺陷 / 没达成 → 写修复指令,**发回原对话**(keep context):
 ```bash
 mmw worker resume --worktree <wt> --instructions <fix.md>
 ```
 verify ↔ resume 直至这份 plan 验收通过。

**Codex 停下说"缺输入 / 计划与现实冲突"**:你根据计划、设计和一手证据判断。小问题有合理默认 → afk 直接给指令 resume(留痕);真缺输入 / 怀疑方向错 → 停下抛用户(`mmw handoff --conclusion needs-context` / `needs-redirection`),别替用户拍方向。

## B4. 全 plan 验完 + 合并

每份 plan 验过(B3)→ `mmw loop step done`。所有 plan 都 done 后 `mmw loop exit-check` 应为 DONE(执行 loop 收工)。并行 plan 各在自己 worktree → 合并回任务分支(解 git 冲突 + 业务 / 功能冲突;本地 merge 不经红线,红线只拦 push / gh pr merge / 部署)。**每合完一个 plan 就清它的子 worktree**(不留孤儿):`git worktree remove <子 worktree>` + `git branch -d codex/<目录名>`。

## B5. ③ 合同门(一次,全 plan 合并后)

全 plan 合并后跑**一次** ③(不 per-plan),只核**跨 plan 合同兑现**:

```bash
mmw review start --stage plan-impl --source "<设计文档 ## Cross-Plan Contract Anchors>"
```

照它打印的 brief 走——**核什么、怎么 checklist、三个出口全在 `references/review/plan-impl.md`**(到这步才读那一份,方法论只此一源)。**不派写码工人、不列 pack**(全 Pack 提交已由 B4 exit-check 保证)。

## B6. 钉产出 → handoff(引擎随即强制 ④终审闸)

**先自检:动了打包面就更新出包钥匙(提示级,非硬闸)**。若本项目有 release adapter(出包钥匙、后面 package 阶段会驱动 `mmw release`),且本次落地动了**打包面**——依赖增删 / 原生扩展 / 打进包的资产 / 入口模块 / 运行时车道——就在 handoff 前按**项目自己的配钥匙规范**更新那把钥匙,让 ④终审看到的是更新后的钥匙、package 阶段的出包前 `verify_key` 不会因钥匙过时硬停。**plugin 只提示"该更钥匙了",怎么配是项目知识**(找项目的 key-config 文档 / `*.release-adapter.json` 约定位置);普通逻辑改动不碰钥匙。**能派生的自动更、结构性的补齐后再 handoff**;不确定动没动打包面,按 diff 是否触及 pyproject / package.json / 依赖清单 / 资产目录 / 原生扩展判断。

```bash
mmw handoff --conclusion pass --produced "<分支提交范围,如 base..HEAD>"
```

→ build 产物通过,**引擎强制进 ④终审闸**(build ∈ `review_gates`,phase 冻住;`mmw where` 吐 `review_start=mmw review start --stage final`,照跑;审过再 handoff pass 才到 closing)。落地撞破设计 / 计划(根因在上游)→ `needs-redirection --to-phase plan`(或 `--to-phase design`)回上游改;卡死或超轮 → `blocked`。(`needs-repair` 只原地返工 build,回不到上游。)
