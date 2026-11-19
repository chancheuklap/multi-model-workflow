# 644-checker-command-fix-scope

## 改了什么

`code-checkers` 在 2026-09-28（`9fd2b41b`）规定了 consuming repository 的检查命令（按技能第 6 步生成的那一条，例如 `scripts/dev/lint.sh`）必须做到的三件事：

- 默认只查本分支相对基线改动的内容，另用一个旗标查整棵树；**修复旗标只改写默认范围选中的文件**。不带全树旗标的 `--fix` 不得对整棵树跑 `ruff format`、`ruff check --fix` 或 `oxlint --fix`。
- 基线分支优先取 `MMW_BASE_REF`：流水线给 ticket 设的是它将合入的分支，从夜基线切出的 ticket 若拿 `origin/dev` 或 `origin/main` 比较，会把整条夜基线都当成本分支改动。
- 有 `.mmw/target.json` 的仓库，`checks` 应当运行这条检查命令。

同一次还给 pyrefly 加了 `disable-project-excludes-heuristics = true` 与 `use-ignore-files = false`（`references/python.md`），否则 `.worktrees/` 下的 ticket worktree 一个文件都扫不到。

## 哪些产物失效

这一改动让 consuming repository 里按旧版技能生成的文件失效，属于 `## 什么改动必须写一份` 的第四类（技能让它生成的文件）；若 `checks` 还没运行检查命令，`.mmw/target.json` 也属第三类。

- `agentflow-hq/agentflow`：
  - `scripts/dev/lint.sh`：2026-09-02 生成，`--fix` 对整棵树修复，基线写死 `origin/dev`。2026-09-30 agentflow #1037 跑一次改了 532 个范围外文件（agentflow #1077）。已在 agentflow `89e6fa139`（分支 `night-remote-diagnostics-1018`）迁好。
  - `pyproject.toml` 的 pyrefly 两项已在位。
  - `.mmw/target.json` 的 `checks` 仍只跑 `uv run pytest tests/guards tests/contracts -q`，没有运行检查命令。
- `agentflow-hq/xiaohuangya`：
  - `scripts/dev/lint.sh`：`--fix` 对整棵树跑 `ruff check --fix` 与 `oxlint --type-aware --fix`（`ruff format` 已只排新增文件）；基线 `LINT_BASE`，默认 `origin/main`，不读 `MMW_BASE_REF`。
  - 仓库没有 `.mmw/target.json`，第三条暂不适用。

## 怎么迁

1. 检查命令的修复旗标不带全树旗标时，只把改动文件交给各修复器：`ruff check --fix <改动的 .py>`、`ruff format <新增的 .py>`、`oxlint --type-aware --fix <改动的 TS/JS>`；全树修复只在显式加全树旗标时进行。验证办法：在 ticket worktree 里新增一个格式很乱的文件、改动一个带可自动修复问题的旧文件，再挑一个未改动但有同类可修问题的旧文件；跑修复后 `git status` 只应出现前两个文件（以及检查命令自己），第三个文件内容不变。
2. 基线：`BASE="${MMW_BASE_REF:-${LINT_BASE:-<仓库默认分支>}}"`，并在输出里打印实际基线。
3. 有 `.mmw/target.json` 的仓库，把检查命令加进 `checks`。加之前确认它在 ticket worktree 里能跑通：两个 Electron 壳的 `node_modules` 是否已装、产品 extras 是否已装。
