---
date: 2026-10-07
amends: []
---

# MMW 写进产品仓库的文件按时效分处放：通用约定在仓库根，MMW 会执行的产品答案在 `.mmw/`，一次开发的全部文件在 `efforts/<effort>/`，临时文件不进仓库

一份文件该不该进仓库、放在哪，先看它多久为真。常驻文件（`AGENTS.md`、`TESTING.md`、`CODING_STANDARDS.md`、`CONTEXT.md`、`.agents/skills/`、`.mmw/`）只要产品在就得为真，进仓库的条件是有东西让它保持为真：执行它的脚本、检查它的 lint，或改了产品就同一提交改它的步骤。一次开发的文件（设计包、样例数据、现有产品的状态清单、屏幕契约、原型、地图的研究笔记）只在这次开发里为真，全部放进 `efforts/<effort>/`，开没开着看 tracker 上的 spec 或地图，目录里不另记。历史文件（`docs/adr/`）带编号，写完不改。临时文件（小改动的请求、问卷、无 brief 的研究、handoff、报告）写到 `.scratch/` 或系统临时目录。

## 要修的是什么

- 一次开发的文件分在两棵树里：屏幕契约在 `docs/specs/<effort>/`，设计包、样例数据和原型在 `prototypes/<effort>/`，两边只靠目录名相同连着。`docs/specs/` 里已经没有 spec（spec 在 tracker 上），`prototypes/` 里放着签过字的设计基准。agentflow 里这条连线已经断过：`docs/specs/work-monitor/screen-contract.yaml` 的 `baselines.look` 指向另一次开发的 `prototypes/hedgehog-boss-console/518/claude-design`，同目录还留着旧验收运行时的 `targets/`，v3 没有脚本读它。
- 四处写入没有规定位置：小改动的请求文件、无 brief 的研究笔记（"somewhere sensible"）、地图研究笔记（"where the repository keeps research notes"）、问卷（写在当前目录）。

## Considered Options

- **一次开发的目录放进 `.mmw/efforts/`。** 否决。ripgrep 默认跳过隐藏目录，agent 的搜索大多用它：在本仓库根目录搜 `data-ui`，默认命中 `.mmw/` 下 0 个文件，加 `--hidden` 命中 2 个。设计包和屏幕契约是 worker 按 `data-ui` id 搜的东西，不能藏起来。
- **只把屏幕契约挪进 `prototypes/<effort>/`。** 否决。改动最小，但签过字的基准和约定会继续待在一个叫原型的目录里，名不副实正是这次要修的毛病之一。
- **一张写入位置表，再加一个检查，技能里写到表外路径就报错。** 否决。每一步写到哪已经写在那一步里，表是第二份，检查只是用来对齐两份的；`mmw-v3/skills/mmw-mode/references/skill-set-rules.md` 的 Duplication 一条把这种对齐器算作删掉一份的理由。另外没有记录到哪次运行因为技能写到布局之外而出错，加机制的前提不成立。

## Consequences

- `efforts/<effort>/` 下的固定位置：`claude-design/`、`example-data/`、`README.md`（现有产品的状态清单）、`screen-contract.yaml`、`prototypes/<issue>/<UI|LOGIC|EXP>/`、`research/<ticket number>-<slug>.md`。
- 还在旧布局的仓库，由 `setup-mmw` 的 `scripts/check.py` 报 `effort layout` 缺，`scripts/migrate_layout.py` 在当前分支用 `git mv` 迁移；每个分支在开始工作时单独迁。旧布局除了 `docs/specs/` 和 `prototypes/`，还有更早的 `docs/prototypes/<effort>/` 与 `docs/research/<effort>/`，一并迁。屏幕契约指向的设计包若放在某个原型目录里，搬到契约自己那次开发的 `efforts/<effort>/claude-design/`。旧验收快照 `targets/` 照搬不删：v3 不读它，但产品自己的测试可能还读（agentflow 的 `tests/gateway/test_work_monitor_task_card.py` 就读）。本仓库已迁；agentflow 尚未迁，在它的临时克隆上试跑过一次。
- 已经结束的开发，目录记录的是当时造了什么，不代表产品现在的样子。
- 这次没动的：`TESTING.md`、`CODING_STANDARDS.md`、`CONTEXT.md` 还没有让它们保持为真的机制；`docs/agents/`、打包配置 `*.release-adapter.json` 的位置，triage 的 `.out-of-scope/`（和 tracker 的 wontfix 重复）也照旧。
