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
| frontmatter 的 `disable-model-invocation: true` | 删掉，这个 skill 在本仓是模型可触发的；`agents/openai.yaml` 的 `policy.allow_implicit_invocation` 一起删。上游改这一行 → 仍然删。规则见 [README.md](README.md#disable-model-invocation) |
| Lessons：`If possible, open the lesson file…` | 改成「起本地 HTTP 服务、给 URL」。上游那句落到 `open <file>` 就是 `file://`，Safari 一类浏览器不允许 `file://` 页面碰自己目录之外的东西，跨目录的样式和超链接一起失效 |
| Assets：`write it as a component in ./assets/ and link to it` | 删掉 `and link to it`。组件仍然只写在 `./assets/`，但课件不链它 |
| Assets：`every lesson links it` | 删掉。理由同上 |
| Assets：新增 `### Self-contained pages` | 我们加的整节：`<!--CSS-->` / `<!--JS-->` 标记块、`./assets/build.py` 回填 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉，跟 `SKILL.md` 的 `disable-model-invocation` 一起。规则见 [README.md](README.md#disable-model-invocation) |

## 上游再动这几段时

- 上游改**组件怎么组织、复用到什么程度**（哪些东西算组件、什么时候抽一个新的）→ **收上游**。
- 上游改**课件怎么引用组件**（`link`、`src`、外部 CDN、构建工具）→ **弃上游，保我们的单文件自足**。
- 上游如果自己也走到了嵌入方案但换了别的机制（例如换标记语法或换构建脚本名）→ **收上游的机制，删掉我们这一节**，避免两套写法并存。
