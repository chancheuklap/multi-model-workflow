# Build · 落地(阶段操作指南)

> 落地阶段。**两种落地模式,进来先看 `mmw where` 报的 `scenario` 选一种**:
> - **模式 A · 主线程就地 TDD**(`scenario=small-change` 小改 / `scenario=bug` 定点修):改动小、根因清楚 → 主线程自己用 `/tdd` 写测试 → 实现 → 验证 → 提交,**不派 Codex、不开子 worktree**(已在任务 worktree 内)。
> - **模式 B · Codex 派发**(`scenario=develop` 大活):多份 ②计划审过的 plan → Codex 写 + Claude 验,各 plan 一 worktree、可并行。
>
> 两模式共同红线:验收吃**跑测试 / 读 diff 的 ground truth**,不吃自述;**默认放权自主跑**(`attended` 才停问),只有真缺输入 / 方向疑 / 合并红线才停;merge/deploy 永远要人批(收尾阶段)。

---

## 模式 A · 主线程就地 TDD(small-change / bug)

主线程自己落地,**不派 Codex**。`prev_outputs`:small-change 没上游产物;bug 带 investigate 钉的根因报告(`docs/investigating/<slug>.md`)。

### A1. 判改动面 → 要不要先写一份单计划

| 改动面 | 怎么做 |
|---|---|
| **定点小改 / 单文件单点修** | 跳过计划,直接 A2 逐步 TDD。 |
| **跨多文件 / 多步骤** | 先写**一份单计划**理清 Task Pack:主线程读完 `${CLAUDE_PLUGIN_ROOT}/skills/orchestrate/references/plan/task-pack.md`(Task Pack 模板 + TDD 步骤一份),落 `docs/plans/<slug>/001-<slug>.md`(**主线程自己写,不派 plan-writer、不进 ②计划审**——bug/小改无审闸),再按 Pack 逐个 TDD。 |

### A2. 逐步 TDD（用 `/tdd`）

**起不起 loop 看改动面**(spec:small-change 不进 loop):

| 改动面 | loop |
|---|---|
| **真一两处的小改**(single-change) | **不起 loop**,直接 TDD 改完提交 → A3 handoff。 |
| **多步**(bug 定点修跨多文件 / A1 的单计划) | 起 execution loop 记步账,逐步走完再 handoff:`mmw loop init --kind execution` → `mmw loop attendance --mode afk` → 每步 `mmw loop step add --id <N.M> --desc "<标题>"`。 |

每步严格 TDD(**测试按仓库测试治理文档的分层 + 写作规范写**——定位 TESTING.md / AGENTS.md 测试节 / tests 规则,找不到才用通用 TDD 纪律;跑通仓库自己的 test guards / lint):

- **bug 定点修**:先按根因报告写一条**复现失败测试**(没复现就先复现,这步等于坐实根因)→ 最小修 → 测试转绿 → 提交。
- **small-change**:写失败测试 → 最小实现 → 转绿 → 提交。
- 主线程在任务 worktree 内提交,**commit message 含 `Pack N.M`**——起了 loop 时 `record-step` hook 据此自动标 step done(没起 loop 则无需,直接提交)。一步一提交。

### A3. 收口 → handoff

改完测试全绿(起了 loop 的话 `mmw loop exit-check` = DONE)后:

```bash
mmw handoff --conclusion pass --produced "<分支提交范围,如 base..HEAD>"
```

→ advance 到 verify(④终审验修复 + 回归)。修着撞出超范围问题 → `mmw spinoff` 登记,别就地扩;根因其实是系统性设计级(要重做设计/拆计划)→ 原地升级完整设计路 `mmw task escalate --to develop`(worktree 不重开、已查成果留着,游标回 investigate 带设计意图重查),升级前先一句话告诉用户。

---

## 模式 B · Codex 派发(develop)

> 落地 = **Codex 写代码 + Claude(你)按计划验收**。把 ②计划审过的 plan 完整落地、不偏离设计。

**红线:**
- Codex **只改源码、禁碰 `docs/`**(已焊进派发 prompt);每 Pack 一提交带 `Pack N.M`。
- **Codex 返回的事实(改了啥、测试结果)是劳动力不是信源**——你 verify 时自己 grep/读/跑坐实。

### B1. 进 + 起落地 loop

`mmw where` → `prev_outputs` = plan 阶段钉的 plan 目录。读该目录拿 Task Pack 清单、acceptance、plan 间依赖。起 loop、把 plan 展开成步账(一份 plan 一步,或按 Pack 更细):

```bash
mmw loop init --kind execution
mmw loop attendance --mode afk           # 放权自主跑;盯着调试设 attended
mmw loop step add --id <plan-或-pack-id> --desc "<标题>"   # 逐项
```

判哪些 plan 互不依赖 → 并行;有 blocked_by 链 → 按序。

### B2. 派 Codex 落地(一条命令进 worktree)

每份 plan 派一个 Codex(脚本代劳开 worktree + 组装规范 prompt + codex exec):

```bash
mmw codex dispatch --plan <plan 绝对路径> --worktree <该 plan 的 worktree 绝对路径>
```

