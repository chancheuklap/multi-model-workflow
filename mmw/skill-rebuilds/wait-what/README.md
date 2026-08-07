# Wait What 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Wait What。当前发布技能仍位于 `mmw/skills/wait-what/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐段中文翻译。翻译保持重新表述、补充必要上下文、ASD-STE100 简化技术英语和通用语言四项要求，不加入 MMW 的可视化、文件保存或 Sites 接线。

第二阶段已经形成单文件精简稿。上游正文只有一个执行段落，没有需要删除的方法内容，因此精简稿完整保留翻译基线。

第三阶段已经在 `candidate/` 形成三文件候选。`candidate/SKILL.md` 保留手动调用，并在文字重述、普通文档可视化和 Logic HTML 三种请求之间路由；`candidate/VISUAL.md` 负责普通文档解释；`candidate/LOGIC.md` 负责让用户用按钮驱动状态模型。Logic HTML 只保存本地产物，除非用户明确要求发布。当前发布技能仍不修改。

## 文件

| 文件 | 作用 |
| --- | --- |
| [upstream-1.2.2.zh-CN.md](upstream-1.2.2.zh-CN.md) | 上游 1.2.2 的逐段中文翻译基线 |
| [translation-audit.md](translation-audit.md) | 术语选择、逐段完整性与无新增语义检查 |
| [simplified.zh-CN.md](simplified.zh-CN.md) | 完整保留上游方法的单文件精简稿 |
| [candidate/](candidate/) | 增加 MMW 领域上下文、普通可视化和 Logic HTML 路由的候选技能 |

本目录中的候选不会被 `mmw skills materialize` 物化。
