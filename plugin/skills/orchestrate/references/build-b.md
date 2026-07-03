# Build · Codex 派发落地(develop)

> 落地 = **Codex 写代码 + Claude(你)按计划验收**。把 ②计划审过的 plan 完整落地、不偏离设计,各 plan 一 worktree、可并行。
> 红线:验收吃**跑测试 / 读 diff 的 ground truth**,不吃自述;afk 只放权自主跑(`attended` 才停问),真缺输入 / 方向疑 / 合并红线才停;merge/deploy 要人批(收尾阶段)。
> - Codex **只改源码、禁碰 `docs/`**(派发 prompt 焊 + `mmw codex dispatch` 收工 fail-closed 核:碰了 docs/ 报 `DOCS_VIOLATION` 退非零,写修复指令 `codex resume` 打回);每 Pack 一提交带 `Pack N.M`。
> - **Codex 返回的事实(改了啥、测试结果)是劳动力不是信源**——你 verify 时自己 grep / 读 / 跑坐实。

## 断点恢复(context 断了 / 中途回来,先跑这个)

`mmw where` 报 `inner_loop=execution` = 落地 loop 没走完。读 `loop-state.json` 的 `steps`,**认步账不认记忆**——哪步派了、派到哪全在里面:

| step 状态 | 含义 | 接着做 |
|---|---|---|
| `done` | 该 plan 已验收提交 | 跳过 |
| `pending` + 有 `worktree` + 该 worktree 内有 `codex-session` | 已派 Codex(可能已在子 worktree 提交) | **别重派**:进那 worktree 读 codex 最后消息 → 走 B3 验收;要补改用 `mmw codex resume --worktree <wt> --instructions <f>` |
| `pending` + 有 `worktree` + 无 `codex-session` | 记了映射但没派成(dispatch 崩) | 重派:回 B2 `mmw codex dispatch` |
| `pending` + 无 `worktree` | 还没轮到 | 正常 B1→B2 派 |

## B1. 进 + 起落地 loop

`mmw where` → `prev_outputs` = plan 阶段钉的 plan 目录。读该目录拿 Task Pack 清单、acceptance、plan 间依赖。起 loop、把 plan 展开成步账(**一份 plan 一步**,派前把 plan 路径 + 分配的子 worktree 记进步账——断点恢复靠它认"哪步=哪 plan=派到哪"):

```bash
mmw loop init --kind execution
mmw loop attendance --mode afk           # 放权自主跑;盯着调试设 attended
mmw loop step add --id <plan-id> --desc "<标题>" --plan <plan 绝对路径> --worktree <该 plan 的子 worktree 绝对路径>   # 逐项
```

判哪些 plan 互不依赖 → 并行;有 blocked_by 链 → 按序。

## B2. 派 Codex 落地(一条命令进 worktree)

每份 plan 派一个 Codex(脚本代劳开 worktree + 组装规范 prompt + codex exec):

```bash
mmw codex dispatch --plan <plan 绝对路径> --worktree <该 plan 的 worktree 绝对路径> \
  --design <设计文档绝对路径> --issue <该 plan 对应 issue 绝对路径>
```

- **子 worktree 落点定死**:`<主仓库>/.claude/worktrees/<slug>-plan-<NNN>`(与任务 worktree 同层,别散落);脚本会自动挂 `codex/<目录名>` 分支并从 `--base`(默认 HEAD)分叉。

- **三文档都传**:Codex 开工要读设计(意图 / 合同)+ 它的 issue(边界)+ 它的计划(实施权威),不能只给计划。
- **按 plan 的 `Complexity` 切模型档**(plan header / Task Pack 的 `Complexity` 字段):`capable`(计费 / 权限 / migration / 跨服务等高风险)→ 加 `--model gpt-5.5 --effort xhigh`;`cheap` / `standard` 用默认(gpt-5.4 xhigh)。高风险 plan 别用低档模型落地。
- 并行:互不依赖的 plan,各自一个 worktree,`run_in_background: true` 同时派(寻找一切安全的并行机会加快进度)。
- **铁律不在 prompt、在 Codex 侧 `worktree-build` skill**(渐进加载,开工前不占 context):prompt 只给角色 + worktree + 三文档路径 + 指向 skill。skill 管:严格 TDD(用 /tdd)、防过度设计 / 兜底、测试对标仓库标准、每 Pack 提交带 `Pack N.M`、禁改 `docs/`、卡住停下报清。
- Codex 在自己 worktree 提交(不走你的 Bash,所以 record-step 不记;进度靠你 verify 后 `mmw loop step done`)。

## B3. 验收(命门:你按计划验,不信 Codex 自述)

Codex 返回后,读它最后消息 + **自己核**(亲验):

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
  mmw codex resume --worktree <wt> --instructions <fix.md>
  ```
  verify ↔ resume 直至这份 plan 验收通过。

**Codex 停下说"缺输入 / 计划与现实冲突"**:你判——小问题有合理默认 → afk 直接给指令 resume(留痕);真缺输入 / 怀疑方向错 → 停下抛用户(`mmw handoff --conclusion needs-context` / `needs-redirection`),别替用户拍方向。

## B4. 全 plan 验完 + 合并

每份 plan 验过(B3)→ `mmw loop step done`。所有 plan 都 done 后 `mmw loop exit-check` 应为 DONE(执行 loop 收工)。并行 plan 各在自己 worktree → 合并回任务分支(解 git 冲突 + 业务 / 功能冲突;`guard-redline` 只拦主分支,任务分支间合并放行)。**每合完一个 plan 就清它的子 worktree**(不留孤儿):`git worktree remove <子 worktree>` + `git branch -d codex/<目录名>`。

## B5. ③ 合同门(一次,全 plan 合并后)

**跨 plan 合同要等所有 plan 都在场才能核**(provider 在 A、consumer 在 B),所以 ③ 在这跑一次、不 per-plan。执行 loop 已 DONE(全 Pack 已提交,B4 已机器核),③ 只核**跨 plan 合同兑现**:

```bash
mmw review start --stage plan-impl --source "<设计文档 ## Cross-Plan Contract Anchors>"
```

照它打印的 brief 走——**核什么、怎么 checklist、三个出口全在 `references/review/plan-impl.md`**(到这步才读那一份,方法论只此一源)。**不派 Codex、不列 pack**(全 Pack 提交已由 B4 exit-check 保证)。

## B6. 钉产出 → handoff(引擎随即强制 ④终审闸)

```bash
mmw handoff --conclusion pass --produced "<分支提交范围,如 base..HEAD>"
```

→ build 产物通过,**引擎强制进 ④终审闸**(build ∈ `review_gates`,phase 冻住;`mmw where` 吐 `review_start=mmw review start --stage final`,照跑;审过再 handoff pass 才到 closing)。落地撞破设计 / 计划(根因在上游)→ `needs-redirection --to-phase plan`(或 `--to-phase design`)回上游改;卡死或超轮 → `blocked`。(`needs-repair` 只原地返工 build,回不到上游。)

## 守住的红线

- 验收吃跑测试 / 读 diff 的 ground truth,不吃自述。**测试本身也要对标仓库标准审**:绿 ≠ 测得对,垃圾测试(空断言 / mock 自家 / 测私有 / 非权威层)当缺陷打回重写。
- Codex 写、Claude 验,Codex 禁改 `docs/`、每 Pack 一提交带 `Pack N.M`。
- afk 只放软停;真缺输入 / 方向疑 / 合并红线必停。
- 修复走 `codex resume` 续原会话(keep context,不重派、不重做已提交 Pack)。
