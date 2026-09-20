# 220-target-json-fields

## 改了什么

`.mmw/target.json` 的字段改为 `start`、`stop`、`discover`、`stories`、`journeys`（默认 `.mmw/journeys`）、`leaves_machine`、`instance`（可选）、`checks`（可选）。`reach`、`transport_off`、`transport_on` 不再是要答的字段。`discover` 打印 origin 类地址加 `instance` / `instance_check`，不再按 electron / web / extension 分地址键。旅程由 `journey.py run <name>` 起停产品。

## 哪些产物失效

- `.mmw/target.json`：仍写 `reach` / `transport_off` / `transport_on`、或缺 `stories` 的，`target --check` 从绿变红（旧键不再被点名，缺 `stories` 被点名）。
- ticket 的 `CHECK:`：整机 `wiring-check.py` / `visual-parity.py` 与手写 `reach` 到达的判据不再是这套字段能驱动的形状；旅程判据改为 `journey.py run <name>`，`EXPECT: JOURNEY OK <name>`。
- screen contract 与 target trees 不因此失效。

## 怎么迁

在消费仓库根跑 `python3 <drive-target scripts>/screen_driver.py target --check`，按它点名的缺项填 `stories`，删掉 `reach` / `transport_off` / `transport_on`。`discover` 改为打印 `origin`、`instance`、`instance_check`。旅程脚本放到 `.mmw/journeys/<name>/`（目录里一个可执行的 `run`，或 `package.json` 的 `scripts.run`）。
