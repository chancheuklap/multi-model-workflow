# plugin2 现状报告(investigate · 2026-06-29)

> 任务:对 plugin2 从头到尾优化。investigate-internal workflow(5 topic / 6 agent)产出,主线程已亲验承重事实。
> **取证不判定**:只摆现状证据,方案/取舍留 design。路径相对仓库根。

## A. 三原则落实(SKILL 路由 / reference 整份 / 不读无关)

- ✅ `plugin2/skills/orchestrate/SKILL.md:1-39` 纯路由(Step0 恢复 + Step1 路由表 → 4 scenario),无方法论内联。
- ❌ `plugin2/skills/write-plan-doc/SKILL.md:37-101` 内联 plan 全部方法论(角色声音/Step1-6 全流程/Git 纪律/handoff 细则),与 orchestrate 纯路由形态不对称。
- ❌ `plugin2/skills/write-design-doc/SKILL.md:27-32` 收尾段内联拆 issue + handoff 结论词细则。
- §/见上见下 **同文档碎片跳转**:`references/review.md:18`(见 §3、§1–§2)、`references/closing.md:3`(见 §合并红线)、`write-design-doc/references/discussion.md:54,61`、三份 `references/scenario/*.md:36,64`(见下「回执」「收尾」)。
- **跨文档碎片指针**:`references/review/final.md:20` + `review/plan-impl.md:16`(→ quartet.md 附录);`write-plan-doc/references/task-pack.md:3,17,32,68` + `plan-self-check.md:12`(→ plan-rigor.md);`write-design-doc/references/design-doc-template.md:65`(→ design-rigor.md)。`task-pack.md` ↔ `plan-rigor.md` 互相回指,单读任一份都不自洽。
- `references/review.md:9-56` 单文件捆 4 道审(①②④ Codex 真审 + ③ 机器合同门),做①设计审须连带读无关的③。

## B. 阶段链路(六阶段+审闸+接力单+回执)

- 主干/审闸/接力单机制自洽:`routes.json:19,40-44`、`flow.sh:71-128`(回执)、`flow.sh:144,206`(接力单钉/读)、test_e2e 验 plan→build 接力。
- phase reference **復述确定逻辑**(与 receipt-jump/flow.sh 重复):`build.md:69`、`review.md:11,38`、`closing.md:18`、`investigate.md:57`。
- **plan 落点多处不一致**:`routes.json:33` `docs/plans/<slug>/` vs `write-plan-doc/SKILL.md:70` `docs/plans/<YYYY-MM-DD>-<slug>/`,SKILL 内部 :70 vs :98 又不一致;`prepare.sh:51` 只 scaffold design/issues/context,**不建 docs/plans**;`task-manifest.schema.json` 的 `docs` 无 `plans` 字段(plan 落点不在单一真相源,只靠接力单)。
- **design 落点不一致**:`routes.json:32` `docs/design/<slug>.md` vs `prepare.sh:64` `docs/design/$slug`(无 .md)。
- **死配置/双源**:`routes.json` 的 `actions`(:7-13)、`backbone`(:19)**无任何脚本读取**,结论→动作硬编码在 flow.sh case,无同步校验。
- **状态回流缺口**:`needs-context` → flow.sh 设 `status=waiting-user`,但无命令把它翻回 `active`(`prepare.sh:86` resume 只读不改),直到下次 handoff 才重算。

## C. 脚本/hook 健壮性(bash 3.2;★ 为实测复现)

- ★ **fail-open 数据丢失**:`loop.sh:28` `write()` / `flow.sh:28` `write_manifest()` = `cat>tmp; mv`。上游 jq 失败→空 stdin→mv 把真文件覆盖成 0 字节。实测 `loop finding add --confidence "8/10"`(非数字,LLM 现实会传)→ `--argjson` 失败 → loop-state.json 从 278B 截空,丢 checklist/findings(`loop.sh:100-101`)。
- ★ **损坏伪装成功**:`loop.sh:141-142` exit-check 不校验 JSON 合法;空文件 → `.pause` 取空串 → 判定输出 `PAUSED:`(空因)且 rc=0。
- ★ **看守 fail-open**:`hooks/guard-loop.sh:15-20` exit-check 出错 `|| exit 0` 放行;`PAUSED:*` 与默认分支都放停 → 损坏/空状态静默解除"未完成不让停"。整链实测:非数字 confidence → 截空 → 假 PAUSED → 子代理被放停。**违"不搞静默兜底"硬规则。**
- 其他吞错:`prepare.sh:115`(worktree remove 失败被 `2>&1`+`|| true` 吞)、`codex-worker.sh:58-66`(codex 非零退出仍返回 0)、`record-step.sh:21`(`|| true` 吞 step done 报错,进度静默不记)。
- **测试全是命令级空跑**:无任何用例注入损坏/空/非法 JSON;截断与假 PAUSED 完全没覆盖(test_loop/test_codex_worker/test_prepare/test_hooks)。

## D. 断点续传(resume)

- 外层够用:`task.json` 持久化 phase_index/gate/计数/phase_outputs/history;`mmw where` 叠 phase_bindings 给 load/do/then(`flow.sh:189-233`)。
- **缺口**:`round` 只 init=0、**全仓无 increment**(`loop.sh:38`),但 schema(loop-state.schema.json:82)+ 审 brief(review.sh:70)都依赖它数轮——审轮上限无支撑。`prev_outputs` 只取 phases[i-1] 不汇总更上游(`flow.sh:206`)。外层(where/handoff/resume)**全文不读 loop-state**,内层 loop 进度不进外层恢复。plan→worktree 映射、in-flight 派发态都不持久化。无 SessionStart hook → 断点恢复靠用户重触发 skill 手跑 where。

## E. 迁移/接线(最致命)

- **plugin2 未注册、hook 未接线**:无 `plugin2/.claude-plugin/plugin.json`、无 `hooks.json`;`marketplace.json:18` 仍指 `./plugin` v5.2.1。3 个 hook(guard-loop/guard-redline/record-step)**没接线就是死脚本**。
- **无 `plugin2/agents/`**:旧有 7 个 agent;`write-plan-doc` 派的 `plan-writer` 在 plugin2 不存在(派了个不存在的 subagent)。
- **record-step 依赖却无强制**:record-step 抽 `Pack N.M`,但旧 `enforce-plan-commit.sh` 没迁,无 hook 强制提交真用该格式。
- **旧能力未迁**(择要):budget 子系统、idempotency 重放保护、direction-check、review-history、merge-brief、dep-batches、各 validate-dispatch hook、`guard-doc-edit`(现仅靠 codex prompt 文本约束"禁改 docs")、`verify-maturity` 成熟度门 + run-all-tests 聚合、build 7 resolver。

## 旁路(已 spinoff,不在本任务主线)

- `[out-of-scope]` 旧 `plugin/state-schema/routes-v1.json:82-105` repair_policy 疑似重复两段(在禁区旧 plugin 内)。

## Open questions(留 design 拍)

- 终态:plugin2 替换 plugin(切 marketplace source)还是并存?决定 E 哪些"必补"。
- `agents/` 独立目录 vs 复用仓库根 `skills/+agents/`?write-plan-doc 的 plan-writer 实指哪套?
- 三原则判据:"碎片跳转"是否含同文档"见上/见下/见 §N",还是仅跨文档?(影响 A 的修整范围)
