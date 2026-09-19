# 450-target-config-check

## 改了什么

`screen_driver.py target --check` 改为 `target_config.py --check`。`screen_driver.py` 已删除，不留转发文件。离线渲染 design side 的代码在 `design_render.py`。输出与退出码与原先 `target --check` 相同。

## 哪些产物失效

- 消费仓库 ticket 里写 `screen_driver.py target --check` 的 `CHECK:`。
- 写着 `screen_driver.py` 路径的 agent 指令（例如 `<ui-acceptance scripts>/screen_driver.py target --check`）。
- screen contract 的格式和 `.mmw/target.json` 的字段没有改变。

## 怎么迁

把 `CHECK:` 和文档里的 `screen_driver.py target --check` 换成 `target_config.py --check`。`--repo`、`--kind`、`--contract` 参数不变。跑通的标志仍是退出 0 且打印 `complete: the judges can drive this repository`。
