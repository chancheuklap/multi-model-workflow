---
name: mmw-closing
description: 完成有 spec 任务的过程材料清理和交回。用于用户要求收尾，或终审提交已登记且无需出包，或安装包实测通过。
---

开始前，遵守目标仓库 `AGENTS.md` 的领域上下文规则。

代码已经落地，终审已经通过。spec 与 plan 长期留在仓库。本技能只清理当前任务的过程材料，并判定这条分支就绪待集成。

## 前置条件

四项必须满足。缺一项就停下，并点名缺失项。

| 检查 | 怎么查 |
| --- | --- |
| 当前 checkout 已绑定任务 | 运行 `mmw task state`。输出必须以 `bound` 开头。第四个字段是工作名 |
| spec 已提交 | 运行 `mmw artifact path spec --name <工作名>`。对输出路径运行 `git cat-file -e "HEAD:<输出路径>"` |
| 每份 plan 已提交 | 从每张 tracer bullet ticket 取得计划文件名。逐份运行 `mmw artifact path plan --name <工作名> --sub <计划文件>`，再检查输出路径已提交 |
| 终审已经完成 | 运行 `mmw artifact path review --name <工作名> --sub final.md`。审查记录必须存在；采信项必须有 `修复提交` |

工作区还必须干净。运行 `git status --porcelain`。输出不是空时停下，并报告改动路径。

没有 spec 的任务不走本技能。

## 1. 清理当前任务的过程材料

先从 `mmw task state` 的第四个字段取得工作名。不要从任务分支名或 worktree 目录名推断工作名。

用下面两条命令取得当前工作名的过程材料父目录：

```bash
scratch_root="$(dirname "$(mmw artifact path scratch --name <工作名> --sub evidence)")"
review_root="$(dirname "$(mmw artifact path review --name <工作名> --sub final.md)")"
```

列出这两个父目录下的现有条目。此时只列出，不删除。

对 scratch 根下的每个候选目标重新解析路径：

- 无范围段的目标运行 `mmw artifact path scratch --name <工作名> --sub <类别内细分>`。
- 位于 `issue-<编号>` 范围段的目标运行 `mmw artifact path scratch --name <工作名> --issue <编号> --sub <类别内细分>`。

对 reviews 根下的每个候选目标运行 `mmw artifact path review --name <工作名> --sub <审查记录>`。

只有候选路径与命令输出完全相同时，才把它加入删除清单。命令拒绝的条目保留，并在交回时报告。

打印删除清单。逐项确认路径属于当前工作名。然后只删除清单中的路径。

保留 spec、plan、prototype 资产和用户选择保存的 research。也保留其他工作名下的全部内容。

完成判据：删除清单中的路径均不存在。清单外的路径保持原样。

## 交回

再次运行 `mmw artifact path spec --name <工作名>`。逐份运行 `mmw artifact path plan --name <工作名> --sub <计划文件>`。

交回时报告以下内容：

- spec 的仓库相对路径。
- 每份 plan 的仓库相对路径。
- 已删除的过程材料路径。
- 因无法确认归属而保留的路径。
- 这条分支就绪待集成。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 前置条件全部满足，而且清理完成 | **停**：交回上述五项。用户要立即集成时移交 `$mmw:mmw-integrate` |
| 候选路径无法由 `mmw artifact path` 解析 | **停**：保留该路径，并报告命令、输出和候选路径 |
| 终审还没跑 | **停**：回 `$mmw:mmw-implement` 第 7 步发起终审 |
| 终审有采信项尚未修复 | **停**：按 `$mmw:mmw-review` 第 7 步完成修复验证 |
