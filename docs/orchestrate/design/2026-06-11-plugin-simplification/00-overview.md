# Plugin 精简总方案 · 总览

> 状态:**待审**(2026-06-11)。本文件是给项目负责人审的完整方案;所有"删/改"依据均已由 Coordinator 亲自 grep/Read/实跑验证,非二手结论。
>
> 一句话:在**不丢功能、性能、稳定性、适配性**的前提下,清掉一批空转的死代码、把重复的两份收敛成一份、把数据层全等的路线合并、把记账型与重复触发的 hook 精简——让这套多模型工作流更轻、更不容易出错。

---

## 1. 范围与守住的底线

**本方案做三件事**:① 无损死代码 / 重复清理;② 路线 5→3 + verdict 压缩 + 子模式澄清;③ hook 13→8。

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
| A3 | 删 `redline-check.sh` + 测试,保留 SKILL 红线类别表 | 不被任何 hook 调用,纯 advisory,关键词与 SKILL 表重复两份;LLM 本就能判红线 | 待落地 |
| A4 | `review-dispatch.content-only` 模板 → 收敛到 `_shared/review-prompt-quartet.md` 运行时注入 | 该锚点只注入 1 处(`codex-review/SKILL.md`),与 quartet 是同一内容的第二份拷贝(措辞已不同步) | 待落地 |
| A5 | `_shared/repair-regression-evidence.md` 合并回 `repair-routing.md` | 全仓库只被 `repair-routing.md:28` 一处引用——放 `_shared/` 是过度抽象 | 待落地 |

### 批次 B · D10 化石清理(纯死注释 / 死分支,hotfix 活逻辑保留)

> 背景:此前一次 D10 决策把 hotfix/quickfix/spike/maintenance 从独立 route 折叠掉,但落地留了残骸。**`cleanup-before-push.sh` 里的 hotfix 是活逻辑(`commit_format_override="hotfix-unreviewed"`),不动。**

| # | 改动 | 已验证依据 |
|---|---|---|
| B1 | `dispatch-route-worker.sh:63` 白名单删 `hotfix\|quickfix\|spike\|maintenance` | 同文件 L53-54 注释自承认"no longer route-worker routes",死分支 |
| B2 | `validate-plan-dispatch.sh:15-16`、`validate-pack-manifest.sh:84` 注释更新 | 注释仍把已折叠子模式列为 route-worker phase,误导 |
| B3 | `control-envelope.md.tmpl:23` phase enum 删 `hotfix\|quickfix\|maintenance`(改模板后跑 `build.sh --apply`) | enum 列了不存在的 route 值 |
| B4 | `verify-maturity.sh:247-252` 化石 check 名("Route 4/6/7")更新 | 折叠后的化石命名,且 check 内容随子模式表述变 |
| B5 | `workflow-infrastructure.md:171` 矛盾句修正 | 残留"Bug/Multi-PR 用 `--route hotfix`"——直接错误 |

### 批次 C · 路线 5→3 + verdict 压缩 + 子模式澄清

| # | 改动 | 已验证依据 / 说明 |
|---|---|---|
| C1 | `routes-v1.json`:三条 route-worker 合并为单条 `route-worker` | 六运行期字段除名全等(实测);三场景由 SKILL 选 agent |
| C2 | `verdict_routing` 压缩:`DISCOVERY_READY`/`DISCOVERY_NOT_NEEDED` 合并;`BLOCKED`/`NEEDS_DISCOVERY`/`NEEDS_PLAN_REVISION` 抽成跨表共享;`direct-repair` 表小写 verdict 规整为大写 | 同构与跨表重复已逐条核对;28 条可压到 ~18 |
| C3 | 子模式文档层澄清:**hotfix=机器子模式(保留)**、**spike=目录约定**,quickfix/maintenance 取消"子模式"提法(它们 = 普通 Light Lane) | 实测仅 hotfix 有机器锚点,余者无独立逻辑 |
| C4 | 同步消费点:`routes.sh`、`dispatch-route-worker.sh`、`validate-*.sh`、相关 SKILL、`state.sh` 的 route enum、`workflow-state-v1.json` / `routes-v1.schema.json` 的 route enum、`verify-maturity` | 路线是流程真相源,改它要扫全部读取方 |

> **顺带理顺的断链**:实测 `bug-investigation` / `multi-pr-merge` **无 `init --route` 显式激活**(multi-pr 走 `merge-brief init`)。合并为单条 `route-worker` + 统一初始化入口时一并修正。

### 批次 D · hook 13→8

