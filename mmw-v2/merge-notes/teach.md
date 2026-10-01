# teach

源目录：`mmw-v2/upstream/skills/productivity/teach/`

## 总原则

上游把课件当**一个目录里的一套文件**：组件放 `./assets/`，课件用相对路径链过去。这在磁盘上成立，但 user 实际看课件时多数不是「用浏览器打开那个目录里的确切路径」——编辑器预览、渲染面板、把单个文件发给别人，相对路径全部落空，课件到手是一堆无样式的文字，而且 user 没法判断 agent 到底有没有写样式。

两条独立的病因，两个改法：

- **样式丢** —— 页面靠相对路径外链组件。改成嵌入：`./assets/` 仍是唯一可编辑的源，课件里放灌进去的副本。这样课件被单独预览、转发也照样对。
- **跨文档链接点不动** —— `file://` 下浏览器不让页面碰自己目录之外的东西，`./lessons/` 与 `./reference/` 互链全部跨目录。嵌入救不了这个，改交付方式：起本地 HTTP 服务给 URL。

组件复用本身照收上游，改的只是引用方式和交付方式。

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 保留，与上游一致；`agents/openai.yaml` 的 `policy.allow_implicit_invocation: false` 一起保留。理由：它把当前目录当成教学工作区，写 `MISSION.md`、`lessons/`、`reference/`、`learning-records/`、`assets/build.py` 并起本地 HTTP 服务；模型可触发时，在产品仓库里问一句「教我 X 怎么工作」就会把这些写进产品根目录。上游改这一行 → 收上游，两处一起跟。规则见 [README.md](README.md#disable-model-invocation) |
| Lessons：`If possible, open the lesson file…` | 改成「起本地 HTTP 服务、给 URL」，理由写在正文：`file://` 下有些浏览器不让页面碰自己目录之外的东西，`./lessons/` 与 `./reference/` 互链因此失效。上游那句落到 `open <file>` 就是 `file://`。`file://` 的浏览器行为是我们的说法，未实测 |
| Lessons：`zone of proximal development` 那段之后新增段（`The reader knows nothing about this topic.` 起） | 我们加的整段。上游只说课件要短、要美；这段定读者（对主题一无所知）和图、字的分工：图管是什么与怎么连，字只做图做不到的三件事（图答的是哪个问题、重点在哪、由此得出什么），字重复图就删字，图要一段话才看得懂就重画。同一段也在 `wait-what/VISUAL.md` 的 `## Draw the page` 与 `improve-codebase-architecture/HTML-REPORT.md` 的 `## Candidate card`，改一处，三处一起改。上游改前后段落 → 收上游，这一段原样保留 |
| Assets：`write it as a component in ./assets/ and link to it` | 删掉 `and link to it`。组件仍然只写在 `./assets/`，但课件不链它 |
| Assets：`every lesson links it` | 删掉。理由同上 |
| Assets：新增 `### Self-contained pages` | 我们加的整节：`<!--CSS-->` / `<!--JS-->` 标记块、`./assets/build.py` 回填，理由写在正文：课件常在目录之外被打开（编辑器预览、渲染面板、转发的单个文件），相对路径外链的组件全部落空，课件到手是无样式的纯文字，所以每页把用到的组件都嵌进去 |
| `## Teaching Workspace` 第一句之后 | 我们加的：工作区是用户学习的那个目录，不是本技能自己放 `*-FORMAT.md` 的目录；当前目录属于别的项目时，先问清楚工作区在哪再动笔。理由：上游 issue #377（OPEN）记录了课件被写进技能目录的真实事故；本机技能目录解析到冻结的安装工作树，写进去就是改了根 `AGENTS.md` `## Self-hosting boundary` 要求不动的安装副本。上游修掉 #377 → 收上游，删我们这一句 |
| `## Teaching Workspace` 文件清单加 `GLOSSARY.md` 一项 | 我们加的：工作区的标准术语表，一个概念一个名字，每份课件和学习记录都用它，格式见 `GLOSSARY-FORMAT.md`。理由：上游 issue #559（OPEN）记录 `GLOSSARY-FORMAT.md` 是个没有入口的孤儿文件，`LEARNING-RECORD-FORMAT.md` 却已经把 `[[GLOSSARY.md]]` 当成存在的文件引用。上游修掉 #559 → 收上游，删我们这一句 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 保留，跟 `SKILL.md` 的 `disable-model-invocation` 一起。规则见 [README.md](README.md#disable-model-invocation) |

## 上游再动这几段时

- 上游改**组件怎么组织、复用到什么程度**（哪些东西算组件、什么时候抽一个新的）→ **收上游**。
- 上游改**课件怎么引用组件**（`link`、`src`、外部 CDN、构建工具）→ **弃上游，保我们的单文件自足**。
- 上游如果自己也走到了嵌入方案但换了别的机制（例如换标记语法或换构建脚本名）→ **收上游的机制，删掉我们这一节**，避免两套写法并存。
