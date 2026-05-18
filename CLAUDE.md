# CLAUDE.md

多模型开发工作流系统。Claude Code plugin（`plugin/`、`plugin-v2/`）+ Codex skills/agents（`.agents/skills/`、`codex/agents/`）。流水线：Discovery → Design Review → Plan → Plan Review → Task Pack Execution → Final Review → Business Report。

Codex runtime 是设计权威。`plugin/` 是兼容层。`plugin-v2/` 是开发中的下一代 Claude plugin。

## 目录结构

- `.agents/skills/orchestrate-*` — Codex skill 源码（discovery / plan-writing / workflow）
- `codex/agents/*.toml` — Codex agent 定义（7 角色）；`sync-agents.sh` 同步到 `~/.codex/agents/`
- `codex/hooks/`、`codex/skills/` — Codex hooks 和 skill 安装脚本
- `plugin/` — Claude Code plugin v1（v0.7.0，兼容层）
- `plugin-v2/` — Claude Code plugin v2（v0.8.0，开发中）；`agents/` + `skills/` + `hooks/`
- `.claude-plugin/marketplace.json` — Marketplace 上架清单

**Source → Runtime**：编辑 `.agents/skills/` 和 `codex/agents/*.toml`，然后 sync 到 `~/.codex/agents/` 和 `~/.agents/skills/`。先改源码再 sync。

## 核心概念

- **Sub-agent 隔离**：Sub-agent 不读 SKILL.md / references。Dispatch prompt 必须自足（phase / source docs / anchors / verification / return contract）。
- **Review budget**：Formal Orchestrate 预算 `2N + 12`（N = pack 数）。80% 触发 Direction Check。
- **合同边界**：跨边界变更（API / Pydantic / DB / JSON payload / task-sync / catalog / adapter / UI form）必须在 dispatch prompt 中写 contract anchors。

## Plugin v2 架构规则

### 渐进式加载

SKILL.md 是骨架——步骤编号 + 一句话 + reference 路径。Coordinator 到达该步骤时才 Read reference。**不在入口一次性加载。**

拆分判定：
- **不同时刻消费** → 拆（Worker dispatch Step 5 vs Reviewer dispatch Step 8 → 两个文件）
- **条件触发** → 拆（Release Gate 只在触碰发布风险面时加载）
- **始终一起用** → 不拆（Disposition + Backflow 路由）

拆分后 `rg -n "旧文件名" plugin-v2/` 扫 stale reference。

### Reference 分类

| 类型 | 导航标记 |
|------|----------|
| **Flow**（步骤序列中有固定位置） | header `> **流程位置**` + 非线性跳转时 footer `> **下一步**` |
| **Lookup**（按需查阅，无位置） | 无 |

### Dispatch-Agent 对齐

每个 dispatch 点对齐 agent 定义三维度：
1. **模式触发**：信号词命中 agent 模式检测表
2. **输入期望**：agent 要求的必填字段全部在 prompt 中提供
3. **返回合同**：Return Contract 结构匹配 agent 默认格式

### Agent 定义 = 行为权威

行为规则（TDD、自检、scope 边界、三次失败协议）写 agent 定义——单一来源，所有 dispatch 场景加载。Dispatch template 只写场景特有信息，不重复 agent 定义的通用规则。

### Reviewer 独立验证

所有 Reviewer Calibration 必须包含"不信任上游报告，独立验证"。按层级定制信任边界：Pack Review 不信 worker 自述；Final Review 不信 pack summary；Multi-PR Review 不信各 PR 的 Final Review 结论。

## 编辑规则

- Runtime 文件（SKILL.md / references / agent definitions / hooks）只放可执行指令，不放背景解释、迁移历史、方法名列表。
- Agent 定义必须包含自足的 return contract，不引用 agent 无法访问的 SKILL.md 或 references。
- 改 `plugin-v2/` 时同步维护该目录下的 `agents.overrides.md`。
- 改 Codex 源码后 sync 到 runtime 并用 `diff` 验证。

## Sync 命令

```bash
bash codex/skills/install-orchestrate-workflow.sh --user --apply
bash codex/agents/sync-agents.sh --apply
bash codex/hooks/install-hooks.sh --apply
# 验证（diff 应为空）
diff -qr .agents/skills/orchestrate-workflow ~/.agents/skills/orchestrate-workflow
diff -qr .agents/skills/orchestrate-discovery ~/.agents/skills/orchestrate-discovery
diff -qr .agents/skills/orchestrate-plan-writing ~/.agents/skills/orchestrate-plan-writing
```

## 验证命令

```bash
# Codex runtime 中不应出现 Claude plugin 概念
rg -n "workflow-auditor|pack-executor|root-cause-analyst|codex-rescue|SendMessage|Agent tool" .agents/skills codex/agents
# 不应有 stale 交叉引用
rg -n "SKILL.md universal|Fill the.*SKILL.md" .agents/skills codex/agents
```

## 安装

```bash
claude plugin install multi-model-workflow@multi-model-workflow
# 或本地加载：
claude --plugin-dir /path/to/multi-model-workflow/plugin
```

需要 Codex plugin 支持跨模型 review dispatch（`codex:codex-rescue`）。
