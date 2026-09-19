# 473-handoff-package-by-pull

## 改了什么

`pull_design.py <manifest.json> <handoff dir> [--reread <dir>] [--tools <dir>]` 现在从 Claude Design 预览完整下载项目，并自动写 `design-manifest.json`、`scenes.json`、scene data、`vendor/` 与 `README.md`。`README.md` 的固定标题是 `# Claude Design handoff package`、`## Viewport and size source`、`## Offline render check`、`## Pull provenance`。scene data 改为按 `data-ui` id 嵌套的显示文字；重复 id 是按文档顺序的列表。scene prop 固定名为 `scene`，每个 scene 名固定为 `<page>.<value>`。

## 哪些产物失效

- consuming repository 中手写的 handoff package `README.md` 与 `scenes.json` 失效；旧的 `{state, vals}` scene data 也失效。
- 使用 `scenario` 或其他 prop 名的 Claude Design 页面不能生成 scene；agentflow 工作监控的现有页面属于这一类。
- screen contract 与 story adapter 中引用旧 scene 名或读取旧 scene data 形状的行失效。
- **target trees**：`scenes.json` 重新生成后，`docs/specs/<effort>/targets/<page>.aria` 与 `.classes` 头部的 `# scenes.json sha256=` 失配，必须随 screen contract 一起重建。
- ticket `CHECK:` 中直接运行 `export_scene_data.py` 的命令失效；该脚本已移出 live skill。

## 怎么迁

1. 把每个 design page 的状态 prop 改名为 `scene`，保留 `editor: "enum"`、`options` 与需要的 `out_of_scope`。
2. 用 `mcp__claude-design__list_files`（`depth: -1`）保存 manifest，用 `render_preview` 的 `serve_url` 设置一次 `MMW_DESIGN_PREVIEW_URL`，再运行 `pull_design.py <manifest.json> <handoff dir>`；只在命令列出的文本文件需要补读时，加 `--reread <dir>` 重跑。
3. 按新生成的 `scenes.json`，把 screen contract 与 story 中的引用改为 `<page>.<value>`；把 story adapter 改为读取以 `data-ui` id 为键、子元素嵌套、重复 id 为列表的新 scene data。