| # | 改动 | 已验证依据 / 说明 |
|---|---|---|
| D1 | `gate-codex-review` + `enforce-repair-round-cap` → 合并为 `gate-codex-task` | 两者共享**完全相同**触发条件 `Bash(*codex*task*)`,前 ~22 行重复解析同一 envelope |
| D2 | `validate-plan-dispatch` + `validate-pack-manifest` → 合并;两次注册(pack-executor* / complex-pack-executor*)收成一条 matcher | 共 matcher、各解析一遍 envelope;A==B 对账可上移到 plan-writing 构建门 |
| D3 | 删 `track-review-budget`,review 计数全部并入 `state.sh budget increment-review` | hook 自述 "observational — dispatch validation already enforces upstream";且双 lane 下记账本就一半手动一半自动,统一单一通道 |
| D4 | `cleanup-before-push` 从 PostToolUse 移到 Closing 显式调用(它已支持 `--force` 直调)+ 修 `:21` 残留裸 grep | 它是清理动作非护栏;`:21` 是 guard 已修的同款 bug class 残留 |
| D5 | `validate-multi-pr-dispatch` 随 C1 处理:当前**无 `if:` 条件**、每次任意 Agent 派发都空跑;4 项 python 检查下沉到 `state.sh merge-brief`,缩成轻量 jq | 与路线合并耦合,一起做 |
| D6 | `track-execution-state` **保留** | claude lane(共享主树)它是权威记账,codex lane 是 fallback;codex lane 不动,故保留 |

**结果**:13 → 8(`session-start`、`guard-premature-push`、`guard-doc-edit`、`agent-return-handler`、`enforce-plan-commit`、`gate-codex-task`、`validate-dispatch`、`track-execution-state`)。

---

## 4. 落地顺序与依赖

```
批次 A(死代码/重复) ── 独立、零风险 ──┐
批次 B(D10 化石)   ── 独立、零风险 ──┤── 先做
                                      │
批次 C(路线 5→3) ←──耦合──→ D5(multi-pr hook)  ── 一起做(风险最高)
                                      │
批次 D1/D2/D3/D4(hook 精简) ── C 之后或并行 ── 后做
```

- **每批独立 commit**,改完跑三验证门,全绿才进下一批。
- A、B 可立即做(已验证零风险)。
- **C 是风险最高的一批**(动 `routes-v1.json` 这个流程真相源 + 全部消费点),单独成 commit、可独立回滚;D5 跟着 C。
- D1/D2/D4 相对独立;**D3 要特别小心**——删 `track-review-budget` 前必须确认所有 review 计数点都改到了 `state.sh`,否则预算漏记。

---

## 5. 验收标准

1. **三验证门全绿**:`build.sh --check`、`run-all-tests.sh`(55 suites)、`verify-maturity.sh`。
2. **行为走查无回归**:5 条路线(合并后 3 条数据记录,但 bug/direct-repair/multi-pr 三场景仍可走通)、双 lane execution、写审异家、断点续传,逐项确认与改动前等价。
3. **删除项 grep 零残留**(活跃代码,排除 `reviews/` 历史)。
4. **每批一个干净 commit**,commit message 说清删/合并了什么及依据。

---

## 6. 风险登记

| 风险 | 批次 | 缓解 |
|---|---|---|
| 路线合并漏改某个消费点 → 路由失效 | C | 改前 grep 全部 `routes`/`dispatch_shape`/`review_required` 读取方;独立 commit 可回滚;三验证门把关 |
| 删 `track-review-budget` 后预算漏记 | D3 | 先把所有派 review 处补上 `state.sh budget increment-review`,再删 hook;用 budget 测试覆盖 |
| 改 `.tmpl` 模板忘跑 `build.sh --apply` → 锚点漂移 | A4/B3 | `build --check` 在 CI/验收门会红,强制同步 |
| verify-maturity 偶发失败(subagent 曾报 2 failed,Coordinator 复跑 0 failed) | 全程 | 已确认为非稳定的临时状态残留,以干净复跑为准;落地中每批复跑确认 |

---

## 7. 支撑材料

- [`codex-sandbox-probe.md`](codex-sandbox-probe.md) —— D1 的实测依据。
- 本方案另有 5 份专项审计(双 lane / 路线 / hook / state.sh / 模板)作为讨论中间产物,其**经验证的要点已并入本文清单**;未采信的二手数字(如 worker-loop "90% 相同",实测逐字仅 ~36 行)已剔除。

---

## 附:本方案不含、列为后续可选

- `state.sh` 深度瘦身:`review-history`(awk 插表格)、`merge-brief verify`(python-in-bash 脆弱)回归主线程判断。与 review/multi-pr 流程耦合,风险中等,另议。
- codex lane 访客模型重构(让 Codex 不碰 plugin 基础设施、住户 `git log` 自取权威 SHA)——降耦合优化,非必须,待有需要时单独立项。
- Ruling 2 双文件状态模型合并——动地基,收益存疑(共享锁使"降竞态"论证不成立),单独评估。
