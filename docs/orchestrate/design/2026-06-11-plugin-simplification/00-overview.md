# Plugin 精简总方案 · 总览

> 状态:**已落地**(2026-06-11)。批次 A/B/C 完成(7 个 commit,净 −171 行,三验证门全绿);批次 C 的路线合并(C1/C2)按负责人决策保留 5 条;批次 D(hook)经逐脚本通读后**判定无可安全精简项**,详见 §3 批次 D。所有"删/改"依据均已由 Coordinator 亲自 grep/Read/实跑验证,非二手结论。
>
> 一句话:在**不丢功能、性能、稳定性、适配性**的前提下,清掉一批空转的死代码、把重复的两份收敛成一份、把折叠后残留的化石注释清干净——让这套多模型工作流更轻、更不容易出错。**结论:真正的冗余在死代码层(已清),路线层与 hook 层是克制的设计,不是臃肿。**

---

## 1. 范围与守住的底线

**本方案实际做成**:① 无损死代码 / 重复清理(批次 A,5 项全做);② D10 折叠后的化石清理(批次 B,5 项全做);③ 子模式文档澄清(批次 C 的 C3)。

**评估后未做**:路线 5→3(C1)与 verdict 压缩(C2)——负责人决策**保留 5 条只做低风险项**,且实测"路线名 = phase 名"深耦合使合并属高风险动地基;hook 13→8(批次 D)——逐脚本通读后判定**无既低风险又真精简的项**(§3 批次 D 给出逐项依据)。

**明确不动(守住的不变量)**:

| 守住的 | 说明 |
|---|---|
| 双执行载体(codex / claude 两条 lane) | 行为、能力、用户怎么选,**一行不改**。codex lane 已实测可用(见 [`codex-sandbox-probe.md`](codex-sandbox-probe.md)) |
| 写审异家 · 并行批次 · 隔离 worktree · 断点续传 | 核心能力与性能特性,全保留 |
| 质量门最小集 | 子代理返回必验、worker 禁改 `docs/`、未勾选任务阻断 push——一个不动 |
| Ruling 2 双文件状态模型 | 合并属"动地基",收益存疑,本轮**不碰**,另行评估 |
| 三个验证门 | 每批改完 `build --check` / `run-all-tests` / `verify-maturity` 必须全绿,行为走查无回归 |

---

## 2. 关键决策记录

- **D1 · codex lane 保留现状。** 起初怀疑"Codex 读不到 / 调不动 plugin 脚本",实测否定了这个判断(读放开、执行允许、写靠 `--add-dir` 放行,均验证可用)。真正的问题是"耦合重、靠一串假设撑着",属于**可选降耦合**而非**必须修**。对一条已验证能跑的核心路径动刀,风险大于收益,故本轮不动。详见 [`codex-sandbox-probe.md`](codex-sandbox-probe.md)。

- **D2 · 路线 5→3。** `direct-repair` / `bug-investigation` / `multi-pr-merge` 三条在 `routes-v1.json` 的六个运行期字段里**除路线名外完全相同**(`phase_transitions=[]`、`budget=unlimited`、`review_required=[]`、无 `repair_policy`、`commit_format=null`),合并为单条 `route-worker`。**注意:合并的是 route 数据记录,不是抹掉三个场景**——派 RCA(bug)、派 executor(direct-repair)、merge-brief 驱动(multi-pr)三个场景照旧存在,由 SKILL 散文按场景选 agent(这本就是现状),只是不再各占一条顶层 route 记录。

- **D3 · 聚焦无损,不蔓延。** `state.sh` 的深度瘦身(`review-history` awk 插表格 ~130 行、`merge-brief verify` 的 python-in-bash)列为**后续可选**,不进本轮——它们与 review / multi-pr 流程耦合,风险中等,且不属于"纯死代码"。

---

## 3. 改动清单(分批,均附已验证依据)

### 批次 A · 无损死代码 / 重复清理(零功能损失)

| # | 改动 | 已验证依据 | 状态 |
|---|---|---|---|
| A1 | 删 `self-verify` 命令 + `self_verifications` 字段 + 5 处引用 | `state.sh:594` 生产 `return 0` 空转;字段无生产读者 | ✅ 已完成 `f2efc7d` |
| A2 | 删 `agent-id` 的 pack-level 死分支 | 全部真实调用方用 `--plan-id`,无一用 `--pack-id` | ✅ 已完成 `e1fab1f` |
| A3 | 删 `redline-check.sh` + 测试,保留 SKILL 红线类别表 | 不被任何 hook 调用,纯 advisory,关键词与 SKILL 表重复两份;LLM 本就能判红线 | ✅ 已完成 `5cf6b84` |
| A4 | `review-dispatch.content-only` 模板 → 收敛到 `_shared/review-prompt-quartet.md` 运行时注入 | 该锚点只注入 1 处(`codex-review/SKILL.md`),与 quartet 是同一内容的第二份拷贝(措辞已不同步) | ✅ 已完成 `fdde179` |
| A5 | `_shared/repair-regression-evidence.md` 合并回 `repair-routing.md` | 全仓库只被 `repair-routing.md:28` 一处引用——放 `_shared/` 是过度抽象 | ✅ 已完成 `54bf889` |

