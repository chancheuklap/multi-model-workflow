# 492-skeleton-by-data-ui-id

## 改了什么

`extract_skeleton.py` 现在按 `(page, data-ui id)` 列出控件，同一个列表项 id
只列一次。它只渲染 `scenes.json` 声明的 scene，并从 screen contract 读取
`locale` 和 `viewports`。它不再生成 target trees。`target_config.py --check`
只校验 `.mmw/target.json` 的运行时字段；`kind` 等旧键会报告为 `stale`，但不影响
退出码。

## 哪些产物失效

- 调用 `extract_skeleton.py` 而没有传 `--contract` 的 ticket `CHECK:` 或 agent
  指令失效。
- 没有顶层 `locale` 或 `viewports` 的 screen contract 不能用于提取 skeleton。
- 依赖 `docs/specs/<effort>/targets/` 下 `.aria` 和 `.classes` 文件的 screen
  contract 配套产物失效；新版提取器不再生成这些 target trees，这些目录可删除。
- `.mmw/target.json` 里的 `kind` 不再参与校验，可以删除。
- 调用 `target_config.py --kinds`、`--kind` 或 `--contract` 的 ticket `CHECK:` 或
  agent 指令失效。

## 怎么迁

1. 在 screen contract 顶层写明 `locale` 和 `viewports`。
2. 把 skeleton 命令改为
   `uv run python <scripts>/extract_skeleton.py <handoff> <skeleton.json> --contract <screen-contract.yaml>`。
3. 删除 screen contract 配套的 `targets/` 目录，以及生成或校验 `.aria`、
   `.classes` target tree 的步骤。
4. 从 `.mmw/target.json` 删除 `kind`；把 `target_config.py --check` 和
   `target_config.py --validate` 调用中的 `--kind`、`--contract` 去掉。
