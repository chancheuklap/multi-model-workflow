# Issue 001 — 基础设施层重构（Template & Reference & Routes）

## What to build

把 plugin 的"广义基础设施层"做一次系统级清理与去重，覆盖：

- **Canonical reference 抽取**（决策 1）：`review-dispatch` / `repair-routing` / `disposition-table` 三个高频 inject 锚点抽取到 `plugin/skills/_shared/` plugin-rooted 绝对路径，禁止相对路径形式。所有原 inject 锚点位置改为 `Read` 引用。
- **死模板 + 孤儿文件批量删除**（决策 2）：删除 `forbidden-shortcuts.md.tmpl` + 2 active anchor inline / `state-write.md.tmpl` + inline / `trust-boundary.md.tmpl` + inline；删除 3 个 multi-pr handbook（共 455 行）；折回 `learnings-confidence-audit.md` / `learnings-trust-gate.md`；删除 `path-a-re-review.md`；删除 `route-extensions/` 副本目录。同步 `verify-maturity.sh` §6.11 共 6 行（3 个 `-f` + 3 个 `grep -q 'Self-Read Protocol'`）。
- **脚本合并**（决策 8）：`record-/validate-review-dispatch.sh` 对合并为 `dispatch-review.sh` 含 `validate` / `record` 子命令；`record-/validate-route-worker-dispatch.sh` 对合并为 `dispatch-route-worker.sh` 同模式。shim 期保留旧 4 个脚本作为转发，渐进迁移所有 producer 引用。
- **Hook 行为变化**（决策 9）：删除 `guard-plan-doc-patch.sh`；`validate-plan-dispatch.sh` Step 6 Manifest 检查从 exit 2 降为 WARN；删除 Step 8 Path A；`validate-multi-pr-dispatch.sh` (b)(d) **保持 exit 2**（不降级）；删除 `gate-codex-review.sh` 的 `--resume` / `targeted-re-review` / `path-a-re-review` 三个分支整段。
- **Routes 4-7 折叠**（决策 10）：runtime route enum 4 值（formal / bug-investigation / multi-pr-merge / direct-repair），Hotfix / Quick Fix / Spike / Maintenance 改为 Route 1 formal + `phase_skip[]` flags + `commit_format_override` + `budget_status: "unlimited"`。
- **外部 Skill 集成对齐 + agent frontmatter 瘦身**（决策 11）：移除 stale `skills:` frontmatter 字段；保留必要的外部 skill inline 引用。
- **Reference 跳跃精简 + 路标补齐**（决策 12）：所有 `plugin/skills/*/references/*.md`（除 `_shared/`）顶部 5 行内必须含路标 blockquote。

完成本 issue 后：基础设施层（模板 / 脚本 / hook / route enum / agent frontmatter / 路标）达到 token economy 标准；下游 Issue 002 / 003 才能在干净的合同基线上展开。

## Small issues

<!-- PENDING: plan-writer 将在 plan-writing 阶段补全小 issue 拆分 -->

## Blocked by

- None — 可立即启动
