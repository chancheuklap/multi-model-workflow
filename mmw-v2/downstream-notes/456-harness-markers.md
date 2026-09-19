# 456-harness-markers

## 改了什么

1. `.mmw/target.json` 必须声明 `harness_markers`（字符串列表）：本产品只为让自己可被驱动而使用的后门标记。`[]` 是合法回答。没有这个键时 `harness-guard.py` 退出 2，点名该键与 `target_config.py --check`，不回退到以前写死的 `/api/dev/`、`transport off`、`__stub`。
2. story service 的代码——`.mmw/stories/` 下的文件，以及 `stories` 命令点名的文件——只引用 `scenes.json`，不引用任何 `.dc.html`。违反时逐个文件一行 `HARNESS DESIGN PAGE <file>:<line>`，退出 1。

## 哪些产物失效

- `.mmw/target.json`：没有 `harness_markers` 的，`harness-guard.py` 从绿变红（退出 2）；`target_config.py --check` 报缺。agentflow 原来靠写死的 Gateway 标记，现在要自己列出。
- story service：直接打开或渲染 `.dc.html` 的捷径现在是 `HARNESS DESIGN PAGE`。ticket 的 `CHECK: harness-guard.py .` 形状不变，但缺键或引用 design page 都会让它不再打印 `HARNESS OK`。
- screen contract 与 target trees 不因此失效。

## 怎么迁

1. 在消费仓库根跑 `python3 <ui-acceptance scripts>/target_config.py --check`，按它点名的缺项填 `harness_markers`。原先依赖写死标记的仓库把实际在用的字符串列出来，例如 `["/api/dev/", "transport off", "__stub"]`；这个产品没有后门标记就写 `[]`。
2. story service 改为只读 `scenes.json`（scene data），不要 import、open 或在页面里指向任何 `.dc.html`。
