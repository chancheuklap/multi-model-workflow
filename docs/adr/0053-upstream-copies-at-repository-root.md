---
date: 2026-10-16
amends: [0032]
---

# 上游的只读副本放在仓库根目录的 `upstream/<name>/`，每份一个 `git subtree --squash` 目录，与上游逐字节相同

主人 2026-10-16 要求：「你现在就把所有 upstream 搬到根目录并拉取最新版本，不要放到票里」。0032 把上游快照放在 `mmw-v3/upstream-*/`。v4 成为唯一在用的一代以后，v4 的技能集规则、`diagram-design` 的 `repo-root` 链接和 `check_wiring.py` 仍要进 `mmw-v3/` 找上游，`mmw-v3/` 因此多了一个与 `--back` 无关的用途。现在有五份副本：`upstream/mattpocock/`（`mattpocock/skills`）、`upstream/pstack/` 与 `upstream/cursor-team-kit/`（`cursor/plugins` 的两个目录，各取 `git subtree split`）、`upstream/diagram-design/`（`cathrynlavery/diagram-design`）、`upstream/e2e/`（`tester-army/e2e` 的 `skills/`，取 split）。主机不从这些副本安装任何东西。只有 v4 与 v3 的 `diagram-design` 经 `repo-root` 链接调用 `upstream/diagram-design/scripts/` 下的脚本。

## 要修的是什么

`mmw-v3/upstream-diagram-design/` 里有 MMW 自己的改动：`scripts/verify-geometry.py` 的 J56、J57 与 `scripts/test-verify-geometry.py` 的 J58。所以这份快照不等于上游，拉新版时会和 MMW 的改动冲突。改后的做法如下。副本保持与上游相同。改过的 `verify-geometry.py` 拷进 v4 与 v3 两个 `diagram-design` 技能的 `scripts/`，`SKILL.md` 的 §6 第 6 条与检查清单改为调用技能自己的这一份。改过的测试放进 `mmw-v4/tests/diagram-design/` 与 `mmw-v3/tests/diagram-design/`，由各自套件的 `run.sh` 运行。

## Considered Options

- **留在 `mmw-v3/` 下。** 否决。v3 只剩 `install.sh --back` 一个用途，v4 的规则不该指进上一代的目录。
- **开票，由夜里的 worker 来搬。** 否决。主人明确不要开票。搬家是否正确由机械比对证明：每份副本的树哈希与原快照或上游的 split 相同。
- **整份 `tester-army/e2e` 仓库进来。** 否决。MMW 只读它的技能文字，CLI 源码用不上，进来只会让副本变大。
- **`diagram-design` 的改动留在副本里，拉新版时手工合并。** 否决。这样副本永远不等于上游，每次拉取都要解冲突，而且改过的测试在副本里没有任何套件运行。

## Consequences

- 拉新版只改 `upstream/` 下的一个目录。技能里的拷贝不会跟着改变，行为上的改动要照 `mmw-v4/skills/writing-for-agents/SKILL-SET-RULES.md` 的 `### Upstream skills` 搬过去。
- `diagram-design` 经 `repo-root` 调用的脚本随上游新版变化，`verify-geometry.py` 除外。
- 0032 中「上游以只读快照留在 `mmw-v3/upstream-mattpocock/`、`mmw-v3/upstream-pstack/`、`mmw-v3/upstream-diagram-design/`」不再成立。`imports.tsv` 仍从历史中的 squash 提交读源文件，不受这次搬家影响。
- `create-verification-skill` 禁止在产品仓库或主机上安装 e2e 技能。`upstream/e2e/` 是只读副本，不在这条禁令内。