- 并行:互不依赖的 plan,各自一个 worktree,`run_in_background: true` 同时派(寻找一切安全的并行机会加快进度)。
- 脚本已把铁律焊进 prompt:严防过度设计/兜底/思考、严格 TDD、每 Pack 提交带 `Pack N.M`、禁改 `docs/`、缺输入就停下说清。
- Codex 在自己 worktree 提交(不走你的 Bash,所以 record-step 不记;进度靠你 verify 后 `mmw loop step done`)。

### B3. 验收(命门:你按计划验,不信 Codex 自述)

Codex 返回后,读它最后消息 + **自己核**(亲验):

- **完整性**:plan 的每条 acceptance 真达成?跑验收命令、读 diff,不认"我做完了"。
- **测试质量(对标仓库标准,防 Codex 写垃圾测试自己绿)**:Codex 写的测试它自己说了不算,你审。先**定位并读仓库测试治理文档**(常见:仓库根或 tests/ 下 TESTING.md、AGENTS.md / CLAUDE.md 测试节、tests 目录 README);**定位不到必须在 verify 回执里标 `no-test-standard waiver`,不准默默跳过**。审 Codex 这份 plan 新增/改动的测试,达不达标:
  - 测**公开可观察行为**(系统读接口 / HTTP 响应 / 文件产物 / 账本行),不断言私有函数 / 内部调用顺序 / 源码文本;
  - mock **只在外部供应商边界**(网络 / 时钟 / 三方),**不 mock 仓库内部自家接缝**;
  - 每个行为在**拥有它的权威层测一次**,不跨层重复断言、不凑覆盖率;
  - 断言**非空、非纯存在性**(`assert True` / 只断"对象存在" = 垃圾);无整段逻辑逐字复制粘贴;
  - 跨模块边界用**正式契约类型**,不裸 dict;违反**仓库声明的禁形态**(若有)即缺陷;
  - 跑通**仓库自己的 test guards / lint / 类型检查**(它们绿是机器底线,但绿 ≠ 测得对)。
- **设计一致性**:落地有没有偏离设计/计划的意图、合同、边界?
- 过了这三关 → `mmw loop step done --id <plan-或-pack-id>`。测试不达标也算"有缺陷":写修复指令 resume 打回**重写测试**,别将就。
- 有缺陷 / 没达成 → 写修复指令,**发回原对话**(keep context):
  ```bash
  mmw codex resume --worktree <wt> --instructions <fix.md>
  ```
  verify ↔ resume 直至这份 plan 验收通过。

**Codex 停下说"缺输入/计划与现实冲突"**:你判——小问题有合理默认 → afk 直接给指令 resume(留痕);真缺输入 / 怀疑方向错 → 停下抛用户(`mmw handoff --conclusion needs-context` / `needs-redirection`),别替用户拍方向。

### B4. 全 plan 验完 + 合并

每份 plan 验过(B3)→ `mmw loop step done`。所有 plan 都 done 后 `mmw loop exit-check` 应为 DONE(执行 loop 收工)。并行 plan 各在自己 worktree → 合并回任务分支(解 git 冲突 + 业务/功能冲突)。

### B5. ③ 合同门(一次,全 plan 合并后)

**跨 plan 合同要等所有 plan 都在场才能核**(provider 在 A、consumer 在 B),所以 ③ 在这跑一次、不per-plan。执行 loop 已 DONE(全 Pack 已提交,B4 已机器核),③ 只核**跨 plan 合同兑现**,不再列 pack:

```bash
mmw review start --stage plan-impl --source "<设计文档 ## Cross-Plan Contract Anchors>"
```

按打印的 brief:逐条合同 `checklist add` → grep/Read 坐实 provider/consumer/版本/迁移/登记 → `checklist cover --evidence <file:line>`;清单全 cover → `exit-check` DONE。合同不达 → `needs-redirection --to-phase build`(回落地补);合同根上错(设计的合同本身不成立)→ `needs-redirection --to-phase design`。**不派 Codex 判断、不列 pack**(全 Pack 提交已由 B4 exit-check 保证)。

### B6. 钉产出 → handoff

```bash
mmw handoff --conclusion pass --produced "<分支提交范围,如 base..HEAD>"
```

→ advance 到 verify(④终审)。落地撞破设计/计划(根因在上游)→ `needs-redirection --to-phase plan`(或 `--to-phase design`)回上游改;卡死或超轮 → `blocked`。(`needs-repair` 只原地返工 build,回不到上游。)

---

## 守住的红线(两模式)

- 验收吃跑测试/读 diff 的 ground truth,不吃自述。**测试本身也要对标仓库标准审**:绿 ≠ 测得对,垃圾测试(空断言 / mock 自家 / 测私有 / 非权威层)当缺陷打回重写。
- 模式 A 主线程就地 TDD、不派 Codex;模式 B Codex 写、Claude 验,Codex 禁改 `docs/`、每 Pack 一提交带 `Pack N.M`。模式 A 是 Claude 自写自验(无独立 checker,偏弱),适用面就是小改 / 定点修;重型落地走模式 B 的 Codex 写 + Claude 独立审测试。
- afk 只放软停;真缺输入/方向疑/合并红线必停。
- 模式 B 修复走 `codex resume` 续原会话(keep context,不重派、不重做已提交 Pack)。