### 批次 B · D10 化石清理(纯死注释 / 死分支,hotfix 活逻辑保留)· ✅ 已完成 `206b9ec` + `085e0ae`

> 背景:此前一次 D10 决策把 hotfix/quickfix/spike/maintenance 从独立 route 折叠掉,但落地留了残骸。**`cleanup-before-push.sh` 里的 hotfix 是活逻辑(`commit_format_override="hotfix-unreviewed"`),不动。**

| # | 改动 | 已验证依据 | 状态 |
|---|---|---|---|
| B1 | `dispatch-route-worker.sh:63` 白名单删 `hotfix\|quickfix\|spike\|maintenance` | 同文件 L53-54 注释自承认"no longer route-worker routes",死分支 | ✅ `206b9ec` |
| B2 | `validate-plan-dispatch.sh:15-16`、`validate-pack-manifest.sh:84` 注释更新 | 注释仍把已折叠子模式列为 route-worker phase,误导 | ✅ `206b9ec` |
| B3 | `control-envelope.md.tmpl:23` phase enum 删 `hotfix\|quickfix\|maintenance`(改模板后跑 `build.sh --apply`) | enum 列了不存在的 route 值 | ✅ `206b9ec` |
| B4 | `verify-maturity.sh:247-252` 化石 check 名("Route 4/6/7")更新 | 折叠后的化石命名,且 check 内容随子模式表述变 | ✅ `085e0ae` |
| B5 | `workflow-infrastructure.md:171` 矛盾句修正 | 残留"Bug/Multi-PR 用 `--route hotfix`"——直接错误 | ✅ `206b9ec` |

### 批次 C · 子模式澄清(C1/C2 按决策取消,仅 C3 落地)

| # | 改动 | 已验证依据 / 说明 | 状态 |
|---|---|---|---|
| C1 | ~~`routes-v1.json`:三条 route-worker 合并为单条~~ | **取消**。负责人决策保留 5 条;实测"route 名 = phase 名"在 `routes.sh`/`verdict-route`/`dispatch-route-worker`/envelope phase enum 多处深耦合,合并属高风险动地基,收益(省一条数据记录)远低于风险 | ❌ 取消 |
| C2 | ~~`verdict_routing` 压缩~~ | **取消**。同 C1——verdict 表按 route/phase 索引,表面"同构"多是有意的语义区分(克制设计),压缩会让 verdict-route 逻辑更难读,非真冗余 | ❌ 取消 |
| C3 | 子模式文档层澄清:**hotfix=机器子模式(保留)**、**spike=目录约定**,quickfix/maintenance 取消"子模式"提法(它们 = 普通 Light Lane) | 实测仅 hotfix 有机器锚点(`commit_format_override`),余者无独立逻辑 | ✅ `085e0ae` |

### 批次 D · hook 精简 —— 逐脚本通读后判定:无可安全精简项

> 通读全部 13 个 hook 脚本(实物代码,非二手)后的结论:**hook 数量 ≠ 臃肿**。13 个脚本是 13 件相互独立的机器强制职责,各自正确地 fail-open 或 fail-closed。原"13→8"目标在"低风险 + 不丢稳定性"过滤下不成立——每个合并都拿"少一个文件"去换 fail 哲学混淆 / 机器强制降级,且实测连"8"都凑不齐(最多 −4 → 9)。逐项依据:

| # | 原计划 | 通读后判定 | 依据(实物代码) |
|---|---|---|---|
| D1 | 合并 `gate-codex-review` + `enforce-repair-round-cap` | **不做(中风险,非精简)** | 两者 fail 哲学相反:`gate-codex-review` 对损坏 state **fail-closed**(L59「无法核验=拒绝」),`enforce-repair-round-cap` 全程 **fail-open**。合并只去掉 ~15 行共享前导,各自 ~60 行核心逻辑照留;把两套相反哲学塞进一个控制流正是 fail-open 暗坑高发区 |
| D2 | 合并 `validate-plan-dispatch` + `validate-pack-manifest` + 折叠 ×2 注册 | **不做(中风险)** | `validate-plan-dispatch` 会**写状态**(L172 `state.sh idempotency append`),`validate-pack-manifest` 纯读;合并后顺序敏感。注册收成 glob `Agent(*pack-executor*)` 虽省 2 行,但若 glob 语义与预期不符=**护栏静默失效**(`if:` 由 CC 运行时判定,无法单测),为省 2 行注册冒护栏停摆风险不划算 |
| D3 | 删 `track-review-budget`,计数并入 `state.sh` | **不做(高风险·北极星)** | `review-dispatch.md` L6-11 明文记载该 split-of-concerns 是**有意设计**:计数由 hook 在 `result` 命令触发瞬间自动完成,Coordinator 无须记得调。删 hook 改成显式调 = 把计费(北极星)从机器强制降级为人工记得,违反"不丢稳定性" |
| D4 | `cleanup-before-push` 移到 Closing 显式调 | **不做(中高风险)** | 它已是双模(hook 自动 + `--force` 直调),且内置 hotfix-defer 活逻辑;移成显式-only = 去掉 push 后的自动清理安全网。`:21` 的 `gh pr create` 分支虽是死分支(hook 只在 `git push *` 触发),但无害,不值得动一个工作中的钩子 |
| D5 | `validate-multi-pr-dispatch` 加 `if:` + 检查下沉 | **不做(不可行)** | `if: Agent(role*)` 匹配的是 `subagent_type`,而 multi-pr-merge 靠 envelope.`phase` 区分、**无独立 subagent_type** 可供过滤;现"无 `if:`、内部解析 envelope"的设计是**正确的**,空跑开销=每次派发一次 envelope 解析,可忽略 |
| D6 | `track-execution-state` 保留 | **保留(判断不变)** | claude lane 权威记账,codex lane fallback;codex lane 不动 |

