# 实施决策日志（AFK 自主落地）

> 用户 2026-06-04 授权：生成设计文档后直接按文档完整真实落地；过程中决策自己拍板并执行、全程记录、最后汇报；不半路停。本文件记录所有判断，供用户回来复核。

## 运行框架决策

| 编号 | 决策 | 理由 |
| --- | --- | --- |
| R1 | **在 `main` 上直接实现**，frequent scoped commit，AFK 不 push | 本仓库开发历史全在 main；全局规则"不在主仓库直接切分支"指别建分支、非别提交；push 需显式授权 |
| R2 | **直接以架构师身份实现，不路由经 plugin 自身的 orchestrate workflow** | 用重型/有 bug 的旧 workflow 自我改造是循环依赖；其预算硬阻断（正是要修的 bug）会在 AFK 卡死我 |
| R3 | **不 merge/不 build-on/不删改 `control-flow-codification` worktree** | 它 v4.0.2、净增 1744 行+更多硬门（与 D3 反向）、落后 main 14 commit；用户要的是基于 main 的简化新设计；仅参考其可用子方案 |
| R4 | 主 `plugin/` 树无 `AGENTS.override.md`（仅 worktree 有）→ 无同步义务，不擅自新建 | 全局规则是"存在则同步"，主树不存在 |
| R5 | Codex 设计评审：文档定稿后若 codex 就绪则跑一轮对抗评审（用户珍视的模式），有效 finding 自己采纳并记录 | 在大规模落地前用外部模型把设计验一遍，降 AFK 风险 |
| R6 | hook 安全：已确认 `enforce-plan-commit`/`guard-premature-push`/`gate-codex-review` 无活跃 run 时全 no-op，commit 不以 `Pack ` 开头 → AFK 提交不被拦 | 见 hook 源码 |

## 设计文档集一致性复核（workflow 2 + 主线程亲验）

一致性审查 verdict=**needs_fixes，但无决策违反、无不变量违反**（"整体质量高"）。发现的是口径/路径瑕疵，处置如下：

| 发现 | 处置决策 |
| --- | --- |
| `dispatch-route-worker.sh` 被 02/07/08 误归类为 "hook"（实际在 `scripts/`，未注册 hooks.json） | **代码权威**：实现时按 script 处理（已亲验在 `plugin/scripts/`）。文档为草案，不做抛光绕路（#14）；最终报告标注 |
| routes-v1.json 字段命名在 02/03/05/07 不统一（`dispatch_shape` vs `dispatch_granularity`、`gate_exemptions` vs `gate_exempt`） | **我即实施者**，用代码里唯一一套命名消解漂移；以 P1 写的 `routes-v1.json` 实际字段为权威 |
| 05 内部 "5 vs 6 个 SKILL" 自相矛盾 | 实测：signpost phase 序列注入 5 个（workflow 除外）、voice/preamble 注入 6 个。实现时按实测 |
| 08 §4.2 部分 test 文件名未逐一验在 | 每期实际跑 `run-all-tests.sh` 时自然暴露不存在的 test，按实际处理 |

**亲验通过的承重引用**（子代理纪律）：`dispatch-route-worker.sh` 在 scripts/ + :48-54 case 白名单属实；`cleanup-before-push.sh:51` `route=="hotfix"` 死代码属实；`bug-investigation-route.md` 在 `orchestrate-workflow/references/`；`pending_post_push_reviews` 零被 `workflow-closing.md` 读。

## 落地分期（依据 08，按 6 期推进）

`P1 routes 数据 → P2 state/hook 改读 → P3 Light Lane+升级门+红线升级 → P6 删假字段`（关键路径串行）；`P4 预算降仪表`、`P5 skill/agent/hook 重构+漂移根治`（解耦并行）。铁律：加法先于减法、fail-open 回退、每期三件套（子集 test + verify-maturity + build --check）全绿才 commit、每期版本 minor+1 双处同步。

### 落地决策（按实施推进逐条追加）

_（每期遇到的问题、我的判断、依据、影响在此追加。）_

## 待用户复核的关键项

- **worktree 改道**（R3）：本次在 main 按新设计实现，未续 `control-flow-codification` worktree。若你本意是续那个 worktree，回来一句话我改道。
- **Codex 设计评审**（R5）：见实施中决定（若 codex 就绪则对高风险代码做评审）。
- 实施中的其他自主决策见上方"落地决策"。
