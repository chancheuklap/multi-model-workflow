# 计划撰写下放 Codex

> 设计文档 · 2026-07-10 · 落地分支 `feat/plan-to-codex`

## 目标

把 plan 阶段的**计划文档撰写**从 Claude 移到第二模型(Claude 宿主=Codex,Droid 宿主=执行档 droid),Claude 主线程只留**编排 + 亲验 + 跨 plan 合同**;**②计划审从第二模型翻成 Claude**,保持"写者 ≠ 审者"的跨模型校验。

分工线一句话:**Claude 管到设计文档为止(调查→propose→design→设计文档);计划起全是"另一个模型写、Claude 审"。** 与落地阶段(Codex 写码 / Claude 审)同极性,整条下游统一。

## 目标态

| 阶段 | 撰写 | 审 |
|---|---|---|
| 调查 / propose / 设计 / 设计文档 | Claude | Codex(设计审 a/b) |
| **计划** | **第二模型**(Claude 宿主 Codex `gpt-5.6-terra xhigh` / Droid 宿主 plan-writer droid) | **Claude**(2 个 code-reviewer,轴A 覆盖质量 / 轴B 合规交叉) |
| 落地 | 第二模型 | Claude |

- **单计划也下放**:不再主线程内联写,统一派第二模型(去掉 plan 阶段的 `write` 步)。
- **跨模型极性两宿主一致**:Droid 宿主把 `plan-writer` droid 模型从 Opus 换 `gpt-5.6-terra`、`reviewer-plan` 从 `gpt-5.6-terra` 换 Claude 家族。

## 落地边界

### 1. Codex 侧写计划走 `worktree-plan` skill(新)

- `plugin/skills/worktree-plan/SKILL.md` = 薄总纲:开工读 design + issue → `codebase-design` 探代码 → 拆小 issue(`to-tickets`)→ 逐 Task Pack 写 → 交付前自检 → 回结构化报告。
- **方法论归 skill 自有 references**:`task-pack.md` / `plan-self-check.md` 在 `worktree-plan/references/` 与 `orchestrate/references/plan/` 各放一份实体 copy(Codex 读不到 orchestrate,须有一份落在它能读的 worktree-plan;orchestrate 那份给 build-a 小改路主线程)。`test_shared_refs_sync.sh` 守两份一致。`worker.sh plan-dispatch` **不再注入方法论路径**——Codex 读自己 skill 自取,对齐 build。
- Codex hub 的 `codebase-design`(探代码)/ `to-tickets`(拆 issue)直接用;完整性 / 复用 / 反过度设计以项目根 CLAUDE.md 为准。
- 安装:`~/.agents/skills/worktree-plan → plugin/skills/worktree-plan`(直接软链,同 `worktree-build` / `worktree-review`;已无 `codex-skills/` 中间层)。

### 2. `worker.sh` 加写计划派发

- 新 `plan-dispatch` / `plan-resume`:`codex exec -C <任务 worktree> --sandbox workspace-write`,prompt 给角色 + design + issue + 落点 + worktree-plan skill 指针 + 两份方法论绝对路径;模型档 `gpt-5.6-terra xhigh`(env `CODEX_PLAN_MODEL` / `CODEX_PLAN_EFFORT`)。
- **不开子 worktree、不 commit**:各 plan 写不同文件(`docs/plans/<slug>/00N.md`)、不动 git index,任务 worktree 内并行安全;主线程统一提交。
- **反向边界门 `check_plan_boundary`**:写计划 Codex 的 diff 必须 ⊆ `{docs/plans/**, docs/issues/**}`;碰源码或 `docs/design/` = `PLAN_VIOLATION` 打回。(与 build 的 `check_docs_boundary` 语义相反——build 禁碰 docs/,plan 只准碰这两个 docs/ 子树。)

### 3. plan 阶段 step 改派

- 去掉 `write` 步(单计划内联写的用途消失),plan 阶段只剩 `orchestrate` + `selfcheck` 两步。
- `orchestrate`(plan-flow.md):映射 plan 清单 + 写跨 plan 合同骨架 + fan-out 派 Codex(单=1 / 多=N,主线程直接 `mmw worker plan-dispatch` 后台)+ 亲验返回 + 回填合同。
- `selfcheck`(plan-self-check.md):主线程跨 plan 覆盖 + ownership 就绪门 + handoff(per-pack 就绪门 Codex 交付前已自检,主线程抽验)。

### 4. ②计划审翻转

- `review.sh` 把 `stage=plan` 从与 design 共用的"2 Codex"分支拆出:Claude 宿主派 **2 个 Claude `code-reviewer` sub-agent**(复用 ④final 派 Claude 审者机制);`stage=design` 仍 2 Codex 不动。
- Droid overlay `stage=plan` 审者档跟着翻成 Claude 家族 droid。

### 5. 删旧件

- 删 `plugin/agents/plan-writer.md`(Claude 不再写计划,方法论进 worktree-plan skill)。
- `plugin/droids/plan-writer.md` 保留,模型 Opus→`gpt-5.6-terra`;`reviewer-plan-a/b.md` 模型 `gpt-5.6-terra`→Claude 家族。

## 验证

- `worker.sh` 测试:`plan-dispatch` 派发包成形 + `check_plan_boundary` 拦源码/design、放行 plans/issues。
- `review.sh` 测试:`stage=plan` on Claude 宿主派 Claude 审者;`stage=design` 不变。
- `build.sh --apply` 后 `--check` 无 DRIFT;全量 `test_*.sh` + `test_build.sh` 绿。
- 双侧 `plugin.json` + marketplace 版本号同步升。

## 责任边界

- 主线程(Coordinator):编排、亲验 Codex 返回、跨 plan 合同回填、计划审收口、提交。
- 第二模型(Codex / plan-writer droid):按 design + issue 拆小 issue、写 plan 文档,不碰源码 / `docs/design/`、不 commit。
- 审者(Claude):跨模型审 Codex 写的计划,findings 交主线程亲验后处置。

## 风险

拆小 issue / 定 Pack 边界带设计味判断,第二模型品味存疑 → 由设计文档 + issue 骨架框死 + Claude 跨模型审兜底。