**结果**:hook 维持 13 个,**一行不改**。这与路线层结论一致——表面"重复"多是有意的克制设计,真冗余只在死代码层(已由批次 A/B 清除)。

> 备选(若负责人愿为"少几个文件"接受中风险):D1(去掉一处隐藏的跨 hook 依赖——`enforce-repair-round-cap` 现靠 `gate-codex-review` 先跑挡无效文件)与 D2 在**配齐完整测试覆盖**前提下可做,但两者都只挪代码不减逻辑,且触碰机器护栏。默认不做。

---

## 4. 实际落地记录(7 个 commit)

```
f2efc7d  A1 删 self-verify 命令 + 字段 + 5 引用
e1fab1f  A2 删 agent-id pack-level 死分支
54bf889  A5 repair-regression-evidence 并回 repair-routing
5cf6b84  A3 删 redline-check.sh + 测试
fdde179  A4 review-dispatch 防幻觉四件套收敛单源
206b9ec  B  D10 折叠化石清理(B1/B2/B3/B5)
085e0ae  C3 + B4  Light Lane 子模式表述 + verify 化石命名
```

- **每批独立 commit**,改完跑三验证门,全绿才进下一批——已逐 commit 执行。
- A、B、C3 已落地(净 −171 行,三门全绿)。
- C1/C2(路线/verdict 合并)按负责人"保留 5 条只做低风险项"决策**取消**。
- 批次 D 通读后判定无安全精简项,**未产生改动**。

---

## 5. 验收标准(已达成)

1. ✅ **三验证门全绿**:`build.sh --check`、`run-all-tests.sh`(54 suites,全过)、`verify-maturity.sh`(115 passed / 0 failed)——末次复跑于 C3 commit 后。
2. ✅ **行为走查无回归**:5 条路线保持原状、双 lane execution、写审异家、断点续传均未触碰,改动全在死代码 / 化石注释 / 文档表述层。
3. ✅ **删除项 grep 零残留**(活跃代码,排除 `reviews/` 历史)——self-verify / agent-id pack-level / redline-check / content-only 模板均已确认无残留引用。
4. ✅ **每批一个干净 commit**,commit message 说清删了什么及依据。

---

## 6. 风险登记(回顾)

| 风险 | 批次 | 实际处置 |
|---|---|---|
| 路线合并漏改某消费点 → 路由失效 | C1/C2 | **规避**:决策保留 5 条,未合并 |
| 删 `track-review-budget` 后预算漏记 | D3 | **规避**:通读判定为北极星机器强制,不删 |
| 改 `.tmpl` 模板忘跑 `build.sh --apply` → 锚点漂移 | A4/B3 | 每次改模板后即跑 `--apply` 并 `--check` 确认,无漂移 |
| verify-maturity 偶发失败(早前 subagent 曾报 2 failed) | 全程 | 已确认为临时状态残留;每批以干净复跑为准,稳定 0 failed |

---

## 7. 支撑材料

- [`codex-sandbox-probe.md`](codex-sandbox-probe.md) —— D1 的实测依据。
- 本方案另有 5 份专项审计(双 lane / 路线 / hook / state.sh / 模板)作为讨论中间产物,其**经验证的要点已并入本文清单**;未采信的二手数字(如 worker-loop "90% 相同",实测逐字仅 ~36 行)已剔除。

---

## 附:本方案不含、列为后续可选

- `state.sh` 深度瘦身:`review-history`(awk 插表格)、`merge-brief verify`(python-in-bash 脆弱)回归主线程判断。与 review/multi-pr 流程耦合,风险中等,另议。
- codex lane 访客模型重构(让 Codex 不碰 plugin 基础设施、住户 `git log` 自取权威 SHA)——降耦合优化,非必须,待有需要时单独立项。
- Ruling 2 双文件状态模型合并——动地基,收益存疑(共享锁使"降竞态"论证不成立),单独评估。
