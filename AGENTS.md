# AGENTS.md — multi-model-workflow 维护协议

本仓库是 Codex Orchestrate Workflow 的源码和同步仓库。当前 Codex 形态以 `plugin-v2/` 的六 phase 架构为蓝本，但运行权威是根目录的 `.agents/skills/`、`codex/agents/` 和 `codex/hooks/`。

旧 Codex V1 已归档到 `archive/2026-05-20-codex-v1/`。不要用归档内容推导当前行为。

## 1. Source / Runtime

| 层级 | 路径 | 作用 |
| --- | --- | --- |
| Codex skill source | `.agents/skills/orchestrate-*` | 六个 Orchestrate phase skill 的源码真相 |
| Codex agent source | `codex/agents/*.toml` | 自定义 `agent_type` 指令模板 |
| Codex hook source | `codex/hooks/*.sh`、`codex/hooks/hooks.json` | user-level hook 的源码真相 |
| Codex skill runtime | `/Users/cheuklapchan/.agents/skills/orchestrate-*` | Codex 实际可加载的 user-level skills |
| Codex agent runtime | `/Users/cheuklapchan/.codex/agents/*.toml` | Codex 实际可调用的 custom sub-agent 配置 |
| Codex hook runtime | `/Users/cheuklapchan/.codex/hooks/multi-model-workflow/`、`/Users/cheuklapchan/.codex/hooks.json` | Codex 实际执行的 user-level hooks |
| Codex agent config | `/Users/cheuklapchan/.codex/config.toml` `[agents.*]` | 把 agent template 注册成可调用 `agent_type` |
| Claude Plugin V2 source | `plugin-v2/` | Claude Code Plugin V2 源；Codex 改造的上游蓝本，不是 runtime |
| Historical source | `plugin/`、`archive/2026-05-20-codex-v1/` | 兼容 / 归档；不作为当前 Codex 设计依据 |

改 Codex 运行行为时，先改 source，再同步 runtime，并验证 diff。不要只改 user-level runtime。

## 2. Current Runtime Shape

六个 phase skill：

| Skill | 职责 |
| --- | --- |
| `orchestrate-workflow` | Entry Gate、Infrastructure、Formal/Bug/Multi-PR route、Closing |
| `orchestrate-discovery` | 模糊输入 → domain alignment → design document → Design Review → issue 过渡 |
| `orchestrate-plan-writing` | reviewed design + issue hierarchy → implementation plan → Plan Review |
| `orchestrate-execution` | reviewed plan → Task Pack worker dispatch → Pack Review → repair loop → early release gate |
| `orchestrate-final-review` | all packs passed → final intent review → lingering tail sweep → final release gate → business report |
| `orchestrate-multi-pr-merge` | 多 PR 交互冲突发现、根因调查、修复、集成审查、顺序合并 |

九个 managed `agent_type`：

| agent_type | 职责 |
| --- | --- |
| `plan_writer` | 从 reviewed design + issue hierarchy 写 implementation plan |
| `coding_worker` | 普通 Task Pack / 明确 repair finding |
| `complex_coding_worker` | 高风险 Task Pack / migration / billing / permission / runtime / shared contract |
| `code_reviewer` | baseline design / plan / pack / final / integration review |
| `release_reviewer` | release-risk supplement，不替代 baseline review |
| `code_explorer` | 窄范围只读代码调查 |
| `complex_code_explorer` | 多模块只读调查 / 架构摩擦 / 未知根因定位 |
| `root_cause_analyst` | bug investigation / repair truncation / Multi-PR systemic conflict |
| `docs_worker` | 低风险文档整理 |

## 3. Runtime Files

Runtime 文件只写会改变 agent 下一步行为的指令：

- trigger / entry router；
- phase 顺序；
- 必读 reference；
- agent routing；
- dispatch contract；
- review / worker contract；
- stop condition；
- finding severity；
- verification gate；
- sync command。

不要写迁移背景、概念复盘、来源说明、README 式介绍、或为了证明理解而写的大段解释。必要历史只放归档 README 或普通说明文档，不放 runtime 指令。

## 4. 运行主体边界

| 文件 | 读者 | 负责什么 | 禁止什么 |
| --- | --- | --- | --- |
| `.agents/skills/orchestrate-workflow/SKILL.md` | 主线程 coordinator | 入口路由、phase 跳转、hard gates、closing | 假设 custom agent 自动知道本文件 |
| `.agents/skills/orchestrate-*/references/*.md` | 主线程 phase owner | phase-specific 检查项、dispatch payload、disposition、repair routing | 写成 sub-agent 自动读取的合同源 |
| `codex/agents/*.toml` | custom agent 自己 | 角色纪律、默认方法、可执行/只读边界、return contract | 引用模糊的 SKILL.md 或重新定义 Orchestrate phase |
| parent dispatch prompt | 主线程发给 custom agent | 本次 phase、source docs、anchors、risk、verification、return contract | 只发“按 Orchestrate 做”这类隐式要求 |

