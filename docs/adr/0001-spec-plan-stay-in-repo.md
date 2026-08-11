# spec 与 plan 长期留在仓库，废除 Wiki 归档

MMW 原来在 `/mmw-closing` 收尾时把 spec 与 plan 推到 GitHub Wiki，再从仓库删除 `docs/specs/<任务 slug>/` 与 `docs/plans/<任务 slug>/`，Wiki 页面是唯一的长期副本。现在改为：spec 与 plan 长期留在仓库，收尾不再删除；`/mmw-closing` 不再写 Wiki；`mmw wiki` 的 `ensure`、`nav`、`verify` 三个子命令退役。理由是仓库里的 spec 与代码在同一条 Git 历史上，能通过提交和 PR 关联到实现，而 Wiki 是另一个 Git 仓库，没有分支，也不参与 PR。

## Considered Options

- **保持现状**：仓库任务期间有，收尾删除，Wiki 页面是唯一长期副本。否决理由有两条。第一，仓库里长期保留领域文档、ADR、prototype 资产和 research，删掉 spec 会让这几样失去它们服务的那份合同。第二，`/mmw-closing` 规定同一个任务 slug 第二次归档时覆盖那一页，也就是同一份 spec 的演进；演进要求下一轮 `/mmw-to-spec` 读到旧 spec，而旧 spec 在仓库里已被删除，在 Wiki 里没有读回路径。`mmw wiki` 只有 `ensure`、`nav`、`verify` 三个子命令，没有把页面内容取回给技能使用的命令。
- **两处都是长期落点**：仓库和 Wiki 各留一份。否决理由是它要额外定一条同步规则，以及两份不一致时哪一份算数。
- **降级成可选的对外发布面**：默认关闭，仓库显式打开才写 Wiki。否决理由同上，可选不改变需要同步规则这一点。

## Consequences

- `mmw/cli/lib/wiki.sh` 整份作废，`mmw` 主入口的 `wiki` 子命令与用法说明一并移除。
- `/mmw-closing` 现有七步中的前六步作废，只剩清理当前任务的过程材料。该技能保留，继续作为「这条分支就绪待集成」的判定点。
- `mmw/skills-src/mmw-start/resuming.md` 的「有没有归档」检查项，由查 Wiki 页面改为查仓库路径。
- spec 与 plan 文件头写 YAML 元数据块。spec 五个字段：`slug`、`summary`、`date`、`branch`、`spec_issue`。plan 一个字段：`ticket`，值是对应的 tracer bullet ticket 的 GitHub issue 编号；plan 文件名中的两位编号是拆 ticket 时的顺序编号，不是 issue 编号。
- 仓库里有一份自动生成的 spec 索引，内容取自各份 spec 的元数据块，收录全部 spec，包括尚未完成的。索引由一条 CLI 命令全量重建，不做增量。
- 不设 `pr` 字段。spec 与实现 PR 的关系由 GitHub 维护：PR 描述写 `Closes #<spec issue 编号>` 之后，该 PR 出现在这张 spec issue 页面上。MMW 中没有任何技能创建或读取 PR，因此没有可靠的回填人。
- 同一个任务 slug 第二次做时覆盖原文件，不在文件里手写修订记录；修订历史由 `git log --follow` 回答。
- 本次没有迁移对象。用户确认从未运行 `/mmw-closing`，也从未使用 Wiki；MMW 自身仓库的 Wiki 未初始化，克隆返回 `Repository not found`。
- 元数据块与索引文件的精确路径和文件名不在本决定内，由 MMW 产物落点合同确定。

来源：Wayfinder decision ticket #27「spec 与 plan 要不要长期留在仓库里」，map #18「MMW 产物归纳与接线合同」。
