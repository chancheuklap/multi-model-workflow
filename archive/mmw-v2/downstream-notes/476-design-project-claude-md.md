# 476-design-project-claude-md

## 改了什么

设计项目根目录要有一份 `CLAUDE.md`，内容是 `mmw-v2/skills/design-pages/references/template-project-claude-md.md` 原样写入。页面约定以它为准：页类前缀 `App · ` / `Component · ` / `Overview`，每个 design page 的 `scene` prop，以及 `data-ui="<区域>.<部件>"`。

## 哪些产物失效

- 没有项目根目录 `CLAUDE.md` 的 Claude Design 项目：在网页里对话的 agent 收不到页面约定，拆页、`scene` prop 和 `data-ui` id 没有同一出处。
- 仍把页面约定写在仓库 skill 正文、而不写进设计项目的做法失效。
- screen contract 的格式和 `.mmw/target.json` 的字段没有改变。target trees 不因这一份说明单独失效。

## 怎么迁

1. 用 `write_files` 把 `template-project-claude-md.md` 原样写成该设计项目根目录的 `CLAUDE.md`（新建项目时，`edit-pages.md` 建立项目的第 4 步就会写）。
2. 已有页面按这份 `CLAUDE.md` 补 `scene` prop、`data-ui` id 和页类前缀；未上线功能列进 `out_of_scope`。
3. 之后的设计改动在 Claude Design 里做，再用 `pull_design.py` 写入 handoff package。