Sub-agent dispatch 必须自足。需要 reference 时，parent 要提供明确路径或粘贴关键合同。

## 5. 系统完整性标准

合格标准：

- Entry Gate 能识别 Formal Orchestrate、Bug Investigation、Multi-PR Merge 和 answer-only。
- Discovery 能把新功能、issue、backlog、PRD、系统性 bug、wrong state、UI/UX 反馈和产品讨论转成可 review design。
- Design Review、Plan Review、Pack Review、Final Review 不跳过。
- Plan Writing 消费 reviewed design 和 confirmed issue hierarchy；缺 issue 时回到 `to-issues`。
- Execution 逐 Task Pack 派正确 worker，review 后 disposition，再 repair。
- Final Review 验证所有 pack 合起来是否满足 design intent，并清扫 worker open items、TODO/FIXME、out-of-scope disposition。
- Release-risk review 由 `release_reviewer` 追加，不能覆盖 baseline `code_reviewer`。
- Review 通过 Codex `codex-companion.mjs` 四步协议派发（按 `orchestrate-workflow/references/external-review-lanes.md`）。
- 未知根因先建立 feedback loop 和可证伪 hypotheses，再修复。
- Worker 按 public behavior vertical TDD，不做 horizontal slicing。
- API、Pydantic、DB、JSON、sync、billing、permission、runtime、UI action 和 helper placement 走正式 contract boundary。
- 最终汇报面向项目负责人说明产品能力、验证证据、残余风险和需要业务决策的事项。

不合格信号：

- 只说安装成功或文件复制成功。
- review 只审代码，不审 design、plan 和 final intent。
- release review 替代 baseline review。
- Task Pack 按文件类型横切。
- custom agent TOML 引用它看不到的 Orchestrate reference。
- runtime 文件出现 `codex-rescue`、`SendMessage`、`Agent tool`、`CLAUDE_PLUGIN_ROOT`、`.claude/multi-model-workflow`。
- 默认自动调用 `claude -p` 并声称它消耗 Claude 订阅额度。

## 6. 修改流程

改 Codex 行为时：

1. 先读当前 `.agents/skills/orchestrate-*` 和相关 references。
2. 读 `codex/agents/*.toml`、`codex/hooks/*`、安装脚本。
3. 只在发现明确缺口时改 source。
4. 改涉及目录时同步维护对应 `agents.overrides.md`。
5. 同步 user-level runtime。
6. 用 diff 验证 source/runtime parity。

不要先检查“是否安装”来代替行为审计。安装只证明文件复制成功，不证明系统设计成立。

## 7. 同步命令

```bash
bash codex/skills/install-orchestrate-runtime.sh --user --apply
bash codex/agents/sync-agents.sh --apply --update-config
bash codex/hooks/install-hooks.sh --apply

for s in orchestrate-workflow orchestrate-discovery orchestrate-plan-writing orchestrate-execution orchestrate-final-review orchestrate-multi-pr-merge; do
  diff -qr ".agents/skills/$s" "/Users/cheuklapchan/.agents/skills/$s"
done

for f in codex/agents/*.toml; do
  diff -q "$f" "/Users/cheuklapchan/.codex/agents/$(basename "$f")"
done

diff -q codex/hooks/session-start.sh /Users/cheuklapchan/.codex/hooks/multi-model-workflow/session-start.sh
diff -q codex/hooks/guard-premature-push.sh /Users/cheuklapchan/.codex/hooks/multi-model-workflow/guard-premature-push.sh
diff -q codex/hooks/track-review-budget.sh /Users/cheuklapchan/.codex/hooks/multi-model-workflow/track-review-budget.sh
diff -q codex/hooks/cleanup-run-state.sh /Users/cheuklapchan/.codex/hooks/multi-model-workflow/cleanup-run-state.sh
```

## 8. 子代理使用

本仓库的 prompt / instruction 维护不要为了委派而委派。可以并行审不同 runtime 面，但主线程必须整合和验收。

可以委派的情况：

- 审单个 phase skill；
- 审 `codex/agents/*.toml`；
- 对照 source/runtime 找漂移；
- 对照 Plugin V2 找未迁移能力。

不要委派的情况：

- 只需要删几段解释性文字；
- 用户正在纠正方向；
- 下一步是关键路径；
- 问题本质是 source/runtime 权威或运行主体边界。

## 9. 用户沟通

用户要的是系统真的可用。沟通时先讲结论，再讲证据；少讲方法论，多讲检查了什么、改了什么、同步到了哪里。用户要求执行时直接执行，不把显然下一步推回用户。
