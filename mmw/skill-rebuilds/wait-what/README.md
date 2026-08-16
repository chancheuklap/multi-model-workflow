# Wait What 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Wait What。当前发布技能位于 `mmw/skills-src/mmw-wait-what/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（一份 7 行 `SKILL.md`）。候选是 **2 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)、[`candidate/HTML.md`](candidate/HTML.md)，按将来位于 `mmw/skills-src/mmw-wait-what/` 书写。技能名是 `mmw-wait-what`。现役技能源目录已改为 `mmw-wait-what`。

上游那一句留下：补上下文、ASD-STE100、领域通用语言。`CONTEXT.md` 换成 `mmw domain path`。默认仍是上一条消息；用户点名文档时说明那份文档。

已叠进候选的接线：

- 三个分支：更简单的文字；解释 HTML（读 `HTML.md`）；要点按钮走状态模型时移交 `/mmw-prototype` 的 Logic HTML。本技能是 user-invoked，别人调不到它，所以 Logic HTML 的做法不写在这里。
- `HTML.md` 是可视化**方法**：图承担主要说明、脚手架、图种、文风。借鉴 `improve-codebase-architecture/candidate/HTML-REPORT.md` 的写法，去掉架构审查专用的 candidate card、glossary 和推荐节。
- 覆盖范围：对话里的回答，以及 MMW 过程里的文档。
- 解释 HTML 的落点：仓库文件写在旁边；上一条消息写到系统临时目录。然后打开。`artifacts.json` 里 `explanation` 仍是 `external`，本轮不改 CLI。

未叠（现役 `VISUAL.md` 有、当作手续丢掉）：

- 「路线一 / 路线二」作为文件骨架。
- 问用户保存到哪个目录。
- 宿主把 HTML 发布成网页、`<同名>.url`、复用上次站点。
- 按调用方是否在等待列完成表。
- `agents/openai.yaml`。`SKILL.md` 已有 `disable-model-invocation: true`。现役仍有这份 Codex 包装；发布时不要再拷进去。

leaf 草稿见 [`candidate/leaf-terms.md`](candidate/leaf-terms.md)。

发布时调用写成 `/mmw-wait-what`。目录与 `name:` 已是 `mmw-wait-what`。同一轮还要核：`mmw/install.sh` 的 Grok 技能拷贝、`mmw/.claude-plugin/plugin.json` 的技能路径、根 `README.md` 技能表。

本轮不派冷读 subagent。

## 先前阶段（中文重建）

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐段中文翻译。翻译保持重新表述、补充必要上下文、ASD-STE100 简化技术英语和通用语言四项要求，不加入 MMW 的可视化、文件保存或 Sites 接线。

第二阶段已经形成单文件精简稿。上游正文只有一个执行段落，没有需要删除的方法内容，因此精简稿完整保留翻译基线。

第三阶段已经在 `../candidate/skills/wait-what/` 形成两文件候选。那份中文候选不是本轮英文底稿。现役 `VISUAL.md` 从那一轮进了发布面：保存、发布、对话内 fragment 的手续多，怎么画几乎没有。本轮英文候选用 `HTML.md` 换掉它。

## 文件

| 文件 | 作用 |
| --- | --- |
| [upstream-1.2.2.zh-CN.md](upstream-1.2.2.zh-CN.md) | 上游 1.2.2 的逐段中文翻译基线 |
| [translation-audit.md](translation-audit.md) | 术语选择、逐段完整性与无新增语义检查 |
| [simplified.zh-CN.md](simplified.zh-CN.md) | 完整保留上游方法的单文件精简稿 |
| [candidate/](candidate/) | 本轮英文接线候选 |
