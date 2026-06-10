# C 块试跑记录（codex-worker.sh 真实派发验证）

> 关联设计：[2026-06-08-orchestrate-scripting.md](2026-06-08-orchestrate-scripting.md) C1–C7
> 夹具：`/tmp/codex-smoke-run`（临时 git 仓库 + 单 Pack 迷你 plan `docs/plans/001-greet.md`）
> 日期：2026-06-10 · 模型：gpt-5.4 xhigh（standard 档）

## 验证目标

给 Codex 一个真实假任务（Pack 1.1：greet 脚本输出 `GREET-OK-20260610` + TDD 验收），验证 v5.0.0 换轨后 Codex worker 能否像 Claude executor 一样：派发、TDD、commit、状态记账、plan-return 合同、回收合并全链路走通。

## 第一轮（修复前）

核心链路打通，并暴露三个根因缺陷：

| 验证点 | 结果 |
| --- | --- |
| `codex exec` 沙箱派发 + session 记账 | ✅ exit=0，session_id 写入 execution-state |
| TDD skill 真实调用 | ✅ 日志见读取 `~/.agents/.../tdd/SKILL.md` 全文后组织红绿循环 |
| RED 真实发生 | ✅ 实现前跑测试 exit 127（`src/greet.sh: No such file or directory`） |
| GREEN + 复验 | ✅ 测试通过，`cat -vet` 确认单行输出 |
| docs/ 禁区 | ✅ 零触碰 |
| 诚实汇报 | ✅ 末尾主动报告两处环境偏差，未假装环境完整 |
| commit 格式 | ❌ 写出 `Pack 001.1.1:`（模板 `Pack <plan.id>.<pack.id>:` 歧义，记账正则会误捕成 `001.1`） |
| 状态官方通道 | ❌ 绕过 `state.sh pack-progress` 手写 execution-state（usage 帮助缺漏该命令，Codex 误判不存在） |
| 行为规范纯净度 | ❌ 读取了 Codex 宿主侧 3.6.2 旧版插件缓存的 SKILL.md / execution-worker-dispatch.md，引入矛盾指令 |

## 三个根因修复

| 修复 | Commit |
| --- | --- |
| state.sh usage 补全 `pack-progress` / `plan-returns`，`execution-plan` 子命令全列 | `70e99ae` |
| commit 格式统一 `Pack <pack_id>:`（pack_id 形如 `1.1` 已含 plan 序号），模板 + handbook + dispatch 规范三处注明禁拼前缀 | `3d810ba` |
| 派工 prompt 注入 state.sh 绝对路径；handbook 适配层加禁令：禁读 Codex 宿主侧插件缓存 | `e1863f2` |

## 第二轮（修复后，重置夹具全新派发）

| 验证点 | 结果 |
| --- | --- |
| commit 格式 | ✅ `Pack 1.1: greet 脚本与测试 — add greet script and verification test` |
| pack-progress 官方通道 | ✅ 日志见真实调用（prompt 注入的绝对路径），execution-state 经正规通道回填 |
| execution-plan complete | ✅ 首次缺 `--run-id` 被脚本拒绝后，Codex 自行核对接口重跑成功并如实汇报 |
| TDD red→green | ✅ 与第一轮同等完整 |
| plan-return 合同 | ✅ verdict=pass，per_pack["1.1"].commit_sha 为 worktree 真实 SHA |
| NEXT 机械路由 | ✅ 输出「verdict=pass → Dispatch Plan Implementation Review（C5 Claude 直审）」 |
| 旧缓存读取 | ⚠️ 仍有 1 次读取（第一轮 3+ 次），但未跟随旧指令，行为零偏离 |

## 端到端收尾（Coordinator 侧）

C5 Claude 直审通过（实现与测试均为 public-behavior 风格、`set -euo pipefail` 完备）→ `state.sh checkbox toggle`（plan 文档勾选成功）→ `execution-plan finish --status completed` → `recycle-plan.sh` 回收：`--no-ff` merge commit（3 parents 确认）、主树复跑测试通过、worktree + 分支 + marker 清理干净、`isolation_status=merged`。

## 遗留事项

- **Codex 宿主侧曾装有 multi-model-workflow 3.6.2 旧版插件**（读旧缓存的根源），已于 2026-06-10 经用户授权彻底卸载：config.toml 插件段 + 8 个 hooks 注册段、插件缓存目录、7 个 agent toml（`~/.codex/agents/`）全部移除（config.toml 留有 `bak-mmw-uninstall-*` 备份）。卸载后 handbook 中临时加的「禁读旧缓存」禁令同步删除——根源已除，防御文本多余。
- C 试跑门（发布后首份真实 Plan 串行试跑通过才开放并行）维持不变，本记录不替代该门。
