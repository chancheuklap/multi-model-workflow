# Build · 落地(阶段操作指南)

> 落地 = **Codex 写代码 + Claude(你)按计划验收**。把 ②计划审过的 plan 完整落地、不偏离设计。**默认放权自主跑**(`attended` 才停问),只有真缺输入 / 方向疑 / 合并红线才停。

**红线:**
- Codex **只改源码、禁碰 `docs/`**(已焊进派发 prompt);每 Pack 一提交带 `Pack N.M`。
- **Codex 返回的事实(改了啥、测试结果)是劳动力不是信源**——你 verify 时自己 grep/读/跑坐实。
- afk 放权只动软停;merge/deploy 永远要人批(收尾阶段)。

---

## 1. 进 + 起落地 loop

`mmw where` → `prev_outputs` = plan 阶段钉的 plan 目录。读该目录拿 Task Pack 清单、acceptance、plan 间依赖。起 loop、把 plan 展开成步账(一份 plan 一步,或按 Pack 更细):

```bash
mmw loop init --kind execution
mmw loop attendance --mode afk           # 放权自主跑;盯着调试设 attended
mmw loop step add --id <plan-或-pack-id> --desc "<标题>"   # 逐项
```

判哪些 plan 互不依赖 → 并行;有 blocked_by 链 → 按序。

## 2. 派 Codex 落地(一条命令进 worktree)

每份 plan 派一个 Codex(脚本代劳开 worktree + 组装规范 prompt + codex exec):

```bash
mmw codex dispatch --plan <plan 绝对路径> --worktree <该 plan 的 worktree 绝对路径>
```

- 并行:互不依赖的 plan,各自一个 worktree,`run_in_background: true` 同时派(寻找一切安全的并行机会加快进度)。
- 脚本已把铁律焊进 prompt:严防过度设计/兜底/思考、严格 TDD、每 Pack 提交带 `Pack N.M`、禁改 `docs/`、缺输入就停下说清。
- Codex 在自己 worktree 提交(不走你的 Bash,所以 record-step 不记;进度靠你 verify 后 `mmw loop step done`)。

## 3. 验收(命门:你按计划验,不信 Codex 自述)

Codex 返回后,读它最后消息 + **自己核**(亲验):

- **完整性**:plan 的每条 acceptance 真达成?跑验收命令、读 diff,不认"我做完了"。
- **设计一致性**:落地有没有偏离设计/计划的意图、合同、边界?
- 过了这两关 → `mmw loop step done --id <plan-或-pack-id>`。
- 有缺陷 / 没达成 → 写修复指令,**发回原对话**(keep context):
  ```bash
  mmw codex resume --worktree <wt> --instructions <fix.md>
  ```
  verify ↔ resume 直至这份 plan 验收通过。

**Codex 停下说"缺输入/计划与现实冲突"**:你判——小问题有合理默认 → afk 直接给指令 resume(留痕);真缺输入 / 怀疑方向错 → 停下抛用户(`mmw handoff --conclusion needs-context` / `needs-redirection`),别替用户拍方向。

## 4. ③ 合同门(每份 plan 验完)

一份 plan 全 Pack 落地 + 验过后,起便宜合同门核跨 plan 合同兑现:

```bash
mmw review start --stage plan-impl --source "<plan 目录>"
```

按提示机器核(合同清单 cover);合同不达 → 回本 plan 补;合同根上错 → 升级。不派 Codex 判断。

## 5. 合并 + 钉产出 → handoff

并行 plan 各在自己 worktree,验完 + ③门过 → 合并回任务分支(解 git 冲突 + 业务/功能冲突),`mmw loop exit-check` 应为 DONE。然后:

```bash
mmw handoff --conclusion pass --produced "<分支提交范围,如 base..HEAD>"
```

→ advance 到 verify(④终审)。落地撞破设计/计划(根因在上游)→ `needs-repair`(回 plan)/ `needs-redirection`(方向);卡死或超轮 → `blocked`。

## 6. 守住的红线

- Codex 写、Claude 验;验收吃跑测试/读 diff 的 ground truth,不吃 Codex 自述。
- Codex 禁改 `docs/`;每 Pack 一提交带 `Pack N.M`。
- afk 只放软停;真缺输入/方向疑/合并红线必停。
- 修复走 `codex resume` 续原会话(keep context,不重派、不重做已提交 Pack)。
